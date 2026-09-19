# Site polish pass: bolder spine, draggable scrub, wider layout, continue-button fix

**Date:** 2026-09-19
**Component:** `index.html`

Four independent, small changes gathered in one session: a visual-confidence
pass inspired by looking at wtfpod.com (spine + CTA), plus three real usage
problems found by actually using the site on a 13" MacBook — a scrub bar
that's hard to grab, wasted margin on a laptop-sized screen, and a layout
regression from the listening-history feature's continue button. Each
change is independent and can ship/be reverted on its own.

## Change 1: Bolder spine + solid CTA

### Problem

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

### Design

Two CSS-only changes, both `color-mix()` opacity bumps on already-existing
rules.

**Spine (`.seg`):**

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
segments, the `.seg-fill` solid overlay itself, all hover/focus mechanics.

**Primary CTA (`.whole`):**

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

### Testing

Visual-only, no new logic. Manual check: spine reads as a clear bar chart
at rest, a finished chapter's segment is visibly more filled than an
unplayed one, both play-button variants are solid-accent by default,
hover changes brightness only (not color/border), mobile's
`.whole{ width:100%; }` still holds.

---

## Change 2: Draggable scrub thumb

### Problem

`#scrub` (`index.html:1175-1180`) only has a `click` handler and no
visible handle — `.player-scrub-fill` is a bare growing bar, `.player-scrub`
itself is 3px tall. There's nothing to visually grab, and nothing to drag:
clicking jumps to a position, but you can't press and drag to scrub through
the episode. Reported directly: "not easy reachable... add a circle button
in exact position of right now playing so I can grab it."

Scoped to the **desktop player bar** only (`#scrub`/`#player`) — the
mobile player (`#mplayer`, shown ≤680px) has its own progress display
(`.mp-fill`) that was never interactive in the first place (mobile relies
on the ±15s skip buttons); adding drag-to-seek there is a separate,
unrequested change.

### Design

Add a visible thumb, always shown (not just on hover — the complaint is
about discoverability, not clutter), and replace the click-only handler
with pointer-based press-drag-release, using
[Pointer Events](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events)
so mouse, touch, and pen all work through one code path.

**Markup** — one new child of `#scrub`, alongside the existing fill:
```html
<div class="player-scrub" id="scrub" role="slider" tabindex="0"
     aria-label="Seek" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
  <div class="player-scrub-fill" id="scrubFill"></div>
  <div class="player-scrub-thumb" id="scrubThumb"></div>
</div>
```

