from decimal import Decimal

from django import forms
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce

from accountability.models import (
    Accountability,
    AccountabilityFile,
    ActivityReportPublication,
    ActivityReportPublicationStatus,
    AnnualStatement,
    BalanceAdjustment,
    BoardParticipation,
    BudgetCommitment,
    ConclusiveOpinion,
    ConclusiveOpinionDeclaration,
    ConflictOfInterestDeclaration,
    Deduction,
    EvaluationReport,
    Expense,
    ExpenseRejection,
    Favored,
    FinancialStatements,
    FinancialStatementsPublication,
    FundTransfer,
    OpinionOrMinutes,
    OpinionOrMinutesPublication,
    PhysicalFinancialExecutionStatement,
    PhysicalFinancialExecutionStatementPublication,
    PurchasingRegulation,
    PurchasingRegulationPublication,
    Refund,
    RelatedCompany,
    ResourceSource,
    Revenue,
)
from bank.models import BankAccount, Transaction
from contracts.models import ContractItem
from utils.fields import DecimalMaskedField
from utils.formats import format_into_brazilian_currency
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseDateFormWidget,
    BaseFileFormWidget,
    BaseNumberFormWidget,
    BaseSelectFormWidget,
    BaseTextAreaFormWidget,
    CustomCheckboxSelectMultiple,
    CustomCPFWidget,
)


