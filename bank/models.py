from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from accounts.models import BaseOrganizationTenantModel
from activity.models import ActivityLog
from utils.choices import MonthChoices


class BankAccount(BaseOrganizationTenantModel):
    class OriginChoices(models.TextChoices):
        MUNICIPAL = "MUNICIPAL", "Municipal"
        FEDERAL = "FEDERAL", "Federal"
        STATE = "STATE", "Estadual"
        COUNTERPART_PARTNER = (
            "COUNTERPART_PARTNER",
            "Contrapartida de parceiro",
        )
        PRIVATE_SPONSOR = "PRIVATE_SPONSOR", "Patrocinador privado"

    class AccountTypeChoices(models.TextChoices):
        CHECKING = "CHECKING", "Conta Corrente"
        INVESTING = "INVESTING", "Investimento"

    bank_name = models.CharField(
        verbose_name="Nome do Banco",
        max_length=128,
        help_text="Name of the bank or financial institution",
    )
    bank_id = models.IntegerField(
        verbose_name="Id do Banco",
        help_text="Bank identification number",
    )

    account = models.CharField(
        verbose_name="Número da Conta",
        max_length=16,
        help_text="Bank account number",
    )
    account_type = models.CharField(
        verbose_name="Tipo da Conta",
        max_length=9,
        choices=AccountTypeChoices.choices,
        default=AccountTypeChoices.CHECKING,
        help_text="Type of bank account (checking or investment)",
    )
    agency = models.CharField(
        verbose_name="Agência",
        max_length=128,
        blank=True,
        null=True,
        help_text="Bank branch/agency number",
    )
    balance = models.DecimalField(
        verbose_name="Saldo Atual",
        decimal_places=2,
        max_digits=12,
        default=Decimal("0.00"),
        help_text="Current account balance",
    )
    origin = models.CharField(
        verbose_name="Origem da Fonte",
        choices=OriginChoices,
        default=OriginChoices.MUNICIPAL,
        max_length=19,
        help_text="Source of funds for this account",
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"{self.bank_name} - {self.account} ({self.account_type_label})"

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=(
                    "organization",
                    "bank_name",
                    "account",
                    "account_type",
                ),
                name="unique_bank_account_per_organization",
            ),
        ]
        indexes = [
            models.Index(fields=["bank_name", "account"]),
            models.Index(fields=["account_type"]),
            models.Index(fields=["origin"]),
        ]

    def clean(self):
        """Validate the bank account data."""
        if self.balance < 0:
            raise ValidationError("Account balance cannot be negative")

        # Validate account number format
        if not self.account.isdigit():
            raise ValidationError("Account number must contain only digits")

    def save(self, *args, **kwargs):
        """Save the bank account after validation."""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def recent_logs(self):
        return ActivityLog.objects.filter(target_object_id=self.id)

    @property
    def account_type_label(self):
        return BankAccount.AccountTypeChoices(self.account_type).label

    @property
    def origin_label(self):
        return BankAccount.OriginChoices(self.origin).label

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


class BankStatement(BaseOrganizationTenantModel):
    """Model representing a bank statement with opening and closing balances."""

    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="Conta Bancária",
        related_name="statements",
        on_delete=models.CASCADE,
        help_text="The bank account this statement belongs to",
    )

    opening_balance = models.DecimalField(
        verbose_name="Saldo no Dia Inicial",
        decimal_places=2,
        max_digits=12,
        null=True,
        blank=True,
        help_text="The balance at the start of the statement period",
    )
    closing_balance = models.DecimalField(
        verbose_name="Saldo no Dia Final",
        decimal_places=2,
        max_digits=12,
        help_text="The balance at the end of the statement period",
    )

    reference_day = models.IntegerField(
        verbose_name="Dia de Referência",
        help_text="The day this statement refers to",
        null=True,
        blank=True,
    )
    reference_month = models.IntegerField(
        verbose_name="Mês",
        choices=MonthChoices,
        default=MonthChoices.JAN,
        help_text="The month this statement refers to",
    )
    reference_year = models.IntegerField(
        verbose_name="Ano",
        default=0,
        help_text="The year this statement refers to",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Extrato Bancário"
        verbose_name_plural = "Extratos Bancários"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("bank_account", "reference_month", "reference_year", "reference_day"),
                name="unique_bank_statement_per_month_year",
            ),
        ]
        indexes = [
            models.Index(fields=["bank_account", "reference_month", "reference_year"]),
            models.Index(fields=["reference_month", "reference_year"]),
        ]

    def clean(self):
        """Validate the statement data."""
        if self.closing_balance is not None and self.opening_balance is not None:
            if self.closing_balance < 0:
                raise ValidationError("Closing balance cannot be negative")
            if self.opening_balance < 0:
                raise ValidationError("Opening balance cannot be negative")

    def save(self, *args, **kwargs):
        """Save the statement after validation."""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def month_label(self):
        return MonthChoices(self.reference_month).label.capitalize()

    def __str__(self) -> str:
        return f"Statement for {self.month_label}/{self.reference_year} - {self.bank_account}"


