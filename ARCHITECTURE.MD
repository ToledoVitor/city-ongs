# Architecture

SITTS (`city-ongs`) is a Django web application for third-sector transparency, accountability, and related financial and contractual workflows. The product surface is server-rendered HTML with shared layout under `templates/`.

## Runtime

- Python 3.12, dependency management with `uv`
- Django (`core.settings`, `manage.py`, `core.wsgi` with Gunicorn in the container image)
- PostgreSQL
- WSGI request path only (no Celery or separate async worker in this repository)

## Application layout

Domain logic is split across Django apps mounted from `core/urls.py`:

| App | Route prefix | Role (high level) |
| --- | --- | --- |
| `accounts` | `/accounts/` | Users, organizations, tenancy hooks |
| `accountability` | `/accountability/` | Accountability domain |
| `bank` | `/bank/` | Banking-related flows |
| `contracts` | `/contracts/` | Contracts and related execution |
| `dashboard` | `/dashboard/` | Dashboards |
| `reports` | `/reports/` | Reporting |
| `transparency_portal` | `/transparencia/` | Public transparency portal |
| `activity` | (no top-level URL include) | Activity logs, notifications, supporting services |

Cross-cutting: `core.middlewares` (errors, forced password change), `accounts.middlewares.TenantMiddleware`, `simple_history` for audit trails, `django.contrib.admin` under `__staff__/admin/`.

## Multi-tenancy

`easy_tenants` scopes data by organization: tenant model `accounts.Organization`, tenant field `organization` on tenant-aware models.

## Configuration and environments

- **Local / development**: `.env` via `django-environ`; Postgres (Docker Compose service `db` or external).
- **Non-development**: settings payload from Google Secret Manager (`GOOGLE_CLOUD_PROJECT`, secret `django_settings`); same PostgreSQL driver stack.

## Integrations and platform

- **Static and media files**: `django-storages` with `GoogleCloudStorage` (`GS_BUCKET_NAME`, `STATIC_URL`).
- **Email**: SendGrid (`SENDGRID_API_KEY`, `SENDGRID_ACCOUNT_SENDER`).
- **Health**: `django-health-check` exposed under `__dev__/api/health_check/` for operations.

## Containers and deployment

- **Local stack**: `docker-compose.yml` — Postgres 16 and the app service (`dockerfile`), development server or as documented in `README.md`.
- **Production-style image**: `dockerfile` installs dependencies with `uv sync`, runs Gunicorn on port 8080. Hosted URLs referenced in settings (e.g. Cloud Run–style origins in `CSRF_TRUSTED_ORIGINS`) align with Google Cloud Run.

## Documentation pointers

- `README.md` — setup, Compose, migrations
- `CLAUDE.MD` — conventions, Makefile commands, app list
- `DESIGN.md` — UI tokens and patterns for templates
