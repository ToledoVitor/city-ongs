from django.contrib import admin

from audesp.forms import AudespCredentialAdminForm
from audesp.models import AudespCredential, AudespSubmission
from utils.admin import BaseModelAdmin


@admin.register(AudespSubmission)
class AudespSubmissionAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "fiscal_year",
        "ajuste_type",
        "status",
        "protocol_number",
        "built_at",
    )
    list_filter = ("organization", "ajuste_type", "status", "fiscal_year")
    search_fields = ("id", "contract__name", "protocol_number")
    readonly_fields = ("payload", "validation_errors", "built_at")


@admin.register(AudespCredential)
class AudespCredentialAdmin(BaseModelAdmin):
    form = AudespCredentialAdminForm
    list_display = ("city_hall", "environment", "is_active")
    list_filter = ("city_hall", "environment", "is_active")
