from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from reports.exporters.commons.pdf_exporter import BasePdf, CommonPDFExporter
from utils.formats import (
    document_mask,
    format_into_brazilian_currency,
    format_into_brazilian_date,
)

# Text constants
TITLE = "ANEXO RP-09 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO"
SUBTITLE = "(REPASSES AO TERCEIRO SETOR - TERMO DE COLABORAÇÃO/FOMENTO)"

NOTIFICATION_ITEMS = [
    (
        "a) o ajuste acima referido e seus aditamentos, bem como o processo "
        "das respectivas prestações de contas estarão sujeitos a análise e "
        "julgamento pelo Tribunal de Contas do Estado de São Paulo cujo "
        "trâmite processual ocorrerá pelo sistema eletrônico;"
    ),
    (
        "b) poderemos ter acesso ao processo tendo vista e extraindo cópias "
        "das manifestações de interesse Despachos e Decisões mediante regular "
        "cadastramento no Sistema de Processo Eletrônico conforme dados "
        "abaixo indicados em consonância com o estabelecido na Resolução "
        "nº01/2011 do TCESP;"
    ),
    (
        "d) as informações pessoais dos responsáveis pelo órgão concessor e "
        "entidade beneficiária estão cadastradas no módulo eletrônico do "
        "'Cadastro Corporativo TCESP - CadTCESP' nos termos previstos no "
        "Artigo 2º das Instruções nº01/2020 conforme 'Declaração(ões) de "
        "Atualização Cadastral' anexa (s);"
    ),
]

NOTIFICATED_ITEMS = [
    (
        "a) O acompanhamento dos atos do processo até seu julgamento final e "
        "consequente publicação;"
    ),
    (
        "b) Se for o caso e de nosso interesse nos prazos e nas formas legais "
        "e regimentais exercer o direito de defesa interpor recursos e o que "
        "mais couber."
    ),
    (
        "c) Este termo corresponde à situação prevista no inciso II do artigo "
        "30 da Lei Complementar nº 709, de 14 de janeiro de 1993, em que, se "
        "houver débito, determinando a notificação do responsável para, no "
        "prazo estabelecido no Regimento Interno, apresentar defesa ou "
        "recolher a importância devida;"
    ),
    (
        "d) A notificação pessoal só ocorrerá caso a defesa apresentada seja "
        "rejeitada, mantida a determinação de recolhimento, conforme §1º do "
        "artigo 30 da citada Lei."
    ),
]

FOOTNOTES = [
    (
        "Valor repassado e exercício, quando se tratar de processo de "
        "prestação de contas."
    ),
    "Facultativo. Indicar quando já constituído.",
    (
        "(*) - O Termo de Ciência e de Notificação deve identificar as "
        "pessoas físicas que tenham concorrido para a prática do ato jurídico,"
        "na condição de ordenador da despesa; de partes contratantes; de "
        "responsáveis por ações de acompanhamento, monitoramento e avaliação; "
        "de responsáveis por processos licitatórios; de responsáveis por "
        "prestações de contas; de responsáveis com atribuições previstas em "
        "atos legais ou administrativos e de interessados relacionados a "
        "processos de competência deste Tribunal. Na hipótese de prestações "
        "de contas, caso o signatário do parecer conclusivo seja distinto "
        "daqueles já arrolados como subscritores do Termo de Ciência e de "
        "Notificação, será ele objeto de notificação específica."
    ),
]


