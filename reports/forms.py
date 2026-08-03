import calendar
from datetime import datetime

from django import forms
from django.forms import formset_factory

from accounts.models import User
from contracts.models import Contract, ContractInterestedPart
from utils.mixins import UserAccessFormMixin
from utils.widgets import BaseSelectFormWidget, ComboboxSelectWidget

_GROUP_PUBLIC_BODIES = "Repasses a órgãos públicos"
_GROUP_THIRD_SECTOR = "Repasses ao terceiro setor"
_GROUP_MANAGEMENT = "Demonstrativos gerenciais"

# (value, label, subtitle, group). Labels and subtitles mirror the anexo
# heading each exporter actually prints, so the picker matches the PDF.
REPORT_MODELS = (
    ("rp_1", "RP-01 — Repasses a órgãos públicos", "", _GROUP_PUBLIC_BODIES),
    (
        "rp_2",
        "RP-02 — Demonstrativo integral de receitas e despesas",
        "Repasses a órgãos públicos",
        _GROUP_PUBLIC_BODIES,
    ),
    (
        "rp_3",
        "RP-03 — Termo de ciência e de notificação",
        "Repasses a órgãos públicos",
        _GROUP_PUBLIC_BODIES,
    ),
    ("rp_4", "RP-04 — Repasses ao terceiro setor", "", _GROUP_THIRD_SECTOR),
    (
        "rp_5",
        "RP-05 — Termo de ciência e de notificação",
        "Contrato de gestão",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_6",
        "RP-06 — Demonstrativo integral de receitas e despesas",
        "Contrato de gestão",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_7",
        "RP-07 — Termo de ciência e de notificação",
        "Termo de parceria",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_8",
        "RP-08 — Demonstrativo integral de receitas e despesas",
        "Termo de parceria",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_9",
        "RP-09 — Termo de ciência e de notificação",
        "Termo de colaboração/fomento",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_10",
        "RP-10 — Demonstrativo integral de receitas e despesas",
        "Termo de colaboração/fomento",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_11",
        "RP-11 — Termo de ciência e de notificação",
        "Termo de convênio",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_12",
        "RP-12 — Demonstrativo integral de receitas e despesas",
        "Termo de convênio",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_13",
        "RP-13 — Termo de ciência e de notificação",
        "Auxílios, subvenções e contribuições",
        _GROUP_THIRD_SECTOR,
    ),
    (
        "rp_14",
        "RP-14 — Demonstrativo integral de receitas e despesas",
        "Auxílios, subvenções e contribuições",
        _GROUP_THIRD_SECTOR,
    ),
    ("period_expenses", "Despesas realizadas no período", "", _GROUP_MANAGEMENT),
    (
        "predicted_versus_realized",
        "Repasses previstos versus realizados",
        "",
        _GROUP_MANAGEMENT,
    ),
    (
        "consolidated",
        "Consolidado das conciliações bancárias",
        "",
        _GROUP_MANAGEMENT,
    ),
)

REPORTS_OPTIONS = [(value, label) for value, label, _, _ in REPORT_MODELS]
REPORT_MODEL_LABELS = dict(REPORTS_OPTIONS)
REPORT_MODEL_DESCRIPTIONS = {
    value: subtitle for value, _, subtitle, _ in REPORT_MODELS if subtitle
}
REPORT_MODEL_GROUPS = {value: group for value, _, _, group in REPORT_MODELS}


class ContractChoiceField(forms.ModelChoiceField):
    """Zero-pads the internal code so the label matches ContractOptionsView."""

    def label_from_instance(self, obj):
        return obj.name_with_code


def year_choices():
    """Callable so a long-lived process still offers the current year after a
    new year rolls over. Must stay a plain function — a staticmethod object in
    a field's `choices` breaks `Field.__deepcopy__` (it cannot be pickled).
    """
    return [(year, year) for year in range(2020, datetime.now().year + 1)]


class AdditionalResponsibleForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Responsável",
        widget=ComboboxSelectWidget(
            url_name="accounts:interested-user-options",
            placeholder="Selecione um usuário",
            search_placeholder="Buscar por nome ou e-mail…",
            empty_text="Nenhum usuário encontrado",
        ),
    )
    interest = forms.ChoiceField(
        choices=[],
        required=False,
        label="Responsabilidade",
        widget=BaseSelectFormWidget(required=False),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)

        if self.request:
            interested_part_users = (
                ContractInterestedPart.objects.filter(
                    contract__area__in=self.request.user.areas.all()
                )
                .values_list("user", flat=True)
                .distinct()
            )

            self.fields["user"].queryset = (
                User.objects.filter(id__in=interested_part_users)
                .order_by("first_name", "last_name")
                .distinct()
            )
            self.fields["interest"].choices = [
                ("", "Selecione o tipo de responsabilidade"),
            ] + list(ContractInterestedPart.InterestLevel.choices)


