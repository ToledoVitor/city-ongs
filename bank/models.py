from django.db import models
from simple_history.models import HistoricalRecords

from activity.models import ActivityLog
from utils.models import BaseModel


class BankAccount(BaseModel):
    class AccountTypeChoices(models.TextChoices):
        CHECKING = "CHECKING", "conta corrente"
        INVESTING = "INVESTING", "investimento"

    bank_name = models.CharField(
        verbose_name="Nome do Banco",
        max_length=128,
    )
    bank_id = models.IntegerField(
        verbose_name="Id do Banco",
    )

    account = models.CharField(
        verbose_name="Número da Conta",
        max_length=16,
    )
    account_type = models.CharField(
        verbose_name="Tipo da Conta",
        max_length=9,
        choices=AccountTypeChoices.choices,
        default=AccountTypeChoices.CHECKING,
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

    @property
    def contract(self):
        if hasattr(self, "checking_account"):
            return self.checking_account
        if hasattr(self, "investing_contract"):
            return self.investing_contract
        return None

class BankStatement(BaseModel):
    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="Conta Bancária",
        related_name="statements",
        on_delete=models.CASCADE,
    )

    balance = models.DecimalField(
        verbose_name="Saldo no Dia",
        decimal_places=2,
        max_digits=12,
    )
    opening_date = models.DateField(
        verbose_name="Data Inicial do Extrato",
        null=True,
        blank=True,
    )
    closing_date = models.DateField(
        verbose_name="Data Final do extrato",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Extrato Bancário"
        verbose_name_plural = "Extratos Bancários"


class Transaction(BaseModel):
    class TransactionTypeChoices(models.TextChoices):
        DEBIT = "DEBIT", "débito"
        CREDIT = "CREDIT", "crédito"
        INT = "INT", "juros"
        DIV = "DIV", "dividendos"
        FEE = "FEE", "taxa"
        SRVCHG = "SRVCHG", "taxa de serviço"
        DEP = "DEP", "depósito"
        ATM = "ATM", "caixa eletrônico"
        POS = "POS", "ponto de venda"
        XFER = "XFER", "transferência entre contas"
        CHECK = "CHECK", "cheque"
        PAYMENT = "PAYMENT", "fatura ou débito"
        CASH = "CASH", "saque"
        DIRECTDEP = "DIRECTDEP", "depósito direto"
        DIRECTDEBIT = "DIRECTDEBIT", "débito automático"
        REPEATPMT = "REPEATPMT", "pagamento recorrente"
        OTHER = "OTHER", "outros"

    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="Conta Bancária",
        related_name="transactions",
        on_delete=models.CASCADE,
    )

    amount = models.DecimalField(
        verbose_name="Valor da Transação",
        decimal_places=2,
        max_digits=12,
    )
    date = models.DateField(
        verbose_name="Data da Transação",
    )

    transaction_type = models.CharField(
        verbose_name="Tipo da Transação",
        max_length=32,
        choices=TransactionTypeChoices.choices,
        default=TransactionTypeChoices.OTHER,
    )
    transaction_id = models.CharField(
        verbose_name="Id da Transação",
        max_length=32,
        null=True,
        blank=True,
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

        constraints = [
            models.UniqueConstraint(
                fields=['transaction_id'],
                name='unique__transaction_id',
                condition=models.Q(
                    transaction_id__isnull=False,
                    deleted_at__isnull=True,
                )
            ),
        ]