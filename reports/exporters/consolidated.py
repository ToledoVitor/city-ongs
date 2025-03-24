from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense, Revenue
from bank.models import BankStatement, Transaction
from contracts.models import Contract
from reports.exporters.commons.exporters import BasePdf
from utils.formats import (
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class ConsolidatedPDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self, contract: Contract, start_date: datetime, end_date: datetime):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(233, 234, 236)
        self.pdf = pdf
        self.contract = contract
        self.start_date = start_date - timedelta(days=365)
        self.end_date = end_date

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def __database_queries(self):
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

    def handle(self):
        self.__database_queries()
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

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_helvetica_font(font_size=12, bold=True)
        self.pdf.cell(
            0,
            0,
            "CONSOLIDADO DAS CONCILIAÇÕES BANCÁRIAS",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_contract_data(self):
        contract_data = [
            ["", "", f"**   Projeto:** {self.contract.name}"],
            [
                "",
                "",
                f"**   Período Consciliado:** {format_into_brazilian_date(self.start_date)} a {format_into_brazilian_date(self.start_date)}",
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
                for id, text in enumerate(item):
                    if id == 1:
                        self.pdf.set_fill_color(225, 225, 225)
                    else:
                        self.pdf.set_fill_color(255, 255, 255)

                    data.cell(text=text, align="L", border=0)

        self.pdf.ln(8)

    def _draw_first_table_title(self):
        self.__set_helvetica_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "Extrato Bancário",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_balance_table(self):
        self.opening_balance = self.statement_queryset.filter(
            reference_month=self.start_date.month,
            reference_year=self.start_date.year,
        ).aggregate(Sum("opening_balance"))["opening_balance__sum"] or Decimal("0.00")

        self.closing_checking_account = self.statement_queryset.filter(
            reference_month=self.end_date.month,
            reference_year=self.end_date.year,
            bank_account=self.checking_account,
        ).aggregate(Sum("closing_balance"))["closing_balance__sum"] or Decimal("0.00")

        self.closing_investing_account = self.statement_queryset.filter(
            reference_month=self.end_date.month,
            reference_year=self.end_date.year,
            bank_account=self.investing_account,
        ).aggregate(Sum("closing_balance"))["closing_balance__sum"] or Decimal("0.00")

        self.closing_balance = (
            self.closing_checking_account + self.closing_investing_account
        )

        revenue_in_time = self.revenue_queryset.filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        )
        body_data = [
            [
                f"{self.checking_account.account_type_label}",
                "(+)" if self.closing_checking_account >= 0 else "(-)",
                f"{format_into_brazilian_currency(self.closing_checking_account)}",
            ],
            [
                self.investing_account.account_type_label
                if self.investing_account
                else "Conta Investimento",
                "(+)" if self.closing_investing_account >= 0 else "(-)",
                f"{format_into_brazilian_currency(self.closing_investing_account)}",
            ],
        ]

        footer_data = [
            "**Total dos Saldos Anteriores**",
            "",
            f"**{format_into_brazilian_currency(self.closing_balance)}**",
        ]

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Saldos Anteriores",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

        self.pdf.ln(1)

    def _draw_rescue_advise(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Aplicações e Resgates dos Recursos Financeiros",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)
        self.pdf.ln(1)

    def _draw_revenue_group_table(self):
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

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Agrupamento das Receitas por Natureza de Receita",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

        self.pdf.ln(1)

    def _draw_expenses_table(self):
        self.all_expense = Expense.objects.filter(
            liquidation__gte=self.start_date, liquidation__lte=self.end_date
        )

        self.planned_expenses = self.all_expense.filter(planned=True)
        self.unplanned_expenses = self.all_expense.filter(planned=False)
        if self.planned_expenses.count():
            planned = self.planned_expenses.aggregate(Sum("value"))["value__sum"]
        else:
            planned = Decimal("0.00")

        if self.unplanned_expenses.count():
            unplanned = self.unplanned_expenses.aggregate(Sum("value"))["value__sum"]
        else:
            unplanned = Decimal("0.00")

        total = planned + unplanned

        self.total_expenses = total

        body_data = [
            [
                "Despesas Planejadas - Previstas no Plano de Trabalho \n ",
                "(-)",
                format_into_brazilian_currency(planned),
            ],
            [
                "Despesas Não Planejadas Desconsiderando despesas com investimento (IOF, IR, etc) \n ",
                "(-)",
                format_into_brazilian_currency(unplanned),
            ],
        ]

        footer_data = [
            "**Total das Despesas**",
            "",
            f"**{format_into_brazilian_currency(total)}**",
        ]

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Despesas",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(225, 225, 225)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

        self.pdf.ln(1)

    def _draw_bank_transfers_table(self):
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
            outgoing = outgoing_transaction.aggregate(Sum("amount"))["amount__sum"]
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

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Transferências Bancárias para outras contas",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)
        self.pdf.ln(1)

    def _draw_final_balance_table(self):
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
                f"{format_into_brazilian_currency(checking_amount)}",
            ],
            [
                self.investing_account.account_type_label
                if self.investing_account
                else "Conta Investimento",
                "(+)" if positive_investing else "(-)",
                f"{format_into_brazilian_currency(investing_amount)}",
            ],
        ]

        footer_data = [
            [
                "**Total dos Saldos Disponíveis (Banco)**",
                "",
                f"**{format_into_brazilian_currency(total)}**",
            ],
            [
                "**Saldo Final Calculado\nEste saldo deverá ser igual ao Total dos Saldos Disponíveis (Banco)**",
                "",
                f"**{format_into_brazilian_currency(calculated_value)}**",
            ],
        ]

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Saldos Finais",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            self.pdf.set_fill_color(225, 225, 225)
            for item in footer_data:
                footer = table.row()
                for text in item:
                    footer.cell(text=text, align="C", border=0)

        self.pdf.ln(self.default_cell_height)

    def _draw_second_table_title(self):
        self.__set_helvetica_font(font_size=10, bold=True)
        self.pdf.set_fill_color(210, 210, 210)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Visão Analítica dos Lançamentos",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            fill=True,
        )

    def _draw_reimbursement_interest_table(self):
        reimbursement_interest_queryset = self.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.REIMBURSEMENT_INTEREST  # TODO não sei se tá certo
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
                    ),  # TODO, receio de criar a label
                    format_into_brazilian_currency(reimbursement.value),
                ]
            )
            total_reimbursement += reimbursement.value

        footer_data = [
            "",
            "",
            f"**{format_into_brazilian_currency(total_reimbursement)}**",
        ]

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Reembolso de Juros, multas, glosas, pagto. Indevido, duplicidade etc",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=7, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

    def _draw_public_pass_on_table(self):
        public_transfer_queryset = self.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.PUBLIC_TRANSFER  # TODO não sei se tá certo
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
                    str(public_transfer.history),  # TODO, receio de criar a label
                    format_into_brazilian_currency(public_transfer.value),
                ]
            )

            total_public_transfer += public_transfer.value

        footer_data = [
            "",
            "",
            f"**{format_into_brazilian_currency(total_public_transfer)}**",
        ]

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Repasse Público",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            self.__set_helvetica_font(font_size=7, bold=False)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)

    def _draw_expenses_analysis_table(self):
        if self.planned_expenses.count():
            total_planned = self.planned_expenses.aggregate(Sum("value"))["value__sum"]
        else:
            total_planned = Decimal("0.00")

        if self.unplanned_expenses.count():
            total_unplanned = self.unplanned_expenses.aggregate(Sum("value"))[
                "value__sum"
            ]
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
                    str(planned.history),  # TODO, receio de criar a label
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
                    str(unplanned.history),  # TODO, receio de criar a label
                    format_into_brazilian_currency(unplanned.value),
                ]
            )

        unplanned_footer_data = [
            "**Despesas Não Planejadas**\n__Desconsiderando despesas com investimento (IOF, IR, etc)__",
            "",
            f"**{format_into_brazilian_currency(total_unplanned)}**",
        ]

        total_data = ["\nTotal Das Despesas", "", f"\n{total_expenses}"]

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Despesas",
            align="C",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        # Despesas Planejadas
        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            self.__set_helvetica_font(font_size=7, bold=False)
            for item in planned_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            for text in planned_footer_data:
                footer.cell(text=text, align="C", border=0)

        # Despesas não Planejadas
        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            self.__set_helvetica_font(font_size=7, bold=False)

            for item in unplanned_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            for text in unplanned_footer_data:
                footer.cell(text=text, align="C", border=0)

        # Total das Despesas
        self.__set_helvetica_font(font_size=8, bold=True)
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
            self.pdf.set_fill_color(225, 225, 225)
            for text in total_data:
                total.cell(text=text, align="C", border=0)

        self.pdf.ln(self.default_cell_height)

    def _draw_release_table(self):
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

        self.__set_helvetica_font(font_size=9, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Lançamentos do extrato bancário não conciliados com o sistema",
            # TODO necessário interação com o Usuário
            align="L",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            self.__set_helvetica_font(font_size=7, bold=False)
            for item in not_in_sistem_data:
                unconcilied = table.row()
                for text in item:
                    unconcilied.cell(text=text, align="C", border=0)

        self.__set_helvetica_font(font_size=9, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Lançamentos do sistema não conciliados com o banco",
            # TODO necessário interação com o Usuário
            align="L",
            fill=True,
            border=0,
        )

        self.pdf.ln(self.default_cell_height)

        self.__set_helvetica_font(font_size=8, bold=False)
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
            self.pdf.set_fill_color(255, 255, 255)
            self.__set_helvetica_font(font_size=7, bold=False)
            for item in not_in_bank_data:
                unconcilied = table.row()
                for text in item:
                    unconcilied.cell(text=text, align="C", border=0)
