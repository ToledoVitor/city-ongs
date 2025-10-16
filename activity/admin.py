from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from activity.models import ActivityLog, Notification
from utils.admin import BaseModelAdmin


@admin.register(ActivityLog)
class ActivityLogAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "user",
        "action",
        "created_at",
    )
    list_filter = ("organization", "action", "created_at")
    search_fields = ("id", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "user",
                    "action",
                    "created_at",
                )
            },
        ),
        (
            _("Objeto Alvo"),
            {
                "fields": (
                    "target_model",
                    "target_object_id",
                    "target_object_str",
                )
            },
        ),
        (
            _("Detalhes"),
            {
                "fields": ("changes", "ip_address", "user_agent"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Notification)
class NotificationAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "recipient",
        "text",
        "category",
        "read_at",
        "created_at",
    )
    list_filter = ("organization", "category", "read_at", "created_at")
    search_fields = (
        "id",
        "text",
        "recipient__email",
        "recipient__first_name",
        "recipient__last_name",
    )
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "recipient",
                    "category",
                    "text",
                    "object_id",
                )
            },
        ),
        (
            _("Datas"),
            {
                "fields": ("created_at", "read_at"),
                "classes": ("collapse",),
            },
        ),
    )
