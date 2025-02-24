import copy
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.db.models import Q, Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense, Revenue
from contracts.choices import NatureCategories
from reports.exporters.commons.exporters import BasePdf
from utils.formats import (
    document_mask,
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class PassOn10PDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self, accountability, start_date, end_date):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.set_font("Helvetica", "", 8)
        self.pdf = pdf
        self.accountability = accountability
        self.start_date = start_date
        self.end_date = end_date

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def __database_queries(self):
        self.checking_account = self.accountability.contract.checking_account
        self.investing_account = self.accountability.contract.investing_account

        # Queries para Receitas
        self.revenue_queryset = Revenue.objects.filter(
            Q(bank_account=self.checking_account)
            | Q(bank_account=self.investing_account),
            receive_date__gte=self.start_date,
            receive_date__lte=self.end_date,
        ).exclude(bank_account__isnull=True)

        self.all_pass_on_values = self.revenue_queryset.aggregate(Sum("value"))[
            "value__sum"
        ] or Decimal("0.00")

        self.previous_balance = self.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.PREVIOUS_BALANCE
        ).aggregate(Sum("value"))["value__sum"] or Decimal("0.00")

        self.investment_income = self.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.INVESTMENT_INCOME
        ).aggregate(Sum("value"))["value__sum"] or Decimal("0.00")

        self.own_resources = self.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.OWN_RESOURCES
        ).aggregate(Sum("value"))["value__sum"] or Decimal("0.00")

        # Queries para Despesas
        self.expense_queryset = Expense.objects.filter(
            accountability__contract=self.accountability.contract,
            liquidation__gte=self.start_date,
            liquidation__lte=self.end_date,
        )

        self.all_expenses_value = self.expense_queryset.aggregate(Sum("value"))[
            "value__sum"
        ] or Decimal("0.00")

    def handle(self):
        self.__database_queries()
        self._draw_header()
        self._draw_informations()
        self._draw_first_table()
        self._draw_partners_data()
        self._draw_documents_table()
        self._draw_header_resources_table()
        self._draw_resources_table()
        self._draw_resources_footer()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_helvetica_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "ANEXO RP-10 - REPASSES AO TERCEIRO SETOR",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=10, bold=False)
        self.pdf.cell(
            0,
            10,
            "DEMONSTRATIVO INTEGRAL DAS RECEITAS E DESPESAS - TERMO DE COLABORAÇÃO/FOMENTO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self):
        self.pdf.cell(
            text=f"**Órgão Público:** {self.accountability.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Organização da Sociedade Civil:** {self.accountability.contract.organization.name}",
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
        self.pdf.cell(
            text=f"**Responsáveis pela OSC:**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)

    def _draw_first_table(self):
        self.__set_helvetica_font(font_size=7, bold=True)
        table_data = [
            [
                f"Nome: {self.accountability.contract.accountability_autority.get_full_name()}",
                f"Papel: {self.accountability.contract.supervision_autority.position} - Confirmar variável",
                f"{document_mask(str(self.accountability.contract.supervision_autority.cpf))}",
            ],
        ]

        col_widths = [70, 60, 60]

        for row in table_data:
            for col_index, col_text in enumerate(row):
                self.pdf.cell(
                    col_widths[col_index],
                    h=self.default_cell_height,
                    text=col_text,
                    border=1,
                    align="L",
                )
            self.pdf.ln()

    def _draw_partners_data(self):
        self.pdf.ln(3)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=f"**Objeto da Parceria:** {self.accountability.contract.objective}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        start = self.accountability.contract.start_of_vigency
        end = self.accountability.contract.end_of_vigency
        self.pdf.cell(
            text=f"**Exercício:** {format_into_brazilian_date(start)} a {format_into_brazilian_date(end)}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Origem dos Recursos (1):** Consolidado de todas as fontes",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(3)

    def _draw_documents_table(self):
        self.__set_helvetica_font(font_size=7, bold=False)
        self.pdf.ln()
        table_data = [
            ["**DOCUMENTO**", "**DATA**", "**VIGÊNCIA**", "**VALOR - R$**"],
            [
                f"Criar Termo de Colaboração",  # TODO criar campo
                f"data",  # TODO após criar campo
                f"{format_into_brazilian_date(self.accountability.contract.end_of_vigency)}",
                f"{format_into_brazilian_currency(self.accountability.contract.total_value)}",
            ],
            [
                "Criar classe de aditamento",  # TODO criar Classe
                "dd/mm/aaaa",
                "dd/mm/aaaa",
                "R$ xx.xxx,xx",
            ],
        ]

        col_widths = [75, 19, 65, 31]
        font = FontFace("Helvetica", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            markdown=True,
            col_widths=col_widths,
        ) as table:
            for item in table_data:
                data = table.row()
                for text in item:
                    data.cell(text=text, align="C")

        self.pdf.ln()

    def _draw_header_resources_table(self):
        self.pdf.ln(7)

        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            190,
            h=self.default_cell_height,
            text="**DEMONSTRATIVO DOS RECURSOS DISPONÍVEIS NO EXERCÍCIO**",
            border=1,
            markdown=True,
            align="C",
        )
        self.pdf.ln(self.default_cell_height)

        table_data = [
            [
                "**DATA PREVISTA PARA O REPASSE (2)**",
                "**VALORES PREVISTOS (R$)**",
                "**DATA DO REPASSE**",
                "**NÚMERO DO DOCUMENTO DE CRÉDITO**",
                "**VALORES REPASSADOS (R$)**",
            ],
            [
                f"{format_into_brazilian_date(self.accountability.contract.end_of_vigency)}",
                f"{format_into_brazilian_currency(self.accountability.contract.total_value)}",
                f"dd/mm/aa",  # TODO seria o mesmoque end_of_vigency?
                f"Nao sei o que é",
                f"{format_into_brazilian_currency(self.all_pass_on_values)}",
            ],
        ]

        col_widths = [40, 35, 25, 50, 40]
        font = FontFace("Helvetica", "", size_pt=7)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            for item in table_data:
                data = table.row()
                for text in item:
                    data.cell(text=text, align="C")

        # Linha cinza
        self.pdf.set_fill_color(233, 234, 236)
        self.pdf.cell(
            190, h=self.default_cell_height, text="", border=1, align="C", fill=True
        )
        self.pdf.set_fill_color(255, 255, 255)
        self.pdf.ln(self.default_cell_height)

    def _draw_resources_table(self):
        extern_revenue_data = [
            [
                "(A) SALDO DO EXERCÍCIO ANTERIOR",
                "",
                f"{format_into_brazilian_currency(self.previous_balance)}",
            ],
            [
                "(B) REPASSES PÚBLICOS NO EXERCÍCIO",
                "",
                f"{format_into_brazilian_currency(self.all_pass_on_values)}",
            ],
            [
                "(C) RECEITAS COM APLICAÇÕES FINANCEIRAS DOS REPASSES PÚBLICOS",
                "",
                f"{format_into_brazilian_currency(self.investment_income)}",
            ],
            [
                "(D) OUTRAS RECEITAS DECORRENTES DA EXECUÇÃO DO AJUSTE (3)",
                "",
                "R$XX.XXX,YZ",  #  TODO Classe de adtamento
            ],
        ]

        sum_items_a_to_d = (
            self.previous_balance + self.all_pass_on_values + self.investment_income
        )  # TODO inserir valor de D

        extern_revenue_data.append(
            [
                "(E) TOTAL DE RECURSOS PÚBLICOS (A + B + C + D)",
                "",
                f"{format_into_brazilian_currency(sum_items_a_to_d)}",
            ]
        )

        extern_revenue_data.append(
            ["", "", ""],
        )

        intern_revenue_data = [
            [
                "(F) RECURSOS PRÓPRIOS DA ENTIDADE PARCEIRA",
                "",
                f"{format_into_brazilian_currency(self.own_resources)}",
            ],
            [
                "(G) TOTAL DE RECURSOS DISPONÍVEIS NO EXERCÍCIO (E + F)",
                "",
                f"{format_into_brazilian_currency(sum_items_a_to_d+self.own_resources)}",
            ],
        ]

        col_widths = [100, 50, 40]
        self.__set_helvetica_font(7)
        font = FontFace("Helvetica", "", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            for item in extern_revenue_data:
                enxtern = table.row()
                for id, text in enumerate(item):
                    if id == 0:
                        text_align = "L"
                    else:
                        text_align = "R"
                    enxtern.cell(text=text, align=text_align)

            for item in intern_revenue_data:
                intern = table.row()
                for id, text in enumerate(item):
                    if id == 0:
                        text_align = "L"
                    else:
                        text_align = "R"
                    intern.cell(text=text, align=text_align)

    def _draw_resources_footer(self):
        self.pdf.ln(self.default_cell_height)
        self.__set_helvetica_font(7)
        self.pdf.cell(
            text="(1) Verba: Federal, Estadual ou Municipal, devendo ser elaborado um anexo para cada fonte de recurso.",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="(2) Incluir valores previstos no exercício anterior e repassados neste exercício.",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="(3) Receitas com estacionamento, aluguéis, entre outras.",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)
