from django.core.files.uploadedfile import InMemoryUploadedFile

from accountability.models import Accountability
from accountability.xlsx import AccountabilityXLSXExporter, AccountabilityXLSXImporter


def export_xlsx_model(accountability: Accountability):
    return AccountabilityXLSXExporter(accountability).handle()

def import_xlsx_model(file: InMemoryUploadedFile, accountability: Accountability):
    return AccountabilityXLSXImporter(file, accountability).handle()
