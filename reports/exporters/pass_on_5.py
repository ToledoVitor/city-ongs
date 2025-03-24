from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from fpdf import XPos, YPos

from reports.exporters.commons.pdf_exporter import BasePdf, CommonPDFExporter
from utils.formats import (
    document_mask,
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class PassOn5PDFExporter(CommonPDFExporter):
    """Exporter for Pass On 5 PDF report."""

    pdf: Optional[BasePdf] = None
    default_cell_height: int = 5

    def __init__(
        self,
        contract: Any,
        start_date: Any,
        end_date: Any,
        responsibles: Optional[List[Dict[str, Any]]] = None,
    ):
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
        self._draw_grantor_authority()
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
        self.pdf.cell(
            0,
            0,
            "ANEXO RP-05 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.set_font(font_size=7, bold=True)
        self.pdf.cell(
            0,
            10,
            "(REPASSES AO TERCEIRO SETOR - CONTRATOS DE GESTÃO)",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self) -> None:
        """Draw the information section with contract details."""
        self.set_font(font_size=7, bold=False)
        self.pdf.cell(
            text=f"**CONTRATANTE:** {self.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**CONTRATADA:** {self.contract.hired_company} ({self.contract.area.name})",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**CONTRATO DE GESTÃO N° (DE ORIGEM):** {self.contract.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**OBJETO:** {self.contract.objective}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=(
                f"**VALOR DO AJUSTE/VALOR REPASSADO (1):** "
                f"{format_into_brazilian_currency(self.contract.total_value)}"
            ),
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.pdf.cell(
            text=(
                f"**EXERCÍCIO (1):** {start.day}/{start.month}/{start.year} a "
                f"{end.day}/{end.month}/{end.year}"
            ),
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="**ADVOGADO(S) / Nº OAB / E-MAIL: (2):**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_notification(self) -> None:
        """Draw the notification section with legal text."""
        self.pdf.ln(3)
        self.set_font(font_size=8)
        self.pdf.cell(
            text="Pelo presente TERMO, nós, abaixo identificados:",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.set_font(font_size=9)
        self.pdf.cell(
            text="**1.  Estamos CIENTES de que:**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.set_font(font_size=8)
        self.pdf.multi_cell(
            text=(
                "a) o ajuste acima referido e seus aditamentos, bem como o processo "
                "das respectivas prestações de contas estarão sujeitos a análise e "
                "julgamento pelo Tribunal de Contas do Estado de São Paulo cujo "
                "trâmite processual ocorrerá pelo sistema eletrônico;"
            ),
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.set_font(font_size=8)
        self.pdf.multi_cell(
            text=(
                "b) poderemos ter acesso ao processo tendo vista e extraindo cópias "
                "das manifestações de interesse Despachos e Decisões mediante regular "
                "cadastramento no Sistema de Processo Eletrônico conforme dados abaixo "
                "indicados em consonância com o estabelecido na Resolução nº01/2011 "
                "do TCESP;"
            ),
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.set_font(font_size=8)
        self.pdf.multi_cell(
            text=(
                f"c) além de disponíveis no processo eletrônico todos os Despachos e "
                f"Decisões que vierem a ser tomados relativamente ao aludido processo "
                f"serão publicados no Diário Oficial do Estado Caderno do Poder "
                f"Legislativo parte do Tribunal de Contas do Estado de São Paulo"
                f"([{self.government_link}]({self.government_link})), em conformidade "
                f"com o artigo 90 da Lei Complementar nº 709 de 14 de janeiro de 1993 "
                f"iniciando-se a partir de então a contagem dos prazos processuais "
                f"conforme regras do Código de Processo Civil;"
            ),
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.set_font(font_size=8)
        self.pdf.multi_cell(
            text=(
                "d) as informações pessoais dos responsáveis pelo órgão concessor e "
                "entidade beneficiária estão cadastradas no módulo eletrônico do "
                "'Cadastro Corporativo TCESP - CadTCESP' nos termos previstos no "
                "Artigo 2º das Instruções nº01/2020 conforme 'Declaração(ões) de "
                "Atualização Cadastral' anexa (s);"
            ),
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_notificated(self) -> None:
        """Draw the notificated section with legal text."""
        self.set_font(font_size=9, bold=True)
        self.pdf.cell(
            text="2.    Damo-nos por NOTIFICADOS para:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.set_font(font_size=8, bold=False)
        self.pdf.multi_cell(
            text=(
                "a) O acompanhamento dos atos do processo até seu julgamento final "
                "e consequente publicação;"
            ),
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.set_font(font_size=8)
        self.pdf.multi_cell(
            text=(
                "b) Se for o caso e de nosso interesse nos prazos e nas formas "
                "legais e regimentais exercer o direito de defesa interpor recursos "
                "e o que mais couber."
            ),
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.set_font(font_size=8)
        self.pdf.multi_cell(
            text=(
                "c) Este termo corresponde à situação prevista no inciso II do "
                "artigo 30 da Lei Complementar nº 709, de 14 de janeiro de 1993, "
                "em que, se houver débito, determinando a notificação do responsável "
                "para, no prazo estabelecido no Regimento Interno, apresentar defesa "
                "ou recolher a importância devida;"
            ),
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.set_font(font_size=8)
        self.pdf.multi_cell(
            text=(
                "d) A notificação pessoal só ocorrerá caso a defesa apresentada "
                "seja rejeitada, mantida a determinação de recolhimento, conforme "
                "§1º do artigo 30 da citada Lei."
            ),
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

        self.set_font(font_size=8)
        self.pdf.multi_cell(
            text=f"**LOCAL:** {self.contract.hired_company.city}",
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

    def _draw_signature_section(
        self,
        title: str,
        name: str,
        position: str,
        document: str,
    ) -> None:
        """Draw a signature section with common fields.

        Args:
            title: Section title
            name: Person's name
            position: Person's position
            document: Person's document number
        """
        self.set_font(font_size=8, bold=True)
        self.pdf.cell(text=title, h=self.default_cell_height)
        self.pdf.ln(4)
        self.set_font(font_size=8, bold=False)
        self.pdf.cell(text=f"Nome: {name}", h=self.default_cell_height)
        self.pdf.ln(4)
        self.set_font(font_size=8)
        self.pdf.cell(text=f"Cargo: {position}", h=self.default_cell_height)
        self.pdf.ln(4)
        self.set_font(font_size=8)
        self.pdf.cell(
            text=document_mask(str(document)),
            h=self.default_cell_height,
        )

        self.pdf.ln(4)
        self.set_font(font_size=8)
        self.pdf.cell(
            text="Assinatura: ___________________________",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_grantor_authority(self) -> None:
        """Draw the grantor authority section."""
        self._draw_signature_section(
            title="AUTORIDADE MÁXIMA DO ÓRGÃO PÚBLICO CONTRATANTE:",
            name=self.contract.organization.city_hall.mayor,
            position=self.contract.organization.city_hall.position,
            document=self.contract.organization.city_hall.document,
        )

    def _draw_expenditure_orderer(self) -> None:
        """Draw the expenditure orderer section."""
        self._draw_signature_section(
            title="ORDENADOR DE DESPESAS DO ÓRGÃO PÚBLICO CONTRATANTE:",
            name=self.contract.contractor_manager.name,
            position=self.contract.contractor_manager.name,
            document=self.contract.contractor_manager.cnpj,
        )

    def _draw_beneficiary_authority(self) -> None:
        """Draw the beneficiary authority section."""
        self._draw_signature_section(
            title="AUTORIDADE MÁXIMA DA ENTIDADE BENEFICIÁRIA:",
            name=self.contract.organization.owner,
            position=self.contract.organization.position,
            document=self.contract.organization.document,
        )

    def _draw_conclusion_signature_owner(self) -> None:
        """Draw the conclusion signature owner section."""
        self.set_font(font_size=8, bold=True)
        self.pdf.cell(
            text="Responsáveis que assinaram o ajuste e/ou Parecer Conclusivo:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="Pelo ÓRGÃO PÚBLICO CONTRATANTE:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._draw_signature_section(
            title="",
            name="Comitê",
            position="Comitê",
            document=self.contract.supervision_autority.cpf,
        )

    def _draw_account_signature_owner(self) -> None:
        """Draw the account signature owner section."""
        self.set_font(font_size=8, bold=True)
        self.pdf.cell(
            text="Responsáveis que assinaram o ajuste e/ou prestação de contas:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="Pela ORGANIZAÇÃO SOCIAL:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._draw_signature_section(
            title="",
            name=self.contract.accountability_autority.get_full_name(),
            position=self.contract.accountability_autority.position,
            document=self.contract.accountability_autority.cpf,
        )

    def _draw_black_line(self) -> None:
        """Draw a black line separator."""
        self.pdf.set_draw_color(0, 0, 0)
        self.pdf.set_line_width(0.5)
        self.pdf.line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.pdf.ln(10)

    def _draw_other_responsable(self) -> None:
        """Draw the other responsible section."""
        self.set_font(font_size=8, bold=True)
        self.pdf.cell(text="DEMAIS RESPONSÁVEIS (*):", h=self.default_cell_height)
        self.pdf.ln(6)

        responsibles = getattr(self, "responsibles", [])
        if responsibles:
            for responsible in responsibles:
                self._draw_responsible_details(responsible)
        else:
            self._draw_empty_responsible()

    def _draw_responsible_details(self, responsible: Dict[str, Any]) -> None:
        """Draw details for a responsible person.

        Args:
            responsible: Dictionary containing responsible person details
        """
        self.set_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Tipo de ato sob sua responsabilidade: {responsible['interest_label']}",
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
            text="Assinatura: ______________________________________",
            w=190,
            h=self.default_cell_height,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

    def _draw_empty_responsible(self) -> None:
        """Draw empty fields for a responsible person."""
        self.set_font(font_size=8, bold=False)
        self.pdf.cell(
            text="Tipo de ato sob sua responsabilidade:",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.pdf.cell(text="Nome:", h=self.default_cell_height)
        self.pdf.ln(6)
        self.pdf.cell(text="Cargo:", h=self.default_cell_height)
        self.pdf.ln(6)
        self.pdf.cell(text="CPF:", h=self.default_cell_height)
        self.pdf.ln(6)
        self.pdf.multi_cell(
            text="Assinatura: ______________________________________",
            w=190,
            h=self.default_cell_height,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

    def _draw_line(self) -> None:
        """Draw a gray line separator."""
        self.pdf.set_draw_color(100, 100, 100)
        self.pdf.set_line_width(0.1)
        self.pdf.line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.pdf.ln(1)

    def _draw_footnote(self) -> None:
        """Draw the footnote section with legal text."""
        self.set_font(font_size=6)
        self.pdf.multi_cell(
            text=(
                "(1) Valor repassado e exercício, quando se tratar de processo de "
                "prestação de contas."
            ),
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.pdf.multi_cell(
            text="(2) Facultativo. Indicar quando já constituído.",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.pdf.multi_cell(
            text=(
                "      (*) - O Termo de Ciência e de Notificação deve identificar as "
                "pessoas físicas que tenham concorrido para a prática do ato jurídico, "
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
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
