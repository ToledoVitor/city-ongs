# CLAUDE.MD

SITTS (`city-ongs`) — Sistema Integrado de Transparência e Transferências
Sociais. A Django app for third-sector accountability: city halls transfer public
money to NGOs under a contract, the NGO reports how it was spent, and the whole
trail is auditable — including machine submission to São Paulo's TCE via the
AUDESP webservice. Server-rendered templates, multi-tenant by organization.

Keep this file short. It is loaded on every request. Task-specific depth lives in
the skills below; non-obvious traps live in Gotchas.

> Filename note: keep this exact name. On a case-insensitive macOS volume a
> sibling `CLAUDE.md` resolves to the same path and can silently replace this
> file. Don't add one.

## Skills — load the one that matches the work

| Skill | When |
|---|---|
| `sitts-ui` | `templates/`, CSS, UI copy. Pairs with `DESIGN.md`, the binding UI spec. |
| `sitts-verify` | Running checks or exercising views, especially without Docker/Postgres. |
| `sitts-audesp` | Anything under `audesp/` or touching TCE-SP payloads. |
| `sitts-deploy` | GCP, Cloud Run, IAM, image retention. |
| `sitts-known-bugs` | Debugging, or before touching `transparency_portal`, `reports/exporters`, the bank OFX import, or accountability review views. |

Run `make help` for commands.

## Code is English-only

Model and class names, fields, choice *member* names, methods, variables — all
English, even though the domain is Brazilian-Portuguese (AUDESP / TCE
compliance). Portuguese is allowed only in `verbose_name`, `help_text`, choice
*labels*, docstrings/comments, and anything rendered to a user.

The exception is established domain acronyms with no English equivalent already
in use here: `cpf`, `cnpj`, `cns`, `cbo`. Keep those as-is rather than inventing
a translation.

## Gotchas

**`organization` is auto-populated — never set it by hand.**
`accounts.middlewares.TenantMiddleware` wraps every authenticated request in
`easy_tenants.tenant_context(request.user.organization)`, and
`OrganizationTenantBaseClass.save()` reads that context. `create_contract_accountability_view`
in `accountability/views.py` is the reference. Several older views still assign it
explicitly (`accountability/views.py:191,201,870,880,1102,1205`,
`contracts/views.py:215,682`) — that's redundant for request-scoped views, not
required, and not a pattern to copy.

**A parent FK excluded from a `ModelForm` silently disables `UniqueConstraint`
validation.** This one ships 500s. The repo-wide pattern is that contract-scoped
child models take their parent FK from the URL in the view, not as a form field
(`BudgetCommitment.contract`, `OpinionOrMinutes.annual_statement`). Django's
`ModelForm._get_validation_exclusions()` puts any field absent from `Meta.fields`
into `exclude`, and `Model._get_unique_checks()` skips a `UniqueConstraint`
**entirely** if **any** of its fields are in `exclude` — regardless of whether
that field has a value on the instance. Pre-setting the FK on an unsaved instance
passed via `instance=` does not help; the skip is keyed off `exclude`, not the
value.

The only fix is checking by hand before saving, in **both** the create view and
any `UpdateView.form_valid()` override. Working example:
[`accountability/views.py:345-365`](accountability/views.py:345) (`accountability_exists`).
Skip it and a genuine duplicate raises an unhandled `IntegrityError` instead of a
validation error.

**Tenant-scoped models need an explicit tenant outside a request.** For scripts
and shells: `from easy_tenants.utils import state; state.set({"enabled": True, "tenant": org})`.
Set it directly — wrapping the whole script in a `with tenant_context(...)` block
does not survive the way you'd expect.

**No async worker.** WSGI request path only (`core.wsgi`, Gunicorn: one process,
4 threads) — no Celery, no queue, no separate worker. Anything slow runs inside the
request or not at all. The threads are newer than some of the code; see
`sitts-deploy` for the two spots holding process-global state.

**Two GCS buckets, and they must stay split.** `sitts-504501-static` is public and
unsigned; `sitts-504501-media` is private with signed URLs. They were one bucket
once, and that configuration let anyone who learned the bucket name enumerate every
contract, bank statement, and attachment. Details in `sitts-deploy`.

**Non-development settings come from Google Secret Manager**, not `.env`. The
payload is the `django_settings` secret in the project named by
`GOOGLE_CLOUD_PROJECT`. `.env` + `django-environ` is the local path only.

**`psycopg2` is compiled from source, not `psycopg2-binary`.** `pg_config` must
be on `PATH` before `uv sync`. On macOS `libpq` is keg-only:
`brew install libpq && export PATH="$(brew --prefix libpq)/bin:$PATH"`.

**Test coverage is two apps, not seven.** `accounts/tests.py` (13 tests) and
`audesp/tests.py` (17) are real. `accountability`, `activity`, `bank`,
`contracts`, and `reports` are one-line stubs. `make test` runs what exists —
don't read a green run as broad coverage, and don't assume an untested path works.

## Non-negotiable

This is a compliance system handling public money. These are not style
preferences.

- **Never edit `.env`, never commit a secret.** Production config lives in Secret Manager.
- **Never fabricate AUDESP reference-table labels.** Some fields store raw TCESP/BACEN numeric codes because the official label lists aren't published (`Expense.issuing_state`, `FundTransfer.bank`, `BalanceAdjustment.bank`). Leaving a raw code is correct; inventing a label that a municipality then files with the TCE is not. Source the official list or leave it.
- **`is_public` on `transparency_portal` is a publication gate, not a UI filter.** Every public view must filter on it. A partnership flipped non-public — under investigation, or opted out — must 404, not render.
- **Deploy is irreversible by hand.** `.github/workflows/production-deploy.yml` fires only on manual `workflow_dispatch`, nothing validates it in CI, and it sends 100% of traffic to the new revision. Image retention is applied by hand, so the rollback horizon is finite. Load `sitts-deploy` before touching it.
- **The audit trail must survive the actor.** `ActivityLog` / `Notification` are the compliance record. Don't add a hard-delete path to them.
- **No destructive git commands unless asked** — no `reset --hard`, no force-push, no branch deletion.
