import logging
from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.query import Prefetch, QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView, UpdateView

from accountability.forms import (
    AccountabilityCreateForm,
    AccountabilityFileForm,
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
    AccountabilityFile,
    Expense,
    ExpenseFile,
    Favored,
    ResourceSource,
    Revenue,
    RevenueFile,
)
from accountability.services import export_xlsx_model, import_xlsx_model
from activity.models import ActivityLog
from contracts.models import Contract
from utils.logging import log_database_operation, log_view_access
from utils.mixins import CommitteeMemberCreateMixin, CommitteeMemberUpdateMixin

logger = logging.getLogger(__name__)


@method_decorator(log_view_access, name="dispatch")
class AccountabilityListView(LoginRequiredMixin, ListView):
    model = Accountability
    context_object_name = "accountabilities"
    paginate_by = 10
    ordering = "month"

    template_name = "accountability/accountability/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        query = self.request.GET.get("q", "")
        queryset = self.model.objects.select_related("contract").filter(
            contract__area__in=self.request.user.areas.all()
        )

        if query:
            queryset = queryset.filter(Q(contract__name__icontains=query))

        queryset = queryset.annotate(
            count_revenues=Count(
                "revenues",
                filter=Q(revenues__deleted_at__isnull=True),
                distinct=True,
            ),
            count_expenses=Count(
                "expenses",
                filter=Q(expenses__deleted_at__isnull=True),
                distinct=True,
            ),
        ).order_by("-year", "-month")

        return queryset

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


class ResourceSourceCreateView(
    CommitteeMemberCreateMixin, LoginRequiredMixin, TemplateView
):
    template_name = "accountability/sources/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = ResourceSourceForm()

        return context

    def post(self, request, *args, **kwargs):
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


@login_required
def update_accountability_revenue_view(request, pk):
    """Update an accountability revenue."""
    revenue = get_object_or_404(Revenue, pk=pk)
    accountability = revenue.accountability

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
                "accountability:accountability-detail", pk=accountability.pk
            )
    else:
        form = RevenueForm(instance=revenue)

    return render(
        request,
        "accountability/revenues/update.html",
        {
            "form": form,
            "accountability": accountability,
            "revenue": revenue,
        },
    )


@login_required
def update_accountability_expense_view(request, pk):
    """Update an accountability expense."""
    expense = get_object_or_404(Expense, pk=pk)
    accountability = expense.accountability

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
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
                "accountability:accountability-detail", pk=accountability.pk
            )
    else:
        form = ExpenseForm(instance=expense)

    return render(
        request,
        "accountability/expenses/update.html",
        {
            "form": form,
            "accountability": accountability,
            "expense": expense,
        },
    )


class ResourceSourceUpdateView(
    CommitteeMemberUpdateMixin, LoginRequiredMixin, UpdateView
):
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


@log_view_access
@login_required
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
                    {
                        "contract": contract,
                        "form": form,
                        "accountability_exists": True,
                    },
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


