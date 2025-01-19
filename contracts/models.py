from django.db import models
from django.db.models import Max
from django_cpf_cnpj.fields import CNPJField
from simple_history.models import HistoricalRecords

from accounts.models import Area, Organization
from activity.models import ActivityLog
from bank.models import BankAccount
from contracts.choices import ItemNatureChoices
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

    organization = models.ForeignKey(
        Organization,
        verbose_name="Organização",
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
        related_name="investing_contracts",
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

    # ITEM ESPECIFICATION
    name = models.CharField(
        verbose_name="Item",
        max_length=128,
    )
    # TODO: remove nulls
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=256,
        null=True,
        blank=True,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
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

    class Meta:
        verbose_name = "Meta"
        verbose_name_plural = "Metas"


class ContractStep(BaseModel):
    goal = models.ForeignKey(
        ContractGoal, related_name="sub_goals", on_delete=models.CASCADE
    )

    # TODO: remove nulls
    name = models.CharField(
        verbose_name="Item",
        max_length=128,
    )
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=256,
        null=True,
        blank=True,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
        max_length=256,
        null=True,
        blank=True,
    )
    resources = models.CharField(
        verbose_name="Recursos",
        max_length=256,
        null=True,
        blank=True,
    )
    
    history = HistoricalRecords()

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"


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

    # ITEM ESPECIFICATION
    name = models.CharField(
        verbose_name="Item",
        max_length=128,
    )
    # TODO: remove nulls
    objective = models.CharField(
        verbose_name="Objetivo",
        max_length=256,
        null=True,
        blank=True,
    )
    methodology = models.CharField(
        verbose_name="Metodologia",
        max_length=256,
        null=True,
        blank=True,
    )

    # EXPENSE ESPECIFICATION
    month_quantity = models.PositiveIntegerField(
        verbose_name="Quantidade de Meses",
        null=True,
        blank=True,
    )
    month_expense = models.DecimalField(
        verbose_name="Custo Mensal",
        decimal_places=2,
        max_digits=12,
        default=0,
    )
    unit_type = models.CharField(
        verbose_name="Tipo da Unidade",
        null=True,
        blank=True,
        max_length=32,
    )
    nature = models.CharField(
        verbose_name="Natureza da Despesa",
        choices=ItemNatureChoices,
        null=True,
        blank=True,
        max_length=34,
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
        return str(self.month_expense).replace(",", ".")

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"
        ordering = ("-month_expense",)
