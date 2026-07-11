from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from accounts.models import (
    Area,
    CededServant,
    CededServantRemunerationPeriod,
    CityHall,
    Committee,
    Employee,
    EmployeeRemunerationPeriod,
    Organization,
    OrganizationDocument,
    User,
)
from utils.admin import BaseModelAdmin


@admin.register(Organization)
class OrganizationAdmin(BaseModelAdmin):
    list_display = ("name", "audesp_entity_code", "created_at", "updated_at")
    search_fields = (
        "id",
        "name",
    )


@admin.register(CityHall)
class CityHallAdmin(BaseModelAdmin):
    list_display = (
        "name",
        "mayor",
        "document",
        "audesp_municipality_code",
        "created_at",
        "updated_at",
    )
    search_fields = ("id", "name", "mayor")


@admin.register(Area)
class AreaAdmin(BaseModelAdmin):
    list_display = ("organization", "name", "created_at", "updated_at")
    list_filter = ("organization",)
    search_fields = (
        "id",
        "name",
    )


@admin.register(Committee)
class CommitteeAdmin(BaseModelAdmin):
    list_display = ("organization", "name", "created_at", "updated_at")
    list_filter = ("organization",)
    search_fields = (
        "id",
        "name",
    )
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
        "password_redefined",
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
        "id",
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
                    "password_expires_at",
                    "password_redefined",
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
    search_fields = (
        "id",
        "title",
    )


class EmployeeRemunerationPeriodInline(admin.TabularInline):
    model = EmployeeRemunerationPeriod
    extra = 0
    fields = ("year", "month", "hours_worked", "gross_remuneration")


@admin.register(Employee)
class EmployeeAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "cpf",
        "cbo",
        "admission_date",
        "termination_date",
        "contractual_salary",
    )
    list_filter = ("organization",)
    search_fields = ("id", "cpf", "cbo")
    inlines = [EmployeeRemunerationPeriodInline]


class CededServantRemunerationPeriodInline(admin.TabularInline):
    model = CededServantRemunerationPeriod
    extra = 0
    fields = ("year", "month", "hours_worked", "gross_remuneration")


@admin.register(CededServant)
class CededServantAdmin(BaseModelAdmin):
    list_display = (
        "organization",
        "cpf",
        "public_position_held",
        "cession_start_date",
        "cession_end_date",
        "payment_burden",
    )
    list_filter = ("organization", "payment_burden")
    search_fields = ("id", "cpf", "public_position_held")
    inlines = [CededServantRemunerationPeriodInline]
