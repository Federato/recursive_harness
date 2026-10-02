# Property chunk 28: task list and status

**Engine behaviour decisions: where our engine and ISO differ by design, or where a bad input silently produces a cheap
policy.** Tasks set 2026-10-02, when chunk 27 closed. Every coverage is built (546 of 546 countrywide premium files) and
every gate point on chunks 1–27 is closed or handed here with its evidence.

**Standing rules carried in.** **Every engine change in this chunk needs the user's go, one item at a time.** The work
before each go is analysis: put the evidence in one table, find a probe that makes the competing rules predict different
answers, run it at ISO, then propose the change. After a change: `206_ --check`, `157_ --all`, the full `104_ --gate`
(the engine changed), and the item's own ISO cases again. Live ISO at **2026-09-17** (OI-105: the only date where ISO and
the corpus use the same package in all 46 states). Puerto Rico excluded. Progress to `results/cf-raas/logs/`.

**Status: OPEN 2026-10-02, 4 of 22** (all seven sets; the user chose to start with Set A). C28-04 done: the proposal is filed and measured. **Next: C28-05, the build, once the user gives the go.**

## The feature sets, and what each buys

**All seven sets are on the list; the user chose the order's start (2026-10-02: Set A first).** Every engine change
still needs the user's go, one item at a time.

| Set | Items | What it buys | Evidence held |
|---|---|---|---|
| **A. Refuse where ISO refuses** | OI-99, OI-103, OI-117 | A policy ISO will not rate is never quietly priced (often at $0) by ours | ~20 concrete refusals across chunks 6–27: `SingleResult` lookups with no row, blank keys (the contents' building `WindstormOrHailDeductible`, FL's Group II territory, NY's `CompletedBasicGroupIISymbol`), `Convert` of a blank. Some empty lookups ISO tolerates (VA, VT): the rule must tell them apart |
| **B. Input validation** | the eight silent-zero inputs, the submitted derived field, NY's missing Group II symbol | A submission that looks valid cannot come out cheap without a word | Eight inputs price at zero (AZ's reduction credit, an unknown `ConstructionType`, no BCEG, no `RatingTypeBasicGroupII`, no Group II territory, a blank `Deductible` on Broad / Special, a construction type spelled as a rating type); many are $0 at ISO too, so this is a validation layer, not a rating change. A submitted `IsNull`-guarded field (e.g. `SpecialBaseRate`) overrides the filed table, at ISO too |
| **C. Messages match ISO** | OI-123, OI-125, OI-126, OI-112, OI-114 | The (level, message) set equals ISO's everywhere, not "equal except these five" | Every one is message-only (premiums equal): an empty `NotExist`; occupancy counts from a submitted `RatingType`; `FirstNonNull` skipping a filed ""; checkbox answers dropped on 2023 editions; `<rul:Null/>` in old builds (no in-force package) |
| **D. Form names** | OI-106 (+ OI-118); OI-116 | Every attached form carries its name and number | All 47 states file their own `Pages` table; ISO resolves 240 of 240 names on chunk 27's responses, ours 135 "Value Not Found". OI-116 (FL SPP condo record) is unexplained: a question for ISO |
| **E. Refer to company** | OI-113 | Minimum premium and other company-judgment answers come back as a referral, not a number | ISO rates no minimum premium (chunk 14); the outcome is `ReferToCompany`; no layer exists yet |
| **F. Dates beyond the corpus** | OI-105 | A request dated after the corpus's coverage is flagged, and the corpus can be refreshed | Measured 2026-10-02 (`242_`): same package in 46 of 46 states at 2026-09-17; 28 states part later; 34 packages missing (IL from 2026-10-01) |
| **G. Housekeeping** | the shared core | `cf_engine` stops importing from `gl_engine`; a neutral home for the interpreter | Deferred since chunk 0; **never bundled with a rating change** |

## Tasks

### RC-1 · The census (1 task, no engine change)

| # | Task | Status | Notes |
|---|---|---|---|
| C28-01 | **Census** (`909_chunk28_census.py`): every open item the register hands to chunk 28, every "chunk 28" mention in the docs and gate files, and the status page's cross-chunk open rows; nothing owned by 28 left out of the sets above | ✅ 2026-10-02 | 12 open Property items (OI-99 103 105 106 112 113 114 116 117 123 125 126), all assigned; 20 OI ids named beside "chunk 28" in the docs, the rest closed or merged; 2 open status rows (housekeeping = set G; GL's choice, not Property's) |

