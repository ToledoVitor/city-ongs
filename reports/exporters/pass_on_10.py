from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

from django.db.models import Q, Sum
from fpdf.fonts import FontFace

from accountability.models import Expense, Revenue
from contracts.choices import NatureCategories
from contracts.models import ContractAddendum
from reports.exporters.commons.pdf_exporter import BasePdf, CommonPDFExporter
from utils.formats import (
    document_mask,
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


# Text constants
TITLE = "ANEXO RP-10 - REPASSES AO TERCEIRO SETOR"
SUBTITLE = (
    "DEMONSTRATIVO INTEGRAL DAS RECEITAS E DESPESAS "
    "TERMO DE COLABORAÇÃO/FOMENTO"
)

RESOURCES_TABLE_HEADERS = [
    "**DATA PREVISTA PARA O REPASSE (2)**",
    "**VALORES PREVISTOS (R$)**",
    "**DATA DO REPASSE**",
    "**NÚMERO DO DOCUMENTO DE CRÉDITO**",
    "**VALORES REPASSADOS (R$)**",
]

EXPENSES_TABLE_HEADERS = [
    "CATEGORIA OU FINALIDADE DA DESPESA (8)",
    "DESPESAS CONTABILIZADAS NESTE EXERCÍCIO (R$)",
    (
        "DESPESAS CONTABILIZADAS EM EXERCÍCIOS "
        "ANTERIORES E PAGAS NESTE EXERCÍCIO (R$) (H)"
    ),
    (
        "DESPESAS CONTABILIZADAS NESTE EXERCÍCIO "
        "E PAGAS NESTE EXERCÍCIO (R$) (I)"
    ),
    (
        "TOTAL DE DESPESAS PAGAS NESTE EXERCÍCIO "
        "(R$) (J= H + I)"
    ),
    (
        "DESPESAS CONTABILIZADAS NESTE EXERCÍCIO A "
        "PAGAR EM EXERCÍCIOS SEGUINTES (R$)"
    ),
]

FOOTNOTES = [
    (
        "(1) Verba: Federal, Estadual ou Municipal, devendo ser "
        "elaborado um anexo para cada fonte de recurso."
    ),
    (
        "(2) Incluir valores previstos no exercício anterior e "
        "repassados neste exercício."
    ),
    "(3) Receitas com estacionamento, aluguéis, entre outras.",
    (
        "(4) Verba: Federal, Estadual, Municipal e Recursos Próprios, "
        "devendo ser elaborado um anexo para cada fonte."
    ),
    "(5) Salários, encargos e benefícios.",
    "(6) Autônomos e pessoa jurídica.",
    "(7) Energia elétrica, água e esgoto, gás, telefone e internet.",
    (
        "(8) No rol exemplificativo incluir também as aquisições e os "
        "compromissos assumidos que não são classificados contabilmente "
        "como DESPESAS, como, por exemplo, aquisição de bens."
    ),
    (
        "(9) Quando a diferença entre a Coluna DESPESAS CONTABILIZADAS "
        "NESTE EXERCÍCIO e a Coluna DESPESAS CONTABILIZADAS NESTE "
        "EXERCÍCIO E PAGAS NESTE EXERCÍCIO for decorrente de descontos "
        "obtidos ou multas por atraso, o resultado não deve aparecer na "
        "coluna DESPESAS CONTABILIZADAS NESTE EXERCÍCIO A PAGAR EM "
        "EXERCÍCIOS SEGUINTES, pois tais valores são contabilizados em "
        "contas de receitas e despesas. Assim sendo, deverá ser indicado "
        "como nota de rodapé os valores e contas correspondentes."
    ),
    "(*) Apenas para entidades da área da Saúde.",
]

DECLARATION_TEXT = (
    "Declaro(amos), na qualidade de responsável(is) pela entidade supra epigrafada, "
    "sob as penas da Lei, que a despesa relacionada comprova a exata aplicação dos "
    "recursos recebidos para os fins indicados, conforme programa de trabalho "
    "aprovado, proposto ao Órgão Público Contratante."
)


@dataclass
class PassOn10PDFExporter(CommonPDFExporter):
    """Exporter for Pass On 10 PDF report."""

    pdf: Optional[BasePdf] = None
    default_cell_height: int = 5

    def __init__(
        self,
        contract: Any,
        start_date: Any,
        end_date: Any,
    ):
        """Initialize the exporter.

        Args:
            contract: The contract to generate the report for
            start_date: Start date of the report
            end_date: End date of the report
        """
        super().__init__()
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date
        self.initialize_pdf()
        self.__database_queries()

    def handle(self) -> BasePdf:
        """Generate the PDF report.

        Returns:
            The generated PDF document
        """
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

    def _draw_header(self) -> None:
        """Draw the header section of the PDF."""
        self.set_font(font_size=10, bold=True)
        self.draw_multi_cell(
            text=f"{TITLE}\n{SUBTITLE}",
            width=190,
            align="C",
        )
        self.ln(5)

    def _draw_informations(self) -> None:
        """Draw the information section of the PDF."""
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=f"**Órgão Público:** {self.contract.organization.city_hall.name}",
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text=f"**Organização da Sociedade Civil:** {self.contract.organization.name}",
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text=f"**CNPJ**: {self.contract.hired_company.cnpj}",
            markdown=True,
        )
        self.ln(4)
        hired_company = self.contract.hired_company
        self.draw_cell(
            text=(
                f"**Endereço e CEP:** {hired_company.city}/{hired_company.uf} | "
                f"{hired_company.street}, nº {hired_company.number} - "
                f"{hired_company.district}"
            ),
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text="**Responsável(is) pela OSC:**",
            markdown=True,
        )
        self.ln(4)

    def _draw_first_table(self) -> None:
        """Draw the first table with responsible information."""
        self.set_font(font_size=7, bold=False)
        table_data = [
            ["", "", " ", f"Nome: {self.contract.accountability_autority.get_full_name()}"],
            ["", "", " ", f"Papel: {self.contract.supervision_autority.position}"],
            ["", "", " ", f"{document_mask(str(self.contract.supervision_autority.cpf))}"],
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
                for idx, text in enumerate(item):
                    if idx == 1:
                        self.pdf.set_fill_color(220, 220, 220)
                    else:
                        self.pdf.set_fill_color(255, 255, 255)
                    data.cell(text=text, align="L", border=0)

    def _draw_partners_data(self) -> None:
        """Draw the partners data section."""
        self.ln(3)
        self.set_font(font_size=8)
        self.draw_cell(
            text=f"**Objeto da Parceria:** {self.contract.objective}",
            markdown=True,
        )
        self.ln(4)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.draw_cell(
            text=(
                f"**Exercício:** {format_into_brazilian_date(start)} a "
                f"{format_into_brazilian_date(end)}"
            ),
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text="**Origem dos Recursos (1):** Consolidado de todas as fontes",
            markdown=True,
        )
        self.ln(3)

    def _draw_documents_table(self) -> None:
        """Draw the documents table."""
        self.set_font(font_size=7, bold=False)
        self.ln()
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
                    addendum.contract.name_with_code,
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

        self.ln()

    def _draw_header_resources_table(self) -> None:
        """Draw the header of the resources table."""
        self.ln(7)
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text="**DEMONSTRATIVO DOS RECURSOS DISPONÍVEIS NO EXERCÍCIO**",
            width=190,
            border=1,
            markdown=True,
            align="C",
        )
        self.ln(4)

        table_data = [
            RESOURCES_TABLE_HEADERS,
            [
                f"{format_into_brazilian_date(self.contract.end_of_vigency)}",
                f"{format_into_brazilian_currency(self.contract.total_value)}",
                "dd/mm/aa",  # TODO seria o mesmo que end_of_vigency?
                "Nao sei o que é",
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
        self.draw_cell(
            text="",
            width=190,
            border=1,
            align="C",
        )
        self.pdf.set_fill_color(255, 255, 255)
        self.ln(4)

    def _draw_resources_table(self) -> None:
        """Draw the resources table."""
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
                "R$XX.XXX,YZ",  # TODO Classe de adtamento
            ],
        ]

        self.sum_items_a_to_d = (
            self.previous_balance + self.all_pass_on_values + self.investment_income
        )  # TODO inserir valor de D

        extern_revenue_data.append(
            [
                "(E) TOTAL DE RECURSOS PÚBLICOS (A + B + C + D)",
                "",
                f"{format_into_brazilian_currency(self.sum_items_a_to_d)}",
            ]
        )

        extern_revenue_data.append(["", "", ""])

        intern_revenue_data = [
            [
                "(F) RECURSOS PRÓPRIOS DA ENTIDADE PARCEIRA",
                "",
                f"{format_into_brazilian_currency(self.own_resources)}",
            ],
            [
                "(G) TOTAL DE RECURSOS DISPONÍVEIS NO EXERCÍCIO (E + F)",
                "",
                f"{format_into_brazilian_currency(self.sum_items_a_to_d+self.own_resources)}",
            ],
        ]

        col_widths = [100, 50, 40]
        self.set_font(font_size=7)
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
                extern = table.row()
                for idx, text in enumerate(item):
                    text_align = "L" if idx == 0 else "R"
                    extern.cell(text=text, align=text_align)

            for item in intern_revenue_data:
                intern = table.row()
                for idx, text in enumerate(item):
                    text_align = "L" if idx == 0 else "R"
                    intern.cell(text=text, align=text_align)

    def _draw_resources_footer(self) -> None:
        """Draw the resources footer section."""
        self.ln(4)
        self.set_font(font_size=7)
        for footnote in FOOTNOTES[:3]:
            self.draw_cell(text=footnote)
            self.ln(4)
        self.ln(10)

    def _draw_expenses_table(self) -> None:
        """Draw the expenses table."""
        self.draw_multi_cell(
            text=(
                "O(s) signatário(s), na qualidade de representante(s) da "
                f"{self.contract.organization.name} ({self.contract.area.name}) vem "
                "indicar, na forma abaixo detalhada, as despesas incorridas e pagas "
                f"no exerício {format_into_brazilian_date(self.start_date)} a "
                f"{format_into_brazilian_date(self.end_date)} bem como as despesas a "
                "pagar no exercício seguinte."
            ),
            width=190,
            markdown=True,
        )

        self.ln(7)
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="DEMONSTRATIVO DAS DESPESAS INCORRIDAS NO EXERCÍCIO",
            width=190,
            border=1,
            align="C",
        )
        self.draw_cell(
            text="ORIGEM DOS RECURSOS (4): **Consolidado de todas as fontes**",
            width=190,
            border=1,
            align="L",
            markdown=True,
        )

        expenses_dict = self.__categorize_expenses()
        expenses_dict = self.__convert_decimal_to_brl(expenses_dict)

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
            for text in EXPENSES_TABLE_HEADERS:
                header.cell(text=text, align="C")
            if table_data:
                self.set_font(font_size=7)
                for item in table_data:
                    body = table.row()
                    for idx, text in enumerate(item):
                        text_align = "L" if idx == 0 else "R"
                        body.cell(text=text, align=text_align)
            self.set_font(font_size=7, bold=True)
            total = table.row()
            for idx, text in enumerate(line_total):
                text_align = "L" if idx == 0 else "R"
                total.cell(text=text, align=text_align)

    def _draw_expenses_footer(self) -> None:
        """Draw the expenses footer section."""
        self.set_font(font_size=7)
        for footnote in FOOTNOTES[3:]:
            self.draw_cell(text=footnote)
            self.ln(4)
        self.ln(7)

    def _draw_financial_table(self) -> None:
        """Draw the financial table."""
        self.ln(7)
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="DEMONSTRATIVO DO SALDO FINANCEIRO DO EXERCÍCIO",
            width=190,
            border=1,
            align="C",
        )

        expenses_dict = self.__categorize_expenses()
        j_value = (
            expenses_dict["TOTAL"]["accounted_and_paid"]
            + expenses_dict["TOTAL"]["paid_on"]
        )
        k_value = self.sum_items_a_to_d - (j_value - self.own_resources)

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
                "Não encontrei o campo",  # TODO
            ],
            [
                "(M) VALOR AUTORIZADO PARA APLICAÇÃO NO EXERCÍCIO SEGUINTE (K - L)",
                "Necessário valores anteriores",  # TODO
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
            self.set_font(font_size=7)
            for item in table_data:
                body = table.row()
                for idx, text in enumerate(item):
                    text_align = "L" if idx == 0 else "R"
                    body.cell(text=text, align=text_align)

    def _draw_last_informations(self) -> None:
        """Draw the last information section."""
        self.ln(7)
        self.set_font(font_size=7)
        self.draw_multi_cell(
            text=DECLARATION_TEXT,
            width=190,
            markdown=True,
        )
        self.ln(9)
        self.draw_multi_cell(
            text="**LOCAL:**",
            width=190,
            markdown=True,
        )
        self.ln(4)
        self.draw_multi_cell(
            text="**DATA:**",
            width=190,
            markdown=True,
        )
        self.ln(8)
        self.draw_multi_cell(
            text="**Responsáveis pela Contratada:**",
            width=190,
            markdown=True,
        )

        table_data = [
            ["", "", " ", f"Nome: {self.contract.supervision_autority.get_full_name()}"],
            ["", "", " ", f"Papel: {self.contract.supervision_autority.position}"],
            ["", "", " ", f"{document_mask(str(self.contract.supervision_autority.cpf))}"],
        ]

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
                for idx, text in enumerate(item):
                    if idx == 1:
                        self.pdf.set_fill_color(220, 220, 220)
                    else:
                        self.pdf.set_fill_color(255, 255, 255)
                    data.cell(text=text, align="L", border=0)

    def __database_queries(self) -> None:
        """Execute database queries to get required data."""
        self.checking_account = self.contract.checking_account
        self.investing_account = self.contract.investing_account

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
            accountability__contract=self.contract,
            liquidation__gte=self.start_date,
            liquidation__lte=self.end_date,
        )

        self.all_expenses_value = self.expense_queryset.aggregate(Sum("value"))[
            "value__sum"
        ] or Decimal("0.00")

        # Querie para Aditivos
        self.addendum_queryset = ContractAddendum.objects.filter(
            contract=self.contract,
        )

    def __categorize_expenses(self) -> Dict[str, Dict[str, Decimal]]:
        """Categorize expenses based on their nature.

        Returns:
            Dictionary with categorized expenses
        """
        expenses = Expense.objects.filter(item__contract=self.contract).filter(
            due_date__gte=self.start_date, due_date__lte=self.end_date
        )

        base_empty_dict = {
            "accounted_on": Decimal("0.00"),
            "not_accounted": Decimal("0.00"),
            "accounted_and_paid": Decimal("0.00"),
            "paid_on": Decimal("0.00"),
            "not_paid": Decimal("0.00"),
        }
        categorized_expenses = {
            "HUMAN_RESOURCES": base_empty_dict.copy(),
            "OTHER_HUMAN_RESOURCES": base_empty_dict.copy(),
            "PERMANENT_GOODS": base_empty_dict.copy(),
            "OTHER_THIRD_PARTY": base_empty_dict.copy(),
            "PUBLIC_UTILITIES": base_empty_dict.copy(),
            "FUEL": base_empty_dict.copy(),
            "FINANCIAL_AND_BANKING": base_empty_dict.copy(),
            "FOODSTUFFS": base_empty_dict.copy(),
            "REAL_STATE": base_empty_dict.copy(),
            "MISCELLANEOUS": base_empty_dict.copy(),
            "MEDICAL_AND_HOSPITAL": base_empty_dict.copy(),
            "MEDICAL_SERVICES": base_empty_dict.copy(),
            "MEDICINES": base_empty_dict.copy(),
            "WORKS": base_empty_dict.copy(),
            "OTHER_EXPENSES": base_empty_dict.copy(),
            "OTHER_CONSUMABLES": base_empty_dict.copy(),
            "TOTAL": base_empty_dict.copy(),
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

    def __get_expense_nature_category(self, expense: Expense) -> Optional[str]:
        """Get the category for an expense based on its nature.

        Args:
            expense: The expense to categorize

        Returns:
            The category name or None if not found
        """
        if not expense.nature:
            return None

        if expense.nature in NatureCategories.HUMAN_RESOURCES:
            return "HUMAN_RESOURCES"

        elif expense.nature in NatureCategories.OTHER_HUMAN_RESOURCES:
            return "OTHER_HUMAN_RESOURCES"

        elif expense.nature in NatureCategories.PERMANENT_GOODS:
            return "PERMANENT_GOODS"

        elif expense.nature in NatureCategories.PERMANENT_GOODS:
            return "OTHER_THIRD_PARTY"

        elif expense.nature in NatureCategories.PERMANENT_GOODS:
            return "PUBLIC_UTILITIES"

        elif expense.nature in NatureCategories.FUEL:
            return "FUEL"

        elif expense.nature in NatureCategories.FINANCIAL_AND_BANKING:
            return "FINANCIAL_AND_BANKING"

        elif expense.nature in NatureCategories.FOODSTUFFS:
            return "FOODSTUFFS"

        elif expense.nature in NatureCategories.REAL_STATE:
            return "REAL_STATE"

        elif expense.nature in NatureCategories.MISCELLANEOUS:
            return "MISCELLANEOUS"

        elif expense.nature in NatureCategories.MEDICAL_AND_HOSPITAL:
            return "MEDICAL_AND_HOSPITAL"

        elif expense.nature in NatureCategories.MEDICAL_AND_HOSPITAL:
            return "MEDICAL_SERVICES"

        elif expense.nature in NatureCategories.MEDICINES:
            return "MEDICINES"

        elif expense.nature in NatureCategories.WORKS:
            return "WORKS"

        elif expense.nature in NatureCategories.OTHER_EXPENSES:
            return "OTHER_EXPENSES"

        elif expense.nature in NatureCategories.OTHER_CONSUMABLES:
            return "OTHER_CONSUMABLES"

        return None

    def __convert_decimal_to_brl(
        self, expenses_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert decimal values to BRL format.

        Args:
            expenses_dict: Dictionary with expense values

        Returns:
            Dictionary with formatted values
        """
        for key, value in expenses_dict.items():
            if isinstance(value, Decimal):
                expenses_dict[key] = format_into_brazilian_currency(value)
            elif isinstance(value, dict):
                self.__convert_decimal_to_brl(value)

        return expenses_dict
