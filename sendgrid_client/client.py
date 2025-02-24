from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sendgrid_client.email_template import template

from django.conf import settings

import logging


logger = logging.getLogger(__name__)


class SendGridClient:
    def __init__(self) -> None:
        self.sendgrid_api_key = settings.SENDGRID_API_KEY
        self.sendgrid_account_sender = settings.SENDGRID_ACCOUNT_SENDER

    def _replace_content(self, html_content) -> str:
        return template.replace("$content$", html_content)

    def notify(self, subject: str, html_content: str, recipients: list[str]):
        if not (
            self.sendgrid_api_key and self.sendgrid_account_sender
        ):
            logger.error("Missing sendgrid credentials for sending email.")
            return

        if not (
            subject and html_content
        ):
            logger.error("Missing subject or html content", subject, html_content)
            return

        replaced_content = self._replace_content(html_content)
        message = Mail(
            from_email=self.sendgrid_account_sender,
            to_emails=recipients,
            subject=replaced_content,
            html_content=html_content,
        )
        try:
            logger.error(f"Sending email with subject: {subject} for {recipients}")
            sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
            response = sendgrid_client.send(message)
            response.raise_for_status()

        except Exception as error:
            logger.error(f"Unable to send email, error: {error}")