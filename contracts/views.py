import locale
import logging
from calendar import month_abbr
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Prefetch, Q, Sum
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from accounts.models import Committee
from activity.models import ActivityLog
from contracts.choices import NatureCategories
from contracts.forms import (
    AssetForm,
    CertificateReferenceForm,
    CompanyCreateForm,
    CompanyUpdateForm,
    ContractAddendumForm,
    ContractCreateUpdateForm,
    ContractDocumentForm,
    ContractDocumentUpdateForm,
    ContractExecutionActivityForm,
    ContractExecutionCreateForm,
    ContractExecutionFileForm,
    ContractExtraStepFormSet,
    ContractGoalForm,
    ContractInterestedForm,
    ContractItemForm,
    ContractItemPurchaseProcessForm,
    ContractItemSupplementForm,
    ContractItemSupplementReviewForm,
    ContractItemSupplementUpdateForm,
    ContractItemValueRequestForm,
    ContractStatusUpdateForm,
    ContractStepFormSet,
    ItemValueReviewForm,
    SupplierContractForm,
)
from contracts.models import (
    Asset,
    CertificateReference,
    Company,
    Contract,
    ContractAddendum,
    ContractDocument,
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
    SupplierContract,
)
from contracts.sections import (
    DEFAULT_SECTION_SLUG,
    Section,
    get_section,
    nav_groups,
)
from utils.choices import StatusChoices
from utils.logging import log_database_operation, log_view_access
from utils.mixins import (
    AdminRequiredMixin,
    CommitteeMemberCreateMixin,
    CommitteeMemberUpdateMixin,
    UserAccessQuerysetMixin,
    UserAccessViewMixin,
)
from utils.views import ComboboxSearchView

logger = logging.getLogger(__name__)


def redirect_to_section(contract_id, section_slug: str | None = None):
    """Redirect to a contract detail section.

    ``contracts-detail`` stays the canonical URL for the default section, so the
    many existing ``redirect("contracts:contracts-detail", ...)`` call sites keep
    working untouched.  Pass a slug to land the user on the section they were
    actually working in.
    """
    if section_slug and section_slug != DEFAULT_SECTION_SLUG:
        return redirect(
            "contracts:contracts-detail-section",
            pk=contract_id,
            section=section_slug,
        )
    return redirect("contracts:contracts-detail", pk=contract_id)


def _accessible_contracts(user):
    """Return tenant-local contracts the user is allowed to access."""
    return UserAccessQuerysetMixin.filter_by_user_access(
        Contract.objects.all(), user
    ).distinct()


def _accessible_contract_or_404(request, pk):
    return get_object_or_404(_accessible_contracts(request.user), id=pk)


def _accessible_supplement_or_404(request, pk, pending_only=False, for_update=False):
    supplements = ContractItemSupplement.objects.select_related("item__contract")
    supplements = supplements.filter(
        item__contract__in=_accessible_contracts(request.user)
    )
    if pending_only:
        supplements = supplements.filter(
            status=ContractItemSupplement.ReviewStatus.IN_REVIEW
        )
    if for_update:
        supplements = supplements.select_for_update()
    return get_object_or_404(supplements, id=pk)


@method_decorator(log_view_access, name="dispatch")
class ContractsListView(UserAccessViewMixin, LoginRequiredMixin, ListView):
    model = Contract
    context_object_name = "contracts_list"
    paginate_by = 10
    apply_distinct = True

    template_name = "contracts/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = Contract.objects.select_related(
            "contractor_manager",
            "hired_manager",
            "area",
            "committee",
            "accountability_autority",
            "supervision_autority",
        )
        queryset = self.get_user_filtered_queryset(queryset)

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
            context["form"] = ContractCreateUpdateForm(request=self.request)

        return context

    def post(self, request, *args, **kwargs):
        form = ContractCreateUpdateForm(request.POST, request=request)
        if form.is_valid():
            with transaction.atomic():
                contract = form.save(commit=False)
                contract.original_value = contract.total_value
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


