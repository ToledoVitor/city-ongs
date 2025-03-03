from django import forms
from django.db.models import Q, Sum

from accountability.models import (
    Accountability,
    Expense,
    Favored,
    ResourceSource,
    Revenue,
)
from bank.models import Transaction
from contracts.models import ContractItem
from utils.fields import DecimalMaskedField
from utils.formats import format_into_brazilian_currency
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseNumberFormWidget,
    BaseSelectFormWidget,
    BaseTextAreaFormWidget,
)


class ResourceSourceCreateForm(forms.ModelForm):
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
            "origin": BaseSelectFormWidget(),
            "category": BaseSelectFormWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        document = cleaned_data.get("document")

        if ResourceSource.objects.filter(name=name, document=document).exists():
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

        if Favored.objects.filter(name=name, document=document).exists():
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
        return (
            f"Data: {obj.date:%d/%m/%Y}, {format_into_brazilian_currency(obj.amount)}"
        )


class ReconcileExpenseForm(forms.Form):
    transactions = CustomTransactionMultipleChoiceField(
        queryset=Transaction.objects.none(),
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "style": "max-height: 200px; overflow-y: scroll;",
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
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["transactions"].queryset = Transaction.objects.filter(
                Q(bank_account=self.contract.checking_account)
                | Q(bank_account=self.contract.investing_account)
            ).filter(expense__isnull=True)
