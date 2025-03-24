from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from fpdf.fonts import FontFace
from contracts.models import Contract
from reports.exporters.commons.pdf_exporter import CommonPDFExporter
from utils.choices import MonthChoices
from utils.formats import (
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class PassOn1PDFExporter(CommonPDFExporter):
    """Exporter for Pass On 1 PDF report."""

    def __init__(self, contract: Contract, start_date: date, end_date: date):
        super().__init__()
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date
        self.initialize_pdf()

    def __database_queries(self) -> None:
        """
        Performs database queries to get contract data.
        Optimized to use select_related and prefetch_related where needed.
        """
        self.contracts_queryset = (
            Contract.objects
            .select_related('area', 'area__city_hall', 'checking_account')
            .filter(
                area__city_hall=self.contract.area.city_hall,
                checking_account__isnull=False,
            )
            .order_by("start_of_vigency")
        )
        
        self.all_values_in_contracts = (
            self.contracts_queryset
            .aggregate(total=Sum("total_value"))
            .get("total") or Decimal("0.00")
        )

    def handle(self):
        """Main method to generate the PDF report."""
        self.__database_queries()
        self._draw_header()
        self._draw_up_informations()
        self._draw_table()
        self._draw_down_informations()
        self._draw_observations()
        return self.pdf

    def _draw_header(self) -> None:
        """Draws the header section of the PDF."""
        self.set_font(font_size=9, bold=True)
        self.draw_multi_cell(
            text=(
                "ANEXO RP-01 REPASSES A ÓRGÃOS PÚBLICOS \n "
                "RELAÇÃO DOS VALORES TRANSFERIDOS DE \n "
                "CORRENTES DE CONVÊNIO OU CARACTERIZADOS COMO "
                "AUXÍLIOS, SUBVENÇÕES OU \n CONTRIBUIÇÕES"
            ),
            height=4,
            align="C",
        )
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_up_informations(self) -> None:
        """Draws the upper information section of the PDF."""
        self.set_font(font_size=8, bold=False)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.draw_cell(
            text=(
                f"**EXERCÍCIO:** {start.day}/{start.month}/{start.year} a "
                f"{end.day}/{end.month}/{end.year}"
            ),
            height=7,
            markdown=True,
        )
        self.draw_cell(
            text=(
                f"**ÓRGÃO CONCESSOR:** "
                f"{self.contract.organization.city_hall.name}"
            ),
            markdown=True,
        )

    # Table constants
    TABLE_UP_HEADER = ["", "LEI", "CONVÊNIO", ""]
    TABLE_HEADER = [
        "TIPO (*)",
        "BENEFICIARIO / CNPJ",
        "ENDEREÇO (Rua, n°, cidade, CEP)",
        "N°",
        "DATA",
        "N°",
        "DATA",
        "FINALIDADE",
        "DATA DO PGTO",
        "FONTE (**)",
        "VALOR EM REAIS",
    ]
    
    # Column widths
    SUB_COL_WIDTHS = [61, 29, 29, 73]  # Total: 190
    # Main columns: TIPO, BENEFICIARIO, ENDEREÇO, N°, DATA, N°, DATA, FINALIDADE,
    # DATA PGTO, FONTE, VALOR
    MAIN_COL_WIDTHS = [15, 20, 26, 14, 15, 14, 15, 19, 17, 17, 20]
    FOOTER_COL_WIDTHS = [154, 36]  # Total: 190

    def _draw_table(self) -> None:
        """Draws the main data table with headers, body and footer."""
        self._draw_table_up_header()
        self._draw_table_main()
        self._draw_table_footer()

    def _draw_table_up_header(self) -> None:
        """Draws the upper header of the table."""
        font = FontFace("FreeSans", "", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=self.SUB_COL_WIDTHS,
            repeat_headings=0,
        ) as table:
            up_header = table.row()
            for text in self.TABLE_UP_HEADER:
                up_header.cell(text=text, align="C")


    def _draw_table_main(self) -> None:
        """Draws the main part of the table with headers and data."""
        # Draw header
        font = FontFace("FreeSans", "", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=self.MAIN_COL_WIDTHS,
            repeat_headings=0,
        ) as table:
            header = table.row()
            for text in self.TABLE_HEADER:
                header.cell(text=text, align="C")


        # Draw body if there's data
        if self.contracts_queryset.exists():
            self.set_font(font_size=6)
            body_data = []
            for contract in self.contracts_queryset:
                hired_company = contract.hired_company
                date_law = contract.law_date
                date_agreement = contract.agreement_date
                
                row_data = [
                    f"{contract.get_concession_type_display()}",
                    f"{contract.organization.name}",
                    f"{hired_company.city}/{hired_company.uf} | "
                    f"{hired_company.street}, nº {hired_company.number} - "
                    f"{hired_company.district}",
                    f"Lei nº {contract.law_num}",
                    f"De {date_law.day} de "
                    f"{MonthChoices(date_law.month).label.capitalize()} de "
                    f"{date_law.year}",
                    f"{contract.agreement_num}/{date_agreement.year}",
                    f"{format_into_brazilian_date(contract.agreement_date)}",
                    f"{contract.objective}",
                    f"{contract.end_of_vigency}",
                    f"{contract.checking_account.origin}",
                    f"{format_into_brazilian_currency(contract.total_value)}",
                ]
                body_data.append(row_data)
            
            font = FontFace("FreeSans", "", size_pt=6)
            with self.pdf.table(
                headings_style=font,
                line_height=4,
                align="L",
                col_widths=self.MAIN_COL_WIDTHS,
                repeat_headings=0,
            ) as table:
                for row_data in body_data:
                    row = table.row()
                    for text in row_data:
                        row.cell(text=text, align="L")

    def _draw_table_footer(self) -> None:
        """Draws the footer of the table with totals."""
        footer_data = [
            [
                "Total:",
                format_into_brazilian_currency(self.all_values_in_contracts),
            ]
        ]
        font = FontFace("FreeSans", "", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=self.FOOTER_COL_WIDTHS,
            repeat_headings=0,
        ) as table:
            footer = table.row()
            for text in footer_data:
                footer.cell(text=text, align="C")

        self.ln(10)

    def _draw_down_informations(self) -> None:
        """Draws the lower information section of the PDF."""
        self.set_font(font_size=8, bold=True)
        contractor_company = self.contract.contractor_company
        self.draw_cell(
            text=(
                f"LOCAL: {contractor_company.city}/{contractor_company.uf} | "
                f"{contractor_company.street}, nº {contractor_company.number} - "
                f"{contractor_company.district}"
            ),
            markdown=True,
        )
        self.ln()
        today = date.today()
        self.draw_cell(
            text=f"DATA: {format_into_brazilian_date(today)}",
            markdown=True,
        )
        self.ln(20)
        self.draw_multi_cell(
            text="**RESPONSÁVEL: NOME, CARGO E ASSINATURA**",
            markdown=True,
        )
        self.ln(8)
        self.draw_cell(text="", width=190, height=10, align="C")
        self.draw_line(
            self.pdf.get_x(),
            self.pdf.get_y(),
            self.pdf.get_x() + 190,
            self.pdf.get_y(),
        )
        self.ln(10)

    def _draw_observations(self) -> None:
        """Draws the observations section of the PDF."""
        self.set_font(font_size=7)
        self.draw_cell(text="(*) Auxílio, subvenção ou contribuição.")
        self.ln(5)
        self.draw_cell(text="(**) Fonte de recursos: federal ou estadual.")
