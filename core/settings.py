import io
import os
from typing import Any, Dict, List

import environ
from google.cloud import secretmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(DEBUG=(bool, False), DEVELOPMENT=(bool, False))
env_file = os.path.join(BASE_DIR, ".env")

DEVELOPMENT = env("DEVELOPMENT")

if DEVELOPMENT:
    env.read_env(env_file)
    # Database
    DATABASES: Dict[str, Dict[str, Any]] = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT", default=None),
        }
    }
    # Cache para desenvolvimento
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://localhost:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
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
    DATABASES: Dict[str, Dict[str, Any]] = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": "",
        }
    }

    # Cache configuration for production
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f'redis://{os.environ.get("REDIS_HOST", "localhost")}:{os.environ.get("REDIS_PORT", "6379")}/1',
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "RETRY_ON_TIMEOUT": True,
                "MAX_CONNECTIONS": 1000,
                "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
                "CONNECTION_POOL_CLASS_KWARGS": {
                    "max_connections": 50,
                    "timeout": 20,
                },
                "PARSER_CLASS": "redis.connection._HiredisParser",
                "COMPRESSOR_CLASS": "django_redis.compressors.zlib.ZlibCompressor",
                "IGNORE_EXCEPTIONS": True,
                "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            },
            "KEY_PREFIX": "sitts",
            "TIMEOUT": 300,  # 5 minutes
        }
    }

    # Cache time for different types of content
    CACHE_MIDDLEWARE_SECONDS = 300  # 5 minutos
    CACHE_MIDDLEWARE_KEY_PREFIX = "sitts"

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
        "cache_file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/cache.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.core.cache": {
            "handlers": ["cache_file"],
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
LOGOUT_REDIRECT_URL = "home"

WSGI_APPLICATION = "core.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "NumericPasswordValidator"),
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Sao_Paulo"

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

WEBSITE_URL = env("WEBSITE_URL", default="localhost")
SENDGRID_API_KEY = env("SENDGRID_API_KEY", default="")
SENDGRID_ACCOUNT_SENDER = env("SENDGRID_ACCOUNT_SENDER", default="")

# Easy tenants configuration
EASY_TENANTS_TENANT_MODEL = "accounts.Organization"
EASY_TENANTS_TENANT_FIELD = "organization"
