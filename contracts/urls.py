from django.urls import path

from contracts.views import ContractsListView, ContractsDetailView, ContractCreateView

urlpatterns = [
    path("", ContractsListView.as_view(), name="contracts-list"),
    path("create/", ContractCreateView.as_view(), name="contracts-create"),
    path("detail/<uuid:pk>/", ContractsDetailView.as_view(), name="contracts-detail"),
]
