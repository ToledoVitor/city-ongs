# Generated by Django 5.1.6 on 2025-03-22 14:47

import uuid

import django.db.models.deletion
import django.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_alter_area_organization"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationTenantBaseClass",
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
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        help_text="The organization associated with this tenant.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_related",
                        to="accounts.organization",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
