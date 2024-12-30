import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView

from accountability.forms import ExpenseSourceCreateForm, RevenueSourceCreateForm
from accountability.models import ExpenseSource, RevenueSource
from activity.models import ActivityLog

logger = logging.getLogger(__name__)


class ExpenseSourceListView(LoginRequiredMixin, ListView):
    model = ExpenseSource
    context_object_name = "sources"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "accountability/expense-source/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            city_hall__in=self.request.user.city_halls.all()
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ExpenseSourceCreateView(LoginRequiredMixin, TemplateView):
    template_name = "accountability/expense-source/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = ExpenseSourceCreateForm(request=self.request)

        return context

    def post(self, request, *args, **kwargs):
        # TODO: should check any user access?
        form = ExpenseSourceCreateForm(request.POST, request=request)
        if form.is_valid():
            with transaction.atomic():
                source = form.save()

                logger.info(f"{request.user.id} - Created new revenue source")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATE_EXPENSE_SOURCE,
                    target_object_id=source.id,
                    target_content_object=source,
                )
                return redirect("accountability:expenses-source-list")

        return self.render_to_response(self.get_context_data(form=form))


class RevenueSourceListView(LoginRequiredMixin, ListView):
    model = RevenueSource
    context_object_name = "sources"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "accountability/revenue-source/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            city_hall__in=self.request.user.city_halls.all()
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class RevenueSourceCreateView(LoginRequiredMixin, TemplateView):
    template_name = "accountability/revenue-source/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = RevenueSourceCreateForm(request=self.request)

        return context

    def post(self, request, *args, **kwargs):
        # TODO: should check any user access?
        form = RevenueSourceCreateForm(request.POST, request=request)
        if form.is_valid():
            with transaction.atomic():
                source = form.save()

                logger.info(f"{request.user.id} - Created new revenue source")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATE_REVENUE_SOURCE,
                    target_object_id=source.id,
                    target_content_object=source,
                )
                return redirect("accountability:revenues-source-list")

        return self.render_to_response(self.get_context_data(form=form))
