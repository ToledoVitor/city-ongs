"""Lógica compartilhada pelos "demonstrativos integrais de receitas e
despesas" (RP-06/08/10/12/14) — resumo de receitas por natureza e
categorização de despesas por natureza. Extraído porque as 5 classes
tinham essa mesma lógica (~250 linhas) duplicada quase byte a byte.
"""

import copy
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Q, QuerySet, Sum

from accountability.models import Expense, Revenue
from contracts.choices import NatureCategories
from contracts.models import Contract
from utils.formats import format_into_brazilian_currency


@dataclass
class RevenueSummary:
    checking_account: object
    investing_account: object
    revenue_queryset: QuerySet
    all_pass_on_values: Decimal
    previous_balance: Decimal
    investment_income: Decimal
    own_resources: Decimal
    other_revenues_value: Decimal
    latest_pass_on_info: dict | None


def build_revenue_summary(
    contract: Contract, start_date: date, end_date: date
) -> RevenueSummary:
    checking_account = contract.checking_account
    investing_account = contract.investing_account

    revenue_queryset = Revenue.objects.filter(
        Q(bank_account=checking_account) | Q(bank_account=investing_account),
        receive_date__gte=start_date,
        receive_date__lte=end_date,
    ).exclude(bank_account__isnull=True)

    def _sum_by_nature(nature: str) -> Decimal:
        return revenue_queryset.filter(revenue_nature=nature).aggregate(Sum("value"))[
            "value__sum"
        ] or Decimal("0.00")

    latest_pass_on_info = (
        revenue_queryset.filter(revenue_nature=Revenue.Nature.PUBLIC_TRANSFER)
        .order_by("-receive_date")
        .values("receive_date", "identification")
        .first()
    )

    return RevenueSummary(
        checking_account=checking_account,
        investing_account=investing_account,
        revenue_queryset=revenue_queryset,
        all_pass_on_values=_sum_by_nature(Revenue.Nature.PUBLIC_TRANSFER),
        previous_balance=_sum_by_nature(Revenue.Nature.PREVIOUS_BALANCE),
        investment_income=_sum_by_nature(Revenue.Nature.INVESTMENT_INCOME),
        own_resources=_sum_by_nature(Revenue.Nature.OWN_RESOURCES),
        other_revenues_value=_sum_by_nature(Revenue.Nature.OTHER_REVENUES),
        latest_pass_on_info=latest_pass_on_info,
    )


_EMPTY_CATEGORY_TOTALS = {
    "accounted_on": Decimal("0.00"),
    "not_accounted": Decimal("0.00"),
    "accounted_and_paid": Decimal("0.00"),
    "paid_on": Decimal("0.00"),
    "not_paid": Decimal("0.00"),
}

# Ordem preservada da cadeia if/elif original — a primeira categoria cuja
# lista de naturezas contém `expense.nature` vence.
_NATURE_CATEGORIES = (
    ("HUMAN_RESOURCES", NatureCategories.HUMAN_RESOURCES),
    ("OTHER_HUMAN_RESOURCES", NatureCategories.OTHER_HUMAN_RESOURCES),
    ("PERMANENT_GOODS", NatureCategories.PERMANENT_GOODS),
    ("OTHER_THIRD_PARTY", NatureCategories.OTHER_THIRD_PARTY),
    ("PUBLIC_UTILITIES", NatureCategories.PUBLIC_UTILITIES),
    ("FUEL", NatureCategories.FUEL),
    ("FINANCIAL_AND_BANKING", NatureCategories.FINANCIAL_AND_BANKING),
    ("FOODSTUFFS", NatureCategories.FOODSTUFFS),
    ("REAL_STATE", NatureCategories.REAL_STATE),
    ("MISCELLANEOUS", NatureCategories.MISCELLANEOUS),
    ("MEDICAL_AND_HOSPITAL", NatureCategories.MEDICAL_AND_HOSPITAL),
    ("MEDICAL_SERVICES", NatureCategories.MEDICAL_SERVICES),
    ("MEDICINES", NatureCategories.MEDICINES),
    ("WORKS", NatureCategories.WORKS),
    ("OTHER_EXPENSES", NatureCategories.OTHER_EXPENSES),
    ("OTHER_CONSUMABLES", NatureCategories.OTHER_CONSUMABLES),
)


