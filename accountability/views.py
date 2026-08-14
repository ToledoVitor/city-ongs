import json
import logging
import unicodedata
from datetime import date
from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction as db_transaction
from django.db.models import Count, Q, Sum
from django.db.models.query import Prefetch, QuerySet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from accountability.forms import (
    AccountabilityCreateForm,
    AccountabilityFileForm,
    ActivityReportPublicationFormSet,
    ActivityReportPublicationStatusForm,
    AnnualStatementCreateForm,
    AnnualStatementUpdateForm,
    BalanceAdjustmentForm,
    BoardParticipationFormSet,
    BudgetCommitmentForm,
    ConclusiveOpinionDeclarationFormSet,
    ConclusiveOpinionForm,
    ConflictOfInterestDeclarationForm,
    DeductionForm,
    EvaluationReportForm,
    ExpenseForm,
    ExpenseRejectionForm,
    FavoredForm,
    FinancialStatementsForm,
    FinancialStatementsPublicationFormSet,
    FundTransferForm,
    ImportXLSXAccountabilityForm,
    OpinionOrMinutesForm,
    OpinionOrMinutesPublicationFormSet,
    PhysicalFinancialExecutionStatementForm,
    PhysicalFinancialExecutionStatementPublicationFormSet,
    PurchasingRegulationForm,
    PurchasingRegulationPublicationFormSet,
    ReconcileExpenseForm,
    ReconcileRevenueForm,
    RefundForm,
    RelatedCompanyFormSet,
    ResourceSourceForm,
    RevenueForm,
)
from accountability.models import (
    Accountability,
    AccountabilityFile,
    ActivityReportPublicationStatus,
    AnnualStatement,
    BalanceAdjustment,
    BudgetCommitment,
    ConclusiveOpinion,
    ConclusiveOpinionDeclaration,
    ConflictOfInterestDeclaration,
    Deduction,
    EvaluationReport,
    Expense,
    ExpenseFile,
    ExpenseRejection,
    Favored,
    FinancialStatements,
    FundTransfer,
    OpinionOrMinutes,
    PhysicalFinancialExecutionStatement,
    PurchasingRegulation,
    Refund,
    ResourceSource,
    Revenue,
    RevenueFile,
)
from accountability.services import export_xlsx_model, import_xlsx_model
from accounts.models import Area, User
from activity.models import ActivityLog
from bank.models import Transaction
from contracts.models import Contract, ContractInterestedPart
from utils.logging import log_database_operation, log_view_access
from utils.mixins import (
    CommitteeMemberCreateMixin,
    CommitteeMemberUpdateMixin,
    UserAccessViewMixin,
)
from utils.regex import only_digits

logger = logging.getLogger(__name__)

EXPENSE_DOCUMENT_MAX_FILES = 50
EXPENSE_DOCUMENT_MAX_SIZE = 10 * 1024 * 1024
EXPENSE_DOCUMENT_PAGE_SIZE = 20
EXPENSE_DOCUMENT_MAX_PAGE_SIZE = 50
EXPENSE_DOCUMENT_EXTENSIONS = {".jpeg", ".jpg", ".pdf", ".png"}
EXPENSE_DOCUMENT_SIGNATURES = {
    ".pdf": (b"%PDF-",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
}


@method_decorator(log_view_access, name="dispatch")
class AccountabilityListView(UserAccessViewMixin, LoginRequiredMixin, ListView):
    model = Accountability
    context_object_name = "accountabilities"
    paginate_by = 10
    ordering = "month"
    contract_field_prefix = "contract__"

    template_name = "accountability/accountability/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        query = self.request.GET.get("q", "")
        queryset = self.model.objects.select_related("contract")
        queryset = self.get_user_filtered_queryset(queryset)

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
            # `organization` is excluded from the form (assigned from the
            # logged-in user, not user input). ResourceSourceForm.clean()
            # only checks (name, document), not the (organization, document)
            # pair the model's own clean()/save() and DB constraint actually
            # enforce - two sources with the same document but different
            # names slip past the form check and only hit the model's check
            # inside save(), which this view never wraps in a try/except, so
            # a genuine duplicate raises an uncaught ValidationError instead
            # of a friendly form error. Check by hand first.
            source_exists = ResourceSource.objects.filter(
                organization=request.user.organization,
                document=only_digits(form.cleaned_data["document"]),
            ).exists()
            if source_exists:
                return self.render_to_response(
                    self.get_context_data(form=form, source_exists=True)
                )

            with db_transaction.atomic():
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
    revenue = get_object_or_404(Revenue, pk=pk)
    accountability = revenue.accountability

    if request.method == "POST":
        if not request.user.can_update_accountability:
            return redirect(
                "accountability:accountability-detail",
                pk=accountability.id,
            )

        form = RevenueForm(
            request.POST, instance=revenue, accountability=accountability
        )
        if form.is_valid():
            with db_transaction.atomic():
                revenue = form.save(commit=False)
                revenue.status = Revenue.ReviewStatus.UPDATED
                revenue.save()
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
        form = RevenueForm(instance=revenue, accountability=accountability)

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
    expense = get_object_or_404(Expense, pk=pk)
    accountability = expense.accountability

    if request.method == "POST":
        if not request.user.can_update_accountability:
            return redirect(
                "accountability:accountability-detail",
                pk=accountability.id,
            )

        form = ExpenseForm(
            request.POST,
            request=request,
            instance=expense,
            accountability=accountability,
        )
        if form.is_valid():
            with db_transaction.atomic():
                expense = form.save(commit=False)
                expense.status = Expense.ReviewStatus.UPDATED
                expense.save()
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
        form = ExpenseForm(
            request=request, instance=expense, accountability=accountability
        )

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

            with db_transaction.atomic():
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

    search_query = request.GET.get("q", "")
    paid_filter = request.GET.get("paid", "all")
    reviwed_filter = request.GET.get("reviwed", "all")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")
    date_type = request.GET.get("date_type", "competence")
    payment_status = request.GET.get("payment_status", "all")  # all, paid, unpaid
    expense_type = request.GET.get("expense_type", "all")  # all, planned, unplanned

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
        .filter(deleted_at__isnull=True)
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
        .filter(deleted_at__isnull=True)
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
        revenues_list = revenues_list.filter(Q(identification__icontains=search_query))
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
    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=pk,
        )

    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_on_execution:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    if request.method == "POST":
        form = AccountabilityFileForm(request.POST)
        if form.is_valid():
            with db_transaction.atomic():
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=file.accountability.id,
        )

    with db_transaction.atomic():
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=pk,
        )
    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail",
            pk=accountability.id,
        )

    if request.method == "POST":
        form = RevenueForm(request.POST, accountability=accountability)
        if form.is_valid():
            with db_transaction.atomic():
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
        )

    with db_transaction.atomic():
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=pk,
        )

    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_on_execution:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    if request.method == "POST":
        form = ExpenseForm(request.POST, request=request, accountability=accountability)
        if form.is_valid():
            with db_transaction.atomic():
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=expense.accountability.id,
        )

    if not expense.accountability.is_on_execution:
        return redirect(next_url, pk=expense.accountability.id)

    with db_transaction.atomic():
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=pk,
        )

    with db_transaction.atomic():
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
            # `organization` is excluded from the form (assigned from the
            # logged-in user, not user input). FavoredForm.clean() only
            # checks (name, document), not the (organization, document) pair
            # the model's own clean()/save() and DB constraint actually
            # enforce - two favoreds with the same document but different
            # names slip past the form check and only hit the model's check
            # inside save(), which this view never wraps in a try/except, so
            # a genuine duplicate raises an uncaught ValidationError instead
            # of a friendly form error. Check by hand first.
            favored_exists = Favored.objects.filter(
                organization=request.user.organization,
                document=only_digits(form.cleaned_data["document"]),
            ).exists()
            if favored_exists:
                return self.render_to_response(
                    self.get_context_data(form=form, favored_exists=True)
                )

            with db_transaction.atomic():
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=pk,
        )

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
                if imported:
                    _ = ActivityLog.objects.create(
                        user=request.user,
                        user_email=request.user.email,
                        action=ActivityLog.ActivityLogChoices.IMPORTED_ACCOUNTABILITY_FILE,
                        target_object_id=accountability.id,
                        target_content_object=accountability,
                    )
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=expense.accountability.id,
        )

    next_url = request.POST.get("next", "accountability:accountability-detail")
    with db_transaction.atomic():
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
        )

    next_url = request.POST.get("next", "accountability:accountability-detail")
    with db_transaction.atomic():
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
    accountability = get_object_or_404(
        Accountability.objects.select_related(
            "contract",
            "contract__supervision_autority",
            "contract__accountability_autority",
        ),
        id=pk,
    )
    if accountability.is_finished:
        return redirect("home")

    if request.method == "GET":
        return redirect("accountability:accountability-detail", pk=accountability.id)

    if request.method == "POST":
        reviewer_id = request.POST.get("reviewer")
        if not reviewer_id:
            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )

        try:
            selected_reviewer = User.objects.get(
                id=reviewer_id,
                organization=request.user.organization,
                access_level=User.AccessChoices.FOLDER_MANAGER,
                is_active=True,
            )
        except Exception:
            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )

        with db_transaction.atomic():
            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.SENT_TO_ANALISYS,
                target_object_id=accountability.id,
                target_content_object=accountability,
            )
            accountability.status = Accountability.ReviewStatus.SENT
            accountability.reviewer = selected_reviewer
            accountability.save()
            Expense.objects.filter(
                accountability=accountability, status=Expense.ReviewStatus.UPDATED
            ).update(status=Expense.ReviewStatus.IN_ANALISIS)
            Revenue.objects.filter(
                accountability=accountability, status=Revenue.ReviewStatus.UPDATED
            ).update(status=Revenue.ReviewStatus.IN_ANALISIS)

            if all(
                [
                    accountability.contract.accountability_autority
                    != selected_reviewer,
                    accountability.contract.supervision_autority != selected_reviewer,
                    not accountability.contract.interested_parts.filter(
                        user=selected_reviewer
                    ).exists(),
                ]
            ):
                ContractInterestedPart.objects.create(
                    contract=accountability.contract,
                    user=selected_reviewer,
                    interest=ContractInterestedPart.InterestLevel.FISCAL_COUNCIL,
                )

            return redirect(
                "accountability:accountability-detail", pk=accountability.id
            )