class Transaction(BaseOrganizationTenantModel):
    """Model representing a bank transaction with its associated expenses/revenues."""

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
        help_text="The bank account this transaction belongs to",
    )

    amount = models.DecimalField(
        verbose_name="Valor da Transação",
        decimal_places=2,
        max_digits=12,
        help_text="The amount of the transaction (positive for credits, negative for debits)",
    )
    date = models.DateField(
        verbose_name="Data da Transação",
        help_text="The date when the transaction occurred",
    )

    transaction_type = models.CharField(
        verbose_name="Tipo da Transação",
        max_length=32,
        choices=TransactionTypeChoices.choices,
        default=TransactionTypeChoices.OTHER,
        help_text="The type of transaction (e.g., credit, debit, transfer)",
    )
    transaction_number = models.CharField(
        verbose_name="Id da Transação",
        max_length=32,
        null=True,
        blank=True,
        help_text="Unique identifier for the transaction from the bank",
    )

    name = models.CharField(
        verbose_name="Nome",
        max_length=128,
        null=True,
        blank=True,
        help_text="Description or name of the transaction",
    )
    memo = models.CharField(
        verbose_name="Notas Adicionais (opcional)",
        max_length=256,
        null=True,
        blank=True,
        help_text="Additional notes or comments about the transaction",
    )

    expense = models.ForeignKey(
        "accountability.Expense",
        verbose_name="Despesa",
        related_name="transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Associated expense record if this is an expense transaction",
    )
    revenue = models.ForeignKey(
        "accountability.Revenue",
        verbose_name="Receita",
        related_name="transactions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Associated revenue record if this is a revenue transaction",
    )

    expenses = models.ManyToManyField(
        "accountability.Expense",
        verbose_name="Despesas",
        related_name="bank_transactions",
        help_text="Multiple expenses associated with this transaction",
    )
    revenues = models.ManyToManyField(
        "accountability.Revenue",
        verbose_name="Receitas",
        related_name="bank_transactions",
        help_text="Multiple revenues associated with this transaction",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Movimentação Bancária"
        verbose_name_plural = "Movimentações Bancárias"
        indexes = [
            models.Index(fields=["bank_account", "date"]),
            models.Index(fields=["transaction_type", "date"]),
            models.Index(fields=["transaction_number"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["transaction_number", "memo", "bank_account"],
                name="unique_transaction_number_per_bank_account",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]
        ordering = ["-date", "-id"]

    def clean(self):
        """Validate the transaction data."""
        if self.transaction_number:
            # Check for duplicate transaction numbers
            existing = Transaction.objects.filter(
                transaction_number=self.transaction_number,
                bank_account=self.bank_account,
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "A transaction with this number already exists for this account"
                )

        # Validate that either expense or revenue is set, but not both
        if self.expense and self.revenue:
            raise ValidationError(
                "A transaction cannot be associated with both an expense and revenue"
            )

    def save(self, *args, **kwargs):
        """Save the transaction after validation."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.date} - {self.transaction_type} - {self.amount}"
