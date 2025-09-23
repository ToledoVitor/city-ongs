import base64
from io import BytesIO
from typing import Any

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView

from contracts.models import Contract, ContractInterestedPart
from reports.forms import ReportForm
from reports.services import export_report


class ReportsView(TemplateView):
    template_name = "reports/export.html"

    def get_form(self):
        return ReportForm(request=self.request)

    def get_context_data(
        self, **kwargs: Any
    ) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = self.get_form()
        context["form"] = form
        context["missing_banks"] = kwargs.get("missing_banks", False)

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
                                        responsible_form.cleaned_data[
                                            "interest"
                                        ]
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


class ReportGenerateAPIView(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            form = ReportForm(request.POST, request=request)
            if not form.is_valid():
                return JsonResponse({
                    "success": False,
                    "errors": form.errors,
                    "message": "Dados do formulário inválidos"
                }, status=400)

            contract: Contract = form.cleaned_data["contract"]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]

            if (
                not contract.checking_account
                and not contract.investing_account
            ):
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
                    if responsible_form.cleaned_data:
                        responsibles.append({
                            "user": responsible_form.cleaned_data["user"],
                            "interest_label": (
                                ContractInterestedPart.InterestLevel(
                                    responsible_form.cleaned_data["interest"]
                                ).label
                            ),
                        })

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
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

            filename = (
                f"{report_model}_{contract.name}_"
                f"{timezone.now().strftime('%Y-%m-%d')}.pdf"
            )

            # Check if it's an AJAX request expecting JSON
            is_ajax = (
                request.headers.get("X-Requested-With") == "XMLHttpRequest"
                and "application/json" in request.headers.get("Accept", "")
            )

            if is_ajax:
                return JsonResponse({
                    "success": True,
                    "pdf_data": pdf_base64,
                    "filename": filename,
                    "contract_name": contract.name,
                    "report_model": report_model,
                    "start_date": start_date.strftime("%d/%m/%Y"),
                    "end_date": end_date.strftime("%d/%m/%Y"),
                })
            else:
                # Return PDF directly (for new tab opening or download)
                pdf_bytes = base64.b64decode(pdf_base64)
                response = HttpResponse(
                    pdf_bytes, content_type="application/pdf"
                )

                # Check if download is forced
                if request.POST.get("download") == "1":
                    response["Content-Disposition"] = (
                        f'attachment; filename="{filename}"'
                    )
                else:
                    response["Content-Disposition"] = (
                        f'inline; filename="{filename}"'
                    )

                return response

        except (ValueError, AttributeError) as e:
            return JsonResponse({
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }, status=500)
