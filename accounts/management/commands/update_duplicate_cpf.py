import random

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User


def generate_valid_cpf():
    """Generate a valid CPF number."""
    # Generate first 9 digits
    cpf = [random.randint(0, 9) for _ in range(9)]

    # Calculate first check digit
    sum = 0
    for i in range(9):
        sum += cpf[i] * (10 - i)
    digit = 11 - (sum % 11)
    if digit > 9:
        digit = 0
    cpf.append(digit)

    # Calculate second check digit
    sum = 0
    for i in range(10):
        sum += cpf[i] * (11 - i)
    digit = 11 - (sum % 11)
    if digit > 9:
        digit = 0
    cpf.append(digit)

    return "".join(map(str, cpf))


class Command(BaseCommand):
    help = "Updates a duplicate CPF to a new valid one"

    def add_arguments(self, parser):
        parser.add_argument(
            "organization_id", type=str, help="Organization ID"
        )
        parser.add_argument("cpf", type=str, help="CPF to update")

    def handle(self, *args, **options):
        organization_id = options["organization_id"]
        cpf = options["cpf"]

        # Find users with the duplicate CPF
        users = User.objects.filter(organization_id=organization_id, cpf=cpf)

        if not users.exists():
            msg = (
                f"No users found with CPF {cpf} "
                f"in organization {organization_id}"
            )
            self.stdout.write(self.style.ERROR(msg))
            return

        if users.count() == 1:
            msg = f"Only one user found with CPF {cpf}. No duplicate found."
            self.stdout.write(self.style.WARNING(msg))
            return

        # Keep the first user's CPF and update the others
        first_user = users.first()
        users_to_update = users.exclude(id=first_user.id)

        with transaction.atomic():
            for user in users_to_update:
                new_cpf = generate_valid_cpf()
                user.cpf = new_cpf
                user.save()
                msg = (
                    f"Updated CPF for user {user.email} "
                    f"from {cpf} to {new_cpf}"
                )
                self.stdout.write(self.style.SUCCESS(msg))
