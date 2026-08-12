from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Q, Sum
from simple_history.models import HistoricalRecords

from accounts.models import BaseOrganizationTenantModel, User
from activity.models import ActivityLog
from bank.models import BankAccount
from contracts.choices import (
    AudespDocumentTypeChoices,
    AudespExpenseCategoryTypeChoices,
    AudespFundingSourceTypeChoices,
    AudespPublicationVehicleChoices,
    NatureChoices,
)
from contracts.models import Contract, ContractItem
from utils.choices import MonthChoices
from utils.validators import validate_cpf, validate_cpf_cnpj


class Accountability(
    BaseOrganizationTenantModel,
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
        max_length=1024,
        null=True,
        blank=True,
    )

    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus.choices,
        default=ReviewStatus.WIP,
        max_length=22,
    )
    reviewer = models.ForeignKey(
        User,
        verbose_name="Responsável pela Análise",
        related_name="accountability_reviews",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    committee_member = models.ForeignKey(
        User,
        verbose_name="Membro do Comitê para Notificação",
        related_name="accountability_notifications",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Membro do comitê que será notificado quando a prestação for aprovada",
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

    class Meta:
        verbose_name = "Prestação de Contas"
        verbose_name_plural = "Prestações de Contas"
        unique_together = ("contract", "month", "year")


class AccountabilityFile(
    BaseOrganizationTenantModel,
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
        max_length=255,
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
        max_length=255,
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


class Expense(BaseOrganizationTenantModel):
    class ReviewStatus(models.TextChoices):
        IN_ANALISIS = "IN_ANALISIS", "Em Análise"
        UPDATED = "UPDATED", "Atualizada"
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
        max_length=1024,
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
        max_length=512,
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

    # AUDESP - Documento Fiscal (manual §8) e Pagamento (manual §9)
    creditor_document_type = models.PositiveSmallIntegerField(
        verbose_name="Tipo do Documento do Credor",
        choices=AudespDocumentTypeChoices,
        null=True,
        blank=True,
    )
    issuing_state = models.PositiveSmallIntegerField(
        verbose_name="Estado Emissor do Documento Fiscal",
        null=True,
        blank=True,
        help_text="Código AUDESP (1-27) — tabela de referência pendente",
    )
    expense_category_type = models.PositiveSmallIntegerField(
        verbose_name="Categoria de Despesas (AUDESP)",
        choices=AudespExpenseCategoryTypeChoices,
        null=True,
        blank=True,
        help_text="Quando o documento tiver mais de uma categoria, informar a de maior valor",
    )
    encumbrance_value = models.DecimalField(
        verbose_name="Valor de Encargos Retidos",
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text="Deve ser informado como zero quando não houver retenção",
    )
    from_apportionment = models.BooleanField(
        verbose_name="Proveniente de Rateio?",
        default=False,
    )
    apportionment_percentage = models.DecimalField(
        verbose_name="Percentual de Rateio",
        decimal_places=2,
        max_digits=5,
        null=True,
        blank=True,
    )
    funding_source_type = models.PositiveSmallIntegerField(
        verbose_name="Fonte de Recurso (AUDESP)",
        choices=AudespFundingSourceTypeChoices,
        null=True,
        blank=True,
    )
    payment_method_type = models.PositiveSmallIntegerField(
        verbose_name="Meio de Pagamento (AUDESP)",
        choices=[(1, "Banco"), (2, "Fundo Fixo")],
        null=True,
        blank=True,
    )
    transaction_number = models.CharField(
        verbose_name="Número da Transação",
        max_length=40,
        null=True,
        blank=True,
        help_text="Para pagamento de Folha Ordinária, pode ser informado como 9999",
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
    def is_approved(self) -> str:
        return self.status == Expense.ReviewStatus.APPROVED

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


class Revenue(BaseOrganizationTenantModel):
    """Model representing revenue entries in the system."""

    class RevenueSource(models.TextChoices):
        CITY_HALL = "CITY_HALL", "Prefeitura"
        COUNTERPART = "COUNTERPART", "Contrapartida"

    class ReviewStatus(models.TextChoices):
        IN_ANALISIS = "IN_ANALISIS", "Em Análise"
        UPDATED = "UPDATED", "Atualizada"
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
        max_length=255,
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
    funding_source_type = models.PositiveSmallIntegerField(
        verbose_name="Fonte de Recurso (AUDESP)",
        choices=AudespFundingSourceTypeChoices,
        null=True,
        blank=True,
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
    def is_approved(self) -> str:
        return self.status == Revenue.ReviewStatus.APPROVED

    @property
    def is_rejected(self) -> str:
        return self.status == Revenue.ReviewStatus.REJECTED

    @property
    def revenue_nature_label(self) -> str:
        if self.revenue_nature:
            return Revenue.Nature(self.revenue_nature).label
        return "-"

    class Meta:
        verbose_name = "Receita"
        verbose_name_plural = "Receitas"


class ExpenseFile(BaseOrganizationTenantModel):
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

    class Meta:
        verbose_name = "Arquivo de Despesa"
        verbose_name_plural = "Arquivo de Despesas"


class RevenueFile(BaseOrganizationTenantModel):
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

    class Meta:
        verbose_name = "Arquivo de Receita"
        verbose_name_plural = "Arquivo de Receitas"


# =============================================================================
# AUDESP Fase V - annual submission envelope and its blocks.
#
# `AnnualStatement` is the (contract, exercicio) anchor: one row per ajuste per
# year, matching AUDESP's own unit of submission (one JSON document per
# descritor.ano). Blocks that are inherently annual (§20-§33 minus employees/
# bens, which are event-dated and stay contract-scoped like Empenho/Repasse/
# Glosa/Desconto/Devolucao below) hang off this header instead of repeating
# (contract, exercicio) on every table.
# =============================================================================


class AnnualStatement(BaseOrganizationTenantModel):
    """AUDESP manual §32 "Prestação de Contas da Entidade Beneficiária" + the
    (contract, fiscal_year) anchor shared by the annual-only blocks below."""

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="annual_statements",
        on_delete=models.CASCADE,
    )
    fiscal_year = models.IntegerField(verbose_name="Exercício")

    statement_date = models.DateField(
        verbose_name="Data da Prestação de Contas",
        null=True,
        blank=True,
        help_text="Data em que a entidade beneficiária concluiu sua prestação de contas do exercício",
    )
    reference_period_start_date = models.DateField(
        verbose_name="Início do Período de Referência",
        null=True,
        blank=True,
    )
    reference_period_end_date = models.DateField(
        verbose_name="Fim do Período de Referência",
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Prestação de Contas Anual (AUDESP)"
        verbose_name_plural = "Prestações de Contas Anuais (AUDESP)"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("contract", "fiscal_year"),
                name="unique_annual_statement_per_contract_fiscal_year",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.contract.name} - {self.fiscal_year}"


class PublicationBase(BaseOrganizationTenantModel):
    """Shared shape + validation rules for manual §22/23/28/29/30 publication lists."""

    publication_vehicle_type = models.PositiveSmallIntegerField(
        verbose_name="Veículo de Publicação",
        choices=AudespPublicationVehicleChoices,
    )
    vehicle_name = models.CharField(
        verbose_name="Nome do Veículo",
        max_length=128,
        null=True,
        blank=True,
        help_text="Obrigatório quando o veículo de publicação é Outros",
    )
    publication_date = models.DateField(verbose_name="Data da Publicação")
    website_url = models.URLField(
        verbose_name="Endereço na Internet",
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class PurchasingRegulation(BaseOrganizationTenantModel):
    """AUDESP manual §22 - Contrato de Gestão only."""

    annual_statement = models.OneToOneField(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="purchasing_regulation",
        on_delete=models.CASCADE,
    )
    had_initial_publication = models.BooleanField(
        verbose_name="Houve Publicação Inicial?",
        default=False,
    )
    was_regulation_amended = models.BooleanField(
        verbose_name="Houve Alteração do Regulamento?",
        null=True,
        blank=True,
    )
    had_amended_regulation_publication = models.BooleanField(
        verbose_name="Houve Publicação do Regulamento Alterado?",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Regulamento de Compras"
        verbose_name_plural = "Regulamentos de Compras"

    def __str__(self) -> str:
        return f"Regulamento de Compras - {self.annual_statement}"


class PurchasingRegulationPublication(PublicationBase):
    class PhaseChoices(models.TextChoices):
        INITIAL = "INITIAL", "Publicação Inicial"
        AMENDMENT = "AMENDMENT", "Publicação da Alteração"

    regulation = models.ForeignKey(
        PurchasingRegulation,
        verbose_name="Regulamento de Compras",
        related_name="publications",
        on_delete=models.CASCADE,
    )
    phase = models.CharField(
        verbose_name="Fase",
        max_length=9,
        choices=PhaseChoices,
    )

    class Meta:
        verbose_name = "Publicação do Regulamento de Compras"
        verbose_name_plural = "Publicações do Regulamento de Compras"


class PhysicalFinancialExecutionStatement(BaseOrganizationTenantModel):
    """AUDESP manual §23 - Termo de Parceria only."""

    annual_statement = models.OneToOneField(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="execution_statement",
        on_delete=models.CASCADE,
    )
    has_statement = models.BooleanField(
        verbose_name="Há Extrato de Execução Física e Financeira?",
        default=False,
    )
    statement_follows_template = models.BooleanField(
        verbose_name="Extrato Elaborado Conforme Modelo?",
        null=True,
        blank=True,
        help_text="Modelo do Anexo II do Decreto Federal nº 3.100/1999",
    )

    class Meta:
        verbose_name = "Extrato de Execução Física e Financeira"
        verbose_name_plural = "Extratos de Execução Física e Financeira"

    def __str__(self) -> str:
        return f"Extrato de Execução - {self.annual_statement}"


class PhysicalFinancialExecutionStatementPublication(PublicationBase):
    statement = models.ForeignKey(
        PhysicalFinancialExecutionStatement,
        verbose_name="Extrato de Execução",
        related_name="publications",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Publicação do Extrato de Execução"
        verbose_name_plural = "Publicações do Extrato de Execução"


class FinancialStatements(BaseOrganizationTenantModel):
    """AUDESP manual §28 - applies to all ajuste types."""

    annual_statement = models.OneToOneField(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="financial_statements",
        on_delete=models.CASCADE,
    )
    accountant_crc_number = models.CharField(
        verbose_name="Número do CRC do Responsável",
        max_length=16,
        null=True,
        blank=True,
    )
    accountant_cpf = models.CharField(
        verbose_name="CPF do Responsável",
        max_length=16,
        validators=[validate_cpf],
        null=True,
        blank=True,
    )
    accountant_crc_in_good_standing = models.BooleanField(
        verbose_name="Situação Regular no CRC?",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Demonstrações Contábeis"
        verbose_name_plural = "Demonstrações Contábeis"

    def __str__(self) -> str:
        return f"Demonstrações Contábeis - {self.annual_statement}"


class FinancialStatementsPublication(PublicationBase):
    financial_statement = models.ForeignKey(
        FinancialStatements,
        verbose_name="Demonstrações Contábeis",
        related_name="publications",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Publicação das Demonstrações Contábeis"
        verbose_name_plural = "Publicações das Demonstrações Contábeis"


class ActivityReportPublicationStatus(BaseOrganizationTenantModel):
    """AUDESP manual §30 - Contrato de Gestão only. NOT the relatório de
    atividades data itself (metas/programas, see contracts.ContractGoal) —
    this tracks whether/where that report was *published*."""

    annual_statement = models.OneToOneField(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="activity_report_publication_status",
        on_delete=models.CASCADE,
    )
    was_published_in_fiscal_year = models.BooleanField(
        verbose_name="Houve Publicação no Exercício?",
        default=False,
    )

    class Meta:
        verbose_name = "Publicação do Relatório de Atividades"
        verbose_name_plural = "Publicações do Relatório de Atividades"

    def __str__(self) -> str:
        return f"Publicação Relatório Atividades - {self.annual_statement}"


class ActivityReportPublication(PublicationBase):
    publication_status = models.ForeignKey(
        ActivityReportPublicationStatus,
        verbose_name="Publicação do Relatório de Atividades",
        related_name="publications",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Item de Publicação do Relatório de Atividades"
        verbose_name_plural = "Itens de Publicação do Relatório de Atividades"


class OpinionOrMinutes(BaseOrganizationTenantModel):
    """AUDESP manual §29 - required combination of types varies by ajuste type
    (enforced by the AUDESP JSON builder, not at the DB level)."""

    class TypeChoices(models.IntegerChoices):
        FISCAL_COUNCIL = 1, "Parecer ou Ata do Conselho Fiscal"
        BOARD_OF_DIRECTORS = 2, "Parecer ou Ata do Conselho de Administração"
        INDEPENDENT_AUDIT = 3, "Parecer da Auditoria Independente"
        PUBLIC_POLICY_COUNCIL = 4, "Parecer do Conselho de Políticas Públicas"

    class ConclusionChoices(models.IntegerChoices):
        UNQUALIFIED_FAVORABLE = 1, "Favorável sem Ressalvas"
        QUALIFIED_FAVORABLE = 2, "Favorável com Ressalvas"
        UNFAVORABLE = 3, "Desfavorável"
        ADVERSE = 4, "Adverso"
        DISCLAIMER_OF_OPINION = 5, "Com Abstenção de Opinião"

    annual_statement = models.ForeignKey(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="opinions_or_minutes",
        on_delete=models.CASCADE,
    )
    type = models.PositiveSmallIntegerField(
        verbose_name="Tipo da Ata ou Parecer",
        choices=TypeChoices,
    )
    was_published = models.BooleanField(
        verbose_name="Houve Publicação?",
        default=False,
    )
    conclusion = models.PositiveSmallIntegerField(
        verbose_name="Conclusão do Parecer",
        choices=ConclusionChoices,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Parecer ou Ata"
        verbose_name_plural = "Pareceres e Atas"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("annual_statement", "type"),
                name="unique_opinion_or_minutes_type_per_annual_statement",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_type_display()} - {self.annual_statement}"


class OpinionOrMinutesPublication(PublicationBase):
    opinion_or_minutes = models.ForeignKey(
        OpinionOrMinutes,
        verbose_name="Parecer ou Ata",
        related_name="publications",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Publicação de Parecer ou Ata"
        verbose_name_plural = "Publicações de Parecer ou Ata"


class EvaluationReport(BaseOrganizationTenantModel):
    """Unifies manual §25 (Comissão de Avaliação, Contrato de Gestão only),
    §26 (Governamental, Convênio only) and §27 (Monitoramento, Termo de
    Colaboração/Fomento only) — identical shape, mutually exclusive by ajuste
    type (enforced by the AUDESP JSON builder, not at the DB level)."""

    class TypeChoices(models.TextChoices):
        EVALUATION_COMMITTEE = (
            "EVALUATION_COMMITTEE",
            "Relatório da Comissão de Avaliação",
        )
        GOVERNMENT_EXECUTION_ANALYSIS = (
            "GOVERNMENT_EXECUTION_ANALYSIS",
            "Relatório Governamental da Análise da Execução",
        )
        MONITORING_AND_EVALUATION = (
            "MONITORING_AND_EVALUATION",
            "Relatório de Monitoramento e Avaliação",
        )

    class ConclusionChoices(models.IntegerChoices):
        UNQUALIFIED_FAVORABLE = 1, "Favorável sem Ressalvas"
        QUALIFIED_FAVORABLE = 2, "Favorável com Ressalvas"
        UNFAVORABLE = 3, "Desfavorável"

    annual_statement = models.ForeignKey(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="evaluation_reports",
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        verbose_name="Tipo de Relatório",
        max_length=30,
        choices=TypeChoices,
    )
    final_report_issued = models.BooleanField(
        verbose_name="Houve Emissão do Relatório Final?",
        default=False,
    )
    conclusion = models.PositiveSmallIntegerField(
        verbose_name="Conclusão do Relatório",
        choices=ConclusionChoices,
        null=True,
        blank=True,
    )
    justification = models.TextField(
        verbose_name="Justificativa",
        null=True,
        blank=True,
        help_text="Obrigatória quando a conclusão é Desfavorável",
    )

    class Meta:
        verbose_name = "Relatório de Avaliação"
        verbose_name_plural = "Relatórios de Avaliação"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("annual_statement", "type"),
                name="unique_evaluation_report_type_per_annual_statement",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_type_display()} - {self.annual_statement}"


class ConflictOfInterestDeclaration(BaseOrganizationTenantModel):
    """AUDESP manual §24 - conflict-of-interest declarations."""

    annual_statement = models.OneToOneField(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="conflict_of_interest_declaration",
        on_delete=models.CASCADE,
    )
    hired_related_companies = models.BooleanField(
        verbose_name="Houve Contratação de Empresas Pertencentes a Dirigentes?",
        default=False,
    )
    had_political_agents_in_board = models.BooleanField(
        verbose_name="Houve Participação de Agentes Políticos no Quadro Diretivo?",
        default=False,
    )
    purchases_comply_with_own_regulation = models.BooleanField(
        verbose_name="Compras/Contratações Adequadas ao Regulamento Próprio?",
        null=True,
        blank=True,
        help_text="Aplicável apenas a Contrato de Gestão e Termo de Parceria",
    )

    class Meta:
        verbose_name = "Declaração"
        verbose_name_plural = "Declarações"

    def __str__(self) -> str:
        return f"Declarações - {self.annual_statement}"


class RelatedCompany(BaseOrganizationTenantModel):
    declaration = models.ForeignKey(
        ConflictOfInterestDeclaration,
        verbose_name="Declaração",
        related_name="related_companies",
        on_delete=models.CASCADE,
    )
    cnpj = models.CharField(
        verbose_name="CNPJ da Empresa Contratada",
        max_length=18,
        validators=[validate_cpf_cnpj],
    )
    cpf = models.CharField(
        verbose_name="CPF do Dirigente/Agente Político",
        max_length=16,
        validators=[validate_cpf],
    )

    class Meta:
        verbose_name = "Empresa Pertencente"
        verbose_name_plural = "Empresas Pertencentes"


class BoardParticipation(BaseOrganizationTenantModel):
    declaration = models.ForeignKey(
        ConflictOfInterestDeclaration,
        verbose_name="Declaração",
        related_name="board_participations",
        on_delete=models.CASCADE,
    )
    officer_cpf = models.CharField(
        verbose_name="CPF do Dirigente/Agente Político",
        max_length=16,
        validators=[validate_cpf],
    )
    hired_cpfs = models.JSONField(
        verbose_name="CPFs dos Contratados",
        default=list,
        blank=True,
    )

    class Meta:
        verbose_name = "Participação no Quadro Diretivo"
        verbose_name_plural = "Participações no Quadro Diretivo"


class ConclusiveOpinion(BaseOrganizationTenantModel):
    """AUDESP manual §33."""

    class ConclusionChoices(models.IntegerChoices):
        FAVORABLE = 1, "Favorável"
        QUALIFIED_FAVORABLE = 2, "Favorável com Ressalvas"
        UNFAVORABLE = 3, "Desfavorável"

    annual_statement = models.OneToOneField(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="conclusive_opinion",
        on_delete=models.CASCADE,
    )
    opinion_identification = models.CharField(
        verbose_name="Identificação do Parecer",
        max_length=32,
        null=True,
        blank=True,
    )
    conclusion = models.PositiveSmallIntegerField(
        verbose_name="Conclusão do Parecer",
        choices=ConclusionChoices,
    )
    remarks = models.TextField(
        verbose_name="Considerações do Parecer",
        null=True,
        blank=True,
        help_text="Obrigatório quando a conclusão é Desfavorável",
    )

    class Meta:
        verbose_name = "Parecer Conclusivo"
        verbose_name_plural = "Pareceres Conclusivos"

    def __str__(self) -> str:
        return f"Parecer Conclusivo - {self.annual_statement}"


class ConclusiveOpinionDeclaration(BaseOrganizationTenantModel):
    class DeclarationTypeChoices(models.IntegerChoices):
        CLAUSE_COMPLIANCE = 1, "Cumprimento das Cláusulas"
        EXPENSE_REGULARITY = 2, "Regularidade dos Gastos"
        RECEIPT_IDENTIFICATION = 3, "Identificação nos Comprovantes"
        LABOR_CHARGES_REGULARITY = (
            4,
            "Regularidade dos Recolhimentos dos Encargos Trabalhistas",
        )
        PRINCIPLES_COMPLIANCE = 5, "Atendimento aos Princípios"
        SITE_VISIT_CONDUCTED = 6, "Realização de Visita"
        SANCTIONS_APPLIED = 7, "Aplicação de Sanções"

    class AnswerChoices(models.IntegerChoices):
        YES = 1, "Sim"
        NO = 2, "Não"
        NOT_APPLICABLE = 3, "Prejudicado"

    conclusive_opinion = models.ForeignKey(
        ConclusiveOpinion,
        verbose_name="Parecer Conclusivo",
        related_name="declarations",
        on_delete=models.CASCADE,
    )
    declaration_type = models.PositiveSmallIntegerField(
        verbose_name="Questionamento",
        choices=DeclarationTypeChoices,
    )
    answer = models.PositiveSmallIntegerField(
        verbose_name="Posicionamento",
        choices=AnswerChoices,
    )
    justification = models.TextField(
        verbose_name="Justificativa",
        null=True,
        blank=True,
        help_text="Obrigatória quando o posicionamento é Não ou Prejudicado (ou Sim, no caso de Aplicação de Sanções)",
    )

    class Meta:
        verbose_name = "Declaração do Parecer Conclusivo"
        verbose_name_plural = "Declarações do Parecer Conclusivo"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("conclusive_opinion", "declaration_type"),
                name="unique_conclusive_opinion_declaration_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_declaration_type_display()} - {self.get_answer_display()}"


class AvailableFunds(BaseOrganizationTenantModel):
    """AUDESP manual §10 - snapshot as of the final date of the exercício."""

    annual_statement = models.OneToOneField(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="available_funds",
        on_delete=models.CASCADE,
    )
    petty_cash_balance = models.DecimalField(
        verbose_name="Saldo do Fundo Fixo",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
    )

    class Meta:
        verbose_name = "Disponibilidade"
        verbose_name_plural = "Disponibilidades"

    def __str__(self) -> str:
        return f"Disponibilidade - {self.annual_statement}"


class BankBalance(BaseOrganizationTenantModel):
    class AccountTypeChoices(models.IntegerChoices):
        CHECKING = 1, "Conta Corrente"
        INVESTING = 2, "Investimento"

    available_funds = models.ForeignKey(
        AvailableFunds,
        verbose_name="Disponibilidade",
        related_name="balances",
        on_delete=models.CASCADE,
    )
    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="Conta Bancária",
        related_name="audesp_balances",
        on_delete=models.CASCADE,
    )
    account_type = models.PositiveSmallIntegerField(
        verbose_name="Tipo da Conta",
        choices=AccountTypeChoices,
    )
    bank_balance = models.DecimalField(
        verbose_name="Saldo Bancário",
        decimal_places=2,
        max_digits=12,
    )
    accounting_balance = models.DecimalField(
        verbose_name="Saldo Contábil",
        decimal_places=2,
        max_digits=12,
    )

    class Meta:
        verbose_name = "Saldo Bancário (AUDESP)"
        verbose_name_plural = "Saldos Bancários (AUDESP)"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("available_funds", "bank_account"),
                name="unique_bank_balance_per_bank_account",
            ),
        ]


# =============================================================================
# Financial ledger - contract-scoped (not tied to one exercício's
# AnnualStatement), since each entry carries its own date and gets filtered
# into whichever exercício's submission by that date, matching how AUDESP
# itself scopes these blocks.
# =============================================================================


class BudgetCommitment(BaseOrganizationTenantModel):
    """AUDESP manual §17 ("empenho")."""

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="budget_commitments",
        on_delete=models.CASCADE,
    )
    number = models.CharField(verbose_name="Número do Empenho", max_length=32)
    issue_date = models.DateField(verbose_name="Data de Emissão")
    economic_classification = models.CharField(
        verbose_name="Classificação Econômica",
        max_length=16,
    )
    funding_source_type = models.PositiveSmallIntegerField(
        verbose_name="Fonte de Recurso",
        choices=AudespFundingSourceTypeChoices,
    )
    value = models.DecimalField(
        verbose_name="Valor do Empenho",
        decimal_places=2,
        max_digits=12,
    )
    description = models.TextField(verbose_name="Histórico")
    spending_authority_cpf = models.CharField(
        verbose_name="CPF do Ordenador de Despesa",
        max_length=16,
        validators=[validate_cpf],
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Empenho"
        verbose_name_plural = "Empenhos"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("contract", "number", "issue_date"),
                name="unique_budget_commitment_per_agreement",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.number} - {self.contract.name}"


class FundTransfer(BaseOrganizationTenantModel):
    """AUDESP manual §18 ("repasse") - the actual transfer execution, linked to
    a BudgetCommitment.

    Distinct from `contracts.ContractMonthTransfer`, which is the upfront
    planning/budget split entered in the contract timeline UI, not an AUDESP
    concept and intentionally left untouched by this model.
    """

    class BankDocumentTypeChoices(models.IntegerChoices):
        BANK_ORDER = 1, "Ordem Bancária"
        OTHER = 2, "Outros"
        CHECK = 3, "Cheque"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="fund_transfers",
        on_delete=models.CASCADE,
    )
    budget_commitment = models.ForeignKey(
        BudgetCommitment,
        verbose_name="Empenho",
        related_name="fund_transfers",
        on_delete=models.PROTECT,
    )
    planned_date = models.DateField(verbose_name="Data Prevista")
    transfer_date = models.DateField(verbose_name="Data do Repasse")
    planned_value = models.DecimalField(
        verbose_name="Valor Previsto",
        decimal_places=2,
        max_digits=12,
    )
    transferred_value = models.DecimalField(
        verbose_name="Valor do Repasse",
        decimal_places=2,
        max_digits=12,
    )
    value_difference_justification = models.TextField(
        verbose_name="Justificativa da Diferença de Valor",
        null=True,
        blank=True,
        help_text="Obrigatória quando valor previsto difere do valor repassado",
    )
    bank_document_type = models.PositiveSmallIntegerField(
        verbose_name="Tipo do Documento Bancário",
        choices=BankDocumentTypeChoices,
    )
    other_description = models.CharField(
        verbose_name="Descrição de Outros Documentos",
        max_length=128,
        null=True,
        blank=True,
    )
    document_number = models.CharField(
        verbose_name="Número do Documento Bancário",
        max_length=32,
    )
    bank = models.PositiveIntegerField(
        verbose_name="Banco",
        help_text="Código do banco (tabela BACEN) — tabela de referência pendente",
    )
    bank_branch = models.CharField(verbose_name="Agência", max_length=16)
    account_number = models.CharField(verbose_name="Conta", max_length=16)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Repasse"
        verbose_name_plural = "Repasses"

    def __str__(self) -> str:
        return f"Repasse {self.transfer_date} - {self.transferred_value}"


class ExpenseRejection(BaseOrganizationTenantModel):
    """AUDESP manual §16 ("glosa") - every documento fiscal in `documentos_fiscais`
    (i.e. every `Expense` of the ajuste) must have an analysis here. Folha
    Ordinária payments have no linked Expense and are keyed by `payment_date`
    instead."""

    class AnalysisResultChoices(models.IntegerChoices):
        APPROVED = 1, "Aprovado"
        PARTIALLY_APPROVED = 2, "Aprovado Parcialmente"
        REJECTED = 3, "Reprovado"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="expense_rejections",
        on_delete=models.CASCADE,
    )
    expense = models.ForeignKey(
        Expense,
        verbose_name="Documento Fiscal (Despesa)",
        related_name="rejections",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Vazio apenas para análise de pagamento de Folha Ordinária",
    )
    payment_date = models.DateField(
        verbose_name="Data do Pagamento (Folha Ordinária)",
        null=True,
        blank=True,
        help_text="Exclusivo e obrigatório para análise de glosa de Folha Ordinária",
    )
    analysis_result = models.PositiveSmallIntegerField(
        verbose_name="Resultado da Análise",
        choices=AnalysisResultChoices,
    )
    rejected_value = models.DecimalField(
        verbose_name="Valor da Glosa",
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text="Obrigatório apenas quando o resultado é Aprovado Parcialmente",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Glosa"
        verbose_name_plural = "Glosas"

    def clean(self):
        if not self.expense_id and not self.payment_date:
            raise ValidationError(
                "Informe a despesa (documento fiscal) ou a data de pagamento da Folha Ordinária"
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        target = self.expense_id or self.payment_date
        return f"Glosa - {target}"


class Deduction(BaseOrganizationTenantModel):
    """AUDESP manual §14 ("desconto") - deduction applied to the repasse value
    for partial or total non-compliance with the plano de trabalho goals."""

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="deductions",
        on_delete=models.CASCADE,
    )
    date = models.DateField(verbose_name="Data")
    description = models.CharField(verbose_name="Descrição", max_length=256)
    value = models.DecimalField(
        verbose_name="Valor",
        decimal_places=2,
        max_digits=12,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Desconto"
        verbose_name_plural = "Descontos"

    def __str__(self) -> str:
        return f"{self.description} - {self.value}"


class Refund(BaseOrganizationTenantModel):
    """AUDESP manual §15 ("devolução")."""

    class NatureChoices(models.IntegerChoices):
        REJECTED_EXPENSE_REFUND_TO_SPECIFIC_ACCOUNT = (
            1,
            "Glosa devolvida à conta bancária específica do repasse público",
        )
        REJECTED_EXPENSE_REFUND_TO_GRANTOR_ACCOUNT = (
            2,
            "Glosa devolvida à conta bancária do órgão público",
        )
        UNUSED_FUNDS = 3, "Valor não aplicado"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="refunds",
        on_delete=models.CASCADE,
    )
    date = models.DateField(verbose_name="Data")
    nature = models.PositiveSmallIntegerField(
        verbose_name="Natureza da Devolução",
        choices=NatureChoices,
    )
    value = models.DecimalField(
        verbose_name="Valor",
        decimal_places=2,
        max_digits=12,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Devolução"
        verbose_name_plural = "Devoluções"

    def __str__(self) -> str:
        return f"{self.get_nature_display()} - {self.value}"


class BalanceAdjustment(BaseOrganizationTenantModel):
    """AUDESP manual §12 "Ajustes de Saldo" - unifies the 4 sub-blocks
    (retificação/inclusão of repasses and pagamentos) via `type`, since each
    is a small variation on the same shape rather than a distinct concept."""

    class TypeChoices(models.TextChoices):
        TRANSFER_CORRECTION = "TRANSFER_CORRECTION", "Retificação de Repasse"
        TRANSFER_INCLUSION = "TRANSFER_INCLUSION", "Inclusão de Repasse"
        PAYMENT_CORRECTION = "PAYMENT_CORRECTION", "Retificação de Pagamento"
        PAYMENT_INCLUSION = "PAYMENT_INCLUSION", "Inclusão de Pagamento"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="balance_adjustments",
        on_delete=models.CASCADE,
    )
    type = models.CharField(
        verbose_name="Tipo de Ajuste",
        max_length=19,
        choices=TypeChoices,
    )

    # Transfer-shaped fields (TRANSFER_CORRECTION / TRANSFER_INCLUSION)
    planned_date = models.DateField(
        verbose_name="Data Prevista",
        null=True,
        blank=True,
    )

    # Shared: transfer_date (transfer types) or payment_date (payment types)
    date = models.DateField(verbose_name="Data")
    funding_source_type = models.PositiveSmallIntegerField(
        verbose_name="Fonte de Recurso",
        choices=AudespFundingSourceTypeChoices,
    )
    # Shared: value (inclusão) or corrected_value (retificação); zero cancels
    # the original entry for correction types.
    value = models.DecimalField(
        verbose_name="Valor",
        decimal_places=2,
        max_digits=12,
    )

    # Payment-shaped fields (PAYMENT_CORRECTION / PAYMENT_INCLUSION)
    expense = models.ForeignKey(
        Expense,
        verbose_name="Documento Fiscal (Despesa)",
        related_name="balance_adjustments",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    payment_method_type = models.PositiveSmallIntegerField(
        verbose_name="Meio de Pagamento",
        choices=[(1, "Banco"), (2, "Fundo Fixo")],
        null=True,
        blank=True,
        help_text="Aplicável apenas a Inclusão de Pagamento",
    )
    bank = models.PositiveIntegerField(verbose_name="Banco", null=True, blank=True)
    bank_branch = models.CharField(
        verbose_name="Agência", max_length=16, null=True, blank=True
    )
    account_number = models.CharField(
        verbose_name="Conta Corrente", max_length=16, null=True, blank=True
    )
    transaction_number = models.CharField(
        verbose_name="Número da Transação",
        max_length=40,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Ajuste de Saldo"
        verbose_name_plural = "Ajustes de Saldo"

    def __str__(self) -> str:
        return f"{self.get_type_display()} - {self.date} - {self.value}"
