---
name: sitts-known-bugs
description: Mapped bugs and tech debt in SITTS with file:line, including several paths that 500 or silently save the wrong value on main. Use before touching transparency_portal, reports/exporters, the bank OFX import, accountability review views, or contract item supplementations — and whenever a bug reproduces in an area you did not change.
---

# Known bugs and debt

Everything here has a `file:line` and was confirmed by reading the code. Before
you spend an afternoon on a bug in one of these areas, check whether it's already
listed — several of these look like your change broke something and predate it.

Full write-ups with suggested fixes: [`references/bugs.md`](references/bugs.md).

## Broken right now — will bite immediately

| Where | What |
|---|---|
| `transparency_portal/views.py:113` | `OrganizationPartnershipListView` **500s on every request**. `get_context_data()` passes an already-evaluated `.values(...).first()` (a dict, or `None`) into `get_object_or_404()`, which needs a Model/Manager/QuerySet. `/transparencia/organization/<uuid>/` is non-functional regardless of the id. |
| `transparency_portal/views.py:72` | **Data exposure.** `PartnershipDetailView` has no `is_public` filter and no login requirement, so a partnership marked non-public renders in full — objective, values, status, and every `FinancialTransfer` row — to anyone with the UUID. Every sibling public view filters `is_public=True`; this one overrides only `get_context_data()`, so `DetailView` falls back to `.objects.all()`. |
| `contracts/views.py:1661` | **Silent data loss.** `contract_item_supplementations_update_view` assigns to `supplement.supplement_value`, but the model field is `suplement_value` (one "p", `models.py:1201`). The save persists the old amount, the redirect happens, and an `ActivityLog` entry is written — so it looks like it worked. The create view at `views.py:1627` does it correctly. |
| `accountability/views.py:1224,1341` | 500 on redirect to the URL name `revisar_item`, which doesn't exist (real names: `accountability:expenses-review` / `expense-review`). Fires when the index is out of bounds or there are no IN_ANALISIS records. `views.py:1244` also reverses `review-expenses` instead of `expenses-review`. |
| `bank/models.py:398` | **Silent double-counting.** `unique_transaction_number_per_bank_account` includes the nullable `memo`, and SQL never equates two NULLs — so rows with the same `transaction_number` + `bank_account` don't collide when `memo` is NULL, which is common in real OFX exports. `ofx_parser.py:91` uses `bulk_create(ignore_conflicts=True)`, which skips `Transaction.clean()` entirely, so the constraint is the only guard. Re-importing a statement inflates `BankAccount.current_balance`. |

## Reports exporters ship placeholder strings to users

All verified by reading each line. These render on **every** export of the given
model, not in an edge case. There are no tests for any exporter.

| File | What renders |
|---|---|
| `reports/exporters/pass_on_2.py:481` | The literal `"Ellipsis"`, seven times — `f"{...}"` formats Python's `Ellipsis` object into the addenda table. |
| `reports/exporters/pass_on_2.py:387,402,404,407` | Prompt text as financial figures: `"Tipo do documento (Holerite, Nota Fiscal, etc...)"` per expense row, plus `"O que sobrou do contrato"`, `"Valor glosado"`, `"Recurso - Devolvido"` as the three balance amounts. |
| `reports/exporters/pass_on_4.py:578` | The literal `"ClassAdendo"` in the "Valor Global do Ajuste" column, while all nine sibling columns compute real values. |
| `reports/exporters/pass_on_8.py:372-373` | `"dd/mm/aa"` and `"Nao sei o que é"` as the pass-on date and credit-document number. |
| `reports/exporters/consolidated.py:878` | A fabricated row — `["22/22/22", "ZZZ Contabilidade", "R$XX.XXX,XX"]` — in both bank-reconciliation tables, unconditionally, with no query behind it. Note `22/22/22` isn't a valid date. |
| `reports/exporters/pass_on_6.py:443`, `pass_on_8.py:430-432` | The row labelled "(E) TOTAL DE RECURSOS PÚBLICOS (A + B + C + D)" omits D. `pass_on_10/12/14.py` compute the same sum correctly with all four terms. |
| `reports/exporters/period_expenses.py:65-71` | The "Período" header always shows the full contract vigency while every table below filters by the requested `start_date`/`end_date`. |

## Performance — N+1 in list views

`contracts/views.py:281` and 7 sibling views (plus `bank/views.py`'s
`BankAccountDetailView`) build `select_related`/`prefetch_related` in
`get_queryset()` and then never call it, because `get_object()` is fully
re-implemented. **Three of the discarded relation names are typos that will raise
the moment the bypass is fixed naively:** `inversting_account` (→
`investing_account`), `goals__goals_reviews` (→ `goal_reviews`),
`items__items_reviews` (→ `item_reviews`); `bank`'s `select_related("contract")`
names a Python `@property`, not a relation. Fix the typos first.

