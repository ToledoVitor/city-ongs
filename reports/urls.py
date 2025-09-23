from django.urls import path

from reports.views import ReportsView, ReportGenerateAPIView

urlpatterns = [
    path("", ReportsView.as_view(), name="reports-page"),
    path(
        "generate/",
        ReportGenerateAPIView.as_view(),
        name="reports-generate-api"
    ),
]
