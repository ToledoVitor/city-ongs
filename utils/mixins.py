import logging
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, QuerySet
from django.shortcuts import redirect

if TYPE_CHECKING:
    from accounts.models import User


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


class UserAccessQuerysetMixin:
    """
    Mixin that provides user-based queryset filtering for models that have
    contract relationships with area-based and authority-based access
    control.
    """

    @staticmethod
    def filter_by_user_access(
        queryset: QuerySet, user: "User", contract_field_prefix: str = ""
    ) -> QuerySet:
        """
        Filter queryset based on user access level and permissions.

        Args:
            queryset: The base queryset to filter
            user: The user requesting access
            contract_field_prefix: Prefix for contract field
                (e.g., 'contract__' or '')

        Returns:
            Filtered queryset based on user permissions
        """
        from accounts.models import User

        if user.access_level in {
            User.AccessChoices.COMMITTEE_MEMBER,
            User.AccessChoices.MASTER,
        }:
            area_filter = f"{contract_field_prefix}area__in"
            return queryset.filter(**{area_filter: user.areas.all()})
        else:
            supervision_filter = f"{contract_field_prefix}supervision_autority"
            accountability_filter = f"{contract_field_prefix}accountability_autority"
            interested_parts_filter = f"{contract_field_prefix}interested_parts__user"

            return queryset.filter(
                Q(**{supervision_filter: user})
                | Q(**{accountability_filter: user})
                | Q(**{interested_parts_filter: user})
            )


class UserAccessViewMixin(UserAccessQuerysetMixin):
    """
    View mixin that automatically applies user-based filtering to querysets.
    """

    contract_field_prefix = ""

    def get_user_filtered_queryset(
        self, queryset: QuerySet, contract_field_prefix: str = None
    ) -> QuerySet:
        """Apply user-based filtering to the provided queryset."""
        prefix = (
            contract_field_prefix
            if contract_field_prefix is not None
            else getattr(self, "contract_field_prefix", "")
        )

        filtered_queryset = self.filter_by_user_access(
            queryset, self.request.user, prefix
        )

        if hasattr(self, "apply_distinct") and self.apply_distinct:
            filtered_queryset = filtered_queryset.distinct()

        return filtered_queryset


class UserAccessFormMixin(UserAccessQuerysetMixin):
    """
    Form mixin that provides user-based queryset filtering for form fields.
    """

    def get_user_filtered_contract_queryset(self, user: "User") -> QuerySet:
        """Get contracts filtered by user access permissions."""
        from contracts.models import Contract

        base_queryset = Contract.objects.all()
        return self.filter_by_user_access(base_queryset, user)
