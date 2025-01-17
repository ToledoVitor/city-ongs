import logging
from decimal import Decimal
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView, TemplateView

from activity.models import ActivityLog
from bank.forms import BankAccountCreateForm, UploadOFXForm
from bank.models import BankAccount

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


class BankAccountCreateView(LoginRequiredMixin, TemplateView):
    template_name = "bank-account/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = BankAccountCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        form = BankAccountCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                contract = form.save(commit=False)
                contract.balance = Decimal("0.00")
                contract.save()

                logger.info(f"{request.user.id} - Created new contract")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_BANK_ACCOUNT,
                    target_object_id=contract.id,
                    target_content_object=contract,
                )
            return redirect("bank:bank-accounts-list")

        return self.render_to_response(self.get_context_data(form=form))


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


def upload_ofx_view(request):
    if request.method == "POST":
        form = UploadOFXForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            breakpoint()
            return redirect("bank:bank-accounts-list")
    else:
        form = UploadOFXForm(request=request)

    return render(request, "bank-account/create.html", {"form": form})
