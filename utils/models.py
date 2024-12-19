from uuid import uuid4

from django.db import models
from django.utils import timezone
from utils.managers import SoftDeleteManager, SoftDeleteManagerAllObjects


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    id = models.UUIDField(models.UUIDField, primary_key=True, default=uuid4)

    class Meta:
        abstract = True


class BaseClass(TimestampedModel, UUIDModel):
    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
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


class ArchiveModel(models.Model):
    archived_at = models.DateTimeField(
        null=True,
        db_index=True,
        blank=True,
        verbose_name="Archived At",
        help_text="The date when this was archived.",
    )

    def archive(self):
        self.archived_at = timezone.now()
        self.save(update_fields=["archived_at", "updated_at"])

    def unarchive(self):
        self.archived_at = None
        self.save(update_fields=["archived_at", "updated_at"])

    class Meta:
        abstract = True


class BaseRecordModel(models.Model):
    recorded_at = models.DateTimeField(
        null=True,
        db_index=True,
        blank=True,
        default=timezone.now,
    )
    note = models.TextField(
        help_text="The note of the record",
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
