import re
from datetime import date, datetime
from decimal import Decimal

from utils.choices import MonthChoices


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


def get_month_range(start_date: date | None, end_date: date | None):
    if not start_date or not end_date:
        return []

    months = []
    year, month = start_date.year, start_date.month

    while (year, month) <= (end_date.year, end_date.month):
        months.append((month, year))
        month += 1
        if month > 12:
            year += 1
            month = 1

    return months
