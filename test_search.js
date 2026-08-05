/* Search matching, pulled straight out of index.html so it can't drift.
   Run: node test_search.js */
const assert = require("assert");
const fs = require("fs");

const html = fs.readFileSync(__dirname + "/index.html", "utf8");

// Lift the real source of norm() and matchBook() rather than retyping them.
const grab = (start, end) => {
  const i = html.indexOf(start);
  assert.ok(i > 0, "not found in index.html: " + start);
  const j = html.indexOf(end, i);
  return html.slice(i, j + end.length);
};
const src = grab("const norm =", '.replace(/\\s+/g, " ").trim();')
          + "\n" + grab("function matchBook(b){", "\n}");

// Minimal stand-ins for the page globals matchBook closes over.
const ctx = { META: {}, Q: "", LANG: "en" };
const harness = `
  ${src}
  const bookCats = slug => (META[slug] && META[slug].categories) || [];
  const split = b => ({ chapters: b.chapters || [] });
  const chTitle = (slug, c) => c.title;
  module.exports = { norm, matchBook, setQ: v => { Q = norm(v); } };
`;
const mod = { exports: {} };
new Function("META", "module", "let Q;" + harness)(ctx.META, mod);
const { norm, matchBook, setQ } = mod.exports;

/* ---- norm(): the Persian folding that makes the box usable at all ---- */
assert.strictEqual(norm("خلاصه‌های"), "خلاصه های", "ZWNJ folds to a space");
assert.strictEqual(norm("كتاب يك"), "کتاب یک", "Arabic ك/ي fold to Persian ک/ی");
assert.strictEqual(norm("  Show   YOUR  Work "), "show your work");
assert.strictEqual(norm(null), "");

/* ---- matchBook() ---- */
const BOOK = { slug: "syw", title: "Show your work",
               chapters: [{ title: "Learn to Take a Punch" },
                          { title: "Teach What You Know" }] };
ctx.META.syw = { title_en: "Show Your Work!", title_fa: "کارت را نشان بده",
                 author: "Austin Kleon", note_en: "On sharing your process",
                 categories: ["Creativity", "Career"] };

const hit = q => { setQ(q); return matchBook(BOOK); };

assert.strictEqual(hit("").viaChapter, false, "empty query matches everything");
assert.ok(hit("kleon"), "author");
assert.ok(hit("SHOW YOUR"), "title, case-insensitive");
assert.ok(hit("creativity"), "category");
assert.ok(hit("sharing"), "note");
assert.ok(hit("نشان"), "Persian title");
assert.ok(hit("کارت را نشان"), "Persian phrase");

// a chapter-only hit is flagged so the book's list gets opened
const ch = hit("punch");
assert.ok(ch && ch.viaChapter === true, "chapter hit must be flagged");
assert.strictEqual(hit("kleon").viaChapter, false, "header hit must not be flagged");

assert.strictEqual(hit("beekeeping"), null, "no match returns null");
assert.strictEqual(hit("zzz"), null);

// the folding must actually pay off end to end
ctx.META.syw.title_fa = "خلاصه‌های کتاب";
assert.ok(hit("خلاصه های"), "typing a space finds a ZWNJ title");
assert.ok(hit("كتاب"), "Arabic keyboard finds Persian text");

console.log("ok");
