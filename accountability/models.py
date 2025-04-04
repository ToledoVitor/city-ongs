from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Q, Sum
from django.forms.models import model_to_dict
from simple_history.models import HistoricalRecords

from accounts.models import BaseOrganizationTenantModel, User
from activity.models import ActivityLog
from bank.models import BankAccount
from contracts.choices import NatureChoices
from contracts.models import Contract, ContractItem
from utils.cache_invalidation import (
    CacheInvalidationMixin,
    invalidate_accountability_cache,
)
from utils.choices import MonthChoices, StatusChoices
from utils.mixins import CacheableModelMixin
from utils.validators import validate_cpf_cnpj


class Accountability(
    CacheInvalidationMixin,
    BaseOrganizationTenantModel,
    CacheableModelMixin,
):
    class ReviewStatus(models.TextChoices):
        WIP = "WIP", "Em Andamento"
        SENT = "SENT", "Enviada para análise"
        CORRECTING = "CORRECTING", "Corrigindo"
        FINISHED = "FINISHED", "Finalizada"

    month = models.IntegerField(
        verbose_name="Mês",
        choices=MonthChoices,
        default=MonthChoices.JAN,
    )
    year = models.IntegerField(
        verbose_name="Ano",
        default=0,
    )

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="accountabilities",
        on_delete=models.CASCADE,
    )
    pendencies = models.CharField(
        verbose_name="Pendências",
        max_length=255,
        null=True,
        blank=True,
    )

    status = models.CharField(
        verbose_name="Status",
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
        max_length=22,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.contract.name} - {self.month}/{self.year}"

    @property
    def month_label(self):
        return MonthChoices(self.month).label.capitalize()

    @property
    def is_on_execution(self) -> bool:
        return self.status in {
            Accountability.ReviewStatus.WIP,
            Accountability.ReviewStatus.CORRECTING,
        }

    @property
    def is_sent(self) -> bool:
        return self.status == Accountability.ReviewStatus.SENT

    @property
    def is_finished(self) -> bool:
        return self.status == Accountability.ReviewStatus.FINISHED

    @property
    def status_label(self) -> str:
        return Accountability.ReviewStatus(self.status).label

    @property
    def recent_logs(self):
        """Get recent activity logs for this accountability and related records."""
        # Get IDs from reverse relationships properly
        revenue_ids = [
            str(id) for id in self.revenues.values_list("id", flat=True)[:10]
        ]
        expense_ids = [
            str(id) for id in self.expenses.values_list("id", flat=True)[:10]
        ]

        return (
            ActivityLog.objects.filter(
                Q(target_object_id=str(self.id))
                | Q(target_object_id__in=revenue_ids)
                | Q(target_object_id__in=expense_ids)
            )
            .select_related("user")
            .distinct()
            .order_by("-created_at")[:10]
        )

    def invalidate_cache(self):
        """
        Invalidate all cache related to this accountability.
        """
        # Access organization_id from BaseOrganizationTenantModel
        invalidate_accountability_cache(self.id, self.organization.id)

    def to_cacheable_dict(self, full=False):
        """
        Convert model instance to a dictionary safe for caching.
        Args:
            full (bool): If True, include all relationships for detail view.
                        If False, only include basic data for list view.
        """
        if not full:
            # Light version for contract page
            return {
                "id": self.id,
                "month": self.month,
                "year": self.year,
                "month_label": self.month_label,
                "status": self.status,
                "status_label": self.status_label,
                "count_revenues": self.revenues.filter(deleted_at__isnull=True).count(),
                "count_expenses": self.expenses.filter(deleted_at__isnull=True).count(),
            }

        # Full version for detail page
        data = super().to_cacheable_dict()

        # Add computed properties
        data.update(
            {
                "month_label": self.month_label,
                "is_on_execution": self.is_on_execution,
                "is_sent": self.is_sent,
                "is_finished": self.is_finished,
                "status_label": self.status_label,
            }
        )

        # Handle related objects for detail view
        if hasattr(self, "revenues"):
            data["revenues"] = [
                revenue.to_cacheable_dict()
                for revenue in self.revenues.filter(deleted_at__isnull=True)[:10]
            ]

        if hasattr(self, "expenses"):
            data["expenses"] = [
                expense.to_cacheable_dict()
                for expense in self.expenses.filter(deleted_at__isnull=True)[:10]
            ]

        if hasattr(self, "files"):
            data["files"] = [
                file.to_cacheable_dict()
                for file in self.files.filter(deleted_at__isnull=True)[:10]
            ]

        return data

    class Meta:
        verbose_name = "Prestação de Contas"
        verbose_name_plural = "Prestações de Contas"
        unique_together = ("contract", "month", "year")


