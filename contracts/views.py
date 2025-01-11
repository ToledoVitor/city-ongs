import logging
from typing import Any

from utils.choices import StatusChoices

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models.query import QuerySet
from django.views.generic import DetailView, ListView, TemplateView

from activity.models import ActivityLog
from contracts.forms import ContractCreateForm
from contracts.models import Contract, ContractItem
from utils.mixins import AdminRequiredMixin

logger = logging.getLogger(__name__)


class ContractsListView(LoginRequiredMixin, ListView):
    model = Contract
    context_object_name = "contracts_list"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "contracts/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset().select_related(
            "contractor_manager",
            "hired_manager",
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ContractsDetailView(LoginRequiredMixin, DetailView):
    model = Contract

    template_name = "contracts/detail.html"
    context_object_name = "contract"

    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().select_related(
            "contractor_company",
            "contractor_manager",
            "hired_company",
            "hired_manager",
            "ong",
        ).prefetch_related(
            "addendums",
            "items",
            "goals",
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context
    
    def post(self, request, pk, *args, **kwargs):
        if not self.request.POST.get("csrfmiddlewaretoken"):
            return redirect("contracts:contracts-list")

        if not (self.request.user and self.request.user.can_change_statuses):
            return redirect("contracts:contracts-list")

        contract = get_object_or_404(Contract, id=pk)
        form_type = self.request.POST.get("form_type", "")

        match form_type:
            case "items_modal":
                item = get_object_or_404(ContractItem, id=request.POST.get("itemId"))
                item.status = request.POST.get("status")
                item.status_pendencies = request.POST.get("pendencies")
                item.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM,
                    target_object_id=item.id,
                    target_content_object=item,
                )

            case _:
                logger.warning(f"form_type: {form_type} is not a valid form")
                return redirect("contracts:contracts-list")

        return redirect("contracts:contracts-detail", pk=contract.id)

class ContractCreateView(AdminRequiredMixin, TemplateView):
    template_name = "contracts/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = ContractCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        form = ContractCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                contract = form.save()

                logger.info(f"{request.user.id} - Created new contract")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT,
                    target_object_id=contract.id,
                    target_content_object=contract,
                )
            return redirect("contracts:contracts-list")

        return self.render_to_response(self.get_context_data(form=form))


def create_contract_item_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")
    
    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        total_expense = request.POST.get("total_expense")
        is_additive = request.POST.get("is_additive", "") == "True" 

        item = ContractItem.objects.create(
            contract=contract,
            name=name,
            description=description,
            total_expense=total_expense,
            is_additive=is_additive,
            status=StatusChoices.ANALYZING,
        )
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_ITEM,
            target_object_id=item.id,
            target_content_object=item,
        )
        return redirect("contracts:contracts-detail", pk=contract.id)

    return render(request, "contracts/items-create.html", {'contract': contract})
