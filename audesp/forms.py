"""Forms for the Fase IV trigger UI (contract-detail tab + the dedicated
Ajuste creation page). See AUDESP_FASE_IV_AUDIT.md §4 for why
`codigo_edital`/`itens` are required, explicit user inputs rather than
fields derived from the contract: both reference a Licitação/Dispensa
record registered elsewhere (typically TCE-SP's own Portal AUDESP), which
this codebase deliberately does not manage.
"""

from django import forms

from accountability.models import BudgetCommitment
from utils.widgets import BaseCharFieldFormWidget, BaseSelectFormWidget


class AudespFaseIVAjusteForm(forms.Form):
    codigo_edital = forms.CharField(
        label="Código do edital/dispensa",
        max_length=25,
        widget=BaseCharFieldFormWidget(placeholder="Ex.: 123/2026"),
        help_text=(
            "Código do processo de licitação/dispensa já registrado no "
            "Portal AUDESP — consulte o setor de licitações se não souber."
        ),
    )
    itens = forms.CharField(
        label="Itens contratados",
        widget=BaseCharFieldFormWidget(placeholder="Ex.: 1, 2, 4"),
        help_text=(
            "Números dos itens do edital/dispensa efetivamente contratados, "
            "separados por vírgula."
        ),
    )
    retificacao = forms.BooleanField(
        label="Esta é uma retificação de um envio anterior",
        required=False,
    )

    def clean_itens(self):
        raw = self.cleaned_data["itens"]
        itens = []
        for chunk in raw.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue
            try:
                item = int(chunk)
            except ValueError:
                raise forms.ValidationError(
                    f"“{chunk}” não é um número de item válido."
                )
            if item < 0:
                raise forms.ValidationError(
                    f"“{chunk}” não é um número de item válido."
                )
            itens.append(item)
        if not itens:
            raise forms.ValidationError(
                "Informe ao menos um item, separado por vírgula."
            )
        return itens


class AudespFaseIVEmpenhoForm(forms.Form):
    budget_commitment = forms.ModelChoiceField(
        queryset=BudgetCommitment.objects.none(),
        label="Empenho",
        empty_label="Selecione um empenho",
        widget=BaseSelectFormWidget(),
    )

    def __init__(self, *args, contract=None, **kwargs):
        super().__init__(*args, **kwargs)
        if contract is not None:
            self.fields[
                "budget_commitment"
            ].queryset = contract.budget_commitments.filter(
                deleted_at__isnull=True
            ).order_by("-issue_date")
