from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

from reports.exporters.commons.pdf_exporter import CommonPDFExporter
from utils.formats import (
    document_mask,
    format_into_brazilian_currency,
    format_into_brazilian_date,
)


@dataclass
class PassOn3PDFExporter(CommonPDFExporter):
    """Exporter for Pass On 3 PDF report."""

    def __init__(
        self,
        contract: Any,
        start_date: date,
        end_date: date,
        responsibles: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__()
        self.contract = contract
        self.start_date = start_date
        self.end_date = end_date
        self.responsibles = responsibles or []
        self.initialize_pdf()

    def handle(self) -> Any:
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
        self._draw_intervener()
        self._draw_black_line()
        self._draw_other_responsable()
        self._draw_line()
        self._draw_footnote()

        return self.pdf

    def _draw_header(self) -> None:
        """Draw the header section of the PDF."""
        self.set_font(font_size=11, bold=True)
        self.draw_cell(
            text="ANEXO RP-03 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO",
            width=190,
            align="C",
        )
        self.set_font(font_size=7, bold=True)
        self.draw_cell(
            text="(REPASSE À ÓRGÃOS PÚBLICOS)",
            width=190,
            align="C",
        )
        self.ln(5)

    def _draw_informations(self) -> None:
        """Draw the information section with contract details."""
        self.set_font(font_size=7, bold=False)
        self._draw_organization_details()
        self._draw_contract_details()
        self._draw_exercise_period()
        self._draw_lawyer_info()

    def _draw_organization_details(self) -> None:
        """Draw organization related details."""
        self.draw_cell(
            text=f"**ÓRGÃO CONCESSOR:** {self.contract.organization.city_hall.name}",
            width=190,
            markdown=True,
        )
        self.ln(self.default_cell_height)

        hired_company = self.contract.hired_company
        area_name = self.contract.area.name
        self.draw_cell(
            text=f"**ÓRGÃO BENEFICIÁRIO:** {hired_company} ({area_name})",
            width=190,
            markdown=True,
        )
        self.ln(self.default_cell_height)

        self.draw_cell(
            text="**INTERVENIENTE (se houver):**",
            width=190,
            markdown=True,
        )
        self.ln(self.default_cell_height)

    def _draw_contract_details(self) -> None:
        """Draw contract related details."""
        self.draw_cell(
            text=f"**Nº DO CONVÊNIO** {self.contract.name}",
            width=190,
            markdown=True,
        )
        self.ln(self.default_cell_height)
        
        self.draw_cell(
            text=(
                f"**VALOR DO AJUSTE/VALOR REPASSADO (1):** "
                f"{format_into_brazilian_currency(self.contract.total_value)}"
            ),
            markdown=True,
        )
        self.ln(self.default_cell_height)

    def _draw_exercise_period(self) -> None:
        """Draw the exercise period information."""
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        self.draw_cell(
            text=(
                f"**EXERCÍCIO (3):** {start.day}/{start.month}/{start.year} a "
                f"{end.day}/{end.month}/{end.year}"
            ),
            markdown=True,
        )
        self.ln(self.default_cell_height)

    def _draw_lawyer_info(self) -> None:
        """Draw lawyer information section."""
        self.draw_cell(
            text="**ADVOGADO(S) / Nº OAB / E-MAIL(4): ** ",
            markdown=True,
        )
        self.ln(10)

    def _draw_notification(self) -> None:
        """Draw the notification section."""
        self.ln(3)
        self.set_font(font_size=8)
        self.draw_cell(
            text="Pelo presente TERMO, nós, abaixo identificados:",
            markdown=True,
        )
        self.ln(4)
        
        self._draw_notification_items()
        self.ln(10)

    def _draw_notification_items(self) -> None:
        """Draw the notification items."""
        self.set_font(font_size=9)
        self.draw_cell(
            text="**1.  Estamos CIENTES de que:**",
            markdown=True,
        )
        self.ln(4)
        
        self.set_font(font_size=8)
        self._draw_notification_item_a()
        self._draw_notification_item_b()
        self._draw_notification_item_c()
        self._draw_notification_item_d()

    def _draw_notification_item_a(self) -> None:
        """Draw notification item a."""
        self.draw_multi_cell(
            text=(
                "a) o ajuste acima referido e seus aditamentos, bem como o processo das "
                "respectivas prestações de contas estarão sujeitos a análise e julgamento "
                "pelo Tribunal de Contas do Estado de São Paulo cujo trâmite processual "
                "ocorrerá pelo sistema eletrônico;"
            ),
            width=190,
            markdown=True,
        )
        self.ln(1)

    def _draw_notification_item_b(self) -> None:
        """Draw notification item b."""
        self.draw_multi_cell(
            text=(
                "b) poderemos ter acesso ao processo tendo vista e extraindo "
                "cópias das manifestações de interesse Despachos e Decisões "
                "mediante regular cadastramento no Sistema de Processo "
                "Eletrônico conforme dados abaixo indicados em consonância com "
                "o estabelecido na Resolução nº01/2011 do TCESP;"
            ),
            width=190,
            markdown=True,
        )
        self.ln(1)

    def _draw_notification_item_c(self) -> None:
        """Draw notification item c."""
        self.draw_multi_cell(
            text=(
                "c) além de disponíveis no processo eletrônico todos os "
                "Despachos e Decisões que vierem a ser tomados relativamente "
                "ao aludido processo serão publicados no Diário Oficial do Estado "
                "Caderno do Poder Legislativo parte do Tribunal de Contas do Estado "
                f"de São Paulo([{self.government_link}]({self.government_link})), "
                "em conformidade com o artigo 90 da Lei Complementar nº 709 de 14 de "
                "janeiro de 1993 iniciando-se a partir de então a contagem dos "
                "prazos processuais conforme regras do Código de Processo Civil;"
            ),
            width=190,
            markdown=True,
        )
        self.ln(1)

    def _draw_notification_item_d(self) -> None:
        """Draw notification item d."""
        self.draw_multi_cell(
            text=(
                "d) as informações pessoais dos responsáveis pelo órgão concessor e "
                "entidade beneficiária estão cadastradas no módulo eletrônico do "
                "'Cadastro Corporativo TCESP - CadTCESP' nos termos previstos no "
                "Artigo 2º das Instruções nº01/2020 conforme 'Declaração(ões) de "
                "Atualização Cadastral' anexa (s);"
            ),
            width=190,
            markdown=True,
        )

    def _draw_notificated(self) -> None:
        """Draw the notificated section."""
        self._draw_notificated_header()
        self._draw_notificated_items()
        self._draw_location_and_date()

    def _draw_notificated_header(self) -> None:
        """Draw the notificated section header."""
        self.set_font(font_size=9, bold=True)
        self.draw_cell(
            text="2.    Damo-nos por NOTIFICADOS para:",
            width=190,
            align="L",
        )
        self.ln(4)

    def _draw_notificated_items(self) -> None:
        """Draw the notificated items."""
        self.set_font(font_size=8, bold=False)
        
        items = [
            (
                "a) O acompanhamento dos atos do processo até seu "
                "julgamento final e consequente publicação;"
            ),
            (
                "b) Se for o caso e de nosso interesse nos prazos e nas "
                "formas legais e regimentais exercer o direito de defesa "
                "interpor recursos e o que mais couber."
            ),
            (
                "c) Este termo corresponde à situação prevista no inciso II "
                "do artigo 30 da Lei Complementar nº 709, de 14 de janeiro "
                "de 1993, em que, se houver débito, determinando a "
                "notificação do responsável para, no prazo estabelecido no "
                "Regimento Interno, apresentar defesa ou recolher a "
                "importância devida;"
            ),
            (
                "d) A notificação pessoal só ocorrerá caso a defesa "
                "apresentada seja rejeitada, mantida a determinação de "
                "recolhimento, conforme §1º do artigo 30 da citada Lei."
            ),
        ]
        
        for item in items:
            self.draw_multi_cell(
                text=item,
                width=190,
                height=4,
            markdown=True,
            )
            self.ln(1)

    def _draw_location_and_date(self) -> None:
        """Draw location and date information."""
        self.set_font(font_size=8)
        self.draw_multi_cell(
            text=f"**LOCAL:** {self.contract.hired_company.city}",
            width=190,
            height=4,
            markdown=True,
        )
        self.ln(3)
        self.draw_multi_cell(
            text=f"**DATA:** {format_into_brazilian_date(date.today())}",
            width=190,
            height=4,
            markdown=True,
        )
        self.ln(10)

    def _draw_grantor_authority(self) -> None:
        """Draw the grantor authority section."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="AUTORIDADE MÁXIMA DO ÓRGÃO CONCESSOR:",
            width=190,
            align="L",
        )
        self.ln(4)
        
        city_hall = self.contract.organization.city_hall
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=f"Nome: {city_hall.mayor}",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=f"Cargo: {city_hall.position}",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=document_mask(str(city_hall.document)),
            width=190,
            align="L",
        )
        self.ln(10)

    def _draw_expenditure_orderer(self) -> None:
        """Draw the expenditure orderer section."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="ORDENADOR DE DESPESAS DO ÓRGÃO CONCESSOR:",
            width=190,
            align="L",
        )
        self.ln(4)
        
        manager = self.contract.contractor_manager
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=f"Nome: {manager.name}",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=f"Cargo: {manager.position}",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=document_mask(str(manager.cnpj)),
            width=190,
            align="L",
        )
        self.ln(8)
        self.draw_cell(
            text="Assinatura: ___________________________",
            width=190,
            align="L",
        )
        self.ln(10)

    def _draw_beneficiary_authority(self) -> None:
        """Draw the beneficiary authority section."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="AUTORIDADE MÁXIMA DO ÓRGÃO BENEFICIÁRIO:",
            width=190,
            align="L",
        )
        self.ln(4)
        
        organization = self.contract.organization
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=f"Nome: {organization.owner}",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=f"Cargo: {organization.position}",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=document_mask(str(organization.document)),
            width=190,
            align="L",
        )
        self.ln(10)

    def _draw_conclusion_signature_owner(self) -> None:
        """Draw the conclusion signature owner section."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="Responsáveis que assinaram o ajuste e/ou Parecer Conclusivo:",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text="PELO ÓRGÃO CONTRATANTE:",
            width=190,
            align="L",
        )
        self.ln(4)
        
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text="Nome: Comitê",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text="Cargo: Comitê",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=document_mask(str(self.contract.supervision_autority.cpf)),
            width=190,
            align="L",
        )
        self.ln(10)

    def _draw_account_signature_owner(self) -> None:
        """Draw the account signature owner section."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="Responsáveis que assinaram o ajuste e/ou prestação de contas:",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text="PELO ÓRGÃO BENEFICIÁRIO:",
            width=190,
            align="L",
        )
        self.ln(4)
        
        authority = self.contract.accountability_autority
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text=f"Nome: {authority.get_full_name()}",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=f"Cargo: {authority.position}",
            width=190,
            align="L",
        )
        self.ln(4)
        self.draw_cell(
            text=document_mask(str(authority.cpf)),
            width=190,
            align="L",
        )
        self.ln(15)

    def _draw_intervener(self) -> None:
        """Draw the intervener section."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="PELO INTERVENIENTE:",
            width=190,
            align="L",
        )
        self.ln(6)
        
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text="Nome:",
            width=190,
            align="L",
        )
        self.ln(6)
        self.draw_cell(
            text="Cargo(se for o caso):",
            width=190,
            align="L",
        )
        self.ln(6)
        self.draw_cell(
            text="CPF:",
            width=190,
            align="L",
        )
        self.ln(6)
        self.draw_multi_cell(
            text="Assinatura:______________________________________",
            width=190,
            height=4,
            align="L",
        )
        self.ln(10)

    def _draw_black_line(self) -> None:
        """Draw a black line separator."""
        self.pdf.set_draw_color(0, 0, 0)
        self.pdf.set_line_width(0.5)
        self.draw_line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.ln(10)

    def _draw_other_responsable(self) -> None:
        """Draw the other responsible section."""
        self.set_font(font_size=8, bold=True)
        self.draw_cell(
            text="DEMAIS RESPONSÁVEIS (*):",
            width=190,
            align="L",
        )
        self.ln(6)

        responsibles = getattr(self, "responsibles", [])
        if responsibles:
            self._draw_responsibles_list(responsibles)
        else:
            self._draw_empty_responsible()

    def _draw_responsibles_list(self, responsibles: List[Dict[str, Any]]) -> None:
        """Draw the list of responsible people.

        Args:
            responsibles: List of responsible people with their details
        """
        for responsible in responsibles:
            self.set_font(font_size=8, bold=False)
            self.draw_cell(
                text=f"Tipo de ato sob sua responsabilidade: {responsible['interest_label']}",
                width=190,
                align="L",
            )
            self.ln(6)
            self.draw_cell(
                text=f"Nome: {responsible['user'].get_full_name()}",
                width=190,
                align="L",
            )
            self.ln(6)
            self.draw_cell(
                text=f"Cargo: {responsible['user'].position}",
                width=190,
                align="L",
            )
            self.ln(6)
            self.draw_cell(
                text=f"Documento: {document_mask(str(responsible['user'].cpf))}",
                width=190,
                align="L",
            )
            self.ln(6)
            self.draw_multi_cell(
                text="Assinatura:______________________________________",
                width=190,
                height=4,
                align="L",
            )
            self.ln(10)

    def _draw_empty_responsible(self) -> None:
        """Draw an empty responsible section."""
        self.set_font(font_size=8, bold=False)
        self.draw_cell(
            text="Tipo de ato sob sua responsabilidade:",
            width=190,
            align="L",
        )
        self.ln(6)
        self.draw_cell(
            text="Nome:",
            width=190,
            align="L",
        )
        self.ln(6)
        self.draw_cell(
            text="Cargo:",
            width=190,
            align="L",
        )
        self.ln(6)
        self.draw_cell(
            text="CPF:",
            width=190,
            align="L",
        )
        self.ln(6)
        self.draw_multi_cell(
            text="Assinatura:______________________________________",
            width=190,
            height=4,
            align="L",
        )
        self.ln(10)

    def _draw_line(self) -> None:
        """Draw a gray line separator."""
        self.pdf.set_draw_color(100, 100, 100)
        self.pdf.set_line_width(0.1)
        self.draw_line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.ln(1)

    def _draw_footnote(self) -> None:
        """Draw the footnote section."""
        self.set_font(font_size=6)
        
        footnotes = [
            "(1) Quando for o caso.",
            "(2) Convênio, Auxílio, Subvenção ou Contribuição.",
            "(3) Valor repassado e exercício, quando se tratar de processo de prestação de contas.",
            "(4) Facultativo. Indicar quando já constituído.",
            (
                "      (*)  O Termo de Ciência e de Notificação deve identificar as "
                "pessoas físicas que tenham concorrido para a prática do ato jurídico, "
                "na condição de ordenador da despesa; de partes contratantes; de "
                "responsáveis por ações de acompanhamento, monitoramento e avaliação; "
                "de responsáveis por processos licitatórios; de responsáveis por "
                "prestações de contas; de responsáveis com atribuições previstas em "
                "atos legais ou administrativos e de interessados relacionados a "
                "processos de competência deste Tribunal. Na hipótese de prestações de "
                "contas, caso o signatário do parecer conclusivo seja distinto daqueles "
                "já arrolados como subscritores do Termo de Ciência e de Notificação, "
                "será ele objeto de notificação específica."
            ),
        ]
        
        for footnote in footnotes:
            self.draw_multi_cell(
                text=footnote,
                width=190,
                height=4,
                markdown=True,
            )
            self.ln(1)
