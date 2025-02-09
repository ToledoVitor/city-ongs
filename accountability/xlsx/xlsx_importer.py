# ruff: noqa: E722

from datetime import datetime
from decimal import Decimal
from typing import Tuple

import numpy as np
import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction

from accountability.models import Accountability, Expense, Revenue
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

        self._store_fr_ids()
        self._store_cb_ids()
        self._store_fv_ids()
        self._store_ia_ids()
        self._store_nr_choices()
        self._store_nd_choices()
        self._store_td_choices()

        revenues_error = self._create_revenues(revenues_df)
        expenses_error = self._create_expenses(expenses_df)
        applications_error = self._create_applications(applications_df)

        imported = False in [revenues_error, expenses_error, applications_error]

        return imported, revenues_error, expenses_error, applications_error

    def _store_fr_ids(self) -> None:
        df = pd.read_excel(self.file, sheet_name="FR")
        mapped_frs = {}
        for line in df.values.tolist():
            mapped_frs[line[0]] = line[1]

        self.mapped_frs = mapped_frs

    def _store_cb_ids(self) -> None:
        df = pd.read_excel(self.file, sheet_name="CB")
        mapped_cbs = {}
        for line in df.values.tolist():
            mapped_cbs[line[0]] = line[1]

        self.mapped_cbs = mapped_cbs

    def _store_fv_ids(self) -> None:
        df = pd.read_excel(self.file, sheet_name="FV")
        mapped_fvs = {}
        for line in df.values.tolist():
            mapped_fvs[line[0]] = line[1]

        self.mapped_fvs = mapped_fvs

    def _store_ia_ids(self) -> None:
        df = pd.read_excel(self.file, sheet_name="IA")
        mapped_ias = {}
        for line in df.values.tolist():
            mapped_ias[line[0]] = line[1]

        self.mapped_ias = mapped_ias

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
        for line in revenues_df.values.tolist()[1:]:
            if not line[2]:
                break

            receive_date = line[4]
            competency = line[5]
            revenues.append(
                Revenue(
                    accountability=self.accountability,
                    identification=line[2],
                    value=Decimal(line[3]),
                    receive_date=datetime(
                        receive_date.year, receive_date.month, receive_date.day
                    ),
                    competency=datetime(
                        competency.year, competency.month, competency.day
                    ),
                    source_id=self.mapped_frs.get(line[6]),
                    bank_account_id=self.mapped_cbs.get(line[7]),
                    revenue_nature=self.mapped_nrs.get(line[8]),
                    observations=line[9],
                )
            )

        error = False
        try:
            with transaction.atomic():
                Revenue.objects.bulk_create(revenues, batch_size=10)
                return error
        except:
            error = True
            return error

    def _create_expenses(self, expenses_df: pd.DataFrame) -> dict:
        expenses_df = expenses_df.replace({np.nan: None})

        expenses = []
        for line in expenses_df.values.tolist()[1:]:
            if not line[2]:
                break

            planned = bool(line[9])

            due_date = line[4]
            competency = line[5]
            expenses.append(
                Expense(
                    accountability=self.accountability,
                    planned=planned,
                    identification=line[2],
                    value=Decimal(line[3]),
                    due_date=datetime(due_date.year, due_date.month, due_date.day),
                    competency=datetime(
                        competency.year, competency.month, competency.day
                    ),
                    source_id=self.mapped_frs.get(line[6], None),
                    nature=self.mapped_nds.get(line[7], None),
                    favored_id=self.mapped_frs.get(line[8], None),
                    item_id=self.mapped_ias.get(line[9], None),
                    document_type=self.mapped_tds.get(line[10], None),
                    document_number=line[11],
                    observations=line[12],
                )
            )

        error = False
        try:
            with transaction.atomic():
                # TODO: Validate here the expense items
                Expense.objects.bulk_create(expenses, batch_size=10)
                return error
        except:
            error = True
            return error

    def _create_applications(self, applications_df: pd.DataFrame) -> dict:
        applications_df = applications_df.replace({np.nan: None})

        transactions = []
        for line in applications_df.values.tolist()[1:]:
            if not line[2]:
                break

            if line[4]:
                transaction_date = line[3]
                transactions.append(
                    Transaction(
                        name="Aplicação / Resgate",
                        amount=Decimal(line[2] * -1),
                        date=datetime(
                            transaction_date.year,
                            transaction_date.month,
                            transaction_date.day,
                        ),
                        bank_account_id=self.mapped_cbs.get(line[4]),
                        origin_source_id=self.mapped_frs.get(line[5]),
                        transaction_type=Transaction.TransactionTypeChoices.OTHER,
                    )
                )

            elif line[6]:
                transaction_date = line[3]
                transactions.append(
                    Transaction(
                        name="Aplicação / Resgate",
                        memo="Aplicação / Resgate",
                        amount=Decimal(line[2]),
                        date=datetime(
                            transaction_date.year,
                            transaction_date.month,
                            transaction_date.day,
                        ),
                        bank_account_id=self.mapped_cbs.get(line[6]),
                        destination_source_id=self.mapped_frs.get(line[7]),
                        transaction_type=Transaction.TransactionTypeChoices.INCOME,
                    )
                )

            else:
                continue

        error = False
        try:
            with transaction.atomic():
                Transaction.objects.bulk_create(transactions, batch_size=10)
                return error
        except:
            error = True
            return error
