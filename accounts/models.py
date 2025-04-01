from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from easy_tenants import get_current_tenant, tenant_context
from easy_tenants.models import TenantAwareAbstract, TenantManager
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

from utils.fields import LowerCaseEmailField
from utils.managers import TenantManagerAllObjects
from utils.models import BaseModel
from utils.validators import validate_cpf, validate_cpf_cnpj


class CityHall(BaseModel):
    """Model representing a city hall with its basic information."""

    name = models.CharField(verbose_name="Prefeitura", max_length=128)
    mayor = models.CharField(
        verbose_name="Prefeito",
        max_length=256,
    )
    document = models.CharField(
        verbose_name="Documento",
        max_length=32,
        validators=[validate_cpf_cnpj],
        help_text="CPF ou CNPJ da prefeitura",
    )

    position = models.CharField(
        verbose_name="cargo",
        max_length=150,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def clean(self):
        """Validate the city hall data."""
        if self.document:
            # Check if document is unique
            existing = CityHall.objects.filter(document=self.document).exclude(
                pk=self.pk
            )
            if existing.exists():
                raise ValidationError("Já existe uma prefeitura com este documento")

    def save(self, *args, **kwargs):
        """Save the city hall after validation."""
        self.clean()
        if self.document is not None:
            string_doc = "".join([i for i in str(self.document) if i.isdigit()])
            self.document = str(string_doc)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        verbose_name = "Prefeitura"
        verbose_name_plural = "Prefeituras"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("document",),
                name="unique_cityhall_document",
            ),
        ]


class Organization(BaseModel):
    """Model representing an organization associated with a city hall."""

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
        validators=[validate_cpf_cnpj],
        help_text="CPF ou CNPJ da organização",
    )

    position = models.CharField(
        verbose_name="cargo",
        max_length=150,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def clean(self):
        """Validate the organization data."""
        if self.document:
            # Check if document is unique within the city hall
            existing = Organization.objects.filter(
                document=self.document, city_hall=self.city_hall
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "Já existe uma organização com este documento nesta prefeitura"
                )

    def save(self, *args, **kwargs):
        """Save the organization after validation."""
        self.clean()
        if self.document is not None:
            string_doc = "".join([i for i in str(self.document) if i.isdigit()])
            self.document = str(string_doc)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return str(f"{self.name} | {self.city_hall.name}")

    class Meta:
        verbose_name = "Organização"
        verbose_name_plural = "Organizações"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("city_hall", "document"),
                name="unique_organization_document_per_cityhall",
            ),
        ]


