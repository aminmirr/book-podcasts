# Book Podcasts — now جان‌مایه (Janmaye)

**The site has moved: https://aminmirr.github.io/janmaye/** — its code and publishing are
maintained in the [`janmaye`](https://github.com/aminmirr/janmaye) repo.

This repo is kept alive on purpose. It does two jobs, and both are permanent.

## What still lives here

| What | Where | Why it stays |
|------|-------|--------------|
| **The audio** | **GitHub Releases**, one release per book, tag `book-<slug>` | Every episode's URL is `https://github.com/aminmirr/book-podcasts/releases/download/book-<slug>/<file>.m4a`. Those links are baked into the site, into shared links and into people's bookmarks, so the releases must never move or be deleted. New episodes are still uploaded here. |
| **A handoff page** | `index.html`, served at https://aminmirr.github.io/book-podcasts/ | A static, Persian-only notice pointing to the new address. It keeps a deep-link hash (`#slug` or `#slug/chapter`), so an old bookmarked chapter still lands on the right place at the new site. It is `noindex`. |
| **A snapshot of the data** | `manifest.json`, `books.meta.json`, `covers/` | Left as they were at the move, as an archive. Nothing reads them any more — the live copies are in `janmaye`. |
| Icons | `icon.png`, `logo.png`, `og.png`, `seal-badge.png` | Used by the handoff page. |

Audio is 64k mono AAC (~4× smaller than NotebookLM's 256k stereo, transparent for
speech): one whole-book episode plus one per chapter, in English and Persian where
available, and a zip per language per book (`<slug>-en.zip`, `<slug>-fa.zip`).

## Do not

- **Delete or rename a release or its assets.** That breaks every existing link.
- **Edit `manifest.json` or `books.meta.json` here.** Nothing reads them; changes belong
  in `janmaye`.
- **Turn off GitHub Pages** without a replacement redirect — old links to
  `aminmirr.github.io/book-podcasts/` would 404 instead of forwarding.

## Publishing new audio

Not done from this repo. The generator (`notebooklm-skill/book_podcast`, see its
`BOOK_PODCAST_README.md`) finishes a book, then runs `janmaye/build_site.py`, which
transcodes the audio, uploads it **to this repo's Releases** (`AUDIO_REPO =
"aminmirr/book-podcasts"` in that script) and rewrites `janmaye`'s manifest. The
dashboard's publish wizard (`p`) asks for the titles, author, cover and categories, then
pushes `janmaye`.

## History

`build_site.py`, `check_translations.py` and the Python and JS test suites used to live
here; they moved to `janmaye` (commit `a0f179c`) and remain in this repo's git history.
The previous README described the full site — search, deep links, likes and suggestions,
the `books.meta.json` fields — and is recoverable with `git show a0f179c^:README.md`.
`janmaye/README.md` is the maintained version of that documentation.
