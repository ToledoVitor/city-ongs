from dataclasses import dataclass

from fpdf import XPos, YPos

from reports.exporters.commons.exporters import BasePdf


@dataclass
class PassOn13PDFExporter:
    pdf = None
    default_cell_height = 5

    def __init__(self, contract):
        pdf = BasePdf(orientation="portrait", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_margins(10, 15, 10)
        pdf.set_font("Helvetica", "", 8)
        self.pdf = pdf
        self.contract = contract

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
        self._draw_entity_authority()
        self._draw_conclusion_signature_owner()
        self._draw_account_signature_owner()

        return self.pdf

    def _draw_header(self):
        # Cabeçalho e títulos
        self.__set_helvetica_font(font_size=11, bold=True)
        self.pdf.cell(
            0,
            0,
            "ANEXO RP-13 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=7, bold=True)
        self.pdf.cell(
            0,
            10,
            "AUXÍLIOS/SUBVENÇÕES/CONTRIBUIÇÕES",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.__set_helvetica_font(font_size=6, bold=False)
        self.pdf.cell(
            0,
            10,
            "(utilização apenas para os repasses anteriores à edição da LF 13019/2014 atualizada)",
            align="C",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        # Espaçamento do título pro próximo dado
        self.pdf.set_y(self.pdf.get_y() + 5)

    def _draw_informations(self):
        self.pdf.cell(
            text=f"**ÓRGÃO/ENTIDADE PÚBLICO(A):** {self.contract.organization.city_hall.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**ENTIDADE BENEFICIÁRIA:** {self.contract.organization.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**AUXÍLIO/SUBVENÇÃO/CONTRIBUIÇÃO:** {self.contract.name}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.pdf.cell(
            text=f"**N° DA LEI AUTORIZADORA:**",  # TODO
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
            text=f"**VALOR DO AJUSTE/VALOR REPASSADO (1):** R$ {self.contract.total_value_with_point}",
            markdown=True,
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
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
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="Estamos CIENTES de que:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.multi_cell(
            text="a) o ajuste acima referido e seus aditamentos / o processo de prestação de contas estará(ão) sujeito(s) a análise e julgamento pelo Tribunal de Contas do Estado de São Paulo cujo trâmite processual ocorrerá pelo sistema eletrônico;",
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="b) poderemos ter acesso ao processo tendo vista e extraindo cópias das manifestações de interesse Despachos e Decisões mediante regular cadastramento no Sistema de Processo Eletrônico conforme dados abaixo indicados em consonância com o estabelecido na Resolução nº 01/2011 do TCESP;",
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="c) além de disponíveis no processo eletrônico todos os Despachos e Decisões que vierem a ser tomados relativamente ao aludido processo serão publicados no Diário Oficial do Estado Caderno do Poder Legislativo parte do Tribunal de Contas do Estado de São Paulo em conformidade com o artigo 90 da Lei Complementar nº 709 de 14 de janeiro de 1993 iniciando-se a partir de então a contagem dos prazos processuais conforme regras do Código de Processo Civil;",
            w=190,
            h=self.default_cell_height,
        )
        self.pdf.ln(1)
        self.__set_helvetica_font(font_size=8)
        self.pdf.multi_cell(
            text="d) as informações pessoais do(s) responsável(is) pelo órgão concessor e entidade beneficiária estão cadastradas no módulo eletrônico do 'Cadastro Corporativo TCESP - CadTCESP' nos termos previstos no Artigo 2º das Instruções nº01/2020 conforme 'Declaração(ões) de Atualização Cadastral' anexa (s);",
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

    def _draw_grantor_authority(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="AUTORIDADE MÁXIMA DO ÓRGÃO PÚBLICO CONCESSOR:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text="Nome: ODAIR DE CARVALHO FERREIRA JUNIOR",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="Cargo: Responsável pela Entidade",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="CPF: ***.*35.008-**",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)

    def _draw_entity_authority(self):
        self.__set_helvetica_font(font_size=8, bold=True)
        self.pdf.cell(
            text="AUTORIDADE MÁXIMA DA ENTIDADE BENEFICIÁRIA:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text="Nome: ODAIR DE CARVALHO FERREIRA JUNIOR",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="Cargo: Responsável pela Entidade",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="CPF: ***.*35.008-**",
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
            text="PELO ÓRGÃO PÚBLICO CONCESSOR:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text="Nome: ODAIR DE CARVALHO FERREIRA JUNIOR",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="Cargo: Responsável pela Entidade",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="CPF: ***.*35.008-**",
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
            text="PELA ENTIDADE BENEFICIÁRIA:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8, bold=False)
        self.pdf.cell(
            text="Nome: ODAIR DE CARVALHO FERREIRA JUNIOR",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="Cargo: Responsável pela Entidade",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self.__set_helvetica_font(font_size=8)
        self.pdf.cell(
            text="CPF: ***.*35.008-**",
            h=self.default_cell_height,
        )
        self.pdf.ln(10)
