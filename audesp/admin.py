from django.contrib import admin

from audesp.models import AudespSubmission
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
