from typing import TYPE_CHECKING

from django.db.models import Manager, Q
from easy_tenants.models import TenantManager

from utils.query import SoftDeleteQueryset

if TYPE_CHECKING:
    from accounts.models import User


class SoftDeleteManagerAllObjects(Manager):
    _queryset_class = SoftDeleteQueryset

    def not_deleted(self):
        return self.get_queryset().not_deleted()

    def delete(self):
        return self.get_queryset().delete()

    def only_deleted(self):
        return self.get_queryset().deleted()

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class SoftDeleteManager(SoftDeleteManagerAllObjects):
    def get_queryset(self):
        return super().get_queryset().not_deleted()


class TenantManagerAllObjects(TenantManager, SoftDeleteManagerAllObjects):
    pass


class TenantManager(TenantManager, SoftDeleteManager):
    pass


class UserAccessMixin:
    """Mixin that provides user-based access filtering methods."""

    def for_user(self, user: "User", contract_field_prefix: str = ""):
        """Filter queryset based on user access level and permissions."""
        from accounts.models import User

        queryset = self.get_queryset()

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


class ContractUserAccessManager(SoftDeleteManager, UserAccessMixin):
    """Manager for Contract model with user access filtering."""

    def for_user(self, user: "User"):
        """Get contracts filtered by user access permissions."""
        return super().for_user(user, contract_field_prefix="")


class AccountabilityUserAccessManager(SoftDeleteManager, UserAccessMixin):
    """Manager for Accountability model with user access filtering."""

    def for_user(self, user: "User"):
        """Get accountabilities filtered by user access permissions."""
        return super().for_user(user, contract_field_prefix="contract__")
