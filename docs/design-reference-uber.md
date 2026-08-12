---
version: alpha
name: Uber-design-analysis
description: An inspired interpretation of Uber's design language — a transportation-and-delivery super-app brand whose web surface is a black-and-white duet, framed by a custom geometric display sans, accented by a single signature pill shape (radius 999px) on every interactive element, and decorated only by editorial 4:3 illustrations of riders, drivers, and city objects.
---

# Design reference — Uber's design language

This is the **reference analysis** SITTS's visual language was derived from, kept
in full. It is not the spec. The spec is [`DESIGN.md`](../DESIGN.md) at the root,
which carries the tokens, the shipped component vocabulary, and the app-surface
semantic extension.

Read this file when you are designing something net-new that has no precedent in
the app and you need the original reasoning — the marketing-surface rhythm, the
promo-band cadence, the illustration system. For day-to-day work inside the app,
`DESIGN.md` plus `templates/ui/_styles.html` is enough, and this file is 5k
tokens you don't need to spend.

Sections below describe **Uber's marketing web surface**, much of which SITTS
does not ship. Where a component has no SITTS counterpart it is marked
*(no SITTS counterpart)*.

## Overview

Uber is a transportation-and-delivery super-app — ride, eats, freight, the whole
urban logistics layer — and the brand's web surface signals that scale through
restraint: no third colour, no accent palette, no illustration that fights the
headline. The page is structurally a black-and-white duet, where black is the
conversion anchor (every CTA pill, every nav login button, the footer fill) and
white carries everything else. The only consistent decoration is a body of
editorial 4:3 illustrations — riders, drivers, parking lots, cars-on-highway —
that ground the marketing without leaking accent colour into the system.

Type is the second decisive voice. Two custom faces carry every page:
`UberMove` at weight 700 for headlines (32–52px display sizes with tight
1.22–1.25 line-height, never letter-spaced), and `UberMoveText` at weights
400 / 500 for body, button, and link. The pairing reads as engineering-grade — no
italic, no decorative weight, no tracking flourish. Headlines are sentence-case;
eyebrows are uppercase only when used as the section eyebrow ("WHY BECOME");
buttons are sentence-case.

The single shape signature is the pill. Every interactive element rounds to
999px — primary CTA, secondary CTA, subtle gray pill, white floating pill,
category chip, app-download badge. Cards and surfaces round to 16px. The
tab-toggle on the hero ride-request form uses an off-shape 36px — barely-pill,
deliberately tighter than the canonical 999px.

**Key characteristics**

- A two-colour CTA hierarchy: black pill for primary conversion targets; white pill (sometimes with a soft drop shadow) for secondary; subtle gray pill for tertiary or chip variants.
- The pill is the single signature shape — 999px on every interactive element except the tab-toggle (36px) and the larger product cards (16px).
- Every headline is sentence-case at display-xl / display-xxl weight 700; no all-caps display.
- Editorial 4:3 illustrations of riders / drivers / cars are the only consistent decorative system; no gradients, no atmospheric backdrops, no shadows that aren't card-elevation hints.
- A signature alternating-band rhythm: white feature card → black promo card (with white text and white CTA) → white feature card → black footer. The black bands are NOT hero-only; they appear mid-page as promo callouts.
- A signature ride-request form card on the hero: pickup pin input + destination input + date/time chip + black "See prices" pill, all stacked inside a 16px shadowed card.

## Colours

### Brand & accent

- **Ink Black** (`#000000`): the brand's only conversion colour. Every primary CTA pill, the footer fill, every dark promo band, every nav login button. The system has no secondary accent.
- **Surface Pressed** (`#e2e2e2`): the pressed-state fill for white pills — a soft grey used only in active / pressed states.
- **Black Elevated** (`#282828`): a near-black used on hover for the translucent white tab-toggle pill. Documented as a system colour because it appears on a recurring brand control.

### Surface