@login_required
def get_available_reviewers_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    user_org = request.user.organization

    available_reviewers = User.objects.filter(
        organization=user_org,
        access_level=User.AccessChoices.FOLDER_MANAGER,
        is_active=True,
    ).order_by("first_name", "last_name")

    default_reviewer = accountability.contract.supervision_autority

    reviewers_data = []
    for reviewer in available_reviewers:
        reviewers_data.append(
            {
                "id": str(reviewer.id),
                "name": reviewer.get_full_name(),
                "email": reviewer.email,
                "is_default": reviewer == default_reviewer,
            }
        )

    return JsonResponse(
        {
            "reviewers": reviewers_data,
            "default_reviewer": str(default_reviewer.id) if default_reviewer else None,
        }
    )


def send_accountability_review_analisys(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    if not accountability.is_sent:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    if not request.user or not request.user.can_review_accountability:
        return redirect("accountability:accountability-detail", pk=accountability.id)

    with db_transaction.atomic():
        review_status = request.POST.get("review_status")
        review_pendencies = request.POST.get("review_pendencies")
        committee_member_id = request.POST.get("committee_member")

        if review_status == Accountability.ReviewStatus.CORRECTING:
            action = ActivityLog.ActivityLogChoices.SENT_TO_CORRECT
        elif review_status == Accountability.ReviewStatus.FINISHED:
            action = ActivityLog.ActivityLogChoices.MARKED_AS_FINISHED

            # Validate committee member selection for approved accountabilities
            if committee_member_id:
                try:
                    committee_member = User.objects.get(
                        id=committee_member_id,
                        organization=request.user.organization,
                        access_level=User.AccessChoices.COMMITTEE_MEMBER,
                        is_active=True,
                    )
                    accountability.committee_member = committee_member
                except User.DoesNotExist:
                    return redirect(
                        "accountability:accountability-detail", pk=accountability.id
                    )
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
    if not request.user or not request.user.can_review_accountability:
        return redirect("accountability:accountability-detail", pk=pk)

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
        with db_transaction.atomic():
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
    if not request.user or not request.user.can_review_accountability:
        return redirect("accountability:accountability-detail", pk=pk)

    accountability = get_object_or_404(
        Accountability.objects.select_related("contract"), id=pk
    )
    expenses = list(
        accountability.expenses.select_related(
            "source",
            "favored",
            "item",
        )
        .prefetch_related(
            Prefetch(
                "files",
                queryset=ExpenseFile.objects.select_related("created_by").filter(
                    deleted_at__isnull=True
                ),
            )
        )
        .filter(status=Expense.ReviewStatus.IN_ANALISIS)
        .order_by("-value")
    )
    total_expenses = len(expenses)

    if index < 0 or index >= total_expenses:
        return redirect("revisar_item", accountability_id=accountability.id, index=0)

    current_expense = expenses[index]
    if request.method == "POST":
        with db_transaction.atomic():
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
    if not request.user or not request.user.can_review_accountability:
        return redirect("accountability:accountability-detail", pk=pk)

    revenue = get_object_or_404(
        Revenue.objects.select_related(
            "accountability",
            "accountability__contract",
            "bank_account",
        ),
        id=revenue_pk,
    )

    if request.method == "POST":
        with db_transaction.atomic():
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
    if not request.user or not request.user.can_review_accountability:
        return redirect("accountability:accountability-detail", pk=pk)

    accountability = get_object_or_404(
        Accountability.objects.select_related("contract"), id=pk
    )
    revenues = list(
        accountability.revenues.select_related(
            "bank_account",
        )
        .prefetch_related(
            Prefetch(
                "files",
                queryset=RevenueFile.objects.select_related("created_by").filter(
                    deleted_at__isnull=True
                ),
            )
        )
        .filter(status=Revenue.ReviewStatus.IN_ANALISIS)
        .order_by("-value")
    )
    total_revenues = len(revenues)

    if index < 0 or index >= total_revenues:
        return redirect("revisar_item", accountability_id=accountability.id, index=0)

    current_revenue = revenues[index]
    if request.method == "POST":
        with db_transaction.atomic():
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
    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=expense.accountability.id,
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
            with db_transaction.atomic():
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
                next_expense = (
                    Expense.objects.filter(
                        accountability=expense.accountability,
                        conciled=False,
                        paid=False,
                    )
                    .order_by("value", "identification")
                    .first()
                )
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
    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
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
            with db_transaction.atomic():
                revenue.conciled = True
                revenue.conciled_at = timezone.now()
                revenue.paid = True
                revenue.liquidation = form.cleaned_data["transactions"][0].date
                revenue.save()
                revenue.bank_transactions.set(form.cleaned_data["transactions"])

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.RECONCILED_REVENUE,
                    target_object_id=revenue.id,
                    target_content_object=revenue,
                )

            action = request.POST.get("action")
            if action == "next":
                next_revenue = (
                    Revenue.objects.filter(
                        accountability=revenue.accountability,
                        conciled=False,
                        paid=False,
                    )
                    .order_by("value", "identification")
                    .first()
                )
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

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=accountability.id,
        )

    files = request.FILES.getlist("files")
    with db_transaction.atomic():
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

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("accountability:accountability-detail", pk=accountability.pk)


