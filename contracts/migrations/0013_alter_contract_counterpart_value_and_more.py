# Generated by Django 5.1.6 on 2025-03-08 22:59

from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "contracts",
            "0012_contract_counterpart_value_contract_municipal_value_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="contract",
            name="counterpart_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor repassado por contrapartida de parceiro",
            ),
        ),
        migrations.AlterField(
            model_name="contract",
            name="municipal_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor repassado pelo município",
            ),
        ),
        migrations.AlterField(
            model_name="historicalcontract",
            name="counterpart_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor repassado por contrapartida de parceiro",
            ),
        ),
        migrations.AlterField(
            model_name="historicalcontract",
            name="municipal_value",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                verbose_name="Valor repassado pelo município",
            ),
        ),
    ]
