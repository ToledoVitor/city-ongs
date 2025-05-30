# Generated by Django 5.1.6 on 2025-03-08 01:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="password_redefined",
            field=models.BooleanField(
                default=False,
                help_text="Usuário já mudou a senha inicial?",
                verbose_name="Senha Redefinida",
            ),
        ),
    ]
