from django import forms

from contracts.models import Contract
from utils.choices import MonthChoices
from utils.widgets import BaseNumberFormWidget, BaseSelectFormWidget

RP_OPTIONS = [
    ("rp_1", "Repasses: Terceiro Setor (RP) - 1"),
    ("rp_2", "Repasses: Terceiro Setor (RP) - 2"),
    ("rp_3", "Repasses: Terceiro Setor (RP) - 3"),
    ("rp_4", "Repasses: Terceiro Setor (RP) - 4"),
    ("rp_5", "Repasses: Terceiro Setor (RP) - 5"),
    ("rp_6", "Repasses: Terceiro Setor (RP) - 6"),
    ("rp_7", "Repasses: Terceiro Setor (RP) - 7"),
    ("rp_8", "Repasses: Terceiro Setor (RP) - 8"),
    ("rp_9", "Repasses: Terceiro Setor (RP) - 9"),
    ("rp_10", "Repasses: Terceiro Setor (RP) - 10"),
    ("rp_11", "Repasses: Terceiro Setor (RP) - 11"),
    ("rp_12", "Repasses: Terceiro Setor (RP) - 12"),
    ("rp_13", "Repasses: Terceiro Setor (RP) - 13"),
    ("rp_14", "Repasses: Terceiro Setor (RP) - 14"),
]

TRANSACTION_OPTIONS = [
    ("period_expenses", "Despesas: Realizadas no Período"),
    (
        "predicted_versus_realized",
        "Demonstrativo de Repasses: Previsto versus Reaizado",
    ),
    (
        "consolidated",
        "Consolidado das Conciliações Bancárias",
    ),
]

REPORTS_OPTIONS = [
    *RP_OPTIONS,
    *TRANSACTION_OPTIONS,
]


class ReportForm(forms.Form):
    report_model = forms.ChoiceField(
        choices=REPORTS_OPTIONS,
        label="Escolha um modelo de relatório",
        widget=BaseSelectFormWidget(),
    )
    contract = forms.ModelChoiceField(
        queryset=Contract.objects.none(),
        label="Escolha um contrato",
        empty_label="Selecione um contrato",
        widget=BaseSelectFormWidget(),
    )
    month = forms.ChoiceField(
        choices=MonthChoices.choices,
        label="Escolha um modelo de relatório",
        widget=BaseSelectFormWidget(),
        required=False,
    )
    year = forms.IntegerField(
        label="Ano",
        widget=BaseNumberFormWidget(),
        required=False,
    )
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self.fields[
            "contract"
        ].queryset = self.request.user.organization.contracts.all()

    def clean(self):
        cleaned_data = super().clean()
        report_model = cleaned_data["report_model"]

        if report_model in [opt[0] for opt in RP_OPTIONS]:
            month = cleaned_data["month"]
            year = cleaned_data["year"]

            if not (month and year):
                raise forms.ValidationError(
                    "É necessário informar um mês e ano de competência"
                )

        elif report_model in [opt[0] for opt in TRANSACTION_OPTIONS]:
            start = cleaned_data["start_date"]
            end = cleaned_data["end_date"]

            if not (start and end):
                raise forms.ValidationError(
                    "É necessário informar uma data de início e de término"
                )

        return cleaned_data
