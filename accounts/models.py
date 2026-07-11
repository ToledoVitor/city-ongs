from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from easy_tenants import get_current_tenant, tenant_context
from easy_tenants.models import TenantAwareAbstract, TenantManager
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

from utils.choices import MonthChoices
from utils.fields import LowerCaseEmailField
from utils.managers import TenantManagerAllObjects
from utils.models import BaseModel
from utils.validators import validate_cnpj, validate_cpf, validate_cpf_cnpj


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
    audesp_municipality_code = models.PositiveIntegerField(
        verbose_name="Código do Município (AUDESP)",
        null=True,
        blank=True,
        help_text="Código do município no Sistema Audesp, conforme planilha em tce.sp.gov.br/audesp/coletor",
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
    audesp_entity_code = models.PositiveIntegerField(
        verbose_name="Código da Entidade (AUDESP)",
        null=True,
        blank=True,
        help_text="Código da entidade no Sistema Audesp — identifica o órgão responsável pela prestação de contas ao TCESP",
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
        null=True,
        blank=True,
    )
    cnpj = models.CharField(
        verbose_name="CNPJ",
        max_length=18,
        validators=[validate_cnpj],
        help_text="Número do CNPJ do usuário. Deve ser único dentro da organização.",
        null=True,
        blank=True,
    )
    phone_number = PhoneNumberField(
        region="BR",
        help_text="Número de telefone pessoal no formato brasileiro (ex: +55 11 99999-9999)",
        null=True,
        blank=True,
    )

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
    deactivated_at = models.DateTimeField(
        verbose_name="Data de Desativação",
        null=True,
        blank=True,
        help_text="Data em que o usuário foi desativado",
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

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["cpf"]),
            models.Index(fields=["cnpj"]),
            models.Index(fields=["access_level"]),
            models.Index(fields=["organization", "access_level"]),
            models.Index(fields=["password_expires_at"]),
        ]
        ordering = ["first_name", "last_name"]
        unique_together = [
            ("organization", "email"),
            ("organization", "cpf", "cnpj"),
        ]
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def clean(self):
        """Validate the user data."""
        # Check if email is unique within the organization
        if self.email:
            existing = User.objects.filter(email=self.email).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "Já existe um usuário com este email nesta organização"
                )

        # Check if document is unique within the organization
        if self.cpf or self.cnpj:
            existing = User.objects.filter(cpf=self.cpf, cnpj=self.cnpj).exclude(
                pk=self.pk
            )
            if existing.exists():
                raise ValidationError(
                    "Já existe um usuário com este documento nesta organização"
                )

        # Ensure user has either CPF or CNPJ, but not both
        if not self.cpf and not self.cnpj:
            raise ValidationError("O usuário deve ter um CPF ou CNPJ")
        if self.cpf and self.cnpj:
            raise ValidationError("O usuário não pode ter CPF e CNPJ simultaneamente")

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
        if self.cnpj is not None:
            string_doc = "".join([i for i in str(self.cnpj) if i.isdigit()])
            self.cnpj = str(string_doc)
        super().save(*args, **kwargs)

    @property
    def document(self) -> str:
        if self.cpf:
            return str(self.cpf)
        if self.cnpj:
            return str(self.cnpj)
        return ""

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
    def can_add_new_organization_committees(self) -> bool:
        """Check if user can add new organization committees."""
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
    def can_update_accountability(self) -> bool:
        """Check if user can update accountability."""
        return not self.is_committee_member and (
            self.is_superuser
            or self.access_level
            in {
                self.AccessChoices.CIVIL_SERVANT,
            }
        )

    @property
    def can_review_accountability(self) -> bool:
        """Check if user can review accountability."""
        return not self.is_committee_member and (
            self.is_superuser
            or self.access_level
            in {
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

    def __str__(self) -> str:
        return str(self.name)


class OrganizationDocument(OrganizationTenantBaseClass):
    DOCUMENT_TYPES = [
        ("balance", "Balanço Patrimonial"),
        ("dre", "Demonstrativo do Resultado do Exercício"),
        ("statute", "Estatuto Social"),
        ("other", "Outro"),
    ]

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        verbose_name="Tipo de Documento",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Título",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )
    file = models.FileField(
        upload_to="organization_documents/%Y/%m/",
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "xls", "xlsx"])],
        verbose_name="Arquivo",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Visível no portal da transparência",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Upload",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização",
    )
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="Enviado por"
    )

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Documento da Organização"
        verbose_name_plural = "Documentos da Organização"

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.organization.name}"