@login_required
def expense_document_workspace_view(request, pk):
    """Manage many expense documents without round-trips between expense pages."""
    accountability = get_object_or_404(
        Accountability.objects.select_related("contract"), id=pk
    )
    if not request.user.can_update_accountability or not accountability.is_on_execution:
        return redirect("accountability:accountability-detail", pk=accountability.id)
    return render(
        request,
        "accountability/expenses/document-workspace.html",
        {"accountability": accountability},
    )


def _workspace_page(request, queryset):
    try:
        page = max(1, int(request.GET.get("page") or 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(request.GET.get("page_size") or EXPENSE_DOCUMENT_PAGE_SIZE)
    except (TypeError, ValueError):
        page_size = EXPENSE_DOCUMENT_PAGE_SIZE
    page_size = max(1, min(page_size, EXPENSE_DOCUMENT_MAX_PAGE_SIZE))
    offset = (page - 1) * page_size
    rows = list(queryset[offset : offset + page_size + 1])
    return rows[:page_size], len(rows) > page_size, page


@require_GET
@login_required
def expense_document_list_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    if not request.user.can_update_accountability or not accountability.is_on_execution:
        return JsonResponse({"error": "Consulta não permitida."}, status=403)

    base_documents = ExpenseFile.objects.filter(
        accountability=accountability,
        deleted_at__isnull=True,
    )
    totals = base_documents.aggregate(
        total=Count("id"),
        unassigned_total=Count("id", filter=Q(expense__isnull=True)),
    )

    documents = base_documents.select_related("expense")
    if request.GET.get("scope") != "all":
        documents = documents.filter(expense__isnull=True)
    query = (request.GET.get("q") or "").strip()
    if query:
        documents = documents.filter(name__icontains=query)
    documents = documents.order_by("-created_at", "pk")

    rows, has_more, page = _workspace_page(request, documents)
    return JsonResponse(
        {
            "results": [
                {
                    "id": str(document.id),
                    "name": document.name,
                    "url": document.file.url,
                    "is_image": document.name.lower().endswith(
                        (".jpg", ".jpeg", ".png")
                    ),
                    "expense_id": (
                        str(document.expense_id) if document.expense_id else None
                    ),
                    "expense_name": (
                        document.expense.identification if document.expense else None
                    ),
                }
                for document in rows
            ],
            "has_more": has_more,
            "page": page,
            "total": totals["total"],
            "unassigned_total": totals["unassigned_total"],
        }
    )


@require_GET
@login_required
def expense_document_expense_list_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    if not request.user.can_update_accountability or not accountability.is_on_execution:
        return JsonResponse({"error": "Consulta não permitida."}, status=403)

    expenses = (
        Expense.objects.filter(
            accountability=accountability,
            deleted_at__isnull=True,
        )
        .select_related("favored")
        .annotate(
            document_count=Count(
                "files",
                filter=Q(files__deleted_at__isnull=True),
                distinct=True,
            )
        )
    )
    query = (request.GET.get("q") or "").strip()
    if query:
        expenses = expenses.filter(
            Q(identification__icontains=query) | Q(favored__name__icontains=query)
        )
    if (request.GET.get("without_documents") or "").lower() == "true":
        expenses = expenses.filter(document_count=0)
    expenses = expenses.order_by(
        "document_count",
        "-value",
        "identification",
        "pk",
    )

    rows, has_more, page = _workspace_page(request, expenses)
    return JsonResponse(
        {
            "results": [
                {
                    "id": str(expense.id),
                    "identification": expense.identification,
                    "favored_name": (
                        expense.favored.name if expense.favored else "Sem favorecido"
                    ),
                    "nature_label": expense.nature_label,
                    "document_type_label": expense.document_type_label,
                    "due_date": (
                        expense.due_date.strftime("%d/%m/%Y")
                        if expense.due_date
                        else None
                    ),
                    "value": str(expense.value),
                    "document_count": expense.document_count,
                }
                for expense in rows
            ],
            "has_more": has_more,
            "page": page,
        }
    )


@require_POST
@login_required
def bulk_upload_expense_documents_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    if not request.user.can_update_accountability or not accountability.is_on_execution:
        return JsonResponse({"error": "Upload não permitido."}, status=403)

    files = request.FILES.getlist("files")
    if not files:
        return JsonResponse({"error": "Selecione ao menos um arquivo."}, status=400)
    if len(files) > EXPENSE_DOCUMENT_MAX_FILES:
        return JsonResponse(
            {
                "error": f"Envie no máximo {EXPENSE_DOCUMENT_MAX_FILES} arquivos por vez."
            },
            status=400,
        )

    errors = []
    for uploaded_file in files:
        extension = (
            f".{uploaded_file.name.rsplit('.', 1)[-1].lower()}"
            if "." in uploaded_file.name
            else ""
        )
        if extension not in EXPENSE_DOCUMENT_EXTENSIONS:
            errors.append(f"{uploaded_file.name}: formato não aceito")
        elif uploaded_file.size > EXPENSE_DOCUMENT_MAX_SIZE:
            errors.append(f"{uploaded_file.name}: excede 10 MB")
        else:
            header = uploaded_file.read(8)
            uploaded_file.seek(0)
            if not any(
                header.startswith(signature)
                for signature in EXPENSE_DOCUMENT_SIGNATURES[extension]
            ):
                errors.append(f"{uploaded_file.name}: conteúdo inválido")
    if errors:
        return JsonResponse({"error": errors[0], "errors": errors}, status=400)

    created = []
    for uploaded_file in files:
        document = ExpenseFile.objects.create(
            accountability=accountability,
            created_by=request.user,
            name=uploaded_file.name[:128],
            file=uploaded_file,
        )
        created.append(
            {
                "id": str(document.id),
                "name": document.name,
                "url": document.file.url,
                "is_image": document.name.lower().endswith((".jpg", ".jpeg", ".png")),
            }
        )

    return JsonResponse({"documents": created}, status=201)


@require_POST
@login_required
def assign_expense_documents_view(request, pk):
    accountability = get_object_or_404(Accountability, id=pk)
    if not request.user.can_update_accountability or not accountability.is_on_execution:
        return JsonResponse({"error": "Alteração não permitida."}, status=403)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Dados inválidos."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Dados inválidos."}, status=400)
    document_ids = payload.get("document_ids") or []
    if not isinstance(document_ids, list) or not document_ids:
        return JsonResponse({"error": "Selecione ao menos um documento."}, status=400)
    if not all(isinstance(document_id, str) for document_id in document_ids):
        return JsonResponse({"error": "Documentos inválidos."}, status=400)

    expense_id = payload.get("expense_id")
    expense = None
    if expense_id:
        expense = get_object_or_404(
            Expense,
            id=expense_id,
            accountability=accountability,
            deleted_at__isnull=True,
        )

    with db_transaction.atomic():
        documents = list(
            ExpenseFile.objects.select_for_update().filter(
                id__in=document_ids,
                accountability=accountability,
                deleted_at__isnull=True,
            )
        )
        if len(documents) != len(set(document_ids)):
            return JsonResponse(
                {"error": "Um ou mais documentos não existem."}, status=400
            )
        for document in documents:
            document.expense = expense
            document.save(update_fields=["expense", "accountability", "updated_at"])

    return JsonResponse(
        {
            "document_ids": [str(document.id) for document in documents],
            "expense_id": str(expense.id) if expense else None,
            "expense_name": expense.identification if expense else None,
        }
    )


