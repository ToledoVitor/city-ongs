from django.contrib import admin

from activity.models import ActivityLog, Notification

admin.site.register(ActivityLog)
admin.site.register(Notification)
