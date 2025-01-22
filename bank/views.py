import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Q
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from activity.models import ActivityLog
from bank.forms import UploadOFXForm, CreateBankAccountForm, TransactionFormSet
from bank.models import BankAccount, BankStatement
from bank.services.ofx_parser import OFXFileParser
from contracts.models import Contract

logger = logging.getLogger(__name__)


class BankAccountsListView(LoginRequiredMixin, ListView):
    model = BankAccount
    context_object_name = "bank_accounts_list"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "bank-account/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "contract",
            )
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(account__icontains=query)
                | Q(bank_name__icontains=query)
                | Q(agency__icontains=query)
                | Q(contract__name__icontains=query)
                | Q(contract__code__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


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
                ).create_bank_account(contract=contract, account_type=form.data["account_type"])

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


def create_bank_account_manual_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        form = CreateBankAccountForm(request.POST)
        transactions_formset = TransactionFormSet(request.POST)
        if form.is_valid():
            try:
                bank_account = OFXFileParser(
                    ofx_file=request.FILES["ofx_file"]
                ).create_bank_account(contract=contract)

                transactions = transactions_formset.save(commit=False)
                for transaction in transactions:
                    transaction.bank_account = bank_account
                    transaction.save()

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
                    "bank-account/manual-create.html",
                    {"form": form, "contract": contract, "account_exists": True},
                )
    else:
        form = CreateBankAccountForm()
        transactions_formset = TransactionFormSet()

    return render(
        request, "bank-account/manual-create.html", {"form": form, "contract": contract, "transactions_formset": transactions_formset}
    )
