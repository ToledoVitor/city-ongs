from django import forms

from accountability.models import (
    Accountability,
    Expense,
    ExpenseSource,
    Revenue,
    RevenueSource,
)
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseNumberFormWidget,
    BaseSelectFormWidget,
    BaseTextAreaFormWidget,
)


class ExpenseSourceCreateForm(forms.ModelForm):
    class Meta:
        model = ExpenseSource
        fields = [
            "name",
            "document",
        ]

        widgets = {
            "organization": BaseSelectFormWidget(placeholder="Prefeitura"),
            "name": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
        }


class ExpenseCreateForm(forms.ModelForm):
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
            # "competency": BaseCharFieldFormWidget(),
            # "liquidation": BaseCharFieldFormWidget(),
            "liquidation_form": BaseSelectFormWidget(),
            "document_type": BaseSelectFormWidget(),
            "document_number": BaseCharFieldFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields[
                "source"
            ].queryset = self.request.user.organization.expense_sources.all()
        else:
            self.fields[
                "source"
            ].queryset = self.request.user.organization.expense_sources.none()


class RevenueSourceCreateForm(forms.ModelForm):
    class Meta:
        model = RevenueSource
        fields = [
            "organization",
            "name",
            "document",
            "contract_number",
            "origin",
            "category",
        ]

        widgets = {
            "organization": BaseSelectFormWidget(placeholder="Organização"),
            "name": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
            "contract_number": BaseCharFieldFormWidget(
                placeholder="xxxx.xxxxx.xx.xx.xx.xx"
            ),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self.fields["city_hall"].queryset = self.request.user.city_halls.all()
        self.fields["origin"].widget.attrs.update(
            {
                "class": " ".join(
                    [
                        "w-full p-2.5 block text-sm border border-gray-300 text-gray-900",
                        "bg-gray-50 rounded-lg focus:ring-blue-500 focus:border-blue-500",
                        "dark:placeholder-gray-600 dark:bg-gray-300 dark:border-gray-600",
                        "dark:text-black dark:focus:ring-blue-500 dark:focus:border-blue-500",
                    ]
                )
            }
        )
        self.fields["category"].widget.attrs.update(
            {
                "class": " ".join(
                    [
                        "w-full p-2.5 block text-sm border border-gray-300 text-gray-900",
                        "bg-gray-50 rounded-lg focus:ring-blue-500 focus:border-blue-500",
                        "dark:placeholder-gray-600 dark:bg-gray-300 dark:border-gray-600",
                        "dark:text-black dark:focus:ring-blue-500 dark:focus:border-blue-500",
                    ]
                )
            }
        )


class RevenueCreateForm(forms.ModelForm):
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
            # "competency": BaseCharFieldFormWidget(),
            # "due_date": BaseCharFieldFormWidget(),
            "source": BaseSelectFormWidget(),
            "revenue_nature": BaseSelectFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields[
                "source"
            ].queryset = self.request.user.organization.revenue_sources.all()
        else:
            self.fields[
                "source"
            ].queryset = self.request.user.organization.revenue_sources.none()


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
