import locale
import logging
from calendar import month_abbr
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Prefetch, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from accounts.models import Committee
from activity.models import ActivityLog
from contracts.choices import NatureCategories
from contracts.forms import (
    CompanyCreateForm,
    CompanyUpdateForm,
    ContractCreateForm,
    ContractExecutionActivityForm,
    ContractExecutionCreateForm,
    ContractExecutionFileForm,
    ContractExtraStepFormSet,
    ContractGoalForm,
    ContractInterestedForm,
    ContractItemForm,
    ContractItemPurchaseProcessForm,
    ContractItemSupplementForm,
    ContractItemSupplementUpdateForm,
    ContractItemValueRequestForm,
    ContractStatusUpdateForm,
    ContractStepFormSet,
    ItemValueReviewForm,
)
from contracts.models import (
    Company,
    Contract,
    ContractExecution,
    ContractExecutionActivity,
    ContractExecutionFile,
    ContractGoal,
    ContractGoalReview,
    ContractInterestedPart,
    ContractItem,
    ContractItemNewValueRequest,
    ContractItemPurchaseProcessDocument,
    ContractItemReview,
    ContractItemSupplement,
    ContractMonthTransfer,
)
from utils.choices import StatusChoices
from utils.logging import log_database_operation, log_view_access
from utils.mixins import (
    AdminRequiredMixin,
    CommitteeMemberCreateMixin,
    CommitteeMemberUpdateMixin,
)

logger = logging.getLogger(__name__)


@method_decorator(log_view_access, name="dispatch")
class ContractsListView(LoginRequiredMixin, ListView):
    model = Contract
    context_object_name = "contracts_list"
    paginate_by = 10

    template_name = "contracts/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = (
            super()
            .get_queryset()
            .filter(
                area__in=self.request.user.areas.all(),
            )
            .select_related(
                "contractor_manager",
                "hired_manager",
                "area",
                "committee",
                "accountability_autority",
                "supervision_autority",
            )
        )

        # Basic search
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(code__icontains=query)
                | Q(internal_code__icontains=query)
                | Q(bidding__icontains=query)
            )

        # Status filter
        status = self.request.GET.get("status")
        if status and status != "all":
            queryset = queryset.filter(status=status)

        # Date range filters
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        date_type = self.request.GET.get("date_type", "vigency")

        if start_date and end_date:
            if date_type == "vigency":
                queryset = queryset.filter(
                    start_of_vigency__gte=start_date,
                    end_of_vigency__lte=end_date,
                )
            elif date_type == "created":
                queryset = queryset.filter(
                    created_at__date__gte=start_date,
                    created_at__date__lte=end_date,
                )

        # Area filter
        area = self.request.GET.get("area")
        if area and area != "all":
            queryset = queryset.filter(area_id=area)

        # Committee filter
        committee = self.request.GET.get("committee")
        if committee and committee != "all":
            queryset = queryset.filter(committee_id=committee)

        # Concession type filter
        concession_type = self.request.GET.get("concession_type")
        if concession_type and concession_type != "all":
            queryset = queryset.filter(concession_type=concession_type)

        return queryset.order_by("-internal_code")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "search_query": self.request.GET.get("q", ""),
                "status": self.request.GET.get("status", "all"),
                "start_date": self.request.GET.get("start_date", ""),
                "end_date": self.request.GET.get("end_date", ""),
                "date_type": self.request.GET.get("date_type", "vigency"),
                "area": self.request.GET.get("area", "all"),
                "committee": self.request.GET.get("committee", "all"),
                "concession_type": self.request.GET.get("concession_type", "all"),
                "areas_list": self.request.user.areas.all(),
                "committees_list": Committee.objects.filter(
                    organization=self.request.user.organization
                ),
            }
        )
        return context


class ContractCreateView(CommitteeMemberCreateMixin, AdminRequiredMixin, TemplateView):
    template_name = "contracts/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = ContractCreateForm(request=self.request)

        return context

    def post(self, request, *args, **kwargs):
        form = ContractCreateForm(request.POST, request=request)
        if form.is_valid():
            with transaction.atomic():
                contract = form.save(commit=False)
                contract.organization = request.user.organization
                contract.file = request.FILES["file"]
                contract.save()

                logger.info(f"{request.user.id} - Created new contract")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT,
                    target_object_id=contract.id,
                    target_content_object=contract,
                )
            return redirect("contracts:contracts-list")

        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(log_view_access, name="dispatch")
class ContractsDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = "contracts/detail.html"
    context_object_name = "contract"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related(
                "contractor_company",
                "contractor_manager",
                "hired_company",
                "hired_manager",
                "organization",
                "inversting_account",
                "checking_account",
            )
            .prefetch_related(
                "accountabilities",
                "addendums",
                "items",
                "items__items_reviews",
                "items__items_reviews__reviewer",
                "interested_parts",
                "interested_parts__user",
                "goals",
                "goals__goals_reviews",
                "goals__goals_reviews__reviewer",
                "goals",
                "goals__steps",
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.filter(
            area__in=self.request.user.areas.all(),
        ).get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)

        executions = (
            self.object.executions.filter(deleted_at__isnull=True)
            .annotate(
                count_activities=Count(
                    "activities",
                    filter=Q(activities__deleted_at__isnull=True),
                    distinct=True,
                ),
                count_files=Count(
                    "files",
                    filter=Q(files__deleted_at__isnull=True),
                    distinct=True,
                ),
            )
            .prefetch_related("activities", "files")
            .order_by("-year", "-month")[:12]
        )
        context["executions"] = executions

        accountabilities = (
            self.object.accountabilities.filter(deleted_at__isnull=True)
            .prefetch_related(
                "revenues",
                "expenses",
            )
            .annotate(
                count_revenues=Count(
                    "revenues",
                    filter=Q(revenues__deleted_at__isnull=True)
                    & Q(deleted_at__isnull=True),
                    distinct=True,
                ),
                count_expenses=Count(
                    "expenses",
                    filter=Q(expenses__deleted_at__isnull=True)
                    & Q(deleted_at__isnull=True),
                    distinct=True,
                ),
            )[:12]
        )
        context["accountabilities"] = accountabilities

        value_requests = ContractItemNewValueRequest.objects.filter(
            raise_item__contract=self.object,
            status=ContractItemNewValueRequest.ReviewStatus.IN_REVIEW,
        ).select_related("raise_item")[:12]
        context["value_requests"] = value_requests

        context["items_totals"] = self.object.items.aggregate(
            total_month=Coalesce(Sum("month_expense"), Value(Decimal("0.00"))),
            total_year=Coalesce(Sum("anual_expense"), Value(Decimal("0.00"))),
        )

        return context

    def post(self, request, pk, *args, **kwargs):
        if not self.request.POST.get("csrfmiddlewaretoken"):
            return redirect("contracts:contracts-list")

        if not self.request.user:
            return redirect("contracts:contracts-list")

        contract = get_object_or_404(Contract, id=pk)
        form_type = self.request.POST.get("form_type", "")
        can_change_statuses = self.request.user.can_change_statuses

        with transaction.atomic():
            match form_type:
                case "items_modal":
                    item = get_object_or_404(
                        ContractItem, id=request.POST.get("item_id")
                    )

                    if can_change_statuses:
                        item.status = request.POST.get("status")
                        item.save()

                        _ = ActivityLog.objects.create(
                            user=request.user,
                            user_email=request.user.email,
                            action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM,
                            target_object_id=item.id,
                            target_content_object=item,
                        )

                    if comment := request.POST.get("comment"):
                        ContractItemReview.objects.create(
                            item=item,
                            reviewer=request.user,
                            comment=comment,
                        )
                        _ = ActivityLog.objects.create(
                            user=request.user,
                            user_email=request.user.email,
                            action=ActivityLog.ActivityLogChoices.COMMENTED_CONTRACT_ITEM,
                            target_object_id=item.id,
                            target_content_object=item,
                        )

                case "goals_modal":
                    goal = get_object_or_404(
                        ContractGoal, id=request.POST.get("goal_id")
                    )

                    if can_change_statuses:
                        goal.status = request.POST.get("status")
                        goal.save()

                        _ = ActivityLog.objects.create(
                            user=request.user,
                            user_email=request.user.email,
                            action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_GOAL,
                            target_object_id=goal.id,
                            target_content_object=goal,
                        )

                    if comment := request.POST.get("comment"):
                        ContractGoalReview.objects.create(
                            goal=goal,
                            reviewer=request.user,
                            comment=comment,
                        )
                        _ = ActivityLog.objects.create(
                            user=request.user,
                            user_email=request.user.email,
                            action=ActivityLog.ActivityLogChoices.COMMENTED_CONTRACT_GOAL,
                            target_object_id=goal.id,
                            target_content_object=goal,
                        )

                case _:
                    logger.warning(f"form_type: {form_type} is not a valid form")
                    return redirect("contracts:contracts-list")

        return redirect("contracts:contracts-detail", pk=contract.id)


