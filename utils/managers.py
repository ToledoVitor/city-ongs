from django.db.models import Manager
from easy_tenants.models import TenantManager

from utils.query import SoftDeleteQueryset


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
