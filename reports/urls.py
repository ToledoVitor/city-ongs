from django.urls import path

from reports.views import ReportGenerateAPIView, ReportsView

urlpatterns = [
    path("", ReportsView.as_view(), name="reports-page"),
    path("generate/", ReportGenerateAPIView.as_view(), name="reports-generate-api"),
]
