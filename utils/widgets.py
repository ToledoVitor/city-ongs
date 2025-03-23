from django import forms
from phonenumber_field.formfields import PhoneNumberField


class BaseCharFieldFormWidget(forms.TextInput):
    def __init__(
        self,
        *args,
        placeholder=None,
        is_password=False,
        required=True,
        **kwargs,
    ):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "w-full",
                        "p-2.5",
                        "block",
                        "text-sm",
                        "border",
                        "rounded-lg",
                        "placeholder-gray-600",
                        "bg-gray-300",
                        "border-gray-600",
                        "text-black",
                        "focus:ring-blue-500",
                        "focus:border-blue-500",
                    ]
                ),
                "required": required,
            }
        )
        if is_password:
            kwargs["attrs"]["type"] = "password"

        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class BaseNumberFormWidget(forms.NumberInput):
    def __init__(self, *args, placeholder=None, required=True, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "w-full",
                        "p-2.5",
                        "block",
                        "text-sm",
                        "border",
                        "rounded-lg",
                        "placeholder-gray-600",
                        "bg-gray-300",
                        "border-gray-600",
                        "text-black",
                        "focus:ring-blue-500",
                        "focus:border-blue-500",
                    ]
                ),
                "required": required,
            }
        )
        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class BaseTextAreaFormWidget(forms.Textarea):
    def __init__(self, *args, placeholder=None, required=True, rows=3, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "w-full",
                        "p-2.5",
                        "block",
                        "text-sm",
                        "border",
                        "rounded-lg",
                        "border",
                        "bg-gray-300",
                        "border-gray-600",
                        "placeholder-gray-600",
                        "text-black",
                        "focus:ring-blue-500",
                        "focus:border-blue-500",
                    ]
                ),
                "rows": rows,
                "required": required,
            }
        )
        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class BaseSelectFormWidget(forms.Select):
    def __init__(self, *args, placeholder=None, required=True, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "w-full",
                        "p-2.5",
                        "block",
                        "text-sm",
                        "border",
                        "rounded-lg",
                        "placeholder-gray-600",
                        "bg-gray-300",
                        "border-gray-600",
                        "text-black",
                        "focus:ring-blue-500",
                        "focus:border-blue-500",
                    ]
                ),
                "required": required,
            }
        )
        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class BaseEmailFormWidget(forms.EmailInput):
    def __init__(self, *args, placeholder=None, required=True, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "border",
                        "text-sm",
                        "rounded-lg",
                        "block",
                        "w-full",
                        "p-2.5",
                        "bg-gray-300",
                        "border-gray-600",
                        "placeholder-gray-600",
                        "text-black",
                        "focus:ring-blue-500",
                        "focus:border-blue-500",
                    ]
                ),
                "required": required,
            }
        )
        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class BaseFileFormWidget(forms.FileInput):
    def __init__(self, *args, required=True, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "block w-full text-sm text-gray-900 border border-gray-600",
                        "rounded-lg cursor-pointer bg-gray-300 focus:outline-none",
                    ]
                ),
                "required": required,
            }
        )
        super().__init__(*args, **kwargs)


class CustomCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def __init__(self, *args, **kwargs):
        self.input_attrs = kwargs.pop("input_attrs", {})
        super().__init__(*args, **kwargs)

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        option["attrs"].update(self.input_attrs)
        return option


class CustomPhoneNumberField(PhoneNumberField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("region", "BR")
        kwargs.setdefault(
            "widget",
            forms.TextInput(
                attrs={
                    "class": " ".join(
                        [
                            "w-full",
                            "p-2.5",
                            "block",
                            "text-sm",
                            "border",
                            "rounded-lg",
                            "placeholder-gray-600",
                            "bg-gray-300",
                            "border-gray-600",
                            "text-black",
                            "focus:ring-blue-500",
                            "focus:border-blue-500",
                        ]
                    ),
                    "placeholder": "(00) 00000-0000",
                    "data-mask": "(00) 00000-0000",
                }
            ),
        )
        super().__init__(*args, **kwargs)
