from io import BytesIO
from typing import Any
from django.views.generic import TemplateView
from django.http import HttpResponse

from datetime import datetime

from reports.forms import ReportForm
from reports.services import export_report


class ReportsView(TemplateView):
    template_name = "reports/export.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["form"] = ReportForm(request=self.request)
        return context
    
    def post(self, request, *args, **kwargs):
        form = ReportForm(request.POST, request=self.request)
        if form.is_valid():
            report_model = form.cleaned_data["report_model"]

            buffer = BytesIO()
            report = export_report(
                contract=form.cleaned_data["contract"],
                report_model=report_model,
                month=form.cleaned_data["month"],
                year=form.cleaned_data["year"],
            )
            report.output(buffer)
            buffer.seek(0)

            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{report_model}-{str(datetime.now().date())}.pdf"'
            return response

        else:
            return self.render_to_response(self.get_context_data(form=form))