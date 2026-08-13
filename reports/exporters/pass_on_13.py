from reports.exporters.commons.certification_term import (
    CertificationTermPDFExporter,
    TermLabels,
)
from utils.formats import format_into_brazilian_currency


class PassOn13PDFExporter(CertificationTermPDFExporter):
    def __init__(self, contract, start_date, end_date, responsibles=None):
        super().__init__(contract, start_date, end_date, responsibles)
        self.labels = TermLabels(
            header_title="ANEXO RP-13 - TERMO DE CIÊNCIA E DE NOTIFICAÇÃO",
            header_subtitle=(
                "(REPASSES AO TERCEIRO SETOR - AUXÍLIOS/SUBVENÇÕES/CONTRIBUIÇÕES)"
            ),
            notice_line=(
                "(utilização apenas para os repasses anteriores à edição da LF "
                "13019/2014 atualizada)"
            ),
            certainty_a_text=(
                "o processo de prestação de contas estará sujeito a análise e julgamento "
                "pelo Tribunal de Contas do Estado de São Paulo cujo trâmite processual "
                "ocorrerá pelo sistema eletrônico;"
            ),
            personal_data_text=(
                "as informações pessoais dos responsáveis pelo órgão concessor e pela "
                "entidade beneficiária estão cadastradas no módulo eletrônico do "
                "'Cadastro Corporativo TCESP - CadTCESP' nos termos previstos no Artigo 2º "
                "das Instruções nº01/2024 conforme 'Declaração(ões) de Atualização "
                "Cadastral' anexa (s);"
            ),
            grantor_authority_title="AUTORIDADE MÁXIMA DO ÓRGÃO PÚBLICO CONCESSOR:",
            grantor_orderer_title="ORDENADOR DE DESPESA DO ÓRGÃO PÚBLICO CONCESSOR:",
            beneficiary_authority_title="AUTORIDADE MÁXIMA DA ENTIDADE BENEFICIÁRIA:",
            conclusion_section_title="Responsáveis pelo repasse e/ou Parecer Conclusivo:",
            conclusion_signature_label="PELO ÓRGÃO PÚBLICO CONCESSOR:",
            account_section_title="Responsáveis pela prestação de contas:",
            account_signature_label="PELA ENTIDADE BENEFICIÁRIA:",
        )

    def _info_lines(self) -> list[str]:
        start = self.contract.start_of_vigency
        end = self.contract.end_of_vigency
        return [
            f"**ÓRGÃO/ENTIDADE PÚBLICO(A):** {self.contract.organization.city_hall.name}",
            (
                "**ENTIDADE BENEFICIÁRIA:** "
                f"{self.contract.hired_company} ({self.contract.area.name})"
            ),
            f"**AUXÍLIO/SUBVENÇÃO/CONTRIBUIÇÃO:** {self.contract.name}",
            f"**N° DA LEI AUTORIZADORA:** {self.contract.law_num or '—'}",
            f"**OBJETO:** {self.contract.objective}",
            f"**VALOR REPASSADO:** {format_into_brazilian_currency(self.contract.total_value)}",
            f"**EXERCÍCIO:** {start.day}/{start.month}/{start.year} a {end.day}/{end.month}/{end.year}",
            "**ADVOGADO(S) / Nº OAB / E-MAIL: (1)**",
        ]

    def _footnote_lines(self) -> list[str]:
        return ["(1) Facultativo. Indicar quando já constituído."]
