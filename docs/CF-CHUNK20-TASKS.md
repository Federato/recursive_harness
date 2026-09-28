# Property chunk 20: task list and status

**Small coverages with their own tables: ten unrelated families, each read on its
own terms.** Tasks set 2026-09-28, while chunk 18 is open and chunk 19 waits.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 20, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`901_chunk20_census.py`](../scripts/cf/901_chunk20_census.py), run 2026-09-28,
28 s, log `results/cf-raas/logs/chunk20_census.log`). It carries the three census checks from
chunks 15 and 17, plus two added after chunk 19's census:
- **Form numbers come from the package's own `Form Pages` table.** They used to come from
  constants in the rule files, which these families lack, or from a hand-typed list.
- **Sibling names are flagged.** Any `Form Pages` row whose display name carries the family's
  wording but whose table name the family pattern misses is printed. This is how chunk 19's
  FL / MT `BuildingGlass…` files were missed.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Order.** After chunk 19. Nothing in chunk 20 reads chunk 18 or 19's records. It does read
chunk 9 (blanket averages), chunk 4's Contents Special rate and chunk 17's Watercraft tables.

**Status: TASKS SET 2026-09-28, 1 of 26** (the census). Next, once chunk 19 is gated: RC-1, C20-02.

---

## In plain English first

- **Radioactive Contamination**: damage from radioactive material used on the premises.
- **Pier and Wharf**: extra causes of loss (ice, collision by a vessel) for piers and wharves.
- **Fire Department Service Charge**: raises the limit for what the fire department bills for attending.
- **Tobacco Sales Warehouses**: tobacco held for auction, rated from its own table.
- **Furs, jewelry, patterns and dies, stamps**: raises the low theft limits on these items.
- **Additional Covered Property**: brings in property the form normally excludes.
- **Food Contamination**: lost income and advertising costs after a health-department shutdown.
- **Mortgageholders Errors and Omissions**: a lender's own cover, priced in layers by number of mortgages.
- **Fungus, Wet Rot, Dry Rot**: raises the mould sub-limit, priced incrementally.
- **Equipment Breakdown**: boilers and machinery bursting or breaking down.

**None of the 30 premium records has ever been priced by ISO** (28 countrywide + 2
NC-only). Four families sit at **$0 on stored policies**, the way chunk 18's did.
Fire Department is on all 364 buildings. Tobacco and all four furs / jewelry / patterns
/ stamps records are on 206 contents rows. The Business Income fungus records are on 82.
RC-1 says why before any golden case.

## What the census found, before any task ran

| Family | Premium records | Stored evidence | Tables read directly (CW rows) | States that rewrite it | Messages (any file) | Editions |
|---|---|---|---|---|---|---|
| **Radioactive Contamination** (CP 10 37; Building, Contents, Special Class, BI, SCBI) | 5 | none | subline (1); reads the **blanket average** `BlktRadioactiveContamination…` (chunk 9) | AL FL KS RI (`SetPremium`, 3 each) | **27**: limit required / not, Limited option vs cause of loss, missing rate, needs attaching when in blanket (×5 coverages) | same in all four |
| **Pier and Wharf** (CP 10 70; structure, Special Class, BI, SCBI) | 4 | none | `PierAndWharfRates` (6), **chunk 17's** `WatercraftExclusionBuybackConstructionOptionsConverted` (7) | AL KS RI (`SetPremium`) | 8 (4 shared with ACP): not valid with cause of loss; ACP required with CP 10 70 (CW, VA) | **1 file differs in CW 2023 V02** (MO) |
| **Fire Department Service Charge** (location) | 1 | **on all 364 buildings, always $0** | `FireDepartmentIncreasedLimit` / `…Factor` (1 each; AZ files its own) | AZ (switch), FL (limit), VA (limit and lookups) | 3: limit not increasing; higher limit needs selection; required coverage forms (KS NY VT own) | same |
| **Tobacco Sales Warehouses** (CP 00 80) | 1 | **on 206 contents rows, $0** | `TobaccoInSalesWarehousesRate` (4) | none | 1 (shared with Fire Department) | same |
| **Furs, jewelry, patterns and dies, stamps** | 4 | **on 206 contents rows, $0** | four base special limits (FL files all four); reads **Contents' `TheftLimitationSpecialFinalRate`** | FL (switches) | **15**: invalid with CP 10 33 or blanket cause of loss; revised amount not increasing; 3 found only by wording | same |
| **Additional Covered Property** (CP 14 10; NC CP 14 11; VA CP 14 12) | 2 + **2 NC-only** | none | **chunk 17's** Watercraft factor (6) and construction table (7), subline | AL KS RI (`SetPremium`); NC (rate, stat codes); NC's own 6 files; VA by form number only | **22**: required with CP 10 35 / 10 70, valid type, not valid with coverage; CW, NC and VA versions | same |
| **Food Contamination** (CP 15 05; BI and SCBI; food only, additional advertising) | 4 | none | food rate, advertising rate, code, subline (1 each; FL files all) | FL (switches, stat codes) | **0** | same |
| **Mortgageholders E&O** (CP 00 70) | 1 | none | `MortgageholdersErrorsAndOmissRate` (85; TX); **five layers**: first 500, next 500, next 4,000, next 10,000, over 15,000 mortgages | AK (limit per mortgage), NY (`SetPremium`), TX (rates) | **17**: a policy-level coverage form: no locations, no blanket, TRIA interplay, CP 10 75 / 76 (NY 77 / 78), Mine Subsidence (IL IN KY OK WV), CT CP 04 61, AK attorney-fee limit | same |
| **Fungus, Wet Rot, Dry Rot** (CP 04 31; policy) | 1 | BI fungus records **on 82 BI rows, $0** | excess-of-sublimit rate (1), incremental rate (1), increased-period factor (5); AK NY file all three | AK NY (switches + own state-only files, no premium), VA (`SetTotalPremium` on BI) | 5: CP 04 31 required, separate premises option, increased-period days (2 by wording) | same |
| **Equipment Breakdown** (CP 10 46; building and BI) | 5 | none | property damage premium (**195**), time element loss cost (15), `OccupancyGroupNumber` (**1,090**; FL GA KS NY), ammonia, codes, subline; hazardous substance is a **manual premium** | FL (switches), NY (BI `SetPremium`) | 2: not with cause of loss; CP 10 47 needs CP 10 46 | same |

