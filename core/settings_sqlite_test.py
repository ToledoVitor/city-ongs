"""Test settings: run the suite without Postgres. Used by `make test-sqlite`."""

from core.settings import *  # noqa: F401,F403

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
