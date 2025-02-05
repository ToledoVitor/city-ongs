from dataclasses import dataclass
from datetime import datetime

from django.db.models import Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from contracts.choices import NatureCategories
from reports.exporters.commons.exporters import BasePdf
from utils.formats import format_into_brazilian_currency


@dataclass
class PassOn1PDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self, contract):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_fill_color(233, 234, 236)
        self.pdf = pdf
        self.contract = contract

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def handle(self):
        self._draw_header()
        self._draw_up_informations()
        self._draw_table()
        self._draw_down_informations()
        self._draw_observations()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
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
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            0,
            7,
            "EXERCÍCIO:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            0,
            "ÓRGÃO CONCESSOR:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(6)

    def _draw_table(self):
        data_up_header = ["", "", "", ""]
        data_header = ["", "", "", "", "", "", "", "", "", "", ""]
        data_body = [
            ["", "", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", "", "", ""],
        ]
        data_footer = ["Total", ""]

        self.pdf.ln(10)
        sub_col_widths = [53, 34, 34, 69]  # Total: 190
        font = FontFace("Helvetica", "", size_pt=6)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="C",
            col_widths=sub_col_widths,
            repeat_headings=0,
        ) as table:
            up_header = table.row()
            for text in data_up_header:
                up_header.cell(text)
        
        self.default_cell_height
        col_widths = [17, 19, 17, 17, 17, 17, 17, 18, 17, 17, 17]  # Total: 190   
        font = FontFace("Helvetica", "", size_pt=6)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            header = table.row()
            for text in data_header:
                header.cell(text)

            if data_body != []:
                self.pdf.set_font("Helvetica", "", 6)
                for item in data_body:
                    body = table.row()
                    for text in item:
                        body.cell(text)

        self.default_cell_height
        footer_col_widths = [160, 30]  # Total: 190
        font = FontFace("Helvetica", "B", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=6,
            align="R",
            col_widths=footer_col_widths,
            repeat_headings=0,
        ) as table:
            total = table.row()
            for text in data_footer:
                total.cell(text, align="R")
        self.pdf.ln(10)

    def _draw_down_informations(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            0,
            0,
            "LOCAL e DATA:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(20)
        self.pdf.multi_cell(
            0,
            0,
            f"RESPONSÁVEL:** {self.contract.supervision_autority.get_full_name()}, {self.contract.supervision_autority.position} e assinatura**",  # TODO
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            markdown=True
        )
        self.pdf.ln(8)
        self.pdf.cell(190, 10, "", ln=True, align="C")
        self.pdf.line(self.pdf.get_x(), self.pdf.get_y(), self.pdf.get_x() + 190, self.pdf.get_y())
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
