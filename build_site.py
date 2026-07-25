#!/usr/bin/env python3
"""
Publish a book's podcast audio to GitHub Releases and refresh manifest.json.

Usage:
    python build_site.py "Show-your-work"                 # one book
    python build_site.py --all                            # every book under BOOKS_ROOT
    python build_site.py --all --no-shrink                # upload already-compressed files as-is

Audio (GBs) goes to Releases (one release per book, tag=book-<slug>); the repo
only holds index.html + manifest.json. Idempotent: re-running re-uploads with
--clobber and rewrites the book's manifest entry. Owner/repo come from the git
remote, so the asset URLs are always correct.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BOOKS_ROOT = Path.home() / "Downloads" / "notebookLM"
SITE_DIR = Path(__file__).resolve().parent
MANIFEST = SITE_DIR / "manifest.json"
LANGS = ("English", "Persian")


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def owner_repo() -> str:
    url = subprocess.run(
        ["git", "-C", str(SITE_DIR), "remote", "get-url", "origin"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    # git@github.com:owner/repo.git  or  https://github.com/owner/repo(.git)
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    if not m:
        sys.exit(f"can't parse owner/repo from remote: {url}")
    return m.group(1)


def episode_title(filename: str) -> str:
    stem = re.sub(r"_(en|fa)$", "", Path(filename).stem)
    if stem == "whole_book":
        return "Full-book overview"
    stem = re.sub(r"^\d+-", "", stem)          # drop merge-order prefix "03-"
    stem = re.sub(r"^\d+(½)?-?", "", stem)      # drop leftover chapter number
    return stem.replace("-", " ").strip() or filename


def shrink(src: Path, dst_dir: Path) -> Path:
    """Transcode to 64k mono AAC (transparent for speech, ~4x smaller). Keeps the
    filename so the release asset name / URL stays stable."""
    dst = dst_dir / src.name
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src),
         "-c:a", "aac", "-b:a", "64k", "-ac", "1", "-movflags", "+faststart", str(dst)],
        check=True,
    )
    return dst


def audio_files(book_dir: Path, lang: str) -> list[Path]:
    d = book_dir / "output_podcast" / lang
    if not d.is_dir():
        return []
    # whole_book first, then numeric order
    return sorted(d.glob("*.m4a"), key=lambda p: (not p.stem.startswith("whole_book"), p.name))


def publish_book(book_name: str, repo: str, do_shrink: bool = True) -> dict | None:
    book_dir = BOOKS_ROOT / book_name
    files = {lang: audio_files(book_dir, lang) for lang in LANGS}
    if not any(files.values()):
        print(f"  skip {book_name}: no audio")
        return None

    slug = slugify(book_name)
    tag = f"book-{slug}"
    title = book_name.replace("-", " ")

    # create the release once (ignore "already exists")
    subprocess.run(
        ["gh", "release", "create", tag, "--repo", repo, "--title", title,
         "--notes", f"Podcast audio for {title}"],
        capture_output=True, text=True,
    )

    all_paths = [p for ps in files.values() for p in ps]
    with tempfile.TemporaryDirectory() as tmp:
        if do_shrink:
            print(f"  shrinking {len(all_paths)} file(s) to 64k mono AAC ...")
            uploads = [shrink(p, Path(tmp)) for p in all_paths]
        else:
            uploads = all_paths  # already compressed — upload as-is (lossless)
        print(f"  uploading to release {tag} ...")
        subprocess.run(
            ["gh", "release", "upload", tag, "--repo", repo, "--clobber", *map(str, uploads)],
            check=True,
        )

    base = f"https://github.com/{repo}/releases/download/{tag}"
    episodes = {
        lang: [{"title": episode_title(p.name), "url": f"{base}/{p.name}"} for p in ps]
        for lang, ps in files.items() if ps
    }
    return {"slug": slug, "title": title, "episodes": episodes}


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"books": []}


def main() -> None:
    args = sys.argv[1:]
    do_shrink = "--no-shrink" not in args
    args = [a for a in args if a != "--no-shrink"]
    if not args:
        sys.exit(__doc__)
    repo = owner_repo()

    if args == ["--all"]:
        names = sorted(p.name for p in BOOKS_ROOT.iterdir() if (p / "output_podcast").is_dir())
    else:
        names = args

    manifest = load_manifest()
    by_slug = {b["slug"]: b for b in manifest["books"]}
    for name in names:
        entry = publish_book(name, repo, do_shrink)
        if entry:
            by_slug[entry["slug"]] = entry

    manifest["books"] = sorted(by_slug.values(), key=lambda b: b["title"])
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {MANIFEST} ({len(manifest['books'])} book(s))")


if __name__ == "__main__":
    main()
