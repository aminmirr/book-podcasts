# Resume Playback & Listening History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remember, per device, where a listener stopped in an episode and which episodes they've finished — with no login and no backend — and surface it as an automatic resume, a "continue listening" row, played marks in each book's chapter list, and a book-level "continue" button.

**Architecture:** Everything lives in the existing single-file static site, `index.html` (no build step, no framework). One new `localStorage` key, `abs-history`, keyed by episode audio URL, following the same pattern as the site's existing `abs-lang`/`abs-rate`/`abs-voter` keys. A small set of pure decision functions (whether to mark played, whether to resume, which entries are "in progress") get pulled straight from the page source into a new `test_history.js`, the same way `test_search.js` already tests `norm()`/`matchBook()`.

**Tech Stack:** Vanilla JS, no dependencies. Node (no framework) for the two `test_*.js` files.

**Spec:** `docs/superpowers/specs/2026-09-17-listening-history-design.md`

## Global Constraints

- Same-device only. No login, no accounts, no cross-device sync, no backend, no new Supabase tables, no new `books.meta.json` fields, no change to `manifest.json` or `build_site.py`.
- `localStorage` key is `abs-history`, matching the existing `abs-` prefix convention.
- No build step — all code is added directly inside the existing single `<script>` block in `index.html`.
- Pure decision logic must be plain top-level `function` declarations with stable, unique text boundaries, so `test_history.js` can extract them verbatim via the same `grab(start, end)` technique `test_search.js` already uses — never rewrite that technique, reuse it.
- Any new user-facing text needs an entry in both `T.fa` and `T.en`.
- Constants: `RESUME_MIN_SECONDS = 5`, `PLAYED_RATIO = 0.95`, `CONTINUE_ROW_LIMIT = 8`, `HISTORY_WRITE_INTERVAL_MS = 5000`.
- Follow the existing visual language: CSS custom properties (`--accent`, `--haze`, `--line`, `--ink-raise`), existing icon constants (`ICON_PLAY`, `ICON_CHECK`, etc.) — no new fonts, no new color values.
- Every `old_string` given below is the exact current text of `index.html` at the point this plan was written; if a prior task in this plan already changed that region, the step says so explicitly and gives the post-edit text to anchor against.

---

## Task 1: Pure history-decision functions + tests

**Files:**
- Modify: `index.html` (new code block after the `split(book)` function)
- Create: `test_history.js`

**Interfaces:**
- Produces: `shouldMarkPlayed(position, duration) → boolean`, `shouldResume(entry) → boolean`, `continueEntries(history) → Array<entry & {url}>`, `mostRecentInProgress(history, slug) → entry|null`, `continueListening(history, limit=8) → Array<entry & {url}>`. Every later task that touches history reads these.
- Consumes: nothing outside this task.

- [ ] **Step 1: Write the failing test**

Create `test_history.js`:

