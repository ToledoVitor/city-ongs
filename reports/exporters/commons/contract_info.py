from utils.formats import document_mask

NOT_INFORMED = "Não Informado"


def expenditure_orderer_info(contract) -> tuple[str, str, str]:
    """Nome, cargo e documento do ordenador de despesa do órgão público parceiro.

    Nenhum dos três valores volta vazio: o fpdf2 recusa ``cell(text="")`` com
    ``ValueError: 'text_line' must have fragments if 'text_line.text_width' is
    None``, o que transformava contrato sem gestor em erro 500 no relatório.
    """
    manager = getattr(contract, "contractor_manager", None)

    name = manager.name if manager and manager.name else NOT_INFORMED

    document = document_mask(str(manager.cnpj)) if manager and manager.cnpj else None
    document = document or f"CNPJ: {NOT_INFORMED}"

    organization = getattr(contract, "organization", None)
    position = getattr(organization, "position", None) if organization else None
    position = position or NOT_INFORMED

    return name, position, document
