from decimal import Decimal
from django.db import models
from simple_history.models import HistoricalRecords

from activity.models import ActivityLog
from utils.choices import MonthChoices
from utils.models import BaseModel


class BankAccount(BaseModel):
    class OriginChoices(models.TextChoices):
        MUNICIPAL = "MUNICIPAL", "Municipal"
        FEDERAL = "FEDERAL", "Federal"
        STATE = "STATE", "Estadual"
        COUNTERPART_PARTNER = "COUNTERPART_PARTNER", "Contrapartida de parceiro"
        PRIVATE_SPONSOR = "PRIVATE_SPONSOR", "Patrocinador privado"

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
        default=Decimal("0.00"),
    )
    origin = models.CharField(
        verbose_name="Origem da Fonte",
        choices=OriginChoices,
        default=OriginChoices.MUNICIPAL,
        max_length=19,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.bank_name} - {self.account} ({self.account_type_label})"

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
        last_statement = self.statements.order_by(
            "-reference_year", "-reference_month"
        ).first()
        if last_statement:
            return f"{last_statement.month_label} de {last_statement.reference_year}"

        return "---"

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

    opening_balance = models.DecimalField(
        verbose_name="Saldo no Dia Inicial",
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
    )
    closing_balance = models.DecimalField(
        # TODO: REMOVE NULL
        verbose_name="Saldo no Dia Final",
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
    )

    reference_month = models.IntegerField(
        verbose_name="Mês",
        choices=MonthChoices,
        default=MonthChoices.JAN,
    )
    reference_year = models.IntegerField(
        verbose_name="Ano",
        default=0,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Extrato Bancário"
        verbose_name_plural = "Extratos Bancários"

    @property
    def month_label(self):
        return MonthChoices(self.reference_month).label.capitalize()


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
        INCOME = "INCOME", "retorno de investimentos"
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
    transaction_number = models.CharField(
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

    expense = models.ForeignKey(
        "accountability.Expense",
        verbose_name="Despesa",
        related_name="transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    revenue = models.ForeignKey(
        "accountability.Revenue",
        verbose_name="Receita",
        related_name="transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Movimentação Bancária"
        verbose_name_plural = "Movimentações Bancárias"

        constraints = [
            models.UniqueConstraint(
                fields=["transaction_number"],
                name="unique__transaction_number",
                condition=models.Q(
                    transaction_number__isnull=False,
                    deleted_at__isnull=True,
                ),
            ),
        ]
