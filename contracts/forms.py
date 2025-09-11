from decimal import Decimal

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Sum

from accounts.models import User
from contracts.models import (
    Company,
    Contract,
    ContractExecution,
    ContractExecutionActivity,
    ContractExecutionFile,
    ContractGoal,
    ContractInterestedPart,
    ContractItem,
    ContractItemNewValueRequest,
    ContractItemSupplement,
    ContractStep,
    ContractAddendum,
    ContractDocument,
)
from utils.fields import DecimalMaskedField
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseFileFormWidget,
    BaseNumberFormWidget,
    BaseSelectFormWidget,
    BaseTextAreaFormWidget,
    CustomPhoneNumberField,
)


class ContractCreateUpdateForm(forms.ModelForm):
    municipal_value = DecimalMaskedField(max_digits=12, decimal_places=2)
    counterpart_value = DecimalMaskedField(max_digits=12, decimal_places=2)
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
            "municipal_value",
            "counterpart_value",
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
            "name": BaseCharFieldFormWidget(placeholder="Contrato xxxxx"),
            "concession_type": BaseSelectFormWidget(),
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

    def clean(self):
        cleaned_data = super().clean()

        total_value = cleaned_data.get("total_value")
        municipal_value = cleaned_data.get("municipal_value")
        counterpart_value = cleaned_data.get("counterpart_value")

        if not all([bool(total_value), bool(total_value), bool(total_value)]):
            self.add_error("total_value", "Valores repassados não podem ser nulos.")

        if total_value != (municipal_value + counterpart_value):
            self.add_error(
                "total_value",
                "A soma dos valores repassados pelo município e contrapartida "
                "são diferentes do valor total do contrato",
            )

        return cleaned_data


class ContractItemForm(forms.ModelForm):
    month_expense = DecimalMaskedField(max_digits=12, decimal_places=2)

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
            "unit_type",
            "nature",
            "source",
            "file",
            "start_date",
            "end_date",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(),
            "objective": BaseTextAreaFormWidget(),
            "methodology": BaseTextAreaFormWidget(required=False),
            "observations": BaseTextAreaFormWidget(required=False),
            "quantity": BaseNumberFormWidget(),
            "month_quantity": BaseNumberFormWidget(),
            "unit_type": BaseCharFieldFormWidget(required=False),
            "nature": BaseSelectFormWidget(),
            "source": BaseSelectFormWidget(),
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
    fk_name="goal",
    form=ContractStepForm,
    extra=1,
    can_delete=True,
)


class ContractAddendumForm(forms.ModelForm):
    total_value = DecimalMaskedField(max_digits=12, decimal_places=2)
    municipal_value = DecimalMaskedField(max_digits=12, decimal_places=2)
    counterpart_value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = ContractAddendum
        fields = [
            "file",
            "start_of_vigency",
            "end_of_vigency",
            "total_value",
            "municipal_value",
            "counterpart_value",
        ]

        widgets = {
            "file": BaseFileFormWidget(required=True),
            "start_of_vigency": BaseCharFieldFormWidget(placeholder="dd/mm/aaaa"),
            "end_of_vigency": BaseCharFieldFormWidget(placeholder="dd/mm/aaaa"),
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


class ContractDocumentForm(forms.ModelForm):
    class Meta:
        model = ContractDocument
        fields = [
            "name",
            "type",
            "file",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="Nome do documento"),
            "type": BaseSelectFormWidget(),
            "file": BaseFileFormWidget(required=True),
        }

    def clean_file(self):
        file = self.cleaned_data.get("file")

        if file:
            extension = file.name.split(".")[-1].lower()
            if extension not in [
                "pdf",
                "doc",
                "docx",
                "xls",
                "xlsx",
                "jpg",
                "jpeg",
                "png",
            ]:
                raise forms.ValidationError(
                    "Arquivo inválido. Somente arquivos do tipo PDF, DOC, "
                    "DOCX, XLS, XLSX, JPG, JPEG ou PNG são permitidos."
                )

            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 10MB."
                )

        return file


class ContractDocumentUpdateForm(forms.ModelForm):
    class Meta:
        model = ContractDocument
        fields = [
            "name",
            "type",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="Nome do documento"),
            "type": BaseSelectFormWidget(),
        }


ContractStepFormSet = forms.inlineformset_factory(
    ContractGoal,
    ContractStep,
    fk_name="goal",
    form=ContractStepForm,
    extra=0,
    can_delete=True,
)


class CompanyCreateForm(forms.ModelForm):
    phone_number = CustomPhoneNumberField()

    class Meta:
        model = Company
        fields = [
            "name",
            "cnpj",
            "phone_number",
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


class CompanyUpdateForm(forms.ModelForm):
    phone_number = CustomPhoneNumberField()

    class Meta:
        model = Company
        fields = [
            "name",
            "phone_number",
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
            ).select_related("goal")
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


class ContractStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Contract
        fields = [
            "status",
        ]

        widgets = {
            "status": BaseSelectFormWidget(),
        }


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


class ContractInterestedForm(forms.ModelForm):
    class Meta:
        model = ContractInterestedPart
        fields = [
            "user",
            "interest",
        ]

        widgets = {
            "user": BaseSelectFormWidget(),
            "interest": BaseSelectFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)

        self.fields["user"].queryset = User.objects.filter(
            organization=self.contract.organization
        )


class ContractItemPurchaseProcessForm(forms.ModelForm):
    aquisition_value = DecimalMaskedField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"), "O valor deve ser maior que zero"),
            MaxValueValidator(Decimal("9999999.99"), "Valor máximo excedido"),
        ],
    )
    supplier_phone = CustomPhoneNumberField(required=False)

    class Meta:
        model = ContractItem
        fields = [
            "purchase_status",
            "observations",
            "aquisition_date",
            "parcel_due_date",
            "aquisition_value",
            "aquisition_parcel_quantity",
            "supplier",
            "supplier_document",
            "supplier_phone",
            "supplier_email",
            "supplier_address",
        ]

        widgets = {
            "purchase_status": BaseSelectFormWidget(),
            "observations": BaseTextAreaFormWidget(required=False),
            "aquisition_parcel_quantity": BaseNumberFormWidget(required=False),
            "supplier": BaseCharFieldFormWidget(required=False),
            "supplier_document": BaseCharFieldFormWidget(required=False),
            "supplier_email": BaseCharFieldFormWidget(required=False),
            "supplier_address": BaseCharFieldFormWidget(required=False),
        }


class ContractItemSupplementForm(forms.ModelForm):
    supplement_value = DecimalMaskedField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"), "O valor deve ser maior que zero"),
            MaxValueValidator(Decimal("9999999.99"), "Valor máximo excedido"),
        ],
    )

    class Meta:
        model = ContractItemSupplement
        fields = [
            "item",
            "supplement_value",
            "observations",
        ]

        widgets = {
            "item": BaseSelectFormWidget(),
            "observations": BaseTextAreaFormWidget(required=False),
        }

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["item"].queryset = ContractItem.objects.filter(
                contract=self.contract
            )


class ContractItemSupplementUpdateForm(forms.ModelForm):
    supplement_value = DecimalMaskedField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"), "O valor deve ser maior que zero"),
            MaxValueValidator(Decimal("9999999.99"), "Valor máximo excedido"),
        ],
    )

    class Meta:
        model = ContractItemSupplement
        fields = [
            "supplement_value",
            "observations",
        ]

        widgets = {
            "observations": BaseTextAreaFormWidget(required=False),
        }
