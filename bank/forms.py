from django import forms

from bank.models import BankAccount, Transaction
from utils.fields import DecimalMaskedField
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseNumberFormWidget,
    BaseSelectFormWidget,
)


class UploadOFXForm(forms.Form):
    account_type = forms.ChoiceField(
        choices=BankAccount.AccountTypeChoices.choices,
        widget=BaseSelectFormWidget(),
    )
    origin = forms.ChoiceField(
        choices=BankAccount.OriginChoices.choices,
        widget=BaseSelectFormWidget(),
    )
    ofx_file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "class": "block w-full text-sm text-black border rounded-lg cursor-pointer focus:outline-none bg-gray-300 border-gray-600 placeholder-gray-400"
            }
        )
    )

    def clean_ofx_file(self):
        ofx_file = self.cleaned_data.get("ofx_file")

        if ofx_file:
            if not ofx_file.name.lower().endswith(".ofx"):
                raise forms.ValidationError(
                    "Somente arquivos do tipo OFX são permitidos."
                )

            if ofx_file.size > 5 * 1024 * 1024:  # Limite de 5 MB
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 5MB."
                )

        return ofx_file


class CreateBankAccountForm(forms.ModelForm):
    closing_date = forms.DateField()
    balance = forms.DecimalField()
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = BankAccount
        fields = [
            "bank_name",
            "bank_id",
            "account",
            "account_type",
            "origin",
            "agency",
            "balance",
        ]

        widgets = {
            "bank_name": BaseCharFieldFormWidget(),
            "bank_id": BaseNumberFormWidget(),
            "account": BaseCharFieldFormWidget(),
            "account_type": BaseSelectFormWidget(),
            "agency": BaseCharFieldFormWidget(),
            "origin": BaseSelectFormWidget(),
            "closing_date": forms.DateInput(
                attrs={"type": "closing_date"}, format="%d/%m/%Y"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["closing_date"].input_formats = ["%d/%m/%Y"]


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "name",
            "memo",
            "amount",
            "transaction_type",
            "transaction_id",
            "date",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "memo": BaseCharFieldFormWidget(),
            "amount": BaseNumberFormWidget(),
            "transaction_id": BaseCharFieldFormWidget(required=False),
            "transaction_type": BaseSelectFormWidget(),
            "date": forms.DateInput(attrs={"type": "date"}, format="%d/%m/%Y"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].input_formats = ["%d/%m/%Y"]


TransactionFormSet = forms.inlineformset_factory(
    BankAccount,
    Transaction,
    form=TransactionForm,
    extra=1,
    can_delete=True,
    min_num=0,
)
