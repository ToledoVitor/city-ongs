from django.urls import path

from bank.views import create_bank_account_manual_view, create_bank_account_ofx_view
from contracts.views import (
    CompanyCreateView,
    CompanyListView,
    ContractCreateView,
    ContractsDetailView,
    ContractsListView,
    ContractExecutionDetailView,
    create_contract_goal_view,
    create_contract_item_view,
    create_execution_activity_view,
    update_contract_goal_view,
    update_contract_item_view,
    create_contract_execution_view,
)

urlpatterns = [
    path("", ContractsListView.as_view(), name="contracts-list"),
    path("create/", ContractCreateView.as_view(), name="contracts-create"),
    path("detail/<uuid:pk>/", ContractsDetailView.as_view(), name="contracts-detail"),
    path(
        "detail/<uuid:pk>/executions/create/",
        create_contract_execution_view,
        name="executions-create",
    ),
    path(
        "executions/detail/<uuid:pk>/",
        ContractExecutionDetailView.as_view(),
        name="executions-detail",
    ),
    path(
        "executions/detail/<uuid:pk>/activities/create",
        create_execution_activity_view,
        name="execution-items-create",
    ),
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
        create_bank_account_ofx_view,
        name="contracts-accounts-auto-create",
    ),
    path(
        "detail/<uuid:pk>/accounts/manual-create/",
        create_bank_account_manual_view,
        name="contracts-accounts-manual-create",
    ),
    path("company/", CompanyListView.as_view(), name="companies-list"),
    path(
        "company/create/",
        CompanyCreateView.as_view(),
        name="companies-create",
    ),
]
