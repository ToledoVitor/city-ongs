"""Corpo compartilhado dos "termos de ciência e notificação" do TCE-SP
(RP-03/05/07/09/11/13). Os 6 modelos oficiais usam o mesmo texto legal —
só mudam os rótulos das partes (ÓRGÃO CONCESSOR/BENEFICIÁRIO, CONTRATANTE/
CONTRATADA, etc.), o bloco de informações do topo e, em dois casos, trechos
extras: RP-03 tem a parte INTERVENIENTE (se houver) e RP-13 tem o aviso da
LF 13019/2014, uma cláusula (a) mais curta e seções de assinatura com nomes
próprios ("Responsáveis pelo repasse", não "...que assinaram o ajuste").

Extraído porque `pass_on_3/5/7/9/11/13.py` eram byte-idênticos entre si
fora do cabeçalho antes desta reescrita — ver REPORTS_TODO.md.
"""

import os
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from fpdf import XPos, YPos

from reports.exporters.base import BasePDFExporter
from utils.formats import document_mask, format_into_brazilian_date

font_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSans.ttf")
font_bold_path = os.path.join(settings.BASE_DIR, "static/fonts/FreeSansBold.ttf")

# (*) final — idêntico, palavra por palavra, nos 6 modelos oficiais.
RESPONSIBLE_FOOTNOTE = (
    "      (*) - O Termo de Ciência e de Notificação deve identificar as pessoas físicas que "
    "tenham concorrido para a prática do ato jurídico,  na  condição  de  ordenador  da  "
    "despesa;  de  partes  contratantes; de responsáveis por ações de acompanhamento, "
    "monitoramento e avaliação; de responsáveis por processos licitatórios; de responsáveis "
    "por prestações de contas; de responsáveis com atribuições previstas em atos legais ou "
    "administrativos e de interessados relacionados a processos de competência deste "
    "Tribunal. Na hipótese de prestações de contas, caso o signatário do parecer conclusivo "
    "seja distinto daqueles já arrolados como subscritores do Termo de Ciência e de "
    "Notificação, será ele objeto de notificação específica."
)

# Itens (b) e (c) da cláusula "Estamos CIENTES de que" — idênticos nos 6
# modelos oficiais. (c) aponta pro Diário Oficial Eletrônico do TCESP, um
# link fixo do próprio Tribunal — não um link do contrato/órgão (a versão
# anterior deste corpo usava `contract.official_government_link` aqui, o
# que divergia do texto oficial).
CERTAINTY_CLAUSE_B = (
    "b) poderemos ter acesso ao processo tendo vista e extraindo cópias das manifestações de "
    "interesse Despachos e Decisões mediante regular cadastramento no Sistema de Processo "
    "Eletrônico em consonância com o estabelecido na Resolução nº01/2011 do TCESP;"
)
CERTAINTY_CLAUSE_C = (
    "c) além de disponíveis no processo eletrônico todos os Despachos e Decisões que vierem a "
    "ser tomados relativamente ao aludido processo serão publicados no Diário Oficial "
    "Eletrônico do Tribunal de Contas do Estado de São Paulo "
    "([https://doe.tce.sp.gov.br/](https://doe.tce.sp.gov.br/)), em conformidade com o artigo "
    "90 da Lei Complementar nº 709 de 14 de janeiro de 1993 iniciando-se a partir de então a "
    "contagem dos prazos processuais conforme regras do Código de Processo Civil;"
)

# Cláusula "Damo-nos por NOTIFICADOS para" — idêntica nos 6 modelos oficiais.
NOTIFICATED_CLAUSE = (
    "a) O acompanhamento dos atos do processo até seu julgamento final e consequente "
    "publicação;",
    "b) Se for o caso e de nosso interesse nos prazos e nas formas legais e regimentais "
    "exercer o direito de defesa interpor recursos e o que mais couber.",
    "c) Este termo corresponde à situação prevista no inciso II do artigo 30 da Lei "
    "Complementar nº 709, de 14 de janeiro de 1993, em que, se houver débito, determinando a "
    "notificação do responsável para, no prazo estabelecido no Regimento Interno, apresentar "
    "defesa ou recolher a importância devida;",
    "d) A notificação pessoal só ocorrerá caso a defesa apresentada seja rejeitada, mantida a "
    "determinação de recolhimento, conforme §1º do artigo 30 da citada Lei.",
)


