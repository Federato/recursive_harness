# Property chunk 21: task list and status

**Sewer backup and condominium options: water backing up through drains, and the
options a commercial condominium unit owner buys.** Tasks set 2026-09-28; chunk 18 is
being built in the other terminal, and chunks 19 and 20 wait.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 21, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`902_chunk21_census.py`](../scripts/cf/902_chunk21_census.py), run 2026-09-28,
3 s, log `results/cf-raas/logs/chunk21_census.log`). It runs the same checks as `901_` (chunk 20):
- messages searched in every rule file;
- `SetPremium` compared in every in-force edition;
- form numbers taken from the package's `Form Pages` table;
- sibling names flagged.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Order.** After chunk 20. Nothing here reads chunks 18–20. It reads chunks 1–7's deductible
factors and final rates, and chunk 15's manual-premium shape (Florida's family).

**Status: IN PROGRESS 2026-09-30, 8 of 21.** RC-1 done (C21-02–C21-05, `207_chunk21_rc1.py`, 107 checks, ~4 min, no ISO calls). C21-06 ISO 5 of 5, C21-07 9 of 9, C21-08 6 of 6 + one pinned OI-103 refusal (`208_chunk21_rc2.py`). Next: C21-09 (Florida condo records live).

---

## In plain English first

- **Discharge from Sewer, Drain or Sump (not flood)**: water backing up into the building
  through the plumbing. It can be bought on the building, contents, special class, and both
  business income versions, each with its own limit.
- **Condominium unit-owner options** (CP 04 18): a unit owner can buy **loss assessment**
  (their share when the association bills owners for a loss) and **miscellaneous real
  property** (fixtures they own that the association does not insure).
- **Florida's commercial units in residential condominiums** (CP 01 54 / CP 17 96): Florida's
  own version for shops inside a residential condo building. It is priced as a
  **company-entered premium**, not from a table.

**None of the 12 premium records has ever been priced by ISO** (7 countrywide + 5 FL-only),
and none appears on a stored example policy. Unlike chunks 18 and 20, there are no $0
records to explain first.

## What the census found, before any task ran

| Family | Premium records | Tables read directly (CW rows) | States that rewrite it | Messages (any file) | Editions |
|---|---|---|---|---|---|
| **Sewer / drain backup** (CP 10 38; Building, Contents, Special Class, BI, SCBI) | 5 | 8, but **one rate table** (2 rows: PD 0.77, BI 0.07) and `DeductibleFactor` (240; 44 states); the other 6 are stat / coverage codes and the subline; **FL files all 8** | FL (its own rate and stat-code rules) | 5: sewer limit not greater than the parent coverage's limit (×5) | same in all four |
| **Condo unit-owner options** (CP 04 18; loss assessment, misc. real property) | 2 | 11: loss assessment rate (15), converted limit (4), **sub-limit rate (9; FL)**, misc. real property rate (1: 0.528), deductible, 3 indivisible sublines, 2 peril-exclusion stat-code tables (AR DC) | **7**: AL KS RI (`SetPremium`); KS NY (the loss-assessment rate rules); FL (sub-limit rules and validation); AL AR DC NY RI (wind / hail excluded indicator) | 13 own + 3 shared with FL: multiples of $5,000 over $10,000 and of $1,000 for the sub-limit; sub-limit ≤ limit; only with the unit-owners form; needs a limit; state forms **CP 04 20 (RI), 04 21 (FL), 04 22 (UT)**; GA valuation | same |
| **FL Commercial Units in Residential Condominiums** (CP 01 54; SPP CP 17 96) | **5 FL-only** | **none**: `ManualPremium` through the modifiers, gated on `CovForm` / `CovType` / `PolicyType` | FL only | 8 (3 shared): not attachable unless the coverage form / policy type fits; one residential condominium record per building | same |