@login_required
def create_contract_item_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_planning:
        return redirect("contracts:contracts-detail", pk=contract.id)

    if request.method == "POST":
        form = ContractItemForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                item: ContractItem = form.save(commit=False)
                item.contract = contract
                item.anual_expense = (
                    item.quantity * item.month_quantity * item.month_expense
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                if request.FILES:
                    item.file = request.FILES["file"]

                item.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_ITEM,
                    target_object_id=item.id,
                    target_content_object=item,
                )
            return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/items-create.html",
                {"contract": contract, "form": form},
            )
    else:
        form = ContractItemForm()
        return render(
            request,
            "contracts/items-create.html",
            {"contract": contract, "form": form},
        )


@login_required
def update_contract_item_view(request, pk, item_pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_planning:
        return redirect("contracts:contracts-detail", pk=contract.id)

    item = get_object_or_404(ContractItem, id=item_pk)

    if request.method == "POST":
        form = ContractItemForm(request.POST, instance=item)
        if form.is_valid():
            with transaction.atomic():
                contract_item: ContractItem = form.save(commit=False)
                contract_item.anual_expense = (
                    contract_item.quantity
                    * contract_item.month_quantity
                    * contract_item.month_expense
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                contract_item.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM,
                    target_object_id=item.id,
                    target_content_object=item,
                )
            return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/items-update.html",
                {"contract": contract, "item": item, "form": form},
            )
    else:
        form = ContractItemForm(instance=item)
        return render(
            request,
            "contracts/items-update.html",
            {"contract": contract, "item": item, "form": form},
        )


@login_required
def create_contract_goal_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_planning:
        return redirect("contracts:contracts-detail", pk=contract.id)

    if request.method == "POST":
        form = ContractGoalForm(request.POST)
        steps_formset = ContractExtraStepFormSet(request.POST)
        if form.is_valid() and steps_formset.is_valid():
            with transaction.atomic():
                goal = form.save(commit=False)
                goal.contract = contract
                goal.save()

                steps = steps_formset.save(commit=False)
                for step in steps:
                    step.goal = goal
                    step.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_GOAL,
                    target_object_id=goal.id,
                    target_content_object=goal,
                )

            return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/goals-create.html",
                {
                    "contract": contract,
                    "form": form,
                    "steps_formset": steps_formset,
                },
            )

    else:
        form = ContractGoalForm()
        steps_formset = ContractExtraStepFormSet()
        return render(
            request,
            "contracts/goals-create.html",
            {
                "contract": contract,
                "form": form,
                "steps_formset": steps_formset,
            },
        )


@login_required
def update_contract_goal_view(request, pk, goal_pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_planning:
        return redirect("contracts:contracts-detail", pk=contract.id)

    goal = get_object_or_404(ContractGoal, id=goal_pk)

    if request.method == "POST":
        form = ContractGoalForm(request.POST, instance=goal)
        steps_formset = ContractStepFormSet(request.POST, instance=goal)
        if form.is_valid() and steps_formset.is_valid():
            with transaction.atomic():
                goal = form.save(commit=False)
                goal.status = StatusChoices.ANALYZING
                goal.status_pendencies = None
                goal.save()

                goal.steps.all().delete()

                if steps_formset.is_valid():
                    steps_formset.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_GOAL,
                    target_object_id=goal.id,
                    target_content_object=goal,
                )
                return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/goals-update.html",
                {
                    "contract": contract,
                    "form": form,
                    "steps_formset": steps_formset,
                },
            )

    else:
        form = ContractGoalForm(instance=goal)
        steps_formset = ContractStepFormSet(instance=goal)
        return render(
            request,
            "contracts/goals-update.html",
            {
                "contract": contract,
                "form": form,
                "steps_formset": steps_formset,
            },
        )


class CompanyListView(LoginRequiredMixin, ListView):
    model = Company
    context_object_name = "companies_list"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "companies/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = (
            super().get_queryset()
            # .select_related(
            #     "contractor_manager",
            #     "hired_manager",
            # )
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(cnpj__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class CompanyCreateView(LoginRequiredMixin, TemplateView):
    template_name = "companies/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = CompanyCreateForm()

        return context

    def post(self, request, *args, **kwargs):
        form = CompanyCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                company = form.save(commit=False)
                company.organization = request.user.organization
                company.phone_number = str(
                    form.cleaned_data["phone_number"].national_number
                )
                company.save()

                logger.info(f"{request.user.id} - Created new company")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_COMPANY,
                    target_object_id=company.id,
                    target_content_object=company,
                )
                return redirect("contracts:companies-list")

        return self.render_to_response(self.get_context_data(form=form))


