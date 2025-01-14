from django import forms

from contracts.models import Contract, ContractGoal, ContractSubGoal
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseSelectFormWidget,
    BaseTextAreaFormWidget,
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
            "ong",
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
            "ong": BaseSelectFormWidget(placeholder="Ong"),
        }


class ContractSubGoalForm(forms.ModelForm):
    class Meta:
        model = ContractSubGoal
        fields = [
            "name",
            "description",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "description": BaseTextAreaFormWidget(),
        }


ContractSubGoalFormSet = forms.inlineformset_factory(
    ContractGoal,
    ContractSubGoal,
    form=ContractSubGoalForm,
    extra=1,
    can_delete=True,
)