class ContractUpdateView(CommitteeMemberUpdateMixin, AdminRequiredMixin, TemplateView):
    template_name = "contracts/edit.html"
    login_url = "/auth/login"

    def get_contract(self):
        return get_object_or_404(Contract, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        contract = self.get_contract()

        if not context.get("form", None):
            context["form"] = ContractCreateUpdateForm(
                instance=contract, request=self.request
            )

        context["contract"] = contract
        return context

    def post(self, request, *args, **kwargs):
        contract = self.get_contract()
        form = ContractCreateUpdateForm(
            request.POST, request.FILES, instance=contract, request=request
        )

        if form.is_valid():
            with transaction.atomic():
                updated_contract = form.save(commit=False)
                if "file" in request.FILES:
                    updated_contract.file = request.FILES["file"]
                updated_contract.save()

                logger.info("%s - Updated contract %s", request.user.id, contract.id)
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_STATUS,
                    target_object_id=contract.id,
                    target_content_object=contract,
                )

            return redirect("contracts:contracts-detail", pk=contract.id)

        return self.render_to_response(self.get_context_data(form=form))


@method_decorator(log_view_access, name="dispatch")
class ContractsDetailView(UserAccessViewMixin, LoginRequiredMixin, DetailView):
    """Contract detail page, rendered one section at a time.

    Every section has its own URL so it can be linked, bookmarked and reached
    with the browser's back button.  Each section declares the queryset work it
    needs in contracts.sections, so a request pays only for the section being
    viewed instead of building all of them.

    A request carrying the ``X-Contract-Section`` header gets just the section
    body, which lets a client swap sections without a page load.  Plain requests
    render the full page, so the nav works as ordinary links too.
    """

    model = Contract
    template_name = "contracts/detail.html"
    context_object_name = "contract"
    login_url = "/auth/login"

    #: Set by clients fetching a single section.
    fragment_header = "HTTP_X_CONTRACT_SECTION"

    #: Which section a modal POST should land on, so submitting from a section
    #: does not bounce the user back to Detalhes.
    post_sections = {
        "items_modal": "items",
        "goals_modal": "goals",
    }

    @cached_property
    def section(self) -> Section:
        section = get_section(self.kwargs.get("section"))
        if section is None:
            raise Http404(
                f"Seção de contrato inexistente: {self.kwargs.get('section')!r}"
            )
        return section

    @property
    def is_fragment(self) -> bool:
        return self.fragment_header in self.request.META

    def get_template_names(self) -> list[str]:
        # A fragment request wants the section body only — no base.html, no nav.
        return [self.section.template] if self.is_fragment else [self.template_name]

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        if self.section.select_related:
            queryset = queryset.select_related(*self.section.select_related)
        if self.section.prefetch_related:
            queryset = queryset.prefetch_related(*self.section.prefetch_related)
        return queryset

    def get_object(self, queryset=None) -> Contract:
        return get_object_or_404(
            self.get_user_filtered_queryset(self.get_queryset()),
            id=self.kwargs["pk"],
        )

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context["section"] = self.section
        context["nav_groups"] = nav_groups()
        context.update(self.section.get_context(self.object))
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

        return redirect_to_section(contract.id, self.post_sections.get(form_type))


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
            # `execution` is excluded from the form (assigned from the URL,
            # not user input), so Django's automatic validate_unique() skips
            # unique_activity_per_execution_step outright (see the analogous
            # comment on accountability.views.create_budget_commitment_view) -
            # check by hand instead of letting a genuine duplicate raise a
            # raw IntegrityError.
            activity_exists = ContractExecutionActivity.objects.filter(
                execution=execution,
                step=form.cleaned_data["step"],
                name=form.cleaned_data["name"],
            ).exists()
            if activity_exists:
                return render(
                    request,
                    "contracts/execution/activity-create.html",
                    {
                        "execution": execution,
                        "form": form,
                        "activity_exists": True,
                    },
                )

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
        # Same excluded-field gap as create_execution_activity_view:
        # `execution` isn't a form field, so Django's automatic
        # validate_unique() skips unique_activity_per_execution_step
        # outright - check by hand.
        exists = (
            ContractExecutionActivity.objects.filter(
                execution=self.object.execution,
                step=form.cleaned_data["step"],
                name=form.cleaned_data["name"],
            )
            .exclude(pk=self.object.pk)
            .exists()
        )
        if exists:
            return self.render_to_response(
                self.get_context_data(form=form, activity_exists=True)
            )

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
        context["interested_parts"] = (
            self.object.interested_parts.filter(deleted_at__isnull=True)
            .select_related("user")
            .order_by("-user__first_name")[:12]
        )
        return context


