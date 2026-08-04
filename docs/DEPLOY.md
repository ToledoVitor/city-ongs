# Deploy

## Production

`.github/workflows/production-deploy.yml`, triggered manually via `workflow_dispatch`. Nothing else triggers it, and no CI check validates changes to it — the first real signal that an edit works is a dispatch.

What one run does:

1. Authenticates to GCP through Workload Identity Federation as `github-deploy@sitts-504501.iam.gserviceaccount.com`.
2. Builds the image and pushes it to Artifact Registry under a timestamped tag.
3. Runs `migrate` and `collectstatic` as the `sitts-pre-deploy` Cloud Run job, reading config from the `django_settings` secret.
4. Deploys to the `sitts` Cloud Run service with 100% traffic to the new revision.
5. Moves the `production` and `latest` tags onto the image it just built.

The Cloud Run scaling flags are pinned in the workflow rather than left to the service's stored config, so an edit in the console cannot silently reintroduce always-on billing.

## What exists in GCP

Project `sitts-504501` (number `665645565019`), everything in `southamerica-east1`. The previous project was deleted; this is a rebuild.

| Resource | Name | Notes |
|---|---|---|
| Cloud SQL | `sitts-db` | POSTGRES_16, `db-f1-micro`, **zonal**, 10GB SSD, public IP, 7 daily backups |
| Cloud Run service | `sitts` | scale-to-zero |
| Cloud Run job | `sitts-pre-deploy` | `migrate` + `collectstatic` |
| Artifact Registry | `cloud-run-source-deploy` | cleanup policy applied |
| GCS | `sitts-504501-static` | **public** — CSS/JS/admin assets |
| GCS | `sitts-504501-media` | **private** — uploads, signed URLs |
| Secret Manager | `django_settings` | all runtime config |
| Runtime SA | `sitts-run@…` | Cloud Run identity |
| Deploy SA | `github-deploy@…` | assumed by GitHub Actions via WIF |

### IAM the workflow actually needs

`github-deploy` holds `run.admin` and `artifactregistry.writer` at project level, `iam.serviceAccountUser` on `sitts-run`, and **`artifactregistry.repoAdmin` on the repository**.

That last one is not optional and fails in a way that looks like success. The final step moves the `production` and `latest` tags onto the new image, and *moving* an existing tag means deleting it first — `artifactregistry.writer` grants create but not `artifactregistry.tags.delete`. So the very first deploy into a fresh project passes (no tags exist yet) and every deploy after it fails on the last step, after the service has already been updated. Granting `repoAdmin` on the repository rather than the project keeps it scoped.

`sitts-run` holds `cloudsql.client`, `logging.logWriter`, `storage.objectAdmin` on both buckets, `secretmanager.secretAccessor` on `django_settings`, and `iam.serviceAccountTokenCreator` **on itself** for signing media URLs.

The Cloud Run service is `--allow-unauthenticated`: it has to be anonymously reachable or nobody can load the login page. Django's own authentication protects the content.

Deliberately **absent**, because each is a fixed monthly charge that buys nothing at this traffic:

- **No load balancer.** The `.run.app` URL is the entry point. A global external ALB costs ~$18-25/mo for the forwarding rule alone, before traffic; Cloud Run domain mapping is the free alternative if a custom domain is needed.
- **No Serverless VPC Access connector.** Cloud SQL has a public IP with *zero* authorized networks, and Cloud Run reaches it through the built-in Cloud SQL connector (`--add-cloudsql-instances`), which is IAM-authenticated and free. Switching the instance to private IP would force a connector back in at ~$15-20/mo.
- **No HA / regional availability.** That is an exact 2x on the Cloud SQL bill.
- **No App Engine.** The old `app.yaml` targeted App Engine Flex, which runs always-on VMs and does not scale to zero.

A billing budget of $15/mo is set on the billing account with alerts at 50%, 80% and 100%. Cloud SQL is the only meaningful line item — everything else lands under ~$1/mo combined.

Cloud SQL has **deletion protection enabled**. To actually delete the instance you must clear it first:

```bash
gcloud sql instances patch sitts-db --project=sitts-504501 --no-deletion-protection
```

## Custom domain

`www.sitts.com.br`, served through a **Cloud Run domain mapping**. It costs nothing and provisions a Google-managed certificate automatically.