@require_POST
@login_required
def upload_revenue_file_view(request, pk):
    """Upload files for a revenue."""
    revenue = get_object_or_404(Revenue, pk=pk)
    accountability = revenue.accountability

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
        )

    files = request.FILES.getlist("files")
    with db_transaction.atomic():
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

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("accountability:accountability-detail", pk=accountability.pk)


@require_POST
@login_required
def delete_expense_file_view(request, pk):
    """Delete an expense file."""
    file = get_object_or_404(ExpenseFile, pk=pk)
    accountability = file.accountability or file.expense.accountability

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=accountability.id,
        )

    with db_transaction.atomic():
        file.delete()
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_EXPENSE_FILE,
            target_object_id=file.expense_id or accountability.id,
            target_content_object=file.expense or accountability,
        )

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("accountability:accountability-detail", pk=accountability.pk)


@require_POST
@login_required
def delete_revenue_file_view(request, pk):
    """Delete a revenue file."""
    file = get_object_or_404(RevenueFile, pk=pk)
    accountability = file.revenue.accountability

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=accountability.id,
        )

    with db_transaction.atomic():
        file.delete()
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_REVENUE_FILE,
            target_object_id=file.revenue.id,
            target_content_object=file.revenue,
        )

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("accountability:accountability-detail", pk=accountability.pk)


class BeneficiariesDashboardView(LoginRequiredMixin, ListView):
    """View to display a dashboard of all beneficiaries with expenses."""

    model = Favored
    template_name = "accountability/beneficiaries/dashboard.html"
    context_object_name = "beneficiaries"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            organization=self.request.user.organization,
            expenses__deleted_at__isnull=True,
        ).distinct()

        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(document__icontains=search_query)
            )

        area_id = self.request.GET.get("area")
        if area_id:
            queryset = queryset.filter(
                expenses__accountability__contract__area_id=area_id
            )

        contract_id = self.request.GET.get("contract")
        if contract_id:
            queryset = queryset.filter(
                expenses__accountability__contract_id=contract_id
            )

        queryset = queryset.annotate(
            total_cost=Sum(
                "expenses__value", filter=Q(expenses__deleted_at__isnull=True)
            )
        ).filter(total_cost__gt=0)  # Only include beneficiaries with expenses

        return queryset.order_by("-total_cost")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["areas"] = Area.objects.filter(
            organization=self.request.user.organization
        ).order_by("name")

        context["contracts"] = Contract.objects.filter(
            organization=self.request.user.organization
        ).order_by("name")

        context["selected_area"] = self.request.GET.get("area")
        context["selected_contract"] = self.request.GET.get("contract")
        context["search_query"] = self.request.GET.get("search", "")

        return context


class AdvancedSearchView(UserAccessViewMixin, LoginRequiredMixin, TemplateView):
    template_name = "accountability/search/advanced_search.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filter parameters
        search_query = self.request.GET.get("q", "")
        record_type = self.request.GET.get("type", "all")  # all, expense, revenue
        start_date = self.request.GET.get("start_date", "")
        end_date = self.request.GET.get("end_date", "")
        conciled_status = self.request.GET.get(
            "conciled", "all"
        )  # all, conciled, not_conciled
        contract_id = self.request.GET.get("contract", "")
        favored_id = self.request.GET.get("favored", "")
        status = self.request.GET.get(
            "status", "all"
        )  # all, pending, approved, rejected
        paid_status = self.request.GET.get("paid", "all")  # all, paid, unpaid

        expenses_list = []
        revenues_list = []
        if record_type in ["all", "expense"]:
            expenses_qs = Expense.objects.select_related(
                "accountability__contract", "item", "favored"
            ).filter(
                deleted_at__isnull=True,
            )

            expenses_qs = self.get_user_filtered_queryset(
                expenses_qs, contract_field_prefix="accountability__contract__"
            )

            if search_query:
                expenses_qs = expenses_qs.filter(
                    Q(identification__icontains=search_query)
                    | Q(item__name__icontains=search_query)
                    | Q(favored__name__icontains=search_query)
                    | Q(accountability__contract__name__icontains=search_query)
                )

            if start_date and end_date:
                expenses_qs = expenses_qs.filter(
                    competency__range=[start_date, end_date]
                )

            if conciled_status != "all":
                expenses_qs = expenses_qs.filter(conciled=conciled_status == "conciled")

            if contract_id:
                expenses_qs = expenses_qs.filter(
                    accountability__contract_id=contract_id
                )

            if favored_id:
                expenses_qs = expenses_qs.filter(favored_id=favored_id)

            if status != "all":
                expenses_qs = expenses_qs.filter(status=status)

            if paid_status != "all":
                expenses_qs = expenses_qs.filter(paid=paid_status == "paid")

            expenses_list = expenses_qs.order_by("-competency", "-value")[:100]

        if record_type in ["all", "revenue"]:
            revenues_qs = Revenue.objects.select_related(
                "accountability__contract", "bank_account"
            ).filter(
                deleted_at__isnull=True,
            )
            revenues_qs = self.get_user_filtered_queryset(
                revenues_qs, contract_field_prefix="accountability__contract__"
            )

            if search_query:
                revenues_qs = revenues_qs.filter(identification__icontains=search_query)

            if start_date and end_date:
                revenues_qs = revenues_qs.filter(
                    competency__range=[start_date, end_date]
                )

            if conciled_status != "all":
                revenues_qs = revenues_qs.filter(conciled=conciled_status == "conciled")

            if contract_id:
                revenues_qs = revenues_qs.filter(
                    accountability__contract_id=contract_id
                )

            if status != "all":
                revenues_qs = revenues_qs.filter(status=status)

            if paid_status != "all":
                revenues_qs = revenues_qs.filter(paid=paid_status == "paid")

            revenues_list = revenues_qs.order_by("-competency", "-value")[:100]

        contracts = Contract.objects.filter(
            area__in=self.request.user.areas.all()
        ).order_by("name")

        favoreds = Favored.objects.filter(
            organization=self.request.user.organization
        ).order_by("name")

        context.update(
            {
                "expenses": expenses_list,
                "revenues": revenues_list,
                "contracts": contracts,
                "favoreds": favoreds,
                "search_query": search_query,
                "record_type": record_type,
                "start_date": start_date,
                "end_date": end_date,
                "conciled_status": conciled_status,
                "contract_id": contract_id,
                "favored_id": favored_id,
                "status": status,
                "paid_status": paid_status,
                "expenses_total": sum(e.value for e in expenses_list),
                "revenues_total": sum(r.value for r in revenues_list),
            }
        )

        return context