def get_monthly_transfers(contract):
    # setlocale muda estado global do processo, não da thread. O container roda
    # 4 threads gunicorn (ver docs/DEPLOY.md), então isto só é seguro porque a
    # imagem já define LC_ALL=pt_BR.UTF-8 e toda thread grava o mesmo valor.
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
    # Estado global do processo — ver a nota em get_monthly_transfers.
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
        form = ContractStatusUpdateForm(request.POST, instance=contract)
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
        form = ContractStatusUpdateForm(instance=contract)
        return render(
            request,
            "contracts/status-update.html",
            {"form": form, "contract": contract},
        )


@log_view_access
@login_required
def item_new_value_request_view(request, pk):
    contract = _accessible_contract_or_404(request, pk)
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_change_statuses:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        with transaction.atomic():
            instance = get_object_or_404(
                self.get_queryset().select_for_update(), id=self.kwargs["pk"]
            )

            instance.status = form.cleaned_data["status"]
            instance.rejection_reason = form.cleaned_data["rejection_reason"]
            instance.save()

            if instance.status == ContractItemNewValueRequest.ReviewStatus.APPROVED:
                instance.raise_item.month_expense += instance.month_raise
                instance.raise_item.anual_expense += instance.anual_raise
                instance.raise_item.save()

                instance.downgrade_item.month_expense -= instance.month_raise
                instance.downgrade_item.anual_expense -= instance.anual_raise
                instance.downgrade_item.save()
            action = ActivityLog.ActivityLogChoices.ANALISED_NEW_VALUE_ITEM

            _ = ActivityLog.objects.create(
                user=self.request.user,
                user_email=self.request.user.email,
                action=action,
                target_object_id=instance.id,
                target_content_object=instance,
            )

        self.object = instance
        return redirect(self.get_success_url())

    def get_queryset(self) -> QuerySet[Any]:
        contracts = _accessible_contracts(self.request.user)
        return ContractItemNewValueRequest.objects.filter(
            raise_item__contract__in=contracts,
            downgrade_item__contract__in=contracts,
            status=ContractItemNewValueRequest.ReviewStatus.IN_REVIEW,
        ).select_related(
            "requested_by",
            "downgrade_item",
            "raise_item",
            "raise_item__contract",
        )

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

    if not request.user or not request.user.can_review_accountability:
        return redirect("contracts:executions-detail", pk=execution.id)

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

    if not request.user or not request.user.can_review_accountability:
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
    contract = _accessible_contract_or_404(request, pk)
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
    contract = _accessible_contract_or_404(request, pk)
    if request.user.is_committee_member:
        raise Http404
    if contract.is_finished:
        return redirect("contracts:item-supplementations", pk=contract.id)

    if request.method == "POST":
        form = ContractItemSupplementForm(request.POST, contract=contract)
        if form.is_valid():
            with transaction.atomic():
                supplement = form.save(commit=False)
                supplement.suplement_value = form.cleaned_data["supplement_value"]
                supplement.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_ITEM_SUPPLEMENT,
                    target_object_id=supplement.id,
                    target_content_object=supplement,
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
    if request.user.is_committee_member:
        raise Http404
    supplement = _accessible_supplement_or_404(request, pk, pending_only=True)
    if request.method == "POST":
        form = ContractItemSupplementUpdateForm(request.POST, instance=supplement)
        if form.is_valid():
            with transaction.atomic():
                supplement = form.save(commit=False)
                supplement.suplement_value = form.cleaned_data["supplement_value"]
                supplement.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM_SUPPLEMENT,
                    target_object_id=supplement.id,
                    target_content_object=supplement,
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


