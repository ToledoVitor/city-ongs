# SITTS — Tech Debt Log

Short, dated entries for items spotted during the visual refactor that should be cleaned up later. Keep each entry to 1–3 lines: what / where / why.

## Format

```
- YYYY-MM-DD — [area] short summary — file_or_url — note (optional)
```

## Entries

- 2026-05-14 — [contracts/detail tabs] Flowbite `data-tabs-toggle` may need fresh init after my CSS changes — `templates/contracts/detail.html` — verify panel swap on click works at runtime (saw possibly stale active state in first browser pass; tabs are styled with `.contract-tab--active`).
- 2026-05-14 — [accountability tables] `accountability/expenses-table.html` (1115 lines), `revenues-table.html` (1002 lines), `accountability/detail.html` (1210 lines) and `search/advanced_search.html` (635 lines) were NOT individually refactored due to volume — they still extend the new shell so chrome renders cleanly but their inline tables/cards retain legacy Tailwind. Refactor in a follow-up pass.
- 2026-05-14 — [accountability flows] expenses/revenues `reconcile`, `review`, `review-single`, `batch-reconcile` (400-600 lines each) not individually refactored; legacy chrome remains inside the new shell. Same as above.
- 2026-05-14 — [transparency_portal] All seven public-facing templates kept their own `base.html` and were NOT refactored — they need a separate pass with public-facing branding considerations.
- 2026-05-14 — [emails] `templates/email/*.html` (15 transactional templates) intentionally left for a separate inline-style pass (email clients strip CSS classes).
- 2026-05-14 — [forms] Some Django form widgets render raw HTML via `{{ form.field }}` and rely on the generic `.ui-form` CSS to look clean. Some forms set their own widget classes in Python which override this — verify on first runtime test of each form.
- 2026-05-14 — [icons] Many pages keep inline SVG icons. A future cleanup could extract a common `templates/ui/icons.html` library to dedupe and keep stroke widths consistent.
- 2026-05-14 — [worktree abandoned] The visual refactor was started in `.claude/worktrees/quirky-noether-bb16a2` but pivoted to the parent at `/Users/vitortoledo/projects/ongs/` because the docker container mounted the parent path. The worktree's REDESIGN.md and TECH_DEBT.md are now stale; the canonical trackers live at `REDESIGN.MD` and `TECH_DEBT.MD` in the parent.
- 2026-05-14 — [contracts/items items-tab] Modal "Avaliar" vs "Detalhes" label is inverted relative to permission check — review user.can_change_statuses vs can_review intent (cosmetic, copy was preserved as-is from legacy template).
- 2026-05-14 — [dashboard] Multi-select dropdowns for Status and Contract were simplified from custom Flowbite dropdown menus to native `<select multiple>` due to time. Functionality preserved but UX is less polished — consider a custom multi-select for the next pass.
- 2026-05-14 — [test coverage] No automated UI test pass was added; visual refactor was verified only via Chrome MCP browser walkthrough at desktop width. Add Playwright/Cypress smoke tests for the most critical flows (login, contracts list/detail, accountability detail).
- 2026-05-14 — [reports/exporter] FIXED in `reports/exporters/pass_on_1.py:_draw_down_informations` — `contractor_company` is now guarded (mirrors the `hired_company` pattern). Renders `LOCAL: —` when missing. Still: the broader exporter assumes lots of optional contract fields are populated; a sweep pass over the other `pass_on_*.py` exporters is worthwhile when more report models surface.
- 2026-05-14 — [reports/export form] The "Demais responsáveis" expand panel iterates `{% for field in form %}` and matches by substring (`responsible`, `autority`, `manager`). Brittle if field names change; consider a `form.responsible_fields` accessor. (`templates/reports/export.html`)