class CompanyUpdateView(LoginRequiredMixin, UpdateView):
    model = Company
    template_name = "companies/update.html"
    form_class = CompanyUpdateForm
    login_url = "/auth/login"
    success_url = reverse_lazy("contracts:companies-list")

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().select_related("organization")

    def form_valid(self, form):
        with transaction.atomic():
            company = form.save(commit=False)
            company.phone_number = str(
                form.cleaned_data["phone_number"].national_number
            )
            company.save()

            logger.info(f"{self.request.user.id} - Updated company")
            _ = ActivityLog.objects.create(
                user=self.request.user,
                user_email=self.request.user.email,
                action=ActivityLog.ActivityLogChoices.UPDATED_COMPANY,
                target_object_id=company.id,
                target_content_object=company,
            )
            return redirect("contracts:companies-list")


class CompanyDetailView(LoginRequiredMixin, DetailView):
    model = Company
    template_name = "companies/detail.html"
    context_object_name = "company"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().select_related("organization")


class ContractItemDetailView(LoginRequiredMixin, DetailView):
    model = ContractItem

    template_name = "contracts/items-detail.html"
    context_object_name = "item"

    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related(
                "organization",
            )
            .prefetch_related(
                "items_reviews",
                "items_reviews__reviewer",
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


@login_required
def create_contract_execution_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_execution:
        return redirect("contracts:contracts-detail", pk=contract.id)

    if request.method == "POST":
        form = ContractExecutionCreateForm(request.POST)
        if form.is_valid():
            execution_exists = ContractExecution.objects.filter(
                contract=contract,
                month=form.cleaned_data["month"],
                year=form.cleaned_data["year"],
            ).exists()
            if execution_exists:
                return render(
                    request,
                    "contracts/execution/create.html",
                    {
                        "contract": contract,
                        "form": form,
                        "execution_exists": True,
                    },
                )

            with transaction.atomic():
                execution = ContractExecution.objects.create(
                    contract=contract,
                    month=form.cleaned_data["month"],
                    year=form.cleaned_data["year"],
                )
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_EXECUTION,
                    target_object_id=execution.id,
                    target_content_object=execution,
                )
            return redirect("contracts:executions-detail", pk=execution.id)
    else:
        form = ContractExecutionCreateForm()
        return render(
            request,
            "contracts/execution/create.html",
            {"contract": contract, "form": form},
        )


class ContractExecutionDetailView(LoginRequiredMixin, DetailView):
    model = ContractExecution

    template_name = "contracts/execution/detail.html"
    context_object_name = "execution"

    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "activities",
                "activities__step",
                "files",
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


@login_required
def create_execution_activity_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    execution = get_object_or_404(ContractExecution, id=pk)
    if request.method == "POST":
        form = ContractExecutionActivityForm(request.POST, execution=execution)
        if form.is_valid():
            with transaction.atomic():
                activity = form.save(commit=False)
                activity.execution = execution
                activity.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_EXECUTION_ACTIVITY,
                    target_object_id=activity.id,
                    target_content_object=activity,
                )
                return redirect("contracts:executions-detail", pk=execution.id)
        else:
            return render(
                request,
                "contracts/execution/activity-create.html",
                {"execution": execution, "form": form},
            )
    else:
        form = ContractExecutionActivityForm(execution=execution)
        return render(
            request,
            "contracts/execution/activity-create.html",
            {"execution": execution, "form": form},
        )


class ContractExecutionActivityUpdateView(
    CommitteeMemberUpdateMixin, LoginRequiredMixin, UpdateView
):
    model = ContractExecutionActivity
    form_class = ContractExecutionActivityForm
    template_name = "contracts/execution/activity-detail.html"
    context_object_name = "activity"

    login_url = "/auth/login"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["execution"] = kwargs["instance"].execution
        return kwargs

    def form_valid(self, form):
        _ = ActivityLog.objects.create(
            user=self.request.user,
            user_email=self.request.user.email,
            action=ActivityLog.ActivityLogChoices.CREATED_EXECUTION_ACTIVITY,
            target_object_id=form.instance.id,
            target_content_object=form.instance,
        )

        return super().form_valid(form)

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related(
                "activity",
                "activity__execution",
                "activity__execution__contract",
            )
        )

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:executions-detail",
            kwargs={"pk": self.object.execution.id},
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])


