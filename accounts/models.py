from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords

from utils.fields import LowerCaseEmailField
from utils.models import BaseModel


class CityHall(BaseModel):
    name = models.CharField(verbose_name="Prefeitura", max_length=128)

    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Prefeitura"
        verbose_name_plural = "Prefeituras"


class Organization(BaseModel):
    city_hall = models.ForeignKey(
        CityHall,
        verbose_name="Prefeitura",
        related_name="organizations",
        on_delete=models.CASCADE,
    )
    name = models.CharField(verbose_name="Nome", max_length=128)

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Organização - {self.name}"

    class Meta:
        verbose_name = "Organização"
        verbose_name_plural = "Organizações"


class Area(BaseModel):
    name = models.CharField(verbose_name="Nome", max_length=128)
    description = models.CharField(
        verbose_name="Descrição",
        max_length=128,
        blank=True,
        null=True,
    )
    city_hall = models.ForeignKey(
        CityHall,
        verbose_name="Prefeitura",
        related_name="areas",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Areas"


class User(AbstractUser):
    class AccessChoices(models.TextChoices):
        MASTER = "MASTER", "master"
        # SOBE CONTRATOS
        CIVIL_SERVANT = "CIVIL_SERVANT", "Funcionário público"  # administrador
        # REVISA E ETC
        FOLDER_MANAGER = (
            "FOLDER_MANAGER",
            "Gestor da pasta",
        )  # Gestor da pasta / Proprietáio da Pasta
        # SOBEM DOCUMENTAÇÃo
        ORGANIZATION_ACCOUNTANT = (
            "ORGANIZATION_ACCOUNTANT",
            "Contador / funcionário da organização",
        )  # usuário final

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
        default=AccessChoices.ORGANIZATION_ACCOUNTANT,
        max_length=23,
    )

    areas = models.ManyToManyField(
        Area,
        related_name="users",
    )
    organization = models.ForeignKey(
        Organization,
        verbose_name="organization",
        related_name="users",
        on_delete=models.CASCADE,
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
    def can_add_new_organization_accountants(self) -> bool:
        return self.is_superuser or self.access_level in {
            self.AccessChoices.MASTER,
            self.AccessChoices.CIVIL_SERVANT,
        }

    @property
    def can_change_statuses(self) -> bool:
        return self.is_superuser or self.access_level in {
            self.AccessChoices.MASTER,
            self.AccessChoices.FOLDER_MANAGER,
        }

    def __str__(self) -> str:
        return f"{super().__str__()} {self.email}"