Also: `ContractsListView` (3 uncached calls per row), `FolderManagersListView`
(2 per row), `transparency_portal` list pages (2 per row on a public
unauthenticated endpoint), the dashboard's per-month query loop (up to 48 queries),
and `BeneficiaryDetailView`'s N+1 that computes a breakdown **no template
renders**.

## Model-level correctness

- `accounts/models.py:329` — `unique_together = [("organization","cpf","cnpj")]` can't stop duplicates: `clean()` requires exactly one of the two, so the other is always NULL. The manual fallback lookup is also missing `organization=`, so it's globally scoped despite its own "nesta organização" error message, and `bulk_create`/`update` skip it entirely.
- `activity/models.py:304,406-411` — `ActivityLog.user` and `Notification.recipient` are `CASCADE`. `User` is `AbstractUser` with no soft delete, so admin's bulk "Delete selected users" wipes that user's entire audit trail. For a compliance platform this defeats the log's purpose. Other `User` FKs in the codebase already use `SET_NULL`.
- `contracts/models.py:386` — `Contract.internal_code` is assigned from a bare `aggregate(Max(...)) + 1` with no lock and no unique constraint. Two concurrent creates get the same value, and it's the contract's stable display id used for import matching.
- `accountability/models.py:1278` — `RelatedCompany.cnpj` uses the permissive `validate_cpf_cnpj`, so an 11-digit CPF passes into a field the AUDESP schema requires to be 14 digits. The sibling `cpf` field correctly uses `validate_cpf`.
- `accountability/models.py:1303` — `BoardParticipation.hired_cpfs` is a bare `JSONField(default=list)` with zero validation; `"abc"`, `12345`, and `{}` all store silently. Backs the same AUDESP §24 conflict-of-interest disclosure.
- `contracts/models.py:911` — `ContractItemPurchaseProcessDocument.item` is nullable with a `# TODO: remove this null=True`. Both real creation paths always set it, but the standalone `ModelAdmin` doesn't restrict the field, so a staff user can create an orphan.
- `contracts/models.py:117-123` — `ConcessionChoices.DEVELOPMENTO` is a typo'd member whose label ("Contrato de Fomento") doesn't match AUDESP's term ("Termo de Fomento"), plus a sixth value `GRANT` with no ajuste-type counterpart. This is why the AUDESP builders never infer from `concession_type` — see `sitts-audesp`.
- CPF/CNPJ typing is inconsistent repo-wide: `Company.cnpj` uses `django_cpf_cnpj`'s typed `CNPJField`, every other document field is a plain `CharField` + validator.

## Dangling doc pointers in user-visible help text

Two `help_text` strings point staff users at an internal audit document that no
longer exists at that path (it's now `references/bugs.md` under this skill):

- `accountability/models.py:534` — `"Código AUDESP (1-27) — tabela de referência pendente (ver DEBTS.md / manual §8.1)"`
- `accountability/models.py:1591` — `"Código do banco (tabela BACEN) — tabela de referência pendente (ver DEBTS.md)"`

Independently of the broken path, admin help text shouldn't cite an internal
tracker at all. Fixing them means editing `help_text`, which Django requires a
migration for — deliberately not done in the docs-only change that moved the file,
so it isn't hidden inside an unrelated commit. Drop the parenthetical and keep
"tabela de referência pendente".

## Stale tests

`audesp.tests.AudespFaseIVViewsTests.test_contract_detail_page_renders_fase_iv_tab`
fails. It asserts `"audesp-fase-iv-tab"` is in the contract detail body, and that
string is in no template — the contract-detail section refactor (`1108463`,
`3bcc42e`) moved each section behind its own URL, so `contracts/detail.html` no
longer references AUDESP at all. The test should fetch the section URL instead.

## Open UI work

The **15 email templates** under `templates/email/` are the only UI surface not on
the design system, and they need inline styles and table layouts rather than the
in-app primitives, because mail clients strip CSS classes. `make audit-templates`
reports them as neutral for that reason. Everything else is done — 156 of 175
templates use `.ui-*`, `home.html` styles itself from the tokens, and nothing is
left on legacy chrome.

Smaller items: the contract items tab's "Avaliar" vs "Detalhes" modal labels are
inverted relative to the permission check (cosmetic, preserved from the legacy
template); the dashboard's Status and Contract multi-selects were simplified to
native `<select multiple>`; `templates/reports/export.html`'s "Demais
responsáveis" panel matches form fields by substring, which breaks if field names
change; the accountability tables dropped the `sticky right-0` actions column, so
row actions scroll away on narrow viewports.
