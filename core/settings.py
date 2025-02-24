import io
import os

import environ
from google.cloud import secretmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(DEBUG=(bool, False), DEVELOPMENT=(bool, False))
env_file = os.path.join(BASE_DIR, ".env")

DEVELOPMENT = env("DEVELOPMENT")

if DEVELOPMENT:
    env.read_env(env_file)
    # Database
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT", default=None),
        }
    }
else:
    print("reading gcloud env settings")
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "sitts-project")
    settings_name = "django_settings"

    # Pull secrets from Secret Manager
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{settings_name}/versions/latest"
    payload = client.access_secret_version(name=name).payload.data.decode("UTF-8")
    env.read_env(io.StringIO(payload))

    # Database
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": "",
        }
    }

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "https://sitts-455340212401.southamerica-east1.run.app",
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
    # Internal apps
    "accountability",
    "activity",
    "accounts",
    "bank",
    "contracts",
    "reports",
    # Third parties
    "django_cpf_cnpj",
    "health_check",
    "health_check.db",
    "simple_history",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
LOGOUT_REDIRECT_URL = "home"

WSGI_APPLICATION = "core.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# [START gaeflex_py_django_static_config]
# Define static storage via django-storages[google]
STATIC_URL = env("STATIC_URL")
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
    },
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
    },
}
GS_QUERYSTRING_AUTH = False
GS_BUCKET_NAME = env("GS_BUCKET_NAME")
GS_DEFAULT_ACL = None
STATICFILES_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
DEFAULT_FILE_STORAGE = "storages.backends.gcloud.GoogleCloudStorage"
# [END gaeflex_py_django_static_config]

# Default primary key field type
# https://docs.djangoproject.com/en/stable/ref/settings/#default-auto-field


AUTH_USER_MODEL = "accounts.User"

DATE_INPUT_FORMATS = [
    "%d/%m/%Y",
    "%Y-%m-%d",  # ISO
]

EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"

WEBSITE_URL = env("WEBSITE_URL", default="localhost")
SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")
SENDGRID_ACCOUNT_SENDER = env("SENDGRID_ACCOUNT_SENDER", default="")
