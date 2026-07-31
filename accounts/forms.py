from django import forms

from accounts.models import Area, OrganizationDocument, User
from audesp.forms import AudespCredentialAdminForm
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


class OrganizationDocumentForm(forms.ModelForm):
    class Meta:
        model = OrganizationDocument
        fields = ["document_type", "title", "description", "file", "is_public"]

        base_input_class = (
            "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg "
            "focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5"
        )

        widgets = {
            "document_type": forms.Select(attrs={"class": base_input_class}),
            "title": forms.TextInput(
                attrs={
                    "class": base_input_class,
                    "placeholder": "Digite o título do documento",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": base_input_class,
                    "rows": "4",
                    "placeholder": "Digite a descrição do documento",
                }
            ),
            "file": forms.FileInput(
                attrs={
                    "class": (
                        "block w-full text-sm text-gray-900 border border-gray-300 "
                        "rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
                    )
                }
            ),
            "is_public": forms.CheckboxInput(
                attrs={
                    "class": (
                        "w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded "
                        "focus:ring-blue-500 focus:ring-2"
                    )
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        super().__init__(*args, **kwargs)
        if organization:
            self.instance.organization = organization


class AudespCredentialSettingsForm(AudespCredentialAdminForm):
    """City-hall-scoped variant of `AudespCredentialAdminForm` for the
    settings page (`accounts:audesp-credentials-form`), reusing its exact
    username/password/DEVELOPMENT validation as-is.

    `city_hall` and `environment` are deliberately dropped from the visible
    fields: the view sets both on the (fetched-or-new) instance before the
    form ever binds, from the URL's `environment` and the current user's
    `request.user.organization.city_hall` — never from user input, so
    nobody can pick another city hall's row through this page.
    """

    class Meta(AudespCredentialAdminForm.Meta):
        fields = ("is_active",)
