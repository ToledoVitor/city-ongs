# Generated by Django 5.1.6 on 2025-03-22 23:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0012_alter_cityhall_unique_together_and_more"),
        (
            "bank",
            "0009_alter_transaction_options_alter_bankaccount_account_and_more",
        ),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="bankaccount",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="bankaccount",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted_at__isnull", True)),
                fields=(
                    "organization",
                    "bank_name",
                    "account",
                    "account_type",
                ),
                name="unique_bank_account_per_organization",
            ),
        ),
    ]