class ResourceSourceForm(forms.ModelForm):
    class Meta:
        model = ResourceSource
        fields = [
            "name",
            "document",
            "origin",
            "category",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
            "document": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
            "origin": BaseSelectFormWidget(),
            "category": BaseSelectFormWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        document = cleaned_data.get("document")

        queryset = ResourceSource.objects.filter(name=name, document=document)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise forms.ValidationError(
                "Já existe uma fonte criada com esse nome e documento."
            )

        return cleaned_data


class ExpenseForm(forms.ModelForm):
    value = DecimalMaskedField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"), "O valor deve ser maior que zero"),
            MaxValueValidator(Decimal("9999999.99"), "Valor máximo excedido"),
        ],
    )

    def clean_identification(self):
        identification = self.cleaned_data.get("identification")
        if identification:
            # Remove caracteres especiais e espaços extras
            identification = " ".join(identification.split())

            # Verifica comprimento mínimo
            if len(identification) < 5:
                raise forms.ValidationError(
                    "A identificação deve ter pelo menos 5 caracteres"
                )

        return identification

    def clean_document_number(self):
        document_number = self.cleaned_data.get("document_number")
        document_type = self.cleaned_data.get("document_type")

        if document_type and not document_number:
            raise forms.ValidationError(
                "O número do documento é obrigatório quando o tipo é informado"
            )

        if document_number and not document_type:
            raise forms.ValidationError(
                "O tipo do documento é obrigatório quando o número é informado"
            )

        return document_number

    def clean(self):
        cleaned_data = super().clean()
        value = cleaned_data.get("value")
        item = cleaned_data.get("item")

        if value and item:
            # Verifica se o valor excede o orçamento do item
            if (
                item.expenses.filter(deleted_at__isnull=True).aggregate(
                    total=Coalesce(Sum("value"), Decimal("0.00"))
                )["total"]
                + value
                > item.anual_expense
            ):
                raise forms.ValidationError(
                    f"O valor excede o orçamento disponível do item "
                    f"({format_into_brazilian_currency(item.anual_expense)})"
                )

        due_date = cleaned_data.get("due_date")
        competency = cleaned_data.get("competency")
        if due_date and competency and due_date < competency:
            raise forms.ValidationError(
                "A data de vencimento não pode ser anterior à data de competência"
            )

        return cleaned_data

    class Meta:
        model = Expense
        fields = [
            "identification",
            "observations",
            "value",
            "source",
            "favored",
            "item",
            "nature",
            "due_date",
            "competency",
            "liquidation",
            "liquidation_form",
            "document_type",
            "document_number",
            "planned",
        ]

        widgets = {
            "identification": BaseCharFieldFormWidget(),
            "observations": BaseTextAreaFormWidget(required=False),
            "value": BaseNumberFormWidget(),
            "source": BaseSelectFormWidget(required=False),
            "favored": BaseSelectFormWidget(required=False),
            "item": BaseSelectFormWidget(required=False),
            "nature": BaseSelectFormWidget(required=False),
            "liquidation_form": BaseSelectFormWidget(),
            "document_type": BaseSelectFormWidget(required=False),
            "document_number": BaseCharFieldFormWidget(required=False),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.accountability = kwargs.pop("accountability", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields["source"].queryset = ResourceSource.objects.filter(
                organization=self.request.user.organization
            )
            self.fields["favored"].queryset = Favored.objects.filter(
                organization=self.request.user.organization
            )
        else:
            self.fields["source"].queryset = ResourceSource.objects.none()
            self.fields["favored"].queryset = Favored.objects.none()

        if self.accountability:
            self.fields["item"].queryset = self.accountability.contract.items.all()
        else:
            self.fields["item"].queryset = ContractItem.objects.none()


class RevenueForm(forms.ModelForm):
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = Revenue
        fields = [
            "identification",
            "observations",
            "value",
            "competency",
            "receive_date",
            "bank_account",
            "source",
            "revenue_nature",
        ]

        widgets = {
            "identification": BaseCharFieldFormWidget(),
            "observations": BaseTextAreaFormWidget(required=False),
            "value": BaseCharFieldFormWidget(),
            "bank_account": BaseSelectFormWidget(),
            "source": BaseSelectFormWidget(),
            "revenue_nature": BaseSelectFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.accountability: Accountability = kwargs.pop("accountability", None)
        super().__init__(*args, **kwargs)

        checking_account_id = getattr(
            self.accountability.contract.checking_account, "id", None
        )
        investing_account_id = getattr(
            self.accountability.contract.investing_account, "id", None
        )
        self.fields["bank_account"].queryset = BankAccount.objects.filter(
            Q(id=checking_account_id) | Q(id=investing_account_id)
        )


class AccountabilityCreateForm(forms.ModelForm):
    class Meta:
        model = Accountability
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


class FavoredForm(forms.ModelForm):
    class Meta:
        model = Favored
        fields = [
            "name",
            "document",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
            "document": BaseCharFieldFormWidget(placeholder="Fonte xxxx"),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        document = cleaned_data.get("document")

        queryset = Favored.objects.filter(name=name, document=document)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)

        if queryset.exists():
            raise forms.ValidationError(
                "Já existe uma fonte criada com esse nome e documento."
            )

        return cleaned_data


class ImportXLSXAccountabilityForm(forms.Form):
    xlsx_file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "class": "block w-full text-sm text-black border rounded-lg cursor-pointer focus:outline-none bg-gray-300 border-gray-600 placeholder-gray-400"
            }
        )
    )

    def clean_xlsx(self):
        xlsx = self.cleaned_data.get("xlsx")

        if xlsx:
            if not (xlsx.name.lower().endswith(".xlsx")):
                raise forms.ValidationError(
                    "Somente arquivos do tipo .xlsx são permitidos."
                )

            if xlsx.size > 10 * 1024 * 1024:  # Limite de 10 MB
                raise forms.ValidationError(
                    "O tamanho máximo permitido para o arquivo é 10MB."
                )

        return xlsx


class CustomTransactionMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        base_string = (
            f"{obj.date:%d/%m/%Y}, "
            f"{format_into_brazilian_currency(obj.amount)}, "
            f"{obj.memo}"
        )
        if obj.name:
            base_string += f", {obj.name}"
        return base_string


