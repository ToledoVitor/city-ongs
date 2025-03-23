import calendar
from datetime import datetime

from django import forms

from contracts.models import Contract
from utils.widgets import BaseSelectFormWidget

REPORTS_OPTIONS = [
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
    ("period_expenses", "Despesas: Realizadas no Período"),
    (
        "predicted_versus_realized",
        "Demonstrativo de Repasses: Previsto versus Realizado",
    ),
    (
        "consolidated",
        "Consolidado das Conciliações Bancárias",
    ),
]


class ReportForm(forms.Form):
    MONTH_CHOICES = [
        (1, "Janeiro"),
        (2, "Fevereiro"),
        (3, "Março"),
        (4, "Abril"),
        (5, "Maio"),
        (6, "Junho"),
        (7, "Julho"),
        (8, "Agosto"),
        (9, "Setembro"),
        (10, "Outubro"),
        (11, "Novembro"),
        (12, "Dezembro"),
    ]
    YEAR_CHOICES = [
        (year, year) for year in range(2020, datetime.now().year + 1)
    ]

    start_month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=True,
        label="Mês Inicial",
        widget=BaseSelectFormWidget(),
    )
    start_year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        required=True,
        label="Ano Inicial",
        widget=BaseSelectFormWidget(),
    )
    end_month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=True,
        label="Mês Final",
        widget=BaseSelectFormWidget(),
    )
    end_year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        required=True,
        label="Ano Final",
        widget=BaseSelectFormWidget(),
    )

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

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        self.fields["contract"].queryset = Contract.objects.filter(
            area__in=self.request.user.areas.all()
        ).order_by("code")

    def clean(self):
        cleaned_data = super().clean()
        try:
            start_month = int(cleaned_data.get("start_month"))
            start_year = int(cleaned_data.get("start_year"))
            end_month = int(cleaned_data.get("end_month"))
            end_year = int(cleaned_data.get("end_year"))
        except (TypeError, ValueError):
            raise forms.ValidationError("Valores inválidos para mês ou ano.")

        start_date = datetime(start_year, start_month, 1)

        last_day = calendar.monthrange(end_year, end_month)[1]
        end_date = datetime(end_year, end_month, last_day)

        if start_date > end_date:
            raise forms.ValidationError(
                "A data de início deve ser anterior à data de término."
            )

        cleaned_data["start_date"] = start_date
        cleaned_data["end_date"] = end_date

        return cleaned_data
