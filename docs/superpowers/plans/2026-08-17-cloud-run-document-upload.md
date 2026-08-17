# Cloud Run Document Upload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore private document uploads on Cloud Run without partial batch writes or raw JSON parser errors.

**Architecture:** Enable django-storages IAM signing in shared production media options. Keep request-scoped database writes atomic and explicitly delete created blobs on failure. Guard browser JSON decoding at the upload boundary.

**Tech Stack:** Django 5, django-storages 1.14.6, Google Cloud Storage, server-rendered JavaScript, unittest.

## Global Constraints

- Keep media bucket private and signed URL expiry at 15 minutes.
- Do not mutate production IAM or clean historical production test data.
- User-facing copy stays Portuguese, sentence case, and concise.
- Follow red-green-refactor for behavior changes.

---

### Task 1: IAM media signing

**Files:**
- Modify: `core/settings.py`
- Test: `accountability/tests.py`

**Interfaces:**
- Consumes: django-storages `GoogleCloudStorage(iam_sign_blob=True)`.
- Produces: `GCS_MEDIA_STORAGE_OPTIONS`, used by production `STORAGES` and tests.

- [ ] **Step 1: Write failing token-only credential test**

Create storage from `GCS_MEDIA_STORAGE_OPTIONS`, call `storage.url()`, and assert
`Blob.generate_signed_url()` receives `service_account_email` and `access_token`.

- [ ] **Step 2: Verify red**

Run: `make test-sqlite TEST=accountability.tests.CloudStorageConfigurationTests`

Expected: FAIL because production options do not enable IAM signing.

- [ ] **Step 3: Enable IAM signing**

Add `"iam_sign_blob": True` to reusable private-media options and wire those
options into `STORAGES["default"]`.

- [ ] **Step 4: Verify green**

Run same focused test. Expected: PASS.

### Task 2: Atomic upload cleanup and JSON response

**Files:**
- Modify: `accountability/views.py`
- Test: `accountability/tests.py`

**Interfaces:**
- Consumes: `_serialize_expense_document(document)` and `db_transaction.atomic()`.
- Produces: `_delete_expense_document_files(documents)` cleanup helper and JSON 500 contract.

- [ ] **Step 1: Write failing rollback test**

Patch storage URL generation to fail after file creation. Post two valid files.
Assert status 500, JSON generic error, zero new rows, and empty media directory.

- [ ] **Step 2: Verify red**

Run focused rollback test. Expected: FAIL with propagated/HTML 500 and persisted first file.

- [ ] **Step 3: Implement transaction and blob cleanup**

Create and serialize documents inside `db_transaction.atomic()`. On exception,
delete every recorded file, log original failure, and return:

```python
JsonResponse(
    {"error": "Não foi possível enviar os documentos. Tente novamente."},
    status=500,
)
```

- [ ] **Step 4: Verify green**

Run focused upload tests. Expected: PASS.

### Task 3: Browser-safe upload errors

**Files:**
- Modify: `templates/accountability/expenses/document-workspace.html`
- Test: `accountability/tests.py`

**Interfaces:**
- Consumes: Fetch `Response`.
- Produces: `parseJsonResponse(response, fallbackMessage)`.

- [ ] **Step 1: Add failing rendered-template assertion**

Assert upload workspace includes stable fallback copy and guarded parser call.

- [ ] **Step 2: Verify red**

Run focused workspace render test. Expected: FAIL because guarded parser is absent.

- [ ] **Step 3: Add guarded parser**

Catch JSON decoding errors and throw fallback message. Use it for upload responses.

- [ ] **Step 4: Verify green**

Run focused workspace test. Expected: PASS.

### Task 4: Verification and PR

**Files:**
- Modify: plan checkboxes as work completes.

**Interfaces:**
- Consumes: completed tasks.
- Produces: verified commit and separate pull request against `main`.

- [ ] **Step 1: Run focused accountability tests**
- [ ] **Step 2: Run `make check`, `make test-sqlite`, and `make audit-templates`**
- [ ] **Step 3: Review diff against `main`**
- [ ] **Step 4: Commit, push branch, and open PR linking issue #80**
