from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from accountability.models import (
    Accountability,
    AccountabilityFile,
    ActivityReportPublication,
    ActivityReportPublicationStatus,
    AnnualStatement,
    AvailableFunds,
    BalanceAdjustment,
    BankBalance,
    BoardParticipation,
    BudgetCommitment,
    ConclusiveOpinion,
    ConclusiveOpinionDeclaration,
    ConflictOfInterestDeclaration,
    Deduction,
    EvaluationReport,
    Expense,
    ExpenseFile,
    ExpenseRejection,
    Favored,
    FinancialStatements,
    FinancialStatementsPublication,
    FundTransfer,
    OpinionOrMinutes,
    OpinionOrMinutesPublication,
    PhysicalFinancialExecutionStatement,
    PhysicalFinancialExecutionStatementPublication,
    PurchasingRegulation,
    PurchasingRegulationPublication,
    Refund,
    RelatedCompany,
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
    search_fields = ("id", "contract__name", "month", "year")
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
        "id",
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
            _("Dados AUDESP"),
            {
                "fields": (
                    "creditor_document_type",
                    "issuing_state",
                    "expense_category_type",
                    "encumbrance_value",
                    "from_apportionment",
                    "apportionment_percentage",
                    "funding_source_type",
                    "payment_method_type",
                    "transaction_number",
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
        "id",
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
                    "funding_source_type",
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
    search_fields = ("id", "name", "document")


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
    search_fields = ("id", "name", "document", "contract_number")


class PurchasingRegulationInline(admin.StackedInline):
    model = PurchasingRegulation
    extra = 0


class PhysicalFinancialExecutionStatementInline(admin.StackedInline):
    model = PhysicalFinancialExecutionStatement
    extra = 0


class FinancialStatementsInline(admin.StackedInline):
    model = FinancialStatements
    extra = 0


class ActivityReportPublicationStatusInline(admin.StackedInline):
    model = ActivityReportPublicationStatus
    extra = 0


class OpinionOrMinutesInline(admin.TabularInline):
    model = OpinionOrMinutes
    extra = 0
    fields = ("type", "was_published", "conclusion")


class EvaluationReportInline(admin.TabularInline):
    model = EvaluationReport
    extra = 0
    fields = ("type", "final_report_issued", "conclusion")


class ConflictOfInterestDeclarationInline(admin.StackedInline):
    model = ConflictOfInterestDeclaration
    extra = 0


class ConclusiveOpinionInline(admin.StackedInline):
    model = ConclusiveOpinion
    extra = 0


class AvailableFundsInline(admin.StackedInline):
    model = AvailableFunds
    extra = 0


class PurchasingRegulationPublicationInline(admin.TabularInline):
    model = PurchasingRegulationPublication
    extra = 0
    fields = (
        "phase",
        "publication_vehicle_type",
        "vehicle_name",
        "publication_date",
        "website_url",
    )


@admin.register(PurchasingRegulation)
class PurchasingRegulationAdmin(BaseModelAdmin):
    list_display = ("organization", "annual_statement", "had_initial_publication")
    list_filter = ("organization",)
    inlines = [PurchasingRegulationPublicationInline]


class PhysicalFinancialExecutionStatementPublicationInline(admin.TabularInline):
    model = PhysicalFinancialExecutionStatementPublication
    extra = 0
    fields = (
        "publication_vehicle_type",
        "vehicle_name",
        "publication_date",
        "website_url",
    )


@admin.register(PhysicalFinancialExecutionStatement)
class PhysicalFinancialExecutionStatementAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "annual_statement",
        "has_statement",
    )
    list_filter = ("organization",)
    inlines = [PhysicalFinancialExecutionStatementPublicationInline]


class FinancialStatementsPublicationInline(admin.TabularInline):
    model = FinancialStatementsPublication
    extra = 0
    fields = (
        "publication_vehicle_type",
        "vehicle_name",
        "publication_date",
        "website_url",
    )


@admin.register(FinancialStatements)
class FinancialStatementsAdmin(BaseModelAdmin):
    list_display = ("organization", "annual_statement", "accountant_crc_number")
    list_filter = ("organization",)
    inlines = [FinancialStatementsPublicationInline]


class ActivityReportPublicationInline(admin.TabularInline):
    model = ActivityReportPublication
    extra = 0
    fields = (
        "publication_vehicle_type",
        "vehicle_name",
        "publication_date",
        "website_url",
    )


@admin.register(ActivityReportPublicationStatus)
class ActivityReportPublicationStatusAdmin(BaseModelAdmin):
    list_display = ("organization", "annual_statement", "was_published_in_fiscal_year")
    list_filter = ("organization",)
    inlines = [ActivityReportPublicationInline]


class OpinionOrMinutesPublicationInline(admin.TabularInline):
    model = OpinionOrMinutesPublication
    extra = 0
    fields = (
        "publication_vehicle_type",
        "vehicle_name",
        "publication_date",
        "website_url",
    )


@admin.register(OpinionOrMinutes)
class OpinionOrMinutesAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "annual_statement",
        "type",
        "was_published",
        "conclusion",
    )
    list_filter = ("organization", "type", "conclusion")
    inlines = [OpinionOrMinutesPublicationInline]


@admin.register(EvaluationReport)
class EvaluationReportAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "annual_statement",
        "type",
        "final_report_issued",
        "conclusion",
    )
    list_filter = ("organization", "type", "conclusion")


