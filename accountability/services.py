from django.core.files.uploadedfile import InMemoryUploadedFile

from accountability.models import Accountability
from accountability.xlsx import AccountabilityXLSXExporter


def export_xlsx_model(accountability: Accountability):
    return AccountabilityXLSXExporter(accountability).handle()


def import_xlsx_model(file: InMemoryUploadedFile, accountability: Accountability):
    # Imported here, not at module scope: the importer pulls in pandas + numpy
    # (~95 MiB resident) and this module is reachable from the URLconf, so a
    # top-level import would charge that to every request path, not just upload.
    from accountability.xlsx import AccountabilityXLSXImporter

    return AccountabilityXLSXImporter(file, accountability).handle()
