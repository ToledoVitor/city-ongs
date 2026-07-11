# CLAUDE.MD

## Read CLAUDE.md and relevant architecture notes before coding

This file is the persistent working guide for Claude Code in this repository. Treat it as a living document: keep it concise, practical, and current. When you learn a durable project convention, workflow, or architectural rule, update this file.

On typical macOS disks the volume is case-insensitive, so keep this single filename (`CLAUDE.MD`). Do not add a separate root `CLAUDE.md` symlink or duplicate; it can replace this file. Tools that expect `CLAUDE.md` usually resolve the same path as `CLAUDE.MD`.

## Authority

Agents must treat this file and `DESIGN.md` as binding project context. Read them before substantive work when the task involves stack, workflows, UI, or product tone. If anything here disagrees with generic advice, follow this repository.

You are a financial specialist working on an accountability project. The project needs to be elegant, clean, smooth, and user friendly: trustworthy copy, clear money flows, and UI that matches `DESIGN.md`.

## Goals

- Make safe, minimal, repo-consistent changes.
- Prefer project conventions over generic framework advice.
- Preserve user work and avoid unrelated edits.
- Keep this file focused on long-lived guidance, not task-specific notes.

## Project Snapshot

- Project name: `city-ongs` / `SITTS - Sistema Integrado de Trânsparencia ao Terceiro Setor`
- Stack: Python `3.12`, Django, PostgreSQL
- Dependency management: `uv`
- Main entrypoint: `manage.py`
- Settings module: `core.settings`
- Main Django apps:
  - `accounts`
  - `accountability`
  - `activity`
  - `bank`
  - `contracts`
  - `dashboard`
  - `reports`
  - `transparency_portal`
- Server-rendered UI uses Django templates under `templates/`

## First Files To Check

When you need project context, prefer these files first:

- `README.md` for local setup and standard commands
- `DESIGN.md` for product and design context
- `FUNCIONALIDADES_SISTEMA.md` for system capabilities and domain behavior
- `core/settings.py` for runtime, environment, logging, and installed apps
- `templates/base.html` for shared layout and frontend conventions

## Standard Workflow

Prefer the existing project commands instead of inventing new ones:

- Start app with Docker: `make up`
- Stop app: `make down`
- Local install: `uv sync`
- Run server locally: `make run`
- Create migrations: `make makemigrations`
- Apply migrations: `make migrate`
- Format code: `make format`
- Install hooks: `make pre-commit`

If a command already exists in `Makefile`, use it first.

## Editing Rules

- Keep changes small and scoped to the user request.
- Do not refactor unrelated code while implementing a feature or fix.
- Preserve naming, file layout, and patterns already used in the touched app.
- Prefer fixing the root cause over adding one-off workarounds.
- Avoid introducing new dependencies unless clearly necessary.
- Do not edit `.env` or commit secrets.
- Be careful with generated or sensitive files.

## Django Conventions

- Keep app-specific logic inside the relevant Django app whenever possible.
- When changing data models, also evaluate whether migrations are required.
- When changing views, check related templates, urls, forms, and permissions.
- When changing templates, keep the current server-rendered approach and reuse base layout patterns.
- Prefer existing service/helper modules when the app already separates business logic from views or models.
- **Code is English-only.** Model/class names, field names, choice member names, method names, variable names — all English, even when modeling a Brazilian-Portuguese domain (e.g. AUDESP/TCE compliance terms). Only `verbose_name`, `help_text`, choice *labels* (the human-facing string in a `Choices` tuple), docstrings/comments, and frontend-rendered text (templates, UI copy) may be in Portuguese. Established domain acronyms with no English equivalent in use elsewhere in the codebase (`cpf`, `cnpj`, `cns`, `cbo`) are the only exception — keep those as-is rather than inventing a translation.

## UI Density & Voice

Binding rules for any UI work in this repo. These are the *defaults* — deviate only when a screen genuinely needs more breathing room and say why in the PR.

### No scrolling on common desktop sizes