@login_required
def create_execution_file_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    execution = get_object_or_404(ContractExecution, id=pk)
    if request.method == "POST":
        file = request.FILES.get("file")
        if file:
            with transaction.atomic():
                execution_file = ContractExecutionFile.objects.create(
                    execution=execution,
                    name=request.POST.get("name"),
                    file=file,
                )

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_EXECUTION_FILE,
                    target_object_id=execution_file.id,
                    target_content_object=execution_file,
                )
                return redirect("contracts:executions-detail", pk=execution.id)
        else:
            form = ContractExecutionFileForm(request.POST)
            return render(
                request,
                "contracts/execution/file-create.html",
                {"execution": execution, "form": form},
            )
    else:
        form = ContractExecutionFileForm()
        return render(
            request,
            "contracts/execution/file-create.html",
            {"execution": execution, "form": form},
        )


@method_decorator(log_view_access, name="dispatch")
class ContractWorkPlanView(LoginRequiredMixin, DetailView):
    model = Contract

    template_name = "contracts/workplan.html"
    context_object_name = "contract"

    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related(
                "area",
                "area__city_hall",
                "hired_company",
                "hired_company",
            )
            .prefetch_related(
                "interested_parts",
                "interested_parts__user",
                "goals",
                "items",
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def group_nature_expenses(self) -> dict:
        groupped_expenses = {
            "Bens Permanentes": {"total": Decimal("0.00")},
            "Combustível": {"total": Decimal("0.00")},
            "Locações Diversas": {"total": Decimal("0.00")},
            "Outras despesas": {"total": Decimal("0.00")},
            "Outros Materiais de Consumo": {"total": Decimal("0.00")},
            "Outros Serviços de Terceiros": {"total": Decimal("0.00")},
            "Recursos Humanos (5)": {"total": Decimal("0.00")},
            "Recursos Humanos (6)": {"total": Decimal("0.00")},
            "Utilidades Públicas (7)": {"total": Decimal("0.00")},
        }

        for item in self.object.items.all():
            if item.nature in NatureCategories.PERMANENT_GOODS:
                group = "Bens Permanentes"
            elif item.nature in NatureCategories.FUEL:
                group = "Combustível"
            elif item.nature in NatureCategories.MISCELLANEOUS:
                group = "Locações Diversas"
            elif item.nature in NatureCategories.OTHER_EXPENSES:
                group = "Outras despesas"
            elif item.nature in NatureCategories.OTHER_CONSUMABLES:
                group = "Outros Materiais de Consumo"
            elif item.nature in NatureCategories.OTHER_THIRD_PARTY:
                group = "Outros Serviços de Terceiros"
            elif item.nature in NatureCategories.HUMAN_RESOURCES:
                group = "Recursos Humanos (5)"
            elif item.nature in NatureCategories.OTHER_HUMAN_RESOURCES:
                group = "Recursos Humanos (6)"
            elif item.nature in NatureCategories.PUBLIC_UTILITIES:
                group = "Utilidades Públicas (7)"
            else:
                continue

            if item.nature_label in groupped_expenses[group]:
                groupped_expenses[group][item.nature_label] += item.anual_expense
                groupped_expenses[group]["total"] += item.anual_expense
            else:
                groupped_expenses[group][item.nature_label] = item.anual_expense
                groupped_expenses[group]["total"] += item.anual_expense

        return groupped_expenses

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["groupped_natures"] = self.group_nature_expenses()
        context["transfers"] = get_monthly_transfers(self.object)
        return context


def get_monthly_transfers(contract):
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

    transfers = (
        contract.month_transfers.values("month", "year", "source")
        .annotate(total_value=Sum("value"))
        .order_by("year", "month")
    )

    monthly_data = {}
    for transfer in transfers:
        month_year = f"{month_abbr[transfer['month']]}/{transfer['year']}"
        if month_year not in monthly_data:
            monthly_data[month_year] = {
                "month": month_year,
                "city_hall": Decimal(0),
                "counterpart": Decimal(0),
                "total": Decimal(0),
            }

        if transfer["source"] == ContractMonthTransfer.TransferSource.CITY_HALL:
            monthly_data[month_year]["city_hall"] = transfer["total_value"]
        elif transfer["source"] == ContractMonthTransfer.TransferSource.COUNTERPART:
            monthly_data[month_year]["counterpart"] = transfer["total_value"]

        monthly_data[month_year]["total"] = (
            monthly_data[month_year]["city_hall"]
            + monthly_data[month_year]["counterpart"]
        )

    return list(monthly_data.values())


@method_decorator(log_view_access, name="dispatch")
class ContractTimelineView(LoginRequiredMixin, DetailView):
    model = Contract

    template_name = "contracts/timeline.html"
    context_object_name = "contract"

    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "month_transfers",
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["transfers"] = get_monthly_transfers(self.object)
        return context


def _get_months_list(contract: Contract):
    locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

    months = []
    current_date = contract.start_of_vigency

    while current_date <= contract.end_of_vigency:
        months.append(current_date.strftime("%b/%Y"))
        current_date += relativedelta(months=1)
    return months


def _groupped_list_values(request):
    city_hall_values = []
    counterpart_values = []

    for key, value in request.POST.items():
        if key.startswith("city_hall_"):
            city_hall_values.append(Decimal(str(value)))
        elif key.startswith("counterpart_"):
            counterpart_values.append(Decimal(str(value)))

    city_hall_values = [
        value
        for _, value in sorted(
            (
                (int(key.split("_")[2]), Decimal(str(value)))
                for key, value in request.POST.items()
                if key.startswith("city_hall_")
            ),
            key=lambda x: x[0],
        )
    ]

    counterpart_values = [
        value
        for _, value in sorted(
            (
                (int(key.split("_")[1]), Decimal(str(value)))
                for key, value in request.POST.items()
                if key.startswith("counterpart_")
            ),
            key=lambda x: x[0],
        )
    ]

    return city_hall_values, counterpart_values


@log_database_operation("update_timeline")
@log_view_access
@login_required
def contract_timeline_update_view(request, pk):
    contract = get_object_or_404(Contract, pk=pk)
    if not contract.is_on_planning:
        return redirect("contracts:contracts-detail", pk=contract.id)

    months = _get_months_list(contract)
    if request.method == "POST":
        city_hall_values, counterpart_values = _groupped_list_values(request)
        wrong_values = False

        if sum(city_hall_values) != contract.municipal_value:
            wrong_values = True
        if sum(counterpart_values) != contract.counterpart_value:
            wrong_values = True
        if sum([*city_hall_values, *counterpart_values]) != contract.total_value:
            wrong_values = True

        if wrong_values:
            context = {
                "contract": contract,
                "months": months,
                "wrong_values": True,
            }
            return render(request, "contracts/timeline-update.html", context)
        else:
            with transaction.atomic():
                month_transfers = []
                months_map = {
                    "Jan": 1,
                    "Fev": 2,
                    "Mar": 3,
                    "Abr": 4,
                    "Mai": 5,
                    "Jun": 6,
                    "Jul": 7,
                    "Ago": 8,
                    "Set": 9,
                    "Out": 10,
                    "Nov": 11,
                    "Dez": 12,
                }

                for idx, month in enumerate(months):
                    m, y = month.split("/")
                    month_transfers.append(
                        ContractMonthTransfer(
                            contract=contract,
                            month=months_map.get(m),
                            year=int(y),
                            source=ContractMonthTransfer.TransferSource.CITY_HALL,
                            value=city_hall_values[idx],
                        )
                    )
                    month_transfers.append(
                        ContractMonthTransfer(
                            contract=contract,
                            month=months_map.get(m),
                            year=int(y),
                            source=ContractMonthTransfer.TransferSource.COUNTERPART,
                            value=counterpart_values[idx],
                        )
                    )

                contract.month_transfers.all().delete()
                ContractMonthTransfer.objects.bulk_create(month_transfers)

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_MONTH_TRASNFER,
                    target_object_id=contract.id,
                    target_content_object=contract,
                )

            return redirect("contracts:contract-timeline", pk=contract.id)
    else:
        context = {
            "contract": contract,
            "months": months,
        }
        return render(request, "contracts/timeline-update.html", context)