- **Canvas** (`#ffffff`): the default page background.
- **Canvas Soft** (`#efefef`): the soft gray fill for category chips, form-input rows inside the ride-request card, and subtle pill buttons.
- **Canvas Softer** (`#f3f3f3`): a slightly lighter gray used as a nested-input fill on white surfaces.

### Text

- **Ink** (`#000000`): every heading and body paragraph on light surfaces.
- **Body** (`#5e5e5e`): secondary text — captions, sub-headings, supporting copy.
- **Hairline Mid** (`#4b4b4b`): a mid-gray for muted link text inside footer columns and breadcrumb-style nav.
- **Mute** (`#afafaf`): the lightest text role — placeholder text, fine print, low-priority metadata.
- **On Dark** (`#ffffff`): all text on ink surfaces (footer, dark promo bands).

### Semantic

The brand does not maintain a separate error / success / warning palette **in its
public marketing surface**. Validation cues come from the primary black or from
the brand's editorial illustrations. The `#0000ee` link colour is the system's
only chromatic — the browser-default link blue, appearing in body-copy inline
links inside legal / footer text.

> **This is the scoped statement SITTS extends.** A marketing page has no status
> to communicate; a reconciliation table does. See `DESIGN.md` §"App surface —
> chrome vs signal" for the extension and its boundary.

## Typography

### Font family

Two custom faces carry the entire system:

1. **A custom geometric display sans** (extracted as `UberMove`) for every headline. Weight 700 only; no italic; no tracking variation. Sizes range from display-sm 20px up to display-xxl 52px on the hero. Line-heights tighten to 1.22–1.25 at display sizes for a poured-on-the-page look.
2. **A custom text sans** (extracted as `UberMoveText`) for body, button, link, and small headings. Weights 400 and 500 are the working pair. Used at 12–18px; 24px maximum for ride-request form labels. Tracking is always neutral.

The two faces share a family DNA but never overlap roles — the display face
never carries a body paragraph; the text face never carries a hero headline.

Both faces are proprietary. The substitutes considered were *Inter* weight 700
with `font-feature-settings: "ss01"` (closest for display) and *Geist* weight 700
(second choice); *Inter* 400/500 for text, with *Plus Jakarta Sans* as a softer
alternative. **SITTS committed to Inter for both roles** — that decision is
recorded in `DESIGN.md` and live at `templates/ui/_styles.html:46-47`. This
paragraph is the reasoning behind it, not an open question.

### Hierarchy

| Token | Size | Weight | Line height | Use |
|---|---|---|---|---|
| display-xxl | 52px | 700 | 64px | Hero headline. |
| display-xl | 36px | 700 | 44px | Page section headlines. |
| display-lg | 32px | 700 | 40px | Promo-card headlines. |
| display-md | 24px | 700 | 32px | Card titles, illustrated-promo headlines. |
| display-sm | 20px | 700 | 28px | Sub-card headings. |
| body-lg | 18px | 500 | 24px | Lead paragraphs and larger body. |
| body-md | 16px | 400 | 24px | Default paragraph body. |
| body-md-strong | 16px | 500 | 20px | Bolded inline body and most button labels. |
| body-sm | 14px | 400 | 20px | Captions, secondary metadata. |
| body-sm-strong | 14px | 500 | 16px | Bold caption / chip labels. |
| caption | 12px | 400 | 20px | Fine print, footer secondary lines. |
| button-large | 18px | 500 | 24px | Large rounded buttons inside the ride-request form. |
| button-md | 16px | 500 | 20px | Default button label. |

### Principles

- **Sentence-case is the voice.** No all-caps headlines. Eyebrow tags ("WHY BECOME") are the rare exception.
- **Weight 700 is for headlines; weight 500 is for buttons and emphasis.** Don't promote button labels to 700.
- **No tracking flourish.** The display face is never letter-spaced, positive or negative.
- **Two faces, two roles.** Display for headlines; text for everything else. Never cross the streams.

## Layout

### Spacing system

