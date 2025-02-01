import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView, TemplateView

from accountability.forms import (
    AccountabilityCreateForm,
    ExpenseForm,
    ExpenseSourceCreateForm,
    FavoredForm,
    RevenueForm,
    RevenueSourceCreateForm,
)
from accountability.models import Accountability, ExpenseSource, Favored, RevenueSource
from accountability.services import AccountabilityCSVExporter
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
            organization=self.request.user.organization
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
            context["form"] = ExpenseSourceCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        # TODO: should check any user access?
        form = ExpenseSourceCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                source = form.save(commit=False)
                source.organization = request.user.organization
                source.save()

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
            organization=self.request.user.organization
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
            context["form"] = RevenueSourceCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        # TODO: should check any user access?
        form = RevenueSourceCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                source = form.save(commit=False)
                source.organization = request.user.organization
                source.save()

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
    expenses_list = accountability.expenses.order_by("-value").select_related(
        "item", "source"
    )
    revenues_list = accountability.revenues.order_by("-value").select_related(
        "bank_account", "source"
    )

    query = request.GET.get("q", "")
    if query:
        expenses_list = expenses_list.filter(
            Q(identification__icontains=query)
            | Q(item__name__icontains=query)
            | Q(source__name__icontains=query)
        )
        revenues_list = revenues_list.filter(
            Q(identification__icontains=query) | Q(source__name__icontains=query)
        )

    expenses_paginator = Paginator(expenses_list, 10)
    expenses_page_number = request.GET.get("expenses_page")
    expenses_page = expenses_paginator.get_page(expenses_page_number)

    revenues_paginator = Paginator(revenues_list, 10)
    revenues_page_number = request.GET.get("revenues_page")
    revenues_page = revenues_paginator.get_page(revenues_page_number)

    context = {
        "object": accountability,
        "expenses_page": expenses_page,
        "revenues_page": revenues_page,
        "search_query": query,
    }
    return render(request, "accountability/accountability/detail.html", context)


def create_accountability_revenue_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    accountability = get_object_or_404(Accountability, id=pk)
    if request.method == "POST":
        form = RevenueForm(request.POST, request=request)
        if form.is_valid():
            with transaction.atomic():
                revenue = form.save(commit=False)
                revenue.accountability = accountability
                revenue.save()

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
        form = RevenueForm(request=request)
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
        form = ExpenseForm(request.POST, request=request, accountability=accountability)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save(commit=False)
                expense.accountability = accountability
                expense.save()

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
        form = ExpenseForm(request=request, accountability=accountability)
        return render(
            request,
            "accountability/expenses/create.html",
            {"accountability": accountability, "form": form},
        )


class FavoredListView(LoginRequiredMixin, ListView):
    model = Favored
    context_object_name = "favoreds_list"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "accountability/favoreds/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            organization=self.request.user.organization
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(document__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FavoredCreateView(LoginRequiredMixin, TemplateView):
    template_name = "accountability/favoreds/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = FavoredForm()

        return context

    def post(self, request, *args, **kwargs):
        # TODO: should check any user access?
        form = FavoredForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                favored = form.save(commit=False)
                favored.organization = request.user.organization
                favored.save()

                logger.info(f"{request.user.id} - Created new favored")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_FAVORED,
                    target_object_id=favored.id,
                    target_content_object=favored,
                )
                return redirect("accountability:favoreds-list")

        return self.render_to_response(self.get_context_data(form=form))


def import_accountability_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    if request.method == "POST":
        step = request.POST.get("step")

        if step == "download":
            accountability = (
                Accountability.objects.select_related(
                    "contract",
                    "contract__organization",
                )
                .prefetch_related(
                    "contract__organization__revenue_sources",
                )
                .get(id=pk)
            )

            xlsx = AccountabilityCSVExporter(accountability=accountability).handle()
            response = HttpResponse(
                xlsx.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="importacao-{accountability.month}-{accountability.year}.xlsx"'
            )
            return response

        elif step == "upload":
            ...

        else:
            return render(
                request,
                "accountability/accountability/import.html",
                {"accountability": accountability},
            )
    else:
        accountability = get_object_or_404(Accountability, id=pk)
        return render(
            request,
            "accountability/accountability/import.html",
            {"accountability": accountability},
        )
