from django import forms
from django.conf import settings
from django.contrib import admin

from audesp import secrets as audesp_secrets
from audesp.models import AudespCredential, AudespSubmission
from utils.admin import BaseModelAdmin


@admin.register(AudespSubmission)
class AudespSubmissionAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "fiscal_year",
        "ajuste_type",
        "retificacao",
        "status",
        "protocol_number",
        "built_at",
    )
    list_filter = (
        "organization",
        "ajuste_type",
        "retificacao",
        "status",
        "fiscal_year",
    )
    search_fields = ("id", "contract__name", "protocol_number")
    readonly_fields = ("payload", "validation_errors", "built_at")


class AudespCredentialAdminForm(forms.ModelForm):
    """Username/password are never stored on the model (see
    `AudespCredential`'s docstring) — this form only collects them to hand
    off to `audesp.secrets.set_credentials`, which writes to GCP Secret
    Manager. In DEVELOPMENT there's nothing to write here: local credentials
    come from `.env`, so both fields are disabled with a pointer to it.
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
            elif not instance.pk:
                raise forms.ValidationError(
                    "Usuário e senha são obrigatórios para uma nova credencial."
                )
        if commit:
            instance.save()
        return instance


@admin.register(AudespCredential)
class AudespCredentialAdmin(BaseModelAdmin):
    form = AudespCredentialAdminForm
    list_display = ("city_hall", "environment", "is_active")
    list_filter = ("city_hall", "environment", "is_active")
