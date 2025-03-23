from django.apps import AppConfig
from django.db.models.signals import post_save


class ActivityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "activity"

    def ready(self) -> None:
        from activity.signals import on_activity_log_post_save

        post_save.connect(
            on_activity_log_post_save, sender="activity.ActivityLog"
        )
