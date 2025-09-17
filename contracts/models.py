import os
from decimal import ROUND_HALF_UP, Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Max, Q
from django_cpf_cnpj.fields import CNPJField
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

from accounts.models import Area, BaseOrganizationTenantModel, Committee, User
from activity.models import ActivityLog
from bank.models import BankAccount
from contracts.choices import NatureChoices
from utils.choices import MonthChoices, StatesChoices, StatusChoices


class Company(BaseOrganizationTenantModel):
    # Info
    name = models.CharField(verbose_name="Nome", max_length=128)
    cnpj = CNPJField(masked=True)
    phone_number = PhoneNumberField(
        region="BR",
        help_text="Telefone da empresa",
        null=True,
        blank=True,
    )

    # Address
    street = models.CharField(
        verbose_name="Rua",
        max_length=128,
        null=True,
        blank=True,
    )
    number = models.IntegerField(
        verbose_name="Número",
        null=True,
        blank=True,
    )
    complement = models.CharField(
        verbose_name="Complemento", max_length=128, null=True, blank=True
    )
    district = models.CharField(
        verbose_name="Bairro",
        max_length=128,
        null=True,
        blank=True,
    )
    city = models.CharField(
        verbose_name="Cidade",
        max_length=128,
        null=True,
        blank=True,
    )
    uf = models.CharField(
        verbose_name="UF",
        choices=StatesChoices.choices,
        max_length=2,
        null=True,
        blank=True,
    )
    postal_code = models.CharField(
        verbose_name="CEP",
        max_length=8,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.name} - {self.cnpj}"

    @property
    def masked_cnpj(self) -> str:
        cnpj = self.cnpj.number
        return f"{cnpj[0:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

    @property
    def masked_phone(self) -> str:
        if not self.phone_number:
            return ""
        return self.phone_number.as_national

    @property
    def full_address(self) -> str:
        address_parts = [
            self.street,
            self.number,
            self.complement,
            self.district,
            self.city,
            self.uf,
            self.postal_code,
        ]
        return ", ".join(
            [str(part).title() for part in address_parts if part is not None]
        )

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"


