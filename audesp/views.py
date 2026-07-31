"""Fase V trigger/status UI.

Lets a user pick a fiscal year + ajuste type, build and locally validate a
payload (audesp.services.build_and_validate), submit it to AUDESP
(audesp.services.submit), and poll its status (audesp.services.check_status).
Plain Django views + server-rendered templates, matching the rest of this
app (a POST re-renders/redirects back to the page, no JSON API) — see
templates/audesp/fase_v/panel.html.

Declaração Negativa is intentionally NOT orchestrated here:
audesp/services.py doesn't wire it up yet (no field records which of the
other 5 ajuste types a negative declaration is actually for — see that
module's docstring and AUDESP_FASE_V_AUDIT.md §10), so this UI only shows a
"not available yet" note for it.

Environment is hardcoded to PILOTO throughout: AudespSubmission has no
persisted field recording which environment a given submission targeted, and
audesp.services.submit/check_status both already default to PILOTO for the
same reason ("the only one with any credentials until produção access is
provisioned" — audesp/services.py). Exposing an environment picker here
without anywhere to remember the choice would be a footgun (checking status
in the wrong environment for a given protocolo), so this stays a fixed
constant until that gap is settled.
"""

import logging
import re
from json import dumps as json_dumps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from audesp import services as audesp_services
from audesp.clients import AudespError
from audesp.forms import CONCESSION_TYPE_AJUSTE_TYPE_HINTS, AudespFaseVBuildForm
from audesp.models import AudespCredential, AudespSubmission
from audesp.secrets import AudespCredentialNotConfigured
from contracts.models import Contract
from utils.mixins import UserAccessViewMixin

logger = logging.getLogger(__name__)

#: Human labels for the top-level payload sections, per AUDESP_FASE_V_AUDIT.md
#: §1.3 ("37 field-blocks in 6 groups"). Falls back to the raw schema key
#: when a section isn't listed here (e.g. one added by a future schema
#: version) so grouping degrades gracefully instead of breaking.
_SECTION_LABELS = {
    "descritor": "Descritor",
    "dados_gerais_entidade_beneficiaria": "Dados gerais da entidade beneficiária",
    "prestacao_contas_entidade_beneficiaria": "Prestação de contas da entidade beneficiária",
    "responsaveis_membros_orgao_concessor": "Responsáveis e membros do órgão concessor",
    "empenhos": "Empenhos",
    "repasses": "Repasses",
    "receitas": "Receitas",
    "contratos": "Contratos",
    "documentos_fiscais": "Documentos fiscais",
    "glosas": "Glosas",
    "pagamentos": "Pagamentos",
    "ajustes_saldo": "Ajustes de saldo",
    "descontos": "Descontos",
    "devolucoes": "Devoluções",
    "disponibilidades": "Disponibilidades",
    "relacao_empregados": "Relação de empregados",
    "servidores_cedidos": "Relação de servidores cedidos",
    "relacao_bens": "Relação de bens",
    "termo_cessao_bens": "Termo de cessão de bens",
    "relatorio_atividades": "Relatório de atividades",
    "relatorio_comissao_avaliacao": "Relatório da comissão de avaliação",
    "relatorio_governamental_analise_execucao": "Relatório governamental de análise da execução",
    "relatorio_monitoramento_avaliacao": "Relatório de monitoramento e avaliação",
    "publicacao_regulamento_compras": "Publicação do regulamento de compras",
    "publicacao_extrato_execucao_fisica_financeira": "Publicação do extrato de execução física-financeira",
    "publicacao_relatorio_atividades": "Publicação do relatório de atividades",
    "demonstracoes_contabeis": "Demonstrações contábeis",
    "publicacoes_parecer_ata": "Publicação do parecer/ata",
    "declaracoes": "Declarações",
    "transparencia": "Transparência",
    "parecer_conclusivo": "Parecer conclusivo",
}

_REQUIRED_PROPERTY_RE = re.compile(r"^'(?P<name>[^']+)' is a required property$")

