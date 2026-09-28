# Property chunk 23: task list and status

**State-only coverages: families that exist in one state's filing and nowhere
else.** Tasks set 2026-09-28; chunk 18 is being built in the other terminal, and chunks 19–22 wait.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 23) and the opening census ([`904_chunk23_census.py`](../scripts/cf/904_chunk23_census.py),
run 2026-09-28, 1 min, log `results/cf-raas/logs/chunk23_census.log`). This census works from the
other end from the earlier ones: it **enumerates every state-only premium file in the 46 in-force
packages** and assigns each to its owning chunk before running the usual checks on chunk 23's own.
For a state-only file, "editions" means that state's own package versions across all batches.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Order.** After chunk 22. Nothing here depends on chunks 18–22 except AK's attorneys' fees, which
reads the Mortgageholders limit (chunk 20). The families build on chunks 9, 10, 12 and 16.

**Status: TASKS SET 2026-09-28, 1 of 22** (the census). Next, once chunk 22 is gated: RC-1, C23-02.

---

## In plain English first

- **Massachusetts heating oil**: cleaning up a leak from a heating-oil tank (priced by base, extra
  tanks and extra buildings), and a location-level **credit** against the pollutant clean-up premium.
- **Massachusetts tenant relocation**: pays tenants' moving costs after a loss, priced per unit up to
  a maximum premium.
- **Alaska attorneys' fees**: Alaska's own charge for attorney-fee cover, a factor on the building's
  and contents' premiums, and on the Mortgageholders E&O limit at policy level.
- **California earthquake**: *Additional Earthquake* (a company-entered premium) and the *Limited
  Earthquake* form for residential landlords (building, contents, business income).
- **Virginia's own Ordinance or Law forms**: a state broad form and a tenants' improvements form,
  rated alongside the countrywide one. Chunk 12 counted them, but its gate left "VA / WV priced
  cases" open; this chunk closes that.

## What the census found, before any task ran

**Ownership of every in-force state-only premium file (80):**

| Owner | Files | States |
|---|---|---|
| chunk 12 (Ordinance or Law), counted; priced cases open, **closed here** | 41 | VA |
| chunk 15 (Y2K), gated | 6 | VA |
| chunk 16 (Mine Subsidence), gated | 9 | IL 2, IN 4, KY 1, OK 1, WV 1 |
| chunk 19 (tenants' glass) | 5 | FL |
| chunk 20 (Additional Covered Property) | 2 | NC |
| chunk 21 (FL condo units) | 5 | FL |
| **chunk 23** | **10** | AK 3, CA 4, MA 3 |
| chunk 25 (flood) | 2 | WV (Ordinance or Law flood) |

No file is unassigned. Ten more state-only files write a premium field without a `SetPremium`.
They are totals containers (FL, MT and NC tenants' / ACP, VA's two O&L containers) and Mine
Subsidence (KY, OK). **MT's glass files carry no premium rule**, so chunk 19's "FL and MT" was
wrong and is corrected there.

**Chunk 23's families:**

| Family | Premium records | How it prices | Tables (state rows) | Messages | State package history | Stored evidence |
|---|---|---|---|---|---|---|
| **MA heating oil** (CP 04 44 credit; remediation) | 2 | remediation = base + additional tanks + additional buildings; credit = the location's pollutant clean-up total × a max discount (chunk 16's Pollutant Clean Up) | 5, one row each: base premium, tanks rate, additional buildings rate, max discount, subline | 2: CP 04 44 needed for the credit; more heating-oil buildings than declared | formulas differ in the 4 packages before 2025; same since | the credit record is **on 9 fixtures, never priced** |
| **MA tenant relocation** (IL 01 08) | 1 | units × factor, **capped by a maximum premium** (`EvalPremium`) | 3: factor, max premium, stat code | **0** | no premium rule before 2023 | none |
| **AK attorneys' fees** (IL 01 21) | 3 | building and contents: factor × **that coverage's total premium**; policy: factor × the **Mortgageholders E&O limit** (chunk 20) | 3: legal-liability factor, mortgageholders factor, limit per mortgage (**17**) | 3: fee limit greater than the CP 00 40 / CP 00 70 limit | building and contents unpriced before 2023; policy formula differs | none |
| **CA Additional / Limited Earthquake** (CP 01 41; CP 10 43) | 4 | Additional EQ: **manual premium**. Limited EQ (building, contents, BI): the **final EQ rate or blanket EQ average** (chunks 9, 10) × limit, with EQ cause-of-loss and legal-liability factors | none of its own | **14**: residential classes only; not with CP 10 29 / 10 45 / 13 10 / 13 20; sprinkler-leakage-only; deductible up to 15%; sub-limit ≤ risk limit | **later CA packages (2026-10-01, 2026-11-01) change a Limited EQ formula**; the one in force at 2026-09-17 is 2025-12-01 | none |
| **VA Ordinance or Law state forms** (CP 04 06, CP 04 27) | 41 (+2 containers) | Cov A on the adjusted rates, B / C / B&C on LOI factors and cause-of-loss adjustments, post-loss factor, pollutant clean-up; tenants' improvements the same per coverage group | 9, all **countrywide** (VA files none) | **22**: VA's 12 own rules, 10 of them twins of countrywide rules for CP 04 05 / 04 26: same-building exclusion, 80% coinsurance, replacement cost with Cov C, blanket improvements | no premium rule in the 2021 package; same since 2022 | none |

