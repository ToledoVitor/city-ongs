from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.functions import ExtractYear
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from accounts.models import OrganizationDocument
from contracts.models import Contract
from transparency_portal.models import (
    AccountabilityReport,
    FinancialTransfer,
    IrregularityReport,
    Organization,
    PartnershipTransparency,
)


class PartnershipListView(ListView):
    model = PartnershipTransparency
    template_name = "transparency_portal/partnership_list.html"
    context_object_name = "partnerships"
    paginate_by = 10
    ordering = ["-contract__start_of_vigency", "contract__name"]

    def get_queryset(self):
        queryset = PartnershipTransparency.objects.filter(is_public=True)

        # Filter by year if provided
        year = self.request.GET.get("year")
        if year:
            queryset = queryset.filter(contract__start_of_vigency__year=year)

        # Filter by organization if provided
        org_id = self.request.GET.get("organization")
        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        # Search by contract name or organization
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(contract__name__icontains=search)
                | Q(organization__name__icontains=search)
            )

        return queryset.select_related("contract", "organization")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obter anos únicos de start_of_vigency usando ExtractYear
        years = (
            Contract.objects.annotate(year=ExtractYear("start_of_vigency"))
            .values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )

        context["years"] = years

        # Obter organizações únicas
        context["organizations"] = (
            PartnershipTransparency.objects.filter(is_public=True)
            .values("organization")
            .distinct()
        )

        return context


class PartnershipDetailView(DetailView):
    model = PartnershipTransparency
    template_name = "transparency_portal/partnership_detail.html"
    context_object_name = "partnership"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        partnership = self.get_object()

        # Get financial transfers
        context["transfers"] = FinancialTransfer.objects.filter(
            partnership=partnership
        ).order_by("-transfer_date")

        # Get accountability reports
        context["accountability_reports"] = AccountabilityReport.objects.filter(
            partnership=partnership
        ).select_related("accountability")

        # Get irregularity reports
        context["irregularity_reports"] = IrregularityReport.objects.filter(
            partnership=partnership
        ).order_by("-report_date")

        return context


class OrganizationPartnershipListView(ListView):
    template_name = "transparency_portal/organization_partnerships.html"
    context_object_name = "partnerships"
    paginate_by = 10

    def get_queryset(self):
        org_id = self.kwargs["org_id"]
        return PartnershipTransparency.objects.filter(
            organization_id=org_id, is_public=True
        ).select_related("contract", "organization")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs["org_id"]
        context["organization"] = get_object_or_404(
            PartnershipTransparency.objects.filter(organization_id=org_id)
            .values("organization__name")
            .first()
        )
        return context


class IrregularityReportCreateView(LoginRequiredMixin, CreateView):
    model = IrregularityReport
    template_name = "transparency_portal/irregularity_report_form.html"
    fields = ["description"]
    success_url = reverse_lazy("transparency:partnership_list")

    def form_valid(self, form):
        partnership_id = self.kwargs["partnership_id"]
        form.instance.partnership = get_object_or_404(
            PartnershipTransparency, id=partnership_id
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        partnership_id = self.kwargs["partnership_id"]
        context["partnership"] = get_object_or_404(
            PartnershipTransparency, id=partnership_id
        )
        return context


class OrganizationDocumentListView(ListView):
    model = OrganizationDocument
    template_name = "transparency_portal/organization_documents.html"
    context_object_name = "documents"
    paginate_by = 10
    ordering = ["-uploaded_at"]

    def get_queryset(self):
        return OrganizationDocument.objects.filter(
            organization_id=self.kwargs["organization_id"], is_public=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = get_object_or_404(
            Organization, id=self.kwargs["organization_id"]
        )
        return context
