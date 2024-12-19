from django.db import models
from django.utils import timezone


class SoftDeleteQueryset(models.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def restore(self):
        return super().update(deleted_at=None)

    def not_deleted(self):
        return super().filter(deleted_at__isnull=True)

    def deleted(self):
        return super().filter(deleted_at__isnull=False)