No date arithmetic, no `Power`, no unregistered element. 41 messages in all.

**What shapes the plan:**

1. **Every family has its own schema and history.** Attach points come from the state's own
   DataDef schema, and "editions" are the state's own package versions: MA's heating-oil formulas
   changed before 2025, tenant relocation and AK's building / contents fees had no premium before
   2023, and VA's forms had none in 2021.
2. **The next California package changes a formula.** At the 2026-09-17 as-of date CA is on its
   2025-12-01 package; packages effective 2026-10-01 and 2026-11-01 differ for Limited Earthquake.
   This is OI-105's question again: which edition ISO serves live, and on what date.
3. **Four families read other chunks' finished values.** MA's credit reads the location's pollutant
   clean-up total (chunk 16). AK's fees read each coverage's total premium and the Mortgageholders
   limit (chunk 20). CA's Limited EQ reads the final EQ rate or blanket EQ average (chunks 9, 10). VA's
   forms read the adjusted rates and LOI factors chunk 12 built.
4. **Two manual or capped shapes.** CA Additional EQ is company-entered (chunk 15's shape); MA
   tenant relocation is capped by a maximum premium. Both need cases either side of the switch
   or cap.
5. **VA closes chunk 12's open item.** 41 files, rated alongside the countrywide Ordinance or Law,
   with VA's own form numbers in 12 message rules (10 twinned with countrywide ones). One VA golden building prices them end to end.
6. **The state-only list closes here**, except WV's two flood files (chunk 25) and the files
   chunks 19–21 own. The ownership table above is the check: 80 files, none unassigned.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C23-01 | **Opening census**: every in-force state-only premium file enumerated and owned; per family formulas, tables, messages by record / form / wording, the state's package history, stored evidence, attach points (state schema), engine readiness | ✅ | **Done 2026-09-28** (`904_chunk23_census.py`, 1 min). Findings above: 80 state-only premium files, none unassigned; chunk 23 owns 10 and closes VA's 41; none ever priced by ISO; 41 messages; MT's glass files price nothing (chunk 19 corrected) |
| C23-02 | **MA's stored credit record**: why the heating-oil credit sits unpriced on 9 fixtures; which input switches the credit and the remediation on. No ISO calls | ⬜ | |
| C23-03 | **Attach map and switches** from each state's own schema: MA location and structure records, AK's three levels, CA's three coverages plus Additional EQ, VA's two containers and 41 coverages; every on-switch (AK 3, CA 3, VA 41, MA 1); blank-input defaults | ⬜ | gate 2 (with C23-05) |
| C23-04 | **Borrowed values**: MA's pollutant clean-up total, AK's coverage totals and Mortgageholders limit, CA's final EQ rate / blanket EQ average, VA's adjusted rates, LOI factors and post-loss factor, each resolved on a real tree; hand = engine on every record | ⬜ | gate 6 |
| C23-05 | **Tables and literals**: every table's rows and keys (AK's 17-row limit-per-mortgage, MA's one-row tables, VA's reliance on 9 countrywide tables); and whether the heating-oil lookup uses chunk 10's two-range fix | ⬜ | gates 2, 5 |
| C23-06 | **Edition timing (OI-105)**: each family's in-force package at 2026-09-17 against later packages (CA 2026-10-01 / 11-01, MA 2026-10-01, AK 2026-11-01); which one ISO serves live, and whether CA's Limited EQ change moves a dollar | ⬜ | gate 8 |

