from django import forms

from contracts.models import Contract


class ContractCreateForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            "name",
            "objective",
            "total_value",
            "start_of_vigency",
            "end_of_vigency",
            "contractor_company",
            "contractor_manager",
            "hired_company",
            "hired_manager",
            "ong",
        ]

    # widgets = {
    #     'title': forms.TextInput(attrs={
    #         'class': 'form-control',   # Adiciona uma classe CSS personalizada
    #         'placeholder': 'Enter the post title',  # Placeholder
    #         'style': 'width: 100%; font-size: 18px;',  # Estilo inline (se necessário)
    #     }),
    # }