def _get_expense_nature_category(expense: Expense) -> str | None:
    if not expense.nature:
        return None
    for label, natures in _NATURE_CATEGORIES:
        if expense.nature in natures:
            return label
    return None


def categorize_expenses(
    contract: Contract, start_date: date, end_date: date, *, inclusive_bounds: bool
) -> dict:
    """
    inclusive_bounds: os 5 exportadores que usam esta função divergiam nessa
    comparação antes da extração — RP-06/08 usavam `<`/`<` (exclusivo) e
    RP-10/12/14 usavam `<=`/`<=` (inclusivo) para decidir se `competency`/
    `due_date` cai dentro do período. Preservado explícito por chamador em
    vez de escolhido um padrão, pra não mudar o valor de nenhum PDF nessa
    extração — ver REPORTS_TODO.md sobre normalizar isso.
    """
    expenses = Expense.objects.filter(
        accountability__contract=contract,
        due_date__gte=start_date,
        due_date__lte=end_date,
    )

    categorized = {
        label: copy.deepcopy(_EMPTY_CATEGORY_TOTALS) for label, _ in _NATURE_CATEGORIES
    }
    categorized["TOTAL"] = copy.deepcopy(_EMPTY_CATEGORY_TOTALS)

    for expense in expenses:
        category = _get_expense_nature_category(expense)
        if not category:
            continue

        if inclusive_bounds:
            accounted_on_period = (
                expense.competency
                and start_date.date() <= expense.competency <= end_date.date()
            )
            paid_on_period = (
                expense.due_date
                and start_date.date() <= expense.due_date <= end_date.date()
            )
        else:
            accounted_on_period = (
                expense.competency
                and start_date.date() < expense.competency < end_date.date()
            )
            paid_on_period = (
                expense.due_date
                and start_date.date() < expense.due_date < end_date.date()
            )

        if paid_on_period and accounted_on_period:
            categorized[category]["accounted_and_paid"] += expense.value
            categorized[category]["accounted_on"] += expense.value
            categorized[category]["paid_on"] += expense.value

            categorized["TOTAL"]["accounted_and_paid"] += expense.value
            categorized["TOTAL"]["paid_on"] += expense.value
            categorized["TOTAL"]["accounted_on"] += expense.value

        elif paid_on_period and not accounted_on_period:
            categorized[category]["not_accounted"] += expense.value
            categorized[category]["paid_on"] += expense.value

            categorized["TOTAL"]["not_accounted"] += expense.value
            categorized["TOTAL"]["paid_on"] += expense.value

        elif not paid_on_period and accounted_on_period:
            categorized[category]["not_paid"] += expense.value
            categorized[category]["accounted_on"] += expense.value

            categorized["TOTAL"]["accounted_on"] += expense.value
            categorized["TOTAL"]["not_paid"] += expense.value

    return categorized


def categorize_paid_expenses(expenses: QuerySet) -> dict:
    """Soma um queryset de despesas já filtrado (`paid=True`, dentro do
    período por `liquidation`) por categoria de natureza.

    Usado pelo RP-14: ao contrário do RP-06/08/10/12, seu anexo não quebra
    a "despesa realizada" em contabilizada/paga (due_date) vs.
    efetivamente paga (liquidation) — as duas tabelas do modelo oficial
    (por categoria e a relação nominal de despesas) precisam bater no
    mesmo total, então ambas devem somar a mesma queryset de origem.
    """
    totals = {label: Decimal("0.00") for label, _ in _NATURE_CATEGORIES}
    totals["TOTAL"] = Decimal("0.00")

    for expense in expenses:
        category = _get_expense_nature_category(expense)
        if not category:
            continue
        totals[category] += expense.value
        totals["TOTAL"] += expense.value

    return totals


def convert_decimal_to_brl(expenses_dict: dict) -> dict:
    """Retorna uma cópia formatada em BRL — não muta `expenses_dict`, para
    que o dict original com os `Decimal` continue reaproveitável por quem
    chamou (ex.: cálculos financeiros que rodam depois da renderização da
    tabela)."""
    result = {}
    for key, value in expenses_dict.items():
        if isinstance(value, Decimal):
            result[key] = format_into_brazilian_currency(value)
        elif isinstance(value, dict):
            result[key] = convert_decimal_to_brl(value)
        else:
            result[key] = value

    return result
