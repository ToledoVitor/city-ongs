import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.query import QuerySet
from django.views.generic import ListView

# from accountability.forms import FolderManagerCreateForm, OngAccountantCreateForm
from accountability.models import RevenueSource, ExpenseSource

logger = logging.getLogger(__name__)


class RevenueSourceListView(LoginRequiredMixin, ListView):
    model = RevenueSource
    context_object_name = "sources"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "accountability/revenue-souce/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            city_hall__in=self.request.user.city_halls.all()
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context

class ExpenseSourceListView(LoginRequiredMixin, ListView):
    model = ExpenseSource
    context_object_name = "sources"
    paginate_by = 10
    ordering = "-created_at"

    template_name = "accountability/expense-source/list.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        queryset = self.model.objects.filter(
            city_hall__in=self.request.user.city_halls.all()
        )
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("q", "")
        return context


# class FolderManagersDetailView(LoginRequiredMixin, DetailView):
#     model = User

#     template_name = "accounts/folder-managers/detail.html"
#     context_object_name = "manager"

#     login_url = "/auth/login"

#     def get_object(self, queryset=None):
#         return self.model.objects.get(id=self.kwargs["pk"])

#     def get_context_data(self, **kwargs) -> dict:
#         context = super().get_context_data(**kwargs)
#         return context


# class FolderManagerCreateView(AdminRequiredMixin, TemplateView):
#     template_name = "accounts/folder-managers/create.html"
#     login_url = "/auth/login"

#     def get_context_data(self, **kwargs) -> dict:
#         context = super().get_context_data(**kwargs)
#         if not context.get("form", None):
#             context["form"] = FolderManagerCreateForm(request=self.request)

#         return context

#     def post(self, request, *args, **kwargs):
#         if not request.user.can_add_new_folder_managers:
#             logger.error(
#                 f"{request.user.id} - dont have access to create new folder managers"
#             )
#             return redirect("home")

#         form = FolderManagerCreateForm(request.POST, request=request)
#         if form.is_valid():
#             with transaction.atomic():
#                 new_user = User.objects.create(
#                     email=form.cleaned_data["email"],
#                     username=form.cleaned_data["email"],
#                     first_name=form.cleaned_data["first_name"],
#                     last_name=form.cleaned_data["last_name"],
#                     password=form.cleaned_data["password"],
#                     access_level=User.AccessChoices.FOLDER_MANAGER,
#                 )

#                 logger.info(f"{request.user.id} - Created new folder manager")
#                 _ = ActivityLog.objects.create(
#                     user=request.user,
#                     user_email=request.user.email,
#                     action=ActivityLog.ActivityLogChoices.CREATED_FOLDER_MANAGER,
#                     target_object_id=new_user.id,
#                     target_content_object=new_user,
#                 )
#                 return redirect("accounts:folder-managers-list")

#         return self.render_to_response(self.get_context_data(form=form))

