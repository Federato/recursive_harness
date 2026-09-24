# Property chunk 14: task list and status

**Policy assembly: the total, the policy-level modifiers, statistical coding.**
Opened 2026-09-24.

Derived from [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) item 14
("aggregation, minimum premium, statistical coding") and the opening census
([`156_chunk14_census.py`](../scripts/cf/156_chunk14_census.py), run 2026-09-24).

**Standing rules carried in.** Analysis and gates only: no engine code
without the user's go. "All states" means the **46**; Puerto Rico is
excluded. Live ISO comparisons at **2026-09-17** (OI-105).

**Status: OPEN 2026-09-24, 17 of 22 tasks. RC-1 to RC-4 COMPLETE** (statistical codes: 12,547 stored ISO stat values equal, strictly, on 293 of 293 responses; state earthquake codes ISO 4 of 4 live; policy modifiers: 23 cases, engine 23 of 23 as derived, ISO 23 of 23; the policy total: golden $1,193 and 8 variants, ISO 9 of 9): every premium and the policy total equal ISO on 293 stored responses; no minimum premium in ISO's rating: a company input, refer to company (user decision; OI-113).

---

## In plain English first

Chunks 1–13 priced every piece of a policy. Chunk 14 is about the policy
as a whole: adding the pieces up into the total ISO returns, the
adjustments applied to the whole policy (the underwriter's credit or debit,
IRPM; the package discount; the multi-premium credit), and the statistical
codes ISO attaches to every record for reporting.

## What the census found, before any task ran

| Where | Count | What it is |
|---|---|---|
| The total | **881 of 882** rule files carry a `CalculateTotalPremium`; **130** rules write `ErcCalculatedTotalPremium` | the policy's own `CalculateTotalPremium` sums **45** record types (locations, the terrorism roll-ups, policy forms), and `ErcCalculateTotalPremium` writes the policy `Premium` |
| **Minimum premium** | **none in our 46 states** | the countrywide `MinimumPremium` and `PolMinPremium` tables are **header-only**, and **no rule in any package reads them**. The only minimum-premium logic in the whole corpus is Puerto Rico's (a residential condominium earthquake endorsement), which is out of scope. ISO's Property service does not apply a minimum premium: it prices a policy, it doesn't administer one |
| Policy modifiers | IRPM 6 rules, package modification 1, multiple-location average rates 1, Standard Property Policy 4, SPP eligibility 1, additional-location reset 1 | IRPM: a policy form with `TotalModificationPct`, state maximum credit / debit tables, and a "cannot exceed 25%" message |
| Statistical coding | **486** stat-code rules (138 dispatchers), **34** tables | a stat code on nearly every record |
| State layer | the policy total overridden in **41** / **43** states; IRPM in **NE** only; the stat-code dispatcher in **FL** only | the total overrides are likely pass-throughs that add state-only records; C14-04 checks |
| Evidence already stored | **293** ISO fixture responses (chunk 13), every one carrying the policy `ErcCalculatedTotalPremium`; **10,633** stat-code values | a first comparison needs no new ISO call |

**Two things that shape the plan:**

1. **Minimum premium is out of ISO's scope.** The build order listed it; the
   corpus doesn't rate it. C14-03 confirms it across every edition and
   records it as a company rule, not an engine gap.
2. **The evidence is already on disk.** The 293 stored ISO responses carry the
   policy total and over ten thousand stat codes, so RC-1 can compare the
   engine against ISO before a single new call.

---

## Task groups, in priority order

### RC-1 · Evidence and scope (5 tasks) — ✅ COMPLETE 2026-09-24

