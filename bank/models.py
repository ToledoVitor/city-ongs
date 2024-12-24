from django.db import models

from utils.choices import MonthChoices
from utils.models import BaseModel
from simple_history.models import HistoricalRecords
from contracts.models import Contract


class Account(BaseModel):
    bank_name = models.CharField(verbose_name="Nome do Banco", max_length=128)
    account = models.IntegerField(verbose_name="Número da Conta")
    agency = models.CharField(verbose_name="Agência", max_length=128)
    balance = models.DecimalField(
        verbose_name="Saldo Atual",
        decimal_places=2,
        max_digits=12,
    )

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="accounts",
        on_delete=models.CASCADE,
        null=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"


class BankStatement(BaseModel):
    # file
    month = models.IntegerField(
        verbose_name="Mês",
        choices=MonthChoices,
        default=MonthChoices.JAN,
    )
    opening_balance = models.DecimalField(
        verbose_name="Valor Inicial",
        decimal_places=2,
        max_digits=12,
    )
    closing_balance = models.DecimalField(
        verbose_name="Valor Final",
        decimal_places=2,
        max_digits=12,
    )

    account = models.ForeignKey(
        Account,
        verbose_name="Conta Bancária",
        related_name="bank_statement",
        on_delete=models.CASCADE,
        null=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Extrato Bancário"
        verbose_name_plural = "Extratos Bancários"


class Transactions(BaseModel):
    source = models.CharField(verbose_name="Origem", max_length=128)
    destination = models.CharField(verbose_name="Destino", max_length=128)
    amount = models.DecimalField(
        verbose_name="Valor da Transação",
        decimal_places=2,
        max_digits=12,
    )

    bank_statement = models.ForeignKey(
        BankStatement,
        verbose_name="Extrato Bancário",
        related_name="transactions",
        on_delete=models.CASCADE,
        null=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Movimentação Bancária"
        verbose_name_plural = "Movimentações Bancárias"
