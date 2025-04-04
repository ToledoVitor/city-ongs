from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from accounts.models import BaseOrganizationTenantModel, User


class ActivityLog(BaseOrganizationTenantModel):
    class ActivityLogChoices(models.TextChoices):
        # accounts
        CREATED_CIVIL_SERVANT = (
            "CREATED_CIVIL_SERVANT",
            "Cadastrou funcionário público",
        )
        UPDATED_CIVIL_SERVANT = (
            "UPDATED_CIVIL_SERVANT",
            "Atualizou funcionário público",
        )
        DELETED_CIVIL_SERVANT = (
            "DELETED_CIVIL_SERVANT",
            "Deletou funcionário público",
        )
        CREATED_FOLDER_MANAGER = (
            "CREATED_FOLDER_MANAGER",
            "Cadastrou gestor de pasta",
        )
        UPDATED_FOLDER_MANAGER = (
            "UPDATED_FOLDER_MANAGER",
            "Atualizou gestor de pasta",
        )
        DELETED_FOLDER_MANAGER = (
            "DELETED_FOLDER_MANAGER",
            "Deletou gestor de pasta",
        )
        ACTIVATED_FOLDER_MANAGER = (
            "ACTIVATED_FOLDER_MANAGER",
            "Ativou gestor de pasta",
        )
        DESACTIVATED_FOLDER_MANAGER = (
            "DESACTIVATED_FOLDER_MANAGER",
            "Desativou gestor de pasta",
        )
        CREATED_ORGANIZATION_ACCOUNTANT = (
            "CREATED_ORGANIZATION_ACCOUNTANT",
            "Cadastrou contador / funcionário da organização",
        )
        UPDATED_ORGANIZATION_ACCOUNTANT = (
            "UPDATED_ORGANIZATION_ACCOUNTANT",
            "Atualizou contador / funcionário da organização",
        )
        DELETED_ORGANIZATION_ACCOUNTANT = (
            "DELETED_ORGANIZATION_ACCOUNTANT",
            "Deletou contador / funcionário da organização",
        )
        ACTIVATED_ORGANIZATION_ACCOUNTANT = (
            "ACTIVATED_ORGANIZATION_ACCOUNTANT",
            "Ativou contador / funcionário da organização",
        )
        DESACTIVATED_ORGANIZATION_ACCOUNTANT = (
            "DESACTIVATED_ORGANIZATION_ACCOUNTANT",
            "Desativou contador / funcionário da organização",
        )
        CREATED_ORGANIZATION_COMMITTEE = (
            "CREATED_ORGANIZATION_COMMITTEE",
            "Cadastrou membro do comitê",
        )
        UPDATED_ORGANIZATION_COMMITTEE = (
            "UPDATED_ORGANIZATION_COMMITTEE",
            "Atualizou membro do comitê",
        )
        DELETED_ORGANIZATION_COMMITTEE = (
            "DELETED_ORGANIZATION_COMMITTEE",
            "Deletou membro do comitê",
        )
        ACTIVATED_ORGANIZATION_COMMITTEE = (
            "ACTIVATED_ORGANIZATION_COMMITTEE",
            "Ativou membro do comitê",
        )
        DESACTIVATED_ORGANIZATION_COMMITTEE = (
            "DESACTIVATED_ORGANIZATION_COMMITTEE",
            "Desativou membro do comitê",
        )
        # accountability
        CREATED_ACCOUNTABILITY = (
            "CREATED_ACCOUNTABILITY",
            "Criou prestação mensal",
        )
        CREATED_ACCOUNTABILITY_FILE = (
            "CREATED_ACCOUNTABILITY_FILE",
            "Subiu documento de prestação",
        )
        DELETED_ACCOUNTABILITY_FILE = (
            "DELETED_ACCOUNTABILITY_FILE",
            "Deletou documento de prestação",
        )
        SENT_TO_ANALISYS = "SENT_TO_ANALISYS", "Enviou para análise"
        SENT_TO_CORRECT = "SENT_TO_CORRECT", "Enviou para correção"
        MARKED_AS_FINISHED = "MARKED_AS_FINISHED", "Marcou como finalizada"
        IMPORTED_ACCOUNTABILITY_FILE = (
            "IMPORTED_ACCOUNTABILITY_FILE",
            "Importou arquivo de prestação",
        )
        # Accountability files
        UPLOADED_EXPENSE_FILE = (
            "UPLOADED_EXPENSE_FILE",
            "Subiu arquivo de despesa",
        )
        UPLOADED_REVENUE_FILE = (
            "UPLOADED_REVENUE_FILE",
            "Subiu arquivo de receita",
        )
        DELETED_EXPENSE_FILE = (
            "DELETED_EXPENSE_FILE",
            "Deletou arquivo de despesa",
        )
        DELETED_REVENUE_FILE = (
            "DELETED_REVENUE_FILE",
            "Deletou arquivo de receita",
        )
        # bank
        CREATED_BANK_ACCOUNT = "CREATED_BANK_ACCOUNT", "Criou conta bancária"
        UPDATED_BANK_ACCOUNT = (
            "UPDATED_BANK_ACCOUNT",
            "Atualizou conta bancária",
        )
        UPLOADED_BALANCE_FILE = (
            "UPLOADED_BALANCE_FILE",
            "subiu extrato bancário",
        )
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
        # contract month transfer
        UPDATED_CONTRACT_MONTH_TRASNFER = (
            "UPDATED_CONTRACT_MONTH_TRASNFER",
            "Atualizou repasse mensal",
        )
        # contract goals
        CREATED_CONTRACT_GOAL = (
            "CREATED_CONTRACT_GOAL",
            "Cadastrou meta do contrato",
        )
        COMMENTED_CONTRACT_GOAL = (
            "COMMENTED_CONTRACT_GOAL",
            "Comentou meta do contrato",
        )
        UPDATED_CONTRACT_GOAL = (
            "UPDATED_CONTRACT_GOAL",
            "Atualizou meta do contrato",
        )
        # contract items
        CREATED_CONTRACT_ITEM = (
            "CREATED_CONTRACT_ITEM",
            "Cadastrou item do contrato",
        )
        COMMENTED_CONTRACT_ITEM = (
            "COMMENTED_CONTRACT_ITEM",
            "Comentou item do contrato",
        )
        UPDATED_CONTRACT_ITEM = (
            "UPDATED_CONTRACT_ITEM",
            "Atualizou item do contrato",
        )
        REQUEST_NEW_VALUE_ITEM = (
            "REQUEST_NEW_VALUE_ITEM",
            "Solicitou nova valor do item",
        )
        ANALISED_NEW_VALUE_ITEM = (
            "ANALISED_NEW_VALUE_ITEM",
            "Analisou pedido de novo valor do item",
        )
        # contract item supplements
        CREATED_CONTRACT_ITEM_SUPPLEMENT = (
            "CREATED_CONTRACT_ITEM_SUPPLEMENT",
            "Cadastrou suplemento de item",
        )
        UPDATED_CONTRACT_ITEM_SUPPLEMENT = (
            "UPDATED_CONTRACT_ITEM_SUPPLEMENT",
            "Atualizou suplemento de item",
        )
        DELETED_CONTRACT_ITEM_SUPPLEMENT = (
            "DELETED_CONTRACT_ITEM_SUPPLEMENT",
            "Deletou suplemento de item",
        )
        # contract item purchase activities
        UPLOADED_CONTRACT_ITEM_PURCHASE_FILE = (
            "UPLOADED_CONTRACT_ITEM_PURCHASE_FILE",
            "Subiu arquivo de compra de item",
        )
        DELETED_CONTRACT_ITEM_PURCHASE_FILE = (
            "DELETED_CONTRACT_ITEM_PURCHASE_FILE",
            "Deletou arquivo de compra de item",
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
        CREATED_EXECUTION_FILE = (
            "CREATED_EXECUTION_FILE",
            "Anexou Arquivo de Atividade",
        )
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
        DELETED_RESOURCES_SOURCE = (
            "DELETED_RESOURCES_SOURCE",
            "Apagou fonte de recurso",
        )
        # revenues
        CREATED_REVENUE = "CREATED_REVENUE", "Cadastrou receita"
        UPDATED_REVENUE = "UPDATED_REVENUE", "Atualizou receita"
        RECONCILED_REVENUE = "RECONCILED_REVENUE", "Conciliou receita"
        REVIEWED_REVENUE = "REVIEWED_REVENUE", "Revisou receita"
        DUPLICATED_REVENUE = "DUPLICATED_REVENUE", "Duplicou receita"
        DELETED_REVENUE = "DELETED_REVENUE", "Deletou receita"

    id = models.BigAutoField(primary_key=True)
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


class Notification(BaseOrganizationTenantModel):
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
        CONTRACT_STATUS = (
            "CONTRACT_STATUS",
            "O Status do contrato foi atualizado",
        )
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
