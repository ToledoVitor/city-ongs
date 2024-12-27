from django.contrib import admin
from django.urls import path, re_path, include

from core.views import HomeView


urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("contracts/", include(("contracts.urls", "contracts"), namespace="contracts")),
    re_path(r"^api/health_check/", include("health_check.urls")),
]
