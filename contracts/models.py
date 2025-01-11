from django.db import models
from django.db.models import Max
from django_cpf_cnpj.fields import CNPJField
from simple_history.models import HistoricalRecords

from accounts.models import Area, Ong
from activity.models import ActivityLog
from utils.choices import StatusChoices
from utils.models import BaseModel


class Company(BaseModel):
    name = models.CharField(verbose_name="Nome", max_length=128)
    cnpj = CNPJField(masked=True)
    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.name} - {self.cnpj}"

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"


class Contract(BaseModel):
    name = models.CharField(verbose_name="Nome do contrato", max_length=128)
    code = models.PositiveIntegerField(
        verbose_name="Código do contrato",
        null=True,
        blank=True,
    )
    objective = models.CharField(verbose_name="Objeto", max_length=128)
    total_value = models.DecimalField(
        verbose_name="Valor do contrato",
        decimal_places=2,
        max_digits=12,
    )
    start_of_vigency = models.DateField(verbose_name="Começo da vigência")
    end_of_vigency = models.DateField(verbose_name="Fim da vigência")

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
        verbose_name="Gestor do Contratada",
        related_name="hired_manager_contracts",
        on_delete=models.CASCADE,
        null=True,
    )

    # Ong
    ong = models.ForeignKey(
        Ong,
        verbose_name="Ong",
        related_name="contracts",
        on_delete=models.CASCADE,
    )

    # Link with city hall area
    area = models.ForeignKey(
        # TODO: remove null
        Area,
        verbose_name="Area",
        related_name="contracts",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"

    @property
    def trailing_code(self):
        return "{:04}".format(self.code)

    @property
    def name_with_code(self):
        return self.trailing_code + f" - {self.name}"

    @property
    def recent_logs(self):
        contract_logs = ActivityLog.objects.filter(
            action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT,
            target_object_id=self.id,
        )

        addendum_ids = [
            str(id) for id in self.addendums.values_list("id", flat=True)[:10]
        ]
        addendum_logs = ActivityLog.objects.filter(
            action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_ADDENDUM,
            target_object_id__in=addendum_ids,
        )

        goals_ids = [str(id) for id in self.goals.values_list("id", flat=True)[:10]]
        goals_logs = ActivityLog.objects.filter(
            action=ActivityLog.ActivityLogChoices.CREATED_CONTRACT_GOAL,
            target_object_id__in=goals_ids,
        )

        items_ids = [str(id) for id in self.items.values_list("id", flat=True)[:10]]
        items_logs = ActivityLog.objects.filter(
            target_object_id__in=items_ids,
        )

        combined_querset = (
            contract_logs | addendum_logs | goals_logs | items_logs
        ).distinct()
        return combined_querset.order_by("-created_at")[:10]

    def save(self, *args, **kwargs):
        if self.code is None:
            max_code = Contract.objects.aggregate(Max("code"))["code__max"]
            self.code = 1 if max_code is None else max_code + 1

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


class ContractAddress(BaseModel):
    street = models.CharField(verbose_name="Rua", max_length=128)
    number = models.IntegerField(verbose_name="Número")
    complement = models.CharField(
        verbose_name="Complemento", max_length=128, null=True, blank=True
    )
    district = models.CharField(verbose_name="Bairro", max_length=128)
    city = models.CharField(verbose_name="Cidade", max_length=128)
    uf = models.CharField(verbose_name="UF", max_length=128)
    postal_code = models.CharField(verbose_name="CEP", max_length=8)

    class Meta:
        verbose_name = "Endereço"
        verbose_name_plural = "Endereços"


class ContractGoal(BaseModel):
    contract = models.ForeignKey(
        # TODO: remove null
        Contract,
        verbose_name="Contrato",
        related_name="goals",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    name = models.CharField(verbose_name="Meta", max_length=128)
    description = models.CharField(verbose_name="Descrição", max_length=128)
    status = models.CharField(
        verbose_name="Status",
        max_length=22,
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Meta"
        verbose_name_plural = "Metas"


class ContractSubGoal(BaseModel):
    name = models.CharField(verbose_name="Item", max_length=128)
    description = models.CharField(verbose_name="Descrição", max_length=128)
    goal = models.ForeignKey(
        ContractGoal, related_name="sub_goals", on_delete=models.CASCADE
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Submeta"
        verbose_name_plural = "Submetas"


class ContractItem(BaseModel):
    contract = models.ForeignKey(
        # TODO: remove null
        Contract,
        verbose_name="Contrato",
        related_name="items",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    name = models.CharField(verbose_name="Item", max_length=128)
    description = models.CharField(verbose_name="Descrição", max_length=128)
    total_expense = models.DecimalField(
        verbose_name="Despesa total",
        decimal_places=2,
        max_digits=12,
    )
    is_additive = models.BooleanField(verbose_name="É aditivo?", default=False)
    status = models.CharField(
        verbose_name="Status",
        max_length=22,
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
    )
    status_pendencies = models.CharField(
        verbose_name="Pendências e erros",
        max_length=255,
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
    def total_expense_with_point(self) -> str:
        return str(self.total_expense).replace(",", ".")

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"
        ordering = ("-total_expense",)
