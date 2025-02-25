from django import forms


class BaseCharFieldFormWidget(forms.TextInput):
    def __init__(
        self, *args, placeholder=None, is_password=False, required=True, **kwargs
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
