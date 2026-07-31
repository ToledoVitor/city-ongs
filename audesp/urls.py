from django.urls import path

from audesp.views import (
    AudespFaseVBuildView,
    AudespFaseVCheckStatusView,
    AudespFaseVPanelView,
    AudespFaseVSubmitView,
)

urlpatterns = [
    path(
        "fase-v/<uuid:contract_id>/",
        AudespFaseVPanelView.as_view(),
        name="fase-v-panel",
    ),
    path(
        "fase-v/<uuid:contract_id>/build/",
        AudespFaseVBuildView.as_view(),
        name="fase-v-build",
    ),
    path(
        "fase-v/<uuid:contract_id>/submissions/<uuid:submission_id>/submit/",
        AudespFaseVSubmitView.as_view(),
        name="fase-v-submit",
    ),
    path(
        "fase-v/<uuid:contract_id>/submissions/<uuid:submission_id>/check-status/",
        AudespFaseVCheckStatusView.as_view(),
        name="fase-v-check-status",
    ),
]
