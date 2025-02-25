import logging
from typing import Callable, Tuple

from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string

from accountability.models import Accountability
from activity.models import ActivityLog, Notification
from contracts.models import (
    Contract,
    ContractGoal,
    ContractItem,
    ContractItemNewValueRequest,
)
from sendgrid_client.client import SendGridClient
from utils.formats import format_into_brazilian_currency

logger = logging.getLogger(__name__)


class ActivityLogEmailNotificationHandler:
    website_url = settings.WEBSITE_URL

    def get_notification_content_builder(
        self, activity_log: ActivityLog
    ) -> Callable | None:
        builders_mapper = {
            # Accountability
            ActivityLog.ActivityLogChoices.CREATED_ACCOUNTABILITY: self.build_accountability_created_log,
            ActivityLog.ActivityLogChoices.SENT_TO_ANALISYS: self.build_accountability_analisys_log,
            ActivityLog.ActivityLogChoices.SENT_TO_CORRECT: self.build_accountability_correct_log,
            # ActivityLog.ActivityLogChoices.MARKED_AS_FINISHED: self.build_accountability_finished_log,
            # Contract
            ActivityLog.ActivityLogChoices.CREATED_CONTRACT: self.build_contract_created_log,
            ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_STATUS: self.build_contract_status_log,
            # Contract Goal
            ActivityLog.ActivityLogChoices.COMMENTED_CONTRACT_GOAL: self.build_goal_comented_log,
            # Contract Item
            ActivityLog.ActivityLogChoices.COMMENTED_CONTRACT_ITEM: self.build_item_comented_log,
            ActivityLog.ActivityLogChoices.REQUEST_NEW_VALUE_ITEM: self.build_item_value_request_log,
            ActivityLog.ActivityLogChoices.ANALISED_NEW_VALUE_ITEM: self.build_item_value_analised_log,
        }
        return builders_mapper.get(activity_log.action, None)

    def handle_log_creation(self, activity_log: ActivityLog) -> None:
        if builder := self.get_notification_content_builder(activity_log):
            with transaction.atomic():
                subject, html_content, recipients = builder(activity_log)

                if not all([subject, html_content, recipients]):
                    logger.error(
                        f"Unable to notify for {activity_log.action}, parameters \n "
                        f"subject: {subject} \n"
                        f"html_content: {html_content} \n"
                        f"recipients: {recipients} \n"
                    )

                logger.info(f"Notifying users for action {activity_log.action}")

            try:
                sendgrid_client = SendGridClient()
                sendgrid_client.notify(
                    subject=subject,
                    html_content=html_content,
                    recipients=recipients,
                )
            except Exception as error:
                logger.error(f"Error when sending email notification: {error}")

    def build_accountability_created_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        accountability: Accountability = activity_log.target_content_object
        contract: Contract = accountability.contract

        subject = "Nova Prestação Iniciada"
        context = {
            "period": f"{accountability.month}/{accountability.year}",
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/accountability/detail/{accountability.id}/",
        }
        html_content = render_to_string("email/new_accountability_email.html", context)

        recipient = accountability.contract.supervision_autority
        Notification.objects.create(
            category=Notification.Category.ACCOUNTABILITY_CREATED,
            recipient=recipient,
            object_id=accountability.id,
            text=f"Prestação {accountability.month}/{accountability.year} para o contrato {contract.name} iniciada",
        )
        recipients = [recipient]

        return subject, html_content, recipients

    def build_accountability_analisys_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        accountability: Accountability = activity_log.target_content_object
        contract: Contract = accountability.contract

        subject = "Prestação Enviada para Análise"
        context = {
            "period": f"{accountability.month}/{accountability.year}",
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/accountability/detail/{accountability.id}/",
        }
        html_content = render_to_string(
            "email/accountability_analisys_email.html", context
        )

        recipient = accountability.contract.supervision_autority
        Notification.objects.create(
            category=Notification.Category.ACCOUNTABILITY_ANALISYS,
            recipient=recipient,
            object_id=accountability.id,
            text=f"Prestação {accountability.month}/{accountability.year} para o contrato {contract.name} enviada para análise",
        )
        recipients = [recipient]

        return subject, html_content, recipients

    def build_accountability_correct_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        accountability: Accountability = activity_log.target_content_object
        contract: Contract = accountability.contract

        subject = "Prestação Enviada para Correção"
        context = {
            "period": f"{accountability.month}/{accountability.year}",
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/accountability/detail/{accountability.id}/",
        }
        html_content = render_to_string(
            "email/accountability_correcting_email.html", context
        )

        recipient = accountability.contract.accountability_autority
        Notification.objects.create(
            category=Notification.Category.ACCOUNTABILITY_CORRECTING,
            recipient=recipient,
            object_id=accountability.id,
            text=f"Prestação {accountability.month}/{accountability.year} para o contrato {contract.name} enviada para correção",
        )
        recipients = [recipient]

        return subject, html_content, recipients

    def build_accountability_finished_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        accountability: Accountability = activity_log.target_content_object
        contract: Contract = accountability.contract

        subject = "Prestação Finalizada"
        context = {
            "period": f"{accountability.month}/{accountability.year}",
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/accountability/detail/{accountability.id}/",
        }
        html_content = render_to_string(
            "email/accountability_finished_email.html", context
        )

        recipient = accountability.contract.accountability_autority
        Notification.objects.create(
            category=Notification.Category.ACCOUNTABILITY_FINISHED,
            recipient=recipient,
            object_id=accountability.id,
            text=f"Prestação {accountability.month}/{accountability.year} para o contrato {contract.name} enviada para correção",
        )
        recipients = [recipient]

        return subject, html_content, recipients

    def build_contract_created_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        contract: Contract = activity_log.target_content_object

        subject = "Novo contrato cadastrado"
        context = {
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/contracts/detail/{contract.id}/",
        }
        html_content = render_to_string("email/new_contract_email.html", context)

        recipients = [contract.accountability_autority, contract.supervision_autority]
        for recipient in recipients:
            if recipient is None:
                continue

            Notification.objects.create(
                category=Notification.Category.CONTRACT_CREATED,
                recipient=recipient,
                object_id=contract.id,
                text=f"Novo contrato cadastrado por {activity_log.user_email}",
            )

        return subject, html_content, recipients

    def build_contract_status_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        contract: Contract = activity_log.target_content_object

        subject = "Status do Contrato Atualizado"
        context = {
            "contract_name": contract.name,
            "contract_status": contract.status_label,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/contracts/detail/{contract.id}/",
        }
        html_content = render_to_string("email/new_contract_status_email.html", context)

        recipients = [contract.accountability_autority, contract.supervision_autority]
        for recipient in recipients:
            if recipient is None:
                continue

            Notification.objects.create(
                category=Notification.Category.CONTRACT_STATUS,
                recipient=recipient,
                object_id=contract.id,
                text=f"Status do contrato atualizado por {activity_log.user_email}",
            )

        return subject, html_content, recipients

    def build_goal_comented_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        goal: ContractGoal = activity_log.target_content_object
        contract: Contract = goal.contract

        subject = "Meta do Contrato Comentada"
        context = {
            "goal": goal.name,
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/contracts/detail/{contract.id}/",
        }
        html_content = render_to_string("email/contract_goal_commented.html", context)

        recipient = contract.accountability_autority
        Notification.objects.create(
            category=Notification.Category.CONTRACT_GOAL_COMMENTED,
            recipient=recipient,
            object_id=contract.id,
            text=f"Meta do contrato comentada por {activity_log.user_email}",
        )
        recipients = [recipient]

        return subject, html_content, recipients

    def build_item_comented_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        item: ContractItem = activity_log.target_content_object
        contract: Contract = item.contract

        subject = "Item do Contrato Comentado"
        context = {
            "item": item.name,
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/contracts/detail/{contract.id}/",
        }
        html_content = render_to_string("email/contract_item_commented.html", context)

        recipient = contract.accountability_autority
        Notification.objects.create(
            category=Notification.Category.CONTRACT_ITEM_COMMENTED,
            recipient=recipient,
            object_id=contract.id,
            text=f"Meta do contrato comentada por {activity_log.user_email}",
        )
        recipients = [recipient]

        return subject, html_content, recipients

    def build_item_value_request_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        value_request: ContractItemNewValueRequest = activity_log.target_content_object
        contract: Contract = value_request.raise_item.contract

        subject = "Novo Pedido de Remanejamento de Gastos"
        context = {
            "raise_item": value_request.raise_item.name,
            "downgrade_item": value_request.downgrade_item.name,
            "month_raise": format_into_brazilian_currency(value_request.month_raise),
            "anual_raise": format_into_brazilian_currency(value_request.anual_raise),
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/contracts/detail/{contract.id}/",
        }
        html_content = render_to_string("email/new_value_requested.html", context)

        recipient = contract.supervision_autority
        Notification.objects.create(
            category=Notification.Category.CONTRACT_ITEM_VALUE_REQUESTED,
            recipient=recipient,
            object_id=contract.id,
            text=f"Pedido de remanejamento de gastos feito por {activity_log.user_email}",
        )
        recipients = [recipient]

        return subject, html_content, recipients

    def build_item_value_analised_log(
        self, activity_log: ActivityLog
    ) -> Tuple[str, str, list[str]]:
        value_request: ContractItemNewValueRequest = activity_log.target_content_object
        contract: Contract = value_request.raise_item.contract

        subject = "Pedido de Remanejamento de Gastos Revisado"
        context = {
            "raise_item": value_request.raise_item.name,
            "downgrade_item": value_request.downgrade_item.name,
            "status": value_request.status_label,
            "contract_name": contract.name,
            "created_by": activity_log.user_email,
            "link": f"{self.website_url}/contracts/detail/{contract.id}/",
        }
        html_content = render_to_string("email/new_value_reviewed.html", context)

        recipient = contract.accountability_autority
        Notification.objects.create(
            category=Notification.Category.CONTRACT_ITEM_VALUE_REVIEWED,
            recipient=recipient,
            object_id=contract.id,
            text=f"Pedido de remanejamento de gastos revisado por {activity_log.user_email}",
        )
        recipients = [recipient]

        return subject, html_content, recipients
