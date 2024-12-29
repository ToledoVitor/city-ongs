from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords

from utils.fields import LowerCaseEmailField
from utils.models import BaseModel


class User(AbstractUser):
    class AccessChoices(models.TextChoices):
        MASTER = "MASTER", "master"
        # SOBE CONTRATOS
        CIVIL_SERVANT = "CIVIL_SERVANT", "Funcionário público"
        # REVISA E ETC
        FOLDER_MANAGER = "FOLDER_MANAGER", "Gestor da pasta"
        # SOBEM DOCUMENTAÇÃo
        ONG_ACCOUNTANT = "ONG_ACCOUNTANT", "Contador / funcionário da ong"

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
    access_level = models.CharField(
        verbose_name="Nível de Acesso",
        choices=AccessChoices,
        default=AccessChoices.ONG_ACCOUNTANT,
        max_length=14,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    @property
    def has_admin_access(self) -> bool:
        return self.is_superuser or self.access_level in {
            self.AccessChoices.MASTER,
            self.AccessChoices.CIVIL_SERVANT,
        }

    @property
    def can_add_new_folder_managers(self) -> bool:
        return self.is_superuser or self.access_level in {
            self.AccessChoices.MASTER,
            self.AccessChoices.CIVIL_SERVANT,
        }

    @property
    def can_add_new_ong_accountants(self) -> bool:
        return self.is_superuser or self.access_level in {
            self.AccessChoices.MASTER,
            self.AccessChoices.CIVIL_SERVANT,
        }

    @property
    def city_hall(self) -> str:
        # TODO: return user city hall
        return "Prefeitura teste prefeitopolis"

    def __str__(self) -> str:
        return f"{super().__str__()} {self.email}"


class Area(BaseModel):
    name = models.CharField(verbose_name="Nome", max_length=128)
    users = models.ManyToManyField(
        User,
        related_name="areas",
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Ong - {self.name}"

    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Areas"


class Ong(BaseModel):
    name = models.CharField(verbose_name="Nome", max_length=128)

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Ong - {self.name}"

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

    def __str__(self) -> str:
        return f"Relação {self.ong.name} - {self.user.email}"

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

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Prefeitura"
        verbose_name_plural = "Prefeituras"