**Sibling names checked, none priced.** MT `MortgageHoldersForm`, MA / TX
`LimitationsOnFungus…` and the Equipment Breakdown suspension form (CW, FL) all have rule
files with no premium. They matter only to the messages task.

No date arithmetic, no `Power`, no unregistered element anywhere in the chunk. **100 message rules**
listed; five are shared between families (one Fire Department / Tobacco, four Pier and Wharf /
ACP), so **95 distinct**.

**What shapes the plan:**

1. **Four families are already on stored policies at $0.** Fire Department (364),
   Tobacco and furs / jewelry / patterns / stamps (206) and the BI fungus records (82).
   As with chunk 18, RC-1 finds the switch before RC-2 predicts a dollar.
2. **Mortgageholders E&O is a different kind of thing.** It is a coverage form in its own
   right, priced by mortgage count in five layers, and it forbids locations, blanket
   rating and (with conditions) TRIA. Its golden case needs probes at each layer boundary,
   and its downstream check must include terrorism.
3. **Fungus is priced in two places.** The Business Income records compute
   `FinalBusinessIncomeFungusPremium`; the single policy-level file reads it with the
   excess-of-sublimit and incremental calculations. VA rewrites the BI side's total.
4. **Borrowed values from four finished chunks.** The blanket radioactive average rate (9),
   Contents' theft-limitation special rate (4), and chunk 17's Watercraft construction and
   factor tables (Pier and Wharf, ACP). C20-04 resolves each in its loop context.
5. **One manual premium.** Equipment Breakdown's hazardous-substance cover (other than
   ammonia) is company-entered, so it is chunk 15's shape.
