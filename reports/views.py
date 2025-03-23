from io import BytesIO
from typing import Any

from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import TemplateView

from contracts.models import Contract, ContractInterestedPart
from reports.forms import ReportForm
from reports.services import export_report


class ReportsView(TemplateView):
    template_name = "reports/export.html"

    def get_form(self):
        return ReportForm(request=self.request)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        context["form"] = form
        context["missing_banks"] = kwargs.get("missing_banks", False)

        if form.is_bound and form.cleaned_data.get("contract"):
            form.get_responsible_formset(form.cleaned_data["contract"])
        elif not form.is_bound and form.fields["contract"].queryset.exists():
            form.get_responsible_formset(form.fields["contract"].queryset.first())

        return context

    def post(self, request, *args, **kwargs):
        form = ReportForm(request.POST, request=request)
        if form.is_valid():
            contract: Contract = form.cleaned_data["contract"]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]

            if not contract.checking_account and not contract.investing_account:
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        missing_banks=True,
                    ),
                )

            responsible_formset = form.get_responsible_formset(contract)
            responsibles = []
            if responsible_formset and responsible_formset.is_valid():
                for responsible_form in responsible_formset.forms:
                    if responsible_form.cleaned_data:
                        responsibles.append(
                            {
                                "user": responsible_form.cleaned_data["user"],
                                "interest_label": (
                                    ContractInterestedPart.InterestLevel(
                                        responsible_form.cleaned_data["interest"]
                                    ).label
                                ),
                            }
                        )

            buffer = BytesIO()

            report_model = form.cleaned_data["report_model"]
            report = export_report(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
                report_model=report_model,
                responsibles=responsibles,
            )
            report.output(buffer)

            buffer.seek(0)

            response = HttpResponse(buffer, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="{report_model}_{contract.name}_'
                f'{timezone.now().strftime("%Y-%m-%d")}.pdf"'
            )
            response.set_cookie("fileDownload", "true", max_age=60)
            return response

        else:
            return self.render_to_response(self.get_context_data(form=form))
