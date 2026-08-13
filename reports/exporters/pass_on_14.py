import os
from datetime import date
from decimal import Decimal

from django.conf import settings
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense, Revenue
from reports.exporters.base import BasePDFExporter
from reports.exporters.commons.integral_statement import (
    build_revenue_summary,
    categorize_expenses,
)
from utils.formats import (
    document_mask,
    format_into_brazilian_currency,
    format_into_brazilian_date,
)

font_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSans.ttf")
font_bold_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSansBold.ttf")

# (rótulo exibido, chave em `categorize_expenses`) — mesmo agrupamento por
# natureza usado no "DEMONSTRATIVO DAS DESPESAS REALIZADAS" do RP-06/08/10/12,
# só que aqui cada categoria vira uma única linha "valor aplicado" em vez da
# quebra H/I/J: o modelo oficial do RP-14 não tem essa quebra.
_EXPENSE_CATEGORIES = (
    ("Recursos humanos (5)", "HUMAN_RESOURCES"),
    ("Recursos humanos (6)", "OTHER_HUMAN_RESOURCES"),
    ("Medicamentos", "MEDICINES"),
    ("Material médico e hospitalar (*)", "MEDICAL_AND_HOSPITAL"),
    ("Gêneros alimentícios", "FOODSTUFFS"),
    ("Outros materiais de consumo", "OTHER_CONSUMABLES"),
    ("Serviços médicos (*)", "MEDICAL_SERVICES"),
    ("Outros serviços de terceiros", "OTHER_THIRD_PARTY"),
    ("Locação de imóveis", "REAL_STATE"),
    ("Locações diversas", "MISCELLANEOUS"),
    ("Utilidades públicas (7)", "PUBLIC_UTILITIES"),
    ("Combustível", "FUEL"),
    ("Bens e materiais permanentes", "PERMANENT_GOODS"),
    ("Obras", "WORKS"),
    ("Despesas financeiras e bancárias", "FINANCIAL_AND_BANKING"),
    ("Outras despesas", "OTHER_EXPENSES"),
)


