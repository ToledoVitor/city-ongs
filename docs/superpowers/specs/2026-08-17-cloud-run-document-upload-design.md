# Cloud Run Document Upload Recovery Design

## Context

Production document uploads fail after storing a file because private media URL
generation tries to sign with Cloud Run's token-only credentials. Issue #80
contains production evidence and root-cause analysis. Historical production data
cleanup is explicitly outside this change.

## Design

Private media storage will enable django-storages' IAM `signBlob` mode while
keeping the bucket private, query-string authentication enabled, and the existing
15-minute expiry. Runtime service-account permissions remain infrastructure
prerequisites documented in `docs/DEPLOY.md`; this PR does not mutate production
IAM.

Bulk upload will become all-or-nothing for rows created by one request. File
validation remains before writes. Creation and response serialization run inside
a database transaction so signed-URL failures roll back every new row. Because
GCS is not transactional, the endpoint records each successfully created model
and explicitly deletes its blob when any later creation or serialization step
fails. Cleanup failures are logged without replacing the original response.

The endpoint will return a short JSON 500 error after cleanup. Upload JavaScript
will also guard JSON decoding so an HTML error from Cloud Run or another proxy
never exposes `Unexpected token '<'` to users. Existing 4xx messages remain
unchanged when valid JSON is returned.

## Verification

- Token-only credentials receive `service_account_email` and `access_token`
  through django-storages' IAM signing path.
- A signed-URL failure during a multi-file request returns JSON, rolls back all
  new `ExpenseFile` rows, and removes all blobs created by that request.
- Successful multi-file upload remains a JSON 201 response.
- Non-JSON upload responses map to `Não foi possível enviar os documentos. Tente
  novamente.`
- Repository checks and full sqlite test suite pass before PR creation.
