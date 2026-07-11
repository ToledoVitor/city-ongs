"""Resolves AUDESP webservice credentials — one (username, password) pair
per (city_hall, environment). Mirrors the DEVELOPMENT branch already used
for the whole Django settings blob in `core/settings.py`: local dev reads a
fixed pair from `.env` (no GCP project needed to run the app locally), while
non-dev environments store the real per-city-hall secret in GCP Secret
Manager — nothing sensitive is ever written to the database.

Secret Manager is per (city_hall, environment) rather than one shared blob
like `django_settings`, because unlike Django settings this is dynamic data
an ops user enters/rotates at runtime through the admin, not deploy-time
config baked into the container.
"""

import json
import os

from django.conf import settings
from google.api_core.exceptions import NotFound
from google.cloud import secretmanager


class AudespCredentialNotConfigured(Exception):
    """No credential is set for this (city_hall, environment) pair."""


def get_credentials(city_hall, environment):
    """Returns (username, password) for `city_hall` in `environment`
    (one of AudespCredential.EnvironmentChoices)."""
    if settings.DEVELOPMENT:
        return _dev_credentials(environment)
    return _secret_manager_get(city_hall, environment)


def set_credentials(city_hall, environment, username, password):
    """Creates/rotates the credential for (city_hall, environment). Only
    meaningful outside DEVELOPMENT — local dev credentials come from `.env`
    directly, there's nothing here to write.
    """
    if settings.DEVELOPMENT:
        raise NotImplementedError(
            "Local dev credentials come from .env "
            "(AUDESP_PILOTO_USERNAME/PASSWORD, AUDESP_PRODUCAO_USERNAME/PASSWORD) "
            "— there's no per-city-hall secret to write in DEVELOPMENT mode."
        )
    _secret_manager_set(city_hall, environment, username, password)


def _dev_credentials(environment):
    pair = settings.AUDESP_DEV_CREDENTIALS.get(environment, {})
    username, password = pair.get("username"), pair.get("password")
    if not username or not password:
        raise AudespCredentialNotConfigured(
            f"AUDESP_{environment}_USERNAME/PASSWORD not set in .env"
        )
    return username, password


def _secret_id(city_hall, environment):
    return f"audesp-credential-{city_hall.id}-{environment.lower()}"


def _project_id():
    return os.environ.get("GOOGLE_CLOUD_PROJECT", "sitts-project")


def _secret_manager_get(city_hall, environment):
    client = secretmanager.SecretManagerServiceClient()
    name = (
        f"projects/{_project_id()}/secrets/{_secret_id(city_hall, environment)}"
        "/versions/latest"
    )
    try:
        payload = client.access_secret_version(name=name).payload.data.decode("utf-8")
    except NotFound as exc:
        raise AudespCredentialNotConfigured(
            f"No AUDESP credential configured for {city_hall} / {environment}"
        ) from exc
    data = json.loads(payload)
    return data["username"], data["password"]


def _secret_manager_set(city_hall, environment, username, password):
    client = secretmanager.SecretManagerServiceClient()
    project = f"projects/{_project_id()}"
    secret_id = _secret_id(city_hall, environment)
    secret_path = f"{project}/secrets/{secret_id}"
    try:
        client.get_secret(name=secret_path)
    except NotFound:
        client.create_secret(
            request={
                "parent": project,
                "secret_id": secret_id,
                "secret": {"replication": {"automatic": {}}},
            }
        )
    payload = json.dumps({"username": username, "password": password}).encode("utf-8")
    client.add_secret_version(
        request={"parent": secret_path, "payload": {"data": payload}}
    )