class AccountabilityFile(
    BaseOrganizationTenantModel,
    CacheableModelMixin,
    CacheInvalidationMixin,
):
    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Prestação",
        related_name="files",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        User,
        verbose_name="Criado por",
        related_name="accountability_files",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/accountabilities/",
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name="Nome do Arquivo",
        max_length=128,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Arquivo de Prestação {self.id}"

    def invalidate_cache(self):
        """
        Invalidate all cache related to this file.
        """
        if self.accountability_id:
            invalidate_accountability_cache(self.accountability_id)

    def to_cacheable_dict(self):
        """
        Convert model instance to a dictionary safe for caching.
        Override to handle file field.
        """
        data = model_to_dict(self)
        data.update(
            {
                "id": self.id,
                "name": self.name,
                "file_url": self.file.url if self.file else None,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "created_by": {
                    "id": self.created_by.id,
                    "name": self.created_by.get_full_name()
                    if self.created_by
                    else None,
                }
                if self.created_by
                else None,
            }
        )
        return data

    class Meta:
        verbose_name = "Arquivo de Prestação"
        verbose_name_plural = "Arquivo de Prestações"


class Favored(BaseOrganizationTenantModel):
    """Model representing a person or entity that receives payments or benefits."""

    name = models.CharField(
        verbose_name="Nome",
        max_length=128,
    )
    document = models.CharField(
        verbose_name="CPF/CNPJ",
        null=True,
        blank=True,
        validators=[validate_cpf_cnpj],
        help_text="CPF ou CNPJ do favorecido",
    )

    def __str__(self) -> str:
        return str(self.name)

    def clean(self):
        """Validate the favored data."""
        if self.document:
            # Check if document is unique within the organization
            existing = Favored.objects.filter(
                document=self.document, organization=self.organization
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "Já existe um favorecido com este documento nesta organização"
                )

    def save(self, *args, **kwargs):
        """Save the favored after validation."""
        self.clean()
        if self.document is not None:
            string_doc = "".join([i for i in str(self.document) if i.isdigit()])
            self.document = str(string_doc)
        super().save(*args, **kwargs)

    def get_total_cost(self):
        """Calculate the total cost of this beneficiary across all contracts."""
        return (
            self.expenses.filter(deleted_at__isnull=True).aggregate(total=Sum("value"))[
                "total"
            ]
            or 0
        )

    def get_cost_by_contract(self, contract):
        """Calculate the cost of this beneficiary for a specific contract."""
        return (
            self.expenses.filter(
                deleted_at__isnull=True, accountability__contract=contract
            ).aggregate(total=Sum("value"))["total"]
            or 0
        )

    def get_cost_by_municipality(self, city_hall):
        """Calculate the cost of this beneficiary for a specific municipality."""
        return (
            self.expenses.filter(
                deleted_at__isnull=True,
                accountability__contract__area__city_hall=city_hall,
            ).aggregate(total=Sum("value"))["total"]
            or 0
        )

    def get_contracts(self):
        """Get all contracts this beneficiary is involved with."""
        return (
            self.expenses.filter(deleted_at__isnull=True)
            .values(
                "accountability__contract__id",
                "accountability__contract__name",
                "accountability__contract__area__city_hall__name",
            )
            .annotate(total_cost=Sum("value"), expense_count=Count("id"))
            .order_by("-total_cost")
        )

    class Meta:
        verbose_name = "Favorecido"
        verbose_name_plural = "Favorecidos"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("organization", "document"),
                name="unique_favored_document_per_organization",
            ),
        ]


