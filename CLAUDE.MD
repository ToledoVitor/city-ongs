# CLAUDE.MD

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
