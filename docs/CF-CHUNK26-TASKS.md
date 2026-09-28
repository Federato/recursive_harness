# Property chunk 26: task list and status

**Specific and Tentative rating: the second way to rate the core coverages, using a rate
published for one building instead of the class tables.** Tasks set 2026-09-28; chunk 18 is
being built in the other terminal, and chunks 19–25 wait.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 26) and the opening census ([`907_chunk26_census.py`](../scripts/cf/907_chunk26_census.py),
run 2026-09-28, 1 min, log `results/cf-raas/logs/chunk26_census.log`). The chunk adds no files, so
this census is a **branch census**. It covers every rule, countrywide and in the 46 states, that tests
`RatingType` / `RatingTypeBasicGroupII` or reads a specific or tentative rate; the tables and domains
behind them; the messages; the editions; and the ISO evidence already stored.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Order.** After chunk 25. The path runs through chunks 1–8's core files. Builders Risk's own
Tentative Group I rate belongs to chunk 24; this chunk only confirms nothing is counted twice.

**Status: TASKS SET 2026-09-28, 1 of 23** (the census). Next, once chunk 25 is gated: RC-1, C26-02.

---

## In plain English first

Normally a building's rate comes from ISO's class tables (**Class** rating). For some buildings
the rating bureau publishes a rate for that exact building (**Specific**), or a provisional one
while the published rate is pending (**Tentative**). Many states also let **Group II** (wind and
extended perils) be rated specifically, but only for buildings above a size threshold for their
hazard level. California has a fourth option, **One-Term Loss Cost**.

**Why this chunk is smaller than the plan said.** The engine does not hand-code rating paths: it
runs ISO's rule files. The Specific and Tentative branches are already in what it runs; they
have never been *tested*. And the evidence is not zero: the Excel-rater and payload-generator
projects stored **hundreds of ISO responses on Specific-rated buildings**. The payload generator
already matched Excel = ISO = engine on its 47 Specific-rated payloads (2026-09-23).

## What the census found, before any task ran

**Countrywide: 7 files, 33 rules.**

| File | What tests the rating type | Values |
|---|---|---|
| **Structure** (chunk 1) | `SetBasicGroupIRate` (reads `SpecificGroupIRate`), `SetRatingIdentificationCode`, attaches the **Tentative Rate** form; and **Class-only** rules: base rate, protection class factor, seven occupancy counts | Class / Specific / Tentative |
| **Business Income** (chunk 5) | `SetBasicGroupIRate`, `SetRatingIdentificationCode` | Class / Specific / Tentative |
| **Personal Property** (chunk 4) | `SetRatingType` (**copied down**, not chosen), `SetBasicGroupIRate` (reads `SpecificGroupIRate` but tests only "Class"), `SetRatingIdentificationCode`; Class-only base rate, fire-safe vault and protection class factors | Class (+ ID code) |
| **Occupancy** | `SetRatingType` (copied down), class code to use and group: Class only | Class |
| **Tentative Rate** (form record) | its own initialisation | — |
| **Builders Risk renovations / premium adjustment** (chunk 24) | completed-building Group I rate with a **Tentative Group I rate** | Class / Specific / Tentative |

Special Class and SCBI have no rating-type branch; Group II, Broad and Special are class-only
countrywide.

**States: 41 of 46 have their own rating-type rules; 36 test `RatingTypeBasicGroupII`.**
The 36 (AL AR CO CT DE FL GA IA IL IN KS KY MA MD MI MN MO MT NC ND NE NH NJ NM NY OH OK PA RI SC SD TN
TX VA WI WY) rate **Specific Group II** on Building, Contents and BI. Eligibility is by hazard level
and floor area: Severe ≥ 10,000 sq ft, High ≥ 25,001, Medium ≥ 50,001, Low never. FL adds a
non-residential risk programme. **Ten states rewrite the Group I branch** (`SetBasicGroupIRate` /
`…BaseRate`): AK AZ CA DC FL IL KY NJ NY WV, most on both building and contents, DC on BI too. CA DC
NJ NY also rewrite Builders Risk's. **ME NV OR UT VT have no rating-type rule** and run the countrywide branch.
Chunk 2 already found the price of omitting `RatingTypeBasicGroupII`: Group II **silently $0** in
36 states.

