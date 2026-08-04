from .xlsx_exporter import AccountabilityXLSXExporter

__all__ = [
    "AccountabilityXLSXExporter",
    "AccountabilityXLSXImporter",
]


def __getattr__(name: str):
    # xlsx_importer imports pandas + numpy, which cost ~95 MiB resident. Only
    # the XLSX *upload* path needs them, but this package is reachable from the
    # URLconf, so an eager import charged that to every worker on every cold
    # start. Resolve it on first access instead (PEP 562).
    if name == "AccountabilityXLSXImporter":
        from .xlsx_importer import AccountabilityXLSXImporter

        return AccountabilityXLSXImporter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
