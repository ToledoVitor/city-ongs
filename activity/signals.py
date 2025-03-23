from activity.models import ActivityLog
from activity.services import ActivityLogEmailNotificationHandler


def on_activity_log_post_save(
    sender, instance: ActivityLog, **kwargs: dict
) -> None:
    created = kwargs.get("created")
    if not created:
        return

    ActivityLogEmailNotificationHandler().handle_log_creation(instance)