#: Both mean "there's no usable AUDESP login for this city hall/environment"
#: — AudespCredential.DoesNotExist is the registry row itself missing,
#: AudespCredentialNotConfigured is the row existing but the actual secret
#: (.env locally / GCP Secret Manager otherwise — see audesp/secrets.py)
#: not being set yet. Both are ops/config problems, not something a
#: contract-detail user can fix, so they get the same message.
_NO_CREDENTIAL_EXCEPTIONS = (
    AudespCredential.DoesNotExist,
    AudespCredentialNotConfigured,
)
_NO_CREDENTIAL_MESSAGE = (
    "Nenhuma credencial AUDESP configurada para a prefeitura deste contrato "
    "no ambiente Piloto. Configure uma em Admin > Credenciais AUDESP."
)


def _group_validation_errors(errors):
    """Groups validate_payload()'s flat [{"message", "path"}, ...] list by
    top-level payload section, for a non-technical-friendly display.

    A root-level "required property missing" error has an EMPTY path (the
    object missing the key is the payload root, not the key itself) even
    though it's about one specific section — e.g. "'documentos_fiscais' is
    a required property" would otherwise dump into a generic bucket
    alongside every other missing-root-key error. Parsing the property name
    back out of the message is what makes those group correctly instead of
    all landing in one undifferentiated "(root)" pile.

    These are still the raw jsonschema message/path strings underneath —
    this pass groups them, it doesn't translate them (see the caption in
    panel.html referencing this).
    """
    groups = {}
    for error in errors:
        path = error.get("path") or ""
        segments = [
            segment for segment in path.split(".") if segment and segment != "(root)"
        ]
        if segments:
            key = segments[0]
        else:
            match = _REQUIRED_PROPERTY_RE.match(error.get("message", ""))
            key = match.group("name") if match else "(root)"
        label = _SECTION_LABELS.get(key, key)
        groups.setdefault(key, {"label": label, "errors": []})["errors"].append(error)
    return sorted(groups.values(), key=lambda group: group["label"])


def _parse_fiscal_year(raw):
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _panel_url(contract, fiscal_year=None):
    url = reverse("audesp:fase-v-panel", args=[contract.id])
    if fiscal_year is not None:
        url = f"{url}?fiscal_year={fiscal_year}"
    return url


class _ContractScopedView(UserAccessViewMixin, LoginRequiredMixin, View):
    """Shared contract lookup, scoped to the requesting user's access level
    the same way ContractsDetailView.get_object() is (contracts/views.py) —
    a Fase V action should never be reachable for a contract the user
    otherwise couldn't open."""

    login_url = "/auth/login"

    def _get_contract(self, contract_id):
        queryset = self.get_user_filtered_queryset(Contract.objects.all())
        return get_object_or_404(queryset, id=contract_id)


class AudespFaseVPanelView(_ContractScopedView):
    """GET-only dedicated page: pick a fiscal year, see/build the current
    submission for (contract, fiscal_year), and browse submission history.
    Linked from the contract detail page's "AUDESP Fase V" tab."""

    def get(self, request, contract_id):
        contract = self._get_contract(contract_id)
        fiscal_year = (
            _parse_fiscal_year(request.GET.get("fiscal_year")) or timezone.now().year
        )

        history = list(
            AudespSubmission.objects.filter(contract=contract, fiscal_year=fiscal_year)[
                :20
            ]
        )
        latest_submission = history[0] if history else None

        if latest_submission:
            initial_ajuste_type = latest_submission.ajuste_type
        else:
            initial_ajuste_type = CONCESSION_TYPE_AJUSTE_TYPE_HINTS.get(
                contract.concession_type, ""
            )
        form = AudespFaseVBuildForm(
            initial={"fiscal_year": fiscal_year, "ajuste_type": initial_ajuste_type}
        )

        error_groups = []
        payload_json = None
        if latest_submission:
            if latest_submission.validation_errors:
                error_groups = _group_validation_errors(
                    latest_submission.validation_errors
                )
            if latest_submission.payload:
                payload_json = json_dumps(
                    latest_submission.payload, ensure_ascii=False, indent=2
                )

        context = {
            "contract": contract,
            "fiscal_year": fiscal_year,
            "form": form,
            "latest_submission": latest_submission,
            "history": history,
            "error_groups": error_groups,
            "payload_json": payload_json,
            "declaracao_negativa_label": AudespSubmission.AjusteTypeChoices.DECLARACAO_NEGATIVA.label,
        }
        return render(request, "audesp/fase_v/panel.html", context)


