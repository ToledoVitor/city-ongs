from uuid import uuid4

from django.db import models
from django.utils import timezone

from utils.managers import SoftDeleteManager, SoftDeleteManagerAllObjects


class BaseModel(models.Model):
    id = models.UUIDField(models.UUIDField, primary_key=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, db_index=True, blank=True)

    def hard_delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.deleted_at = None
        self.save()

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManagerAllObjects()

    class Meta:
        abstract = True
