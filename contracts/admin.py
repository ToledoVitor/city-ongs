from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from contracts.models import (
    Company,
    Contract,
    ContractAddendum,
    ContractExecution,
    ContractExecutionActivity,
    ContractExecutionFile,
    ContractGoal,
    ContractGoalReview,
    ContractInterestedPart,
    ContractItem,
    ContractItemNewValueRequest,
    ContractItemPurchaseProcessDocument,
    ContractItemReview,
    ContractItemSupplement,
    ContractStep,
)
from utils.admin import BaseModelAdmin


class ContractAddendumInline(admin.TabularInline):
    model = ContractAddendum
    extra = 0
    fields = ("number", "status", "description")


class ContractGoalInline(admin.TabularInline):
    model = ContractGoal
    extra = 0
    fields = ("description", "status")


class ContractStepInline(admin.TabularInline):
    model = ContractStep
    extra = 0
    readonly_fields = ("created_at",)
    fields = (
        "name",
        "status",
        "description",
        "created_at",
    )


class ContractItemInline(admin.TabularInline):
    model = ContractItem
    extra = 0
    fields = ("description", "value")


class ContractExecutionInline(admin.TabularInline):
    model = ContractExecution
    extra = 0
    fields = ("status", "start_date", "end_date", "description")


class ContractItemNewValueRequestInline(admin.TabularInline):
    model = ContractItemNewValueRequest
    fk_name = "raise_item"
    extra = 0
    readonly_fields = ("created_at",)
    fields = (
        "raise_item",
        "downgrade_item",
        "month_raise",
        "anual_raise",
        "status",
        "created_at",
    )


@admin.register(Company)
class CompanyAdmin(BaseModelAdmin):
    list_display = ("organization", "name", "cnpj", "created_at")
    list_filter = ("organization",)
    search_fields = ("name", "cnpj")


@admin.register(Contract)
class ContractAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "name",
        "status",
        "created_at",
    )
    list_filter = (
        "organization",
        "status",
        "created_at",
    )
    search_fields = ("name", "description")
    inlines = [
        ContractGoalInline,
        ContractItemInline,
    ]
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "name",
                    "status",
                    "description",
                )
            },
        ),
        (
            _("Datas"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (_("Valores"), {"fields": ("total_value", "monthly_value")}),
    )


class ContractExecutionActivityInline(admin.TabularInline):
    model = ContractExecutionActivity
    extra = 0
    fields = ("type", "status", "description")


class ContractExecutionFileInline(admin.TabularInline):
    model = ContractExecutionFile
    extra = 0
    fields = ("name", "type")


@admin.register(ContractExecution)
class ContractExecutionAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "status",
        "created_at",
    )
    list_filter = (
        "organization",
        "status",
        "contract",
        "created_at",
    )
    search_fields = ("contract__name", "description")
    inlines = [ContractExecutionActivityInline, ContractExecutionFileInline]


class ContractGoalReviewInline(admin.TabularInline):
    model = ContractGoalReview
    extra = 0
    fields = ("reviewer", "comment")


@admin.register(ContractGoal)
class ContractGoalAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "name",
        "created_at",
    )
    list_filter = ("organization", "status", "contract")
    search_fields = ("name", "contract__name")
    inlines = [ContractGoalReviewInline]


class ContractItemReviewInline(admin.TabularInline):
    model = ContractItemReview
    extra = 0
    fields = ("reviewer", "comment")


class ContractItemPurchaseProcessDocumentInline(admin.TabularInline):
    model = ContractItemPurchaseProcessDocument
    extra = 0
    fields = ("file",)


class ContractItemSupplementInline(admin.TabularInline):
    model = ContractItemSupplement
    extra = 0
    fields = ("suplement_value",)


@admin.register(ContractItem)
class ContractItemAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "name",
        "created_at",
    )
    list_filter = ("organization", "contract")
    search_fields = ("name", "contract__name")
    inlines = [
        ContractItemReviewInline,
        ContractItemNewValueRequestInline,
        ContractItemPurchaseProcessDocumentInline,
        ContractItemSupplementInline,
    ]


@admin.register(ContractItemPurchaseProcessDocument)
class ContractItemPurchaseProcessDocumentAdmin(BaseModelAdmin):
    list_display = ("organization", "file", "created_at")
    list_filter = ("organization",)
    search_fields = ("file",)


@admin.register(ContractItemSupplement)
class ContractItemSupplementAdmin(BaseModelAdmin):
    list_display = ("organization", "item", "suplement_value", "status")
    list_filter = ("organization", "item", "status")
    search_fields = ("item__name",)


@admin.register(ContractInterestedPart)
class ContractInterestedPartAdmin(BaseModelAdmin):
    list_display = ("organization", "contract", "user", "interest")
    list_filter = ("organization", "contract", "user", "interest")
    search_fields = ("contract__name", "user__name")
