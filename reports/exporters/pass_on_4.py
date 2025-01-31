from dataclasses import dataclass
from datetime import datetime

from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from reports.exporters.commons.exporters import BasePdf


@dataclass
class PassOn4PDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self, contract):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.set_font("Helvetica", "", 8)
        self.pdf = pdf
        self.contract = contract

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def handle(self):
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
        self.__set_helvetica_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "ANEXO RP-04 - REPASSES AO TERCEIRO SETOR",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=10, bold=False)
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
        self.__set_helvetica_font(font_size=8)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.pdf.cell(
            text=f"**VALORES REPASSADOS DURANTE O EXERCÍCIO DE:** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
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
        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.ln()
        headers = [
            ("Contrato de Gestão Nº"),
            ("Beneficiário"),
            ("CNPJ"),
            ("Endereço"),
            ("Data"),
            ("Vigência até"),
            ("Valor Global do Ajuste"),
            ("Objeto"),
            ("Fonte"),
            ("Valor Repassado no Exercício"),
        ]
        table_data = []
        total_line = [
            ("Total:"),
            ("R$ 0,00"),
        ]

        col_widths = [15, 20, 10, 15, 15, 15, 20, 30, 20, 20]
        font = FontFace("Helvetica", "B", size_pt=6)

        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            header = table.row()
            for datum_index, datum_text in enumerate(headers):
                header.cell(datum_text)
            if table_data != []:
                data = table.row()
                for datum_index, datum_text in enumerate(table_data):
                    data.cell(datum_text)

        col_widths = [178, 22]
        font = FontFace("Helvetica", "B", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            total = table.row()
            for datum_index, datum_text in enumerate(total_line):
                total.cell(datum_text)

        self.pdf.ln(10)

    def _draw_partner_table(self):
        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.ln()
        headers = [
            ("Termo de Parceria Nº"),
            ("Beneficiário"),
            ("CNPJ"),
            ("Endereço"),
            ("Data"),
            ("Vigência até"),
            ("Valor Global do Ajuste"),
            ("Objeto"),
            ("Fonte"),
            ("Valor Repassado no Exercício"),
        ]
        table_data = []
        total_line = [
            ("Total:"),
            ("R$ 0,00"),
        ]

        col_widths = [15, 20, 10, 15, 15, 15, 20, 30, 20, 20]
        font = FontFace("Helvetica", "B", size_pt=6)

        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            header = table.row()
            for datum_index, datum_text in enumerate(headers):
                header.cell(datum_text)
            if table_data != []:
                data = table.row()
                for datum_index, datum_text in enumerate(table_data):
                    data.cell(datum_text)

        col_widths = [178, 22]
        font = FontFace("Helvetica", "B", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            total = table.row()
            for datum_index, datum_text in enumerate(total_line):
                total.cell(datum_text)

        self.pdf.ln(10)

    def _draw_collaborator_table(self):
        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.ln()
        headers = [
            ("Termo de Colaboração Nº"),
            ("Beneficiário"),
            ("CNPJ"),
            ("Endereço"),
            ("Data"),
            ("Vigência até"),
            ("Valor Global do Ajuste"),
            ("Objeto"),
            ("Fonte"),
            ("Valor Repassado no Exercício"),
        ]
        table_data = [
            ("10/2023"),
            ("Associação Comunidade Varzina - Eco & Vida (Meio Ambiente)"),
            ("02.834.119/0001-95"),
            (
                "Rua Feres Sada, 82 - Loteamento Parque Empresarial São Luiz, Várzea Paulista - null, Brasil"
            ),
            ("26/09/2023"),
            ("26/09/2023"),
            ("R$ 1.538.185,32"),
            (
                "Executar a coleta de recicláveis no município de Várzea Paulista - SP, em acordo com a Política Nacional de Resíduos Sólidos (PNRS)"
            ),
            ("Consolidado de todas as fontes"),
            ("R$ 0,00"),
        ]
        total_line = [
            ("Total:"),
            ("R$ 0,00"),
        ]

        col_widths = [15, 20, 10, 15, 15, 15, 20, 30, 20, 20]
        font = FontFace("Helvetica", "B", size_pt=6)

        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            header = table.row()
            for datum_index, datum_text in enumerate(headers):
                header.cell(datum_text)
            if table_data != []:
                self.pdf.set_font("Helvetica", "", 5)
                data = table.row()
                for datum_index, datum_text in enumerate(table_data):
                    data.cell(datum_text)

        col_widths = [178, 22]
        font = FontFace("Helvetica", "B", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            total = table.row()
            for datum_index, datum_text in enumerate(total_line):
                total.cell(datum_text)

        self.pdf.ln(10)

    def _draw_promotion_table(self):
        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.ln(3)
        headers = [
            ("Contrato de Fomento Nº"),
            ("Beneficiário"),
            ("CNPJ"),
            ("Endereço"),
            ("Data"),
            ("Vigência até"),
            ("Valor Global do Ajuste"),
            ("Objeto"),
            ("Fonte"),
            ("Valor Repassado no Exercício"),
        ]
        table_data = []
        total_line = [
            ("Total:"),
            ("R$ 0,00"),
        ]

        col_widths = [15, 20, 10, 15, 15, 15, 20, 30, 20, 20]
        font = FontFace("Helvetica", "B", size_pt=6)

        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            header = table.row()
            for datum_index, datum_text in enumerate(headers):
                header.cell(datum_text)
            if table_data != []:
                data = table.row()
                for datum_index, datum_text in enumerate(table_data):
                    data.cell(datum_text)

        col_widths = [178, 22]
        font = FontFace("Helvetica", "B", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            total = table.row()
            for datum_index, datum_text in enumerate(total_line):
                total.cell(datum_text)

        self.pdf.ln(10)

    def _draw_agreement_table(self):
        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.ln()
        headers = [
            ("Convênio Nº"),
            ("Beneficiário"),
            ("CNPJ"),
            ("Endereço"),
            ("Data"),
            ("Vigência até"),
            ("Valor Global do Ajuste"),
            ("Objeto"),
            ("Fonte"),
            ("Valor Repassado no Exercício"),
        ]
        table_data = []
        total_line = [
            ("Total:"),
            ("R$ 0,00"),
        ]

        col_widths = [15, 20, 10, 15, 15, 15, 20, 30, 20, 20]
        font = FontFace("Helvetica", "B", size_pt=6)

        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            header = table.row()
            for datum_index, datum_text in enumerate(headers):
                header.cell(datum_text)
            if table_data != []:
                data = table.row()
                for datum_index, datum_text in enumerate(table_data):
                    data.cell(datum_text)

        col_widths = [178, 22]
        font = FontFace("Helvetica", "B", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            total = table.row()
            for datum_index, datum_text in enumerate(total_line):
                total.cell(datum_text)

        self.pdf.ln(self.default_cell_height)

    def _draw_concession_table(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="II - AUXÍLIOS, SUBVENÇÕES E/OU CONTRIBUIÇÕES PAGOS:",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(2)
        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.ln()
        headers = [
            ("Tipo da Concessão"),
            ("Beneficiário"),
            ("CNPJ"),
            ("Endereço"),
            ("Data"),
            ("Vigência até"),
            ("Valor Global do Ajuste"),
            ("Objeto"),
            ("Fonte"),
            ("Valor Repassado no Exercício"),
        ]
        table_data = []
        total_line = [
            ("Total:"),
            ("R$ 0,00"),
        ]

        col_widths = [15, 20, 10, 15, 15, 15, 20, 30, 20, 20]
        font = FontFace("Helvetica", "B", size_pt=6)

        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            header = table.row()
            for datum_index, datum_text in enumerate(headers):
                header.cell(datum_text)
            if table_data != []:
                data = table.row()
                for datum_index, datum_text in enumerate(table_data):
                    data.cell(datum_text)

        col_widths = [178, 22]
        font = FontFace("Helvetica", "B", size_pt=6)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="L",
            col_widths=col_widths,
        ) as table:
            total = table.row()
            for datum_index, datum_text in enumerate(total_line):
                total.cell(datum_text)

        self.pdf.ln(self.default_cell_height)
