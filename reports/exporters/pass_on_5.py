from reports.exporters.commons.certification_term import (
    CertificationTermPDFExporter,
    TermLabels,
)
from utils.formats import format_into_brazilian_currency


class PassOn5PDFExporter(CertificationTermPDFExporter):
    def __init__(self, contract, start_date, end_date, responsibles=None):
        super().__init__(contract, start_date, end_date, responsibles)
        self.labels = TermLabels(
            header_title="ANEXO RP-05 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO",
            header_subtitle="(REPASSES AO TERCEIRO SETOR - CONTRATOS DE GESTÃO)",
            certainty_a_text=(
                "o ajuste acima referido e seus aditamentos, bem como o processo das "
                "respectivas prestações de contas estarão sujeitos a análise e julgamento "
                "pelo Tribunal de Contas do Estado de São Paulo cujo trâmite processual "
                "ocorrerá pelo sistema eletrônico;"
            ),
            personal_data_text=(
                "as informações pessoais dos responsáveis pela contratante e contratada, "
                "bem como dos interessados, estão cadastradas no módulo eletrônico do "
                "'Cadastro Corporativo TCESP - CadTCESP' nos termos previstos no Artigo 2º "
                "das Instruções nº01/2024 conforme 'Declaração(ões) de Atualização "
                "Cadastral' anexa (s);"
            ),
            grantor_authority_title="AUTORIDADE MÁXIMA DO ÓRGÃO PÚBLICO CONTRATANTE:",
            grantor_orderer_title="ORDENADOR DE DESPESA DO ÓRGÃO PÚBLICO CONTRATANTE:",
            beneficiary_authority_title="AUTORIDADE MÁXIMA DA ENTIDADE BENEFICIÁRIA:",
            conclusion_section_title="Responsáveis que assinaram o ajuste e/ou Parecer Conclusivo:",
            conclusion_signature_label="PELO ÓRGÃO PÚBLICO CONTRATANTE:",
            account_section_title="Responsáveis que assinaram o ajuste e/ou prestação de contas:",
            account_signature_label="PELA ORGANIZAÇÃO SOCIAL:",
        )

    def _info_lines(self) -> list[str]:
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        return [
            f"**CONTRATANTE:** {self.contract.organization.city_hall.name}",
            f"**CONTRATADA:** {self.contract.hired_company} ({self.contract.area.name})",
            f"**CONTRATO DE GESTÃO N° (DE ORIGEM):** {self.contract.name}",
            f"**OBJETO:** {self.contract.objective}",
            (
                "**VALOR DO AJUSTE/VALOR REPASSADO (1):** "
                f"{format_into_brazilian_currency(self.contract.total_value)}"
            ),
            f"**EXERCÍCIO (1):** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
            "**ADVOGADO(S) / Nº OAB / E-MAIL: (2)**",
        ]

    def _footnote_lines(self) -> list[str]:
        return [
            "Valor repassado e exercício, quando se tratar de processo de prestação de contas.",
            "(2) Facultativo. Indicar quando já constituído.",
        ]
