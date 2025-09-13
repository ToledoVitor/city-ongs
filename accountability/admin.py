from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from accountability.models import (
    Accountability,
    AccountabilityFile,
    Expense,
    ExpenseFile,
    Favored,
    ResourceSource,
    Revenue,
    RevenueFile,
)
from utils.admin import BaseModelAdmin


class AccountabilityFileInline(admin.TabularInline):
    model = AccountabilityFile
    extra = 0
    fields = ("name", "file")


@admin.register(Accountability)
class AccountabilityAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "month",
        "year",
        "status",
        "created_at",
    )
    list_filter = (
        "organization",
        "status",
        "contract",
        "month",
        "year",
    )
    search_fields = ("contract__name", "month", "year")
    inlines = [AccountabilityFileInline]
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "contract",
                    "status",
                )
            },
        ),
        (
            _("Datas"),
            {
                "fields": (
                    "month",
                    "year",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


class ExpenseFileInline(admin.TabularInline):
    model = ExpenseFile
    extra = 0
    fields = ("name", "file")


@admin.register(Expense)
class ExpenseAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "accountability",
        "identification",
        "favored",
        "value",
        "competency",
        "status",
        "paid",
        "conciled",
        "created_at",
    )
    list_filter = (
        "organization",
        "accountability__contract",
        "status",
        "paid",
        "conciled",
        "planned",
        "competency",
        "liquidation",
        "source",
        "nature",
    )
    search_fields = (
        "identification",
        "favored__name",
        "favored__document",
        "accountability__contract__name",
        "observations",
        "document_number",
    )
    inlines = [ExpenseFileInline]
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "accountability",
                    "identification",
                    "favored",
                    "source",
                    "item",
                    "value",
                    "nature",
                )
            },
        ),
        (
            _("Status e Flags"),
            {
                "fields": (
                    "status",
                    "paid",
                    "conciled",
                    "planned",
                    "pendencies",
                )
            },
        ),
        (
            _("Datas"),
            {
                "fields": (
                    "competency",
                    "due_date",
                    "liquidation",
                    "conciled_at",
                    "deleted_at",
                )
            },
        ),
        (
            _("Documentos"),
            {
                "fields": (
                    "document_type",
                    "document_number",
                    "liquidation_form",
                )
            },
        ),
        (
            _("Observações"),
            {
                "fields": (
                    "observations",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


class RevenueFileInline(admin.TabularInline):
    model = RevenueFile
    extra = 0
    fields = ("name", "file")


@admin.register(Revenue)
class RevenueAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "accountability",
        "source",
        "value",
        "competency",
        "receive_date",
        "created_at",
    )
    list_filter = (
        "organization",
        "accountability",
        "source",
        "competency",
        "receive_date",
    )
    search_fields = (
        "identification",
        "accountability__contract__name",
        "observations",
    )
    inlines = [RevenueFileInline]
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "accountability",
                    "identification",
                    "source",
                    "bank_account",
                    "value",
                    "revenue_nature",
                )
            },
        ),
        (
            _("Detalhes"),
            {"fields": ("observations", "created_at", "updated_at")},
        ),
    )


@admin.register(Favored)
class FavoredAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "name",
        "document",
        "created_at",
    )
    list_filter = ("organization",)
    search_fields = ("name", "document")


@admin.register(ResourceSource)
class ResourceSourceAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "name",
        "document",
        "origin",
        "category",
        "created_at",
    )
    list_filter = (
        "organization",
        "origin",
        "category",
    )
    search_fields = ("name", "document", "contract_number")
