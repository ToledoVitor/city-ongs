from dataclasses import dataclass
from datetime import datetime

from fpdf import XPos, YPos
from fpdf.fonts import FontFace
from commons.exporters import BasePdf


@dataclass
class PassOn6PDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(233, 234, 236)
        self.pdf = pdf

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
            "ANEXO RP-06 - DEMONSTRATIVO INTEGRAL DAS RECEITAS E DESPESAS \n (CONTRATO DE GESTÃO)",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=10, bold=False)
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_informations(self):
        self.pdf.cell(
            text="**Contratante:** Prefeitura Municipal de Várzea Paulista",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="**Contratada:** Associação Com unidade Varzina - Eco & Vida (Meio Ambiente)",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="**CNPJ**: 02.834.119/0001-95",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="**Endereço e CEP:** Rua Feres Sada 82 - Loteamento Parque Empresarial São Luís",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="**Responsáveis pela Organização Social:**",
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
            text="**Objeto do Contrato de Gestão:** Executar a coleta de recicláveis no município de Várzea Paulista - SP, em acordo com a Política Nacional de Resíduos Sólidos (PNRS)",
            markdown=True,
            h=self.default_cell_height,
            w=190,
            max_line_height=self.default_cell_height,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            text="**Exercício:** 01/11/2024 a 30/11/2024",
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
        table_data = [
            [
                "Bens e Materiais permanentes",
                "R$0,00",
            ],
            [
                "Combustível",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Despesas financeiras e bancárias",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Gêneros Alimentícios",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Locação de Imóveis",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Locações Diversas",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Material Médico e Hospitalar",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Medicamentos",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Obras",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Outras despesas",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
            [
                "Outros Materiais de Consumo",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
                "R$0,00",
            ],
        ]

        line_total = [
            "Total",
            "R$0,00",
            "R$0,00",
            "R$0,00",
            "R$0,00",
            "R$0,00",
        ]

        col_widths = [40, 30, 30, 30, 30, 30]  # Total: 190
        font = FontFace("Helvetica", "B", size_pt=8)
        (self.pdf.set_fill_color(255, 255, 255),)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
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
            self.pdf.set_font("Helvetica", "B", 8)
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
        font = FontFace("Helvetica", "B", size_pt=8)
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


if __name__ == "__main__":
    pdf = PassOn6PDFExporter().handle()
    pdf.output(f"rp6-{str(datetime.now().time())[0:8]}.pdf")
