from django import template


register = template.Library()


@register.simple_tag
def zip_months(months, revenues, expenses, transfers):
    if not all(
        isinstance(lst, list)
        for lst in [months, revenues, expenses, transfers]
    ):
        return []

    return list(zip(months, revenues, expenses, transfers))


@register.filter
def div(value, divisor):
    try:
        return value / divisor if divisor else 0
    except (TypeError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, factor):
    try:
        return value * factor
    except (TypeError, ValueError):
        return 0


@register.filter
def brazilian_month(month):
    return {
        "January": "Janeiro",
        "February": "Fevereiro",
        "March": "Março",
        "April": "Abril",
        "May": "Maio",
        "June": "Junho",
        "July": "Julho",
        "August": "Agosto",
        "September": "Setembro",
        "October": "Outubro",
        "November": "Novembro",
        "December": "Dezembro",
    }[month]


@register.filter
def replace_comma(value):
    """Replace comma with period in a number string."""
    if isinstance(value, str):
        return value.replace(',', '.')
    return value