@log_view_access
@login_required
def accountability_detail_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)

    # Get filter parameters
    search_query = request.GET.get("q", "")
    paid_filter = request.GET.get("paid", "all")
    reviwed_filter = request.GET.get("reviwed", "all")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    date_type = request.GET.get(
        "date_type", "competence"
    )  # competence, liquidation, due_date, conciliation
    payment_status = request.GET.get("payment_status", "all")  # all, paid, unpaid
    expense_type = request.GET.get("expense_type", "all")  # all, planned, unplanned

    # Base querysets
    expenses_list = (
        Expense.objects.filter(accountability=accountability)
        .select_related("item", "favored")
        .prefetch_related(
            Prefetch(
                "files",
                queryset=ExpenseFile.objects.select_related("created_by").filter(
                    deleted_at__isnull=True
                ),
            )
        )
        .annotate(
            count_files=Count(
                "files",
                filter=Q(files__deleted_at__isnull=True),
                distinct=True,
            )
        )
        .order_by("-value")
    )

    revenues_list = (
        Revenue.objects.filter(accountability=accountability)
        .select_related("bank_account")
        .prefetch_related(
            Prefetch(
                "files",
                queryset=RevenueFile.objects.select_related("created_by").filter(
                    deleted_at__isnull=True
                ),
            )
        )
        .annotate(
            count_files=Count(
                "files",
                filter=Q(files__deleted_at__isnull=True),
                distinct=True,
            )
        )
        .order_by("-value")
    )

    documents_list = AccountabilityFile.objects.filter(
        accountability=accountability,
    ).select_related("created_by")

    # Apply filters
    if search_query:
        expenses_list = expenses_list.filter(
            Q(identification__icontains=search_query)
            | Q(item__name__icontains=search_query)
            | Q(favored__name__icontains=search_query)
        )
        revenues_list = revenues_list.filter(
            Q(bank_account__name__icontains=search_query)
        )
        documents_list = documents_list.filter(Q(name__icontains=search_query))

    # Apply payment status filter
    if paid_filter != "all":
        expenses_list = expenses_list.filter(paid=paid_filter == "true")
        revenues_list = revenues_list.filter(paid=paid_filter == "true")

    # Apply review status filter
    if reviwed_filter != "all":
        expenses_list = expenses_list.filter(status=reviwed_filter)
        revenues_list = revenues_list.filter(status=reviwed_filter)

    # Apply date range filter
    if start_date and end_date:
        match date_type:
            case "competence":
                expenses_list = expenses_list.filter(
                    competency__range=[start_date, end_date]
                )
                revenues_list = revenues_list.filter(
                    competency__range=[start_date, end_date]
                )
            case "liquidation":
                expenses_list = expenses_list.filter(
                    liquidation__range=[start_date, end_date]
                )
                revenues_list = revenues_list.filter(
                    competency__range=[start_date, end_date]
                )
            case "due_date":
                expenses_list = expenses_list.filter(
                    due_date__range=[start_date, end_date]
                )
                revenues_list = revenues_list.filter(
                    competency__range=[start_date, end_date]
                )
            case "conciliation":
                expenses_list = expenses_list.filter(
                    conciled_at__range=[start_date, end_date]
                )
                revenues_list = revenues_list.filter(
                    conciled_at__range=[start_date, end_date]
                )
            case _:
                pass

    # Apply payment status filter
    if payment_status != "all":
        match payment_status:
            case "paid":
                expenses_list = expenses_list.filter(paid=True)
                revenues_list = revenues_list.filter(paid=True)
            case "unpaid":
                expenses_list = expenses_list.filter(paid=False)
                revenues_list = revenues_list.filter(paid=False)
            case _:
                pass

    # Apply expense type filter
    if expense_type != "all":
        match expense_type:
            case "planned":
                expenses_list = expenses_list.filter(planned=True)
            case "unplanned":
                expenses_list = expenses_list.filter(planned=False)
            case _:
                pass

    expenses_paginator = Paginator(expenses_list, 10)
    revenues_paginator = Paginator(revenues_list, 10)

    expenses_page = expenses_paginator.get_page(request.GET.get("expenses_page"))
    revenues_page = revenues_paginator.get_page(request.GET.get("revenues_page"))

    context = {
        "accountability": accountability,
        "expenses_page": expenses_page,
        "revenues_page": revenues_page,
        "documents": documents_list,
        "expenses_total": expenses_list.aggregate(Sum("value"))["value__sum"] or 0,
        "revenues_total": revenues_list.aggregate(Sum("value"))["value__sum"] or 0,
        "search_query": search_query,
        "start_date": start_date,
        "end_date": end_date,
        "date_type": date_type,
        "payment_status": payment_status,
        "expense_type": expense_type,
    }

    return render(request, "accountability/accountability/detail.html", context)


