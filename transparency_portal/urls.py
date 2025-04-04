from django.urls import path

from . import views

app_name = "transparency"

urlpatterns = [
    path(
        "",
        views.PartnershipListView.as_view(),
        name="partnership_list",
    ),
    path(
        "partnership/<uuid:pk>/",
        views.PartnershipDetailView.as_view(),
        name="partnership_detail",
    ),
    path(
        "organization/<uuid:org_id>/",
        views.OrganizationPartnershipListView.as_view(),
        name="organization_partnerships",
    ),
    path(
        "partnership/<uuid:partnership_id>/report-irregularity/",
        views.IrregularityReportCreateView.as_view(),
        name="report_irregularity",
    ),
]
