import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import TemplateView

from accounts.models import User
from sendgrid_client.client import SendGridClient

logger = logging.getLogger(__name__)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"
    login_url = "/auth/login"


def send_reset_email(user: User, reset_url: str):
    context = {
        "reset_url": reset_url,
        "user": user,
    }
    html_content = render_to_string(
        "registration/password_reset_email.html",
        context,
    )
    sendgrid_client = SendGridClient()
    sendgrid_client.notify(
        subject="Recuperação de Senha",
        html_content=html_content,
        recipients=[user],
    )
    logger.info(f"Sending recovery password email for {user.email}")


class CustomPasswordResetView(PasswordResetView):
    email_template_name = "registration/password_reset_email.html"
    html_email_template_name = (
        "registration/password_reset_email.html"  # Template de email em HTML
    )
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = self.request.build_absolute_uri(
                reverse_lazy(
                    "password_reset_confirm", kwargs={"uidb64": uid, "token": token}
                )
            )
            send_reset_email(user, reset_url)
        except User.DoesNotExist:
            logger.info(f"Requested email {email} does not exists")
            pass  # Dont reveal user does not exist

        return HttpResponseRedirect(self.get_success_url())