**Sibling names checked, none priced.** GA's and FL's condominium-association forms, UT's and
GA's unit-owner change forms, and GA's wind / hail special-class form all have rule files
with no premium. One sibling is a false match: "Sump" matched Manufacturers Consequential
Loss *Assumption* (chunk 19's). No date arithmetic, no `Power`, no unregistered element.
**30 message rules listed, 27 distinct.** One of those is chunk 20's Fire Department rule, which
names the unit-owners form, so **26 are this chunk's**.

**What shapes the plan:**

1. **Loss assessment is tiered arithmetic, not a lookup.** The limit is rated at 1,000 /
   5,000 / 10,000, plus a per-$5,000 rate above 10,000. The sub-limit adds three bands
   (up to 5,000; 6,000–10,000; over 10,000) at a per-$1,000 rate, by cause of loss. That's 21
   rules in one file. The golden case puts a limit in every tier and a sub-limit in every
   band, so a wrong band gives a different dollar.
2. **Sewer's "8 tables" are one rate and seven codes.** The plan asked which are live: the
   2-row rate and the deductible factor price the premium; the rest set stat and coverage
   codes. RC-1 confirms this on a real tree, and C21-18 tests the codes downstream.
3. **Sewer's limit is capped by its parent.** Five messages refuse a sewer limit above the
   building, contents, special class or BI limit. The zero and message cases test at the
   cap, one dollar over and one under.
4. **Florida's family is a manual premium.** The five FL-only records take a company-entered
   `ManualPremium` through the modifiers (chunk 15's shape), switched on only for the right
   coverage form, coverage type and policy type. The payload must carry all three. The
   records' attach point needs FL's own DataDef schema; the countrywide one does not know them.
5. **The condo options have four form numbers.** CP 04 18 countrywide, CP 04 20 in RI,
   CP 04 21 in FL and CP 04 22 in UT (which must pair with CP 00 18 or CP 17 98). The state
   sweep must use each state's own form.
6. **No cyber-incident factor anywhere in the chunk.** Every earlier chunk had one. C21-13
   confirms the absence rather than assuming it.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C21-01 | **Opening census**: population, formulas, tables, messages by record and by form / wording (forms from `Form Pages`), sibling names, every edition, state layer, stored evidence, attach points, engine readiness | ✅ | **Done 2026-09-28** (`902_chunk21_census.py`, 3 s). Findings above: 7 CW + 5 FL-only premium records, none priced by ISO; 26 messages of this chunk's own; identical in all four editions; siblings carry no premium; no date nodes; no unregistered element |
| C21-02 | **Attach map and switches**: Sewer under its five parents; the options container under Personal Property and its two coverage records; the FL records' parents from **FL's own DataDef schema**; every on-switch (`SetCoverageOnPolicyIndicator`, the `CovForm` / `CovType` / `PolicyType` gates); every blank-input default that zeroes a premium. No ISO calls | ✅ | **Done 2026-09-30** (`207_chunk21_rc1.py`, ~1 min, engine only). All 12 records placed from their own package schema. **Sewer** has no switch rule: its own limit is the switch (`DischargeLimitPD` / `DischargeLimitBI`); at 25,000 on OR: PD 167 / PP 170 / SpecClass 164 / BI 17 / SpecClass BI 17. Attached with **no limit**, PD records price **$1** (blank limit skipped in the Product under propagate) and BI $0 — **an ISO probe for C21-06 (engine 1 vs 0)**. **Condo options**: the container limits are the switch, `CovForm` is not; `LossAssessmentLimit` is an **enum** (`0 / 1,000 / 5,000 / 10,000 / Over 10,000` + `LossAssessmentLimitOver10000`), "10000" leaves the rate blank and the premium 0; a blank `LossAssessmentDeductible` gives DeductibleFactor 0 and premium 0; "All Other" is **not a deductible value** (it is the cause key the 250 rule passes to its own table; corrected by C21-04), so it finds no factor row and prices 0; 250 → 1.1, Not Applicable → 1. MRP reads the container's `LossAssessmentDeductible` too (93 alone, 102 with 250). **FL**: the three CPP records price only when `CovForm` unit owners / `CovType` Condominium Association **and** `PolicyType` Commercial Property Policy (else 0); the two **SPP records are ISO auto-attach forms**: created when CovForm + PolicyType SPP + class 0331–0343 (OccupClass) / `ItemsBelongToResidentialCondo` Yes (SpecClass), **removed** otherwise. AL/KS/RI rewrite MRP `SetPremium` | gate 2 |
| C21-03 | **Borrowed values**: Sewer BI's `FinalRate`, the parent limits the sewer caps read, `DeductibleFactor` / `Deductible250Factor` by coverage, `LossCostMultiplier` and the modifiers, each resolved on a real tree in its loop context; hand = engine on every record | ✅ | **Done 2026-09-30** (`207_chunk21_rc1.py`): **hand = engine on 33 cases** (5 records × as built / deductible 250 / N/A / 5,000 / parent LCM 1.25 / policy mods, + No Waiting Period on both BI records, + PP with a Building sewer record). Each record reads its **own** rule file: Building bands its deductible on the parent `TotAmtInsurance`, Special Class on `LimitToUse`; **Personal Property has no deductible rule — it borrows the Building sewer record's `DeductibleFactor`, else 1**; mods sit 6 up (PD), 10 up (PP), 8 up (BI). **OR files its own `DeductibleFactor`** (463 rows; CW-only hand was wrong by 0.93 vs 0.98). **No Waiting Period zeroes sewer BI**: `FinalRate` = Rate × the endorsement's `Factor`, which is `BaseFactor − 1` = 0 (its table has no rows) — **ISO probe for C21-06 (engine $0 vs $17)** | gate 6 |
| C21-04 | **Loss assessment by hand**: the 21 rules traced step by step, with each tier's and band's arithmetic written down and checked against the engine at every boundary (1,000 / 5,000 / 10,000 / 15,000; sub-limit 5,000 / 6,000 / 10,000 / 11,000) before any ISO call | ✅ | **Done 2026-09-30** (`207_chunk21_rc1.py`): **hand = engine on 33 cases** across every tier (0 / 1,000 / 5,000 / 10,000 / Over 10,000 at 12,000, 15,000, 17,500, 20,000), every sub-limit band (1,000 … 20,000 incl. 5,500 and 11,500), Basic / Broad / Special and the SPP path (Basic), and deductibles 250 / N/A / 500 / 1,000 / 2,500 / blank. Rules in plain words: Over 10,000 rate = (limit/5,000 − 2) × the "Over 10,000" rate + the 10,000 rate; sub-limit thousands N = sub/1,000 − 1, priced 4 at the first band rate, 5 at the second, the rest at the third; the deductible bands on the **loss assessment limit**, not a building value. Edges ISO's own rules allow, **for the C21-07 probes**: a non-multiple below 15,000 (12,000) prices with no message (0.4 of a step); 17,500 prices **$0** with the multiple-of-5,000 message; a sub-limit 11,500 prices as none with the multiple-of-1,000 message, but 5,500 passes (the check only runs above 10,000); a sub-limit over the limit still prices, with a message. Stat amount rounds before truncating (17,500 → 18) |
| C21-05 | **Tables and literals**: every table's rows and key literals (the "Over 10,000" and band strings, the misc. real property `Y` key), and every state-filed table under any name (FL's eight sewer tables and sub-limit rate; AR DC stat codes); which of Sewer's 8 tables price and which only code | ✅ | **Done 2026-09-30** (`207_chunk21_rc1.py`): every lookup in the chunk's files in all 46 in-force packages: **every literal and caller-passed key has a row** (0 problems); the dropdown values of `LossAssessmentLimit` are all keyed ("Over 10,000" is absent from the converted-limit table but the rule never looks it up). Sewer has **6 CW tables; one prices** (`DischargeFromSewerDrainOrSump`, PD 0.77 / BI 0.07), five only set codes; the census's "8" counted the two deductible tables. **FL files empty copies of 7** (the 6 sewer tables + the sub-limit rate) **and its parent rules never call the sewer records**: on the engine FL attaches the sewer form but prices nothing — **ISO probe for C21-06** (engine: no premium; the alternative: CW rates). All seven CW records on one policy **in every state on the engine**: only FL leaves any unpriced; AL/KS/RI price misc. real property without the loss assessment deductible (93 vs 102); CA/NY sewer 158 (own deductible tables); AR/DC file their own peril-exclusion stat codes | gates 2, 5 |

### RC-2 · Golden cases (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C21-06 | **Sewer backup**: all five parents, PD and BI rates, a deductible that moves a dollar; ISO live | ✅ | **Done 2026-09-30** (`208_chunk21_rc2.py --live`, 1 min): **ISO agrees on 5 of 5**, every premium on each policy (124–136) and every message; predicted by 207_'s hand model = SetPremium evaluator = engine. SW1 all five at 25,000: 167 / 167 / 164 / 17 / 17. SW2 building deductible 250, special class 5,000: 186 / 186 (PP borrows) / 130. SW3 PP alone: **170** (factor 1, nothing to borrow; the own-parent reading gave 167). SW4 limits 50k/10k/30k/100k/40k: 332 / 68 / 197 / 69 / 28. **SW5 probe: No Waiting Period attached, ISO prices sewer BI $0 on both parents**, as the rules read (rate × the endorsement's BaseFactor − 1) | gate 1 |
| C21-07 | **Loss assessment**: a limit in each tier (incl. one over 10,000), a sub-limit in each band, Basic / Broad / Special; ISO live | ✅ | **Done 2026-09-30** (`208_chunk21_rc2.py --live`, 1 min): **ISO agrees on 9 of 9**, every premium on each policy (126) and every message; predicted by 207_'s `la_by_hand` = SetPremium evaluator = engine. LA1 1,000 Special ded 1,000: 3. LA2 5,000 Broad ded 500 sub 3,000: 8. LA3 10,000 Basic N/A sub 8,000: 15. LA4 Over 10,000 = 25,000 Special 250 sub 14,000: 26. LA5 20,000 Broad 2,500 sub 10,000 (band edge): 17. **Probes, all as the rules read**: 12,000 prices **6 with no message** (the multiple-of-5,000 check starts at 15,000); 17,500 prices **$0 with the multiple-of-5,000 message**; sub-limit 11,500 is **ignored (8) with the multiple-of-1,000 message**; sub-limit 5,500 prices **16 with no message** (the check runs only above 10,000) | |
| C21-08 | **Miscellaneous real property**: two limits and the three causes of loss, with and without a deductible factor; ISO live | ✅ | **Done 2026-09-30** (`208_chunk21_rc2.py --live`): **ISO agrees on 6 of 6**, every premium (126) and message. Rate 0.528 (no cause key: Basic = Broad = Special); the factor reads the container's `LossAssessmentDeductible`: blank / N/A → 1 (93; loss assessment's blank gives 0), 250 → 1.1 (102), 1,000 at 50,000 → 223, 2,500 at 50,000 → 196. **Found on the first send: the options container CREATES both coverage records whether sent or not, and the loss assessment switch tests only for "0", so misc. real property alone must send `LossAssessmentLimit` "0"; blank switches loss assessment on and ISO refuses at `LossAssessmentRate` (keys CW, blank, cause) while ours prices $0 — OI-103**, pinned as MRZ (a refusal is the expected result) | |
| C21-09 | **FL Commercial Units in Residential Condominiums**: all five records (occupancy, special class, building, and both Standard Property Policy versions) with a manual premium through the modifiers; ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C21-10 | **Zero cases**: sewer limit blank / 0 / at the parent limit; loss assessment "0"; sub-limit without a limit; the options record with neither limit; FL records on the wrong coverage form, coverage type or policy type; manual premium blank; predict both readings, ISO live | ⬜ | gate 4 |
| C21-11 | **Messages**: all 26, each triggered and silent. The multiples-of rules are tested one either side ($15,000 vs $12,000; $3,000 vs $3,500), the sewer caps one dollar over and under, and each state's form (RI UT FL GA); ISO live | ⬜ | gate 9 |
| C21-12 | **Shared names**: `Rate`, `FinalRate`, `DeductibleFactor`, `LimitToUse`, `ManualPremium`, `CovForm`, `CovType`, `PolicyType`, `WindstormOrHailExcludedIndicator`, diffed rather than assumed; who writes each; whether a submitted value survives | ⬜ | gate 6 |
| C21-13 | **Exclusions and stat codes**: confirm no cyber-incident factor reaches any formula; the wind / hail excluded indicator (AL AR DC NY RI) and AR DC's peril-exclusion stat-code tables, tested where the indicator changes a code | ⬜ | gate 7 |

