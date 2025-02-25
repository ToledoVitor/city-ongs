from datetime import datetime
from io import BytesIO
from typing import Any

from django.http import HttpResponse
from django.views.generic import TemplateView

from contracts.models import Contract
from reports.forms import ReportForm
from reports.services import export_report, get_model_for_report


class ReportsView(TemplateView):
    template_name = "reports/export.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = ReportForm(request=self.request)
        context["missing_accountability"] = kwargs.get("missing_accountability", False)
        context["missing_banks"] = kwargs.get("missing_banks", False)
        return context

    def post(self, request, *args, **kwargs):
        form = ReportForm(request.POST, request=self.request)
        if form.is_valid():
            model, start_date, end_date = get_model_for_report(form)

            if type(model) is Contract and (
                not model.checking_account and not model.investing_account
            ):
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        missing_banks=True,
                    ),
                )

            if not model:
                return self.render_to_response(
                    self.get_context_data(
                        form=form,
                        missing_accountability=True,
                    ),
                )

            buffer = BytesIO()

            report_model = form.cleaned_data["report_model"]
            report = export_report(
                model=model,
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
            return response

        else:
            return self.render_to_response(self.get_context_data(form=form))
