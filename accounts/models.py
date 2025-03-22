from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

from utils.fields import LowerCaseEmailField
from utils.models import BaseModel


class CityHall(BaseModel):
    name = models.CharField(verbose_name="Prefeitura", max_length=128)
    mayor = models.CharField(
        verbose_name="Prefeito",
        max_length=256,
    )
    document = models.CharField(
        verbose_name="Documento",
        max_length=32,
    )

    position = models.CharField(
        verbose_name="cargo",
        max_length=150,
        null=True,
        blank=True,
    )

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

    owner = models.CharField(
        verbose_name="Presidente",
        max_length=256,
        null=True,
        blank=True,
    )
    document = models.CharField(
        verbose_name="Documento",
        max_length=32,
        null=True,
        blank=True,
    )

    position = models.CharField(
        verbose_name="cargo",
        max_length=150,
        null=True,
        blank=True,
    )

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
    organization = models.ForeignKey(
        Organization,
        verbose_name="Organização",
        related_name="areas",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.name} | {self.organization.name}"

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
    cpf = models.CharField(
        verbose_name="Cpf",
        max_length=16,
    )
    phone_number = PhoneNumberField(
        region="BR",
        help_text="Telefone pessoal do usuário",
        null=True,
        blank=True,
    )

    password_expires_at = models.DateTimeField(
        null=True,
        default=None,
        blank=True,
    )
    password_redefined = models.BooleanField(
        verbose_name="Senha Redefinida",
        help_text="Usuário já mudou a senha inicial?",
        default=False,
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
    position = models.CharField(
        verbose_name="cargo",
        max_length=150,
        null=True,
        blank=True,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    @property
    def masked_phone(self) -> str:
        if not self.phone_number:
            return ""
        return self.phone_number.as_national

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

    @property
    def unread_notifications(self):
        return self.notifications.filter(read_at__isnull=True).count()

    @property
    def last_actions(self):
        return

    def save(self, *args, **kwargs):
        if self.cpf is not None:
            string_doc = "".join([i for i in str(self.cpf) if i.isdigit()])
            self.cpf = str(string_doc)

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.get_full_name()} -  {self.email}"
