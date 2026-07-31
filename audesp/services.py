"""Thin orchestration: build -> validate -> submit -> poll, for one of the 5
real ajuste types (Declaração Negativa is deliberately not wired up here —
see the note at the bottom of this module), plus the Fase IV Ajuste/Empenho
orchestration near the bottom.

This is glue, not a full ops workflow: retificação support is limited to
setting the payload's `retificacao` flag (`build_and_validate`) and
guarding/reflecting its cascade-exclusion side effect (`submit`, manual
§1.2 point 4) — no inconformidade surfacing UI, no scheduling. See
AUDESP_FASE_V_AUDIT.md §8 Phase 5 and §9 for what's still missing around
this.
"""

from django.db import transaction
from easy_tenants import tenant_context

from audesp.builders import (
    contrato_gestao,
    convenio,
    termo_colaboracao,
    termo_fomento,
    termo_parceria,
)
from audesp.builders.fase_iv import ajuste as fase_iv_ajuste
from audesp.builders.fase_iv import empenho as fase_iv_empenho
from audesp.clients import AudespClient
from audesp.models import AudespCredential, AudespFaseIVSubmission, AudespSubmission
from audesp.validators import validate_fase_iv_payload, validate_payload

_BUILDERS = {
    AudespSubmission.AjusteTypeChoices.CONTRATO_GESTAO: contrato_gestao.build_payload,
    AudespSubmission.AjusteTypeChoices.CONVENIO: convenio.build_payload,
    AudespSubmission.AjusteTypeChoices.TERMO_COLABORACAO: termo_colaboracao.build_payload,
    AudespSubmission.AjusteTypeChoices.TERMO_FOMENTO: termo_fomento.build_payload,
    AudespSubmission.AjusteTypeChoices.TERMO_PARCERIA: termo_parceria.build_payload,
}

# "Live" at TCESP: still stored (or awaiting a first consulta) rather than
# already rejected/excluded. Exactly the statuses manual §1.2 point 4 says a
# retificação of an earlier exercício will cascade-exclude.
_LIVE_STATUSES = (
    AudespSubmission.StatusChoices.SUBMITTED,
    AudespSubmission.StatusChoices.ACCEPTED,
)


class AudespCascadeConfirmationRequired(Exception):
    """Raised by `submit` for a retificação (`submission.retificacao=True`)
    when one or more later exercícios of the same (contract, ajuste_type)
    are still SUBMITTED/ACCEPTED at TCESP. Per manual §1.2 point 4,
    retifying an exercício older than the latest submitted one cascades:
    TCESP flips every later exercício to `Excluído` server-side.

    This is the pre-submission warning AUDESP_FASE_V_AUDIT.md §9 calls for
    ("the ops UI must warn before submission, not after") — call `submit`
    again with `confirm_cascade=True` once that warning has been shown to
    (and accepted by) whoever triggered the submission.
    """

    def __init__(self, submission, affected_submissions):
        self.submission = submission
        self.affected_submissions = list(affected_submissions)
        self.affected_fiscal_years = sorted(
            {s.fiscal_year for s in self.affected_submissions}
        )
        years = ", ".join(str(year) for year in self.affected_fiscal_years)
        super().__init__(
            f"Retifying fiscal_year {submission.fiscal_year} for "
            f"{submission.contract} ({submission.ajuste_type}) will cascade-"
            f"exclude already-submitted exercício(s) {years} at TCESP. Pass "
            "confirm_cascade=True to submit() to proceed and mark them "
            "EXCLUDED locally."
        )


