from django import forms

from accounts.models import Area, User
from utils.regex import password_is_valid
from utils.widgets import BaseCharFieldFormWidget, BaseEmailFormWidget


class FolderManagerCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirme a senha"
    )
    areas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "areas",
        ]

        widgets = {
            "email": BaseEmailFormWidget(placeholder=""),
            "first_name": BaseCharFieldFormWidget(placeholder=""),
            "last_name": BaseCharFieldFormWidget(placeholder=""),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields["areas"].queryset = self.request.user.areas.all()

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        areas = cleaned_data.get("areas", [])

        if not password_is_valid(password):
            self.add_error("password", "A senha não atende aos critérios.")

        if password != confirm_password:
            self.add_error("confirm_password", "As senhas não coincidem.")

        if len(areas) < 1:
            self.add_error("areas", "Você deve escolher pelo menos uma área.")

        return cleaned_data


class OrganizationAccountantCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirme a senha"
    )

    areas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "areas",
        ]

        widgets = {
            "email": BaseEmailFormWidget(placeholder=""),
            "first_name": BaseCharFieldFormWidget(placeholder=""),
            "last_name": BaseCharFieldFormWidget(placeholder=""),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields["areas"].queryset = self.request.user.areas.all()

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        areas = cleaned_data.get("areas", [])

        if not password_is_valid(password):
            self.add_error("password", "A senha não atende aos critérios.")

        if password != confirm_password:
            self.add_error("confirm_password", "As senhas não coincidem.")

        if len(areas) < 1:
            self.add_error("areas", "Você deve escolher pelo menos uma área.")

        return cleaned_data
