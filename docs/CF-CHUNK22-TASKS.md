# Property chunk 22: task list and status

**Multi-location: the Value Reporting Form and Additional Locations Special
Coinsurance. This is the first chunk whose prices depend on more than one location.**
Tasks set 2026-09-28; chunk 18 is being built in the other terminal, and chunks 19–21 wait.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 22, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`903_chunk22_census.py`](../scripts/cf/903_chunk22_census.py), run 2026-09-28,
3 s, log `results/cf-raas/logs/chunk22_census.log`). It runs the same checks as `902_` (messages in
every rule file, `SetPremium` per in-force edition, form numbers from `Form Pages`, sibling
names). It adds a tenth for this chunk: **the multi-location trail**, meaning every rule file,
countrywide and in the 46 states, that writes or reads a multi-location average-rate field or
runs the additional-locations roll-up.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Order.** After chunk 21. It reads chunk 9's blanket average rates and every coverage's
finished rate (chunks 1–8, 10), and it runs rules in the **main ruleset, which is already built**
(see point 3 below). **No stored ISO policy has more than one location**, so every golden case is a
new live probe.

**Status: TASKS SET 2026-09-28, 1 of 24** (the census). Next, once chunk 21 is gated: RC-1, C22-02.

**Carried from chunk 21 (2026-09-30): the census `903_` now diffs EVERY rule of the family files across the four countrywide editions** (`scripts/cf/_edition_rules.py`, chunk 20's gate item): 19 family files: MO V02 29, V03 4, V04 0 rule differences from 2026 V01. The editions task must judge each one; the census's earlier "identical in all four editions" was a SetPremium-only check. Chunk 21 also found its own edition difference in a PARENT file (MO's sewer caps read `Limit`, not `LimitToUse`): diff the parent files' rules that name this chunk's records too.

---

## In plain English first

- **Value Reporting Form** (CP 13 10): instead of fixing a contents limit, the insured
  reports values each period. On a multi-location risk the insurer can price every location at one
  **multiple-location average rate** (MLAR) rather than each location's own rate. A
  **General Information** record at policy level holds the reporting details and prices
  incidental and newly acquired locations.
- **Additional Locations Special Coinsurance** (CP 13 20): lets smaller extra locations carry a
  special coinsurance arrangement, priced at the same average rates.
- The two forms **cannot be on the same policy** (a message says so). Each writes its own set
  of average rates.

**None of the 16 premium records has ever been priced by ISO**, and none appears on any
stored example policy.

## What the census found, before any task ran

| Family | Premium records | Rate source | Tables read directly (CW rows) | States that rewrite it | Messages (any file) | Editions |
|---|---|---|---|---|---|---|
| **Value Reporting Form** (CP 13 10; Group I, Group II, Broad, Special, EQ + General Information) | 6 | each coverage chooses between its **MLAR**, the **blanket average rate** (chunk 9) and **its own final rate**, keyed on `MultiLocAvgRatesIndicator` and `IncludedInBlkt`. General Information prices **incidental and acquired locations** | 10: incidental locations rate (4), acquired locations rate (1), new business factor (1), seasonal risk factor (1), coinsurance (3; FL), 3 indivisible sublines, 2 peril-exclusion stat-code tables (AR DC) | AL AR DC NY RI (wind / hail excluded indicator only) | **29** (3 shared with CP 13 20): average value only when MLAR is used / new business; alcoholic beverage tax value needs CP 99 10; cause of loss identical across reported records; not with CP 10 29 / 10 45 / 12 30 / 13 20; CP 13 30 needs CP 13 10; General Information required; Public Institutional Plan (AL KS RI); CA CP 10 43 sub-limit | same in all four |
| **Additional Locations Special Coinsurance** (CP 13 20; Provisions per contents row + General Information; Group I, Group II, Broad, Special, EQ) | 10 | the **MLAR** it writes itself × coinsurance factor × limit; General Information uses the **total incidental-locations limit** | `AddlLocSpclCoinsFactor` (1), and the Value Reporting Form's **incidental locations rate** (4) | none | **14** (3 shared): General Information required; not with Agreed Value, blanket, CP 10 29 / 10 45, CP 13 10; cause of loss, coinsurance and EQ identical on every record; CA CP 10 43 | same |

**The multi-location trail (check 10).** Three families of writer, one reader set:

| Where | Writes | Reads |
|---|---|---|
| **Value Reporting General Information** (policy; 169 KB, 56 rules) | the five MLARs, `MLARLimit`, `TotalValueForMLARCalc`, `MaxPrsnlPropLimitForMLARCalc` | `MultiLocAvgRates` |
| **Value Reporting Form** (per contents row; 40 KB) | the five MLARs again | the indicator, its own MLARs |
| **Additional Locations General Information** (policy; 60 KB) | the five MLARs again, `TotalFullValueForMLARCalc` | its own totals |
| **Main ruleset (built)** | `MultiLocAvgRates`: `SetMultipleLocationsAvgRate` sets "Not Used" when no Value Reporting General Information exists, else copies it from record [1] (only when blank) | |
| **Main ruleset (built)** | `ErcResetPrsnlPropPremiumForAdditionalLocations` runs the Additional Locations roll-up for each General Information record | |
| **Personal Property (built)**; 9 states rewrite the file: AK AL AR CA DC FL GA NY RI | `MultiLocAvgRatesIndicator` | `MultiLocAvgRates`, `MLARLimit`, `TotalValueForMLARCalc` |
| **Occupancy (built)** | | `MultiLocAvgRatesIndicator` |
| **Blanket Rating Detail (built, chunk 9)**; CA rewrites | | `MultiLocAvgRates` |

Sibling names checked: only `BuildersRiskReportingForm`, which is chunk 24's. **44 message rules
listed, 41 distinct.** One is Builders Risk's, which leaves **40 in scope**. Three shared ones (terrorism
sub-limit, deductible "Not Applicable", non-owned trailers) are already tested by other chunks.
No date arithmetic, no `Power`, no unregistered element.

**What shapes the plan:**

1. **Three writers of the same five fields.** `BasicGroupIMLAR`, `BasicGroupIIMLAR`, `BroadMLAR`,
   `SpecialMLAR` and `EQMLAR` are each written by the Value Reporting General Information, by the
   Value Reporting Form on each contents row, and by the Additional Locations General
   Information. The forms are mutually exclusive, but the first two are on the same policy. RC-1
   establishes the order of writes and which value each reader sees, on a real tree, before any
   dollar is predicted. This is the standing "same field name ≠ same value" rule at its widest yet.
2. **Three rate sources per Value Reporting coverage.** Each reads its MLAR, the blanket
   average rate or its own final rate. The golden cases put the three at different values so the
   reading chosen decides the dollar.
3. **The chunk reaches into built code.** Two rules in the main ruleset, Personal Property's
   indicator rule (rewritten in 9 states), Occupancy and chunk 9's Blanket Rating Detail all
   touch these fields. Today they sit on "Not Used" (C14-14). Every stored policy must re-rate
   **unchanged**, which the census of built files alone cannot show.
4. **The plan's "resets the Contents premium" is not what the rule says.** The main-ruleset rule
   runs a General Information rule that loops every location's contents rows and writes the **sum
   of their Additional Locations Provisions premiums** into the General Information record's
   `PrsnlPropPremium`. That is a roll-up; the Contents premium itself is not reset. C22-03 traces
   it and C22-12 confirms which reading holds, live.
5. **The General Information file is the largest single rule file in the remaining build.**
   169 KB and 56 rules: incidental and acquired locations, new business, seasonal risk. It gets
   its own hand trace (C22-05) before any golden case.
6. **Averages round.** An average rate across locations is a division; where it rounds, and
   whether the sum or each term rounds first, decides the dollar on a large schedule (C22-20).
7. **Every probe is new.** There is no stored multi-location evidence at all.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C22-01 | **Opening census**: population, formulas, tables, messages by record and by form / wording, sibling names, every edition, state layer, stored evidence, attach points, engine readiness, **and the multi-location trail** | ✅ | **Done 2026-09-28** (`903_chunk22_census.py`, 3 s). Findings above: 16 premium records, none priced by ISO or stored; 40 messages in scope; three writers of the five MLARs; the main ruleset, Personal Property, Occupancy and Blanket Rating Detail touch the fields; identical in all four editions; no unregistered element |
| C22-02 | **Who writes the MLARs, in what order**: on a real two-location tree, trace each of the five MLARs and their totals through all three writers; which value each reader sees, and when; what CP 13 10 + CP 13 20 together would do if the message is ignored. No ISO calls | ⬜ | gate 6 |
| C22-03 | **The built touchpoints**: `SetMultipleLocationsAvgRate` (the "Not Used" default vs the copy from record [1]; the blank-only guard), Personal Property's indicator rule and its 9 state rewrites, Occupancy's read, Blanket Rating Detail's read (and CA's rewrite), and the roll-up (sum into `PrsnlPropPremium`, not a reset). **Re-rate all 293 stored policies unchanged** | ⬜ | gate 6 |
| C22-04 | **Attach map and switches**: the Value Reporting Form under each contents row, both General Information records at policy level, Provisions under contents; every on-switch; the three rate sources per Value Reporting coverage and what selects each; blank-input defaults that zero a premium | ⬜ | gate 2 (with C22-06) |
| C22-05 | **Value Reporting General Information by hand**: the 56 rules traced: incidental and acquired locations premiums, `NewBusnFactor`, `SeasonalRiskFactor`, the four incidental-locations rate rows, the MLAR arithmetic (`TotalValueForMLARCalc`, `MaxPrsnlPropLimitForMLARCalc`, `MLARLimit`); every step written down and checked against the engine | ⬜ | |
| C22-06 | **Tables and literals**: all 11 distinct tables' rows and key literals, the `MultiLocAvgRates` values ("Used", "Not Used", …) and where each comes from, FL's coinsurance, AR DC stat-code tables | ⬜ | gates 2, 5 |

