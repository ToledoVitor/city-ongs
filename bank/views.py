import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction as django_transaction
from django.db.models import Prefetch
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView

from activity.models import ActivityLog
from bank.forms import (
    CreateBankAccountForm,
    TransactionFormSet,
    UpdateBankStatementForm,
    UpdateOFXForm,
    UploadOFXForm,
)
from bank.models import BankAccount, BankStatement
from bank.services.ofx_parser import OFXFileParser
from contracts.models import Contract

logger = logging.getLogger(__name__)


class BankAccountDetailView(LoginRequiredMixin, DetailView):
    model = BankAccount
    template_name = "bank-account/detail.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related(
                "contract",
            )
            .prefetch_related(
                Prefetch(
                    "statements",
                    queryset=BankStatement.objects.order_by("-closing_date"),
                ),
                Prefetch(
                    "transactions", queryset=BankStatement.objects.order_by("-date")
                ),
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


def create_bank_account_ofx_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        form = UploadOFXForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                bank_account = OFXFileParser(
                    ofx_file=request.FILES["ofx_file"]
                ).create_bank_account(
                    contract=contract, account_type=form.data["account_type"]
                )

                logger.info(f"{request.user.id} - Created new bank account")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_BANK_ACCOUNT,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPLOADED_BALANCE_FILE,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                return redirect("contracts:contracts-detail", pk=contract.id)
            except ValidationError:
                return render(
                    request,
                    "bank-account/ofx-create.html",
                    {"form": form, "contract": contract, "account_exists": True},
                )
    else:
        form = UploadOFXForm()

    return render(
        request, "bank-account/ofx-create.html", {"form": form, "contract": contract}
    )


def update_bank_account_ofx_view(request, pk):
    bank_account = get_object_or_404(BankAccount, id=pk)
    if request.method == "POST":
        form = UpdateOFXForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                OFXFileParser(
                    ofx_file=request.FILES["ofx_file"]
                ).update_bank_account_balance(bank_account=bank_account)

                logger.info(f"{request.user.id} - Updated bank account")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPLOADED_BALANCE_FILE,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                return redirect("bank:bank-accounts-detail", pk=bank_account.id)
            except ValidationError:
                return render(
                    request,
                    "bank-account/ofx-update.html",
                    {"form": form, "object": bank_account, "statement_exists": True},
                )
    else:
        form = UpdateOFXForm()
        return render(
            request,
            "bank-account/ofx-update.html",
            {"form": form, "object": bank_account},
        )


def create_bank_account_manual_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        form = CreateBankAccountForm(request.POST)
        transactions_formset = TransactionFormSet(request.POST)
        if form.is_valid() and transactions_formset.is_valid():
            if _account_type_already_created(
                contract, form.cleaned_data["account_type"]
            ):
                return render(
                    request,
                    "bank-account/manual-create.html",
                    {
                        "form": form,
                        "contract": contract,
                        "transactions_formset": transactions_formset,
                        "account_exists": True,
                    },
                )

            if BankAccount.objects.filter(
                bank_name=form.cleaned_data["bank_name"],
                bank_id=form.cleaned_data["bank_id"],
                account=form.cleaned_data["account"],
                account_type=form.cleaned_data["account_type"],
            ).exists():
                return render(
                    request,
                    "bank-account/manual-create.html",
                    {
                        "form": form,
                        "contract": contract,
                        "transactions_formset": transactions_formset,
                    },
                )

            with django_transaction.atomic():
                bank_account = BankAccount.objects.create(
                    bank_name=form.cleaned_data["bank_name"],
                    bank_id=form.cleaned_data["bank_id"],
                    account=form.cleaned_data["account"],
                    account_type=form.cleaned_data["account_type"],
                    agency=form.cleaned_data["agency"],
                    balance=form.cleaned_data["balance"],
                    origin=form.cleaned_data["origin"],
                )
                BankStatement.objects.create(
                    bank_account=bank_account,
                    closing_balance=form.cleaned_data["balance"],
                    reference_month=form.cleaned_data["closing_date"].month,
                    reference_year=form.cleaned_data["closing_date"].year,
                )

                transactions = transactions_formset.save(commit=False)
                for transaction in transactions:
                    transaction.bank_account = bank_account
                    transaction.save()

                if bank_account.account_type == "CHECKING":
                    contract.checking_account = bank_account
                else:
                    contract.investing_account = bank_account

                contract.save()

                logger.info(f"{request.user.id} - Created new bank account")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_BANK_ACCOUNT,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                return redirect("bank:bank-accounts-detail", pk=bank_account.id)
    else:
        form = CreateBankAccountForm()
        transactions_formset = TransactionFormSet()

    return render(
        request,
        "bank-account/manual-create.html",
        {
            "form": form,
            "contract": contract,
            "transactions_formset": transactions_formset,
        },
    )


def update_bank_account_manual_view(request, pk):
    bank_account = get_object_or_404(BankAccount, id=pk)
    if request.method == "POST":
        form = UpdateBankStatementForm(request.POST)
        transactions_formset = TransactionFormSet(request.POST)
        if form.is_valid() and transactions_formset.is_valid():
            if _statement_already_uploaded(
                bank_account=bank_account,
                month=form.cleaned_data["reference_month"],
                year=form.cleaned_data["reference_year"],
            ):
                return render(
                    request,
                    "bank-account/manual-update.html",
                    {
                        "form": form,
                        "object": bank_account,
                        "transactions_formset": transactions_formset,
                        "statement_exists": True,
                    },
                )

            with django_transaction.atomic():
                BankStatement.objects.create(
                    bank_account=bank_account,
                    reference_month=form.cleaned_data["reference_month"],
                    reference_year=form.cleaned_data["reference_year"],
                    opening_balance=form.cleaned_data["opening_balance"],
                    closing_balance=form.cleaned_data["closing_balance"],
                )

                transactions = transactions_formset.save(commit=False)
                for transaction in transactions:
                    transaction.bank_account = bank_account
                    transaction.save()

                logger.info(f"{request.user.id} - Updated bank account")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_BANK_ACCOUNT,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                return redirect("bank:bank-accounts-detail", pk=bank_account.id)

    else:
        form = UpdateBankStatementForm()
        transactions_formset = TransactionFormSet()
        return render(
            request,
            "bank-account/manual-update.html",
            {
                "form": form,
                "object": bank_account,
                "transactions_formset": transactions_formset,
            },
        )


def _statement_already_uploaded(bank_account: BankAccount, month: int, year: int):
    return BankStatement.objects.filter(
        bank_account=bank_account, reference_month=month, reference_year=year
    ).exists()


def _account_type_already_created(contract: Contract, account_type: str):
    if account_type == "CHECKING":
        return contract.checking_account is not None

    if account_type == "INVESTING":
        return contract.investing_account is not None

    return True
