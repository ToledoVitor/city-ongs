from django.urls import path

from contracts.views import ContractCreateView, ContractsDetailView, ContractsListView, create_contract_item_view

urlpatterns = [
    path("", ContractsListView.as_view(), name="contracts-list"),
    path("create/", ContractCreateView.as_view(), name="contracts-create"),
    path("detail/<uuid:pk>/", ContractsDetailView.as_view(), name="contracts-detail"),
    path("detail/<uuid:pk>/items/create/", create_contract_item_view, name="contracts-item-create"),
    path("detail/<uuid:pk>/goals/create/", ContractsDetailView.as_view(), name="contracts-goals-create"),
    path("detail/<uuid:pk>/addendums/create/", ContractsDetailView.as_view(), name="contracts-addendum-create"),
]