| # | Task | Status | Notes |
|---|---|---|---|
| C14-01 | **Opening census**: the total, minimum premium, modifiers, stat codes, state layer, stored evidence | ✅ | **Done 2026-09-24** (`156_chunk14_census.py`). Findings above. First cut miscounted KY/IL "mine subsidence" as minimum premium (the pattern matched "Min" in "Mine"); fixed |
| C14-02 | **Replay the 293 stored ISO responses** for the policy total: the policy `Premium` / `ErcCalculatedTotalPremium` and every record's `Premium`, field for field. No ISO calls | ✅ | **Done 2026-09-24** (`157_chunk14_c14-02_total_replay.py`, offline, in the regression). The 293 stored ISO fixture responses re-rated: **all 14,236 premium values equal to ISO**, every record's `Premium` and `ErcCalculatedTotalPremium`, and **the policy total equal on 293 of 293**. The first run showed one miss (KY mine subsidence, ISO $16, ours blank) that was **my replay helper, not the engine**: its cache of rule-addressed singleton records was keyed by the countrywide edition only, so Oregon's set was reused for Kentucky, whose own rules address the mine-subsidence record bare. Keyed by parent and state, it matches. **Regression cost (user-approved 2026-09-24):** the regression runs a fixed 46-fixture covering sample (every state and every premium-bearing record type; 3,193 values, ~45 s); `--all` runs all 293 (~4 min) at every chunk close-out and edition change. A one-pass fixture index halved the full run on its own (7.7 → 3.8 min) |
| C14-03 | **Minimum premium**: confirm no rule reads a minimum-premium table in any edition or state (PR aside), and record it as a company rule outside ISO's rating | ✅ | Scope decision for the user. **Done 2026-09-24** (`158_chunk14_rc1_scope_machinery.py`). **No rule in the 50 packages our 46 states resolve to reads a minimum-premium table**, and the countrywide `MinimumPremium` / `PolMinPremium` tables are header-only. The only minimum premium in the corpus is Puerto Rico's (condominium earthquake), out of scope. **ISO's Property rating applies no minimum premium**; a minimum is a company rule. **User decision 2026-09-24: minimum premium is a company input, and the outcome is "refer to company"** (GL's `ReferToCompany`: a legitimate rating outcome the caller resolves by supplying a value, not an error). The Property engine has no company-input or referral layer yet; logged as **OI-113**, not built |
| C14-04 | **State overrides of the total** (41 / 43 states): pass-through or rewrite, and which state-only records each adds | ✅ | **Done 2026-09-24** (`158_…`). **All 41 state overrides of `CalculateTotalPremium` call the parent edition's and add state-only records** (state forms, KY/IL mine subsidence, Alaska's terrorism forms) with **no arithmetic of their own**; **all 43 overrides of `ErcCalculateTotalPremium` are pure pass-throughs**. DC and MD don't override; NJ, OH, UT file no state policy file |
| C14-05 | **The total's machinery**: operand types, the `PremiumIndicator` gate, negative premiums (Debris Removal under $25,000, chunk 12), inert records (`TotPremiumCoverage`) | ✅ | **Done 2026-09-24** (`158_…`). **4,008 `CalculateTotalPremium` rules, 8,392 operators, every one a shape the engine handles.** `SetPremiumIndicator` counts any non-zero premium, so **a negative premium enters the total**: chunk 12's Debris Removal under $25,000 (−$21 / −$3) gives ISO's total **$269** (= 261 + 32 − 21 − 3), and ours $269; the ordinary case $348 and the limit-at-minimum case $293 also equal ISO. `TotPremiumCoverage` is inert (premium hard-coded 0; chunk 13) |

### RC-2 · The policy total (4 tasks) — ✅ COMPLETE 2026-09-24

