from django.db import models
from django.db.models import Max
from django_cpf_cnpj.fields import CNPJField
from simple_history.models import HistoricalRecords

from accounts.models import Area, Ong
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

    def save(self, *args, **kwargs):
        if self.code is None:
            max_code = Contract.objects.aggregate(Max("code"))["code__max"]
            self.code = 1 if max_code is None else max_code + 1

        super().save(*args, **kwargs)


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
    name = models.CharField(verbose_name="Meta", max_length=128)
    description = models.CharField(verbose_name="Descrição", max_length=128)
    status = models.CharField(
        verbose_name="Status",
        max_length=22,
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
    )

    history = HistoricalRecords()

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

    class Meta:
        verbose_name = "Submeta"
        verbose_name_plural = "Submetas"


class ContractItem(BaseModel):
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

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"