**CSS** — thumb sized as an obvious, easy grab target; visual size stays
modest but the interactive area is bigger than the visual dot (a common,
deliberate mismatch — see MDN's touch-target guidance), via a transparent
padding trick rather than an oversized visible circle:

```css
.player-scrub{ height:3px; background:var(--line); cursor:pointer; position:relative; touch-action:none; }
.player-scrub-thumb{
  position:absolute; inset-block-start:50%; inset-inline-start:0;
  width:12px; height:12px; margin-inline-start:-6px; border-radius:50%;
  background:var(--accent); transform:translateY(-50%);
  box-shadow:0 0 0 8px transparent; /* invisible, enlarges the hit area without enlarging the dot */
  transition:box-shadow .15s ease;
}
.player-scrub:hover .player-scrub-thumb,
.player-scrub-thumb:active{ box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 20%,transparent); }
```

`inset-inline-start` (not `left`) so the thumb's position flips correctly
under `dir="rtl"` automatically, matching the file's existing logical-
property convention.

**JS** — replace the `click` listener with pointer drag, reusing the
existing RTL-aware x-calculation rather than duplicating it:

```js
function scrubRatio(clientX){
  const r=$("#scrub").getBoundingClientRect();
  const x = document.dir==="rtl" ? r.right-clientX : clientX-r.left;
  return Math.min(Math.max(x/r.width,0),1);
}
function seekTo(ratio){
  if(!audio.duration) return;
  audio.currentTime = ratio*audio.duration;
  $("#scrubFill").style.width=(ratio*100)+"%";
  $("#scrubThumb").style.insetInlineStart=(ratio*100)+"%";
}
let scrubbing=false;
$("#scrub").addEventListener("pointerdown",e=>{
  if(!audio.duration) return;
  scrubbing=true; e.currentTarget.setPointerCapture(e.pointerId);
  seekTo(scrubRatio(e.clientX));
});
$("#scrub").addEventListener("pointermove",e=>{ if(scrubbing) seekTo(scrubRatio(e.clientX)); });
$("#scrub").addEventListener("pointerup",()=>{ scrubbing=false; });
$("#scrub").addEventListener("pointercancel",()=>{ scrubbing=false; });
$("#scrub").addEventListener("keydown",e=>{
  if(!audio.duration) return;
  if(e.key==="ArrowRight") audio.currentTime=Math.min(audio.duration,audio.currentTime+5);
  else if(e.key==="ArrowLeft") audio.currentTime=Math.max(0,audio.currentTime-5);
  else return;
  e.preventDefault();
});
```

The existing `timeupdate` handler (`index.html:1140`) already sets
`#scrubFill`'s width every tick — it needs one added line to also move the
thumb (`$("#scrubThumb").style.insetInlineStart=p*100+"%"`), so the thumb
tracks normal playback, not just drags. `aria-valuenow` should update
alongside it, in both places (`timeupdate` and `seekTo`), keeping the
`role="slider"` genuinely accurate per this repo's own "real ARIA on
custom controls" rule.

`touch-action:none` on `.player-scrub` stops the browser's native
scroll/zoom gestures from fighting a touch-drag on the bar itself.

### Testing

Manual: click-to-seek still works (a press+release with no movement is
just a zero-distance drag); press-and-drag left/right scrubs live, audio
position follows the drag in real time; thumb visually sits exactly at
current playback position at rest and during normal playback, not just
mid-drag; dragging past either end clamps to 0%/100% rather than throwing;
arrow-left/right seek ±5s when the scrub bar has focus; test under both
`dir="ltr"` and `dir="rtl"` (language toggle) — the thumb and drag
direction must both flip correctly, not just the fill bar.

---

## Change 3: Wider content column on laptop screens

### Problem

`.wrap{ max-width:1000px; ... }` caps the entire page's content column.
On a 13" MacBook — commonly an ~1440px-wide viewport at default scaling —
that leaves roughly 150-200px of empty margin on each side, reported as
"a very big margin." The 1000px cap was chosen for a reading-room feel
appropriate to long-form prose, but the actual content here (book cards,
chapter rows, the spine) is a structured catalog, not continuous prose —
it doesn't need as tight a line-length constraint as an article would.

### Design

One-line change:

```css
.wrap{ max-width:1200px; margin-inline:auto; padding-inline:var(--gutter); }   /* was 1000px */
```

1200px keeps a deliberate cap (this remains a bounded, designed column on
very wide monitors, not edge-to-edge sprawl) while meaningfully closing
the gap on a 13"-class laptop. `--gutter`'s existing `clamp(20px,5vw,64px)`
is untouched — it already scales sensibly and isn't the source of the
complaint.

### Testing

Manual, at a ~1440px browser width (13" MacBook default): confirm the
margin is visibly smaller without the page feeling cramped, chapter rows
and book cards don't feel awkwardly stretched, nothing overflows or wraps
badly at the new width. Also spot-check at a genuinely wide monitor
width (≥1920px) to confirm the cap still reads as intentional, not
accidentally removed.

---

## Change 4: Fix continue-button layout regression

### Problem

Reported: "after adding and enabling continue buttons to books, structure
messed up. continue button is so big that causes buttons and book title
mix with each other. and also width of book descriptions and book title
became so small."

Root cause: `.book-top{ grid-template-columns:1fr auto; }` — the left
(`1fr`) column holds the cover and titles/description, the right (`auto`)
column is `.book-side`, which holds the play button(s) and download link.
`auto` sizes to the *intrinsic* (max-content) width of whatever's inside
it. Before the continue-button feature, `.book-side` held one
non-wrapping pill button; now, when a book has something in progress, it
holds two (`.whole` "Full summary" and a second `.whole` "Continue: …",
both `white-space:nowrap`) side by side in a plain flex row
(`.book-side{ display:flex; gap:10px; }`) with no width limit. A long
"Continue: Chapter 4 — <title>" label balloons the row's natural width,
which balloons the `auto` grid track, which steals space from the `1fr`
title column — exactly the squeeze reported.

### Design

Two changes to `.book-side` and one to `.whole`'s inner label, so the
title column keeps its space regardless of how long a continue-button
label gets:

```css
.book-side{ display:flex; flex-wrap:wrap; gap:10px; align-items:center;
  max-width:260px; justify-content:flex-end; }
```

- `max-width:260px` caps what the grid's `auto` track can claim — this is
  what actually fixes the title-column squeeze, since a grid `auto` track
  sizes from its item's own constrained width, not its unconstrained
  content width.
- `flex-wrap:wrap` lets the two buttons (plus the download icon) drop to
  a second line inside that capped width instead of overflowing it,
  rather than trying to force both onto one cramped row.
- `justify-content:flex-end` keeps the buttons right-aligned (start-
  aligned under RTL, since this is a logical-direction-aware property)
  against the column edge, matching the current visual alignment, whether
  they're on one line or wrapped to two.

```css
.whole{ min-width:0; }
.whole span{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; min-width:0; }
```

`min-width:0` on the flex item itself is required for the inner
`overflow:hidden` to actually take effect — a flex item's default
`min-width:auto` otherwise refuses to shrink below its content's natural
size, which is the standard flexbox truncation gotcha. With this, a long
"Continue: …" label truncates with an ellipsis instead of forcing the
button (and the column) wider — the button never grows past what
`max-width:260px` allows, and the duration/checkmark in the `<small>`
stays fully visible since only the label `<span>` truncates.

Mobile is unaffected but needs one explicit override, since the existing
mobile breakpoint already collapses `.book-top` to a single column and
relies on `.whole{ width:100%; }` for full-width buttons:

```css
@media (max-width:680px){
  .book-side{ max-width:none; }   /* the 260px cap only exists to protect the desktop grid column */
}
```

### Testing

Manual: a book with no in-progress episode (single "Full summary" button)
looks unchanged. A book with a short continue-label fits both buttons on
one line, right-aligned, same as before. A book with a long "Continue:
Chapter N — <long title>" label truncates with an ellipsis rather than
growing the button or squeezing the title column — book title and
description keep their full, pre-existing width in every case. At
mobile width, buttons remain full-width stacked as before (unaffected by
the new cap). Test with the language toggle (RTL) to confirm
`justify-content:flex-end` and the ellipsis both still align/truncate
correctly rather than assuming LTR.

---

## What none of this changes

No new colors, no new components beyond the scrub thumb `<div>` itself,
no change to the listening-history feature's logic (`HISTORY`,
`playHistoryEntry`, `mostRecentInProgress`, etc. — Change 4 only touches
CSS and one flex property, not the JS that decides *when* a continue
button appears), no build step, no new dependencies.