@login_required
def create_accountability_file_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_on_execution:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    if request.method == "POST":
        form = AccountabilityFileForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                file = AccountabilityFile.objects.create(
                    accountability=accountability,
                    created_by=request.user,
                    name=form.cleaned_data["name"],
                    file=request.FILES["file"],
                )

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_ACCOUNTABILITY_FILE,
                    target_object_id=file.id,
                    target_content_object=file,
                )
                return redirect(
                    "accountability:accountability-detail",
                    pk=accountability.id,
                )
        else:
            return render(
                request,
                "accountability/files/create.html",
                {"accountability": accountability, "form": form},
            )
    else:
        form = AccountabilityFileForm()
        return render(
            request,
            "accountability/files/create.html",
            {"accountability": accountability, "form": form},
        )


@login_required
@require_POST
def accountability_file_delete_view(request, pk):
    file = get_object_or_404(
        AccountabilityFile.objects.select_related("accountability"), id=pk
    )
    next_url = request.POST.get("next", "accountability:accountability-detail")

    if not file.accountability.is_on_execution:
        return redirect(next_url, pk=file.accountability.id)

    with transaction.atomic():
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_ACCOUNTABILITY_FILE,
            target_object_id=file.id,
            target_content_object=file,
        )
        file.delete()
        return redirect(next_url, pk=file.accountability.id)


@login_required
def create_accountability_revenue_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_on_execution:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    if request.method == "POST":
        form = RevenueForm(request.POST, accountability=accountability)
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
        form = RevenueForm(accountability=accountability)
        return render(
            request,
            "accountability/revenues/create.html",
            {"accountability": accountability, "form": form},
        )


@login_required
def duplicate_accountability_revenue_view(request, pk):
    revenue = get_object_or_404(Revenue.objects.select_related("accountability"), id=pk)
    next_url = request.POST.get("next", "accountability:accountability-detail")

    if not revenue.accountability.is_on_execution:
        return redirect(next_url, pk=revenue.accountability.id)

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
        return redirect(next_url, pk=revenue.accountability.id)


@login_required
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


@login_required
def duplicate_accountability_expense_view(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("accountability"), id=pk)
    next_url = request.POST.get("next", "accountability:accountability-detail")

    if not expense.accountability.is_on_execution:
        return redirect(next_url, pk=expense.accountability.id)

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
        return redirect(next_url, pk=expense.accountability.id)


@login_required
def gloss_accountability_expense_view(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("accountability"), id=pk)
    next_url = request.POST.get("next", "accountability:accountability-detail")

    if not expense.accountability.is_on_execution:
        return redirect(next_url, pk=expense.accountability.id)

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
        return redirect(next_url, pk=expense.accountability.id)


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


class FavoredCreateView(CommitteeMemberCreateMixin, LoginRequiredMixin, TemplateView):
    template_name = "accountability/favoreds/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = FavoredForm()

        return context

    def post(self, request, *args, **kwargs):
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


@login_required
def update_favored_view(request, pk):
    favored = get_object_or_404(Favored, pk=pk)

    if request.method == "POST":
        form = FavoredForm(request.POST, instance=favored)
        if form.is_valid():
            form.save()
            return redirect("accountability:favoreds-list")
    else:
        form = FavoredForm(instance=favored)

    return render(
        request,
        "accountability/favoreds/create.html",
        {
            "form": form,
            "favored": favored,
        },
    )


@log_database_operation("import_accountability")
@log_view_access
@login_required
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
            response.set_cookie("fileDownload", "true", max_age=60)
            return response

        elif step == "upload":
            form = ImportXLSXAccountabilityForm(request.POST, request.FILES)
            if form.is_valid():
                (
                    imported,
                    revenues_error,
                    expenses_error,
                    applications_error,
                ) = import_xlsx_model(
                    file=form.cleaned_data["xlsx_file"],
                    accountability=accountability,
                )
                if any([revenues_error, expenses_error, applications_error]):
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
                        "accountability:accountability-detail",
                        pk=accountability.id,
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


