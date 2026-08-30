---
name: check-fa-translations
description: Research whether newly added books have an official Persian translation and record it in books.meta.json's translated_fa field. Use when asked to check translations, check translated_fa, or after adding new books whose translation status is still null/unknown.
---

# Check Persian translation status

`books.meta.json`'s `translated_fa` field drives the "no official Persian
translation" seal badge on the site (`index.html`'s `.no-fa`). Every new book
starts at `null` (unchecked) — `build_site.py`'s `seed_meta()` only ever seeds
it as a placeholder (see `build_site.py` around `e.setdefault("translated_fa",
None)`). Nothing fills in the real value automatically. This skill is the
repeatable way to do that.

## Steps

1. Run `python3 check_translations.py --list` in this repo. It prints every
   book still `null`, with its English title, Persian title, and author.
2. If the list is empty, say so and stop — nothing to do.
3. For each book, use WebSearch (English title + author is usually more
   reliable than the Persian title, which may just be a working translation
   we made up, not the market's actual name for it) to find whether an
   **official, published** Persian translation exists.
   - **Good evidence**: a listing on a real Iranian bookstore or publisher
     site (iranketab.ir, taaghche.com, fidibo.com, gisoom.com, ketabplus,
     shahreketabonline.com, or a known publisher like نشر ماهی / نشر نی /
     خوارزمی) that names a translator and publisher.
   - **Not evidence**: a news/analysis article that renders the title into
     Persian for its own summary (this happens a lot for current-events
     nonfiction and looks like a hit but isn't a translation), an unofficial
     PDF, or a fan translation with no named publisher.
   - When a single search hit is ambiguous, fetch the author's page on a
     bookstore site (e.g. `iranketab.ir/profile/...`) — the store's full list
     of what it carries for that author is stronger evidence than one hit.
4. Once confident, record it:
   `python3 check_translations.py --set <slug> true` (translated) or
   `--set <slug> false` (confirmed not translated). If you genuinely can't
   tell either way, leave it `null` — don't guess.
5. Report a short table: book → verdict → the source you used for each.
6. Ask before committing/pushing — `books.meta.json` is read live by the
   published site, same as any other edit to it.

## Why not fully automatic

Whether a translation is "official" is a judgment call (a bookstore listing
vs. a review article vs. a pirated PDF), so this stays a research step a
model does with WebSearch, not a deterministic lookup. `check_translations.py`
only handles the bookkeeping half — listing what's pending and writing the
verdict back atomically once you've actually decided it.
