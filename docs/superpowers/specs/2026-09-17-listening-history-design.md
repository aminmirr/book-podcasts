# Resume playback & listening history

**Date:** 2026-09-17
**Component:** `index.html`

## Problem

The site remembers nothing about a returning listener except language, playback
speed and their public votes. Close the tab mid-chapter and the next visit starts
that episode from zero — on a book with a dozen chapters, finding your place again
means scrubbing by ear. There's also no way to see, at a glance, which chapters
you've actually finished versus skimmed.

## Scope

Same-device only. No login, no accounts, no cross-device sync, no backend. Pure
`localStorage`, matching how `abs-lang`, `abs-rate` and `abs-voter` already work.
Two things this adds:

1. **Resume** — reopening an episode you'd started picks up where you left off.
2. **History** — episodes you've finished are visibly marked, and a "continue
   listening" row surfaces what's in progress.

Not in scope: recommendations, syncing across devices, anything server-side. If a
listener clears site data or switches browsers, history is gone — that's accepted,
not a bug.

## Data model

One `localStorage` key, `abs-history`, holding a JSON object keyed by **episode
audio URL** (`tr.src` — already unique per book, chapter and language, and stable
per the README's permanent-links guarantee):

```json
{
  "https://github.com/.../04-8-Learn-to-Take-a-Punch_en.m4a": {
    "position": 812.4,
    "duration": 1400.2,
    "played": false,
    "at": 1758100000000,
    "slug": "show-your-work",
    "lang": "en",
    "kind": "chapter",
    "idx": 3,
    "book": "Show Your Work!",
    "label": "Chapter 4 — Learn to Take a Punch"
  }
}
```

`book`/`label`/`lang` are denormalized (not re-derived from the live DOM) because
`LANG` is a single global toggle — `render()` only keeps one language's chapter
list mounted at a time (`split()` reads `book.episodes[langKey()]`). An entry
recorded in English must still be renderable while the site is currently showing
Persian, so the continue-listening row can't depend on DOM state matching the
entry's language.

Keying by URL rather than by chapter key (the language-agnostic id used for deep
links) is deliberate: English and Persian versions of the same chapter are
different recordings. Finishing one must not mark the other as heard, and each
needs its own resume position since durations differ.

No pruning. Total episode count across the whole catalogue is in the low hundreds;
the resulting JSON is trivially small.

## Writing

On the existing `audio` element's `timeupdate` listener, throttled to persist at
most once per ~5s (`timeupdate` fires ~4x/sec — writing every tick is wasted
work), plus unconditionally on `pause`, `ended`, and `beforeunload`. Each write
upserts `position`, `duration`, `at` for `cur().src`.

`played` is set `true` on `ended`, or when `position / duration >= 0.95` (covers
players that never quite reach a clean `ended`, e.g. a source with trailing
silence trimmed oddly). Sticky once true — later partial replays never revert it.

## Resuming

In `load()`, after `loadedmetadata` fires: look up `abs-history[tr.src]`. If it
exists, isn't `played`, and `position` is more than a few seconds in, seek
`audio.currentTime` to it. Otherwise start at 0. This is the same hook already
used for keep-your-place-across-language-switch (`resume()` at line ~1086), so it
covers deep links and normal chapter clicks for free — no separate code path.

A `played` episode always restarts at 0 when clicked again; the "finished" state
means completion is a permanent badge, not a rewindable position.

## UI

**Continue listening row.** A horizontal strip below the search/category chips,
above the book list. Built from `abs-history` entries where `played` is false and
`position` clears the same "meaningful" threshold used for resuming, sorted by
`at` descending, capped at 8. Each card: cover, book title, episode label,
progress (`position/duration`). Hidden entirely when empty (first-time visitors
see nothing new).

Clicking a card resumes playback at the saved position. If the entry's `lang`
differs from the currently displayed `LANG`, switch first — reusing the existing
`$("[data-setlang]")` click handler's keep-position logic rather than duplicating
it — then start the track from `book.episodes[lang]` (available regardless of
which language is currently rendered; no DOM rebuild required beyond the normal
language switch).

**Book-level continue.** Each book card's `whole` button (top of the card —
today it always plays the standalone whole-book overview episode) is the de
facto "play this book" affordance, since a book has no single continuous
audiobook track — the overview and each chapter are independent episodes. When
a book has *any* in-progress `abs-history` entry (whole-book or a chapter,
whichever this slug's entries most recently had `at` touched), the button
resumes that specific episode at its saved position instead of restarting the
overview, and its label reflects that ("Continue: Chapter 4" instead of "Whole
Book"). This reuses the exact same resume-a-specific-track path as a
continue-listening card click — same lookup, same cross-language handling — just
triggered from the book card instead of the row. A book with nothing in
progress behaves exactly as it does today: the button plays the overview.

Once every episode in a book is `played`, the button reverts to its current
behavior (plays the overview from 0) — there's nothing left to "continue."

Needs one new string in both the `EN` and `FA` dictionaries (alongside the
existing `whole`, `chapters`, `showToc`, ... entries) — a "Continue" label to
pair with the resumed episode's own name.

**Played marks.** A small dot/check on each chapter row and the whole-book row
in `paintSpines()`'s existing per-book loop, when `abs-history[url].played` is
true for that row's URL under the *currently displayed* language only — an
English listen must not mark the Persian row.

## Testing

Extract the pure decisions into small standalone functions and cover them the
way `test_search.js` already covers this file's other pure logic — no framework,
node-run assertions, DOM and `fetch` untouched:

- `shouldMarkPlayed(position, duration)` — true at `ended`, true at ≥95%, false
  below it, false on zero/garbage duration.
- `shouldResume(entry)` — false when missing, false when `played`, false when
  `position` is negligible, true otherwise.
- continue-listening selection: filters out `played`, sorts by `at` desc, caps
  at 8.
- `mostRecentInProgress(slug)` — given the history map and a book slug, returns
  the entry with the latest `at` among that slug's unplayed, meaningfully-started
  entries, or `null`. Backs both the continue-listening row and the book-level
  continue button, so it's tested once.

`test_history.js`, new file, same style as `test_search.js`.

## What this does not change

No new `books.meta.json` fields, no new Supabase tables, no change to
`manifest.json` or `build_site.py`. Votes and suggestions are untouched — this is
a second, unrelated `localStorage`-only feature that happens to sit next to the
existing `abs-voter` id without using it.
