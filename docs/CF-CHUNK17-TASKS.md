# Property chunk 17: task list and status

**Business Income add-ons: six families that change how Business Income is covered.**
Opened 2026-09-25.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 17, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`179_chunk17_census.py`](../scripts/cf/179_chunk17_census.py), run 2026-09-25),
which carries chunk 15's two census checks: messages searched in **every** rule file, and each
premium rule compared in **every countrywide edition a state stands on**.

**Standing rules carried in.** Analysis and gates only: no engine code
without the user's go. "All states" means the **46**; Puerto Rico is
excluded. Live ISO comparisons at **2026-09-17** (OI-105). Live payloads set
`WindstormOrHailDeductible` (OI-103) and use a special-class description the
state files (C15-16). Every figure is predicted by hand from the family's own
filed table and rule **before** it runs (chunk 16's `174_` evaluator and
`175_` method), and each probe is chosen so the competing readings give
different dollars.

**Status: OPEN 2026-09-25, 1 of 23 tasks** (the census). Next: RC-1, C17-02.

---

## In plain English first

These six are options on a Business Income policy. They either narrow the cover
(pay ordinary payroll for fewer days; deduct the power and heating bills the
business saves while shut) or add a slice of cover (a landlord's lost rent, a
mine's shutdown, a boat accident, a truck breakdown away from the premises).
**None of their 32 premium records has ever been priced by ISO** in our stored
responses. Unlike chunk 16, we have no ISO evidence to start from, so every
record needs its own golden case.

They price in four ways:
- **A slice of Business Income's own rate** (payroll, power-and-heat): chunk
  16's shape. The filed factors are 1.12 / 1.06 / 1.00 for 0 / 90 / 180 payroll
  days. If the premium uses (factor − 1), as chunk 16's containers did, 180
  days prices **$0**. RC-1 checks this before any prediction.
- **The family's own rate table** (Mining, Watercraft).
- **Landlord Rental Value runs its own rate chain.** It reads the building's
  Business Income adjustments and base rates, not Business Income's final
  rate, and five states rewrite it.
- **Off-Premises Interruption is its own small rating plan:** a loss cost for
  collision or other-than-collision, then a waiting period, extended cover and
  an insurance-to-exposure factor. Five states rewrite it and Florida switches
  it.

## What the census found, before any task ran

| Family | Premium records | ISO has priced | Tables read directly (CW rows) | States that rewrite it | Messages naming it, any file | Editions |
|---|---|---|---|---|---|---|
| **Ordinary Payroll Limitation or Exclusion** (CP 15 10) | 6 (BI and SCBI × BGI, BGII, EQ) | 0 | `PayrollExclusionAndLimitationFactor` (3: 0 days 1.12, 90 days 1.06, 180 days 1.00) | none | 4: CP 15 10 vs the Extra Expense form; minimum 50% coinsurance (BI, SCBI) | same in all four |
| **Power, Heat and Refrigeration Deduction** (CP 15 11) | 6 (BI and SCBI × BGI, BGII, EQ) | 0 | `PowerHeatAndRefrigerationFactor` (1: 1.06) | none | 4: as CP 15 10 | same |
| **Mining Properties BI** | 4 (BI and SCBI × BGI, BGII) | 0 (on 3 fixtures, never a premium) | `MiningPropertiesBusnIncomeRate` (6: option None / Limited / Broad × Group I / II; "None" = 0) | none | 0 | same |
| **Landlord as Additional Insured, Rental Value** | 10 (BI and SCBI × BGI, BGII, Broad, EQ, Special) | 0 | `BusnIncomeFactor` (131; FL files its own), `BroadFormBaseRate` (30), `SpecialFormIncldgTheftTimeElementBaseRate` (24; FL) | **5**: CT (`ErcRate`); FL, KS, NY, VT (`SetPremium`); KS, NY (`SetSpecialBaseRate`) | 0 | same |
| **Watercraft Exclusion Buyback** | 2 (BI, SCBI; Special cause) | 0 (on **82** fixtures, always $0) | `WatercraftExclBuybackFactor` (6: options 1–4 0.016, 5–6 0.024) | none | 0 | same |
| **Off-Premises Interruption of Business** (CP 15 06, vehicles and mobile equipment) | 4 (BI and SCBI × Collision, Other Than Collision) | 0 | **13**: loss cost (6), waiting period (3), extended BI (13; AK), insurance-to-exposure (4; AK) and its stat code (4; AK), covered-cause endorsements (3; AR DC NY RI), 7 coverage / stat code tables (1 each) | **6**: AK AR DC NY RI (`SetPremium`; AR DC NY RI `SetWindHailExclFactor`; AK its own stat codes); FL (switch) | 3: CP 15 06 vs cause of loss (BI, SCBI); FL vs a residential class code | same |

**What shapes the plan:**

1. **No stored ISO evidence at all.** Chunk 16 started from 37 matching stored
   premiums; here all 32 records are unpriced. RC-2 therefore needs a golden
   case for **every** record, one policy per family, and RC-1 must explain why
   the 82 fixtures carrying Watercraft Exclusion Buyback (and the 3 carrying
   Mining) all show $0: the switch, the option or the cause of loss.
2. **Two families are chunk 16's shape.** Ordinary Payroll and Power, Heat and
   Refrigeration read Business Income's `Final…Rate` × `Factor` × `LimitToUse`
   through the modifiers, like no waiting period. The factor is built in a
   detail or container record (`SetBaseFactor` / `SetFactor`). If it is
   base − 1, as in chunk 16, 180 payroll days (1.00) is a natural zero case.
   C17-04 reads the rule before this is assumed.
3. **Two families price from their own rate.** Mining's rate is by coverage
   option and cause, × the loss cost multiplier. Watercraft is Special-cause
   only: its factor by construction option × LCM × limit.
4. **Landlord Rental Value is the hardest of the rate-driven five.** It reads
   the parent's cause-of-loss adjustments, a type-of-risk factor
   (`BusnIncomeFactor`, 131 rows; FL's own), the Broad base rate and
   **`PolicyType`**, and the Special base rate with a theft exclusion. The census
   shows its Broad formula reads **no loss cost multiplier**: check that before
   predicting. Five states rewrite it, which is why the plan starts its golden
   cases here.
5. **Off-Premises Interruption is a separate rating plan**, with its own loss
   costs and up to seven factors, each rounded at 3 decimals. The
   other-than-collision form adds earthquake, flood and wind-hail endorsement
   factors that the policy's other coverages switch on. AR DC NY RI file their
   own endorsement factors; AK its own extended-BI and insurance-to-exposure
   tables and stat codes.
6. **Editions and engine are clear.** Every premium file exists and is
   identical in all four countrywide editions (so Missouri needs one
   confirming probe, not a special case), and every `rul:` element is already
   registered.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C17-01 | **Opening census**: population, formulas, tables, messages in every file, every edition, state layer, stored evidence, attach points, engine readiness | ✅ | **Done 2026-09-25** (`179_chunk17_census.py`). Findings above: 32 premium records, 0 priced by ISO; 20 tables; 11 message rules; 11 state rewrites (10 states; FL in both families); identical in all four editions; no unregistered element |
| C17-02 | **The $0 fixtures**: why the 82 Watercraft Exclusion Buyback fixtures and 3 Mining fixtures price $0 at ISO and in ours (switch, option, cause of loss); which input turns each on. No ISO calls | ⬜ | |
| C17-03 | **Attach map and switches**: every record's parent (containers and detail tables under Business Income / Special Class BI; Off-Premises' detail table), the containers' own rules (`SetBaseFactor`, `SetFactor`, `SetLimitToUse`), and every rule that forces $0 | ⬜ | gate 2 (with C17-05) |
| C17-04 | **Borrowed values**: resolve every path to another record (`Final…Rate`, `LimitToUse`, `EQLimitToUse`, cause-of-loss adjustments, base rates, `PolicyType`, LCM, the modifiers, the cyber-exclusion "…ToUse" factors, Off-Premises' EQ / flood / wind-hail factors) on a real tree, in its loop context; confirm each is set before it is read; hand = engine on every record | ⬜ | gate 6 |
| C17-05 | **Tables and literals**: every table's rows, every hardcoded key, and every state-filed table under any name (FL `BusnIncomeFactor` and Special base rate; AK extended BI, insurance-to-exposure; AR DC NY RI covered-cause factors; any state name the census missed) | ⬜ | gates 2, 5 |

### RC-2 · Golden cases (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C17-06 | **Landlord Rental Value**: all 10 records (BI and SCBI × BGI, BGII, Broad, EQ, Special) on chunk 7's Oregon policy, each predicted from its own chain (type-of-risk factor, base rates, `PolicyType`, theft exclusion); the Broad form's missing LCM settled by a discriminating limit; ISO live | ⬜ | gate 1 |
| C17-07 | **Ordinary Payroll Limitation**: all 6 records at 0 and 90 days (factor 1.12, 1.06), each predicted; ISO live | ⬜ | |
| C17-08 | **Power, Heat and Refrigeration Deduction**: all 6 records (factor 1.06); ISO live | ⬜ | |
| C17-09 | **Mining Properties BI**: all 4 records, Limited and Broad options (rate × LCM × limit); ISO live | ⬜ | |
| C17-10 | **Watercraft Exclusion Buyback**: both records, an option from each factor band (0.016, 0.024), Special cause; ISO live | ⬜ | |
| C17-11 | **Off-Premises Interruption**: Collision and Other Than Collision on BI and SCBI, with a waiting period, extended BI and insurance-to-exposure chosen so each 3-decimal rounding decides a dollar; the OTC form with and without the earthquake, flood and wind-hail factors; ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C17-12 | **Zero cases**: 180 payroll days (factor 1.00); Mining option "None" (rate 0); blank days, option, construction option, time period, loss cost keys, limit; the parent Business Income "No Coverage" or $0; an EQ record without earthquake; each switch off; predict both readings, ISO live | ⬜ | gate 4 |
| C17-13 | **Messages**: the 11 found (CP 15 10 and CP 15 11 vs the Extra Expense form and the 50% coinsurance minimum, BI and SCBI; CP 15 06 vs cause of loss; FL's residential class), each triggered and silent; and a search by form number for any message on Mining, Landlord or Watercraft the census's record-name search could miss; ISO live | ⬜ | gate 9 |
| C17-14 | **Shared names**: `Factor`, `BaseFactor`, `LimitToUse`, `Limit`, `Rate`, `PolicyType`, the `…ToUse` cyber factors and `CoverageOnPolicyIndicator` on each record and its parent, diffed rather than assumed; who writes each, and whether a submitted value survives (chunk 16: ISO honoured a submitted `Factor`) | ⬜ | gate 6 |
| C17-15 | **Exclusion records**: the cyber-incident exclusion factors in every formula, and Off-Premises' wind-hail exclusion factor: which record drives each, tested at a limit where 0.995 moves a dollar | ⬜ | gate 7 |

### RC-4 · States and editions (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C17-16 | **Landlord Rental Value's five states**: CT's `ErcRate`, FL KS NY VT's `SetPremium`, KS NY's `SetSpecialBaseRate`, FL's own tables; each predicted from the state's rows; ISO live | ⬜ | |
| C17-17 | **Off-Premises Interruption's six states**: AK (own extended-BI and insurance-to-exposure tables, stat codes), AR DC NY RI (own covered-cause factors, `SetWindHailExclFactor`, `SetPremium`), FL (switch, residential class); ISO live | ⬜ | |
| C17-18 | **Editions**: one probe on each older countrywide parent (MO 2023 V02; CA or NC V03; a V04 state) confirming the identical formulas price the same | ⬜ | gate 8 |
| C17-19 | **All 46 states**: every family on every state's own package, predicted per state; ISO live | ⬜ | gate 3 |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C17-20 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; terrorism (these sit inside Business Income, which terrorism prices); statistical codes (Off-Premises' coverage, Option A and insurance-to-exposure codes); ISO live | ⬜ | |
| C17-21 | **Regression**: add the chunk 17 scripts and pin the golden figures; CLEAN for chunks 0–17; `157_ --all` | ⬜ | |
| C17-22 | **Census close**: count the six families as built in `166_` (290 → 322 of 546, 59%) | ⬜ | |
| C17-23 | **File `CF-CHUNK17-GATE.md`** | ⬜ | 32 countrywide premium files |
