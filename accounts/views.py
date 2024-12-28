from typing import Any

from accounts.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.views.generic import ListView, DetailView, TemplateView
from utils.mixins import AdminRequiredMixin

from django.shortcuts import redirect

from accounts.forms import FolderManagerCreateForm, OngAccountantCreateForm


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


class FolderManagerCreateView(AdminRequiredMixin, TemplateView):
    template_name = "accounts/folder-managers/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = FolderManagerCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        form = FolderManagerCreateForm(request.POST)
        if form.is_valid():
            _ = User.objects.create(
                email=form.cleaned_data["email"],
                username=form.cleaned_data["email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                password=form.cleaned_data["password"],
                access_level=User.AccessChoices.FOLDER_MANAGER,
            )
            return redirect("accounts:folder-managers-list")
        return self.render_to_response(self.get_context_data(form=form))


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


class OngAccountantCreateView(AdminRequiredMixin, TemplateView):
    template_name = "accounts/ong-accountants/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = OngAccountantCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        form = OngAccountantCreateForm(request.POST)
        if form.is_valid():
            _ = User.objects.create(
                email=form.cleaned_data["email"],
                username=form.cleaned_data["email"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
                password=form.cleaned_data["password"],
                access_level=User.AccessChoices.ONG_ACCOUNTANT,
            )
            return redirect("accounts:ong-accountants-list")
        return self.render_to_response(self.get_context_data(form=form))