class Contract(BaseOrganizationTenantModel):
    """
    Contract model representing agreements between organizations.
    """

    class ContractStatusChoices(models.TextChoices):
        PLANNING = "PLANNING", "planejamento"
        EXECUTION = "EXECUTION", "em execução"
        FINISHED = "FINISHED", "finalizado"

    class ConcessionChoices(models.TextChoices):
        MANAGEMENT = "MANAGEMENT", "Contrato de Gestão"
        PARTNERSHIP = "PARTNERSHIP", "Termo de Parceria"
        COLLABORATION = "COLLABORATION", "Termo de Colaboração"
        DEVELOPMENTO = "DEVELOPMENTO", "Contrato de Fomento"
        AGREEMENT = "AGREEMENT", "Convênio"
        GRANT = "GRANT", "Concessão"

    # Specifications
    name = models.CharField(verbose_name="Nome do contrato", max_length=128)
    concession_type = models.CharField(
        verbose_name="Tipo de Concessão",
        choices=ConcessionChoices.choices,
        default=ConcessionChoices.MANAGEMENT,
        max_length=128,
    )
    code = models.CharField(
        verbose_name="Código do contrato",
        max_length=16,
        null=True,
        blank=True,
    )
    internal_code = models.PositiveIntegerField(
        verbose_name="Código interno para importação",
    )
    objective = models.CharField(verbose_name="Objeto", max_length=255)
    bidding = models.CharField(
        verbose_name="Licitação",
        max_length=255,
    )

    # Law and Agreement
    law_num = models.CharField(
        verbose_name="Número da Lei",
        max_length=255,
        null=True,
        blank=True,
    )
    law_date = models.DateField(
        verbose_name="Data da Lei",
        null=True,
        blank=True,
    )

    agreement_num = models.CharField(
        verbose_name="Número do Convênio",
        max_length=255,
        null=True,
        blank=True,
    )
    agreement_date = models.DateField(
        verbose_name="Data do Convênio",
        null=True,
        blank=True,
    )

    # Values
    original_value = models.DecimalField(
        verbose_name="Valor original do contrato",
        decimal_places=2,
        max_digits=12,
    )
    total_value = models.DecimalField(
        verbose_name="Valor do contrato",
        decimal_places=2,
        max_digits=12,
    )
    municipal_value = models.DecimalField(
        verbose_name="Valor repassado pelo município",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
    )
    counterpart_value = models.DecimalField(
        verbose_name="Valor repassado por contrapartida de parceiro",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
    )

    # Dates
    start_of_vigency = models.DateField(verbose_name="Começo da vigência")
    end_of_vigency = models.DateField(verbose_name="Fim da vigência")
    status = models.CharField(
        verbose_name="Status",
        choices=ContractStatusChoices,
        default=ContractStatusChoices.PLANNING,
        max_length=13,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/contracts/",
        null=True,
        blank=True,
    )

    # Contractor
    contractor_company = models.ForeignKey(
        Company,
        verbose_name="Contratante",
        related_name="company_contracts",
        on_delete=models.CASCADE,
        null=True,
    )
    contractor_manager = models.ForeignKey(
        Company,
        verbose_name="Gestor do Contratante",
        related_name="company_manager_contracts",
        on_delete=models.CASCADE,
        null=True,
    )

    # Hired
    hired_company = models.ForeignKey(
        Company,
        verbose_name="Contratada",
        related_name="hired_contracts",
        on_delete=models.CASCADE,
        null=True,
    )
    hired_manager = models.ForeignKey(
        Company,
        verbose_name="Gestor da Contratada",
        related_name="hired_manager_contracts",
        on_delete=models.CASCADE,
        null=True,
    )

    # Link with city hall area
    area = models.ForeignKey(
        Area,
        verbose_name="Area",
        related_name="contracts",
        on_delete=models.CASCADE,
    )
    committee = models.ForeignKey(
        Committee,
        verbose_name="Comitê",
        related_name="contracts",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # bank accounts
    checking_account = models.OneToOneField(
        BankAccount,
        verbose_name="Conta Corrente",
        related_name="checking_account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    investing_account = models.OneToOneField(
        BankAccount,
        verbose_name="Conta Investimento",
        related_name="investing_contract",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Autority users
    accountability_autority = models.ForeignKey(
        User,
        related_name="accountability_contracts",
        verbose_name="Responsável Contábil",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    supervision_autority = models.ForeignKey(
        User,
        related_name="supervision_contracts",
        verbose_name="Responsável Fiscal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    def __str__(self) -> str:
        return f"{self.internal_code} - {self.name}"

    @property
    def trailing_code(self):
        return "{:04}".format(self.internal_code)

    @property
    def name_with_code(self):
        return self.trailing_code + f" - {self.name}"

    @property
    def status_label(self) -> str:
        return Contract.ContractStatusChoices(self.status).label

    @property
    def concession_type_label(self) -> str:
        return Contract.ConcessionChoices(self.concession_type).label

    @property
    def total_value_with_point(self) -> str:
        return str(self.total_value).replace(".", ",")

    @property
    def is_on_planning(self) -> bool:
        return self.status == Contract.ContractStatusChoices.PLANNING

    @property
    def is_on_execution(self) -> bool:
        return self.status == Contract.ContractStatusChoices.EXECUTION

    @property
    def is_finished(self) -> bool:
        return self.status == Contract.ContractStatusChoices.FINISHED

    @property
    def recent_logs(self):
        # Coletando IDs necessários em uma única query para cada tipo
        related_ids = {
            "addendum": list(self.addendums.values_list("id", flat=True)[:10]),
            "goals": list(self.goals.values_list("id", flat=True)[:10]),
            "items": list(self.items.values_list("id", flat=True)[:10]),
            "accountabilities": list(
                self.accountabilities.values_list("id", flat=True)[:10]
            ),
            "interested": list(self.interested_parts.values_list("id", flat=True)[:10]),
        }
        return (
            ActivityLog.objects.filter(
                Q(target_object_id=str(self.id))
                | Q(target_object_id__in=related_ids["addendum"])
                | Q(target_object_id__in=related_ids["goals"])
                | Q(target_object_id__in=related_ids["items"])
                | Q(target_object_id__in=related_ids["accountabilities"])
                | Q(target_object_id__in=related_ids["interested"])
            )
            .select_related("user")
            .distinct()
            .order_by("-created_at")[:10]
        )

    @property
    def month_income_value(self):
        months_amount = (self.end_of_vigency - self.start_of_vigency).days // 30
        value_per_month = self.total_value / months_amount
        return value_per_month.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        if self.internal_code is None:
            max_code = Contract.objects.aggregate(Max("internal_code"))[
                "internal_code__max"
            ]
            self.internal_code = 1 if max_code is None else max_code + 1
        super().save(*args, **kwargs)


class ContractInterestedPart(BaseOrganizationTenantModel):
    class InterestLevel(models.TextChoices):
        PROJECT_MANAGER = "PROJECT_MANAGER", "Gestor de Projeto"
        FINANCIAL_MANAGER = "FINANCIAL_MANAGER", "Gestor Financeiro"
        TECHNICAL_MANAGER = "TECHNICAL_MANAGER", "Responsável Técnico"
        PROJECT_COORDINATOR = "PROJECT_COORDINATOR", "Coordenador do Projeto"
        ENTITY_RESPONSIBLE = "ENTITY_RESPONSIBLE", "Responsável pela Entidade"
        FISCAL_COUNCIL = "FISCAL_COUNCIL", "Conselho Fiscal"
        VICE_PRESIDENT = "VICE_PRESIDENT", "Vice Presidente"
        TREASURER = "TREASURER", "Tesoureiro"
        SECRETARY = "SECRETARY", "Secretário"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="interested_parts",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        User,
        verbose_name="Usuario",
        related_name="interested_parts",
        on_delete=models.CASCADE,
    )
    interest = models.CharField(
        verbose_name="Interesse",
        choices=InterestLevel.choices,
        default=InterestLevel.PROJECT_MANAGER,
        max_length=19,
    )

    @property
    def interest_label(self) -> str:
        return ContractInterestedPart.InterestLevel(self.interest).label

    class Meta:
        verbose_name = "Parte Interessada"
        verbose_name_plural = "Partes Interessadas"


class ContractMonthTransfer(
    BaseOrganizationTenantModel,
):
    class TransferSource(models.TextChoices):
        CITY_HALL = "CITY_HALL", "Prefeitura"
        COUNTERPART = "COUNTERPART", "Contrapartida"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="month_transfers",
        on_delete=models.CASCADE,
    )
    month = models.IntegerField(
        verbose_name="Mês",
        choices=MonthChoices,
        default=MonthChoices.JAN,
    )
    year = models.IntegerField(
        verbose_name="Ano",
        default=0,
    )
    source = models.CharField(
        verbose_name="Fonte do Repasse",
        choices=TransferSource.choices,
        default=TransferSource.CITY_HALL,
        max_length=255,
    )
    value = models.DecimalField(
        verbose_name="Valor do Repasse",
        decimal_places=2,
        max_digits=12,
    )

    class Meta:
        verbose_name = "Repasse Mensal"
        verbose_name_plural = "Repasses Mensais"


class ContractAddendum(BaseOrganizationTenantModel):
    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="addendums",
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/contract-addendums/",
        null=True,
        blank=True,
    )

    # Datas
    start_of_vigency = models.DateField(verbose_name="Começo da vigência")
    end_of_vigency = models.DateField(verbose_name="Fim da vigência")

    # Values
    total_value = models.DecimalField(
        verbose_name="Valor do contrato",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
    )
    municipal_value = models.DecimalField(
        verbose_name="Valor repassado pelo município",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
    )
    counterpart_value = models.DecimalField(
        verbose_name="Valor repassado por contrapartida de parceiro",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Aditivo de Contrato"
        verbose_name_plural = "Aditivos de Contrato"


class ContractDocument(BaseOrganizationTenantModel):
    class DocumentType(models.TextChoices):
        ADDENDUM = "ADDENDUM", "Aditivo"
        CONTRACT = "CONTRACT", "Contrato"
        SPREADSHEET = "SPREADSHEET", "Planilha"
        TERMS = "TERMS", "Termos"
        OTHER = "OTHER", "Outro"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="documents",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name="Nome",
        max_length=128,
    )
    type = models.CharField(
        verbose_name="Tipo",
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        max_length=128,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/contract-documents/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Documento de Contrato"
        verbose_name_plural = "Documentos de Contrato"


class ContractGoal(
    BaseOrganizationTenantModel,
):
    """Model representing a goal within a contract with its specifications."""

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="goals",
        on_delete=models.CASCADE,
    )

    # ITEM ESPECIFICATION
    name = models.CharField(
        verbose_name="Item",
        max_length=256,
    )
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=1024,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
        max_length=1024,
    )
    observations = models.CharField(
        verbose_name="Observações",
        max_length=1024,
        null=True,
        blank=True,
    )

    status = models.CharField(
        verbose_name="Status",
        max_length=22,
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.name

    @property
    def status_label(self) -> str:
        return StatusChoices(self.status).label

    @property
    def last_reviews(self) -> str:
        return self.goal_reviews.order_by("-created_at")[:10]

    class Meta:
        verbose_name = "Meta"
        verbose_name_plural = "Metas"


class ContractGoalReview(BaseOrganizationTenantModel):
    """Model representing a review/comment on a contract goal."""

    goal = models.ForeignKey(
        ContractGoal,
        verbose_name="Meta",
        related_name="goal_reviews",
        on_delete=models.CASCADE,
    )
    reviewer = models.ForeignKey(
        User,
        verbose_name="Revisor",
        related_name="goal_reviews",
        on_delete=models.CASCADE,
    )
    comment = models.CharField(
        verbose_name="Comentário",
        max_length=1024,
    )

    class Meta:
        verbose_name = "Revisão de Meta"
        verbose_name_plural = "Revisões de Metas"


class ContractStep(BaseOrganizationTenantModel):
    """Model representing a step within a contract goal."""

    goal = models.ForeignKey(
        ContractGoal, related_name="steps", on_delete=models.CASCADE
    )

    name = models.CharField(
        verbose_name="Item",
        max_length=128,
    )
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=1024,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
        max_length=1024,
    )
    resources = models.CharField(
        verbose_name="Recursos",
        max_length=1024,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return str(f"Etapa: {self.name} | Meta: {self.goal.name}")

    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"


class ContractItem(BaseOrganizationTenantModel):
    class ResourceSource(models.TextChoices):
        CITY_HALL = "CITY_HALL", "Prefeitura"
        COUNTERPART = "COUNTERPART", "Contrapartida de Parceiro"

    class PurchaseStatus(models.TextChoices):
        ANALYZING = "ANALYZING", "Analisando Opções"
        IN_PROGRESS = "IN_PROGRESS", "Em Andamento"
        FINISHED = "FINISHED", "Finalizado"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="items",
        on_delete=models.CASCADE,
    )
    source = models.CharField(
        verbose_name="Fonte do Recurso",
        choices=ResourceSource.choices,
        default=ResourceSource.CITY_HALL,
        max_length=11,
    )

    # ITEM ESPECIFICATION
    name = models.CharField(
        verbose_name="Item",
        max_length=128,
    )
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=1024,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
        max_length=1024,
        null=True,
        blank=True,
    )
    observations = models.CharField(
        verbose_name="Observações",
        max_length=1024,
        null=True,
        blank=True,
    )

    # EXPENSE ESPECIFICATION
    month_quantity = models.PositiveIntegerField(
        verbose_name="Quantidade de Meses",
    )
    month_expense = models.DecimalField(
        verbose_name="Custo Mensal Unitário",
        decimal_places=2,
        max_digits=12,
    )
    anual_expense = models.DecimalField(
        verbose_name="Custo Anual",
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Quantidade",
        default=1,
    )
    unit_type = models.CharField(
        verbose_name="Tipo da Unidade",
        max_length=128,
        null=True,
        blank=True,
    )
    nature = models.CharField(
        verbose_name="Natureza da Despesa",
        choices=NatureChoices,
        max_length=34,
    )

    # DATES
    start_date = models.DateField(
        verbose_name="Data Inicial",
        null=True,
        blank=True,
    )
    end_date = models.DateField(
        verbose_name="Data Final",
        null=True,
        blank=True,
    )

    is_additive = models.BooleanField(verbose_name="É aditivo?", default=False)

    status = models.CharField(
        verbose_name="Status",
        max_length=22,
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
    )

    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/contract-items/",
        null=True,
        blank=True,
    )

    # AQUISITION STATUS
    purchase_status = models.CharField(
        verbose_name="Status de Compra",
        choices=PurchaseStatus.choices,
        default=PurchaseStatus.ANALYZING,
        max_length=22,
    )
    aquisition_date = models.DateField(
        verbose_name="Data da Aquisição",
        null=True,
        blank=True,
    )
    parcel_due_date = models.DateField(
        verbose_name="Data de Vencimento das Parcelas",
        null=True,
        blank=True,
    )
    aquisition_value = models.DecimalField(
        verbose_name="Valor da Aquisição",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
    )
    aquisition_parcel_quantity = models.PositiveIntegerField(
        verbose_name="Quantidade de Parcelas",
        null=True,
        blank=True,
    )

    # SUPPLIER
    supplier = models.CharField(
        verbose_name="Fornecedor",
        max_length=256,
        null=True,
        blank=True,
    )
    supplier_document = models.CharField(
        verbose_name="Documento do Fornecedor",
        max_length=256,
        null=True,
        blank=True,
    )
    supplier_phone = models.CharField(
        verbose_name="Telefone do Fornecedor",
        max_length=256,
        null=True,
        blank=True,
    )
    supplier_email = models.EmailField(
        verbose_name="Email do Fornecedor",
        max_length=256,
        null=True,
        blank=True,
    )
    supplier_address = models.CharField(
        verbose_name="Endereço do Fornecedor",
        max_length=256,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return str(self.name)

    @property
    def source_label(self) -> str:
        return ContractItem.ResourceSource(self.source).label

    @property
    def status_label(self) -> str:
        return StatusChoices(self.status).label

    @property
    def nature_label(self) -> str:
        return NatureChoices(self.nature).label

    @property
    def purchase_status_label(self) -> str:
        return ContractItem.PurchaseStatus(self.purchase_status).label

    @property
    def anual_expense_with_point(self) -> str:
        return str(self.anual_expense).replace(",", ".")

    @property
    def month_expense_with_point(self) -> str:
        return str(self.month_expense).replace(",", ".")

    @property
    def total_month_expense(self) -> str:
        return self.month_expense * self.quantity

    @property
    def last_reviews(self) -> str:
        return self.item_reviews.order_by("-created_at")[:10]

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"
        ordering = ("-month_expense",)


class ContractItemPurchaseProcessDocument(BaseOrganizationTenantModel):
    item = models.ForeignKey(
        # TODO: remove this null=True, blank=True
        ContractItem,
        verbose_name="Processo de Compra",
        related_name="purchase_documents",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name="Nome",
        max_length=256,
        null=True,
        blank=True,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/contract-item-purchase-process-documents/",
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"Documento de Compra - {self.file.name}"

    class Meta:
        verbose_name = "Documento do Processo de Compra"
        verbose_name_plural = "Documentos do Processo de Compra"


class ContractItemReview(BaseOrganizationTenantModel):
    item = models.ForeignKey(
        ContractItem,
        verbose_name="Item",
        related_name="item_reviews",
        on_delete=models.CASCADE,
    )
    reviewer = models.ForeignKey(
        User,
        verbose_name="Revisor",
        related_name="item_reviews",
        on_delete=models.CASCADE,
    )
    comment = models.CharField(
        verbose_name="Comentário",
        max_length=255,
    )

    class Meta:
        verbose_name = "Revisão de Item"
        verbose_name_plural = "Revisões de Itens"


class ContractExecution(BaseOrganizationTenantModel):
    class ReviewStatus(models.TextChoices):
        WIP = "WIP", "Em Andamento"
        SENT = "SENT", "Enviada para análise"
        CORRECTING = "CORRECTING", "Corrigindo"
        FINISHED = "FINISHED", "Finalizada"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Execução",
        related_name="executions",
        on_delete=models.CASCADE,
    )
    month = models.IntegerField(
        verbose_name="Mês",
        choices=MonthChoices,
        default=MonthChoices.JAN,
    )
    year = models.IntegerField(
        verbose_name="Ano",
        default=0,
    )
    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus,
        default=ReviewStatus.WIP,
        max_length=10,
    )

    class Meta:
        verbose_name = "Relatório de Execução"
        verbose_name_plural = "Relatórios de Execução"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("contract", "month", "year"),
                name="unique_execution_per_contract_month_year",
            ),
        ]

    def __str__(self) -> str:
        return f"Execution {self.month}/{self.year}"

    @property
    def status_label(self) -> bool:
        return ContractExecution.ReviewStatus(self.status).label

    @property
    def is_on_execution(self) -> bool:
        return self.status in {
            ContractExecution.ReviewStatus.WIP,
            ContractExecution.ReviewStatus.CORRECTING,
        }

    @property
    def is_sent(self) -> bool:
        return self.status == ContractExecution.ReviewStatus.SENT

    @property
    def is_finished(self) -> bool:
        return self.status == ContractExecution.ReviewStatus.FINISHED

    @property
    def month_text(self) -> str:
        return MonthChoices(self.month).label

    @property
    def recent_logs(self):
        execution_logs = ActivityLog.objects.filter(target_object_id=self.id)

        activities_ids = [
            str(id) for id in self.activities.values_list("id", flat=True)[:10]
        ]
        activities_logs = ActivityLog.objects.filter(
            target_object_id__in=activities_ids,
        )

        files_ids = [str(id) for id in self.files.values_list("id", flat=True)[:10]]
        files_logs = ActivityLog.objects.filter(
            target_object_id__in=files_ids,
        )

        combined_querset = (execution_logs | activities_logs | files_logs).distinct()
        return combined_querset.order_by("-created_at")[:10]


