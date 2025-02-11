# Generated by Django 5.1.4 on 2025-02-06 00:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contracts", "0010_contractexecutionfile_execution_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="contractexecution",
            name="status",
            field=models.CharField(
                choices=[
                    ("WIP", "Em Andamento"),
                    ("SENT", "Enviada para análise"),
                    ("CORRECTING", "Corrigindo"),
                    ("FINISHED", "Finalizada"),
                ],
                default="WIP",
                max_length=10,
                verbose_name="Status",
            ),
        ),
    ]
