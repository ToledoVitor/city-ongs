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
    def to_python(self, value):
        if isinstance(value, str):
            value = re.sub(r"\.", "", value).replace(",", ".")
        return super().to_python(value)
