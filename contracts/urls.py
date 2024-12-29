from django.urls import path

from contracts.views import ContractCreateView, ContractsDetailView, ContractsListView

urlpatterns = [
    path("", ContractsListView.as_view(), name="contracts-list"),
    path("create/", ContractCreateView.as_view(), name="contracts-create"),
    path("detail/<uuid:pk>/", ContractsDetailView.as_view(), name="contracts-detail"),
]
