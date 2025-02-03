import re


def password_is_valid(password: str) -> bool:
    regex = r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*()-_=+]{8,}$"

    if re.match(regex, password):
        return True
    return False
