from django import forms

from accountability.models import ExpenseSource, RevenueSource
from utils.widgets import BaseCharFieldFormWidget, BaseSelectFormWidget


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

    # def clean(self):
    #     return cleaned_data
