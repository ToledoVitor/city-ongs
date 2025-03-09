from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from accounts.models import User
from utils.models import BaseModel


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
        SENT_TO_ANALISYS = "SENT_TO_ANALISYS", "Enviou para análise"
        SENT_TO_CORRECT = "SENT_TO_CORRECT", "Enviou para correção"
        MARKED_AS_FINISHED = "MARKED_AS_FINISHED", "Marcou como finalizada"
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
        UPDATED_CONTRACT_STATUS = (
            "UPDATED_CONTRACT_STATUS",
            "Atualizou status do contrato",
        )
        # contract interested
        CREATED_CONTRACT_INTERESTED = (
            "CREATED_CONTRACT_INTERESTED",
            "Cadastrou interessado no contrato",
        )
        UPDATED_CONTRACT_INTERESTED = (
            "UPDATED_CONTRACT_INTERESTED",
            "Atualizou interessado no contrato",
        )
        DELETED_CONTRACT_INTERESTED = (
            "DELETED_CONTRACT_INTERESTED",
            "Deletou interessado no contrato",
        )
        # contract goals
        CREATED_CONTRACT_GOAL = "CREATED_CONTRACT_GOAL", "Cadastrou meta do contrato"
        COMMENTED_CONTRACT_GOAL = "COMMENTED_CONTRACT_GOAL", "Comentou meta do contrato"
        UPDATED_CONTRACT_GOAL = "UPDATED_CONTRACT_GOAL", "Atualizou meta do contrato"
        # contract items
        CREATED_CONTRACT_ITEM = "CREATED_CONTRACT_ITEM", "Cadastrou item do contrato"
        COMMENTED_CONTRACT_ITEM = "COMMENTED_CONTRACT_ITEM", "Comentou item do contrato"
        UPDATED_CONTRACT_ITEM = "UPDATED_CONTRACT_ITEM", "Atualizou item do contrato"
        REQUEST_NEW_VALUE_ITEM = (
            "REQUEST_NEW_VALUE_ITEM",
            "Solicitou nova valor do item",
        )
        ANALISED_NEW_VALUE_ITEM = (
            "ANALISED_NEW_VALUE_ITEM",
            "Analisou pedido de novo valor do item",
        )
        # contract executions
        CREATED_CONTRACT_EXECUTION = (
            "CREATED_CONTRACT_EXECUTION",
            "Criou relatório de execução",
        )
        EXECUTION_TO_ANALISYS = (
            "EXECUTION_TO_ANALISYS",
            "Enviou relatório para análise",
        )
        EXECUTION_SENT_TO_CORRECT = (
            "EXECUTION_SENT_TO_CORRECT",
            "Enviou relatório para correção",
        )
        EXECUTION_MARKED_AS_FINISHED = (
            "EXECUTION_MARKED_AS_FINISHED",
            "Marcou relatório como finalizada",
        )
        # contract executions activities
        CREATED_EXECUTION_ACTIVITY = (
            "CREATED_EXECUTION_ACTIVITY",
            "Criou Atividade Executada",
        )
        UPDATED_EXECUTION_ACTIVITY = (
            "UPDATED_EXECUTION_ACTIVITY",
            "Atualizou Atividade Executada",
        )
        # contract executions files
        CREATED_EXECUTION_FILE = "CREATED_EXECUTION_FILE", "Anexou Arquivo de Atividade"
        UPDATED_EXECUTION_FILE = (
            "UPDATED_EXECUTION_FILE",
            "Atualizou Arquivo de Atividade",
        )
        # expenses
        CREATED_EXPENSE = "CREATED_EXPENSE", "Cadastrou despesa"
        UPDATED_EXPENSE = "UPDATED_EXPENSE", "Atualizou despesa"
        GLOSSED_EXPENSE = "GLOSSED_EXPENSE", "Glosou despesa"
        RECONCILED_EXPENSE = "RECONCILED_EXPENSE", "Conciliou despesa"
        REVIEWED_EXPENSE = "REVIEWED_EXPENSE", "Revisou despesa"
        DUPLICATED_EXPENSE = "DUPLICATED_EXPENSE", "Duplicou despesa"
        DELETED_EXPENSE = "DELETED_EXPENSE", "Deletou despesa"
        # favored
        CREATED_FAVORED = "CREATED_FAVORED", "Cadastrou favorecido"
        UPDATED_FAVORED = "UPDATED_FAVORED", "Atualizou favorecido"
        DELETED_FAVORED = "DELETED_FAVORED", "Apagou favorecido"
        # sources
        CREATED_RESOURCES_SOURCE = (
            "CREATED_RESOURCES_SOURCE",
            "Cadastrou fonte de recurso",
        )
        UPDATED_RESOURCES_SOURCE = (
            "UPDATED_RESOURCES_SOURCE",
            "Atualizou fonte de recurso",
        )
        DELETED_RESOURCES_SOURCE = "DELETED_RESOURCES_SOURCE", "Apagou fonte de recurso"
        # revenues
        CREATED_REVENUE = "CREATED_REVENUE", "Cadastrou receita"
        UPDATED_REVENUE = "UPDATED_REVENUE", "Atualizou receita"
        RECONCILED_REVENUE = "RECONCILED_REVENUE", "Conciliou receita"
        REVIEWED_REVENUE = "REVIEWED_REVENUE", "Revisou receita"
        DUPLICATED_REVENUE = "DUPLICATED_REVENUE", "Duplicou receita"
        DELETED_REVENUE = "DELETED_REVENUE", "Deletou receita"

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
        max_length=128,
        null=True,
        blank=True,
    )

    action = models.CharField(
        verbose_name="Ação",
        choices=ActivityLogChoices,
        max_length=128,
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
        max_length=128,
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


class Notification(BaseModel):
    class Category(models.TextChoices):
        ACCOUNTABILITY_CREATED = (
            "ACCOUNTABILITY_CREATED",
            "Uma nova prestação foi criada",
        )
        ACCOUNTABILITY_ANALISYS = (
            "ACCOUNTABILITY_ANALISYS",
            "Prestação enviada para análise",
        )
        ACCOUNTABILITY_CORRECTING = (
            "ACCOUNTABILITY_CORRECTING",
            "Prestação enviada para correção",
        )
        ACCOUNTABILITY_FINISHED = (
            "ACCOUNTABILITY_FINISHED",
            "Prestação marcada como finalizada",
        )
        CONTRACT_CREATED = "CONTRACT_CREATED", "Um novo contrato foi criado"
        CONTRACT_STATUS = "CONTRACT_STATUS", "O Status do contrato foi atualizado"
        CONTRACT_GOAL_COMMENTED = (
            "CONTRACT_GOAL_COMMENTED",
            "Meta do contrato comentada",
        )
        CONTRACT_ITEM_COMMENTED = (
            "CONTRACT_ITEM_COMMENTED",
            "Item do contrato comentada",
        )
        CONTRACT_ITEM_VALUE_REQUESTED = (
            "CONTRACT_ITEM_VALUE_REQUESTED",
            "Pedido de remanejamento de gastos feito",
        )
        CONTRACT_ITEM_VALUE_REVIEWED = (
            "CONTRACT_ITEM_VALUE_REVIEWED",
            "Pedido de remanejamento de gastos revisado",
        )
        EXECUTION_ANALISYS = (
            "EXECUTION_ANALISYS",
            "Execução enviada para análise",
        )
        EXECUTION_CORRECTING = (
            "EXECUTION_CORRECTING",
            "Execução enviada para correção",
        )
        EXECUTION_FINISHED = (
            "EXECUTION_FINISHED",
            "Execução marcada como finalizada",
        )

    recipient = models.ForeignKey(
        User,
        verbose_name="Destinatário",
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    read_at = models.DateTimeField(
        verbose_name="Lida em:",
        null=True,
        blank=True,
    )

    category = models.CharField(
        verbose_name="Categoria",
        choices=Category.choices,
        max_length=32,
    )
    object_id = models.UUIDField(
        verbose_name="ID do objeto",
    )
    text = models.CharField(
        verbose_name="Texto",
        max_length=255,
    )

    @property
    def category_label(self) -> str:
        return Notification.Category(self.category).label

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
