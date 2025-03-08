import copy
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from contracts.choices import NatureCategories
from contracts.models import Contract
from reports.exporters.commons.exporters import BasePdf
from utils.choices import MonthChoices
from utils.formats import (
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class PassOn1PDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self, contract, start_date, end_date):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(233, 234, 236)
        self.pdf = pdf
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def __database_queries(self):
        self.contracts_queryset = Contract.objects.filter(
            area__city_hall=self.contract.area.city_hall, checking_account__isnull=False
        ).order_by("start_of_vigency")
        self.all_values_in_contracts = self.contracts_queryset.filter().aggregate(
            Sum("total_value")
        )["total_value__sum"] or Decimal("0.00")

    def handle(self):
        self.__database_queries()
        self._draw_header()
        self._draw_up_informations()
        self._draw_table()
        self._draw_down_informations()
        self._draw_observations()

        return self.pdf

    def _draw_header(self):
        self.__set_helvetica_font(font_size=9, bold=True)
        self.pdf.multi_cell(
            0,
            4,
            "ANEXO RP-01 REPASSES A ÓRGÃOS PÚBLICOS \n RELAÇÃO DOS VALORES TRANSFERIDOS DE \n CORRENTES DE CONVÊNIO OU CARACTERIZADOS COMO AUXÍLIOS, SUBVENÇÕES OU \n CONTRIBUIÇÕES",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_up_informations(self):
        # Cabeçalho e títulos
        self.__set_helvetica_font(font_size=8, bold=False)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.pdf.cell(
            0,
            7,
            text=f"**EXERCÍCIO:** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            0,
            f"**ÓRGÃO CONCESSOR:** {self.contract.organization.city_hall.name}",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    def _draw_table(self):
        data_up_header = ["", "LEI", "CONVÊNIO", ""]
        data_header = [
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
        data_body = []

        hired_company = self.contract.hired_company
        date_law = self.contract.law_date
        date_agreement = self.contract.agreement_date
        for contract in self.contracts_queryset:
            data_body.append(
                [
                    f"{contract.concession_type}",  # Tipo de Concessão
                    f"{contract.organization.name}",  # BENEFICIARIO
                    f"{hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",  # ENDEREÇO
                    f"Lei nº {contract.law_num}",  # N° da Lei
                    f"De {date_law.day} de {MonthChoices(date_law.month).label.capitalize()} de {date_law.year}",  # DATA da Lei
                    f"{contract.agreement_num}/{date_agreement.year}",  # N° do Convênio
                    f"{format_into_brazilian_date(contract.agreement_date)}",  # DATA do Convênio
                    f"{contract.objective}",  # FINALIDADE
                    f"{contract.end_of_vigency}",  # DATA DO PAGAMENTO
                    f"{contract.checking_account.origin}",  # FONTE
                    f"{format_into_brazilian_currency(contract.total_value)}",  # VALOR EM REAIS
                ]
            )
        data_footer = [
            "Total:",
            f"{format_into_brazilian_currency(self.all_values_in_contracts)}",
        ]

        self.pdf.ln(10)
        sub_col_widths = [61, 29, 29, 73]  # Total: 190
        font = FontFace("Helvetica", "", size_pt=6)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=sub_col_widths,
            repeat_headings=0,
        ) as table:
            up_header = table.row()
            for text in data_up_header:
                up_header.cell(text=text, align="C")

        self.default_cell_height
        col_widths = [15, 20, 26, 14, 15, 14, 15, 19, 17, 17, 20]  # Total: 190
        font = FontFace("Helvetica", "", size_pt=6)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            header = table.row()
            for text in data_header:
                header.cell(text=text, align="C")

            if data_body != []:
                self.pdf.set_font("Helvetica", "", 6)
                for item in data_body:
                    body = table.row()
                    for text in item:
                        body.cell(text=text, align="L")

        self.default_cell_height
        footer_col_widths = [154, 36]  # Total: 190
        font = FontFace("Helvetica", "B", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="R",
            col_widths=footer_col_widths,
            repeat_headings=0,
        ) as table:
            total = table.row()
            for text in data_footer:
                total.cell(text=text, align="R")
        self.pdf.ln(10)

    def _draw_down_informations(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        contractor_company = self.contract.contractor_company
        self.pdf.cell(
            0,
            0,
            f"LOCAL: {contractor_company.city}/{contractor_company.uf} | {contractor_company.street}, nº {contractor_company.number} - {contractor_company.district}",  # ENDEREÇO
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(self.default_cell_height)
        today = date.today()
        self.pdf.cell(
            0,
            0,
            f"DATA: {format_into_brazilian_date(today)}",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(20)
        self.pdf.multi_cell(
            0,
            0,
            f"**RESPONSÁVEL: NOME, CARGO E ASSINATURA**",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            markdown=True,
        )
        self.pdf.ln(8)
        self.pdf.cell(190, 10, "", ln=True, align="C")
        self.pdf.line(
            self.pdf.get_x(), self.pdf.get_y(), self.pdf.get_x() + 190, self.pdf.get_y()
        )
        self.pdf.ln(10)

    def _draw_observations(self):
        self.__set_helvetica_font(font_size=7)
        self.pdf.cell(
            0,
            0,
            "(*) Auxílio, subvenção ou contribuição.",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(5)
        self.pdf.cell(
            0,
            0,
            f"(**) Fonte de recursos: federal ou estadual.",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
