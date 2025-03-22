import os
from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.db.models import Q
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Revenue
from contracts.models import Contract
from reports.exporters.commons.exporters import BasePdf
from utils.formats import format_into_brazilian_currency, format_into_brazilian_date

font_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSans.ttf")
font_bold_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSansBold.ttf")


@dataclass
class PassOn4PDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self, contract, start_date, end_date):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.add_font("FreeSans", "", font_path, uni=True)
        pdf.add_font("FreeSans", "B", font_bold_path, uni=True)
        pdf.set_font("FreeSans", "", 8)
        self.pdf = pdf
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date

    def __set_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("FreeSans", "B", font_size)
        else:
            self.pdf.set_font("FreeSans", "", font_size)

    def __background_gray_color(self, gray):
        if gray:
            self.pdf.set_fill_color(233, 234, 236)
        else:
            self.pdf.set_fill_color(255, 255, 255)

    def __database_queries(self):
        self.checking_account = self.contract.checking_account
        self.investing_account = self.contract.investing_account

        self.revenue_queryset = Revenue.objects.filter(
            Q(bank_account=self.checking_account)
            | Q(bank_account=self.investing_account)
        ).exclude(bank_account__isnull=True)

    def handle(self):
        self.__database_queries()
        self._draw_header()
        self._draw_informations()
        self._draw_manager_table()
        self._draw_partner_table()
        self._draw_collaborator_table()
        self._draw_promotion_table()
        self._draw_agreement_table()
        self._draw_concession_table()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_font(font_size=10, bold=True)
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
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self):
        self.__set_font(font_size=8, bold=False)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.pdf.cell(
            text=f"**VALORES REPASSADOS DURANTE O EXERCÍCIO DE:** {format_into_brazilian_date(start)} a {format_into_brazilian_date(end)}",
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

    def _draw_manager_table(self):
        manager_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.MANAGEMENT  # Não é Revenue
        )

        self.pdf.ln()
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
        hired_company = self.contract.hired_company
        contract = self.contract
        table_data = []
        total_revenue_value = Decimal("0.00")
        for revenue in manager_queryset:
            table_data.append(
                [
                    f"{contract.code}",
                    f"{contract.organization.name}",
                    f"{hired_company.cnpj}",
                    f"{hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
                    f"{revenue.receive_date}",
                    f"{contract.end_of_vigency}",
                    "Valor Global do Ajuste - Valor do adendo",
                    f"{contract.objective}",
                    f"{revenue.source}",
                    f"{format_into_brazilian_currency(revenue.value)}",
                ]
            )
            total_revenue_value += revenue.value

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

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
            self.__background_gray_color(gray=True)
            header = table.row()
            for text in header_data:
                header.cell(text=text, align="C")

            self.__set_font(self.default_cell_height)
            for item in table_data:
                self.__background_gray_color(gray=False)
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
            self.__background_gray_color(gray=True)
            footer = table.row()
            for text in footer_data:
                footer.cell(text=text, align="R")

        self.pdf.ln(10)

    def _draw_partner_table(self):
        partner_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.PARTNERSHIP
        )
        self.__set_font(font_size=7, bold=True)
        self.pdf.ln()
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
        hired_company = self.contract.hired_company
        contract = self.contract
        table_data = []
        total_revenue_value = Decimal("0.00")
        for revenue in partner_queryset:
            table_data.append(
                [
                    f"{contract.code}",
                    f"{contract.organization.name}",
                    f"{hired_company.cnpj}",
                    f"{hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
                    f"{revenue.receive_date}",
                    f"{contract.end_of_vigency}",
                    "Valor Global do Ajuste - Valor do adendo",
                    f"{contract.objective}",
                    f"{revenue.source}",
                    f"{format_into_brazilian_currency(revenue.value)}",
                ]
            )
            total_revenue_value += revenue.value

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

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
            self.__background_gray_color(gray=True)
            header = table.row()
            for text in header_data:
                header.cell(text=text, align="C")

            self.__set_font(self.default_cell_height)
            for item in table_data:
                self.__background_gray_color(gray=False)
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
            self.__background_gray_color(gray=True)
            footer = table.row()
            for text in footer_data:
                footer.cell(text=text, align="R")

        self.pdf.ln(10)

    def _draw_collaborator_table(self):
        collaborator_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.COLLABORATION
        )
        self.__set_font(font_size=7, bold=True)
        self.pdf.ln()
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
        hired_company = self.contract.hired_company
        contract = self.contract
        table_data = []
        total_revenue_value = Decimal("0.00")
        for revenue in collaborator_queryset:
            table_data.append(
                [
                    f"{contract.code}",
                    f"{contract.organization.name}",
                    f"{hired_company.cnpj}",
                    f"{hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
                    f"{revenue.receive_date}",
                    f"{contract.end_of_vigency}",
                    "Valor Global do Ajuste - Valor do adendo",
                    f"{contract.objective}",
                    f"{revenue.source}",
                    f"{format_into_brazilian_currency(revenue.value)}",
                ]
            )
            total_revenue_value += revenue.value

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

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
            self.__background_gray_color(gray=True)
            header = table.row()
            for text in header_data:
                header.cell(text=text, align="C")

            self.__set_font(self.default_cell_height)
            for item in table_data:
                self.__background_gray_color(gray=False)
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
            self.__background_gray_color(gray=True)
            footer = table.row()
            for text in footer_data:
                footer.cell(text=text, align="R")

        self.pdf.ln(10)

    def _draw_promotion_table(self):
        promotion_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.DEVELOPMENTO
        )
        self.__set_font(font_size=7, bold=True)
        self.pdf.ln(3)
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
        hired_company = self.contract.hired_company
        contract = self.contract
        table_data = []
        total_revenue_value = Decimal("0.00")
        for revenue in promotion_queryset:
            table_data.append(
                [
                    f"{contract.code}",
                    f"{contract.organization.name}",
                    f"{hired_company.cnpj}",
                    f"{hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
                    f"{revenue.receive_date}",
                    f"{contract.end_of_vigency}",
                    "Valor Global do Ajuste - Valor do adendo",
                    f"{contract.objective}",
                    f"{revenue.source}",
                    f"{format_into_brazilian_currency(revenue.value)}",
                ]
            )
            total_revenue_value += revenue.value

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

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
            self.__background_gray_color(gray=True)
            header = table.row()
            for text in header_data:
                header.cell(text=text, align="C")

            self.__set_font(self.default_cell_height)
            for item in table_data:
                self.__background_gray_color(gray=False)
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
            self.__background_gray_color(gray=True)
            footer = table.row()
            for text in footer_data:
                footer.cell(text=text, align="R")

        self.pdf.ln(10)

    def _draw_agreement_table(self):
        agreement_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.AGREEMENT
        )
        self.__set_font(font_size=7, bold=True)
        self.pdf.ln()
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
        hired_company = self.contract.hired_company
        contract = self.contract
        table_data = []
        total_revenue_value = Decimal("0.00")
        for revenue in agreement_queryset:
            table_data.append(
                [
                    f"{contract.code}",
                    f"{contract.organization.name}",
                    f"{hired_company.cnpj}",
                    f"{hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
                    f"{revenue.receive_date}",
                    f"{contract.end_of_vigency}",
                    "Valor Global do Ajuste - Valor do adendo",
                    f"{contract.objective}",
                    f"{revenue.source}",
                    f"{format_into_brazilian_currency(revenue.value)}",
                ]
            )
            total_revenue_value += revenue.value

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

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
            self.__background_gray_color(gray=True)
            header = table.row()
            for text in header_data:
                header.cell(text=text, align="C")

            self.__set_font(self.default_cell_height)
            for item in table_data:
                self.__background_gray_color(gray=False)
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
            self.__background_gray_color(gray=True)
            footer = table.row()
            for text in footer_data:
                footer.cell(text=text, align="R")

        self.pdf.ln(10)

    def _draw_concession_table(self):
        concession_queryset = self.revenue_queryset.filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        ).filter(
            accountability__contract__concession_type=Contract.ConcessionChoices.GRANT
        )
        self.__set_font(font_size=8, bold=True)
        self.pdf.cell(
            text="II - AUXÍLIOS, SUBVENÇÕES E/OU CONTRIBUIÇÕES PAGOS:",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(2)
        self.__set_font(font_size=7, bold=True)
        self.pdf.ln()
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
        hired_company = self.contract.hired_company
        contract = self.contract
        table_data = []
        total_revenue_value = Decimal("0.00")
        for revenue in concession_queryset:
            table_data.append(
                [
                    f"{contract.concession_type}",
                    f"{contract.organization.name}",
                    f"{hired_company.cnpj}",
                    f"{hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
                    f"{revenue.receive_date}",
                    f"{format_into_brazilian_date(contract.end_of_vigency)}",
                    "ClassAdendo",  # TODO criar classe adendo
                    f"{contract.objective}",
                    f"{revenue.source}",
                    f"{format_into_brazilian_currency(revenue.value)}",
                ]
            )
            total_revenue_value += revenue.value

        footer_data = [
            "**Total:**",
            f"**{format_into_brazilian_currency(total_revenue_value)}**",
        ]

        col_widths = [15, 20, 10, 15, 15, 15, 20, 30, 20, 20]
        font = FontFace("FreeSans", "", size_pt=7)

        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            markdown=True,
            col_widths=col_widths,
        ) as table:
            header = table.row()
            self.__background_gray_color(gray=True)
            for text in header_data:
                header.cell(text=text, align="C")

            self.pdf.set_font("FreeSans", "", 7)
            self.__background_gray_color(gray=False)
            for item in table_data:
                data = table.row()
                for text in item:
                    data.cell(text=text, align="C")

        col_widths = [178, 22]
        font = FontFace("FreeSans", "", size_pt=7)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="L",
            markdown=True,
            col_widths=col_widths,
        ) as table:
            footer = table.row()
            self.__background_gray_color(gray=True)
            for text in footer_data:
                footer.cell(text=text, align="R")
