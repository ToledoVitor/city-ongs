"""HTTP client for the TCESP AUDESP webservice — Fase V and Fase IV share
one base URL, one login/token mechanism, and one client class; only the
submission paths and payload shapes differ (confirmed from the same
OpenAPI spec, `audesp.tce.sp.gov.br/api/audesp.yaml`, for both phases).

Fase V endpoint paths, auth header format, multipart field name, and
status values below come straight from the manual (v1.18) and the
downloaded JSON Schemas — see AUDESP_FASE_V_AUDIT.md §1.2 for the workflow
this mirrors (login -> submit -> consulta -> retificação) and §6 for why
this lives in its own module rather than inside a builder or model.

Fase IV endpoint paths (`/recepcao-fase-4/f4/enviar-ajuste`,
`/f4/consulta/{protocolo}`) come from the same OpenAPI spec — see
AUDESP_FASE_IV_AUDIT.md.

Not yet exercised against a live server — no TCESP piloto credentials are
provisioned yet. Verified so far only against a mocked HTTP layer (request
shape: URL, headers, multipart body — see the scratchpad test referenced in
AUDESP_FASE_V_AUDIT.md §8 Phase 5). The retry count/backoff/timeout below
are starting guesses to revisit once real latency and rate limits are
observed; the JWT-expiry handling is deliberately conservative (a fixed TTL,
not a decoded `exp` claim) for the same reason — see `_token_expired`.
"""

import json
import time

import requests
from django.conf import settings

_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2  # doubled each attempt: 2s, 4s, 8s
_TIMEOUT_SECONDS = 30
_TOKEN_EXPIRY_LEEWAY_SECONDS = 30


class AudespError(Exception):
    """Base for all AudespClient errors."""


class AudespAuthenticationError(AudespError):
    """`/login` failed — bad credentials, locked account, or missing
    "Transmissão Pacotes - Fase V" permission for this environment."""


class AudespValidationError(AudespError):
    """The webservice rejected the payload (HTTP 400). This is a *second*,
    server-side validation — distinct from `audesp.validators.validate_payload`,
    since AUDESP enforces business rules (manual §5-§34 prose) that plain
    JSON Schema can't express. `errors` holds the parsed response body.
    """

    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors if errors is not None else []


class AudespConnectionError(AudespError):
    """Network-level failure (timeout, DNS, connection refused) after
    exhausting retries — safe to retry the whole operation later, unlike
    AudespValidationError which never is."""


