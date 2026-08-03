# Deploy

## Production

`.github/workflows/production-deploy.yml`, triggered manually via `workflow_dispatch`. Nothing else triggers it, and no CI check validates changes to it — the first real signal that an edit works is a dispatch.

What one run does:

1. Authenticates to GCP through Workload Identity Federation as `github-deploy@sitts-project.iam.gserviceaccount.com`.
2. Builds the image and pushes it to Artifact Registry under a timestamped tag.
3. Runs `migrate` and `collectstatic` as the `sitts-pre-deploy` Cloud Run job, reading config from the `django_settings` secret.
4. Deploys to the `sitts` Cloud Run service with 100% traffic to the new revision.
5. Moves the `production` and `latest` tags onto the image it just built.

The Cloud Run scaling flags are pinned in the workflow (`--min-instances=0 --max-instances=2 --cpu-throttling`) rather than left to the service's stored config, so an edit in the console cannot silently reintroduce always-on billing.

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
