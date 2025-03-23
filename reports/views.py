from datetime import datetime
from io import BytesIO
from typing import Any

from django.http import HttpResponse
from django.utils.timezone import make_aware
from django.views.generic import TemplateView

from reports.forms import ReportForm
from reports.services import export_report


class ReportsView(TemplateView):
    template_name = "reports/export.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form", ReportForm(request=self.request))
        context["missing_banks"] = kwargs.get("missing_banks", False)
        return context

    def post(self, request, *args, **kwargs):
        form = ReportForm(request.POST, request=self.request)
        if form.is_valid():
            contract = form.cleaned_data["contract"]

            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]

            start_date = make_aware(start_date)
            end_date = make_aware(end_date)

            if (
                not contract.checking_account
                and not contract.investing_account
            ):
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        missing_banks=True,
                    ),
                )

            buffer = BytesIO()

            report_model = form.cleaned_data["report_model"]
            report = export_report(
                contract=contract,
                start_date=start_date,
                end_date=end_date,
                report_model=report_model,
            )
            report.output(buffer)

            buffer.seek(0)

            response = HttpResponse(buffer, content_type="application/pdf")
            response["Content-Disposition"] = (
                f'attachment; filename="{report_model}-{str(datetime.now().date())}.pdf"'
            )
            response.set_cookie("fileDownload", "true", max_age=60)
            return response

        else:
            return self.render_to_response(self.get_context_data(form=form))