class ResourceSource(BaseOrganizationTenantModel):
    class OriginChoices(models.TextChoices):
        FEDERAL = "FEDERAL", "Federal"
        STATE = "STATE", "Estadual"
        MUNICIPAL = "MUNICIPAL", "Municipal"
        COUNTERPART_PARTNER = (
            "COUNTERPART_PARTNER",
            "Contrapartida de parceiro",
        )
        PRIVATE_SPONSOR = "PRIVATE_SPONSOR", "Patrocinador privado"
        PARLIAMENTARY = "PARLIAMENTARY", "Emenda Parlamentar"

    class CategoryChoices(models.TextChoices):
        NOT_APPLIABLE = "NOT_APPLIABLE", "Não Aplicavél"
        COOPERATION_AGREEMENT = "COOPERATION_AGREEMENT", "Acordo de Cooperação"
        AGREEMENT = "AGREEMENT", "Convênio"
        COLLABORATION_AGREEMENT = (
            "COLLABORATION_AGREEMENT",
            "Termo de Colaboração",
        )
        PROMOTION_AGREEMENT = "PROMOTION_AGREEMENT", "Termo de Fomento"
        DONATION_AGREEMENT = "DONATION_AGREEMENT", "Contrato de Doação"
        MANAGEMENT_AGREEMENT = "MANAGEMENT_AGREEMENT", "Contrato de Gestão"
        TRANSFER_AGREEMENT = "TRANSFER_AGREEMENT", "Contrato de Repasse"
        PARTNERSHIP_AGREEMENT = "PARTNERSHIP_AGREEMENT", "Termo de Parceria"

    name = models.CharField(
        verbose_name="Nome",
        max_length=128,
    )
    document = models.CharField(
        verbose_name="CPF/CNPJ",
        null=True,
        blank=True,
        validators=[validate_cpf_cnpj],
        help_text="CPF ou CNPJ da fonte de recursos",
    )
    contract_number = models.CharField(
        verbose_name="Número do contrato",
        max_length=32,
        null=True,
        blank=True,
    )

    origin = models.CharField(
        verbose_name="Origem",
        choices=OriginChoices,
        default=OriginChoices.MUNICIPAL,
        max_length=19,
    )
    category = models.CharField(
        verbose_name="Categoria",
        choices=CategoryChoices,
        default=CategoryChoices.NOT_APPLIABLE,
        max_length=23,
    )

    def __str__(self) -> str:
        return str(self.name)

    def clean(self):
        """Validate the resource source data."""
        if self.document:
            # Check if document is unique within the organization
            existing = ResourceSource.objects.filter(
                document=self.document, organization=self.organization
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "Já existe uma fonte com este documento nesta organização"
                )

    def save(self, *args, **kwargs):
        """Save the resource source after validation."""
        self.clean()
        if self.document is not None:
            string_doc = "".join([i for i in str(self.document) if i.isdigit()])
            self.document = str(string_doc)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Fonte de Recursos"
        verbose_name_plural = "Fontes de Recursos"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("organization", "document"),
                name="unique_resource_source_document_per_organization",
            ),
        ]

    @property
    def origin_label(self) -> str:
        return ResourceSource.OriginChoices(self.origin).label

    @property
    def category_label(self) -> str:
        return ResourceSource.CategoryChoices(self.category).label


