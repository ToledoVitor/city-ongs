from django import forms

from .models import IrregularityReport


class IrregularityReportForm(forms.ModelForm):
    class Meta:
        model = IrregularityReport
        fields = ["description"]
        widgets = {
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": (
                        "Descreva detalhadamente a irregularidade observada..."
                    ),
                }
            )
        }
