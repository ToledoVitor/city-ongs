from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from django.conf import settings
from accounts.models import User

import logging


logger = logging.getLogger(__name__)


class SendGridClient:
    def __init__(self) -> None:
        self.sendgrid_api_key = settings.SENDGRID_API_KEY
        self.sendgrid_account_sender = settings.SENDGRID_ACCOUNT_SENDER

    def notify(self, subject: str, html_content: str, recipients: list[User]):
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

        to_emails = [recipient.email for recipient in recipients]
        message = Mail(
            from_email=self.sendgrid_account_sender,
            to_emails=to_emails,
            subject=subject,
            html_content=html_content,
        )
        print(html_content)
        try:
            logger.error(f"Sending email with subject: {subject} for {to_emails}")
            sendgrid_client = SendGridAPIClient(self.sendgrid_api_key)
            sendgrid_client.send(message)

        except Exception as error:
            logger.error(f"Unable to send email, error: {error}")