class AudespClient:
    """Talks to the AUDESP Fase V webservice on behalf of one
    `AudespCredential` (one organization + environment pair).
    """

    _SUBMIT_PATHS = {
        "CONTRATO_GESTAO": "/f5/enviar-prestacao-contas-contrato-gestao",
        "CONVENIO": "/f5/enviar-prestacao-contas-convenio",
        "TERMO_COLABORACAO": "/f5/enviar-prestacao-contas-termo-colaboracao",
        "TERMO_FOMENTO": "/f5/enviar-prestacao-contas-termo_fomento",
        "TERMO_PARCERIA": "/f5/enviar-prestacao-contas-termo-parceria",
    }
    _DECLARACAO_NEGATIVA_PATH = "/f5/declaracao-negativa"
    _FASE_IV_AJUSTE_PATH = "/recepcao-fase-4/f4/enviar-ajuste"

    def __init__(self, credential):
        self.credential = credential
        self._base_url = settings.AUDESP_BASE_URLS[credential.environment]
        self._token = None
        self._token_issued_at = None

    # --- auth ---

    def _login(self):
        username, password = self.credential.get_credentials()
        response = self._request_with_retry(
            "POST",
            f"{self._base_url}/login",
            headers={"x-authorization": f"{username}:{password}"},
        )
        if response.status_code != 200:
            raise AudespAuthenticationError(
                f"AUDESP login failed ({response.status_code}): {response.text}"
            )
        self._token = response.json()["token"]
        self._token_issued_at = time.time()

    def _token_expired(self):
        """A fixed TTL (`settings.AUDESP_TOKEN_TTL_SECONDS`), not a decoded
        JWT `exp` claim — we haven't seen a real token yet to confirm its
        claim shape, so a conservative constant is the honest starting
        point. Swap for real expiry-reading once a live login response is
        available.
        """
        if self._token is None:
            return True
        age = time.time() - self._token_issued_at
        return age >= (settings.AUDESP_TOKEN_TTL_SECONDS - _TOKEN_EXPIRY_LEEWAY_SECONDS)

    def _auth_headers(self):
        if self._token_expired():
            self._login()
        return {"Authorization": f"Bearer {self._token}"}

    # --- submission ---

    def submit(self, ajuste_type, payload):
        """POST a built (and ideally already locally-validated) payload for
        `ajuste_type` (one of AudespSubmission.AjusteTypeChoices, excluding
        DECLARACAO_NEGATIVA — use `submit_declaracao_negativa` for that).
        Returns `{"protocolo": str, "mensagem": str}`.
        """
        return self._submit_to(self._SUBMIT_PATHS[ajuste_type], payload)

    def submit_declaracao_negativa(self, payload):
        return self._submit_to(self._DECLARACAO_NEGATIVA_PATH, payload)

    def enviar_ajuste(self, payload):
        """POST a Fase IV payload — either an "ajuste" or an "empenho"
        shape (see audesp.builders.fase_iv), both accepted at this same
        endpoint per the manual's "Empenho is a sub-módulo of Ajuste" note.
        Returns `{"protocolo": str, "mensagem": str}`.
        """
        return self._submit_to(self._FASE_IV_AJUSTE_PATH, payload)

    def _submit_to(self, path, payload):
        response = self._request_with_retry(
            "POST",
            f"{self._base_url}{path}",
            headers=self._auth_headers(),
            files={
                "documentoJSON": (
                    "documento.json",
                    json.dumps(payload),
                    "application/json",
                )
            },
        )
        if response.status_code == 400:
            raise AudespValidationError(
                "AUDESP rejected the payload", errors=_safe_json(response)
            )
        self._raise_for_status(response)
        return response.json()

    # --- consulta ---

    def consulta(self, protocolo):
        """`GET /f5/consulta/{protocolo}` -> `{"status": str, "erros": [...]}`.
        Status values (manual §1.2.3): `Recebido` -> `Armazenado` (accepted)
        | `Rejeitado` (see `erros[]`, classificação Indicativo/Impeditivo)
        -> eventually `Substituído` (overwritten by retificação) or
        `Excluído` (cascaded exclusion from a retificação on an earlier
        exercício).
        """
        response = self._request_with_retry(
            "GET",
            f"{self._base_url}/f5/consulta/{protocolo}",
            headers=self._auth_headers(),
        )
        self._raise_for_status(response)
        return response.json()

    def consulta_fase_iv(self, protocolo):
        """`GET /f4/consulta/{protocolo}` -> same shape as `consulta`
        (Fase V's own status query); status vocabulary not yet confirmed
        against a live Fase IV response — see AUDESP_FASE_IV_AUDIT.md.
        """
        response = self._request_with_retry(
            "GET",
            f"{self._base_url}/f4/consulta/{protocolo}",
            headers=self._auth_headers(),
        )
        self._raise_for_status(response)
        return response.json()

    # --- retry/backoff ---

    def _request_with_retry(self, method, url, **kwargs):
        last_error = None
        for attempt in range(_MAX_RETRIES):
            try:
                return requests.request(method, url, timeout=_TIMEOUT_SECONDS, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_error = exc
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_BACKOFF_SECONDS * (2**attempt))
        raise AudespConnectionError(
            f"Could not reach AUDESP after {_MAX_RETRIES} attempts: {last_error}"
        ) from last_error

    def _raise_for_status(self, response):
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise AudespError(
                f"AUDESP request failed ({response.status_code}): {response.text}"
            ) from exc


def _safe_json(response):
    try:
        return response.json()
    except ValueError:
        return [{"message": response.text}]
