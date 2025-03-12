import logging
from decimal import Decimal
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, TemplateView, UpdateView

from accountability.forms import (
    AccountabilityCreateForm,
    ExpenseForm,
    FavoredForm,
    ImportXLSXAccountabilityForm,
    ReconcileExpenseForm,
    ReconcileRevenueForm,
    ResourceSourceForm,
    RevenueForm,
)
from accountability.models import (
    Accountability,
    Expense,
    ExpenseFile,
    Favored,
    ResourceSource,
    Revenue,
)
from accountability.services import export_xlsx_model, import_xlsx_model
from activity.models import ActivityLog
from contracts.models import Contract

logger = logging.getLogger(__name__)


class AccountabilityListView(LoginRequiredMixin, ListView):
    model = Accountability
    context_object_name = "accountabilities"
    paginate_by = 10
    ordering = "month"

    template_name = "accountability/accountability/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.select_related(
            "contract",
        ).filter(contract__organization=self.request.user.organization)

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(Q(contract__name__icontains=query))

        return queryset.annotate(
            count_revenues=Count(
                "revenues", filter=Q(revenues__deleted_at__isnull=True), distinct=True
            ),
            count_expenses=Count(
                "expenses", filter=Q(expenses__deleted_at__isnull=True), distinct=True
            ),
        ).order_by("-year", "-month")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ResourceSourceListView(LoginRequiredMixin, ListView):
    model = ResourceSource
    context_object_name = "sources"
    paginate_by = 10
    ordering = "name"

    template_name = "accountability/sources/list.html"
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
        return queryset.order_by("name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ResourceSourceCreateView(LoginRequiredMixin, TemplateView):
    template_name = "accountability/sources/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = ResourceSourceForm()

        return context

    def post(self, request, *args, **kwargs):
        # TODO: should check any user access?
        form = ResourceSourceForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                source = form.save(commit=False)
                source.organization = request.user.organization
                source.save()

                logger.info(f"{request.user.id} - Created new resource source")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_RESOURCES_SOURCE,
                    target_object_id=source.id,
                    target_content_object=source,
                )
                return redirect("accountability:sources-list")

        return self.render_to_response(self.get_context_data(form=form))


class ResourceSourceUpdateView(LoginRequiredMixin, UpdateView):
    model = ResourceSource
    form_class = ResourceSourceForm
    template_name = "accountability/sources/create.html"
    context_object_name = "source"

    login_url = "/auth/login"

    def form_valid(self, form):
        _ = ActivityLog.objects.create(
            user=self.request.user,
            user_email=self.request.user.email,
            action=ActivityLog.ActivityLogChoices.UPDATED_RESOURCES_SOURCE,
            target_object_id=form.instance.id,
            target_content_object=form.instance,
        )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy("accountability:sources-list")

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])


def create_contract_accountability_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_execution:
        return redirect("contracts:contracts-detail", pk=contract.id)

    if request.method == "POST":
        form = AccountabilityCreateForm(request.POST)
        if form.is_valid():
            accountability_exists = Accountability.objects.filter(
                contract=contract,
                month=form.cleaned_data["month"],
                year=form.cleaned_data["year"],
            ).exists()
            if accountability_exists:
                return render(
                    request,
                    "accountability/accountability/create.html",
                    {"contract": contract, "form": form, "accountability_exists": True},
                )

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
        "bank_account",
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

    status_flag = request.GET.get("paid", "all")
    if status_flag == "true":
        expenses_list = expenses_list.filter(conciled=True)
        revenues_list = revenues_list.filter(conciled=True)
    elif status_flag == "false":
        expenses_list = expenses_list.filter(conciled=False)
        revenues_list = revenues_list.filter(conciled=False)

    expenses_paginator = Paginator(expenses_list, 10)
    expenses_page_number = request.GET.get("expenses_page")
    expenses_page = expenses_paginator.get_page(expenses_page_number)

    revenues_paginator = Paginator(revenues_list, 10)
    revenues_page_number = request.GET.get("revenues_page")
    revenues_page = revenues_paginator.get_page(revenues_page_number)

    context = {
        "object": accountability,
        "expenses_page": expenses_page,
        "expenses_total": expenses_list.aggregate(Sum("value"))["value__sum"]
        or Decimal("0.00"),
        "revenues_page": revenues_page,
        "revenues_total": revenues_list.aggregate(Sum("value"))["value__sum"]
        or Decimal("0.00"),
        "search_query": query,
    }
    return render(request, "accountability/accountability/detail.html", context)