class ContractExecutionActivity(BaseOrganizationTenantModel):
    execution = models.ForeignKey(
        ContractExecution,
        verbose_name="Relatório de Execução",
        related_name="activities",
        on_delete=models.CASCADE,
    )
    step = models.ForeignKey(
        ContractStep,
        verbose_name="Etapa",
        related_name="activities",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name="Nome",
        max_length=128,
    )
    description = models.CharField(
        verbose_name="Descrição",
        max_length=256,
    )
    percentage = models.DecimalField(
        verbose_name="Porcentagem Completa",
        max_digits=3,
        decimal_places=0,
        default=Decimal(0),
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Atividade Executada"
        verbose_name_plural = "Atividades Executadas"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("execution", "step", "name"),
                name="unique_activity_per_execution_step",
            ),
        ]


class ContractExecutionFile(BaseOrganizationTenantModel):
    execution = models.ForeignKey(
        ContractExecution,
        verbose_name="Relatório de Execução",
        related_name="files",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name="Nome",
        max_length=128,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/contracts/executions",
    )

    class Meta:
        verbose_name = "Arquivo de Atividade"
        verbose_name_plural = "Arquivos de Atividades"

    def __str__(self) -> str:
        return str(self.name)

    @property
    def file_type(self) -> str:
        return os.path.splitext(self.file.name)[1]


