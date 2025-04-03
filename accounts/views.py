import logging
from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView

from accounts.forms import (
    AreasForm,
    FolderManagerCreateForm,
    OrganizationAccountantCreateForm,
    OrganizationCommitteeCreateForm,
)
from accounts.models import User
from accounts.services import notify_user_account_created
from activity.models import ActivityLog, Notification
from utils.mixins import AdminRequiredMixin
from utils.password import generate_random_password

logger = logging.getLogger(__name__)


class FolderManagersListView(AdminRequiredMixin, ListView):
    model = User
    context_object_name = "managers_list"
    paginate_by = 10
    ordering = "email"

    template_name = "accounts/folder-managers/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            access_level=User.AccessChoices.FOLDER_MANAGER,
            areas__in=self.request.user.areas.all(),
        ).distinct()

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query),
            )
        return queryset.order_by("email")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class FolderManagersDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/folder-managers/detail.html"
    context_object_name = "manager"

    def get_queryset(self):
        return User.objects.filter(access_level=User.AccessChoices.FOLDER_MANAGER)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AreasForm(
            user=self.request.user, initial={"areas": self.object.areas.all()}
        )
        return context

    def post(self, request, *args, **kwargs):
        manager = self.get_object()
        if not request.user.has_admin_access:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        form = AreasForm(request.POST, user=request.user)
        if form.is_valid():
            manager.first_name = request.POST.get("first_name")
            manager.last_name = request.POST.get("last_name")
            manager.cpf = request.POST.get("cpf")
            manager.position = request.POST.get("position")
            manager.is_active = request.POST.get("is_active") == "True"
            manager.phone_number = request.POST.get("phone_number")

            manager.areas.set(form.cleaned_data["areas"])
            manager.save()

            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.UPDATED_FOLDER_MANAGER,
                target_object_id=manager.id,
                target_content_object=manager,
            )

        return redirect("accounts:folder-managers-list")


class FolderManagerCreateView(AdminRequiredMixin, TemplateView):
    template_name = "accounts/folder-managers/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = FolderManagerCreateForm(request=self.request)

        return context

    def post(self, request, *args, **kwargs):
        if not request.user.can_add_new_folder_managers:
            logger.error(
                f"{request.user.id} - dont have access to create new folder managers",
            )
            return redirect("home")

        form = FolderManagerCreateForm(request.POST, request=request)
        if form.is_valid():
            with transaction.atomic():
                password = generate_random_password()
                new_user = User.objects.create(
                    email=form.cleaned_data.get("email"),
                    position=form.cleaned_data.get("position"),
                    phone_number=str(
                        form.cleaned_data["phone_number"].national_number,
                    ),
                    cpf=form.cleaned_data.get("cpf"),
                    username=form.cleaned_data.get("email"),
                    first_name=form.cleaned_data.get("first_name"),
                    last_name=form.cleaned_data.get("last_name"),
                    organization=self.request.user.organization,
                    access_level=User.AccessChoices.FOLDER_MANAGER,
                )
                new_user.set_password(password)
                new_user.save()
                new_user.areas.set(form.cleaned_data["areas"])

                logger.info(f"{request.user.id} - Created new folder manager")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_FOLDER_MANAGER,
                    target_object_id=new_user.id,
                    target_content_object=new_user,
                )

                notify_user_account_created(new_user, password)

            return redirect("accounts:folder-managers-list")

        return self.render_to_response(self.get_context_data(form=form))


class OrganizationAccountantsListView(AdminRequiredMixin, ListView):
    model = User
    context_object_name = "accountants_list"
    paginate_by = 10
    ordering = "email"

    template_name = "accounts/organization-accountants/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            access_level=User.AccessChoices.ORGANIZATION_ACCOUNTANT,
            areas__in=self.request.user.areas.all(),
        ).distinct()

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query),
            )
        return queryset.order_by("email")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class OrganizationAccountantsDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/organization-accountants/detail.html"
    context_object_name = "accountant"

    def get_queryset(self):
        return User.objects.filter(
            access_level=User.AccessChoices.ORGANIZATION_ACCOUNTANT
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AreasForm(
            user=self.request.user, initial={"areas": self.object.areas.all()}
        )
        return context

    def post(self, request, *args, **kwargs):
        accountant = self.get_object()
        if not request.user.has_admin_access:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        form = AreasForm(request.POST, user=request.user)
        if form.is_valid():
            accountant.first_name = request.POST.get("first_name")
            accountant.last_name = request.POST.get("last_name")
            accountant.cpf = request.POST.get("cpf")
            accountant.position = request.POST.get("position")
            accountant.is_active = request.POST.get("is_active") == "True"
            accountant.phone_number = request.POST.get("phone_number")

            accountant.areas.set(form.cleaned_data["areas"])
            accountant.save()

            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.UPDATED_ORGANIZATION_ACCOUNTANT,
                target_object_id=accountant.id,
                target_content_object=accountant,
            )

        return redirect("accounts:organization-accountants-list")


