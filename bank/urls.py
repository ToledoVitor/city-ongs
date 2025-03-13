from django.urls import path

from bank.views import (
    BankAccountDetailView,
    bank_statement_view,
    update_bank_account_manual_view,
    update_bank_account_ofx_view,
)

urlpatterns = [
    path(
        "detail/<uuid:pk>/",
        BankAccountDetailView.as_view(),
        name="bank-accounts-detail",
    ),
    path(
        "detail/<uuid:pk>/statement/",
        bank_statement_view,
        name="bank-accounts-statement",
    ),
    path(
        "detail/<uuid:pk>/update-statements/",
        update_bank_account_ofx_view,
        name="bank-statements-update",
    ),
    path(
        "detail/<uuid:pk>/manual-update-statements/",
        update_bank_account_manual_view,
        name="bank-statements-manual-update",
    ),
]
