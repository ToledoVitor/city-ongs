from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView

from contracts.models import Contract


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
