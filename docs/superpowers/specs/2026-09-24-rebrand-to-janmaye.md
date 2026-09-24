# Rebrand to جان‌مایه (Janmaye)

**Date:** 2026-09-24
**Components:** `book-podcasts` (site repo), a new `janmaye` repo, `notebooklm_book_podcast` (generator repo)

## Problem

The site needs a real name. "book-podcasts" was always a placeholder repo
name, never a brand. The new name is **جان‌مایه** (Jān-māye — "essence" /
"the vital core of something"), transliterated **Janmaye** for the
English UI and the URL.

The live site must move to a new address, but the *old* address
(`aminmirr.github.io/book-podcasts/`) can't just disappear — it's already
been shared/bookmarked. GitHub does not auto-redirect Pages URLs on a
repo rename (verified against GitHub's own docs), so the old address
needs a real page at it: a static handoff notice with a link to the new
site.

Separately: the site currently hosts 390 episodes' worth of audio as
GitHub Release assets under `aminmirr/book-podcasts`. Nothing about a
rebrand justifies moving or re-uploading any of that — it should keep
living exactly where it is, forever, regardless of where the *site*
itself moves to.

## Decisions made during design

- **New repo, not a rename.** GitHub's automatic rename-redirect breaks
  the moment a *new* repo is created at the old name (verified via
  GitHub's docs) — and a stub page at the old name is exactly a new
  repo-content-at-old-name situation. Renaming in place and then trying
  to add a stub would fight its own redirect. So: `book-podcasts` is kept
  exactly as it is (never renamed, never vacated), and a brand new repo
  `janmaye` becomes the live site going forward.
- **Audio hosting never moves.** All existing and all future episode
  audio uploads keep targeting `aminmirr/book-podcasts`'s Releases,
  unconditionally forever. This required noticing that `build_site.py`
  currently derives *both* "where do I write output files" and "which
  repo do I upload audio to" from the same source
  (`SITE_DIR = Path(__file__).resolve().parent`) — those two concerns
  get decoupled (see below) so moving the site's output location doesn't
  drag audio hosting along with it.
- **`janmaye` gets its own real, independently-generated `manifest.json`/
  `books.meta.json`**, not a copy that needs manual syncing and not a
  live cross-origin fetch from `book-podcasts` on every page load. The
  existing automation (`book_queue.py` → `build_site.py`) simply runs
  against `janmaye` going forward, exactly as it always has against
  `book-podcasts` — same pipeline, no new manual step, no runtime
  coupling between the two sites.
- **Full git history carried over** into `janmaye` via a full clone
  (not a fresh init) — the specs, plans, and commit history documenting
  how this site was actually built are worth keeping, and there's no
  downside to a private development history following the rebrand.

## Design

### 1. `book_podcasts`'s `build_site.py`: decouple upload target from output location

Today:
```python
SITE_DIR = Path(__file__).resolve().parent
...
def owner_repo() -> str:
    url = subprocess.run(["git", "-C", str(SITE_DIR), "remote", "get-url", "origin"], ...).stdout.strip()
    ...
```
`owner_repo()` derives the upload target from wherever the script
physically lives. That coupling is incidental, not load-bearing — fix:
```python
SITE_DIR = Path(__file__).resolve().parent      # unchanged: output files follow the script's location
AUDIO_REPO = "aminmirr/book-podcasts"            # new: audio upload target, pinned regardless of SITE_DIR

def owner_repo() -> str:
    return AUDIO_REPO
```
Once `build_site.py` itself lives inside `janmaye` (see migration below),
`SITE_DIR` naturally resolves to `~/develpment/janmaye`, so
`manifest.json`/`books.meta.json` are written and read there — while
every `gh release upload`/`gh release view` call still targets
`aminmirr/book-podcasts`, unconditionally.

### 2. `janmaye` repo: full mirror of `book-podcasts`, then rebrand

Created as a genuinely new GitHub repo, seeded via a full clone of
`book-podcasts` (all history, all files — `index.html`, `build_site.py`,
every test file, `docs/`, `covers/`, the existing `manifest.json`/
`books.meta.json` with all 390 working episode URLs already in them),
remote repointed at `janmaye`, then:

- `index.html`: `T.fa.mark` → `"جان‌مایه"`, `T.en.mark` → `"Janmaye"`,
  `<title>`, `document.title` (both LANG branches), meta `description`,
  `og:title`, `og:description`, `og:url`, `og:image` → updated to the
  new name/address. Footer `#repoLink` href and the `REPO_URL` constant
  (used for the suggestion dialog's GitHub issue links) → point at
  `github.com/aminmirr/janmaye`.
- `build_site.py`: the `AUDIO_REPO` decoupling above.
- `README.md`: live URL and repo references updated.
- `manifest.json` / `books.meta.json`: **untouched** — they already
  contain 390 working `book-podcasts` release URLs from the mirror; nothing
  needs regenerating for existing episodes.
- GitHub Pages enabled on the new repo (same settings as
  `book-podcasts`: serve from `main`, root).

### 3. `book-podcasts`: becomes a static handoff page

Its `index.html` is replaced with a minimal page reusing the real site's
visual language (dark background, the same type/color tokens) — not a
bare unstyled page:

- Bilingual notice (Persian primary, matching the real site's default):
  the site moved, here's the new address.
- One large button linking to `https://aminmirr.github.io/janmaye/`.
- Preserves deep links: if the old URL was visited with a hash
  (`#slug` or `#slug/chapter`), the button's target includes that same
  hash, so a bookmarked chapter link still lands on the right chapter at
  the new address instead of dropping the visitor on the homepage.
- `build_site.py`, its Python test counterparts, and anything else that
  assumed this repo runs live automation are removed from the working
  tree (kept in git history, not deleted from the record — just no
  longer part of what a visitor or a future maintainer sees as "the
  active thing here"). `manifest.json`, `books.meta.json`, and `covers/`
  stay, as an honest record of what's still actually hosted here (the
  audio).

### 4. Generator repo (`notebooklm_book_podcast`): repoint `SITE_DIR`

- `config.py`: `SITE_DIR = Path.home() / "develpment/janmaye"` (was
  `book-podcasts`).
- `CLAUDE.md`: update prose references to the site repo's name/location.
- No other code changes — `book_queue.py`/`book_queue_app.py` already
  read `SITE_DIR` indirectly via `gen.config.SITE_DIR`, never hardcode
  the name themselves (confirmed by the earlier audit).

## What this does not change

Nothing about the generator's audio pipeline, quota handling, profile
management, or chapter logic. Nothing about the 390 existing episodes'
URLs — they keep working exactly as they do today, forever, hosted where
they already are. No re-upload of any existing audio.

## Known pre-existing issue, not in scope

`books.meta.json` has two `"cover"` entries that are absolute local
filesystem paths instead of the relative `covers/...` path every other
entry uses — already broken today (those two covers don't render for
any visitor), unrelated to this migration, not fixed here.

## Testing

`node test_search.js && node test_history.js` in `janmaye` (mirrored,
unaffected by the rebrand edits — pure text/URL changes). Manual: both
sites load, `janmaye` shows the new brand and a working player,
`book-podcasts` shows the handoff page and its button lands on the right
place, including with a chapter hash appended to the old URL.
