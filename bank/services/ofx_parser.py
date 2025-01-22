import logging
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from ofxtools.Parser import OFXTree

from bank.models import BankAccount, BankStatement, Transaction
from contracts.models import Contract

logger = logging.getLogger(__name__)


@dataclass
class OFXFileParser:
    ofx_data = None

    def __init__(self, ofx_file: InMemoryUploadedFile, *args, **kwargs):
        ofx_data = self._parse_ofx_file(ofx_file)
        self.ofx_data = ofx_data

    @property
    def account_data(self) -> dict:
        return {
            "bank_name": self.ofx_data.org,
            "bank_id": self.ofx_data.bankmsgsrsv1.statements[0].bankid,
            "agency_id": self.ofx_data.bankmsgsrsv1.statements[0].branchid,
            "account_id": self.ofx_data.bankmsgsrsv1.statements[0].acctid,
        }

    @property
    def balance_amount(self) -> Decimal:
        return self.ofx_data.bankmsgsrsv1.statements[0].balance.balamt

    @property
    def balance_date(self) -> datetime:
        return {
            "date_start": self.ofx_data.bankmsgsrsv1.statements[0].dtstart,
            "date_end": self.ofx_data.bankmsgsrsv1.statements[0].dtend,
        }

    @property
    def transactions_list(self) -> list:
        return self.ofx_data.statements[0].transactions

    def is_account_already_created(self) -> bool:
        return False

    def create_bank_account(self, contract: Contract, account_type: str) -> bool:
        account_data = self.account_data

        bank_name = account_data["bank_name"]
        bank_id = account_data["bank_id"]
        agency = account_data["agency_id"]
        account = account_data["account_id"]

        if BankAccount.objects.filter(
            bank_name=bank_name,
            bank_id=bank_id,
            agency=agency,
            account=account,
            account_type=account_type,
        ).exists():
            logger.warning(
                f"Bank Account {account_data["account_id"]} - Already exists"
            )
            raise ValidationError("Conta bancária já cadastrada.")

        with transaction.atomic():
            bank_account = BankAccount.objects.create(
                bank_name=bank_name,
                bank_id=bank_id,
                agency=agency,
                account=account,
                account_type=account_type,
                balance=self.balance_amount,
            )
            if account_type == "CHECKING":
                contract.checking_account = bank_account
            elif account_type == "INVESTING":
                contract.investing_account = bank_account
            else:
                logger.info(f"Account type of {account_type} is not a valid type")
                raise ValidationError(f"Conta tipo {account_type} não é valida")

            contract.save()

            balance_date = self.balance_date
            BankStatement.objects.create(
                bank_account=bank_account,
                balance=self.balance_amount,
                opening_date=balance_date["date_start"],
                closing_date=balance_date["date_end"],
            )

            transactions = self._updated_transactions(bank_account)
            Transaction.objects.bulk_create(transactions)

            return bank_account

    def update_bank_account_balance(self) -> bool:
        return ...

    def _updated_transactions(self, bank_account: BankAccount) -> None:
        return [
            Transaction(
                bank_account=bank_account,
                transaction_type=transaction.trntype,
                transaction_id=transaction.fitid,
                name=transaction.name,
                amount=transaction.trnamt,
                date=transaction.dtposted,
                memo=getattr(transaction, "memo", None),
            )
            for transaction in self.transactions_list
        ]

    def _parse_ofx_file(self, ofx_file: InMemoryUploadedFile):
        ofx_content = ofx_file.read().decode("latin1")

        modified_ofx_content = self._truncate_checknum_in_memory(ofx_content)
        with tempfile.NamedTemporaryFile(
            delete=False, mode="w", suffix=".ofx"
        ) as temp_file:
            temp_file.write(modified_ofx_content)
            temp_file_path = temp_file.name

        ofx_tree = OFXTree()
        ofx_tree.parse(temp_file_path)

        ofx = ofx_tree.convert()
        return ofx

    def _truncate_checknum_in_memory(self, ofx_content, max_length=12):
        """
        Truncate the values of 'checknum' OFX file content in memory.
        Some values of checknum has more than 12 digist which is the max_length for the field
        """

        def truncate_match(match):
            value = match.group(1)
            return f"<CHECKNUM>{value[:max_length]} \r\n\t"

        pattern = r"<CHECKNUM>(.*?) \r\n\t"
        modified_ofx_content = re.sub(pattern, truncate_match, ofx_content)
        return modified_ofx_content
