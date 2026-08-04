# Deploy

## Production

`.github/workflows/production-deploy.yml`, triggered manually via `workflow_dispatch`. Nothing else triggers it, and no CI check validates changes to it — the first real signal that an edit works is a dispatch.

What one run does:

1. Authenticates to GCP through Workload Identity Federation as `github-deploy@sitts-project.iam.gserviceaccount.com`.
2. Builds the image and pushes it to Artifact Registry under a timestamped tag.
3. Runs `migrate` and `collectstatic` as the `sitts-pre-deploy` Cloud Run job, reading config from the `django_settings` secret.
4. Deploys to the `sitts` Cloud Run service with 100% traffic to the new revision.
5. Moves the `production` and `latest` tags onto the image it just built.

The Cloud Run scaling flags are pinned in the workflow rather than left to the service's stored config, so an edit in the console cannot silently reintroduce always-on billing.

## Instance sizing

`--cpu=1 --memory=512Mi --execution-environment=gen1 --concurrency=8 --timeout=300`, on top of `--min-instances=0 --max-instances=2 --cpu-throttling`.

### Why 512Mi

Measured, not guessed. A benchmark boots the real production image, builds the WSGI app, and renders all 17 reports against a contract carrying 20,000 expenses and 20,000 revenues — far past anything in production today:

| stage | RSS |
|---|---|
| idle worker (WSGI app built, before first request) | ~108 MiB |
| after the URLconf resolves | ~159 MiB |
| peak, rendering all 17 reports twice | ~342 MiB |

512Mi leaves ~170 MiB over that peak. 256Mi and 384Mi are both under it, so 512Mi is the smallest tier that fits. If the footprint ever drops meaningfully, gen1 does allow going below 512Mi — gen2 does not.

Two things move that number:

- **pandas + numpy cost ~95 MiB resident** and are needed only by the XLSX *upload* path. `accountability/xlsx/__init__.py` defers that import (PEP 562 module `__getattr__`) so a worker that never handles an upload never pays it. That lowers the *floor* — RSS after URLconf resolution went from ~202 MiB to ~159 MiB — but not the peak, which is dominated by report rendering rather than by imports.
- **Report rendering churns memory the allocator only partly returns to the OS**, so a long-lived worker drifts upward. `--max-requests 400` in the dockerfile recycles the worker and puts a floor under the drift.

One caveat on that peak: it is RSS sampled in-process, not an observed OOM. Nobody has yet run the suite under a hard 256Mi/384Mi cgroup cap to find where it actually dies. 512Mi is sized from measured peak plus headroom — the conservative direction — but the empirical floor is still unverified.

### Why 1 vCPU, and not less

Cloud Run allows fractional CPU down to 0.08, which looks like the cheaper choice and is not: **below 1 vCPU, maximum concurrency is forced to 1**. Every simultaneous request would then need its own instance, and `--max-instances=2` would cap the entire service at two in-flight requests. Under request-based billing one shared instance is both cheaper and faster.

### Why gen1

gen2 buys full Linux compatibility that nothing here needs, boots slower, and floors memory at 512Mi. With `--min-instances=0` almost every request pays a cold start, so startup latency is the thing worth optimising.

### Concurrency and threads

`--concurrency=8` sits against the 4 gunicorn threads configured in the dockerfile. Mild queueing on one instance is cheaper than spinning up a second. The thread count is also the per-instance database connection ceiling: Django holds one Postgres connection per thread (`CONN_MAX_AGE` in `core/settings.py`), so `max-instances=2 x 4 threads` is at most 8 connections against the database — worth re-checking against `max_connections` if either number changes.

`--timeout=300` bounds how long a wedged request can keep an instance billable. gunicorn's own `--timeout 0` is deliberate: Cloud Run enforces the real limit, and a large PDF export can legitimately run long.

## Image size

With `--min-instances=0` the image is pulled on essentially every cold start, so its size is latency (and billed startup time), not just registry storage.

