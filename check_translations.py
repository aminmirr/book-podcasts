#!/usr/bin/env python3
"""Bookkeeping for books.meta.json's translated_fa field.

Deciding whether a book has an official Persian translation needs real
research (a bookstore/publisher listing, not a review article) — this script
only does the mechanical part: `--list` finds books still unchecked (None),
`--set` records the verdict once you (or Claude, via the check-fa-translations
skill) have actually verified it.
"""
import json
import sys
from pathlib import Path

META = Path(__file__).parent / "books.meta.json"


def load() -> dict:
    return json.loads(META.read_text())


def save(meta: dict) -> None:
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def cmd_list(meta: dict) -> None:
    pending = {slug: e for slug, e in meta.items() if e.get("translated_fa") is None}
    if not pending:
        print("Nothing pending — every book has translated_fa set.")
        return
    for slug, e in pending.items():
        print(slug)
        print(f"  title_en: {e.get('title_en', '')}")
        print(f"  title_fa: {e.get('title_fa', '')}")
        print(f"  author:   {e.get('author', '')}")


def cmd_set(meta: dict, slug: str, raw_value: str) -> None:
    if slug not in meta:
        sys.exit(f"no such book: {slug}")
    lookup = {"true": True, "false": False, "null": None}
    key = raw_value.lower()
    if key not in lookup:
        sys.exit("value must be true, false, or null")
    meta[slug]["translated_fa"] = lookup[key]
    save(meta)
    print(f"{slug}: translated_fa -> {lookup[key]}")


def main() -> None:
    args = sys.argv[1:]
    meta = load()
    if not args or args[0] == "--list":
        cmd_list(meta)
    elif args[0] == "--set" and len(args) == 3:
        cmd_set(meta, args[1], args[2])
    else:
        sys.exit(
            "Usage:\n"
            "  check_translations.py --list\n"
            "  check_translations.py --set <slug> true|false|null"
        )


if __name__ == "__main__":
    main()
