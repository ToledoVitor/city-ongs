import re


def password_is_valid(password: str) -> bool:
    regex = r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,16}$"

    if re.fullmatch(regex, password):
        return True
    return False
