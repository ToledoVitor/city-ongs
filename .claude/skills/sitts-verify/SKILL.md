---
name: sitts-verify
description: How to actually run checks and exercise views in SITTS, including with no Docker and no Postgres available. Use when you need to validate a change, run the test suite, reproduce a view end-to-end, or seed realistic data. Covers the env-var floor, the sqlite in-memory harness, and the easy_tenants tenant context outside a request.
---

# Verifying SITTS changes

Every command here was run in this repo. Where something has a caveat, the
caveat is real, not defensive hedging.

## The env-var floor

`core/settings.py` reads 19 variables through `django-environ` and will not
import without them. You do **not** need a `.env` file — export them in the
shell. Values can be junk for anything that isn't a real connection:

```bash
export DEVELOPMENT=True DEBUG=True SECRET_KEY=x \
  DB_NAME=x DB_USER=x DB_PASSWORD=x DB_HOST=localhost DB_PORT=5432 \
  STATIC_URL=/static/ WEBSITE_URL=http://localhost:8000 \
  GS_BUCKET_NAME=x GS_STATIC_BUCKET_NAME=x GS_MEDIA_BUCKET_NAME=x \
  SENDGRID_API_KEY=x SENDGRID_ACCOUNT_SENDER=x@x.com \
  AUDESP_PILOTO_USERNAME=x AUDESP_PILOTO_PASSWORD=x \
  AUDESP_PRODUCAO_USERNAME=x AUDESP_PRODUCAO_PASSWORD=x
```

`.env.example` is the canonical list (it also has the optional
`AUDESP_TOKEN_TTL_SECONDS`).

## What works with no database at all

```bash
make check   # manage.py check + makemigrations --check --dry-run
```

`check` is clean and silent. `makemigrations --check` emits a
`RuntimeWarning: Got an error checking a consistent migration history` because it
tries to reach Postgres, then still reports correctly — **"No changes detected"
is a valid pass even with that warning above it.** Don't chase the warning.

## Running the test suite

```bash
make test          # needs Postgres up (make up)
make test-sqlite   # no Postgres needed
```

`make test-sqlite` runs against `core/settings_sqlite_test.py`, which is
`core.settings` with `DATABASES` swapped for sqlite `:memory:`.

**Coverage is two apps, not seven.** `accounts/tests.py` has 11 tests (AUDESP
credential settings) and `audesp/tests.py` has 12 (Fase IV views, build, submit).
`accountability`, `activity`, `bank`, `contracts`, and `reports` are one-line
stubs. 23 tests is the whole suite — a green run says almost nothing about the
rest of the app.

**One test currently fails**, and it isn't yours:
`audesp.tests.AudespFaseIVViewsTests.test_contract_detail_page_renders_fase_iv_tab`
asserts `"audesp-fase-iv-tab"` appears in the contract detail body. That string
exists in no template — the contract-detail section refactor (`1108463`,
`3bcc42e`) moved each section to its own URL, so `templates/contracts/detail.html`
no longer references AUDESP at all. The test needs updating to fetch the section
URL instead. See `sitts-known-bugs`.

## Exercising a view end-to-end without Postgres

This works, verified. Two ordering rules make or break it.

```python
# Run from the repo root — `core` must be importable.
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# RULE 1: swap DATABASES on the settings *module*, BEFORE django.setup().
from core import settings as s
s.DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
}

django.setup()

from django.core.management import call_command
call_command("migrate", verbosity=0, run_syncdb=True)

# Idempotent, and covers most domain models including AUDESP Fase V fixtures.
from accounts.management.commands.seed_dev import run_seed
run_seed()

from accounts.models import Organization, User
org = Organization.objects.first()

# RULE 2: tenant-scoped models need a tenant set explicitly outside a request.
from easy_tenants.utils import state
state.set({"enabled": True, "tenant": org})

from django.test import Client
client = Client()
client.force_login(User.objects.filter(organization=org).first())
print(client.get("/contracts/").status_code)   # -> 200
```

**Rule 1, why it matters:** mutating `django.conf.settings.DATABASES` *after*
`django.setup()` is too late. Populating the app registry already cached a
`DatabaseWrapper` against the old config, so you get Postgres connection errors
despite the sqlite setting. Mutate `core.settings.DATABASES` before setup.

**Rule 2, why it matters:** `TenantMiddleware` is what normally establishes the
tenant, and there's no middleware in a plain script. Set it via `state.set()`
directly — wrapping the script body in `with tenant_context(org):` does not hold
the way you'd expect across the imports and queries that follow.

## Formatting and linting

```bash
make format        # ruff
make pre-commit    # install the hook
```

`.pre-commit-config.yaml` runs `ruff --fix` only. There is no type checker and no
CI workflow that validates code — `.github/workflows/` contains just the manual
production deploy. Nothing catches a regression for you; run the checks yourself.

## Template coverage

```bash
make audit-templates
```

Classifies every shipped template by `.ui-*` usage, token-only usage, leftover
chromatic Tailwind, or neutral-for-a-known-reason. Trust it over a bare grep for
`ui-`: a page can be fully on the system with zero utility classes.

## What you cannot verify here

Be explicit in your report when one of these applies rather than implying you
checked it:

- **Real Postgres behaviour** — sqlite accepts things Postgres rejects, and the repo uses a Postgres `unaccent` extension migration (`accounts/migrations/0003_unaccent_extension.py`). Constraint and collation behaviour can differ.
- **The AUDESP webservice** — `audesp/tests.py` stubs the transport. No test touches piloto or produção.
- **PDF exporter output** — the `reports/exporters/*` modules have no tests at all, and several ship placeholder strings (see `sitts-known-bugs`).
- **Browser behaviour** — no Playwright, no Cypress, no viewport assertions.
