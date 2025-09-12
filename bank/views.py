import logging
from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction as django_transaction
from django.db.models import Prefetch, Sum
from django.db.models.query import QuerySet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now as tz_now
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView

from activity.models import ActivityLog
from bank.forms import (
    BankAccountForm,
    TransactionFormSet,
    UpdateBankStatementForm,
    UpdateOFXForm,
)
from bank.models import BankAccount, BankStatement
from bank.services.ofx_exporter import OFXStatementExporter
from bank.services.ofx_parser import OFXFileParser
from contracts.models import Contract

logger = logging.getLogger(__name__)


class BankAccountDetailView(LoginRequiredMixin, DetailView):
    model = BankAccount
    template_name = "bank-account/detail.html"
    login_url = "/auth/login"

    def get_queryset(self) -> QuerySet[Any]:
        return (
            super()
            .get_queryset()
            .select_related(
                "contract",
            )
            .prefetch_related(
                Prefetch(
                    "statements",
                    queryset=BankStatement.objects.order_by("-closing_date"),
                ),
                Prefetch(
                    "transactions",
                    queryset=BankStatement.objects.order_by("-date"),
                ),
            )
        )

    def get_object(self, queryset=None):
        return self.model.objects.get(id=self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        return context


@login_required
@csrf_exempt
def preparse_ofx_file_view(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    bank_account = get_object_or_404(BankAccount, id=pk)
    if "ofx_file" not in request.FILES:
        return JsonResponse({"error": "No file provided"}, status=400)

    try:
        parser = OFXFileParser(ofx_file=request.FILES["ofx_file"])
        period_info = parser.statement_period_info

        existing_statement = BankStatement.objects.filter(
            bank_account=bank_account,
            reference_month=period_info["month"],
            reference_year=period_info["year"],
        ).exists()

        return JsonResponse({
            "success": True,
            "period": period_info,
            "statement_exists": existing_statement,
            "account_info": {
                "bank_name": parser.account_data.get("bank_name"),
                "account_id": parser.account_data.get("account_id"),
            }
        })

    except ValidationError as e:
        logger.error(f"Validation error parsing OFX file: {str(e)}")
        error_message = str(e)
        if hasattr(e, 'message'):
            error_message = e.message
        elif hasattr(e, 'messages') and e.messages:
            error_message = e.messages[0] if isinstance(e.messages, list) else str(e.messages)
        
        return JsonResponse({
            "success": False,
            "error": error_message
        })
    except Exception as e:
        logger.error(f"Unexpected error parsing OFX file: {str(e)}")
        return JsonResponse({
            "success": False,
            "error": "Erro ao analisar arquivo OFX. Verifique se o arquivo está válido."
        })


@login_required
def update_bank_account_ofx_view(request, pk):
    bank_account = get_object_or_404(BankAccount, id=pk)
    if request.method == "POST":
        form = UpdateOFXForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                OFXFileParser(
                    ofx_file=request.FILES["ofx_file"]
                ).update_bank_account_balance(bank_account=bank_account)

                logger.info(f"{request.user.id} - Updated bank account")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPLOADED_BALANCE_FILE,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                return redirect("bank:bank-accounts-detail", pk=bank_account.id)
            except Exception as e:
                logger.error(f"Error updating bank account: {str(e)}")
                return render(
                    request,
                    "bank-account/ofx-update.html",
                    {
                        "form": form,
                        "object": bank_account,
                        "statement_exists": True,
                    },
                )
    else:
        form = UpdateOFXForm()
        return render(
            request,
            "bank-account/ofx-update.html",
            {"form": form, "object": bank_account},
        )


@login_required
def create_bank_account_view(request, pk):
    contract = get_object_or_404(Contract, id=pk)
    if request.method == "POST":
        form = BankAccountForm(request.POST)
        if form.is_valid():
            if _account_type_already_created(
                contract, form.cleaned_data["account_type"]
            ):
                return render(
                    request,
                    "bank-account/create.html",
                    {
                        "form": form,
                        "contract": contract,
                        "account_exists": True,
                    },
                )

            with django_transaction.atomic():
                bank_account = form.save()
                if bank_account.account_type == "CHECKING":
                    contract.checking_account = bank_account
                else:
                    contract.investing_account = bank_account

                contract.save()

                logger.info(f"{request.user.id} - Created new bank account")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.CREATED_BANK_ACCOUNT,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                return redirect("bank:bank-accounts-detail", pk=bank_account.id)
    else:
        form = BankAccountForm()

    return render(
        request,
        "bank-account/create.html",
        {
            "form": form,
            "contract": contract,
        },
    )


@login_required
def update_bank_account_manual_view(request, pk):
    bank_account = get_object_or_404(BankAccount, id=pk)
    if request.method == "POST":
        form = UpdateBankStatementForm(request.POST)
        transactions_formset = TransactionFormSet(request.POST)
        if form.is_valid() and transactions_formset.is_valid():
            if _statement_already_uploaded(
                bank_account=bank_account,
                month=form.cleaned_data["reference_month"],
                year=form.cleaned_data["reference_year"],
            ):
                return render(
                    request,
                    "bank-account/manual-update.html",
                    {
                        "form": form,
                        "object": bank_account,
                        "transactions_formset": transactions_formset,
                        "statement_exists": True,
                    },
                )

            with django_transaction.atomic():
                BankStatement.objects.create(
                    bank_account=bank_account,
                    reference_month=form.cleaned_data["reference_month"],
                    reference_year=form.cleaned_data["reference_year"],
                    opening_balance=form.cleaned_data["opening_balance"],
                    closing_balance=form.cleaned_data["closing_balance"],
                )

                transactions = transactions_formset.save(commit=False)
                for transaction in transactions:
                    transaction.bank_account = bank_account
                    transaction.save()

                logger.info(f"{request.user.id} - Updated bank account")
                _ = ActivityLog.objects.create(
                    user=request.user,
                    user_email=request.user.email,
                    action=ActivityLog.ActivityLogChoices.UPDATED_BANK_ACCOUNT,
                    target_object_id=bank_account.id,
                    target_content_object=bank_account,
                )
                return redirect("bank:bank-accounts-detail", pk=bank_account.id)

    else:
        form = UpdateBankStatementForm()
        transactions_formset = TransactionFormSet()
        return render(
            request,
            "bank-account/manual-update.html",
            {
                "form": form,
                "object": bank_account,
                "transactions_formset": transactions_formset,
            },
        )


def _statement_already_uploaded(bank_account: BankAccount, month: int, year: int):
    return BankStatement.objects.filter(
        bank_account=bank_account, reference_month=month, reference_year=year
    ).exists()


def _account_type_already_created(contract: Contract, account_type: str):
    if account_type == "CHECKING":
        return contract.checking_account is not None

    if account_type == "INVESTING":
        return contract.investing_account is not None

    return True


@login_required
def bank_statement_view(request, pk):
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    status_filter = request.GET.get("status", "all")  # "all", "reconciled" ou "pending"

    account = get_object_or_404(BankAccount, id=pk)

    if not (start_date_str and end_date_str):
        context = {
            "account": account,
            "statement_days": [],
            "start_date": start_date_str,
            "end_date": end_date_str,
            "status": status_filter,
        }
        return render(request, "bank-account/statement.html", context)

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

    all_transactions = (
        account.transactions.filter(date__gte=start_date)
        .prefetch_related(
            "expenses",
            "revenues",
        )
        .order_by("-date")
    )

    daily_totals = (
        all_transactions.values("date")
        .annotate(total_day=Sum("amount"))
        .order_by("-date")
    )
    daily_totals_dict = {item["date"]: item["total_day"] for item in daily_totals}

    statement_days = []
    current_balance = account.balance
    sorted_dates_desc = sorted(daily_totals_dict.keys(), reverse=True)
    for day in sorted_dates_desc:
        total_day = daily_totals_dict[day]
        close_balance = current_balance
        open_balance = close_balance - total_day

        transactions_day = [t for t in all_transactions if t.date == day]
        statement_days.append(
            {
                "date": day,
                "open_balance": open_balance,
                "close_balance": close_balance,
                "all_transactions": transactions_day,
            }
        )
        current_balance = open_balance
    statement_days.reverse()

    display_statement_days = []
    for day_info in statement_days:
        if not (start_date <= day_info["date"] <= end_date):
            continue

        displayed_transactions = []
        for t in day_info["all_transactions"]:
            trans_status = (
                "Conciliada"
                if (t.expenses.exists() or t.revenues.exists())
                else "Pendente"
            )
            if (
                status_filter == "all"
                or (
                    status_filter == "reconciled"
                    and (t.expenses.exists() or t.revenues.exists())
                )
                or (
                    status_filter == "pending"
                    and not (t.expenses.exists() or t.revenues.exists())
                )
            ):
                displayed_transactions.append(
                    {
                        "obj": t,
                        "status": trans_status,
                    }
                )
        day_info["transactions"] = displayed_transactions
        display_statement_days.append(day_info)

    context = {
        "account": account,
        "statement_days": display_statement_days,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "status": status_filter,
    }
    return render(request, "bank-account/statement.html", context)


def bank_statement_ofx_export_view(request, pk):
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = tz_now().date() - timedelta(days=30)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = tz_now().date()

    account = get_object_or_404(BankAccount, id=pk)
    transactions = account.transactions.filter(
        date__range=[start_date, end_date]
    ).order_by("date")

    ofx_content = OFXStatementExporter.handle(
        account=account,
        transactions=transactions,
        start_date=start_date,
        end_date=end_date,
    )
    response = HttpResponse(ofx_content, content_type="application/x-ofx")
    filename = f"extrato_{account.account}.ofx"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.set_cookie("fileDownload", "true", max_age=60)
    return response
