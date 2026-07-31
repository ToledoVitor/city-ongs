"""Form for the Fase V trigger UI (audesp/views.py) — pick a fiscal year and
an ajuste type, then build+validate a payload via audesp.services.
Declaração Negativa is deliberately excluded from the choices: services.py
doesn't orchestrate it yet (see its module docstring).
"""

from django import forms
from django.utils import timezone

from audesp.models import AudespSubmission
from contracts.models import Contract

#: Only the 5 ajuste types services.build_and_validate actually knows how to
#: build — DECLARACAO_NEGATIVA is excluded on purpose (see module docstring).
REAL_AJUSTE_TYPE_CHOICES = [
    (choice.value, choice.label)
    for choice in AudespSubmission.AjusteTypeChoices
    if choice != AudespSubmission.AjusteTypeChoices.DECLARACAO_NEGATIVA
]

#: Best-effort *default suggestion* only, never an auto-decision — per
#: DEBTS.md ("Contract.ConcessionChoices doesn't map 1:1 onto AUDESP's 5
#: ajuste types"), GRANT ("Concessão") has no corresponding Fase V ajuste
#: type at all, so it's left out rather than guessed at, and DEVELOPMENTO's
#: label ("Contrato de Fomento") doesn't match AUDESP's own term for the
#: same instrument ("Termo de Fomento") even though the mapping itself
#: holds. The form field this seeds is always an explicit, user-editable
#: choice — this dict only pre-selects a starting value.
CONCESSION_TYPE_AJUSTE_TYPE_HINTS = {
    Contract.ConcessionChoices.MANAGEMENT: AudespSubmission.AjusteTypeChoices.CONTRATO_GESTAO,
    Contract.ConcessionChoices.PARTNERSHIP: AudespSubmission.AjusteTypeChoices.TERMO_PARCERIA,
    Contract.ConcessionChoices.COLLABORATION: AudespSubmission.AjusteTypeChoices.TERMO_COLABORACAO,
    Contract.ConcessionChoices.DEVELOPMENTO: AudespSubmission.AjusteTypeChoices.TERMO_FOMENTO,
    Contract.ConcessionChoices.AGREEMENT: AudespSubmission.AjusteTypeChoices.CONVENIO,
}


class AudespFaseVBuildForm(forms.Form):
    fiscal_year = forms.IntegerField(
        label="Exercício",
        min_value=2000,
        max_value=2100,
        initial=timezone.now().year,
        widget=forms.NumberInput(attrs={"class": "filter-field__control"}),
    )
    ajuste_type = forms.ChoiceField(
        label="Tipo de ajuste (AUDESP)",
        choices=REAL_AJUSTE_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "filter-field__control"}),
    )
