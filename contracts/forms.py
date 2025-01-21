from django import forms

from accounts.models import Organization
from contracts.models import Contract, ContractGoal, ContractStep, Company
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseSelectFormWidget,
    BaseTextAreaFormWidget,
    BaseFileFormWidget,
)


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
            "organization",
            "file",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="TC 10/23 - Teste"),
            "objective": BaseTextAreaFormWidget(placeholder="Objetivo xxxx"),
            "contractor_company": BaseSelectFormWidget(
                placeholder="Empresa Contratante"
            ),
            "contractor_manager": BaseSelectFormWidget(
                placeholder="Gestor do Contratante"
            ),
            "hired_company": BaseSelectFormWidget(placeholder="Empresa Contratada"),
            "hired_manager": BaseSelectFormWidget(placeholder="Gestor da Contratada"),
            "organization": BaseSelectFormWidget(placeholder="Organização"),
            "file": BaseFileFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self.fields["organization"].queryset = Organization.objects.filter(
            user_organization_relationships__user=self.request.user
        )

    def clean_ofx_file(self):
        ofx_file = self.cleaned_data.get("ofx_file")

        if ofx_file:
            if not ofx_file.name.lower().endswith(".ofx"):
                raise forms.ValidationError(
                    "Somente arquivos do tipo OFX são permitidos."
                )

            if ofx_file.size > 10 * 1024 * 1024:  # Limite de 10 MB
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 10MB."
                )

        return ofx_file


class ContractStepForm(forms.ModelForm):
    class Meta:
        model = ContractStep
        fields = [
            "name",
            "objective",
            "methodology",
            "resources",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "objective": BaseTextAreaFormWidget(),
            "methodology": BaseTextAreaFormWidget(),
            "resources": BaseTextAreaFormWidget(),
        }


ContractStepFormSet = forms.inlineformset_factory(
    ContractGoal,
    ContractStep,
    form=ContractStepForm,
    extra=1,
    can_delete=True,
)


class CompanyCreateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "cnpj",
            # Address
            "street",
            "number",
            "complement",
            "district",
            "city",
            "uf",
            "postal_code",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "cnpj": BaseCharFieldFormWidget(),
            "street": BaseCharFieldFormWidget(),
            "complement": BaseCharFieldFormWidget(required=False),
            "district": BaseCharFieldFormWidget(),
            "city": BaseCharFieldFormWidget(),
            "uf": BaseSelectFormWidget(),
            "postal_code": BaseCharFieldFormWidget(),
        }
