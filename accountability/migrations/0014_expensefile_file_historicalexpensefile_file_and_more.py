# Generated by Django 5.1.4 on 2025-02-08 21:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accountability", "0013_remove_historicalaccountabilityfile_expense_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="expensefile",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="uploads/expenses/",
                verbose_name="Arquivo",
            ),
        ),
        migrations.AddField(
            model_name="historicalexpensefile",
            name="file",
            field=models.TextField(
                blank=True, max_length=100, null=True, verbose_name="Arquivo"
            ),
        ),
        migrations.AddField(
            model_name="historicalrevenuefile",
            name="file",
            field=models.TextField(
                blank=True, max_length=100, null=True, verbose_name="Arquivo"
            ),
        ),
        migrations.AddField(
            model_name="revenuefile",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="uploads/revenues/",
                verbose_name="Arquivo",
            ),
        ),
        migrations.AlterField(
            model_name="expensefile",
            name="expense",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="files",
                to="accountability.expense",
                verbose_name="Despesa",
            ),
        ),
        migrations.AlterField(
            model_name="revenuefile",
            name="revenue",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="files",
                to="accountability.revenue",
                verbose_name="Recurso",
            ),
        ),
    ]
