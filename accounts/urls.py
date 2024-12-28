from django.urls import path

from accounts.views import (
    FolderManagersListView,
    FolderManagersDetailView,
    OngAccountantsListView,
    OngAccountantsDetailView,
)

urlpatterns = [
    # Folder Managers Views
    path(
        "folder-managers/",
        FolderManagersListView.as_view(),
        name="folder-managers-list",
    ),
    path(
        "folder-managers/detail/<uuid:pk>/",
        FolderManagersDetailView.as_view(),
        name="folder-managers-detail",
    ),
    # Ong Accountant Views
    path(
        "ong-accountants/",
        OngAccountantsListView.as_view(),
        name="ong-accountants-list",
    ),
    path(
        "ong-accountants/detail/<int:pk>/",
        OngAccountantsDetailView.as_view(),
        name="ong-accountants-detail",
    ),
]
