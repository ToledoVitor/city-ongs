import logging
from typing import Any

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from accountability.models import Accountability
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView

from accountability.forms import (
    AccountabilityCreateForm,
    ExpenseSourceCreateForm,
    RevenueSourceCreateForm,
    ExpenseCreateForm,
    RevenueCreateForm,
)
from accountability.models import ExpenseSource, RevenueSource
from activity.models import ActivityLog
from contracts.models import Contract

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
                    action=ActivityLog.ActivityLogChoices.CREATED_EXPENSE_SOURCE,
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
                    action=ActivityLog.ActivityLogChoices.CREATED_REVENUE_SOURCE,
                    target_object_id=source.id,
                    target_content_object=source,
                )
                return redirect("accountability:revenues-source-list")

        return self.render_to_response(self.get_context_data(form=form))


def create_contract_accountability_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        form = AccountabilityCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                accountability = Accountability.objects.create(
                    contract=contract,
                    month=form.cleaned_data["month"],
                    year=form.cleaned_data["year"],
                )
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_ACCOUNTABILITY,
                    target_object_id=accountability.id,
                    target_content_object=accountability,
                )
            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )
        else:
            return render(
                request,
                "accountability/accountability/create.html",
                {"contract": contract, "form": form},
            )
    else:
        form = AccountabilityCreateForm()
        return render(
            request,
            "accountability/accountability/create.html",
            {"contract": contract, "form": form},
        )


def accountability_detail_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    expenses_list = accountability.expenses.all()
    revenues_list = accountability.revenues.all()

    expenses_paginator = Paginator(expenses_list, 5)
    expenses_page_number = request.GET.get("expenses_page")
    expenses_page = expenses_paginator.get_page(expenses_page_number)

    revenues_paginator = Paginator(revenues_list, 5)
    revenues_page_number = request.GET.get("revenues_page")
    revenues_page = revenues_paginator.get_page(revenues_page_number)

    context = {
        "object": accountability,
        "expenses_page": expenses_page,
        "revenues_page": revenues_page,
    }
    return render(request, "accountability/accountability/detail.html", context)


def create_accountability_revenue_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    accountability = get_object_or_404(Accountability, id=pk)
    if request.method == "POST":
        form = RevenueCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                revenue = form.save()
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_REVENUE,
                    target_object_id=revenue.id,
                    target_content_object=revenue,
                )
            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )
        else:
            return render(
                request,
                "accountability/revenues/create.html",
                {"accountability": accountability, "form": form},
            )
    else:
        form = RevenueCreateForm()
        return render(
            request,
            "accountability/revenues/create.html",
            {"accountability": accountability, "form": form},
        )


def create_accountability_expense_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    accountability = get_object_or_404(Accountability, id=pk)
    if request.method == "POST":
        form = ExpenseCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save()
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_EXPENSE,
                    target_object_id=expense.id,
                    target_content_object=expense,
                )
            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )
        else:
            return render(
                request,
                "accountability/expenses/create.html",
                {"accountability": accountability, "form": form},
            )
    else:
        form = ExpenseCreateForm()
        return render(
            request,
            "accountability/expenses/create.html",
            {"accountability": accountability, "form": form},
        )
