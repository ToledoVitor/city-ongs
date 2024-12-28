from typing import Any
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.views.generic import TemplateView, DetailView, ListView
from utils.mixins import AdminRequiredMixin

from django.shortcuts import redirect

from contracts.models import Contract
from contracts.forms import ContractCreateForm


class ContractsListView(LoginRequiredMixin, ListView):
    model = Contract
    context_object_name = "contracts_list"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "contracts/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return self.model.objects.all()


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
        context["form"] = ContractCreateForm()
        return context

    def post(self, request, *args, **kwargs):
        form = ContractCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("contracts:contracts-list")
        return self.render_to_response(self.get_context_data(form=form))
