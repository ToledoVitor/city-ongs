import calendar
from datetime import date, datetime

from accountability.models import Accountability
from contracts.models import Contract
from reports.exporters import (
    PassOn1PDFExporter,
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
)


<<<<<<< Updated upstream
def export_pass_on_3(accountability: Accountability, start_date: date, end_date: date):
=======
def export_pass_on_1(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn1PDFExporter(contract).handle()


def export_pass_on_3(contract: Contract, start_date: date, end_date: date):
>>>>>>> Stashed changes
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn3PDFExporter(contract).handle()


<<<<<<< Updated upstream
def export_pass_on_4(accountability: Accountability, start_date: date, end_date: date):
=======
def export_pass_on_4(
    contract: Contract, start_date: date, end_date: date
):  # TOcontract: Contract, start_date: date, end_date: dateD -> NoneO
>>>>>>> Stashed changes
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn4PDFExporter(contract).handle()


def export_pass_on_5(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn5PDFExporter(contract).handle()


def export_pass_on_6(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn6PDFExporter(contract).handle()


def export_pass_on_7(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn7PDFExporter(contract).handle()


def export_pass_on_8(accountability: Accountability, start_date: date, end_date: date):
    return PassOn8PDFExporter(
        accountability=accountability,
        start_date=start_date,
        end_date=end_date,
    ).handle()


def export_pass_on_9(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn9PDFExporter(contract).handle()


def export_pass_on_10(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn10PDFExporter(contract).handle()


def export_pass_on_11(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn11PDFExporter(contract).handle()


def export_pass_on_12(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn12PDFExporter(contract).handle()


def export_pass_on_13(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn13PDFExporter(contract).handle()


def export_pass_on_14(accountability: Accountability, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn14PDFExporter(contract).handle()


def _get_start_end_date(month: int, year: int):
    last_day = calendar.monthrange(year, month)[1]

    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, last_day)
    return start_date, end_date


def export_report(contract: Contract, report_model: str, month: int, year: int):
    start_date, end_date = _get_start_end_date(int(month), int(year))
    accountability = (
        Accountability.objects.filter(
            month=month,
            year=year,
            contract=contract,
        )
        .select_related(
            "contract",
            "contract__organization",
            "contract__organization__city_hall",
            "contract__hired_company",
        )
        .first()
    )

    if not accountability:
        # TODO: raise error and validate its finished accountability
        return

    match report_model:
<<<<<<< Updated upstream
        # case "rp_1":
        #     return export_pass_on_1(accountability, start_date, end_date)
=======
        case "rp_1":
            return export_pass_on_1(contract, start_date, end_date)
>>>>>>> Stashed changes

        # case "rp_2":
        #     return export_pass_on_2(accountability, start_date, end_date)

        case "rp_3":
            return export_pass_on_3(accountability, start_date, end_date)

        case "rp_4":
            return export_pass_on_4(accountability, start_date, end_date)

        case "rp_5":
            return export_pass_on_5(accountability, start_date, end_date)

        case "rp_6":
            return export_pass_on_6(accountability, start_date, end_date)

        case "rp_7":
            return export_pass_on_7(accountability, start_date, end_date)

        case "rp_8":
            return export_pass_on_8(accountability, start_date, end_date)

        case "rp_9":
            return export_pass_on_9(accountability, start_date, end_date)

        case "rp_10":
            return export_pass_on_10(accountability, start_date, end_date)

        case "rp_11":
            return export_pass_on_11(accountability, start_date, end_date)

        case "rp_12":
            return export_pass_on_12(accountability, start_date, end_date)

        case "rp_13":
            return export_pass_on_13(accountability, start_date, end_date)

        case "rp_14":
            return export_pass_on_14(accountability, start_date, end_date)

        case _:
            raise ValueError(f"Report model {report_model} is not a valid option")
