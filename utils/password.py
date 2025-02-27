import secrets
import string


def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters) for _ in range(length))
