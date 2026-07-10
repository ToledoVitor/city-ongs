# DEBTS.md

Findings hit while implementing the AUDESP Fase V plan ([AUDESP_FASE_V_AUDIT.md](AUDESP_FASE_V_AUDIT.md)) that are **not** part of that refactor — bugs, inconsistencies, missing coverage, unrelated tech debt. Logged here instead of fixed inline, so the AUDESP work stays scoped.

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

Not resolved here because building an accurate label table means sourcing the official TCESP/BACEN domain lists, not writing code — this is exactly the "Phase 1: reference data" step already called out in [AUDESP_FASE_V_AUDIT.md](AUDESP_FASE_V_AUDIT.md) §8. Fabricating labels in a compliance system is worse than leaving the raw code.

**Suggested fix**: source the official lists (BACEN's public bank-code table for `banco`; a TCESP support ticket or the Fase IV cadastro for `estado_emissor`) and convert both to proper `IntegerChoices` before the JSON builder (Phase 4) starts relying on them for display purposes — the raw values are already correct for the wire format either way.

---