### RC-2 · Golden cases (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C23-07 | **MA heating oil**: remediation with extra tanks and extra buildings, and the location credit against a pollutant clean-up premium; ISO live | ⬜ | gate 1 |
| C23-08 | **MA tenant relocation**: unit counts either side of the maximum premium; ISO live | ⬜ | |
| C23-09 | **AK attorneys' fees**: building and contents fees on known coverage totals, and the policy-level fee on a Mortgageholders E&O limit; ISO live | ⬜ | |
| C23-10 | **CA earthquake**: Limited EQ on building, contents and BI, not blanketed and blanketed; Additional EQ's manual premium through the modifiers; ISO live | ⬜ | |
| C23-11 | **VA Ordinance or Law state forms**: one VA golden building with the broad form (Cov A, B, C, B&C, pollutant clean-up) and the tenants' improvements form, on all five coverage groups, alongside the countrywide form; ISO live (closes chunk 12's open "VA priced case") | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C23-12 | **Zero cases**: no tanks / no buildings; credit without CP 04 44; zero units; AK fees with no mortgageholders limit; CA Limited EQ on a non-residential class; VA forms with no limits; each switch off; predict both readings, ISO live | ⬜ | gate 4 |
| C23-13 | **Messages**: all 41, triggered and silent, VA's 12 rules against their 10 countrywide twins, CA's 15% deductible and sub-limit rules at the boundary; ISO live | ⬜ | gate 9 |
| C23-14 | **Shared names**: `Factor`, `LimitToUse`, `ManualPremium`, `PostLossFactor`, the `TotalPremium…CauseOfLossToUse` totals, `ErcCalculatedTotalPremium` / `CoverageSumPremium` on the containers, diffed rather than assumed; whether a submitted value survives | ⬜ | gate 6 |
| C23-15 | **Exclusion records**: the cyber-incident factors in CA's and VA's formulas; confirm MA and AK read none; each at a limit where the factor moves a dollar | ⬜ | gate 7 |

### RC-4 · States and the list (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C23-16 | **Each family on its state's full policy**: the state's other rewrites present (VA's countrywide Ordinance or Law beside its own; CA's other EQ rewrites; MA's Pollutant Clean Up), so the interaction is priced, not assumed; ISO live | ⬜ | gate 3 |
| C23-17 | **The state-only list, closed**: re-run the ownership enumeration at the gate; confirm none unassigned, MT's glass files price nothing, WV's two flood files wait for chunk 25, and every owner chunk's task list names its files | ⬜ | |
| C23-18 | **Older packages**: one probe on the pre-2023 MA and AK packages and the 2021 VA package where ISO still serves them, confirming "no premium rule" means no premium | ⬜ | |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C23-19 | **Downstream**: each state's policy total moves by exactly the families' premiums, containers included; terrorism; stat codes and sublines; ISO live | ⬜ | |
| C23-20 | **Regression**: add the chunk 23 scripts and pin the golden figures; full run CLEAN for chunks 0–23 (`--jobs 4`); `157_ --all` | ⬜ | |
| C23-21 | **Census close**: no countrywide files (still 520 of 546); record the state-only list as closed in `166_`'s output except chunk 25's two | ⬜ | |
| C23-22 | **File `CF-CHUNK23-GATE.md`** | ⬜ | 10 state-only premium files + VA's 41 |
