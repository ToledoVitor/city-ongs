from django.urls import path

from accountability.views import (
    ExpenseSourceCreateView,
    ExpenseSourceListView,
    FavoredCreateView,
    FavoredListView,
    RevenueSourceCreateView,
    RevenueSourceListView,
    accountability_detail_view,
    create_accountability_expense_view,
    create_accountability_revenue_view,
    create_contract_accountability_view,
    upload_accountability_file_view,
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
    path(
        "<uuid:pk>/accountability/upload",
        upload_accountability_file_view,
        name="accountability-upload",
    ),
    path("detail/<uuid:pk>", accountability_detail_view, name="accountability-detail"),
    path(
        "detail/<uuid:pk>/import",
        create_contract_accountability_view,
        name="accountability-create",
    ),
    path(
        "<uuid:pk>/accountability/expenses/create",
        create_accountability_expense_view,
        name="expenses-create",
    ),
    path(
        "<uuid:pk>/accountability/revenues/create",
        create_accountability_revenue_view,
        name="revenues-create",
    ),
    path("favoreds/", FavoredListView.as_view(), name="favoreds-list"),
    path(
        "favoreds/create/",
        FavoredCreateView.as_view(),
        name="favoreds-create",
    ),
]