class OrganizationTenantBaseClass(BaseModel, TenantAwareAbstract):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        help_text="The organization associated with this tenant.",
        related_name="%(app_label)s_%(class)s_related",
        null=True,
        blank=True,
    )

    objects = TenantManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Set tenant field on save"""
        if get_current_tenant():
            return super().save(*args, **kwargs)

        with tenant_context(self.organization):
            super().save(*args, **kwargs)


class BaseOrganizationTenantModel(OrganizationTenantBaseClass, BaseModel):
    objects = TenantManager()
    all_objects = TenantManagerAllObjects()

    class Meta:
        abstract = True


class Area(BaseModel):
    """Model representing an area within an organization."""

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
        return str(f"{self.name} | {self.organization.name}")

    class Meta:
        verbose_name = "Area"
        verbose_name_plural = "Areas"


class User(AbstractUser):
    class AccessChoices(models.TextChoices):
        MASTER = "MASTER", "Master"
        CIVIL_SERVANT = "CIVIL_SERVANT", "Funcionário público"
        FOLDER_MANAGER = "FOLDER_MANAGER", "Gestor da pasta"
        ORGANIZATION_ACCOUNTANT = (
            "ORGANIZATION_ACCOUNTANT",
            "Contador / funcionário da organização",
        )
        COMMITTEE_MEMBER = "COMMITTEE_MEMBER", "Membro do comitê"

    username = models.CharField(
        max_length=150,
        unique=False,
        null=True,
        blank=True,
        help_text="Nome de usuário opcional. Se não fornecido, o email será usado.",
    )
    email = LowerCaseEmailField(
        unique=True,
        help_text="Endereço de email do usuário. Será usado para login e notificações.",
    )
    cpf = models.CharField(
        verbose_name="CPF",
        max_length=16,
        validators=[validate_cpf],
        help_text="Número do CPF do usuário. Deve ser único dentro da organização.",
    )
    phone_number = PhoneNumberField(
        region="BR",
        help_text="Número de telefone pessoal no formato brasileiro (ex: +55 11 99999-9999)",
        null=True,
        blank=True,
    )  # type: PhoneNumberField

    password_expires_at = models.DateTimeField(
        verbose_name="Data de Expiração da Senha",
        null=True,
        blank=True,
        help_text="Data em que a senha do usuário expira",
    )
    password_redefined = models.BooleanField(
        verbose_name="Senha Redefinida",
        help_text="Indica se o usuário já alterou sua senha inicial",
        default=False,
    )
    access_level = models.CharField(
        verbose_name="Nível de Acesso",
        choices=AccessChoices,
        default=AccessChoices.ORGANIZATION_ACCOUNTANT,
        max_length=23,
        help_text="Nível de acesso do usuário no sistema. Define suas permissões.",
    )

    areas = models.ManyToManyField(
        Area,
        related_name="users",
        help_text="Áreas dentro da organização que este usuário tem acesso",
    )
    organization = models.ForeignKey(
        Organization,
        verbose_name="organization",
        related_name="users",
        on_delete=models.CASCADE,
        help_text="A organização à qual este usuário pertence",
    )
    position = models.CharField(
        verbose_name="cargo",
        max_length=150,
        null=True,
        blank=True,
        help_text="Cargo ou função do usuário na organização",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["cpf"]),
            models.Index(fields=["access_level"]),
            models.Index(fields=["organization", "access_level"]),
            models.Index(fields=["password_expires_at"]),
        ]
        ordering = ["first_name", "last_name"]
        unique_together = [
            ("organization", "email"),
            ("organization", "cpf"),
        ]

    def clean(self):
        """Validate the user data."""
        # Check if email is unique within the organization
        if self.email:
            existing = User.objects.filter(
                email=self.email, organization=self.organization
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "Já existe um usuário com este email nesta organização"
                )

        # Check if CPF is unique within the organization
        if self.cpf:
            existing = User.objects.filter(
                cpf=self.cpf, organization=self.organization
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "Já existe um usuário com este CPF nesta organização"
                )

        # Validate password expiration
        if self.password_expires_at and self.password_expires_at < timezone.now():
            raise ValidationError(
                "A data de expiração da senha não pode estar no passado"
            )

    def save(self, *args, **kwargs):
        """Save the user after validation."""
        self.clean()
        if self.cpf is not None:
            string_doc = "".join([i for i in str(self.cpf) if i.isdigit()])
            self.cpf = str(string_doc)
        super().save(*args, **kwargs)

    @property
    def masked_phone(self) -> str:
        if not self.phone_number:
            return ""
        return self.phone_number.as_national  # type: ignore

    @property
    def has_admin_access(self) -> bool:
        """Check if user has administrative access."""
        return self.is_superuser or self.access_level in {
            self.AccessChoices.MASTER,
            self.AccessChoices.CIVIL_SERVANT,
        }

    @property
    def is_committee_member(self) -> bool:
        """Check if user is a committee member."""
        return self.access_level == self.AccessChoices.COMMITTEE_MEMBER

    @property
    def has_read_only_access(self) -> bool:
        """Check if user has read-only access (committee member or admin)."""
        return self.access_level == self.AccessChoices.COMMITTEE_MEMBER

    @property
    def can_add_new_folder_managers(self) -> bool:
        """Check if user can add new folder managers."""
        return not self.is_committee_member and (
            self.is_superuser
            or self.access_level
            in {
                self.AccessChoices.MASTER,
                self.AccessChoices.CIVIL_SERVANT,
            }
        )

    @property
    def can_add_new_organization_accountants(self) -> bool:
        """Check if user can add new organization accountants."""
        return not self.is_committee_member and (
            self.is_superuser
            or self.access_level
            in {
                self.AccessChoices.MASTER,
                self.AccessChoices.CIVIL_SERVANT,
            }
        )

    @property
    def can_change_statuses(self) -> bool:
        """Check if user can change statuses."""
        return not self.is_committee_member and (
            self.is_superuser
            or self.access_level
            in {
                self.AccessChoices.MASTER,
                self.AccessChoices.FOLDER_MANAGER,
            }
        )

    @property
    def unread_notifications(self):
        return self.notifications.filter(read_at__isnull=True).count()

    def __str__(self) -> str:
        return f"{self.get_full_name()} -  {self.email}"


class Committee(OrganizationTenantBaseClass):
    """Model representing a committee with its members."""

    name = models.CharField(verbose_name="Nome do Comitê", max_length=128)
    city_hall = models.ForeignKey(
        CityHall,
        verbose_name="Prefeitura",
        related_name="committees",
        on_delete=models.CASCADE,
    )
    members = models.ManyToManyField(
        User,
        verbose_name="Membros",
        related_name="committees",
        blank=True,
    )

    class Meta:
        verbose_name = "Comitê"
        verbose_name_plural = "Comitês"