class ReconcileExpenseForm(forms.Form):
    transactions = CustomTransactionMultipleChoiceField(
        queryset=Transaction.objects.none(),
        widget=CustomCheckboxSelectMultiple(
            input_attrs={
                "class": "w-4 h-4 text-blue-600 rounded-sm focus:ring-blue-600 ring-offset-gray-800 focus:ring-2 bg-gray-400 border-gray-500"
            }
        ),
        required=True,
    )

    class Meta:
        model: Expense
        fields = [
            "transactions",
        ]

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        self.expense = kwargs.pop("expense", None)
        self.relateds = kwargs.pop("relateds", [])
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["transactions"].queryset = (
                Transaction.objects.filter(
                    Q(bank_account=self.contract.checking_account)
                    | Q(bank_account=self.contract.investing_account)
                )
                .filter(
                    expenses=None,
                    revenues=None,
                    amount__lte=0,
                )
                .order_by("date")
            )

    def clean_transactions(self):
        transactions = self.cleaned_data.get("transactions")

        if not transactions:
            raise forms.ValidationError("Informe as transações correspondentes")

        transaction_amount = sum([transaction.amount for transaction in transactions])
        expenses_amount = self.expense.value
        for related_expense in self.relateds:
            expenses_amount += related_expense.value

        if abs(transaction_amount) != abs(expenses_amount):
            raise forms.ValidationError(
                "Soma das transações diferente do valor da despesa."
            )

        if not all(
            [transaction.date == self.expense.due_date for transaction in transactions]
        ):
            raise forms.ValidationError(
                "As transações devem ter a mesma data da despesa."
            )

        return transactions


class ReconcileRevenueForm(forms.Form):
    transactions = CustomTransactionMultipleChoiceField(
        queryset=Transaction.objects.none(),
        widget=CustomCheckboxSelectMultiple(
            input_attrs={
                "class": "w-4 h-4 text-blue-600 rounded-sm focus:ring-blue-600 ring-offset-gray-800 focus:ring-2 bg-gray-400 border-gray-500"
            }
        ),
        required=True,
    )

    class Meta:
        model: Revenue
        fields = [
            "transactions",
        ]

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        self.revenue = kwargs.pop("revenue", None)
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["transactions"].queryset = (
                Transaction.objects.filter(
                    Q(bank_account=self.contract.checking_account)
                    | Q(bank_account=self.contract.investing_account)
                )
                .filter(
                    expenses=None,
                    revenues=None,
                    amount__gte=0,
                )
                .order_by("date")
            )

    def clean_transactions(self):
        transactions = self.cleaned_data.get("transactions")

        if not transactions:
            raise forms.ValidationError("Informe as transações correspondentes")

        amount = sum([transaction.amount for transaction in transactions])
        if amount != self.revenue.value:
            raise forms.ValidationError(
                "Soma das transações diferente do valor da receita."
            )

        return transactions


class AccountabilityFileForm(forms.ModelForm):
    class Meta:
        model = AccountabilityFile
        fields = [
            "name",
            "file",
        ]

        widgets = {
            "name": BaseCharFieldFormWidget(placeholder="Arquivo xxxxx"),
            "file": BaseFileFormWidget(),
        }


# =============================================================================
# AUDESP Fase V - AnnualStatement (the (contract, fiscal_year) anchor) and its
# blocks. See accountability/models.py for the full field-by-field docstrings.
# =============================================================================


class AnnualStatementCreateForm(forms.ModelForm):
    class Meta:
        model = AnnualStatement
        fields = ["fiscal_year"]

        widgets = {
            "fiscal_year": BaseNumberFormWidget(placeholder="2025"),
        }


class AnnualStatementUpdateForm(forms.ModelForm):
    class Meta:
        model = AnnualStatement
        fields = [
            "statement_date",
            "reference_period_start_date",
            "reference_period_end_date",
        ]

        widgets = {
            "statement_date": BaseDateFormWidget(required=False),
            "reference_period_start_date": BaseDateFormWidget(required=False),
            "reference_period_end_date": BaseDateFormWidget(required=False),
        }


class BudgetCommitmentForm(forms.ModelForm):
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = BudgetCommitment
        fields = [
            "number",
            "issue_date",
            "economic_classification",
            "funding_source_type",
            "value",
            "description",
            "spending_authority_cpf",
        ]

        widgets = {
            "number": BaseCharFieldFormWidget(),
            "issue_date": BaseDateFormWidget(),
            "economic_classification": BaseCharFieldFormWidget(),
            "funding_source_type": BaseSelectFormWidget(),
            "description": BaseTextAreaFormWidget(),
            "spending_authority_cpf": CustomCPFWidget(),
        }


