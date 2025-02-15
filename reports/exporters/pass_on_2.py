import copy
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense, Revenue
from bank.models import BankStatement
from contracts.choices import NatureCategories
from reports.exporters.commons.exporters import BasePdf
from utils.formats import format_into_brazilian_currency


@dataclass
class PassOn2PDFExporter:
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
        self.start_date = start_date - timedelta(days=365)
        self.end_date = end_date

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def __database_queries(self):
        self.checking_account = self.accountability.contract.checking_account
        self.investing_account = self.accountability.contract.investing_account

        self.statement_queryset = (
            BankStatement.objects.filter(
                Q(bank_account=self.checking_account)
                | Q(bank_account=self.investing_account)
            )
            .filter(
                Q(reference_month__gte=self.start_date.month, reference_year__gte=self.start_date.year)
                | Q(reference_month__lt=self.start_date.month, reference_year__gt=self.start_date.year)
            )
            .order_by("reference_year", "reference_month")
            .exclude(bank_account__isnull=True)
        )

        self.revenue_queryset = Revenue.objects.filter(
            Q(bank_account=self.checking_account)
            | Q(bank_account=self.investing_account)
        ).exclude(bank_account__isnull=True)

    def handle(self):
        self.__database_queries()
        self._draw_header()
        self._draw_form()
        self._draw_table_I()
        self._draw_signatories_notification()
        self._draw_table_II()
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
            "ANEXO RP-02 - REPASSES A ÓRGÃOS PÚBLICOS \n DEMONSTRATIVO INTEGRAL DE RECEITAS E DESPESAS",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_form(self):
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            0,
            6,
            text=f"**ÓRGÃO CONCESSOR:** {self.accountability.contract.organization.city_hall.name}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            f"**TIPO DE CONCESSÃO (1):** {self.accountability.contract.concession_type}",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "**LEI AUTORIZADORA OU CONVÊNIO:**",  # TODO não sei o que é.
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            text=f"**OBJETO DA PARCERIA:** {self.accountability.contract.objective}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        start = self.accountability.contract.start_of_vigency
        end = self.accountability.contract.end_of_vigency
        self.pdf.cell(
            text=f"**EXERCÍCIO:** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            text=f"**ÓRGÃO BENEFICIÁRIO:** {self.accountability.contract.organization.name}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        hired_company = self.accountability.contract.hired_company
        self.pdf.cell(
            0,
            6,
            f"**CNPJ:** {hired_company.cnpj}",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            text=f"**Endereço e CEP:** {hired_company.city}/{hired_company.uf} | {hired_company.street}, nº {hired_company.number} - {hired_company.district}",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            f"**RESPONSÁVEL(IS) PELO ÓRGÃO:**",  # TODO perguntar ao Felipe, quem seriam os responsáveis
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.default_cell_height
        self.pdf.cell(
            0,
            6,
            "**VALOR TOTAL RECEBIDO NO EXERCÍCIO.** __(DEMONSTRAR POR FONTE DE RECURSO)__",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            markdown=True,
        )
        self.pdf.ln(2)

    def _draw_table_I(self):
        opening_balance = self.statement_queryset.filter(
            reference_month=self.start_date.month,
            reference_year=self.start_date.year,          
        ).aggregate(Sum("opening_balance"))["opening_balance__sum"] or Decimal("0.00")
        
        closing_checking_account = self.statement_queryset.filter(
            reference_month=self.end_date.month,
            reference_year=self.end_date.year,
            bank_account=self.checking_account,         
        ).aggregate(Sum("closing_balance"))["closing_balance__sum"] or Decimal("0.00")
        
        closing_investing_account = self.statement_queryset.filter(
            reference_month=self.end_date.month,
            reference_year=self.end_date.year,
            bank_account=self.investing_account,           
        ).aggregate(Sum("closing_balance"))["closing_balance__sum"] or Decimal("0.00")

        closing_balance = closing_checking_account + closing_investing_account

        revenue_in_time = self.revenue_queryset.filter(
            receive_date__gte=self.start_date, receive_date__lte=self.end_date
        )
        self.revenue_total = Decimal("0.00")
    
        contract = self.accountability.contract
        table_data = [
            ["", format_into_brazilian_currency(contract.total_value)],
            [
                "SALDO DO EXERCÍCIO ANTERIOR",
                format_into_brazilian_currency(opening_balance),
            ],
            [
                "REPASSADOS NO EXERCÍCIO (DATA)",
                "",
            ],  # TODO perguntar ao Felipe/Ronaldo como receberia sem ser no exercício?
            ["__(INDICAR AS FONTES DO RECURSO)__", "R$"],
        ]

        for revenue in revenue_in_time:
            table_data.append(
                [
                    revenue.revenue_nature_label,
                    format_into_brazilian_currency(revenue.value),
                ]
            )
            self.revenue_total += revenue.value

        table_data.append(
            [
                "RECEITA COM APLICAÇÕES FINANCEIRAS DOS REPASSES PÚBLICOS",
                format_into_brazilian_currency(closing_investing_account),
            ]
        ) 
        table_data.append(
            ["TOTAL", format_into_brazilian_currency(closing_balance)]
        )  # adicionar tupla a cima
        table_data.append(
            [
                "RECURSOS PRÓPRIOS APLICADOS PELO BENEFICIÁRIO",
                format_into_brazilian_currency(closing_checking_account),
            ]
        )

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
        pass_on_queryt = self.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.PUBLIC_TRANSFER
        )
        
        up_table_data = [
            [
                "DATA DO DOCUMENTO",
                "ESPECIFICAÇÃO DO DOCUMENTO FISCAL (2)",
                "CREDOR",
                "NATUREZA DA DESPESA RESUMIDAMENTE",
                "VALORES R$",
            ],
        ]
        
        for revenue in pass_on_queryt:
            up_table_data.append(
                [
                    revenue.receive_date, 
                    "Perguntar ao Felipe/Ronaldo", 
                    "Perguntar ao Felipe/Ronaldo", 
                    "", 
                    ""
                ],
            )
                             
        down_table_data = [
            ["TOTAL DAS DESPESAS", ""],
            ["RECURSO DO REPASSE NÃO APLICADO", ""],
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
                    up_data.cell(text=text, align="C")

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
                    down_data.cell(text=text, align="C")

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