@log_database_operation("change_contract_status")
@log_view_access
@login_required
def contract_status_change_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not request.user.has_admin_access:
        return redirect("contracts:contracts-detail", pk=contract.id)

    if request.method == "POST":
        form = ContractStatusUpdateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                contract.status = form.cleaned_data["status"]
                contract.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_STATUS,
                    target_object_id=contract.id,
                    target_content_object=contract,
                )
                return redirect("contracts:contracts-detail", pk=contract.id)
    else:
        form = ContractStatusUpdateForm()
        return render(
            request,
            "contracts/status-update.html",
            {"form": form, "contract": contract},
        )


@log_view_access
@login_required
def item_new_value_request_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        form = ContractItemValueRequestForm(request.POST, contract=contract)
        if form.is_valid():
            with transaction.atomic():
                value_request = form.save(commit=False)
                value_request.requested_by = request.user
                value_request.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.REQUEST_NEW_VALUE_ITEM,
                    target_object_id=contract.id,
                    target_content_object=contract,
                )
                return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/items/request-raise.html",
                {
                    "form": form,
                    "contract": contract,
                },
            )
    else:
        form = ContractItemValueRequestForm(contract=contract)
        return render(
            request,
            "contracts/items/request-raise.html",
            {
                "form": form,
                "contract": contract,
            },
        )


