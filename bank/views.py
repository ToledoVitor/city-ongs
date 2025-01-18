import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView

from activity.models import ActivityLog
from bank.forms import UploadOFXForm
from bank.models import BankAccount
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
            .prefetch_related(
                "statements",
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
    context_object_name = "bank_account"

    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related(
                "contract",
            )
            # .prefetch_related(
            # )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


def create_banck_account_view(request):
    if request.method == "POST":
        form = UploadOFXForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            contract = Contract.objects.get(id=form.data["contract"])
            try:
                bank_account = OFXFileParser(
                    ofx_file=request.FILES["ofx_file"]
                ).create_bank_account(contract=contract)

                logger.info(f"{request.user.id} - Created new bank account")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_BANK_ACCOUNT,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                return redirect("bank:bank-accounts-list")
            except ValidationError:
                return render(
                    request,
                    "bank-account/create.html",
                    {"form": form, "account_exists": True},
                )
    else:
        form = UploadOFXForm(request=request)

    return render(request, "bank-account/create.html", {"form": form})
