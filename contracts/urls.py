from django.urls import path

from contracts.views import ContractsListView, ContractsDetailView

urlpatterns = [
    path("", ContractsListView.as_view(), name="contracts-list"),
    path("<uuid:pk>/", ContractsDetailView.as_view(), name="contracts-detail"),
]
