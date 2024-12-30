import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models.query import QuerySet
from django.shortcuts import redirect
from django.views.generic import DetailView, ListView, TemplateView

from activity.models import ActivityLog
from contracts.forms import ContractCreateForm
from contracts.models import Contract
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
        queryset = super().get_queryset()
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

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


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
