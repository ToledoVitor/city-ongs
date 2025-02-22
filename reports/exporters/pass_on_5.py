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
class PassOn5PDFExporter:
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
        self._draw_informations()
        self._draw_notification()
        self._draw_notificated()
        self._draw_hiring_authority()
        self._draw_beneficiary_authority()
        self._draw_conclusion_signature_owner()
        self._draw_account_signature_owner()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_helvetica_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "ANEXO RP-05 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=7, bold=False)
        self.pdf.cell(
            0,
            10,
            "CONTRATOS DE GESTÃO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self):
        self.pdf.cell(
            text=f"**CONTRATANTE:** {self.accountability.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**CONTRATADA:** {self.accountability.contract.organization.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**CONTRATO DE GESTÃO N° (DE ORIGEM):** {self.accountability.contract.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**OBJETO:** {self.accountability.contract.objective}",
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
            text=f"**EXERCÍCIO (1):** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
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
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="**Estamos CIENTES de que:**",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="a) o ajuste acima referido e seus aditamentos / o processo de prestação de contas estará(ão) sujeito(s) a análise e julgamento pelo Tribunal de Contas do Estado de São Paulo cujo trâmite processual ocorrerá pelo sistema eletrônico;",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="b) poderemos ter acesso ao processo tendo vista e extraindo cópias das manifestações de interesse Despachos e Decisões mediante regular cadastramento no Sistema de Processo Eletrônico conforme dados abaixo indicados em consonância com o estabelecido na Resolução nº 01/2011 do TCESP;",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="c) além de disponíveis no processo eletrônico todos os Despachos e Decisões que vierem a ser tomados relativamente ao aludido processo serão publicados no Diário Oficial do Estado Caderno do Poder Legislativo parte do Tribunal de Contas do Estado de São Paulo em conformidade com o artigo 90 da Lei Complementar nº 709 de 14 de janeiro de 1993 iniciando-se a partir de então a contagem dos prazos processuais conforme regras do Código de Processo Civil;",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="d) as informações pessoais do(s) responsável(is) pelo órgão concessor e entidade beneficiária estão cadastradas no módulo eletrônico do 'Cadastro Corporativo TCESP - CadTCESP' nos termos previstos no Artigo 2º das Instruções nº01/2020 conforme 'Declaração(ões) de Atualização Cadastral' anexa (s);",
            markdown=True,
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_notificated(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="Damo-nos por NOTIFICADOS para:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.multi_cell(
            text="a) O acompanhamento dos atos do processo até seu julgamento final e consequente publicação;",
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="b) Se for o caso e de nosso interesse nos prazos e nas formas legais e regimentais exercer o direito de defesa interpor recursos e o que mais couber.",
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_hiring_authority(self):
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
            text="Responsáveis que assinaram o ajuste e/ou Parecer Conclusivo:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="PELO ÓRGÃO PÚBLICO CONTRATANTE:",
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
            text="Responsáveis que assinaram o ajuste e respectiva prestação de contas:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text="PELO ÓRGANIZAÇÃO SOCIAL:",
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
