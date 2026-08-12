# Known bugs and tech debt — full write-ups

> Moved here from the repo root (`DEBTS.md`) during the context audit, and merged
> with the visual-refactor log that used to live in `TECH_DEBT.MD`. Loaded via the
> `sitts-known-bugs` skill; the skill's own SKILL.md is the index.
>
> `TECH_DEBT.MD` was an append-only log that contradicted itself — several entries
> dated 2026-05-14 said a refactor was pending and later entries on the same date
> said it was DONE. Only the resolved outcome is carried forward below, under
> "Visual refactor — what actually remains".

Findings hit while implementing the AUDESP Fase V plan (`../../sitts-audesp/references/fase-v.md`) that are **not** part of that refactor — bugs, inconsistencies, missing coverage, unrelated tech debt. Logged here instead of fixed inline, so the AUDESP work stays scoped.

Format per entry: file:line, what's wrong, why it's out of scope, suggested fix (if obvious).

---

## CPF/CNPJ stored as plain CharField+validator almost everywhere, typed field in one place

`contracts/models.py:21` (`Company.cnpj`) uses `django_cpf_cnpj`'s typed `CNPJField`. Every other document field — `accounts/models.py:25` (`CityHall.document`), `accounts/models.py:91` (`Organization.document`), `accounts/models.py:231,239` (`User.cpf`/`User.cnpj`), `accountability/models.py:174` (`Favored.document`), `accountability/models.py:289` (`ResourceSource.document`) — is a plain `CharField` + `validate_cpf`/`validate_cnpj`/`validate_cpf_cnpj`. Not touched during the AUDESP build: normalizing field types repo-wide is a real, separate mechanical migration (new field type, data backfill, form/admin updates) unrelated to the Fase V schema work, and touches models the AUDESP refactor doesn't otherwise need to open. All new AUDESP-related CPF/CNPJ fields added by this refactor follow the dominant existing pattern (CharField + validator) for consistency with the app they land in, not the `CNPJField` outlier.