The alternative is a global external Application Load Balancer, which is what most Cloud Run documentation steers you toward. Its forwarding rule alone is roughly $18-25/mo before a single request — more than the entire rest of this project's infrastructure combined, for a service handling three users. Domain mapping carries a lower availability SLO and Google treats it as legacy, but at this scale that is the correct trade.

Domain mappings *are* supported in `southamerica-east1`, despite the region gaps in Google's own docs. Verified by attempting one: the failure was ownership verification, not region.

### Bringing up a domain

1. Verify ownership in Google Search Console. `gcloud domains verify sitts.com.br` opens the right page; the TXT record it asks for goes in Hostinger's DNS. Verify the **apex**, not `www` — the apex covers every subdomain.
2. `gcloud beta run domain-mappings create --service=sitts --domain=www.sitts.com.br --region=southamerica-east1`.
3. Add the DNS records that command prints, at Hostinger. For a subdomain it is a single `CNAME` to `ghs.googlehosted.com.`
4. Wait for the certificate. Usually ~15 minutes, occasionally hours. `gcloud beta run domain-mappings describe` reports status.

Only `www` is mapped. The apex is handled by Hostinger's own domain forwarding to `https://www.sitts.com.br`, which avoids pinning Google's four A records at the apex and keeps one canonical host for cookies and sessions.

After DNS resolves, `WEBSITE_URL` in the `django_settings` secret must move to the new domain — it builds the links in password-reset emails, so it is the one setting that silently breaks if forgotten.

## Reaching a running deployment

Cloud Run has no SSH and no exec. There are three ways in; which one you want depends on whether you need the production *container* or just the production *database*.

### 1. A one-off management command

Runs inside the real image with the real `django_settings` secret. This is the right tool for `migrate`, `showmigrations`, `createsuperuser`, or a data fix that must see production config.

It works by overriding the arguments of the existing pre-deploy job:

```bash
gcloud beta run jobs execute sitts-pre-deploy \
  --project=sitts-504501 --region=southamerica-east1 \
  --args="-c" \
  --args="set -o allexport; source /secrets/DJANGO_SETTINGS; set +o allexport; python manage.py showmigrations" \
  --wait
```

`beta` is required — `--args` override does not exist on the GA `gcloud run jobs execute`. Note this is strictly non-interactive: no `manage.py shell`, and any command that prompts will hang until the task timeout. Output goes to Cloud Logging, not your terminal.

### 2. An interactive Django shell against the production database

Cloud Run cannot give you one, but the Cloud SQL Auth Proxy plus a local checkout can. Start the tunnel:

```bash
./cloud-sql-proxy sitts-504501:southamerica-east1:sitts-db --port 5433 --token "$(gcloud auth print-access-token)"
```

`--token` is not optional in practice. The proxy defaults to Application Default Credentials, which are a *separate* credential from your `gcloud` CLI login and go stale independently — the symptom is `invalid_grant / reauth related error (invalid_rapt)` and a connection that closes immediately. Passing the CLI's own access token sidesteps the whole problem. The token lasts about an hour.

Then pull the production config and point a local Django at the tunnel:

```bash
gcloud secrets versions access latest --secret=django_settings --project=sitts-504501 > /tmp/prod.env
```

```bash
PYTHONPATH="$PWD" DEVELOPMENT=true DEBUG=false SECRET_KEY=unused \
DB_NAME=sitts DB_USER=sitts DB_PASSWORD="$(grep '^DB_PASSWORD=' /tmp/prod.env | cut -d= -f2-)" \
DB_HOST=127.0.0.1 DB_PORT=5433 STATIC_URL=/static/ GS_BUCKET_NAME=sitts-504501-media \
uv run python manage.py shell
```

Four things to be careful about:

- **This is production data.** There is no undo, and `db-f1-micro` restores are not fast.
- `DEVELOPMENT=true` only changes *where settings come from* — env instead of Secret Manager. It does not point anything at a local database. The tunnel is what decides that.
- `GS_BUCKET_NAME` above is the real bucket. Anything that writes a `FileField` touches production storage.
- Delete `/tmp/prod.env` when you are done; it holds the database password and `SECRET_KEY`.

### 3. Raw psql

Same tunnel, no Django:

```bash
psql -h 127.0.0.1 -p 5433 -U sitts -d sitts
```

## Creating the first superuser

