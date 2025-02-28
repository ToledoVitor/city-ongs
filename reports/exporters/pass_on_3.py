import copy
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Q
from fpdf import XPos, YPos
from fpdf.fonts import FontFace

from accountability.models import Expense
from contracts.choices import NatureCategories
from reports.exporters.commons.exporters import BasePdf
from utils.formats import document_mask, format_into_brazilian_currency


@dataclass
class PassOn3PDFExporter:
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
        self.government_link = (
            "https://doe.tce.sp.gov.br/"  # TODO criar variável em models de contrato
        )

    def __set_helvetica_font(self, font_size=7, bold=False):
        if bold:
            self.pdf.set_font("Helvetica", "B", font_size)
        else:
            self.pdf.set_font("Helvetica", "", font_size)

    def handle(self):
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

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_helvetica_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "ANEXO RP-03 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=7, bold=False)
        self.pdf.cell(
            0,
            10,
            "(REPASSE À ÓRGÃOS PÚBLICOS)",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self):
        self.pdf.cell(
            text=f"**ÓRGÃO CONCESSOR:** {self.accountability.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**ÓRGÃO BENEFICIÁRIO:** {self.accountability.contract.organization.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**Nº** {self.accountability.contract.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**VALOR DO AJUSTE/VALOR REPASSADO (1):** R$ {self.accountability.contract.total_value_with_point}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        start = self.accountability.contract.start_of_vigency
        end = self.accountability.contract.end_of_vigency
        self.pdf.cell(
            text=f"**EXERCÍCIO (3):** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**ADVOGADO(S) / Nº OAB / E-MAIL(4): ** ",  # TODO Criar campo "advogados"
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_notification(self):
        self.pdf.ln(3)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="Pelo presente TERMO, nós, abaixo identificados:",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=9)
        self.pdf.cell(
            text="**1.  Estamos CIENTES de que:**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="a) o ajuste acima referido e seus aditamentos, bem como o processo das respectivas prestações de contas estarão sujeitos a análise e julgamento pelo Tribunal de Contas do Estado de São Paulo cujo trâmite processual ocorrerá pelo sistema eletrônico;",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="b) poderemos ter acesso ao processo tendo vista e extraindo cópias das manifestações de interesse Despachos e Decisões mediante regular cadastramento no Sistema de Processo Eletrônico conforme dados abaixo indicados em consonância com o estabelecido na Resolução nº01/2011 do TCESP;",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text=f"c) além de disponíveis no processo eletrônico todos os Despachos e Decisões que vierem a ser tomados relativamente ao aludido processo serão publicados no Diário Oficial do Estado Caderno do Poder Legislativo parte do Tribunal de Contas do Estado de São Paulo([{self.government_link}]({self.government_link})), em conformidade com o artigo 90 da Lei Complementar nº 709 de 14 de janeiro de 1993 iniciando-se a partir de então a contagem dos prazos processuais conforme regras do Código de Processo Civil;",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="d) as informações pessoais dos responsáveis pelo órgão concessor e entidade beneficiária estão cadastradas no módulo eletrônico do 'Cadastro Corporativo TCESP - CadTCESP' nos termos previstos no Artigo 2º das Instruções nº01/2020 conforme 'Declaração(ões) de Atualização Cadastral' anexa (s);",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_notificated(self):
        self.__set_helvetica_font(font_size=9, bold=True)
        self.pdf.cell(
            text="2.    Damo-nos por NOTIFICADOS para:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.multi_cell(
            text="a) O acompanhamento dos atos do processo até seu julgamento final e consequente publicação;",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="b) Se for o caso e de nosso interesse nos prazos e nas formas legais e regimentais exercer o direito de defesa interpor recursos e o que mais couber.",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="c) Este termo corresponde à situação prevista no inciso II do artigo 30 da Lei Complementar nº 709, de 14 de janeiro de 1993, em que, se houver débito, determinando a notificação do responsável para, no prazo estabelecido no Regimento Interno, apresentar defesa ou recolher a importância devida;",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="d) A notificação pessoal só ocorrerá caso a defesa apresentada seja rejeitada, mantida a determinação de recolhimento, conforme §1º do artigo 30 da citada Lei.",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text=f"**LOCAL:** {self.accountability.contract.hired_company.city}",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(3)
        self.pdf.multi_cell(
            text=f"**DATA:**",  # É preenchido pelo Usuário
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

    def _draw_grantor_authority(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="AUTORIDADE MÁXIMA DO ÓRGÃO/ENTIDADE CONCESSOR:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: {self.accountability.contract.organization.city_hall.mayor}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: {self.accountability.contract.organization.city_hall.position}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=document_mask(
                str(self.accountability.contract.organization.city_hall.document)
            ),
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_expenditure_orderer(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="ORDENADOR DE DESPESAS DO ÓRGÃO CONCESSOR:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: A criar",  # TODO classe ou variável de ordenapor
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: A criar",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=document_mask(
                # str(self.accountability.contract.organization.city_hall.document)
                "A criar"
            ),
            h=self.default_cell_height,
        )
        self.pdf.ln(5)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=f"Assinatura: ___________________________",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_beneficiary_authority(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="AUTORIDADE MÁXIMA DO ÓRGÃO/ENTIDADE BENEFICIÁRIO:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: {self.accountability.contract.organization.owner}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: {self.accountability.contract.organization.position}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=document_mask(
                str(self.accountability.contract.organization.document)
            ),  # TODO
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_conclusion_signature_owner(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text=f"Responsáveis que assinaram o ajuste e/ou Parecer Conclusivo:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"PELO ÓRGÃO/ENTIDADE CONTRATANTE:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: {self.accountability.contract.supervision_autority.get_full_name()}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: {self.accountability.contract.supervision_autority.position}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=document_mask(
                str(self.accountability.contract.supervision_autority.cpf)
            ),
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_account_signature_owner(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text=f"Responsáveis que assinaram o ajuste e/ou prestação de contas:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"PELO ÓRGÃO/ENTIDADE BENEFICIÁRIO:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome: {self.accountability.contract.accountability_autority.get_full_name()}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=f"Cargo: {self.accountability.contract.accountability_autority.position}",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text=document_mask(
                str(self.accountability.contract.accountability_autority.cpf)
            ),
            h=self.default_cell_height,
        )
        self.pdf.ln(15)

    def _draw_intervener(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text=f"PELO INTERVENIENTE:",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text=f"Nome:",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.pdf.cell(
            text=f"Cargo(se for o caso):",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.pdf.cell(
            text=f"CPF:",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.pdf.multi_cell(
            text="Assinatura:______________________________________",
            w=190,
            h=self.default_cell_height,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(10)

    def _draw_black_line(self):
        self.pdf.set_draw_color(0, 0, 0)
        self.pdf.set_line_width(0.5)
        self.pdf.line(10, self.pdf.get_y(), self.pdf.w - 10, self.pdf.get_y())
        self.pdf.ln(10)

    def _draw_other_responsable(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="DEMAIS RESPONSÁVEIS (*):",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text="Tipo de ato sob sua responsabilidade:",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text="Nome:",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.pdf.cell(
            text=f"Cargo:",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.pdf.cell(
            text=f"CPF:",
            h=self.default_cell_height,
        )
        self.pdf.ln(6)
        self.pdf.multi_cell(
            text="Assinatura:______________________________________",
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
        self.__set_helvetica_font(font_size=6)
        self.pdf.multi_cell(
            text="(1) Quando for o caso.",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.pdf.multi_cell(
            text="(2) Convênio, Auxílio, Subvenção ou Contribuição.",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.pdf.multi_cell(
            text="(3) Valor repassado e exercício, quando se tratar de processo de prestação de contas.",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.pdf.multi_cell(
            text="(4) Facultativo. Indicar quando já constituído.",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.pdf.ln(1)
        self.pdf.multi_cell(
            text="      (*)  O Termo de Ciência e de Notificação deve identificar as pessoas físicas que tenham concorrido para a prática do ato jurídico,  na  condição  de  ordenador  da  despesa;  de  partes  contratantes; de responsáveis por ações de acompanhamento, monitoramento e avaliação; de responsáveis por processos licitatórios; de responsáveis por prestações de contas; de responsáveis com atribuições previstas em atos legais ou administrativos e de interessados relacionados a processos de competência deste Tribunal. Na hipótese de prestações de contas, caso o signatário do parecer conclusivo seja distinto daqueles já arrolados como subscritores do Termo de Ciência e de Notificação, será ele objeto de notificação específica. ",
            w=190,
            h=4,
            markdown=True,
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
