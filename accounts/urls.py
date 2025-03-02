from django.urls import path

from accounts.views import (
    FolderManagerCreateView,
    FolderManagersDetailView,
    FolderManagersListView,
    OrganizationAccountantCreateView,
    OrganizationAccountantsDetailView,
    OrganizationAccountantsListView,
    read_notification_view,
    user_unread_notifications,
)

urlpatterns = [
    # Folder Managers Views
    path(
        "notifications/",
        user_unread_notifications,
        name="user-notifications",
    ),
    path(
        "notifications/<uuid:pk>/read",
        read_notification_view,
        name="user-read-notifications",
    ),
    path(
        "folder-managers/",
        FolderManagersListView.as_view(),
        name="folder-managers-list",
    ),
    path(
        "folder-managers/create/",
        FolderManagerCreateView.as_view(),
        name="folder-managers-create",
    ),
    path(
        "folder-managers/detail/<int:pk>/",
        FolderManagersDetailView.as_view(),
        name="folder-managers-detail",
    ),
    # Organization Accountant Views
    path(
        "organization-accountants/",
        OrganizationAccountantsListView.as_view(),
        name="organization-accountants-list",
    ),
    path(
        "organization-accountants/create/",
        OrganizationAccountantCreateView.as_view(),
        name="organization-accountants-create",
    ),
    path(
        "organization-accountants/detail/<int:pk>/",
        OrganizationAccountantsDetailView.as_view(),
        name="organization-accountants-detail",
    ),
]
