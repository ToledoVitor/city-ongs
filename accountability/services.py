from accountability.models import Accountability
from accountability.csv import AccountabilityCSVExporter, AccountabilityCSVImporter


def export_csv_model(accountability: Accountability):
    return AccountabilityCSVExporter(accountability).handle()


def import_csv_model(accountability: Accountability):
    return AccountabilityCSVImporter(accountability).handle()