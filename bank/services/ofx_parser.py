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
    def opening_balance_amount(self) -> Decimal:
        return self.ofx_data.bankmsgsrsv1.statements[0].balance.balamt

    @property
    def closing_balance_amount(self) -> Decimal:
        return self.ofx_data.bankmsgsrsv1.statements[0].ledgerbal.balamt

    @property
    def balance_date(self) -> datetime:
        return self.ofx_data.bankmsgsrsv1.statements[0].dtend

    @property
    def statement_start_date(self) -> datetime:
        return self.ofx_data.bankmsgsrsv1.statements[0].dtstart

    @property
    def statement_period_info(self) -> dict:
        start_date = self.statement_start_date
        end_date = self.balance_date
        return {
            "start_date": start_date.strftime("%d/%m/%Y"),
            "end_date": end_date.strftime("%d/%m/%Y"),
            "month": end_date.month,
            "year": end_date.year,
            "month_name": end_date.strftime("%B"),
        }

    @property
    def transactions_list(self) -> list:
        return self.ofx_data.statements[0].transactions

    # def create_bank_account(self, contract: Contract, account_type: str) -> bool:
    #     account_data = self.account_data

    #     bank_name = account_data["bank_name"]
    #     bank_id = account_data["bank_id"]
    #     agency = account_data["agency_id"]
    #     account = account_data["account_id"]

    #     if BankAccount.objects.filter(
    #         bank_name=bank_name,
    #         bank_id=bank_id,
    #         agency=agency,
    #         account=account,
    #         account_type=account_type,
    #     ).exists():
    #         logger.warning(
    #             f"Bank Account {account_data["account_id"]} - Already exists"
    #         )
    #         raise ValidationError("Conta bancária já cadastrada.")

    #     with transaction.atomic():
    #         bank_account = BankAccount.objects.create(
    #             bank_name=bank_name,
    #             bank_id=bank_id,
    #             agency=agency,
    #             account=account,
    #             account_type=account_type,
    #             balance=self.closing_balance_amount,
    #         )
    #         if account_type == "CHECKING":
    #             contract.checking_account = bank_account
    #         elif account_type == "INVESTING":
    #             contract.investing_account = bank_account
    #         else:
    #             logger.info(f"Account type of {account_type} is not a valid type")
    #             raise ValidationError(f"Conta tipo {account_type} não é valida")

    #         contract.save()

    #         # TODO: if has previous statement, delete
    #         BankStatement.objects.create(
    #             bank_account=bank_account,
    #             opening_balance=self.opening_balance_amount,
    #             closing_balance=self.closing_balance_amount,
    #             reference_month=self.balance_date.month,
    #             reference_year=self.balance_date.year,
    #         )

    #         transactions = self._updated_transactions(bank_account)
    #         Transaction.objects.bulk_create(transactions)

    #         return bank_account

    def update_bank_account_balance(self, bank_account: BankAccount) -> bool:
        if BankStatement.objects.filter(
            bank_account=bank_account,
            reference_month=self.balance_date.month,
            reference_year=self.balance_date.year,
        ).exists():
            logger.warning(
                f"Bank Statement for {self.balance_date.month}/{self.balance_date.year} already exists"
            )
            raise ValidationError("Extrato bancário já cadastrada.")

        with transaction.atomic():
            bank_account.balance = self.closing_balance_amount
            bank_account.save()

            BankStatement.objects.create(
                bank_account=bank_account,
                opening_balance=self.opening_balance_amount,
                closing_balance=self.closing_balance_amount,
                reference_month=self.balance_date.month,
                reference_year=self.balance_date.year,
            )

            transactions = self._updated_transactions(bank_account)
            Transaction.objects.bulk_create(transactions)

            return

    def _updated_transactions(self, bank_account: BankAccount) -> None:
        return [
            Transaction(
                bank_account=bank_account,
                transaction_type=transaction.trntype,
                transaction_number=transaction.checknum,
                name=transaction.name,
                amount=transaction.trnamt,
                date=datetime.strptime(transaction.dtposted, "%Y%m%d").date(),
                memo=getattr(transaction, "memo", None),
            )
            for transaction in self.transactions_list
        ]

    def _parse_ofx_file(self, ofx_file: InMemoryUploadedFile):
        # Try multiple encodings to handle different OFX file formats
        encodings_to_try = ["cp1252", "windows-1252", "latin1", "utf-8", "iso-8859-1"]
        ofx_content = None
        for encoding in encodings_to_try:
            try:
                ofx_file.seek(0)
                ofx_content = ofx_file.read().decode(encoding, errors="replace")
                logger.info(f"Successfully decoded OFX file using {encoding} encoding")
                break
            except Exception as e:
                logger.warning(f"Failed to decode with {encoding}: {str(e)}")
                continue

        if ofx_content is None:
            try:
                ofx_file.seek(0)
                raw_content = ofx_file.read()
                ofx_content = raw_content.decode("cp1252", errors="replace")
                logger.warning("Used forced cp1252 decoding with error replacement")
            except Exception:
                raise ValidationError(
                    "Não foi possível decodificar o arquivo OFX. Verifique se o arquivo não está corrompido."
                )

        fixed_ofx_content = self._fix_malformed_ofx(ofx_content)
        modified_ofx_content = self._truncate_checknum_in_memory(fixed_ofx_content)

        # Simple approach: try different encodings for the temp file
        for encoding in ["cp1252", "latin1", "utf-8"]:
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, mode="w", suffix=".ofx", encoding=encoding
                ) as temp_file:
                    temp_file.write(modified_ofx_content)
                    temp_file_path = temp_file.name

                ofx_tree = OFXTree()
                ofx_tree.parse(temp_file_path)
                ofx = ofx_tree.convert()
                logger.info(f"Successfully parsed OFX file with {encoding}")
                return ofx

            except Exception as e:
                logger.warning(f"Failed with {encoding}: {str(e)}")
                continue

        raise ValidationError("Arquivo OFX corrompido e não pode ser processado.")

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

    def _fix_malformed_ofx(self, ofx_content):
        logger.info("Fixing missing closing tags...")

        lines = ofx_content.split("\n")
        fixed_lines = self._fix_missing_closing_tags(lines)
        result_lines = self._fix_stmttrn_blocks(fixed_lines)

        result = "\n".join(result_lines)
        logger.info("Missing closing tags fixed")
        return result

    def _fix_missing_closing_tags(self, lines):
        tags_to_fix = [
            "DTSERVER",
            "LANGUAGE",
            "DTACCTUP",
            "TRNUID",
            "CODE",
            "SEVERITY",
            "CURDEF",
            "BALAMT",
            "DTASOF",
            "MKTGINFO",
        ]

        fixed_lines = []
        for line in lines:
            processed_line = line

            for tag in tags_to_fix:
                if self._needs_closing_tag(processed_line, tag):
                    processed_line = processed_line.rstrip() + f"</{tag}>"
                    break

            fixed_lines.append(processed_line)

        return fixed_lines

    def _needs_closing_tag(self, line, tag):
        opening_tag = f"<{tag}>"
        closing_tag = f"</{tag}>"
        return opening_tag in line and closing_tag not in line

    def _fix_stmttrn_blocks(self, lines):
        result_lines = []

        for i, line in enumerate(lines):
            result_lines.append(line)

            if self._should_close_stmttrn(lines, i, line):
                result_lines.append("\t </STMTTRN>")

        return result_lines

    def _should_close_stmttrn(self, lines, current_index, current_line):
        if current_index + 1 >= len(lines):
            return False

        if not current_line.strip() or current_line.strip().startswith("<"):
            return False

        next_line = lines[current_index + 1].strip()
        return next_line.startswith("<STMTTRN>") or next_line.startswith(
            "</BANKTRANLIST>"
        )
