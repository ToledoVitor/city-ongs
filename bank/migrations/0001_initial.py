# Generated by Django 5.1.4 on 2024-12-24 15:54

import uuid

import django.db.models.deletion
import django.db.models.fields
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contracts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                        verbose_name=django.db.models.fields.UUIDField,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "bank_name",
                    models.CharField(max_length=128, verbose_name="Nome do Banco"),
                ),
                ("account", models.IntegerField(verbose_name="Número da Conta")),
                ("agency", models.CharField(max_length=128, verbose_name="Agência")),
                (
                    "balance",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Saldo Atual"
                    ),
                ),
                (
                    "contract",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accounts",
                        to="contracts.contract",
                        verbose_name="Contrato",
                    ),
                ),
            ],
            options={
                "verbose_name": "Conta Bancária",
                "verbose_name_plural": "Contas Bancárias",
            },
        ),
        migrations.CreateModel(
            name="BankStatement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                        verbose_name=django.db.models.fields.UUIDField,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "month",
                    models.IntegerField(
                        choices=[
                            (1, "janeiro"),
                            (2, "fevereiro"),
                            (3, "março"),
                            (4, "abril"),
                            (5, "maio"),
                            (6, "junho"),
                            (7, "julho"),
                            (8, "agosto"),
                            (9, "setembro"),
                            (10, "outubro"),
                            (11, "novembro"),
                            (12, "dezembro"),
                        ],
                        default=1,
                        verbose_name="Mês",
                    ),
                ),
                (
                    "opening_balance",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Valor Inicial"
                    ),
                ),
                (
                    "closing_balance",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Valor Final"
                    ),
                ),
                (
                    "account",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bank_statement",
                        to="bank.account",
                        verbose_name="Conta Bancária",
                    ),
                ),
            ],
            options={
                "verbose_name": "Extrato Bancário",
                "verbose_name_plural": "Extratos Bancários",
            },
        ),
        migrations.CreateModel(
            name="HistoricalAccount",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        verbose_name=django.db.models.fields.UUIDField,
                    ),
                ),
                ("created_at", models.DateTimeField(blank=True, editable=False)),
                ("updated_at", models.DateTimeField(blank=True, editable=False)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "bank_name",
                    models.CharField(max_length=128, verbose_name="Nome do Banco"),
                ),
                ("account", models.IntegerField(verbose_name="Número da Conta")),
                ("agency", models.CharField(max_length=128, verbose_name="Agência")),
                (
                    "balance",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Saldo Atual"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "contract",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="contracts.contract",
                        verbose_name="Contrato",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Conta Bancária",
                "verbose_name_plural": "historical Contas Bancárias",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalBankStatement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        verbose_name=django.db.models.fields.UUIDField,
                    ),
                ),
                ("created_at", models.DateTimeField(blank=True, editable=False)),
                ("updated_at", models.DateTimeField(blank=True, editable=False)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "month",
                    models.IntegerField(
                        choices=[
                            (1, "janeiro"),
                            (2, "fevereiro"),
                            (3, "março"),
                            (4, "abril"),
                            (5, "maio"),
                            (6, "junho"),
                            (7, "julho"),
                            (8, "agosto"),
                            (9, "setembro"),
                            (10, "outubro"),
                            (11, "novembro"),
                            (12, "dezembro"),
                        ],
                        default=1,
                        verbose_name="Mês",
                    ),
                ),
                (
                    "opening_balance",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Valor Inicial"
                    ),
                ),
                (
                    "closing_balance",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Valor Final"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "account",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="bank.account",
                        verbose_name="Conta Bancária",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Extrato Bancário",
                "verbose_name_plural": "historical Extratos Bancários",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalTransactions",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        verbose_name=django.db.models.fields.UUIDField,
                    ),
                ),
                ("created_at", models.DateTimeField(blank=True, editable=False)),
                ("updated_at", models.DateTimeField(blank=True, editable=False)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                ("source", models.CharField(max_length=128, verbose_name="Origem")),
                (
                    "destination",
                    models.CharField(max_length=128, verbose_name="Destino"),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        verbose_name="Valor da Transação",
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "bank_statement",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="bank.bankstatement",
                        verbose_name="Extrato Bancário",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Movimentação Bancária",
                "verbose_name_plural": "historical Movimentações Bancárias",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="Transactions",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        primary_key=True,
                        serialize=False,
                        verbose_name=django.db.models.fields.UUIDField,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                ("source", models.CharField(max_length=128, verbose_name="Origem")),
                (
                    "destination",
                    models.CharField(max_length=128, verbose_name="Destino"),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        verbose_name="Valor da Transação",
                    ),
                ),
                (
                    "bank_statement",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to="bank.bankstatement",
                        verbose_name="Extrato Bancário",
                    ),
                ),
            ],
            options={
                "verbose_name": "Movimentação Bancária",
                "verbose_name_plural": "Movimentações Bancárias",
            },
        ),
    ]