### RC-4 · States and editions (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C21-14 | **The condo rewrites**: AL KS RI `SetPremium`; KS NY loss-assessment rate rules; FL sub-limit rules and validation; RI CP 04 20, FL CP 04 21, UT CP 04 22 with CP 00 18 / 17 98; GA and UT's change forms; each predicted from the state's own rule and tables; ISO live | ⬜ | |
| C21-15 | **Florida's sewer**: FL's own rate and all eight tables on the five parents; ISO live | ⬜ | |
| C21-16 | **Editions**: all premium rules identical in the four editions; one probe each on MO (2023 V02), a V03 and a V04 state. **Carried from chunk 20's gate (2026-09-30): diff EVERY rule of each family file across the four editions, not just `SetPremium`** (chunk 20's every-rule diff in `203_` found 6 differences where the census's SetPremium-only check found 1; chunk 21's census `902_` ran SetPremium-only), and move that diff into the census template for chunks 22-27 | ⬜ | gate 8 |
| C21-17 | **All 46 states**: every family on every state's own package, with each state's own condo form, predicted per state; ISO live | ⬜ | gate 3 |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C21-18 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; terrorism; Sewer's stat and coverage codes and subline; the exposure stat amount; ISO live | ⬜ | |
| C21-19 | **Regression**: add the chunk 21 scripts and pin the golden figures; full run CLEAN for chunks 0–21 (`--jobs 4`); `157_ --all` | ⬜ | |
| C21-20 | **Census close**: count the two families as built in `166_` (497 → 504 of 546, 92%) | ⬜ | |
| C21-21 | **File `CF-CHUNK21-GATE.md`** | ⬜ | 7 countrywide premium files + FL's 5 |
