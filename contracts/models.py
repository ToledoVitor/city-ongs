from django.db import models
from django_cpf_cnpj.fields import CNPJField

from utils.choices import StatusChoices


class Company(models.Model):
    name = models.CharField(verbose_name="Nome", max_length=128)
    cnpj = CNPJField(masked=True)


class Contract(models.Model):
    name = models.CharField(verbose_name="Nome do contrato", max_length=128)
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
        Company, verbose_name="Contratante", related_name="company_contracts"
    )
    contractor_manager = models.ForeignKey(
        Company,
        verbose_name="Gestor do Contratante",
        related_name="company_manager_contracts",
    )

    # Hired
    hired_company = models.ForeignKey(
        Company, verbose_name="Contratado", related_name="hired_contracts"
    )
    hired_manager = models.ForeignKey(
        Company,
        verbose_name="Gestor do Contratado",
        related_name="hired_manager_contracts",
    )

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"


class ContractAddress(models.Model):
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


class ContractGoal(models.Model):
    name = models.CharField(verbose_name="Meta", max_length=128)
    description = models.CharField(verbose_name="Descrição", max_length=128)
    status = models.CharField(
        verbose_name="Status",
        max_length=16,
        choices=StatusChoices,
        default=StatusChoices.DRAFT,
    )

    class Meta:
        verbose_name = "Meta"
        verbose_name_plural = "Metas"


class ContractSubGoal(models.Model):
    name = models.CharField(verbose_name="Item", max_length=128)
    description = models.CharField(verbose_name="Descrição", max_length=128)
    goal = models.ForeignKey(
        ContractGoal, related_name="sub_goals", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Submeta"
        verbose_name_plural = "Submetas"


class ContractItem(models.Model):
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
        max_length=16,
        choices=StatusChoices,
        default=StatusChoices.DRAFT,
    )

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Itens"

    # 6.18
    # status:
    # analise, correcao, aprovada, aprovada c ressalva, rejeitada