class OrganizationAccountantCreateView(AdminRequiredMixin, TemplateView):
    template_name = "accounts/organization-accountants/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = OrganizationAccountantCreateForm(request=self.request)

        return context

    def post(self, request, *args, **kwargs):
        if not request.user.can_add_new_organization_accountants:
            logger.error(
                f"{request.user.id} - dont have access to create new organization accountant"
            )
            return redirect("home")

        form = OrganizationAccountantCreateForm(request.POST, request=request)
        if form.is_valid():
            with transaction.atomic():
                password = generate_random_password()
                new_user = User.objects.create(
                    email=form.cleaned_data.get("email"),
                    position=form.cleaned_data.get("position"),
                    phone_number=str(form.cleaned_data["phone_number"].national_number),
                    cpf=form.cleaned_data.get("cpf"),
                    username=form.cleaned_data.get("email"),
                    first_name=form.cleaned_data.get("first_name"),
                    last_name=form.cleaned_data.get("last_name"),
                    organization=self.request.user.organization,
                    access_level=User.AccessChoices.ORGANIZATION_ACCOUNTANT,
                )
                new_user.set_password(password)
                new_user.save()
                new_user.areas.set(form.cleaned_data["areas"])

                logger.info(f"{request.user.id} - Created new organization accountant")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_ORGANIZATION_ACCOUNTANT,
                    target_object_id=new_user.id,
                    target_content_object=new_user,
                )

                notify_user_account_created(new_user, password)

            return redirect("accounts:organization-accountants-list")

        return self.render_to_response(self.get_context_data(form=form))


class OrganizationCommitteesListView(AdminRequiredMixin, ListView):
    model = User
    context_object_name = "committees_list"
    paginate_by = 10
    ordering = "email"

    template_name = "accounts/organization-committees/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            access_level=User.AccessChoices.COMMITTEE_MEMBER,
            areas__in=self.request.user.areas.all(),
        ).distinct()

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query),
            )
        return queryset.order_by("email")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


class OrganizationCommitteeCreateView(AdminRequiredMixin, TemplateView):
    template_name = "accounts/organization-committees/create.html"
    login_url = "/auth/login"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        if not context.get("form", None):
            context["form"] = OrganizationCommitteeCreateForm(request=self.request)

        return context

    def post(self, request, *args, **kwargs):
        if not request.user.can_add_new_organization_committees:
            logger.error(
                f"{request.user.id} - dont have access to create new organization committee"
            )
            return redirect("home")

        form = OrganizationCommitteeCreateForm(request.POST, request=request)
        if form.is_valid():
            with transaction.atomic():
                password = generate_random_password()
                new_user = User.objects.create(
                    email=form.cleaned_data.get("email"),
                    position="Membro do Comitê",
                    phone_number=str(form.cleaned_data["phone_number"].national_number),
                    cpf=form.cleaned_data.get("cpf"),
                    username=form.cleaned_data.get("email"),
                    first_name=form.cleaned_data.get("first_name"),
                    last_name=form.cleaned_data.get("last_name"),
                    organization=self.request.user.organization,
                    access_level=User.AccessChoices.COMMITTEE_MEMBER,
                )
                new_user.set_password(password)
                new_user.save()
                new_user.areas.set(form.cleaned_data["areas"])

                logger.info(f"{request.user.id} - Created new organization committee")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_ORGANIZATION_COMMITTEE,
                    target_object_id=new_user.id,
                    target_content_object=new_user,
                )

                notify_user_account_created(new_user, password)

            return redirect("accounts:organization-committees-list")

        return self.render_to_response(self.get_context_data(form=form))


class OrganizationCommitteesDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/organization-committees/detail.html"
    context_object_name = "committee"

    def get_queryset(self):
        return User.objects.filter(access_level=User.AccessChoices.COMMITTEE_MEMBER)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = AreasForm(
            user=self.request.user, initial={"areas": self.object.areas.all()}
        )
        return context

    def post(self, request, *args, **kwargs):
        committee = self.get_object()
        if not request.user.has_admin_access:
            return JsonResponse({"error": "Unauthorized"}, status=403)

        form = AreasForm(request.POST, user=request.user)
        if form.is_valid():
            committee.first_name = request.POST.get("first_name")
            committee.last_name = request.POST.get("last_name")
            committee.cpf = request.POST.get("cpf")
            committee.position = request.POST.get("position")
            committee.is_active = request.POST.get("is_active") == "True"
            committee.phone_number = request.POST.get("phone_number")

            committee.areas.set(form.cleaned_data["areas"])
            committee.save()

            _ = ActivityLog.objects.create(
                user=request.user,
                user_email=request.user.email,
                action=ActivityLog.ActivityLogChoices.UPDATED_ORGANIZATION_COMMITTEE,
                target_object_id=committee.id,
                target_content_object=committee,
            )

        return redirect("accounts:organization-committees-list")


