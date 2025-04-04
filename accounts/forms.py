from django import forms

from accounts.models import Area, User
from utils.widgets import (
    BaseCharFieldFormWidget,
    BaseEmailFormWidget,
    CustomCNPJWidget,
    CustomCPFWidget,
    CustomPhoneNumberField,
)


def email_exists(email: str) -> bool:
    return User.objects.filter(email=email).exists()


class FolderManagerCreateForm(forms.ModelForm):
    areas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )
    phone_number = CustomPhoneNumberField()

    class Meta:
        model = User
        fields = [
            "email",
            "cpf",
            "cnpj",
            "phone_number",
            "first_name",
            "last_name",
            "position",
            "areas",
        ]

        widgets = {
            "email": BaseEmailFormWidget(placeholder=""),
            "cpf": CustomCPFWidget(),
            "cnpj": CustomCNPJWidget(),
            "first_name": BaseCharFieldFormWidget(placeholder=""),
            "last_name": BaseCharFieldFormWidget(placeholder=""),
            "position": BaseCharFieldFormWidget(placeholder=""),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields["areas"].queryset = self.request.user.areas.all()

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        areas = cleaned_data.get("areas", [])

        if email_exists(email):
            self.add_error("email", "Já existe uma conta cadastrada com esse email.")

        if len(areas) < 1:
            self.add_error("areas", "Você deve escolher pelo menos uma pasta gestora.")

        return cleaned_data


class OrganizationAccountantCreateForm(forms.ModelForm):
    areas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )
    phone_number = CustomPhoneNumberField()

    class Meta:
        model = User
        fields = [
            "email",
            "cpf",
            "cnpj",
            "phone_number",
            "first_name",
            "last_name",
            "position",
            "areas",
        ]

        widgets = {
            "email": BaseEmailFormWidget(placeholder=""),
            "cpf": CustomCPFWidget(),
            "cnpj": CustomCNPJWidget(),
            "first_name": BaseCharFieldFormWidget(placeholder=""),
            "last_name": BaseCharFieldFormWidget(placeholder=""),
            "position": BaseCharFieldFormWidget(placeholder=""),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if self.request:
            self.fields["areas"].queryset = self.request.user.areas.all()

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        areas = cleaned_data.get("areas", [])

        if email_exists(email):
            self.add_error("email", "Já existe uma conta cadastrada com esse email.")

        if len(areas) < 1:
            self.add_error("areas", "Você deve escolher pelo menos uma pasta gestora.")

        return cleaned_data


class OrganizationCommitteeCreateForm(forms.ModelForm):
    areas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )
    phone_number = CustomPhoneNumberField()

    class Meta:
        model = User
        fields = [
            "email",
            "cpf",
            "cnpj",
            "phone_number",
            "first_name",
            "last_name",
            "areas",
        ]

        widgets = {
            "email": BaseEmailFormWidget(placeholder=""),
            "cpf": CustomCPFWidget(),
            "cnpj": CustomCNPJWidget(),
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
        email = cleaned_data.get("email")
        areas = cleaned_data.get("areas", [])

        if email_exists(email):
            self.add_error("email", "Já existe uma conta cadastrada com esse email.")

        if len(areas) < 1:
            self.add_error("areas", "Você deve escolher pelo menos uma pasta gestora.")

        return cleaned_data


class AreasForm(forms.Form):
    areas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields["areas"].queryset = user.areas.all()
