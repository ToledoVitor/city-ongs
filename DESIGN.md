---
version: 1
name: SITTS design spec
description: The binding UI spec for SITTS. A black-and-white ink/canvas duet with pill geometry, a geometric sans at two roles, and sentence-case voice — derived from Uber's design language (see docs/design-reference-uber.md) and extended with a semantic signal layer for the dense app surface.

colors:
  # Brand & accent — the only conversion colour is ink black.
  primary: "#000000"
  on-primary: "#ffffff"
  black-elevated: "#282828"
  surface-pressed: "#e2e2e2"
  # Text
  ink: "#000000"
  body: "#5e5e5e"
  hairline-mid: "#4b4b4b"
  mute: "#afafaf"
  on-dark: "#ffffff"
  # Surface
  canvas: "#ffffff"
  canvas-soft: "#efefef"
  canvas-softer: "#f3f3f3"
  # Signal — see "App surface" below. Never used as chrome.
  link: "#0000ee"
  toast-success: "#1f8a3b"
  toast-error: "#d92121"
  toast-warning: "#c98a00"
  toast-info: "#2a6ef5"

typography:
  font-display: "Inter, system-ui, Helvetica Neue, Arial, sans-serif"
  font-text: "Inter, system-ui, Helvetica Neue, Arial, sans-serif"
  font-mono: "JetBrains Mono, ui-monospace, monospace"
  display-xxl: { size: 52px, weight: 700, lineHeight: 64px }
  display-xl:  { size: 36px, weight: 700, lineHeight: 44px }
  display-lg:  { size: 32px, weight: 700, lineHeight: 40px }
  display-md:  { size: 24px, weight: 700, lineHeight: 32px }
  display-sm:  { size: 20px, weight: 700, lineHeight: 28px }
  body-lg:        { size: 18px, weight: 500, lineHeight: 24px }
  body-md:        { size: 16px, weight: 400, lineHeight: 24px }
  body-md-strong: { size: 16px, weight: 500, lineHeight: 20px }
  body-sm:        { size: 14px, weight: 400, lineHeight: 20px }
  body-sm-strong: { size: 14px, weight: 500, lineHeight: 16px }
  caption:        { size: 12px, weight: 400, lineHeight: 20px }

rounded:
  none: 0px
  md: 8px
  lg: 12px
  xl: 16px
  pill: 999px
  pill-tab: 36px
  full: 9999px

spacing:
  xxs: 4px
  xs: 6px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  2xl: 24px
  3xl: 32px

elevation:
  shadow-1: "0 4px 16px rgba(0, 0, 0, 0.12)"
  shadow-2: "0 4px 16px rgba(0, 0, 0, 0.16)"
  shadow-3: "0 2px 8px rgba(0, 0, 0, 0.16)"
---

## What this is

The binding UI spec for SITTS. Every value above is live in
`templates/ui/_styles.html`'s `:root` — this frontmatter and that block are the
same contract in two formats. If they ever disagree, **the CSS is right and this
file is stale**; fix this file.

The visual language is derived from Uber's. That is deliberate, not incidental:
the ink/canvas duet, the 999px pill on every interactive element, the two-role
geometric sans, and the sentence-case voice all come from there. The full
reference analysis — including the marketing surfaces SITTS doesn't ship (hero
bands, promo cards, the ride-request card, app-download pills, the editorial
illustration system) — lives in
[`docs/design-reference-uber.md`](docs/design-reference-uber.md). Read that when
designing something net-new that has no precedent in the app. For everything
else, this file plus the shipped CSS is enough.

## Foundations

**Colour is a duet.** Ink `#000000` is the only conversion colour: every primary
button, every dark band, the sidebar. Canvas `#ffffff` carries everything else,
with `canvas-soft` / `canvas-softer` for tinted sub-surfaces and pressed states.
There is no second brand accent. Do not introduce orange, purple, teal, or a
gradient as chrome.

**Type is two roles, one family.** `font-display` at weight 700 for headings
(20–52px, tight 1.22–1.25 line-height, never letter-spaced); `font-text` at 400
/ 500 for body, buttons, and links (12–18px). Both resolve to **Inter** — the
originals were proprietary, and Inter at `ss01` is the substitute this project
committed to. Never cross the roles: the display face carries no paragraph, the
text face carries no headline.

**The pill is the shape signature.** `rounded.pill` 999px on every interactive
element. Cards are `rounded.xl` 16px. Two documented exceptions: `.ui-btn--lg`
takes `rounded.xl` (the large-form CTA), and inputs take `rounded.md` 8px.

**Sentence case is the voice.** Headings, buttons, menu items. The only
uppercase in the system is the 11px field-label caption
(`text-transform: uppercase; letter-spacing: 0.4px` — `_styles.html:512`).

**Elevation defaults to flat.** Level 0 is the norm; cards lean on
canvas-vs-canvas-soft contrast. `shadow-1` for elevated cards, `shadow-2` for
modals and form cards, `shadow-3` for floating pills. Do not shadow every card.

## App surface — chrome vs signal

This is the one place SITTS extends its source. The reference language is a
marketing surface with no error/success/warning palette; SITTS is a dense
internal app about public money, where status *is* the content. Blanket "no
colour but ink" would make a reconciliation table unreadable.

