# ruff: noqa: E722

import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import List, Tuple

import numpy as np
import pandas as pd
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.db.utils import DatabaseError, IntegrityError

from accountability.models import Accountability, Expense, Favored, Revenue
from bank.models import Transaction
from contracts.choices import NatureChoices
from contracts.models import ContractItem

logger = logging.getLogger(__name__)


class AccountabilityXLSXImporter:
    def __init__(self, file: InMemoryUploadedFile, accountability: Accountability):
        self.file = file
        self.accountability = accountability
        self.mapped_fds: dict = {}
        self.mapped_cbs: dict = {}
        self.mapped_fvs: dict = {}
        self.mapped_ias: dict = {}
        self.mapped_frs: dict = {}
        self.mapped_nrs: dict = {}
        self.mapped_nds: dict = {}
        self.mapped_tds: dict = {}

    def handle(self) -> Tuple[bool, List[str], List[str], List[str]]:
        """
        Process the XLSX file and create records.
        Returns tuple of (success, revenue_errors, expense_errors, application_errors)
        """
        try:
            xls = pd.ExcelFile(self.file)
            revenues_df = pd.read_excel(xls, sheet_name="1. RECEITAS")
            expenses_df = pd.read_excel(xls, sheet_name="2. DESPESAS")
            applications_df = pd.read_excel(xls, sheet_name="3. APLICACOES E RESGATES")
        except ValueError:
            raise ValueError("Excel sheets are not in the right format")

        # Store mapping data
        self._store_fd_ids(xls)
        self._store_cb_ids(xls)
        self._store_fv_ids(xls)
        self._store_ia_ids(xls)
        self._store_fr_choices()
        self._store_nr_choices()
        self._store_nd_choices()
        self._store_td_choices()

        # Process each sheet
        revenues_error = self._create_revenues(revenues_df)
        expenses_error = self._create_expenses(expenses_df)
        applications_error = self._create_applications(applications_df)

        imported = not any([revenues_error, expenses_error, applications_error])
        return imported, revenues_error, expenses_error, applications_error

    def _store_fd_ids(self, xls: pd.ExcelFile) -> None:
        df = pd.read_excel(xls, sheet_name="FD")
        self.mapped_fds = {line[0]: line[1] for line in df.values.tolist()}

    def _store_cb_ids(self, xls: pd.ExcelFile) -> None:
        df = pd.read_excel(xls, sheet_name="CB")
        self.mapped_cbs = {line[0]: line[1] for line in df.values.tolist()}

    def _store_fv_ids(self, xls: pd.ExcelFile) -> None:
        df = pd.read_excel(xls, sheet_name="FV")
        organization = self.accountability.contract.organization

        records = [
            {
                "name": row[0],
                "document": re.sub(r"\D", "", str(row[1])) if row[1] else None,
            }
            for row in df.values.tolist()
            if row[0]
        ]
        documents = [record["document"] for record in records if record["document"]]
        existing_favored = Favored.objects.filter(
            organization=organization,
            document__in=documents,
        )

        existing_map = {fav.document: fav for fav in existing_favored}
        new_favoreds = []
        for record in records:
            doc = record.get("document")
            if doc and doc in existing_map:
                continue

            new_favoreds.append(
                Favored(
                    organization=organization,
                    name=str(record["name"])[:127],
                    document=doc,
                )
            )

        if new_favoreds:
            Favored.objects.bulk_create(new_favoreds, ignore_conflicts=True)

        all_favored = Favored.objects.filter(
            organization=organization,
            document__in=documents,
        )

        self.mapped_fvs = {fav.name: str(fav.id) for fav in all_favored}

    def _store_ia_ids(self, xls: pd.ExcelFile) -> None:
        df = pd.read_excel(xls, sheet_name="IA")
        self.mapped_ias = {line[0]: line[1] for line in df.values.tolist()}

    def _store_fr_choices(self) -> None:
        self.mapped_frs = {
            label: value for value, label in Revenue.RevenueSource.choices
        }

    def _store_nr_choices(self) -> None:
        self.mapped_nrs = {label: value for value, label in Revenue.Nature.choices}

    def _store_nd_choices(self) -> None:
        self.mapped_nds = {label: value for value, label in NatureChoices.choices}

    def _store_td_choices(self) -> None:
        self.mapped_tds = {
            label: value for value, label in Expense.DocumentChoices.choices
        }

    def _create_revenues(self, revenues_df: pd.DataFrame) -> List[str]:
        revenues_df = revenues_df.replace({np.nan: None})

        revenues = []
        errors = []
        for index, line in enumerate(revenues_df.values.tolist()[1:], start=2):
            if not line[2]:
                break

            receive_date = line[4]
            competency = line[5]
            revenue = Revenue(
                accountability=self.accountability,
                identification=line[2],
                value=Decimal(line[3]).quantize(Decimal("0.01")),
                receive_date=datetime(
                    receive_date.year, receive_date.month, receive_date.day
                ),
                competency=datetime(competency.year, competency.month, competency.day),
                source=self.mapped_frs.get(line[6]),
                bank_account_id=self.mapped_cbs.get(line[7]),
                revenue_nature=self.mapped_nrs.get(line[8]),
                observations=line[9],
            )

            try:
                revenue.full_clean()
                revenues.append(revenue)
            except ValidationError as e:
                errors.append(f"Receita {line[0]}: {" ".join(e.messages)}")

        if errors:
            return errors

        try:
            with db_transaction.atomic():
                Revenue.objects.bulk_create(revenues, batch_size=100)
            return []
        except (ValidationError, IntegrityError, DatabaseError) as e:
            logger.error("Error creating revenues: %s", str(e))
            return errors

    def _create_expenses(self, expenses_df: pd.DataFrame) -> List[str]:
        expenses_df = expenses_df.replace({np.nan: None})
        expenses = []
        errors = []

        new_expense_per_item = {}

        for index, line in enumerate(expenses_df.values.tolist()[1:], start=2):
            if not line[2]:
                break

            planned = bool(line[9])
            due_date = line[4]
            competency = line[5]
            item_id = self.mapped_ias.get(line[9], None)

            if planned and not item_id:
                errors.append(
                    "Despesa {}: Despesa planejada precisa ter um item "
                    "associado.".format(line[0])
                )
                continue

            expense = Expense(
                accountability=self.accountability,
                planned=planned,
                identification=line[2],
                value=Decimal(line[3]).quantize(Decimal("0.01")),
                due_date=datetime(due_date.year, due_date.month, due_date.day),
                competency=datetime(competency.year, competency.month, competency.day),
                source_id=self.mapped_fds.get(line[6], None),
                nature=self.mapped_nds.get(line[7], None),
                favored_id=self.mapped_fvs.get(line[8], None),
                item_id=item_id,
                document_type=self.mapped_tds.get(line[10], None),
                document_number=line[11],
                observations=line[12],
            )

            try:
                expense.full_clean()
                expenses.append(expense)
                if planned:
                    new_expense_per_item.setdefault(item_id, Decimal("0.00"))
                    new_expense_per_item[item_id] += expense.value
            except ValidationError as e:
                errors.append(f"Despesa {line[0]}: {" ".join(e.messages)}")

        for item_id, new_value in new_expense_per_item.items():
            existing_expenses = Expense.objects.filter(
                item_id=item_id,
                planned=True,
                accountability__contract=self.accountability.contract,
            ).aggregate(total=Sum("value"))["total"] or Decimal("0.00")

            contract_item = ContractItem.objects.get(pk=item_id)
            total_planned = existing_expenses + new_value
            if total_planned > contract_item.anual_expense:
                errors.append(
                    "O total de despesas para o item "
                    f"'{contract_item}' ({total_planned}) ultrapassa o "
                    f"limite anual de {contract_item.anual_expense}."
                )

        if errors:
            return errors

        try:
            with db_transaction.atomic():
                Expense.objects.bulk_create(expenses, batch_size=10)
            return []
        except (ValidationError, IntegrityError, DatabaseError) as e:
            logger.error("Error creating expenses: %s", str(e))
            return errors

    def _create_applications(self, applications_df: pd.DataFrame) -> List[str]:
        applications_df = applications_df.replace({np.nan: None})

        transactions = []
        errors = []
        for index, line in enumerate(applications_df.values.tolist()[1:], start=2):
            if not line[2]:
                break

            if line[4]:
                transaction_date = line[3]
                transaction = Transaction(
                    name="Aplicação / Resgate",
                    memo="Aplicação / Resgate",
                    transaction_type=Transaction.TransactionTypeChoices.OTHER,
                    date=datetime(
                        transaction_date.year,
                        transaction_date.month,
                        transaction_date.day,
                    ),
                    amount=Decimal(abs(line[2]) * -1).quantize(Decimal("0.01")),
                    transaction_number=line[4],
                    bank_account_id=self.mapped_cbs.get(line[5]),
                )

            elif line[6]:
                transaction_date = line[3]
                transaction = Transaction(
                    transaction_type=Transaction.TransactionTypeChoices.INCOME,
                    name="Aplicação / Resgate",
                    memo="Aplicação / Resgate",
                    date=datetime(
                        transaction_date.year,
                        transaction_date.month,
                        transaction_date.day,
                    ),
                    amount=Decimal(abs(line[2])).quantize(Decimal("0.01")),
                    transaction_number=line[4],
                    bank_account_id=self.mapped_cbs.get(line[6]),
                )

            else:
                continue

            try:
                transaction.full_clean()
                transactions.append(transaction)
            except ValidationError as e:
                errors.append(f"Aplicação {line[0]}: {" ".join(e.messages)}")

        if errors:
            return errors

        try:
            with db_transaction.atomic():
                Transaction.objects.bulk_create(transactions, batch_size=10)
            return []
        except (ValidationError, IntegrityError, DatabaseError) as e:
            logger.error("Error creating applications: %s", str(e))
            return errors