```js
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd ~/develpment/book-podcasts && node test_history.js`
Expected: `AssertionError` — `not found in index.html: const HISTORY_KEY=` (the source doesn't exist yet).

- [ ] **Step 3: Implement in index.html**

Using Edit, find this exact block:

```
/* split a book's episodes for the current language into {full, chapters[]} */
function split(book){
  const eps = (book.episodes && book.episodes[langKey()]) || [];
  return { full: eps.find(isWhole) || null,
           chapters: eps.filter(e=>!isWhole(e)) };
}
```

Replace it with itself plus this new block appended after it:

```
/* split a book's episodes for the current language into {full, chapters[]} */
function split(book){
  const eps = (book.episodes && book.episodes[langKey()]) || [];
  return { full: eps.find(isWhole) || null,
           chapters: eps.filter(e=>!isWhole(e)) };
}

/* ---------------- listening history (localStorage, same-device only) ----------------
   Resume position + finished/in-progress state, keyed by episode audio URL (unique per
   book, chapter and language). See docs/superpowers/specs/2026-09-17-listening-history-design.md */
const HISTORY_KEY="abs-history";
const RESUME_MIN_SECONDS=5;      // ignore a resume position this close to the start
const PLAYED_RATIO=0.95;         // finished enough to count as "played"
const CONTINUE_ROW_LIMIT=8;

function shouldMarkPlayed(position,duration){
  return !!duration && duration>0 && (position/duration)>=PLAYED_RATIO;
}
function shouldResume(entry){
  return !!entry && !entry.played && (entry.position||0) > RESUME_MIN_SECONDS;
}
function continueEntries(history){
  return Object.keys(history).map(url=>({url,...history[url]})).filter(shouldResume);
}
function mostRecentInProgress(history,slug){
  const list=continueEntries(history).filter(e=>e.slug===slug);
  return list.length ? list.reduce((a,b)=>b.at>a.at?b:a) : null;
}
function continueListening(history,limit=CONTINUE_ROW_LIMIT){
  return continueEntries(history).sort((a,b)=>b.at-a.at).slice(0,limit);
}
```

- [ ] **Step 4: Run it to verify it passes**

Run: `cd ~/develpment/book-podcasts && node test_history.js`
Expected: `ok`

- [ ] **Step 5: Run the existing search test to confirm nothing else broke**

Run: `node test_search.js`
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add index.html test_history.js
git commit -m "$(cat <<'EOF'
Add listening-history decision functions + tests

Pure logic only: whether an episode counts as played, whether a
saved position is worth resuming, and which entries make up
"continue listening". No UI or storage wiring yet.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Kbni88Fed1e2MpJNcainQp
EOF
)"
```

---

## Task 2: Storage plumbing + resume-on-load

**Files:**
- Modify: `index.html`

**Interfaces:**
- Consumes: `shouldMarkPlayed`, `shouldResume` (Task 1); `cur()`, `audio`, `refs`, `LANG` (existing).
- Produces: `loadHistory()`, `saveHistory(history)`, `HISTORY` (the live in-memory map), `recordEntry(tr, position, duration, forcePlayed)`, `maybeRecordProgress()`, `forceRecordProgress(played)`. Tasks 3–5 read/write `HISTORY` through these.

- [ ] **Step 1: Add storage functions, right after Task 1's block**

Using Edit, find:

```
function continueListening(history,limit=CONTINUE_ROW_LIMIT){
  return continueEntries(history).sort((a,b)=>b.at-a.at).slice(0,limit);
}
```

Replace with itself plus:

```
function continueListening(history,limit=CONTINUE_ROW_LIMIT){
  return continueEntries(history).sort((a,b)=>b.at-a.at).slice(0,limit);
}

function loadHistory(){
  const raw=localStorage.getItem(HISTORY_KEY);
  if(!raw) return {};
  try{ return JSON.parse(raw); }catch{ return {}; }
}
function saveHistory(history){ localStorage.setItem(HISTORY_KEY, JSON.stringify(history)); }
const HISTORY = loadHistory();

/* tr is a track object from mkTrack() — carries slug/kind/idx/book/label/src already,
   so nothing needs re-deriving from the DOM. Sticky: once played, stays played. */
function recordEntry(tr, position, duration, forcePlayed){
  const prev = HISTORY[tr.src];
  HISTORY[tr.src] = {
    position, duration,
    played: forcePlayed || (prev && prev.played) || shouldMarkPlayed(position, duration),
    at: Date.now(),
    slug: tr.slug, lang: LANG, kind: tr.kind, idx: tr.idx, book: tr.book, label: tr.label,
  };
  saveHistory(HISTORY);
}

