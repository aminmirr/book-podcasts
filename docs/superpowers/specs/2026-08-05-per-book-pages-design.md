# Per-book pages

**Date:** 2026-08-05
**Component:** `index.html`, `build_site.py` (book-podcasts)

## Problem

The site is one `index.html` listing every book. Three things follow from that:

- **Every shared link previews identically.** One `og:title` and one `og:image` for the
  whole site, so a link to Show Your Work looks the same as a link to Die with Zero.
  Social crawlers do not run JavaScript, so no client-side routing can fix this — a
  distinct preview needs a distinct file.
- **A book entry cannot grow.** Anything added to one book is added to the scroll
  length of all of them.
- **Browsing is scrolling.** Eight books today, more coming.

Wanted alongside these: type in the search box, see matching things listed under it,
click one, land on that thing's page.

Explicitly *not* a goal: search-engine ranking. It may follow, but nothing here is
designed for it.

## The governing constraint

Loading a new file stops audio. On a podcast site that is the dominant force: a
listener browsing while an episode plays must not have it cut off. So the site keeps
one running application and swaps views in place, while still exposing one real file
per book for the crawlers that need one.

## Design

### URLs and files

```
/                          index — dense rows
/book/<slug>/              book page
/app.css  /app.js          shared by both
```

`build_site.py` generates `book/<slug>/index.html` at publish time. Each is a **thin
shell**: `<title>`, `og:title`, `og:description`, `og:image` (the book's cover) and
`og:url` baked in, plus the shared `app.css` and `app.js`.

The shell deliberately does **not** bake in the book's content. It fetches
`manifest.json` and `books.meta.json` at runtime exactly as the index does today.
Editing a title, cover or note therefore still appears immediately with no
regeneration; only the preview card lags until the next publish, and those fields
change rarely. Baking content in would create a silent staleness trap where the page
and the JSON disagree.

Both routes into a URL are first-class:

| Entry | Behaviour |
|---|---|
| Direct visit or shared link | The real file loads. Crawlers read the OG tags. The app renders the book. |
| Click inside the site | `pushState` swaps the view. No file load, **audio continues.** Back and forward work via `popstate`. |

### Index

Dense rows, one per book: cover thumbnail, title, author, chapter count, total
duration, and the spine bar. The whole row is the link to the book page. The current
search-and-category filtering stays.

### Book page

Everything a list entry shows today, given room: large cover, both titles, author,
categories, votes, whole-book play, download-all, chapter list open by default,
per-chapter copy-link and download.

Two additions, both derived from existing data — nothing new to write by hand:

- **Both languages at once.** Persian and English chapter lists side by side rather
  than only the one matching the toggle. Many books are uneven (Show Your Work: 6
  English, 3 Persian); showing both states plainly what exists instead of hiding half
  of it behind a control.
- **Also in this category.** A strip of books sharing a category, from `categories`
  already in `books.meta.json`, so the end of a page offers somewhere to go.

### Search

Typing opens a panel beneath the box: matching books first, then matching chapters
grouped under their book. Click a book to open its page; click a chapter to open its
page with that chapter loaded. Enter dismisses the panel and leaves the index filtered
to the matches — today's behaviour, unchanged.

Matching reuses `matchBook()` and the Persian folding in `norm()`, already covered by
`test_search.js`.

### Old links must not rot

The hash links shipped on 2026-08-04 (`#show-your-work/04-8-Learn-to-Take-a-Punch`)
are superseded by `/book/show-your-work/#04-8-Learn-to-Take-a-Punch`. On load, a hash
in the old shape redirects to the new path. Anything already shared keeps working.

## Costs, accepted

- **`index.html` stops being self-contained.** CSS and JS move to `app.css` / `app.js`
  so book pages share them instead of duplicating ~60 KB each. `build_site.py` becomes
  a build step for the site, not only a publisher, and the README's "single file, no
  build step" claim must be corrected.
- **A new book's page exists only after a publish.**
- **No JavaScript means no content.** Crawlers get their preview tags; a human with JS
  disabled sees an empty page. True today as well, now across more URLs.

## Rejected: hash-only routing

`#/book/<slug>` needs no generated files and keeps audio playing, but crawlers ignore
the fragment and would keep showing the generic site card. It fails the first
requirement outright.

## Rejected: full multi-page, no shared shell

One real page per book with no client-side routing is the simplest thing that could
work and gives perfect previews, but every navigation stops playback. Rejected on the
governing constraint.

## Build order

Three steps, each shippable alone:

1. Routing, book pages, dense index. (This is the risky one — it touches everything.)
2. Search dropdown.
3. Related books and the dual-language chapter lists.

## Testing

- `test_search.js` continues to lift its subject out of the source, so extracting
  `app.js` must keep the matching functions greppable in the same shape.
- A new `test_pages.py` asserts, for each generated shell: it exists for every book in
  the manifest, its `og:image` resolves to a real cover path or an absolute URL, its
  `og:url` matches its own location, and it references `app.css` / `app.js` by a path
  that resolves from its own depth.
- Browser checks per step: audio survives an in-app navigation; back and forward land
  on the right view; a direct load of `/book/<slug>/` renders the book; an old-format
  hash link redirects to its new path.
