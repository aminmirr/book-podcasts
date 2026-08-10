# Upload only what changed

**Date:** 2026-08-10
**Component:** `build_site.py`

## Problem

`publish_book()` uploads every file of a book on every run, whether or not anything
about it changed. Removing two episodes from Show Your Work today meant re-uploading
the fourteen that were untouched, plus rebuilding and re-uploading both zips.

Measured on that run: 14 episodes at roughly 30 seconds each, then a 74 MB zip that
alone took over seven minutes. The whole republish took an hour. Show Your Work was
republished twice today, so about 440 MB left the machine to delete two files.

This used to be a manual step taken rarely. It is now automatic: the queue runs
`build_site.py --upload-only` every time a book finishes, and a book that gains one
episode re-uploads its entire back catalogue. Tukey is 482 MB across 48 assets; Show
Your Work is 305 MB across 18.

## Design

Ask the release what it already holds, and skip anything that matches.

```bash
gh release view book-<slug> --repo <repo> --json assets
```

That returns `name` and `size` per asset. An upload is skipped when an asset of the
same name already exists with the same byte count. Everything else uploads as now,
with `--clobber`.

### Size is the comparison, and its ceiling

Two different files of identical byte length would be treated as identical. For
64 kbps AAC of differing speech that is not a practical concern, and the alternative —
hashing — would mean downloading each asset to compare, which costs the bandwidth this
is meant to save. GitHub's asset listing exposes no checksum.

The consequence to accept: if an episode is regenerated and happens to encode to
exactly the same size, the site keeps the old audio. `--force-upload` (below) is the
escape hatch, and the regenerate flow already replaces assets under new keys in
practice.

### Ordering against `shrink()`

The comparison must be against the file that would actually be uploaded, not the
source. A file needing transcode is shrunk first, then compared, so a re-run still
skips the upload but pays the local CPU again. That is the right way round: the
transcode is seconds, the upload is minutes.

In practice this rarely bites. `already_small()` means audio from the generator
uploads untouched, so the local file *is* the asset and its size is known without
doing any work.

### Zips

The same rule covers them with nothing added. `make_zip()` uses `ZIP_STORED` over the
same files in the same order, so an unchanged episode set produces an identical
archive size and the upload is skipped. Change the set — as removing Thank You did —
and the size moves, so it uploads.

### `--force-upload`

Re-upload everything, ignoring what the release reports. This is not hypothetical: a
`gh release upload` for Tukey was killed mid-transfer on 3 August and sat suspended
for seven days. If an asset were truncated at full declared size, only a forced
re-upload would repair it.

### When the listing cannot be read

A missing release, a network failure, or unparseable JSON falls back to uploading
everything. The safe default is the current behaviour; skipping is the optimisation,
so any doubt resolves toward doing the work.

## Reporting

The progress bar counts what is actually being sent, with the saving stated:

```
  uploading to release book-show-your-work ...
  14 of 16 already uploaded — sending 2
  [####################] 2/2  05-10-Stick-Around_fa.m4a
```

A run with nothing to send says so and skips the bar entirely.

## What this does not change

Nothing about the manifest, the metadata prompts, or the commit. `manifest.json` is
still rewritten from the local files on every run, so an episode removed locally still
disappears from the site even though nothing uploads. Skipping uploads must not become
skipping the manifest rewrite — that is what makes a removal take effect.

## Testing

`test_upload_skip.py`, in the shape of `test_categories.py`: assert-based, no network.

- an asset with a matching name and size is skipped; a differing size uploads
- a name absent from the release always uploads
- an empty or unreadable asset listing uploads everything
- `--force-upload` uploads everything even when every size matches
- the reported counts match what was actually sent

The `gh` calls are stubbed; what is under test is the decision, not the transfer.

## Expected effect

A book that gains one episode uploads that episode and two zips instead of its whole
catalogue. For Tukey that is roughly 20 MB instead of 482 MB. A republish where
nothing changed uploads nothing and finishes in the time it takes to list the assets.
