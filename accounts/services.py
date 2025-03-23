import logging

from django.conf import settings
from django.template.loader import render_to_string

from accounts.models import User
from sendgrid_client.client import SendGridClient

logger = logging.getLogger(__name__)


def notify_user_account_created(user: User, password: str):
    logger.info(f"Notifying user {user.email} for acount creation")

    try:
        context = {
            "user_name": user.get_full_name(),
            "password": password,
            "website_url": settings.WEBSITE_URL,
        }
        html_content = render_to_string(
            "email/account_created_email.html", context
        )

        sendgrid_client = SendGridClient()
        sendgrid_client.notify(
            subject="Seja Bem Vindo ao SITTS!",
            html_content=html_content,
            recipients=[user],
        )
    except Exception as error:
        logger.error(f"Error while notifying account creation: {error}")