@login_required
def user_unread_notifications(request):
    unread_notifications = request.user.notifications.filter(
        read_at__isnull=True
    ).order_by("-created_at")

    notifications = [
        {
            "id": notification.id,
            "category": notification.category_label,
            "text": notification.text,
            "created_at": notification.created_at.strftime("%d/%m/%Y %H:%M"),
            "read_url": reverse(
                "accounts:user-read-notifications", args=[str(notification.id)]
            ),
        }
        for notification in unread_notifications
    ]

    return JsonResponse({"notifications": notifications})


@login_required
def read_notification_view(request, pk):
    notification = get_object_or_404(Notification, id=pk, recipient=request.user)

    notification.read_at = timezone.now()
    notification.save()

    redirects = {
        Notification.Category.ACCOUNTABILITY_CREATED: "accountability:accountability-detail",
        Notification.Category.ACCOUNTABILITY_ANALISYS: "accountability:accountability-detail",
        Notification.Category.ACCOUNTABILITY_CORRECTING: "accountability:accountability-detail",
        Notification.Category.ACCOUNTABILITY_FINISHED: "accountability:accountability-detail",
        Notification.Category.CONTRACT_CREATED: "contracts:contracts-detail",
        Notification.Category.CONTRACT_STATUS: "contracts:contracts-detail",
        Notification.Category.CONTRACT_GOAL_COMMENTED: "contracts:contracts-detail",
        Notification.Category.CONTRACT_ITEM_COMMENTED: "contracts:contracts-detail",
        Notification.Category.CONTRACT_ITEM_VALUE_REQUESTED: "contracts:contracts-detail",
        Notification.Category.CONTRACT_ITEM_VALUE_REVIEWED: "contracts:contracts-detail",
    }
    destiny_url = redirects.get(notification.category, None)
    if not destiny_url:
        return redirect("home")

    return redirect(destiny_url, pk=notification.object_id)


@login_required
@require_POST
def toggle_folder_manager_status(request, pk):
    manager = get_object_or_404(
        User, pk=pk, access_level=User.AccessChoices.FOLDER_MANAGER
    )
    if not request.user.has_admin_access:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    manager.is_active = not manager.is_active
    if not manager.is_active:
        manager.deactivated_at = timezone.now()
    else:
        manager.deactivated_at = None
    manager.save()

    action = (
        "DESACTIVATED_FOLDER_MANAGER"
        if not manager.is_active
        else "ACTIVATED_FOLDER_MANAGER"
    )
    ActivityLog.objects.create(
        user=request.user,
        user_email=request.user.email,
        action=action,
        target_object_id=str(manager.id),
    )

    return redirect("accounts:folder-managers-list")


@login_required
@require_POST
def toggle_organization_accountant_status(request, pk):
    accountant = get_object_or_404(
        User, pk=pk, access_level=User.AccessChoices.ORGANIZATION_ACCOUNTANT
    )
    if not request.user.has_admin_access:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    accountant.is_active = not accountant.is_active
    if not accountant.is_active:
        accountant.deactivated_at = timezone.now()
    else:
        accountant.deactivated_at = None
    accountant.save()

    action = (
        "DESACTIVATED_ORGANIZATION_ACCOUNTANT"
        if not accountant.is_active
        else "ACTIVATED_ORGANIZATION_ACCOUNTANT"
    )
    ActivityLog.objects.create(
        user=request.user,
        user_email=request.user.email,
        action=action,
        target_object_id=str(accountant.id),
    )

    return redirect("accounts:organization-accountants-list")


@login_required
@require_POST
def toggle_organization_committee_status(request, pk):
    committee = get_object_or_404(
        User, pk=pk, access_level=User.AccessChoices.COMMITTEE_MEMBER
    )
    if not request.user.has_admin_access:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    committee.is_active = not committee.is_active
    if not committee.is_active:
        committee.deactivated_at = timezone.now()
    else:
        committee.deactivated_at = None
    committee.save()

    action = (
        "DESACTIVATED_ORGANIZATION_COMMITTEE"
        if not committee.is_active
        else "ACTIVATED_ORGANIZATION_COMMITTEE"
    )
    ActivityLog.objects.create(
        user=request.user,
        user_email=request.user.email,
        action=action,
        target_object_id=str(committee.id),
    )

    return redirect("accounts:organization-committees-list")