class ItemValueRequestReviewView(LoginRequiredMixin, UpdateView):
    model = ContractItemNewValueRequest
    form_class = ItemValueReviewForm

    template_name = "contracts/items/review-request.html"
    context_object_name = "object"

    login_url = "/auth/login"

    def form_valid(self, form):
        with transaction.atomic():
            instance = form.save(commit=False)

            instance.raise_item.month_expense += instance.month_raise
            instance.raise_item.anual_expense += instance.anual_raise
            instance.raise_item.save()

            instance.downgrade_item.month_expense -= instance.month_raise
            instance.downgrade_item.anual_expense -= instance.anual_raise
            instance.downgrade_item.save()

            _ = ActivityLog.objects.create(
                user=self.request.user,
                user_email=self.request.user.email,
                action=ActivityLog.ActivityLogChoices.ANALISED_NEW_VALUE_ITEM,
                target_object_id=instance.raise_item.contract.id,
                target_content_object=instance.raise_item.contract,
            )

        return super().form_valid(form)

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related(
                "requested_by",
                "downgrade_item",
                "raise_item",
                "raise_item__contract",
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail",
            kwargs={"pk": self.object.raise_item.contract.id},
        )


@login_required
def send_execution_to_analisys_view(request, pk):
    execution = get_object_or_404(ContractExecution, id=pk)
    if execution.is_finished:
        return redirect("home")

    with transaction.atomic():
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.EXECUTION_TO_ANALISYS,
            target_object_id=execution.id,
            target_content_object=execution,
        )
        execution.status = ContractExecution.ReviewStatus.SENT
        execution.save()
        return redirect("contracts:executions-detail", pk=execution.id)


def send_accountability_review_analisys(request, pk):
    execution = get_object_or_404(ContractExecution, id=pk)
    if not execution.is_sent:
        return redirect("contracts:executions-detail", pk=execution.id)

    if not request.user or not request.user.can_change_statuses:
        return redirect("contracts:executions-detail", pk=execution.id)

    with transaction.atomic():
        review_status = request.POST.get("review_status")

        if review_status == ContractExecution.ReviewStatus.CORRECTING:
            action = ActivityLog.ActivityLogChoices.EXECUTION_SENT_TO_CORRECT
        elif review_status == ContractExecution.ReviewStatus.FINISHED:
            action = ActivityLog.ActivityLogChoices.EXECUTION_MARKED_AS_FINISHED
        else:
            raise ValueError(f"{review_status} - Is an unnknow status review")

        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=action,
            target_object_id=execution.id,
            target_content_object=execution,
        )
        execution.status = review_status
        execution.save()
        return redirect("contracts:executions-detail", pk=execution.id)


@login_required
def create_contract_interested_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = ContractInterestedForm(request.POST, contract=contract)
        if form.is_valid():
            with transaction.atomic():
                interested: ContractInterestedPart = form.save(commit=False)
                interested.contract = contract
                interested.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_INTERESTED,
                    target_object_id=interested.id,
                    target_content_object=interested,
                )
            return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/interesteds-create.html",
                {"contract": contract, "form": form},
            )
    else:
        form = ContractInterestedForm(contract=contract)
        return render(
            request,
            "contracts/interesteds-create.html",
            {"contract": contract, "form": form},
        )


@login_required
def update_contract_interested_view(request, pk, item_pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    interested = get_object_or_404(ContractInterestedPart, id=item_pk)

    if request.method == "POST":
        form = ContractInterestedForm(
            request.POST, instance=interested, contract=contract
        )
        if form.is_valid():
            with transaction.atomic():
                interested: ContractInterestedPart = form.save()
                interested.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_INTERESTED,
                    target_object_id=interested.id,
                    target_content_object=interested,
                )
            return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/interesteds-create.html",
                {"contract": contract, "interested": interested, "form": form},
            )
    else:
        form = ContractInterestedForm(instance=interested, contract=contract)
        return render(
            request,
            "contracts/interesteds-create.html",
            {"contract": contract, "interested": interested, "form": form},
        )


@login_required
def interested_delete_view(request, pk):
    interested = get_object_or_404(
        ContractInterestedPart.objects.select_related("contract"), id=pk
    )

    contract_id = interested.contract.id
    with transaction.atomic():
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_CONTRACT_INTERESTED,
            target_object_id=interested.id,
            target_content_object=interested,
        )
        interested.delete()
        return redirect("contracts:contracts-detail", pk=contract_id)


