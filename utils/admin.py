from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """Base admin class with common fields and methods."""

    readonly_fields = ("id", "pk", "created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        """Add organization to readonly fields if object exists."""
        return self.readonly_fields