### RC-2 · Set A, refuse where ISO refuses (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C28-02 | **The refusal table**: every refusal on record (OI-99, OI-103, OI-117 and the gate files) in one table (chunk, state, matrix, keys, ISO, ours, the request file), each re-sent live at 2026-09-17 so the table is current; beside it, the empty lookups ISO tolerates (VA, VT) | ✅ 2026-10-02 | [`CF-CHUNK28-REFUSALS.md`](CF-CHUNK28-REFUSALS.md), `245_`: **66 refusals reproduce live; 65 are a `SingleResult` lookup with no row**, ours prices all 66 and records the same miss in each; across **1,689 rated requests ours never misses a `SingleResult` lookup** (672,950 designed `FirstResult` misses). The exception: VT's empty earthquake tier table (ours falls back to countrywide, ISO refuses). Plus 20 recorded-only, 1 `Convert` (OI-117), 4 unbound (ours refuses too), 17 payload-format |
| C28-03 | **The distinguishing rule**: competing rules for what separates refused lookups from tolerated ones, each predicting a different answer on one probe set; ISO live | ✅ 2026-10-02 | [`CF-CHUNK28-REFUSALS.md`](CF-CHUNK28-REFUSALS.md) § C28-03: **R1 holds** (`SingleResult` no-row refuses); refuted: any-miss (672,950 tolerated `FirstResult` misses), arithmetic-only (two stat-code refusals); R4 "last lookup" picks the same lookups in force (no probe can separate); fallback-after sites unreachable. **Empty state tables split by table:** VT vacancy and NY off-premises fall back to CW (rated), the EQ stub refuses in MA TN VT (`246_`); the definition idea refuted; "all-constant keys" fits all five, untested |
| C28-04 | **Proposal** written up: the rule, which lookups it touches (a census over every in-force package), and what each golden case and stored request would do | ✅ 2026-10-02 | [`CF-CHUNK28-PROPOSAL-A.md`](CF-CHUNK28-PROPOSAL-A.md), measured with the engine's own switch (`247_`, no code change): ours would refuse **65 of 66** live ISO refusals at ISO's own table (66 with the EQ stub exception), **0 new refusals** in 1,690 rated requests, and `104_ --quick` fails only on 4 cases ISO itself refuses (golden 1, 4, 8 contents fixed by sending the building's windstorm deductible, figures unchanged). **Awaiting the user's go for C28-05** |
| C28-05 | **Build** (with the go) | ⬜ | |
| C28-06 | **Regression and ISO**: `206_ --check`, `157_ --all`, the full `104_ --gate`; then every case in C28-02's table: ours refuses exactly where ISO does | ⬜ | |

### RC-3 · Set C, messages match ISO (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C28-07 | **OI-126 and OI-123** (interpreter: `FirstNonNull` with a "" constant; an empty `NotExist`): a probe telling the readings apart; the smaller change proposed | ⬜ | the user's go |
| C28-08 | **OI-125** (a submitted value standing in for a field the rules write later): probe a second unguarded computed field before generalising | ⬜ | the user's go |
| C28-09 | **OI-112** (2023-edition checkbox answers): propose reading them as blank on those parents, or documenting it | ⬜ | the user's go |
| C28-10 | **OI-114** (`<rul:Null/>`, old builds only): the discriminating probe at a back date, then null-as-false or leave | ⬜ | the user's go |
| C28-11 | **Build and confirm** each item given a go; the (level, message) multisets re-compared on chunk 27's cases | ⬜ | |

### RC-4 · Set D, form names (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C28-12 | **OI-106**: `FormPage` tables resolved as state rows plus countrywide rows (state first); Rate and Domain tables stay wholesale | ⬜ | the user's go |
| C28-13 | **Confirm**: every `ErcFormName` / `ErcFormNumber` on chunk 27's saved responses equal to ISO's | ⬜ | |
| C28-14 | **OI-116**: the question for ISO written up (the three probes and their responses); ours keeps the record until answered | ⬜ | |

### RC-5 · Sets B and E, validation and referral (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C28-15 | **The silent-zero table**: each of the eight inputs (and NY's missing Group II symbol) run on ours and at ISO, classed "ISO also $0" (validation only) or a divergence (moves to set A or C) | ⬜ | analysis |
| C28-16 | **Design**: one outcome layer above the premium (rated / refer to company / invalid input), what triggers each (C28-15's table, OI-113), and how a caller sees it | ⬜ | the user's go |
| C28-17 | **Build** (with the go), never changing a premium ISO agrees with | ⬜ | |
| C28-18 | **Confirm**: every C28-15 input returns its outcome; every golden case still rates, unchanged | ⬜ | |

### RC-6 · Set F, dates beyond the corpus (2 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C28-19 | **Flag out-of-coverage dates**: a request dated after the latest package the corpus holds for its state, against the dates `242_` measured | ⬜ | the user's go |
| C28-20 | **Corpus refresh** (a data job, not an engine change): the 34 missing packages, if the user wants dates past 2026-09-17; `242_` re-run until every date matches | ⬜ | the user's decision |

### RC-7 · Close-out (2 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C28-21 | **Set G, housekeeping**: only if the user asks, and never in the same change as a rating fix | ⬜ | optional |
| C28-22 | **File `CF-CHUNK28-GATE.md`**: each item fixed, documented as matching ISO, or left open with the user's decision recorded | ⬜ | |