def create_accountability_revenue_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_on_execution:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    if request.method == "POST":
        form = RevenueForm(request.POST)
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
        form = RevenueForm()
        return render(
            request,
            "accountability/revenues/create.html",
            {"accountability": accountability, "form": form},
        )


def update_accountability_revenue_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    revenue = get_object_or_404(Revenue.objects.select_related("accountability"), id=pk)
    if not revenue.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail", pk=revenue.accountability.id
        )

    if request.method == "POST":
        form = RevenueForm(request.POST, instance=revenue)
        if form.is_valid():
            with transaction.atomic():
                revenue = form.save()
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_REVENUE,
                    target_object_id=revenue.id,
                    target_content_object=revenue,
                )
            return redirect(
                "accountability:accountability-detail", pk=revenue.accountability.id
            )
        else:
            return render(
                request,
                "accountability/revenues/update.html",
                {"revenue": revenue, "form": form},
            )
    else:
        form = RevenueForm(instance=revenue)
        return render(
            request,
            "accountability/revenues/update.html",
            {"revenue": revenue, "form": form},
        )


def duplicate_accountability_revenue_view(request, pk):
    revenue = get_object_or_404(Revenue.objects.select_related("accountability"), id=pk)
    if not revenue.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail", pk=revenue.accountability.id
        )

    with transaction.atomic():
        revenue.id = None
        revenue.save()
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DUPLICATED_REVENUE,
            target_object_id=revenue.id,
            target_content_object=revenue,
        )
        return redirect(
            "accountability:accountability-detail", pk=revenue.accountability.id
        )


def create_accountability_expense_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_on_execution:
        return redirect("accountability:accountability-detail", pk=accountability.id)

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


def update_accountability_expense_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    expense = get_object_or_404(Expense.objects.select_related("accountability"), id=pk)
    if not expense.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail", pk=expense.accountability.id
        )

    if request.method == "POST":
        form = ExpenseForm(
            request.POST,
            request=request,
            instance=expense,
            accountability=expense.accountability,
        )
        if form.is_valid():
            with transaction.atomic():
                expense = form.save()
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_EXPENSE,
                    target_object_id=expense.id,
                    target_content_object=expense,
                )
            return redirect(
                "accountability:accountability-detail", pk=expense.accountability.id
            )
        else:
            return render(
                request,
                "accountability/expenses/update.html",
                {"expense": expense, "form": form},
            )
    else:
        form = ExpenseForm(
            request=request, instance=expense, accountability=expense.accountability
        )
        return render(
            request,
            "accountability/expenses/update.html",
            {"expense": expense, "form": form},
        )


def duplicate_accountability_expense_view(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("accountability"), id=pk)
    if not expense.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail", pk=expense.accountability.id
        )

    with transaction.atomic():
        expense.id = None
        expense.paid = False
        expense.conciled = False
        expense.save()
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DUPLICATED_EXPENSE,
            target_object_id=expense.id,
            target_content_object=expense,
        )
        return redirect(
            "accountability:accountability-detail", pk=expense.accountability.id
        )


def gloss_accountability_expense_view(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("accountability"), id=pk)
    if not expense.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail", pk=expense.accountability.id
        )

    with transaction.atomic():
        expense.planned = False
        expense.item = None
        expense.save()
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.GLOSSED_EXPENSE,
            target_object_id=expense.id,
            target_content_object=expense,
        )
        return redirect(
            "accountability:accountability-detail", pk=expense.accountability.id
        )


