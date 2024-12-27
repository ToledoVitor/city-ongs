from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView
from utils.mixins import AdminRequiredMixin

from django.shortcuts import redirect

from contracts.models import Contract
from contracts.forms import ContractCreateForm


class ContractsListView(LoginRequiredMixin, TemplateView):
    template_name = "contracts/contracts-list.html"
    login_url = "/accounts/login"

    def get_context_data(self, **kwargs) -> dict:
        return {
            "user": self.request.user,
            "contract_results": Contract.objects.all(),
        }


class ContractsDetailView(LoginRequiredMixin, DetailView):
    model = Contract

    template_name = "contracts/contracts-detail.html"
    context_object_name = "contract"

    login_url = "/accounts/login"

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


class ContractCreateView(AdminRequiredMixin, TemplateView):
    template_name = "contracts/contracts-create.html"
    login_url = "/accounts/login"

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