@login_required
def contract_item_purchases_list_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if not contract.items.count:
        return redirect("contracts:contracts-detail", pk=contract.id)

    items = (
        ContractItem.objects.filter(contract=contract)
        .prefetch_related(
            Prefetch(
                "purchase_documents",
                queryset=ContractItemPurchaseProcessDocument.objects.filter(
                    deleted_at__isnull=True,
                ),
            ),
        )
        .annotate(
            files_count=Count(
                "purchase_documents",
                filter=Q(purchase_documents__deleted_at__isnull=True),
                distinct=True,
            ),
        )
    )

    return render(
        request,
        "contracts/items/purchases.html",
        {"contract": contract, "items": items},
    )


@login_required
def contract_item_purchases_update_view(request, pk):
    item = get_object_or_404(ContractItem, id=pk)

    if request.method == "POST":
        form = ContractItemPurchaseProcessForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect("contracts:item-purchases", pk=item.contract.id)
        else:
            return render(
                request,
                "contracts/items/purchases-update.html",
                {"item": item, "form": form},
            )

    else:
        form = ContractItemPurchaseProcessForm(instance=item)
        return render(
            request,
            "contracts/items/purchases-update.html",
            {"item": item, "form": form},
        )


@login_required
def contract_item_supplementations_list_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if not contract.items.count:
        return redirect("contracts:contracts-detail", pk=contract.id)

    supplementations = ContractItemSupplement.objects.filter(item__contract=contract)
    return render(
        request,
        "contracts/items/supplementations.html",
        {"contract": contract, "supplementations": supplementations},
    )


@login_required
def contract_item_supplementations_create_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if contract.is_finished:
        return redirect("contracts:item-supplementations", pk=contract.id)

    if request.method == "POST":
        form = ContractItemSupplementForm(request.POST, contract=contract)
        if form.is_valid():
            with transaction.atomic():
                supplement = form.save(commit=False)
                supplement.supplement_value = form.cleaned_data["supplement_value"]
                supplement.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_ITEM_SUPPLEMENT,
                    target_object_id=supplement.item.id,
                    target_content_object=supplement.item,
                )
            return redirect("contracts:item-supplementations", pk=contract.id)
        else:
            return render(
                request,
                "contracts/items/supplementations-create.html",
                {"contract": contract, "form": form},
            )
    else:
        form = ContractItemSupplementForm(contract=contract)
        return render(
            request,
            "contracts/items/supplementations-create.html",
            {"contract": contract, "form": form},
        )


@login_required
def contract_item_supplementations_update_view(request, pk):
    supplement = get_object_or_404(ContractItemSupplement, id=pk)
    if request.method == "POST":
        form = ContractItemSupplementUpdateForm(request.POST, instance=supplement)
        if form.is_valid():
            with transaction.atomic():
                supplement = form.save(commit=False)
                supplement.supplement_value = form.cleaned_data["supplement_value"]
                supplement.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM_SUPPLEMENT,
                    target_object_id=supplement.item.id,
                    target_content_object=supplement.item,
                )
                return redirect(
                    "contracts:item-supplementations",
                    pk=supplement.item.contract.id,
                )
        else:
            return render(
                request,
                "contracts/items/supplementations-update.html",
                {"supplement": supplement, "form": form},
            )
    else:
        form = ContractItemSupplementUpdateForm(instance=supplement)
        return render(
            request,
            "contracts/items/supplementations-update.html",
            {"supplement": supplement, "form": form},
        )


@require_POST
@login_required
def contract_item_purchase_file_upload_view(request, pk):
    """Upload files for an item purchase."""

    item = get_object_or_404(ContractItem, id=pk)
    files = request.FILES.getlist("files")
    with transaction.atomic():
        for file in files:
            ContractItemPurchaseProcessDocument.objects.create(
                item=item,
                file=file,
                name=file.name,
            )
            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.UPLOADED_CONTRACT_ITEM_PURCHASE_FILE,
                target_object_id=item.id,
                target_content_object=item,
            )

    return redirect("contracts:item-purchases", pk=item.contract.id)


@require_POST
@login_required
def contract_item_purchase_file_delete_view(request, pk):
    file = get_object_or_404(ContractItemPurchaseProcessDocument, id=pk)

    with transaction.atomic():
        file.delete()
        _ = ActivityLog.objects.create(
            user=request.user,
            user_email=request.user.email,
            action=ActivityLog.ActivityLogChoices.DELETED_CONTRACT_ITEM_PURCHASE_FILE,
            target_object_id=file.id,
            target_content_object=file,
        )

    return redirect("contracts:item-purchases", pk=file.item.contract.id)
