import calendar
from datetime import date, datetime

from contracts.models import Contract
from reports.exporters import (
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


def export_pass_on_3(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn3PDFExporter(contract).handle()


def export_pass_on_4():  # TOcontract: Contract, start_date: date, end_date: dateD -> NoneO
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn4PDFExporter(contract).handle()


def export_pass_on_5(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn5PDFExporter(contract).handle()


def export_pass_on_6(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn6PDFExporter(contract).handle()


def export_pass_on_7(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn7PDFExporter(contract).handle()


def export_pass_on_8(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn8PDFExporter(contract).handle()


def export_pass_on_9(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn9PDFExporter(contract).handle()


def export_pass_on_10(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn10PDFExporter(contract).handle()


def export_pass_on_11(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn11PDFExporter(contract).handle()


def export_pass_on_12(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn12PDFExporter(contract).handle()


def export_pass_on_13(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn13PDFExporter(contract).handle()


def export_pass_on_14(contract: Contract, start_date: date, end_date: date):
    contract = Contract.objects.first()  # get(id=contract_id)
    return PassOn14PDFExporter(contract).handle()


def _get_start_end_date(month: int, year: int):
    last_day = calendar.monthrange(year, month)[1]
    
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, last_day)
    return start_date, end_date

def export_report(contract: Contract, report_model: str, month: int, year: int):
    start_date, end_date = _get_start_end_date(int(month), int(year))
    match report_model:
        # case "rp_1":
        #     return export_pass_on_1(contract, start_date, end_date)

        # case "rp_2":
        #     return export_pass_on_2(contract, start_date, end_date)

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

        case _:
            raise ValueError(f"Report model {report_model} is not a valid option")