class FundTransferForm(forms.ModelForm):
    planned_value = DecimalMaskedField(max_digits=12, decimal_places=2)
    transferred_value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = FundTransfer
        fields = [
            "budget_commitment",
            "planned_date",
            "transfer_date",
            "planned_value",
            "transferred_value",
            "value_difference_justification",
            "bank_document_type",
            "other_description",
            "document_number",
            "bank",
            "bank_branch",
            "account_number",
        ]

        widgets = {
            "budget_commitment": BaseSelectFormWidget(),
            "planned_date": BaseDateFormWidget(),
            "transfer_date": BaseDateFormWidget(),
            "value_difference_justification": BaseTextAreaFormWidget(required=False),
            "bank_document_type": BaseSelectFormWidget(),
            "other_description": BaseCharFieldFormWidget(required=False),
            "document_number": BaseCharFieldFormWidget(),
            "bank": BaseNumberFormWidget(placeholder="Código do banco (tabela BACEN)"),
            "bank_branch": BaseCharFieldFormWidget(),
            "account_number": BaseCharFieldFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["budget_commitment"].queryset = BudgetCommitment.objects.filter(
                contract=self.contract
            )
        else:
            self.fields["budget_commitment"].queryset = BudgetCommitment.objects.none()


class ExpenseRejectionForm(forms.ModelForm):
    rejected_value = DecimalMaskedField(max_digits=12, decimal_places=2, required=False)

    class Meta:
        model = ExpenseRejection
        fields = [
            "expense",
            "payment_date",
            "analysis_result",
            "rejected_value",
        ]

        widgets = {
            "expense": BaseSelectFormWidget(required=False),
            "payment_date": BaseDateFormWidget(required=False),
            "analysis_result": BaseSelectFormWidget(),
        }

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["expense"].queryset = Expense.objects.filter(
                accountability__contract=self.contract
            )
        else:
            self.fields["expense"].queryset = Expense.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("expense") and not cleaned_data.get("payment_date"):
            raise forms.ValidationError(
                "Informe a despesa (documento fiscal) ou a data de pagamento da "
                "Folha Ordinária."
            )
        return cleaned_data


class DeductionForm(forms.ModelForm):
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = Deduction
        fields = ["date", "description", "value"]

        widgets = {
            "date": BaseDateFormWidget(),
            "description": BaseCharFieldFormWidget(),
        }


class RefundForm(forms.ModelForm):
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = Refund
        fields = ["date", "nature", "value"]

        widgets = {
            "date": BaseDateFormWidget(),
            "nature": BaseSelectFormWidget(),
        }


class BalanceAdjustmentForm(forms.ModelForm):
    value = DecimalMaskedField(max_digits=12, decimal_places=2)

    class Meta:
        model = BalanceAdjustment
        fields = [
            "type",
            "planned_date",
            "date",
            "funding_source_type",
            "value",
            "expense",
            "payment_method_type",
            "bank",
            "bank_branch",
            "account_number",
            "transaction_number",
        ]

        widgets = {
            "type": BaseSelectFormWidget(),
            "planned_date": BaseDateFormWidget(required=False),
            "date": BaseDateFormWidget(),
            "funding_source_type": BaseSelectFormWidget(),
            "expense": BaseSelectFormWidget(required=False),
            "payment_method_type": BaseSelectFormWidget(required=False),
            "bank": BaseNumberFormWidget(required=False),
            "bank_branch": BaseCharFieldFormWidget(required=False),
            "account_number": BaseCharFieldFormWidget(required=False),
            "transaction_number": BaseCharFieldFormWidget(required=False),
        }

    def __init__(self, *args, **kwargs):
        self.contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)

        if self.contract:
            self.fields["expense"].queryset = Expense.objects.filter(
                accountability__contract=self.contract
            )
        else:
            self.fields["expense"].queryset = Expense.objects.none()


# --- §22 Regulamento de Compras (Contrato de Gestão only) -------------------


class PurchasingRegulationForm(forms.ModelForm):
    class Meta:
        model = PurchasingRegulation
        fields = [
            "had_initial_publication",
            "was_regulation_amended",
            "had_amended_regulation_publication",
        ]


