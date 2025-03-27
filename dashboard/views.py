from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from accountability.models import Accountability, Expense, Revenue
from contracts.models import Contract, ContractMonthTransfer


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    login_url = "/auth/login"

    brazilian_months = {
        1: "Janeiro",
        2: "Fevereiro",
        3: "Março",
        4: "Abril",
        5: "Maio",
        6: "Junho",
        7: "Julho",
        8: "Agosto",
        9: "Setembro",
        10: "Outubro",
        11: "Novembro",
        12: "Dezembro",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        period = self.request.GET.get("period", "current_month")

        status_raw = self.request.GET.getlist("status[]", [])
        status_list = []
        for status in status_raw:
            status_list.extend(status.split(","))

        contract_raw = self.request.GET.getlist("contract[]", [])
        contract_list = []
        for contract in contract_raw:
            contract_list.extend(contract.split(","))

        status_list = [s for s in status_list if s]
        contract_list = [c for c in contract_list if c]

        context["period"] = period
        context["selected_status"] = status_list
        context["selected_contracts"] = contract_list

        start_date = None

        contracts = Contract.objects.filter(area__in=self.request.user.areas.all())

        accountabilities = Accountability.objects.filter(
            contract__area__in=self.request.user.areas.all()
        )

        today = timezone.now().date()
        match period:
            case "current_month":
                start_date = today.replace(day=1)
            case "last_3_months":
                start_date = (today - relativedelta(months=2)).replace(day=1)
            case "last_6_months":
                start_date = (today - relativedelta(months=5)).replace(day=1)
            case "last_year":
                start_date = (today - relativedelta(months=11)).replace(day=1)
            case _:
                start_date = (today - relativedelta(years=1)).replace(day=1)

        accountabilities = accountabilities.filter(
            Q(year__gt=start_date.year)
            | Q(year=start_date.year, month__gte=start_date.month)
        ).filter(Q(year__lt=today.year) | Q(year=today.year, month__lte=today.month))

        if status_list:
            accountabilities = accountabilities.filter(status__in=status_list)

        if contract_list:
            accountabilities = accountabilities.filter(contract_id__in=contract_list)

        context["total_contracts"] = contracts.count()
        context["active_accountabilities"] = accountabilities.filter(
            status__in=["WIP", "SENT", "CORRECTING"]
        ).count()

        revenues = Revenue.objects.filter(
            accountability__in=accountabilities, deleted_at__isnull=True
        )
        expenses = Expense.objects.filter(
            accountability__in=accountabilities, deleted_at__isnull=True
        )

        if contract_list:
            revenues = revenues.filter(accountability__contract_id__in=contract_list)
            expenses = expenses.filter(accountability__contract_id__in=contract_list)

        context["total_revenue"] = revenues.aggregate(total=Sum("value"))["total"] or 0
        context["total_expenses"] = expenses.aggregate(total=Sum("value"))["total"] or 0

        context["recent_accountabilities"] = (
            accountabilities.select_related("contract")
            .annotate(
                count_revenues=Count(
                    "revenues",
                    filter=Q(revenues__deleted_at__isnull=True),
                    distinct=True,
                ),
                count_expenses=Count(
                    "expenses",
                    filter=Q(expenses__deleted_at__isnull=True),
                    distinct=True,
                ),
            )
            .order_by("-year", "-month")[:10]
        )

        months = []
        monthly_data = []
        revenue_data = []
        expenses_data = []
        transfer_data = []

        match period:
            case "last_year":
                num_months = 12
                start_date = (today - relativedelta(months=11)).replace(day=1)
            case "last_6_months":
                num_months = 6
                start_date = (today - relativedelta(months=5)).replace(day=1)
            case "last_3_months":
                num_months = 3
                start_date = (today - relativedelta(months=2)).replace(day=1)
            case "current_month":
                num_months = 1
                start_date = today.replace(day=1)
            case _:
                num_months = 1
                start_date = today.replace(day=1)

        current_date = start_date
        for _ in range(num_months):
            month_name = current_date.strftime("%B")
            months.append(month_name)

            monthly_count = accountabilities.filter(
                year=current_date.year,
                month=current_date.month,
            ).count()
            monthly_data.append(monthly_count)

            month_revenues = (
                revenues.filter(
                    accountability__year=current_date.year,
                    accountability__month=current_date.month,
                ).aggregate(total=Sum("value"))["total"]
                or 0
            )
            revenue_data.append(float(month_revenues))

            month_expenses = (
                expenses.filter(
                    accountability__year=current_date.year,
                    accountability__month=current_date.month,
                ).aggregate(total=Sum("value"))["total"]
                or 0
            )
            expenses_data.append(float(month_expenses))

            if contract_list:
                month_transfer = (
                    ContractMonthTransfer.objects.filter(
                        contract__id__in=contract_list,
                        year=current_date.year,
                        month=current_date.month,
                    ).aggregate(total=Sum("value"))["total"]
                    or 0
                )
            else:
                month_transfer = (
                    ContractMonthTransfer.objects.filter(
                        contract__in=contracts,
                        year=current_date.year,
                        month=current_date.month,
                    ).aggregate(total=Sum("value"))["total"]
                    or 0
                )

            transfer_data.append(float(month_transfer))
            current_date = current_date + relativedelta(months=1)

        context["monthly_labels"] = months
        context["monthly_data"] = monthly_data
        context["months_labels"] = months
        context["revenue_data"] = revenue_data
        context["expenses_data"] = expenses_data
        context["transfer_data"] = transfer_data
        context["contracts"] = contracts
        context["monthly_progress_data"] = list(
            zip(months, revenue_data, expenses_data, transfer_data)
        )

        return context
