"""Section registry for the contract detail page.

The detail page is split into one URL per section (see the
``contracts-detail-section`` route).  A single registry drives four things at
once, so adding a section means adding one entry here and nothing else:

* which slugs the URL resolver accepts (anything else 404s);
* what the left contextual nav renders (group, label, icon);
* which template holds the section body;
* which queryset work the section actually needs.

The last point is the reason this exists.  The page used to render all eleven
sections on every request, so every visit paid for every tab.  Each section now
declares its own ``select_related`` / ``prefetch_related`` / extra context, and
the view builds only that.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable

from django.db.models import Sum, Value
from django.db.models.functions import Coalesce

# Icons are the ``d`` attribute of a single path drawn on a 24x24 stroke grid,
# matching the sidebar icon set in templates/base.html.
ICON_DETAILS = "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"  # noqa: E501
ICON_PEOPLE = "M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"  # noqa: E501
ICON_BANK = "M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"  # noqa: E501
ICON_DOCS = "M9 12h6m-6 4h6M9 8h6m4 13H5a2 2 0 01-2-2V5a2 2 0 012-2h14a2 2 0 012 2v14a2 2 0 01-2 2z"  # noqa: E501
ICON_GOALS = "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"  # noqa: E501
ICON_ITEMS = "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"  # noqa: E501
ICON_EXECUTION = "M13 10V3L4 14h7v7l9-11h-7z"
ICON_ACCOUNTABILITY = "M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"  # noqa: E501
ICON_CALENDAR = "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"  # noqa: E501
ICON_TRANSFER = "M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"
ICON_ADJUST = "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
ICON_REGISTRY = "M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
ICON_CHECK = "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"

# Nav group order on the page mirrors the contract lifecycle: what it is, what
# was promised, what happened, what gets reported to the TCE.
GROUP_CONTRACT = "Contrato"
GROUP_PLANNING = "Planejamento"
GROUP_EXECUTION = "Execução"
GROUP_AUDESP = "AUDESP"

GROUP_ORDER = (GROUP_CONTRACT, GROUP_PLANNING, GROUP_EXECUTION, GROUP_AUDESP)


@dataclass(frozen=True)
class Section:
    """One navigable section of the contract detail page."""

    slug: str
    label: str
    group: str
    template: str
    icon: str
    #: Applied to the ``Contract`` lookup itself.
    select_related: tuple[str, ...] = ()
    prefetch_related: tuple[str, ...] = ()
    #: Extra template context, built from the resolved contract.
    context: Callable[..., dict] | None = field(default=None, compare=False)

    def get_context(self, contract) -> dict:
        return self.context(contract) if self.context else {}


def _recent(manager, order_by: str, *, limit: int = 12, select_related: tuple = ()):
    """Latest non-deleted rows of a reverse relation, newest first."""
    queryset = manager.filter(deleted_at__isnull=True)
    if select_related:
        queryset = queryset.select_related(*select_related)
    return queryset.order_by(order_by)[:limit]


def _interesteds_context(contract) -> dict:
    return {
        "interested_parts": contract.interested_parts.filter(deleted_at__isnull=True)
        .select_related("user")
        .order_by("user__first_name")[:12]
    }


def _documents_context(contract) -> dict:
    return {
        "addendums": _recent(contract.addendums, "-created_at"),
        "documents": _recent(contract.documents, "-created_at"),
    }


def _items_context(contract) -> dict:
    from contracts.models import ContractItemNewValueRequest

    return {
        "items_totals": contract.items.aggregate(
            total_month=Coalesce(Sum("month_expense"), Value(Decimal("0.00"))),
            total_year=Coalesce(Sum("anual_expense"), Value(Decimal("0.00"))),
        ),
        "value_requests": ContractItemNewValueRequest.objects.filter(
            raise_item__contract=contract,
            status=ContractItemNewValueRequest.ReviewStatus.IN_REVIEW,
        ).select_related("raise_item")[:12],
    }


def _execution_context(contract) -> dict:
    from django.db.models import Count, Q

    return {
        "executions": contract.executions.filter(deleted_at__isnull=True)
        .annotate(
            count_activities=Count(
                "activities",
                filter=Q(activities__deleted_at__isnull=True),
                distinct=True,
            ),
            count_files=Count(
                "files", filter=Q(files__deleted_at__isnull=True), distinct=True
            ),
        )
        .prefetch_related("activities", "files")
        .order_by("-year", "-month")[:12]
    }


def _accountability_context(contract) -> dict:
    from django.db.models import Count, Q

    return {
        "accountabilities": contract.accountabilities.filter(deleted_at__isnull=True)
        .prefetch_related("revenues", "expenses")
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
        )
        .order_by("-year", "-month")[:12]
    }


def _audesp_statements_context(contract) -> dict:
    return {"annual_statements": _recent(contract.annual_statements, "-fiscal_year")}


def _audesp_transfers_context(contract) -> dict:
    return {
        "budget_commitments": _recent(contract.budget_commitments, "-issue_date"),
        "fund_transfers": _recent(
            contract.fund_transfers,
            "-transfer_date",
            select_related=("budget_commitment",),
        ),
    }


def _audesp_adjustments_context(contract) -> dict:
    return {
        "balance_adjustments": _recent(contract.balance_adjustments, "-date"),
        "expense_rejections": _recent(contract.expense_rejections, "-created_at"),
        "deductions": _recent(contract.deductions, "-date"),
        "refunds": _recent(contract.refunds, "-date"),
    }


def _audesp_registry_context(contract) -> dict:
    return {
        "supplier_contracts": _recent(contract.supplier_contracts, "-signature_date"),
        "assets": _recent(contract.assets, "-date"),
        "certificate_references": _recent(contract.certificate_references, "type"),
    }


def _audesp_fase_iv_context(contract) -> dict:
    # The submission list comes from the audesp_fase_iv_submissions_for template
    # tag; the tab only needs the commitments to build the empenho form.
    return {"budget_commitments": _recent(contract.budget_commitments, "-issue_date")}


SECTIONS: tuple[Section, ...] = (
    Section(
        slug="details",
        label="Detalhes",
        group=GROUP_CONTRACT,
        template="contracts/tabs/details-tab.html",
        icon=ICON_DETAILS,
        select_related=(
            "contractor_company",
            "contractor_manager",
            "hired_company",
            "hired_manager",
            "organization",
            "area",
        ),
    ),
    Section(
        slug="interesteds",
        label="Interessados",
        group=GROUP_CONTRACT,
        template="contracts/tabs/interesteds-tab.html",
        icon=ICON_PEOPLE,
        context=_interesteds_context,
    ),
    Section(
        slug="accounts",
        label="Contas bancárias",
        group=GROUP_CONTRACT,
        template="contracts/tabs/banks-tab.html",
        icon=ICON_BANK,
        select_related=("checking_account", "investing_account"),
    ),
    Section(
        slug="addendums",
        label="Aditivos e documentos",
        group=GROUP_CONTRACT,
        template="contracts/tabs/documents-tab.html",
        icon=ICON_DOCS,
        context=_documents_context,
    ),
    Section(
        slug="goals",
        label="Metas",
        group=GROUP_PLANNING,
        template="contracts/tabs/goals-tab.html",
        icon=ICON_GOALS,
        # Reviews are deliberately not prefetched: ContractGoal.last_reviews
        # re-orders and slices the relation, so a prefetch cache cannot serve it
        # and would only add a wasted query.
        prefetch_related=("goals", "goals__steps"),
    ),
    Section(
        slug="items",
        label="Itens e orçamento",
        group=GROUP_PLANNING,
        template="contracts/tabs/items-tab.html",
        icon=ICON_ITEMS,
        # See the note on the goals section — ContractItem.last_reviews slices,
        # so item reviews are not prefetchable here either.
        prefetch_related=("items",),
        context=_items_context,
    ),
    Section(
        slug="execution",
        label="Relatórios de execução",
        group=GROUP_EXECUTION,
        template="contracts/tabs/execution-tab.html",
        icon=ICON_EXECUTION,
        context=_execution_context,
    ),
    Section(
        slug="accountability",
        label="Prestação de contas",
        group=GROUP_EXECUTION,
        template="contracts/tabs/accountability-tab.html",
        icon=ICON_ACCOUNTABILITY,
        context=_accountability_context,
    ),
    Section(
        slug="audesp",
        label="Prestações anuais",
        group=GROUP_AUDESP,
        template="contracts/tabs/audesp-statements-tab.html",
        icon=ICON_CALENDAR,
        context=_audesp_statements_context,
    ),
    Section(
        slug="audesp-transfers",
        label="Empenhos e repasses",
        group=GROUP_AUDESP,
        template="contracts/tabs/audesp-transfers-tab.html",
        icon=ICON_TRANSFER,
        context=_audesp_transfers_context,
    ),
    Section(
        slug="audesp-adjustments",
        label="Ajustes e glosas",
        group=GROUP_AUDESP,
        template="contracts/tabs/audesp-adjustments-tab.html",
        icon=ICON_ADJUST,
        context=_audesp_adjustments_context,
    ),
    Section(
        slug="audesp-registry",
        label="Fornecedores, bens e certidões",
        group=GROUP_AUDESP,
        template="contracts/tabs/audesp-registry-tab.html",
        icon=ICON_REGISTRY,
        context=_audesp_registry_context,
    ),
    Section(
        slug="audesp-fase-iv",
        label="Fase IV — Licitações",
        group=GROUP_AUDESP,
        template="contracts/tabs/audesp-fase-iv-tab.html",
        icon=ICON_CHECK,
        context=_audesp_fase_iv_context,
    ),
    Section(
        slug="audesp-fase-v",
        label="Fase V — Repasses",
        group=GROUP_AUDESP,
        template="contracts/tabs/audesp-fase-v-tab.html",
        icon=ICON_CHECK,
    ),
)

SECTIONS_BY_SLUG: dict[str, Section] = {section.slug: section for section in SECTIONS}

DEFAULT_SECTION_SLUG = "details"


def get_section(slug: str | None) -> Section | None:
    """Resolve a slug to a section, or ``None`` when it is not a real section."""
    return SECTIONS_BY_SLUG.get(slug or DEFAULT_SECTION_SLUG)


def nav_groups() -> list[dict]:
    """Sections bucketed into their nav groups, in lifecycle order."""
    return [
        {
            "label": group,
            "sections": [s for s in SECTIONS if s.group == group],
        }
        for group in GROUP_ORDER
    ]
