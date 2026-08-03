import base64
import logging
from io import BytesIO
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views.generic import TemplateView

from contracts.models import Contract, ContractInterestedPart
from reports.forms import REPORT_MODEL_LABELS, ReportForm
from reports.services import export_report

logger = logging.getLogger(__name__)

GENERIC_FAILURE_MESSAGE = "Não foi possível gerar o relatório. Revise o contrato e o período e tente novamente."


def build_report_filename(report_model: str, contract: Contract) -> str:
    """Slug-based filename — no spaces, no accents, stable across platforms."""
    return (
        f"{slugify(report_model)}-{slugify(contract.name_with_code)}"
        f"-{timezone.now().strftime('%Y-%m-%d')}.pdf"
    )


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "reports/export.html"
    # settings has no LOGIN_URL, so Django's /accounts/login/ default would
    # 404. Matches the login_url used across the contracts views.
    login_url = "/auth/login"

    def get_form(self):
        return ReportForm(request=self.request)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        context["form"] = form

        if form.is_bound and "contract" in form.data:
            try:
                contract_id = form.data.get("contract")
                if contract_id:
                    contract = Contract.objects.get(id=contract_id)
                    form.get_responsible_formset(contract)
            except (Contract.DoesNotExist, ValueError, TypeError):
                pass
        else:
            form.get_responsible_formset()

        return context

    def post(self, request):
        form = ReportForm(request.POST, request=request)
        if form.is_valid():
            contract: Contract = form.cleaned_data["contract"]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]

            if not contract.checking_account and not contract.investing_account:
                messages.error(
                    request,
                    "O contrato escolhido ainda está em planejamento "
                    "e/ou não tem contas bancárias cadastradas.",
                )
                return self.render_to_response(self.get_context_data(form=form))

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
            filename = build_report_filename(report_model, contract)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            response.set_cookie("fileDownload", "true", max_age=60)
            return response

        else:
            return self.render_to_response(self.get_context_data(form=form))


class ReportGenerateAPIView(LoginRequiredMixin, TemplateView):
    login_url = "/auth/login"

    def post(self, request):
        try:
            form = ReportForm(request.POST, request=request)
            if not form.is_valid():
                return JsonResponse(
                    {
                        "success": False,
                        "errors": form.errors,
                        "message": "Dados do formulário inválidos",
                    },
                    status=400,
                )

            contract: Contract = form.cleaned_data["contract"]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]

            if not contract.checking_account and not contract.investing_account:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "O contrato escolhido ainda está em "
                        "planejamento e/ou não tem contas "
                        "bancárias cadastradas.",
                    },
                    status=400,
                )

            responsible_formset = form.get_responsible_formset(contract)
            responsibles = []
            if responsible_formset and responsible_formset.is_valid():
                for responsible_form in responsible_formset.forms:
                    if (
                        responsible_form.cleaned_data
                        and responsible_form.cleaned_data.get("user")
                    ):
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

            pdf_data = buffer.read()
            pdf_base64 = base64.b64encode(pdf_data).decode("utf-8")

            filename = build_report_filename(report_model, contract)

            # Check if it's an AJAX request expecting JSON
            is_ajax = request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest" and "application/json" in request.headers.get(
                "Accept", ""
            )

            if is_ajax:
                return JsonResponse(
                    {
                        "success": True,
                        "pdf_data": pdf_base64,
                        "filename": filename,
                        "contract_name": contract.name_with_code,
                        "report_model": report_model,
                        "report_model_label": REPORT_MODEL_LABELS.get(
                            report_model, report_model
                        ),
                        "start_date": start_date.strftime("%d/%m/%Y"),
                        "end_date": end_date.strftime("%d/%m/%Y"),
                    }
                )
            else:
                # Return PDF directly (for new tab opening or download)
                pdf_bytes = base64.b64decode(pdf_base64)
                response = HttpResponse(pdf_bytes, content_type="application/pdf")

                # Check if download is forced
                if request.POST.get("download") == "1":
                    response["Content-Disposition"] = (
                        f'attachment; filename="{filename}"'
                    )
                else:
                    response["Content-Disposition"] = f'inline; filename="{filename}"'

                return response

        except (ValueError, AttributeError, TypeError, KeyError):
            # The exception text leaks internals (attribute names, model
            # internals) straight into the UI, so it goes to the log and the
            # user gets an actionable message instead.
            logger.exception(
                "Report generation failed for user %s",
                getattr(request.user, "id", None),
            )
            return JsonResponse(
                {"success": False, "message": GENERIC_FAILURE_MESSAGE}, status=500
            )
