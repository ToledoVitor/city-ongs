from django.urls import path

from audesp.views import (
    AudespFaseIVAjusteCreateView,
    audesp_fase_iv_empenho_create_view,
    audesp_fase_iv_submission_submit_view,
)

urlpatterns = [
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
