from django.urls import path

from bank.views import (
    BankAccountDetailView,
)

urlpatterns = [
    path(
        "detail/<uuid:pk>/",
        BankAccountDetailView.as_view(),
        name="bank-accounts-detail",
    ),
]
