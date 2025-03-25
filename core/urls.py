from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path

from core.views import (
    CustomPasswordResetView,
    HomeView,
    force_password_change_view,
    test_redis,
)

urlpatterns = [
    # Dev Internal
    re_path(r"^__dev__/api/health_check/", include("health_check.urls")),
    path("__dev__/api/redis/", test_redis, name="test_redis"),
    # Admin
    path("__staff__/admin/", admin.site.urls),
    # Auth
    path("auth/login/", auth_views.LoginView.as_view(), name="login"),
    path("auth/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "auth/password_reset/",
        CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "auth/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "auth/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "auth/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    # Domain apps
    path("", HomeView.as_view(), name="home"),
    path(
        "auth/force-password-change/",
        force_password_change_view,
        name="force-password-change",
    ),
    path(
        "accountability/",
        include(
            ("accountability.urls", "accountability"),
            namespace="accountability",
        ),
    ),
    path(
        "accounts/",
        include(("accounts.urls", "accounts"), namespace="accounts"),
    ),
    path("bank/", include(("bank.urls", "bank"), namespace="bank")),
    path(
        "contracts/",
        include(("contracts.urls", "contracts"), namespace="contracts"),
    ),
    path(
        "reports/",
        include(("reports.urls", "reports"), namespace="reports"),
    ),
    path(
        "dashboard/",
        include(("dashboard.urls", "dashboard"), namespace="dashboard"),
    ),
]
