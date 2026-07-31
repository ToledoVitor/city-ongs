"""Trigger/status UI for AUDESP Fase IV ("Licitações e Contratos"): register
an Ajuste (contract/instrument registration) or an Empenho (budget
commitment note) with TCESP, and submit an already-built, valid submission.

See AUDESP_FASE_IV_AUDIT.md for what this can and can't do — in
particular, `codigo_edital`/`itens` reference a Licitação/Dispensa record
this codebase does not register (an external prerequisite), and
Licitação/Dispensa registration itself is out of scope.

Server-rendered only, no API/JSON endpoint: every action is a plain POST
that either re-renders the page with the result (Ajuste — see
AudespFaseIVAjusteCreateView's docstring for why it stays on-page instead
of redirecting) or redirects back to the contract detail page with a
toast (Empenho, submit).
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST

from audesp import services
from audesp.clients import AudespError
from audesp.forms import AudespFaseIVAjusteForm, AudespFaseIVEmpenhoForm
from audesp.models import AudespCredential, AudespFaseIVSubmission
from audesp.secrets import AudespCredentialNotConfigured
from contracts.models import Contract

logger = logging.getLogger(__name__)


class AudespFaseIVAjusteCreateView(LoginRequiredMixin, View):
    """Builds + locally validates a Fase IV "ajuste" payload for a contract.

    Stays on this same page across attempts — the built payload's
    validation status is shown in a preview pane after each POST — rather
    than redirecting away on success, per DESIGN.md's preview-first rule
    for forms that produce an artifact (the built JSON document). A
    follow-up "Enviar ao AUDESP" POST (see AudespFaseIVSubmissionSubmitView)
    submits the built submission and reloads this same page via
    `?submission=<id>` so the updated status is visible in place.
    """

    template_name = "audesp/fase_iv/ajuste_create.html"
    login_url = "/auth/login"

    def get(self, request, contract_pk):
        contract = get_object_or_404(Contract, id=contract_pk)
        form = AudespFaseIVAjusteForm()
        submission = self._submission_from_query(request, contract)
        return self._render(request, contract, form, submission)

    def post(self, request, contract_pk):
        contract = get_object_or_404(Contract, id=contract_pk)
        form = AudespFaseIVAjusteForm(request.POST)
        submission = None
        if form.is_valid():
            try:
                submission = services.build_and_validate_fase_iv_ajuste(
                    contract,
                    codigo_edital=form.cleaned_data["codigo_edital"],
                    itens=form.cleaned_data["itens"],
                    retificacao=form.cleaned_data["retificacao"],
                )
            except ValueError as exc:
                # Raised by the builder when the contract has no
                # BudgetCommitment to source fonteRecursosContratacao from —
                # a data-completeness problem, not a form-input mistake.
                form.add_error(None, str(exc))
        return self._render(request, contract, form, submission)

    def _submission_from_query(self, request, contract):
        submission_id = request.GET.get("submission")
        if not submission_id:
            return None
        return AudespFaseIVSubmission.objects.filter(
            id=submission_id,
            contract=contract,
            document_type=AudespFaseIVSubmission.DocumentTypeChoices.AJUSTE,
        ).first()

    def _render(self, request, contract, form, submission):
        return render(
            request,
            self.template_name,
            {"contract": contract, "form": form, "submission": submission},
        )


@login_required(login_url="/auth/login")
@require_POST
def audesp_fase_iv_empenho_create_view(request, contract_pk):
    """Builds + locally validates a Fase IV "empenho" payload for an
    existing BudgetCommitment. No extra inputs beyond picking which
    BudgetCommitment, so this is a single inline form on the contract's
    AUDESP Fase IV tab rather than its own page — result surfaces as a
    toast plus a new row in that tab's submission history.
    """
    contract = get_object_or_404(Contract, id=contract_pk)
    form = AudespFaseIVEmpenhoForm(request.POST, contract=contract)
    if form.is_valid():
        submission = services.build_and_validate_fase_iv_empenho(
            form.cleaned_data["budget_commitment"]
        )
        if submission.status == AudespFaseIVSubmission.StatusChoices.VALID:
            messages.success(
                request,
                "Empenho registrado e válido — envie ao AUDESP na aba "
                "AUDESP Fase IV.",
            )
        else:
            messages.error(
                request,
                "Empenho registrado com erros de validação — confira a "
                "aba AUDESP Fase IV.",
            )
    else:
        error = next(
            iter(form.errors.get("budget_commitment", [])),
            "Selecione um empenho válido.",
        )
        messages.error(request, error)
    return redirect("contracts:contracts-detail", pk=contract.id)


@login_required(login_url="/auth/login")
@require_POST
def audesp_fase_iv_submission_submit_view(request, pk):
    """Submits an already-built, VALID AudespFaseIVSubmission (either
    document_type) to the AUDESP webservice. No credentials are
    provisioned in most environments yet (see AUDESP_FASE_V_AUDIT.md §8
    Phase 5) — connection/authentication failures are caught and surfaced
    as a toast rather than a 500.
    """
    submission = get_object_or_404(AudespFaseIVSubmission, id=pk)

    if submission.status != AudespFaseIVSubmission.StatusChoices.VALID:
        messages.error(
            request,
            "Apenas submissões válidas (status “Válido”) podem ser "
            "enviadas ao AUDESP.",
        )
    else:
        try:
            services.submit_fase_iv(submission)
        except (AudespCredential.DoesNotExist, AudespCredentialNotConfigured):
            messages.error(
                request,
                "Nenhuma credencial AUDESP configurada para este "
                "ambiente — fale com o administrador do sistema.",
            )
        except AudespError as exc:
            logger.warning(
                "AUDESP Fase IV submit failed for submission %s: %s",
                submission.id,
                exc,
            )
            messages.error(
                request,
                "Não foi possível enviar ao AUDESP agora. Tente novamente "
                "mais tarde.",
            )
        else:
            messages.success(request, "Documento enviado ao AUDESP com sucesso.")

    if submission.document_type == AudespFaseIVSubmission.DocumentTypeChoices.AJUSTE:
        detail_url = reverse(
            "audesp:fase-iv-ajuste-create", args=[submission.contract_id]
        )
        return redirect(f"{detail_url}?submission={submission.id}")
    return redirect("contracts:contracts-detail", pk=submission.contract_id)
