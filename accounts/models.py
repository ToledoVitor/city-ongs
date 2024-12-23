from django.db import models
from django.contrib.auth.models import AbstractUser

from utils.fields import LowerCaseEmailField


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=False,
        null=True,
        blank=True,
    )
    email = LowerCaseEmailField(unique=True)
    password_expires_at = models.DateTimeField(
        null=True,
        default=None,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        return f"{super().__str__()} {self.email}"
