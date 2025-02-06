import copy
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from django.db.models import Q
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense
from contracts.choices import NatureCategories
from reports.exporters.commons.exporters import BasePdf
from utils.formats import format_into_brazilian_currency


@dataclass
class PeriodEpensesPDFExporter:
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
        self.start_date = start_date
        self.end_date = end_date

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def handle(self):
        self._draw_header()
        self._draw_informations()
        self._draw_account_data()
        # self._draw_signatories_notification()
        # self._draw_table_II()
        # self._draw_org_notification()
        # self._draw_table_III()
        # self._draw_observation()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_helvetica_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "DESPESAS REALIZADAS DO PERÍODO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=8, bold=False)
        start = self.accountability.contract.start_of_vigency
        end = self.accountability.contract.end_of_vigency
        self.pdf.cell(
            0,
            10,
            # TODO confirmar período
            f"Período: {start.day}/{start.month}/{start.year} à {end.day}/{end.month}/{end.year}",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self):
        self.pdf.cell(
            text=f"**Órgão Concessor:** {self.accountability.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Tipo de Concessão:** {self.accountability.contract.concession_type}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Nº:** {self.accountability.contract.code}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Entidade Beneficiária:** {self.accountability.contract.organization.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**CNPJ**: {self.accountability.contract.hired_company.cnpj}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        hired_company = self.accountability.contract.hired_company
        self.pdf.cell(
            # TODO averiguar se dados pertence a entidade "Contratada"
            text=f"**Endereço e CEP:** {hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.multi_cell(
            text=f"**Objeto da Parceria:** {self.accountability.contract.objective}",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=self.default_cell_height,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        
        self.pdf.ln(8)


    def _draw_account_data(self):
        ...
        