@dataclass
class TermLabels:
    """Rótulos que variam entre os 6 anexos. Cada campo aqui corresponde a
    um texto do modelo oficial que muda conforme o par de partes do ajuste
    (órgão concessor/beneficiário, contratante/contratada, etc.)."""

    header_title: str
    header_subtitle: str
    certainty_a_text: str
    personal_data_text: str
    grantor_authority_title: str
    grantor_orderer_title: str
    beneficiary_authority_title: str
    conclusion_section_title: str
    conclusion_signature_label: str
    account_section_title: str
    account_signature_label: str
    notice_line: str | None = None


class CertificationTermPDFExporter(BasePDFExporter):
    """Base dos "termo de ciência e notificação". Subclasses definem
    `self.labels` (`TermLabels`), `_info_lines()` e `_footnote_lines()`
    no `__init__`/nesses métodos; RP-03 também sobrescreve os ganchos de
    interveniente e `_local_city()`."""

    labels: TermLabels

    def __init__(self, contract, start_date, end_date, responsibles=None):
        super().__init__()
        self.initialize_pdf(
            font_specs=[("", font_path), ("B", font_bold_path)],
            base_font_size=8,
            fill_color=(233, 234, 236),
        )
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date
        self.responsibles = responsibles or []

    def _info_lines(self) -> list[str]:
        raise NotImplementedError

    def _footnote_lines(self) -> list[str]:
        raise NotImplementedError

    def _local_city(self) -> str:
        return self.contract.hired_company.city

    def handle(self):
        self._draw_header()
        self._draw_informations()
        self._draw_notification()
        self._draw_notificated()
        self._draw_public_authority()
        self._draw_expenditure_orderer()
        self._draw_beneficiary_authority()
        self._draw_extra_authority_sections()
        self._draw_conclusion_signature_owner()
        self._draw_account_signature_owner()
        self._draw_extra_signature_sections()
        self._draw_black_line()
        self._draw_other_responsable()
        self._draw_line()
        self._draw_footnote()

        return self.pdf

    def _draw_extra_authority_sections(self):
        """Gancho para partes extras (ex.: INTERVENIENTE do RP-03)."""

    def _draw_extra_signature_sections(self):
        """Gancho para blocos de assinatura extras (ex.: RP-03)."""

    def _draw_header(self):
        self._set_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            self.labels.header_title,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self._set_font(font_size=7, bold=True)
        self.pdf.cell(
            0,
            10,
            self.labels.header_subtitle,
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        if self.labels.notice_line:
            self._set_font(font_size=7, bold=True)
            self.pdf.multi_cell(
                190,
                4,
                self.labels.notice_line,
                align="C",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self):
        self._set_font(font_size=7, bold=False)
        for line in self._info_lines():
            self.pdf.cell(text=line, markdown=True, h=self.default_cell_height)
            self.pdf.ln(4)
        self.pdf.ln(6)

    def _draw_notification(self):
        self.pdf.ln(3)
        self._set_font(font_size=8)
        self.pdf.cell(
            text="Pelo presente TERMO, nós, abaixo identificados:",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=9)
        self.pdf.cell(
            text="**1.  Estamos CIENTES de que:**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        for text in (
            f"a) {self.labels.certainty_a_text}",
            CERTAINTY_CLAUSE_B,
            CERTAINTY_CLAUSE_C,
        ):
            self.pdf.multi_cell(
                text=text, markdown=True, w=190, h=self.default_cell_height
            )
            self.pdf.ln(1)
        self.pdf.multi_cell(
            text=f"d) {self.labels.personal_data_text}",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_notificated(self):
        self._set_font(font_size=9, bold=True)
        self.pdf.cell(
            text="2.    Damo-nos por NOTIFICADOS para:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        for text in NOTIFICATED_CLAUSE:
            self.pdf.multi_cell(
                text=text,
                w=190,
                h=4,
                markdown=True,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            self.pdf.ln(1)
        self.pdf.ln(9)

        self._set_font(font_size=8)
        self.pdf.multi_cell(
            text=f"**LOCAL:** {self._local_city()}",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(3)
        self.pdf.multi_cell(
            text=f"**DATA:** {format_into_brazilian_date(date.today())}",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

    def _draw_public_authority(self):
        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            text=self.labels.grantor_authority_title,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: {self.contract.organization.city_hall.mayor}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: {self.contract.organization.city_hall.position}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=document_mask(str(self.contract.organization.city_hall.document))
            or "CNPJ: Não Informado",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_expenditure_orderer(self):
        manager = self.contract.contractor_manager

        manager_name = manager.name if manager else "Não Informado"
        manager_cnpj = document_mask(
            str(manager.cnpj) if manager and manager.cnpj else ""
        )

        org = getattr(self.contract, "organization", None)
        position_value = getattr(org, "position", None) if org else None
        cargo_text = position_value if position_value else "Não Informado"

        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            text=self.labels.grantor_orderer_title,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: {manager_name}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: {cargo_text}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=manager_cnpj or "CNPJ: Não Informado",
            h=self.default_cell_height,
        )
        self.pdf.ln(5)
        self._set_font(font_size=8)
        self.pdf.cell(
            text="Assinatura: ___________________________",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_beneficiary_authority(self):
        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            text=self.labels.beneficiary_authority_title,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: {self.contract.organization.owner}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: {self.contract.organization.position}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=document_mask(str(self.contract.organization.document))
            or "CNPJ: Não Informado",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_conclusion_signature_owner(self):
        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            text=self.labels.conclusion_section_title,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=self.labels.conclusion_signature_label,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            text="Nome: Comitê",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text="Cargo: Comitê",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=document_mask(str(self.contract.supervision_autority.cpf))
            or "CPF: Não Informado",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_account_signature_owner(self):
        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            text=self.labels.account_section_title,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=self.labels.account_signature_label,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: {self.contract.accountability_autority.get_full_name()}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: {self.contract.accountability_autority.position}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8)
        self.pdf.cell(
            text=document_mask(str(self.contract.accountability_autority.cpf))
            or "CPF: Não Informado",
            h=self.default_cell_height,
        )
        self.pdf.ln(15)

    def _draw_black_line(self):
        self.pdf.set_draw_color(0, 0, 0)
        self.pdf.set_line_width(0.5)
        self.pdf.line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.pdf.ln(10)

    def _draw_other_responsable(self):
        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            text="DEMAIS RESPONSÁVEIS (*):",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)

        responsibles = getattr(self, "responsibles", [])
        if responsibles:
            for responsible in responsibles:
                self._set_font(font_size=8, bold=False)
                self.pdf.cell(
                    text=(
                        "Tipo de ato sob sua responsabilidade: "
                        f"{responsible['interest_label']}"
                    ),
                    h=self.default_cell_height,
                )
                self.pdf.ln(6)
                self.pdf.cell(
                    text=f"Nome: {responsible['user'].get_full_name()}",
                    h=self.default_cell_height,
                )
                self.pdf.ln(6)
                self.pdf.cell(
                    text=f"Cargo: {responsible['user'].position}",
                    h=self.default_cell_height,
                )
                self.pdf.ln(6)
                self.pdf.cell(
                    text=f"Documento: {document_mask(str(responsible['user'].cpf))}",
                    h=self.default_cell_height,
                )
                self.pdf.ln(6)
                self.pdf.multi_cell(
                    text=("Assinatura:______________________________________"),
                    w=190,
                    h=self.default_cell_height,
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                )
                self.pdf.ln(10)
        else:
            self._set_font(font_size=8, bold=False)
            self.pdf.cell(
                text="Tipo de ato sob sua responsabilidade:",
                h=self.default_cell_height,
            )
            self.pdf.ln(6)
            self.pdf.cell(
                text="Nome:",
                h=self.default_cell_height,
            )
            self.pdf.ln(6)
            self.pdf.cell(
                text="Cargo:",
                h=self.default_cell_height,
            )
            self.pdf.ln(6)
            self.pdf.cell(
                text="CPF:",
                h=self.default_cell_height,
            )
            self.pdf.ln(6)
            self.pdf.multi_cell(
                text=("Assinatura:______________________________________"),
                w=190,
                h=self.default_cell_height,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            self.pdf.ln(10)

    def _draw_line(self):
        self.pdf.set_draw_color(100, 100, 100)
        self.pdf.set_line_width(0.1)
        self.pdf.line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.pdf.ln(1)

    def _draw_footnote(self):
        self._set_font(font_size=6)
        for text in self._footnote_lines():
            self.pdf.multi_cell(
                text=text,
                w=190,
                h=4,
                markdown=True,
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            self.pdf.ln(1)
        self.pdf.multi_cell(
            text=RESPONSIBLE_FOOTNOTE,
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
