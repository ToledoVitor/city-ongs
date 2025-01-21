import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, TemplateView

from activity.models import ActivityLog
from contracts.forms import CompanyCreateForm, ContractCreateForm, ContractStepFormSet
from contracts.models import Company, Contract, ContractGoal, ContractItem
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
                contract = form.save()

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
            )
            .prefetch_related(
                "addendums",
                "items",
                "goals",
                "goals__sub_goals",
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

        if not (self.request.user and self.request.user.can_change_statuses):
            return redirect("contracts:contracts-list")

        contract = get_object_or_404(Contract, id=pk)
        form_type = self.request.POST.get("form_type", "")

        match form_type:
            case "items_modal":
                item = get_object_or_404(ContractItem, id=request.POST.get("itemId"))
                item.status = request.POST.get("status")
                item.status_pendencies = request.POST.get("pendencies")
                item.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM,
                    target_object_id=item.id,
                    target_content_object=item,
                )

            case "goals_modal":
                goal = get_object_or_404(ContractGoal, id=request.POST.get("goalId"))
                goal.status = request.POST.get("status")
                goal.status_pendencies = request.POST.get("pendencies")
                goal.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_GOAL,
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
        with transaction.atomic():
            name = request.POST.get("name")
            objective = request.POST.get("objective")
            methodology = request.POST.get("methodology")
            month_quantity = request.POST.get("month_quantity")
            month_expense = request.POST.get("month_expense")
            unit_type = request.POST.get("unit_type")
            nature = request.POST.get("nature")
            is_additive = request.POST.get("is_additive", "") == "True"

            item = ContractItem.objects.create(
                contract=contract,
                name=name,
                objective=objective,
                methodology=methodology,
                month_quantity=month_quantity,
                month_expense=month_expense,
                unit_type=unit_type,
                nature=nature,
                is_additive=is_additive,
                status=StatusChoices.ANALYZING,
            )
            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_ITEM,
                target_object_id=item.id,
                target_content_object=item,
            )

        return redirect("contracts:contracts-detail", pk=contract.id)

    return render(request, "contracts/items-create.html", {"contract": contract})


def update_contract_item_view(request, pk, item_pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    item = get_object_or_404(ContractItem, id=item_pk)

    if request.method == "POST":
        with transaction.atomic():
            item.name = request.POST.get("name")
            item.description = request.POST.get("description")
            item.total_expense = request.POST.get("total_expense")
            item.is_additive = request.POST.get("is_additive", "") == "True"
            item.status = StatusChoices.ANALYZING
            item.status_pendencies = None
            item.save()

            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM,
                target_object_id=item.id,
                target_content_object=item,
            )

        return redirect("contracts:contracts-detail", pk=contract.id)

    return render(
        request, "contracts/items-update.html", {"contract": contract, "item": item}
    )


def create_contract_goal_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        steps_formset = ContractStepFormSet(request.POST)
        if steps_formset.is_valid():
            with transaction.atomic():
                name = request.POST.get("name")
                description = request.POST.get("description")

                goal = ContractGoal.objects.create(
                    contract=contract,
                    name=name,
                    description=description,
                    status=StatusChoices.ANALYZING,
                )
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
        steps_formset = ContractStepFormSet()
        return render(
            request,
            "contracts/goals-create.html",
            {"contract": contract, "steps_formset": steps_formset},
        )


def update_contract_goal_view(request, pk, goal_pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    goal = get_object_or_404(ContractGoal, id=goal_pk)

    if request.method == "POST":
        with transaction.atomic():
            goal.name = request.POST.get("name")
            goal.description = request.POST.get("description")
            goal.status = StatusChoices.ANALYZING
            goal.status_pendencies = None
            goal.save()

            goal.sub_goals.all().delete()

            steps_formset = ContractStepFormSet(request.POST, instance=goal)
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
        steps_formset = ContractStepFormSet()
        return render(
            request,
            "contracts/goals-update.html",
            {"contract": contract, "goal": goal, "steps_formset": steps_formset},
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
                source = form.save()

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