let lastHistoryWriteAt = 0;
const HISTORY_WRITE_INTERVAL_MS = 5000;
function maybeRecordProgress(){
  const tr=cur(); if(!tr || !audio.duration) return;
  const now=Date.now();
  if(now - lastHistoryWriteAt < HISTORY_WRITE_INTERVAL_MS) return;
  lastHistoryWriteAt = now;
  recordEntry(tr, audio.currentTime, audio.duration, false);
}
function forceRecordProgress(played){
  const tr=cur(); if(!tr || !audio.duration) return;
  lastHistoryWriteAt = Date.now();
  recordEntry(tr, audio.currentTime, audio.duration, played);
}
```

- [ ] **Step 2: Wire resume-on-load**

Using Edit, find:

```js
function load(autoplay){
  const tr=cur(); if(!tr) return;
  audio.src=tr.src;
  $("#pTitle").textContent=tr.label; $("#pTitle").classList.remove("err");
  $("#pSub").textContent=tr.book;
  $("#player").classList.add("on"); document.body.classList.add("has-player");
  mpSetTrack(tr); mp.classList.add("on");
  if(autoplay && mIsMobile()) mExpand();            // open expanded when they play something
  $("#prev").disabled = qi<=0;
  $("#next").disabled = qi>=queue.length-1;
  if(autoplay) audio.play().catch(fail);
  paintSpines();
}
```

Replace with:

```js
function load(autoplay){
  const tr=cur(); if(!tr) return;
  audio.src=tr.src;
  $("#pTitle").textContent=tr.label; $("#pTitle").classList.remove("err");
  $("#pSub").textContent=tr.book;
  $("#player").classList.add("on"); document.body.classList.add("has-player");
  mpSetTrack(tr); mp.classList.add("on");
  if(autoplay && mIsMobile()) mExpand();            // open expanded when they play something
  $("#prev").disabled = qi<=0;
  $("#next").disabled = qi>=queue.length-1;
  const histEntry=HISTORY[tr.src];
  if(shouldResume(histEntry)){
    audio.addEventListener("loadedmetadata",()=>{ audio.currentTime=histEntry.position; },{once:true});
  }
  if(autoplay) audio.play().catch(fail);
  paintSpines();
}
```

(`resume()`, used by the language-switch toggle, calls `load(false)` and then adds its own ratio-based `loadedmetadata` listener afterward — that one fires second and wins, which is correct: an explicit language switch should override a stale resume position. No change needed there.)

- [ ] **Step 3: Wire the write hooks**

Using Edit, find:

```js
audio.addEventListener("play",paintSpines);
audio.addEventListener("pause",paintSpines);
audio.addEventListener("error",()=>{ if(audio.src) fail(); });
audio.addEventListener("ended",()=>{
  const tr=cur();
  if(tr){ const R=refs[tr.slug]; if(R&&tr.kind==="chapter") R.segs[tr.idx].dataset.done="1"; }
  if(qi<queue.length-1){ qi++; load(true); } else { paintSpines(); }
});
```

Replace with:

```js
audio.addEventListener("play",paintSpines);
audio.addEventListener("pause",paintSpines);
audio.addEventListener("pause",()=>forceRecordProgress(false));
addEventListener("beforeunload",()=>forceRecordProgress(false));
audio.addEventListener("error",()=>{ if(audio.src) fail(); });
audio.addEventListener("ended",()=>{
  const tr=cur();
  if(tr){ const R=refs[tr.slug]; if(R&&tr.kind==="chapter") R.segs[tr.idx].dataset.done="1"; }
  forceRecordProgress(true);
  if(qi<queue.length-1){ qi++; load(true); } else { paintSpines(); }
});
```

- [ ] **Step 4: Wire the throttled write**

Using Edit, find:

```js
audio.addEventListener("timeupdate",()=>{
  if(!audio.duration) return;
  const p=audio.currentTime/audio.duration;
  $("#scrubFill").style.width=p*100+"%";
  $("#pCur").textContent=clock(audio.currentTime);
  $("#pDur").textContent=clock(audio.duration);
  $$(".mp-fill").forEach(f=>f.style.width=p*100+"%");
  $("#mpCur").textContent=faDigits(clock(audio.currentTime));
  $("#mpDur").textContent=faDigits(clock(audio.duration));
  const tr=cur();
  if(tr&&tr.kind==="chapter"){ const R=refs[tr.slug]; R&&R.fills[tr.idx]&&(R.fills[tr.idx].style.width=p*100+"%"); }
});
```

Replace with the same body plus one line at the end:

```js
audio.addEventListener("timeupdate",()=>{
  if(!audio.duration) return;
  const p=audio.currentTime/audio.duration;
  $("#scrubFill").style.width=p*100+"%";
  $("#pCur").textContent=clock(audio.currentTime);
  $("#pDur").textContent=clock(audio.duration);
  $$(".mp-fill").forEach(f=>f.style.width=p*100+"%");
  $("#mpCur").textContent=faDigits(clock(audio.currentTime));
  $("#mpDur").textContent=faDigits(clock(audio.duration));
  const tr=cur();
  if(tr&&tr.kind==="chapter"){ const R=refs[tr.slug]; R&&R.fills[tr.idx]&&(R.fills[tr.idx].style.width=p*100+"%"); }
  maybeRecordProgress();
});
```

- [ ] **Step 5: Manual verification**

Run: `cd ~/develpment/book-podcasts && python3 -m http.server 8000`, open `http://localhost:8000` in a browser.

- Play any chapter for >5 seconds, then pause. Open DevTools → Application → Local Storage → `abs-history`. Confirm one entry keyed by that episode's `.m4a` URL, with `position` roughly matching where you paused and `played:false`.
- Reload the page and click that same chapter again. Confirm playback starts at the saved position, not from 0.
- Seek to within the last few seconds of a short episode (or a whole-book overview) and let it finish. Confirm the entry's `played` becomes `true` in Local Storage, and that clicking the same episode again afterward starts over at 0 (finished episodes always restart).