@login_required
@require_POST
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("accountability"), id=pk)
    if not expense.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail",
            pk=expense.accountability.id,
        )

    next_url = request.POST.get("next", "accountability:accountability-detail")
    with transaction.atomic():
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_EXPENSE,
            target_object_id=expense.id,
            target_content_object=expense,
        )
        expense.delete()
        return redirect(next_url, pk=expense.accountability.id)


@login_required
@require_POST
def revenue_delete_view(request, pk):
    revenue = get_object_or_404(Revenue.objects.select_related("accountability"), id=pk)
    if not revenue.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
        )

    next_url = request.POST.get("next", "accountability:accountability-detail")
    with transaction.atomic():
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_REVENUE,
            target_object_id=revenue.id,
            target_content_object=revenue,
        )
        revenue.delete()
        return redirect(next_url, pk=revenue.accountability.id)


@login_required
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
        review_pendencies = request.POST.get("review_pendencies")

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
        accountability.pendencies = review_pendencies
        accountability.save()
        return redirect("accountability:accountability-detail", pk=accountability.id)


@log_database_operation("review_expense")
@log_view_access
def review_accountability_single_expense(request, pk, expense_pk):
    expense = get_object_or_404(
        Expense.objects.select_related(
            "accountability",
            "accountability__contract",
            "source",
            "favored",
            "item",
        ),
        id=expense_pk,
    )

    if request.method == "POST":
        with transaction.atomic():
            expense.status = request.POST.get("status")
            expense.pendencies = request.POST.get("pendencies")
            expense.save()

            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.REVIEWED_EXPENSE,
                target_object_id=expense.id,
                target_content_object=expense,
            )
            return redirect(
                "accountability:accountability-detail",
                pk=expense.accountability.id,
            )
    else:
        return render(
            request,
            "accountability/expenses/review-single.html",
            {"expense": expense},
        )


@log_database_operation("review_expenses")
@log_view_access
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
        .filter(status=Expense.ReviewStatus.IN_ANALISIS)
        .order_by("-value")
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
                "accountability:review-expenses",
                pk=accountability.id,
                index=next_index,
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


@log_database_operation("review_revenue")
@log_view_access
def review_accountability_single_revenue(request, pk, revenue_pk):
    revenue = get_object_or_404(
        Revenue.objects.select_related(
            "accountability",
            "accountability__contract",
            "bank_account",
        ),
        id=revenue_pk,
    )

    if request.method == "POST":
        with transaction.atomic():
            revenue.status = request.POST.get("status")
            revenue.pendencies = request.POST.get("pendencies")
            revenue.save()

            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.REVIEWED_REVENUE,
                target_object_id=revenue.id,
                target_content_object=revenue,
            )
            return redirect(
                "accountability:accountability-detail",
                pk=revenue.accountability.id,
            )
    else:
        return render(
            request,
            "accountability/revenues/review-single.html",
            {"revenue": revenue},
        )


