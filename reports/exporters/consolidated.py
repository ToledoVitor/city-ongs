from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db.models import Q, Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense, Revenue
from bank.models import BankStatement, Transaction
from contracts.models import Contract
from reports.exporters.commons.pdf_exporter import CommonPDFExporter
from utils.formats import (
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class ConsolidatedPDFExporter(CommonPDFExporter):
    """PDF exporter for consolidated bank reconciliation reports."""

    # Constants for text
    TITLE = "CONSOLIDADO DAS CONCILIAÇÕES BANCÁRIAS"
    SUBTITLE = "Extrato Bancário"
    BALANCE_TITLE = "Saldos Anteriores"
    RESCUE_TITLE = (
        "Aplicações e Resgates dos Recursos Financeiros"
    )
    REVENUE_TITLE = (
        "Agrupamento das Receitas por Natureza de Receita"
    )
    EXPENSES_TITLE = "Despesas"
    TRANSFERS_TITLE = (
        "Transferências Bancárias para outras contas"
    )
    FINAL_BALANCE_TITLE = "Saldos Finais"
    ANALYTICAL_TITLE = "Visão Analítica dos Lançamentos"
    REIMBURSEMENT_TITLE = (
        "Reembolso de Juros, multas, glosas, pagto. "
        "Indevido, duplicidade etc"
    )
    PUBLIC_TRANSFER_TITLE = "Repasse Público"
    EXPENSES_ANALYSIS_TITLE = "Despesas"
    UNCONCILED_BANK_TITLE = (
        "Lançamentos do extrato bancário não conciliados "
        "com o sistema"
    )
    UNCONCILED_SYSTEM_TITLE = (
        "Lançamentos do sistema não conciliados com o banco"
    )

    def __init__(
        self, contract: Contract, start_date: datetime, end_date: datetime
    ):
        """Initialize the exporter.

        Args:
            contract: The contract to generate the report for
            start_date: Start date for the report period
            end_date: End date for the report period
        """
        super().__init__()
        self.contract = contract
        self.start_date = start_date - timedelta(days=365)
        self.end_date = end_date
        self.default_cell_height = 5

    def _database_queries(self) -> None:
        """Execute database queries to gather required data."""
        self.checking_account = self.contract.checking_account
        self.investing_account = self.contract.investing_account

        self.statement_queryset = (
            BankStatement.objects.filter(
                Q(bank_account=self.checking_account)
                | Q(bank_account=self.investing_account)
            )
            .filter(
                Q(
                    reference_month__gte=self.start_date.month,
                    reference_year__gte=self.start_date.year,
                )
                | Q(
                    reference_month__lt=self.start_date.month,
                    reference_year__gt=self.start_date.year,
                )
            )
            .order_by("reference_year", "reference_month")
            .exclude(bank_account__isnull=True)
        )

        self.revenue_queryset = Revenue.objects.filter(
            Q(bank_account=self.checking_account)
            | Q(bank_account=self.investing_account)
        ).exclude(bank_account__isnull=True)

    def handle(self) -> Any:
        """Generate the PDF report.

        Returns:
            The generated PDF document
        """
        self._database_queries()
        self._draw_header()
        self._draw_contract_data()
        self._draw_first_table_title()
        self._draw_balance_table()
        self._draw_rescue_advise()
        self._draw_revenue_group_table()
        self._draw_expenses_table()
        self._draw_bank_transfers_table()
        self._draw_final_balance_table()
        self._draw_second_table_title()
        self._draw_reimbursement_interest_table()
        self._draw_public_pass_on_table()
        self._draw_expenses_analysis_table()
        self._draw_release_table()

        return self.pdf

    def _draw_header(self) -> None:
        """Draw the report header."""
        self.set_font("Helvetica", "B", 12)
        self.draw_cell(
            text=self.TITLE,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_contract_data(self) -> None:
        """Draw contract information section."""
        contract_data = [
            ["", "", f"**   Projeto:** {self.contract.name}"],
            [
                "",
                "",
                (
                    f"**   Período Consciliado:** "
                    f"{format_into_brazilian_date(self.start_date)} a "
                    f"{format_into_brazilian_date(self.start_date)}"
                ),
            ],
            [
                "",
                "",
                f"**   Banco:** {self.checking_account.bank_name}",
            ],
            [
                "",
                "",
                f"**   Conta:** {self.checking_account.account}",
            ],
            [
                "",
                "",
                f"**   Agência:** {self.checking_account.agency}",
            ],
        ]

        self.__set_helvetica_font(font_size=9, bold=False)
        col_widths = [1, 2, 187]
        font = FontFace("Helvetica", "", size_pt=9)
        with self.pdf.table(
            headings_style=font,
            line_height=5,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            for item in contract_data:
                data = table.row()
                for idx, text in enumerate(item):
                    if idx == 1:
                        self.set_fill_color(gray=True)
                    else:
                        self.set_fill_color(gray=False)

                    data.cell(text=text, align="L", border=0)

        self.ln(8)

    def _draw_first_table_title(self) -> None:
        """Draw the first table title."""
        self.set_font("Helvetica", "B", 11)
        self.draw_cell(
            text=self.SUBTITLE,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_balance_table(self) -> None:
        """Draw the balance table."""
        self.opening_balance = (
            self.statement_queryset.filter(
                reference_month=self.start_date.month,
                reference_year=self.start_date.year,
            )
            .aggregate(Sum("opening_balance"))["opening_balance__sum"]
            or Decimal("0.00")
        )

        self.closing_checking_account = (
            self.statement_queryset.filter(
                reference_month=self.end_date.month,
                reference_year=self.end_date.year,
                bank_account=self.checking_account,
            )
            .aggregate(Sum("closing_balance"))["closing_balance__sum"]
            or Decimal("0.00")
        )

        self.closing_investing_account = (
            self.statement_queryset.filter(
                reference_month=self.end_date.month,
                reference_year=self.end_date.year,
                bank_account=self.investing_account,
            )
            .aggregate(Sum("closing_balance"))["closing_balance__sum"]
            or Decimal("0.00")
        )

        self.closing_balance = (
            self.closing_checking_account + self.closing_investing_account
        )

        body_data = [
            [
                f"{self.checking_account.account_type_label}",
                "(+)" if self.closing_checking_account >= 0 else "(-)",
                format_into_brazilian_currency(self.closing_checking_account),
            ],
            [
                (
                    self.investing_account.account_type_label
                    if self.investing_account
                    else "Conta Investimento"
                ),
                "(+)" if self.closing_investing_account >= 0 else "(-)",
                format_into_brazilian_currency(self.closing_investing_account),
            ],
        ]

        footer_data = [
            "**Total dos Saldos Anteriores**",
            "",
            f"**{format_into_brazilian_currency(self.closing_balance)}**",
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.BALANCE_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 8)
        col_widths = [90, 70, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=5,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.set_fill_color(gray=True)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

        self.ln(1)

    def _draw_rescue_advise(self) -> None:
        """Draw the rescue advise section."""
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.RESCUE_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)
        self.ln(1)

    def _draw_revenue_group_table(self) -> None:
        """Draw the revenue group table."""
        self.revenue_queryset = (
            Revenue.objects.filter(
                Q(bank_account=self.checking_account)
                | Q(bank_account=self.investing_account)
            )
            .filter(
                receive_date__gte=self.start_date,
                receive_date__lte=self.end_date,
            )
            .exclude(bank_account__isnull=True)
        )

        body_data = []
        total = Decimal("0.00")

        for revenue in self.revenue_queryset:
            body_data.append(
                [
                    revenue.revenue_nature_label,
                    "(+)",
                    format_into_brazilian_currency(revenue.value),
                ]
            )

            total += revenue.value

        self.total_revenues = total

        footer_data = [
            "**Total das Receitas**",
            "",
            f"**{format_into_brazilian_currency(total)}**",
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.REVENUE_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 8)
        col_widths = [90, 70, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=5,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.set_fill_color(gray=True)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

        self.ln(1)

    def _draw_expenses_table(self) -> None:
        """Draw the expenses table."""
        self.all_expense = Expense.objects.filter(
            liquidation__gte=self.start_date,
            liquidation__lte=self.end_date
        )

        self.planned_expenses = self.all_expense.filter(planned=True)
        self.unplanned_expenses = self.all_expense.filter(planned=False)
        if self.planned_expenses.count():
            planned = (
                self.planned_expenses.aggregate(Sum("value"))["value__sum"]
            )
        else:
            planned = Decimal("0.00")

        if self.unplanned_expenses.count():
            unplanned = (
                self.unplanned_expenses.aggregate(Sum("value"))["value__sum"]
            )
        else:
            unplanned = Decimal("0.00")

        total = planned + unplanned

        self.total_expenses = total

        body_data = [
            [
                (
                    "Despesas Planejadas - "
                    "Previstas no Plano de Trabalho \n "
                ),
                "(-)",
                format_into_brazilian_currency(planned),
            ],
            [
                (
                    "Despesas Não Planejadas "
                    "Desconsiderando despesas com investimento "
                    "(IOF, IR, etc) \n "
                ),
                "(-)",
                format_into_brazilian_currency(unplanned),
            ],
        ]

        footer_data = [
            "**Total das Despesas**",
            "",
            f"**{format_into_brazilian_currency(total)}**",
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.EXPENSES_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 8)
        col_widths = [90, 70, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=self.default_cell_height,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

        self.set_font("Helvetica", "", 8)
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=5,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            footer = table.row()
            self.set_fill_color(gray=True)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

        self.ln(1)

    def _draw_bank_transfers_table(self) -> None:
        """Draw the bank transfers table."""
        self.transaction_queryset = (
            Transaction.objects.filter(
                Q(bank_account=self.checking_account)
                | Q(bank_account=self.investing_account)
            )
            .filter(date__gte=self.start_date, date__lte=self.end_date)
            .exclude(bank_account__isnull=True)
        )

        income_transaction = self.transaction_queryset.filter(
            amount__gt=Decimal("0.00")
        )
        outgoing_transaction = self.transaction_queryset.filter(
            amount__lt=Decimal("0.00")
        )

        if income_transaction.count():
            income = income_transaction.aggregate(Sum("amount"))["amount__sum"]
        else:
            income = Decimal("0.00")

        if outgoing_transaction.count():
            outgoing = outgoing_transaction.aggregate(Sum("amount"))[
                "amount__sum"
            ]
        else:
            outgoing = Decimal("0.00")

        body_data = [
            [
                "Entradas",
                "(+)",
                f"{format_into_brazilian_currency(income)}",
            ],
            [
                "Saídas" if self.investing_account else "Saídas",
                "(-)",
                f"{format_into_brazilian_currency(outgoing)}",
            ],
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.TRANSFERS_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 8)
        col_widths = [90, 70, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=5,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text="",
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)
        self.ln(1)

    def _draw_final_balance_table(self) -> None:
        """Draw the final balance table."""
        checking_amount = self.closing_checking_account
        if self.closing_investing_account:
            investing_amount = self.closing_investing_account
        else:
            investing_amount = Decimal("0.00")

        positive_checking = checking_amount >= 0
        positive_investing = investing_amount >= 0

        total = checking_amount + investing_amount

        calculated_value = (
            self.opening_balance + self.total_revenues + self.total_expenses
        )

        body_data = [
            [
                f"{self.checking_account.account_type_label}",
                "(+)" if positive_checking else "(-)",
                format_into_brazilian_currency(checking_amount),
            ],
            [
                (
                    self.investing_account.account_type_label
                    if self.investing_account
                    else "Conta Investimento"
                ),
                "(+)" if positive_investing else "(-)",
                format_into_brazilian_currency(investing_amount),
            ],
        ]

        footer_data = [
            [
                "**Total dos Saldos Disponíveis (Banco)**",
                "",
                f"**{format_into_brazilian_currency(total)}**",
            ],
            [
                (
                    "**Saldo Final Calculado\n"
                    "Este saldo deverá ser igual ao Total dos "
                    "Saldos Disponíveis (Banco)**"
                ),
                "",
                f"**{format_into_brazilian_currency(calculated_value)}**",
            ],
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.FINAL_BALANCE_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 8)
        col_widths = [90, 70, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=5,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            self.set_fill_color(gray=True)
            for item in footer_data:
                footer = table.row()
                for text in item:
                    footer.cell(text=text, align="C", border=0)

        self.ln(self.default_cell_height)

    def _draw_second_table_title(self) -> None:
        """Draw the second table title."""
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.ANALYTICAL_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            fill=True,
        )

    def _draw_reimbursement_interest_table(self) -> None:
        """Draw the reimbursement interest table."""
        reimbursement_interest_queryset = self.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.REIMBURSEMENT_INTEREST
        )
        total_reimbursement = Decimal("0.00")
        body_data = [
            [
                "**Data**",
                "**Histórico**",
                "**Valor**",
            ]
        ]

        for reimbursement in reimbursement_interest_queryset:
            body_data.append(
                [
                    format_into_brazilian_date(reimbursement.receive_date),
                    str(
                        reimbursement.bank_account.revenue.revenue_nature_label
                    ),
                    format_into_brazilian_currency(reimbursement.value),
                ]
            )
            total_reimbursement += reimbursement.value

        footer_data = [
            "",
            "",
            f"**{format_into_brazilian_currency(total_reimbursement)}**",
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.REIMBURSEMENT_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 7)
        col_widths = [80, 80, 30]
        font = FontFace("Helvetica", "", size_pt=7)
        with self.pdf.table(
            headings_style=font,
            line_height=self.default_cell_height,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.set_fill_color(gray=True)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

    def _draw_public_pass_on_table(self) -> None:
        """Draw the public pass on table."""
        public_transfer_queryset = self.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.PUBLIC_TRANSFER
        )
        total_public_transfer = Decimal("0.00")
        body_data = []

        body_data.append(
            [
                "**Data**",
                "**Histórico**",
                "**Valor**",
            ]
        )

        for public_transfer in public_transfer_queryset:
            body_data.append(
                [
                    format_into_brazilian_date(public_transfer.receive_date),
                    str(public_transfer.history),
                    format_into_brazilian_currency(public_transfer.value),
                ]
            )

            total_public_transfer += public_transfer.value

        footer_data = [
            "",
            "",
            f"**{format_into_brazilian_currency(total_public_transfer)}**",
        ]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.PUBLIC_TRANSFER_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 8)
        col_widths = [80, 80, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=self.default_cell_height,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            self.set_font("Helvetica", "", 7)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.set_fill_color(gray=True)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

    def _draw_expenses_analysis_table(self) -> None:
        """Draw the expenses analysis table."""
        if self.planned_expenses.count():
            total_planned = (
                self.planned_expenses.aggregate(Sum("value"))["value__sum"]
            )
        else:
            total_planned = Decimal("0.00")

        if self.unplanned_expenses.count():
            total_unplanned = (
                self.unplanned_expenses.aggregate(Sum("value"))["value__sum"]
            )
        else:
            total_unplanned = Decimal("0.00")

        total_expenses = total_planned + total_unplanned

        planned_data = [
            [
                "**Data**",
                "**Histórico**",
                "**Valor**",
            ],
        ]

        unplanned_data = [
            [
                "**Data**",
                "**Histórico**",
                "**Valor**",
            ],
        ]

        for planned in self.planned_expenses:
            planned_data.append(
                [
                    format_into_brazilian_date(planned.liquidation),
                    str(planned.history),
                    format_into_brazilian_currency(planned.value),
                ]
            )

        planned_footer_data = [
            "**Despesas Planejadas**",
            "",
            f"**{format_into_brazilian_currency(total_planned)}**",
        ]

        for unplanned in self.unplanned_expenses:
            planned_data.append(
                [
                    format_into_brazilian_date(unplanned.liquidation),
                    str(unplanned.history),
                    format_into_brazilian_currency(unplanned.value),
                ]
            )

        unplanned_footer_data = [
            (
                "**Despesas Não Planejadas**\n"
                "__Desconsiderando despesas com investimento "
                "(IOF, IR, etc)__"
            ),
            "",
            f"**{format_into_brazilian_currency(total_unplanned)}**",
        ]

        total_data = ["\nTotal Das Despesas", "", f"\n{total_expenses}"]

        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.EXPENSES_ANALYSIS_TITLE,
            w=190,
            h=self.default_cell_height,
            align="C",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        # Despesas Planejadas
        self.set_font("Helvetica", "", 8)
        col_widths = [80, 80, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=self.default_cell_height,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            self.set_font("Helvetica", "", 7)
            for item in planned_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.set_fill_color(gray=True)
            for text in planned_footer_data:
                footer.cell(text=text, align="C", border=0)

        # Despesas não Planejadas
        self.set_font("Helvetica", "", 8)
        col_widths = [80, 80, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=self.default_cell_height,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            self.set_font("Helvetica", "", 7)

            for item in unplanned_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.set_fill_color(gray=True)
            for text in unplanned_footer_data:
                footer.cell(text=text, align="C", border=0)

        # Total das Despesas
        self.set_font("Helvetica", "B", 8)
        col_widths = [80, 80, 30]
        font = FontFace("Helvetica", "B", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=self.default_cell_height,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            total = table.row()
            self.set_fill_color(gray=True)
            for text in total_data:
                total.cell(text=text, align="C", border=0)

        self.ln(self.default_cell_height)

    def _draw_release_table(self) -> None:
        """Draw the release table."""
        not_in_sistem_data = [
            [
                "**Data**",
                "**Histórico**",
                "**Valor**",
            ],
            [
                "22/22/22",
                "ZZZ Contabilidade",
                "R$XX.XXX,XX",
            ],
        ]

        not_in_bank_data = [
            [
                "**Data**",
                "**Histórico**",
                "**Valor**",
            ],
            [
                "22/22/22",
                "ZZZ Contabilidade",
                "R$XX.XXX,XX",
            ],
        ]

        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.UNCONCILED_BANK_TITLE,
            w=190,
            h=self.default_cell_height,
            align="L",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 8)
        col_widths = [80, 80, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=self.default_cell_height,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            self.set_font("Helvetica", "", 7)
            for item in not_in_sistem_data:
                unconcilied = table.row()
                for text in item:
                    unconcilied.cell(text=text, align="C", border=0)

        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(gray=True)
        self.draw_cell(
            text=self.UNCONCILED_SYSTEM_TITLE,
            w=190,
            h=self.default_cell_height,
            align="L",
            fill=True,
            border=0,
        )

        self.ln(self.default_cell_height)

        self.set_font("Helvetica", "", 8)
        col_widths = [80, 80, 30]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=self.default_cell_height,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=False)
            self.set_font("Helvetica", "", 7)
            for item in not_in_bank_data:
                unconcilied = table.row()
                for text in item:
                    unconcilied.cell(text=text, align="C", border=0)
