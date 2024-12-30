from django.contrib import admin
from django.urls import include, path, re_path

from core.views import HomeView

urlpatterns = [
    # Internal
    path("admin/", admin.site.urls),
    path("auth/", include("django.contrib.auth.urls")),
    # Domain apps
    path("", HomeView.as_view(), name="home"),
    path("accountability/", include(("accountability.urls", "accountability"), namespace="accountability")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("contracts/", include(("contracts.urls", "contracts"), namespace="contracts")),
    # Health Check
    re_path(r"^api/health_check/", include("health_check.urls")),
]
