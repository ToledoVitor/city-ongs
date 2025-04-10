# Generated by Django 5.1.6 on 2025-03-15 15:21

import uuid

import django.db.models.deletion
import django.db.models.fields
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accountability", "0009_alter_resourcesource_origin"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountabilityFile",
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
                    "file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="uploads/accountabilities/",
                        verbose_name="Arquivo",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        max_length=128,
                        null=True,
                        verbose_name="Nome do Arquivo",
                    ),
                ),
                (
                    "accountability",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="files",
                        to="accountability.accountability",
                        verbose_name="Prestação",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="accountability_files",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Arquivo de Prestação",
                "verbose_name_plural": "Arquivo de Prestações",
            },
        ),
        migrations.CreateModel(
            name="HistoricalAccountabilityFile",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        verbose_name=django.db.models.fields.UUIDField,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(blank=True, editable=False),
                ),
                (
                    "updated_at",
                    models.DateTimeField(blank=True, editable=False),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "file",
                    models.TextField(
                        blank=True,
                        max_length=100,
                        null=True,
                        verbose_name="Arquivo",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        max_length=128,
                        null=True,
                        verbose_name="Nome do Arquivo",
                    ),
                ),
                (
                    "history_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("history_date", models.DateTimeField(db_index=True)),
                (
                    "history_change_reason",
                    models.CharField(max_length=100, null=True),
                ),
                (
                    "history_type",
                    models.CharField(
                        choices=[
                            ("+", "Created"),
                            ("~", "Changed"),
                            ("-", "Deleted"),
                        ],
                        max_length=1,
                    ),
                ),
                (
                    "accountability",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="accountability.accountability",
                        verbose_name="Prestação",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Arquivo de Prestação",
                "verbose_name_plural": "historical Arquivo de Prestações",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