The rule is **chrome vs signal**, and it is absolute in both directions.

**Signal — semantic colour is required here.** It carries meaning a reader must
not have to parse:

| Surface | Class | Meaning |
|---|---|---|
| Status pill | `.ui-status--success \| error \| warning \| info \| neutral \| dark` | `Paga` success, `Não paga` error, `Em análise` warning, `Conciliada` info |
| Inline alert | `.ui-alert--success \| error \| warning \| info \| danger` | severity of the message |
| Toast | `.ui-toast--success \| error \| warning \| info` | outcome of the action |
| Destructive action | `.ui-btn--danger`, `.ui-icon-btn--danger`, `.ui-chip--danger` | irreversible — soft red surface |
| Chart / KPI series | series colours | differentiates sources, categories, money flows |
| Inline indicator | small dot / check / triangle | unread, verified, warning |

**Chrome — ink and canvas only, no exceptions.** Buttons (primary = ink,
secondary = canvas + ink border, subtle = canvas-soft), cards, page background,
sidebar, navigation, headings, body text, hero CTAs. A blue "Salvar" button is a
bug. A green "Aprovar" button is also a bug — approval is chrome; the resulting
status pill is the signal.

One accent at a time in dense areas. Don't stack three coloured buttons in a row.

**Known gap:** the four `toast-*` tokens above cover the status pill's 8px dot,
but each pill's surface and text colour is still a hardcoded hex pair in
`_styles.html:829-836` (`#e9f7ee`/`#155724`, `#fde9e9`/`#842029`,
`#fcf3da`/`#735200`, `#e7f0fd`/`#1c4ea8`). Promote those to `:root` when you next
touch that block. The `:root` comment calling the semantic tokens "for toasts
only" predates the status pills and is no longer accurate.

## Component vocabulary

These are the shipped class names — the real contract. Reuse them; do not write
parallel chrome inline.

| Family | Variants | Notes |
|---|---|---|
| `.ui-btn` | `primary` `secondary` `subtle` `floating` `ghost` `danger` · `sm` `lg` `full` | 44px default, `--sm` 36px, `--lg` 56px + `rounded.xl` |
| `.ui-card` | `soft` `softer` `dark` `elevated` `flush` · `sm` `lg` | `rounded.xl`, `space.2xl` padding |
| `.ui-input` `.ui-select` `.ui-textarea` | `on-soft` `has-icon-right` | `rounded.md`; `.ui-form` styles raw Django-rendered fields |
| `.ui-table` | `auto` `hover-link` | wrap in `.ui-table-wrap` / `.ui-table-scroll` for contained overflow |
| `.ui-status` | `success` `error` `warning` `info` `neutral` `dark` | signal — see above |
| `.ui-alert` | `success` `error` `warning` `info` `danger` | signal |
| `.ui-toast` | `success` `error` `warning` `info` | signal; queued by `ui/_scripts.html` |
| `.ui-modal__*` | — | global modal chrome; per-row modals use this, not Flowbite defaults |
| `.ui-badge` `.ui-chip` | `dark` `outline` · `action` `danger` `warning` | |
| `.ui-empty` | `compact` | one strong line + one action |
| `.ui-icon-btn` | `danger` | row actions |
| `.ui-display-*` `.ui-body-*` `.ui-caption` | — | the type scale as utilities |
| `.ui-stack` `.ui-row` `.ui-grid-2` `.ui-grid-3` `.ui-toolbar` | spacing tokens | layout primitives |
| `.filter-row` `.filter-field` | — | the shared filter pattern; don't reinvent |
| `.ui-breadcrumb` `.ui-tabs` `.ui-tab--active` | — | |

Django-include primitives live in `templates/ui/`: `button.html`, `card.html`,
`text_input.html`, `password_input.html`, `text_link.html`, `alert.html`,
`badge.html`, `toast.html`, `combobox.html`, `wordmark.html`.

## Do's and Don'ts

**Do**

- Reserve ink for the primary action. One ink pill per visible viewport.
- Put `rounded.pill` on every interactive element; `rounded.xl` on cards.
- Set headings in `.ui-display-*` weight 700, sentence case.
- Use semantic colour for status, severity, and destructive intent — and only there.
- Contain overflow in the card or table (`.ui-table-wrap`), never on `<body>`.
- Pin primary actions to a footer inside the card, not floating at the page bottom.

**Don't**

- Don't introduce a second brand accent as chrome. No gradients, no decorative colour.
- Don't colour a button by its verb. Ink, canvas, or canvas-soft — plus `--danger` for irreversible.
- Don't use all-caps display headings. Uppercase is the 11px field label only.
- Don't letter-space the display face.
- Don't shadow every card. Level 0 flat is the default.
- Don't hand-roll chrome that `.ui-*` already covers.

## Where the truth lives

| Question | Answer |
|---|---|
| What are the tokens? | `templates/ui/_styles.html` `:root` (lines 19–73) |
| What does a component look like? | `.claude/skills/sitts-ui/references/mockup.html` |
| What primitives can I include? | `templates/ui/*.html` |
| Which templates are on the system? | `python scripts/audit_templates.py` |
| Density, copy, and layout rules | skill `sitts-ui` |
| Where did this language come from? | `docs/design-reference-uber.md` |
