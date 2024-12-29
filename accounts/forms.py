from django import forms

from accounts.models import User
from utils.regex import password_is_valid
from utils.widgets import BaseCharFieldFormWidget, BaseEmailFormWidget


class FolderManagerCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirme a senha"
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
        ]

        widgets = {
            "email": BaseEmailFormWidget(placeholder=""),
            "first_name": BaseCharFieldFormWidget(placeholder=""),
            "last_name": BaseCharFieldFormWidget(placeholder=""),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if not password_is_valid(password):
            self.add_error("password", "A senha não atende aos critérios.")

        if password != confirm_password:
            self.add_error("confirm_password", "As senhas não coincidem.")

        return cleaned_data


class OngAccountantCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="Confirme a senha"
    )

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
        ]

        widgets = {
            "email": BaseEmailFormWidget(placeholder=""),
            "first_name": BaseCharFieldFormWidget(placeholder=""),
            "last_name": BaseCharFieldFormWidget(placeholder=""),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if not password_is_valid(password):
            self.add_error("password", "A senha não atende aos critérios.")

        if password != confirm_password:
            self.add_error("confirm_password", "As senhas não coincidem.")

        return cleaned_data