- **Base unit**: 4px. Most captured values are multiples of 4 with a few 6px sub-multiples (10, 14) inside button padding.
- **Tokens**: xxs 4 · xs 6 · sm 8 · md 12 · lg 16 · xl 20 · 2xl 24 · 3xl 32.
- **Section padding**: marketing bands sit at 32px top/bottom on tighter pages and 32px for hero bands; promo cards inset at 24px.
- **Card interior padding**: content cards at 24px; the ride-request form uses 16px to keep the form compact.
- **Inline gap**: button rows, category chip rows, app-store pill rows use 12px between siblings.

### Grid & container

- **Max width**: ~1200px container; centred with horizontal gutters of 32px on desktop, 16px on mobile.
- **Column patterns**: promo-card rows 2-up at desktop (image left + content right, alternating sides), 1-up at mobile; category chips horizontal flex with wrap; FAQ rows full-width single-column; app-download pills 2-up desktop / 1-up mobile.

### Whitespace philosophy

Card-to-card spacing carries the rhythm — between two stacked promo cards
there's roughly a full 32px gutter; inside a card the headline / paragraph / CTA
stack is tight (8px between siblings). The black promo bands and the footer have
no internal hairlines — content sits on flat ink with white text.

### Responsive strategy *(marketing breakpoints — SITTS uses its own)*

| Name | Width | Key changes |
|---|---|---|
| Mobile | < 600px | Nav collapses to hamburger; promo cards stack; ride-request form becomes full-width. |
| Mobile-Large | 600–767px | Same as Mobile; chip rows enable horizontal scroll. |
| Tablet | 768–1119px | 2-up promo grid at upper widths; nav stays horizontal until ≥ 1120px. |
| Desktop | 1120–1135px | Full nav row visible; promo cards 2-up. |
| Desktop-Large | ≥ 1136px | Container caps at ~1200px; bands stay edge-to-edge while content centres. |

### Touch targets

The pill primary button renders at ~44px tall (10px vertical padding + 24px
label line-height); the larger rounded button at ~56px. Both meet WCAG AAA at all
breakpoints. Category chips inflate to ≥ 44px tall through extra padding on
touch viewports. *(SITTS ships these as `.ui-btn` 44px / `.ui-btn--lg` 56px /
`.ui-btn--sm` 36px.)*

### Collapsing strategy

- **Nav**: full link row + Help / Log in / Sign up pills at desktop. Collapses to logo + hamburger at mobile; menu overlays full-screen with the same link list stacked. *(SITTS uses a sidebar shell instead — `templates/base.html`.)*
- **Ride-request form card**: at desktop the form sits inside a max-490px 16px card with shadow; at mobile full-width edge-to-edge. *(no SITTS counterpart)*
- **Promo cards**: image-left + content-right (or alternating) at desktop; image always above content at mobile.
- **Annual showcase card**: scales from a 2:3 desktop frame to a 4:3 mobile frame; date text resizes proportionally. *(no SITTS counterpart)*

### Image behaviour

- **Editorial illustrations**: 4:3 or 16:9 hard-edge rectangles; never cropped to a circle, never tilted. Aspect preserved.
- **Photography**: square or landscape; framed inside 16px card chrome.
- **Maps in ride-request flow**: full-bleed inside a card; rounded corners follow the parent card. *(no SITTS counterpart)*
- **Logo bar**: SVG vector, monochrome, consistent height.

## Elevation & depth

| Level | Treatment | Use |
|---|---|---|
| Level 0 — Flat | No shadow, no border. | Default — most cards and surfaces lean on hairline-of-canvas contrast. |
| Level 1 — Subtle Drop | `rgba(0,0,0,0.12) 0 4px 16px` | Card-elevated frames around promo cards on light bands. |
| Level 2 — Card Drop | `rgba(0,0,0,0.16) 0 4px 16px` | The ride-request form card on the hero; large content cards with embedded forms. |
| Level 3 — Pill Float | `rgba(0,0,0,0.16) 0 2px 8px` | The floating white pill button over hero photography. |