class BeneficiaryDetailView(LoginRequiredMixin, DetailView):
    """View to display detailed information about a beneficiary."""

    model = Favored
    template_name = "accountability/beneficiaries/detail.html"
    context_object_name = "beneficiary"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        beneficiary = self.get_object()

        expenses = (
            Expense.objects.filter(favored=beneficiary, deleted_at__isnull=True)
            .select_related("accountability__contract")
            .order_by("-competency")
        )

        contracts = Contract.objects.filter(
            accountabilities__expenses__favored=beneficiary,
            accountabilities__expenses__deleted_at__isnull=True,
        ).distinct()

        contract_costs = []
        for contract in contracts:
            # Calculate cost for this contract
            cost = (
                Expense.objects.filter(
                    favored=beneficiary,
                    accountability__contract=contract,
                    deleted_at__isnull=True,
                ).aggregate(total=Sum("value"))["total"]
                or 0
            )

            contract_costs.append({"contract": contract, "cost": cost})

        # Calculate total cost
        total_cost = (
            Expense.objects.filter(
                favored=beneficiary, deleted_at__isnull=True
            ).aggregate(total=Sum("value"))["total"]
            or 0
        )

        context["contract_costs"] = contract_costs
        context["total_cost"] = total_cost
        context["expenses"] = expenses

        return context


@log_view_access
@login_required
def batch_reconcile_expenses_view(request, pk):
    """Batch reconciliation view for expenses."""
    if not request.user or not request.user.can_update_accountability:
        return redirect("accountability:accountability-detail", pk=pk)

    accountability = get_object_or_404(Accountability, id=pk)

    if not accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail",
            pk=accountability.id,
        )

    contract = accountability.contract
    unreconciled_expenses = (
        Expense.objects.filter(
            accountability=accountability, conciled=False, deleted_at__isnull=True
        )
        .select_related("favored", "item")
        .order_by("-value")
    )

    start_date = date(accountability.year, accountability.month, 1)
    if accountability.month == 12:
        end_date = date(accountability.year + 1, 1, 1)
    else:
        end_date = date(accountability.year, accountability.month + 1, 1)

    available_transactions = (
        Transaction.objects.filter(
            Q(bank_account=contract.checking_account)
            | Q(bank_account=contract.investing_account)
        )
        .filter(
            expenses__isnull=True,
            amount__lt=0,  # Negative amounts for expenses
            date__gte=start_date,
            date__lt=end_date,
        )
        .order_by("date")
    )

    def normalize_text(text):
        if not text:
            return ""

        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
        return text.upper()

    matches = []
    used_transaction_ids = set()

    for expense in unreconciled_expenses:
        candidate_transactions = [
            t
            for t in available_transactions
            if abs(abs(t.amount) - expense.value) < 0.01
            and t.id not in used_transaction_ids
        ]

        matched_transaction = None

        if len(candidate_transactions) == 1:
            matched_transaction = candidate_transactions[0]
        elif len(candidate_transactions) > 1 and expense.favored:
            first_name = expense.favored.name.split()[0] if expense.favored.name else ""
            first_name_normalized = normalize_text(first_name)
            if first_name_normalized and len(first_name_normalized) > 2:
                matching_by_name = []
                for transaction in candidate_transactions:
                    transaction_text = normalize_text(
                        f"{transaction.memo or ''} {transaction.name or ''}"
                    )
                    if first_name_normalized in transaction_text:
                        matching_by_name.append(transaction)

                if len(matching_by_name) == 1:
                    matched_transaction = matching_by_name[0]

        if matched_transaction:
            used_transaction_ids.add(matched_transaction.id)
            matches.append(
                {
                    "expense": expense,
                    "transaction": matched_transaction,
                    "matched": True,
                }
            )
        else:
            matches.append({"expense": expense, "transaction": None, "matched": False})

    if request.method == "POST":
        reconciliations = []

        for expense in unreconciled_expenses:
            transaction_id = request.POST.get(f"transaction_{expense.id}")
            # Only process if user selected a transaction (not empty)
            if transaction_id and transaction_id.strip():
                try:
                    trans = Transaction.objects.get(id=transaction_id)
                    reconciliations.append((expense, trans))
                except Transaction.DoesNotExist:
                    continue
            # If transaction_id is empty or None, we skip this expense (user was unsure)
        if reconciliations:
            with db_transaction.atomic():
                for expense, trans in reconciliations:
                    expense.conciled = True
                    expense.conciled_at = timezone.now()
                    expense.paid = True
                    expense.liquidation = trans.date
                    expense.save()

                    expense.bank_transactions.add(trans)
                    ActivityLog.objects.create(
                        user=request.user,
                        user_email=request.user.email,
                        action=ActivityLog.ActivityLogChoices.RECONCILED_EXPENSE,
                        target_object_id=expense.id,
                        target_content_object=expense,
                    )

                return redirect(
                    "accountability:accountability-detail", pk=accountability.id
                )

    context = {
        "accountability": accountability,
        "matches": matches,
        "available_transactions": available_transactions,
        "unreconciled_count": unreconciled_expenses.count(),
    }

    return render(request, "accountability/expenses/batch-reconcile.html", context)


@log_database_operation("unreconcile_expense")
@log_view_access
@login_required
def unreconcile_expense_view(request, pk):
    expense = get_object_or_404(
        Expense.objects.select_related(
            "accountability",
            "accountability__contract",
        ),
        id=pk,
    )

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=expense.accountability.id,
        )

    if not expense.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail",
            pk=expense.accountability.id,
        )

    if not expense.conciled:
        return redirect(
            "accountability:accountability-detail",
            pk=expense.accountability.id,
        )

    if request.method == "POST":
        with db_transaction.atomic():
            expense.conciled = False
            expense.conciled_at = None
            expense.paid = False
            expense.liquidation = None
            expense.save()
            expense.bank_transactions.clear()
            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.UPDATED_EXPENSE,
                target_object_id=expense.id,
                target_content_object=expense,
            )

        return redirect(
            "accountability:accountability-detail",
            pk=expense.accountability.id,
        )

    return redirect(
        "accountability:accountability-detail",
        pk=expense.accountability.id,
    )


@log_database_operation("unreconcile_revenue")
@log_view_access
@login_required
def unreconcile_revenue_view(request, pk):
    revenue = get_object_or_404(
        Revenue.objects.select_related(
            "accountability",
            "accountability__contract",
        ),
        id=pk,
    )

    if not request.user.can_update_accountability:
        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
        )

    if not revenue.accountability.is_on_execution:
        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
        )

    if not revenue.conciled:
        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
        )

    if request.method == "POST":
        with db_transaction.atomic():
            revenue.conciled = False
            revenue.conciled_at = None
            revenue.paid = False
            revenue.save()
            revenue.transactions.clear()
            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.UPDATED_REVENUE,
                target_object_id=revenue.id,
                target_content_object=revenue,
            )

        return redirect(
            "accountability:accountability-detail",
            pk=revenue.accountability.id,
        )

    return redirect(
        "accountability:accountability-detail",
        pk=revenue.accountability.id,
    )


