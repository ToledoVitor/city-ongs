from django.urls import path

from accountability.views import RevenueSourceListView, ExpenseSourceListView

urlpatterns = [
    path("revenues/", RevenueSourceListView.as_view(), name="revenues-source-list"),
    # path("revenues/create/", ContractCreateView.as_view(), name="contracts-create"),
    # path("detail/<uuid:pk>/", ContractsDetailView.as_view(), name="contracts-detail"),
    path("expenses/", ExpenseSourceListView.as_view(), name="expenses-source-list"),
]
