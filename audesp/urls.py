from django.urls import path

from audesp.views import (
    AudespFaseIVAjusteCreateView,
    AudespFaseVBuildView,
    AudespFaseVCheckStatusView,
    AudespFaseVPanelView,
    AudespFaseVSubmitView,
    audesp_fase_iv_empenho_create_view,
    audesp_fase_iv_submission_submit_view,
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
    path(
        "fase-iv/ajuste/<uuid:contract_pk>/",
        AudespFaseIVAjusteCreateView.as_view(),
        name="fase-iv-ajuste-create",
    ),
    path(
        "fase-iv/empenho/<uuid:contract_pk>/",
        audesp_fase_iv_empenho_create_view,
        name="fase-iv-empenho-create",
    ),
    path(
        "fase-iv/submissions/<uuid:pk>/submit/",
        audesp_fase_iv_submission_submit_view,
        name="fase-iv-submission-submit",
    ),
]
