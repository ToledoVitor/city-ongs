import copy
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Q
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense
from contracts.choices import NatureCategories
from reports.exporters.commons.exporters import BasePdf
from utils.formats import format_into_brazilian_currency


@dataclass
class PassOn8PDFExporter:
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
        self.__set_helvetica_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "ANEXO RP-08 - DEMONSTRATIVO INTEGRAL DAS RECEITAS E DESPESAS (TERMO DE PARCERIA)",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=10, bold=False)
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_informations(self):
        self.pdf.cell(
            text=f"**Órgão Público Parceiro:** {self.accountability.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Organização Social de Interesse Público:** {self.accountability.contract.organization.name}",
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
            text="**Responsáveis pela OSCIP:**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)

    def _draw_first_table(self):
        self.__set_helvetica_font(font_size=7, bold=True)
        table_data = [
            ["Nome", "Papel", "CPF"],
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
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text=f"**Objeto da Parceria:** {self.accountability.contract.objective}",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=self.default_cell_height,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        start = self.accountability.contract.start_of_vigency
        end = self.accountability.contract.end_of_vigency
        self.pdf.cell(
            text=f"**Exercício:** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
            markdown=True,
            h=self.default_cell_height,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            text="**Origem dos Recursos (1):** Consolidado de todas as fontes",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)

    def _draw_documents_table(self):
        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.ln()
        headers = ["DOCUMENTO", "DATA", "VIGÊNCIA", "VALOR - R$"]
        table_data = [
            [
                "Termo de Colaboração nº 10/2023",
                "26/09/2023",
                "26/09/2023 - 26/09/2024",
                "R$ 761.992,32",
            ],
            [
                "Aditamento Nº 1",
                "25/09/2024",
                "26/09/2024 - 25/09/2025",
                "R$ 776.193,00",
            ],
        ]

        col_widths = [75, 19, 65, 31]
        self.__set_helvetica_font(font_size=8, bold=True)

        for col_index, header in enumerate(headers):
            self.pdf.cell(
                col_widths[col_index],
                h=self.default_cell_height,
                text=header,
                border=1,
                align="C",
            )
        self.pdf.ln()

        self.__set_helvetica_font()
        for row in table_data:
            for col_index, col_text in enumerate(row):
                self.pdf.cell(
                    col_widths[col_index],
                    h=self.default_cell_height,
                    text=col_text,
                    border=1,
                    align="C",
                )
            self.pdf.ln()

    def _draw_header_resources_table(self):
        self.pdf.ln(7)

        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            190,
            h=self.default_cell_height,
            text="DEMONSTRATIVO DOS RECURSOS DISPONÍVEIS NO EXERCÍCIO",
            border=1,
            align="C",
        )
        self.pdf.ln(self.default_cell_height)

        headers = [
            "DATA PREVISTA PARA O REPASSE (2)",
            "VALORES PREVISTOS (R$)",
            "DATA DO REPASSE",
            "NÚMERO DO DOCUMENTO DE CRÉDITO",
            "VALORES REPASSADOS (R$)",
        ]
        table_data = [
            [
                "10/2024",
                "64.682,75",
                "05/11/2024",
                "552766000230001",
                "64.682,75",
            ],
        ]
        col_widths = [40, 35, 25, 50, 40]

        for col_index, header in enumerate(headers):
            x = self.pdf.get_x()
            y = self.pdf.get_y()
            self.pdf.multi_cell(col_widths[col_index], 4, header, border=1, align="C")
            self.pdf.set_xy(x + col_widths[col_index], y)
        self.pdf.ln(8)

        self.__set_helvetica_font()
        for row in table_data:
            for col_index, col_text in enumerate(row):
                if col_index == 4:
                    self.pdf.cell(
                        col_widths[col_index],
                        h=self.default_cell_height,
                        text=col_text,
                        border=1,
                        align="R",
                    )
                else:
                    self.pdf.cell(
                        col_widths[col_index],
                        h=self.default_cell_height,
                        text=col_text,
                        border=1,
                        align="C",
                    )
            self.pdf.ln()

        # Linha cinza
        self.pdf.cell(
            190, h=self.default_cell_height, text="", border=1, align="C", fill=True
        )
        self.pdf.ln(self.default_cell_height)

    def _draw_resources_table(self):
        extern_revenue_data = [
            ["(A) SALDO DO EXERCÍCIO ANTERIOR", "", "R$ 42.554,87"],
            ["(B) REPASSES PÚBLICOS NO EXERCÍCIO", "", "R$ 64.682,75"],
            [
                "(C) RECEITAS COM APLICAÇÕES FINANCEIRAS DOS REPASSES PÚBLICOS",
                "",
                "R$ 0,00",
            ],
            [
                "(D) OUTRAS RECEITAS DECORRENTES DA EXECUÇÃO DO AJUSTE (3)",
                "",
                "R$ 0,00",
            ],
            ["(E) TOTAL DE RECURSOS PÚBLICOS (A + B + C + D)", "", "R$ 107.237,62"],
            ["", "", ""],
        ]
        intern_revenue_data = [
            ["(F) RECURSOS PRÓPRIOS DA ENTIDADE PARCEIRA", "", "R$ 0,00"],
            [
                "(G) TOTAL DE RECURSOS DISPONÍVEIS NO EXERCÍCIO (E + F)",
                "",
                "R$ 107.237,62",
            ],
        ]

        self.__set_helvetica_font()
        col_widths = [100, 50, 40]

        for row in extern_revenue_data:
            for col_index, col_text in enumerate(row):
                if col_index == 2:
                    self.pdf.cell(
                        col_widths[col_index],
                        h=self.default_cell_height,
                        text=col_text,
                        border=1,
                        align="R",
                    )
                else:
                    self.pdf.cell(
                        col_widths[col_index],
                        h=self.default_cell_height,
                        text=col_text,
                        border=1,
                        align="L",
                    )
            self.pdf.ln()

        for row_index, row in enumerate(intern_revenue_data):
            for col_index, col_text in enumerate(row):
                if col_index == 2:
                    self.pdf.cell(
                        col_widths[col_index],
                        h=self.default_cell_height,
                        text=col_text,
                        border=1,
                        align="R",
                    )
                else:
                    self.pdf.cell(
                        col_widths[col_index],
                        h=self.default_cell_height,
                        text=col_text,
                        border=1,
                        align="L",
                    )
            if row_index != len(intern_revenue_data) - 1:
                self.pdf.ln()

    def _draw_resources_footer(self):
        self.pdf.ln(self.default_cell_height)
        self.__set_helvetica_font()
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
            text="O(s) signatário(s), na qualidade de representante(s) da Associação Comunidade Varzina - Eco & Vida (Meio Ambiente) vem indicar, na forma abaixo detalhada, as despesas incorridas e pagas no exerício 01/01/2025 a 31/12/2025 bem como as despesas a pagar no exercício seguinte.",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=4,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        self.pdf.ln(7)
        self.__set_helvetica_font(font_size=8, bold=True)
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
        expenses_dict = self.__categorize_expenses()
        expenses_dict = self.__convert_decimal_to_brl(expenses_dict)

        table_data = [
            [
                "Bens e Materiais permanentes",
                expenses_dict["PERMANENT_GOODS"]["accounted_on"],
                expenses_dict["PERMANENT_GOODS"]["not_accounted"],
                expenses_dict["PERMANENT_GOODS"]["accounted_and_paid"],
                expenses_dict["PERMANENT_GOODS"]["paid_on"],
                expenses_dict["PERMANENT_GOODS"]["not_paid"],
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
                "Despesas financeiras e bancárias",
                expenses_dict["FINANCIAL_AND_BANKING"]["accounted_on"],
                expenses_dict["FINANCIAL_AND_BANKING"]["not_accounted"],
                expenses_dict["FINANCIAL_AND_BANKING"]["accounted_and_paid"],
                expenses_dict["FINANCIAL_AND_BANKING"]["paid_on"],
                expenses_dict["FINANCIAL_AND_BANKING"]["not_paid"],
            ],
            [
                "Gêneros Alimentícios",
                expenses_dict["FOODSTUFFS"]["accounted_on"],
                expenses_dict["FOODSTUFFS"]["not_accounted"],
                expenses_dict["FOODSTUFFS"]["accounted_and_paid"],
                expenses_dict["FOODSTUFFS"]["paid_on"],
                expenses_dict["FOODSTUFFS"]["not_paid"],
            ],
            [
                "Locação de Imóveis",
                expenses_dict["REAL_STATE"]["accounted_on"],
                expenses_dict["REAL_STATE"]["not_accounted"],
                expenses_dict["REAL_STATE"]["accounted_and_paid"],
                expenses_dict["REAL_STATE"]["paid_on"],
                expenses_dict["REAL_STATE"]["not_paid"],
            ],
            [
                "Locações Diversas",
                expenses_dict["MISCELLANEOUS"]["accounted_on"],
                expenses_dict["MISCELLANEOUS"]["not_accounted"],
                expenses_dict["MISCELLANEOUS"]["accounted_and_paid"],
                expenses_dict["MISCELLANEOUS"]["paid_on"],
                expenses_dict["MISCELLANEOUS"]["not_paid"],
            ],
            [
                "Material Médico e Hospitalar",
                expenses_dict["MEDICAL_AND_HOSPITAL"]["accounted_on"],
                expenses_dict["MEDICAL_AND_HOSPITAL"]["not_accounted"],
                expenses_dict["MEDICAL_AND_HOSPITAL"]["accounted_and_paid"],
                expenses_dict["MEDICAL_AND_HOSPITAL"]["paid_on"],
                expenses_dict["MEDICAL_AND_HOSPITAL"]["not_paid"],
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
                "Obras",
                expenses_dict["WORKS"]["accounted_on"],
                expenses_dict["WORKS"]["not_accounted"],
                expenses_dict["WORKS"]["accounted_and_paid"],
                expenses_dict["WORKS"]["paid_on"],
                expenses_dict["WORKS"]["not_paid"],
            ],
            [
                "Outras despesas",
                expenses_dict["OTHER_EXPENSES"]["accounted_on"],
                expenses_dict["OTHER_EXPENSES"]["not_accounted"],
                expenses_dict["OTHER_EXPENSES"]["accounted_and_paid"],
                expenses_dict["OTHER_EXPENSES"]["paid_on"],
                expenses_dict["OTHER_EXPENSES"]["not_paid"],
            ],
            [
                "Outros Materiais de Consumo",
                expenses_dict["OTHER_CONSUMABLES"]["accounted_on"],
                expenses_dict["OTHER_CONSUMABLES"]["not_accounted"],
                expenses_dict["OTHER_CONSUMABLES"]["accounted_and_paid"],
                expenses_dict["OTHER_CONSUMABLES"]["paid_on"],
                expenses_dict["OTHER_CONSUMABLES"]["not_paid"],
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
        font = FontFace("Helvetica", "B", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)

        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            header = table.row()
            for text in headers:
                header.cell(text)
            if table_data != []:
                self.pdf.set_font("Helvetica", "", 7)
                for item in table_data:
                    body = table.row()
                    for text in item:
                        body.cell(text)
            self.pdf.set_font("Helvetica", "B", 7)
            total = table.row()
            for text in line_total:
                total.cell(text)

    def _draw_expenses_footer(self):
        self.__set_helvetica_font()
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
        self.pdf.ln(4)
        self.pdf.cell(
            text="(8) No rol exemplificativo incluir também as aquisições e os compromissos assumidos que não são classificados contabilmente como DESPESAS, como, por exemplo, aquisição de bens permanentes.",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="(9) Quando a diferença entre a Coluna DESPESAS CONTABILIZADAS NESTE EXERCÍCIO e a Coluna DESPESAS CONTABILIZADAS NESTE EXERCÍCIO E PAGAS NESTE EXERCÍCIO for decorrente de descontos obtidos ou pagamento de multa por atraso, o resultado não deve aparecer na coluna DESPESAS CONTABILIZADAS NESTE EXERCÍCIO A PAGAR EM EXERCÍCIOS SEGUINTES, uma vez que tais descontos ou multas são contabilizados em contas de receitas ou despesas. Assim sendo deverá se indicado como nota de rodapé os valores e as respectivas contas de receitas e despesas.",
            h=self.default_cell_height,
        )
        self.pdf.ln(7)
        self.pdf.cell(
            text="(*) Apenas para entidades da área da Saúde.",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)

    def _draw_financial_table(self):
        self.pdf.ln(7)
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            190,
            h=self.default_cell_height,
            text="DEMONSTRATIVO DO SALDO FINANCEIRO DO EXERCÍCIO",
            border=1,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        table_data = [
            [
                "(G) TOTAL DE RECURSOS DISPONÍVEL NO EXERCÍCIO",
                "R$R$ 38.343,81",
            ],
            [
                "(J) DESPESAS PAGAS NO EXERCÍCIO (H+I)",
                "R$0,00",
            ],
            [
                "(K) RECURSO PÚBLICO NÃO APLICADO [E - (J - F)]",
                "R$ 38.343,81",
            ],
            [
                "(L) VALOR DEVOLVIDO AO ÓRGÃO PÚBLICO",
                "R$0,00",
            ],
            [
                "(M) VALOR AUTORIZADO PARA APLICAÇÃO NO EXERCÍCIO SEGUINTE (K - L)",
                "R$ 38.343,81",
            ],
        ]

        col_widths = [160, 30]  # Total: 190
        font = FontFace("Helvetica", "", 7)
        # self.pdf.set_fill_color(255, 255, 255),
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            self.pdf.set_font("Helvetica", "", 7)
            for item in table_data:
                body = table.row()
                for text in item:
                    body.cell(text)

    def _draw_last_informations(self):
        self.pdf.ln(7)
        self.__set_helvetica_font()
        self.pdf.multi_cell(
            text="Declaro(amos), na qualidade de responsável(is) pela entidade supra epigrafada, sob as penas da Lei, que a despesa relacionada comprova a exata aplicação dos recursos recebidos para os fins indicados, conforme programa de trabalho aprovado, proposto ao Órgão Público Parceiro.",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=4,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(9)
        self.pdf.cell(
            text="Prefeitura Municipal de Várzea Paulista, Quarta-feira, 15 de Janeiro de 2025",
            h=self.default_cell_height,
        )
        self.pdf.ln(7)

    def __categorize_expenses(self) -> dict:
        expenses = Expense.objects.filter(
            Q(accountability=self.accountability)
            | Q(item__contract=self.accountability.contract)
        )

        base_empty_dict = {
            "accounted_on": Decimal(0.00),
            "not_accounted": Decimal(0.00),
            "accounted_and_paid": Decimal(0.00),
            "paid_on": Decimal(0.00),
            "not_paid": Decimal(0.00),
        }
        categorized_expenses = {
            "PERMANENT_GOODS": copy.deepcopy(base_empty_dict),
            "FUEL": copy.deepcopy(base_empty_dict),
            "FINANCIAL_AND_BANKING": copy.deepcopy(base_empty_dict),
            "FOODSTUFFS": copy.deepcopy(base_empty_dict),
            "REAL_STATE": copy.deepcopy(base_empty_dict),
            "MISCELLANEOUS": copy.deepcopy(base_empty_dict),
            "MEDICAL_AND_HOSPITAL": copy.deepcopy(base_empty_dict),
            "MEDICINES": copy.deepcopy(base_empty_dict),
            "WORKS": copy.deepcopy(base_empty_dict),
            "OTHER_EXPENSES": copy.deepcopy(base_empty_dict),
            "OTHER_CONSUMABLES": copy.deepcopy(base_empty_dict),
            "TOTAL": copy.deepcopy(base_empty_dict),
        }

        for expense in expenses:
            expense_category = self.__get_expense_nature_category(expense=expense)
            if not expense_category:
                continue

            accounted_on_period = (
                expense.competency
                and self.start_date.date() < expense.competency < self.end_date.date()
            )
            paid_on_period = (
                expense.due_date
                and self.start_date.date() < expense.due_date < self.end_date.date()
            )

            if paid_on_period and accounted_on_period:
                categorized_expenses[expense_category]["accounted_and_paid"] += (
                    expense.value
                )
                categorized_expenses[expense_category]["accounted_on"] += expense.value
                categorized_expenses[expense_category]["paid_on"] += expense.value

                categorized_expenses["TOTAL"]["accounted_and_paid"] += expense.value
                categorized_expenses["TOTAL"]["paid_on"] += expense.value
                categorized_expenses["TOTAL"]["accounted_on"] += expense.value

            elif paid_on_period and not accounted_on_period:
                categorized_expenses[expense_category]["not_accounted"] += expense.value
                categorized_expenses[expense_category]["paid_on"] += expense.value

                categorized_expenses["TOTAL"]["not_accounted"] += expense.value
                categorized_expenses["TOTAL"]["paid_on"] += expense.value

            elif not paid_on_period and accounted_on_period:
                categorized_expenses[expense_category]["not_paid"] += expense.value
                categorized_expenses[expense_category]["accounted_on"] += expense.value

                categorized_expenses["TOTAL"]["accounted_on"] += expense.value
                categorized_expenses["TOTAL"]["not_paid"] += expense.value

        return categorized_expenses

    def __get_expense_nature_category(self, expense: Expense):
        if not expense.nature:
            return None

        if expense.nature in NatureCategories.PERMANENT_GOODS:
            return "PERMANENT_GOODS"

        if expense.nature in NatureCategories.FUEL:
            return "FUEL"

        if expense.nature in NatureCategories.FINANCIAL_AND_BANKING:
            return "FINANCIAL_AND_BANKING"

        if expense.nature in NatureCategories.FOODSTUFFS:
            return "FOODSTUFFS"

        if expense.nature in NatureCategories.REAL_STATE:
            return "REAL_STATE"

        if expense.nature in NatureCategories.MISCELLANEOUS:
            return "MISCELLANEOUS"

        if expense.nature in NatureCategories.MEDICAL_AND_HOSPITAL:
            return "MEDICAL_AND_HOSPITAL"

        if expense.nature in NatureCategories.MEDICINES:
            return "MEDICINES"

        if expense.nature in NatureCategories.WORKS:
            return "WORKS"

        if expense.nature in NatureCategories.OTHER_EXPENSES:
            return "OTHER_EXPENSES"

        if expense.nature in NatureCategories.OTHER_CONSUMABLES:
            return "OTHER_CONSUMABLES"

        return None

    def __convert_decimal_to_brl(self, expenses_dict):
        for key, value in expenses_dict.items():
            if isinstance(value, Decimal):
                expenses_dict[key] = format_into_brazilian_currency(value)
            elif isinstance(value, dict):
                self.__convert_decimal_to_brl(value)

        return expenses_dict
