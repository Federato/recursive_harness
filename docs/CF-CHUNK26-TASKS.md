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

**Status: GATED 2026-10-02, 23 of 23, 9 of 9** ([`CF-CHUNK26-GATE.md`](CF-CHUNK26-GATE.md); RC-1–RC-5 `234_`–`238_`, every premium ISO agreed on; no engine change). 546 of 546 unchanged; the second rating path built. Open: OI-124 (ISO agrees), OI-125 (messages only).

## RC-1 findings (2026-10-02), in plain English first

**The stored evidence already agrees.** The 598 stored Specific / Tentative requests are 138 distinct policies (the scenario
runs repeat), 126 with an ISO response, in 16 states (AL CA CT FL IA KY MI MO NC NJ NY OH OK SC UT WV). **Every one re-rates
with every premium equal to ISO (15,234 premiums) and the same messages.** The hand model (below) equals the engine on all
122 Specific / Tentative buildings, their contents and BI, and on all 15 Group II rates under a state's Specific Group II rule.

| What | Finding |
|---|---|
| **Building Group I** | Specific / Tentative replace the whole class chain with r3(r3(SpecificGroupIRate × LCM) × sprinkler-leakage-not-excluded factor × roof ACV factor) (CW). **FL, NY, WV and MO (CW 2023 V02)** round once and drop the roof factor; **KY** rounds once and keeps it; **CA** adds "One-Term Loss Cost" to the same branch. Base rate, protection class and territory factors are not in the formula |
| **Copied, not chosen** | the occupancy and the contents COPY the building's `RatingType`. **Contents price on their OWN `SpecificGroupIRate`** (any value but "Class"); with none of their own they rate **0** (a silent $0 Group I, probed live in RC-3). **BI uses the building's `SpecificGroupIRate`** (MO V02: the building's final rate × the BI adjustment, any rating type) |
| **Tentative** | prices exactly like Specific; it also attaches the Tentative Rate form record. Specific and Tentative share rating identification code 1 (Class: 2) |
| **Group II** | 36 states carry `RatingTypeBasicGroupII`. "Specific" → r3(r3(r3(SpecificGroupIIRate × LCM) × BCEG) [× (1 − wind mitigation credits) in 3 states]); **NY**: (rate + plastic-greenhouse factor) × LCM × windstorm protective devices. **Blank → 0.0 on building, contents and BI** (chunk 2's silent zero, shown on OK). Messages: Severe < 10,000 sq ft (20 states), High < 25,001 (20), Medium < 50,001 (21); **FL: Specific Group II is not eligible on 21 residential class codes** (0074–0343), message only |
| **California One-Term Loss Cost** | the building and contents price exactly as Specific; **BI's rule does not name it, so BI's Group I rate falls to 1.0** and no rating identification code is written: probed live in C26-11 |
| **Zero Group II at ISO** | the census's 11 are 4 distinct policies, all buildings with CovType "Legal Liability" (no building Group II to price): explained |
| **RC-2 (C26-07..11)** | **ISO agrees on all 7 golden cases**, each with a competing reading ISO did not match: Specific building Group I $362 (class $287), contents $150 on their own 0.200 (class $197), BI $137 on the building's rate (class $109); Tentative the same plus the Tentative Rate form; contents' own 0.450 → $335 (the building's rate would give $223); **SC Specific Group II** at Severe 10,000 / High 25,001 / Medium 50,001 sq ft: building $67, contents $37, BI $24 (Class $175 / $90 / $12); **CA One-Term: BI $538 at rate 1.0 (OI-124)**, not the Specific reading's $121. Payload: outside OR set the location's `BasicGroupIIRatingTerr` to a territory the state's Group II rate table files (SC: Inland / Seacoast / Beach): the class base-rate lookup runs even on a Specific Group II building and ISO refuses a missing row (ours priced: OI-99) |
| **RC-3 (C26-12..15)** | **A blank `RatingType` prices the building's Group I at rate 1.0 ($1,204, where Specific gives $362 and Class $287) and BI at 1.0 ($538)**; the contents still take their own specific rate; ISO the same. No `SpecificGroupIRate` → building AND BI Group I $0 (BI reads the building's rate), silently; contents with none of their own $0. Specific on a class code the domain offers only for Class (0581) rates as written (domains are not enforced in rating). Blank `RatingTypeBasicGroupII` → Group II $0 on all three, silently. The hazard messages fire below each threshold (SC Severe 9,999, High 25,000, Medium 50,000; OK's period wording; MI / OH Low) **and the specific Group II still prices**; FL's residential-class message on building and contents; DC's fraternity message on Class only. A submitted occupancy / contents `RatingType` is overwritten by the copy; a submitted building `BasicGroupIRate` survives ($602 at 0.500) while BI keeps reading `SpecificGroupIRate`. Protection class, the Group I territory factor and the contents' fire-safe vault factor move no Specific dollar (each moves a Class one). **OI-125**: the occupancy counts behind seven "only one … per building" messages are 0 at ISO even when the occupancy's rating type is submitted; ours counts it (messages only). No rule reads a `TentativeRate` field; Builders Risk's `TentativeGroupIRate` is read only by its own renovations / premium adjustment |
| **RC-4 (C26-16..19)** | **All 46 states agree with ISO** on a Specific building (Group I everywhere, Specific Group II in the 36 states that offer it). A submitted roof ACV factor of 0.900 made each state's shape show: the countrywide shape (and CA, the five countrywide-branch states ME NV OR UT VT, and AK AZ DC IL NJ, whose rewrites keep it) and KY price on 0.270 (OR building $326), **FL NY WV and MO ignore the roof factor** and price on 0.300 (FL / NY $354). **MO's CW 2023 V02 rules, and ISO follows them**: no roof factor ($362, the 2026 reading 0.270), and BI on the building's FINAL rate (a submitted 0.500 → BI 0.400, $215; the 2026 reading keeps BI at 0.240). Of the census's edition differences only MO's 4 rules name the rating type (V03's 91 and V02's other 139 are elsewhere in the core files, V04 none); MO's two conditional-mandatory rules call `SetRatingType` exactly as 2026 does |
| **The 31 failed calls** | none touches the rating type: ISO refused on missing rows in Special Class tables (14), wind hazard (5), BCEG EQ (5), FL's cyber factors (5), a legal-liability option (1) and one payload type (1). **Ours prices all 31**: more cases of OI-99 (a lookup that finds no row is an error at ISO), for chunk 28 |

**Carried from chunk 21 (2026-09-30): the census `907_` now diffs EVERY rule of the family files across the four countrywide editions** (`scripts/cf/_edition_rules.py`, chunk 20's gate item): 7 files naming the rating-type fields: MO V02 143, V03 91, V04 0 rule differences from 2026 V01. The editions task must judge each one; the census's earlier "identical in all four editions" was a SetPremium-only check. Chunk 21 also found its own edition difference in a PARENT file (MO's sewer caps read `Limit`, not `LimitToUse`): diff the parent files' rules that name this chunk's records too.

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
| C26-02 | **Replay the stored evidence**: run the engine on every stored Specific / Tentative request with a response (583 + 5 + 13, 14 states); hand = engine = ISO on the building and its contents / BI, by state; explain the 11 zero Group II premiums and the 33 failed calls. No ISO calls | ✅ | **Done 2026-10-02** (`234_`): 598 stored → 138 distinct → 126 with a response, 16 states: **every premium equal to ISO on 126 of 126** (15,234), messages equal on 126; hand = engine on 122 buildings / contents / BI and 15 Group II rates; the 4 distinct zero Group II premiums are Legal Liability buildings; the 31 failed calls are missing rows elsewhere, which ours prices (OI-99) |
| C26-03 | **The branch map on real trees**: where `RatingType` is set and where it is copied (Occupancy, Personal Property), each `SetBasicGroupIRate` and `SetRatingIdentificationCode`, the Tentative Rate form attach, the Class-only rules | ✅ | gate 6. **Done 2026-10-02** (`234_`): `RatingType` set on the building and COPIED to the occupancy and the contents; Tentative Rate form attaches only on Tentative; identification code 1 (Specific / Tentative) vs 2 (Class); the Specific formula carries none of the class-only factors (C26-15 moves each) |
| C26-04 | **Contents and BI on a Specific building**: which rate each uses (own `SpecificGroupIRate`, the building's, or class), traced and then predicted both ways | ✅ | gate 6. **Done 2026-10-02** (`234_`): contents on their own `SpecificGroupIRate` (0.200, where the building's 0.300 would differ); BI on the building's (0.255); contents with no own rate → 0 |
| C26-05 | **Specific Group II**: the 36 states' rules, hazard-level and floor-area eligibility, `RatingTypeBasicGroupII` defaults (chunk 2's silent zero), FL's non-residential programme | ✅ | **Done 2026-10-02** (`234_`): 36 states; three Specific shapes (32 BCEG, 3 + wind mitigation, NY greenhouse + protective devices); thresholds 10,000 / 25,001 / 50,001 by hazard; blank `RatingTypeBasicGroupII` → 0.0 on all three records; FL excludes 21 residential class codes |
| C26-06 | **Domains**: the 146 eligible class codes, `DomainCovForm` by rating type, FL GA KS NY's own domains, and CA's **"One-Term Loss Cost"** (what it selects and prices) | ✅ | gates 2, 5. **Done 2026-10-02** (`234_`): rating types are domain-driven (`DomainClassCodeBldg` 146 Specific / Tentative codes, occupancy 142, `DomainCovForm` keyed by policy type and rating type, 26 rows; FL GA KS NY CA file their own); **CA One-Term Loss Cost** prices building / contents as Specific, BI falls to 1.0 (probe C26-11) |

### RC-2 · Golden cases (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-07 | **Building Specific Group I** in a countrywide-branch state (OR), a rate chosen so the class rate would give a different dollar; ISO live | ✅ | gate 1. **Done 2026-10-02** (`235_` G1): building Specific 0.300 → Group I $362 (the class rate would give $287), contents $150, BI $137; ISO agrees on 123 of 123 premiums and the messages |
| C26-08 | **Tentative**: building, contents and BI, with the Tentative Rate form record; ISO live | ✅ | **Done 2026-10-02** (`235_` G2): Tentative prices exactly as Specific ($362 / $150 / $137) and attaches the Tentative Rate form record; ISO agrees |
| C26-09 | **Contents and BI on a Specific building**, predicted under each reading C26-04 left standing; ISO live | ✅ | **Done 2026-10-02** (`235_` G1, G3): contents on their OWN rate (0.450 → $335; on the building's 0.300 they would be $223), BI on the building's ($137); ISO agrees, matching neither competing reading |
| C26-10 | **Specific Group II**: Severe, High and Medium hazard just above their floor-area thresholds, in a state with the rule; ISO live | ✅ | **Done 2026-10-02** (`235_` S1–S3, SC): Severe 10,000, High 25,001, Medium 50,001 sq ft (each at its threshold: eligible, no message); Specific Group II building $67, contents $37, BI $24 vs Class $175 / $90 / $12; ISO agrees. The location's Group II territory must be one the state's rate table files (ISO refused '001') |
| C26-11 | **California One-Term Loss Cost**: building (and contents / BI if offered); ISO live | ✅ | **Done 2026-10-02** (`235_` C1, CA): building $354 and contents $146 as Specific; **BI $538 at rate 1.0** (BI's rule does not name One-Term), not $121; rating identification code blank on building and BI at ISO and ours; ISO agrees on 137 of 137: **OI-124** |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-12 | **Zero cases**: Specific or Tentative with no rate; an ineligible class code; `RatingTypeBasicGroupII` blank; Group II Specific below the floor area; `RatingType` sent on Special Class (ignored); predict both readings, ISO live | ✅ | gate 4. **Done 2026-10-02** (`236_` Z1–Z6): no specific rate → building and BI $0; contents with no own rate $0; a Class-only class code rates as written; blank Group II rating type → Group II $0 on all three; **blank `RatingType` → rate 1.0 on building ($1,204) and BI ($538)**; `RatingType` on the Special Class ignored; ISO agrees on every premium and message |
| C26-13 | **Messages**: all 11, each triggered and silent, the floor areas at 9,999 / 10,000, 25,000 / 25,001 and 50,000 / 50,001, FL's programme and DC's fraternity rule; ISO live | ✅ | gate 9. **Done 2026-10-02** (`236_` M1–M8b, with RC-2's silent S1–S3): Severe / High / Medium fired one below each threshold (SC; OK's wording with a period), Low in MI and OH (both wordings), FL's non-residential message on building and contents, DC's fraternity message on Class and silent on Specific; the specific Group II still prices under the message; ISO agrees on every (level, message) |
| C26-14 | **Shared names**: `RatingType` on Structure vs the copies on Occupancy and Personal Property, `SpecificGroupIRate` on Structure vs Personal Property, `TentativeRate` vs Builders Risk's `TentativeGroupIRate`, diffed rather than assumed; whether a submitted copy survives | ✅ | gate 6. **Done 2026-10-02** (`236_` S1, S2, and the rule text): a submitted occupancy / contents `RatingType` is overwritten by the copy; a submitted building `BasicGroupIRate` survives ($602) and BI still reads `SpecificGroupIRate`; contents' and building's `SpecificGroupIRate` are independent (RC-2 G3); no rule reads a `TentativeRate` field, and Builders Risk's `TentativeGroupIRate` is read only by its renovations / premium adjustment: nothing counted twice; ISO agrees |
| C26-15 | **The class-only factors drop out**: protection class, base rate, fire-safe vault, occupancy counts, each set to a value that would move a class-rated dollar, on a Specific building | ✅ | gate 7. **Done 2026-10-02** (`236_` K1–K4d): protection class 10, Group I territory "Balance of State" and a fire-safe vault factor of 0.5 leave every Specific premium equal to G1's while each moves a Class premium; the seven occupancy counts are Class-only (a Specific building stays 0); **OI-125**: the count is 0 at ISO even with the occupancy's rating type submitted (ours 2, message only) |

### RC-4 · States and editions (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-16 | **The Group I rewrites**: AK AZ CA DC FL IL KY NJ NY WV (and DC's specific-loss-cost rule), each predicted from the state's own rule; ISO live | ✅ | **Done 2026-10-02** (`237_` S-AK … S-WV): each rewrite priced from the state's own rule: AK AZ DC IL NJ keep the countrywide shape; CA adds One-Term; FL NY WV round once without the roof factor ($354 where the countrywide shape gives $326); KY keeps it; DC's fraternity rule in RC-3; ISO agrees on every premium and message |
| C26-17 | **The five countrywide-branch states** (ME NV OR UT VT): the CW path confirmed, including that Group II stays class-rated there | ✅ | **Done 2026-10-02** (`237_` S-ME S-NV S-OR S-UT S-VT): the countrywide path (roof factor in: 0.270, OR $326); Group II stays class-rated there (no RatingTypeBasicGroupII rule); ISO agrees |
| C26-18 | **Editions**: MO (CW 2023 V02) golden probes for the 4 rules that differ; one probe each on a V03 and a V04 state | ✅ | gate 8. **Done 2026-10-02** (`237_` E-MO1, E-MO2, the every-rule diff): MO (V02) prices Specific without the roof factor (0.300, not 0.270) and BI on the building's FINAL rate (0.400 / $215 where 2026 gives 0.240): **ISO follows V02** on both; MO's two conditional-mandatory differences do not touch the branch; NC (V03, 91 differences, none naming the rating type) and IL (V04, none) price as 2026 in their S- cases |
| C26-19 | **All 46 states**: a Specific building per state, Group I everywhere and Group II where offered, predicted per state; ISO live | ✅ | gate 3. **Done 2026-10-02** (`237_ --live --states`, 4 batches): **all 46 states agree with ISO**, every premium and (level, message); Specific Group II in the 36 states (each on its first filed Group II territory and wind-hazard territory) |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C26-20 | **Downstream and no-move**: the policy total on a Specific building, with a clean test predicted first; terrorism; the rating identification stat codes; **chunks 1–8's golden figures and all 293 stored policies unchanged**; ISO live | ✅ | **Done 2026-10-02** (`238_ --live`): Class → Specific moves the total by exactly the core records' differences, +$56 (OR) / +$701 (rates doubled, the clean test) / +$68 (FL) / −$149 (SC Group II) / −$794 (MO), predicted before each call and equal at ISO; every other premium and terrorism unchanged; stat values and identification codes equal; chunks 1–8's golden figures and the 293 stored policies unchanged (C26-21) |
| C26-21 | **Regression**: add the chunk 26 scripts and the replay (C26-02) as a regression check; full run CLEAN for chunks 0–26 (`--jobs 4`); `157_ --all` | ✅ | **Done 2026-10-02** (no engine change: the scaled-back gate): `104_ --quick` CLEAN (34 scripts, every golden case of chunks 1–26 and the chunk 26 scripts, the 234_ replay as the regression check); `206_ --check` SNAPSHOT CLEAN (1,697 requests); `157_ --all` 293 of 293; 235_ pinned (362 150 335 137 67 37 24 354 146 538) |
| C26-22 | **Census close**: no new files (546 of 546 unchanged); record the second rating path as built in `CF-BUILD-STATUS.html` and `Coverage_Inventory_And_Tracking.md` | ✅ | **Done 2026-10-02**: `166_` 546 of 546 unchanged; the second rating path recorded as built on the status page and in `Coverage_Inventory_And_Tracking.md` (engine only; the Excel rater's gap unchanged) |
| C26-23 | **File `CF-CHUNK26-GATE.md`** | ✅ | **Done 2026-10-02**: [`CF-CHUNK26-GATE.md`](CF-CHUNK26-GATE.md), 9 of 9 |
