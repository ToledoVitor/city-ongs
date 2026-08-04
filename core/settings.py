import io
import os
from datetime import timedelta
from typing import Any, Dict, List

import environ
from google.cloud import secretmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(DEBUG=(bool, False), DEVELOPMENT=(bool, False))
env_file = os.path.join(BASE_DIR, ".env")
env.read_env(env_file)

DEVELOPMENT = env("DEVELOPMENT")

# Reuse each worker's Postgres connection instead of dialing a new one per
# request. On Cloud Run the round trip to Cloud SQL is the single biggest
# fixed cost in a short request, and every connection held open is one of the
# instance's scarce slots on a small Postgres tier — hence a short TTL rather
# than a persistent pool.
#
# CONN_HEALTH_CHECKS is what makes reuse safe here: with cpu-throttling the
# instance is frozen between requests, so a socket can go dead unnoticed.
# Django then pings the connection before handing it over and reconnects
# instead of raising InterfaceError on the first query.
#
# Budget the ceiling as max_cloud_run_instances x gunicorn_threads. Keep it
# under the database's max_connections.
CONN_MAX_AGE = env.int("CONN_MAX_AGE", default=60)
CONN_HEALTH_CHECKS = True

if DEVELOPMENT:
    # Database
    DATABASES: Dict[str, Dict[str, Any]] = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT", default=None),
            "CONN_MAX_AGE": CONN_MAX_AGE,
            "CONN_HEALTH_CHECKS": CONN_HEALTH_CHECKS,
        }
    }
else:
    print("reading gcloud env settings")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "sitts-504501")
    settings_name = "django_settings"

    # Pull secrets from Secret Manager
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
    payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")
    env.read_env(io.StringIO(payload))

    # Database
    DATABASES: Dict[str, Dict[str, Any]] = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": "",
            "CONN_MAX_AGE": CONN_MAX_AGE,
            "CONN_HEALTH_CHECKS": CONN_HEALTH_CHECKS,
        }
    }

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/django.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "utils.logging": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Ensure logs directory exists
if not os.path.exists(os.path.join(BASE_DIR, "logs")):
    os.makedirs(os.path.join(BASE_DIR, "logs"))

ALLOWED_HOSTS: List[str] = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://sitts-bdhqfqo3cq-rj.a.run.app",
    "https://gestao-sitts-web.com",
]

# Application definition
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Registers the `unaccent` lookup used by ComboboxSearchView so searching
    # "saude" matches "Saúde". Requires the unaccent extension (see the
    # accounts.0003 migration).
    "django.contrib.postgres",
    # Internal apps
    "accountability",
    "activity",
    "accounts",
    "audesp",
    "bank",
    "contracts",
    "dashboard",
    "reports",
    "transparency_portal",
    # Third parties
    "easy_tenants",
    "django_cpf_cnpj",
    "health_check",
    "health_check.db",
    "simple_history",
    "phonenumber_field",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Internal Middlewares
    "core.middlewares.ErrorHandlingMiddleware",
    "core.middlewares.ForcePasswordChangeMiddleware",
    "accounts.middlewares.TenantMiddleware",
    # Third parties
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR + "/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

WSGI_APPLICATION = "core.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation.NumericPasswordValidator"),
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images) and user uploads.
#
# Two buckets on purpose. Uploaded documents — contracts, bank statements,
# accountability attachments — carry CPF and municipal financial data;
# stylesheets do not. Serving both from one public bucket makes every upload
# world-readable, and `roles/storage.objectViewer` on allUsers also grants
# storage.objects.list, so the entire media set would be enumerable by anyone
# who found the bucket name. Keep the two apart.
STATIC_URL = env("STATIC_URL")

# Falls back to the single pre-split bucket so an environment that has not been
# migrated yet still boots. Read with a default of its own: passing
# `default=env("GS_BUCKET_NAME")` would evaluate eagerly and raise even when the
# two new names are set.
_legacy_bucket = env("GS_BUCKET_NAME", default="")
GS_STATIC_BUCKET_NAME = env("GS_STATIC_BUCKET_NAME", default=_legacy_bucket)
GS_MEDIA_BUCKET_NAME = env("GS_MEDIA_BUCKET_NAME", default=_legacy_bucket)

STORAGES = {
    # Private bucket. querystring_auth signs every URL, so a link works for the
    # signature's lifetime and cannot be guessed or shared indefinitely.
    # Templates render `{{ obj.file.url }}` directly, so this is what stands
    # between an upload and the open internet.
    #
    # Signing on Cloud Run goes through the IAM signBlob API rather than a key
    # file: the runtime service account needs roles/iam.serviceAccountTokenCreator
    # on itself (see docs/DEPLOY.md).
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_MEDIA_BUCKET_NAME,
            "default_acl": None,
            "querystring_auth": True,
            "expiration": timedelta(minutes=15),
        },
    },
    # Public bucket: CSS/JS/admin assets only. Unsigned so URLs stay stable and
    # cacheable — nothing here is sensitive.
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_STATIC_BUCKET_NAME,
            "default_acl": None,
            "querystring_auth": False,
        },
    },
}

# Kept for anything still reading the module-level name directly.
GS_BUCKET_NAME = GS_MEDIA_BUCKET_NAME

# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field


AUTH_USER_MODEL = "accounts.User"

DATE_INPUT_FORMATS = [
    "%d/%m/%Y",
    "%Y-%m-%d",  # ISO
]

WEBSITE_URL = env("WEBSITE_URL", default="localhost")
SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")
SENDGRID_ACCOUNT_SENDER = env("SENDGRID_ACCOUNT_SENDER", default="")

# AUDESP Fase V webservice (see AUDESP_FASE_V_AUDIT.md §1.2/§6)
AUDESP_BASE_URLS = {
    "PILOTO": "https://audesp-piloto.tce.sp.gov.br",
    "PRODUCAO": "https://audesp.tce.sp.gov.br",
}
# Local-dev-only AUDESP credentials (see audesp/secrets.py) — non-dev
# environments resolve credentials from GCP Secret Manager instead, one
# secret per (city_hall, environment), never from settings/env.
AUDESP_DEV_CREDENTIALS = {
    "PILOTO": {
        "username": env("AUDESP_PILOTO_USERNAME", default=""),
        "password": env("AUDESP_PILOTO_PASSWORD", default=""),
    },
    "PRODUCAO": {
        "username": env("AUDESP_PRODUCAO_USERNAME", default=""),
        "password": env("AUDESP_PRODUCAO_PASSWORD", default=""),
    },
}
# Placeholder TTL until a real login response lets us read the JWT's own exp claim.
AUDESP_TOKEN_TTL_SECONDS = env.int("AUDESP_TOKEN_TTL_SECONDS", default=600)

# Easy tenants configuration
EASY_TENANTS_TENANT_MODEL = "accounts.Organization"
EASY_TENANTS_TENANT_FIELD = "organization"
