from django import forms

from utils.widgets import BaseSelectFormWidget, BaseNumberFormWidget
from utils.choices import MonthChoices
from contracts.models import Contract


REPORTS_OPTIONS = [
    ("rp_1", "Anexo RP 1"),
    ("rp_2", "Anexo RP 2"),
    ("rp_3", "Anexo RP 3"),
    ("rp_4", "Anexo RP 4"),
    ("rp_5", "Anexo RP 5"),
    ("rp_6", "Anexo RP 6"),
    ("rp_7", "Anexo RP 7"),
    ("rp_8", "Anexo RP 8"),
    ("rp_9", "Anexo RP 9"),
    ("rp_10", "Anexo RP 10"),
    ("rp_11", "Anexo RP 11"),
    ("rp_12", "Anexo RP 12"),
    ("rp_13", "Anexo RP 13"),
    ("rp_14", "Anexo RP 14"),
]


class ReportForm(forms.Form):
    report_model = forms.ChoiceField(
        choices=REPORTS_OPTIONS,
        label="Escolha um modelo de relatório",
        widget=BaseSelectFormWidget(),
    )
    month = forms.ChoiceField(
        choices=MonthChoices.choices,
        label="Escolha um modelo de relatório",
        widget=BaseSelectFormWidget(),
    )
    year = forms.IntegerField(
        label="Ano",
        widget=BaseNumberFormWidget(),
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

        self.fields["contract"].queryset = self.request.user.organization.contracts.all()
