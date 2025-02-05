from django import forms

from accountability.models import (
    Accountability,
    Expense,
    Favored,
    ResourceSource,
    Revenue,
)
from contracts.models import ContractItem
from utils.fields import DecimalMaskedField
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
        ]

        widgets = {
            "identification": BaseCharFieldFormWidget(),
            "observations": BaseTextAreaFormWidget(),
            "value": BaseNumberFormWidget(),
            "source": BaseSelectFormWidget(required=False),
            "favored": BaseSelectFormWidget(required=False),
            "item": BaseSelectFormWidget(),
            "nature": BaseSelectFormWidget(),
            "liquidation_form": BaseSelectFormWidget(),
            "document_type": BaseSelectFormWidget(),
            "document_number": BaseCharFieldFormWidget(),
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


class RevenueForm(forms.ModelForm):
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = Revenue
        fields = [
            "identification",
            "observations",
            "value",
            "competency",
            "due_date",
            "source",
            "bank_account",
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
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields[
                "source"
            ].queryset = self.request.user.organization.resource_sources.all()
        else:
            self.fields[
                "source"
            ].queryset = self.request.user.organization.resource_sources.none()


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