6. **Three form numbers for one coverage.** ACP is CP 14 10 countrywide, CP 14 11 in NC
   (with NC's own six files) and CP 14 12 in VA. VA uses the countrywide files, so the
   difference shows up only in messages.
7. **Editions are nearly quiet.** Only Pier and Wharf's BI file differs, in MO's CW 2023 V02.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C20-01 | **Opening census**: population, formulas, tables, messages by record **and by form / wording** (forms from `Form Pages`), sibling names, every edition, state layer, stored evidence, attach points, engine readiness | ✅ | **Done 2026-09-28** (`901_chunk20_census.py`, 28 s). Findings above: 30 premium records (28 CW + 2 NC), none priced by ISO; 95 distinct message rules; 1 file differs in CW 2023 V02; siblings carry no premium; no date nodes; no unregistered element |
| C20-02 | **The $0 records**: why Fire Department (364), Tobacco and the four special-limit records (206) and BI fungus (82) price $0 on stored policies; which input switches each on, flipped one at a time. No ISO calls | ⬜ | |
| C20-03 | **Attach map and switches**: every record's parent (location, occupancy, contents, BI, SCBI, policy for Mortgageholders and Fungus; ACP's summary / detail records), the conditional forms (Tobacco on its occupancy, EB's BI record), every on-switch shape, every blank-input default that zeroes a premium | ⬜ | gate 2 (with C20-05) |
| C20-04 | **Borrowed values**: the blanket radioactive average rate, `TheftLimitationSpecialFinalRate`, chunk 17's Watercraft construction / factor tables, `FinalBusinessIncomeFungusPremium`, `LossCostMultiplier` and the modifiers, each resolved on a real tree in its loop context; hand = engine on every record, ordinary and blanket policy | ⬜ | gate 6 |
| C20-05 | **Tables and literals**: every table's rows and key literals (the 195-row EB premium, the 1,090-row occupancy group, the 85-row mortgageholders table and its layers), and every state-filed table under any name (AZ FL AK NY TX, and FL GA KS NY for occupancy group) | ⬜ | gates 2, 5 |

### RC-2 · Golden cases (9 tasks), single-file families first

| # | Task | Status | Notes |
|---|---|---|---|
| C20-06 | **Fire Department Service Charge**: an increased limit that moves a dollar; ISO live | ⬜ | gate 1 |
| C20-07 | **Tobacco Sales Warehouses**: two rows of the 4-row rate table on a tobacco occupancy; ISO live | ⬜ | |
| C20-08 | **Mortgageholders E&O**: mortgage counts at and across **each layer boundary** (500, 1,000, 5,000, 15,000), so a wrong layer gives a different dollar; ISO live | ⬜ | |
| C20-09 | **Fungus**: policy limit and separate limits, the increased-period factor, with a BI fungus record feeding the policy premium; excess-of-sublimit and incremental both deciding a dollar; ISO live | ⬜ | |
| C20-10 | **Furs, jewelry, patterns, stamps**: each raised above its base special limit (the precious-metals table has 3 rows); ISO live | ⬜ | |
| C20-11 | **Radioactive Contamination**: all five coverages, not blanketed and blanketed (the average-rate reading discriminated); ISO live | ⬜ | |
| C20-12 | **Pier and Wharf and Additional Covered Property**: both on chunk 17's construction table, two construction options each; Pier and Wharf on structure, Special Class, BI, SCBI; ISO live | ⬜ | |
| C20-13 | **Food Contamination**: food only and additional advertising, on BI and SCBI; ISO live | ⬜ | |
| C20-14 | **Equipment Breakdown**: property damage from the 195-row table by occupancy group, BI loss cost with and without waiting period, ammonia; hazardous substance as a manual premium; ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C20-15 | **Zero cases**: each limit blank or not increased; mortgage count 0; Radioactive in blanket without the form; Tobacco off its occupancy; EB BI without building EB; each switch off; predict both readings, ISO live | ⬜ | gate 4 |
| C20-16 | **Messages**: all 95 distinct, each triggered and silent, including the NC and VA ACP versions, the Mortgageholders / TRIA pair, and the siblings' messages; ISO live | ⬜ | gate 9 |
| C20-17 | **Shared names**: `Rate`, `Factor`, `LimitToUse`, `LossCostMultiplier`, `IncludedInBlkt`, the Watercraft construction fields shared with chunk 17, `CoverageOnPolicyIndicator`, diffed rather than assumed; who writes each; whether a submitted value survives | ⬜ | gate 6 |
| C20-18 | **Exclusion records**: the cyber-incident factors in Fire Department, Mortgageholders, ACP and Equipment Breakdown (four different factor names), each at a limit where the factor moves a dollar | ⬜ | gate 7 |

### RC-4 · States and editions (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C20-19 | **The formula rewrites**: AL FL KS RI Radioactive; AL KS RI Pier and Wharf and ACP; AZ FL VA Fire Department; AK NY TX Mortgageholders; VA fungus total; NY EB BI; FL's switches; each predicted from the state's own rule and tables; ISO live | ⬜ | |
| C20-20 | **State-only and state-form cases**: NC's six ACP files (CP 14 11), VA's CP 14 12 on countrywide files, AK and NY's own fungus files and tables; ISO live | ⬜ | |
| C20-21 | **Editions**: MO (CW 2023 V02) golden probe for Pier and Wharf BI, whose formula differs; one probe each on a V03 and a V04 state | ⬜ | gate 8 |
| C20-22 | **All 46 states**: every family on every state's own package, predicted per state; ISO live | ⬜ | gate 3 |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C20-23 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; terrorism (and Mortgageholders' TRIA rule); stat codes and sublines; the blanket roll-up unmoved except by Radioactive; ISO live | ⬜ | |
| C20-24 | **Regression**: add the chunk 20 scripts and pin the golden figures; full run CLEAN for chunks 0–20 (`--jobs 4`); `157_ --all` | ⬜ | |
| C20-25 | **Census close**: count the ten families as built in `166_` (469 → 497 of 546, 91%) | ⬜ | |
| C20-26 | **File `CF-CHUNK20-GATE.md`** | ⬜ | 28 countrywide premium files + NC's 2 |
