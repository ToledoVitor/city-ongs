from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q, Sum

from fpdf.fonts import FontFace
from accountability.models import Expense, Revenue
from bank.models import BankStatement
from reports.exporters.commons.pdf_exporter import CommonPDFExporter
from utils.formats import (
    document_mask,
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class PassOn2PDFExporter(CommonPDFExporter):
    """Exporter for Pass On 2 PDF report."""

    def __init__(self, contract, start_date: date, end_date: date):
        super().__init__()
        self.contract = contract
        self.start_date = start_date - timedelta(days=365)
        self.end_date = end_date
        self.initialize_pdf()

    def _database_queries(self) -> None:
        """Performs database queries to get required data."""
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

        self.revenue_queryset = (
            Revenue.objects.filter(
                accountability__contract=self.contract,
                receive_date__gte=self.start_date,
                receive_date__lte=self.end_date,
            )
            .filter(
                Q(bank_account=self.checking_account)
                | Q(bank_account=self.investing_account)
            )
            .exclude(bank_account__isnull=True)
        )

        self.expense_queryset = Expense.objects.filter(
            accountability__contract=self.contract,
            liquidation__gte=self.start_date,
            liquidation__lte=self.end_date,
        )

        self.paid_expenses = self.expense_queryset.filter(paid=True)

    def handle(self):
        """Main method to generate the PDF report."""
        self._database_queries()
        self._draw_header()
        self._draw_form()
        self._draw_table_I()
        self._draw_signatories_notification()
        self._draw_table_II()
        self._draw_org_notification()
        self._draw_table_III()
        self._draw_observation()

        return self.pdf

    def _draw_header(self) -> None:
        """Draws the header section of the PDF."""
        self.set_font(font_size=9, bold=True)
        self.draw_multi_cell(
            text=(
                "ANEXO RP-02 - REPASSES A ÓRGÃOS PÚBLICOS \n "
                "DEMONSTRATIVO INTEGRAL DE RECEITAS E DESPESAS"
            ),
            height=4,
            align="C",
        )
        self.ln(10)

    def _draw_form(self) -> None:
        """Draws the form section with contract details."""
        self.set_font(font_size=8, bold=False)
        
        # Draw organization details
        self._draw_organization_details()
        
        # Draw contract details
        self._draw_contract_details()
        
        # Draw company details
        self._draw_company_details()
        
        # Draw responsible details
        self._draw_responsible_details()
        
        # Draw total value section
        self._draw_total_value_section()

    def _draw_organization_details(self) -> None:
        """Draws organization related details."""
        city_hall_name = self.contract.organization.city_hall.name
        self.draw_cell(
            text=f"**ÓRGÃO CONCESSOR:** {city_hall_name}",
            markdown=True,
            align="L",
        )
        self.draw_cell(
            text=(
                f"**TIPO DE CONCESSÃO (1):** "
                f"{self.contract.get_concession_type_display()}"
            ),
            markdown=True,
            align="L",
        )

    def _draw_contract_details(self) -> None:
        """Draws contract related details."""
        law_or_agreement = (
            str(self.contract.law_num) if self.contract.law_num
            else str(self.contract.agreement_num)
        )
        self.draw_cell(
            text=f"**LEI AUTORIZADORA OU CONVÊNIO:** {law_or_agreement}",
            markdown=True,
            align="L",
        )
        self.draw_cell(
            text=f"**OBJETO DA PARCERIA:** {self.contract.objective}",
            markdown=True,
            align="L",
        )
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.draw_cell(
            text=(
                f"**EXERCÍCIO:** {format_into_brazilian_date(start)} a "
                f"{format_into_brazilian_date(end)}"
            ),
            markdown=True,
            align="L",
        )

    def _draw_company_details(self) -> None:
        """Draws company related details."""
        self.draw_cell(
            text=f"**ÓRGÃO BENEFICIÁRIO:** {self.contract.organization.name}",
            markdown=True,
            align="L",
        )
        hired_company = self.contract.hired_company
        self.draw_cell(
            text=f"**CNPJ:** {hired_company.cnpj}",
            markdown=True,
            align="L",
        )
        self.draw_cell(
            text=(
                f"**Endereço e CEP:** {hired_company.city}/{hired_company.uf} | "
                f"{hired_company.street}, nº {hired_company.number} - "
                f"{hired_company.district}"
            ),
            markdown=True,
            align="L",
        )

    def _draw_responsible_details(self) -> None:
        """Draws responsible person details."""
        self.draw_cell(
            text="**RESPONSÁVEL(IS) PELO ÓRGÃO:**",
            markdown=True,
            align="L",
        )
        self.set_font(font_size=7, bold=False)
        
        accountability_autority = self.contract.accountability_autority
        supervision_autority = self.contract.supervision_autority
        
        table_data = [
            ["", "", " ", f"Nome: {accountability_autority.get_full_name()}"],
            ["", "", " ", f"Papel: {supervision_autority.position}"],
            ["", "", " ", f"{document_mask(str(supervision_autority.cpf))}"],
        ]

        font = FontFace("FreeSans", "", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="L",
            col_widths=[1, 2, 2, 185],  # Total: 190
            repeat_headings=0,
        ) as table:
            for row_data in table_data:
                row = table.row()
                for text in row_data:
                    row.cell(text=text, align="L")

    def _draw_total_value_section(self) -> None:
        """Draws the total value section."""
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=(
                "**VALOR TOTAL RECEBIDO NO EXERCÍCIO.** "
                "__(DEMONSTRAR POR FONTE DE RECURSO)__"
            ),
            markdown=True,
            align="L",
        )
        self.ln(2)

    def _draw_table_I(self) -> None:
        """Draws table I with financial data."""
        # Get opening balance
        opening_balance = (
            self.statement_queryset.filter(
            reference_month=self.start_date.month,
            reference_year=self.start_date.year,
            )
            .aggregate(Sum("opening_balance"))["opening_balance__sum"] 
            or Decimal("0.00")
        )

        # Get closing balances
        closing_checking = (
            self.statement_queryset.filter(
            reference_month=self.end_date.month,
            reference_year=self.end_date.year,
            bank_account=self.checking_account,
            )
            .aggregate(Sum("closing_balance"))["closing_balance__sum"] 
            or Decimal("0.00")
        )

        closing_investing = (
            self.statement_queryset.filter(
            reference_month=self.end_date.month,
            reference_year=self.end_date.year,
            bank_account=self.investing_account,
            )
            .aggregate(Sum("closing_balance"))["closing_balance__sum"] 
            or Decimal("0.00")
        )

        closing_balance = closing_checking + closing_investing

        # Get revenue data
        revenue_in_time = self.revenue_queryset.filter(
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date
        )
        self.revenue_total = Decimal("0.00")

        # Prepare table data
        contract = self.contract
        table_data = [
            ["", format_into_brazilian_currency(contract.total_value)],
            [
                "SALDO DO EXERCÍCIO ANTERIOR",
                format_into_brazilian_currency(opening_balance),
            ],
            ["REPASSADOS NO EXERCÍCIO (DATA)", ""],
            ["__(INDICAR AS FONTES DO RECURSO)__", "R$"],
        ]

        for revenue in revenue_in_time:
            table_data.append(
                [
                    revenue.revenue_nature_label,
                    format_into_brazilian_currency(revenue.value),
                ]
            )
            self.revenue_total += revenue.value

        table_data.extend([
            [
                "RECEITA COM APLICAÇÕES FINANCEIRAS DOS REPASSES PÚBLICOS",
                format_into_brazilian_currency(closing_investing),
            ],
            ["TOTAL", format_into_brazilian_currency(closing_balance)],
            [
                "RECURSOS PRÓPRIOS APLICADOS PELO BENEFICIÁRIO",
                format_into_brazilian_currency(closing_checking),
            ],
        ])

        self.set_font(font_size=7, bold=True)
        self.draw_cell(
            text="I - DEMONSTRATIVO DOS REPASSES PÚBLICOS RECEBIDOS",
            width=190,
            align="L",
            border=1,
        )

        font = FontFace("FreeSans", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=[150, 40],  # Total: 190
            repeat_headings=0,
        ) as table:
            for row_data in table_data:
                row = table.row()
                for text in row_data:
                    row.cell(text=text, align="C")

        self.ln(15)

    def _draw_signatories_notification(self) -> None:
        """Draws the signatories notification section."""
        self.set_font(font_size=8, bold=True)
        self.draw_multi_cell(
            text=(
                "O(S) SIGNATÁRIO(S), NA QUALIDADE DE REPRESENTANTE(S) DO "
                "ÓRGÃO PÚBLICO BENEFICIÁRIO VEM INDICAR, NA FORMA ABAIXO "
                "DETALHADA, A APLICAÇÃO DOS RECURSOS RECEBIDOS NO EXERCÍCIO "
                "SUPRAMENCIONADO, NA IMPORTÂNCIA TOTAL DE \n R$ ______________ "
                "(POR EXTENSO)."
            ),
            width=190,
            height=5,
            align="J",
        )
        self.ln(10)

    def _draw_table_II(self) -> None:
        """Draws table II with expense data."""
        # Prepare table data
        up_table_data = [
            [
                "DATA DO DOCUMENTO",
                "ESPECIFICAÇÃO DO DOCUMENTO FISCAL (2)",
                "CREDOR",
                "NATUREZA DA DESPESA RESUMIDAMENTE",
                "VALORES R$",
            ],
        ]

        total_expense_value = Decimal("0.00")
        for expense in self.paid_expenses:
            up_table_data.append(
                [
                    format_into_brazilian_date(expense.liquidation),
                    "Tipo do documento (Holerite, Nota Fiscal, etc...)",  # TODO
                    expense.favored.name,
                    expense.nature_label,
                    format_into_brazilian_currency(expense.value),
                ],
            )
            total_expense_value += expense.value

        down_table_data = [
            [
                "TOTAL DAS DESPESAS",
                format_into_brazilian_currency(total_expense_value),
            ],
            [
                "RECURSO DO REPASSE NÃO APLICADO",
                "O que sobrou do contrato",  # TODO
            ],
            [
                "VALOR DEVOLVIDO AO ÓRGÃO CONCESSOR",
                "Valor glosado",  # TODO
            ],
            [
                "VALOR AUTORIZADO PARA APLICAÇÃO NO EXERCÍCIO SEGUINTE",
                "Recurso - Devolvido",  # TODO
            ],
        ]

        # Draw table header
        self.set_font(font_size=7, bold=True)
        self.draw_cell(
            text=(
                "II - DEMONSTRATIVO DAS DESPESAS REALIZADAS COM "
                "RECURSOS DO REPASSE"
            ),
            width=190,
            align="L",
        )

        # Draw main table
        font = FontFace("FreeSans", "", size_pt=7)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=[38, 38, 38, 38, 38],
            repeat_headings=0,
        ) as table:
            for row_data in up_table_data:
                row = table.row()
                for text in row_data:
                    row.cell(text=text, align="C")

        # Draw summary table
        font = FontFace("FreeSans", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=[152, 38],  # Total: 190,
            repeat_headings=0,
        ) as table:
            for row_data in down_table_data:
                row = table.row()
                for text in row_data:
                    row.cell(text=text, align="C")

        self.ln(10)

    def _draw_org_notification(self) -> None:
        """Draws the organization notification section."""
        self.set_font(font_size=8, bold=True)
        self.draw_multi_cell(
            text=(
                "DECLARAMOS, NA QUALIDADE DE RESPONSÁVEIS PELO ÓRGÃO "
                "BENEFICIÁRIO SUPRA EPIGRAFADO, SOB AS PENAS DA LEI, QUE A "
                "DESPESA RELACIONADA, EXAMINADA PELO CONTROLE INTERNO, "
                "COMPROVA A EXATA APLICAÇÃO DOS RECURSOS RECEBIDOS PARA OS "
                "FINS INDICADOS, CONFORME PROGRAMA DE TRABALHO APROVADO, "
                "PROPOSTO AO ÓRGÃO CONCESSOR."
            ),
            width=190,
            height=5,
            align="J",
        )
        self.ln(15)

    def _draw_table_III(self) -> None:
        """Draws table III with adjustments data."""
        table_data = [
            [
                "AJUSTE Nº",
                "DATA",
                "CONTRATADO / CNPJ",
                "OBJETO RESUMIDO",
                "LICITAÇÃO Nº(4)",
                "FONTE (5)",
                "VALOR GLOBAL DO AJUSTE",
            ],
        ]
        # TODO: Após adendo (Ajuste = Adendo), necessário criar tabela
        table_data.append(["..."] * 7)

        self.set_font(font_size=7, bold=True)
        self.draw_cell(
            text=(
                "III - AJUSTES VINCULADOS ÀS DESPESAS CUSTEADAS COM "
                "RECURSOS DO REPASSE (3)"
            ),
            width=190,
            align="C",
        )

        font = FontFace("FreeSans", "", size_pt=7)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=[27, 25, 30, 27, 27, 27, 27],  # Total: 190
            repeat_headings=0,
        ) as table:
            for row_data in table_data:
                row = table.row()
                for text in row_data:
                    row.cell(text=text, align="C")

        self.ln(10)

    def _draw_observation(self) -> None:
        """Draws the observation section."""
        self.set_font(font_size=8, bold=True)
        contractor_company = self.contract.contractor_company
        self.draw_cell(
            text=(
                f"LOCAL: {contractor_company.city}/{contractor_company.uf} | "
                f"{contractor_company.street}, nº {contractor_company.number} - "
                f"{contractor_company.district}"
            ),
            markdown=True,
            align="L",
        )
        self.ln(self.default_cell_height)
        today = date.today()
        self.draw_cell(
            text=f"DATA: {format_into_brazilian_date(today)}",
            markdown=True,
            align="L",
        )
        self.ln(20)
        self.draw_multi_cell(
            text="**RESPONSÁVEL: NOME, CARGO E ASSINATURA**",
            markdown=True,
            align="L",
        )
        self.ln(8)
        self.draw_cell(text="", width=190, height=10, align="C")
        self.draw_line(
            self.pdf.get_x(),
            self.pdf.get_y(),
            self.pdf.get_x() + 190,
            self.pdf.get_y(),
        )
        self.ln(3)
        self.set_font(font_size=7, bold=False)
        self.draw_cell(text="(1) convênio ou auxílio/subvenção ou contribuição.")
        self.ln(self.default_cell_height)
        self.draw_cell(text="(2) notas fiscais e recibos")
        self.ln(self.default_cell_height)
        self.draw_cell(
            text=(
                "(3) contrato; contrato de gestão; termo de parceria; termo de "
                "colaboração; termo de fomento; etc."
            ),
            align="L",
        )
        self.ln(self.default_cell_height)
        self.draw_cell(
            text=(
                "(4) modalidade, ou, no caso de dispensa e/ou inexigibilidade, "
                "a base legal."
            ),
            align="L",
        )
        self.ln(self.default_cell_height)
        self.draw_cell(text="(5) fonte de recursos: federal ou estadual.", align="L")
