from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Optional

from django.db.models import Q
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Revenue
from contracts.models import Contract
from reports.exporters.commons.pdf_exporter import BasePdf, CommonPDFExporter
from utils.formats import (
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class PassOn4PDFExporter(CommonPDFExporter):
    """Exporter for Pass On 4 PDF report."""

    pdf: Optional[BasePdf] = None
    default_cell_height: int = 5

    def __init__(
        self,
        contract: Contract,
        start_date: Any,
        end_date: Any,
    ):
        super().__init__()
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date
        self.initialize_pdf()

        self.checking_account = self.contract.checking_account
        self.investing_account = self.contract.investing_account

        self.revenue_queryset = Revenue.objects.filter(
            Q(bank_account=self.checking_account)
            | Q(bank_account=self.investing_account)
        ).exclude(bank_account__isnull=True)

    def handle(self) -> BasePdf:
        """Generate the PDF report.

        Returns:
            The generated PDF document
        """
        self._draw_header()
        self._draw_informations()
        self._draw_manager_table()
        self._draw_partner_table()
        self._draw_collaborator_table()
        self._draw_promotion_table()
        self._draw_agreement_table()
        self._draw_concession_table()

        return self.pdf

    def _draw_header(self) -> None:
        """Draw the header section of the PDF."""
        self.set_font(font_size=10, bold=True)
        self.pdf.cell(
            0,
            0,
            "ANEXO RP-04 - REPASSES AO TERCEIRO SETOR",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            0,
            10,
            "RELAÇÃO DOS VALORES TRANSFERIDOS",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self) -> None:
        """Draw the information section with contract details."""
        self.set_font(font_size=8, bold=False)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.pdf.cell(
            text=(
                f"**VALORES REPASSADOS DURANTE O EXERCÍCIO DE:** "
                f"{format_into_brazilian_date(start)} a "
                f"{format_into_brazilian_date(end)}"
            ),
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**ÓRGÃO CONCESSOR:** {self.contract.organization.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(10)
        self.pdf.cell(
            text="**I - DECORRENTES DE AJUSTES:**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(12)

    def _draw_table(
        self,
        header_data: List[str],
        table_data: List[List[str]],
        footer_data: List[str],
        title: Optional[str] = None,
    ) -> None:
        """Draw a table with header, data and footer.

        Args:
            header_data: List of header texts
            table_data: List of data rows
            footer_data: List of footer texts
            title: Optional title for the table
        """
        if title:
            self.set_font(font_size=7, bold=True)
            self.pdf.ln()
            self.pdf.cell(
                text=title,
                markdown=True,
                h=self.default_cell_height,
            )
            self.pdf.ln(2)

        font = FontFace("FreeSans", "", size_pt=7)
        data_col_widths = [15, 20, 10, 15, 15, 15, 20, 30, 20, 20]

        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            markdown=True,
            col_widths=data_col_widths,
            repeat_headings=0,
        ) as table:
            self.set_fill_color(gray=True)
            header = table.row()
            for text in header_data:
                header.cell(text=text, align="C")

            self.set_font(self.default_cell_height)
            for item in table_data:
                self.set_fill_color(gray=False)
                data = table.row()
                for text in item:
                    data.cell(text=text, align="C")

        footer_col_widths = [178, 22]
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="L",
            col_widths=footer_col_widths,
            markdown=True,
        ) as table:
            self.set_fill_color(gray=True)
            footer = table.row()
            for text in footer_data:
                footer.cell(text=text, align="R")

        self.pdf.ln(10)

    def _prepare_table_data(
        self,
        revenue_queryset: Any,
        contract: Contract,
        hired_company: Any,
        concession_type: str,
    ) -> tuple[List[List[str]], Decimal]:
        """Prepare table data from revenue queryset.

        Args:
            revenue_queryset: QuerySet of revenue objects
            contract: The contract object
            hired_company: The hired company object
            concession_type: Type of concession

        Returns:
            Tuple containing table data and total revenue value
        """
        table_data = []
        total_revenue_value = Decimal("0.00")
        
        for revenue in revenue_queryset:
            address = (
                f"{hired_company.city}/{hired_company.uf} | "
                f"{hired_company.street}, nº {hired_company.number} - "
                f"{hired_company.district}"
            )
            table_data.append(
                [
                    f"{contract.code}",
                    f"{contract.organization.name}",
                    f"{hired_company.cnpj}",
                    address,
                    f"{revenue.receive_date}",
                    f"{contract.end_of_vigency}",
                    "Valor Global do Ajuste - Valor do adendo",
                    f"{contract.objective}",
                    f"{revenue.source}",
                    f"{format_into_brazilian_currency(revenue.value)}",
                ]
            )
            total_revenue_value += revenue.value

        return table_data, total_revenue_value

    def _draw_manager_table(self) -> None:
        """Draw the manager table section."""
        manager_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date,
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.MANAGEMENT
        )

        header_data = [
            "**Contrato de Gestão Nº**",
            "**Beneficiário**",
            "**CNPJ**",
            "**Endereço**",
            "**Data**",
            "**Vigência até**",
            "**Valor Global do Ajuste**",
            "**Objeto**",
            "**Fonte:**",
            "**Valor Repassado no Exercício**",
        ]

        table_data, total_revenue_value = self._prepare_table_data(
            manager_queryset,
            self.contract,
            self.contract.hired_company,
            "MANAGEMENT",
        )

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

        self._draw_table(header_data, table_data, footer_data)

    def _draw_partner_table(self) -> None:
        """Draw the partner table section."""
        partner_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date,
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.PARTNERSHIP
        )

        header_data = [
            "**Termo de Parceria Nº**",
            "**Beneficiário**",
            "**CNPJ**",
            "**Endereço**",
            "**Data**",
            "**Vigência até**",
            "**Valor Global do Ajuste**",
            "**Objeto**",
            "**Fonte**",
            "**Valor Repassado no Exercício**",
        ]

        table_data, total_revenue_value = self._prepare_table_data(
            partner_queryset,
            self.contract,
            self.contract.hired_company,
            "PARTNERSHIP",
        )

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

        self._draw_table(header_data, table_data, footer_data)

    def _draw_collaborator_table(self) -> None:
        """Draw the collaborator table section."""
        collaborator_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date,
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.COLLABORATION
        )

        header_data = [
            "**Termo de Colaboração Nº**",
            "**Beneficiário**",
            "**CNPJ**",
            "**Endereço**",
            "**Data**",
            "**Vigência até**",
            "**Valor Global do Ajuste**",
            "**Objeto**",
            "**Fonte**",
            "**Valor Repassado no Exercício**",
        ]

        table_data, total_revenue_value = self._prepare_table_data(
            collaborator_queryset,
            self.contract,
            self.contract.hired_company,
            "COLLABORATION",
        )

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

        self._draw_table(header_data, table_data, footer_data)

    def _draw_promotion_table(self) -> None:
        """Draw the promotion table section."""
        promotion_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date,
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.DEVELOPMENTO
        )

        header_data = [
            "**Contrato de Fomento Nº**",
            "**Beneficiário**",
            "**CNPJ**",
            "**Endereço**",
            "**Data**",
            "**Vigência até**",
            "**Valor Global do Ajuste**",
            "**Objeto**",
            "**Fonte**",
            "**Valor Repassado no Exercício**",
        ]

        table_data, total_revenue_value = self._prepare_table_data(
            promotion_queryset,
            self.contract,
            self.contract.hired_company,
            "DEVELOPMENTO",
        )

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

        self._draw_table(header_data, table_data, footer_data)

    def _draw_agreement_table(self) -> None:
        """Draw the agreement table section."""
        agreement_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date,
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.AGREEMENT
        )

        header_data = [
            "**Convênio Nº**",
            "**Beneficiário**",
            "**CNPJ**",
            "**Endereço**",
            "**Data**",
            "**Vigência até**",
            "**Valor Global do Ajuste**",
            "**Objeto**",
            "**Fonte**",
            "**Valor Repassado no Exercício**",
        ]

        table_data, total_revenue_value = self._prepare_table_data(
            agreement_queryset,
            self.contract,
            self.contract.hired_company,
            "AGREEMENT",
        )

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

        self._draw_table(header_data, table_data, footer_data)

    def _draw_concession_table(self) -> None:
        """Draw the concession table section."""
        concession_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date,
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.GRANT
        )

        self.set_font(font_size=8, bold=True)
        self.pdf.cell(
            text="II - AUXÍLIOS, SUBVENÇÕES E/OU CONTRIBUIÇÕES PAGOS:",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(2)

        header_data = [
            "**Tipo da Concessão**",
            "**Beneficiário**",
            "**CNPJ**",
            "**Endereço**",
            "**Data**",
            "**Vigência até**",
            "**Valor Global do Ajuste**",
            "**Objeto**",
            "**Fonte**",
            "**Valor Repassado no Exercício**",
        ]

        table_data, total_revenue_value = self._prepare_table_data(
            concession_queryset,
            self.contract,
            self.contract.hired_company,
            "GRANT",
        )

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

        self._draw_table(header_data, table_data, footer_data)
