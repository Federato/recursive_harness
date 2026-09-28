# Property chunk 27: task list and status

**Open gate points and open items on closed chunks: the loose ends, closed with evidence.**
Tasks set 2026-09-28. No coverage and no rating arithmetic, so, as the plan says, it **can run
alongside any chunk**, including now, beside chunk 18.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 27) and the opening census ([`908_chunk27_census.py`](../scripts/cf/908_chunk27_census.py),
run 2026-09-28, log `results/cf-raas/logs/chunk27_census.log`). The plan card lists five rows. The census
does not trust it; it **enumerates** instead:
- every gate file's score and its rows not passed;
- every OI in the register, and any OI mentioned in the docs but missing from it;
- the resume page's per-state gaps and "Open" notes;
- the status page's cross-chunk open items and unchecked rows on closed cards.

**Standing rules carried in.** Analysis and gates only: **no engine code without the user's go.**
This chunk closes items **with evidence**; anything whose fix is an engine change is handed to chunk
28 with its evidence, not changed here. "All states" means the **46**; Puerto Rico is excluded.
Live ISO comparisons at **2026-09-17** (OI-105). Every figure and message set is predicted before it
runs. Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`.

**Status: TASKS SET 2026-09-28, 1 of 18** (the census). Next: C27-02, which can start now.

---

## In plain English first

Chunks 1–17 are closed, but not every gate point was passed on every chunk, and a handful of
questions were parked along the way. None of them changes a premium on the path we rate. This
chunk works through them one at a time and ends each one in one of two ways: **closed with
evidence**, or **handed to chunk 28** as a decision about the engine, with the evidence attached.

## What the census found, before any task ran

**Gates not fully passed**

| Chunk | Score | What is open |
|---|---|---|
| 1, 2 | "8 of 8" (older format; point 9 added later) | **Point 9, validation messages**: owed retroactively. Chunk 1 fires three ISO messages on every case. Chunk 2 also has TX's wind / hail "fourth shape, not yet traced" |
| 3, 4, 5, 6 | 8 of 9 | **Point 9**: 3–4 messages per case, **matched by ISO exactly** (chunk 6), but never gated |
| 7 | 8 of 9 | **Point 9 with a real gap**: **ISO 3 messages, engine 5** on the Basic call; **ISO 1, engine 4** with the parent's deductible removed |
| 8 | 7 of 9 | **Point 8 held open**: CA and FL (PR out of scope) produce no Legal Liability premium, reason not established. Point 9 owed |
| 9–17 | 9 of 9 | — (chunk 12's gate left two non-blocking items: see below) |

**The plan card's "point 2 on chunks 6 and 8" is stale**: both gate files show point 2 passed (✅), with
row counts stated (chunk 6: 13 tables, three header-only; chunk 8: 2 / 4 / 4 rows, no state filings).
Chunk 8's "Builders Risk + reporting form refuses vs rates $1 ❌" row is OI-110, **fixed 2026-09-23**.

**Evidence that should close point 9 cheaply.** Chunk 13 (C13-27) showed **all 293 stored ISO
responses carry a message set identical to the engine's**, and chunk 14 compared messages on 92 state
cases. That covers the paths chunks 1–6 rate. What is missing is the per-chunk tally on each golden
case, which chunk 9 did in `78_chunk9_c9-12_message_tally.py`.

**Open items (register: `docs/OPEN-ITEMS.md`)**

| OI | Status | What | Where it lands |
|---|---|---|---|
| OI-101 | OPEN | Leasehold Interest Special prices $0 without a Theft Exclusion. **ISO does the same** | here: close as "matches ISO", documented |
| OI-103 | OPEN | ISO refuses where we price (a dozen+ cases) | **chunk 28** (its opener) |
| OI-105 | OPEN | ISO serves newer editions than the corpus holds (OR 2027; chunk 23 adds CA, MA and AK packages after 2026-09-17) | here: a corpus question, not an engine one |
| OI-106 | OPEN | form names miss the countrywide `Pages` rows when a state files its own; no premium effect | evidence here, the change in **chunk 28** |
| OI-112 | OPEN | older editions: ISO clears three cause-of-loss answers on CP 03 20 and fires a message; no premium effect | evidence here, the change in **chunk 28** |
| OI-113 | BACKLOG | minimum premium: refer to company | **chunk 28** |
| **OI-114** | open, **no register row** | `rul:Null` in a test on the 2020 / 2021 editions (VA 2021 cannot be rated whole); no in-force package affected | here: register it; the change is **chunk 28** |

**Per-state gaps (logged since chunk 2):** TX's wind / hail shape untraced; DC and IL have no
`BCEGFactor` row for their own Group II territory; MT and NY (and PR, out of scope) resolve to an empty
Group II symbol table.

**Chunk 12's non-blocking leftovers:** re-probe theft on drones and Dependent Properties with the
exclusion on the Contents and BI records; **priced FL / VA / WV Ordinance or Law cases**. VA is now
chunk 23's C23-11 and WV's flood forms are chunk 25's. FL, and WV's non-flood forms, stay here.

**Already owned by chunk 28, not repeated here:** input validation (the silent zeros), a submitted
derived field overriding the filed table, the shared core's housekeeping.

---

## Task groups, in priority order

### RC-1 · The register (2 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C27-01 | **Opening census**: every gate file's score and open rows, every OI and its status, the resume page's gaps and notes, the status page's cross-chunk items and unchecked rows | ✅ | **Done 2026-09-28** (`908_chunk27_census.py`). Findings above: point 9 owed on chunks 1–8, a real message gap on chunk 7, point 8 on chunk 8; 6 open OIs plus unregistered OI-114; 3 per-state gaps; 2 chunk 12 leftovers; the card's point-2 row stale |
| C27-02 | **Register hygiene**: add OI-114's row to `OPEN-ITEMS.md`; mark the stale card rows (point 2 on chunks 6 / 8 passed; chunk 8's ❌ is OI-110, fixed), each with its date; one list of what chunk 27 owns and what it hands to chunk 28 | ⬜ | no ISO calls |

### RC-2 · Gate point 9, validation messages (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C27-03 | **Chunks 1–6**: a message tally on each golden case (chunk 9's `78_` method), each message explained or matched to ISO's, with C13-27's 293-response evidence cited; update each gate file to 9 of 9 where it holds | ⬜ | closes point 9 ×6 |
| C27-04 | **Chunk 7's gap**: why the engine fires 5 messages where ISO fires 3 (and 4 vs 1); each extra message named, traced to its rule, and classed as a message ISO clears (OI-112-like) or an engine difference, which goes to chunk 28 with the evidence; ISO live | ⬜ | closes or hands off point 9 on 7 |
| C27-05 | **Chunk 8**: the message tally on its golden case, as in C27-03; ISO live if any is unexplained | ⬜ | closes point 9 on 8 |

### RC-3 · Chunk 8 point 8 and the per-state gaps (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C27-06 | **CA and FL Legal Liability**: why neither produces a Legal Liability premium; each state's own rule, edition and tables traced, predicted, then probed; ISO live | ⬜ | closes point 8 on chunk 8 |
| C27-07 | **TX wind / hail**: trace the fourth shape chunk 2 logged, predict it, and price a TX building with wind / hail excluded and not; ISO live | ⬜ | |
| C27-08 | **DC and IL `BCEGFactor`**: no row for their own Group II territory. What the engine does (null → $0?) and what ISO does, on one probe each; a refusal becomes an OI-103 case for chunk 28 | ⬜ | |
| C27-09 | **MT and NY Group II symbol**: the empty symbol table traced; what a building rates at in each; ISO live; again, a refusal goes to chunk 28 | ⬜ | |

### RC-4 · Chunk 12's leftovers and the open items (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C27-10 | **Theft on drones and Dependent Properties**: the re-probe chunk 12 held open, the exclusion on the Contents and BI records; predicted, then ISO live | ⬜ | |
| C27-11 | **FL and WV Ordinance or Law priced cases**: a golden building in each, the state mechanisms priced end to end (VA is chunk 23's C23-11; WV's flood forms chunk 25's); ISO live | ⬜ | |
| C27-12 | **OI-101**: record ISO's agreement (Special $0 without a Theft Exclusion) with the evidence, add it to the rater simplifications backlog if the rater differs, and close | ⬜ | |
| C27-13 | **OI-105, corpus coverage**: list, per state, the packages ISO serves after 2026-09-17 that the corpus lacks (OR 2027; CA MA AK from chunk 23); probe which ISO uses on which date; propose the as-of date policy | ⬜ | a corpus question, not an engine change |
| C27-14 | **OI-106 and OI-112, the evidence**: each case reproduced and bounded (states, editions, messages and echoed values), no premium effect confirmed; handed to chunk 28 with a proposed change | ⬜ | |
| C27-15 | **OI-114**: the `rul:Null` test on the 2020 / 2021 editions, which states and dates it touches (none in force), and whether any live probe date reaches it; handed to chunk 28 | ⬜ | |

### RC-5 · Close-out (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C27-16 | **Gate files updated**: chunks 1–8 re-scored with the points closed, each change dated; the status page's cards and cross-chunk table brought in line | ⬜ | |
| C27-17 | **Regression**: add the chunk 27 scripts (the message tallies pinned); full run CLEAN (`--jobs 4`); `157_ --all` | ⬜ | |
| C27-18 | **File `CF-CHUNK27-GATE.md`**: every item closed with evidence or handed to chunk 28, nothing left unlabelled | ⬜ | |
