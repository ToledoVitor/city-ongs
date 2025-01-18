from django.urls import path

from bank.views import (
    BankAccountDetailView,
    BankAccountsListView,
    create_banck_account_view,
)

urlpatterns = [
    path("", BankAccountsListView.as_view(), name="bank-accounts-list"),
    path("create/", create_banck_account_view, name="bank-accounts-create"),
    path(
        "detail/<uuid:pk>/",
        BankAccountDetailView.as_view(),
        name="bank-accounts-detail",
    ),
]
