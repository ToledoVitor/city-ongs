import os
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense
from contracts.models import ContractAddendum
from reports.exporters.base import BasePDFExporter
from reports.exporters.commons.integral_statement import (
    build_revenue_summary,
    categorize_expenses,
    convert_decimal_to_brl,
)
from utils.formats import (
    document_mask,
    format_into_brazilian_currency,
    format_into_brazilian_date,
)

font_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSans.ttf")
font_bold_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSansBold.ttf")


class PassOn10PDFExporter(BasePDFExporter):
    def __init__(self, contract, start_date, end_date):
        super().__init__()
        self.initialize_pdf(
            font_specs=[("", font_path), ("B", font_bold_path)],
            base_font_size=8,
        )
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date

    def __database_queries(self):
        summary = build_revenue_summary(self.contract, self.start_date, self.end_date)
        self.checking_account = summary.checking_account
        self.investing_account = summary.investing_account
        self.revenue_queryset = summary.revenue_queryset
        self.all_pass_on_values = summary.all_pass_on_values
        self.previous_balance = summary.previous_balance
        self.investment_income = summary.investment_income
        self.own_resources = summary.own_resources
        self.other_revenues_value = summary.other_revenues_value
        self.latest_pass_on_info = summary.latest_pass_on_info

        self.expense_queryset = Expense.objects.filter(
            accountability__contract=self.contract,
            liquidation__gte=self.start_date,
            liquidation__lte=self.end_date,
        )

        self.addendum_queryset = ContractAddendum.objects.filter(
            contract=self.contract,
        )

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
        self._draw_expenses_table()
        self._draw_expenses_footer()
        self._draw_financial_table()
        self._draw_last_informations()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
        self._set_font(font_size=10, bold=True)
        self.pdf.multi_cell(
            0,
            self.default_cell_height,
            "ANEXO RP-10 - REPASSES AO TERCEIRO SETOR \n DEMONSTRATIVO INTEGRAL DAS RECEITAS E DESPESAS TERMO DE COLABORAÇÃO/FOMENTO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self):
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"**Órgão Público:** {self.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(self.default_cell_height)
        self.pdf.cell(
            text=f"**Organização da Sociedade Civil:** {self.contract.organization.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(self.default_cell_height)
        self.pdf.cell(
            text=f"**CNPJ**: {self.contract.hired_company.cnpj}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(self.default_cell_height)
        hired_company = self.contract.hired_company
        self.pdf.cell(
            text=f"**Endereço e CEP:** {hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(self.default_cell_height)
        self.pdf.cell(
            text="**Responsável(is) pela OSC:**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(self.default_cell_height)

    def _draw_first_table(self):
        self._set_font(font_size=7, bold=False)
        table_data = []
        table_data.append(
            [
                "",
                "",
                " ",
                f"Nome: {self.contract.accountability_autority.get_full_name()}",
            ]
        )
        (
            table_data.append(
                [
                    "",
                    "",
                    " ",
                    f"Papel: {self.contract.supervision_autority.position}",
                ]
            ),
        )
        table_data.append(
            [
                "",
                "",
                " ",
                f"{document_mask(str(self.contract.supervision_autority.cpf))}",
            ]
        )

        col_widths = [1, 2, 2, 185]  # Total de 190
        font = FontFace("FreeSans", "", size_pt=8)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="L",
            markdown=True,
            col_widths=col_widths,
        ) as table:
            for item in table_data:
                data = table.row()
                for id, text in enumerate(item):
                    if id == 1:
                        self.pdf.set_fill_color(220, 220, 220)
                    else:
                        self.pdf.set_fill_color(255, 255, 255)
                    data.cell(text=text, align="L", border=0)

    def _draw_partners_data(self):
        self.pdf.ln(3)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=f"**Objeto da Parceria:** {self.contract.objective}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.pdf.cell(
            text=f"**Exercício:** {format_into_brazilian_date(start)} a {format_into_brazilian_date(end)}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="**Origem dos Recursos (1):** Consolidado de todas as fontes",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(3)

    def _draw_documents_table(self):
        self._set_font(font_size=7, bold=False)
        self.pdf.ln()
        table_data = [
            ["**DOCUMENTO**", "**DATA**", "**VIGÊNCIA**", "**VALOR - R$**"],
            [
                self.contract.name_with_code,
                format_into_brazilian_date(self.contract.start_of_vigency),
                format_into_brazilian_date(self.contract.end_of_vigency),
                format_into_brazilian_currency(self.contract.total_value),
            ],
        ]

        for addendum in self.addendum_queryset:
            table_data.append(
                [
                    self.contract.name_with_code,
                    format_into_brazilian_date(addendum.start_of_vigency),
                    format_into_brazilian_date(addendum.end_of_vigency),
                    format_into_brazilian_currency(addendum.total_value),
                ]
            )

        col_widths = [75, 19, 65, 31]
        font = FontFace("FreeSans", "", size_pt=8)
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

        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            190,
            h=self.default_cell_height,
            text="**DEMONSTRATIVO DOS RECURSOS DISPONÍVEIS NO EXERCÍCIO**",
            border=1,
            markdown=True,
            align="C",
        )
        self.pdf.ln(self.default_cell_height)
        pass_on_date = (
            self.latest_pass_on_info.get("receive_date")
            if self.latest_pass_on_info
            else None
        )

        table_data = [
            [
                "**DATA PREVISTA PARA O REPASSE (2)**",
                "**VALORES PREVISTOS (R$)**",
                "**DATA DO REPASSE**",
                "**NÚMERO DO DOCUMENTO DE CRÉDITO**",
                "**VALORES REPASSADOS (R$)**",
            ],
            [
                f"{format_into_brazilian_date(self.contract.end_of_vigency)}",
                f"{format_into_brazilian_currency(self.contract.total_value)}",
                f"{format_into_brazilian_date(pass_on_date)}"
                if pass_on_date
                else "N/A",
                f"{self.contract.internal_code}",
                f"{format_into_brazilian_currency(self.all_pass_on_values)}",
            ],
        ]

        col_widths = [40, 35, 25, 50, 40]
        font = FontFace("FreeSans", "", size_pt=7)
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
            190,
            h=self.default_cell_height,
            text="",
            border=1,
            align="C",
            fill=True,
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
                f"{format_into_brazilian_currency(self.other_revenues_value)}",
            ],
        ]

        self.sum_items_a_to_d = (
            self.previous_balance
            + self.all_pass_on_values
            + self.investment_income
            + self.other_revenues_value
        )

        extern_revenue_data.append(
            [
                "(E) TOTAL DE RECURSOS PÚBLICOS (A + B + C + D)",
                "",
                f"{format_into_brazilian_currency(self.sum_items_a_to_d)}",
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
                f"{format_into_brazilian_currency(self.sum_items_a_to_d + self.own_resources)}",
            ],
        ]

        col_widths = [100, 50, 40]
        self._set_font(7)
        font = FontFace("FreeSans", "", size_pt=7)
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
        self._set_font(7)
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

    def _draw_expenses_table(self):
        self.pdf.multi_cell(
            text=f"O(s) signatário(s), na qualidade de representante(s) do(a) {self.contract.name} vem indicar, na forma abaixo detalhada, as despesas incorridas e pagas no exerício {format_into_brazilian_date(self.start_date)} a {format_into_brazilian_date(self.end_date)} bem como as despesas a pagar no exercício seguinte.",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=4,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        self.pdf.ln(7)
        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            190,
            h=self.default_cell_height,
            text="DEMONSTRATIVO DAS DESPESAS INCORRIDAS NO EXERCÍCIO",
            border=1,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            190,
            h=self.default_cell_height,
            text="ORIGEM DOS RECURSOS (4): **Consolidado de todas as fontes**",
            border=1,
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        headers = [
            "CATEGORIA OU FINALIDADE DA DESPESA (8)",
            "DESPESAS CONTABILIZADAS NESTE EXERCÍCIO (R$)",
            "DESPESAS CONTABILIZADAS EM EXERCÍCIOS ANTERIORES E PAGAS NESTE EXERCÍCIO (R$) (H)",
            "DESPESAS CONTABILIZADAS NESTE EXERCÍCIO E PAGAS NESTE EXERCÍCIO (R$) (I)",
            "TOTAL DE DESPESAS PAGAS NESTE EXERCÍCIO (R$) (J= H + I)",
            "DESPESAS CONTABILIZADAS NESTE EXERCÍCIO A PAGAR EM EXERCÍCIOS SEGUINTES (R$)",
        ]
        expenses_dict = categorize_expenses(
            self.contract, self.start_date, self.end_date, inclusive_bounds=True
        )
        expenses_dict = convert_decimal_to_brl(expenses_dict)

        table_data = [
            [
                "Recursos humanos (5)",
                expenses_dict["HUMAN_RESOURCES"]["accounted_on"],
                expenses_dict["HUMAN_RESOURCES"]["not_accounted"],
                expenses_dict["HUMAN_RESOURCES"]["accounted_and_paid"],
                expenses_dict["HUMAN_RESOURCES"]["paid_on"],
                expenses_dict["HUMAN_RESOURCES"]["not_paid"],
            ],
            [
                "Recursos humanos (6)",
                expenses_dict["OTHER_HUMAN_RESOURCES"]["accounted_on"],
                expenses_dict["OTHER_HUMAN_RESOURCES"]["not_accounted"],
                expenses_dict["OTHER_HUMAN_RESOURCES"]["accounted_and_paid"],
                expenses_dict["OTHER_HUMAN_RESOURCES"]["paid_on"],
                expenses_dict["OTHER_HUMAN_RESOURCES"]["not_paid"],
            ],
            [
                "Medicamentos",
                expenses_dict["MEDICINES"]["accounted_on"],
                expenses_dict["MEDICINES"]["not_accounted"],
                expenses_dict["MEDICINES"]["accounted_and_paid"],
                expenses_dict["MEDICINES"]["paid_on"],
                expenses_dict["MEDICINES"]["not_paid"],
            ],
            [
                "Material médico e hospitalar (*)",
                expenses_dict["MEDICAL_AND_HOSPITAL"]["accounted_on"],
                expenses_dict["MEDICAL_AND_HOSPITAL"]["not_accounted"],
                expenses_dict["MEDICAL_AND_HOSPITAL"]["accounted_and_paid"],
                expenses_dict["MEDICAL_AND_HOSPITAL"]["paid_on"],
                expenses_dict["MEDICAL_AND_HOSPITAL"]["not_paid"],
            ],
            [
                "Gêneros alimentícios",
                expenses_dict["FOODSTUFFS"]["accounted_on"],
                expenses_dict["FOODSTUFFS"]["not_accounted"],
                expenses_dict["FOODSTUFFS"]["accounted_and_paid"],
                expenses_dict["FOODSTUFFS"]["paid_on"],
                expenses_dict["FOODSTUFFS"]["not_paid"],
            ],
            [
                "Outros materiais de consumo",
                expenses_dict["OTHER_CONSUMABLES"]["accounted_on"],
                expenses_dict["OTHER_CONSUMABLES"]["not_accounted"],
                expenses_dict["OTHER_CONSUMABLES"]["accounted_and_paid"],
                expenses_dict["OTHER_CONSUMABLES"]["paid_on"],
                expenses_dict["OTHER_CONSUMABLES"]["not_paid"],
            ],
            [
                "Serviços médicos (*)",
                expenses_dict["MEDICAL_SERVICES"]["accounted_on"],
                expenses_dict["MEDICAL_SERVICES"]["not_accounted"],
                expenses_dict["MEDICAL_SERVICES"]["accounted_and_paid"],
                expenses_dict["MEDICAL_SERVICES"]["paid_on"],
                expenses_dict["MEDICAL_SERVICES"]["not_paid"],
            ],
            [
                "Outros serviços de terceiros",
                expenses_dict["OTHER_THIRD_PARTY"]["accounted_on"],
                expenses_dict["OTHER_THIRD_PARTY"]["not_accounted"],
                expenses_dict["OTHER_THIRD_PARTY"]["accounted_and_paid"],
                expenses_dict["OTHER_THIRD_PARTY"]["paid_on"],
                expenses_dict["OTHER_THIRD_PARTY"]["not_paid"],
            ],
            [
                "Locação de imóveis",
                expenses_dict["REAL_STATE"]["accounted_on"],
                expenses_dict["REAL_STATE"]["not_accounted"],
                expenses_dict["REAL_STATE"]["accounted_and_paid"],
                expenses_dict["REAL_STATE"]["paid_on"],
                expenses_dict["REAL_STATE"]["not_paid"],
            ],
            [
                "Locações diversas",
                expenses_dict["MISCELLANEOUS"]["accounted_on"],
                expenses_dict["MISCELLANEOUS"]["not_accounted"],
                expenses_dict["MISCELLANEOUS"]["accounted_and_paid"],
                expenses_dict["MISCELLANEOUS"]["paid_on"],
                expenses_dict["MISCELLANEOUS"]["not_paid"],
            ],
            [
                "Utilidades públicas (7)",
                expenses_dict["PUBLIC_UTILITIES"]["accounted_on"],
                expenses_dict["PUBLIC_UTILITIES"]["not_accounted"],
                expenses_dict["PUBLIC_UTILITIES"]["accounted_and_paid"],
                expenses_dict["PUBLIC_UTILITIES"]["paid_on"],
                expenses_dict["PUBLIC_UTILITIES"]["not_paid"],
            ],
            [
                "Combustível",
                expenses_dict["FUEL"]["accounted_on"],
                expenses_dict["FUEL"]["not_accounted"],
                expenses_dict["FUEL"]["accounted_and_paid"],
                expenses_dict["FUEL"]["paid_on"],
                expenses_dict["FUEL"]["not_paid"],
            ],
            [
                "Bens e materiais permanentes",
                expenses_dict["PERMANENT_GOODS"]["accounted_on"],
                expenses_dict["PERMANENT_GOODS"]["not_accounted"],
                expenses_dict["PERMANENT_GOODS"]["accounted_and_paid"],
                expenses_dict["PERMANENT_GOODS"]["paid_on"],
                expenses_dict["PERMANENT_GOODS"]["not_paid"],
            ],
            [
                "Obras",
                expenses_dict["WORKS"]["accounted_on"],
                expenses_dict["WORKS"]["not_accounted"],
                expenses_dict["WORKS"]["accounted_and_paid"],
                expenses_dict["WORKS"]["paid_on"],
                expenses_dict["WORKS"]["not_paid"],
            ],
            [
                "Despesas financeiras e bancárias",
                expenses_dict["FINANCIAL_AND_BANKING"]["accounted_on"],
                expenses_dict["FINANCIAL_AND_BANKING"]["not_accounted"],
                expenses_dict["FINANCIAL_AND_BANKING"]["accounted_and_paid"],
                expenses_dict["FINANCIAL_AND_BANKING"]["paid_on"],
                expenses_dict["FINANCIAL_AND_BANKING"]["not_paid"],
            ],
            [
                "Outras despesas",
                expenses_dict["OTHER_EXPENSES"]["accounted_on"],
                expenses_dict["OTHER_EXPENSES"]["not_accounted"],
                expenses_dict["OTHER_EXPENSES"]["accounted_and_paid"],
                expenses_dict["OTHER_EXPENSES"]["paid_on"],
                expenses_dict["OTHER_EXPENSES"]["not_paid"],
            ],
        ]

        line_total = [
            "Total",
            expenses_dict["TOTAL"]["accounted_on"],
            expenses_dict["TOTAL"]["not_accounted"],
            expenses_dict["TOTAL"]["accounted_and_paid"],
            expenses_dict["TOTAL"]["paid_on"],
            expenses_dict["TOTAL"]["not_paid"],
        ]

        col_widths = [40, 30, 30, 30, 30, 30]  # Total: 190
        font = FontFace("FreeSans", "B", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)

        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            header = table.row()
            for text in headers:
                header.cell(text=text, align="C")
            if table_data != []:
                self.pdf.set_font("FreeSans", "", 7)
                for item in table_data:
                    body = table.row()
                    for id, text in enumerate(item):
                        if id == 0:
                            text_align = "L"
                        else:
                            text_align = "R"
                        body.cell(text=text, align=text_align)
            self.pdf.set_font("FreeSans", "B", 7)
            total = table.row()
            for id, text in enumerate(line_total):
                if id == 0:
                    text_align = "L"
                else:
                    text_align = "R"
                total.cell(text=text, align=text_align)

    def _draw_expenses_footer(self):
        self._set_font()
        self.pdf.cell(
            text="(4) Verba: Federal, Estadual, Municipal e Recursos Próprios, devendo ser elaborado um anexo para cada fonte de recurso.",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="(5) Salários, encargos e benefícios.",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="(6) Autônomos e pessoa jurídica.",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="(7) Energia elétrica, água e esgoto, gás, telefone e internet.",
            h=self.default_cell_height,
        )
        self.pdf.ln(5)
        self.pdf.multi_cell(
            190,
            text="(8) No rol exemplificativo incluir também as aquisições e os compromissos assumidos que não são classificados contabilmente como DESPESAS, como, por exemplo, aquisição de bens permanentes.",
            h=3,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(w=190, text="", h=1)  # It works, please do not erase
        self.pdf.ln()
        self.pdf.multi_cell(
            190,
            text="(9) Quando a diferença entre a Coluna DESPESAS CONTABILIZADAS NESTE EXERCÍCIO e a Coluna DESPESAS CONTABILIZADAS NESTE EXERCÍCIO E PAGAS NESTE EXERCÍCIO for decorrente de descontos obtidos ou pagamento de multa por atraso, o resultado não deve aparecer na coluna DESPESAS CONTABILIZADAS NESTE EXERCÍCIO A PAGAR EM EXERCÍCIOS SEGUINTES, uma vez que tais descontos ou multas são contabilizados em contas de receitas ou despesas. Assim sendo deverá se indicado como nota de rodapé os valores e as respectivas contas de receitas e despesas.",
            h=4,
            new_x=XPos.LMARGIN,
        )
        self.pdf.ln(7)
        self.pdf.cell(
            text="(*) Apenas para entidades da área da Saúde.",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)

    def _draw_financial_table(self):
        self.pdf.ln(7)
        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            190,
            h=self.default_cell_height,
            text="DEMONSTRATIVO DO SALDO FINANCEIRO DO EXERCÍCIO",
            border=1,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        expenses_dict = categorize_expenses(
            self.contract, self.start_date, self.end_date, inclusive_bounds=True
        )
        non_planned_paid_expenses_sum = self.expense_queryset.filter(
            planned=False
        ).aggregate(sum=Sum("value"))["sum"] or Decimal("0.00")

        j_value = expenses_dict["TOTAL"]["paid_on"]
        k_value = self.sum_items_a_to_d - (j_value - self.own_resources)
        l_value = non_planned_paid_expenses_sum
        m_value = k_value - l_value

        table_data = [
            [
                "(G) TOTAL DE RECURSOS DISPONÍVEL NO EXERCÍCIO",
                f"{format_into_brazilian_currency(self.contract.total_value)}",
            ],
            [
                "(J) DESPESAS PAGAS NO EXERCÍCIO (H+I)",
                format_into_brazilian_currency(j_value),
            ],
            [
                "(K) RECURSO PÚBLICO NÃO APLICADO [E - (J - F)]",
                format_into_brazilian_currency(k_value),
            ],
            [
                "(L) VALOR DEVOLVIDO AO ÓRGÃO PÚBLICO",
                format_into_brazilian_currency(l_value),
            ],
            [
                "(M) VALOR AUTORIZADO PARA APLICAÇÃO NO EXERCÍCIO SEGUINTE (K - L)",
                format_into_brazilian_currency(m_value),
            ],
        ]

        col_widths = [160, 30]  # Total: 190
        font = FontFace("FreeSans", "", 7)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            self.pdf.set_font("FreeSans", "", 7)
            for item in table_data:
                body = table.row()
                for id, text in enumerate(item):
                    if id == 0:
                        text_align = "L"
                    else:
                        text_align = "R"
                    body.cell(text=text, align=text_align)

    def _draw_last_informations(self):
        self.pdf.ln(7)
        self._set_font()
        self.pdf.multi_cell(
            text="Declaro(amos), na qualidade de responsável(is) pela entidade supra epigrafada, sob as penas da Lei, que a despesa relacionada comprova a exata aplicação dos recursos recebidos para os fins indicados, conforme programa de trabalho aprovado, proposto ao Órgão Público Contratante.",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=4,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(9)
        self.pdf.multi_cell(
            text="**LOCAL:**",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=4,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(4)
        self.pdf.multi_cell(
            text="**DATA:**",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=4,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(8)
        self.pdf.multi_cell(
            text="**Responsáveis pela Contratada:**",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=4,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        table_data = []
        table_data.append(
            [
                "",
                "",
                " ",
                f"Nome: {self.contract.supervision_autority.get_full_name()}",
            ]
        )
        (
            table_data.append(
                [
                    "",
                    "",
                    " ",
                    f"Papel: {self.contract.supervision_autority.position}",
                ]
            ),
        )
        table_data.append(
            [
                "",
                "",
                " ",
                f"{document_mask(str(self.contract.supervision_autority.cpf))}",
            ]
        )

        col_widths = [1, 2, 2, 185]  # Total de 190
        font = FontFace("FreeSans", "")
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="L",
            markdown=True,
            col_widths=col_widths,
        ) as table:
            for item in table_data:
                data = table.row()
                for id, text in enumerate(item):
                    if id == 1:
                        self.pdf.set_fill_color(220, 220, 220)
                    else:
                        self.pdf.set_fill_color(255, 255, 255)
                    data.cell(text=text, align="L", border=0)
