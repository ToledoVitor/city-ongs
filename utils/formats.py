import re
from datetime import datetime
from decimal import Decimal


def format_into_brazilian_currency(value: Decimal | None):
    if not value:
        return "R$ 0,00"

    return (
        f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )


def document_mask(document: str | None):
    if not document:
        return None

    document = re.sub(r"\D", "", document)

    if len(document) == 11:  # CPF
        return f"CPF: ***.***.{document[6:9]}-{document[9:]}**"
    elif len(document) == 14:  # CNPJ
        return f"CNPJ: **.{document[2:5]}.{document[5:8]}/{document[8:12]}-**"
    else:
        return f"DOC: {document}"


def format_into_brazilian_date(date: datetime | None):
    if not date:
        return ""

    day = f"{date.day:02d}"
    month = f"{date.month:02d}"
    year = date.year

    return f"{day}/{month}/{year}"
