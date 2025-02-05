from django import forms

from accounts.models import User
from contracts.models import Company, Contract, ContractGoal, ContractItem, ContractStep
from utils.fields import DecimalMaskedField
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseFileFormWidget,
    BaseNumberFormWidget,
    BaseSelectFormWidget,
    BaseTextAreaFormWidget,
)


class ContractCreateForm(forms.ModelForm):
    total_value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = Contract
        fields = [
            "name",
            "bidding",
            "objective",
            "total_value",
            "start_of_vigency",
            "end_of_vigency",
            "contractor_company",
            "contractor_manager",
            "hired_company",
            "hired_manager",
            "accountability_autority",
            "supervision_autority",
            "area",
            "file",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="TC 10/23 - Teste"),
            "bidding": BaseCharFieldFormWidget(),
            "objective": BaseTextAreaFormWidget(placeholder="Objetivo xxxx"),
            "contractor_company": BaseSelectFormWidget(
                placeholder="Empresa Contratante"
            ),
            "contractor_manager": BaseSelectFormWidget(
                placeholder="Gestor do Contratante"
            ),
            "accountability_autority": BaseSelectFormWidget(
                placeholder="Responsável Contábil",
            ),
            "supervision_autority": BaseSelectFormWidget(
                placeholder="Fiscal Responsável",
            ),
            "hired_company": BaseSelectFormWidget(placeholder="Empresa Contratada"),
            "hired_manager": BaseSelectFormWidget(placeholder="Gestor da Contratada"),
            "area": BaseSelectFormWidget(placeholder="Area de Atuação"),
            "file": BaseFileFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        user_org = self.request.user.organization

        self.fields["area"].queryset = self.request.user.areas.all()
        self.fields["accountability_autority"].queryset = User.objects.filter(
            organization=user_org,
            access_level=User.AccessChoices.ORGANIZATION_ACCOUNTANT,
        )
        self.fields["supervision_autority"].queryset = User.objects.filter(
            organization=user_org,
            access_level=User.AccessChoices.FOLDER_MANAGER,
        )

    def clean_file(self):
        file = self.cleaned_data.get("file")

        if file:
            if not file.name.lower().endswith(".pdf"):
                raise forms.ValidationError(
                    "Somente arquivos do tipo PDF são permitidos."
                )

            if file.size > 10 * 1024 * 1024:  # Limite de 10 MB
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 10MB."
                )

        return file


class ContractItemForm(forms.ModelForm):
    month_expense = DecimalMaskedField(max_digits=12, decimal_places=2)
    anual_expense = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = ContractItem
        fields = [
            "name",
            "objective",
            "methodology",
            "observations",
            "month_quantity",
            "month_expense",
            "anual_expense",
            "unit_type",
            "nature",
            "file",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "objective": BaseTextAreaFormWidget(),
            "methodology": BaseTextAreaFormWidget(),
            "observations": BaseTextAreaFormWidget(),
            "month_quantity": BaseNumberFormWidget(),
            "unit_type": BaseCharFieldFormWidget(),
            "nature": BaseSelectFormWidget(),
            "file": BaseFileFormWidget(required=False),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")

        if file:
            if not file.name.lower().endswith(".pdf"):
                raise forms.ValidationError(
                    "Somente arquivos do tipo PDF são permitidos."
                )

            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 10MB."
                )

        return file

class ContractGoalForm(forms.ModelForm):
    class Meta:
        model = ContractGoal
        fields = [
            "name",
            "objective",
            "methodology",
            "observations",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "objective": BaseTextAreaFormWidget(),
            "methodology": BaseTextAreaFormWidget(),
            "observations": BaseTextAreaFormWidget(),
        }


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


ContractExtraStepFormSet = forms.inlineformset_factory(
    ContractGoal,
    ContractStep,
    form=ContractStepForm,
    extra=1,
    can_delete=True,
)


ContractStepFormSet = forms.inlineformset_factory(
    ContractGoal,
    ContractStep,
    form=ContractStepForm,
    extra=0,
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
