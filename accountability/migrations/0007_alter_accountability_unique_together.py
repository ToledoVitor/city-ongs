# Generated by Django 5.1.4 on 2025-02-05 18:51

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accountability", "0006_alter_accountability_status_and_more"),
        ("contracts", "0006_contractexecutionfile_contractexecution_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="accountability",
            unique_together={("contract", "month", "year")},
        ),
    ]
