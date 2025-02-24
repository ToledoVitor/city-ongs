from dataclasses import dataclass
from datetime import datetime

from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense, Revenue
from contracts.models import Contract
from reports.exporters.commons.exporters import BasePdf
from utils.formats import format_into_brazilian_currency, format_into_brazilian_date


@dataclass
class PeriodEpensesPDFExporter:
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
        self._draw_pass_on_table()
        self._draw_expenses_table()

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
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
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
            text=f"**Órgão Concessor:** {self.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Tipo de Concessão:** {self.contract.concession_type}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Nº:** {self.contract.code}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Entidade Beneficiária:** {self.contract.organization.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**CNPJ**: {self.contract.hired_company.cnpj}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        hired_company = self.contract.hired_company
        self.pdf.cell(
            # TODO averiguar se dados pertence a entidade "Contratada"
            text=f"**Endereço e CEP:** {hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.multi_cell(
            text=f"**Objeto da Parceria:** {self.contract.objective}",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=self.default_cell_height,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        self.pdf.ln(8)

    def _draw_account_data(self):
        account_data = [
            ["", "", f"**   Conta:** {self.contract.checking_account}"],
            [
                "",
                "",
                f"**   Banco:** {self.contract.checking_account.bank_name}",
            ],
            [
                "",
                "",
                f"**   Agência:** {self.contract.checking_account.agency}",
            ],
            [
                "",
                "",
                f"**   Nº da Conta** {self.contract.checking_account.account}",
            ],
            [
                "",
                "",
                f"**   Fontes de Recurso:** {self.contract.checking_account.origin}",
            ],
        ]

        self.__set_helvetica_font(font_size=10, bold=True)
        self.pdf.cell(
            0,
            self.default_cell_height,
            text="Dados da Conta",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="L",
        )

        self.__set_helvetica_font(font_size=9, bold=False)
        col_widths = [1, 2, 187]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            for item in account_data:
                data = table.row()
                for id, text in enumerate(item):
                    if id == 1:
                        self.pdf.set_fill_color(225, 225, 225)
                    else:
                        self.pdf.set_fill_color(255, 255, 255)

                    data.cell(text=text, align="L", border=0)

        self.pdf.ln(8)

    def _draw_pass_on_table(self):
        pass_on_head = [
            "**Repasse**",
            "**Valor**",
            "**Data Docto.**",
            "**Competência**",
            "**Recebimento**",
        ]

        revenues = Revenue.objects.filter(
            accountability__contract=self.contract,
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date,
        )
        pass_on_data = [
            *[
                [
                    revenue.revenue_nature_label,
                    format_into_brazilian_currency(revenue.value),
                    format_into_brazilian_date(revenue.receive_date),
                    format_into_brazilian_date(revenue.competency),
                    format_into_brazilian_date(revenue.receive_date),
                ]
                for revenue in revenues
            ]
        ]

        self.__set_helvetica_font(font_size=10, bold=True)
        self.pdf.cell(
            0,
            self.default_cell_height,
            text="Repasses",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="L",
        )

        self.__set_helvetica_font(font_size=7, bold=False)
        col_widths = [43, 34, 33, 40, 40]  # Total: 190
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.pdf.set_fill_color(225, 225, 225)
            head = table.row()
            for text in pass_on_head:
                head.cell(text=text, align="C")

            self.pdf.set_fill_color(255, 255, 255)
            for item in pass_on_data:
                data = table.row()
                for text in item:
                    data.cell(text=text, align="C")

        self.pdf.ln(6)

    def _draw_expenses_table(self):
        expenses_head = [
            "**Item**",
            "**Competência**",
            "**Tipo**",
            "**Nº do Documento**",
            "**Favorecido**",
            "**Identificação da Despesa**",
            "**Forma de Liquidação**",
            "**Data de Liquidação**",
            "**Nº Docto. Vinculado**",
            "**Valor**",
        ]

        expenses = Expense.objects.filter(
            accountability__contract=self.contract,
            due_date__gte=self.start_date,
            due_date__lte=self.end_date,
        )
        expenses_data = [
            *[
                [
                    expense.item.name if expense.item else "",
                    format_into_brazilian_date(expense.competency),
                    expense.document_type_label,
                    expense.document_number,
                    expense.favored.name if expense.favored else "",
                    expense.identification,
                    expense.liquidation_form_label,
                    format_into_brazilian_date(expense.liquidation),
                    self.contract.code,
                    format_into_brazilian_currency(expense.value),
                ]
                for expense in expenses
            ]
        ]

        self.__set_helvetica_font(font_size=10, bold=True)
        self.pdf.cell(
            0,
            self.default_cell_height,
            text="Despesas",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="L",
        )

        self.__set_helvetica_font(font_size=7, bold=False)
        col_widths = [18, 20, 20, 15, 27, 20, 20, 20, 15, 15]  # Total: 190
        font = FontFace("Helvetica", "", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            self.pdf.set_fill_color(225, 225, 225)
            head = table.row()
            for text in expenses_head:
                head.cell(text=text, align="C")

            self.pdf.set_fill_color(255, 255, 255)
            for item in expenses_data:
                data = table.row()
                for text in item:
                    data.cell(text=text, align="C")

        self.pdf.ln(8)

        self.__set_helvetica_font(font_size=7, bold=False)
        self.pdf.cell(
            0,
            self.default_cell_height,
            text="Responsáveis pela Contratada:",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="L",
        )
