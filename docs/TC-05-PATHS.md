# TC-05: the rating-path catalog per state (the Readiness Matrix's denominator)

**Done 2026-10-06, no ISO calls.** For each line, the rating paths a policy can walk, grouped into the design spec's
coverages (`readiness-matrix-integration.md` §4), and for each state which paths **apply** and which are **n/a** (D5).
This is the first version of TC-09's coverage → path configuration. Applicability is necessary, not sufficient: a path
counts toward Passed only when a scenario walks it and ISO agrees (RC-1 onward).

## In plain English

Almost every path applies almost everywhere. Variation between states lives in the *values* (loss costs, rates,
increased-limit factors) and in a set of state rule overrides, not in which paths exist. The useful "n/a" cells are
few and specific: Property's BCEG in New York and DC, GL's size-of-risk plan in 16 states. **The brief's GL column list
does not match ISO's content in four places** (below); those are the user's calls before TC-09.

## Commercial Property: 17 paths, 6 coverages (`scripts/tc/tc05_cp_paths.py`)

Form paths are decided **by rating**: the app's sample is rated in each state on the Special, Broad and Basic forms, and
a path applies where the engine prices it (table names mislead: CA rates Group I on district tables, AK and FL on
their own). BCEG, extra expense and wind/hail % apply where their tables resolve with rows.

| Coverage | Paths | Applies | n/a |
|---|---|---|---|
| Building | Group I, Group II, Specific / Tentative rate, BCEG, coinsurance | 46 (BCEG 44) | PR (the sample doesn't rate there); BCEG: **NY, DC** read none (chunk 27) |
| BPP | Group I, Group II, Specific, coinsurance | 46 | PR |
| Business income | Group I, Group II, coinsurance (incl. other than 80%) | 46 | PR |
| Extra expense | the extra-expense factor | 47 | none |
| Causes of loss | Basic, Broad, Special | 46 | PR |
| Wind/hail ded. | % deductible | 47 | none |

47 states have a Property package (ID, LA, MS, WA have none; PR is off the ISO subscription). **"Sprinkler credit"**,
named in the brief, is not a separate Property table: sprinklered risks rate through the class and leakage tables. It
is left out of the catalog until the user decides what it should mean.

## General Liability: 51 jurisdictions (`scripts/tc/tc05_gl_paths.py`, `tc05_gl_basis.py`)

49 states, DC and PR resolve; **HI has no package**; PR rates but can't be checked against ISO (OI-86). Measured at
2026-10-06 and at the 2027-04-01 cliff.

| Coverage | Paths (stable ids) | Applies |
|---|---|---|
| Prem/Ops | basis payroll, area, gross sales, units, other (59 basis values) · ELP industry / company · ILF direct · split BI/PD limits · size of risk · LCM filed / company · minimum premium · state exceptions | all 51, but **size of risk 35** (n/a: AR CA DE FL GA IL KY LA MA MN NM NV NY PR SC TX) and **state exceptions 22** (CA GA IN KY MA MD MO MS MT ND NH NJ NY OH OK PR TN TX UT VA WA WY) |
| Prod/CO | basis gross sales, payroll · included · ELP industry / company · ILF direct · minimum premium · state exceptions | all 51; **area and units: 0** (no state rates Prod/CO on them); state exceptions **20** (AK AR AZ CT IN LA MD MO MT ND NH NJ NV NY OK PR SD TN UT VT) |
| Cov B · P&AI | included · excluded | 51; **never priced on its own**: included in the Prem/Ops rate |
| Cov C · Med pay | basic · increased · excluded | 51; LA, NJ, NY file their own factors |
| Deductibles | BI, PD, BI/PD × per occurrence / per claim, for Prem/Ops and Prod/CO (12) | 51; every deductible factor is countrywide (no state files its own) |

**At 2027-04-01 the path set changes:** minimum premium has rows only in CA, GA, NJ, NY, WA; size of risk survives only in
NJ and WA; increased medical payments move to a new table (`IncreasedMedPayLimitFactor`) in 46 states; a P&AI limit
table appears in 46. **The matrix needs an as-of date.**

## Where the brief and ISO's GL content disagree (decided 2026-10-06: D8-D13 in `TC-PLAN.md`)

Decided: (1) renamed **Size of risk**; (2) **filed at $0, testable**; (3) **filed at zero, testable**; (4) Cov B **kept, included / excluded**; (5) **all tracked as paths**; (6) Prod/CO area and units **left out**.

1. **"ILF interpolated" does not exist.** ISO's GL ILF tables are flat (discrete limit pairs); the only interpolated
   lookup in GL is the **size-of-risk** relativity. Proposal: rename the column "Size of risk".
2. **Minimum premium is filed as $0** in every state and parent (`PremOpsMinPremium`, `ProdsCompldOpsMinPremium`,
   `SpecialCombinedMinPremium`); the manual reads it as a company matter. Show it as "filed at $0" or as n/a?
3. **Per-claim deductibles give no credit**: all 45 per-claim rows are 0 in every deductible table (per-occurrence rows
   are non-zero). "Filed at zero", n/a, or refer?
4. **Cov B is not separately rated**: its column can only show included / excluded.
5. **Paths the brief misses**: ELP industry / company classes, size of risk, split BI/PD limits, company LCM, the "other"
   premium bases, claims-made (NY files its table empty: not offered there?), governmental-units and stop-gap ILF, and
   the 2026 → 2027 medical-payments change.
6. **The brief over-claims Prod/CO area and units**: no state rates on them.
