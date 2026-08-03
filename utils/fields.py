import re

from django import forms
from django.db import models


class LowerCaseEmailField(models.EmailField):
    def to_python(self, value):
        value = super().to_python(value)
        if isinstance(value, str):
            return value.lower()
        return value

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if isinstance(value, str):
            return value.lower()
        return value


class DecimalMaskedField(forms.DecimalField):
    # Money fields sit next to `utils.widgets` controls in every form that uses
    # them, so they need the same `ui-input` geometry. Set only the class here —
    # `required` comes from the field, and hardcoding it in attrs would mark the
    # `required=False` call sites as required in the rendered HTML.
    widget = forms.NumberInput(attrs={"class": "ui-input"})

    def to_python(self, value):
        if isinstance(value, str):
            value = re.sub(r"\.", "", value).replace(",", ".")
        return super().to_python(value)