### Decorative depth

- **Black bands as polarity-flip depth**: pure black mid-page bands break the white-on-white rhythm. The polarity shift IS the depth cue.
- **Editorial illustrations as in-card depth**: every promo card has a single 4:3 illustration as its left or right column. The illustration's visual weight is part of the card's elevation read.
- **Pill geometry as micro-depth**: 999px applied at varying button heights creates a stack of nested pills that reads as visual hierarchy.

## Shapes

| Token | Value | Use |
|---|---|---|
| none | 0px | Full-bleed hero bands, footer fill, raw image edges. |
| md | 8px | Form-input fields. |
| lg | 12px | Smaller secondary card chrome. |
| xl | 16px | Canonical card radius — promo cards, content cards, ride-request form card, annual-showcase card, large rounded buttons. |
| pill | 999px | The signature interactive shape — every pill button, category chip, app-download pill, icon button. |
| pill-tab | 36px | The translucent-white tab-toggle pill on the hero (Ride / Drive). |
| full | 9999px | Identical effect to pill for circular icon containers. |

### Photography geometry *(mostly no SITTS counterpart)*

- **Editorial illustrations**: 4:3 landscape inside promo cards; 16:9 for full-width showcase frames.
- **Driver / rider portraits**: 4:5 portrait crop; framed by 16px card chrome.
- **Annual showcase image**: 2:3 portrait at desktop, scaling to 4:3 at mobile. The image fills the card; the headline overlays the bottom.
- **Logo bar**: monochrome SVG vectors at consistent ~24px height.
- **Avatars**: square or full-circle, never a rounded-square.

## Components

### Buttons

**`button-primary`** — the canonical black pill, the conversion target. Background primary, text on-primary, label at button-md, padding 12/12, shape pill.

**`button-secondary`** — the white pill paired with the black primary. Background canvas, text ink, same label and padding, shape pill.

**`button-subtle`** — the gray secondary pill for tertiary actions inside cards. Background canvas-soft, text ink, label at button-md, padding 12/16, shape pill.

**`button-floating`** — the white pill with a subtle drop-shadow that floats over a dark or photographic surface. Background canvas, text ink, padding 12, shape pill, Level 3 shadow.

**`button-large-rounded`** — the bigger black CTA used inside the ride-request flow. Background primary, text on-primary, label at button-large, padding 16/20, shape **xl 16px** — the only black CTA that breaks the pill rule, used in the larger form context. *(SITTS ships this as `.ui-btn--lg`.)*

**`button-tab-translucent`** — the tab-toggle on the hero ride-request form (Ride / Drive). Background canvas, text ink, label at body-md-strong, shape pill-tab 36px. *(no SITTS counterpart)*

### Cards & containers

**`card-content`** — the canonical content card. Background canvas, text ink, padding 24, shape xl. No shadow by default.

**`card-elevated`** — the content card with Level 1 subtle drop. Same padding and shape.

**`card-soft-tinted`** — the gray-tinted card used as a sub-region inside the page. Background canvas-soft, padding 24, shape xl.

**`promo-card-illustrated`** — the 2-column promo card with illustration on one side and copy on the other. Background canvas, padding 24, shape xl. Headline at display-md or larger.

**`promo-card-on-dark`** — the polarity-flipped promo card in black. Background ink, text on-dark, padding 24, shape xl.

**`request-form-card`** — the hero ride-request form chrome. Background canvas, padding 16, shape xl, Level 2 shadow. *(no SITTS counterpart)*

**`request-form-input-row`** — the per-field row inside the request-form card. Background canvas-soft, padding 16, shape md. Hosts an icon + label + value. *(no SITTS counterpart)*

**`showcase-image-card`** — the giant annual showcase card. Background ink, text on-dark overlay, padding 32, shape xl. Display-xxl headline overlays the bottom of the image. *(no SITTS counterpart)*

