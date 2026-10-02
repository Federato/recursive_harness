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

**Status: RC-2 done 2026-10-02, 5 of 18** (RC-1: the census refreshed, the register cleaned; RC-2: point 9 closed on chunks 1–8, `239_chunk27_rc2.py --live`, 25 of 25 agree with ISO, OI-126 registered; no engine change). **Next: RC-3, C27-06 (CA and FL Legal Liability).**

## Who owns what (C27-02, 2026-10-02)

Every open item in the register and every gate point still open on a closed chunk, with its owner. **Chunk 27 closes with evidence; chunk 28 decides engine changes (each needs the user's go).**

| Item | What | Owner | Task |
|---|---|---|---|
| Point 9 on chunks 1–6 | message tallies, ISO-matched on 293 stored responses | **27** | C27-03 |
| Point 9 on chunk 7 | ISO 3 messages vs ours 5 (and 1 vs 4) | **27** (a real engine difference goes to 28) | C27-04 |
| Points 8 and 9 on chunk 8 | CA / FL Legal Liability $0; message tally | **27** | C27-05, C27-06 |
| Per-state gaps | TX wind / hail shape; DC IL `BCEGFactor`; MT NY Group II symbol | **27** (a refusal becomes an OI-103 case for 28) | C27-07..09 |
| Chunk 12 leftovers | theft on drones / Dependent Properties; FL and WV (non-flood) O&L priced cases (VA and WV flood closed by chunks 23 / 25) | **27** | C27-10, C27-11 |
| OI-101, OI-119, OI-122, OI-124 | filed rules where **ISO agrees with ours** (Leasehold Special $0; VR "Used" refused; flood op-unit BI; CA One-Term BI) | **27**: close as "matches ISO", documented for submitters | C27-12 (scope widened 2026-10-02 from OI-101 alone) |
| OI-105 | ISO serves newer packages than the corpus | **27**: a corpus / as-of question | C27-13 |
| OI-106 (+ OI-118 merged), OI-112 | form names via `Pages`; older-edition CP 03 20 echo | evidence **27**, the change **28** | C27-14 |
| OI-116 | FL SPP condo record: ISO never attaches it, ours prices; **unexplained** | **27**: trace and route | C27-14 (added 2026-10-02) |
| OI-114 (+ OI-120 merged) | `<rul:Null/>` in old builds (5 packages, none in force) | evidence **27**, the change **28** | C27-15 |
| OI-99, OI-103, OI-117 | ISO refuses where ours prices (missing rows, blank keys, blank `Convert`; 31 more from chunk 26) | **28** | — |
| OI-123, OI-125 | message-only differences (empty `NotExist`; occupancy counts) | **28** | — |
| OI-113 | minimum premium: refer to company | **28** (backlog, user decision) | — |
| Input validation, submitted derived fields, the shared core's housekeeping | standing design questions | **28** | — |
| OI-115, OI-121 | closed / fixed | — | — |

## Census refresh (2026-10-02), before any other task

`908_chunk27_census.py` re-run against the docs as they stand after chunks 18–26 (log `results/cf-raas/logs/chunk27_census.log`;
the 2026-09-28 run kept as `chunk27_census_20260928.log`). The script now writes UTF-8 (a plain run crashed on the ⬜ symbol under
the Windows code page; nothing else changed).

| What | 2026-09-28 | 2026-10-02 |
|---|---|---|
| Gates not fully passed | chunks 1–8 | **the same chunks 1–8, the same points**: point 9 on 1–7 (chunk 7's real gap: ISO 3 messages, ours 5), point 8 on chunk 8; chunks 9–26 are all 9 of 9 |
| OIs in the register | to OI-113, plus OI-114 unregistered | **eleven more, OI-115 to OI-125** (routing below); **OI-114 still has no register row** |
| Duplicates | — | **OI-120 is OI-114** (the same 2020 countrywide `rul:Null` in `Structure.DoMessageAtLeastOneBuildingOrPersonalPropertyRecord…`, found twice: chunk 15 VA 2021, chunk 23 MA / AK / VA); **OI-118 is OI-106** (a state's own `Pages` table hides the countrywide form rows): C27-02 merges each pair |
| Stale claims on the status page | — | the "Commit status" row says "checked 2026-09-24, through chunk 14" (git: through chunk 25, `294d8a1`; chunk 26 uncommitted); the input-validation row says five inputs where the resume page says eight: C27-02 corrects both, dated |
| Per-state gaps | TX wind / hail; DC IL BCEG; MT NY Group II symbol | unchanged |
| Chunk 12 leftovers | FL / VA / WV priced O&L, theft on drones / Dependent Properties | **VA closed by chunk 23** (C23-11, 41 files ISO-confirmed); **WV's flood O&L closed by chunk 25** (C25-20); FL and WV's non-flood forms, and the theft re-probe, stay here |
| Chunk 17's Off-Premises flood factor | open | **closed by chunk 25** (C25-22) |

**Routing the new items** (each ends closed with evidence here, or handed to chunk 28 with its evidence):

| OI | What | Lands |
|---|---|---|
| OI-115, OI-121 | closed / fixed in their chunks | nothing to do |
| OI-116 | FL's SPP special-class condo record: ISO never attaches it, ours prices it; **unexplained** | **here**: trace why before routing |
| OI-117 | a blank `Convert` to a number: ISO refuses, ours rates | **chunk 28** (OI-103's family) |
| OI-118 | = OI-106 | merged in C27-02; the change in **chunk 28** |
| OI-119 | ISO refuses every Value Reporting "Used" policy; ours agrees | **here**: close as "matches ISO", documented (an ISO defect) |
| OI-120 | = OI-114 | merged in C27-02; the change in **chunk 28** |
| OI-122, OI-124 | filed rules that miss a case; **ISO agrees with ours** | **here**: close as "matches ISO", documented for submitters |
| OI-123, OI-125 | messages only: ISO and ours differ (empty `NotExist`; occupancy counts) | **chunk 28** (engine changes, each needs the go) |

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
| C27-01 | **Opening census**: every gate file's score and open rows, every OI and its status, the resume page's gaps and notes, the status page's cross-chunk items and unchecked rows | ✅ | **Done 2026-09-28** (`908_chunk27_census.py`); **refreshed 2026-10-02** (table above: chunks 1–8 unchanged, OI-115–125 routed, two duplicate pairs, two stale status-page claims, three items closed by chunks 23 / 25). Findings above: point 9 owed on chunks 1–8, a real message gap on chunk 7, point 8 on chunk 8; 6 open OIs plus unregistered OI-114; 3 per-state gaps; 2 chunk 12 leftovers; the card's point-2 row stale |
| C27-02 | **Register hygiene**: add OI-114's row to `OPEN-ITEMS.md`; mark the stale card rows (point 2 on chunks 6 / 8 passed; chunk 8's ❌ is OI-110, fixed), each with its date; one list of what chunk 27 owns and what it hands to chunk 28 | ✅ | **Done 2026-10-02** (no ISO calls). **OI-114 registered** as the canonical row and **OI-120 merged into it** (the same `<rul:Null/>` in the same 2020 rule); a census of every CF package found `<rul:Null/>` in 5, none in force (CW 2019 and 2020, FL 2019, **NC 2023-08 / 2024-02** in the flood operational-unit rule, now recorded). **OI-118 merged into OI-106** (the same `Pages` resolution). Stale rows corrected with dates: the status page's commit status (through chunk 25, not 14), input validation (eight inputs, not five), gate point 9 (owed on chunks 1–8, not 1–2), the chunk 27 plan row (point 2 struck); chunk 8's gate row ❌ marked fixed by OI-110. The ownership table above |

### RC-2 · Gate point 9, validation messages (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C27-03 | **Chunks 1–6**: a message tally on each golden case (chunk 9's `78_` method), each message explained or matched to ISO's, with C13-27's 293-response evidence cited; update each gate file to 9 of 9 where it holds | ✅ 2026-10-02 | `239_ --live`: 13 golden cases (chunks 1–6) sent to ISO as the engine rates them, every (level, message) equal; the 4 contents cases refused as built (no building `WindstormOrHailDeductible`, OI-103) agree once it is sent. Three new messages registered (M-004 theft deductible, M-005 full value, M-006 Legal Liability deductible). Gate files 1–6: point 9 closed |
| C27-04 | **Chunk 7's gap**: why the engine fires 5 messages where ISO fires 3 (and 4 vs 1); each extra message named, traced to its rule, and classed as a message ISO clears (OI-112-like) or an engine difference, which goes to chunk 28 with the evidence; ISO live | ✅ 2026-10-02 | The old 3-vs-5 compared two inputs: `53_` sent ISO a hand-built sparse payload, the engine rated `50_`'s tree. The same request: 5 = 5, 5 = 5, 6 = 6. Deductible removed: ISO 3, ours 4, the extra traced to `Location.SetMultipleDiffDeductibleSpclIndicator` (ours "Yes", ISO "No"): **OI-126**, an engine difference for chunk 28. Point 9 closed, explained |
| C27-05 | **Chunk 8**: the message tally on its golden case, as in C27-03; ISO live if any is unexplained | ✅ 2026-10-02 | Building 2 = 2 ×3; Contents 3 = 3, 3 = 3, 4 = 4 with the building's windstorm deductible (the lookup reads the building: why chunk 8's copy on the contents failed); **chunk 8's contents $132 / $15 / $11 / $93 now ISO-confirmed**. Point 9 closed |

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
| C27-12 | **OI-101** (scope widened 2026-10-02: also OI-119, OI-122, OI-124, the same "ISO agrees" pattern): record ISO's agreement (Special $0 without a Theft Exclusion) with the evidence, add it to the rater simplifications backlog if the rater differs, and close | ⬜ | |
| C27-13 | **OI-105, corpus coverage**: list, per state, the packages ISO serves after 2026-09-17 that the corpus lacks (OR 2027; CA MA AK from chunk 23); probe which ISO uses on which date; propose the as-of date policy | ⬜ | a corpus question, not an engine change |
| C27-14 | **OI-106 (+ OI-118) and OI-112, the evidence** (added 2026-10-02: trace OI-116, FL's SPP condo record, and route it): each case reproduced and bounded (states, editions, messages and echoed values), no premium effect confirmed; handed to chunk 28 with a proposed change | ⬜ | |
| C27-15 | **OI-114** (+ OI-120, merged 2026-10-02; the package census is in its row): the `rul:Null` test on the 2020 / 2021 editions, which states and dates it touches (none in force), and whether any live probe date reaches it; handed to chunk 28 | ⬜ | |

### RC-5 · Close-out (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C27-16 | **Gate files updated**: chunks 1–8 re-scored with the points closed, each change dated; the status page's cards and cross-chunk table brought in line | ⬜ | |
| C27-17 | **Regression**: add the chunk 27 scripts (the message tallies pinned); full run CLEAN (`--jobs 4`); `157_ --all` | ⬜ | |
| C27-18 | **File `CF-CHUNK27-GATE.md`**: every item closed with evidence or handed to chunk 28, nothing left unlabelled | ⬜ | |
