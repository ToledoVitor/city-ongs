"""Shared shapes reused across ajuste-type builders — one function per
recurring pattern from the AUDESP Fase V manual (v1.18), so each builder
composes these instead of re-deriving the same JSON shape independently."""

from decimal import Decimal


def serialize_date(value):
    """AUDESP dates are ISO strings (YYYY-MM-DD)."""
    if value is None:
        return None
    return value.isoformat()


def serialize_money(value):
    """AUDESP monetary fields are JSON numbers with 2 decimal places."""
    if value is None:
        return None
    return float(Decimal(value).quantize(Decimal("0.01")))


def serialize_agency(value):
    """AUDESP's "agencia" fields are integers (e.g. 1), while our
    `BankAccount.agency`/similar fields are free-text strings that may carry
    leading zeros (e.g. "0001") — cast to strip them."""
    if value is None or value == "":
        return None
    return int(value)


def serialize_creditor(document_type, document_number, name=None):
    """Manual §7/§8/§9/§12/§16 "credor" triple.

    `name` is only required by AUDESP when document_type is RNE, but we
    include it whenever present since the manual's rules only make it
    conditionally *mandatory*, never forbidden.
    """
    data = {
        "documento_tipo": document_type,
        "documento_numero": document_number,
    }
    if name:
        data["nome"] = name
    return data


def serialize_publications(publications):
    """Manual §22.1 "publicacoes" shape, shared by §22/23/28/29/30.

    `publications` is any iterable of PublicationBase-derived instances.
    """
    result = []
    for publication in publications:
        entry = {
            "tipo_veiculo_publicacao": publication.publication_vehicle_type,
        }
        if publication.vehicle_name:
            entry["nome_veiculo"] = publication.vehicle_name
        entry["data_publicacao"] = serialize_date(publication.publication_date)
        if publication.website_url:
            entry["endereco_internet"] = publication.website_url
        result.append(entry)
    return result
