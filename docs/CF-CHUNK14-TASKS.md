# Property chunk 14: task list and status

**Policy assembly: the total, the policy-level modifiers, statistical coding.**
Opened 2026-09-24.

Derived from [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) item 14
("aggregation, minimum premium, statistical coding") and the opening census
([`156_chunk14_census.py`](../scripts/cf/156_chunk14_census.py), run 2026-09-24).

**Standing rules carried in.** Analysis and gates only: no engine code
without the user's go. "All states" means the **46**; Puerto Rico is
excluded. Live ISO comparisons at **2026-09-17** (OI-105).

**Status: OPEN 2026-09-24, 5 of 22 tasks. RC-1 COMPLETE**: every premium and the policy total equal ISO on 293 stored responses; no minimum premium in ISO's rating: a company input, refer to company (user decision; OI-113).

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

### RC-2 · The policy total (4 tasks) — gate 1

| # | Task | Status | Notes |
|---|---|---|---|
| C14-06 | **Golden case**: chunk 13's five-coverage policy plus terrorism and an endorsement; hand-derive the policy total; ISO live | ⬜ | **gate 1** |
| C14-07 | **What the total counts**: zero, negative and form-only records; ISO live | ⬜ | |
| C14-08 | **More than one location and building**, and the additional-location reset (`ErcResetPrsnlPropPremiumForAdditionalLocations`) | ⬜ | |
| C14-09 | **Rounding**: whole-dollar premiums summed against the 2-decimal roll-ups | ⬜ | |

### RC-3 · Policy modifiers (5 tasks) — gates 4 and 5

| # | Task | Status | Notes |
|---|---|---|---|
| C14-10 | **IRPM**: the form, `TotalModificationPct`, the state maximum credit / debit, the 25% message, which premiums it multiplies; NE's override | ⬜ | The rater work found IRPM hard-coded to 1.0 once (R-4) |
| C14-11 | **Package modification factor** | ⬜ | |
| C14-12 | **Multi-premium and dispersion credit** (the policy-level user factor) | ⬜ | |
| C14-13 | **Standard Property Policy** (CP 00 99): its Group I / II factors, eligibility and messages | ⬜ | |
| C14-14 | **Multiple-location average rates** (value reporting form) | ⬜ | |

### RC-4 · Statistical coding (3 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C14-15 | **Stat-code census** by record type; the 34 tables, which are state-filed | ⬜ | |
| C14-16 | **Stat codes against ISO**: the 10,633 stored values, field for field | ⬜ | |
| C14-17 | **State stat-code rules**: FL's dispatcher, state-filed tables | ⬜ | |

### RC-5 · Confirmation and close-out (5 tasks) — gates 2, 3, 6–9

| # | Task | Status | Notes |
|---|---|---|---|
| C14-18 | **All 46 states**: the policy total and the modifiers, each state's own rows | ⬜ | **gates 2, 3, 8** |
| C14-19 | **Zero cases**: no coverage, all-zero coverages, IRPM beyond the state maximum, blank modifiers | ⬜ | **gate 4** |
| C14-20 | **Shared names and messages**: `Premium` / `ErcCalculatedTotalPremium` on every record type; the IRPM and SPP messages | ⬜ | **gates 6, 9** |
| C14-21 | **Regression**: add chunk 14 to `104_…regression.py`; clean for chunks 0–14 | ⬜ | |
| C14-22 | **File `CF-CHUNK14-GATE.md`** | ⬜ | |