class PassOn14PDFExporter(BasePDFExporter):
    def __init__(self, contract, start_date, end_date):
        super().__init__()
        self.initialize_pdf(
            font_specs=[("", font_path), ("B", font_bold_path)],
            base_font_size=8,
            fill_color=(233, 234, 236),
        )
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date

    def __database_queries(self):
        summary = build_revenue_summary(self.contract, self.start_date, self.end_date)
        self.all_pass_on_values = summary.all_pass_on_values
        self.investment_income = summary.investment_income
        self.own_resources = summary.own_resources

        self.pass_on_queryset = summary.revenue_queryset.filter(
            revenue_nature=Revenue.Nature.PUBLIC_TRANSFER
        ).order_by("receive_date")

        self.expense_queryset = Expense.objects.filter(
            accountability__contract=self.contract,
            liquidation__gte=self.start_date,
            liquidation__lte=self.end_date,
        ).select_related("favored")
        self.paid_expenses = self.expense_queryset.filter(paid=True).order_by(
            "liquidation"
        )

        self.categorized_expenses = categorize_expenses(
            self.contract, self.start_date, self.end_date, inclusive_bounds=True
        )

    def handle(self):
        self.__database_queries()
        self._draw_header()
        self._draw_form()
        self._draw_table_received()
        self._draw_signatories_notification()
        self._draw_table_expenses()
        self._draw_table_expense_list()
        self._draw_org_notification()
        self._draw_observation()

        return self.pdf

    def _draw_header(self):
        self._set_font(font_size=9, bold=True)
        self.pdf.multi_cell(
            0,
            4,
            (
                "ANEXO RP-14 - REPASSES AO TERCEIRO SETOR \n DEMONSTRATIVO INTEGRAL DAS "
                "RECEITAS E DESPESAS \n AUXÍLIOS / SUBVENÇÕES / CONTRIBUIÇÕES"
            ),
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.set_y(self.pdf.get_y() + 10)

    def _draw_form(self):
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            0,
            self.default_cell_height,
            text=f"**ÓRGÃO CONCESSOR:** {self.contract.organization.city_hall.name}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            0,
            self.default_cell_height,
            f"**TIPO DE CONCESSÃO (1):** {self.contract.get_concession_type_display()}",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            0,
            self.default_cell_height,
            f"**LEI AUTORIZADORA:** {self.contract.law_num or '—'}",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            0,
            self.default_cell_height,
            text=f"**OBJETO:** {self.contract.objective}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.pdf.cell(
            0,
            self.default_cell_height,
            text=f"**EXERCÍCIO:** {format_into_brazilian_date(start)} a {format_into_brazilian_date(end)}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            0,
            self.default_cell_height,
            text=f"**ENTIDADE BENEFICIÁRIA:** {self.contract.organization.name}",
            markdown=True,
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        hired_company = self.contract.hired_company
        self.pdf.cell(
            0,
            self.default_cell_height,
            f"**CNPJ:** {hired_company.cnpj}",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            0,
            self.default_cell_height,
            text=(
                "**Endereço e CEP:** "
                f"{hired_company.city}/{hired_company.uf} | {hired_company.street}, "
                f"nº {hired_company.number} - {hired_company.district}"
            ),
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.cell(
            0,
            self.default_cell_height,
            "**RESPONSÁVEL(IS) PELA ENTIDADE:**",
            align="L",
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self._set_font(font_size=7, bold=False)
        table_data = [
            [
                "",
                "",
                " ",
                f"Nome: {self.contract.accountability_autority.get_full_name()}",
            ],
            ["", "", " ", f"Papel: {self.contract.supervision_autority.position}"],
            ["", "", " ", document_mask(str(self.contract.supervision_autority.cpf))],
        ]
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
                for column_index, text in enumerate(item):
                    self.pdf.set_fill_color(
                        220 if column_index == 1 else 255,
                        220 if column_index == 1 else 255,
                        220 if column_index == 1 else 255,
                    )
                    data.cell(text=text, align="L", border=0)

        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            0,
            self.default_cell_height,
            f"**VALOR TOTAL RECEBIDO:** {format_into_brazilian_currency(self.all_pass_on_values)}",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            markdown=True,
        )
        self.pdf.cell(
            0,
            self.default_cell_height,
            "**ORIGEM DOS RECURSOS (2):** Consolidado de todas as fontes",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            markdown=True,
        )
        self.pdf.ln(2)

    def _draw_table_received(self):
        self._set_font(font_size=7, bold=True)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "DEMONSTRATIVO DOS REPASSES PÚBLICOS RECEBIDOS",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            border=1,
        )

        table_data = [
            [
                "VALORES PREVISTOS - R$",
                "DOC. DE CRÉDITO Nº",
                "DATA",
                "VALORES REPASSADOS - R$",
            ]
        ]
        for pass_on in self.pass_on_queryset:
            table_data.append(
                [
                    format_into_brazilian_currency(self.contract.total_value),
                    pass_on.identification or "—",
                    format_into_brazilian_date(pass_on.receive_date),
                    format_into_brazilian_currency(pass_on.value),
                ]
            )

        col_widths = [47, 48, 47, 48]  # Total: 190
        font = FontFace("FreeSans", "B", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            for item in table_data:
                row = table.row()
                for text in item:
                    row.cell(text=text, align="C")

        total_received = self.all_pass_on_values + self.investment_income
        footer_data = [
            [
                "RECEITA COM APLICAÇÕES FINANCEIRAS DOS REPASSES PÚBLICOS",
                format_into_brazilian_currency(self.investment_income),
            ],
            ["TOTAL", format_into_brazilian_currency(total_received)],
            [
                "RECURSOS PRÓPRIOS APLICADOS PELA ENTIDADE",
                format_into_brazilian_currency(self.own_resources),
            ],
        ]
        col_widths = [150, 40]  # Total: 190
        font = FontFace("FreeSans", "B", size_pt=7)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
            markdown=True,
        ) as table:
            for item in footer_data:
                row = table.row()
                for text in item:
                    row.cell(text=text)

        self.pdf.ln(10)

    def _draw_signatories_notification(self):
        self._set_font(font_size=8, bold=True)
        self.pdf.multi_cell(
            190,
            5,
            (
                "O(s) signatário(s), na qualidade de representante(s) da entidade "
                f"beneficiária {self.contract.organization.name} vem indicar, na forma "
                "abaixo detalhada, a aplicação dos recursos recebidos no exercício supra "
                "mencionado, na importância total de R$ ______________ (por extenso)."
            ),
            align="J",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

    def _draw_table_expenses(self):
        self._set_font(font_size=7, bold=True)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "DEMONSTRATIVO DAS DESPESAS REALIZADAS",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            border=1,
        )

        period_label = (
            f"{format_into_brazilian_date(self.start_date)} a "
            f"{format_into_brazilian_date(self.end_date)}"
        )
        table_data = [
            [
                "CATEGORIA OU FINALIDADE DA DESPESA",
                "PERÍODO DE REALIZAÇÃO",
                "VALOR APLICADO - R$",
            ]
        ]
        for label, category_key in _EXPENSE_CATEGORIES:
            value = self.categorized_expenses[category_key]["paid_on"]
            table_data.append(
                [label, period_label, format_into_brazilian_currency(value)]
            )

        total_paid = self.categorized_expenses["TOTAL"]["paid_on"]
        col_widths = [90, 60, 40]  # Total: 190
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
            for text in table_data[0]:
                header.cell(text=text, align="C")
            self.pdf.set_font("FreeSans", "", 7)
            for item in table_data[1:]:
                row = table.row()
                for column_index, text in enumerate(item):
                    row.cell(text=text, align="L" if column_index == 0 else "R")

        unapplied_value = self.all_pass_on_values - total_paid
        footer_data = [
            ["TOTAL DAS DESPESAS", format_into_brazilian_currency(total_paid)],
            [
                "RECURSO PÚBLICO NÃO APLICADO",
                format_into_brazilian_currency(unapplied_value),
            ],
            # Não há campo no modelo que registre devolução efetiva de
            # recursos ao órgão concessor — deixado em branco em vez de
            # inventar um valor, mesma decisão já tomada no RP-02.
            ["VALOR DEVOLVIDO AO ÓRGÃO CONCESSOR", "—"],
            ["VALOR AUTORIZADO PARA APLICAÇÃO NO EXERCÍCIO SEGUINTE", "—"],
        ]
        col_widths = [150, 40]  # Total: 190
        font = FontFace("FreeSans", "B", size_pt=7)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            for item in footer_data:
                row = table.row()
                for column_index, text in enumerate(item):
                    row.cell(text=text, align="L" if column_index == 0 else "R")

        self.pdf.ln(10)

    def _draw_table_expense_list(self):
        self._set_font(font_size=7, bold=True)
        self.pdf.cell(
            190,
            self.default_cell_height,
            "RELAÇÃO DAS DESPESAS (4)",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            border=1,
        )

        table_data = [
            [
                "DATA DO DOCUMENTO",
                "ESPECIFICAÇÃO DO DOCUMENTO FISCAL (3)",
                "CREDOR",
                "NATUREZA DA DESPESA RESUMIDAMENTE",
                "VALORES R$",
            ]
        ]
        total_expense_value = Decimal("0.00")
        for expense in self.paid_expenses:
            table_data.append(
                [
                    format_into_brazilian_date(expense.liquidation),
                    expense.liquidation_form_label or "—",
                    expense.favored.name,
                    expense.nature_label,
                    format_into_brazilian_currency(expense.value),
                ]
            )
            total_expense_value += expense.value
        table_data.append(
            ["TOTAL", "", "", "", format_into_brazilian_currency(total_expense_value)]
        )

        col_widths = [38, 38, 38, 38, 38]  # Total: 190
        font = FontFace("FreeSans", "B", size_pt=7)
        self.pdf.set_fill_color(255, 255, 255)
        with self.pdf.table(
            headings_style=font,
            line_height=4,
            align="C",
            col_widths=col_widths,
            repeat_headings=0,
        ) as table:
            for item in table_data:
                row = table.row()
                for text in item:
                    row.cell(text=text, align="C")

        self.pdf.ln(10)

    def _draw_org_notification(self):
        self._set_font(font_size=8, bold=True)
        self.pdf.multi_cell(
            190,
            5,
            (
                "Declaro(amos), na qualidade de responsável(is) pela entidade supra "
                "epigrafada, sob as penas da Lei, que a despesa relacionada, examinada "
                "pelo Conselho Fiscal, comprova a exata aplicação dos recursos recebidos "
                "para os fins indicados, conforme programa de trabalho aprovado, proposto "
                "ao Órgão Concessor."
            ),
            align="J",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

    def _draw_observation(self):
        self._set_font(font_size=8, bold=False)
        hired_company = self.contract.hired_company
        self.pdf.cell(
            0,
            0,
            f"LOCAL: {hired_company.city if hired_company else '—'}",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(self.default_cell_height)
        self.pdf.cell(
            0,
            0,
            f"DATA: {format_into_brazilian_date(date.today())}",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            0,
            0,
            "DIRIGENTE: (nome, cargo e assinatura)",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        organization = self.contract.organization
        self.pdf.cell(
            0,
            0,
            f"Nome: {organization.owner} | Cargo: {organization.position}",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            0,
            0,
            "Assinatura: ___________________________",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            0,
            0,
            "MEMBROS DO CONSELHO FISCAL: (nomes e assinatura)",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(0, 0, "Nome:", align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.pdf.ln(4)
        self.pdf.cell(
            0,
            0,
            "Assinatura: ___________________________",
            align="L",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

        self._set_font(font_size=7, bold=False)
        for footnote in (
            "(1) Auxílio, subvenção ou contribuição.",
            "(2) Origem dos recursos: federal, estadual ou municipal, devendo ser "
            "elaborado um Anexo para cada fonte de recurso.",
            "(3) Notas Fiscais e recibos.",
            "(4) No rol das despesas incluir também os gastos que não são classificados "
            "contabilmente como DESPESAS, como, por exemplo, aquisição de bens "
            "permanentes.",
        ):
            self.pdf.multi_cell(
                190,
                4,
                footnote,
                align="L",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            self.pdf.ln(1)
