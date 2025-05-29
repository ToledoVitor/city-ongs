import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
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
            self.request,
            "Membros do comitê têm acesso somente para visualização.",
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


class OrganizationPermissionMixin(UserPassesTestMixin):
    """
    Mixin para verificar se o usuário tem permissão para acessar recursos da organização.
    Verifica se o objeto pertence à organização do usuário e se o usuário tem acesso à área.
    """

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not self.has_organization_permission(obj):
            raise PermissionDenied
        return obj

    def has_organization_permission(self, obj):
        # Verifica se o objeto tem organização
        if not hasattr(obj, "organization"):
            return True

        # Verifica se pertence à organização do usuário
        if obj.organization != self.request.user.organization:
            return False

        # Verifica se o objeto tem área
        if hasattr(obj, "area"):
            return obj.area in self.request.user.areas.all()

        return True

    def test_func(self):
        return self.request.user.is_authenticated


class AreaPermissionMixin(UserPassesTestMixin):
    """
    Mixin para verificar se o usuário tem permissão para acessar recursos da área.
    """

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False

        area_id = self.kwargs.get("area_id")
        if not area_id:
            return True

        return self.request.user.areas.filter(id=area_id).exists()


class ContractPermissionMixin(OrganizationPermissionMixin):
    """
    Mixin específico para contratos, que verifica permissões adicionais.
    """

    def has_organization_permission(self, obj):
        if not super().has_organization_permission(obj):
            return False

        # Verifica se o usuário é parte interessada do contrato
        return obj.interested_parts.filter(user=self.request.user).exists()
