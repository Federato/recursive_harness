# Chunk 11 golden case: Leasehold Interest, Tenants Lease

**Derived by hand 2026-09-22, before the engine ran.** Script:
[`114_chunk11_golden_case.py`](../scripts/cf/114_chunk11_golden_case.py).
Group A companions (C11-11/12/13):
[`115_chunk11_groupA_annuity.py`](../scripts/cf/115_chunk11_groupA_annuity.py).

## In plain English first

A tenant with a below-market lease loses money if the building burns and the
lease is cancelled. Leasehold Interest insures that loss. The loss isn't a
limit the insured types in. The rules **work it out**: take the monthly
advantage, multiply by the months left on the lease, and discount to today's
money. They do this twice, once for the day the policy starts and once for
the day it ends, and average the two. That average is then rated like a
building limit, at the building's own rate.

## The risk

Chunk 2's golden risk, unchanged: Oregon, class 0951, Frame, Portland,
protection class 3, `CauseOfLoss = Basic`, $100,000 Building. It prices at
**$261 Basic Group I + $32 Basic Group II**, and both must stay unmoved.

Added on top:

| Where | Field | Value | Why |
|---|---|---|---|
| Policy root | `ExpDate` | `01/01/2028` | `SetNumberOfMonths` reads `EffDate` **and** `ExpDate`. Earlier golden cases never set `ExpDate` |
| LI record (under the Structure) | `PercentInterest` | `10%` | Key into both annuity tables, which hold whole points 5%–15% only |
| | `LeaseEffDate` | `01/01/2025` | Lease began before the policy |
| | `LeaseExpDate` | `01/01/2037` | Ends 10 years after inception |
| | `TenantsGrossLeaseholdInt` | `1500` | Monthly leasehold advantage |

## Correction after the first run: LI is a structure type, not an add-on

**The first run produced nothing on the LI record, and the derivation
had missed why.** The Structure's
`AttachFormCommercialPropertyLeaseholdInterestCoverageForm` keeps the LI
record only when **`PolicyType = "Commercial Property Policy"` and the
Structure's own `CovType = "Leasehold Interest"`**. Otherwise it runs
`Remove … RemoveMultiple="true"`, which deletes the record with no message.
The first submission put LI under a `CovType = Building` structure, so it was
silently deleted. That's a new silent-removal shape for C11-04: a
submitted coverage that disappears instead of pricing at $0.

What changed in the submission (the Domain Tables for a `Leasehold Interest`
structure confirm each value):

| Field | Was | Now | Domain table |
|---|---|---|---|
| `CommercialProperty/PolicyType` | unset | `Commercial Property Policy` | `DomainCovTypeBldg` |
| Structure `CovType` | `Building` | `Leasehold Interest` | `DomainCovTypeBldg` |
| Structure `Coinsurance` | `90%` | `Not Applicable` | `DomainCoinsuranceBldg`, the only value |
| Structure `Limit` | `100000` | removed | `DomainLimitBldg`: blank, 0–0 |

**The arithmetic in steps 1–20 does not change.** The Structure's rate
inputs do not depend on `CovType`. A dependency walk from
`SetBasicGroupICauseOfLossAdjustment` (43 rules) and
`SetBasicGroupIICauseOfLossAdjustment` (28 rules) finds no rule that reads
`CovType`. `LookupBasicGroupIRate` keys on the constant `"Building"`, and
`LookupBasicGroupIIRate` on the constant `"Bldg"`. So 0.239 and 0.027 still
hold. **Step 21 does change**: with `CovType = Leasehold Interest`, there is
no Building coverage on this structure, so it has no $261 / $32 to protect.
Chunk 2's own premiums are protected by re-running chunk 2's script instead.

## Where LI sits, confirmed from the schema

`CommercialPropertyLeaseholdInterestCoverageFormTable` is a child of
**`CommercialPropertyStructure`**. So `../../BasicGroupICauseOfLossAdjustment`
is the Structure's own rate, and `../../../../../../../IRPMFactor` (from a
coverage record) is the **policy-level** `CommercialProperty` record. The
parent's `InitializeRuleSet` appends all 20 grid records unconditionally.
Each one then switches on or off by its own gate.

## Step by step

