# Generated by Django 5.1.6 on 2025-03-09 21:19

from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contracts", "0016_contractmonthtransfer_month_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="contractaddendum",
            name="counterpart_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor repassado por contrapartida de parceiro",
            ),
        ),
        migrations.AddField(
            model_name="contractaddendum",
            name="municipal_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor repassado pelo município",
            ),
        ),
        migrations.AddField(
            model_name="contractaddendum",
            name="total_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor do contrato",
            ),
        ),
        migrations.AddField(
            model_name="historicalcontractaddendum",
            name="counterpart_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor repassado por contrapartida de parceiro",
            ),
        ),
        migrations.AddField(
            model_name="historicalcontractaddendum",
            name="municipal_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor repassado pelo município",
            ),
        ),
        migrations.AddField(
            model_name="historicalcontractaddendum",
            name="total_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor do contrato",
            ),
        ),
    ]
