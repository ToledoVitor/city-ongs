from django.db import models
from simple_history.models import HistoricalRecords

from activity.models import ActivityLog
from utils.models import BaseModel


class BankAccount(BaseModel):
    # TODO: remove nulls
    bank_name = models.CharField(
        verbose_name="Nome do Banco",
        max_length=128,
        blank=True,
        null=True,
    )
    bank_id = models.IntegerField(
        verbose_name="Id do Banco",
        blank=True,
        null=True,
    )

    account = models.CharField(
        verbose_name="Número da Conta",
        max_length=16,
        blank=True,
        null=True,
    )
    account_type = models.CharField(
        verbose_name="Tipo da Conta",
        max_length=16,
        blank=True,
        null=True,
    )
    agency = models.CharField(
        verbose_name="Agência",
        max_length=128,
        blank=True,
        null=True,
    )
    balance = models.DecimalField(
        verbose_name="Saldo Atual",
        decimal_places=2,
        max_digits=12,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.bank_name} - {self.account}"

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"

    @property
    def recent_logs(self):
        return ActivityLog.objects.filter(target_object_id=self.id)

    @property
    def account_type_label(self):
        types = {
            "CHECKING": "Conta Corrente",
        }
        return types.get(self.account_type, self.account_type)

    @property
    def last_statement_update(self):
        last_statement = self.statements.order_by("-closing_date").first()
        if last_statement:
            return {
                "start": last_statement.opening_date,
                "end": last_statement.closing_date,
            }
        else:
            return None

    @property
    def last_transactions(self):
        return self.transactions.order_by("-date")[:10]


class BankStatement(BaseModel):
    # TODO: Remove nulls
    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="Conta Bancária",
        related_name="statements",
        on_delete=models.CASCADE,
        null=True,
    )

    balance = models.DecimalField(
        verbose_name="Saldo no Dia",
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
    )
    opening_date = models.DateField(
        verbose_name="Data Inicial do Extrato",
        null=True,
        blank=True,
    )
    closing_date = models.DateField(
        verbose_name="Data Final do extrato",
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Extrato Bancário"
        verbose_name_plural = "Extratos Bancários"


class Transaction(BaseModel):
    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="Conta Bancária",
        related_name="transactions",
        on_delete=models.CASCADE,
        null=True,
    )

    amount = models.DecimalField(
        verbose_name="Valor da Transação",
        decimal_places=2,
        max_digits=12,
    )
    # TODO: remove null
    date = models.DateField(
        verbose_name="Data da Transação",
        null=True,
        blank=True,
    )

    transaction_type = models.CharField(
        verbose_name="Tipo da Transação",
        max_length=32,
        null=True,
        blank=True,
    )
    transaction_id = models.CharField(
        verbose_name="Id da Transação",
        max_length=32,
        null=True,
        blank=True,
        unique=True,
    )

    name = models.CharField(
        verbose_name="Nome",
        max_length=128,
        null=True,
        blank=True,
    )
    memo = models.CharField(
        verbose_name="Notas Adicionais (opcional)",
        max_length=256,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Movimentação Bancária"
        verbose_name_plural = "Movimentações Bancárias"
