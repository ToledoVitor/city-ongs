from dataclasses import dataclass
from datetime import datetime

from fpdf import XPos, YPos
from commons.exporters import BasePdf


@dataclass
class PassOn10PDFExporter:
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
        self._draw_resources_table()
        self._draw_resume_table()
        self._draw_table_footer()

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
            text="**Órgão Público:** Prefeitura Municipal de Várzea Paulista",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="**Organização da Sociedade Civil:** Associação Com unidade Varzina - Eco & Vida (Meio Ambiente)",
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
            text="**Responsáveis pela OSC:**", markdown=True, h=self.default_cell_height
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
        self.pdf.ln(3)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="**Objeto da Parceria:** Executar a coleta de recicláveis no município de Várzea Paulista - SP",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="**Exercício:** 01/11/2024 a 30/11/2024",
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

    def _draw_resources_table(self):
        self.pdf.ln(6)

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

    def _draw_resume_table(self):
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

    def _draw_table_footer(self):
        self.pdf.ln(self.default_cell_height)
        self.__set_helvetica_font()
        self.pdf.cell(
            text="(1) Verba: Federal, Estadual ou Municipal, devendo ser elaborado um anexo para cada fonte de recurso.",
            h=self.default_cell_height,
        )
        self.pdf.ln(3)
        self.pdf.cell(
            text="(2) Incluir valores previstos no exercício anterior e repassados neste exercício.",
            h=self.default_cell_height,
        )
        self.pdf.ln(3)
        self.pdf.cell(
            text="(3) Receitas com estacionamento, aluguéis, entre outras.",
            h=self.default_cell_height,
        )

if __name__ == "__main__":
    pdf = PassOn10PDFExporter().handle()
    pdf.output(f"rp10-{str(datetime.now().time())[0:8]}.pdf")