| # | Value | Rule | Arithmetic | Predicted |
|---|---|---|---|---|
| 1 | `AnnuityConstant` | `SetAnnuityConstant` → `LeaseholdInterestAnnuityConstant[CW]("10%")` | table row | **125.40537** |
| 2 | `DiscFactor` | `SetDiscFactor` → `LeaseholdInterestDiscFactor[CW]("10%")` | table row | **0.99208894** |
| 3 | `NumOfMonthsRemainingAtInception` | `SetNumberOfMonths` | (2037−2027)×12 + (1−1) − [day 1 < day 1 ? 1 : 0] | **120** |
| 4 | `NumOfMonthsRemainingAtExpiration` | same | (2037−2028)×12 + 0 − 0 | **108** |
| 5 | `DiscFactorRaisedTo…AtInception` | `SetComplimentOfDiscFactorIncep` (**the `rul:Power`**) | 0.99208894^120 | 0.38554312868… |
| 6 | `ComplimentOfDiscFactorIncep` | same | 1 − step 5 | 0.61445687131… |
| 7 | `ComplimentOfDiscFactorExpir` | `SetComplimentOfDiscFactorExpir` | 1 − 0.99208894^108 = 1 − 0.42409745923… | 0.57590254076… |
| 8 | `NetLeaseholdInterestFactorAtInception` | `DecimalPlaces=4` | 125.40537 × 0.61445687… = 77.056191… | **77.0562** |
| 9 | `NetLeaseholdInterestFactorAtExpiration` | `DecimalPlaces=4` | 125.40537 × 0.57590254… = 72.221271… | **72.2213** |
| 10 | `TenantsNetLeaseholdInterestAtInception` | `DecimalPlaces=0` | 1500 × 77.0562 = 115,584.3 | **115,584** |
| 11 | `TenantsNetLeaseholdInterestAtExpiration` | `DecimalPlaces=0` | 1500 × 72.2213 = 108,331.95 | **108,332** |
| 12 | `TenantsNetLeaseholdInt` | `SetTenantsNetLeaseholdInt`, `DecimalPlaces=0` | (108,332 + 115,584) / 2 | **111,958** |
| 13 | `TotCoveredLeaseholdIntNet` | `SetTotCoveredLeaseholdIntNet` | **Sum** of the 4 sub-coverage nets; 3 are 0 | **111,958** |
| 14 | `BasicGroupICauseOfLossAdjmt` | ancestor copy from the Structure | chunk 1 step 3 | **0.239** |
| 15 | `BasicGroupIICauseOfLossAdjmt` | ancestor copy from the Structure | chunk 2 step 5 | **0.027** |
| 16 | Tenants **BGI** `Premium` | 5 nested `Product DecimalPlaces=0` | round(1,119.58 × 0.239) = round(267.58) = 268, then × PackageMod 1.0 × IRPM 1.0 × 2 Cyber 1.0 | **$268** |
| 17 | Tenants **BGII** `Premium` | same shape | round(1,119.58 × 0.027) = round(30.23) | **$30** |
| 18 | Tenants Broad / Special / EQ | gates: `CauseOfLoss` = Broad / = Special / EQ elected | none true | **$0 each, record switched off** |
| 19 | Other 3 sub-coverages × 5 forms | gate: own gross/monthly field ≠ 0 | none supplied | **$0 each** |
| 20 | LI `ErcCalculatedTotalPremium` | sum of the 20 children | 268 + 30 | **$298** |
| 21 | ~~Building BGI / BGII~~ | see the correction above | this structure carries no Building coverage; chunk 2's script is re-run instead | ~~$261 / $32~~ **chunk 2 green** |

## Things the derivation found before the run

1. **C11-20 is answered by the rule text: it's a sum, not a selection.**
   `SetTotCoveredLeaseholdIntNet` is a plain `Sum` of the four sub-coverage
   nets. But it is **not what gets rated**. Each sub-coverage's premium
   reads its **own** net (`../TenantsNetLeaseholdInt`), not the total. The
   total is informational. That's a different shape from chunk 5's
   `SetFactor`, and running this case confirms it.
2. **The `rul:Power` guard is one of seven, not one.** `DiscFactor`, both
   `DiscFactorRaisedTo…` values, both `ComplimentOfDiscFactor…` values and
   both `NetLeaseholdInterestFactor…` values are each `IsNull`-guarded. A
   submission can inject at any of those points. `AnnuityConstant` is the
   only annuity input **without** a guard: it is always overwritten from the
   table. C11-12 tests three injection points, not just the Power.
3. **Every premium rounds to whole dollars at each of five steps.**
   `round(Net/100 × rate)` happens *before* any multiplier. So the rate is
   applied to a whole-dollar figure, which differs from rounding once at the
   end.
4. ~~**`ExpDate` matters here for the first time.**~~ **Withdrawn during
   C11-04.** I reasoned that a missing `ExpDate` would default to
   `01/01/0001` and zero both month counts. It doesn't: ISO's `Default` block
   sets `ExpDate = EffDate + 1 year` on every run, overwriting whatever was
   submitted. `ExpDate` is not an input. Supplying it in this golden case was
   harmless (it equals EffDate + 1 year) but unnecessary. See
   `CF-CHUNK11-ZERO-CASES.md`, Z5.
5. **A rounding tie is one input away.** With gross = **1,000** instead of
   1,500, step 12 is (72,221 + 77,056)/2 = **74,638.5**, an exact half. That
   is a ready-made OI-70 probe for the live ISO call (C11-22). It is avoided
   here on purpose, so the golden case doesn't depend on the tie rule.
6. **`0 ** 0` is a trap in our engine, not ISO's.** If `PercentInterest` is
   blank, `DiscFactor` becomes 0.0. If the lease has also expired, months =
   0, and the `rul:Power` evaluates 0^0. Python's `Decimal` raises
   `InvalidOperation` there; .NET's `Math.Pow(0,0)` returns 1. Logged for
   C11-04.
