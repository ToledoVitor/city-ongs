"""Thin orchestration: build -> validate -> submit -> poll, for one of the 5
real ajuste types (Declaração Negativa is deliberately not wired up here —
see the note at the bottom of this module).

This is glue, not a full ops workflow: no retificação handling, no
inconformidade surfacing UI, no scheduling. See AUDESP_FASE_V_AUDIT.md §8
Phase 5 for what's still missing around this.
"""

from audesp.builders import (
    contrato_gestao,
    convenio,
    termo_colaboracao,
    termo_fomento,
    termo_parceria,
)
from audesp.clients import AudespClient
from audesp.models import AudespCredential, AudespSubmission
from audesp.validators import validate_payload

_BUILDERS = {
    AudespSubmission.AjusteTypeChoices.CONTRATO_GESTAO: contrato_gestao.build_payload,
    AudespSubmission.AjusteTypeChoices.CONVENIO: convenio.build_payload,
    AudespSubmission.AjusteTypeChoices.TERMO_COLABORACAO: termo_colaboracao.build_payload,
    AudespSubmission.AjusteTypeChoices.TERMO_FOMENTO: termo_fomento.build_payload,
    AudespSubmission.AjusteTypeChoices.TERMO_PARCERIA: termo_parceria.build_payload,
}


def build_and_validate(contract, fiscal_year, ajuste_type):
    """Builds + locally validates a payload, recording the attempt as a new
    AudespSubmission row regardless of outcome (INVALID if validate_payload
    finds errors, VALID if it doesn't) — never talks to the webservice. Call
    `submit` separately once you have a VALID submission you want to send.
    """
    payload = _BUILDERS[ajuste_type](contract, fiscal_year)
    errors = validate_payload(payload, ajuste_type)
    return AudespSubmission.objects.create(
        organization=contract.organization,
        contract=contract,
        fiscal_year=fiscal_year,
        ajuste_type=ajuste_type,
        status=AudespSubmission.StatusChoices.INVALID
        if errors
        else AudespSubmission.StatusChoices.VALID,
        payload=payload,
        validation_errors=errors,
    )


def submit(submission, environment=AudespCredential.EnvironmentChoices.PILOTO):
    """Sends an already-built, already-VALID AudespSubmission to the
    webservice. Defaults to the piloto environment since that's the only
    one with any credentials until produção access is provisioned.
    """
    if submission.status != AudespSubmission.StatusChoices.VALID:
        raise ValueError(
            f"Cannot submit an AudespSubmission with status {submission.status!r} — "
            "only VALID submissions (passed local schema validation) may be sent."
        )
    client = _client_for(submission.organization.city_hall, environment)
    result = client.submit(submission.ajuste_type, submission.payload)
    submission.protocol_number = result["protocolo"]
    submission.status = AudespSubmission.StatusChoices.SUBMITTED
    submission.save(update_fields=["protocol_number", "status"])
    return submission


def check_status(submission, environment=AudespCredential.EnvironmentChoices.PILOTO):
    """Polls `/f5/consulta` and updates `submission.status`/`validation_errors`
    from the result. Manual §1.2.3 status values not mapped below
    (`Recebido`, `Substituído`, `Excluído`) are left as-is — surfacing those
    correctly needs the retificação flow this module doesn't implement yet.
    """
    if not submission.protocol_number:
        raise ValueError("Cannot check status before submitting — no protocolo yet.")
    client = _client_for(submission.organization.city_hall, environment)
    result = client.consulta(submission.protocol_number)
    status_map = {
        "Armazenado": AudespSubmission.StatusChoices.ACCEPTED,
        "Rejeitado": AudespSubmission.StatusChoices.REJECTED,
    }
    new_status = status_map.get(result.get("status"))
    if new_status:
        submission.status = new_status
    submission.validation_errors = result.get("erros", [])
    submission.save(update_fields=["status", "validation_errors"])
    return submission


def _client_for(city_hall, environment):
    credential = AudespCredential.objects.get(
        city_hall=city_hall, environment=environment, is_active=True
    )
    return AudespClient(credential)


# Declaração Negativa isn't wired up here on purpose: AudespClient.
# submit_declaracao_negativa exists and works the same way, but
# AudespSubmission.ajuste_type already has a DECLARACAO_NEGATIVA choice with
# no field recording *which* of the other 5 real ajuste types it's a
# negative declaration *for* — building this orchestration would mean
# guessing at that modeling gap instead of deciding it. See
# AUDESP_FASE_V_AUDIT.md §10.