**Suggested fix**: pick one convention (likely `django_cpf_cnpj`'s typed fields, since the package is already a dependency) and migrate the rest in a dedicated pass, updating admin/forms that reference `.document`/`.cpf`/`.cnpj` as plain strings.

## Pre-existing TODO on `Contract.official_government_link`

`contracts/models.py:296` has `# TODO verificar se campo está criado corretamente` above `official_government_link`. Predates this session, unrelated to AUDESP — not resolved here.

## AUDESP reference tables without official label text (stored as raw integers for now)

Two fields added during the Fase V model build store the raw AUDESP numeric code with no `choices=` label mapping, because the manual and JSON Schema don't give complete label text for them (unlike `fonte_recurso_tipo`, `categoria_despesas_tipo`, etc., which do and got full `IntegerChoices`):

- `Expense.issuing_state` (`accountability/models.py`) — 27 numeric codes (manual §8), presumably IBGE UF codes, no label list published.
- `FundTransfer.bank` / `BalanceAdjustment.bank` (`accountability/models.py`) — full BACEN bank-code list (~400+ values per the schema `enum`), no labels at all in the schema or manual.

Not resolved here because building an accurate label table means sourcing the official TCESP/BACEN domain lists, not writing code — this is exactly the "Phase 1: reference data" step already called out in `sitts-audesp/references/fase-v.md` §8. Fabricating labels in a compliance system is worse than leaving the raw code.

**Suggested fix**: source the official lists (BACEN's public bank-code table for `banco`; a TCESP support ticket or the Fase IV cadastro for `estado_emissor`) and convert both to proper `IntegerChoices` before the JSON builder (Phase 4) starts relying on them for display purposes — the raw values are already correct for the wire format either way.

## `Contract.ConcessionChoices` doesn't map 1:1 onto AUDESP's 5 ajuste types

`contracts/models.py:117-123` (pre-existing, predates AUDESP work): `DEVELOPMENTO = "Contrato de Fomento"` has a typo in the member name (should be `DEVELOPMENT`) and its label doesn't match AUDESP's official term ("Termo de Fomento", not "Contrato de Fomento"). There's also a 6th value, `GRANT = "Concessão"`, with no corresponding Fase V ajuste type at all. Not fixed here — `concession_type` is a live field referenced elsewhere in the codebase (reports, dashboard), and renaming/relabeling it is an unrelated mechanical change with its own blast radius (stored values, any code doing string comparisons against `"DEVELOPMENTO"`).

Practical effect on the AUDESP builders: `audesp/builders/declaracao_negativa.py`'s `build_payload(contract, fiscal_year, ajuste_type)` deliberately takes `ajuste_type` as an explicit parameter instead of inferring it from `contract.concession_type`, to avoid depending on this lossy/typo'd mapping. The other 5 builders (`convenio.py`, `contrato_gestao.py`, etc.) don't read `concession_type` either — the caller picks which builder module to call directly.

**Suggested fix**: rename `DEVELOPMENTO` → `DEVELOPMENT` (with a data migration for existing rows), relabel to "Termo de Fomento", and decide whether `GRANT`/"Concessão" contracts are legitimately out of AUDESP scope or were meant to be one of the 5 (likely Contrato de Gestão or Convênio, given typical concessão-adjacent legal structures) — needs a domain-knowledge call, not just a code fix.

## RP-02 exporter renders literal "Ellipsis" in the addenda table instead of real data

`reports/exporters/pass_on_2.py:481` — `_draw_table_III` unconditionally appends a row of seven `f"{...}"` placeholders to the addenda/ajuste table; `f"{...}"` evaluates to the literal string `"Ellipsis"` (Python's `Ellipsis` object formatted into an f-string), not real data. The neighboring comment (`# TODO Após adendo (Ajuste = Adendo), necessário criar tabela`) shows the author knew this was a stub, but it ships unconditionally on every RP-02 export, reachable via `reports/services.py`'s `export_pass_on_2` (dispatched from `reports/views.py` for `report_model == "rp_2"`). Unrelated to AUDESP Fase V — this is the legacy `reports` app's PDF exporter, not the Fase V JSON builders.

**Suggested fix**: query the contract's actual addenda (`ContractAddendum`) to populate the row, or omit the row entirely until that query is implemented.

## RP-02 exporter hardcodes instructional placeholder text as financial figures

`reports/exporters/pass_on_2.py:387,402,404,407` — `_draw_table_II` renders literal prompt/placeholder strings in place of real values: `"Tipo do documento (Holerite, Nota Fiscal, etc...)"` (per-expense document type, repeats for every row), `"O que sobrou do contrato"`, `"Valor glosado"`, and `"Recurso - Devolvido"` (the three balance figures making up the row's total). All four are marked `# TODO` by the original author. Same exporter as above; unrelated to AUDESP Fase V.

**Suggested fix**: wire in the real per-expense document-type field and compute the three balance figures (unapplied transferred resource, value returned to the granting body, amount authorized for next year) from the contract/accountability data.

## RP-04 exporter renders the literal string "ClassAdendo" instead of the global ajuste value

`reports/exporters/pass_on_4.py:578` — in `_draw_concession_table` (the "II - Auxílios, Subvenções..." table), the "Valor Global do Ajuste" column always renders the literal string `"ClassAdendo"` (`# TODO criar classe adendo`) instead of a computed monetary value, while every other column in the same row is a real formatted field. Unrelated to AUDESP Fase V — legacy `reports` exporter.

**Suggested fix**: compute the actual global ajuste value (e.g. `contract.total_value` adjusted for addenda) the same way the other 9 columns in the row are computed.

## RP-06/RP-08 "total public resources" sum omits item D (other revenues)

`reports/exporters/pass_on_6.py:443` and the identical construct at `reports/exporters/pass_on_8.py:430-432` — `sum_items_a_to_d = previous_balance + all_pass_on_values + investment_income` (`# TODO inserir valor de D`) omits `other_revenues_value` (item D), even though the row it feeds is labeled "(E) TOTAL DE RECURSOS PÚBLICOS (A + B + C + D)" and D is computed and displayed in its own row directly above. Sibling exporters `pass_on_10.py`/`pass_on_12.py`/`pass_on_14.py` compute the identical sum correctly with all four terms, confirming this is a copy-paste gap in these two files rather than intended behavior. Unrelated to AUDESP Fase V — legacy `reports` exporters.

**Suggested fix**: add `+ self.other_revenues_value` to the sum in both files, matching the sibling exporters.

## RP-08 exporter hardcodes "dd/mm/aa" and "Nao sei o que é" as real report values

`reports/exporters/pass_on_8.py:372-373` — the "resources available" table's pass-on-date and credit-document-number cells are hardcoded to the literal strings `"dd/mm/aa"` and `"Nao sei o que é"` instead of real data, and ship on every RP-08 export. Sibling exporter `pass_on_6.py` computes `self.latest_pass_on_info` (a `Revenue` query filtered to `PUBLIC_TRANSFER`, pulling `receive_date`/`identification`) at `pass_on_6.py:80` and wires it into this same table at `367-368`. **Correction to the original entry, which claimed pass_on_8 also computes it: it does not** — `latest_pass_on_info` appears nowhere in `pass_on_8.py`, so the fix has to add the query, not just use it. Unrelated to AUDESP Fase V — legacy `reports` exporter.

**Suggested fix**: source the real values from `self.latest_pass_on_info`, mirroring how `pass_on_6.py` already does it.

## Consolidated report's bank-reconciliation tables always show one fabricated row

`reports/exporters/consolidated.py:878` — `_draw_release_table`'s "unreconciled bank statement" and "unreconciled system" tables both hardcode a single fake data row (`["22/22/22", "ZZZ Contabilidade", "R$XX.XXX,XX"]` — not even a valid date), with no query against real bank/ledger records and no conditional guard, so it renders unconditionally on every consolidated report (`export_consolidated`, reachable from `reports/views.py`). Unrelated to AUDESP Fase V — legacy `reports` exporter.

**Suggested fix**: query the real unreconciled bank-statement/ledger entries for the period (likely from the `bank` app's models) and render an empty state when there's nothing to reconcile.

## Period-expenses report header shows the full contract vigency instead of the requested period

`reports/exporters/period_expenses.py:65-71` — `_draw_header`'s "Período" label always reads `contract.start_of_vigency`/`end_of_vigency` (the entire contract vigency), while every table below (`_draw_pass_on_table`, `_draw_expenses_table`) filters by the exporter's own `self.start_date`/`self.end_date` constructor params, which the header never reads — flagged by the developer's own `# TODO confirmar período`, unresolved. Sibling exporters `predicted_versus_realized.py` and `consolidated.py` both source their "Período" line from `self.start_date`/`self.end_date`, confirming this file is the outlier. Unrelated to AUDESP Fase V — legacy `reports` exporter.

**Suggested fix**: use `self.start_date`/`self.end_date` in `_draw_header`, consistent with the rest of the class and its sibling exporters.

## `ContractItemPurchaseProcessDocument.item` is nullable, but only its unrestricted standalone admin can actually leave it null

`contracts/models.py:911` has `# TODO: remove this null=True, blank=True` above the `item` FK, and both real creation paths (`contracts/views.py:1699` upload view; the `TabularInline` at `contracts/admin.py:270-273`) always set `item`. But the model is also registered as its own top-level `ModelAdmin` (`contracts/admin.py:300-307`) with no field restriction, so a staff user can create one directly via `/admin/` leaving `item` blank, producing an orphaned document invisible to item-scoped views/lists. Pre-existing, unrelated to AUDESP Fase V.

**Suggested fix**: now that both real creation paths already always set `item`, drop `null=True, blank=True` and add the migration, per the existing TODO.

## Editing a contract item's supplementation amount silently no-ops due to a field-name typo

`contracts/views.py:1661` — `contract_item_supplementations_update_view` assigns the edited amount to `supplement.supplement_value`, but the model's real field is `suplement_value` (one "p", `contracts/models.py:1201`). `ContractItemSupplementForm`/`ContractItemSupplementUpdateForm` (`contracts/forms.py:653-667`, `686-699`) both declare a correctly-spelled `supplement_value` form field that matches no real model field, so Django's `ModelForm` never writes it back automatically. The create view works around this correctly (`views.py:1627`: `supplement.suplement_value = form.cleaned_data["supplement_value"]`), but the update view assigns to the wrong, non-persisted attribute name, so `supplement.save()` re-persists the old amount unchanged — the redirect still happens and an `ActivityLog` entry is still logged, so the page behaves as if it succeeded. `templates/contracts/items/supplementations-update.html:29` also renders `{{ supplement.supplement_value }}`, which is always empty, so the edit form shows a blank amount field even before submitting. Unrelated to AUDESP Fase V.

**Suggested fix**: minimal fix — assign `supplement.suplement_value = form.cleaned_data["supplement_value"]` at `views.py:1661` (matching the create view) and fix the template to read `supplement.suplement_value`. Better fix — rename the model field itself (`suplement_value` → `supplement_value`, with a migration, plus `contracts/admin.py:279,312` and `Meta.ordering`) so form, view, admin, and template all agree on one spelling.

## Bank transaction duplicate-import guard doesn't catch duplicates when `memo` is NULL

`bank/models.py:398` — `unique_transaction_number_per_bank_account` (`UniqueConstraint(fields=["transaction_number", "memo", "bank_account"], condition=Q(deleted_at__isnull=True))`) includes the nullable `memo` field; under standard SQL semantics NULL is never equal to NULL, so two rows with the same `transaction_number`+`bank_account` but `memo=NULL` don't collide with the constraint. The real import path, `OFXFileParser.import_statement` (`bank/services/ofx_parser.py:91`), calls `Transaction.objects.bulk_create(transactions, ignore_conflicts=True)`, which bypasses `Transaction.clean()`'s equivalent Python-level check entirely — so the DB constraint is the only remaining safeguard, and `memo` is commonly absent/null in many banks' OFX exports. Re-importing the same statement (a plausible user mistake) can silently insert duplicate `Transaction` rows, double-counting `BankAccount.current_balance`. Unrelated to AUDESP Fase V.

**Suggested fix**: drop `memo` from the constraint and key it on `(bank_account, transaction_number)` only, with `condition=Q(transaction_number__isnull=False, deleted_at__isnull=True)` so manual entries without a bank-supplied transaction_number aren't spuriously constrained.

## `ActivityLog`/`Notification` cascade-delete the audit trail when a `User` is deleted

`activity/models.py:304` (`ActivityLog.user`) and `activity/models.py:406-411` (`Notification.recipient`) both use `on_delete=CASCADE` on their FK to `User`. `User` is `AbstractUser`, not `BaseModel` — it has no soft-delete override, so any delete of a `User` row (including Django admin's default bulk "Delete selected users" action, which `accounts/admin.py`'s `CustomUserAdmin` doesn't restrict) is a real SQL DELETE that wipes every `ActivityLog`/`Notification` row that user ever generated, with no separate history table to fall back on. For a compliance/accountability platform, an audit log that disappears exactly when the actor's account is removed defeats the purpose of keeping it. Unrelated to AUDESP Fase V.

**Suggested fix**: change `on_delete` to `PROTECT` or `SET_NULL` — the codebase already uses `SET_NULL` for other `User` FKs like `Contract.accountability_autority`/`supervision_autority`; apply the same pattern here.

## `Contract.internal_code` has no unique constraint and is assigned via a non-atomic max()+1 read

`contracts/models.py:386` — `save()` computes `Contract.objects.aggregate(Max("internal_code"))` and assigns `max + 1` with no `select_for_update()`/transaction locking, and neither the field definition nor any migration adds a unique constraint on it. Two concurrent contract-creation requests can both read the same current max before either INSERT commits, computing the identical next value with nothing rejecting the second insert. `trailing_code`/`name_with_code` expose this as the contract's stable display id, used for import-matching against an external system. Unrelated to AUDESP Fase V.

**Suggested fix**: add a `UniqueConstraint(fields=("organization", "internal_code"), condition=Q(deleted_at__isnull=True))` (matching the pattern already used elsewhere in this file for `ContractExecution`, `ContractGoalAnnualResult`, etc.) and compute the next value inside a locked transaction rather than a bare aggregate.

## `User`'s CPF/CNPJ uniqueness constraint can't actually stop duplicates, and its manual fallback isn't org-scoped

`accounts/models.py:329` — `unique_together = [("organization", "cpf", "cnpj")]` cannot stop two users in the same org from sharing a CPF (or CNPJ), because `clean()` requires exactly one of `cpf`/`cnpj` to be set, so the other column is always NULL, and SQL never treats two NULLs as equal. The only actual enforcement is `clean()`'s own manual lookup (`User.objects.filter(cpf=self.cpf, cnpj=self.cnpj).exclude(pk=self.pk)`), which is itself missing `organization=self.organization` (so it's scoped globally, not "nesta organização" as its own error message claims), and which is skipped entirely by `bulk_create`/`queryset.update()`/fixture loads. A bulk user-import could silently create two logins sharing one CPF within an org. Unrelated to AUDESP Fase V.

**Suggested fix**: replace the 3-column `unique_together` with two partial `UniqueConstraint`s scoped per-organization (`UniqueConstraint(fields=("organization","cpf"), condition=Q(cpf__isnull=False))` and the equivalent for `cnpj`), and fix `clean()`'s lookup to include `organization=self.organization`.

## `RelatedCompany.cnpj` accepts an 11-digit CPF because it uses the permissive `validate_cpf_cnpj`

`accountability/models.py:1278` — this field records, for the AUDESP conflict-of-interest declaration, the CNPJ of a company hired by the entity that's owned by one of its own officers; a person's CPF has no business validating here, but `validate_cpf_cnpj` (which accepts either an 11-digit CPF or 14-digit CNPJ) silently lets one through. The sibling field on the same model, `cpf` (line 1280-1284), correctly uses `validate_cpf`, showing the mismatch is a mistake. The official AUDESP JSON schema's corresponding property is a strict 14-digit pattern, and `audesp/builders/common.py` already wires this field straight into that schema property, so a CPF slipping past the model validator would produce a payload violating the schema. This is a pre-existing model field the Fase V builder merely reads, not part of the refactor itself.

**Suggested fix**: import `validate_cnpj` from `utils.validators` (currently only `validate_cpf`/`validate_cpf_cnpj` are imported at `accountability/models.py:20`) and use it on this field.

## `BoardParticipation.hired_cpfs` has zero format validation, unlike every other CPF field in the codebase

`accountability/models.py:1303` — `hired_cpfs = models.JSONField(default=list, blank=True)` only guarantees the value is JSON-serializable; nothing stops entries like `"abc"`, `12345`, or `{}` from being silently stored, whereas `officer_cpf` on the same model (two lines above) validates with `validate_cpf`. This field backs the same AUDESP §24 conflict-of-interest disclosure as the finding above (which officers' relatives were hired), so a typo or partial paste when entering multiple CPFs is accepted silently and only surfaces, if at all, at JSON-schema validation or TCESP submission time. Pre-existing model field, not part of the Fase V refactor itself.

**Suggested fix**: validate each list entry with `validate_cpf` in the model's `clean()`, or normalize to a child model (one row per hired CPF) matching how this app already models other one-to-many AUDESP data (e.g. `RelatedCompany`, `EmployeeRemunerationPeriod`).

## Public transparency-portal partnership detail page ignores `is_public` entirely

`transparency_portal/views.py:72` — `PartnershipDetailView` has no `is_public` filter and no login requirement, so a partnership explicitly marked non-public is still fully viewable by anyone who has its URL. Every sibling public view in this file (`PartnershipListView`, `OrganizationPartnershipListView`, `OrganizationDocumentListView`) explicitly filters `is_public=True`; this view overrides only `get_context_data()`, not `get_queryset()`, so Django's generic `DetailView` falls back to `PartnershipTransparency.objects.all()`. Hitting `/transparencia/partnership/<uuid:pk>/` directly renders the full page — objective, agreement number/dates, values, status, plus every `FinancialTransfer` row (date, value, free-text credited-account field, document type/number/year) — for any partnership regardless of `is_public`. A staff member flipping `is_public=False` on a partnership under investigation or opted out expects it hidden, but the page stays live at its UUID. Unrelated to AUDESP Fase V.

**Suggested fix**: add `def get_queryset(self): return PartnershipTransparency.objects.filter(is_public=True)` to `PartnershipDetailView`, mirroring the sibling views, so a non-public partnership 404s instead of rendering.

## `OrganizationPartnershipListView` throws an unhandled exception on every request

`transparency_portal/views.py:113` — `get_context_data()` passes an already-evaluated `.values("organization__name").first()` result (a plain `dict`, or `None` when there's no match) as the first argument to `get_object_or_404()`, which requires a Model/Manager/QuerySet. Reproduced directly: `get_object_or_404(None)` raises `ValueError: First argument to get_object_or_404() must be a Model, Manager, or QuerySet, not 'NoneType'.`, and `get_object_or_404({...})` raises `AttributeError: 'dict' object has no attribute 'model'`. Either way, `GET /transparencia/organization/<uuid:org_id>/` (`organization_partnerships`) 500s regardless of whether `org_id` is valid — the page is non-functional as written. Pre-existing since the original "start transparency portal" commit; unrelated to AUDESP Fase V.

**Suggested fix**: fetch the organization directly instead of routing an already-resolved value back through `get_object_or_404`, e.g. `context["organization"] = get_object_or_404(Organization, id=org_id)` — matching the correct pattern already used two classes below in `OrganizationDocumentListView.get_context_data()`.

## Several `DetailView`/`UpdateView` classes discard their own `get_queryset()` optimizations, and 3 of the discarded relation names are typos that would crash if the bypass were fixed naively

`contracts/views.py:281` — `ContractsDetailView.get_object()` is fully re-implemented (`self.model.objects.all()` filtered by `get_user_filtered_queryset`) and never calls `self.get_queryset()`, so its `select_related`(6 fields)/`prefetch_related`(11 paths) built at lines 253-279 are dead code for the actual page render. The same get_queryset()-built-but-never-used pattern repeats verbatim at `ContractItemDetailView`, `ContractExecutionDetailView`, `ContractExecutionActivityUpdateView`, `ContractWorkPlanView`, `ContractTimelineView`, `ItemValueRequestReviewView` (all in this file), and `bank/views.py`'s `BankAccountDetailView`. Separately, three of the discarded relation names are typos that would raise immediately if the bypass were ever removed without fixing them first: `select_related("inversting_account")` (line 263, should be `investing_account`), `prefetch_related("goals__goals_reviews", ...)` (line 275, should be `goal_reviews`), `prefetch_related("items__items_reviews", ...)` (line 270, should be `item_reviews`); `bank/views.py`'s `BankAccountDetailView` additionally has `select_related("contract")`, but `BankAccount` has no `contract` field (only a `contract` Python `@property`). Net effect: pages like the contract detail view (rendered across 7 tabs) issue 40+ avoidable queries for a mid-size contract. Unrelated to AUDESP Fase V.

**Suggested fix**: fix the typos first (`investing_account`, `goal_reviews`, `item_reviews`; drop `bank`'s `select_related("contract")` since it's a property, not a relation), then change each `get_object()` to build on `self.get_queryset()`, e.g. `def get_object(self, queryset=None): return self.get_queryset().get(id=self.kwargs["pk"])`.

## Public transparency-portal list pages trigger 2 extra uncached queries per row via unmemoized properties

`transparency_portal/models.py:55` — `PartnershipTransparency.released_value` and `.accountability_status` (lines 64-75) are `@property` methods that each run a fresh, uncached query. Both `PartnershipListView` (paginate_by=10, no login required) and `OrganizationPartnershipListView` render them per-row in their templates, with no annotate/prefetch covering either — up to 20 avoidable queries per page load on a public, unauthenticated endpoint. Unrelated to AUDESP Fase V.

**Suggested fix**: annotate both directly on the queryset in both views — `released_value` via a filtered `Sum("contract__accountabilities__revenues__value", filter=Q(status=APPROVED))`; `accountability_status` via a `Subquery(OuterRef(...))` pulling the latest `Accountability.status` per contract. Keep the properties only as a fallback for single-object use.

## `ContractsListView`'s addendums count triggers 3 extra queries per row with no annotate

`contracts/views.py:85` — `get_queryset()` selects 6 FK fields but never touches `addendums`, while `templates/contracts/list.html:207-208` calls `{% if contract.addendums.exists %}` then `{{ contract.addendums.count }}` twice — three separate uncached manager calls per row, up to 30 extra queries per page at `paginate_by=10`. The sibling `AccountabilityListView` already solves the identical problem via `.annotate(count_revenues=Count(...), count_expenses=Count(...))`, confirming this is a fixable inconsistency rather than a hard problem. Unrelated to AUDESP Fase V.

**Suggested fix**: add `.annotate(addendums_count=Count("addendums", filter=Q(addendums__deleted_at__isnull=True), distinct=True))` and reference `contract.addendums_count` in the template instead of `.exists()`/`.count()`.

## `FolderManagersListView`'s areas column triggers 2 extra queries per row with no prefetch

`accounts/views.py:49` — `get_queryset()` has no `prefetch_related` for the `areas` M2M, while `templates/accounts/folder-managers/list.html:55,57` calls `{% if manager.areas.count %}` then `{% for area in manager.areas.all %}` — an uncached COUNT then a separate SELECT per row, up to 20 extra queries per page at `paginate_by=10`. Unrelated to AUDESP Fase V.

**Suggested fix**: add `.prefetch_related("areas")` to `get_queryset()`, and change the template to `{% if manager.areas.all %}` instead of `.count`.

## Dashboard's monthly chart data is built with a per-month query loop instead of one grouped query

`dashboard/views.py:145` — `get_context_data()`'s `for _ in range(num_months):` loop (up to 12 iterations for `period=last_year`) calls a `.count()` and three separate `.aggregate(Sum(...))` calls every iteration, none sharing a single grouped query — up to 48 extra queries on top of the page's other counts/aggregates. Unrelated to AUDESP Fase V.

**Suggested fix**: replace the per-month loop with grouped queries computed once, e.g. `accountabilities.values("year","month").annotate(count=Count("id"))`, `revenues.values("accountability__year","accountability__month").annotate(total=Sum("value"))`, etc., then index the results by `(year, month)` in a plain dict while building the months list.

## `BeneficiaryDetailView` computes a per-contract cost breakdown in a query loop that's never even rendered

`accountability/views.py:2008` — `get_context_data()` loops over the beneficiary's contracts computing one `Expense.objects.filter(...).aggregate(Sum("value"))` per contract (classic N+1), plus a redundant `self.get_object()` re-fetch and an unconditional `total_cost` aggregate — and none of `contract_costs`/`total_cost` appear anywhere in `templates/accountability/beneficiaries/detail.html` or any other template in the repo. Pure waste on every beneficiary detail page view. Unrelated to AUDESP Fase V.

**Suggested fix**: delete the dead computation entirely, or if a cost-by-contract breakdown was the intended feature, replace the loop with one grouped query (`Expense.objects.filter(favored=beneficiary, deleted_at__isnull=True).values("accountability__contract").annotate(cost=Sum("value"))`) and actually wire it into the template.

---

---

## Visual refactor — what actually remains

Reconciled from the old `TECH_DEBT.MD` log against the current tree via
`make audit-templates` (175 templates: 156 on `.ui-*`, 1 token-only, 0 legacy).
Entries the log listed as pending and later marked DONE are omitted.

### Open

- **The 15 email templates** (`templates/email/*.html`) are the only UI surface not
  on the design system. They need inline styles and table layouts, not the in-app
  primitives, because mail clients strip CSS classes.
  `templates/registration/password_reset_email.html` belongs to this set too — it's
  wrapped by `email/base_email.html` despite its location.

- **`templates/reports/export.html`** — the "Demais responsáveis" expand panel
  iterates `{% for field in form %}` and matches by substring (`responsible`,
  `autority`, `manager`). Brittle if field names change; a
  `form.responsible_fields` accessor would be sturdier.

- **Accountability tables lost the sticky actions column.** The original
  `expenses-table.html` / `revenues-table.html` used `sticky right-0 z-10` on the
  actions `<td>` so Visualizar/Duplicar/Excluir stayed visible during horizontal
  scroll. The refactor dropped it. The tables fit common viewport widths today, so
  it doesn't bite yet; on a narrower laptop or a wider data shape it will.
  Reintroduce as `.ui-table__cell--sticky-right`
  (`position: sticky; right: 0; background-color: var(--color-canvas)`).

- **Contract items tab** — the "Avaliar" vs "Detalhes" modal label is inverted
  relative to the permission check (`user.can_change_statuses` vs `can_review`).
  Cosmetic; the copy was preserved as-is from the legacy template.

- **Dashboard multi-selects** — the Status and Contract filters were simplified
  from custom Flowbite dropdowns to native `<select multiple>` under time
  pressure. Functionality is intact, polish isn't.

- **Inline SVG icons are duplicated across many pages.** Extracting a
  `templates/ui/icons.html` library would dedupe them and keep stroke widths
  consistent.

- **No automated UI tests.** The refactor was verified by browser walkthrough at
  desktop width only. There is no Playwright/Cypress smoke coverage for login,
  contracts list/detail, or accountability detail — and no viewport assertion
  behind the density rule in `sitts-ui`.

- **Some Django form widgets set their own classes in Python**, which overrides the
  generic `.ui-form` CSS. Verify the rendered control rather than assuming the
  stylesheet won.

### Resolved, kept for context

- The per-row modals in `expenses-table.html` (6 types) and `revenues-table.html`
  (5) were migrated to `.ui-modal__*` / `.ui-alert*` / `.ui-btn--danger`. The
  "Documentos" two-column modal uses `.exp-docs-grid` / `.exp-docs-list` /
  `.exp-docs-dropzone`, and the drag-drop handler toggles
  `.exp-docs-dropzone--active` rather than the old `bg-green-50`.
- `advanced_search.html` and all seven reconcile/review flows were refactored.
  `.ui-status` got a global `white-space: nowrap` so short status pills don't wrap
  in narrow cells.
- `reports/exporters/pass_on_1.py:_draw_down_informations` now guards
  `contractor_company` and renders `LOCAL: —` when it's missing. The broader
  concern stands: the other `pass_on_*.py` exporters still assume many optional
  contract fields are populated.
- The contract detail tabs were reworked again after that log was written — each
  section now has its own URL (`1108463`, `3bcc42e`), which is what left
  `audesp/tests.py`'s Fase IV tab assertion stale. The old note about Flowbite
  `data-tabs-toggle` needing re-init no longer applies.

### One deliberate-looking wart that is deliberate

`templates/accountability/accountability/detail.html:603-611` contains seven
`bg-blue-600` references. They are **not** leftover legacy chrome — the segmented
control's active state is still toggled by JS using Tailwind class names, and this
CSS force-maps them to ink with `!important`. Removing the override without
changing the JS makes the active tab invisible. `make audit-templates` reports this
file as PARTIAL for that reason.
