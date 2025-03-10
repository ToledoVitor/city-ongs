# ruff: noqa: E722

import re
from datetime import datetime
from decimal import Decimal
from typing import Tuple

import numpy as np
import pandas as pd
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction

from accountability.models import Accountability, Expense, Favored, Revenue
from bank.models import Transaction
from contracts.choices import NatureChoices


class AccountabilityXLSXImporter:
    def __init__(self, file: InMemoryUploadedFile, accountability: Accountability):
        self.file = file
        self.accountability = accountability

    def handle(self) -> Tuple[bool, bool, bool, bool]:
        try:
            revenues_df = pd.read_excel(self.file, sheet_name="1. RECEITAS")
            expenses_df = pd.read_excel(self.file, sheet_name="2. DESPESAS")
            applications_df = pd.read_excel(
                self.file, sheet_name="3. APLICACOES E RESGATES"
            )
        except ValueError:
            raise ValueError("Excel sheets are not in the right format")

        self._store_fd_ids()
        self._store_cb_ids()
        self._store_fv_ids()
        self._store_ia_ids()
        self._store_fr_choices()
        self._store_nr_choices()
        self._store_nd_choices()
        self._store_td_choices()

        revenues_error = self._create_revenues(revenues_df)
        expenses_error = self._create_expenses(expenses_df)
        applications_error = self._create_applications(applications_df)

        imported = False in [revenues_error, expenses_error, applications_error]

        return imported, revenues_error, expenses_error, applications_error

    def _store_fd_ids(self) -> None:
        df = pd.read_excel(self.file, sheet_name="FD")
        mapped_fds = {}
        for line in df.values.tolist():
            mapped_fds[line[0]] = line[1]

        self.mapped_fds = mapped_fds

    def _store_cb_ids(self) -> None:
        df = pd.read_excel(self.file, sheet_name="CB")
        mapped_cbs = {}
        for line in df.values.tolist():
            mapped_cbs[line[0]] = line[1]

        self.mapped_cbs = mapped_cbs

    def _store_fv_ids(self) -> None:
        df = pd.read_excel(self.file, sheet_name="FV")
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
            # Favored already exists
            if doc and doc in existing_map:
                continue

            # New Favored
            new_favoreds.append(
                Favored(
                    organization=organization,
                    name=str(record["name"])[:127],
                    document=doc,
                )
            )

        if new_favoreds:
            Favored.objects.bulk_create(new_favoreds)

        all_favored = Favored.objects.filter(
            organization=organization,
            document__in=documents,
        )

        mapped_fvs = {fav.name: str(fav.id) for fav in all_favored}
        self.mapped_fvs = mapped_fvs

    def _store_ia_ids(self) -> None:
        df = pd.read_excel(self.file, sheet_name="IA")
        mapped_ias = {}
        for line in df.values.tolist():
            mapped_ias[line[0]] = line[1]

        self.mapped_ias = mapped_ias

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

    def _create_revenues(self, revenues_df: pd.DataFrame) -> dict:
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
            errors.append(f"Linha {index}: {" ".join(e.messages)}")

        if errors:
            return errors

        try:
            with transaction.atomic():
                Revenue.objects.bulk_create(revenues, batch_size=100)
            return []
        except Exception:
            return errors

    def _create_expenses(self, expenses_df: pd.DataFrame) -> dict:
        expenses_df = expenses_df.replace({np.nan: None})

        expenses = []
        errors = []
        for index, line in enumerate(expenses_df.values.tolist()[1:], start=2):
            if not line[2]:
                break

            planned = bool(line[9])

            due_date = line[4]
            competency = line[5]
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
                item_id=self.mapped_ias.get(line[9], None),
                document_type=self.mapped_tds.get(line[10], None),
                document_number=line[11],
                observations=line[12],
            )

            try:
                expense.full_clean()
                expenses.append(expense)
            except ValidationError as e:
                errors.append(f"Linha {index}: {" ".join(e.messages)}")

        if errors:
            return errors

        try:
            with transaction.atomic():
                Expense.objects.bulk_create(expenses, batch_size=10)
                return []
        except:
            return errors

    def _create_applications(self, applications_df: pd.DataFrame) -> dict:
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
                errors.append(f"Linha {index}: {" ".join(e.messages)}")

        if errors:
            return errors

        try:
            with transaction.atomic():
                Transaction.objects.bulk_create(transactions, batch_size=10)
                return []
        except:
            return errors
