from django.urls import path

from accountability.views import (
    FavoredCreateView,
    FavoredListView,
    ResourceSourceCreateView,
    ResourceSourceListView,
    accountability_detail_view,
    create_accountability_expense_view,
    create_accountability_revenue_view,
    create_contract_accountability_view,
    import_accountability_view,
)

urlpatterns = [
    path("sources/", ResourceSourceListView.as_view(), name="sources-list"),
    path(
        "sources/create/",
        ResourceSourceCreateView.as_view(),
        name="sources-create",
    ),
    path(
        "<uuid:pk>/accountability/import",
        import_accountability_view,
        name="accountability-import",
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