### RC-2 · Golden cases (6 tasks), all new live probes

| # | Task | Status | Notes |
|---|---|---|---|
| C22-07 | **Value Reporting, MLAR not used**: two locations with different rates, each coverage group (Group I, Group II, Broad, Special, EQ) at its own final rate; the baseline; ISO live | ⬜ | gate 1 |
| C22-08 | **Value Reporting, MLAR used**: the same two locations with the average rate chosen so it equals neither location's; new-business average value; the alcoholic beverage tax value (CP 99 10); ISO live | ⬜ | |
| C22-09 | **Value Reporting, blanketed**: blanket average rate vs MLAR vs own rate on one policy, each at a different value, so precedence decides the dollar; ISO live | ⬜ | |
| C22-10 | **Value Reporting General Information**: incidental and acquired locations, seasonal risk, new business; each factor chosen to move a dollar; ISO live | ⬜ | |
| C22-11 | **Additional Locations Special Coinsurance**: two and three locations, Provisions on each contents row, General Information on the total incidental limit, EQ; ISO live | ⬜ | |
| C22-12 | **The roll-up**: the Contents premiums and the General Information `PrsnlPropPremium` before and after Additional Locations is added, predicted under both readings (roll-up vs reset); ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C22-13 | **Zero cases**: Value Reporting with no General Information; MLAR "Used" on one location; average value on a renewal; blank reported values; Additional Locations with no Provisions, with blanket, with Agreed Value; each switch off; predict both readings, ISO live | ⬜ | gate 4 |
| C22-14 | **Messages**: all 40, each triggered and silent, especially the "identical on every record" rules (cause of loss, coinsurance, EQ) across locations, the mutual exclusion, and the state versions (AL KS RI, CA); ISO live | ⬜ | gate 9 |
| C22-15 | **Shared names**: the five MLARs (three writers), `MultiLocAvgRates` and its indicator, `PrsnlPropPremium`, `LimitToUse`, `CoinsuranceFactor`, `IncludedInBlkt`, `TotalIncLocsLimit`, diffed rather than assumed; whether a submitted MLAR survives any writer | ⬜ | gate 6 |
| C22-16 | **Exclusion records**: the cyber-incident factors in all 16 premium formulas, and the wind / hail excluded indicator, each at a limit where it moves a dollar | ⬜ | gate 7 |

