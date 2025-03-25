from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.utils import timezone
from django.views.generic import TemplateView

from accountability.models import Accountability, Expense, Revenue
from contracts.models import Contract


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    login_url = "/auth/login"

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
        if period != "all":
            if period == "current_month":
                start_date = today.replace(day=1)
            elif period == "last_3_months":
                start_date = (today - relativedelta(months=2)).replace(day=1)
            elif period == "last_6_months":
                start_date = (today - relativedelta(months=5)).replace(day=1)
            elif period == "last_year":
                start_date = (today - relativedelta(months=11)).replace(day=1)

            if start_date:
                accountabilities = accountabilities.filter(
                    Q(year__gt=start_date.year)
                    | Q(year=start_date.year, month__gte=start_date.month)
                ).filter(
                    Q(year__lt=today.year) | Q(year=today.year, month__lte=today.month)
                )

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

        if period == "all":
            num_months = 12
            start_date = today - relativedelta(months=11)
        elif period == "current_month":
            num_months = 1
            start_date = today.replace(day=1)
        elif period == "last_3_months":
            num_months = 3
            start_date = (today - relativedelta(months=2)).replace(day=1)
        elif period == "last_6_months":
            num_months = 6
            start_date = (today - relativedelta(months=5)).replace(day=1)
        else:  # last_year
            num_months = 12
            start_date = (today - relativedelta(months=11)).replace(day=1)

        current_date = start_date
        for _ in range(num_months):
            month_name = current_date.strftime("%B")
            months.append(month_name)

            monthly_count = accountabilities.filter(
                year=current_date.year, month=current_date.month, status="FINISHED"
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

            current_date = current_date + relativedelta(months=1)

        context["monthly_labels"] = months
        context["monthly_data"] = monthly_data
        context["months_labels"] = months
        context["revenue_data"] = revenue_data
        context["expenses_data"] = expenses_data

        context["contracts"] = contracts
        return context
