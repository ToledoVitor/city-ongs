---
name: sitts-deploy
description: What will bite you when deploying SITTS to GCP Cloud Run — the manual unguarded deploy, the IAM grant that fails looking like success, the setting that silently breaks password-reset emails, and the bucket split that must stay split. Use before editing the deploy workflow, changing Cloud Run flags, touching GCS/Secret Manager/IAM, moving the domain, or reasoning about image size and instance sizing.
---

# Deploying SITTS

Full reasoning lives in [`docs/DEPLOY.md`](../../../docs/DEPLOY.md) — project
inventory, IAM matrix, the instance-sizing benchmark, image-size analysis, and the
Artifact Registry policy. It's ~4.4k tokens and worth reading before any real
infra change. This skill is the subset that is irreversible or fails silently.

Project `sitts-504501`, region `southamerica-east1`, everything scale-to-zero on
a $15/mo budget. Three users. Infra decisions here optimise for *not* paying
fixed monthly charges — don't "fix" the absence of a load balancer or a VPC
connector without reading why they're absent.

## Before you dispatch

**There is no safety net.** `.github/workflows/production-deploy.yml` runs only on
manual `workflow_dispatch`, nothing validates it in CI, and step 4 sends **100% of
traffic** to the new revision. Quoting the doc: "the first real signal that an edit
works is a dispatch." A broken edit to that workflow is discovered in production.

**The rollback horizon is finite.** `production` and `latest` are *moving* tags, so
an image that served production 40 days ago is untagged today and eligible for
deletion. You can roll back to whichever is larger — the 5 most recent builds or
30 days. Not further. Raise `keepCount` / `olderThan` in
`.github/artifact-registry-cleanup-policy.json` *before* you need it.

**Migrations run before the deploy, as a separate job.** `sitts-pre-deploy` runs
`migrate` + `collectstatic`. A migration that fails leaves the old revision serving
and the schema half-moved — the usual Django caveats about backward-compatible
migrations apply, with no blue/green to hide behind.

## The three failures that look like success

**`artifactregistry.repoAdmin` on the repository.** The last workflow step moves
the `production` and `latest` tags onto the new image, and *moving* a tag means
deleting it first. `artifactregistry.writer` grants create but not
`artifactregistry.tags.delete`. So the **first** deploy into a fresh project
succeeds (no tags to delete yet) and **every deploy after it** fails on the final
step — after the Cloud Run service has already been updated. Grant `repoAdmin`
scoped to the repository, not the project.

**`WEBSITE_URL` after a domain change.** It lives in the `django_settings` secret
and builds the links in password-reset emails. Move the domain without updating it
and the app looks fine while every reset link points at the old host. This is
called out in the doc as "the one setting that silently breaks if forgotten."

**`iam.serviceAccountTokenCreator` on `sitts-run`, granted to itself.** Media URLs
are signed via the IAM `signBlob` API rather than a key file. Remove that
self-binding — it reads like a mistake in an IAM audit — and every file link in the
app breaks.

## Never merge the two buckets

`sitts-504501-static` is public and unsigned (CSS, JS, admin assets).
`sitts-504501-media` is private with 15-minute signed URLs (uploads).

They were one bucket once, with `GS_QUERYSTRING_AUTH = False`. Unsigned URLs only
work on a world-readable bucket, and `storage.objectViewer` on `allUsers` also
grants `storage.objects.list` — so anyone who learned the bucket name could
enumerate and download every contract, bank statement, and accountability
attachment in a system that also stores CPF. Consolidating the buckets, or turning
off `querystring_auth` on media, recreates that hole exactly.

Known limit, not yet fixed: a signed URL is bearer access for its lifetime and
nothing checks that the requester belongs to the tenant owning the file. Serving
uploads through a permission-checked Django view is the real fix.

## Cloud SQL

`sitts-db` is POSTGRES_16, `db-f1-micro`, **zonal** (no HA — that's an exact 2x on
the bill), 7 daily backups, public IP with zero authorized networks, reached
through the built-in Cloud SQL connector.

Deletion protection is on. Deleting requires clearing it first:

```bash
gcloud sql instances patch sitts-db --project=sitts-504501 --no-deletion-protection
```

## Instance flags are pinned in the workflow on purpose

`--cpu=1 --memory=1Gi --execution-environment=gen1 --concurrency=4 --timeout=300`,
with `--min-instances=0 --max-instances=2 --cpu-throttling`. They're set in the
workflow rather than left to the service's stored config so a console edit can't
silently reintroduce always-on billing.

Two traps if you change them:

- **Below 1 vCPU, Cloud Run forces concurrency to 1.** Fractional CPU looks cheaper and isn't: with `--max-instances=2` the whole service would cap at two in-flight requests.
- **`--concurrency=4` matches the 4 gunicorn threads** in the dockerfile, and that thread count is also the per-instance Postgres connection ceiling (`CONN_MAX_AGE`). `2 instances x 4 threads` = at most 8 connections. Re-check against `max_connections` if either moves.

The 1Gi tier is justified by a benchmark in the doc (peak ~342 MiB rendering all
17 reports). Two honest caveats the doc states: that peak is **serial**, and the
concurrent-render figure that actually governs the tier is inferred, not measured.

## Threads are newer than some of the code

The image used to run a single synchronous worker, so nothing had to be
thread-safe. Two spots hold process-global state now shared across 4 threads.
Neither is known to misbehave; both matter before raising the thread count:

- `contracts/views.py` calls `locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")` inside request handlers. `setlocale` is process-wide, not thread-local. Benign only because the image sets `LC_ALL=pt_BR.UTF-8`, so every thread writes the same value.
- `reports/exporters/base.py` keeps live exporters in a class-level `weakref.WeakSet` and exposes `cleanup_all()`, which would close PDFs belonging to other threads' in-flight requests. Nothing calls it today.

## Retention policy is applied by hand

Not by the workflow, deliberately: the deploy SA lacks
`artifactregistry.repositories.update`, retention changes are rare while deploys
are frequent, and a wrong delete policy costs unrecoverable images while a failed
deploy only costs a release.

Always `--dry-run` first, review the matches in Cloud Logging, then `--no-dry-run`.
Exact commands are in `docs/DEPLOY.md` §"Applying it". The command is declarative
and replaces stored policies, so it's safe to re-run.

## Don't reintroduce these

Each is a fixed monthly charge that buys nothing at three users, and each was
removed on purpose: a global external load balancer (~$18-25/mo for the forwarding
rule alone), a Serverless VPC Access connector (~$15-20/mo, only needed if Cloud
SQL moves to private IP), Cloud SQL HA, and App Engine (`app.yaml` targeted Flex,
which runs always-on VMs and can't scale to zero).

`www.sitts.com.br` uses a **Cloud Run domain mapping**, not a load balancer — free,
auto-provisioned certificate, lower availability SLO, and the right trade here.
Only `www` is mapped; the apex forwards from Hostinger to keep one canonical host
for cookies and sessions.

## Image size is cold-start latency

With `--min-instances=0` the image is pulled on nearly every cold start.

`psycopg2-binary` is deliberately **not** used even though it would remove the
builder stage: the binary wheel bundles its own libssl, this image already loads
`cryptography` in the same process, and that's the collision psycopg upstream
warns about. The builder stage costs build time, not image size.

Watch for a dependency declared twice into the same import path — `psycopg2` vs
`psycopg2-binary` and `phonenumbers` vs `django-phonenumber-field[phonenumberslite]`
each cost real MB while install-order decided which won. Removing the redundant
halves took the image from 497 MB to 444 MB.
