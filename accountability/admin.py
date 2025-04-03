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
    fields = ("name", "type")


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
            {"fields": ("start_date", "end_date", "created_at", "updated_at")},
        ),
    )


class ExpenseFileInline(admin.TabularInline):
    model = ExpenseFile
    extra = 0
    fields = ("name",)


@admin.register(Expense)
class ExpenseAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "accountability",
        "favored",
        "value",
        "competency",
        "status",
        "created_at",
    )
    list_filter = (
        "organization",
        "accountability",
        "status",
        "competency",
        "paid",
        "conciled",
    )
    search_fields = (
        "identification",
        "favored__name",
        "accountability__contract__name",
    )
    inlines = [ExpenseFileInline]
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "accountability",
                    "favored",
                    "value",
                    "date",
                )
            },
        ),
        (_("Detalhes"), {"fields": ("description", "created_at", "updated_at")}),
    )


class RevenueFileInline(admin.TabularInline):
    model = RevenueFile
    extra = 0
    fields = ("name",)


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
    search_fields = ("description", "accountability__contract__number", "source__name")
    inlines = [RevenueFileInline]
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "accountability",
                    "source",
                    "value",
                    "date",
                )
            },
        ),
        (_("Detalhes"), {"fields": ("description", "created_at", "updated_at")}),
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
