#!/usr/bin/env python3
"""Research cache for books.meta.json's translated_fa / title_fa / note_fa.

Deciding whether a book has an official Persian translation needs real
research (a bookstore/publisher listing, not a review article), and a good
~100-word summary needs someone (Claude) to actually read/know the book —
that's what the check-fa-translations skill does. This script is the
bookkeeping half:

  --list                                    what still needs research (and
                                             syncs anything the cache can
                                             already answer)
  --register <slug> true <title_fa> [--note "..."]   record a confirmed
                                             translation, optionally with a
                                             ~100-word Persian summary
  --register <slug> false [--note "..."]    record a confirmed
                                             non-translation, same --note
  --slug-for <pdf-path>                     preview the slug a PDF will get
                                             once it goes through the
                                             podcast pipeline

The cache lives at BASE_OUTPUT_DIR/_translation_research.json — shared with
the book_podcast generator repo (same ~/Downloads/notebookLM directory it
already uses for _profiles.json/_errors.jsonl) — precisely so a book can be
researched before it has even been fed to the generator. build_site.py's
seed_meta() reads the same file and applies it automatically the first time
that book is published, so registering ahead of time means no repeat
research later.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

META = Path(__file__).parent / "books.meta.json"
RESEARCH_FILE = Path.home() / "Downloads" / "notebookLM" / "_translation_research.json"


def load_meta() -> dict:
    return json.loads(META.read_text())


def save_meta(meta: dict) -> None:
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def load_research() -> dict:
    return json.loads(RESEARCH_FILE.read_text()) if RESEARCH_FILE.exists() else {}


def save_research(research: dict) -> None:
    RESEARCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = RESEARCH_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(research, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(RESEARCH_FILE)


def apply_cached(entry: dict, cached: dict) -> list[str]:
    """Fill in an unset books.meta.json entry from a cached result. Never
    overwrites a value someone already set by hand."""
    changed = []
    if entry.get("translated_fa") is None and cached.get("translated_fa") is not None:
        entry["translated_fa"] = cached["translated_fa"]
        changed.append("translated_fa")
    if not entry.get("title_fa") and cached.get("title_fa"):
        entry["title_fa"] = cached["title_fa"]
        changed.append("title_fa")
    if not entry.get("note_fa") and cached.get("note_fa"):
        entry["note_fa"] = cached["note_fa"]
        changed.append("note_fa")
    return changed


def predict_slug(pdf_path: str) -> str:
    """Mirrors notebooklm_book_podcast_multi.py's book_name_from_pdf() followed
    by build_site.py's slugify() — the two steps that turn a PDF filename into
    the slug books.meta.json will eventually use. A preview, not a guarantee:
    if the two ever drift apart, or the PDF gets renamed before it's run,
    check the real slug in books.meta.json once the book is published and
    re-register under that key."""
    stem = Path(pdf_path).stem
    stem = re.sub(r"-[a-z]{4,8}$", "", stem)
    stem = re.sub(r"[^\w\s-]", "", stem)
    stem = re.sub(r"[\s_]+", "-", stem.strip())[:60]
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def cmd_list() -> None:
    meta = load_meta()
    research = load_research()

    synced = []
    for slug, entry in meta.items():
        if entry.get("translated_fa") is not None:
            continue
        cached = research.get(slug)
        if cached and (changed := apply_cached(entry, cached)):
            synced.append((slug, changed))
    if synced:
        save_meta(meta)
        for slug, changed in synced:
            print(f"synced from cache: {slug} ({', '.join(changed)})")

    pending = {slug: e for slug, e in meta.items() if e.get("translated_fa") is None}
    if not pending:
        print("Nothing pending — every book has translated_fa set.")
        return
    print("\nNeeds research:" if synced else "Needs research:")
    for slug, e in pending.items():
        print(slug)
        print(f"  title_en: {e.get('title_en', '')}")
        print(f"  title_fa: {e.get('title_fa', '')}")
        print(f"  author:   {e.get('author', '')}")


def cmd_register(slug: str, translated: bool, title_fa: str | None, note_fa: str | None = None) -> None:
    if translated and not title_fa:
        sys.exit("registering translated_fa=true needs the official Persian title")

    research = load_research()
    record = {"translated_fa": translated, "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if translated:
        record["title_fa"] = title_fa
    if note_fa:
        record["note_fa"] = note_fa
    research[slug] = record
    save_research(research)
    summary = f"translated_fa={translated}"
    if translated:
        summary += f", title_fa={title_fa!r}"
    if note_fa:
        summary += f", note_fa=({len(note_fa.split())} words)"
    print(f"cached: {slug} -> {summary}")

    meta = load_meta()
    if slug not in meta:
        print("not in books.meta.json yet — will apply automatically once this book is published")
        return
    changed = apply_cached(meta[slug], record)
    if changed:
        save_meta(meta)
        print(f"applied to books.meta.json: {', '.join(changed)}")
    else:
        print("books.meta.json already has its own value(s) here — left untouched")


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] == "--list":
        cmd_list()
    elif args[0] == "--register" and len(args) >= 3:
        slug, verdict, *rest = args[1:]
        if verdict.lower() not in ("true", "false"):
            sys.exit("verdict must be true or false")
        note_fa = None
        if "--note" in rest:
            i = rest.index("--note")
            note_fa = rest[i + 1] if i + 1 < len(rest) else None
            rest = rest[:i] + rest[i + 2:]
        title_fa = rest[0] if rest else None
        cmd_register(slug, verdict.lower() == "true", title_fa, note_fa)
    elif args[0] == "--slug-for" and len(args) == 2:
        print(predict_slug(args[1]))
    else:
        sys.exit(
            "Usage:\n"
            "  check_translations.py --list\n"
            "  check_translations.py --register <slug> true <persian-title> [--note \"...\"]\n"
            "  check_translations.py --register <slug> false [--note \"...\"]\n"
            "  check_translations.py --slug-for <pdf-path>"
        )


if __name__ == "__main__":
    main()
