import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from activity.models import ActivityLog
from contracts.forms import (
    CompanyCreateForm,
    ContractCreateForm,
    ContractExtraStepFormSet,
    ContractGoalForm,
    ContractItemForm,
    ContractStepFormSet,
    ContractExecutionCreateForm,
    ContractExecutionActivityForm,
    ContractExecutionFileForm,
)
from contracts.models import (
    Company,
    Contract,
    ContractExecutionActivity,
    ContractGoal,
    ContractExecution,
    ContractGoalReview,
    ContractItem,
    ContractItemReview,
    ContractExecutionFile
)
from utils.choices import StatusChoices
from utils.mixins import AdminRequiredMixin

logger = logging.getLogger(__name__)


class ContractsListView(LoginRequiredMixin, ListView):
    model = Contract
    context_object_name = "contracts_list"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "contracts/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = (
            super()
            .get_queryset()
            .select_related(
                "contractor_manager",
                "hired_manager",
            )
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class ContractCreateView(AdminRequiredMixin, TemplateView):
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
                "goals",
                "goals__goals_reviews",
                "goals__goals_reviews__reviewer",
                "goals",
                "goals__steps",
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
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


def create_contract_item_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        form = ContractItemForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                item = form.save(commit=False)
                item.contract = contract
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
            request, "contracts/items-create.html", {"contract": contract, "form": form}
        )


def update_contract_item_view(request, pk, item_pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    item = get_object_or_404(ContractItem, id=item_pk)

    if request.method == "POST":
        form = ContractItemForm(request.POST, instance=item)
        if form.is_valid():
            with transaction.atomic():
                form.save()
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


def create_contract_goal_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
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


def update_contract_goal_view(request, pk, goal_pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
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
                source = form.save(commit=False)
                source.organization = request.user.organization
                source.save()

                logger.info(f"{request.user.id} - Created new company")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_COMPANY,
                    target_object_id=source.id,
                    target_content_object=source,
                )
                return redirect("contracts:companies-list")

        return self.render_to_response(self.get_context_data(form=form))


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


def create_contract_execution_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
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
                    {"contract": contract, "form": form, "execution_exists": True},
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
            return redirect(
                "contracts:executions-detail", pk=execution.id
            )
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
        return super().get_queryset().prefetch_related(
            "activities",
            "activities__step",
            "files",
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


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
                return redirect(
                    "contracts:executions-detail", pk=execution.id
                )
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


class ContractExecutionActivityUpdateView(LoginRequiredMixin, UpdateView):
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
        ActivityLog.objects.create(
            user=self.request.user,
            user_email=self.request.user.email,
            action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT,
            target_object_id=form.instance.id,
            target_content_object=form.instance,
        )

        return super().form_valid(form)

    def get_queryset(self) -> QuerySet[Any]:
        return super().get_queryset().select_related(
            "activity",
            "activity__execution",
            "activity__execution__contract",
        )
    
    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:executions-detail", kwargs={"pk": self.object.execution.id}
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])
    

def create_execution_file_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    execution = get_object_or_404(ContractExecution, id=pk)    
    if request.method == "POST":
        form = ContractExecutionFileForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                execution_file = ContractExecutionFile.objects.create(
                    execution=execution,
                    name=form.cleaned_data["name"],
                    file=request.FILES["file"],
                )

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_EXECUTION_FILE,
                    target_object_id=execution_file.id,
                    target_content_object=execution_file,
                )
                return redirect(
                    "contracts:executions-detail", pk=execution.id
                )
        else:
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

