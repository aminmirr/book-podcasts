"""Only send what the release doesn't already have.

Every file of a book was re-uploaded on every run: removing two episodes from Show
Your Work re-sent the fourteen untouched ones plus both zips, about an hour. The queue
now republishes automatically whenever a book finishes, so this happens unattended.

Run: python3 test_upload_skip.py
"""
import importlib.util
import json
import tempfile
import types
from pathlib import Path

s = importlib.util.spec_from_file_location("bs", Path(__file__).with_name("build_site.py"))
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

tmp = Path(tempfile.mkdtemp())


def f(name, size):
    p = tmp / name
    p.write_bytes(b"x" * size)
    return p


a, b, c = f("a.m4a", 100), f("b.m4a", 200), f("c.m4a", 300)


# ── the decision ──────────────────────────────────────────────────────────────

# same name, same size → already there
assert m.to_upload([a], {"a.m4a": 100}) == []

# same name, different size → the file changed, send it
assert m.to_upload([a], {"a.m4a": 99}) == [a]

# not on the release at all → send it
assert m.to_upload([a], {"b.m4a": 100}) == [a]

# mixed: only the ones that differ or are absent
assert m.to_upload([a, b, c], {"a.m4a": 100, "b.m4a": 999}) == [b, c]

# nothing known → everything uploads, which is the old behaviour
assert m.to_upload([a, b, c], {}) == [a, b, c]

# --force-upload ignores a perfect match: the escape hatch for a truncated asset
assert m.to_upload([a, b], {"a.m4a": 100, "b.m4a": 200}, force=True) == [a, b]

# and the count the run reports is just the difference
uploads = [a, b, c]
todo = m.to_upload(uploads, {"a.m4a": 100})
assert (len(uploads) - len(todo), len(todo)) == (1, 2)


# ── reading the release ───────────────────────────────────────────────────────

def stub_gh(returncode=0, stdout=""):
    m.subprocess = types.SimpleNamespace(
        run=lambda *a, **kw: types.SimpleNamespace(returncode=returncode, stdout=stdout))


stub_gh(stdout=json.dumps({"assets": [{"name": "a.m4a", "size": 100},
                                      {"name": "b.m4a", "size": 200}]}))
assert m.release_assets("tag", "o/r") == {"a.m4a": 100, "b.m4a": 200}

# a release with no assets yet
stub_gh(stdout=json.dumps({"assets": []}))
assert m.release_assets("tag", "o/r") == {}
stub_gh(stdout=json.dumps({"assets": None}))
assert m.release_assets("tag", "o/r") == {}

# every failure falls back to "know nothing", so everything uploads — the safe
# default is the old behaviour, and skipping is what has to be earned
stub_gh(returncode=1, stdout="")                       # no such release / no network
assert m.release_assets("tag", "o/r") == {}
stub_gh(stdout="not json at all")
assert m.release_assets("tag", "o/r") == {}
stub_gh(stdout=json.dumps({"assets": [{"name": "a.m4a"}]}))   # missing size
assert m.release_assets("tag", "o/r") == {}

# and that fallback really does mean "upload everything"
assert m.to_upload([a, b, c], m.release_assets("tag", "o/r")) == [a, b, c]

print("ok")