7. **The EQ cell is the only one that skips PackageMod and IRPM.** That's
   4 sub-coverages × 4 non-EQ forms = the census's "16 of 32 files".
</content>
</invoke>

## Result (2026-09-22)

**MATCH on every value after two corrections to the submission and one
authorized engine fix.** In the order they were found:

1. **The record was silently deleted** (the correction above). This was a
   derivation miss, fixed in the submission.
2. **Engine gap: `GreaterThan`/`LessThan` refused two dates.**
   `SetNumberOfMonths` compares `LeaseExpDate` against `EffDate`. The
   interpreter's ordered comparisons only accepted numbers. The census's
   "every node already implemented" was true of the node names and false of
   their operand types. **Fixed 2026-09-22 with the user's authorization**:
   `_cmp` in `gl_engine/interp/nodes.py` now compares two dates as dates.
   Every other operand shape takes the old path unchanged, including a date
   against the `01/01/0001` sentinel, which still refuses. Scope: 28 ordered
   date comparisons in 5 countrywide files, 2 of them premium-bearing (this
   one and Builders Risk's `SetProRate`). The other 13 rules are period
   validation messages. None was reachable before, because no earlier
   submission supplied those dates.
3. **Finding 8, a prediction miss.** The derivation said the Tenants
   **Earthquake** cell would be off. It came back **on** (premium $0). The
   gate is `EQCovIndicator ≠ "No Coverage" AND ≠ "Not Applicable"`, and a
   blank field satisfies both, so **blank reads as elected**. This is chunk
   10's blank-`SprinklerSystem` shape again. The submission now sends the
   domain-correct `"No Coverage"`. The blank case goes to C11-04.

After those, all 20 values match: annuity 125.40537 / 0.99208894, months
120 / 108, factors 77.0562 / 72.2213, nets 115,584 / 108,332 → 111,958, and
premiums **$268 BGI + $30 BGII = $298**. Every other grid cell is off.
Chunk 2's own script is still green at $261 / $32. **One validation
message**: "Either CP 10 75 Or CP 10 76 must be attached", owed to C11-09.

## Group A companions: predictions written before the run

Script: `115_chunk11_groupA_annuity.py`. Every case is the golden case
with **one** input changed. Inputs whose average lands on an exact half were
**deliberately avoided** (12%, 11%, 8% and 5% all tie at gross 1,500), so
these checks don't depend on the rounding rule.

### C11-11: the annuity, traced

| Case | Change | Months | Factors | Nets → avg | BGI / BGII |
|---|---|---|---|---|---|
| A | none (golden) | 120 / 108 | 77.0562 / 72.2213 | 115,584 / 108,332 → 111,958 | **268 / 30** |
| B | `EffDate 03/15/2027`, `ExpDate 03/15/2028`, `LeaseExpDate 06/10/2037` | (10×12 + 3 − **1**) = **122** / (9×12 + 3 − 1) = **110**. The −1 applies because day 10 < day 15 | 77.8182 / 73.0594 | 116,727 / 109,589 → 113,158 | **270 / 31** |

**What the rules do, confirmed by reading them:** the average is of the
two *whole-dollar nets* (`(AtExpiration + AtInception) / 2`, rounded), not
of the factors. The build order's "averaged inception-to-expiration" holds.
**The tables are internally consistent.** For all 11 rows, `DiscFactor` =
(1 + annual rate)^(−1/12) to within 5×10⁻⁹, and `AnnuityConstant` = v/(1−v)
from the unrounded v. So "10%" means 10% a year, discounted monthly, and the
factor is the present value of one payment at the end of each remaining
month.

### C11-12: injecting a derived field

| Case | Injected on the LI record | Predicted | Why |
|---|---|---|---|
| A | `DiscFactorRaisedToNumOfMonthsRemainingAtInception = 0.5` (**the `rul:Power` bypassed**) | factor-inc 62.7027, net-inc 94,054, avg 101,193 → **242 / 27** | guard honours the submitted value |
| B | `DiscFactor = 0.99` | 0.99^120 and 0.99^108 → 87.8615 / 83.0492 → 131,792 / 124,574 → 128,183 → **306 / 35** | `SetDiscFactor` is guarded too |
| C | `NetLeaseholdInterestFactorAtInception = 100` | 150,000 / 108,332 → 129,166 → **309 / 35** | guarded |
| D (control) | `AnnuityConstant = 200` | **268 / 30**, unchanged | `SetAnnuityConstant` has **no** guard, so the table overwrites it |

### C11-13: the live inputs

| Case | Change only | Predicted |
|---|---|---|
| A | `PercentInterest = 13%` → A 97.68636, v 0.98986689 | 68.9091 / 65.1680 → 103,364 / 97,752 → 100,558 → **240 / 27** |
| B | `LeaseExpDate = 01/01/2032` → 60 / 48 months | 47.5385 / 39.7518 → 71,308 / 59,628 → 65,468 → **156 / 18** |