@admin.register(AnnualStatement)
class AnnualStatementAdmin(BaseModelAdmin):
    list_display = ("organization", "contract", "fiscal_year", "statement_date")
    list_filter = ("organization", "fiscal_year")
    search_fields = ("id", "contract__name")
    inlines = [
        PurchasingRegulationInline,
        PhysicalFinancialExecutionStatementInline,
        FinancialStatementsInline,
        ActivityReportPublicationStatusInline,
        OpinionOrMinutesInline,
        EvaluationReportInline,
        ConflictOfInterestDeclarationInline,
        ConclusiveOpinionInline,
        AvailableFundsInline,
    ]


@admin.register(BankBalance)
class BankBalanceAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "available_funds",
        "bank_account",
        "account_type",
        "bank_balance",
        "accounting_balance",
    )
    list_filter = ("organization", "account_type")


class RelatedCompanyInline(admin.TabularInline):
    model = RelatedCompany
    extra = 0


class BoardParticipationInline(admin.TabularInline):
    model = BoardParticipation
    extra = 0


class ConclusiveOpinionDeclarationInline(admin.TabularInline):
    model = ConclusiveOpinionDeclaration
    extra = 0
    fields = ("declaration_type", "answer", "justification")


@admin.register(ConflictOfInterestDeclaration)
class ConflictOfInterestDeclarationAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "annual_statement",
        "hired_related_companies",
        "had_political_agents_in_board",
    )
    list_filter = ("organization",)
    inlines = [RelatedCompanyInline, BoardParticipationInline]


@admin.register(ConclusiveOpinion)
class ConclusiveOpinionAdmin(BaseModelAdmin):
    list_display = ("organization", "annual_statement", "conclusion")
    list_filter = ("organization", "conclusion")
    inlines = [ConclusiveOpinionDeclarationInline]


@admin.register(BudgetCommitment)
class BudgetCommitmentAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "number",
        "issue_date",
        "value",
        "funding_source_type",
    )
    list_filter = ("organization", "contract", "funding_source_type")
    search_fields = ("id", "number", "contract__name", "spending_authority_cpf")


@admin.register(FundTransfer)
class FundTransferAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "budget_commitment",
        "transfer_date",
        "planned_value",
        "transferred_value",
    )
    list_filter = ("organization", "contract")
    search_fields = ("id", "contract__name", "document_number")


@admin.register(ExpenseRejection)
class ExpenseRejectionAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "expense",
        "payment_date",
        "analysis_result",
        "rejected_value",
    )
    list_filter = ("organization", "contract", "analysis_result")
    search_fields = ("id", "contract__name")


@admin.register(Deduction)
class DeductionAdmin(BaseModelAdmin):
    list_display = ("organization", "contract", "date", "description", "value")
    list_filter = ("organization", "contract")
    search_fields = ("id", "contract__name", "description")


@admin.register(Refund)
class RefundAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "contract",
        "date",
        "nature",
        "value",
    )
    list_filter = ("organization", "contract", "nature")
    search_fields = ("id", "contract__name")


@admin.register(BalanceAdjustment)
class BalanceAdjustmentAdmin(BaseModelAdmin):
    list_display = ("organization", "contract", "type", "date", "value")
    list_filter = ("organization", "contract", "type")
    search_fields = ("id", "contract__name")