class ContractItemNewValueRequest(BaseOrganizationTenantModel):
    class ReviewStatus(models.TextChoices):
        IN_REVIEW = "IN_REVIEW", "Em revisão"
        REJECTED = "REJECTED", "Rejeitado"
        APPROVED = "APPROVED", "Aprovado"

    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus.choices,
        default=ReviewStatus.IN_REVIEW,
        max_length=9,
    )
    rejection_reason = models.CharField(
        verbose_name="Motivo da rejeição",
        max_length=255,
        null=True,
        blank=True,
    )

    requested_by = models.ForeignKey(
        User,
        verbose_name="Solicitado por",
        related_name="item_value_requests",
        on_delete=models.CASCADE,
    )
    downgrade_item = models.ForeignKey(
        ContractItem,
        verbose_name="Item para diminuir valor",
        related_name="downgrade_requests",
        on_delete=models.CASCADE,
    )
    raise_item = models.ForeignKey(
        ContractItem,
        verbose_name="Item para aumentar valor",
        related_name="raise_requests",
        on_delete=models.CASCADE,
    )
    month_raise = models.DecimalField(
        verbose_name="Incrementeo Mensal",
        decimal_places=2,
        max_digits=12,
    )
    anual_raise = models.DecimalField(
        verbose_name="Incremento Anual",
        decimal_places=2,
        max_digits=12,
    )

    @property
    def status_label(self) -> str:
        return ContractItemNewValueRequest.ReviewStatus(self.status).label

    class Meta:
        verbose_name = "Solicitação de Valor Item"
        verbose_name_plural = "Solicitações de Valores Item"


class ContractItemSupplement(BaseOrganizationTenantModel):
    class ReviewStatus(models.TextChoices):
        IN_REVIEW = "IN_REVIEW", "Em revisão"
        REJECTED = "REJECTED", "Rejeitado"
        APPROVED = "APPROVED", "Aprovado"

    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus.choices,
        default=ReviewStatus.IN_REVIEW,
        max_length=9,
    )

    item = models.ForeignKey(
        ContractItem,
        verbose_name="Item",
        related_name="supplements",
        on_delete=models.CASCADE,
    )
    suplement_value = models.DecimalField(
        verbose_name="Valor do suplemento",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
    )
    observations = models.TextField(
        verbose_name="Observações",
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.item.name} - {self.suplement_value}"

    @property
    def status_label(self) -> str:
        return ContractItemSupplement.ReviewStatus(self.status).label

    class Meta:
        ordering = ("-suplement_value",)
        verbose_name = "Suplemento de Item"
        verbose_name_plural = "Suplementos de Itens"
