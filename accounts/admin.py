from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from accounts.models import (
    Area,
    CityHall,
    Committee,
    Organization,
    OrganizationDocument,
    User,
)
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
class CustomUserAdmin(BaseModelAdmin):
    list_display = (
        "username",
        "email",
        "cpf",
        "cnpj",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "groups",
        "areas",
    )
    readonly_fields = (
        "id",
        "last_login",
        "date_joined",
    )
    search_fields = (
        "username",
        "email",
        "cpf",
        "cnpj",
        "first_name",
        "last_name",
    )
    ordering = ("username",)

    fieldsets = (
        (None, {"fields": ("id", "username", "password")}),
        (
            "Informações Pessoais",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "cpf",
                    "cnpj",
                    "position",
                    "phone_number",
                ),
            },
        ),
        (
            "Permissões",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "access_level",
                    "groups",
                    "user_permissions",
                    "areas",
                    "organization",
                ),
            },
        ),
        (
            "Datas Importantes",
            {
                "fields": ("last_login", "date_joined"),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    "groups",
                    "areas",
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions", "areas")


@admin.register(OrganizationDocument)
class OrganizationDocumentAdmin(BaseModelAdmin):
    list_display = ("organization", "title", "created_at", "updated_at")
    list_filter = ("organization",)
    search_fields = ("title",)
