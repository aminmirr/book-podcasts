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

`build_site.py` uploads each book's `.m4a` files as Release assets and rewrites
its `manifest.json` entry. Then commit the manifest — the audio never enters git.