Two dependencies were declared twice in ways that silently inflated it. Both wheels in each pair install into the *same* import path, so which one won was install-order luck, and uninstalling either could delete files the other still claimed:

- `psycopg2` **and** `psycopg2-binary` — same `psycopg2/` package. The source build won in practice, leaving ~11 MB of the binary wheel's bundled libpq/libssl unused in the image.
- `phonenumbers` **and** `django-phonenumber-field[phonenumberslite]` — same `phonenumbers/` package. The explicit `phonenumbers` pin dragged back the 38 MB of geocoding/carrier metadata the `lite` extra exists to avoid, *and* pinned an older version over the newer one.

Dropping the redundant halves took the image from 497 MB to 444 MB with no behaviour change.

`psycopg2-binary` is the one that looks tempting to keep, because it would remove the builder stage entirely. It is deliberately not used: the binary wheel bundles its own libssl, this image already loads `cryptography` in the same process, and that is the collision psycopg upstream warns about. The builder stage costs build time, not image size.

Note for local development on macOS: building `psycopg2` from source needs `pg_config` on `PATH` (`brew install libpq`).

## Artifact Registry retention

Every dispatch pushes a new timestamped image and Artifact Registry bills per GB stored, so the repository needs a retention policy or the cost grows without bound. The policy lives at `.github/artifact-registry-cleanup-policy.json`:

- `keep-tagged-releases` — never delete anything tagged `production` or `latest`.
- `keep-5-most-recent` — never delete the 5 newest versions.
- `delete-stale-timestamped-builds` — delete anything older than 30 days.

Keep rules take precedence over Delete rules, so the first two bound the third.

### This policy is applied by hand, not by the deploy workflow

Deliberate, for three reasons:

- **IAM.** Setting a cleanup policy needs `artifactregistry.repositories.update`. The deploy service account needs only image push plus Cloud Run deploy, and `roles/artifactregistry.writer` does not include repository update. Wiring the step into the workflow would either fail every deploy with `PERMISSION_DENIED` or force granting the CI identity admin over the production registry — a permission expansion for no operational gain.
- **Cadence.** Retention config changes almost never; deploys are frequent. Re-asserting the policy on every run buys nothing, and it means a bad edit to the JSON becomes a live delete policy on the next deploy with no separate review.
- **Blast radius.** A failed deploy costs a release. A wrong delete policy costs images that cannot be recovered. Those two failure modes deserve different gates.

### Applying it

Run from a machine authenticated as an account with registry admin on `sitts-project` (the deploy service account does not have it — see above). Note that the active `gcloud` project is probably not `sitts-project`, hence the explicit `--project`.

Arm it in dry-run mode first. Policies are evaluated and the matches are logged, but nothing is deleted:

```bash
gcloud artifacts repositories set-cleanup-policies cloud-run-source-deploy --project=sitts-project --location=southamerica-east1 --policy=.github/artifact-registry-cleanup-policy.json --dry-run
```

Review what it would have removed in Cloud Logging before going further. Once the matches look right, make it live:

```bash
gcloud artifacts repositories set-cleanup-policies cloud-run-source-deploy --project=sitts-project --location=southamerica-east1 --policy=.github/artifact-registry-cleanup-policy.json --no-dry-run
```

Confirm what the repository ended up with:

```bash
gcloud artifacts repositories describe cloud-run-source-deploy --project=sitts-project --location=southamerica-east1
```

Re-run the same command after editing the JSON — it is declarative and replaces the stored policies, so it is safe to apply repeatedly.

### Rollback horizon

`production` and `latest` are moving tags: a new deploy takes them off the previous image. An image that served production 40 days ago is therefore untagged today and eligible for deletion, because only the *current* `production` image is protected by `keep-tagged-releases`.

The effective rollback window is whichever is larger — the 5 most recent builds, or 30 days. If a release cadence ever needs to roll back further than that, raise `keepCount` or `olderThan` before it matters, not after.