class FavoredListView(LoginRequiredMixin, ListView):
    model = Favored
    context_object_name = "favoreds_list"
    paginate_by = 10
    ordering = "name"

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
        return queryset.order_by("name")

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


class FavoredUpdateView(LoginRequiredMixin, UpdateView):
    model = Favored
    form_class = FavoredForm
    template_name = "accountability/favoreds/create.html"
    context_object_name = "favored"

    login_url = "/auth/login"

    def form_valid(self, form):
        _ = ActivityLog.objects.create(
            user=self.request.user,
            user_email=self.request.user.email,
            action=ActivityLog.ActivityLogChoices.UPDATED_FAVORED,
            target_object_id=form.instance.id,
            target_content_object=form.instance,
        )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy("accountability:favoreds-list")

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])


def import_accountability_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    if request.method == "POST":
        accountability = (
            Accountability.objects.select_related(
                "contract",
                "contract__checking_account",
                "contract__investing_account",
                "contract__organization",
            )
            .prefetch_related(
                "contract__items",
                "contract__organization__favoreds",
                "contract__organization__resource_sources",
            )
            .get(id=pk)
        )
        if not accountability.is_on_execution:
            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )

        step = request.POST.get("step")
        if step == "download":
            xlsx = export_xlsx_model(accountability=accountability)
            response = HttpResponse(
                xlsx.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                f'attachment; filename="importacao-{accountability.month}-{accountability.year}.xlsx"'
            )
            return response

        elif step == "upload":
            form = ImportXLSXAccountabilityForm(request.POST, request.FILES)
            if form.is_valid():
                imported, revenues_error, expenses_error, applications_error = (
                    import_xlsx_model(
                        file=form.cleaned_data["xlsx_file"],
                        accountability=accountability,
                    )
                )
                if any[(revenues_error, expenses_error, applications_error)]:
                    return render(
                        request,
                        "accountability/accountability/import.html",
                        {
                            "accountability": accountability,
                            "form": form,
                            "imported": imported,
                            "revenues_error": revenues_error,
                            "expenses_error": expenses_error,
                            "applications_error": applications_error,
                        },
                    )
                else:
                    _ = ActivityLog.objects.create(
                        user=request.user,
                        user_email=request.user.email,
                        action=ActivityLog.ActivityLogChoices.IMPORTED_ACCOUNTABILITY_FILE,
                        target_object_id=accountability.id,
                        target_content_object=accountability,
                    )
                    return redirect(
                        "accountability:accountability-detail", pk=accountability.id
                    )
            else:
                return render(
                    request,
                    "accountability/accountability/import.html",
                    {"accountability": accountability, "form": form},
                )

        else:
            return redirect(
                "accountability:accountability-import", pk=accountability.id
            )

    else:
        accountability = get_object_or_404(
            Accountability.objects.select_related("contract"), id=pk
        )
        form = ImportXLSXAccountabilityForm()
        return render(
            request,
            "accountability/accountability/import.html",
            {"accountability": accountability, "form": form},
        )


def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("accountability"), id=pk)
    if not expense.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail", pk=expense.accountability.id
        )

    with transaction.atomic():
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_EXPENSE,
            target_object_id=expense.id,
            target_content_object=expense,
        )
        expense.delete()
        return redirect(
            "accountability:accountability-detail", pk=expense.accountability.id
        )


def revenue_delete_view(request, pk):
    revenue = get_object_or_404(Revenue.objects.select_related("accountability"), id=pk)
    if not revenue.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail", pk=revenue.accountability.id
        )

    with transaction.atomic():
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_REVENUE,
            target_object_id=revenue.id,
            target_content_object=revenue,
        )
        revenue.delete()
        return redirect(
            "accountability:accountability-detail", pk=revenue.accountability.id
        )


def send_accountability_to_analisys_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    if accountability.is_finished:
        return redirect("home")

    with transaction.atomic():
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.SENT_TO_ANALISYS,
            target_object_id=accountability.id,
            target_content_object=accountability,
        )
        accountability.status = Accountability.ReviewStatus.SENT
        accountability.save()
        return redirect("accountability:accountability-detail", pk=accountability.id)


