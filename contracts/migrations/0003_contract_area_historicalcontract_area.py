# Generated by Django 5.1.4 on 2024-12-30 17:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_area_city_hall_historicalarea_city_hall"),
        ("contracts", "0002_contract_code_historicalcontract_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="area",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="contracts",
                to="accounts.area",
                verbose_name="Area",
            ),
        ),
        migrations.AddField(
            model_name="historicalcontract",
            name="area",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="accounts.area",
                verbose_name="Area",
            ),
        ),
    ]