| # | Task | Status | Notes |
|---|---|---|---|
| C14-06 | **Golden case**: chunk 13's five-coverage policy plus terrorism and an endorsement; hand-derive the policy total; ISO live | ✅ | **Done 2026-09-24** (`159_chunk14_rc2_total.py`). Chunk 7's five-coverage policy ($1,104: building 263/32, contents 223/24, BI 112/13, SC 66/209, SCBI 39/123) + terrorism in effect ($34, chunk 13) + Debris Removal 60,000 ($49 + $6, chunk 12): **policy total $1,193, derived by hand. Engine 6 of 6; ISO live: agrees on all 126 premiums** |
| C14-07 | **What the total counts**: zero, negative and form-only records; ISO live | ✅ | **Done 2026-09-24** (`159_chunk14_rc2_total.py`). On chunk 2's $293 building: Debris Removal at exposure 0 → **$293**; negative (−$21 / −$3) → **$269**; terrorism with the certified-acts answer blank (disclosure $0) → **$293**; terrorism override $500 → **$793**; building "No Coverage" + Debris Removal (still charged $42 + $5) → **$47**. **ISO agrees on all five**, field for field |
| C14-08 | **More than one location and building**, and the additional-location reset (`ErcResetPrsnlPropPremiumForAdditionalLocations`) | ✅ | **Done 2026-09-24** (`159_chunk14_rc2_total.py`). Two locations, each chunk 2's building with terrorism: **$602**; two buildings on one location: also **$602**, because each **structure's** own total keys its deductible band (TotAmtInsurance = the structure's limit + contents at that structure, chunk 1), not the location's. My first prediction ($606) assumed the location total; the engine and ISO were right. **ISO agrees on both.** `ErcResetPrsnlPropPremiumForAdditionalLocations` belongs to the Additional Locations Special Coinsurance endorsement (12 rule files, in no ISO fixture): **already tracked as not built, B9 in `Coverage_Inventory_And_Tracking.md`**; not tested here |
| C14-09 | **Rounding**: whole-dollar premiums summed against the 2-decimal roll-ups | ✅ | **Done 2026-09-24** (`159_chunk14_rc2_total.py`). **The total adds whole-dollar premiums; it never rounds a raw sum.** Discriminating case: two buildings whose terrorism works out to $0.357 each (Remainder of State, IL 09 53, fire exception 0.4): $0 each, **total $586**; rounding the raw 0.715 would give $587. **ISO: $586** |

### RC-3 · Policy modifiers (5 tasks) — gates 4 and 5 — ✅ COMPLETE 2026-09-24

| # | Task | Status | Notes |
|---|---|---|---|
| C14-10 | **IRPM**: the form, `TotalModificationPct`, the state maximum credit / debit, the 25% message, which premiums it multiplies; NE's override | ✅ | **Done 2026-09-24** (`160_chunk14_rc3_modifiers.py`). Six category percentages → `IRPMConversion` → summed → `IRPMFactor` = round3(1 + t/100), capped at the state limit; **a supplied `IRPMFactor` wins** (IsNull guard). Oregon: −10% → 0.9 → $264; +30 → 1.25 + message → $366; −30 → 0.75 → $220; IRPM No with `CPPIRPMFactor` 0.85 → $249; supplied 1.1 → $322. **The cap and the message are separate rules, and states change them separately:** NY ±15 on its **own twelve categories** (the CW six are ignored; first prediction wrong, engine right), its own 15% message, and a second "all credits" message that adds the IRPM *percent* to the multi-premium *factor*, so +25 trips it; MO credit −35 with a **seventh** category (expense reduction) and its own message; GA caps at 25 but warns at 15; VA silent; NE IRPM off (1.0 unless supplied). 12 state cases, ISO agrees on every premium and message. **Missouri, IRPM on with the expense category blank: ISO refuses the policy, ours prices** (logged on OI-103; pinned as O4). |
| C14-11 | **Package modification factor** | ✅ | **Done 2026-09-24** (`160_chunk14_rc3_modifiers.py`). The policy's factor reaches the building only when the building's own is blank: policy 0.8 → $209 + $26 = **$235**; building 1.0 set → **$293**. ISO agrees. |
| C14-12 | **Multi-premium and dispersion credit** (the policy-level user factor) | ✅ | **Done 2026-09-24** (`160_chunk14_rc3_modifiers.py`). `MultiPremiumAndDispersionCreditFactorUser` 0.9, building blank → $235 + $29 = **$264**. ISO agrees. |
| C14-13 | **Standard Property Policy** (CP 00 99): its Group I / II factors, eligibility and messages | ✅ | **Done 2026-09-24** (`160_chunk14_rc3_modifiers.py`). CW 0.98 on Group I and II, applied at the **cause-of-loss step**, so it rounds through the chain (0.239 → 0.234 → … → 0.255): $255 + $31 = **$286**, not 0.98 × 293. Eligibility is 17 "not valid with the Standard Property Policy" **messages** (never refusals); the five-coverage policy as SPP raises the Business Income one and still prices it (ISO $1,087, 119 premiums agree). |
| C14-14 | **Multiple-location average rates** (value reporting form) | ✅ | **Done 2026-09-24** (`160_chunk14_rc3_modifiers.py`). With no value reporting form, `MultiLocAvgRates` defaults to "Not Used" on the policy and nothing prices off it ($293). The value reporting form itself is unbuilt, tracked in `Coverage_Inventory_And_Tracking.md`. |

### RC-4 · Statistical coding (3 tasks) — ✅ COMPLETE 2026-09-24

| # | Task | Status | Notes |
|---|---|---|---|
| C14-15 | **Stat-code census** by record type; the 34 tables, which are state-filed | ✅ | **Done 2026-09-24** (census in `162_`'s docstring and here). Every countrywide edition our 46 states sit on files **46** stat-code tables. **22 tables are state-filed**: the deductible codes (All-other, Wind/Hail, general) in 43 states, Earthquake deductible in 45 (TX its own 37-row version), and single-state tables (FL BCEG / sinkhole / EQ construction, NY coinsurance, NC protection class, AL state exception, CA wildfire, MA oil / tenant relocation, AR/DC peril exclusion, 6 windstorm-mitigation states). **State stat rules in 18 states** (the dispatcher `ErcSetStatisticalCodes` is overridden in 18, not FL only as the opening census read). The stored responses carry 51 stat field names, 12,547 values. |
| C14-16 | **Stat codes against ISO**: the 10,633 stored values, field for field | ✅ | **Done 2026-09-24** (`161_chunk14_c14-16_statcode_replay.py`, offline, sample in the regression). **All 12,547 stat values on 293 of 293 stored ISO responses equal ours**, compared **strictly**: a code is text, so "07" ≠ "7" and "" ≠ "0" (the premium comparer treats those as equal numbers; not good enough for codes). The 10,633 in the census counted `…StatCode` keys only; the full set adds stat amounts, stat premiums and `…ForStat` fields. |
| C14-17 | **State stat-code rules**: FL's dispatcher, state-filed tables | ✅ | **Done 2026-09-24** (`162_chunk14_rc4_state_statcodes.py`, ISO live). The stored responses already exercise most state mechanisms with real values (AL/AR/DC/NY/RI deductible codes, NC, NY, AL/KY wind mitigation, AL, CA wildfire, FL sinkhole, VA, AK/AZ terrorism), and the **blanking** states (AK/NY mold, DC/NY BCEG), where ISO's blank must meet ours. Not in any stored response: a state **earthquake** code. The lookup is state row first, CW second; **FL class 2A → "21"** (CW has no 2A) and TX / OR / FL deductible codes: **ISO 4 of 4 as predicted**. **TX files "97" for off-grid EQ deductibles (7%, 11%…) but no premium factor for them**, so ISO refuses before the code (OI-103 shape): the "97" rows are unreachable through the percentage form. **Out of scope, with their coverages:** stat codes of unbuilt coverages: Off-Premises Interruption (AK), MA heating-oil remediation and tenant relocation, Condominium Unit-Owners Optional Coverages and the Value Reporting Form (AR/DC peril-exclusion codes). |

### RC-5 · Confirmation and close-out (5 tasks) — gates 2, 3, 6–9

| # | Task | Status | Notes |
|---|---|---|---|
| C14-18 | **All 46 states**: the policy total and the modifiers, each state's own rows | ⬜ | **gates 2, 3, 8** |
| C14-19 | **Zero cases**: no coverage, all-zero coverages, IRPM beyond the state maximum, blank modifiers | ⬜ | **gate 4** |
| C14-20 | **Shared names and messages**: `Premium` / `ErcCalculatedTotalPremium` on every record type; the IRPM and SPP messages | ⬜ | **gates 6, 9** |
| C14-21 | **Regression**: add chunk 14 to `104_…regression.py`; clean for chunks 0–14 | ⬜ | |
| C14-22 | **File `CF-CHUNK14-GATE.md`** | ⬜ | |