- [ ] **Step 6: Run both tests to confirm nothing regressed**

Run: `node test_search.js && node test_history.js`
Expected: both print `ok`.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Persist playback position and record resume/write hooks

Writes throttled to every ~5s during playback plus immediately on
pause/ended/beforeunload; load() seeks to a saved position when one
exists and the episode isn't already finished.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Kbni88Fed1e2MpJNcainQp
EOF
)"
```

---

## Task 3: Persisted played marks (spine + chapter list)

**Files:**
- Modify: `index.html`

**Interfaces:**
- Consumes: `HISTORY` (Task 2), `ICON_CHECK` (existing).
- Produces: nothing new consumed by later tasks — this is a leaf/visual task.

- [ ] **Step 1: Initialize persisted state when building each chapter row**

Using Edit, find:

```js
  chapters.forEach((c,i)=>{
    const title=chTitle(b.slug,c);
    const seg=document.createElement("button");
    seg.type="button"; seg.className="seg";
    seg.style.flexGrow=String(Math.max((c.seconds||60)/60,1));
    seg.title=`${L.chShort} ${num(i+1)} — ${title}`;   // hover: no duration
    seg.setAttribute("aria-label",seg.title);
    seg.innerHTML=`<span class="seg-fill"></span>`;
    seg.addEventListener("click",()=>start(tracks,i));
    spine.append(seg);
    R.segs.push(seg); R.fills.push($(".seg-fill",seg));

    const row=document.createElement("button");
    row.type="button"; row.className="ch";
    row.innerHTML=`<span class="ch-n">${String(i+1).padStart(2,"0")}</span>
      <span class="ch-t">${esc(title)}</span>
      <span class="ch-d mono">${dur(c.seconds)}</span>`;
    row.addEventListener("click",()=>start(tracks,i));
```

Replace with:

```js
  chapters.forEach((c,i)=>{
    const title=chTitle(b.slug,c);
    const played = HISTORY[c.url] && HISTORY[c.url].played;
    const seg=document.createElement("button");
    seg.type="button"; seg.className="seg";
    if(played) seg.dataset.done="1";
    seg.style.flexGrow=String(Math.max((c.seconds||60)/60,1));
    seg.title=`${L.chShort} ${num(i+1)} — ${title}`;   // hover: no duration
    seg.setAttribute("aria-label",seg.title);
    seg.innerHTML=`<span class="seg-fill"></span>`;
    seg.addEventListener("click",()=>start(tracks,i));
    spine.append(seg);
    R.segs.push(seg); R.fills.push($(".seg-fill",seg));

    const row=document.createElement("button");
    row.type="button"; row.className="ch";
    row.innerHTML=`<span class="ch-n">${String(i+1).padStart(2,"0")}</span>
      <span class="ch-t">${esc(title)}</span>
      <span class="ch-d mono">${played?`<span class="ch-played">${ICON_CHECK}</span>`:""}${dur(c.seconds)}</span>`;
    row.addEventListener("click",()=>start(tracks,i));
```

(`.seg[data-done="1"]` already exists in the CSS and already meant "finished" — it was only ever set live during the same session by the `ended` handler, never initialized from anything persisted. This is the first time it reads real history.)

- [ ] **Step 2: Live-update the chapter row's checkmark when an episode finishes, in the same run**

Using Edit, find (this is the `ended` listener as Task 2 left it):

```js
audio.addEventListener("ended",()=>{
  const tr=cur();
  if(tr){ const R=refs[tr.slug]; if(R&&tr.kind==="chapter") R.segs[tr.idx].dataset.done="1"; }
  forceRecordProgress(true);
  if(qi<queue.length-1){ qi++; load(true); } else { paintSpines(); }
});
```

Replace with:

```js
audio.addEventListener("ended",()=>{
  const tr=cur();
  if(tr){
    const R=refs[tr.slug];
    if(R&&tr.kind==="chapter"){
      R.segs[tr.idx].dataset.done="1";
      if(R.chs[tr.idx] && !R.chs[tr.idx].querySelector(".ch-played")){
        const d=$(".ch-d",R.chs[tr.idx]);
        d&&d.insertAdjacentHTML("afterbegin", `<span class="ch-played">${ICON_CHECK}</span>`);
      }
    }
  }
  forceRecordProgress(true);
  if(qi<queue.length-1){ qi++; load(true); } else { paintSpines(); }
});
```

- [ ] **Step 3: Add CSS for the checkmark**

Using Edit, find:

```css
.ch-d{ color:var(--haze); font-size:.8rem; white-space:nowrap; }
.missing{ color:var(--haze); }
```

Replace with:

```css
.ch-d{ color:var(--haze); font-size:.8rem; white-space:nowrap; }
.ch-played{ display:inline-flex; width:11px; height:11px; margin-inline-end:5px;
  vertical-align:-1px; color:var(--accent); }
.ch-played svg{ width:100%; height:100%; }
.missing{ color:var(--haze); }
```

- [ ] **Step 4: Manual verification**

Reload the dev server from Task 2. Let a chapter play to the end (or seek to the last few seconds and wait). Confirm, without reloading the page, that its TOC row immediately gets a small checkmark before the duration and its spine segment darkens. Reload the page and confirm both marks are still there (this is the part that didn't work before this task — the `ended` handler already did the spine-only, session-only version).

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Persist and show played marks in the chapter spine and list

The spine's data-done marker already existed but was session-only.
It, plus a new checkmark on the chapter row itself, now read from
the same localStorage history Task 2 writes.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Kbni88Fed1e2MpJNcainQp
EOF
)"
```

---

## Task 4: Book-level continue button

**Files:**
- Modify: `index.html`

**Interfaces:**
- Consumes: `mostRecentInProgress`, `continueListening` (Task 1); `HISTORY` (Task 2); `split`, `mkTrack`, `start`, `DATA`, `render`, `LANG` (existing).
- Produces: `playHistoryEntry(entry)` — Task 5's continue-listening row calls this too.

- [ ] **Step 1: Add `playHistoryEntry()`, right after `resume()`**

Using Edit, find:

```js
function resume(keep, ratio){
  const b=(DATA.books||[]).find(x=>x.slug===keep.slug); if(!b) return;
  const {full,chapters}=split(b);
  if(keep.kind==="full"){
    if(!full) return; queue=[mkTrack(b,"full",full,0)]; qi=0;
  } else {
    if(!chapters[keep.idx]) return;
    queue=chapters.map((c,i)=>mkTrack(b,"chapter",c,i)); qi=keep.idx;
  }
  load(false);
  audio.addEventListener("loadedmetadata",()=>{ if(audio.duration) audio.currentTime=ratio*audio.duration; },{once:true});
  if(keep.playing) audio.play().catch(fail);
}
```

Replace with itself plus:

```js
function resume(keep, ratio){
  const b=(DATA.books||[]).find(x=>x.slug===keep.slug); if(!b) return;
  const {full,chapters}=split(b);
  if(keep.kind==="full"){
    if(!full) return; queue=[mkTrack(b,"full",full,0)]; qi=0;
  } else {
    if(!chapters[keep.idx]) return;
    queue=chapters.map((c,i)=>mkTrack(b,"chapter",c,i)); qi=keep.idx;
  }
  load(false);
  audio.addEventListener("loadedmetadata",()=>{ if(audio.duration) audio.currentTime=ratio*audio.duration; },{once:true});
  if(keep.playing) audio.play().catch(fail);
}

/* Resume a specific history entry — used by the continue-listening row and a
   book's own "Continue: <episode>" button. If the entry's language differs from
   what's currently shown, switch first (same idea as the language toggle above);
   the saved position itself is restored automatically by load()'s own check. */
function playHistoryEntry(entry){
  const b=(DATA.books||[]).find(x=>x.slug===entry.slug); if(!b) return;
  if(entry.lang!==LANG){ LANG=entry.lang; localStorage.setItem("abs-lang",LANG); render(); }
  const {full,chapters}=split(b);
  if(entry.kind==="full"){
    if(!full) return;
    start([mkTrack(b,"full",full,0)],0);
  }else{
    if(!chapters[entry.idx]) return;
    start(chapters.map((c,i)=>mkTrack(b,"chapter",c,i)), entry.idx);
  }
}
```

- [ ] **Step 2: Make the whole-button context-aware**

Using Edit, find:

```js
  // whole-book: play + download
  const side=$(".book-side",el);
  if(full){
    const w=document.createElement("button");
    w.type="button"; w.className="whole"; w.dataset.on="0";
    w.innerHTML=`${ICON_PLAY}<span>${esc(L.whole)}</span><small>${dur(full.seconds)}</small>`;
    w.addEventListener("click",()=>{
      if(cur()?.slug===b.slug && cur()?.kind==="full"){ audio.paused?audio.play():audio.pause(); return; }
      start([mkTrack(b,"full",full,0)],0);
    });
    side.append(w); R.whole=w; R.fullTrack=mkTrack(b,"full",full,0);
    const dl=document.createElement("a");
    dl.className="whole-dl"; dl.href=full.url; dl.setAttribute("download","");
    dl.title=L.dlWhole; dl.setAttribute("aria-label",L.dlWhole); dl.innerHTML=ICON_DL;
    side.append(dl);
  } else {
    side.innerHTML=`<span class="mono missing">${esc(L.missing)}</span>`;
  }
```

Replace with:

```js
  // whole-book: play + download
  const side=$(".book-side",el);
  const continueEntry = mostRecentInProgress(HISTORY, b.slug);
  R.continueEntry = continueEntry;
  if(full){
    const w=document.createElement("button");
    w.type="button"; w.className="whole"; w.dataset.on="0";
    const wholeHist = HISTORY[full.url];
    const label = continueEntry ? `${L.continue}: ${continueEntry.label}` : L.whole;
    const shownDur = continueEntry ? dur(continueEntry.duration) : dur(full.seconds);
    const mark = (!continueEntry && wholeHist && wholeHist.played) ? ICON_CHECK : "";
    w.innerHTML=`${ICON_PLAY}<span>${esc(label)}</span><small>${mark}${shownDur}</small>`;
    w.addEventListener("click",()=>{
      if(continueEntry){
        if(cur() && cur().src===continueEntry.url){ audio.paused?audio.play():audio.pause(); return; }
        playHistoryEntry(continueEntry);
        return;
      }
      if(cur()?.slug===b.slug && cur()?.kind==="full"){ audio.paused?audio.play():audio.pause(); return; }
      start([mkTrack(b,"full",full,0)],0);
    });
    side.append(w); R.whole=w; R.fullTrack=mkTrack(b,"full",full,0);
    const dl=document.createElement("a");
    dl.className="whole-dl"; dl.href=full.url; dl.setAttribute("download","");
    dl.title=L.dlWhole; dl.setAttribute("aria-label",L.dlWhole); dl.innerHTML=ICON_DL;
    side.append(dl);
  } else {
    side.innerHTML=`<span class="mono missing">${esc(L.missing)}</span>`;
  }
```

- [ ] **Step 3: Keep the button's "now playing" highlight correct when it's showing a continue target**

Using Edit, find:

```js
function paintSpines(){
  const tr=cur();
  for(const slug in refs){
    const R=refs[slug];
    R.whole && (R.whole.dataset.on = (tr&&tr.slug===slug&&tr.kind==="full"&&!audio.paused)?"1":"0");
    R.segs.forEach((s,i)=>{
```

Replace with:

```js
function paintSpines(){
  const tr=cur();
  for(const slug in refs){
    const R=refs[slug];
    const wholeActive = tr && tr.slug===slug && (
      (tr.kind==="full" && !R.continueEntry) ||
      (R.continueEntry && tr.kind===R.continueEntry.kind && tr.idx===R.continueEntry.idx)
    );
    R.whole && (R.whole.dataset.on = (wholeActive && !audio.paused)?"1":"0");
    R.segs.forEach((s,i)=>{
```

- [ ] **Step 4: New strings**

Using Edit, find (Persian dictionary):

```
  hour:"ساعت", minute:"دقیقه", chShort:"فصل" },
```

Replace with:

```
  hour:"ساعت", minute:"دقیقه", chShort:"فصل",
  continue:"ادامه", continueTitle:"ادامه‌ی شنیدن" },
```

Using Edit, find (English dictionary):

```
  hour:"h", minute:"min", chShort:"Ch." }
```

Replace with:

```
  hour:"h", minute:"min", chShort:"Ch.",
  continue:"Continue", continueTitle:"Continue listening" }
```

- [ ] **Step 5: CSS for the checkmark inside the whole button**

Using Edit, find:

```css
.whole small{ opacity:.6; font-size:.8em; }
```

Replace with:

```css
.whole small{ opacity:.6; font-size:.8em; }
.whole small svg{ width:10px; height:10px; vertical-align:-1px; margin-inline-end:4px; }
```

- [ ] **Step 6: Manual verification**

Using the dev server from earlier tasks:

- Start a chapter, let it play past 5 seconds, then navigate elsewhere (search for something else) so the book's card unmounts and remounts, or just reload the page. Reopen the book: its top button should now read "Continue: <that chapter's label>" with that chapter's own duration, not "Full summary".
- Click it. Confirm it resumes that exact chapter at the saved position (reuses Task 2's resume-on-load) and that clicking again toggles pause/play rather than restarting.
- Let that chapter finish (or manually mark it played by seeking near the end). With no other chapter in progress, reload and confirm the button reverts to "Full summary" / normal behavior.
- With no history at all for a book, confirm its button is unchanged from before this plan.

- [ ] **Step 7: Run both tests**

Run: `node test_search.js && node test_history.js`
Expected: both print `ok`.

- [ ] **Step 8: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Make the whole-book button continue an in-progress episode

A book's play button is the only "play this book" affordance it
has, so when something in that book is partway through, the button
resumes it instead of always restarting the overview.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Kbni88Fed1e2MpJNcainQp
EOF
)"
```

---

## Task 5: Continue-listening row

**Files:**
- Modify: `index.html`

**Interfaces:**
- Consumes: `continueListening` (Task 1), `HISTORY` (Task 2), `playHistoryEntry` (Task 4), `META`, `DATA`, `t()`, `esc()`.
- Produces: `renderContinueRow()`, called from `render()`.

- [ ] **Step 1: Markup**

Using Edit, find:

```html
  <main><div id="list"></div><div class="msg" id="msg" data-i18n="loading"></div></main>
```

Replace with:

```html
  <main>
    <div class="continue-wrap" id="continueWrap" hidden>
      <p class="mono continue-title" data-i18n="continueTitle"></p>
      <div class="continue-row" id="continueRow"></div>
    </div>
    <div id="list"></div>
    <div class="msg" id="msg" data-i18n="loading"></div>
  </main>
```

- [ ] **Step 2: CSS**

Using Edit, find:

```css
.book-cats{ display:flex; flex-wrap:wrap; gap:7px; margin-top:14px; }
.book-cats .cat{ font-size:.72rem; padding:4px 11px; }
```

Replace with:

```css
.book-cats{ display:flex; flex-wrap:wrap; gap:7px; margin-top:14px; }
.book-cats .cat{ font-size:.72rem; padding:4px 11px; }

/* continue-listening row — recently started, unfinished episodes across all books */
.continue-wrap{ margin-top:8px; }
.continue-wrap[hidden]{ display:none; }
.continue-title{ color:var(--haze); margin-bottom:12px; }
.continue-row{ display:flex; gap:14px; overflow-x:auto; padding-block:2px 8px; }
.continue-card{ flex:none; width:168px; display:flex; flex-direction:column; gap:7px;
  background:none; border:0; padding:0; cursor:pointer; text-align:start; font:inherit; color:inherit; }
.continue-card:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
.continue-cover{ width:100%; aspect-ratio:2/3; object-fit:cover; border-radius:4px;
  border:1px solid var(--line); background:var(--ink-raise); }
.continue-book{ font-size:.82rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.continue-ep{ font-size:.75rem; color:var(--haze); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.continue-bar{ height:2px; background:var(--line); border-radius:2px; overflow:hidden; }
.continue-bar-fill{ height:100%; background:var(--accent); }
```

- [ ] **Step 3: `renderContinueRow()`, right after `playHistoryEntry()`**

Using Edit, find (this is Task 4's addition, verbatim):

```js
function playHistoryEntry(entry){
  const b=(DATA.books||[]).find(x=>x.slug===entry.slug); if(!b) return;
  if(entry.lang!==LANG){ LANG=entry.lang; localStorage.setItem("abs-lang",LANG); render(); }
  const {full,chapters}=split(b);
  if(entry.kind==="full"){
    if(!full) return;
    start([mkTrack(b,"full",full,0)],0);
  }else{
    if(!chapters[entry.idx]) return;
    start(chapters.map((c,i)=>mkTrack(b,"chapter",c,i)), entry.idx);
  }
}
```

Replace with itself plus:

```js
function playHistoryEntry(entry){
  const b=(DATA.books||[]).find(x=>x.slug===entry.slug); if(!b) return;
  if(entry.lang!==LANG){ LANG=entry.lang; localStorage.setItem("abs-lang",LANG); render(); }
  const {full,chapters}=split(b);
  if(entry.kind==="full"){
    if(!full) return;
    start([mkTrack(b,"full",full,0)],0);
  }else{
    if(!chapters[entry.idx]) return;
    start(chapters.map((c,i)=>mkTrack(b,"chapter",c,i)), entry.idx);
  }
}

function renderContinueRow(){
  const wrap=$("#continueWrap"), row=$("#continueRow");
  const entries = DATA ? continueListening(HISTORY) : [];
  if(!entries.length){ wrap.hidden=true; row.innerHTML=""; return; }
  const L=t();
  row.innerHTML="";
  entries.forEach(e=>{
    const cover=(META[e.slug]&&META[e.slug].cover)||"";
    const pct = e.duration ? Math.min(100, Math.round((e.position/e.duration)*100)) : 0;
    const card=document.createElement("button");
    card.type="button"; card.className="continue-card";
    card.innerHTML=`
      ${cover?`<img class="continue-cover" src="${esc(cover)}" alt="" loading="lazy" onerror="this.remove()">`:""}
      <span class="continue-book">${esc(e.book)}</span>
      <span class="continue-ep">${esc(e.label)}</span>
      <span class="continue-bar"><span class="continue-bar-fill" style="width:${pct}%"></span></span>`;
    card.addEventListener("click",()=>playHistoryEntry(e));
    row.append(card);
  });
  $(".continue-title",wrap).textContent=L.continueTitle;
  wrap.hidden=false;
}
```

- [ ] **Step 4: Call it from `render()`**

Using Edit, find:

```js
  if(!hits.length){
    $("#msg").hidden=false;
    $("#msg").textContent = Q ? `${L.noResults} “${$("#q").value.trim()}”` : L.empty;
  }
  paintSpines();
  paintVotes();
}
```

Replace with:

```js
  if(!hits.length){
    $("#msg").hidden=false;
    $("#msg").textContent = Q ? `${L.noResults} “${$("#q").value.trim()}”` : L.empty;
  }
  paintSpines();
  paintVotes();
  renderContinueRow();
}
```

- [ ] **Step 5: Manual verification**

With at least one in-progress (unplayed, >5s) entry in `abs-history` from earlier tasks' testing, reload the page. Confirm a "Continue listening" row appears above the book list — a horizontally-scrollable strip with a cover, book title, episode label and a thin progress bar. Click a card: confirm it starts that exact episode at the saved position, switching the language toggle first if the entry's language differs from what's currently shown. Mark that entry played (let it finish) and reload: confirm it drops out of the row. With `abs-history` cleared entirely (DevTools → clear that key), reload and confirm the row and its heading are fully absent — no empty gap.

- [ ] **Step 6: Run both tests**

Run: `node test_search.js && node test_history.js`
Expected: both print `ok`.

- [ ] **Step 7: Commit**

```bash
git add index.html
git commit -m "$(cat <<'EOF'
Add the continue-listening row

Surfaces in-progress episodes across every book, most recent first,
so a returning listener doesn't have to remember which book or
chapter they were on.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Kbni88Fed1e2MpJNcainQp
EOF
)"
```

---

## Task 6: End-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `cd ~/develpment/book-podcasts && node test_search.js && node test_history.js`
Expected: both print `ok`.

- [ ] **Step 2: Full manual walkthrough**

With `python3 -m http.server 8000` running and `abs-history` cleared to start clean:

1. Open a book with several chapters. Play chapter 2 for ~20 seconds, then close the tab entirely (not just pause).
2. Reopen the site. Confirm: the book's whole-button now reads "Continue: Chapter 2 — <title>"; a "Continue listening" card for it appears at the top; chapter 2's own row/segment does **not** yet show a played mark (it isn't finished).
3. Click the continue-listening card. Confirm playback resumes at ~20 seconds in, not from 0.
4. Let chapter 2 finish playing naturally (or seek to the last few seconds and wait for `ended`). Confirm immediately, without reloading: chapter 2's TOC row gets a checkmark, its spine segment darkens.
5. Reload the page. Confirm both marks persisted, the continue-listening card for chapter 2 is gone (it's finished, not in-progress), and the book's whole-button is back to "Full summary" (nothing else in that book is in progress).
6. Switch the site's language toggle. Confirm nothing in this feature breaks the existing keep-your-place-across-language behavior (still works exactly as before).
7. On a book with zero history, confirm every affected surface (whole-button, chapter rows, continue-listening row) looks exactly as it did before this plan.

- [ ] **Step 3: Confirm the spec's data-model guarantee holds**

In DevTools, inspect `localStorage.abs-history`. Confirm entries are keyed by full episode URL (not chapter key), and that playing the same chapter in the other language (if available) creates a **separate** entry rather than overwriting the first.

- [ ] **Step 4: Report**

No commit for this task — it's verification of Tasks 1–5, which are already committed individually. If any check in Step 2 or 3 fails, fix it as part of the task whose commit introduced the problem (re-open that task) rather than papering over it here.