# =============================================================================
# AUDESP Fase V - user-facing CRUD for the Phase 0 domain models. Until now
# these existed only in Django admin (see accountability/admin.py); the views
# below give city hall / OSC staff an actual in-app way to enter this data.
#
# Design notes:
# - None of these views write to `activity.ActivityLog`: every existing
#   `ActivityLogChoices` member is specific to an already-shipped feature, and
#   adding new members would alter `ActivityLog.action`'s `choices=` kwarg,
#   which `makemigrations` treats as a model state change requiring a new
#   migration - contradicting this change's "views/urls/templates only, no
#   model changes" scope.
# - `organization` is intentionally never set explicitly on these new rows:
#   `accounts.middlewares.TenantMiddleware` already wraps every authenticated
#   request in `tenant_context(request.user.organization)`, and
#   `OrganizationTenantBaseClass.save()` picks that up automatically - the
#   same assumption `create_contract_accountability_view` above already
#   relies on.
# =============================================================================


@method_decorator(log_view_access, name="dispatch")
class AnnualStatementListView(UserAccessViewMixin, LoginRequiredMixin, ListView):
    model = AnnualStatement
    context_object_name = "annual_statements"
    paginate_by = 10
    ordering = "-fiscal_year"
    contract_field_prefix = "contract__"

    template_name = "accountability/annual_statement/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        query = self.request.GET.get("q", "")
        queryset = self.model.objects.select_related("contract")
        queryset = self.get_user_filtered_queryset(queryset)

        if query:
            queryset = queryset.filter(Q(contract__name__icontains=query))

        return queryset.order_by("-fiscal_year", "contract__name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


@login_required
def create_contract_annual_statement_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = AnnualStatementCreateForm(request.POST)
        if form.is_valid():
            exists = AnnualStatement.objects.filter(
                contract=contract,
                fiscal_year=form.cleaned_data["fiscal_year"],
            ).exists()
            if exists:
                return render(
                    request,
                    "accountability/annual_statement/create.html",
                    {
                        "contract": contract,
                        "form": form,
                        "annual_statement_exists": True,
                    },
                )

            annual_statement = form.save(commit=False)
            annual_statement.contract = contract
            annual_statement.save()
            return redirect(
                "accountability:annual-statement-detail", pk=annual_statement.id
            )

        return render(
            request,
            "accountability/annual_statement/create.html",
            {"contract": contract, "form": form},
        )

    form = AnnualStatementCreateForm()
    return render(
        request,
        "accountability/annual_statement/create.html",
        {"contract": contract, "form": form},
    )


@login_required
def annual_statement_detail_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )

    context = {
        "annual_statement": annual_statement,
        "contract": annual_statement.contract,
        "purchasing_regulation": getattr(
            annual_statement, "purchasing_regulation", None
        ),
        "execution_statement": getattr(annual_statement, "execution_statement", None),
        "financial_statements": getattr(annual_statement, "financial_statements", None),
        "activity_report_publication_status": getattr(
            annual_statement, "activity_report_publication_status", None
        ),
        "conflict_of_interest_declaration": getattr(
            annual_statement, "conflict_of_interest_declaration", None
        ),
        "conclusive_opinion": getattr(annual_statement, "conclusive_opinion", None),
        "opinions_or_minutes": annual_statement.opinions_or_minutes.order_by("type"),
        "evaluation_reports": annual_statement.evaluation_reports.order_by("type"),
    }
    return render(request, "accountability/annual_statement/detail.html", context)


class AnnualStatementUpdateView(LoginRequiredMixin, UpdateView):
    model = AnnualStatement
    form_class = AnnualStatementUpdateForm
    template_name = "accountability/annual_statement/update.html"
    context_object_name = "annual_statement"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_success_url(self) -> str:
        return reverse_lazy(
            "accountability:annual-statement-detail", kwargs={"pk": self.object.id}
        )


# --- Empenhos (BudgetCommitment) and Repasses (FundTransfer) - manual §17/§18,
# both contract-scoped ledgers surfaced as a tab on the contract detail page.


@login_required
def create_budget_commitment_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = BudgetCommitmentForm(request.POST)
        if form.is_valid():
            # `contract` is excluded from the form (assigned from the URL, not
            # user input), so Django's automatic validate_unique() silently
            # skips `unique_budget_commitment_per_agreement` entirely (any
            # constraint touching an excluded field is skipped, regardless of
            # what the instance's field value actually is) - check by hand or
            # a genuine duplicate raises a raw IntegrityError instead of a
            # friendly form error.
            exists = BudgetCommitment.objects.filter(
                contract=contract,
                number=form.cleaned_data["number"],
                issue_date=form.cleaned_data["issue_date"],
            ).exists()
            if exists:
                return render(
                    request,
                    "accountability/budget_commitment/create.html",
                    {
                        "contract": contract,
                        "form": form,
                        "budget_commitment_exists": True,
                    },
                )

            budget_commitment = form.save(commit=False)
            budget_commitment.contract = contract
            budget_commitment.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "accountability/budget_commitment/create.html",
            {"contract": contract, "form": form},
        )

    form = BudgetCommitmentForm()
    return render(
        request,
        "accountability/budget_commitment/create.html",
        {"contract": contract, "form": form},
    )


class BudgetCommitmentUpdateView(LoginRequiredMixin, UpdateView):
    model = BudgetCommitment
    form_class = BudgetCommitmentForm
    template_name = "accountability/budget_commitment/create.html"
    context_object_name = "budget_commitment"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contract"] = self.object.contract
        return context

    def form_valid(self, form):
        # Same excluded-field gap as create_budget_commitment_view: `contract`
        # isn't a form field, so Django's automatic validate_unique() skips
        # unique_budget_commitment_per_agreement outright - check by hand.
        exists = (
            BudgetCommitment.objects.filter(
                contract=self.object.contract,
                number=form.cleaned_data["number"],
                issue_date=form.cleaned_data["issue_date"],
            )
            .exclude(pk=self.object.pk)
            .exists()
        )
        if exists:
            return self.render_to_response(
                self.get_context_data(form=form, budget_commitment_exists=True)
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail", kwargs={"pk": self.object.contract.id}
        )


# --- §12 Ajustes de Saldo, §14 Descontos, §15 Devoluções, §16 Glosas - all
# simple contract-scoped ledger adjustments, same tab as Empenhos/Repasses.


@login_required
def create_balance_adjustment_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = BalanceAdjustmentForm(request.POST, contract=contract)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.contract = contract
            adjustment.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "accountability/balance_adjustment/create.html",
            {"contract": contract, "form": form},
        )

    form = BalanceAdjustmentForm(contract=contract)
    return render(
        request,
        "accountability/balance_adjustment/create.html",
        {"contract": contract, "form": form},
    )


class BalanceAdjustmentUpdateView(LoginRequiredMixin, UpdateView):
    model = BalanceAdjustment
    form_class = BalanceAdjustmentForm
    template_name = "accountability/balance_adjustment/create.html"
    context_object_name = "balance_adjustment"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["contract"] = self.object.contract
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contract"] = self.object.contract
        return context

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail", kwargs={"pk": self.object.contract.id}
        )