@dataclass
class PassOn9PDFExporter(CommonPDFExporter):
    """Exporter for Pass On 9 PDF report."""

    pdf: Optional[BasePdf] = None
    default_cell_height: int = 5

    def __init__(
        self,
        contract: Any,
        start_date: Any,
        end_date: Any,
        responsibles: Optional[List[Dict[str, Any]]] = None,
    ):
        """Initialize the exporter.

        Args:
            contract: The contract to generate the report for
            start_date: Start date of the report
            end_date: End date of the report
            responsibles: List of responsible people
        """
        super().__init__()
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date
        self.responsibles = responsibles or []
        self.initialize_pdf()

    def handle(self) -> BasePdf:
        """Generate the PDF report.

        Returns:
            The generated PDF document
        """
        self._draw_header()
        self._draw_informations()
        self._draw_notification()
        self._draw_notificated()
        self._draw_public_authority()
        self._draw_expenditure_orderer()
        self._draw_beneficiary_authority()
        self._draw_conclusion_signature_owner()
        self._draw_account_signature_owner()
        self._draw_black_line()
        self._draw_other_responsable()
        self._draw_line()
        self._draw_footnote()

        return self.pdf

    def _draw_header(self) -> None:
        """Draw the header section of the PDF."""
        self.set_font(font_size=11, bold=True)
        self.draw_cell(
            text=TITLE,
            width=190,
            align="C",
        )
        self.set_font(font_size=7, bold=True)
        self.draw_cell(
            text=SUBTITLE,
            width=190,
            align="C",
        )
        self.ln(5)

    def _draw_informations(self) -> None:
        """Draw the information section of the PDF."""
        self.set_font(font_size=7, bold=False)
        self.draw_cell(
            text=(
                f"**ÓRGÃO/ENTIDADE PÚBLICO(A):** "
                f"{self.contract.organization.city_hall.name}"
            ),
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text=(
                f"**ORGANIZAÇÃO DA SOCIEDADE CIVIL PARCEIRA:** "
                f"{self.contract.hired_company} ({self.contract.area.name})"
            ),
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text=(
                f"**TERMO DE COLABORAÇÃO/FOMENTO N° (DE ORIGEM):** "
                f"{self.contract.name}"
            ),
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text=f"**OBJETO:** {self.contract.objective}",
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text=(
                f"**VALOR DO AJUSTE/VALOR REPASSADO (1):** "
                f"{format_into_brazilian_currency(self.contract.total_value)}"
            ),
            markdown=True,
        )
        self.ln(4)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.draw_cell(
            text=(
                f"**EXERCÍCIO (1):** {start.day}/{start.month}/{start.year} a "
                f"{end.day}/{end.month}/{end.year}"
            ),
            markdown=True,
        )
        self.ln(4)
        self.draw_cell(
            text="**ADVOGADO(S) / Nº OAB / E-MAIL: (2)**",
            markdown=True,
        )
        self.ln(10)

    def _draw_notification(self) -> None:
        """Draw the notification section of the PDF."""
        self.ln(3)
        self.set_font(font_size=8)
        self.draw_cell(
            text="Pelo presente TERMO, nós, abaixo identificados:",
            markdown=True,
        )
        self.ln(4)
        self.set_font(font_size=9)
        self.draw_cell(
            text="**1.  Estamos CIENTES de que:**",
            markdown=True,
        )
        self.ln(4)
        self.set_font(font_size=8)
        for item in NOTIFICATION_ITEMS:
            self.draw_multi_cell(
                text=item,
                width=190,
                markdown=True,
            )
            self.ln(1)
        self.ln(10)

    def _draw_notificated(self) -> None:
        """Draw the notificated section of the PDF."""
        self.set_font(font_size=9, bold=True)
        self.draw_cell(
            text="2.    Damo-nos por NOTIFICADOS para:",
        )
        self.ln(4)
        self.set_font(font_size=8, bold=False)
        for item in NOTIFICATED_ITEMS:
            self.draw_multi_cell(
                text=item,
                width=190,
                markdown=True,
            )
            self.ln(1)

        self.set_font(font_size=8)
        self.draw_multi_cell(
            text=f"**LOCAL:** {self.contract.hired_company.city}",
            width=190,
            markdown=True,
        )
        self.ln(3)
        self.draw_multi_cell(
            text=f"**DATA:** {format_into_brazilian_date(date.today())}",
            width=190,
            markdown=True,
        )
        self.ln(10)

    def _draw_public_authority(self) -> None:
        """Draw the public authority section of the PDF."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="AUTORIDADE MÁXIMA DO ÓRGÃO PÚBLICO PARCEIRO:",
        )
        self.ln(4)
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=f"Nome: {self.contract.organization.city_hall.mayor}",
        )
        self.ln(4)
        self.set_font(font_size=8)
        doc = document_mask(str(self.contract.organization.city_hall.document))
        self.draw_cell(text=doc)
        self.ln(10)

    def _draw_expenditure_orderer(self) -> None:
        """Draw the expenditure orderer section of the PDF."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="ORDENADOR DE DESPESA DO ÓRGÃO PÚBLICO PARCEIRO:",
        )
        self.ln(4)
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=f"Nome: {self.contract.contractor_manager.name}",
        )
        self.ln(4)
        self.set_font(font_size=8)
        self.draw_cell(
            text=f"Cargo: {self.contract.contractor_manager.name}",
        )
        self.ln(4)
        self.set_font(font_size=8)
        self.draw_cell(
            text=document_mask(str(self.contract.contractor_manager.cnpj)),
        )
        self.ln(5)
        self.set_font(font_size=8)
        self.draw_cell(
            text="Assinatura: ___________________________",
        )
        self.ln(10)

    def _draw_beneficiary_authority(self) -> None:
        """Draw the beneficiary authority section of the PDF."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="AUTORIDADE MÁXIMA DO ENTIDADE BENEFICIÁRIO:",
        )
        self.ln(4)
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=f"Nome: {self.contract.organization.owner}",
        )
        self.ln(4)
        self.set_font(font_size=8)
        self.draw_cell(
            text=f"Cargo: {self.contract.organization.position}",
        )
        self.ln(4)
        self.set_font(font_size=8)
        self.draw_cell(
            text=document_mask(str(self.contract.organization.document)),
        )
        self.ln(10)

    def _draw_conclusion_signature_owner(self) -> None:
        """Draw the conclusion signature owner section of the PDF."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text=(
                "Responsáveis que assinaram o ajuste e/ou Parecer Conclusivo:"
            ),
        )
        self.ln(4)
        self.draw_cell(
            text="PELO ÓRGÃO PÚBLICO PARCEIRO:",
        )
        self.ln(4)
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text="Nome: Comitê",
        )
        self.ln(4)
        self.set_font(font_size=8)
        self.draw_cell(
            text="Cargo: Comitê",
        )
        self.ln(4)
        self.set_font(font_size=8)
        self.draw_cell(
            text=document_mask(str(self.contract.supervision_autority.cpf)),
        )
        self.ln(10)

    def _draw_account_signature_owner(self) -> None:
        """Draw the account signature owner section of the PDF."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text=(
                "Responsáveis que assinaram o ajuste e/ou prestação de contas:"
            ),
        )
        self.ln(4)
        self.draw_cell(
            text="PELA ENTIDADE PARCEIRA:",
        )
        self.ln(4)
        self.set_font(font_size=8, bold=False)
        name = self.contract.accountability_autority.get_full_name()
        self.draw_cell(text=f"Nome: {name}")
        self.ln(4)
        self.set_font(font_size=8)
        self.draw_cell(
            text=f"Cargo: {self.contract.accountability_autority.position}",
        )
        self.ln(4)
        self.set_font(font_size=8)
        doc = document_mask(str(self.contract.accountability_autority.cpf))
        self.draw_cell(text=doc)
        self.ln(15)

    def _draw_black_line(self) -> None:
        """Draw a black line separator."""
        self.pdf.set_draw_color(0, 0, 0)
        self.pdf.set_line_width(0.5)
        self.draw_line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.ln(10)

    def _draw_other_responsable(self) -> None:
        """Draw the other responsible section of the PDF."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="DEMAIS RESPONSÁVEIS (*):",
        )
        self.ln(6)

        if self.responsibles:
            for responsible in self.responsibles:
                self.set_font(font_size=8, bold=False)
                self.draw_cell(
                    text=(
                        "Tipo de ato sob sua responsabilidade: "
                        f"{responsible['interest_label']}"
                    ),
                )
                self.ln(6)
                name = responsible['user'].get_full_name()
                self.draw_cell(text=f"Nome: {name}")
                self.ln(6)
                self.draw_cell(
                    text=f"Cargo: {responsible['user'].position}",
                )
                self.ln(6)
                doc = document_mask(str(responsible['user'].cpf))
                self.draw_cell(text=f"Documento: {doc}")
                self.ln(6)
                self.draw_multi_cell(
                    text="Assinatura: ______________________________________",
                    width=190,
                )
                self.ln(10)
        else:
            self._draw_empty_responsible()

    def _draw_empty_responsible(self) -> None:
        """Draw empty fields for a responsible person."""
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text="Tipo de ato sob sua responsabilidade:",
        )
        self.ln(6)
        self.draw_cell(text="Nome:")
        self.ln(6)
        self.draw_cell(text="Cargo:")
        self.ln(6)
        self.draw_cell(text="CPF:")
        self.ln(6)
        self.draw_multi_cell(
            text="Assinatura: ______________________________________",
            width=190,
        )
        self.ln(10)

    def _draw_line(self) -> None:
        """Draw a gray line separator."""
        self.pdf.set_draw_color(100, 100, 100)
        self.pdf.set_line_width(0.1)
        self.draw_line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.ln(1)

    def _draw_footnote(self) -> None:
        """Draw the footnote section of the PDF."""
        self.set_font(font_size=6)
        for footnote in FOOTNOTES:
            self.draw_multi_cell(
                text=footnote,
                width=190,
                markdown=True,
            )
            self.ln(1)
