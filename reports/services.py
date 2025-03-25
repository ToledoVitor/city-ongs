from datetime import date, datetime

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


def export_pass_on_3(
    contract: Contract, start_date: date, end_date: date, responsibles: list = None
):
    return PassOn3PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
        responsibles=responsibles,
    ).handle()


def export_pass_on_4(contract: Contract, start_date: date, end_date: date):
    return PassOn4PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_5(
    contract: Contract, start_date: date, end_date: date, responsibles: list = None
):
    return PassOn5PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
        responsibles=responsibles,
    ).handle()


def export_pass_on_6(contract: Contract, start_date: date, end_date: date):
    return PassOn6PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_7(
    contract: Contract, start_date: date, end_date: date, responsibles: list = None
):
    return PassOn7PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
        responsibles=responsibles,
    ).handle()


def export_pass_on_8(contract: Contract, start_date: date, end_date: date):
    return PassOn8PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_9(
    contract: Contract, start_date: date, end_date: date, responsibles: list = None
):
    return PassOn9PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
        responsibles=responsibles,
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


def export_pass_on_13(
    contract: Contract, start_date: date, end_date: date, responsibles: list = None
):
    return PassOn13PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
        responsibles=responsibles,
    ).handle()


def export_pass_on_14(contract: Contract, start_date: date, end_date: date):
    return PassOn14PDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_period_expenses(contract: Contract, start_date: date, end_date: date):
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
    responsibles: list = None,
):
    match report_model:
        case "rp_1":
            return export_pass_on_1(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "rp_2":
            return export_pass_on_2(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "rp_3":
            return export_pass_on_3(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
                responsibles=responsibles,
            )

        case "rp_4":
            return export_pass_on_4(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "rp_5":
            return export_pass_on_5(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
                responsibles=responsibles,
            )

        case "rp_6":
            return export_pass_on_6(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "rp_7":
            return export_pass_on_7(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
                responsibles=responsibles,
            )

        case "rp_8":
            return export_pass_on_8(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "rp_9":
            return export_pass_on_9(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
                responsibles=responsibles,
            )

        case "rp_10":
            return export_pass_on_10(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "rp_11":
            return export_pass_on_11(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "rp_12":
            return export_pass_on_12(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "rp_13":
            return export_pass_on_13(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
                responsibles=responsibles,
            )

        case "rp_14":
            return export_pass_on_14(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "period_expenses":
            return export_period_expenses(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "predicted_versus_realized":
            return export_predicted_versus_realized(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case "consolidated":
            return export_consolidated(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
            )

        case _:
            raise ValueError(f"Report model {report_model} is not a valid option")