@login_required
def create_expense_rejection_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = ExpenseRejectionForm(request.POST, contract=contract)
        if form.is_valid():
            rejection = form.save(commit=False)
            rejection.contract = contract
            rejection.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "accountability/expense_rejection/create.html",
            {"contract": contract, "form": form},
        )

    form = ExpenseRejectionForm(contract=contract)
    return render(
        request,
        "accountability/expense_rejection/create.html",
        {"contract": contract, "form": form},
    )


class ExpenseRejectionUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpenseRejection
    form_class = ExpenseRejectionForm
    template_name = "accountability/expense_rejection/create.html"
    context_object_name = "expense_rejection"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["contract"] = self.object.contract
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contract"] = self.object.contract
        return context

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail", kwargs={"pk": self.object.contract.id}
        )


@login_required
def create_deduction_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = DeductionForm(request.POST)
        if form.is_valid():
            deduction = form.save(commit=False)
            deduction.contract = contract
            deduction.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "accountability/deduction/create.html",
            {"contract": contract, "form": form},
        )

    form = DeductionForm()
    return render(
        request,
        "accountability/deduction/create.html",
        {"contract": contract, "form": form},
    )


class DeductionUpdateView(LoginRequiredMixin, UpdateView):
    model = Deduction
    form_class = DeductionForm
    template_name = "accountability/deduction/create.html"
    context_object_name = "deduction"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contract"] = self.object.contract
        return context

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail", kwargs={"pk": self.object.contract.id}
        )


@login_required
def create_refund_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = RefundForm(request.POST)
        if form.is_valid():
            refund = form.save(commit=False)
            refund.contract = contract
            refund.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "accountability/refund/create.html",
            {"contract": contract, "form": form},
        )

    form = RefundForm()
    return render(
        request,
        "accountability/refund/create.html",
        {"contract": contract, "form": form},
    )


class RefundUpdateView(LoginRequiredMixin, UpdateView):
    model = Refund
    form_class = RefundForm
    template_name = "accountability/refund/create.html"
    context_object_name = "refund"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contract"] = self.object.contract
        return context

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail", kwargs={"pk": self.object.contract.id}
        )


# --- §22 Regulamento de Compras, §23 Extrato de Execução, §28 Demonstrações
# Contábeis and §30 Publicação do Relatório de Atividades are all a single
# one-to-one "settings for this year" record plus a small list of
# publications - so each gets a get-or-create-then-edit view of identical
# shape, just parametrized by model/form/formset.


@login_required
def annual_statement_purchasing_regulation_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )
    regulation, _ = PurchasingRegulation.objects.get_or_create(
        annual_statement=annual_statement
    )

    if request.method == "POST":
        form = PurchasingRegulationForm(request.POST, instance=regulation)
        formset = PurchasingRegulationPublicationFormSet(
            request.POST, instance=regulation
        )
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                form.save()
                formset.save()
            return redirect(
                "accountability:annual-statement-detail", pk=annual_statement.id
            )
    else:
        form = PurchasingRegulationForm(instance=regulation)
        formset = PurchasingRegulationPublicationFormSet(instance=regulation)

    return render(
        request,
        "accountability/annual_statement/purchasing_regulation.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "form": form,
            "formset": formset,
        },
    )


@login_required
def annual_statement_execution_statement_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )
    statement, _ = PhysicalFinancialExecutionStatement.objects.get_or_create(
        annual_statement=annual_statement
    )

    if request.method == "POST":
        form = PhysicalFinancialExecutionStatementForm(request.POST, instance=statement)
        formset = PhysicalFinancialExecutionStatementPublicationFormSet(
            request.POST, instance=statement
        )
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                form.save()
                formset.save()
            return redirect(
                "accountability:annual-statement-detail", pk=annual_statement.id
            )
    else:
        form = PhysicalFinancialExecutionStatementForm(instance=statement)
        formset = PhysicalFinancialExecutionStatementPublicationFormSet(
            instance=statement
        )

    return render(
        request,
        "accountability/annual_statement/execution_statement.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "form": form,
            "formset": formset,
        },
    )


@login_required
def annual_statement_financial_statements_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )
    statements, _ = FinancialStatements.objects.get_or_create(
        annual_statement=annual_statement
    )

    if request.method == "POST":
        form = FinancialStatementsForm(request.POST, instance=statements)
        formset = FinancialStatementsPublicationFormSet(
            request.POST, instance=statements
        )
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                form.save()
                formset.save()
            return redirect(
                "accountability:annual-statement-detail", pk=annual_statement.id
            )
    else:
        form = FinancialStatementsForm(instance=statements)
        formset = FinancialStatementsPublicationFormSet(instance=statements)

    return render(
        request,
        "accountability/annual_statement/financial_statements.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "form": form,
            "formset": formset,
        },
    )


@login_required
def annual_statement_activity_report_publication_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )
    status, _ = ActivityReportPublicationStatus.objects.get_or_create(
        annual_statement=annual_statement
    )

    if request.method == "POST":
        form = ActivityReportPublicationStatusForm(request.POST, instance=status)
        formset = ActivityReportPublicationFormSet(request.POST, instance=status)
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                form.save()
                formset.save()
            return redirect(
                "accountability:annual-statement-detail", pk=annual_statement.id
            )
    else:
        form = ActivityReportPublicationStatusForm(instance=status)
        formset = ActivityReportPublicationFormSet(instance=status)

    return render(
        request,
        "accountability/annual_statement/activity_report_publication.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "form": form,
            "formset": formset,
        },
    )


# --- §29 Parecer ou Ata - FK (not one-to-one): a statement can carry more
# than one, one per `OpinionOrMinutes.TypeChoices` member.


@login_required
def create_annual_statement_opinion_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )

    opinion_type_exists = False

    if request.method == "POST":
        form = OpinionOrMinutesForm(request.POST)
        formset = OpinionOrMinutesPublicationFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            # `annual_statement` is excluded from the form, so
            # unique_opinion_or_minutes_type_per_annual_statement is never
            # checked by Django's automatic validate_unique() (see the
            # analogous comment on create_budget_commitment_view) - check by
            # hand instead of letting a genuine duplicate raise a raw
            # IntegrityError.
            opinion_type_exists = OpinionOrMinutes.objects.filter(
                annual_statement=annual_statement,
                type=form.cleaned_data["type"],
            ).exists()
            if not opinion_type_exists:
                with db_transaction.atomic():
                    opinion = form.save(commit=False)
                    opinion.annual_statement = annual_statement
                    opinion.save()

                    publications = formset.save(commit=False)
                    for publication in publications:
                        publication.opinion_or_minutes = opinion
                        publication.save()

                return redirect(
                    "accountability:annual-statement-detail", pk=annual_statement.id
                )
    else:
        form = OpinionOrMinutesForm()
        formset = OpinionOrMinutesPublicationFormSet()

    return render(
        request,
        "accountability/annual_statement/opinion_form.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "form": form,
            "formset": formset,
            "opinion_type_exists": opinion_type_exists,
        },
    )


