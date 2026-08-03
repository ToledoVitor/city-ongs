from django import forms

from accounts.models import Area, OrganizationDocument, User
from audesp.forms import AudespCredentialAdminForm
from utils.widgets import (
    INPUT_CLASS,
    SELECT_CLASS,
    TEXTAREA_CLASS,
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

        widgets = {
            "document_type": forms.Select(attrs={"class": SELECT_CLASS}),
            "title": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "Digite o título do documento",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": TEXTAREA_CLASS,
                    "rows": "4",
                    "placeholder": "Digite a descrição do documento",
                }
            ),
            # No class: `.ui-form input[type="file"]` gives file inputs their own
            # 52px dashed affordance, which suits them better than `ui-input`.
            "file": forms.FileInput(),
            # No class: `.ui-form input[type="checkbox"]` sizes it and sets
            # `accent-color`, and a bare checkbox renders natively elsewhere.
            "is_public": forms.CheckboxInput(),
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