class Employee(BaseOrganizationTenantModel):
    """AUDESP manual §5 "Relação de Empregados da Entidade Beneficiária".

    Scoped to the organization (not to a single Contract/ajuste): an employee's
    admissão/demissão/salário aren't tied to one ajuste, and the same employee may
    be reported across several ajustes' prestações de contas.
    """

    cpf = models.CharField(
        verbose_name="CPF",
        max_length=16,
        validators=[validate_cpf],
    )
    admission_date = models.DateField(verbose_name="Data de Admissão")
    termination_date = models.DateField(
        verbose_name="Data de Demissão",
        null=True,
        blank=True,
    )
    cbo = models.CharField(
        verbose_name="CBO",
        max_length=16,
        help_text="Código Brasileiro de Ocupação. Para estagiários, usar o código equivalente à função exercida.",
    )
    cns = models.CharField(
        verbose_name="CNS",
        max_length=15,
        null=True,
        blank=True,
        help_text="Cartão Nacional de Saúde — obrigatório quando o CBO corresponde a médico (subgrupo 225)",
    )
    contractual_salary = models.DecimalField(
        verbose_name="Salário Contratual",
        decimal_places=2,
        max_digits=12,
        help_text="Situação no início do exercício",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Empregado"
        verbose_name_plural = "Empregados"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("organization", "cpf", "admission_date"),
                name="unique_employee_per_organization",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cpf} - {self.organization.name}"


class EmployeeRemunerationPeriod(BaseOrganizationTenantModel):
    employee = models.ForeignKey(
        Employee,
        verbose_name="Empregado",
        related_name="remuneration_periods",
        on_delete=models.CASCADE,
    )
    year = models.IntegerField(verbose_name="Ano")
    month = models.IntegerField(verbose_name="Mês", choices=MonthChoices)
    hours_worked = models.DecimalField(
        verbose_name="Carga Horária",
        decimal_places=2,
        max_digits=6,
    )
    gross_remuneration = models.DecimalField(
        verbose_name="Remuneração Bruta",
        decimal_places=2,
        max_digits=12,
    )

    class Meta:
        verbose_name = "Remuneração Mensal de Empregado"
        verbose_name_plural = "Remunerações Mensais de Empregados"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("employee", "year", "month"),
                name="unique_employee_remuneration_period",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.employee.cpf} - {self.month}/{self.year}"


class CededServant(BaseOrganizationTenantModel):
    """AUDESP manual §13 "Relação de Servidores Cedidos pelo Órgão Concessor".

    Does not apply to prestações de contas of Termo de Colaboração / Termo de Fomento
    (enforced by the AUDESP JSON builder, not at the DB level).
    """

    class PaymentBurdenChoices(models.IntegerChoices):
        GRANTING_AGENCY = 1, "Órgão Concessor"
        BENEFICIARY_ENTITY = 2, "Entidade Beneficiada"
        BOTH = 3, "Ambos"

    cpf = models.CharField(
        verbose_name="CPF",
        max_length=16,
        validators=[validate_cpf],
    )
    cession_start_date = models.DateField(verbose_name="Data Inicial da Cessão")
    cession_end_date = models.DateField(
        verbose_name="Data Final da Cessão",
        null=True,
        blank=True,
    )
    public_position_held = models.CharField(
        verbose_name="Cargo Público Ocupado",
        max_length=128,
    )
    role_performed = models.CharField(
        verbose_name="Função Desempenhada na Entidade Beneficiária",
        max_length=128,
    )
    payment_burden = models.PositiveSmallIntegerField(
        verbose_name="Ônus do Pagamento",
        choices=PaymentBurdenChoices,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Servidor Cedido"
        verbose_name_plural = "Servidores Cedidos"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("organization", "cpf", "cession_start_date"),
                name="unique_ceded_servant_per_organization",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cpf} - {self.organization.name}"

    @property
    def payment_burden_label(self) -> str:
        return CededServant.PaymentBurdenChoices(self.payment_burden).label


class CededServantRemunerationPeriod(BaseOrganizationTenantModel):
    servant = models.ForeignKey(
        CededServant,
        verbose_name="Servidor Cedido",
        related_name="remuneration_periods",
        on_delete=models.CASCADE,
    )
    year = models.IntegerField(verbose_name="Ano")
    month = models.IntegerField(verbose_name="Mês", choices=MonthChoices)
    hours_worked = models.DecimalField(
        verbose_name="Carga Horária",
        decimal_places=2,
        max_digits=6,
    )
    gross_remuneration = models.DecimalField(
        verbose_name="Remuneração Bruta",
        decimal_places=2,
        max_digits=12,
    )

    class Meta:
        verbose_name = "Remuneração Mensal de Servidor Cedido"
        verbose_name_plural = "Remunerações Mensais de Servidores Cedidos"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("servant", "year", "month"),
                name="unique_ceded_servant_remuneration_period",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.servant.cpf} - {self.month}/{self.year}"
