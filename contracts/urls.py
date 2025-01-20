from django.urls import path

from bank.views import create_bank_account_view
from contracts.views import (
    ContractCreateView,
    ContractsDetailView,
    ContractsListView,
    create_contract_goal_view,
    create_contract_item_view,
    update_contract_goal_view,
    update_contract_item_view,
    CompanyListView,
    CompanyCreateView,
)

urlpatterns = [
    path("", ContractsListView.as_view(), name="contracts-list"),
    path("create/", ContractCreateView.as_view(), name="contracts-create"),
    path("detail/<uuid:pk>/", ContractsDetailView.as_view(), name="contracts-detail"),
    path(
        "detail/<uuid:pk>/items/create/",
        create_contract_item_view,
        name="contracts-item-create",
    ),
    path(
        "detail/<uuid:pk>/items/update/<uuid:item_pk>",
        update_contract_item_view,
        name="contracts-item-update",
    ),
    path(
        "detail/<uuid:pk>/goals/create/",
        create_contract_goal_view,
        name="contracts-goals-create",
    ),
    path(
        "detail/<uuid:pk>/goals/update/<uuid:goal_pk>",
        update_contract_goal_view,
        name="contracts-goals-update",
    ),
    path(
        "detail/<uuid:pk>/addendums/create/",
        ContractsDetailView.as_view(),
        name="contracts-addendum-create",
    ),
    path(
        "detail/<uuid:pk>/accounts/create/",
        create_bank_account_view,
        name="contracts-accounts-create",
    ),
    path("company/", CompanyListView.as_view(), name="companies-list"),
    path(
        "company/create/",
        CompanyCreateView.as_view(),
        name="companies-create",
    ),

]