def build_and_validate(contract, fiscal_year, ajuste_type, retificacao=False):
    """Builds + locally validates a payload, recording the attempt as a new
    AudespSubmission row regardless of outcome (INVALID if validate_payload
    finds errors, VALID if it doesn't) — never talks to the webservice. Call
    `submit` separately once you have a VALID submission you want to send.

    `retificacao=True` marks this as a retificação (manual §1.2 point 4): a
    full resend that replaces the prior submission for this exercício. Sets
    the top-level `retificacao` JSON key -- an optional boolean present in
    all 5 real ajuste-type schemas (confirmed directly against
    docs/audesp/; Declaração Negativa's schema has no such property, but
    that builder isn't routed through here anyway) -- to match, and records
    it on the AudespSubmission row so `submit` knows to run the
    cascade-exclusion check below.
    """
    payload = _BUILDERS[ajuste_type](contract, fiscal_year)
    payload["retificacao"] = retificacao
    errors = validate_payload(payload, ajuste_type)
    return AudespSubmission.objects.create(
        organization=contract.organization,
        contract=contract,
        fiscal_year=fiscal_year,
        ajuste_type=ajuste_type,
        retificacao=retificacao,
        status=AudespSubmission.StatusChoices.INVALID
        if errors
        else AudespSubmission.StatusChoices.VALID,
        payload=payload,
        validation_errors=errors,
    )


def find_cascade_affected_submissions(contract, fiscal_year, ajuste_type):
    """AudespSubmission rows for (contract, ajuste_type) with a fiscal_year
    later than `fiscal_year`, still SUBMITTED or ACCEPTED -- exactly the
    set manual §1.2 point 4 says TCESP will flip to `Excluído` server-side
    if a retificação of `fiscal_year` is sent. Public (not `submit`-only) so
    a caller can preview the cascade impact before ever building or
    submitting the retificação itself, per AUDESP_FASE_V_AUDIT.md §9 ("the
    ops UI must warn before submission, not after").

    Doesn't dedupe multiple build/submit attempts for the same later
    fiscal_year: AudespSubmission is append-only (one row per attempt, not
    a singleton, per its own docstring), and a later REJECTED retry never
    un-stores an earlier ACCEPTED attempt at TCESP -- so any later-year row
    still SUBMITTED/ACCEPTED counts as live, regardless of whether a newer,
    differently-statused attempt also exists for that same year.
    """
    with tenant_context(contract.organization):
        return list(
            AudespSubmission.objects.filter(
                contract=contract,
                ajuste_type=ajuste_type,
                fiscal_year__gt=fiscal_year,
                status__in=_LIVE_STATUSES,
            )
        )


def submit(
    submission,
    environment=AudespCredential.EnvironmentChoices.PILOTO,
    confirm_cascade=False,
):
    """Sends an already-built, already-VALID AudespSubmission to the
    webservice. Defaults to the piloto environment since that's the only
    one with any credentials until produção access is provisioned.

    For a retificação (`submission.retificacao=True`) that would cascade-
    exclude later exercícios still SUBMITTED/ACCEPTED at TCESP (manual §1.2
    point 4), raises `AudespCascadeConfirmationRequired` unless
    `confirm_cascade=True`. Once confirmed (or when nothing is affected),
    those later AudespSubmissions are flipped to EXCLUDED locally as a side
    effect of a successful send -- matching what TCESP does server-side, so
    our records don't silently go stale (AUDESP_FASE_V_AUDIT.md §9).
    """
    if submission.status != AudespSubmission.StatusChoices.VALID:
        raise ValueError(
            f"Cannot submit an AudespSubmission with status {submission.status!r} — "
            "only VALID submissions (passed local schema validation) may be sent."
        )

    affected = (
        find_cascade_affected_submissions(
            submission.contract, submission.fiscal_year, submission.ajuste_type
        )
        if submission.retificacao
        else []
    )
    if affected and not confirm_cascade:
        raise AudespCascadeConfirmationRequired(submission, affected)

    client = _client_for(submission.organization.city_hall, environment)
    result = client.submit(submission.ajuste_type, submission.payload)

    with transaction.atomic():
        submission.protocol_number = result["protocolo"]
        submission.status = AudespSubmission.StatusChoices.SUBMITTED
        submission.save(update_fields=["protocol_number", "status"])
        if affected:
            with tenant_context(submission.organization):
                AudespSubmission.objects.filter(
                    pk__in=[affected_submission.pk for affected_submission in affected]
                ).update(status=AudespSubmission.StatusChoices.EXCLUDED)

    return submission


