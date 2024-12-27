from django import forms


class BaseCharFieldFormWidget(forms.TextInput):
    def __init__(self, *args, placeholder=None, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "w-full p-2.5 block text-sm border border-gray-300 text-gray-900",
                        "bg-gray-50 rounded-lg focus:ring-blue-500 focus:border-blue-500",
                        "dark:placeholder-gray-600 dark:bg-gray-300 dark:border-gray-600",
                        "dark:text-black dark:focus:ring-blue-500 dark:focus:border-blue-500",
                    ]
                ),
            }
        )
        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class BaseTextAreaFormWidget(forms.Textarea):
    def __init__(self, *args, placeholder=None, rows=3, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "w-full p-2.5 block text-sm border bg-gray-50 rounded-lg text-gray-900",
                        "border border-gray-300 focus:ring-blue-500 focus:border-blue-500",
                        "dark:bg-gray-300 dark:border-gray-600 dark:placeholder-gray-600",
                        "dark:text-black dark:focus:ring-blue-500 dark:focus:border-blue-500",
                    ]
                ),
                "rows": rows,
            }
        )
        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


class BaseSelectFormWidget(forms.Select):
    def __init__(self, *args, placeholder=None, **kwargs):
        kwargs.setdefault("attrs", {}).update(
            {
                "class": " ".join(
                    [
                        "bg-gray-50 border border-gray-300 text-black",
                        "text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500",
                        "block w-full p-2.5 dark:bg-gray-300 dark:border-gray-600",
                        "dark:placeholder-gray-800 dark:text-black",
                        "dark:focus:ring-blue-500 dark:focus:border-blue-500",
                    ]
                ),
            }
        )
        if placeholder:
            kwargs["attrs"]["placeholder"] = placeholder

        super().__init__(*args, **kwargs)


# class BaseDecimalFormWidget(forms.DecimalField):
#     def __init__(self, *args, placeholder=None, **kwargs):
#         kwargs.setdefault('attrs', {}).update({
#             "class": " ".join([
#                 "block p-2.5 w-full z-20 ps-10 text-sm text-gray-900 bg-gray-50",
#                 "rounded-s-lg border-e-gray-50 border-e-2 border border-gray-300",
#                 "focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-300",
#                 "dark:border-e-gray-700 dark:border-gray-600 dark:placeholder-gray-800",
#                 "dark:text-black dark:focus:border-blue-500",
#             ]),
#             "step": "0.01",
#         })
#         if placeholder:
#             kwargs['attrs']['placeholder'] = placeholder

#         super().__init__(*args, **kwargs)
