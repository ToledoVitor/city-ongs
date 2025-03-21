# Generated by Django 5.1.6 on 2025-03-12 14:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accountability", "0008_remove_expense_transaction_and_more"),
        ("bank", "0005_remove_transaction_unique__transaction_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="expenses",
            field=models.ManyToManyField(
                related_name="bank_transactions",
                to="accountability.expense",
                verbose_name="Despesas",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="revenues",
            field=models.ManyToManyField(
                related_name="bank_transactions",
                to="accountability.revenue",
                verbose_name="Receitas",
            ),
        ),
    ]
