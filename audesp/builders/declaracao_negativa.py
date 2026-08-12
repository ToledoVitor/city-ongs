"""Builds the Fase V JSON payload for a Declaração Negativa.

Manual §4: submitted instead of the full prestação de contas when `contract`
had zero financial movement for a given ajuste type in `fiscal_year`. Its
schema requires only `descritor` + `codigo_ajuste` — but unlike the other 5
ajuste types, `descritor.tipo_documento` is an enum of all 5 real ajuste
type labels rather than a fixed const, since a Declaração Negativa always
declares "no movement" *for* one specific real ajuste type.
"""

from easy_tenants import tenant_context

from audesp.builders import common
from audesp.models import AudespSubmission

_TIPO_DOCUMENTO_BY_AJUSTE_TYPE = {
    AudespSubmission.AjusteTypeChoices.CONTRATO_GESTAO: "Prestação de Contas de Contrato de Gestão",
    AudespSubmission.AjusteTypeChoices.CONVENIO: "Prestação de Contas de Convênio",
    AudespSubmission.AjusteTypeChoices.TERMO_COLABORACAO: "Prestação de Contas de Termo de Colaboração",
    AudespSubmission.AjusteTypeChoices.TERMO_FOMENTO: "Prestação de Contas de Termo de Fomento",
    AudespSubmission.AjusteTypeChoices.TERMO_PARCERIA: "Prestação de Contas de Termo de Parceria",
}


def build_payload(contract, fiscal_year, ajuste_type):
    """`ajuste_type` must be one of the 5 real ajuste types (any
    `AudespSubmission.AjusteTypeChoices` value except DECLARACAO_NEGATIVA
    itself) — it isn't inferred from `contract.concession_type`, since that
    pre-existing field doesn't map 1:1 onto AUDESP's 5 ajuste types (it also
    has a GRANT/"Concessão" option with no AUDESP equivalent — see the
    `sitts-known-bugs` skill).
    """
    with tenant_context(contract.organization):
        return {
            "descritor": common.build_descritor(
                contract, fiscal_year, _TIPO_DOCUMENTO_BY_AJUSTE_TYPE[ajuste_type]
            ),
            "codigo_ajuste": contract.audesp_agreement_code,
        }
