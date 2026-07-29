# Book Podcasts

Static site listing AI-generated podcast summaries of books (English + Persian),
made with [NotebookLM](https://notebooklm.google.com/). Audio is hosted on this
repo's **GitHub Releases** (one release per book); the site is just `index.html`
reading `manifest.json`.

## Publish / update

```bash
python build_site.py "Show-your-work"   # one book (dir name under ~/Downloads/notebookLM)
python build_site.py --all              # every book with audio
git add manifest.json && git commit -m "publish" && git push
```

`build_site.py` transcodes each book's `.m4a` files to 64k mono AAC (transparent
for speech, ~4× smaller than NotebookLM's 256k stereo), uploads them as Release
assets, and rewrites its `manifest.json` entry. Then commit the manifest — the
audio never enters git. Requires `ffmpeg`.

## Editing book details

Two data files, on purpose:

- **`manifest.json`** — *generated* by `build_site.py`. Episodes, URLs, durations.
  Don't hand-edit; it gets overwritten on every publish. These facts are certain.
- **`books.meta.json`** — *yours to edit*. Keyed by book slug, with fields you control:

  ```json
  "show-your-work": {
    "title_en": "Show Your Work!",   // English title (shown bold)
    "title_fa": "کارت را نشان بده",   // Persian title
    "author":   "Austin Kleon",
    "cover":    "covers/show-your-work.jpg",  // repo path OR full https:// URL
    "note_en":  "One-line description in English",
    "note_fa":  "توضیح کوتاه به فارسی"
  }
  ```

  Edit any of these, `git commit && git push`, done. **These edits are never
  touched by `build_site.py`** — it only *adds* stubs for new books, so your
  edits survive every re-publish and every change to `index.html`.

**Covers:** drop an image in `covers/` (e.g. `covers/show-your-work.jpg`) and set
`cover` to that path, or point `cover` at any external image URL. Leave it `""`
for no cover. Missing/broken images just render without a cover — no breakage.
