from django import forms
from django.conf import settings

from audesp import secrets as audesp_secrets
from audesp.models import AudespCredential


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
