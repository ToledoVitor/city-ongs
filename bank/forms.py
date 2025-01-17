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


class UploadOFXForm(forms.Form):
    contract = forms.ModelChoiceField(
        queryset=Contract.objects.none(),
        widget=BaseSelectFormWidget(placeholder="Contrato Vinculado à Conta"),
    )
    ofx_file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "class": "block w-full text-sm text-black border border-gray-300 rounded-lg cursor-pointer dark:text-black focus:outline-none bg-gray-300 dark:border-gray-600 dark:placeholder-gray-400"
            }
        )
    )

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if request:
            user_areas = request.user.areas.all()
            self.fields["contract"].queryset = Contract.objects.filter(
                area__in=user_areas
            )

    def clean_ofx_file(self):
        ofx_file = self.cleaned_data.get("ofx_file")

        if ofx_file:
            if not ofx_file.name.lower().endswith(".ofx"):
                raise forms.ValidationError("Somente arquivos OFX são permitidos.")

            # Verificar o tamanho do arquivo (opcional)
            if ofx_file.size > 5 * 1024 * 1024:  # Limite de 5 MB
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 5MB."
                )

        return ofx_file

    # # Verificar o tipo MIME (opcional)
    # if ofx_file.content_type != 'application/pdf':
    #     raise forms.ValidationError("O arquivo enviado não é um OFX válido.")