**Domains.** Countrywide, Specific and Tentative are offered on **146 of 396** building class codes
(Class on 104), and `DomainCovForm` is keyed by rating type. **CA adds a fourth value, "One-Term Loss
Cost"**, on 150+ class codes. FL GA KS NY file their own class-code domains; KS its own coverage forms.

**Messages: 11 rules.** The hazard-level floor-area thresholds (in ~20 packages, two wordings), FL's
non-residential programme (2), and DC's "fraternity or sorority houses are ineligible for class
rating; specific loss costs apply".

**Editions.** Missouri's CW 2023 V02 differs in **4 branch rules**: Structure's and Business
Income's `SetBasicGroupIRate`, and two conditional-mandatory rules.

**Evidence already stored** (requests; most have a paired ISO response):

| Rating type | Requests | States | ISO premium on the building |
|---|---|---|---|
| `RatingType` = Specific | 583 (47 payload generator, 536 scenarios) | FL 426, AL 24, OK 19, SC 19, CT 16, MI 14, WV UT NJ NC KY IA 13 each, CA 12, MO 6 | Group I **non-zero on 566**; Group II non-zero on 555, **zero on 11** |
| `RatingType` = Tentative | 5 | FL | Group I and II non-zero on all 5 |
| `RatingTypeBasicGroupII` = Specific | 13 | FL, OH, NY | non-zero |
| failed calls | 33 | | refused: reason to establish |

**What shapes the plan:**

1. **Replay before probing.** Hundreds of ISO answers already exist. RC-1 runs the engine on every
   stored Specific / Tentative request with a response, so the first result is hand = engine = ISO,
   or a list of disagreements, at no ISO cost.
2. **The rating type is copied down, not chosen, on contents and occupancy.** Personal Property's
   `SetBasicGroupIRate` reads `SpecificGroupIRate` but tests only "Class". Whether contents on a
   Specific building uses its own specific rate, the building's, or the class rate has to be traced,
   not assumed. The rater sends both.
3. **Specific Group II is the state layer, and its default is a silent zero.** 36 states, eligibility
   by hazard level and floor area; the 11 zero Group II premiums in the evidence and chunk 2's finding
   point at `RatingTypeBasicGroupII` defaults.
4. **Class-only factors drop out.** On a Specific building the base rate, protection class factor,
   fire-safe vault factor and occupancy counts are skipped. Each is tested at a value where it would
   have moved a dollar, so "skipped" is proven rather than coincidental.
5. **California's fourth value.** "One-Term Loss Cost" appears only in CA's domains. What it
   prices is unknown until traced.
6. **Chunks 1–8 must not move.** Every golden figure and all 293 stored policies stay put on the
   Class path.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-01 | **Opening census**: every rating-type branch in CW and the 46 states, tables and domains, messages, editions, and the stored evidence with ISO's premiums | ✅ | **Done 2026-09-28** (`907_chunk26_census.py`, 1 min). Findings above: 7 CW files / 33 rules; 41 states with rules, 36 on Group II; CA's fourth value; 11 messages; MO differs in 4 rules; 583 Specific + 5 Tentative + 13 Group II Specific requests priced by ISO |