### RC-4 · States, editions and scale (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C22-17 | **The state layer**: AL AR DC NY RI's wind / hail indicator and AR DC's peril-exclusion codes; the 9 Personal Property rewrites (AK AL AR CA DC FL GA NY RI) as they touch the indicator; CA's Blanket Rating Detail; the Public Institutional Plan (AL KS RI); ISO live | ⬜ | |
| C22-18 | **Editions**: identical in all four; one multi-location probe each on MO (2023 V02), a V03 and a V04 state | ⬜ | gate 8 |
| C22-19 | **All 46 states**: a multi-location policy with each family on every state's own package, predicted per state; ISO live | ⬜ | gate 3 |
| C22-20 | **Scale and rounding**: a larger schedule (e.g. 8 locations of mixed rates) where rounding the average vs rounding each term gives different dollars; ISO live | ⬜ | |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C22-21 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; the blanket roll-up (chunk 9); terrorism; stat codes; **the 293 stored policies re-rated unchanged**; ISO live | ⬜ | |
| C22-22 | **Regression**: add the chunk 22 scripts and pin the golden figures; full run CLEAN for chunks 0–22 (`--jobs 4`); `157_ --all` | ⬜ | |
| C22-23 | **Census close**: count the two families as built in `166_` (504 → 520 of 546, 95%) | ⬜ | |
| C22-24 | **File `CF-CHUNK22-GATE.md`** | ⬜ | 16 countrywide premium files |