class PurchasingRegulationPublicationForm(forms.ModelForm):
    class Meta:
        model = PurchasingRegulationPublication
        fields = [
            "phase",
            "publication_vehicle_type",
            "vehicle_name",
            "publication_date",
            "website_url",
        ]

        widgets = {
            "phase": BaseSelectFormWidget(),
            "publication_vehicle_type": BaseSelectFormWidget(),
            "vehicle_name": BaseCharFieldFormWidget(required=False),
            "publication_date": BaseDateFormWidget(),
            "website_url": BaseCharFieldFormWidget(required=False),
        }


PurchasingRegulationPublicationFormSet = forms.inlineformset_factory(
    PurchasingRegulation,
    PurchasingRegulationPublication,
    fk_name="regulation",
    form=PurchasingRegulationPublicationForm,
    extra=1,
    can_delete=True,
)


# --- §23 Extrato de Execução Física e Financeira (Termo de Parceria only) ---


class PhysicalFinancialExecutionStatementForm(forms.ModelForm):
    class Meta:
        model = PhysicalFinancialExecutionStatement
        fields = ["has_statement", "statement_follows_template"]


class PhysicalFinancialExecutionStatementPublicationForm(forms.ModelForm):
    class Meta:
        model = PhysicalFinancialExecutionStatementPublication
        fields = [
            "publication_vehicle_type",
            "vehicle_name",
            "publication_date",
            "website_url",
        ]

        widgets = {
            "publication_vehicle_type": BaseSelectFormWidget(),
            "vehicle_name": BaseCharFieldFormWidget(required=False),
            "publication_date": BaseDateFormWidget(),
            "website_url": BaseCharFieldFormWidget(required=False),
        }


PhysicalFinancialExecutionStatementPublicationFormSet = forms.inlineformset_factory(
    PhysicalFinancialExecutionStatement,
    PhysicalFinancialExecutionStatementPublication,
    fk_name="statement",
    form=PhysicalFinancialExecutionStatementPublicationForm,
    extra=1,
    can_delete=True,
)


# --- §28 Demonstrações Contábeis (todos os tipos de ajuste) -----------------


class FinancialStatementsForm(forms.ModelForm):
    class Meta:
        model = FinancialStatements
        fields = [
            "accountant_crc_number",
            "accountant_cpf",
            "accountant_crc_in_good_standing",
        ]

        widgets = {
            "accountant_crc_number": BaseCharFieldFormWidget(required=False),
            "accountant_cpf": CustomCPFWidget(),
        }


class FinancialStatementsPublicationForm(forms.ModelForm):
    class Meta:
        model = FinancialStatementsPublication
        fields = [
            "publication_vehicle_type",
            "vehicle_name",
            "publication_date",
            "website_url",
        ]

        widgets = {
            "publication_vehicle_type": BaseSelectFormWidget(),
            "vehicle_name": BaseCharFieldFormWidget(required=False),
            "publication_date": BaseDateFormWidget(),
            "website_url": BaseCharFieldFormWidget(required=False),
        }


FinancialStatementsPublicationFormSet = forms.inlineformset_factory(
    FinancialStatements,
    FinancialStatementsPublication,
    fk_name="financial_statement",
    form=FinancialStatementsPublicationForm,
    extra=1,
    can_delete=True,
)


# --- §30 Publicação do Relatório de Atividades (Contrato de Gestão only) ----


class ActivityReportPublicationStatusForm(forms.ModelForm):
    class Meta:
        model = ActivityReportPublicationStatus
        fields = ["was_published_in_fiscal_year"]


class ActivityReportPublicationForm(forms.ModelForm):
    class Meta:
        model = ActivityReportPublication
        fields = [
            "publication_vehicle_type",
            "vehicle_name",
            "publication_date",
            "website_url",
        ]

        widgets = {
            "publication_vehicle_type": BaseSelectFormWidget(),
            "vehicle_name": BaseCharFieldFormWidget(required=False),
            "publication_date": BaseDateFormWidget(),
            "website_url": BaseCharFieldFormWidget(required=False),
        }


ActivityReportPublicationFormSet = forms.inlineformset_factory(
    ActivityReportPublicationStatus,
    ActivityReportPublication,
    fk_name="publication_status",
    form=ActivityReportPublicationForm,
    extra=1,
    can_delete=True,
)


# --- §29 Parecer ou Ata (combinação varia por tipo de ajuste) ---------------


