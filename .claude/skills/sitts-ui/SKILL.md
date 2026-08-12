---
name: sitts-ui
description: Density, layout, and copy rules for SITTS's server-rendered UI. Use when working on anything under templates/, editing CSS in templates/ui/_styles.html, writing or reviewing user-facing Portuguese copy, or building a new page/form/table. Pairs with DESIGN.md, the binding token and component spec.
---

# SITTS UI

`DESIGN.md` at the repo root is the binding spec: tokens, the shipped `.ui-*`
component vocabulary, and the chrome-vs-signal rule for semantic colour. Read it.
This skill is the part that isn't tokens — density, layout, copy, and the traps.

## Precedence, when two sources disagree

1. **`templates/ui/_styles.html`** — the shipped CSS. It is the implementation; it wins.
2. **`DESIGN.md`** — the spec. If it disagrees with the CSS, the spec is stale: fix `DESIGN.md`.
3. **`docs/design-reference-uber.md`** — the reference the language came from. Consult for net-new design with no precedent in the app. Never override 1 or 2 with it — it describes a marketing site, and much of it has no SITTS counterpart.

There is no light/dark theming. The app is light-only; the sidebar is dark by
design, not by theme. Don't add `prefers-color-scheme` blocks.

## Density

The app is dense on purpose — these are people reconciling hundreds of expense
rows, not visitors reading a landing page.

**The target: a list, detail, dashboard, or form page fits 1366×768 without the
document scrolling.** Treat that as the rubric you design toward, not a gate you
prove. There's no viewport test in the repo, so nobody can hand you a pass/fail —
if a page doesn't fit, the fix is to cut or tighten content, not to let the page
grow and shrug.

- **Overflow is contained, never on `<body>`.** Wide tables go in `.ui-table-wrap` or `.ui-table-scroll` (both already `overflow-x: auto`). Long card content scrolls inside the card body. The user should always see the page chrome. A horizontally scrolling *page* is a bug; a horizontally scrolling *table* is the intended primitive.
- Before reaching for the scroll container on a table: tighten columns, drop padding, truncate with `.ui-text-truncate`, hide low-signal columns at narrower widths.
- Controls in dense areas: `.ui-btn--sm` (36px). Reserve the default `.ui-btn` (44px `min-height`, 46px rendered) for the page's primary action and `.ui-btn--lg` (56/58px) for hero CTAs on `home.html` and auth pages.
- Form fields in dense app forms want a 36–40px control height, ~14px text. `.ui-form`'s default is the ~52px marketing/auth size. `.ui-form--compact` is the dense override — currently defined locally in `templates/reports/export.html:252-266`. **If you need it on a second page, promote it to `_styles.html` rather than copying the block.**
- Form field labels are `.ui-field__label` — 14px, weight 500, ink, **sentence case** (`_styles.html:225`). Pair with `.ui-field__hint` / `.ui-field__error` inside a `.ui-field` wrapper.
- The 11px uppercase style is *not* the form-label style. It belongs to exactly four selectors: `.filter-field__label` (`_styles.html:908`), `.ui-table thead th`, `.ui-dl dt`, `.ui-combobox__group`. Don't apply it to form fields.
- Filters: use `.filter-row` / `.filter-field` / `.filter-field__label`. Don't reinvent the pattern.
- Pin submit/save/cancel to a footer inside the card, not floating at the bottom of a growing form.

## Copy

Portuguese, sentence case, and short. One screen, one job — state it in the
heading and skip the subhead unless the heading genuinely can't carry it.

- Cut the throat-clearing: "Bem-vindo ao", "Por favor", "Aqui você pode", "Clique no botão abaixo".
- Errors: what's wrong, then what to do. Short enough to read in one pass.
- Empty states: one strong line plus one action. `.ui-empty` (or `--compact`).
- Money and compliance wording is load-bearing. "Glosado", "conciliado", "repasse", "prestação de contas" are domain terms with legal meaning — don't paraphrase them into friendlier words.

## Pages that produce an artifact

When a form generates something — a PDF, a report, a message — lay it out as
inputs left, live preview right. Don't make the user submit blind.

The preview pane needs four states: **empty** (CTA back to the form), **loading**
(spinner + one line), **success** (the actual artifact), **error** (the real
message + a retry affordance). Wire download/share/copy off the same artifact
already in the browser — no second round-trip to the server.

`templates/reports/export.html` is the worked example: the AJAX response is
decoded to a blob, rendered in an `<iframe>`, and the same blob URL powers the
download button.

## Traps

**The segmented control's active state is toggled by JS using Tailwind class
names.** `templates/accountability/accountability/detail.html:603-611` maps
`.seg-group__btn.bg-blue-600` and `.bg-blue-600.text-white` to ink with
`!important`. Those aren't leftover legacy chrome — they're a deliberate bridge.
Delete the override without first changing the JS and the active tab goes
invisible.

**Standalone pages don't use `.ui-*` utilities and that's correct.** `login.html`,
the four `password_reset_*`, `force_password_change.html`, `home.html`, and
`transparency_portal/base.html` have their own shell and consume tokens directly
via `var(--color-*)` (`home.html` has 43 such references). They're on the design
system; they just don't extend `templates/base.html`. Don't "fix" them into
`.ui-*` classes.

**Email templates use no tokens at all, by design.** The 15 files under
`templates/email/` need inline styles and table layouts — Gmail and Outlook strip
CSS classes. They are the one genuinely unrefactored UI surface left; see
`sitts-known-bugs`.

**Django widgets can override the generic form CSS.** `.ui-form` styles raw
`{{ form.field }}` output, but a form that sets widget classes in Python wins over
it. Check the rendered control when a field looks wrong.

**There are two alert implementations.** `.ui-alert` + `.ui-alert--*` (used in 7
templates) puts a semantic dot on a canvas-softer surface; the `ui/alert.html`
include (used in 2) inline-styles a semantic 3px left border on canvas-soft.
Same intent, different mechanism. Prefer the classes — that's the dominant
pattern. `--danger` and `--error` are aliases.

## The primitives document themselves

Every include in `templates/ui/` opens with a `{% comment %}` block listing its
props, defaults, and usage. Read the file rather than guessing — they're accurate
and colocated, so they can't drift from the implementation.

`button` · `card` · `text_input` · `password_input` · `text_link` · `alert` ·
`badge` · `toast` · `combobox` (+ `combobox_widget`, `_combobox_control`) ·
`wordmark`. Plus `_styles.html` (tokens + all `.ui-*` CSS) and `_scripts.html`
(password toggle, toast queue).

For a Django form field that needs a searchable select, use
`utils.widgets.ComboboxSelectWidget` rather than including `combobox.html` by
hand.

## Verify your work

Templates on the design system vs. not:

```bash
python tools/audit_templates.py
```

To see every primitive rendered on one page:

```bash
python tools/build_ui_mockup.py && open .claude/skills/sitts-ui/references/mockup.html
```

The mockup embeds the `<style>` block straight out of
`templates/ui/_styles.html`, so it cannot drift from the shipped CSS. Regenerate
it after editing tokens or components.
