# Bolder spine + solid CTA

**Date:** 2026-09-19
**Component:** `index.html`

## Problem

The site's one real signature element — the chapter spine, where segment
width already encodes actual chapter length — is visually too quiet to
read as a deliberate piece of information design at a glance; it currently
looks more like a faint decorative bar than a bar chart. The primary play
button (`.whole`, used for both "Full summary" and the "Continue: …"
button) is outline-only until something is actively playing, so the
site's single most important call-to-action has no visual weight by
default.

Prompted by looking at `wtfpod.com/podcast` for redesign inspiration
(see `docs/research/wtfpod.com/DESIGN_TOKENS.md`): its confidence comes
almost entirely from bold, flat color used deliberately rather than any
decoration. The scope here is narrow on purpose — borrow that confidence
by turning up contrast on what already exists, not by importing new
components. No new colors, no layout change, no RTL-sensitive change.

## Design

Two CSS-only changes in `index.html`, both are `color-mix()` opacity
bumps on already-existing rules.

### Spine (`.seg`)

```css
.seg{ background:color-mix(in srgb,var(--accent) 30%,transparent); }   /* was 17% */
.seg:hover{ background:color-mix(in srgb,var(--accent) 55%,transparent); }   /* was 40% */
.seg[data-done="1"]{ background:color-mix(in srgb,var(--accent) 60%,transparent); }   /* was 34% */
.seg[data-now="1"]{ background:color-mix(in srgb,var(--accent) 30%,transparent); }   /* was 22% */
```

`data-now`'s new value (30%) intentionally matches the new base value
rather than exceeding it by much, because `.seg-fill` — the solid-accent
overlay that shows actual live playback position within the currently
loaded segment — sits on top of it. Pushing `data-now` much past base
would reduce the contrast between "container" and "live progress," making
the spine harder to read while something is actually playing, which
defeats the point.

Unchanged: `26px` height, `2px` border-radius, `2px` gap between
segments, the `.seg-fill` solid overlay itself, all hover/focus
mechanics.

### Primary CTA (`.whole`)

Currently:
```css
.whole{ background:none; color:var(--paper); border:1px solid var(--line); ... }
.whole:hover{ border-color:var(--accent); color:var(--accent); }
.whole[data-on="1"]{ background:var(--accent); border-color:var(--accent); color:var(--ink); }
```

New: the `[data-on="1"]` treatment becomes the default, and hover changes
from a color/border swap to a brightness bump on the already-filled
button — the same pattern this file already uses for `.btn-primary` in
the suggestion dialog (`filter:brightness(1.08)`), not a new hover idiom:

```css
.whole{ background:var(--accent); color:var(--ink); border:1px solid var(--accent); ... }
.whole:hover{ filter:brightness(1.08); }
```

`[data-on="1"]`'s CSS rule becomes byte-for-byte identical to the new
default, so it should be **removed** rather than kept as dead CSS.
`paintSpines()`'s JS should keep setting `dataset.on` exactly as it does
today — that JS is now inert with respect to the button's appearance, but
touching it is out of scope here: it's shared logic that also drives
`R.continueBtn`'s highlight (from the listening-history feature), and
removing the attribute write is a separate, unrelated cleanup this spec
isn't asking for.

The download-link icon (`.whole-dl`) and the `<small>` duration/checkmark
text inside `.whole` are unaffected — no contrast issue, since duration
text was already legible on `--paper`-on-transparent and stays legible on
`--ink`-on-accent (same contrast direction the existing `[data-on="1"]`
state already proved out).

## Testing

Visual-only change, no new logic, nothing for `test_search.js` or
`test_history.js` to cover. Manual check: load the site, confirm the
spine reads as a clear bar chart at rest (not just on hover/play), confirm
a finished chapter's segment is visibly more filled than an unplayed one,
confirm the "Full summary" and "Continue: …" buttons are solid-accent by
default rather than only while playing, confirm hover no longer changes
border/text color (only brightness), confirm nothing regresses at the
mobile breakpoint (`.whole{ width:100%; }` already exists and is
untouched).

## What this does not change

No new components, no new CSS custom properties, no layout/spacing
change, no RTL-specific behavior (nothing here is direction-sensitive),
no change to the listening-history feature's logic — only the visual
weight of two things that already existed.
