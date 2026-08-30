---
name: check-fa-translations
description: Research whether a book has an official Persian translation and cache the result (translated yes/no, and its official Persian title if so) so a later publish never re-researches it. Use when asked to check translations, check translated_fa, research a book's translation status, or after adding new books whose translation status is still null/unknown.
---

# Check Persian translation status

`books.meta.json`'s `translated_fa` field drives the "no official Persian
translation" seal badge on the site (`index.html`'s `.no-fa`). Every new book
starts at `null` (unchecked) — `build_site.py`'s `seed_meta()` only ever seeds
it as a placeholder. Nothing fills in the real value automatically — that's
what this skill does, and it works whether the book is already published,
already sitting in `books.meta.json` unpublished, or hasn't even been fed to
the podcast generator yet.

The result is cached at `~/Downloads/notebookLM/_translation_research.json` —
shared with the `book_podcast` generator repo, keyed by the same slug
`books.meta.json` uses. `build_site.py`'s `seed_meta()` reads that cache on
every publish and fills in `translated_fa` (and `title_fa`, from the official
translation, when translated) for any book that doesn't already have its own
value — so research done today needs no repeat once the book is actually
turned into a podcast and published.

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
3. Record the verdict:
   - Translated: `python3 check_translations.py --register <slug> true "<official Persian title>"`
   - Not translated: `python3 check_translations.py --register <slug> false`
   - If genuinely uncertain, register nothing — leave it for a later pass
     rather than guessing.
   `--register` writes the cache immediately, and — if the slug is already in
   `books.meta.json` — applies it there too unless the book already has its
   own value for that field (a hand edit always wins).
4. Report a short table: book → verdict → source used for each.
5. If anything changed in `books.meta.json` (not just the cache), ask before
   committing/pushing — it's read live by the published site.

## Why not fully automatic

Whether a translation is "official" is a judgment call (a bookstore listing
vs. a review article vs. a pirated PDF), so this stays a research step done
with WebSearch, not a deterministic lookup. `check_translations.py` only
handles the bookkeeping half: previewing slugs, listing what's pending,
syncing the cache into `books.meta.json`, and writing a verdict once you've
actually decided it. `build_site.py` does the same sync automatically on
every publish, so a book researched ahead of time never needs it repeated.