- A standard page (list, detail, dashboard, form) should **fit a 1366×768 viewport without the document scrolling**. Test at that size before declaring done.
- **Horizontal scroll is a bug, not a feature.** If a table is wider than the viewport: tighten columns, drop padding, truncate values with `text-overflow: ellipsis`, hide low-signal columns at narrower breakpoints — anything before `overflow-x: auto` on the page.
- Long content goes in a *contained* scroll area (a card body, a modal body, an iframe), never on `<body>`. The user should always see the page chrome.
- Pin primary actions (submit, save, cancel) to a footer inside the card, not floating at the bottom of an ever-growing form.

### Compact controls

- Form fields: 36–40px tall, 8–12px horizontal padding, 14px text. The 52px `.ui-form` default is for marketing/auth pages, not dense app forms — use `.ui-form--compact` (defined on `/reports`) or inline the override.
- Labels: 11px, uppercase, 0.4px letter-spacing, `color: var(--color-body)`, weight 500. Above the control, 4px gap.
- Buttons in dense areas use `.ui-btn--sm`. Reserve `.ui-btn` (default size) for hero calls-to-action.
- Filters: use the shared `.filter-row` / `.filter-field` pattern from `templates/ui/_styles.html`. Don't reinvent.

### Concise copy

- **One screen, one job.** State it in the heading. No subhead unless the heading really can't carry it alone.
- Sentence case for everything (headings, buttons, menu items). No ALL-CAPS labels except the 11px caption style.
- Cut "Bem-vindo ao", "Por favor", "Aqui você pode", "Clique no botão abaixo". Trust the user.
- Empty states are **one strong line + one small line**, not a paragraph. Pair with a clear action.
- Errors say what's wrong + what to do, in that order, in fewer than 12 words when possible.

### Preview-first when there's an output

- When a form *produces* something (a PDF, a report, a generated message), the page should be **inputs on the left, live preview/result on the right**. Don't make the user submit blind.
- Preview pane needs four states: empty (cta back to the form), loading (spinner + 1 line), success (the actual artifact), error (the real message + retry affordance).
- Success state should also wire up download/share/copy on the same artifact — no second request to the server.

### Visual fidelity to `DESIGN.md`

The base palette is the ink/canvas duet, but **semantic color earns its keep where it communicates meaning**. The distinction is *chrome* (decorative) vs *signal* (meaningful).

**Use ink/canvas only for:**

- Buttons (primary = ink, secondary = canvas-soft, subtle = transparent). No blue/indigo/purple/green/red button chrome.
- Card surfaces, page backgrounds, sidebar, navigation. No gradients, no decorative accents.
- Hero CTAs, headings, body text.

**Use semantic color (red / green / yellow / blue / orange) for:**

- **Status pills** — `Paga` green, `Não paga` red, `Em análise` warning, `Conciliada` info. Use `.ui-status` + `.ui-status--success|warning|error|info` from `_styles.html`, never bespoke `bg-*` classes.
- **Toasts and alerts** — variant follows severity (`success`, `error`, `warning`, `info`).
- **Charts and KPIs** — series colors differentiate sources/categories. Money flows, multi-source dashboards, comparison views.
- **Inline indicators** — red dot for unread, green check for verified, orange triangle for warning. Small and purposeful.
- **Destructive confirmations** — soft red surface on the "Excluir" action in modals.

**Geometry:** pill (`var(--rounded-pill)`) for buttons & chips; `var(--rounded-xl)` for cards. One accent at a time in dense areas — don't stack three competing colored buttons in the same row.

## Validation

Always verify changes proportionally to the risk:

- Run focused checks for the touched area first.
- For Python/style issues, prefer `make format`.
- For migrations, ensure they are created only when model changes require them.
- For UI/template changes, describe the manual path to verify if automated coverage is not available.
- If you could not run validation, say so explicitly.

## Safety Rules

- Never overwrite or revert user changes you did not make.
- Ignore unrelated dirty-worktree files unless the user asks otherwise.
- Never use destructive git commands unless explicitly requested.
- Before making broad changes, confirm the pattern by reading the local implementation first.
- Prefer repository evidence over assumptions.

## How To Maintain This File

Update `CLAUDE.MD` when you discover stable information such as:

- architectural boundaries
- naming conventions
- recurring pitfalls
- preferred commands
- testing expectations
- deployment or environment constraints that affect coding work

Do not add:

- temporary task notes
- personal reminders that are not repo conventions
- noisy checklists with no project-specific value

When updating this file, optimize for future agents: short, specific, and actionable beats comprehensive but vague.
