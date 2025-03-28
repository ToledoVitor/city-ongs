from django.urls import path

from bank.views import create_bank_account_view
from contracts.views import (
    CompanyCreateView,
    CompanyListView,
    ContractCreateView,
    ContractExecutionActivityUpdateView,
    ContractExecutionDetailView,
    ContractsDetailView,
    ContractsListView,
    ContractTimelineView,
    ContractWorkPlanView,
    ItemValueRequestReviewView,
    contract_status_change_view,
    contract_timeline_update_view,
    create_contract_execution_view,
    create_contract_goal_view,
    create_contract_interested_view,
    create_contract_item_view,
    create_execution_activity_view,
    create_execution_file_view,
    interested_delete_view,
    item_new_value_request_view,
    send_accountability_review_analisys,
    send_execution_to_analisys_view,
    update_contract_goal_view,
    update_contract_interested_view,
    update_contract_item_view,
)

urlpatterns = [
    path("", ContractsListView.as_view(), name="contracts-list"),
    path("create/", ContractCreateView.as_view(), name="contracts-create"),
    path(
        "detail/<uuid:pk>/",
        ContractsDetailView.as_view(),
        name="contracts-detail",
    ),
    path(
        "detail/<uuid:pk>/workplan/",
        ContractWorkPlanView.as_view(),
        name="contract-workplan",
    ),
    path(
        "detail/<uuid:pk>/timeline/",
        ContractTimelineView.as_view(),
        name="contract-timeline",
    ),
    path(
        "detail/<uuid:pk>/timeline/update",
        contract_timeline_update_view,
        name="timeline-update",
    ),
    path(
        "detail/<uuid:pk>/change-status/",
        contract_status_change_view,
        name="contract-status-change",
    ),
    path(
        "detail/<uuid:pk>/request-new-value/",
        item_new_value_request_view,
        name="item-request-new-value",
    ),
    path(
        "detail/<uuid:pk>/executions/create/",
        create_contract_execution_view,
        name="executions-create",
    ),
    path(
        "activities/<uuid:pk>/",
        ContractExecutionActivityUpdateView.as_view(),
        name="activities-detail",
    ),
    path(
        "executions/detail/<uuid:pk>/",
        ContractExecutionDetailView.as_view(),
        name="executions-detail",
    ),
    path(
        "executions/detail/<uuid:pk>/send-to-analisys",
        send_execution_to_analisys_view,
        name="send-execution-to-analisys",
    ),
    path(
        "executions/detail/<uuid:pk>/send-review-analisys",
        send_accountability_review_analisys,
        name="send-execution-review-analisys",
    ),
    path(
        "executions/detail/<uuid:pk>/activities/create",
        create_execution_activity_view,
        name="execution-items-create",
    ),
    path(
        "executions/detail/<uuid:pk>/files/create",
        create_execution_file_view,
        name="execution-files-create",
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
        "detail/<uuid:pk>/interesteds/create/",
        create_contract_interested_view,
        name="contracts-interesteds-create",
    ),
    path(
        "detail/<uuid:pk>/interesteds/update/<uuid:item_pk>",
        update_contract_interested_view,
        name="contracts-interesteds-update",
    ),
    path(
        "detail/<uuid:pk>/interesteds/delete/",
        interested_delete_view,
        name="interested-delete",
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
    path(
        "requests/<uuid:pk>/review",
        ItemValueRequestReviewView.as_view(),
        name="review-value-requests",
    ),
]
