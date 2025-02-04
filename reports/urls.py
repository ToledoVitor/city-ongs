from django.urls import path

from reports.views import ReportsView


urlpatterns = [
    path("", ReportsView.as_view(), name="reports-page"),
]