### Inputs & forms

**`text-input`** — the canonical text input. Background canvas-soft, text ink, body at body-md, padding 16, shape **md 8px**.

> The frontmatter of the original analysis listed `rounded: none` for this
> component while the prose said 8px. The shipped CSS resolves it: 8px
> (`--rounded-md`). Note also that SITTS's dense app forms override the padding
> down to a 36–40px control height via `.ui-form--compact`; the 16px padding here
> yields the ~52px marketing/auth height.

**`text-input-on-soft`** — the nested input on a white card (slightly lighter fill: canvas-softer). Otherwise identical.

### Navigation

**`nav-bar`** — the sticky top nav. Background canvas on light pages, switches to ink on the rare dark page. Padding 16/32. *(SITTS uses a dark sidebar shell instead.)*

**`nav-link`** — the link row inside nav-bar. Text ink, body-md-strong 500.

**`footer`** — the deep-black footer band. Background primary, text on-dark, padding 32/32. Body at body-sm; column eyebrows at body-md-strong.

### Signature components *(marketing — mostly no SITTS counterpart)*

**`hero-band-light`** — the white hero with the ride-request card. Background canvas, padding 32/32. Headline at display-xxl 52px/700 on the left; request-form-card on the right.

**`hero-band-dark`** — the rare black hero. Background ink, text on-dark, same display-xxl scale; CTA inverts to the white secondary pill.

**`category-button`** — the horizontal-scroll category row. Background canvas-soft, text ink, label at body-sm-strong, padding 8/16, shape pill. An icon precedes the label.

**`faq-row`** — the FAQ accordion item. Background canvas, question at body-md-strong, padding 16/0. No card chrome — hairline dividers between rows.

**`app-download-pill`** — the "Download the Rider app" pill. Background ink, text on-dark, label at body-md-strong, padding 12/20, shape pill.

**`icon-button-circular`** — the round icon container used in the nav and inside the ride-request card. Background canvas-soft, dark icon, shape full. No label.

### Links

**`link-blue`** — the system-default browser-blue link inside legal / footer fine print. Text `#0000ee`, body-md.
**`link-on-dark`** — the white link inside dark bands.
**`link-mute`** — the muted gray link inside footer columns (hairline-mid).
**`link-mute-soft`** — the lightest gray link, for low-priority secondary text on dark surfaces (mute).

## Do's and Don'ts *(as captured from the reference)*

### Do

- Reserve `#000000` for every primary CTA pill. One black pill per visible viewport is the brand's whole conversion story.
- Use 999px on every interactive element (buttons, chips, app pills). The pill IS the geometric signature.
- Render cards at 16px — promo cards, content cards, the ride-request form card, the annual-showcase card all share this radius.
- Set every headline in a display token at weight 700 in sentence-case. The display face never carries body copy.
- Use polarity-flipped black promo bands mid-page to break up white-on-white rhythm. The polarity shift IS the depth cue.
- Anchor every promo card with a 4:3 editorial illustration; never use generic stock imagery.

### Don't

- Don't introduce a second brand accent colour (orange, blue, green). The reference UI is black-and-white plus grayscale; new accents flatten the system. *(SITTS scopes this to chrome — see `DESIGN.md` §"App surface".)*
- Don't render the primary CTA as a 16px rectangle except inside the larger ride-request flow, where `button-large-rounded` is the documented exception.
- Don't use all-caps display headlines. Sentence-case is the voice; uppercase is restricted to rare eyebrow tags.
- Don't drop a soft drop-shadow on every card. Level 0 flat is the default; shadow is reserved for the floating pill and the ride-request form.
- Don't reduce the brand to its illustration system alone. The pill geometry + black/white duet carries the brand even without illustrations.
- Don't tighten or loosen letter-spacing on the display face. Default tracking is part of the voice.
- Don't use 9999px for square cards — pill 999px and full 9999px are identical for interactive elements, but cards stay at 16px.
