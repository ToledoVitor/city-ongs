# AGENTS.md

The working guide for this repository is **[`CLAUDE.MD`](CLAUDE.MD)**. Read it
before coding. It applies to every agent, not only Claude Code, and it is short
on purpose: repo summary, the English-only naming rule, the non-obvious gotchas,
and the non-negotiables for a system that moves public money.

**[`DESIGN.md`](DESIGN.md)** is the binding UI spec — read it before any work on
`templates/`, CSS, or user-facing copy.

Deeper, task-specific guidance is split into files under `.claude/skills/`. Each
is a short `SKILL.md` plus references; read the one that matches your task rather
than all of them:

| Skill | When |
|---|---|
| `sitts-ui` | Templates, CSS, UI copy |
| `sitts-verify` | Running checks, exercising views without Docker/Postgres |
| `sitts-audesp` | `audesp/`, TCE-SP payloads |
| `sitts-deploy` | GCP, Cloud Run, IAM, image retention |
| `sitts-known-bugs` | Debugging; read before touching `transparency_portal`, `reports/exporters`, the bank OFX import, or accountability review views |

Run `make help` for commands.

This file is a pointer on purpose. It used to duplicate `CLAUDE.MD` in full and
drifted out of sync, so the same guidance lived in two places and disagreed. Add
durable project conventions to `CLAUDE.MD` instead, and leave this file as a
signpost.
