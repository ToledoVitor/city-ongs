from django.db import models

from utils.choices import StatusChoices


class Contract(models.Model):
    name = models.CharField(verbose_name="Nome do contrato", max_length=128)
    total_value = models.DecimalField(
        verbose_name="Valor do contrato",
        decimal_places=2,
        max_digits=12,
    )
    start_of_vigency = models.DateField(verbose_name="Começo da vigência")
    end_of_vigency = models.DateField(verbose_name="Fim da vigência")

    ## Campos usuários -> contratantes

    class Meta:
        verbose_name = "Contrato"
        verbose_name_plural = "Contratos"


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