| C26-02 | **Replay the stored evidence**: run the engine on every stored Specific / Tentative request with a response (583 + 5 + 13, 14 states); hand = engine = ISO on the building and its contents / BI, by state; explain the 11 zero Group II premiums and the 33 failed calls. No ISO calls | ⬜ | |
| C26-03 | **The branch map on real trees**: where `RatingType` is set and where it is copied (Occupancy, Personal Property), each `SetBasicGroupIRate` and `SetRatingIdentificationCode`, the Tentative Rate form attach, the Class-only rules | ⬜ | gate 6 |
| C26-04 | **Contents and BI on a Specific building**: which rate each uses (own `SpecificGroupIRate`, the building's, or class), traced and then predicted both ways | ⬜ | gate 6 |
| C26-05 | **Specific Group II**: the 36 states' rules, hazard-level and floor-area eligibility, `RatingTypeBasicGroupII` defaults (chunk 2's silent zero), FL's non-residential programme | ⬜ | |
| C26-06 | **Domains**: the 146 eligible class codes, `DomainCovForm` by rating type, FL GA KS NY's own domains, and CA's **"One-Term Loss Cost"** (what it selects and prices) | ⬜ | gates 2, 5 |

### RC-2 · Golden cases (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-07 | **Building Specific Group I** in a countrywide-branch state (OR), a rate chosen so the class rate would give a different dollar; ISO live | ⬜ | gate 1 |
| C26-08 | **Tentative**: building, contents and BI, with the Tentative Rate form record; ISO live | ⬜ | |
| C26-09 | **Contents and BI on a Specific building**, predicted under each reading C26-04 left standing; ISO live | ⬜ | |
| C26-10 | **Specific Group II**: Severe, High and Medium hazard just above their floor-area thresholds, in a state with the rule; ISO live | ⬜ | |
| C26-11 | **California One-Term Loss Cost**: building (and contents / BI if offered); ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-12 | **Zero cases**: Specific or Tentative with no rate; an ineligible class code; `RatingTypeBasicGroupII` blank; Group II Specific below the floor area; `RatingType` sent on Special Class (ignored); predict both readings, ISO live | ⬜ | gate 4 |
| C26-13 | **Messages**: all 11, each triggered and silent, the floor areas at 9,999 / 10,000, 25,000 / 25,001 and 50,000 / 50,001, FL's programme and DC's fraternity rule; ISO live | ⬜ | gate 9 |
| C26-14 | **Shared names**: `RatingType` on Structure vs the copies on Occupancy and Personal Property, `SpecificGroupIRate` on Structure vs Personal Property, `TentativeRate` vs Builders Risk's `TentativeGroupIRate`, diffed rather than assumed; whether a submitted copy survives | ⬜ | gate 6 |
| C26-15 | **The class-only factors drop out**: protection class, base rate, fire-safe vault, occupancy counts, each set to a value that would move a class-rated dollar, on a Specific building | ⬜ | gate 7 |

### RC-4 · States and editions (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-16 | **The Group I rewrites**: AK AZ CA DC FL IL KY NJ NY WV (and DC's specific-loss-cost rule), each predicted from the state's own rule; ISO live | ⬜ | |
| C26-17 | **The five countrywide-branch states** (ME NV OR UT VT): the CW path confirmed, including that Group II stays class-rated there | ⬜ | |
| C26-18 | **Editions**: MO (CW 2023 V02) golden probes for the 4 rules that differ; one probe each on a V03 and a V04 state | ⬜ | gate 8 |
| C26-19 | **All 46 states**: a Specific building per state, Group I everywhere and Group II where offered, predicted per state; ISO live | ⬜ | gate 3 |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-20 | **Downstream and no-move**: the policy total on a Specific building, with a clean test predicted first; terrorism; the rating identification stat codes; **chunks 1–8's golden figures and all 293 stored policies unchanged**; ISO live | ⬜ | |
| C26-21 | **Regression**: add the chunk 26 scripts and the replay (C26-02) as a regression check; full run CLEAN for chunks 0–26 (`--jobs 4`); `157_ --all` | ⬜ | |
| C26-22 | **Census close**: no new files (546 of 546 unchanged); record the second rating path as built in `CF-BUILD-STATUS.html` and `Coverage_Inventory_And_Tracking.md` | ⬜ | |
| C26-23 | **File `CF-CHUNK26-GATE.md`** | ⬜ | |