def check_status(submission, environment=AudespCredential.EnvironmentChoices.PILOTO):
    """Polls `/f5/consulta` and updates `submission.status`/`validation_errors`
    from the result. `Excluído` (cascaded exclusion from a retificação on an
    earlier exercício, manual §1.2 point 4) maps to `StatusChoices.EXCLUDED`
    -- `submit`'s own cascade check already flips this locally when *we*
    are the ones sending that retificação, but this poll is what catches it
    if TCESP excludes a submission for any other reason (e.g. a retificação
    submitted through another channel/user). `Recebido`/`Substituído`
    (overwritten by a same-exercício retificação) are still left as-is --
    surfacing `Substituído` correctly needs the still-unbuilt ops UI to show
    which of a contract's several append-only AudespSubmission rows per
    exercício is "current".
    """
    if not submission.protocol_number:
        raise ValueError("Cannot check status before submitting — no protocolo yet.")
    client = _client_for(submission.organization.city_hall, environment)
    result = client.consulta(submission.protocol_number)
    status_map = {
        "Armazenado": AudespSubmission.StatusChoices.ACCEPTED,
        "Rejeitado": AudespSubmission.StatusChoices.REJECTED,
        "Excluído": AudespSubmission.StatusChoices.EXCLUDED,
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


# --- Fase IV (see AUDESP_FASE_IV_AUDIT.md) ---


def build_and_validate_fase_iv_ajuste(
    contract, *, codigo_edital, itens, retificacao=False, funding_sources=None
):
    """Builds + locally validates a Fase IV "ajuste" payload, recording the
    attempt as a new AudespFaseIVSubmission row regardless of outcome.
    `codigo_edital`/`itens` reference a Licitação/Dispensa record this
    codebase doesn't register — see fase_iv.ajuste.build_payload's
    docstring and AUDESP_FASE_IV_AUDIT.md before calling this with real data.
    """
    payload = fase_iv_ajuste.build_payload(
        contract,
        codigo_edital=codigo_edital,
        itens=itens,
        retificacao=retificacao,
        funding_sources=funding_sources,
    )
    errors = validate_fase_iv_payload(payload, "AJUSTE")
    return AudespFaseIVSubmission.objects.create(
        organization=contract.organization,
        contract=contract,
        document_type=AudespFaseIVSubmission.DocumentTypeChoices.AJUSTE,
        status=AudespFaseIVSubmission.StatusChoices.INVALID
        if errors
        else AudespFaseIVSubmission.StatusChoices.VALID,
        payload=payload,
        validation_errors=errors,
    )


def build_and_validate_fase_iv_empenho(budget_commitment, *, retificacao=False):
    """Same as `build_and_validate_fase_iv_ajuste`, for the "empenho"
    sub-módulo payload shape — requires `budget_commitment.contract` to
    already have a real `audesp_agreement_code` (the ajuste this empenho
    is registered against).
    """
    payload = fase_iv_empenho.build_payload(budget_commitment, retificacao=retificacao)
    errors = validate_fase_iv_payload(payload, "EMPENHO")
    return AudespFaseIVSubmission.objects.create(
        organization=budget_commitment.contract.organization,
        contract=budget_commitment.contract,
        budget_commitment=budget_commitment,
        document_type=AudespFaseIVSubmission.DocumentTypeChoices.EMPENHO,
        status=AudespFaseIVSubmission.StatusChoices.INVALID
        if errors
        else AudespFaseIVSubmission.StatusChoices.VALID,
        payload=payload,
        validation_errors=errors,
    )


def submit_fase_iv(submission, environment=AudespCredential.EnvironmentChoices.PILOTO):
    """Sends an already-built, already-VALID AudespFaseIVSubmission (either
    document_type) to the webservice — both go through the same
    `enviar_ajuste` client method per the manual's sub-módulo note.
    """
    if submission.status != AudespFaseIVSubmission.StatusChoices.VALID:
        raise ValueError(
            f"Cannot submit an AudespFaseIVSubmission with status "
            f"{submission.status!r} — only VALID submissions may be sent."
        )
    client = _client_for(submission.contract.organization.city_hall, environment)
    result = client.enviar_ajuste(submission.payload)
    submission.protocol_number = result["protocolo"]
    submission.status = AudespFaseIVSubmission.StatusChoices.SUBMITTED
    submission.save(update_fields=["protocol_number", "status"])
    return submission
