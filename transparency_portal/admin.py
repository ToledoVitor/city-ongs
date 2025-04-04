from django.contrib import admin

from .models import (
    AccountabilityReport,
    FinancialTransfer,
    IrregularityReport,
    PartnershipTransparency,
)


@admin.register(PartnershipTransparency)
class PartnershipTransparencyAdmin(admin.ModelAdmin):
    list_display = ("contract", "organization", "last_updated", "is_public")
    list_filter = ("is_public", "last_updated")
    search_fields = ("contract__name", "organization__organization__name")
    readonly_fields = ("last_updated",)
    ordering = ("-last_updated",)


@admin.register(FinancialTransfer)
class FinancialTransferAdmin(admin.ModelAdmin):
    list_display = (
        "partnership",
        "transfer_date",
        "value",
        "document_type",
        "document_number",
    )
    list_filter = ("transfer_date", "document_type")
    search_fields = ("partnership__contract__name", "document_number")
    ordering = ("-transfer_date",)


@admin.register(AccountabilityReport)
class AccountabilityReportAdmin(admin.ModelAdmin):
    list_display = (
        "partnership",
        "accountability",
        "activities_description",
        "goals_achievement",
    )
    list_filter = ("accountability__status",)
    search_fields = ("partnership__contract__name", "activities_description")
    ordering = ("-accountability__year", "-accountability__month")


@admin.register(IrregularityReport)
class IrregularityReportAdmin(admin.ModelAdmin):
    list_display = ("partnership", "report_date", "status", "resolution")
    list_filter = ("status", "report_date")
    search_fields = ("partnership__contract__name", "description")
    ordering = ("-report_date",)
