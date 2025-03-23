from datetime import date, datetime
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce

from contracts.models import Contract
from reports.exporters import (
    ConsolidatedPDFExporter,
    PassOn1PDFExporter,
    PassOn2PDFExporter,
    PassOn3PDFExporter,
    PassOn4PDFExporter,
    PassOn5PDFExporter,
    PassOn6PDFExporter,
    PassOn7PDFExporter,
    PassOn8PDFExporter,
    PassOn9PDFExporter,
    PassOn10PDFExporter,
    PassOn11PDFExporter,
    PassOn12PDFExporter,
    PassOn13PDFExporter,
    PassOn14PDFExporter,
    PeriodEpensesPDFExporter,
    PredictedVersusRealizedPDFExporter,
)
from utils.cache_keys import (
    CACHE_TIMES,
    get_accountability_detail_key,
    get_accountability_stats_key,
    get_contract_detail_key,
    get_contract_stats_key,
)
from utils.logging import log_database_operation


def export_pass_on_1(contract: Contract, start_date: date, end_date: date):
    return PassOn1PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_2(contract: Contract, start_date: date, end_date: date):
    return PassOn2PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_3(contract: Contract, start_date: date, end_date: date):
    return PassOn3PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_4(contract: Contract, start_date: date, end_date: date):
    return PassOn4PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_5(contract: Contract, start_date: date, end_date: date):
    return PassOn5PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_6(contract: Contract, start_date: date, end_date: date):
    return PassOn6PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_7(contract: Contract, start_date: date, end_date: date):
    return PassOn7PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_8(contract: Contract, start_date: date, end_date: date):
    return PassOn8PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_9(contract: Contract, start_date: date, end_date: date):
    return PassOn9PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_10(contract: Contract, start_date: date, end_date: date):
    return PassOn10PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_11(contract: Contract, start_date: date, end_date: date):
    return PassOn11PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_12(contract: Contract, start_date: date, end_date: date):
    return PassOn12PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_13(contract: Contract, start_date: date, end_date: date):
    return PassOn13PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_14(contract: Contract, start_date: date, end_date: date):
    return PassOn14PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_period_expenses(
    contract: Contract, start_date: date, end_date: date
):
    return PeriodEpensesPDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_predicted_versus_realized(
    contract: Contract, start_date: date, end_date: date
):
    return PredictedVersusRealizedPDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_consolidated(contract: Contract, start_date: date, end_date: date):
    return ConsolidatedPDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_report(
    contract: Contract,
    start_date: datetime,
    end_date: datetime,
    report_model: str,
):
    match report_model:
        case "rp_1":
            return export_pass_on_1(contract, start_date, end_date)

        case "rp_2":
            return export_pass_on_2(contract, start_date, end_date)

        case "rp_3":
            return export_pass_on_3(contract, start_date, end_date)

        case "rp_4":
            return export_pass_on_4(contract, start_date, end_date)

        case "rp_5":
            return export_pass_on_5(contract, start_date, end_date)

        case "rp_6":
            return export_pass_on_6(contract, start_date, end_date)

        case "rp_7":
            return export_pass_on_7(contract, start_date, end_date)

        case "rp_8":
            return export_pass_on_8(contract, start_date, end_date)

        case "rp_9":
            return export_pass_on_9(contract, start_date, end_date)

        case "rp_10":
            return export_pass_on_10(contract, start_date, end_date)

        case "rp_11":
            return export_pass_on_11(contract, start_date, end_date)

        case "rp_12":
            return export_pass_on_12(contract, start_date, end_date)

        case "rp_13":
            return export_pass_on_13(contract, start_date, end_date)

        case "rp_14":
            return export_pass_on_14(contract, start_date, end_date)

        case "period_expenses":
            return export_period_expenses(contract, start_date, end_date)

        case "predicted_versus_realized":
            return export_predicted_versus_realized(
                contract, start_date, end_date
            )

        case "consolidated":
            return export_consolidated(contract, start_date, end_date)
        case _:
            raise ValueError(
                f"Report model {report_model} is not a valid option"
            )


class ReportCacheService:
    """
    Service to manage reports and statistics caching.
    """

    @staticmethod
    @log_database_operation("get_contract_stats")
    def get_contract_stats(contract_id):
        """
        Gets contract statistics from cache or calculates if they don't exist.
        """
        cache_key = get_contract_stats_key(contract_id)
        stats = cache.get(cache_key)

        if stats is None:
            from contracts.models import Contract

            contract = Contract.objects.get(id=contract_id)

            stats = {
                "total_value": contract.items.aggregate(
                    total=Coalesce(
                        Sum("anual_expense"), Value(Decimal("0.00"))
                    )
                )["total"],
                "total_expenses": contract.accountabilities.aggregate(
                    total=Coalesce(
                        Sum(
                            "expenses__value",
                            filter=Q(expenses__deleted_at__isnull=True),
                        ),
                        Value(Decimal("0.00")),
                    )
                )["total"],
                "total_revenues": contract.accountabilities.aggregate(
                    total=Coalesce(
                        Sum(
                            "revenues__value",
                            filter=Q(revenues__deleted_at__isnull=True),
                        ),
                        Value(Decimal("0.00")),
                    )
                )["total"],
                "pending_items": contract.items.filter(
                    status="pending"
                ).count(),
            }

            cache.set(cache_key, stats, CACHE_TIMES["STATS"])

        return stats

    @staticmethod
    @log_database_operation("get_accountability_stats")
    def get_accountability_stats(accountability_id):
        """
        Gets accountability statistics from cache or calculates if they don't exist.
        """
        cache_key = get_accountability_stats_key(accountability_id)
        stats = cache.get(cache_key)

        if stats is None:
            from accountability.models import Accountability

            accountability = Accountability.objects.get(id=accountability_id)

            stats = {
                "total_expenses": accountability.expenses.aggregate(
                    total=Coalesce(
                        Sum("value", filter=Q(deleted_at__isnull=True)),
                        Value(Decimal("0.00")),
                    )
                )["total"],
                "total_revenues": accountability.revenues.aggregate(
                    total=Coalesce(
                        Sum("value", filter=Q(deleted_at__isnull=True)),
                        Value(Decimal("0.00")),
                    )
                )["total"],
                "pending_expenses": accountability.expenses.filter(
                    status="in_analysis"
                ).count(),
                "pending_revenues": accountability.revenues.filter(
                    status="in_analysis"
                ).count(),
            }

            cache.set(cache_key, stats, CACHE_TIMES["STATS"])

        return stats

    @staticmethod
    @log_database_operation("invalidate_contract_cache")
    def invalidate_contract_cache(contract_id):
        """
        Invalidates the cache for a specific contract.
        """
        cache.delete(get_contract_stats_key(contract_id))
        cache.delete(get_contract_detail_key(contract_id))

    @staticmethod
    @log_database_operation("invalidate_accountability_cache")
    def invalidate_accountability_cache(accountability_id):
        """
        Invalidates the cache for a specific accountability.
        """
        cache.delete(get_accountability_stats_key(accountability_id))
        cache.delete(get_accountability_detail_key(accountability_id))