def send_accountability_review_analisys(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_sent:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    if not request.user or not request.user.can_change_statuses:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    with transaction.atomic():
        review_status = request.POST.get("review_status")

        if review_status == Accountability.ReviewStatus.CORRECTING:
            action = ActivityLog.ActivityLogChoices.SENT_TO_CORRECT
        elif review_status == Accountability.ReviewStatus.FINISHED:
            action = ActivityLog.ActivityLogChoices.MARKED_AS_FINISHED
        else:
            raise ValueError(f"{review_status} - Is an unnknow status review")

        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=action,
            target_object_id=accountability.id,
            target_content_object=accountability,
        )
        accountability.status = review_status
        accountability.save()
        return redirect("accountability:accountability-detail", pk=accountability.id)


def review_accountability_expenses(request, pk, index):
    accountability = get_object_or_404(
        Accountability.objects.select_related("contract"), id=pk
    )
    expenses = list(
        accountability.expenses.select_related(
            "source",
            "favored",
            "item",
        )
        .prefetch_related("files")
        .all()
        .order_by("-created_at")
    )
    total_expenses = len(expenses)

    if index < 0 or index >= total_expenses:
        return redirect("revisar_item", accountability_id=accountability.id, index=0)

    current_expense = expenses[index]
    if request.method == "POST":
        with transaction.atomic():
            current_expense.status = request.POST.get("status")
            current_expense.pendencies = request.POST.get("pendencies")
            current_expense.save()

            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.REVIEWED_EXPENSE,
                target_object_id=current_expense.id,
                target_content_object=current_expense,
            )

        action = request.POST.get("action")
        if action == "next":
            next_index = index + 1 if index < total_expenses - 1 else index
            return redirect(
                "accountability:review-expenses", pk=accountability.id, index=next_index
            )
        elif action == "previous":
            previous_index = index - 1 if index > 0 else 0
            return redirect(
                "accountability:review-expenses",
                pk=accountability.id,
                index=previous_index,
            )
        elif action == "save_all":
            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )

    context = {
        "accountability": accountability,
        "expense": current_expense,
        "current_expense_index": index + 1,
        "total_expenses": total_expenses,
    }
    return render(
        request,
        "accountability/expenses/review.html",
        context,
    )


def review_accountability_revenues(request, pk, index):
    accountability = get_object_or_404(
        Accountability.objects.select_related("contract"), id=pk
    )
    revenues = list(
        accountability.revenues.select_related(
            "bank_account",
        )
        .prefetch_related("files")
        .all()
        .order_by("-created_at")
    )
    total_revenues = len(revenues)

    if index < 0 or index >= total_revenues:
        return redirect("revisar_item", accountability_id=accountability.id, index=0)

    current_revenue = revenues[index]
    if request.method == "POST":
        with transaction.atomic():
            current_revenue.status = request.POST.get("status")
            current_revenue.pendencies = request.POST.get("pendencies")
            current_revenue.save()

            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.REVIEWED_REVENUE,
                target_object_id=current_revenue.id,
                target_content_object=current_revenue,
            )

        action = request.POST.get("action")
        if action == "next":
            next_index = index + 1 if index < total_revenues - 1 else index
            return redirect(
                "accountability:review-revenues", pk=accountability.id, index=next_index
            )
        elif action == "previous":
            previous_index = index - 1 if index > 0 else 0
            return redirect(
                "accountability:review-revenues",
                pk=accountability.id,
                index=previous_index,
            )
        elif action == "save_all":
            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )

    context = {
        "accountability": accountability,
        "revenue": current_revenue,
        "current_revenue_index": index + 1,
        "total_revenues": total_revenues,
    }
    return render(
        request,
        "accountability/revenues/review.html",
        context,
    )


