from django import forms

from accountability.models import Accountability, ExpenseSource, RevenueSource
from utils.widgets import BaseCharFieldFormWidget, BaseSelectFormWidget, BaseNumberFormWidget


class ExpenseSourceCreateForm(forms.ModelForm):
    class Meta:
        model = ExpenseSource
        fields = [
            "city_hall",
            "name",
            "document",
        ]

        widgets = {
            "city_hall": BaseSelectFormWidget(placeholder="Prefeitura"),
            "name": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields["city_hall"].queryset = self.request.user.city_halls.all()


class RevenueSourceCreateForm(forms.ModelForm):
    class Meta:
        model = RevenueSource
        fields = [
            "city_hall",
            "name",
            "document",
            "contract_number",
            "origin",
            "category",
        ]

        widgets = {
            "city_hall": BaseSelectFormWidget(placeholder="Prefeitura"),
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