# wtfpod.com/podcast — design reference

Extracted via browser inspection (`getComputedStyle`) on 2026-09-18, for
design inspiration on the book-podcasts redesign. **Tokens and structure
only** — no screenshots or copyrighted text/images from the source site are
stored in this repo; episode titles/descriptions below are described
generically, not quoted.

## Fonts

- Display headline (episode titles): `rucksack`, weight 900, ~38px at
  desktop card width, line-height ≈ font-size (very tight, ~1.0).
- Body / UI (nav, date pills, "Listen" links, paragraph text):
  `canada-type-gibson` (fallback `arial, sans-serif`).
- A third family (`freight-sans-pro`) appears somewhere on the page but
  wasn't isolated to a specific element in this pass.

## Colors

- Accent teal (episode-card header block): `rgb(6, 175, 196)` (`#06AFC4`).
- CTA orange ("LISTEN →" link): `rgb(252, 87, 48)` (`#FC5730`).
- Date pill: black background (`rgb(0,0,0)`), white text, uppercase,
  12px / weight 700, letter-spacing 1.2px, padding `4px 10px`, **sharp
  corners (border-radius: 0)**.
- Page background: light grey `rgb(240, 240, 240)` between cards; card
  body itself is white.
- Body text: near-black `rgb(33, 35, 38)` / `rgb(65, 72, 73)` for
  secondary text.

## Card construction

- Each episode card (`<article class="entry">`) has **no border-radius, no
  box-shadow** — flat, blocky. Corners are sharp everywhere on the page.
- The card's "gutter" isn't a CSS `gap` — it's a **15px solid border in the
  page's grey background color** on the article itself. Visually this
  reads as thin grey seams between white cards, not a design pattern
  worth copying literally, but confirms the whole aesthetic avoids
  shadows/radius entirely in favor of flat color blocks and line
  separation.
- Card anatomy, top to bottom: black uppercase date pill → teal block
  containing the white, heavy-weight episode title → white body with a
  short teaser paragraph → an orange "LISTEN →" text link (no button
  chrome, just colored uppercase text + arrow glyph).

## Layout

- Simple 3-column grid of episode cards at desktop width (≥1440px),
  reflowing top-to-bottom. No visible grid gap beyond the border trick
  above.
- Top nav: flat white bar, simple text links, **no scroll-driven
  behavior** — background, shadow, and size are unchanged whether the
  page is scrolled or not (checked at scroll position 600px vs. 0).
- No animations, no scroll-snap, no hover-transition were detected on
  this page in a quick sweep — it's a static, information-dense list,
  not an animated landing page. (Not an exhaustive interaction audit —
  this was a design-tokens pass, not a full clone-website reconnaissance.)

## The one signature element

A hand-lettered, scratchy "WTF" wordmark logo in the header — clearly
custom artwork, not a font. This is the page's one truly bespoke visual
element; everything else (grid, pills, flat cards) is fairly generic
editorial-blog structure carrying a strong personality through color and
type choices alone.