AdditionalResponsibleFormSet = formset_factory(
    AdditionalResponsibleForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
    max_num=6,
)


class AdditionalResponsibleFormSetWrapper(AdditionalResponsibleFormSet):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["request"] = self.request
        kwargs["contract"] = self.contract
        return kwargs


class ReportForm(UserAccessFormMixin, forms.Form):
    MONTH_CHOICES = [
        (1, "Janeiro"),
        (2, "Fevereiro"),
        (3, "Março"),
        (4, "Abril"),
        (5, "Maio"),
        (6, "Junho"),
        (7, "Julho"),
        (8, "Agosto"),
        (9, "Setembro"),
        (10, "Outubro"),
        (11, "Novembro"),
        (12, "Dezembro"),
    ]

    start_month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=True,
        label="Mês inicial",
        widget=BaseSelectFormWidget(),
    )
    start_year = forms.ChoiceField(
        choices=year_choices,
        required=True,
        label="Ano inicial",
        widget=BaseSelectFormWidget(),
    )
    end_month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        required=True,
        label="Mês final",
        widget=BaseSelectFormWidget(),
    )
    end_year = forms.ChoiceField(
        choices=year_choices,
        required=True,
        label="Ano final",
        widget=BaseSelectFormWidget(),
    )

    report_model = forms.ChoiceField(
        # Leading blank choice: without it the field silently defaults to the
        # first model and a user can generate a report they never chose.
        choices=[("", "Selecione um modelo")] + REPORTS_OPTIONS,
        label="Modelo de relatório",
        widget=ComboboxSelectWidget(
            placeholder="Selecione um modelo",
            search_placeholder="Buscar por anexo ou tipo…",
            empty_text="Nenhum modelo encontrado",
            descriptions=REPORT_MODEL_DESCRIPTIONS,
            groups=REPORT_MODEL_GROUPS,
        ),
    )
    contract = ContractChoiceField(
        queryset=Contract.objects.none(),
        label="Contrato",
        widget=ComboboxSelectWidget(
            url_name="contracts:contract-options",
            placeholder="Selecione um contrato",
            search_placeholder="Buscar por nome ou código…",
            empty_text="Nenhum contrato encontrado",
        ),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # `.distinct()` matters: the non-master branch of filter_by_user_access
        # joins interested_parts, which multiplies rows per contract.
        self.fields["contract"].queryset = (
            self.get_user_filtered_contract_queryset(self.request.user)
            .distinct()
            .order_by("-internal_code")
        )

        # Default to the current year to date. The previous defaults were the
        # first choice of each select (January 2020), which produced a valid
        # but meaningless report on an untouched form.
        today = datetime.now()
        self.fields["start_month"].initial = 1
        self.fields["start_year"].initial = today.year
        self.fields["end_month"].initial = today.month
        self.fields["end_year"].initial = today.year

        self.responsible_formset = None

    def get_responsible_formset(self, contract=None):
        # Always create formset without instance since we're not editing
        # existing records, just collecting data for the report
        if not self.responsible_formset:
            self.responsible_formset = AdditionalResponsibleFormSetWrapper(
                data=self.data if self.is_bound else None,
                prefix="responsibles",
                request=self.request,
                contract=contract,
            )
        return self.responsible_formset

    def clean(self):
        cleaned_data = super().clean()
        try:
            start_month = int(cleaned_data.get("start_month"))
            start_year = int(cleaned_data.get("start_year"))
            end_month = int(cleaned_data.get("end_month"))
            end_year = int(cleaned_data.get("end_year"))
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError("Valores inválidos para mês ou ano.") from exc

        start_date = datetime(start_year, start_month, 1)

        last_day = calendar.monthrange(end_year, end_month)[1]
        end_date = datetime(end_year, end_month, last_day)

        if start_date > end_date:
            raise forms.ValidationError(
                "A data de início deve ser anterior à data de término."
            )

        cleaned_data["start_date"] = start_date
        cleaned_data["end_date"] = end_date

        if "contract" in cleaned_data:
            contract = cleaned_data["contract"]
            formset = self.get_responsible_formset(contract)
            if formset and formset.is_bound:
                has_data = any(
                    form.has_changed()
                    or (
                        any(form.initial.values())
                        if hasattr(form, "initial") and form.initial
                        else form.has_changed()
                    )
                    for form in formset.forms
                )
                if has_data and not formset.is_valid():
                    for form in formset.forms:
                        if form.has_changed() and form.errors:
                            for field, errors in form.errors.items():
                                error_msg = f"Responsável: {field}: {', '.join(errors)}"
                                self.add_error(None, error_msg)

        return cleaned_data
