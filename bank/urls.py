from django.urls import path

from bank.views import (
    BankAccountCreateView,
    BankAccountsListView,
)

urlpatterns = [
    path("", BankAccountsListView.as_view(), name="bank-accounts-list"),
    path("create/", BankAccountCreateView.as_view(), name="bank-accounts-create"),
]
