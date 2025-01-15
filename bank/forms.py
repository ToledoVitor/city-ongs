from django import forms

from bank.models import BankAccount
from contracts.models import Contract
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseSelectFormWidget,
)


class BankAccountCreateForm(forms.ModelForm):
    class Meta:
        model = BankAccount
        fields = [
            "bank_name",
            "account",
            "agency",
            "contract",
        ]

        widgets = {
            "bank_name": BaseCharFieldFormWidget(placeholder="Banco do Brasil S.A."),
            "account": BaseCharFieldFormWidget(placeholder="xxxxxxxx"),
            "agency": BaseCharFieldFormWidget(placeholder="xxxx"),
            "contract": BaseSelectFormWidget(placeholder="Contrato Vinculado à Conta"),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            user_areas = self.request.user.areas.all()
            self.fields["contrato"].queryset = Contract.objects.filter(
                area__in=user_areas
            )
