from typing import Any

from accounts.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.views.generic import ListView, DetailView
from utils.mixins import AdminRequiredMixin


class FolderManagersListView(AdminRequiredMixin, ListView):
    model = User
    context_object_name = "managers_list"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "accounts/folder-managers/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return self.model.objects.filter(access_level=User.AccessChoices.FOLDER_MANAGER)


class FolderManagersDetailView(LoginRequiredMixin, DetailView):
    model = User

    template_name = "accounts/folder-managers/detail.html"
    context_object_name = "manager"

    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


class OngAccountantsListView(AdminRequiredMixin, ListView):
    model = User
    context_object_name = "accountants_list"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "accounts/ong-accountants/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return self.model.objects.filter(access_level=User.AccessChoices.ONG_ACCOUNTANT)


class OngAccountantsDetailView(LoginRequiredMixin, DetailView):
    model = User

    template_name = "accounts/ong-accountants/detail.html"
    context_object_name = "accountant"

    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context
