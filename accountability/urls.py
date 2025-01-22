from django.urls import path

from accountability.views import (
    ExpenseSourceCreateView,
    ExpenseSourceListView,
    RevenueSourceCreateView,
    RevenueSourceListView,
    create_contract_accountability_view,
)

urlpatterns = [
    path("expenses/", ExpenseSourceListView.as_view(), name="expenses-source-list"),
    path(
        "expenses/create/",
        ExpenseSourceCreateView.as_view(),
        name="expenses-source-create",
    ),
    # path("detail/<uuid:pk>/", ContractsDetailView.as_view(), name="contracts-detail"),
    path("revenues/", RevenueSourceListView.as_view(), name="revenues-source-list"),
    path(
        "revenues/create/",
        RevenueSourceCreateView.as_view(),
        name="revenues-source-create",
    ),
    path("<uuid:pk>/accountability/create", create_contract_accountability_view, name="accountability-create"),
]
