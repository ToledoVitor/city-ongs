from django.urls import path

from bank.views import (
    BankAccountDetailView,
    BankAccountsListView,
    upload_ofx_view,
)

urlpatterns = [
    path("", BankAccountsListView.as_view(), name="bank-accounts-list"),
    path("create/", upload_ofx_view, name="bank-accounts-create"),
    path(
        "detail/<uuid:pk>/",
        BankAccountDetailView.as_view(),
        name="bank-accounts-detail",
    ),
]
