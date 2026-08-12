from django import forms
from django.conf import settings
from django.utils import timezone

from accountability.models import BudgetCommitment
from audesp import secrets as audesp_secrets
from audesp.models import AudespCredential, AudespSubmission
from contracts.models import Contract
from utils.widgets import BaseCharFieldFormWidget, BaseSelectFormWidget


class AudespCredentialAdminForm(forms.ModelForm):
    """Username/password are never stored on the model (see
    `AudespCredential`'s docstring) — this form only collects them to hand
    off to `audesp.secrets.set_credentials`, which writes to GCP Secret
    Manager. In DEVELOPMENT there's nothing to write here: local credentials
    come from `.env`, so both fields are disabled with a pointer to it.

    Lives outside `audesp/admin.py` (which only imports and registers it)
    so the same validation can be reused by non-admin UI — see
    `accounts.forms.AudespCredentialSettingsForm`, which backs the
    city-hall-scoped settings page under `accounts:audesp-credentials-list`.
    """

    username = forms.CharField(label="Usuário", required=False)
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Deixe em branco para manter a senha atual.",
    )

    class Meta:
        model = AudespCredential
        fields = ("city_hall", "environment", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if settings.DEVELOPMENT:
            for field_name in ("username", "password"):
                self.fields[field_name].disabled = True
                self.fields[field_name].help_text = (
                    "Ambiente de desenvolvimento: defina AUDESP_PILOTO_USERNAME/"
                    "PASSWORD ou AUDESP_PRODUCAO_USERNAME/PASSWORD no .env."
                )

    def save(self, commit=True):
        instance = super().save(commit=False)
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if not settings.DEVELOPMENT:
            if username and password:
                audesp_secrets.set_credentials(
                    instance.city_hall, instance.environment, username, password
                )
            elif instance._state.adding:
                # NOTE: `instance.pk` is truthy even for a brand-new row here
                # — `BaseModel.id` defaults to `uuid4()` at construction time,
                # not at INSERT time — so "no pk yet" can't detect "is this a
                # create". `_state.adding` is Django's own is-this-persisted-
                # yet flag and stays correct regardless of the pk strategy.
                raise forms.ValidationError(
                    "Usuário e senha são obrigatórios para uma nova credencial."
                )
        if commit:
            instance.save()
        return instance


#: Only the 5 ajuste types services.build_and_validate actually knows how to
#: build — DECLARACAO_NEGATIVA is excluded on purpose (see module docstring).
REAL_AJUSTE_TYPE_CHOICES = [
    (choice.value, choice.label)
    for choice in AudespSubmission.AjusteTypeChoices
    if choice != AudespSubmission.AjusteTypeChoices.DECLARACAO_NEGATIVA
]

#: Best-effort *default suggestion* only, never an auto-decision — per
#: the `sitts-known-bugs` skill ("Contract.ConcessionChoices doesn't map 1:1
#: onto AUDESP's 5 ajuste types"), GRANT ("Concessão") has no Fase V ajuste
#: type at all, so it's left out rather than guessed at, and DEVELOPMENTO's
#: label ("Contrato de Fomento") doesn't match AUDESP's own term for the
#: same instrument ("Termo de Fomento") even though the mapping itself
#: holds. The form field this seeds is always an explicit, user-editable
#: choice — this dict only pre-selects a starting value.
CONCESSION_TYPE_AJUSTE_TYPE_HINTS = {
    Contract.ConcessionChoices.MANAGEMENT: AudespSubmission.AjusteTypeChoices.CONTRATO_GESTAO,
    Contract.ConcessionChoices.PARTNERSHIP: AudespSubmission.AjusteTypeChoices.TERMO_PARCERIA,
    Contract.ConcessionChoices.COLLABORATION: AudespSubmission.AjusteTypeChoices.TERMO_COLABORACAO,
    Contract.ConcessionChoices.DEVELOPMENTO: AudespSubmission.AjusteTypeChoices.TERMO_FOMENTO,
    Contract.ConcessionChoices.AGREEMENT: AudespSubmission.AjusteTypeChoices.CONVENIO,
}


class AudespFaseVBuildForm(forms.Form):
    fiscal_year = forms.IntegerField(
        label="Exercício",
        min_value=2000,
        max_value=2100,
        initial=timezone.now().year,
        widget=forms.NumberInput(attrs={"class": "filter-field__control"}),
    )
    ajuste_type = forms.ChoiceField(
        label="Tipo de ajuste (AUDESP)",
        choices=REAL_AJUSTE_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "filter-field__control"}),
    )


# --- Fase IV (contract-detail tab + the dedicated Ajuste creation page).
# See AUDESP_FASE_IV_AUDIT.md §4 for why `codigo_edital`/`itens` are
# required, explicit user inputs rather than fields derived from the
# contract: both reference a Licitação/Dispensa record registered
# elsewhere (typically TCE-SP's own Portal AUDESP), which this codebase
# deliberately does not manage. ---


class AudespFaseIVAjusteForm(forms.Form):
    codigo_edital = forms.CharField(
        label="Código do edital/dispensa",
        max_length=25,
        widget=BaseCharFieldFormWidget(placeholder="Ex.: 123/2026"),
        help_text=(
            "Código do processo de licitação/dispensa já registrado no "
            "Portal AUDESP — consulte o setor de licitações se não souber."
        ),
    )
    itens = forms.CharField(
        label="Itens contratados",
        widget=BaseCharFieldFormWidget(placeholder="Ex.: 1, 2, 4"),
        help_text=(
            "Números dos itens do edital/dispensa efetivamente contratados, "
            "separados por vírgula."
        ),
    )
    retificacao = forms.BooleanField(
        label="Esta é uma retificação de um envio anterior",
        required=False,
    )

    def clean_itens(self):
        raw = self.cleaned_data["itens"]
        itens = []
        for chunk in raw.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                item = int(chunk)
            except ValueError:
                raise forms.ValidationError(
                    f"“{chunk}” não é um número de item válido."
                )
            if item < 0:
                raise forms.ValidationError(
                    f"“{chunk}” não é um número de item válido."
                )
            itens.append(item)
        if not itens:
            raise forms.ValidationError(
                "Informe ao menos um item, separado por vírgula."
            )
        return itens


class AudespFaseIVEmpenhoForm(forms.Form):
    budget_commitment = forms.ModelChoiceField(
        queryset=BudgetCommitment.objects.none(),
        label="Empenho",
        empty_label="Selecione um empenho",
        widget=BaseSelectFormWidget(),
    )

    def __init__(self, *args, contract=None, **kwargs):
        super().__init__(*args, **kwargs)
        if contract is not None:
            self.fields[
                "budget_commitment"
            ].queryset = contract.budget_commitments.filter(
                deleted_at__isnull=True
            ).order_by("-issue_date")
