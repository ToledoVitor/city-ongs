import calendar
from datetime import date, datetime

from accountability.models import Accountability
from contracts.models import Contract
from reports.forms import ReportForm, TRANSACTION_OPTIONS
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


def export_pass_on_1(accountability: Accountability, start_date: date, end_date: date):
    return PassOn1PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_2(accountability: Accountability, start_date: date, end_date: date):
    return PassOn2PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_3(accountability: Accountability, start_date: date, end_date: date):
    return PassOn3PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_4(accountability: Accountability, start_date: date, end_date: date):
    return PassOn4PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_5(accountability: Accountability, start_date: date, end_date: date):
    return PassOn5PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_6(accountability: Accountability, start_date: date, end_date: date):
    return PassOn6PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_7(accountability: Accountability, start_date: date, end_date: date):
    return PassOn7PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_8(accountability: Accountability, start_date: date, end_date: date):
    return PassOn8PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_9(accountability: Accountability, start_date: date, end_date: date):
    return PassOn9PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_10(accountability: Accountability, start_date: date, end_date: date):
    return PassOn10PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_11(accountability: Accountability, start_date: date, end_date: date):
    return PassOn11PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_12(accountability: Accountability, start_date: date, end_date: date):
    return PassOn12PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_13(accountability: Accountability, start_date: date, end_date: date):
    return PassOn13PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_14(accountability: Accountability, start_date: date, end_date: date):
    return PassOn14PDFExporter(
        accountability=accountability,
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


def export_consolidated(
    contract: Contract, start_date: date, end_date: date
):
    return ConsolidatedPDFExporter(
        contract=contract,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def _get_start_end_date(month: int, year: int):
    last_day = calendar.monthrange(year, month)[1]

    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, last_day)
    return start_date, end_date


def get_model_for_report(form: ReportForm):
    cleaned_data = form.cleaned_data
    transaction_reports = {opt[0] for opt in TRANSACTION_OPTIONS}
    if cleaned_data["report_model"] in transaction_reports:
        return (
            cleaned_data["contract"],
            cleaned_data["start_date"],
            cleaned_data["end_date"],
        )
    
    else:
        start_date, end_date = _get_start_end_date(
            month=int(cleaned_data["month"]),
            year=int(cleaned_data["year"]),
        )
        return (
                (
                Accountability.objects.filter(
                    month=cleaned_data["month"],
                    year=cleaned_data["year"],
                    contract=cleaned_data["contract"],
                )
                .select_related(
                    "contract",
                    "contract__organization",
                    "contract__organization__city_hall",
                    "contract__hired_company",
                )
                .first()
            ),
            start_date,
            end_date,
        )

def export_report(
    model: Accountability | Contract,
    start_date: datetime,
    end_date: datetime,
    report_model: str,
):
    match report_model:
        case "rp_1":
            return export_pass_on_1(model, start_date, end_date)

        case "rp_2":
            return export_pass_on_2(model, start_date, end_date)

        case "rp_3":
            return export_pass_on_3(model, start_date, end_date)

        case "rp_4":
            return export_pass_on_4(model, start_date, end_date)

        case "rp_5":
            return export_pass_on_5(model, start_date, end_date)

        case "rp_6":
            return export_pass_on_6(model, start_date, end_date)

        case "rp_7":
            return export_pass_on_7(model, start_date, end_date)

        case "rp_8":
            return export_pass_on_8(model, start_date, end_date)

        case "rp_9":
            return export_pass_on_9(model, start_date, end_date)

        case "rp_10":
            return export_pass_on_10(model, start_date, end_date)

        case "rp_11":
            return export_pass_on_11(model, start_date, end_date)

        case "rp_12":
            return export_pass_on_12(model, start_date, end_date)

        case "rp_13":
            return export_pass_on_13(model, start_date, end_date)

        case "rp_14":
            return export_pass_on_14(model, start_date, end_date)

        case "period_expenses":
            return export_period_expenses(model, start_date, end_date)

        case "predicted_versus_realized":
            return export_predicted_versus_realized(
                model, start_date, end_date
            )

        case "consolidated":
            return export_consolidated(model, start_date, end_date)

        case _:
            raise ValueError(f"Report model {report_model} is not a valid option")
