from django import forms
from phonenumber_field.formfields import PhoneNumberField

# Control classes are defined in `templates/ui/_styles.html`. Emit those instead
# of Tailwind utilities: the `.ui-*` rules are element-scoped
# (`input.ui-input`, `select.ui-input`, …), so they carry the ink/canvas palette
# from DESIGN.md with or without a surrounding `.ui-form` wrapper.
#
# Selects and textareas carry `ui-select`/`ui-textarea` on top of `ui-input`.
# The generic `.ui-form` fallbacks are written as `select:not(.ui-select)` /
# `textarea:not(.ui-textarea)` — specificity (0,2,1), which outranks
# `select.ui-input` (0,1,1). Without the extra token those fallbacks would keep
# winning inside a `.ui-form`. It also restores `resize: vertical`, which
# `ui-input` alone does not set on a textarea.
INPUT_CLASS = "ui-input"
SELECT_CLASS = "ui-input ui-select"
TEXTAREA_CLASS = "ui-input ui-textarea"


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
                "class": INPUT_CLASS,
                "required": required,
            }
        )
        if is_password:
            kwargs["attrs"]["type"] = "password"

        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class BaseDateFormWidget(forms.DateInput):
    def __init__(self, *args, placeholder="dd/mm/aaaa", required=True, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": INPUT_CLASS,
                "required": required,
                "placeholder": placeholder,
                "datepicker": "",
                "datepicker-autohide": "",
                "datepicker-format": "dd/mm/yyyy",
                "datepicker-language": "pt",
            }
        )
        super().__init__(*args, **kwargs)


class BaseNumberFormWidget(forms.NumberInput):
    def __init__(self, *args, placeholder=None, required=True, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": INPUT_CLASS,
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
                "class": TEXTAREA_CLASS,
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
                "class": SELECT_CLASS,
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
                "class": INPUT_CLASS,
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
                "class": INPUT_CLASS,
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
                    "class": INPUT_CLASS,
                    "placeholder": "(00) 00000-0000",
                    "data-mask": "(00) 00000-0000",
                    "type": "tel",
                    "inputmode": "numeric",
                }
            ),
        )
        super().__init__(*args, **kwargs)


class CustomCPFWidget(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "attrs",
            {
                "class": INPUT_CLASS,
                "placeholder": "000.000.000-00",
                "data-mask": "000.000.000-00",
                "type": "text",
                "inputmode": "numeric",
            },
        )
        super().__init__(*args, **kwargs)


class CustomCNPJWidget(forms.TextInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "attrs",
            {
                "class": INPUT_CLASS,
                "placeholder": "00.000.000/0000-00",
                "data-mask": "00.000.000/0000-00",
                "type": "text",
                "inputmode": "numeric",
            },
        )
        super().__init__(*args, **kwargs)
