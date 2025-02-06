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
        # self._draw_form()
        # self._draw_table_I()
        # self._draw_signatories_notification()
        # self._draw_table_II()
        # self._draw_org_notification()
        # self._draw_table_III()
        # self._draw_observation()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_helvetica_font(font_size=9, bold=True)
        self.pdf.multi_cell(
            0,
            4,
            "DESPESAS REALIZADAS DO PERÍODO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_form(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            0,
            6,
            "ÓRGÃO CONCESSOR:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "TIPO DE CONCESSÃO: (1)",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "LEI AUTORIZADORA OU CONVÊNIO:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "OBJETO:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "EXERCÍCIO:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "ÓRGÃO BENEFICIÁRIO:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "CNPJ:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "ENDEREÇO E CEP:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "RESPONSÁVEL(IS) PELO ÓRGÃO:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "VALOR TOTAL RECEBIDO NO EXERCÍCIO: __(DEMONSTRAR POR FONTE DE RECURSO)__",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            markdown=True,
        )
        self.pdf.ln(10)

    def _draw_table_I(self):
        table_data = [
            ["", "VALORES R$"],
            ["SALDO DO EXERCÍCIO ANTERIOR", "R$"],
            ["REPASSADOS NO EXERCÍCIO (DATA)", ""],
            ["__(INDICAR AS FONTES DO RECURSO)__", "R$"],
            ["", "R$"],
            ["", "R$"],
            ["", "R$"],
            ["RECEITA COM APLICAÇÕES FINANCEIRAS DOS REPASSES PÚBLICOS", "R$"],
            ["TOTAL", "R$"],
            ["RECURSOS PRÓPRIOS APLICADOS PELO BENEFICIÁRIO", "R$"],
        ]

        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "I - DEMONSTRATIVO DOS REPASSES PÚBLICOS RECEBIDOS",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            border=1,
        )

        self.default_cell_height
        col_widths = [150, 40]  # Total: 190
        font = FontFace("Helvetica", "B", size_pt=8)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            for item in table_data:
                body = table.row()
                for text in item:
                    body.cell(text)

        self.pdf.ln(15)

    def _draw_signatories_notification(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.multi_cell(
            190,
            5,
            "O(S) SIGNATÁRIO(S), NA QUALIDADE DE REPRESENTANTE(S) DO ÓRGÃO PÚBLICO BENEFICIÁRIO VEM INDICAR, NA FORMA ABAIXO DETALHADA, A APLICAÇÃO DOS RECURSOS RECEBIDOS NO EXERCÍCIO SUPRAMENCIONADO, NA IMPORTÂNCIA TOTAL DE \n R$ ______________ (POR EXTENSO).",
            align="J",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

    def _draw_table_II(self):
        up_table_data = [
            [
                "DATA DO DOCUMENTO",
                "ESPECIFICAÇÃO DO DOCUMENTO FISCAL (2)",
                "CREDOR",
                "NATUREZA DA DESPESA RESUMIDAMENTE",
                "VALORES R$",
            ],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
        ]
        down_table_data = [
            ["TOTAL DAS DESPESAS", ""],
            ["RECURSO SO REPASSE NÃO APLICADO", ""],
            ["VALOR DEVOLVIDO AO ÓRGÃO CONCESSOR", ""],
            ["VALOR AUTORIZADO PARA APLICAÇÃO NO EXERCÍCIO SEGUINTE", ""],
        ]

        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "II - DEMONSTRATIVO DAS DESPESAS REALIZADAS COM RECURSOS DO REPASSE",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            border=1,
        )

        self.default_cell_height
        col_widths = [38, 38, 38, 38, 38]  # Total: 190
        font = FontFace("Helvetica", "B", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            for item in up_table_data:
                up_data = table.row()
                for text in item:
                    up_data.cell(text)

        col_widths = [152, 38]  # Total: 190
        font = FontFace("Helvetica", "B", size_pt=8)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            for item in down_table_data:
                down_data = table.row()
                for text in item:
                    down_data.cell(text)

        self.pdf.ln(10)

    def _draw_org_notification(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.multi_cell(
            190,
            5,
            "DECLARAMOS, NA QUALIDADE DE RESPONSÁVEIS PELO ÓRGÃO BENEFICIÁRIO SUPRA EPIGRAFADO, SOB AS PENAS DA LEI, QUE A DESPESA RELACIONADA, EXAMINADA PELO CONTROLE INTERNO, COMPROVA A EXATA APLICAÇÃO DOS RECURSOS RECEBIDOS PARA OS FINS INDICADOS, CONFORME PROGRAMA DE TRABALHO APROVADO, PROPOSTO AO ÓRGÃO CONCESSOR.",
            align="J",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(15)

    def _draw_table_III(self):
        table_data = [
            [
                "AJUSTE Nº",
                "DATA",
                "CONTRATADO / CNPJ",
                "OBJETO RESUMIDO",
                "LICITAÇÃO Nº(4)",
                "FONTE (5)",
                "VALOR GLOBAL DO AJUSTE",
            ],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
            ["", "", "", "", "", "", ""],
        ]

        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "III - AJUSTES VINCULADOS ÀS DESPESAS CUSTEADAS COM RECURSOS DO REPASSE (3)",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            border=1,
        )

        self.default_cell_height
        col_widths = [27, 25, 30, 27, 27, 27, 27]  # Total: 190
        font = FontFace("Helvetica", "B", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)
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
                    data.cell(text)

        self.pdf.ln(3)

    def _draw_observation(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            0,
            0,
            "LOCAL e DATA:",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(6)
        self.pdf.multi_cell(
            0,
            0,
            f"RESPONSÁVEL: NOME, CARGO E ASSINATURA",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(8)
        self.pdf.cell(190, 10, "", ln=True, align="C")
        self.pdf.line(
            self.pdf.get_x(), self.pdf.get_y(), self.pdf.get_x() + 190, self.pdf.get_y()
        )
        self.pdf.ln(3)
        self.__set_helvetica_font(font_size=7, bold=False)
        self.pdf.cell(
            0,
            0,
            "(1) convênio ou auxílio/subvenção ou contribuição.",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(self.default_cell_height)
        self.pdf.cell(
            0,
            0,
            "(2) notas fiscais e recibos",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(self.default_cell_height)
        self.pdf.cell(
            0,
            0,
            "(3) contrato; contrato de gestão; termo de parceria; termo de colaboração; termo de fomento; etc.",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(self.default_cell_height)
        self.pdf.cell(
            0,
            0,
            "(4) modalidade, ou, no caso de dispensa e/ou inexigibilidade, a base legal.",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(self.default_cell_height)
        self.pdf.cell(
            0,
            0,
            "(5) fonte de recursos: federal ou estadual.",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