`manage.py createsuperuser` does not work on this model and the `superuser` Makefile target must not be used against a real environment — it hardcodes a known password.

Three model constraints make this less mechanical than usual:

- `USERNAME_FIELD` is `email`, and `organization` is a non-nullable FK that `REQUIRED_FIELDS` does not include, so the interactive command cannot supply it.
- A `User` needs an `Organization`, which needs a `CityHall`. Both must exist first.
- `User.save()` calls `clean()` directly, which requires **exactly one** of `cpf` or `cnpj`. This is not skippable via `full_clean(exclude=...)` — the check runs on every save.

So the account has to be built explicitly: create the `CityHall`, create the `Organization`, then construct the `User` with `organization`, one of `cpf`/`cnpj`, `is_staff`, `is_superuser`, and `set_password()`.

Leave `password_redefined=False`. `ForcePasswordChangeMiddleware` then redirects the account to `/auth/force-password-change/` until the password is changed, which makes any generated bootstrap password single-use.

## Storage: two buckets, on purpose

Uploads and static assets are split, and they must stay split.

Templates render `{{ obj.file.url }}` directly, so whatever the storage backend returns *is* the link handed to the browser. Before the split there was one bucket with `GS_QUERYSTRING_AUTH = False`, meaning unsigned URLs — which only work if the bucket is world-readable. `roles/storage.objectViewer` on `allUsers` also grants `storage.objects.list`, so that configuration would have let anyone who learned the bucket name enumerate and download every contract, bank statement and accountability attachment in the system, on a product that also stores CPF.

Now:

- `sitts-504501-static` is public and unsigned. It holds CSS, JS and Django admin assets. Nothing sensitive, and unsigned URLs stay cacheable.
- `sitts-504501-media` is private. `querystring_auth` is on, so every URL is signed and expires after 15 minutes.

Signing from Cloud Run uses the IAM `signBlob` API rather than a service-account key file, which is why `sitts-run` holds `roles/iam.serviceAccountTokenCreator` **on itself**. Remove that binding and every file link in the app breaks.

Note what this does *not* do: a signed URL is bearer access for its lifetime, and nothing checks that the requester belongs to the tenant that owns the file. Serving uploads through a permission-checked Django view is the real fix if the threat model tightens.

## Instance sizing

`--cpu=1 --memory=1Gi --execution-environment=gen1 --concurrency=4 --timeout=300`, on top of `--min-instances=0 --max-instances=2 --cpu-throttling`.

### Why 1Gi

A benchmark boots the real production image, builds the WSGI app, and renders all 17 reports against a contract carrying 20,000 expenses and 20,000 revenues — far past anything in production today:

| stage | RSS |
|---|---|
| idle worker (WSGI app built, before first request) | ~108 MiB |
| after the URLconf resolves | ~159 MiB |
| peak, rendering all 17 reports twice | ~342 MiB |

**That peak is a serial figure — one report at a time.** The service runs 4 gunicorn threads in a single process, so two design partners exporting large reports at the same moment share one heap. On the 512Mi tier the ~170 MiB of apparent headroom is consumed by the second concurrent render, and the failure mode is an OOM kill: the instance dies, the request returns 503, and nothing is written to Cloud Logging.

1Gi is chosen because the smaller tier optimises a number that is already zero. Cloud Run's free tier covers 360,000 GiB-seconds per month; at three concurrent users this service uses a low single-digit percentage of it, so 512Mi and 1Gi bill identically. Sizing tightly buys nothing and costs availability.

Two things move the underlying number:

- **pandas + numpy cost ~95 MiB resident** and are needed only by the XLSX *upload* path. `accountability/xlsx/__init__.py` defers that import (PEP 562 module `__getattr__`) so a worker that never handles an upload never pays it. That lowers the *floor* — RSS after URLconf resolution went from ~202 MiB to ~159 MiB — but not the peak, which is dominated by report rendering rather than by imports.
- **Report rendering churns memory the allocator only partly returns to the OS**, so a long-lived worker drifts upward. `--max-requests 400` in the dockerfile recycles the worker and puts a floor under the drift.

Two caveats on the peak. It is RSS sampled in-process, not an observed OOM — nobody has run the suite under a hard cgroup cap to find where it actually dies. And it has only ever been measured single-threaded; the concurrent-render peak that actually governs the tier is inferred, not measured. Measuring it is the obvious next step if the tier is ever revisited.

