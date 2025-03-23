from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from utils.admin import BaseModelAdmin
from bank.models import BankAccount, BankStatement, Transaction


class BankStatementInline(admin.TabularInline):
    model = BankStatement
    extra = 0
    readonly_fields = ("opening_balance", "closing_balance")
    fields = (
        "reference_month",
        "reference_year",
        "opening_balance",
        "closing_balance",
    )


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ("amount", "date", "transaction_number")
    fields = ("date", "transaction_type", "amount", "name", "memo")


@admin.register(BankAccount)
class BankAccountAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "bank_name",
        "account",
        "account_type",
        "agency",
        "balance",
        "origin",
    )
    list_filter = ("organization", "account_type", "origin", "bank_name")
    search_fields = ("bank_name", "account", "agency")
    readonly_fields = ("balance",)
    inlines = [BankStatementInline, TransactionInline]
    fieldsets = (
        (_("Informações Básicas"), {
            "fields": (
                "organization",
                "bank_name",
                "bank_id",
                "account",
                "account_type",
                "agency",
            )
        }),
        (_("Informações Financeiras"), {
            "fields": ("balance", "origin")
        }),
    )


@admin.register(BankStatement)
class BankStatementAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "bank_account",
        "reference_month",
        "reference_year",
        "opening_balance",
        "closing_balance",
    )
    list_filter = (
        "organization",
        "reference_month",
        "reference_year",
        "bank_account",
    )
    search_fields = ("bank_account__bank_name", "bank_account__account")
    readonly_fields = ("opening_balance", "closing_balance")
    fieldsets = (
        (_("Conta Bancária"), {
            "fields": ("organization", "bank_account")
        }),
        (_("Período"), {
            "fields": ("reference_month", "reference_year")
        }),
        (_("Saldos"), {
            "fields": ("opening_balance", "closing_balance")
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "bank_account",
        "date",
        "transaction_type",
        "amount",
        "name",
    )
    list_filter = (
        "organization",
        "transaction_type",
        "date",
        "bank_account",
    )
    search_fields = (
        "name",
        "memo",
        "bank_account__bank_name",
        "bank_account__account",
    )   
    readonly_fields = ("amount", "date", "transaction_number")
    fieldsets = (
        (_("Informações Básicas"), {
            "fields": (
                "organization",
                "bank_account",
                "date",
                "transaction_type",
                "transaction_number",
            )
        }),
        (_("Detalhes da Transação"), {
            "fields": ("amount", "name", "memo")
        }),
        (_("Associações"), {
            "fields": (
                "expense",
                "revenue",
                "expenses",
                "revenues",
            ),
            "classes": ("collapse",),
        }),
    )