class AudespFaseVBuildView(_ContractScopedView):
    """POST-only: builds + locally validates a new payload for (contract,
    fiscal_year, ajuste_type), recording it as a new AudespSubmission
    (VALID or INVALID) regardless of outcome, then redirects back to the
    panel — never renders JSON, matches this app's plain-form convention."""

    def post(self, request, contract_id):
        contract = self._get_contract(contract_id)
        form = AudespFaseVBuildForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Informe um exercício e um tipo de ajuste válidos.")
            return redirect(_panel_url(contract))

        fiscal_year = form.cleaned_data["fiscal_year"]
        ajuste_type = form.cleaned_data["ajuste_type"]

        try:
            submission = audesp_services.build_and_validate(
                contract, fiscal_year, ajuste_type
            )
        except Exception:
            # Broad on purpose: the builder pipeline reaches across ~20
            # related models (contracts, accountability, accounts...) and,
            # while AUDESP_FASE_V_AUDIT.md §8 documents it's meant to
            # degrade to an INVALID submission rather than raise, that's
            # only been proven for the Convênio reference build — a 500
            # here would be strictly worse for a non-technical user than a
            # clear "try again" message, so an unexpected exception is
            # logged and turned into one instead of propagating.
            logger.exception(
                "AUDESP Fase V build failed for contract=%s fiscal_year=%s ajuste_type=%s",
                contract.id,
                fiscal_year,
                ajuste_type,
            )
            messages.error(
                request,
                "Não foi possível montar o payload. Verifique se os dados do "
                "contrato e da prestação de contas estão completos e tente "
                "novamente.",
            )
            return redirect(_panel_url(contract, fiscal_year))

        if submission.status == AudespSubmission.StatusChoices.VALID:
            messages.success(request, "Payload montado e validado com sucesso.")
        else:
            error_count = len(submission.validation_errors)
            messages.warning(
                request,
                f"Payload montado, mas com {error_count} erro(s) de validação "
                "— veja os detalhes abaixo.",
            )
        return redirect(_panel_url(contract, fiscal_year))


class AudespFaseVSubmitView(_ContractScopedView):
    """POST-only: sends an already-VALID AudespSubmission to the AUDESP
    Piloto webservice."""

    def post(self, request, contract_id, submission_id):
        contract = self._get_contract(contract_id)
        submission = get_object_or_404(
            AudespSubmission, id=submission_id, contract=contract
        )

        if submission.status != AudespSubmission.StatusChoices.VALID:
            messages.error(
                request, "Só é possível enviar um payload com status Válido."
            )
            return redirect(_panel_url(contract, submission.fiscal_year))

        try:
            audesp_services.submit(submission)
        except _NO_CREDENTIAL_EXCEPTIONS:
            messages.error(request, _NO_CREDENTIAL_MESSAGE)
        except (AudespError, ValueError) as exc:
            messages.error(request, f"Falha ao enviar para a AUDESP: {exc}")
        else:
            messages.success(
                request, f"Enviado à AUDESP — protocolo {submission.protocol_number}."
            )
        return redirect(_panel_url(contract, submission.fiscal_year))


class AudespFaseVCheckStatusView(_ContractScopedView):
    """POST-only: polls AUDESP's /consulta for an already-submitted
    AudespSubmission and refreshes its status/validation_errors."""

    def post(self, request, contract_id, submission_id):
        contract = self._get_contract(contract_id)
        submission = get_object_or_404(
            AudespSubmission, id=submission_id, contract=contract
        )

        if not submission.protocol_number:
            messages.error(request, "Este payload ainda não foi enviado à AUDESP.")
            return redirect(_panel_url(contract, submission.fiscal_year))

        try:
            audesp_services.check_status(submission)
        except _NO_CREDENTIAL_EXCEPTIONS:
            messages.error(request, _NO_CREDENTIAL_MESSAGE)
        except (AudespError, ValueError) as exc:
            messages.error(request, f"Falha ao consultar status na AUDESP: {exc}")
        else:
            messages.success(
                request, f"Status atualizado: {submission.get_status_display()}."
            )
        return redirect(_panel_url(contract, submission.fiscal_year))
