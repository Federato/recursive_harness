# Property chunk 27: the gate

**Open gate points and open items on closed chunks: the loose ends, closed with evidence.** Filed 2026-10-02.
**18 of 18 tasks done.** Task record: [`CF-CHUNK27-TASKS.md`](CF-CHUNK27-TASKS.md). No coverage, no engine change;
546 of 546 countrywide premium files built, unchanged.

**In plain English.** Twenty-six chunks left a tail: gate points never closed on the earliest chunks, per-state oddities
logged and not traced, and open items with no owner. This chunk took each one, predicted what ISO would do, asked ISO,
and either closed it with the evidence or handed it to chunk 28 as an engine decision. **Nothing is left unlabelled.**
Every live comparison agreed with ISO on every premium; the four message-only differences found are registered
(OI-126) or carried (OI-112, OI-123, OI-125).

## Every item, and where it ended

| Item | Outcome | Evidence |
|---|---|---|
| **Point 9 (messages), chunks 1–8** | ✅ closed, all eight | `239_chunk27_rc2.py --live`: 25 runs, every (level, message) multiset equal to ISO except one explained difference (OI-126). Chunk 7's old "ISO 3, engine 5" compared a hand-built ISO payload with the engine's full tree. Register M-004..M-006 added |
| **Point 8, chunk 8** (CA / FL Legal Liability) | ✅ closed, chunk 8 at 9 of 9 | `240_chunk27_rc3.py --live`: CA's zero was no location `District` ($57 / $68 with it), FL prices $59 today; neither was Legal Liability |
| **Chunk 2's per-state gaps** (TX, DC, IL, MT, NY) | ✅ closed | `240_`: TX a flat 0.1 wind / hail factor ($800 → $79); DC and NY read no BCEG; IL maps "Cook County" to "Cook"; MT's symbol resolves; NY's Group II symbol is a submitted input |
| **Chunk 12's leftovers** (theft on drones / Dependent Properties; FL, WV Ordinance or Law) | ✅ closed | `241_chunk27_rc4.py --live`, 11 of 11: the drone reads the contents' theft factor ($187 → $75), Dependent Properties the BI's ($19 → $16); FL charges Coverage A on the whole factor, WV's B & C-only forms price no Coverage A |
| **OI-101, OI-119, OI-122, OI-124** | ✅ closed: **matches ISO** | Documented for submitters; no rater backlog row (the rater builds none; CA One-Term in the rater not checked: RULE #0) |
| **OI-114 (+ OI-120), OI-118 → OI-106** | ✅ register cleaned (C27-02) | One canonical row each |
| **OI-105** (ISO serves newer packages) | → chunk 28, set F | `242_`, 276 live calls: same package in 46 of 46 states at 2026-09-17; 34 newer packages missing; an as-of policy proposed |
| **OI-106** (form names) | → chunk 28, set D | All 47 states file their own `Pages` table; ours 135 of 240 form names "Value Not Found", ISO none |
| **OI-112** (CP 03 20 answers on 2023 editions) | → chunk 28, set C | `243_`: on MA (2023 V04) ISO drops every value sent; the fields are checkboxes in those editions |
| **OI-114** (`<rul:Null/>`) | → chunk 28, set C | `244_`: CW 2020-12 in 43 states to 2024-09; no in-force package; no 2026-09-17 probe reaches it |
| **OI-116** (FL SPP condo record) | → chunk 28, set D | Two more readings ruled out; a question for ISO |
| **OI-126** (new: `FirstNonNull` skips a filed "") | → chunk 28, set C | One extra CP 03 20 message; messages only |
| **OI-103** (two more blank-key refusals) | → chunk 28, set A | The contents' building `WindstormOrHailDeductible`, FL's Group II territory, NY's `CompletedBasicGroupIISymbol` |

## Gate checks (C27-17; no engine change in the chunk)

`206_ --check` **SNAPSHOT CLEAN** (1,760 stored requests, 1,276,743 fields, nothing moved; 501 new since the baseline);
`157_ --all` **293 of 293** (14,236 premium values and every policy total equal to ISO); `104_ --quick` **CLEAN** (34
scripts, every golden case of chunks 1–27). The full `104_ --gate` was not run: no engine change in the chunk (the
scaled-back rule).

Registered in `104_`: `239_` (every golden-case message in the register), `240_`, `241_` (each case as predicted).

## Gate files re-scored (C27-16)

Chunks 1–2: point 9 noted on their eight-point gates; chunks 3–7: 9 of 9; chunk 8: 9 of 9. Each change dated in its file.
The status page's per-state-gaps and point-9 rows brought in line, dated.