@login_required
def contract_item_supplementations_review_view(request, pk):
    if not request.user.can_change_statuses:
        raise Http404

    supplement = _accessible_supplement_or_404(request, pk, pending_only=True)
    if request.method == "POST":
        form = ContractItemSupplementReviewForm(request.POST, instance=supplement)
        if form.is_valid():
            with transaction.atomic():
                supplement = _accessible_supplement_or_404(
                    request, pk, pending_only=True, for_update=True
                )
                supplement.status = form.cleaned_data["status"]
                supplement.rejection_reason = form.cleaned_data["rejection_reason"]
                supplement.reviewed_by = request.user
                supplement.reviewed_at = timezone.now()
                supplement.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_ITEM_SUPPLEMENT,
                    target_object_id=supplement.id,
                    target_content_object=supplement,
                )
            return redirect(
                "contracts:item-supplementations", pk=supplement.item.contract.id
            )
    else:
        form = ContractItemSupplementReviewForm(instance=supplement)

    return render(
        request,
        "contracts/items/supplementations-review.html",
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


@login_required
def create_contract_addendum_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_planning:
        return redirect("contracts:contracts-detail", pk=contract.id)

    if request.method == "POST":
        form = ContractAddendumForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                addendum: ContractAddendum = form.save(commit=False)
                addendum.contract = contract
                addendum.save()

                contract.total_value = addendum.total_value
                contract.municipal_value = addendum.municipal_value
                contract.counterpart_value = addendum.counterpart_value
                contract.end_of_vigency = addendum.end_of_vigency
                contract.save(
                    update_fields=[
                        "updated_at",
                        "total_value",
                        "municipal_value",
                        "counterpart_value",
                        "end_of_vigency",
                    ]
                )

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_ADDENDUM,
                    target_object_id=addendum.id,
                    target_content_object=addendum,
                )
            return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/addendums-create.html",
                {"contract": contract, "form": form},
            )
    else:
        form = ContractAddendumForm()
        return render(
            request,
            "contracts/addendums-create.html",
            {"contract": contract, "form": form},
        )


@login_required
def create_contract_document_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_planning:
        return redirect("contracts:contracts-detail", pk=contract.id)

    if request.method == "POST":
        form = ContractDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                document: ContractDocument = form.save(commit=False)
                document.contract = contract
                document.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_DOCUMENT,
                    target_object_id=document.id,
                    target_content_object=document,
                )
            return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/documents-create.html",
                {"contract": contract, "form": form},
            )
    else:
        form = ContractDocumentForm()
        return render(
            request,
            "contracts/documents-create.html",
            {"contract": contract, "form": form},
        )


@login_required
def update_contract_document_view(request, pk, document_pk):
    if not request.user:
        return redirect("/accounts-login/")

    contract = get_object_or_404(Contract, id=pk)
    if not contract.is_on_planning:
        return redirect("contracts:contracts-detail", pk=contract.id)

    document = get_object_or_404(ContractDocument, id=document_pk)

    if request.method == "POST":
        form = ContractDocumentUpdateForm(request.POST, instance=document)
        if form.is_valid():
            with transaction.atomic():
                form.save()

                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_DOCUMENT,
                    target_object_id=document.id,
                    target_content_object=document,
                )
            return redirect("contracts:contracts-detail", pk=contract.id)
        else:
            return render(
                request,
                "contracts/documents-update.html",
                {"contract": contract, "document": document, "form": form},
            )
    else:
        form = ContractDocumentUpdateForm(instance=document)
        return render(
            request,
            "contracts/documents-update.html",
            {"contract": contract, "document": document, "form": form},
        )


@login_required
def delete_contract_document_view(request, pk):
    if not request.user:
        return redirect("/accounts-login/")

    document = get_object_or_404(ContractDocument, id=pk)
    document.delete()
    return redirect("contracts:contracts-detail", pk=document.contract.id)


# =============================================================================
# AUDESP Fase V - contracts-app models (§6 Relação de Bens, §7 Contratos,
# §20/§21 referências de certidão), surfaced as the "AUDESP" tab on the
# contract detail page (templates/contracts/tabs/audesp-tab.html). Same
# "no ActivityLog / no explicit organization=" reasoning documented in
# accountability/views.py applies here too.
# =============================================================================


@login_required
def create_supplier_contract_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = SupplierContractForm(request.POST)
        if form.is_valid():
            # `contract` is excluded from the form, so
            # unique_supplier_contract_per_agreement is never checked by
            # Django's automatic validate_unique() (any constraint touching
            # an excluded field is skipped outright - see the analogous
            # comment on accountability.views.create_budget_commitment_view) -
            # check by hand instead of letting a genuine duplicate raise a
            # raw IntegrityError.
            exists = SupplierContract.objects.filter(
                contract=contract,
                number=form.cleaned_data["number"],
                signature_date=form.cleaned_data["signature_date"],
                creditor_document_type=form.cleaned_data["creditor_document_type"],
                creditor_document_number=form.cleaned_data["creditor_document_number"],
            ).exists()
            if exists:
                return render(
                    request,
                    "contracts/supplier-contract-create.html",
                    {
                        "contract": contract,
                        "form": form,
                        "supplier_contract_exists": True,
                    },
                )

            supplier_contract = form.save(commit=False)
            supplier_contract.contract = contract
            supplier_contract.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "contracts/supplier-contract-create.html",
            {"contract": contract, "form": form},
        )

    form = SupplierContractForm()
    return render(
        request,
        "contracts/supplier-contract-create.html",
        {"contract": contract, "form": form},
    )


