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
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`.

**Regression, scaled back (user, 2026-10-01).** After an RC: no regression run unless `cf_engine` / `gl_engine`
changed since the last clean run; the RC's own script is the check. After an engine change: `206_ --check` + the
scripts that exercise the changed node. At the gate: `206_ --check` and `157_ --all`; the full `104_ --gate` only if
the engine changed during the chunk.

**Order.** After chunk 22. Nothing here depends on chunks 18–22 except AK's attorneys' fees, which
reads the Mortgageholders limit (chunk 20). The families build on chunks 9, 10, 12 and 16.

**Status: OPEN, 18 of 22 (RC-4 done 2026-10-01, `222_chunk23_rc4.py --live`: four fuller state policies, the state-only list closed, three old-package probes, all agree with ISO; OI-120 opened; no engine change). RC-3 done 2026-10-01, `221_chunk23_rc3.py --live`: 43 zero / message / shared-name / exclusion cases ALL AGREE with ISO, every (level, message) equal; no engine change, no regression run). RC-2 done 2026-10-01, `220_chunk23_rc2.py --live`: 12 golden cases ALL AGREE with ISO, 1,727 premiums field for field, every message equal; no engine change, no regression run). RC-1 done 2026-10-01, `219_chunk23_rc1.py`, all checks pass, 37 s, no ISO calls; no engine change).** Next: RC-5, C23-19 (downstream).

**RC-1 findings (2026-10-01), in plain English first:**

1. **MA's credit has never priced because nothing switched it on.** It needs a heating-oil remediation record on a
   building at the location; ISO's sample policies send the credit record alone. The credit amount comes from MA's own
   Pollutant Clean Up location record when its `RemediationForReleaseOfHeatingOilAdditionalBuildings` is "Yes":
   -min(min(deduction, that record's premiums), max discount), and the deduction applies the loss-cost multiplier twice.
2. **MA tenant relocation's cap is per unit**: min(max premium, factor x the building's Group I rate x LOI) x units, so
   adding units never reaches the cap (C23-08's "units either side" becomes "a rate either side").
3. **AK's attorneys' fees exist only on Legal Liability**: off it, the building and contents fee records are removed;
   the policy fee is removed without a Mortgageholders E&O record. Each fee is the coverage's total premium x (fee
   limit / its limit-to-use - 1) x factor, with the ratio unrounded.
4. **CA**: Limited EQ is limit / 100 x the final EQ rate (blanket average when blanketed) x the cyber factors (from the
   policy; BI's own ensuing-causes factor). Its later packages fix a typo in a redundant test: no dollar moves.
5. **VA's 41 records follow chunk 12's shapes on VA's own forms**; VA files no tables (9 countrywide one-row ones).
   The tenants' form reads **no cyber factors** (the broad form does), and the broad form's Special Coverage A uses the
   Group I cyber pair.

**Carried from chunk 21 (2026-09-30): the census `904_` now diffs EVERY rule of the family files across the four countrywide editions** (`scripts/cf/_edition_rules.py`, chunk 20's gate item): 55 family files: MO V02 22 (Ordinance or Law SetPremium among them), V03 2, V04 0 rule differences from 2026 V01. The editions task must judge each one; the census's earlier "identical in all four editions" was a SetPremium-only check. Chunk 21 also found its own edition difference in a PARENT file (MO's sewer caps read `Limit`, not `LimitToUse`): diff the parent files' rules that name this chunk's records too.

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
| **AK attorneys' fees** (IL 01 21) | 3 | building and contents: factor × **that coverage's total premium**; policy: factor × the **Mortgageholders E&O limit** (chunk 20) | 3: legal-liability factor, mortgageholders factor, limit per mortgage (**17**) | 3: fee limit greater than the CP 00 40 / CP 00 70 limit | building and contents unpriced before 2023 (**corrected 2026-10-01, C23-18: AK 2020 prices them inside `ErcRate`**); policy formula differs | none |
| **CA Additional / Limited Earthquake** (CP 01 41; CP 10 43) | 4 | Additional EQ: **manual premium**. Limited EQ (building, contents, BI): the **final EQ rate or blanket EQ average** (chunks 9, 10) × limit, with EQ cause-of-loss and legal-liability factors | none of its own | **14**: residential classes only; not with CP 10 29 / 10 45 / 13 10 / 13 20; sprinkler-leakage-only; deductible up to 15%; sub-limit ≤ risk limit | **later CA packages (2026-10-01, 2026-11-01) change a Limited EQ formula**; the one in force at 2026-09-17 is 2025-12-01 | none |
| **VA Ordinance or Law state forms** (CP 04 06, CP 04 27) | 41 (+2 containers) | Cov A on the adjusted rates, B / C / B&C on LOI factors and cause-of-loss adjustments, post-loss factor, pollutant clean-up; tenants' improvements the same per coverage group | 9, all **countrywide** (VA files none) | **22**: VA's 12 own rules, 10 of them twins of countrywide rules for CP 04 05 / 04 26: same-building exclusion, 80% coinsurance, replacement cost with Cov C, blanket improvements | no premium rule in the 2021 package (**corrected 2026-10-01, C23-18: it prices inside `ErcRate`**); same since 2022 | none |

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

### RC-1 · Evidence and plumbing (6 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C23-01 | **Opening census**: every in-force state-only premium file enumerated and owned; per family formulas, tables, messages by record / form / wording, the state's package history, stored evidence, attach points (state schema), engine readiness | ✅ | **Done 2026-09-28** (`904_chunk23_census.py`, 1 min). Findings above: 80 state-only premium files, none unassigned; chunk 23 owns 10 and closes VA's 41; none ever priced by ISO; 41 messages; MT's glass files price nothing (chunk 19 corrected) |
| C23-02 | **MA's stored credit record**: why the heating-oil credit sits unpriced on 9 fixtures; which input switches the credit and the remediation on. No ISO calls | ✅ | **Done 2026-10-01** (`219_`): **10 stored MA responses** carry the credit record, all **$0 with `CoverageOnPolicyIndicator` 0 at ISO and ours**: no building at the location has a heating-oil remediation record, which is the credit's only switch. ISO's own MA sample payloads send the credit record empty |
| C23-03 | **Attach map and switches** from each state's own schema: MA location and structure records, AK's three levels, CA's three coverages plus Additional EQ, VA's two containers and 41 coverages; every on-switch (AK 3, CA 3, VA 41, MA 1); blank-input defaults | ✅ | **Done 2026-10-01** (`219_`): all 51 premium records placed by their state's schema (MA location / structure; AK policy / structure / contents; CA structure, contents, BI; VA two containers under the structure). **AK's three fees attach only on Legal Liability** (building `CovType` "Legal Liability"; the occupancy's Legal Liability form record) **and the policy fee only with a Mortgageholders E&O record**; otherwise the attach rules REMOVE them. VA switches on `CovType` (A / B / C / B&C) and the cause; the pollutant record on its premium; MA tenant relocation, the remediation and CA have no switch |
| C23-04 | **Borrowed values**: MA's pollutant clean-up total, AK's coverage totals and Mortgageholders limit, CA's final EQ rate / blanket EQ average, VA's adjusted rates, LOI factors and post-loss factor, each resolved on a real tree; hand = engine on every record | ✅ | **Done 2026-10-01** (`219_`, 13 trees): **hand = evaluator = engine on every record** in MA (remediation $241 / $67, credit -$17, relocation $10 / $104 for 4 / 40 units), AK ($4 / $1 / $1, $0 at ratio 1), CA (Limited EQ $12 / $4 / $3, Additional EQ $250 incl. 249.5 rounding) and all 41 VA records on four CovTypes (e.g. Cov A $41, B $59, C $89, pollutant $150; post-loss Yes: Cov A $48, B&C $151). The VA container factors predicted from the filed tables, not read off the engine |
| C23-05 | **Tables and literals**: every table's rows and keys (AK's 17-row limit-per-mortgage, MA's one-row tables, VA's reliance on 9 countrywide tables); and whether the heating-oil lookup uses chunk 10's two-range fix | ✅ | **Done 2026-10-01** (`219_`): MA 8 one-row state tables; AK 2 one-row + **`MortgageholdersLimitOfInsPerMortgAmount` 17 rows**; CA reads no rate table; **VA files none: 9 countrywide one-row tables** (Cov A 1.15, EQ 1.85, post-loss 1.02, six coverage indicators). Every literal key has a row; **no family lookup is banded** (chunk 10's two-range fix is not on these paths). The families' numeric input fields are read from each state's schema up front (chunk 22's gap 2) |
| C23-06 | **Edition timing (OI-105)**: each family's in-force package at 2026-09-17 against later packages (CA 2026-10-01 / 11-01, MA 2026-10-01, AK 2026-11-01); which one ISO serves live, and whether CA's Limited EQ change moves a dollar | ✅ | **Done 2026-10-01** (`219_`): in force at 2026-09-17: MA 2026-03-01 V02, AK 2026-06-01 V01, CA 2025-12-01 V01, VA 2026-06-01 V01. Later packages: MA 2026-10-01 and AK 2026-11-01 (V01, V02) change **no** family rule; **CA's three later packages change one test in the Limited EQ building formula: a typo fix ("Legal Liabilty" -> "Legal Liability") in a clause the next clause makes redundant: no dollar** (the same tree prices the same). VA has none later. Which package ISO serves: every RC-2 case is sent at 2026-09-17 and compared field for field |

### RC-2 · Golden cases (5 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C23-07 | **MA heating oil**: remediation with extra tanks and extra buildings, and the location credit against a pollutant clean-up premium; ISO live | ✅ | **Done 2026-10-01** (`220_ --live` H1-H3, all agree with ISO): remediation $241 (3 tanks + 2 buildings) / $67 (1 tank); the location credit **-$17 at its cap** (deduction 30 > max 20) and **-$9 under it** (Pollutant Clean Up 20,000: deduction 10); 132 premiums each, messages equal |
| C23-08 | **MA tenant relocation**: unit counts either side of the maximum premium; ISO live | ✅ | **Done 2026-10-01** (R1, R2, agree): the cap is **per unit**: 6 units under it $16; a submitted building Group I rate of 2.0 pushes the per-unit calc over 10, so 3 units = **$30** |
| C23-09 | **AK attorneys' fees**: building and contents fees on known coverage totals, and the policy-level fee on a Mortgageholders E&O limit; ISO live | ✅ | **Done 2026-10-01** (K1, K2, agree): on Legal Liability, building fee $12 (10 x its limit), contents $8 (4 x), policy fee $11 (500,000 on Mortgageholders 25,000 x 1,000); **74,999 -> $1: ISO truncates** the per-mortgage ratio (2, not 3). Payloads send the Mortgageholders limit as text (200_'s `payload`) |
| C23-10 | **CA earthquake**: Limited EQ on building, contents and BI, not blanketed and blanketed; Additional EQ's manual premium through the modifiers; ISO live | ✅ | **Done 2026-10-01** (C1, C2, agree): Limited EQ $80 / $24 / $21 on 1,000,000 / 400,000 / 300,000; **Additional EQ 1,234.5 -> $1,235 (half-up at ISO too)**; **a blanketed Limited EQ building is unreachable**: blanket EQ values are set only with an EQ endorsement record, which Limited EQ excludes, so it prices $0 and ISO raises "Blanket ID number entered contains no EQ blanket coverage", as predicted |
| C23-11 | **VA Ordinance or Law state forms**: one VA golden building with the broad form (Cov A, B, C, B&C, pollutant clean-up) and the tenants' improvements form, on all five coverage groups, alongside the countrywide form; ISO live (closes chunk 12's open "VA priced case") | ✅ | **Done 2026-10-01** (V1-V3, agree; **closes chunk 12's open "VA priced case"**): all 41 VA records on three CovTypes and three causes, beside the countrywide form in V1 (187 premiums): e.g. broad form Cov B $591 / C $886 at Group I, B&C $1,500 with post-loss "Yes", pollutant $150; the tenants' form prices the same figures (no cyber factor at factor 1) |

### RC-3 · Zero cases, messages and names (4 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C23-12 | **Zero cases**: no tanks / no buildings; credit without CP 04 44; zero units; AK fees with no mortgageholders limit; CA Limited EQ on a non-residential class; VA forms with no limits; each switch off; predict both readings, ISO live | ✅ | **Done 2026-10-01** (`221_ --live` Z1-Z10, all agree with ISO): MA no tanks = base only; the credit with no remediation record $0 + the CP 04 44 message; 0 units $0; AK fee limits 0 $0; **AK fee limits under the coverage limits price NEGATIVE fees (-$1 / -$1 / -$0), as written, with all three messages**; CA earthquake off removes the Limited EQ records; Additional EQ 0 $0; VA blank B / C limits $0; pollutant 0 off; **a blank VA CovType switches the broad form's Cov A ON ($41) but the tenants' Cov A OFF** |
| C23-13 | **Messages**: all 41, triggered and silent, VA's 12 rules against their 10 countrywide twins, CA's 15% deductible and sub-limit rules at the boundary; ISO live | ✅ | **Done 2026-10-01** (`221_ --live`, MS, MC1-MC9, MV1-MV8, all agree, every (level, message) equal): **30 of chunk 23's own message rules fired at their level** (MA 2, AK 3, CA 15 incl. RC-2's class messages, VA 10) and each checked silent where it should be (MS, MC2 residential 0074, MV3b replacement cost, MV7b). CA's CP 10 43 + 13 10 / 13 20 pair fired in chunk 22 RC-4. Not fired: VA's two "80% in Blanket" rules. VA's 10 countrywide twins are covered by the multiset on the CP 04 05 / 04 26 cases (MV4, MV8) and chunk 12 |
| C23-14 | **Shared names**: `Factor`, `LimitToUse`, `ManualPremium`, `PostLossFactor`, the `TotalPremium…CauseOfLossToUse` totals, `ErcCalculatedTotalPremium` / `CoverageSumPremium` on the containers, diffed rather than assumed; whether a submitted value survives | ✅ | **Done 2026-10-01** (S1-S6, MV7b, agree): submitted VA Factor 2.0 (Cov A $279), PostLossFactor 1.5 (Cov A $202, B $886), AK fee LimitToUse 3, MA HeatingOilBaseLossCost 100 ($263), TotalPollutantCleanUpCredit 5 (-$5), BasePremium 500 ($674) all **survive** (IsNull guards). **`PersPropertyIncludedInBlanket` does not**: the countrywide CP 04 26 message rule re-computes it from the contents' blanket flag on every building, so VA's CP 04 27 rule fires only when the contents are really blanketed (MV7) and a submitted "Yes" is overwritten (MV7b) |
| C23-15 | **Exclusion records**: the cyber-incident factors in CA's and VA's formulas; confirm MA and AK read none; each at a limit where the factor moves a dollar | ✅ | **Done 2026-10-01** (X1-X5, agree): the cyber exclusion moves VA's broad form (Cov B $5,876 at 2,000,000) and **not its tenants' form** (reads no cyber factor); CA's Limited EQ unchanged (the EQ cyber factor is 1.00); AK's fees and MA's records read none (unchanged) |

### RC-4 · States and the list (3 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C23-16 | **Each family on its state's full policy**: the state's other rewrites present (VA's countrywide Ordinance or Law beside its own; CA's other EQ rewrites; MA's Pollutant Clean Up), so the interaction is priced, not assumed; ISO live | ✅ | **Done 2026-10-01** (`222_ --live`, F-MA / F-AK / F-CA / F-VA, all agree with ISO, every premium and message): MA on two locations (credit -$17 where a building has remediation, $0 where none does, relocation per building); AK with a Legal Liability building + contents and an ordinary second building (its fee record removed); CA with Limited EQ on two buildings + contents + BI and Additional EQ on both; VA with the broad form, the countrywide CP 04 05 and the tenants' form on three buildings (227 premiums) |
| C23-17 | **The state-only list, closed**: re-run the ownership enumeration at the gate; confirm none unassigned, MT's glass files price nothing, WV's two flood files wait for chunk 25, and every owner chunk's task list names its files | ✅ | **Done 2026-10-01** (`222_`, re-running `904_`): **80 in-force state-only premium files, none unassigned** (chunks 12 41, 15 6, 16 9, 19 5, 20 2, 21 5, 23 10, 25 2); MT's glass file is a totals file only (prices nothing); WV's two flood files wait for chunk 25; each owner chunk's task list names its files. And: no in-force package writes a coverage premium outside a `SetPremium` rule (only the policy total), so 520 of 546 stands |
| C23-18 | **Older packages**: one probe on the pre-2023 MA and AK packages and the 2021 VA package where ISO still serves them, confirming "no premium rule" means no premium | ✅ | **Done 2026-10-01** (O-MA / O-AK / O-VA, ISO at 2022-07-01 / 2021-07-01, agree with the old packages' rule text): MA 2022's tenant relocation really has no premium writer ($0 at ISO). **The census's "no premium rule" was wrong for AK 2020 and VA 2021**: those files price inside a rule named `ErcRate`, not `SetPremium` (ISO prices AK's fees $1 / $2 and VA's Special and pollutant records). **OI-120 (new): our engine cannot rate any pre-2022-10 policy** (the 2020 countrywide package has a `Null` inside a condition), so the old figures are ISO's only |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C23-19 | **Downstream**: each state's policy total moves by exactly the families' premiums, containers included; terrorism; stat codes and sublines; ISO live | ⬜ | |
| C23-20 | **Regression**: add the chunk 23 scripts and pin the golden figures; full run CLEAN for chunks 0–23 (`--jobs 4`); `157_ --all` | ⬜ | |
| C23-21 | **Census close**: no countrywide files (still 520 of 546); record the state-only list as closed in `166_`'s output except chunk 25's two | ⬜ | |
| C23-22 | **File `CF-CHUNK23-GATE.md`** | ⬜ | 10 state-only premium files + VA's 41 |
