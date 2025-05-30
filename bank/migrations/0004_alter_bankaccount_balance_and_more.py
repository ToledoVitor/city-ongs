# Generated by Django 5.1.6 on 2025-03-10 18:40

from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "bank",
            "0003_remove_historicaltransaction_destination_source_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="bankaccount",
            name="balance",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Saldo Atual",
            ),
        ),
        migrations.AlterField(
            model_name="historicalbankaccount",
            name="balance",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Saldo Atual",
            ),
        ),
    ]
