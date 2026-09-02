"""translated_fa can be researched ahead of time and cached, so a book never
needs re-research once it's actually turned into a podcast and published.

Exercises check_translations.py's cache (apply_cached, predict_slug,
--register/--list) and build_site.py's seed_meta() picking the same cache up
automatically on publish.

Runs against temp files — never the live books.meta.json or the shared
~/Downloads/notebookLM/_translation_research.json.
Run: python3 test_translation_research.py
"""
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bs = load("bs", "build_site.py")
ct = load("ct", "check_translations.py")

tmp = Path(tempfile.mkdtemp())


# ── apply_cached: fills only what's unset ─────────────────────────────────────

e = {"translated_fa": None, "title_fa": ""}
changed = ct.apply_cached(e, {"translated_fa": True, "title_fa": "جامعه باز و دشمنان آن"})
assert changed == ["translated_fa", "title_fa"], changed
assert e == {"translated_fa": True, "title_fa": "جامعه باز و دشمنان آن"}

# a hand-set value is never overwritten
e = {"translated_fa": False, "title_fa": "عنوان دستی"}
changed = ct.apply_cached(e, {"translated_fa": True, "title_fa": "چیز دیگر"})
assert changed == [], changed
assert e == {"translated_fa": False, "title_fa": "عنوان دستی"}

# translated_fa=false needs no title
e = {"translated_fa": None, "title_fa": ""}
changed = ct.apply_cached(e, {"translated_fa": False})
assert changed == ["translated_fa"], changed
assert e["title_fa"] == ""

# note_fa fills in the same way, and is independent of translated_fa/title_fa
e = {"translated_fa": True, "title_fa": "عنوان دستی", "note_fa": ""}
changed = ct.apply_cached(e, {"translated_fa": True, "title_fa": "چیز دیگر", "note_fa": "خلاصه‌ی تازه"})
assert changed == ["note_fa"], changed
assert e["title_fa"] == "عنوان دستی"           # untouched, hand-set
assert e["note_fa"] == "خلاصه‌ی تازه"           # filled, was empty

# an existing note_fa is never overwritten either
e = {"translated_fa": None, "note_fa": "خلاصه‌ی قبلی"}
changed = ct.apply_cached(e, {"translated_fa": False, "note_fa": "خلاصه‌ی جدید"})
assert changed == ["translated_fa"], changed
assert e["note_fa"] == "خلاصه‌ی قبلی"


# ── predict_slug matches the generator's real slug chain ──────────────────────

assert ct.predict_slug("Chris-Brooks-Introductory-Econometrics-for-Finance-2008.pdf") == \
    "chris-brooks-introductory-econometrics-for-finance-2008"
assert ct.predict_slug("Some Book Title.pdf") == "some-book-title"


# ── --register / --list against isolated files ────────────────────────────────

ct.META = tmp / "books.meta.json"
ct.RESEARCH_FILE = tmp / "_translation_research.json"
ct.META.write_text(json.dumps({
    "known-book": {"title_en": "Known Book", "title_fa": "", "author": "A", "translated_fa": None},
}))

ct.cmd_register("known-book", True, "کتاب معروف")
meta = json.loads(ct.META.read_text())
assert meta["known-book"]["translated_fa"] is True
assert meta["known-book"]["title_fa"] == "کتاب معروف"
research = json.loads(ct.RESEARCH_FILE.read_text())
assert research["known-book"] == {"translated_fa": True, "title_fa": "کتاب معروف",
                                   "checked_at": research["known-book"]["checked_at"]}

# registering a slug not in books.meta.json yet only touches the cache
ct.cmd_register("future-book", False, None)
meta = json.loads(ct.META.read_text())
assert "future-book" not in meta
research = json.loads(ct.RESEARCH_FILE.read_text())
assert research["future-book"]["translated_fa"] is False
assert "title_fa" not in research["future-book"]

# --list syncs a still-null book from the cache automatically
ct.META.write_text(json.dumps({
    "future-book": {"title_en": "Future Book", "title_fa": "", "author": "B", "translated_fa": None},
}))
real_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    ct.cmd_list()
    out = sys.stdout.getvalue()
finally:
    sys.stdout = real_stdout
assert "synced from cache: future-book" in out, out
meta = json.loads(ct.META.read_text())
assert meta["future-book"]["translated_fa"] is False


# ── the actual CLI: --register ... --note "..." ────────────────────────────────

ct.META.write_text(json.dumps({
    "note-book": {"title_en": "Note Book", "title_fa": "", "note_fa": "", "translated_fa": None},
}))
sys.argv = ["check_translations.py", "--register", "note-book", "true", "عنوان رسمی",
            "--note", "این یک خلاصه‌ی آزمایشی است."]
ct.main()
meta = json.loads(ct.META.read_text())
assert meta["note-book"]["title_fa"] == "عنوان رسمی"
assert meta["note-book"]["note_fa"] == "این یک خلاصه‌ی آزمایشی است."
research = json.loads(ct.RESEARCH_FILE.read_text())
assert research["note-book"]["note_fa"] == "این یک خلاصه‌ی آزمایشی است."

# --note also works standing alone with a false verdict (no title needed)
ct.META.write_text(json.dumps({
    "note-book-2": {"title_en": "Note Book 2", "title_fa": "", "note_fa": "", "translated_fa": None},
}))
sys.argv = ["check_translations.py", "--register", "note-book-2", "false", "--note", "خلاصه‌ی دوم."]
ct.main()
meta = json.loads(ct.META.read_text())
assert meta["note-book-2"]["translated_fa"] is False
assert meta["note-book-2"]["note_fa"] == "خلاصه‌ی دوم."


# ── seed_meta() applies the same cache automatically at publish time ──────────

bs.META = tmp / "site_meta.json"
bs.TRANSLATION_RESEARCH_FILE = tmp / "_translation_research.json"  # the same cache file
bs.META.write_text(json.dumps({}))
research = json.loads(bs.TRANSLATION_RESEARCH_FILE.read_text())
research["brand-new-book"] = {"translated_fa": True, "title_fa": "کتاب کاملا جدید",
                               "note_fa": "خلاصه‌ی کتاب کاملا جدید."}
bs.TRANSLATION_RESEARCH_FILE.write_text(json.dumps(research))

manifest = {"books": [
    {"slug": "future-book", "title": "Future Book", "episodes": {}},
    {"slug": "brand-new-book", "title": "Brand New Book", "episodes": {}},
]}
bs.seed_meta(manifest)
seeded = json.loads(bs.META.read_text())
assert seeded["future-book"]["translated_fa"] is False          # from the earlier --list sync
assert seeded["brand-new-book"]["translated_fa"] is True        # picked up on first publish
assert seeded["brand-new-book"]["title_fa"] == "کتاب کاملا جدید"
assert seeded["brand-new-book"]["note_fa"] == "خلاصه‌ی کتاب کاملا جدید."

print("ok")
