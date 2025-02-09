import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense, Revenue
from contracts.choices import NatureCategories
from reports.exporters.commons.exporters import BasePdf
from utils.choices import MonthChoices
from utils.formats import (
    format_into_brazilian_currency,
    format_into_brazilian_date,
    get_month_range,
)


@dataclass
class ConsolidatedPDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self, accountability, start_date, end_date):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(233, 234, 236)
        self.pdf = pdf
        self.accountability = accountability
        self.start_date = start_date - timedelta(days=365)
        self.end_date = end_date

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def handle(self):
        self._draw_header()
        self._draw_contract_data()
        self._draw_first_table_title()
        self._draw_balance_table()

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
            ["", "", f"**   Projeto:** {self.accountability.contract.name}"],
            [
                "",
                "",
                f"**   Período Consciliado:** {format_into_brazilian_date(self.start_date)} a {format_into_brazilian_date(self.start_date)}",
            ],
            [
                "",
                "",
                f"**   Banco:** {self.accountability.contract.checking_account.bank_name}",
            ],
            [
                "",
                "",
                f"**   Conta:** {self.accountability.contract.checking_account.account}",
            ],
            [
                "",
                "",
                f"**   Agência:** {self.accountability.contract.checking_account.agency}",
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
        data = []

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.set_fill_color(225, 225, 225)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "Saldos Anteriores",
            align="L",
            fill=True,
            border=0,
        )

        # col_widths = [90, 50, 50]
        # font = FontFace("Helvetica", "", size_pt=8)
        # with self.pdf.table(
        #     headings_style=font,
        #     line_height=5,
        #     align="C",
        #     col_widths=col_widths,
        #     repeat_headings=0,
        #     markdown=True,
        # ) as table:
        #     head = table.row()
        #     self.pdf.set_fill_color(225, 225, 225)
        #     for text in head_data:
        #         head.cell(text=text, align="C", border=0)

        #     self.pdf.set_fill_color(255, 255, 255)
        #     self.__set_helvetica_font(font_size=8, bold=False)
        #     for item in body_data:
        #         body = table.row()
        #         for text in item:
        #             body.cell(text=text, align="C", border=0)

        #     footer = table.row()
        #     self.pdf.set_fill_color(225, 225, 225)
        #     self.__set_helvetica_font(font_size=8, bold=False)
        #     for text in footer_data:
        #         footer.cell(text=text, align="C", border=0)
