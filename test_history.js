/* Listening-history decisions, pulled straight out of index.html so it can't drift.
   Run: node test_history.js */
const assert = require("assert");
const fs = require("fs");

const html = fs.readFileSync(__dirname + "/index.html", "utf8");

const grab = (start, end) => {
  const i = html.indexOf(start);
  assert.ok(i > 0, "not found in index.html: " + start);
  const j = html.indexOf(end, i);
  return html.slice(i, j + end.length);
};
const src = grab("const HISTORY_KEY=", ".slice(0,limit);\n}");

const mod = { exports: {} };
new Function("module", src + "\nmodule.exports = { shouldMarkPlayed, shouldResume, continueEntries, mostRecentInProgress, continueListening };")(mod);
const { shouldMarkPlayed, shouldResume, continueEntries, mostRecentInProgress, continueListening } = mod.exports;

/* ---- shouldMarkPlayed(): finished enough to count as "played" ---- */
assert.strictEqual(shouldMarkPlayed(950, 1000), true, "95% exactly counts as played");
assert.strictEqual(shouldMarkPlayed(940, 1000), false, "94% is not played yet");
assert.strictEqual(shouldMarkPlayed(100, 0), false, "zero duration is never played");
assert.strictEqual(shouldMarkPlayed(0, 0), false);

/* ---- shouldResume(): worth seeking back to on reopen ---- */
assert.strictEqual(shouldResume(null), false, "missing entry never resumes");
assert.strictEqual(shouldResume(undefined), false);
assert.strictEqual(shouldResume({position:100,duration:200,played:true}), false, "finished entries restart at 0");
assert.strictEqual(shouldResume({position:2,duration:200,played:false}), false, "a couple seconds in isn't meaningful");
assert.strictEqual(shouldResume({position:5,duration:200,played:false}), false, "exactly the threshold doesn't count");
assert.strictEqual(shouldResume({position:30,duration:200,played:false}), true);

/* ---- continueEntries()/continueListening()/mostRecentInProgress() ---- */
const history = {
  "a.m4a": {position:30, duration:200, played:false, at:100, slug:"book-a", book:"Book A", label:"Ch 1"},
  "b.m4a": {position:190,duration:200, played:true,  at:200, slug:"book-a", book:"Book A", label:"Ch 2"}, // finished
  "c.m4a": {position:2,  duration:200, played:false, at:300, slug:"book-a", book:"Book A", label:"Ch 3"}, // too early
  "d.m4a": {position:50, duration:300, played:false, at:400, slug:"book-b", book:"Book B", label:"Full"},
};

const entries = continueEntries(history);
assert.strictEqual(entries.length, 2, "only meaningfully-started, unfinished entries survive");
assert.ok(entries.every(e=>e.url), "each entry carries its own url");

const list = continueListening(history);
assert.deepStrictEqual(list.map(e=>e.url), ["d.m4a","a.m4a"], "most recently touched first");

assert.strictEqual(mostRecentInProgress(history,"book-a").url, "a.m4a");
assert.strictEqual(mostRecentInProgress(history,"book-b").url, "d.m4a");
assert.strictEqual(mostRecentInProgress(history,"book-c"), null, "no entries for an unknown slug");

// cap at CONTINUE_ROW_LIMIT (8)
const many = {};
for(let i=0;i<12;i++) many["e"+i+".m4a"] = {position:30,duration:200,played:false,at:i,slug:"x"};
const capped = continueListening(many);
assert.strictEqual(capped.length, 8, "capped at 8");
assert.strictEqual(capped[0].url, "e11.m4a", "most recent of the twelve leads");

console.log("ok");
