from decimal import Decimal


def format_into_brazilian_currency(value: Decimal | None):
    if not value:
        return "R$ 0,00"

    return (
        f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
