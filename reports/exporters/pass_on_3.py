from reports.exporters.commons.certification_term import (
    CertificationTermPDFExporter,
    TermLabels,
)
from utils.formats import format_into_brazilian_currency


class PassOn3PDFExporter(CertificationTermPDFExporter):
    def __init__(self, contract, start_date, end_date, responsibles=None):
        super().__init__(contract, start_date, end_date, responsibles)
        self.labels = TermLabels(
            header_title="ANEXO RP-03 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO",
            header_subtitle="(REPASSES A ÓRGÃOS PÚBLICOS)",
            certainty_a_text=(
                "o ajuste acima referido e seus aditamentos, bem como o processo das "
                "respectivas prestações de contas estarão sujeitos a análise e julgamento "
                "pelo Tribunal de Contas do Estado de São Paulo cujo trâmite processual "
                "ocorrerá pelo sistema eletrônico;"
            ),
            personal_data_text=(
                "as informações pessoais dos responsáveis pelos órgãos concessor e "
                "beneficiário, bem como do interveniente e interessados, estão cadastradas "
                "no módulo eletrônico do 'Cadastro Corporativo TCESP - CadTCESP' nos "
                "termos previstos no Artigo 2º das Instruções nº01/2024 conforme "
                "'Declaração(ões) de Atualização Cadastral' anexa (s);"
            ),
            grantor_authority_title="AUTORIDADE MÁXIMA DO ÓRGÃO CONCESSOR:",
            grantor_orderer_title="ORDENADOR DE DESPESAS DO ÓRGÃO CONCESSOR:",
            beneficiary_authority_title="AUTORIDADE MÁXIMA DO ÓRGÃO BENEFICIÁRIO:",
            conclusion_section_title="Responsáveis que assinaram o ajuste e/ou Parecer Conclusivo:",
            conclusion_signature_label="PELO ÓRGÃO CONCESSOR:",
            account_section_title="Responsáveis que assinaram o ajuste e/ou prestação de contas:",
            account_signature_label="PELO ÓRGÃO BENEFICIÁRIO:",
        )

    def _local_city(self) -> str:
        contractor_company = self.contract.contractor_company
        return contractor_company.city if contractor_company else "—"

    def _info_lines(self) -> list[str]:
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        return [
            f"**ÓRGÃO CONCESSOR:** {self.contract.organization.city_hall.name}",
            f"**ÓRGÃO BENEFICIÁRIO:** {self.contract.organization.name}",
            "**INTERVENIENTE (se houver):**",
            f"**Nº DO CONVÊNIO: (1)** {self.contract.agreement_num or '—'}",
            f"**TIPO DE CONCESSÃO: (2)** {self.contract.get_concession_type_display()}",
            (
                "**VALOR DO AJUSTE/VALOR REPASSADO (3):** "
                f"{format_into_brazilian_currency(self.contract.total_value)}"
            ),
            f"**EXERCÍCIO (3):** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
            "**ADVOGADO(S) / Nº OAB / E-MAIL: (4)**",
        ]

    def _footnote_lines(self) -> list[str]:
        return [
            "(1) Quando for o caso.",
            "(2) Convênio, Auxílio, Subvenção ou Contribuição.",
            "(3) Valor repassado e exercício, quando se tratar de processo de prestação de contas.",
            "(4) Facultativo. Indicar quando já constituído.",
        ]

    def _draw_extra_signature_sections(self):
        self._set_font(font_size=8, bold=True)
        self.pdf.cell(
            text="PELO INTERVENIENTE:",
            h=self.default_cell_height,
        )
        self.pdf.ln(4)
        self._set_font(font_size=8, bold=False)
        self.pdf.cell(text="Nome:", h=self.default_cell_height)
        self.pdf.ln(4)
        self.pdf.cell(text="Cargo (se for o caso):", h=self.default_cell_height)
        self.pdf.ln(4)
        self.pdf.cell(text="CPF:", h=self.default_cell_height)
        self.pdf.ln(4)
        self.pdf.cell(text="Assinatura:", h=self.default_cell_height)
        self.pdf.ln(15)