class Expense(BaseOrganizationTenantModel, CacheableModelMixin):
    class ReviewStatus(models.TextChoices):
        IN_ANALISIS = "IN_ANALISIS", "Em Análise"
        REJECTED = "REJECTED", "Rejeitada"
        APPROVED = "APPROVED", "Aprovada"

    class LiquidationChoices(models.TextChoices):
        BILL = "BILL", "Boleto"
        CHECK = "CHECK", "Cheque"
        DEBIT_CREDIT_CARD = "DEBIT_CREDIT_CARD", "Cartão Débito/Crédito"
        DIRECT_DEBIT = "DIRECT_DEBIT", "Débito em Conta"
        ELETRONIC_TRANSFER = "ELETRONIC_TRANSFER", "Transferência Eletrônica"
        MONEY = "MONEY", "Dinheiro"
        OBTV = "OBTV", "OBTV"

    class DocumentChoices(models.TextChoices):
        INSURANCE_POLICY = "INSURANCE_POLICY", "Apolice de Seguro"
        DEBIT_NOTICE = "DEBIT_NOTICE", "Aviso de Débito"
        PAY_SLIP = "PAY_SLIP", "Boleto"
        TAX_RECEIPT = "TAX_RECEIPT", "Cupom Fiscal"
        DARF = "DARF", "DARF"
        INVOICE = "INVOICE", "Fatura"
        GPS = "GPS", "GPS"
        GRCS_DOC = "GRCS_DOC", "GRCS ou DOC"
        GRF = "GRF", "GRF"
        GRRF = "GRRF", "GRRF"
        PAYSLIP = "PAYSLIP", "Holerite"
        NF = "NF", "NF"
        NFE = "NFE", "NF-E"
        NFS = "NFS", "NFS"
        NFSE = "NFSE", "NFS-E"
        NF_INVOICES = (
            "NF_INVOICES",
            "Notas Fiscais (Eletronica, Serviços, etc)",
        )
        OTHERS = "OTHERS", "Outros"
        RECEIPT = "RECEIPT", "Recibo"
        VACATION_RECEIPT = "VACATION_RECEIPT", "Recibo de Férias"
        RPA = "RPA", "RPA"
        TERMINATION_AGREEMENT = "TERMINATION_AGREEMENT", "Termo de Rescisão"

    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Prestação",
        related_name="expenses",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus.choices,
        default=ReviewStatus.IN_ANALISIS,
        max_length=11,
    )
    pendencies = models.CharField(
        verbose_name="Pendências",
        max_length=255,
        null=True,
        blank=True,
    )

    # flags
    paid = models.BooleanField(verbose_name="Pago?", default=False)
    conciled = models.BooleanField(verbose_name="Conciliado?", default=False)
    planned = models.BooleanField(verbose_name="Planejado?", default=True)

    # specifications
    identification = models.CharField(
        verbose_name="Identificação da Despesa",
        max_length=128,
    )
    observations = models.CharField(
        verbose_name="Observações",
        max_length=256,
        null=True,
        blank=True,
    )
    value = models.DecimalField(
        verbose_name="Valor da Despesa",
        decimal_places=2,
        max_digits=12,
    )

    # relations
    source = models.ForeignKey(
        ResourceSource,
        verbose_name="Fonte de Despesa",
        related_name="expenses",
        on_delete=models.CASCADE,
    )
    favored = models.ForeignKey(
        Favored,
        verbose_name="Favorecido",
        related_name="expenses",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    item = models.ForeignKey(
        ContractItem,
        verbose_name="Item Relacionado",
        related_name="expenses",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    nature = models.CharField(
        verbose_name="Natureza da Despesa",
        choices=NatureChoices.choices,
        max_length=34,
        null=True,
        blank=True,
    )

    # dates
    due_date = models.DateField(
        verbose_name="Vencimento",
        null=True,
        blank=True,
    )
    competency = models.DateField(
        verbose_name="Competência",
    )
    liquidation = models.DateField(
        verbose_name="Liquidação",
        null=True,
        blank=True,
    )
    liquidation_form = models.CharField(
        verbose_name="Forma de Liquidação",
        choices=LiquidationChoices.choices,
        default=LiquidationChoices.ELETRONIC_TRANSFER,
        max_length=18,
    )
    conciled_at = models.DateTimeField(
        verbose_name="Data de Liquidação",
        null=True,
        blank=True,
    )

    # documents
    document_type = models.CharField(
        verbose_name="Tipo de Documento",
        choices=DocumentChoices.choices,
        max_length=21,
        null=True,
        blank=True,
    )
    document_number = models.CharField(
        verbose_name="Número do documento",
        max_length=64,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"

    @property
    def nature_label(self) -> str:
        if self.nature:
            return NatureChoices(self.nature).label
        return "-"

    @property
    def status_label(self) -> str:
        return Expense.ReviewStatus(self.status).label

    @property
    def is_rejected(self) -> str:
        return self.status == Expense.ReviewStatus.REJECTED

    @property
    def document_type_label(self) -> str:
        if self.document_type:
            return Expense.DocumentChoices(self.document_type).label
        return "-"

    @property
    def liquidation_form_label(self) -> str:
        if self.liquidation_form:
            return Expense.LiquidationChoices(self.liquidation_form).label
        return ""

    def __str__(self) -> str:
        return f"Despesa {self.id}"

    def to_cacheable_dict(self):
        """Convert model instance to a dictionary safe for caching."""
        # Exclude file-related fields and foreign keys that might have files
        exclude_fields = ["files"]

        # Get base data excluding file fields
        data = model_to_dict(self, exclude=exclude_fields)

        # Add computed properties
        data.update(
            {
                "nature_label": self.nature_label,
                "status_label": self.status_label,
                "is_rejected": self.is_rejected,
                "document_type_label": self.document_type_label,
                "liquidation_form_label": self.liquidation_form_label,
            }
        )

        # Handle related objects carefully
        if hasattr(self, "source"):
            data["source_name"] = self.source.name if self.source else None

        if hasattr(self, "favored"):
            data["favored_name"] = self.favored.name if self.favored else None

        if hasattr(self, "item"):
            data["item_name"] = self.item.name if self.item else None

        # Handle files separately - only store minimal file info
        if hasattr(self, "files"):
            data["files"] = [
                {
                    "id": file.id,
                    "name": file.name,
                    "file_url": file.file.url if file.file else None,
                }
                for file in self.files.filter(deleted_at__isnull=True)
            ]

        return data


class Revenue(BaseOrganizationTenantModel, CacheableModelMixin):
    """Model representing revenue entries in the system."""

    class RevenueSource(models.TextChoices):
        CITY_HALL = "CITY_HALL", "Prefeitura"
        COUNTERPART = "COUNTERPART", "Contrapartida"

    class ReviewStatus(models.TextChoices):
        IN_ANALISIS = "IN_ANALISIS", "Em Análise"
        REJECTED = "REJECTED", "Rejeitada"
        APPROVED = "APPROVED", "Aprovada"

    class Nature(models.TextChoices):
        UNDUE_CREDIT = "UNDUE_CREDIT", "Crédito Indevido"
        BANK_DEPOSIT = "BANK_DEPOSIT", "Depósito Bancário"
        RETURN_DEPOSIT = (
            "RETURN_DEPOSIT",
            "Depósito para devolução ao Órgão Concedente",
        )
        PAYMENT_REVERSAL = "PAYMENT_REVERSAL", "Estorno de Pagamento"
        FEE_REVERSAL = "FEE_REVERSAL", "Estorno de Tarifas"
        OTHER_REVENUES = (
            "OTHER_REVENUES",
            "Outras Receitas decorrentes da execução do ajuste",
        )
        OWN_RESOURCES = "OWN_RESOURCES", "Recurso próprio da entidade parceira"
        REIMBURSEMENT_INTEREST = (
            "REIMBURSEMENT_INTEREST",
            "Reembolso de Juros, multas, glosas, pagto. Indevido, duplicidade etc",
        )
        FEE_REIMBURSEMENT = "FEE_REIMBURSEMENT", "Reembolso de Tarifas"
        INVESTMENT_INCOME = "INVESTMENT_INCOME", "Rendimento de Aplicação"
        SAVINGS_INCOME = "SAVINGS_INCOME", "Rendimento de Poupança"
        PUBLIC_TRANSFER = "PUBLIC_TRANSFER", "Repasse Público"
        PREVIOUS_BALANCE = "PREVIOUS_BALANCE", "Saldo anterior para acerto"

    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Contabilidade",
        related_name="revenues",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus.choices,
        default=ReviewStatus.IN_ANALISIS,
        max_length=11,
    )
    pendencies = models.CharField(
        verbose_name="Pendências",
        max_length=255,
        null=True,
        blank=True,
    )

    # flags
    paid = models.BooleanField(verbose_name="Pago?", default=False)
    conciled = models.BooleanField(verbose_name="Conciliado?", default=False)
    conciled_at = models.DateTimeField(
        verbose_name="Data de Liquidação",
        null=True,
        blank=True,
    )

    # specifications
    identification = models.CharField(
        verbose_name="Identificação da Despesa",
        max_length=128,
    )
    observations = models.CharField(
        verbose_name="Observações",
        max_length=256,
        null=True,
        blank=True,
    )
    value = models.DecimalField(
        verbose_name="Valor da Despesa",
        decimal_places=2,
        max_digits=12,
    )

    # dates
    competency = models.DateField(
        verbose_name="Competência",
    )
    receive_date = models.DateField(
        verbose_name="Data de Recebimento",
        null=True,
        blank=True,
    )

    source = models.CharField(
        verbose_name="Fonte de Recurso",
        choices=RevenueSource.choices,
        default=RevenueSource.CITY_HALL,
    )
    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="Conta Bancária Destino",
        related_name="revenues",
        on_delete=models.CASCADE,
    )
    revenue_nature = models.CharField(
        verbose_name="Natureza da Receita",
        choices=Nature.choices,
        default=Nature.BANK_DEPOSIT,
        max_length=22,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Receita {self.identification}"

    @property
    def source_label(self) -> str:
        return Revenue.RevenueSource(self.source).label

    @property
    def status_label(self) -> str:
        return Revenue.ReviewStatus(self.status).label

    @property
    def is_rejected(self) -> str:
        return self.status == Revenue.ReviewStatus.REJECTED

    @property
    def revenue_nature_label(self) -> str:
        if self.revenue_nature:
            return Revenue.Nature(self.revenue_nature).label
        return "-"

    def to_cacheable_dict(self):
        """Convert model instance to a dictionary safe for caching."""
        data = model_to_dict(self, exclude=["files"])

        # Add computed properties
        data.update(
            {
                "source_label": self.source_label,
                "status_label": self.status_label,
                "is_rejected": self.is_rejected,
                "revenue_nature_label": self.revenue_nature_label,
            }
        )

        # Handle files
        if hasattr(self, "files"):
            data["files"] = [
                {
                    "id": file.id,
                    "name": file.name,
                    "file_url": file.file.url if file.file else None,
                }
                for file in self.files.filter(deleted_at__isnull=True)
            ]

        return data

    class Meta:
        verbose_name = "Receita"
        verbose_name_plural = "Receitas"


class ExpenseFile(
    BaseOrganizationTenantModel,
    CacheableModelMixin,
    CacheInvalidationMixin,
):
    expense = models.ForeignKey(
        Expense,
        verbose_name="Despesa",
        related_name="files",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        User,
        verbose_name="Criado por",
        related_name="expense_files",
        on_delete=models.PROTECT,
    )

    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/expenses/",
    )
    name = models.CharField(
        verbose_name="Nome do Arquivo",
        max_length=128,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Arquivo de Despesa {self.id}"

    def invalidate_cache(self):
        """
        Invalidate all cache related to this file.
        """
        if self.expense_id:
            expense = self.expense
            if expense and expense.accountability_id:
                invalidate_accountability_cache(expense.accountability_id)

    def to_cacheable_dict(self):
        """
        Convert model instance to a dictionary safe for caching.
        Override to handle file field.
        """
        data = model_to_dict(self)
        data.update(
            {
                "id": self.id,
                "name": self.name,
                "file_url": self.file.url if self.file else None,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "created_by": {
                    "id": self.created_by.id,
                    "name": self.created_by.get_full_name()
                    if self.created_by
                    else None,
                }
                if self.created_by
                else None,
            }
        )
        return data

    class Meta:
        verbose_name = "Arquivo de Despesa"
        verbose_name_plural = "Arquivo de Despesas"


class RevenueFile(
    BaseOrganizationTenantModel,
    CacheableModelMixin,
    CacheInvalidationMixin,
):
    revenue = models.ForeignKey(
        Revenue,
        verbose_name="Recurso",
        related_name="files",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        User,
        verbose_name="Criado por",
        related_name="revenue_files",
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        verbose_name="Nome do Arquivo",
        max_length=128,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/revenues/",
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Arquivo de Receita {self.id}"

    def invalidate_cache(self):
        """
        Invalidate all cache related to this file.
        """
        if self.revenue_id:
            revenue = self.revenue
            if revenue and revenue.accountability_id:
                invalidate_accountability_cache(revenue.accountability_id)

    def to_cacheable_dict(self):
        """
        Convert model instance to a dictionary safe for caching.
        Override to handle file field.
        """
        data = model_to_dict(self)
        data.update(
            {
                "id": self.id,
                "name": self.name,
                "file_url": self.file.url if self.file else None,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "created_by": {
                    "id": self.created_by.id,
                    "name": self.created_by.get_full_name()
                    if self.created_by
                    else None,
                }
                if self.created_by
                else None,
            }
        )
        return data

    class Meta:
        verbose_name = "Arquivo de Receita"
        verbose_name_plural = "Arquivo de Receitas"