@login_required
def update_annual_statement_opinion_view(request, pk, opinion_pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )
    opinion = get_object_or_404(
        OpinionOrMinutes, id=opinion_pk, annual_statement=annual_statement
    )

    opinion_type_exists = False

    if request.method == "POST":
        form = OpinionOrMinutesForm(request.POST, instance=opinion)
        formset = OpinionOrMinutesPublicationFormSet(request.POST, instance=opinion)
        if form.is_valid() and formset.is_valid():
            # Same excluded-field gap as create_annual_statement_opinion_view
            # - check by hand.
            opinion_type_exists = (
                OpinionOrMinutes.objects.filter(
                    annual_statement=annual_statement,
                    type=form.cleaned_data["type"],
                )
                .exclude(pk=opinion.pk)
                .exists()
            )
            if not opinion_type_exists:
                with db_transaction.atomic():
                    form.save()
                    formset.save()
                return redirect(
                    "accountability:annual-statement-detail", pk=annual_statement.id
                )
    else:
        form = OpinionOrMinutesForm(instance=opinion)
        formset = OpinionOrMinutesPublicationFormSet(instance=opinion)

    return render(
        request,
        "accountability/annual_statement/opinion_form.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "opinion": opinion,
            "form": form,
            "formset": formset,
            "opinion_type_exists": opinion_type_exists,
        },
    )


# --- §25/§26/§27 Relatório de Avaliação/Governamental/Monitoramento - FK, no
# publications of its own.


@login_required
def create_annual_statement_evaluation_report_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )

    report_type_exists = False

    if request.method == "POST":
        form = EvaluationReportForm(request.POST)
        if form.is_valid():
            # `annual_statement` is excluded from the form, so
            # unique_evaluation_report_type_per_annual_statement is never
            # checked by Django's automatic validate_unique() (see the
            # analogous comment on create_budget_commitment_view) - check by
            # hand instead of letting a genuine duplicate raise a raw
            # IntegrityError.
            report_type_exists = EvaluationReport.objects.filter(
                annual_statement=annual_statement,
                type=form.cleaned_data["type"],
            ).exists()
            if not report_type_exists:
                report = form.save(commit=False)
                report.annual_statement = annual_statement
                report.save()
                return redirect(
                    "accountability:annual-statement-detail", pk=annual_statement.id
                )
    else:
        form = EvaluationReportForm()

    return render(
        request,
        "accountability/annual_statement/evaluation_report_form.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "report_type_exists": report_type_exists,
            "form": form,
        },
    )


class EvaluationReportUpdateView(LoginRequiredMixin, UpdateView):
    model = EvaluationReport
    form_class = EvaluationReportForm
    template_name = "accountability/annual_statement/evaluation_report_form.html"
    context_object_name = "report"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("annual_statement__contract").get(
            id=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["annual_statement"] = self.object.annual_statement
        context["contract"] = self.object.annual_statement.contract
        return context

    def form_valid(self, form):
        # Same excluded-field gap as create_annual_statement_evaluation_report_view
        # - check by hand.
        exists = (
            EvaluationReport.objects.filter(
                annual_statement=self.object.annual_statement,
                type=form.cleaned_data["type"],
            )
            .exclude(pk=self.object.pk)
            .exists()
        )
        if exists:
            return self.render_to_response(
                self.get_context_data(form=form, report_type_exists=True)
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(
            "accountability:annual-statement-detail",
            kwargs={"pk": self.object.annual_statement.id},
        )


# --- §24 Declarações (conflito de interesse) - one-to-one plus two small
# inline lists (empresas pertencentes / participação no quadro diretivo).


@login_required
def annual_statement_conflict_of_interest_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )
    declaration, _ = ConflictOfInterestDeclaration.objects.get_or_create(
        annual_statement=annual_statement
    )

    if request.method == "POST":
        form = ConflictOfInterestDeclarationForm(request.POST, instance=declaration)
        companies_formset = RelatedCompanyFormSet(
            request.POST, instance=declaration, prefix="companies"
        )
        board_formset = BoardParticipationFormSet(
            request.POST, instance=declaration, prefix="board"
        )
        if (
            form.is_valid()
            and companies_formset.is_valid()
            and board_formset.is_valid()
        ):
            with db_transaction.atomic():
                form.save()
                companies_formset.save()
                board_formset.save()
            return redirect(
                "accountability:annual-statement-detail", pk=annual_statement.id
            )
    else:
        form = ConflictOfInterestDeclarationForm(instance=declaration)
        companies_formset = RelatedCompanyFormSet(
            instance=declaration, prefix="companies"
        )
        board_formset = BoardParticipationFormSet(instance=declaration, prefix="board")

    return render(
        request,
        "accountability/annual_statement/conflict_of_interest.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "form": form,
            "companies_formset": companies_formset,
            "board_formset": board_formset,
        },
    )


# --- §33 Parecer Conclusivo - one-to-one plus exactly 7 fixed declarations
# (one per `ConclusiveOpinionDeclaration.DeclarationTypeChoices` member).


@login_required
def annual_statement_conclusive_opinion_view(request, pk):
    annual_statement = get_object_or_404(
        AnnualStatement.objects.select_related("contract"), id=pk
    )
    opinion, _ = ConclusiveOpinion.objects.get_or_create(
        annual_statement=annual_statement
    )

    for (
        declaration_type,
        _label,
    ) in ConclusiveOpinionDeclaration.DeclarationTypeChoices.choices:
        ConclusiveOpinionDeclaration.objects.get_or_create(
            conclusive_opinion=opinion, declaration_type=declaration_type
        )

    declarations_queryset = opinion.declarations.order_by("declaration_type")

    if request.method == "POST":
        form = ConclusiveOpinionForm(request.POST, instance=opinion)
        formset = ConclusiveOpinionDeclarationFormSet(
            request.POST, queryset=declarations_queryset
        )
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                form.save()
                formset.save()
            return redirect(
                "accountability:annual-statement-detail", pk=annual_statement.id
            )
    else:
        form = ConclusiveOpinionForm(instance=opinion)
        formset = ConclusiveOpinionDeclarationFormSet(queryset=declarations_queryset)

    return render(
        request,
        "accountability/annual_statement/conclusive_opinion.html",
        {
            "annual_statement": annual_statement,
            "contract": annual_statement.contract,
            "form": form,
            "formset": formset,
        },
    )


@login_required
def create_fund_transfer_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    budget_commitments_exist = BudgetCommitment.objects.filter(
        contract=contract
    ).exists()

    if request.method == "POST":
        form = FundTransferForm(request.POST, contract=contract)
        if form.is_valid():
            fund_transfer = form.save(commit=False)
            fund_transfer.contract = contract
            fund_transfer.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "accountability/fund_transfer/create.html",
            {
                "contract": contract,
                "form": form,
                "budget_commitments_exist": budget_commitments_exist,
            },
        )

    form = FundTransferForm(contract=contract)
    return render(
        request,
        "accountability/fund_transfer/create.html",
        {
            "contract": contract,
            "form": form,
            "budget_commitments_exist": budget_commitments_exist,
        },
    )


class FundTransferUpdateView(LoginRequiredMixin, UpdateView):
    model = FundTransfer
    form_class = FundTransferForm
    template_name = "accountability/fund_transfer/create.html"
    context_object_name = "fund_transfer"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["contract"] = self.object.contract
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contract"] = self.object.contract
        context["budget_commitments_exist"] = True
        return context

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail", kwargs={"pk": self.object.contract.id}
        )
