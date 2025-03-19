from django import forms
from django.db.models import Q, Sum

from accountability.models import (
    Accountability,
    AccountabilityFile,
    Expense,
    Favored,
    ResourceSource,
    Revenue,
)
from bank.models import BankAccount, Transaction
from contracts.models import ContractItem
from utils.fields import DecimalMaskedField
from utils.formats import format_into_brazilian_currency
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseFileFormWidget,
    BaseNumberFormWidget,
    BaseSelectFormWidget,
    BaseTextAreaFormWidget,
    CustomCheckboxSelectMultiple,
)


class ResourceSourceForm(forms.ModelForm):
    class Meta:
        model = ResourceSource
        fields = [
            "name",
            "document",
            "origin",
            "category",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
            "document": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
            "origin": BaseSelectFormWidget(),
            "category": BaseSelectFormWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        document = cleaned_data.get("document")

        queryset = ResourceSource.objects.filter(name=name, document=document)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise forms.ValidationError(
                "Já existe uma fonte criada com esse nome e documento."
            )

        return cleaned_data


class ExpenseForm(forms.ModelForm):
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = Expense
        fields = [
            "identification",
            "observations",
            "value",
            "source",
            "favored",
            "item",
            "nature",
            "due_date",
            "competency",
            "liquidation",
            "liquidation_form",
            "document_type",
            "document_number",
            "planned",
        ]

        widgets = {
            "identification": BaseCharFieldFormWidget(),
            "observations": BaseTextAreaFormWidget(),
            "value": BaseNumberFormWidget(),
            "source": BaseSelectFormWidget(required=False),
            "favored": BaseSelectFormWidget(required=False),
            "item": BaseSelectFormWidget(required=False),
            "nature": BaseSelectFormWidget(required=False),
            "liquidation_form": BaseSelectFormWidget(),
            "document_type": BaseSelectFormWidget(required=False),
            "document_number": BaseCharFieldFormWidget(required=False),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.accountability = kwargs.pop("accountability", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields[
                "source"
            ].queryset = self.request.user.organization.resource_sources.all()
            self.fields[
                "favored"
            ].queryset = self.request.user.organization.favoreds.all()
        else:
            self.fields["source"].queryset = ResourceSource.objects.none()
            self.fields["favored"].queryset = Favored.objects.none()

        if self.accountability:
            self.fields["item"].queryset = self.accountability.contract.items.all()
        else:
            self.fields["item"].queryset = ContractItem.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        planned = cleaned_data["planned"]
        item = cleaned_data["item"]

        if planned and not item:
            raise forms.ValidationError(
                "As despesas planejadas devem estar relacionadas com um item de"
                " aquisição do contrato."
            )
        elif not planned and item:
            raise forms.ValidationError(
                "As despesas não planejadas não podem estar relacionadas com um item de"
                " aquisição do contrato."
            )
        elif not planned and not cleaned_data["nature"]:
            raise forms.ValidationError(
                "As despesas não planejadas precisam ter uma natureza da despesa."
            )

        if planned:
            expended_value = item.expenses.filter(deleted_at__isnull=True).aggregate(
                Sum("value")
            )["value__sum"]
            if (expended_value + cleaned_data["value"]) > item.anual_expense:
                raise forms.ValidationError(
                    "A despesa ultrapassará o custo anual planejado."
                    "Solicite um remanejamento na página de items."
                )

        return cleaned_data


class RevenueForm(forms.ModelForm):
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = Revenue
        fields = [
            "identification",
            "observations",
            "value",
            "competency",
            "receive_date",
            "bank_account",
            "source",
            "revenue_nature",
        ]

        widgets = {
            "identification": BaseCharFieldFormWidget(),
            "observations": BaseTextAreaFormWidget(),
            "value": BaseCharFieldFormWidget(),
            "bank_account": BaseSelectFormWidget(),
            "source": BaseSelectFormWidget(),
            "revenue_nature": BaseSelectFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.accountability: Accountability = kwargs.pop("accountability", None)
        super().__init__(*args, **kwargs)

        checking_account_id = getattr(
            self.accountability.contract.checking_account, "id", None
        )
        investing_account_id = getattr(
            self.accountability.contract.investing_account, "id", None
        )
        self.fields["bank_account"].queryset = BankAccount.objects.filter(
            Q(id=checking_account_id) | Q(id=investing_account_id)
        )


class AccountabilityCreateForm(forms.ModelForm):
    class Meta:
        model = Accountability
        fields = [
            "month",
            "year",
        ]

        widgets = {
            "month": BaseSelectFormWidget(),
            "year": BaseNumberFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["year"].initial = 2025


class FavoredForm(forms.ModelForm):
    class Meta:
        model = Favored
        fields = [
            "name",
            "document",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
            "document": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        document = cleaned_data.get("document")

        queryset = Favored.objects.filter(name=name, document=document)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise forms.ValidationError(
                "Já existe uma fonte criada com esse nome e documento."
            )

        return cleaned_data


class ImportXLSXAccountabilityForm(forms.Form):
    xlsx_file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "class": "block w-full text-sm text-black border rounded-lg cursor-pointer focus:outline-none bg-gray-300 border-gray-600 placeholder-gray-400"
            }
        )
    )

    def clean_xlsx(self):
        xlsx = self.cleaned_data.get("xlsx")

        if xlsx:
            if not (xlsx.name.lower().endswith(".xlsx")):
                raise forms.ValidationError(
                    "Somente arquivos do tipo .xlsx são permitidos."
                )

            if xlsx.size > 10 * 1024 * 1024:  # Limite de 10 MB
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 10MB."
                )

        return xlsx


class CustomTransactionMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.date:%d/%m/%Y}, {format_into_brazilian_currency(obj.amount)}, {obj.memo}, {obj.name}"


class ReconcileExpenseForm(forms.Form):
    transactions = CustomTransactionMultipleChoiceField(
        queryset=Transaction.objects.none(),
        widget=CustomCheckboxSelectMultiple(
            input_attrs={
                "class": "w-4 h-4 text-blue-600 rounded-sm focus:ring-blue-600 ring-offset-gray-800 focus:ring-2 bg-gray-400 border-gray-500"
            }
        ),
        required=True,
    )

    class Meta:
        model: Expense
        fields = [
            "transactions",
        ]

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        self.expense = kwargs.pop("expense", None)
        self.relateds = kwargs.pop("relateds", [])
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["transactions"].queryset = (
                Transaction.objects.filter(
                    Q(bank_account=self.contract.checking_account)
                    | Q(bank_account=self.contract.investing_account)
                )
                .filter(
                    expenses=None,
                    revenues=None,
                    amount__lte=0,
                )
                .order_by("date")
            )

    def clean_transactions(self):
        transactions = self.cleaned_data.get("transactions")

        if not transactions:
            raise forms.ValidationError("Informe as transações correspondentes")

        transaction_amount = sum([transaction.amount for transaction in transactions])
        expenses_amount = self.expense.value
        for related_expense in self.relateds:
            expenses_amount += related_expense.value

        if abs(transaction_amount) != abs(expenses_amount):
            raise forms.ValidationError(
                "Soma das transações diferente do valor da despesa."
            )

        return transactions


class ReconcileRevenueForm(forms.Form):
    transactions = CustomTransactionMultipleChoiceField(
        queryset=Transaction.objects.none(),
        widget=CustomCheckboxSelectMultiple(
            input_attrs={
                "class": "w-4 h-4 text-blue-600 rounded-sm focus:ring-blue-600 ring-offset-gray-800 focus:ring-2 bg-gray-400 border-gray-500"
            }
        ),
        required=True,
    )

    class Meta:
        model: Revenue
        fields = [
            "transactions",
        ]

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        self.revenue = kwargs.pop("revenue", None)
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["transactions"].queryset = (
                Transaction.objects.filter(
                    Q(bank_account=self.contract.checking_account)
                    | Q(bank_account=self.contract.investing_account)
                )
                .filter(
                    expenses=None,
                    revenues=None,
                    amount__gte=0,
                )
                .order_by("date")
            )

    def clean_transactions(self):
        transactions = self.cleaned_data.get("transactions")

        if not transactions:
            raise forms.ValidationError("Informe as transações correspondentes")

        amount = sum([transaction.amount for transaction in transactions])
        if amount != self.revenue.value:
            raise forms.ValidationError(
                "Soma das transações diferente do valor da receita."
            )

        return transactions


class AccountabilityFileForm(forms.ModelForm):
    class Meta:
        model = AccountabilityFile
        fields = [
            "name",
            "file",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="Arquivo xxxxx"),
            "file": BaseFileFormWidget(),
        }
