import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class AdminRequiredMixin(LoginRequiredMixin):
    login_url = "/accounts-login/"

    def handle_no_permission(self):
        logger.warning(f"Unauthorized access attempt to {self.request.path}")
        return redirect(self.login_url)

    def dispatch(self, request, *args, **kwargs):
        if not request.user:
            return redirect(self.login_url)

        if not request.user.has_admin_access:
            logger.warning(
                f"Unauthorized access attempt to {self.request.path} - {self.request.user.get_full_name()}"
            )
            return redirect("contracts:contracts-list")

        return super().dispatch(request, *args, **kwargs)
