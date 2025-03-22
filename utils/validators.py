from django.core.exceptions import ValidationError


def validate_cpf(value):
    """Validate CPF format and check digit.

    Args:
        value: The CPF value to validate.

    Raises:
        ValidationError: If the CPF is invalid.
    """
    if not value:
        return

    # Remove non-digits
    cpf = "".join(filter(str.isdigit, value))

    if len(cpf) != 11:
        raise ValidationError("CPF deve ter exatamente 11 dígitos")

    # Check for known invalid CPFs
    if cpf in [
        "00000000000",
        "11111111111",
        "22222222222",
        "33333333333",
        "44444444444",
        "55555555555",
        "66666666666",
        "77777777777",
        "88888888888",
        "99999999999",
    ]:
        raise ValidationError("CPF inválido")

    # Validate first check digit
    sum = 0
    for i in range(9):
        sum += int(cpf[i]) * (10 - i)
    digit = 11 - (sum % 11)
    if digit > 9:
        digit = 0
    if digit != int(cpf[9]):
        raise ValidationError("CPF inválido")

    # Validate second check digit
    sum = 0
    for i in range(10):
        sum += int(cpf[i]) * (11 - i)
    digit = 11 - (sum % 11)
    if digit > 9:
        digit = 0
    if digit != int(cpf[10]):
        raise ValidationError("CPF inválido")


def validate_cnpj(value):
    """Validate CNPJ format and check digit.

    Args:
        value: The CNPJ value to validate.

    Raises:
        ValidationError: If the CNPJ is invalid.
    """
    if not value:
        return

    # Remove non-digits
    cnpj = "".join(filter(str.isdigit, value))

    if len(cnpj) != 14:
        raise ValidationError("CNPJ deve ter exatamente 14 dígitos")

    # Check for known invalid CNPJs
    if cnpj in [
        "00000000000000",
        "11111111111111",
        "22222222222222",
        "33333333333333",
        "44444444444444",
        "55555555555555",
        "66666666666666",
        "77777777777777",
        "88888888888888",
        "99999999999999",
    ]:
        raise ValidationError("CNPJ inválido")

    # Validate first check digit
    sum = 0
    weight = 5
    for i in range(12):
        sum += int(cnpj[i]) * weight
        weight = weight - 1 if weight > 2 else 9
    digit = 11 - (sum % 11)
    if digit > 9:
        digit = 0
    if digit != int(cnpj[12]):
        raise ValidationError("CNPJ inválido")

    # Validate second check digit
    sum = 0
    weight = 6
    for i in range(13):
        sum += int(cnpj[i]) * weight
        weight = weight - 1 if weight > 2 else 9
    digit = 11 - (sum % 11)
    if digit > 9:
        digit = 0
    if digit != int(cnpj[13]):
        raise ValidationError("CNPJ inválido")


def validate_cpf_cnpj(value):
    """Validate CPF or CNPJ format and check digit.

    This validator will check if the value is either a valid CPF (11 digits)
    or a valid CNPJ (14 digits).

    Args:
        value: The CPF or CNPJ value to validate.

    Raises:
        ValidationError: If the value is neither a valid CPF nor a valid CNPJ.
    """
    if not value:
        return

    # Remove non-digits
    doc = "".join(filter(str.isdigit, value))

    if len(doc) == 11:
        validate_cpf(doc)
    elif len(doc) == 14:
        validate_cnpj(doc)
    else:
        raise ValidationError(
            "Documento deve ser um CPF (11 dígitos) ou CNPJ (14 dígitos)"
        )
