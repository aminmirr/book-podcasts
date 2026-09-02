---
name: check-fa-translations
description: Research whether a book has an official Persian translation and cache the result (translated yes/no, its official Persian title if so, and a ~100-word Persian summary) so a later publish never re-researches it. Use when asked to check translations, check translated_fa, research a book's translation status, write/shorten a book's summary or note_fa, or after adding new books whose translation status is still null/unknown.
---

# Check Persian translation status + write the summary

`books.meta.json`'s `translated_fa` field drives the "no official Persian
translation" seal badge on the site (`index.html`'s `.no-fa`). Every new book
starts at `null` (unchecked) — `build_site.py`'s `seed_meta()` only ever seeds
it as a placeholder. Nothing fills in the real value automatically — that's
what this skill does, and it works whether the book is already published,
already sitting in `books.meta.json` unpublished, or hasn't even been fed to
the podcast generator yet. While a book is open for this research anyway,
this skill also drafts (or tightens) its `note_fa` — the ~100-word Persian
summary shown under the title on the site — so that doesn't sit at 0 words
or run long later either.

The result is cached at `~/Downloads/notebookLM/_translation_research.json` —
shared with the `book_podcast` generator repo, keyed by the same slug
`books.meta.json` uses. `build_site.py`'s `seed_meta()` reads that cache on
every publish and fills in `translated_fa`, `title_fa` (the official
translation, when translated), and `note_fa` for any book that doesn't
already have its own value — so research done today needs no repeat once the
book is actually turned into a podcast and published.

## Steps

1. Figure out the slug to research:
   - Already in `books.meta.json`? Use that slug — `python3
     check_translations.py --list` prints every book still `null` there,
     with English/Persian titles and author, so you don't have to look it up
     by hand.
   - Not in the pipeline yet (just a candidate book, maybe not even
     downloaded as a PDF)? Use `python3 check_translations.py --slug-for
     <pdf-path>` if a PDF is already in hand — it previews the exact slug
     the generator + site will eventually give it. Otherwise ask the user
     what filename/slug they intend to use, since the cache key has to match
     what `books.meta.json` ends up with or the sync at publish time misses it
     (harmless if it does — the book just falls back to needing research
     again, same as today).
2. WebSearch (English title + author is usually more reliable than a Persian
   title, which may just be a working translation someone made up rather than
   the market's actual name for it) to find whether an **official, published**
   Persian translation exists.
   - **Good evidence**: a listing on a real Iranian bookstore or publisher
     site (iranketab.ir, taaghche.com, fidibo.com, gisoom.com, ketabplus,
     shahreketabonline.com, or a known publisher like نشر ماهی / نشر نی /
     خوارزمی) that names a translator and publisher.
   - **Not evidence**: a news/analysis article that renders the title into
     Persian for its own summary (common for current-events nonfiction, and
     looks like a hit but isn't a translation), an unofficial PDF, or a fan
     translation with no named publisher.
   - When a single search hit is ambiguous, fetch the author's page on a
     bookstore site (e.g. `iranketab.ir/profile/...`) — the store's full list
     of what it carries for that author is stronger evidence than one hit.
3. Check the book's `note_fa` (in `books.meta.json` if it's there, or the
   research cache otherwise): missing, or way over ~100 words? Write one —
   see **The summary** below. Skip this step only if it's already a
   reasonable ~100-word summary (the existing books mostly sit at 95-120
   words; that's fine, don't rewrite something that isn't broken).
4. Record the verdict (and the summary, if you wrote one):
   - Translated: `python3 check_translations.py --register <slug> true "<official Persian title>" [--note "<~100-word summary>"]`
   - Not translated: `python3 check_translations.py --register <slug> false [--note "<~100-word summary>"]`
   - If genuinely uncertain about the translation status, register nothing
     for it — leave it for a later pass rather than guessing. (The summary
     doesn't have that problem — write it regardless of the translation
     verdict.)
   `--register` writes the cache immediately, and — if the slug is already in
   `books.meta.json` — applies each field there too, unless the book already
   has its own value for that field (a hand edit always wins; if you're
   deliberately correcting an existing value — like a summary that's grown
   too long — edit `books.meta.json` directly instead of relying on
   `--register`, which won't overwrite it).
5. Report a short table: book → verdict → source used for each, and note
   which summaries were written or shortened.
6. If anything changed in `books.meta.json` (not just the cache), ask before
   committing/pushing — it's read live by the published site.

## The summary

`note_fa` is what a reader sees under the title before deciding whether to
listen — write it like the existing ones read (see any current entry in
`books.meta.json` for the tone): a hook, the author and real context, the
book's actual core argument or structure, and what kind of reader it's for.
Target ~100 words (the existing books range roughly 95-120; don't chase an
exact number). Same honesty rule as the rest of the site
(`FRONTEND_DESIGN.md`): only what you actually know about the book — no
invented claims, no marketing filler. If you don't know the book well enough
to summarize it accurately, say so instead of guessing.

## Why not fully automatic

Whether a translation is "official" is a judgment call (a bookstore listing
vs. a review article vs. a pirated PDF), and a good summary needs someone
who's actually read/knows the book — so both stay a step done by Claude, not
a deterministic lookup. `check_translations.py` only handles the bookkeeping
half: previewing slugs, listing what's pending, syncing the cache into
`books.meta.json`, and writing a verdict (translation status, title, and
summary) once you've actually produced it. `build_site.py` does the same
sync automatically on every publish, so research done ahead of time never
needs to be repeated.
