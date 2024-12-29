from django.db import models
from simple_history.models import HistoricalRecords

from accounts.models import User
from contracts.models import Contract
from utils.choices import MonthChoices, StatusChoices
from utils.models import BaseModel


class Accountability(BaseModel):
    month = models.IntegerField(
        verbose_name="Mês",
        choices=MonthChoices,
        default=MonthChoices.JAN,
    )
    year = models.IntegerField(
        verbose_name="Ano",
        # TODO: remake migrations and remove default
        default=0,
    )

    status = models.CharField(
        verbose_name="Status",
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
        max_length=22,
    )

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="accountabilities",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Prestação mês {self.month}"

    class Meta:
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"
        unique_together = ("month", "year")


class Expense(BaseModel):
    paid = models.BooleanField(verbose_name="Pago", default=False)
    reconciled = models.BooleanField(verbose_name="Conciliado", default=False)

    value = models.DecimalField(
        verbose_name="Valor da Despesa",
        decimal_places=2,
        max_digits=12,
    )

    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Prestação",
        related_name="expenses",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Despesa {self.id}"

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"


class ExpenseAnalysis(BaseModel):
    status = models.CharField(
        verbose_name="Status",
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
        max_length=22,
    )
    comments = models.CharField(verbose_name="Comentários", max_length=256)
    pending = models.CharField(verbose_name="Pendências", max_length=256)

    reviwer = models.ForeignKey(
        User,
        verbose_name="Usuário",
        related_name="reviwers",
        on_delete=models.CASCADE,
    )
    expense = models.ForeignKey(
        Expense,
        verbose_name="Despesa",
        related_name="expenses_analysis",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Análise {self.id} - {self.status}"

    class Meta:
        verbose_name = "Análise de Despesa"
        verbose_name_plural = "Análise de Despesas"


class Revenue(BaseModel):
    value = models.DecimalField(
        verbose_name="Valor da Despesa",
        decimal_places=2,
        max_digits=12,
    )

    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Receita",
        related_name="revenues",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Receita {self.id}"

    class Meta:
        verbose_name = "Receita"
        verbose_name_plural = "Receitas"


class AccountabilityFile(BaseModel):
    # file
    category = models.CharField(verbose_name="Tipo de Anexo", max_length=128)

    expense = models.ForeignKey(
        Expense,
        verbose_name="Despesa",
        related_name="accountabilitie_files",
        on_delete=models.CASCADE,
    )

    revenue = models.ForeignKey(
        Revenue,
        verbose_name="Receita",
        related_name="accountabilitie_files",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Arquivo de Prestação {self.id}"

    class Meta:
        verbose_name = "Receita"
        verbose_name_plural = "Receitas"
