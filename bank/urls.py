from django.urls import path

from bank.views import (
    BankAccountCreateView,
    BankAccountDetailView,
    BankAccountsListView,
)

urlpatterns = [
    path("", BankAccountsListView.as_view(), name="bank-accounts-list"),
    path("create/", BankAccountCreateView.as_view(), name="bank-accounts-create"),
    path(
        "detail/<uuid:pk>/",
        BankAccountDetailView.as_view(),
        name="bank-accounts-detail",
    ),
]
