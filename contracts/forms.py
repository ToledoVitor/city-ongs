from decimal import Decimal

from django import forms
from django.db.models import Sum

from accounts.models import User
from contracts.models import (
    Company,
    Contract,
    ContractExecution,
    ContractExecutionActivity,
    ContractExecutionFile,
    ContractGoal,
    ContractItem,
    ContractItemNewValueRequest,
    ContractStep,
)
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
            "concession_type",
            "bidding",
            "law_num",
            "law_date",
            "agreement_num",
            "agreement_date",
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
            "concession_type": BaseCharFieldFormWidget(),
            "bidding": BaseCharFieldFormWidget(),
            "law_num": BaseCharFieldFormWidget(),
            "agreement_num": BaseCharFieldFormWidget(),
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
            "quantity",
            "month_quantity",
            "month_expense",
            "anual_expense",
            "unit_type",
            "nature",
            "file",
            "start_date",
            "end_date",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "objective": BaseTextAreaFormWidget(),
            "methodology": BaseTextAreaFormWidget(),
            "observations": BaseTextAreaFormWidget(),
            "quantity": BaseNumberFormWidget(),
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
            "observations": BaseTextAreaFormWidget(required=False),
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
            "number": BaseNumberFormWidget(),
            "complement": BaseCharFieldFormWidget(required=False),
            "district": BaseCharFieldFormWidget(),
            "city": BaseCharFieldFormWidget(),
            "uf": BaseSelectFormWidget(),
            "postal_code": BaseNumberFormWidget(),
        }


class ContractExecutionCreateForm(forms.ModelForm):
    class Meta:
        model = ContractExecution
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


class ContractExecutionActivityForm(forms.ModelForm):
    class Meta:
        model = ContractExecutionActivity
        fields = [
            "step",
            "name",
            "description",
            "percentage",
        ]

        widgets = {
            "step": BaseSelectFormWidget(),
            "name": BaseCharFieldFormWidget(),
            "description": BaseTextAreaFormWidget(),
            "percentage": BaseNumberFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.execution = kwargs.pop("execution", None)
        super().__init__(*args, **kwargs)
        if self.execution:
            self.fields["step"].queryset = ContractStep.objects.filter(
                goal__contract=self.execution.contract
            )
        else:
            self.fields["step"].queryset = ContractExecution.objects.none()


class ContractExecutionFileForm(forms.ModelForm):
    class Meta:
        model = ContractExecutionFile
        fields = [
            "name",
            "file",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "file": BaseFileFormWidget(),
        }


class ContractStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=Contract.ContractStatusChoices.choices,
        widget=BaseSelectFormWidget(),
    )


class ContractItemValueRequestForm(forms.ModelForm):
    month_raise = DecimalMaskedField(max_digits=12, decimal_places=2)
    anual_raise = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = ContractItemNewValueRequest
        fields = [
            "downgrade_item",
            "raise_item",
            "month_raise",
            "anual_raise",
        ]

        widgets = {
            "downgrade_item": BaseSelectFormWidget(),
            "raise_item": BaseSelectFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["downgrade_item"].queryset = ContractItem.objects.filter(
                contract=self.contract
            )
            self.fields["raise_item"].queryset = ContractItem.objects.filter(
                contract=self.contract
            )

    def clean(self):
        cleaned_data = super().clean()

        downgrade_item = cleaned_data["downgrade_item"]
        raise_item = cleaned_data["raise_item"]

        if downgrade_item == raise_item:
            raise forms.ValidationError("Escolha items diferentes.")

        if (
            raise_item.raise_requests.filter(
                status=ContractItemNewValueRequest.ReviewStatus.IN_REVIEW
            ).exists()
            or raise_item.downgrade_requests.filter(
                status=ContractItemNewValueRequest.ReviewStatus.IN_REVIEW
            ).exists()
        ):
            raise forms.ValidationError(
                "Já existe um solicitação de remanejamento para o item à incrementar."
            )

        if (
            downgrade_item.raise_requests.filter(
                status=ContractItemNewValueRequest.ReviewStatus.IN_REVIEW
            ).exists()
            or downgrade_item.downgrade_requests.filter(
                status=ContractItemNewValueRequest.ReviewStatus.IN_REVIEW
            ).exists()
        ):
            raise forms.ValidationError(
                "Já existe um solicitação de remanejamento para o item à diminuir."
            )

        if cleaned_data["anual_raise"] < cleaned_data["month_raise"]:
            raise forms.ValidationError(
                "O acréscimo anual não pode ser menor do que o acréscimo mensal."
            )

        expended_value = downgrade_item.expenses.filter(
            deleted_at__isnull=True
        ).aggregate(Sum("value"))["value__sum"] or Decimal("0.00")

        if (downgrade_item.anual_expense - cleaned_data["anual_raise"]) <= Decimal(
            "0.00"
        ):
            raise forms.ValidationError(
                "Não é possível criar a solicitação. O item à ser remanejado"
                "ficará com valor negativo."
            )

        if expended_value > (
            downgrade_item.anual_expense - cleaned_data["anual_raise"]
        ):
            raise forms.ValidationError(
                "Não é possível criar a solicitação. O item à ser remanejado não"
                "atingirá o valor necessário para cobrir as despesas anuais."
            )

        return cleaned_data


class ItemValueReviewForm(forms.ModelForm):
    class Meta:
        model = ContractItemNewValueRequest
        fields = [
            "status",
            "rejection_reason",
        ]

    def clean(self):
        cleaned_data = super().clean()

        rejected = cleaned_data["status"] == "REJECTED"
        if rejected and not cleaned_data["rejection_reason"]:
            raise forms.ValidationError("É necessário informar um motivo para rejeição")

        return cleaned_data
