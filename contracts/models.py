import os
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Max
from django_cpf_cnpj.fields import CNPJField
from simple_history.models import HistoricalRecords

from accounts.models import Area, Organization, User
from activity.models import ActivityLog
from bank.models import BankAccount
from contracts.choices import NatureChoices
from utils.choices import MonthChoices, StatesChoices, StatusChoices
from utils.models import BaseModel


class Company(BaseModel):
    # Info
    name = models.CharField(verbose_name="Nome", max_length=128)
    cnpj = CNPJField(masked=True)

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

    organization = models.ForeignKey(
        Organization,
        verbose_name="Organização",
        related_name="companies",
        on_delete=models.CASCADE,
    )
    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.name} - {self.cnpj}"

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"


class Contract(BaseModel):
    class ContractStatusChoices(models.TextChoices):
        PLANNING = "PLANNING", "planejamento"
        EXECUTION = "EXECUTION", "em execução"
        FINISHED = "FINISHED", "finalizado"

    # Specifications
    name = models.CharField(verbose_name="Nome do contrato", max_length=128)
    concession_type = models.CharField(
        # TODO: remove null
        verbose_name="Tipo de Concessão",
        max_length=32,
        null=True,
        blank=True,
    )
    code = models.CharField(
        verbose_name="Código do contrato",
        max_length=16,
        null=True,
        blank=True,
    )
    internal_code = models.PositiveIntegerField(
        verbose_name="Código interno para importação",
        null=True,
        blank=True,
    )
    objective = models.CharField(verbose_name="Objeto", max_length=128)
    bidding = models.CharField(
        # TODO: remove null
        verbose_name="Licitação",
        max_length=32,
        null=True,
        blank=True,
    )

    # Dates and values
    total_value = models.DecimalField(
        verbose_name="Valor do contrato",
        decimal_places=2,
        max_digits=12,
    )
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

    organization = models.ForeignKey(
        Organization,
        verbose_name="Organização",
        related_name="contracts",
        on_delete=models.CASCADE,
    )

    # Link with city hall area
    area = models.ForeignKey(
        Area,
        verbose_name="Area",
        related_name="contracts",
        on_delete=models.CASCADE,
    )

    # bank accounts
    checking_account = models.OneToOneField(
        BankAccount,
        verbose_name="Conta Corrente",
        related_name="checking_account",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    investing_account = models.OneToOneField(
        BankAccount,
        verbose_name="Conta Investimento",
        related_name="investing_contract",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # Autority users
    accountability_autority = models.ForeignKey(
        User,
        related_name="accountability_contracts",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    supervision_autority = models.ForeignKey(
        User,
        related_name="supervision_contracts",
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
        contract_logs = ActivityLog.objects.filter(target_object_id=self.id)

        addendum_ids = [
            str(id) for id in self.addendums.values_list("id", flat=True)[:10]
        ]
        addendum_logs = ActivityLog.objects.filter(
            target_object_id__in=addendum_ids,
        )

        goals_ids = [str(id) for id in self.goals.values_list("id", flat=True)[:10]]
        goals_logs = ActivityLog.objects.filter(
            target_object_id__in=goals_ids,
        )

        items_ids = [str(id) for id in self.items.values_list("id", flat=True)[:10]]
        items_logs = ActivityLog.objects.filter(
            target_object_id__in=items_ids,
        )

        accountability_ids = [
            str(id) for id in self.accountabilities.values_list("id", flat=True)[:10]
        ]
        accountability_logs = ActivityLog.objects.filter(
            target_object_id__in=accountability_ids,
        )

        combined_querset = (
            contract_logs
            | addendum_logs
            | goals_logs
            | items_logs
            | accountability_logs
        ).distinct()
        return combined_querset.order_by("-created_at")[:10]

    def save(self, *args, **kwargs):
        if self.internal_code is None:
            max_code = Contract.objects.aggregate(Max("internal_code"))[
                "internal_code__max"
            ]
            self.internal_code = 1 if max_code is None else max_code + 1
        super().save(*args, **kwargs)


class ContractAddendum(BaseModel):
    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="addendums",
        on_delete=models.CASCADE,
    )
    start_of_vigency = models.DateField(verbose_name="Começo da vigência")
    end_of_vigency = models.DateField(verbose_name="Fim da vigência")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Aditivo de Contrato"
        verbose_name_plural = "Aditivos de Contrato"


class ContractGoal(BaseModel):
    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="goals",
        on_delete=models.CASCADE,
    )

    # ITEM ESPECIFICATION
    name = models.CharField(
        verbose_name="Item",
        max_length=128,
    )
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=256,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
        max_length=256,
    )
    observations = models.CharField(
        verbose_name="Observações",
        max_length=256,
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


class ContractGoalReview(BaseModel):
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
        max_length=255,
    )

    class Meta:
        verbose_name = "Revisão de Meta"
        verbose_name_plural = "Revisões de Metas"


class ContractStep(BaseModel):
    goal = models.ForeignKey(
        ContractGoal, related_name="steps", on_delete=models.CASCADE
    )

    name = models.CharField(
        verbose_name="Item",
        max_length=128,
    )
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=256,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
        max_length=256,
    )
    resources = models.CharField(
        verbose_name="Recursos",
        max_length=256,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"


class ContractItem(BaseModel):
    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="items",
        on_delete=models.CASCADE,
    )

    # ITEM ESPECIFICATION
    name = models.CharField(
        verbose_name="Item",
        max_length=128,
    )
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=256,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
        max_length=256,
    )
    observations = models.CharField(
        verbose_name="Observações",
        max_length=256,
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
        max_length=32,
    )
    nature = models.CharField(
        verbose_name="Natureza da Despesa",
        choices=NatureChoices,
        max_length=34,
    )

    # DATES
    start_date = models.DateField(
        # TODO: remove null
        verbose_name="Data Inicial",
        null=True,
        blank=True,
    )
    end_date = models.DateField(
        # TODO: remove null
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

    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.name

    @property
    def status_label(self) -> str:
        return StatusChoices(self.status).label

    @property
    def nature_label(self) -> str:
        return NatureChoices(self.nature).label

    @property
    def anual_expense_with_point(self) -> str:
        return str(self.anual_expense).replace(",", ".")

    @property
    def month_expense_with_point(self) -> str:
        return str(self.month_expense).replace(",", ".")

    @property
    def last_reviews(self) -> str:
        return self.item_reviews.order_by("-created_at")[:10]

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"
        ordering = ("-month_expense",)


class ContractItemReview(BaseModel):
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


class ContractExecution(BaseModel):
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
        unique_together = ("contract", "month", "year")

    def __str__(self) -> str:
        return f"Execution {self.month}/{self.year}"

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


class ContractExecutionActivity(BaseModel):
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
        max_length=32,
    )
    description = models.CharField(
        # TODO: remove null
        verbose_name="Descrição",
        max_length=256,
        null=True,
        blank=True,
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
        unique_together = ("execution", "step", "name")


class ContractExecutionFile(BaseModel):
    execution = models.ForeignKey(
        # TODO: remove null
        ContractExecution,
        verbose_name="Relatório de Execução",
        related_name="files",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name="Nome",
        max_length=32,
        null=True,
        blank=True,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/contracts/executions",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Arquivo de Atividade"
        verbose_name_plural = "Arquivos de Atividades"

    def __str__(self) -> str:
        return self.name

    @property
    def file_type(self) -> str:
        return os.path.splitext(self.file.name)[1]
