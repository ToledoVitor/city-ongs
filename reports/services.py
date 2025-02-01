from datetime import datetime

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


def export_pass_on_3():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn3PDFExporter(contract).handle()
    pdf.output(f"rp3-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_4():  # TODO
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn4PDFExporter(contract).handle()
    pdf.output(f"rp4-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_5():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn5PDFExporter(contract).handle()
    pdf.output(f"rp5-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_6():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn6PDFExporter(contract).handle()
    pdf.output(f"rp6-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_7():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn7PDFExporter(contract).handle()
    pdf.output(f"rp7-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_8():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn8PDFExporter(contract).handle()
    pdf.output(f"rp8-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_9():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn9PDFExporter(contract).handle()
    pdf.output(f"rp9-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_10():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn10PDFExporter(contract).handle()
    pdf.output(f"rp10-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_11():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn11PDFExporter(contract).handle()
    pdf.output(f"rp11-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_12():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn12PDFExporter(contract).handle()
    pdf.output(f"rp12-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_13():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn13PDFExporter(contract).handle()
    pdf.output(f"rp13-{str(datetime.now().time())[0:8]}.pdf")


def export_pass_on_14():
    contract = Contract.objects.first()  # get(id=contract_id)
    pdf = PassOn14PDFExporter(contract).handle()
    pdf.output(f"rp14-{str(datetime.now().time())[0:8]}.pdf")
