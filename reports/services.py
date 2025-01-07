from reports.exporters import ContractProgressPDFExporter


def export_contract_progress():
    contract_id = "ID - Contrato"
    return ContractProgressPDFExporter().handle(contract_id=contract_id)


pdf.cell(0, 10, "Center-aligned text", align="C", ln=True)