class OpinionOrMinutesForm(forms.ModelForm):
    class Meta:
        model = OpinionOrMinutes
        fields = ["type", "was_published", "conclusion"]

        widgets = {
            "type": BaseSelectFormWidget(),
            "conclusion": BaseSelectFormWidget(required=False),
        }


class OpinionOrMinutesPublicationForm(forms.ModelForm):
    class Meta:
        model = OpinionOrMinutesPublication
        fields = [
            "publication_vehicle_type",
            "vehicle_name",
            "publication_date",
            "website_url",
        ]

        widgets = {
            "publication_vehicle_type": BaseSelectFormWidget(),
            "vehicle_name": BaseCharFieldFormWidget(required=False),
            "publication_date": BaseDateFormWidget(),
            "website_url": BaseCharFieldFormWidget(required=False),
        }


OpinionOrMinutesPublicationFormSet = forms.inlineformset_factory(
    OpinionOrMinutes,
    OpinionOrMinutesPublication,
    fk_name="opinion_or_minutes",
    form=OpinionOrMinutesPublicationForm,
    extra=1,
    can_delete=True,
)


# --- §25/26/27 Relatório de Avaliação/Governamental/Monitoramento -----------


class EvaluationReportForm(forms.ModelForm):
    class Meta:
        model = EvaluationReport
        fields = ["type", "final_report_issued", "conclusion", "justification"]

        widgets = {
            "type": BaseSelectFormWidget(),
            "conclusion": BaseSelectFormWidget(required=False),
            "justification": BaseTextAreaFormWidget(required=False),
        }


# --- §24 Declarações (conflito de interesse) --------------------------------


class ConflictOfInterestDeclarationForm(forms.ModelForm):
    class Meta:
        model = ConflictOfInterestDeclaration
        fields = [
            "hired_related_companies",
            "had_political_agents_in_board",
            "purchases_comply_with_own_regulation",
        ]


class RelatedCompanyForm(forms.ModelForm):
    class Meta:
        model = RelatedCompany
        fields = ["cnpj", "cpf"]

        widgets = {
            "cnpj": BaseCharFieldFormWidget(placeholder="00.000.000/0000-00"),
            "cpf": CustomCPFWidget(),
        }


RelatedCompanyFormSet = forms.inlineformset_factory(
    ConflictOfInterestDeclaration,
    RelatedCompany,
    fk_name="declaration",
    form=RelatedCompanyForm,
    extra=1,
    can_delete=True,
)


class BoardParticipationForm(forms.ModelForm):
    class Meta:
        model = BoardParticipation
        fields = ["officer_cpf", "hired_cpfs"]

        widgets = {
            "officer_cpf": CustomCPFWidget(),
            "hired_cpfs": BaseTextAreaFormWidget(required=False, rows=2),
        }
        help_texts = {
            "hired_cpfs": (
                'Lista de CPFs em formato JSON, ex.: ["12345678900", "98765432100"]'
            ),
        }


BoardParticipationFormSet = forms.inlineformset_factory(
    ConflictOfInterestDeclaration,
    BoardParticipation,
    fk_name="declaration",
    form=BoardParticipationForm,
    extra=1,
    can_delete=True,
)


# --- §33 Parecer Conclusivo --------------------------------------------------


class ConclusiveOpinionForm(forms.ModelForm):
    class Meta:
        model = ConclusiveOpinion
        fields = ["opinion_identification", "conclusion", "remarks"]

        widgets = {
            "opinion_identification": BaseCharFieldFormWidget(required=False),
            "conclusion": BaseSelectFormWidget(),
            "remarks": BaseTextAreaFormWidget(required=False),
        }


class ConclusiveOpinionDeclarationForm(forms.ModelForm):
    class Meta:
        model = ConclusiveOpinionDeclaration
        fields = ["answer", "justification"]

        widgets = {
            "answer": BaseSelectFormWidget(),
            "justification": BaseTextAreaFormWidget(required=False, rows=2),
        }


ConclusiveOpinionDeclarationFormSet = forms.modelformset_factory(
    ConclusiveOpinionDeclaration,
    form=ConclusiveOpinionDeclarationForm,
    extra=0,
    can_delete=False,
)
