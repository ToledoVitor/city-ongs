import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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
                f"Unauthorized access attempt to {self.request.path} - "
                f"{self.request.user.get_full_name()}"
            )
            return redirect("contracts:contracts-list")

        return super().dispatch(request, *args, **kwargs)


class CommitteeMemberReadOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to prevent committee members from modifying data."""

    def test_func(self):
        """Check if user is not a committee member."""
        return not self.request.user.is_committee_member

    def handle_no_permission(self):
        """Handle unauthorized access."""
        messages.error(
            self.request, "Membros do comitê têm acesso somente para visualização."
        )
        return redirect("home")


class CommitteeMemberCreateMixin(CommitteeMemberReadOnlyMixin):
    """Mixin to prevent committee members from creating objects."""

    def test_func(self):
        """Check if user is not a committee member."""
        return not self.request.user.is_committee_member


class CommitteeMemberUpdateMixin(CommitteeMemberReadOnlyMixin):
    """Mixin to prevent committee members from updating objects."""

    def test_func(self):
        """Check if user is not a committee member."""
        return not self.request.user.is_committee_member


class CommitteeMemberDeleteMixin(CommitteeMemberReadOnlyMixin):
    """Mixin to prevent committee members from deleting objects."""

    def test_func(self):
        """Check if user is not a committee member."""
        return not self.request.user.is_committee_member
