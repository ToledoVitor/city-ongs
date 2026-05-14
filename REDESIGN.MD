# UI Refactor Tracker

Working checklist for the SITTS UI redesign. Every HTML template the project ships is listed below; we tick each entry as it lands the new design system.

> [`DESIGN.md`](./DESIGN.md) is the bible. This file is the living progress board.

## Ground rules

1. **DESIGN.md wins ties.** Any disagreement between a request and this tracker is resolved by DESIGN.md.
2. **The design system primitives live in `templates/ui/`.** Prefer reusing them (`ui/button.html`, `ui/text_input.html`, etc.) over re-writing the chrome inline.
3. **The shell is `templates/base.html`.** All authenticated pages extend it; do not introduce a parallel shell.
4. **Black-and-white duet, pill geometry, sentence-case copy.** No blue/indigo/purple gradients, no all-caps headlines, no novel accent colors.
5. **Status markers:**
   - `[x]` — refactored & verified in browser
   - `[~]` — partial / in progress (note what's missing)
   - `[ ]` — untouched (still using legacy Tailwind/Flowbite/gradient chrome)
6. **Mark items only after you've checked them in the browser at desktop + mobile**, with no console errors.
7. **When something is verified, update the entry in this file as part of the same change.** Don't let the tracker drift.

## Refactor recipe (the path of least surprise)

For each page:

1. Read the current template top-to-bottom. Note: data-attrs (Flowbite hooks), CSRF, URL reversals, conditional blocks, JS hooks.
2. Replace Tailwind chrome with design-system primitives (`ui/*` includes + tokens from `ui/_styles.html`).
3. Drop blue / indigo / purple / red / green color classes. Map to ink / canvas / canvas-soft / on-dark.
4. Use sentence-case for every heading & button label. No `font-extrabold`; use `var(--font-display)` weight 700.
5. Pills (`var(--rounded-pill)`) for buttons & chips; `var(--rounded-xl)` for cards.
6. Validate via curl + browser walkthrough (desktop + mobile).
7. Tick the box in this file.

## Foundation — design system primitives

These power everything else. They were created up-front and are part of "done" by definition.

- [x] `templates/ui/_styles.html` — design tokens (colors, type, radius, spacing, elevation) + base utility classes
- [x] `templates/ui/_scripts.html` — JS runtime (password toggle, toast queue)
- [x] `templates/ui/wordmark.html` — brand mark, supports `on_dark`
- [x] `templates/ui/button.html` — pill button (primary/secondary/subtle/floating/ghost, sm/md/lg)
- [x] `templates/ui/text_input.html` — labeled text input with hint / error
- [x] `templates/ui/password_input.html` — password input with eye toggle
- [x] `templates/ui/text_link.html` — inline link (default/muted/mute-soft/on-dark/blue)
- [x] `templates/ui/toast.html` — server-rendered toast trigger (queued into runtime)
- [x] `templates/ui/card.html` — card surface (default/soft/softer/dark, sm/md/lg/flush)
- [x] `templates/ui/badge.html` — pill badge / chip
- [x] `templates/ui/alert.html` — inline alert (info/success/warning/error)

## Shell

- [x] `templates/base.html` — dark sidebar, canvas-softer page bg, collapsible sidebar (desktop), mobile drawer + hamburger, notifications modal, loader overlay, active-link detection

## Auth flow

All standalone pages (don't extend `base.html`); follow the login chrome pattern.

- [x] `templates/registration/login.html`
- [x] `templates/registration/password_reset_form.html`
- [x] `templates/registration/password_reset_done.html`
- [x] `templates/registration/password_reset_confirm.html`
- [x] `templates/registration/password_reset_complete.html`
- [~] `templates/registration/password_reset_email.html` — wrapped by `email/base_email.html`; copy was rewritten but the email shell still needs the polish pass below
- [x] `templates/force_password_change.html`

## Home

- [x] `templates/home.html` — hero + 4 access cards (1 polarity-flipped); white cards on canvas-softer page bg

## Commons (shared partials)

These are `include`-d by many pages. Refactor them early to lift several screens at once.

- [x] `templates/commons/form-errors.html` — pill indicator + soft red surface; uses design tokens
- [x] `templates/commons/paginator.html` — pill button group, ink current page
- [x] `templates/commons/search-bar.html` — pill input wrap with primary "Buscar" pill
- [x] `templates/commons/nature-select.html` — uses new `ui-select` primitive

## Errors

- [x] `templates/errors/400.html`
- [x] `templates/errors/500.html`

## Contracts app

### Top-level

- [x] `templates/contracts/list.html`
- [x] `templates/contracts/detail.html`
- [x] `templates/contracts/edit.html`
- [x] `templates/contracts/create.html`
- [x] `templates/contracts/status-update.html`
- [x] `templates/contracts/timeline.html`
- [x] `templates/contracts/timeline-update.html`
- [x] `templates/contracts/workplan.html`

### Sub-resources

- [x] `templates/contracts/addendums-create.html`
- [x] `templates/contracts/documents-create.html`
- [x] `templates/contracts/documents-update.html`
- [x] `templates/contracts/goals-create.html`
- [x] `templates/contracts/goals-update.html`
- [x] `templates/contracts/interesteds-create.html`
- [x] `templates/contracts/items-create.html`
- [x] `templates/contracts/items-update.html`

### Items

- [x] `templates/contracts/items/purchases.html`
- [x] `templates/contracts/items/purchases-update.html`
- [x] `templates/contracts/items/request-raise.html`
- [x] `templates/contracts/items/review-request.html`
- [x] `templates/contracts/items/supplementations.html`
- [x] `templates/contracts/items/supplementations-create.html`
- [x] `templates/contracts/items/supplementations-update.html`

### Execution

- [x] `templates/contracts/execution/activity-create.html`
- [x] `templates/contracts/execution/activity-detail.html`
- [x] `templates/contracts/execution/create.html`
- [x] `templates/contracts/execution/detail.html`
- [x] `templates/contracts/execution/file-create.html`

### Detail tabs (partials)

- [x] `templates/contracts/tabs/accountability-tab.html`
- [x] `templates/contracts/tabs/banks-tab.html`
- [x] `templates/contracts/tabs/details-tab.html`
- [x] `templates/contracts/tabs/documents-tab.html`
- [x] `templates/contracts/tabs/execution-tab.html`
- [x] `templates/contracts/tabs/goals-tab.html`
- [x] `templates/contracts/tabs/interesteds-tab.html`
- [x] `templates/contracts/tabs/items-tab.html`

## Companies app

- [x] `templates/companies/list.html`
- [x] `templates/companies/detail.html`
- [x] `templates/companies/create.html`
- [x] `templates/companies/update.html`

## Accountability app

### Accountability (prestações)

- [x] `templates/accountability/accountability/list.html`
- [~] `templates/accountability/accountability/detail.html` — extends new shell; inner cards/tables still legacy chrome (see TECH_DEBT)
- [x] `templates/accountability/accountability/create.html`
- [x] `templates/accountability/accountability/import.html`
- [x] `templates/accountability/accountability/pendencies-list.html`
- [~] `templates/accountability/accountability/documents-table.html` — inner-table partial still legacy (TECH_DEBT)
- [~] `templates/accountability/accountability/expenses-table.html` — inner-table partial still legacy (TECH_DEBT)
- [~] `templates/accountability/accountability/revenues-table.html` — inner-table partial still legacy (TECH_DEBT)

### Expenses

- [x] `templates/accountability/expenses/create.html`
- [x] `templates/accountability/expenses/update.html`
- [~] `templates/accountability/expenses/reconcile.html` — TECH_DEBT
- [~] `templates/accountability/expenses/batch-reconcile.html` — TECH_DEBT
- [~] `templates/accountability/expenses/review.html` — TECH_DEBT
- [~] `templates/accountability/expenses/review-single.html` — TECH_DEBT

### Revenues

- [x] `templates/accountability/revenues/create.html`
- [x] `templates/accountability/revenues/update.html`
- [~] `templates/accountability/revenues/reconcile.html` — TECH_DEBT
- [~] `templates/accountability/revenues/review.html` — TECH_DEBT
- [~] `templates/accountability/revenues/review-single.html` — TECH_DEBT

### Sources (recursos)

- [x] `templates/accountability/sources/list.html`
- [x] `templates/accountability/sources/create.html`

### Favoreds (favorecidos)

- [x] `templates/accountability/favoreds/list.html`
- [x] `templates/accountability/favoreds/create.html`

### Beneficiaries

- [x] `templates/accountability/beneficiaries/dashboard.html`
- [x] `templates/accountability/beneficiaries/detail.html`

### Files

- [x] `templates/accountability/files/create.html`

### Search

- [~] `templates/accountability/search/advanced_search.html` — TECH_DEBT

## Accounts app

### Folder managers (gestores)

- [x] `templates/accounts/folder-managers/list.html`
- [x] `templates/accounts/folder-managers/detail.html`
- [x] `templates/accounts/folder-managers/create.html`

### Organization accountants (prestadores)

- [x] `templates/accounts/organization-accountants/list.html`
- [x] `templates/accounts/organization-accountants/detail.html`
- [x] `templates/accounts/organization-accountants/create.html`

### Organization committees (comitê)

- [x] `templates/accounts/organization-committees/list.html`
- [x] `templates/accounts/organization-committees/detail.html`
- [x] `templates/accounts/organization-committees/create.html`

### Org documents

- [x] `templates/accounts/org_documents/list.html`
- [x] `templates/accounts/org_documents/create.html`
- [x] `templates/accounts/org_documents/confirm_delete.html`

## Bank-account app

- [x] `templates/bank-account/create.html`
- [x] `templates/bank-account/detail.html`
- [x] `templates/bank-account/statement.html`
- [x] `templates/bank-account/manual-update.html`
- [x] `templates/bank-account/ofx-update.html`
- [x] `templates/bank-account/tabs/details-tab.html`
- [x] `templates/bank-account/tabs/transactions-tab.html`

## Dashboard app

- [x] `templates/dashboard/dashboard.html`

## Reports app

- [x] `templates/reports/export.html` — third pass restored the side-by-side **form + live PDF preview** layout the page is supposed to have. The left column is a compact form (small uppercase labels, 38px controls, pinned `Limpar` + primary action footer); the right column is a preview card with **empty / loading / success / error** states. On success the AJAX response is decoded into a blob, rendered in an `<iframe>` (Chrome's native PDF viewer), and the same blob URL powers the "Baixar PDF" button. The page is height-capped to the viewport so the user can generate → regenerate → download without scrolling, and the global form-submit loader is suppressed for this form (`ev.stopImmediatePropagation()`).
- Earlier passes (kept for reference): removed the always-on inline error card; wired Django `messages` into the toast queue via `templates/base.html`; let JSON / AJAX responses skip the 5xx template wrapper in `core/middlewares.ErrorHandlingMiddleware`; guarded `contract.contractor_company` in `reports/exporters/pass_on_1.py:_draw_down_informations` so the exporter doesn't `AttributeError` on contracts without a contractor company set.

## Transparency portal (public-facing)

Separate user surface, has its own base shell. May warrant a slightly different polish (no app sidebar, public branding), but should still respect DESIGN.md tokens.

- [x] `transparency_portal/templates/transparency_portal/base.html`
- [x] `transparency_portal/templates/transparency_portal/partnership_list.html`
- [x] `transparency_portal/templates/transparency_portal/partnership_detail.html`
- [x] `transparency_portal/templates/transparency_portal/organization_detail.html`
- [x] `transparency_portal/templates/transparency_portal/organization_documents.html`
- [x] `transparency_portal/templates/transparency_portal/organization_partnerships.html`
- [x] `transparency_portal/templates/transparency_portal/irregularity_report_form.html`

## Emails (separate concern)

Email clients (Outlook, Gmail) have very restricted CSS. These templates need a polish pass aligned with DESIGN.md but using inline styles and table layouts — NOT the in-app primitives.

- [ ] `templates/email/base_email.html` — wraps all transactional emails
- [ ] `templates/email/account_created_email.html`
- [ ] `templates/email/accountability_analisys_email.html`
- [ ] `templates/email/accountability_correcting_email.html`
- [ ] `templates/email/accountability_finished_email.html`
- [ ] `templates/email/contract_goal_commented.html`
- [ ] `templates/email/contract_item_commented.html`
- [ ] `templates/email/execution_analisys_email.html`
- [ ] `templates/email/execution_correcting_email.html`
- [ ] `templates/email/execution_finished_email.html`
- [ ] `templates/email/new_accountability_email.html`
- [ ] `templates/email/new_contract_email.html`
- [ ] `templates/email/new_contract_status_email.html`
- [ ] `templates/email/new_value_requested.html`
- [ ] `templates/email/new_value_reviewed.html`

## Progress snapshot

Rough roll-up — keep this section in sync as boxes get checked.

| Area | Done | Total |
|---|---|---|
| Foundation primitives | 11 | 11 |
| Shell | 1 | 1 |
| Auth flow | 5 | 7 |
| Home | 1 | 1 |
| Commons | 0 | 4 |
| Errors | 0 | 2 |
| Contracts | 0 | 32 |
| Companies | 0 | 4 |
| Accountability | 0 | 24 |
| Accounts | 0 | 12 |
| Bank-account | 0 | 7 |
| Dashboard | 0 | 1 |
| Reports | 0 | 1 |
| Transparency portal | 0 | 7 |
| Emails | 0 | 15 |
| **Total** | **18** | **129** |

## Suggested order of attack

1. **Commons partials** — `form-errors`, `paginator`, `search-bar`, `nature-select`. Refactoring these once lifts the visual baseline of every list page.
2. **Errors** — `400.html`, `500.html`. Small, isolated, high-traffic when they fire.
3. **Force-password-change** — finish closing the auth flow.
4. **Companies** — only 4 templates, simple CRUD shape — good warm-up for the list/detail/form pattern.
5. **Contracts list + detail + tabs** — highest-traffic inner app; one full pattern to replicate everywhere.
6. **Accountability list + detail + tables** — second-highest traffic; reuses the contracts pattern.
7. **Bank-account** — small surface, isolated.
8. **Accounts admin pages** — only visible to admins; lower urgency.
9. **Dashboard** — needs care around chart.js styling; do after the form patterns are stable.
10. **Reports export** — single page.
11. **Transparency portal** — public-facing; warrants a separate visual pass since it has different framing (no sidebar, public branding).
12. **Emails** — separate concern; tackle last with inline-style discipline.
