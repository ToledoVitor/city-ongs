from django.db import models
from simple_history.models import HistoricalRecords

from accounts.models import CityHall, User
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


class ExpenseSource(BaseModel):
    city_hall = models.ForeignKey(
        CityHall,
        verbose_name="Prefeitura",
        related_name="expense_sources",
        on_delete=models.CASCADE,
    )
    name = models.CharField(verbose_name="Nome da fonte", max_length=64)
    document = models.IntegerField(
        verbose_name="CPF/CNPJ da fonte",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Fonte de Despesa"
        verbose_name_plural = "Fonte de Despesas"
        unique_together = ("city_hall", "name")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.document is not None:
            string_doc = "".join([i for i in str(self.document) if i.isdigit()])
            self.document = int(string_doc)

        super().save(*args, **kwargs)


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
    source = models.ForeignKey(
        ExpenseSource,
        verbose_name="Fonte",
        related_name="expenses",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"

    def __str__(self) -> str:
        return f"Despesa {self.id}"


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
        related_name="expense_anaysis",
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


class RevenueSource(BaseModel):
    class OriginChoices(models.TextChoices):
        FEDERAL = "FEDERAL", "Federal"
        STATE = "STATE", "Estadual"
        MUNICIPAL = "MUNICIPAL", "Municipal"
        COUNTERPART_PARTNER = "COUNTERPART_PARTNER", "Contrapartida de parceiro"
        PRIVATE_SPONSOR = "PRIVATE_SPONSOR", "Patrocinador privado"

    class CategoryChoices(models.TextChoices):
        NOT_APPLIABLE = "NOT_APPLIABLE", "Não Aplicavél"
        COOPERATION_AGREEMENT = "COOPERATION_AGREEMENT", "Acordo de Cooperação"
        AGREEMENT = "AGREEMENT", "Convênio"
        COLLABORATION_AGREEMENT = "COLLABORATION_AGREEMENT", "Termo de Colaboração"
        PROMOTION_AGREEMENT = "PROMOTION_AGREEMENT", "Termo de Fomento"
        DONATION_AGREEMENT = "DONATION_AGREEMENT", "Contrato de Doação"
        MANAGEMENT_AGREEMENT = "MANAGEMENT_AGREEMENT", "Contrato de Gestão"
        TRANSFER_AGREEMENT = "TRANSFER_AGREEMENT", "Contrato de Repasse"
        PARTNERSHIP_AGREEMENT = "PARTNERSHIP_AGREEMENT", "Termo de Parceria"

    city_hall = models.ForeignKey(
        CityHall,
        verbose_name="Prefeitura",
        related_name="revenue_sources",
        on_delete=models.CASCADE,
    )

    name = models.CharField(verbose_name="Nome da fonte", max_length=64)
    document = models.IntegerField(
        verbose_name="CPF/CNPJ da fonte",
        null=True,
        blank=True,
    )
    contract_number = models.CharField(
        verbose_name="Número do contrato",
        max_length=32,
        null=True,
        blank=True,
    )

    origin = models.CharField(
        verbose_name="Origem da Fonte",
        choices=OriginChoices,
        default=OriginChoices.FEDERAL,
        max_length=19,
    )
    category = models.CharField(
        verbose_name="Categoria",
        choices=CategoryChoices,
        default=CategoryChoices.NOT_APPLIABLE,
        max_length=23,
    )

    class Meta:
        verbose_name = "Fonte de Recurso"
        verbose_name_plural = "Fonte de Recursos"
        unique_together = ("city_hall", "name")

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.document is not None:
            string_doc = "".join([i for i in str(self.document) if i.isdigit()])
            self.document = int(string_doc)

        super().save(*args, **kwargs)


class Revenue(BaseModel):
    value = models.DecimalField(
        verbose_name="Valor da Despesa",
        decimal_places=2,
        max_digits=12,
    )

    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Contabilidade",
        related_name="revenues",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Receita {self.id}"

    class Meta:
        verbose_name = "Recurso"
        verbose_name_plural = "Recursos"


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
        verbose_name="Recurso",
        related_name="accountabilitie_files",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Arquivo de Prestação {self.id}"

    class Meta:
        verbose_name = "Receita"
        verbose_name_plural = "Receitas"
