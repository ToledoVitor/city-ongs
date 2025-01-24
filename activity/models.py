from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from accounts.models import User


class ActivityLog(models.Model):
    class ActivityLogChoices(models.TextChoices):
        # accounts
        CREATED_CIVIL_SERVANT = "CREATED_CIVIL_SERVANT", "Criou funcionário público"
        CREATED_FOLDER_MANAGER = "CREATED_FOLDER_MANAGER", "Criou gestor de pasta"
        CREATED_ORGANIZATION_ACCOUNTANT = (
            "CREATED_ORGANIZATION_ACCOUNTANT",
            "Criou contador / funcionário organização",
        )
        # accountability
        CREATED_ACCOUNTABILITY = "CREATED_ACCOUNTABILITY", "Criou prestação mensal"
        UPDATED_ACCOUNTABILITY = "UPDATED_ACCOUNTABILITY", "Atualizou prestação mensal"
        # bank
        CREATED_BANK_ACCOUNT = "CREATED_BANK_ACCOUNT", "Criou conta bancária"
        UPDATED_BANK_ACCOUNT = "UPDATED_BANK_ACCOUNT", "Atualizou conta bancária"
        UPLOADED_BALANCE_FILE = "UPLOADED_BALANCE_FILE", "subiu extrato bancário"
        # company
        CREATED_COMPANY = "CREATED_COMPANY", "Criou empresa"
        UPDATED_COMPANY = "UPDATED_COMPANY", "Atualizou empresa"
        # contracts
        CREATED_CONTRACT = "CREATED_CONTRACT", "Criou contrato"
        CREATED_CONTRACT_ADDENDUM = (
            "CREATED_CONTRACT_ADDENDUM",
            "Criou aditivo de contrato",
        )
        # contract goals
        CREATED_CONTRACT_GOAL = "CREATED_CONTRACT_GOAL", "Cadastrou meta do contrato"
        UPDATED_CONTRACT_GOAL = "UPDATED_CONTRACT_GOAL", "Atualizou meta do contrato"
        # contract items
        CREATED_CONTRACT_ITEM = "CREATED_CONTRACT_ITEM", "Cadastrou item do contrato"
        UPDATED_CONTRACT_ITEM = "UPDATED_CONTRACT_ITEM", "Atualizou item do contrato"
        # expenses
        CREATED_EXPENSE = "CREATED_EXPENSE", "Cadastrou despesa"
        UPDATED_EXPENSE = "UPDATED_EXPENSE", "Atualizou despesa"
        CREATED_EXPENSE_SOURCE = "CREATED_EXPENSE_SOURCE", "Cadastrou fonte de despesa"
        DELETED_EXPENSE_SOURCE = "DELETED_EXPENSE_SOURCE", "Apagou fonte de despesa"
        # revenues
        CREATED_REVENUE = "CREATED_REVENUE", "Cadastrou receita"
        UPDATED_REVENUE = "UPDATED_REVENUE", "Atualizou receita"
        CREATED_REVENUE_SOURCE = "CREATED_REVENUE_SOURCE", "Cadastrou fonte de recurso"
        DELETED_REVENUE_SOURCE = "DELETED_REVENUE_SOURCE", "Apagou fonte de recurso"

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
