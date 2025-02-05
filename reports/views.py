from datetime import datetime
from io import BytesIO
from typing import Any

from django.http import HttpResponse
from django.views.generic import TemplateView

from reports.forms import ReportForm
from reports.services import export_report, get_accountability


class ReportsView(TemplateView):
    template_name = "reports/export.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = ReportForm(request=self.request)
        context["missing_accountability"] = kwargs.get("missing_accountability", False)
        return context

    def post(self, request, *args, **kwargs):
        form = ReportForm(request.POST, request=self.request)
        if form.is_valid():
            accountability = get_accountability(
                contract=form.cleaned_data["contract"],
                month=form.cleaned_data["month"],
                year=form.cleaned_data["year"],
            )
            if not accountability:
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        missing_accountability=True,
                    ),
                )

            report_model = form.cleaned_data["report_model"]
            buffer = BytesIO()
            report = export_report(
                accountability=accountability,
                report_model=report_model,
            )
            report.output(buffer)
            buffer.seek(0)

            response = HttpResponse(buffer, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="{report_model}-{str(datetime.now().date())}.pdf"'
            )
            return response

        else:
            return self.render_to_response(self.get_context_data(form=form))
