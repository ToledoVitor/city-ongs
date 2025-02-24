from typing import Callable, Tuple
import logging

from django.db import transaction
from django.conf import settings
from activity.models import ActivityLog, Notification
from contracts.models import Contract
from sendgrid_client.client import SendGridClient


logger = logging.getLogger(__name__)


class ActivityLogEmailNotificationHandler:
    website_url = settings.WEBSITE_URL

    def get_notification_content_builder(self, activity_log: ActivityLog) -> Callable | None:
        builders_mapper = {
            # Accountability
            ActivityLog.ActivityLogChoices.CREATED_ACCOUNTABILITY: self.build_accountability_created_log,
            ActivityLog.ActivityLogChoices.SENT_TO_ANALISYS: self.build_accountability_analisys_log,
            ActivityLog.ActivityLogChoices.SENT_TO_CORRECT: self.build_accountability_correct_log,
            ActivityLog.ActivityLogChoices.MARKED_AS_FINISHED: self.build_accountability_finished_log,
            # Contract
            ActivityLog.ActivityLogChoices.CREATED_CONTRACT: self.build_contract_created_log,
            ActivityLog.ActivityLogChoices.UPDATED_CONTRACT_STATUS: self.build_contract_status_log,
            # Contract Goal
            ActivityLog.ActivityLogChoices.COMMENTED_CONTRACT_GOAL : self.build_goal_comented_log,
            # Contract Item
            ActivityLog.ActivityLogChoices.COMMENTED_CONTRACT_ITEM : self.build_item_comented_log,
            ActivityLog.ActivityLogChoices.REQUEST_NEW_VALUE_ITEM : self.build_item_request_log,
            ActivityLog.ActivityLogChoices.ANALISED_NEW_VALUE_ITEM : self.build_item_analised_log,
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

            sendgrid_client = SendGridClient()
            sendgrid_client.notify(
                subject=subject,
                html_content=html_content,
                recipients=recipients,
            )

    def build_accountability_created_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...

    def build_accountability_analisys_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...

    def build_accountability_correct_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...

    def build_accountability_finished_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...

    def build_contract_created_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        contract: Contract = activity_log.target_content_object

        subject = "Novo contrato cadastrado"
        html_content = f"""
            <p class="header">Olá,</p>
            <p class="content">
                Um novo contrato foi cadastrado por {activity_log.user_email}.
                Confira os detalhes clicando no botão abaixo:
            </p>
            <div class="button-container">
                <a href="{self.website_url}/contracts/" class="button">Ver Contrato</a>
            </div>
            <p class="footer">Este é um e-mail automático. Por favor, não responda.</p>
        """
        recipients = [contract.accountability_autority, contract.supervision_autority]

        for recipient in recipients:
            if recipient is None:
                continue

            Notification.objects.create(
                category=Notification.Category.CONTRACT_CREATED,
                recipient=recipient,
                object_id=contract.id,
                text=f"Olá {recipient.cpf}, o usuário {activity_log.user_email} cadastrou um novo contrato",
            )

        return subject, html_content, recipients

    def build_contract_status_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...

    def build_goal_comented_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...

    def build_item_comented_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...

    def build_item_request_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...

    def build_item_analised_log(self, activity_log: ActivityLog) -> Tuple[str, str, list[str]]:
        ...
    