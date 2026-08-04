# Book Podcasts

A static site listing AI-generated podcast summaries of books (English + Persian),
made with [NotebookLM](https://notebooklm.google.com/).

**Live:** https://aminmirr.github.io/book-podcasts/ · GitHub Pages off `main`.

Each book has one **whole-book** episode (standalone overview) plus one episode
**per chapter**. Two languages per book where available.

## How it's put together

| Layer | Where | Notes |
|-------|-------|-------|
| Site | `index.html` (single file, no build step) | Reads `manifest.json` + `books.meta.json` at load |
| Audio | **GitHub Releases** (one release per book, tag `book-<slug>`) | 64k mono AAC; never enters git |
| Generated data | `manifest.json` | episodes, URLs, **durations** — do not hand-edit |
| Editable data | `books.meta.json` | titles, author, cover, notes, categories, chapter titles |
| Covers | `covers/*` | referenced from `books.meta.json` |
| Logo | `logo.png` (master) → `icon.png`, `og.png` | favicon + social preview; regenerate the two from the master, don't edit them |
| Likes + suggestions | **Supabase** (anon key + RLS) | see below |

## Publish / update audio

```bash
python build_site.py                       # list books, pick one
python build_site.py tukey                 # any distinct part of the folder name
python build_site.py --all                 # every book with audio
```

Drop the cover image in `covers/` first. After uploading, the script asks for the
book's titles (EN/FA), author, cover (pick from a numbered list of `covers/`, or paste
a URL) and up to 3 categories, writes them into `books.meta.json`, then offers to
commit and push. It only asks about books that don't already have an author and a
cover, so republishing is silent. Everything else — chapter titles, notes — stays a
file edit.

`build_site.py` transcodes each `.m4a` to 64k mono AAC (~4× smaller than NotebookLM's
256k stereo, transparent for speech), reads durations via `ffprobe`, uploads them as
Release assets with a progress bar, and rewrites the book's `manifest.json` entry.
Requires `ffmpeg`. It also **seeds** `books.meta.json` with a stub for any new book
(never overwriting existing edits).

Files that are already ~64k mono upload untouched, so republishing never re-encodes
good audio (`--no-shrink` forces that for every file). Book names are matched loosely
— `tukey` finds `Exploratory-Data-Analysis--John-W-Tukey` — but never guessed: an
ambiguous or unknown name exits instead of creating an empty release under a typo.

## Editing book details — `books.meta.json`

`manifest.json` is generated (overwritten on every publish); `books.meta.json` is
**yours** and is never overwritten. Keyed by book slug:

```json
"show-your-work": {
  "title_en": "Show Your Work!",              // English title (shown bold)
  "title_fa": "کارت را نشان بده",              // Persian title
  "author":   "Austin Kleon",
  "cover":    "covers/show-your-work.jpg",     // repo path OR full https:// URL
  "note_en":  "One-line description",
  "note_fa":  "توضیح کوتاه",
  "categories": ["Creativity", "Career"],      // up to 3; clickable filters on the site
  "chapters": {                                 // per-chapter title overrides (EN/FA)
    "00-A-New-Way-of-Operating": { "title_en": "A New Way of Operating", "title_fa": "" }
  }
}
```

Edit, `git commit && git push`, done. `build_site.py` uses `setdefault` everywhere,
so it only **adds** missing keys — your edits always survive a republish.

- **Chapter titles:** keyed by chapter key (the filename minus `_en`/`_fa`), shared by
  both languages. English is pre-filled from filenames; add `title_fa` for Persian.
- **Covers:** drop an image in `covers/` and point `cover` at it, or use any `https://`
  URL. Missing/broken images just render without a cover.
- **Categories:** ≤3 per book. They become clickable chips that filter the list.

## Site features

- Reading-room design (Newsreader serif + Vazirmatn, one amber/verdigris accent),
  bilingual EN/FA with RTL, per-chapter **spine** sized by listening length.
- Per-book **like / dislike** and a **suggest a book** flow (GitHub issue *or*
  anonymous Supabase form).
- **Mobile player** (≤680px): a custom expanded/collapsed player that opens expanded
  when you play something and auto-collapses when you scroll or interact elsewhere.
  Desktop keeps the compact bottom bar. Both have 15s skip + playback speed.

## Likes & suggestions (Supabase)

Static sites can't store data, so votes/suggestions use a Supabase project via its
**anon public key** (safe to ship in the browser — gated by Row-Level Security).

- Config lives in `index.html` (`SB_URL`, `SB_KEY`).
- Tables: `votes` (one row per `slug`+browser `voter`, value ±1; anon can read/insert/
  update, **not delete**) and `suggestions` (anon can **insert only** — visitors cannot
  read others' suggestions; you read them in the Supabase dashboard → Table Editor).
- The `service_role` key is **never** used here and must stay secret.

Reading incoming suggestions: Supabase dashboard → **Table Editor → `suggestions`**.