def reconcile_expense_view(request, pk):
    expense = get_object_or_404(
        Expense.objects.select_related(
            "accountability",
            "accountability__contract",
            "accountability__contract__checking_account",
            "accountability__contract__investing_account",
        ),
        id=pk,
    )
    contract = expense.accountability.contract

    total_expenses = Expense.objects.filter(
        accountability=expense.accountability
    ).count()
    conciled_expenses = Expense.objects.filter(
        accountability=expense.accountability, conciled=True
    ).count()

    if request.method == "POST":
        form = ReconcileExpenseForm(request.POST, contract=contract, expense=expense)
        files = request.FILES.getlist("files")

        if form.is_valid():
            with transaction.atomic():
                expense.conciled = True
                expense.paid = True
                expense.liquidation = form.cleaned_data["transactions"][0].date
                expense.save()
                expense.transactions.set(form.cleaned_data["transactions"])

                for file in files:
                    ExpenseFile.objects.create(
                        expense=expense,
                        created_by=request.user,
                        name=file.name,
                        file=file,
                    )

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.RECONCILED_EXPENSE,
                    target_object_id=expense.id,
                    target_content_object=expense,
                )

            action = request.POST.get("action")
            if action == "next":
                next_expense = Expense.objects.filter(
                    accountability=expense.accountability,
                    conciled=False,
                    paid=False,
                ).first()
                if next_expense:
                    return redirect(
                        "accountability:expense-reconcile", pk=next_expense.id
                    )
                else:
                    return redirect(
                        "accountability:accountability-detail",
                        pk=expense.accountability.id,
                    )
            else:
                return redirect(
                    "accountability:accountability-detail", pk=expense.accountability.id
                )

        else:
            return render(
                request,
                "accountability/expenses/reconcile.html",
                {
                    "form": form,
                    "expense": expense,
                    "total": total_expenses,
                    "conciled": conciled_expenses,
                },
            )
    else:
        form = ReconcileExpenseForm(contract=contract)
        return render(
            request,
            "accountability/expenses/reconcile.html",
            {
                "form": form,
                "expense": expense,
                "total": total_expenses,
                "conciled": conciled_expenses,
            },
        )


def reconcile_revenue_view(request, pk):
    revenue = get_object_or_404(
        Revenue.objects.select_related(
            "accountability",
            "accountability__contract",
            "accountability__contract__checking_account",
            "accountability__contract__investing_account",
        ),
        id=pk,
    )
    contract = revenue.accountability.contract

    total_revenues = Revenue.objects.filter(
        accountability=revenue.accountability
    ).count()
    conciled_revenues = Revenue.objects.filter(
        accountability=revenue.accountability, conciled=True
    ).count()

    if request.method == "POST":
        form = ReconcileRevenueForm(request.POST, contract=contract, revenue=revenue)

        if form.is_valid():
            with transaction.atomic():
                revenue.conciled = True
                revenue.paid = True
                revenue.liquidation = form.cleaned_data["transactions"][0].date
                revenue.save()
                revenue.transactions.set(form.cleaned_data["transactions"])

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.RECONCILED_REVENUE,
                    target_object_id=revenue.id,
                    target_content_object=revenue,
                )

            action = request.POST.get("action")
            if action == "next":
                next_revenue = Revenue.objects.filter(
                    accountability=revenue.accountability,
                    conciled=False,
                    paid=False,
                ).first()
                if next_revenue:
                    return redirect(
                        "accountability:revenue-reconcile", pk=next_revenue.id
                    )
                else:
                    return redirect(
                        "accountability:accountability-detail",
                        pk=revenue.accountability.id,
                    )
            else:
                return redirect(
                    "accountability:accountability-detail", pk=revenue.accountability.id
                )

        else:
            return render(
                request,
                "accountability/revenues/reconcile.html",
                {
                    "form": form,
                    "revenue": revenue,
                    "total": total_revenues,
                    "conciled": conciled_revenues,
                },
            )
    else:
        form = ReconcileRevenueForm(contract=contract)
        return render(
            request,
            "accountability/revenues/reconcile.html",
            {
                "form": form,
                "revenue": revenue,
                "total": total_revenues,
                "conciled": conciled_revenues,
            },
        )
