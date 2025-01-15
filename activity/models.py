from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from accounts.models import User


class ActivityLog(models.Model):
    class ActivityLogChoices(models.TextChoices):
        # accounts
        CREATED_CIVIL_SERVANT = "CREATED_CIVIL_SERVANT", "criou funcionário público"
        CREATED_FOLDER_MANAGER = "CREATED_FOLDER_MANAGER", "criou gestor de pasta"
        CREATED_ONG_ACCOUNTANT = (
            "CREATED_ONG_ACCOUNTANT",
            "criou contador / funcionário ong",
        )
        # accountability
        CREATED_ACCOUNTABILITY = "CREATED_ACCOUNTABILITY", "criou contabilidade mês"
        UPDATED_ACCOUNTABILITY = "UPDATED_ACCOUNTABILITY", "atualizou contabilidade mês"
        # bank
        CREATED_BANK_ACCOUNT = "CREATED_BANK_ACCOUNT", "criou conta bancária"
        UPDATED_BANK_ACCOUNT = "UPDATED_BANK_ACCOUNT", "atualizou conta bancária"
        # contracts
        CREATED_CONTRACT = "CREATED_CONTRACT", "criou contrato"
        CREATED_CONTRACT_ADDENDUM = (
            "CREATED_CONTRACT_ADDENDUM",
            "criou aditivo de contrato",
        )
        # contract goals
        CREATED_CONTRACT_GOAL = "CREATED_CONTRACT_GOAL", "criou meta do contrato"
        UPDATED_CONTRACT_GOAL = "UPDATED_CONTRACT_GOAL", "atualizou meta do contrato"
        # contract items
        CREATED_CONTRACT_ITEM = "CREATED_CONTRACT_ITEM", "criou item do contrato"
        UPDATED_CONTRACT_ITEM = "UPDATED_CONTRACT_ITEM", "atualizou item do contrato"
        # expenses
        CREATE_EXPENSE_SOURCE = "CREATE_EXPENSE_SOURCE", "criou fonte de despesa"
        DELETED_EXPENSE_SOURCE = "DELETED_EXPENSE_SOURCE", "apagou fonte de despesa"
        # revenues
        CREATE_REVENUE_SOURCE = "CREATE_REVENUE_SOURCE", "criou fonte de recurso"
        DELETED_REVENUE_SOURCE = "DELETED_REVENUE_SOURCE", "apagou fonte de recurso"

    created_at = models.DateTimeField(
        verbose_name="Hora do registro",
        auto_now_add=True,
        editable=False,
    )

    user = models.ForeignKey(
        User,
        related_name="actions",
        on_delete=models.CASCADE,
    )
    user_email = models.CharField(
        verbose_name="Email do Usuário",
        max_length=32,
        null=True,
        blank=True,
    )

    action = models.CharField(
        verbose_name="Ação",
        choices=ActivityLogChoices,
        max_length=32,
    )

    target_content_type = models.ForeignKey(
        ContentType,
        verbose_name="Content Type do alvo",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    target_object_id = models.CharField(
        verbose_name="ID do alvo",
        max_length=32,
        null=True,
        blank=True,
    )
    target_content_object = GenericForeignKey("target_content_type", "target_object_id")

    def __str__(self) -> str:
        return f"{self.user_email} - {"self.action"}"

    @property
    def action_label(self) -> str:
        return ActivityLog.ActivityLogChoices(self.action).label

    class Meta:
        verbose_name = "Registro de Atividade"
        verbose_name = "Registro de Atividade"

        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user_email", "action"]),
        ]
