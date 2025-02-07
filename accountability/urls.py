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
    send_accountability_review_analisys,
    send_accountability_to_analisys_view,
    import_accountability_view,
    expense_delete_view,
    revenue_delete_view,
    update_accountability_revenue_view,
    update_accountability_expense_view,
    duplicate_accountability_expense_view,
    duplicate_accountability_revenue_view,
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
    path("detail/<uuid:pk>/send-to-analisys", send_accountability_to_analisys_view, name="send-to-analisys"),
    path("detail/<uuid:pk>/send-review-analisys", send_accountability_review_analisys, name="send-review-analisys"),
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
    path("expenses/<uuid:pk>/update/", update_accountability_expense_view, name="expense-update"),
    path("expenses/<uuid:pk>/duplicate/", duplicate_accountability_expense_view, name="expense-duplicate"),
    path("expenses/<uuid:pk>/delete/", expense_delete_view, name="expense-delete"),
    path("revenues/<uuid:pk>/update/", update_accountability_revenue_view, name="revenue-update"),
    path("revenues/<uuid:pk>/duplicate/", duplicate_accountability_revenue_view, name="revenue-duplicate"),
    path("revenues/<uuid:pk>/delete/", revenue_delete_view, name="revenue-delete"),
]
