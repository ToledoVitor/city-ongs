from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from django.db.models import Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Revenue
from contracts.models import Contract
from reports.exporters.commons.pdf_exporter import CommonPDFExporter
from utils.choices import MonthChoices
from utils.formats import format_into_brazilian_currency, get_month_range


@dataclass
class PredictedVersusRealizedPDFExporter(CommonPDFExporter):
    """PDF exporter for predicted versus realized revenue reports."""

    # Constants for text
    TITLE = (
        "DEMONSTRATIVO DE REPASSES PREVISTO X REALIZADO"
    )
    RESOURCE_SOURCE = "Consolidado de todas as fontes"
    TABLE_HEADERS = ["**PERÍODO**", "**PREVISTO**", "**REALIZADO**"]
    TABLE_FOOTER = "**TOTAL**"

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

    def handle(self) -> Any:
        """Generate the PDF report.

        Returns:
            The generated PDF document
        """
        self._draw_header()
        self._draw_contract_data()
        self._draw_table()

        return self.pdf

    def _draw_header(self) -> None:
        """Draw the report header."""
        self.set_font("Helvetica", "B", 11)
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
            ["", "", f"**   Fonte Recurso:** {self.RESOURCE_SOURCE}"],
            [
                "",
                "",
                (
                    f"**   Período:** "
                    f"{MonthChoices(self.start_date.month).label.capitalize()} "
                    f"de {self.start_date.year} a "
                    f"{MonthChoices(self.end_date.month).label.capitalize()} "
                    f"de {self.end_date.year}"
                ),
            ],
        ]

        self.set_font("Helvetica", "", 9)
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
                        self.pdf.set_fill_color(225, 225, 225)
                    else:
                        self.pdf.set_fill_color(255, 255, 255)

                    data.cell(text=text, align="L", border=0)

        self.pdf.ln(8)

    def _draw_table(self) -> None:
        """Draw the main data table."""
        months_range = get_month_range(self.start_date, self.end_date)
        all_revenue = Revenue.objects.filter(
            accountability_id__in=self.contract.accountabilities.values_list(
                "id", flat=True
            )
        ).filter(receive_date__gte=self.start_date, receive_date__lte=self.end_date)
        month_income_value = self.contract.month_income_value

        body_data = []
        total_predicted = month_income_value * len(months_range)
        total_realized = all_revenue.aggregate(Sum("value"))["value__sum"]

        for month, year in months_range:
            revenue = all_revenue.filter(
                receive_date__month=month, receive_date__year=year
            ).aggregate(Sum("value"))["value__sum"]

            body_data.append(
                [
                    f"{MonthChoices(month).label.capitalize()} de {year}",
                    format_into_brazilian_currency(month_income_value),
                    format_into_brazilian_currency(revenue),
                ]
            )

        footer_data = [
            self.TABLE_FOOTER,
            format_into_brazilian_currency(total_predicted),
            format_into_brazilian_currency(total_realized),
        ]

        col_widths = [90, 50, 50]
        font = FontFace("Helvetica", "", size_pt=8)
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
            for text in self.TABLE_HEADERS:
                head.cell(text=text, align="C", border=0)

            self.pdf.set_fill_color(255, 255, 255)
            self.set_font("Helvetica", "", 8)
            for item in body_data:
                body = table.row()
                for text in item:
                    body.cell(text=text, align="C", border=0)

            footer = table.row()
            self.pdf.set_fill_color(225, 225, 225)
            self.set_font("Helvetica", "", 8)
            for text in footer_data:
                footer.cell(text=text, align="C", border=0)