### Why 1 vCPU, and not less

Cloud Run allows fractional CPU down to 0.08, which looks like the cheaper choice and is not: **below 1 vCPU, maximum concurrency is forced to 1**. Every simultaneous request would then need its own instance, and `--max-instances=2` would cap the entire service at two in-flight requests. Under request-based billing one shared instance is both cheaper and faster.

### Why gen1

gen2 buys full Linux compatibility that nothing here needs, boots slower, and floors memory at 512Mi. With `--min-instances=0` almost every request pays a cold start, so startup latency is the thing worth optimising.

This one is an assumption carried from the general case rather than a measurement against this image. If cold starts turn out to be the dominant complaint from design partners, time a gen2 revision before assuming gen1 is the faster of the two.

### Concurrency and threads

`--concurrency=4` matches the 4 gunicorn threads configured in the dockerfile. Dispatching more requests than the process can actually run in parallel does not add throughput — the surplus parks in the kernel socket backlog, where Cloud Run's autoscaler cannot see it and gunicorn's `--timeout 0` does not bound it. Matching the two also makes the memory ceiling deterministic: at most four concurrent report renders per instance, which is what the tier in *Why 1Gi* is sized against.

The thread count is also the per-instance database connection ceiling: Django holds one Postgres connection per thread (`CONN_MAX_AGE` in `core/settings.py`), so `max-instances=2 x 4 threads` is at most 8 connections against the database — worth re-checking against `max_connections` if either number changes.

`--timeout=300` bounds how long a wedged request can keep an instance billable. gunicorn's own `--timeout 0` is deliberate: Cloud Run enforces the real limit, and a large PDF export can legitimately run long.

### Threads are new, and some module state predates them

Before this configuration the image ran a single synchronous worker, so nothing in the codebase had to be thread-safe. Two places hold process-global state that is now shared across four request threads. Neither is known to misbehave today; both are worth remembering before raising the thread count:

- `contracts/views.py` calls `locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")` inside request handlers. `setlocale` mutates process-wide state, not thread-local state. It is benign here only because the image already sets `LC_ALL=pt_BR.UTF-8`, so every thread writes the identical value.
- `reports/exporters/base.py` tracks live exporters in a class-level `weakref.WeakSet` and exposes `cleanup_all()`, which would close PDFs belonging to other threads' in-flight requests. Nothing calls it today.

### If the database ever moves off Cloud SQL

`CONN_MAX_AGE=60` assumes a direct connection. Behind a transaction-mode pooler (PgBouncer, Supabase's Supavisor) persistent connections and server-side cursors both break: set `CONN_MAX_AGE=0` and `DISABLE_SERVER_SIDE_CURSORS=True`, or use the pooler's session-mode port.

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

Run from a machine authenticated as an account with registry admin on `sitts-504501` (the deploy service account does not have it — see above). Note that the active `gcloud` project is probably not `sitts-504501`, hence the explicit `--project`.

Arm it in dry-run mode first. Policies are evaluated and the matches are logged, but nothing is deleted:

```bash
gcloud artifacts repositories set-cleanup-policies cloud-run-source-deploy --project=sitts-504501 --location=southamerica-east1 --policy=.github/artifact-registry-cleanup-policy.json --dry-run
```

Review what it would have removed in Cloud Logging before going further. Once the matches look right, make it live:

```bash
gcloud artifacts repositories set-cleanup-policies cloud-run-source-deploy --project=sitts-504501 --location=southamerica-east1 --policy=.github/artifact-registry-cleanup-policy.json --no-dry-run
```

Confirm what the repository ended up with:

```bash
gcloud artifacts repositories describe cloud-run-source-deploy --project=sitts-504501 --location=southamerica-east1
```

Re-run the same command after editing the JSON — it is declarative and replaces the stored policies, so it is safe to apply repeatedly.

### Rollback horizon

`production` and `latest` are moving tags: a new deploy takes them off the previous image. An image that served production 40 days ago is therefore untagged today and eligible for deletion, because only the *current* `production` image is protected by `keep-tagged-releases`.

The effective rollback window is whichever is larger — the 5 most recent builds, or 30 days. If a release cadence ever needs to roll back further than that, raise `keepCount` or `olderThan` before it matters, not after.