@log_database_operation("review_revenues")
@log_view_access
def review_accountability_revenues(request, pk, index):
    accountability = get_object_or_404(
        Accountability.objects.select_related("contract"), id=pk
    )
    revenues = list(
        accountability.revenues.select_related(
            "bank_account",
        )
        .prefetch_related("files")
        .filter(status=Revenue.ReviewStatus.IN_ANALISIS)
        .order_by("-value")
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
                "accountability:review-revenues",
                pk=accountability.id,
                index=next_index,
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


@log_database_operation("reconcile_expense")
@log_view_access
@login_required
def reconcile_expense_view(request, pk):
    expense = get_object_or_404(
        Expense.objects.select_related(
            "accountability",
            "accountability__contract",
            "accountability__contract__checking_account",
            "accountability__contract__investing_account",
            "favored",
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
    unpaid_expenses = (
        Expense.objects.filter(
            accountability=expense.accountability,
            paid=False,
            conciled=False,
        )
        .prefetch_related("favored")
        .exclude(id=expense.id)
    )

    if request.method == "POST":
        relateds = Expense.objects.filter(
            id__in=request.POST.getlist("related_expenses", [])
        )
        form = ReconcileExpenseForm(
            request.POST,
            contract=contract,
            expense=expense,
            relateds=relateds,
        )
        files = request.FILES.getlist("files")

        if form.is_valid():
            with transaction.atomic():
                expense.conciled = True
                expense.conciled_at = timezone.now()
                expense.paid = True
                expense.liquidation = form.cleaned_data["transactions"][0].date
                expense.save()
                expense.bank_transactions.set(form.cleaned_data["transactions"])

                for related in relateds:
                    related.conciled = True
                    related.conciled_at = timezone.now()
                    related.paid = True
                    related.liquidation = form.cleaned_data["transactions"][0].date
                    related.save()
                    related.bank_transactions.set(form.cleaned_data["transactions"])

                for file in files:
                    ExpenseFile.objects.create(
                        expense=expense,
                        created_by=request.user,
                        name=file.name,
                        file=file,
                    )
                    for related in relateds:
                        ExpenseFile.objects.create(
                            expense=related,
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
                    "accountability:accountability-detail",
                    pk=expense.accountability.id,
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
                    "unpaid_expenses": unpaid_expenses,
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
                "unpaid_expenses": unpaid_expenses,
            },
        )


@log_database_operation("reconcile_revenue")
@log_view_access
@login_required
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
                revenue.conciled_at = timezone.now()
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
                    "accountability:accountability-detail",
                    pk=revenue.accountability.id,
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


@log_view_access
@login_required
def accountability_pendencies_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    expenses = (
        Expense.objects.filter(
            accountability=accountability,
            pendencies__isnull=False,
        )
        .exclude(
            pendencies="",
        )
        .select_related("favored")
    )
    revenues = Revenue.objects.filter(
        accountability=accountability,
        pendencies__isnull=False,
    ).exclude(
        pendencies="",
    )

    return render(
        request,
        "accountability/accountability/pendencies-list.html",
        {
            "accountability": accountability,
            "expenses": expenses,
            "revenues": revenues,
        },
    )


@require_POST
@login_required
def upload_expense_file_view(request, pk):
    """Upload files for an expense."""
    expense = get_object_or_404(Expense, pk=pk)
    accountability = expense.accountability

    files = request.FILES.getlist("files")
    with transaction.atomic():
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
                action=ActivityLog.ActivityLogChoices.UPLOADED_EXPENSE_FILE,
                target_object_id=expense.id,
                target_content_object=expense,
            )

    return redirect("accountability:accountability-detail", pk=accountability.pk)


@require_POST
@login_required
def upload_revenue_file_view(request, pk):
    """Upload files for a revenue."""
    revenue = get_object_or_404(Revenue, pk=pk)
    accountability = revenue.accountability

    files = request.FILES.getlist("files")
    with transaction.atomic():
        for file in files:
            RevenueFile.objects.create(
                revenue=revenue,
                created_by=request.user,
                name=file.name,
                file=file,
            )
            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.UPLOADED_REVENUE_FILE,
                target_object_id=revenue.id,
                target_content_object=revenue,
            )

    return redirect("accountability:accountability-detail", pk=accountability.pk)


@require_POST
@login_required
def delete_expense_file_view(request, pk):
    """Delete an expense file."""
    file = get_object_or_404(ExpenseFile, pk=pk)
    accountability = file.expense.accountability

    with transaction.atomic():
        file.delete()
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_EXPENSE_FILE,
            target_object_id=file.expense.id,
            target_content_object=file.expense,
        )

    return redirect("accountability:accountability-detail", pk=accountability.pk)


@require_POST
@login_required
def delete_revenue_file_view(request, pk):
    """Delete a revenue file."""
    file = get_object_or_404(RevenueFile, pk=pk)
    accountability = file.revenue.accountability

    with transaction.atomic():
        file.delete()
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_REVENUE_FILE,
            target_object_id=file.revenue.id,
            target_content_object=file.revenue,
        )

    return redirect("accountability:accountability-detail", pk=accountability.pk)
