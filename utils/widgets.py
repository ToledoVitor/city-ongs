from django import forms
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
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
                "required": required,
            }
        )
        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class ComboboxSelectWidget(forms.Select):
    """Searchable select backed by `ui/combobox.html`.

    Two modes, matching the component:

    * remote (`url_name` given) — `optgroups()` is neutered so **no** option is
      ever serialized into the page. The browser fetches pages of 10 from the
      endpoint instead, which keeps the rendered payload constant no matter how
      large the queryset grows. `ModelChoiceField.to_python()` still validates
      the submitted id against the field's queryset, so access scoping is
      unchanged — only rendering is decoupled.
    * static (no `url_name`) — the field's own choices are embedded as JSON and
      filtered client-side. `descriptions` adds a second line per option and
      `groups` buckets them under headings.

    The widget renders through `render_to_string` rather than Django's form
    renderer because this project keeps templates in a project-level `DIRS`
    entry, which the default `DjangoTemplates` form renderer does not search.
    """

    template_name = "ui/combobox_widget.html"

    def __init__(
        self,
        *args,
        url_name=None,
        placeholder="Selecione",
        search_placeholder="Buscar…",
        empty_text="Nenhum resultado",
        descriptions=None,
        groups=None,
        page_size=10,
        size="sm",
        surface=None,
        **kwargs,
    ):
        self.url_name = url_name
        self.placeholder = placeholder
        self.search_placeholder = search_placeholder
        self.empty_text = empty_text
        self.descriptions = descriptions or {}
        self.groups = groups or {}
        self.page_size = page_size
        self.size = size
        self.surface = surface
        super().__init__(*args, **kwargs)

    @property
    def is_remote(self) -> bool:
        return bool(self.url_name)

    def id_for_label(self, id_):
        # The focusable control is the trigger button, not the wrapper div, so
        # `<label for="{{ field.id_for_label }}">` points at something usable.
        return f"{id_}-trigger" if id_ else id_

    def optgroups(self, name, value, attrs=None):
        # Remote mode never ships the option list; static mode ships it as JSON
        # in `combobox.options` instead of as <option> elements.
        return []

    def _static_options(self) -> list[dict]:
        options = []
        for choice_value, choice_label in self.choices:
            if choice_value in ("", None):
                # The blank choice becomes the trigger placeholder.
                continue
            option = {"id": str(choice_value), "text": str(choice_label)}
            description = self.descriptions.get(choice_value)
            if description:
                option["subtext"] = str(description)
            group = self.groups.get(choice_value)
            if group:
                option["group"] = str(group)
            options.append(option)
        return options

    def _selected_text(self, value) -> str:
        if value in ("", None):
            return ""
        iterator = self.choices
        queryset = getattr(iterator, "queryset", None)
        if queryset is not None:
            # Single targeted lookup — never evaluates the whole queryset.
            obj = queryset.filter(pk=value).first()
            if obj is None:
                return ""
            field = getattr(iterator, "field", None)
            return str(field.label_from_instance(obj) if field else obj)
        for choice_value, choice_label in self.choices:
            if str(choice_value) == str(value):
                return str(choice_label)
        return ""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        raw_value = value[0] if isinstance(value, list | tuple) and value else value
        raw_value = "" if raw_value is None else str(raw_value)

        context["widget"]["combobox"] = {
            "url": reverse(self.url_name) if self.is_remote else "",
            "options": [] if self.is_remote else self._static_options(),
            "value": raw_value,
            "selected_text": self._selected_text(raw_value),
            "placeholder": self.placeholder,
            "search_placeholder": self.search_placeholder,
            "empty_text": self.empty_text,
            "page_size": self.page_size,
            "size": self.size,
            "surface": self.surface,
            # Set by the form template via add_error → attrs; mirrored here so
            # the control can flag aria-invalid without a second lookup.
            "error": bool(attrs and attrs.get("aria-invalid")),
        }
        return context

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        return mark_safe(  # noqa: S308 - template output is already escaped
            render_to_string(self.template_name, context)
        )


class BaseEmailFormWidget(forms.EmailInput):
    def __init__(self, *args, placeholder=None, required=True, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
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
                "placeholder": "00.000.000/0000-00",
                "data-mask": "00.000.000/0000-00",
                "type": "text",
                "inputmode": "numeric",
            },
        )
        super().__init__(*args, **kwargs)
