from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from accounts.models import Area, CityHall, Committee, Organization, User
from utils.admin import BaseModelAdmin


@admin.register(Organization)
class OrganizationAdmin(BaseModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(CityHall)
class CityHallAdmin(BaseModelAdmin):
    list_display = ("name", "mayor", "document", "created_at", "updated_at")
    search_fields = ("name", "mayor")


@admin.register(Area)
class AreaAdmin(BaseModelAdmin):
    list_display = ("organization", "name", "created_at", "updated_at")
    list_filter = ("organization",)
    search_fields = ("name",)


@admin.register(Committee)
class CommitteeAdmin(BaseModelAdmin):
    list_display = ("organization", "name", "created_at", "updated_at")
    list_filter = ("organization",)
    search_fields = ("name",)
    filter_horizontal = ("members",)
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "name",
                    "city_hall",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            _("Membros"),
            {
                "fields": ("members",),
            },
        ),
    )


@admin.register(User)
class UserAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "email",
        "first_name",
        "last_name",
        "is_active",
    )
    list_filter = ("organization", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login",)
    fieldsets = (
        (
            _("Informações Básicas"),
            {
                "fields": (
                    "organization",
                    "email",
                    "first_name",
                    "last_name",
                    "is_active",
                )
            },
        ),
        (
            _("Permissões"),
            {
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Datas Importantes"),
            {
                "fields": ("last_login",),
                "classes": ("collapse",),
            },
        ),
    )
