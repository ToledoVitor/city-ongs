import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Revenue
from contracts.models import Contract
from reports.exporters.commons.exporters import BasePdf
from utils.choices import MonthChoices
from utils.formats import format_into_brazilian_currency, get_month_range

font_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSans.ttf")
font_bold_path = os.path.join(
    settings.BASE_DIR, "static/fonts/FreeSansBold.ttf"
)


@dataclass
class PredictedVersusRealizedPDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(
        self, contract: Contract, start_date: datetime, end_date: datetime
    ):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.add_font("FreeSans", "", font_path, uni=True)
        pdf.add_font("FreeSans", "B", font_bold_path, uni=True)
        pdf.set_fill_color(233, 234, 236)
        self.pdf = pdf
        self.contract = contract
        self.start_date = start_date - timedelta(days=365)
        self.end_date = end_date

    def __set_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("FreeSans", "B", font_size)
        else:
            self.pdf.set_font("FreeSans", "", font_size)

    def handle(self):
        self._draw_header()
        self._draw_contract_data()
        self._draw_table()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "DEMONSTRATIVO DE REPASSES PREVISTO X REALIZADO",
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
                "**   Fonte Recurso:** Consolidado de todas as fontes",
            ],
            [
                "",
                "",
                f"**   Período:** {MonthChoices(self.start_date.month).label.capitalize()} de {self.start_date.year} a {MonthChoices(self.end_date.month).label.capitalize()} de {self.end_date.year}",
            ],
        ]

        self.__set_font(font_size=9, bold=False)
        col_widths = [1, 2, 187]
        font = FontFace("FreeSans", "", size_pt=9)
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

    def _draw_table(self):
        months_range = get_month_range(self.start_date, self.end_date)
        all_revenue = Revenue.objects.filter(
            accountability_id__in=self.contract.accountabilities.values_list(
                "id", flat=True
            )
        ).filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        )
        month_income_value = self.contract.month_income_value

        head_data = [
            "**PERÍODO**",
            "**PREVISTO**",
            "**REALIZADO**",
        ]
        body_data = []
        footer_data = [
            "**TOTAL**",
            format_into_brazilian_currency(
                month_income_value * len(months_range)
            ),
            format_into_brazilian_currency(
                all_revenue.aggregate(Sum("value"))["value__sum"]
            ),
        ]

        for month, year in months_range:
            revenue = all_revenue.filter(
                receive_date__month=month, receive_date__year=year
            ).aggregate(Sum("value"))["value__sum"]

            body_data.append(
                [
                    f"{MonthChoices(month).label.capitalize()} de {year}",
                    format_into_brazilian_currency(month_income_value),  # TODO
                    format_into_brazilian_currency(revenue),
                ]
            )

        col_widths = [90, 50, 50]
        font = FontFace("FreeSans", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=5,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            head = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            for text in head_data:
                head.cell(text=text, align="C", border=0)

            self.pdf.set_fill_color(255, 255, 255)
            self.__set_font(font_size=8, bold=False)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            self.__set_font(font_size=8, bold=False)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)