class SupplierContractUpdateView(LoginRequiredMixin, UpdateView):
    model = SupplierContract
    form_class = SupplierContractForm
    template_name = "contracts/supplier-contract-create.html"
    context_object_name = "supplier_contract"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contract"] = self.object.contract
        return context

    def form_valid(self, form):
        # Same excluded-field gap as create_supplier_contract_view - check
        # by hand.
        exists = (
            SupplierContract.objects.filter(
                contract=self.object.contract,
                number=form.cleaned_data["number"],
                signature_date=form.cleaned_data["signature_date"],
                creditor_document_type=form.cleaned_data["creditor_document_type"],
                creditor_document_number=form.cleaned_data["creditor_document_number"],
            )
            .exclude(pk=self.object.pk)
            .exists()
        )
        if exists:
            return self.render_to_response(
                self.get_context_data(form=form, supplier_contract_exists=True)
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail", kwargs={"pk": self.object.contract.id}
        )


@login_required
def create_asset_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.contract = contract
            asset.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "contracts/asset-create.html",
            {"contract": contract, "form": form},
        )

    form = AssetForm()
    return render(
        request,
        "contracts/asset-create.html",
        {"contract": contract, "form": form},
    )


class AssetUpdateView(LoginRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = "contracts/asset-create.html"
    context_object_name = "asset"
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
def create_certificate_reference_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)

    if request.method == "POST":
        form = CertificateReferenceForm(request.POST)
        if form.is_valid():
            # `contract` is excluded from the form, so
            # unique_certificate_reference_per_type is never checked by
            # Django's automatic validate_unique() (see the analogous comment
            # on accountability.views.create_budget_commitment_view) - check
            # by hand instead of letting a genuine duplicate raise a raw
            # IntegrityError.
            exists = CertificateReference.objects.filter(
                contract=contract, type=form.cleaned_data["type"]
            ).exists()
            if exists:
                return render(
                    request,
                    "contracts/certificate-reference-create.html",
                    {
                        "contract": contract,
                        "form": form,
                        "certificate_reference_exists": True,
                    },
                )

            reference = form.save(commit=False)
            reference.contract = contract
            reference.save()
            return redirect("contracts:contracts-detail", pk=contract.id)
        return render(
            request,
            "contracts/certificate-reference-create.html",
            {"contract": contract, "form": form},
        )

    form = CertificateReferenceForm()
    return render(
        request,
        "contracts/certificate-reference-create.html",
        {"contract": contract, "form": form},
    )


class CertificateReferenceUpdateView(LoginRequiredMixin, UpdateView):
    model = CertificateReference
    form_class = CertificateReferenceForm
    template_name = "contracts/certificate-reference-create.html"
    context_object_name = "certificate_reference"
    login_url = "/auth/login"

    def get_object(self, queryset=None):
        return self.model.objects.select_related("contract").get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contract"] = self.object.contract
        return context

    def form_valid(self, form):
        # Same excluded-field gap as create_certificate_reference_view -
        # check by hand.
        exists = (
            CertificateReference.objects.filter(
                contract=self.object.contract, type=form.cleaned_data["type"]
            )
            .exclude(pk=self.object.pk)
            .exists()
        )
        if exists:
            return self.render_to_response(
                self.get_context_data(form=form, certificate_reference_exists=True)
            )
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse_lazy(
            "contracts:contracts-detail", kwargs={"pk": self.object.contract.id}
        )


class ContractOptionsView(UserAccessQuerysetMixin, ComboboxSearchView):
    """Option source for contract comboboxes.

    Scoped with the same `filter_by_user_access` rules the contract form
    fields use, so the endpoint never widens what a user can already pick.
    """

    search_fields = ("name", "objective", "code")
    numeric_search_fields = ("internal_code",)
    ordering = ("-internal_code",)

    def get_queryset(self) -> QuerySet[Any]:
        return (
            self.filter_by_user_access(Contract.objects.all(), self.request.user)
            .select_related("area")
            .distinct()
        )

    def serialize(self, obj) -> dict:
        # Must match ContractChoiceField.label_from_instance so the label the
        # endpoint returns and the one rendered for a preselected value agree.
        return {
            "id": str(obj.pk),
            "text": obj.name_with_code,
            "subtext": obj.status_label,
        }
