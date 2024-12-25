from django.db import models
from django.contrib.auth.models import AbstractUser

from utils.fields import LowerCaseEmailField
from utils.models import BaseModel
from simple_history.models import HistoricalRecords


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


class Ong(BaseModel):
    name = models.CharField(verbose_name="Nome", max_length=128)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Ong"
        verbose_name_plural = "Ongs"


class UserOngRelatioship(BaseModel):
    user = models.ForeignKey(
        User,
        verbose_name="Usuário",
        related_name="user_ong_relationships",
        on_delete=models.CASCADE,
    )

    ong = models.ForeignKey(
        Ong,
        verbose_name="Ong",
        related_name="user_ong_relationships",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Relação Ong-Usuário"
        verbose_name_plural = "Relações Ong-Usuário"


class CityHall(BaseModel):
    name = models.CharField(verbose_name="Prefeitura", max_length=128)
    users = models.ManyToManyField(
        User,
        verbose_name="Usuários",
        related_name="city_halls",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Prefeitura"
        verbose_name_plural = "Prefeituras"
