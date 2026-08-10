"""Categories are picked from what's in use, so they stop drifting.

Free-typing produced the mess this fixes: Data alongside Data Science, Finance
alongside Personal Finance, and seven of twelve categories used exactly once.

Runs against a COPY of books.meta.json — never the live file.
Run: python3 test_categories.py
"""
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

s = importlib.util.spec_from_file_location("bs", Path(__file__).with_name("build_site.py"))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

META = {
    "a": {"categories": ["Business", "Management"]},
    "b": {"categories": ["Business", "Data"]},
    "c": {"categories": ["Data Science"]},
    "d": {"categories": []},
}


# ── the list is whatever books use ────────────────────────────────────────────

counts = m.category_counts(META)
assert counts == {"Business": 2, "Data": 1, "Data Science": 1, "Management": 1}, counts
assert list(counts) == sorted(counts), "sorted, so the numbering is stable between runs"
assert m.category_counts({}) == {}


# ── parsing what you type ─────────────────────────────────────────────────────

known = list(counts)                       # Business, Data, Data Science, Management

assert m.parse_categories("1", known) == ["Business"]
assert m.parse_categories("1,4", known) == ["Business", "Management"]
assert m.parse_categories(" 1 , 4 ", known) == ["Business", "Management"]

# a new name is taken as typed
assert m.parse_categories("Design", known) == ["Design"]
# numbers and new names mix in one line
assert m.parse_categories("1, Design", known) == ["Business", "Design"]

# typing an existing name resolves to it whatever the casing — case drift is most of
# how the current mess happened
assert m.parse_categories("business", known) == ["Business"]
assert m.parse_categories("DATA SCIENCE", known) == ["Data Science"]

# capped, and never repeats one
assert m.parse_categories("1,2,3,4", known) == ["Business", "Data", "Data Science"]
assert m.parse_categories("1,1,2", known) == ["Business", "Data"]
assert len(m.parse_categories("a,b,c,d,e", known)) == m.MAX_CATEGORIES

# out-of-range numbers are names, not crashes
assert m.parse_categories("99", known) == ["99"]
assert m.parse_categories("", known) == []


# ── renaming, which is also merging ───────────────────────────────────────────

meta = json.loads(json.dumps(META))
touched = m.rename_category(meta, "Data", "Data Science")
assert touched == ["b"], touched
assert meta["b"]["categories"] == ["Business", "Data Science"]
assert meta["a"]["categories"] == ["Business", "Management"], "other books untouched"
assert m.category_counts(meta)["Data Science"] == 2

# a book holding both names ends up with one, not a duplicate
meta = {"x": {"categories": ["Data", "Data Science"]}}
m.rename_category(meta, "Data", "Data Science")
assert meta["x"]["categories"] == ["Data Science"], meta

# renaming something nobody uses changes nothing
meta = json.loads(json.dumps(META))
assert m.rename_category(meta, "Nope", "Other") == []
assert meta == META

# a book with no categories is not given one
assert "categories" in META["d"] and META["d"]["categories"] == []


# ── the prompt ────────────────────────────────────────────────────────────────

def ask(typed, current=()):
    tmp = Path(tempfile.mkdtemp()) / "books.meta.json"
    tmp.write_text(json.dumps(META))
    m.META = tmp
    sys.stdin = io.StringIO(typed + "\n")
    sys.stdin.isatty = lambda: True
    return m.ask_categories(list(current), META)

assert ask("1, Design") == ["Business", "Design"]
# Enter keeps what the book already had, rather than clearing it
assert ask("", current=["Career"]) == ["Career"]
assert ask("") == []

print("ok")
