# Unmanned Aircraft — Rating Algorithms

**Source ERC package:** `GL_CW_20231201_V03`
**Line:** General Liability (GL), Countrywide, subline 370 — Unmanned Aircraft, Rule 37
**Reformatted from:** `docs/gates/GATE-370-UNMANNED-AIRCRAFT.md` (filed 2026-08-11, as-of date 2026-08-11), cross-checked against `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.2.9, `docs/erc/03-RATING-STRUCTURE.md`, and `docs/rating-engine/A3-ENDORSEMENT-CATALOG.md`
**Documented:** 2026-08-20
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — an offline engine run of OK with one designated drone added (no ISO sample carries one) at 2026-10-02 (GL_OK_20261001_V01 / GL_CW_20261001_V01) and 2027-04-01 (GL_OK_20270401_V04 / GL_CW_20270401_V02), with edge cases rated in `underwriting` mode, plus rule-XML hash diffs of the three drone rule files across all 12 CW editions; corrections are marked **(engine)**.

> **Edition note (engine).** The drone rules in `GL_CW_20231201_V03` are byte-identical (canonical XML
> hash) to `GL_CW_20260101_V01` and `GL_CW_20261001_V01`, so this doc's base derivation is still the
> current CW. **CW 20270401 V01/V02** change five things:
> - The coverage gate (`SetCoverageOnPolicyIndicator`) now reads `UnmannedAircraftCoverageOptions =
>   "Limited Coverage For Designated Unmanned Aircraft"` instead of `LimitedCovForDesignatedUnmannedAircraft
>   = "Yes"`, and requires `Subline = Premises/Operations and Products/Completed Operations`.
> - `SetPremium` gains a **$1 floor**: premium 1 when the product rounds to 0 while `AdjustedRate > 0`.
> - `" CSL"` is no longer appended to limits before the ILF lookup (OI-96/97); `unmannedAircraftAggregateLimitLookup`
>   is deleted.
> - The policy-level `GeneralLiabilityUnmannedAircraft` min-premium rules (`SetMinimumPremium`,
>   `SetMinPremium`, `LookupUnmannedAircraftMinPremium`) are removed.
> - The usage/place domain and table values change case ("Education and research", "Other usage, …",
>   "Private land", "Not applicable"). The keys are case-sensitive (`CaseInsensitive="false"`).
>
> Engine premiums for the same drone are identical at both dates: **CovA 316, CovB 216**.

Unmanned Aircraft is a single subline (370, Rule 37) rated on two independent coverages:

- **Coverage A** — Bodily Injury / Property Damage (`…UnmannedAircraftCovABIPDCoverage`)
- **Coverage B** — Personal & Advertising Injury (`…UnmannedAircraftCovBPAICoverage`)

62 rules across both, per GATE-370-UNMANNED-AIRCRAFT.md §1.

> **This subline is company-rated in its entirety.** Rule 37 manual paragraph C.2 states:
> *"All applicable loss costs and modifiers referenced in Paragraphs C.2.b. and C.2.d. and Tables
> D., E. and F. must be referred to company before using."* The algorithm below documents the
> filed ERC computation — the countrywide loss-cost, LCM, claims-made, modifier, ILF, and
> deductible tables all resolve to real numbers and the rules run end to end — but per the manual
> every one of those numbers is a reference value, not a usable filed price, and the risk must be
> referred. (GATE-370-UNMANNED-AIRCRAFT.md §4, item 4/7 in the manual-confirmation table.)

**Basis of premium: each unmanned aircraft** — a unit count, no ÷1000 exposure step
(GATE-370-UNMANNED-AIRCRAFT.md §1, manual C.2.a).

---

## Master orchestration

Both coverage groups gate identically, then run the same 13-rule shape (Coverage B drops the
deductible step from the premium formula only):

```
ErcProcess:
    if CoverageOnPolicyIndicator == 0:
        Premium = 0.0
    else:
        1  SetAggregateLimit
        2  SetmaximumTakeoffWeightCeiling      <- empty rule; logic inlined at point of use (see Step 2)
        3  SetLossCost
        4  SetLCM
        5  SetClaimsMadeMultiplier
        6  SetBaseRate
        7  SetOwnershipAndOperationBIPDRatingModifiers    (Coverage A) / ...PAIRatingModifiers (Coverage B)
        8  SetPrimaryPlaceOfOperationBIPDRatingModifiers  (Coverage A) / ...PAIRatingModifiers (Coverage B)
        9  SetUsageBIPDRatingModifiers                    (Coverage A) / SetUsagePAIRatingModifiers (Coverage B)
        10 SetAjustedRate            <- misspelled rule name; target datadef AdjustedRate is spelled correctly
        11 SetILF
        12 SetDeductibleFactor        (Coverage A only)
        13 SetPremium
```

(GATE-370-UNMANNED-AIRCRAFT.md §1, table of 13 numbered rules.)

**(engine) Confirmed as executed.** `ErcProcess` gates on `CoverageOnPolicyIndicator`. When it is on,
it runs `ErcSetRatesAndFactors` (rules 1–12 in the order above) and then `ErcRate` (`SetPremium`,
`SetPremiumIndicator`). In CW 20270401 `ErcSetRatesAndFactors` also runs three `Set…IntNumeric` limit
converters. The indicator is 1 only when **all** of these hold:
- a CG 24 50 / 24 51 / 24 52 *Limited Coverage For Designated Unmanned Aircraft* record exists;
- the policy gate is met: `LimitedCovForDesignatedUnmannedAircraft = "Yes"` (≤ 20261001), or
  `UnmannedAircraftCoverageOptions = "Limited Coverage For Designated Unmanned Aircraft"` plus the combined
  subline (20270401);
- the drone's `CovAApplies = "Yes"` (or `CovBApplies` for Coverage B).

Every ISO sample input in `Payloads/` sends `LimitedCovForDesignatedUnmannedAircraft = "No"`, so no ISO
golden exercises this subline. The drone record sits under the classification
(`GeneralLiabilityUnmannedAircraftTable`), and the CG 24 50 record at policy level.

**Drone borrows Prem/Ops's machinery wholesale** — the LCM, claims-made multiplier, ILF, and all
three deductible tables are the Premises/Operations lookups reused directly (`LookupPremOpsLCM`,
`LookupPremOpsClaimsMadeMultiplierAllOther`, `LookupILFPremOps`, `LookupDedFactorPremOps{CSL,BI,PD}`).
It borrows the *tables*, not Prem/Ops's already-computed values, so it carries no cross-coverage
(E18) dependency (GATE-370-UNMANNED-AIRCRAFT.md §1).

~~Not resolved in source docs — whether `SetLCM`, `SetClaimsMadeMultiplier`, and `SetILF` are computed
once and shared between Coverage A and Coverage B.~~ **(engine) Resolved:** independently. Each coverage
group has its own copies of every rule and lookup, and the engine trace shows both groups performing their
own `PremOpsLCM`, claims-made, and `ILFPremOps` lookups (same values).

---

## File map

| Piece | Rule / group | Citation |
|---|---|---|
| Rate build-up + premium, Coverage A (BI/PD) | `…UnmannedAircraftCovABIPDCoverage` | GATE-370-UNMANNED-AIRCRAFT.md §1 |
| Rate build-up + premium, Coverage B (PAI) | `…UnmannedAircraftCovBPAICoverage` | GATE-370-UNMANNED-AIRCRAFT.md §1 |
| Validation-only rules | `GeneralLiabilityUnmannedAircraft` (3 `DoMessage*` rules, none about usage) | GATE-370-UNMANNED-AIRCRAFT.md §0 |
| Weight guard | `DoMessageWeightOfDroneCheck` — `MaximumTakeoffWeight <= 0` → error | GATE-370-UNMANNED-AIRCRAFT.md §0, §3 |
| Rate tables | see `UnmannedAircraft_ERC_Tables.md` | — |
| Terrorism sub-coverage — **out of scope for this doc** | `GeneralLiabilityUnmannedAircraftTerrorismCoverage` | `docs/rating-engine/A2-CW-RULE-CATALOG.md` line 451 |

~~Not resolved in source docs — exact ERC XML file names/paths.~~ **(engine)** The files are
`Rules/GeneralLiabilityUnmannedAircraftCovABIPDCoverageRules.Rule.xml`,
`Rules/GeneralLiabilityUnmannedAircraftCovBPAICoverageRules.Rule.xml`, and
`Rules/GeneralLiabilityUnmannedAircraftRules.Rule.xml` (stat codes, `DoMessage*`, and min premium
≤ 20261001), plus the policy-level `GeneralLiabilityLimitedCovForDesignatedUnmannedAircraftPremiumToReachMinCoverageRules.Rule.xml`.
All sit in each CW package. Other citations remain to the gate doc's section headings.

---

## Coverage A (BI/PD) — rate build-up

### Step 1 — Aggregate limit
`SetAggregateLimit`, via `unmannedAircraftAggregateLimitLookup` (GATE-370-UNMANNED-AIRCRAFT.md §1,
item 1). Not resolved in source docs — the lookup's keys and values. **(engine) Resolved:** there is no
table. `SetAggregateLimit` copies the drone's own `AggregateLimit` input (blank if absent).
`unmannedAircraftAggregateLimitLookup` is a string helper that appends `" CSL"` for the ILF lookup, and it
is deleted in CW 20270401. Legal values come from `DomainUnmannedAircraftAggregateLimit`, keyed by the
policy each-occurrence limit. Engine: `AggregateLimit = '1,000,000'`.

In 8 states (IN, MO, MT, ND, NH, OK, TN, UT) this rule and its lookup table are overridden by a
governmental-units increased-limits variant — see § State deviations below.

### Step 2 — Maximum takeoff weight ceiling
`SetmaximumTakeoffWeightCeiling` is an **empty rule that is still called** — its body carries only
a developer comment: `<!--Logic for maximumTakeoffWeightCeiling moved to be inline where used.-->`
(GATE-370-UNMANNED-AIRCRAFT.md §2). The actual computation, given in §3, is a rounded-offset
ceiling:

```
maximumTakeoffWeightCeiling = Convert<int>( round( MaximumTakeoffWeight + 0.499, 0 ) )
```

~~Not resolved in source docs — exactly which downstream rule performs this inline computation.~~
**(engine)** It is the helper rule `maximumTakeoffWeightCeiling` (type integer), called from `SetLossCost`.
A null `MaximumTakeoffWeight` gives 0. Engine: 10 lb → `round(10.499, 0)` → **10**.

### Step 3 — Loss cost
`SetLossCost` (GATE-370-UNMANNED-AIRCRAFT.md §1, item 3):

```
if maximumTakeoffWeightCeiling != 0:
    LossCost = LookupUnmannedAircraftLimitedLiabilityBIPDLossCost(weight band)
else:
    LossCost = <not specified — see below>
```

`LookupUnmannedAircraftLimitedLiabilityBIPDLossCost` reads matrix
`UnmannedAircraftLimitedLiabilityBIPDLossCost` (countrywide only, 0/51 states filed — §5), banded on
`MaximumTakeoffWeight`:

| Weight `>` | `≤` | BI/PD loss cost |
|---|---|---|
| 0 | 1 | 66.11 |
| 1 | 5 | 110.19 |
| 5 | 15 | 154.26 |
| 15 | 55 | 220.37 |
| 55 | 2147483647 | **0** |

(GATE-370-UNMANNED-AIRCRAFT.md §3.) The `>55 lb` row prices at 0 — refer to company (§3, §0).

~~Not resolved in source docs — what `LossCost` resolves to when `maximumTakeoffWeightCeiling == 0`.~~
**(engine)** It resolves to `0.0` (a constant). Engine, weight 0: `LossCost` 0, both premiums 0, and
message *"Please enter the Maximum Takeoff Weight to be greater than 0"*. Engine, 10 lb → band (5, 15] →
**154.26**. Engine, 60 lb → band (55, ∞) → **0**: CovA and CovB both 0, so the drone is priced at $0. In
`underwriting` mode R19 is raised (`UnmannedAircraftLimitedLiabilityBIPDLossCost … -> 0`). This is how
the engine treats the PRD's ">55 lb encoded as 0 = Refer To Company": R19 in underwriting mode, and a
silent $0 in `strict-erc`. The 2027 $1 floor does not rescue it, because `AdjustedRate` is 0.

### Step 4 — LCM
`SetLCM` → `LookupPremOpsLCM`, countrywide, value **1** — the Premises/Operations LCM reused
directly (E15, confirmed again on this subline). Live here (unlike liquor and railroad, where the
same lookup is called but has no effect) (GATE-370-UNMANNED-AIRCRAFT.md §1).

### Step 5 — Claims-made multiplier
`SetClaimsMadeMultiplier` → `LookupPremOpsClaimsMadeMultiplierAllOther` — explicitly the
Premises/Operations **"All Other"** claims-made multiplier variant, per manual C.2.c: *"Claims-made
multipliers are found in Rule 23. Use Premises/Operations All Other claims-made multipliers."*
(GATE-370-UNMANNED-AIRCRAFT.md §1, §4 item 2.)

NY overrides this rule with its own selector — see § State deviations. **(engine)** For an occurrence
policy the trace writes `ClaimsMadeMultiplier = 1.0` (OK, both dates).

### Step 6 — Base rate
`SetBaseRate` (GATE-370-UNMANNED-AIRCRAFT.md §1, item 6):

```
BaseRate = round(LossCost x LCM x ClaimsMadeMultiplier, 3)
```
**(engine)** 154.26 × 1 × 1.0 → **154.260** (CovA); 87.63 → **87.630** (CovB).

### Step 7 — Ownership and Operation modifier
`SetOwnershipAndOperationBIPDRatingModifiers` — 9 rows, countrywide
(`UnmannedAircraftOwnershipAndOperationBIPDRatingModifiers`), 1/51 states (WA) filing an override
(§5). Full row values not resolved in source docs — the gate doc gives only the zero-cell count: 3
of 9 rows price at **0** (refer to company), one of which is confirmed to be the row **"Non-owned
unmanned aircraft operated by other parties"** (GATE-370-UNMANNED-AIRCRAFT.md §7a, resolving OI-49).

**(engine) Row values, read from CW 20261001 V01 / 20270401 V02 (unchanged; BI/PD and PAI identical):**

| Ownership and operation | Factor |
|---|---|
| Unmanned aircraft owned and operated by the insured | 1 |
| Unmanned aircraft rented or leased to and operated by the insured | 1 |
| Unmanned aircraft operations are contracted out to a subcontractor | 0.4 |
| The insured is a hired operator/pilot operating unmanned aircraft provided by client | 1 |
| Unmanned aircraft rented or leased to others | 0.9 |
| Owned unmanned aircraft operated on insured's behalf by hired operator | 0.9 |
| Non-owned unmanned aircraft operated by other parties | **0** |
| Not Applicable | **0** |
| Unknown | **0** |

### Step 8 — Primary Place of Operation modifier
`SetPrimaryPlaceOfOperationBIPDRatingModifiers` — 9 rows, countrywide
(`UnmannedAircraftPrimaryPlaceOfOperationBIPDRatingModifiers`), 1/51 states (WA) filing an override
(§5). 2 of 9 rows price at **0** (§7a). Row values not resolved in source docs. **(engine)** Rural 0.8 ·
Urban 1.2 · Suburban 1 · Indoors 1.3 · Private Land 0.6 · Over bodies of water 0.6 · High concentration of
people 1.3 · Not Applicable **0** · Unknown **0**. BI/PD and PAI are identical. 2027 respells "Private
land" and "Not applicable".

### Step 9 — Usage modifier
`SetUsageBIPDRatingModifiers` — 12 rows, countrywide (`UnmannedAircraftUsageBIPDRatingModifiers`),
0/51 states filed. Full values confirmed cell-for-cell against manual Table 37.E
(GATE-370-UNMANNED-AIRCRAFT.md §0):

| # | Usage | BI/PD modifier |
|---|---|---|
| 1 | Aerial photography, surveillance, inspection, survey, data collection, media | 1.00 |
| 2 | Firefighting, search and rescue, other emergency services | **0 (RTC)** |
| 3 | Crop spraying, dispersing of chemicals | **0 (RTC)** |
| 4 | Internet access, other communication services | **0 (RTC)** |
| 5 | Delivery of goods or merchandise, transport of cargo | 1.50 |
| 6 | Weather and environmental monitoring | 1.25 |
| 7 | Education and research | 1.00 |
| 8 | Operator/Pilot training | 1.10 |
| 9 | Entertainment, demonstrations, special events, sports (incl. drone racing) | **0 (RTC)** |
| 10 | Towing signs/banners, pulling twine/cable, distribution of materials | 1.25 |
| 11 | Manufacturing, sales, repair or rental of unmanned aircraft — testing only | 0.80 |
| 12 | Other usage, not otherwise classified | **0 (RTC)** |

Else-branch: `SetUsageBIPDRatingModifiers` writes `0.0` when `Usage` is empty — a sixth path to a
zero-rated modifier, independent of the five RTC rows above (GATE-370-UNMANNED-AIRCRAFT.md §0).

**(engine)** Table labels are the full filed strings, e.g. "Aerial photography, surveillance,
inspection, survey, data collection, media services", "Education and Research". CW 20270401 respells
rows 7 and 12 as "Education and research" and "Other usage, not otherwise classified". The key is
case-sensitive, so a pre-2027 spelling sent to a 2027 edition misses. The engine run (OK@2027-04-01,
"Education and Research") rated the drone at **$0** with no message. **The Usage axis has no `Unknown`
or `Not Applicable` row** (12 rows, domain likewise); only the other two axes do.

**Referral requirement (engine obligation, not an ERC guard).** ERC multiplies all three
modifiers into `AdjustedRate` (Step 10) with **no test of any kind** — `Rules referencing
UsageRatingMod: 2 — both the rating rules that multiply by it` (§0). Per this project's rule:
*any of the three rating modifiers resolving to `0` must raise `REFER` before it multiplies.*
`Unknown` is itself a filed domain value on ~~all three axes~~ **(engine) the Ownership and Place axes
(not Usage)** and also prices `0` — a broker who
cannot resolve which single category applies per axis submits `Unknown`, which is a licensed way
to trigger the same referral (§7a). This is a submission-level / engine-level requirement layered
on top of ERC, not something ERC itself enforces.

**(engine) How the built engine does it.** Register entry **R19** (`gl_engine/rating/referrals.py`,
`d_zero_rating_factor`, reported under R14) runs only in `underwriting` mode. It raises when any
*lookup* in the trace whose detail contains "UnmannedAircraft" returns 0. The multiply is not stopped:
the zero is priced and a REFER is attached. Engine results, OK@2026-10-02:

| Input | CovA / CovB | R19 raised by |
|---|---|---|
| 60 lb | 0 / 0 | both loss-cost lookups → 0 |
| Usage = Firefighting | **0 / 162** (PAI 0.9 still prices) | usage lookup → 0 |
| Ownership = Unknown | 0 / 0 | ownership lookups → 0 |
| Usage empty | 0 / 0 | **only** the min-premium lookup below; the empty-usage else-branch writes a constant, not a lookup |
| 10 lb, all factors valid | 316 / 216 | **`UnmannedAircraftMinPremium` → 0** |

Two register defects follow (engine findings, not fixed here):
- **False positive.** `UnmannedAircraftMinPremium` (CW value 0, meaning "no minimum") is looked up on
  every drone policy, by `GeneralLiabilityUnmannedAircraftRules` ≤ 20261001 and by
  `…LimitedCovForDesignatedUnmannedAircraftPremiumToReachMinCoverage` in 2027. So **every** drone
  policy refers under R19.
- **False negative.** A constant-0 modifier (empty Usage) or a lookup *miss* (a wrong-case 2027 usage
  value) zero-prices the drone without any qualifying lookup. Such a drone would not refer if the
  min-premium false positive were fixed.

### Step 10 — Adjusted rate
`SetAjustedRate` *(sic — rule name is misspelled; the target datadef `AdjustedRate` is spelled
correctly)* (GATE-370-UNMANNED-AIRCRAFT.md §1 item 10, §2):

```
AdjustedRate = round(
    BaseRate
  x OwnershipAndOpRatingMod
  x PrimaryPlaceOfOpRatingMod
  x UsageRatingMod
, 3)
```

Per manual C.2.d, confirmed exact including modifier order (GATE-370-UNMANNED-AIRCRAFT.md §4 item 4).
**(engine)** CovA 154.260 × 1 × 1 × 1 → **154.260**; CovB 87.630 × 1 × 1 × 1.2 = 105.156 → **105.156**.

**Manual gap not implemented in ERC:** C.2.d(1)–(3) requires that where more than one category
applies on an axis, the **highest** rating modifier be assigned. ERC takes a single submitted value
per axis with no max-of-many logic. Resolved as a **submission requirement** (OI-48, §7a): the
submission must arrive with one resolved category per axis; if ambiguous, the broker submits the
applicable referral category, or `Unknown` if unresolvable.

### Step 11 — Increased limits factor
`SetILF` → `LookupILFPremOps` — the Premises/Operations ILF table reused directly. Described in the
gate doc only by size (15,857 characters — the largest single rule in any gate reviewed to date);
its keys and values are **not resolved in source docs**
(GATE-370-UNMANNED-AIRCRAFT.md §1 item 11).

**(engine) Resolved from the rule body and the trace.** The lookup is `ILFPremOps[Factor]`, keyed on
(State, **table assignment fixed at 3**, each-occurrence limit, aggregate limit). The limits are chosen
from the drone aggregate `A`, the policy Prem/Ops occurrence `O` and the policy general aggregate `G`
(the subline must include Prem/Ops):
- if `A < O`: (`A`, `A`);
- else if `A ≤ G`: (`O`, `A`).

Up to 20261001 the `A` arguments get `" CSL"` appended; 2027 drops it. Engine, A = O = 1,000,000,
G = 2,000,000: `ILFPremOps['OK', 3, '1,000,000 CSL', '1,000,000 CSL'] = 2.05` (2026-10-02) and
`['OK', 3, '1,000,000', '1,000,000'] = 2.05` (2027-04-01).

In 8 states (IN, MO, MT, ND, NH, OK, TN, UT), `SetILF` is overridden together with
`SetAggregateLimit` by a governmental-units increased-limits variant — see § State deviations.

### Step 12 — Deductible factor (Coverage A only)
`SetDeductibleFactor` → `LookupDedFactorPremOps{CSL,BI,PD}` — three Premises/Operations deductible
tables (Combined Single Limit / Bodily Injury / Property Damage) reused directly
(GATE-370-UNMANNED-AIRCRAFT.md §1 item 12). ~~Not resolved in source docs — which of the three is
selected under what condition.~~ **(engine)** The selection, from the drone's deductible inputs:
- `BIPDDeductible` set and not "No Deductible" → **CSL** table;
- else `BIDeductible` and `PDDeductible` both set → **BI + PD** (summed);
- else BI only → **BI** table; PD only → **PD** table;
- else → `0.0`.

Engine, BIPD "No Deductible": `DeductibleFactor = 0`.

Coverage B's premium formula (Step 13) drops the deductible term entirely, so this step applies to
Coverage A only.

---

## Coverage A (BI/PD) — premium

### Gate
`ErcProcess`: `CoverageOnPolicyIndicator == 0` → `Premium = 0.0`; otherwise the 13-rule chain runs
and produces a rate (GATE-370-UNMANNED-AIRCRAFT.md §1).

### Branch A — standard (only branch)
`SetPremium` (GATE-370-UNMANNED-AIRCRAFT.md §1, item 13):

```
Premium =
    AdjustedRate
  x (ILF - DeductibleFactor)
  x PackageModFactor
  x ExperienceRatingModificationFactor
  x ExpenseModification
  x ModToUse
```

Unlike the CF Structure premium rules, the gate doc gives no evidence of multiple `CovType`-keyed
branches (scheduled / Legal Liability / blanket) for this subline — Unmanned Aircraft premium is a
single formula gated only by `CoverageOnPolicyIndicator`. No comparison-of-branches table applies.

~~Not resolved in source docs — decimal-place rounding convention for the premium product.~~
**(engine)** `Product ToDataDef=Premium DecimalPlaces=0`: the whole product is rounded once to whole
dollars. Engine: 154.260 × (2.05 − 0) × 1 × 1 × 1 × 1 = 316.233 → **316** (OK, both dates).
CW 20270401 adds `Premium = 1 if round(…) = 0 and AdjustedRate > 0`.

**Policy-level minimum (engine).** `UnmannedAircraftMinPremium` = 0 (CW, every edition), so
`…LimitedCovForDesignatedUnmannedAircraftPremiumToReachMinCoverage` writes `Premium = 0.0`. Its
`SetTotalUnmannedAircraftPremium` sums `CovA.Premium` and `CovB.Premium` per drone inside one `ForEach`.
The engine returned **216** (CovB only) instead of 532. `gl_engine/interp/nodes.py` `_for_each` yields
only the *last* child of a multi-child `ForEach` body. No premium effect today because the minimum is
0, but it is a latent interpreter defect.

---

## Coverage B (PAI) — differences

Coverage B (`…UnmannedAircraftCovBPAICoverage`) runs the **same 13-rule shape** as Coverage A, with
these named differences (GATE-370-UNMANNED-AIRCRAFT.md §0, §1):

- Step 3 uses `UnmannedAircraftLimitedLiabilityPAILossCost` (2 rows, CW only) instead of the BI/PD
  loss-cost table.
- Steps 7–9 use the PAI-suffixed modifier rules/tables: `SetOwnershipAndOperationPAIRatingModifiers`,
  `SetPrimaryPlaceOfOperationPAIRatingModifiers`, `SetUsagePAIRatingModifiers`.
- Step 12 (deductible factor) does not apply to Coverage B.
- Step 13 premium formula **drops the deductible term** (see below).

### PAI loss cost table
`UnmannedAircraftLimitedLiabilityPAILossCost`, countrywide, 0/51 states, 2 rows:

| Weight | PAI loss cost |
|---|---|
| 0–55 lb | 87.63 |
| `>55` lb | **0** |

(GATE-370-UNMANNED-AIRCRAFT.md §3, §5.)

### PAI usage modifier
`UnmannedAircraftUsagePAIRatingModifiers`, 12 rows, countrywide, confirmed cell-for-cell against
manual Table 37.E (GATE-370-UNMANNED-AIRCRAFT.md §0):

| # | Usage | PAI modifier |
|---|---|---|
| 1 | Aerial photography, surveillance, inspection, survey, data collection, media | 1.20 |
| 2 | Firefighting, search and rescue, other emergency services | 0.90 |
| 3 | Crop spraying, dispersing of chemicals | 0.90 |
| 4 | Internet access, other communication services | **0 (RTC)** |
| 5 | Delivery of goods or merchandise, transport of cargo | 0.90 |
| 6 | Weather and environmental monitoring | 0.90 |
| 7 | Education and research | 1.00 |
| 8 | Operator/Pilot training | 1.00 |
| 9 | Entertainment, demonstrations, special events, sports (incl. drone racing) | **0 (RTC)** |
| 10 | Towing signs/banners, pulling twine/cable, distribution of materials | 1.00 |
| 11 | Manufacturing, sales, repair or rental of unmanned aircraft — testing only | 0.80 |
| 12 | Other usage, not otherwise classified | **0 (RTC)** |

**Same usage, different meaning per coverage.** Firefighting is a referral (RTC) for BI/PD (row 2
above) and a real factor, 0.90, for PAI. A sentinel/referral register keyed only on `(table, value)`
is wrong for this subline; it must be keyed on `(table, column, row)` (GATE-370-UNMANNED-AIRCRAFT.md
§0, finding 3).

### PAI ownership/place modifiers
`UnmannedAircraftOwnershipAndOperationPAIRatingModifiers` (9 rows, 3 zero cells) and
`UnmannedAircraftPrimaryPlaceOfOperationPAIRatingModifiers` (9 rows, 2 zero cells) — same zero-cell
counts as their BI/PD counterparts; full row values not resolved in source docs
(GATE-370-UNMANNED-AIRCRAFT.md §7a).

### Coverage B premium formula
```
Premium =
    AdjustedRate
  x ILF
  x PackageModFactor
  x ExperienceRatingModificationFactor
  x ExpenseModification
  x ModToUse
```

The gate doc states only that "Coverage B drops the deductible term" from the Coverage A formula
(§1, item 13); it does not reproduce Coverage B's formula verbatim. The reconstruction above assumes
the deductible term is simply omitted and `ILF` is used un-adjusted (rather than, say, `(ILF - 0)`).
**(engine) Confirmed literally.** The rule is `Product DecimalPlaces=0 (AdjustedRate, ILF, PackageModFactor,
ExperienceRatingModificationFactor, ExpenseModification, ModToUse)`, with the same 2027 $1 floor.
Engine: 105.156 × 2.05 = 215.5698 → **216**.

---

## Coverage A vs Coverage B — side by side

| | Coverage A (BI/PD) | Coverage B (PAI) |
|---|---|---|
| Loss cost table | `UnmannedAircraftLimitedLiabilityBIPDLossCost` (5 rows) | `UnmannedAircraftLimitedLiabilityPAILossCost` (2 rows) |
| Ownership/Operation modifier | `...BIPDRatingModifiers` (9 rows, 3 zero) | `...PAIRatingModifiers` (9 rows, 3 zero) |
| Primary Place of Operation modifier | `...BIPDRatingModifiers` (9 rows, 2 zero) | `...PAIRatingModifiers` (9 rows, 2 zero) |
| Usage modifier | `...BIPDRatingModifiers` (12 rows, 5 zero) | `...PAIRatingModifiers` (12 rows, 3 zero) |
| Deductible factor step | present (`SetDeductibleFactor`) | absent |
| Premium formula | `AdjustedRate x (ILF - DeductibleFactor) x ...` | `AdjustedRate x ILF x ...` (**(engine)** confirmed literal) |
| Total zero/RTC cells across both modifier axes + usage | ~~8~~ **10** (5 usage + 3 ownership + 2 place; **(engine)** re-counted from the table files) | 8 (3 + 3 + 2) — the 18 total matches "18 of 60" |
| Engine, 10 lb / aerial / owned / suburban / 1M agg (OK) | **316** | **216** |

Both coverages price **0** above 55 lb takeoff weight and share the LCM, claims-made multiplier
(unless NY), and ILF/deductible source tables borrowed from Premises/Operations.

---

## Endorsement forms (rating-adjacent, not filed rates)

Per `docs/rating-engine/A3-ENDORSEMENT-CATALOG.md` §"Rule 37 — Unmanned Aircraft (370)":

| Form | Endorsement | Role |
|---|---|---|
| `CG 21 09` | Exclusion Unmanned Aircraft Endorsement | `REFERENCED` |
| `CG 21 10` | Exclusion Unmanned Aircraft (Coverage A Only) Endorsement | `REFERENCED` |
| `CG 21 11` | Exclusion Unmanned Aircraft (Coverage B Only) Endorsement | `REFERENCED` |
| `CG 24 50` | Limited Coverage For Designated Unmanned Aircraft Endorsement | `REFERENCED` |
| `CG 24 51` | Limited Coverage For Designated Unmanned Aircraft (Coverage A Only) Endorsement | `REFERENCED` |
| `CG 24 52` | Limited Coverage For Designated Unmanned Aircraft (Coverage B Only) Endorsement | `REFERENCED` |
| `CG 24 55` | Unmanned Aircraft Endorsement | `REFERENCED` |
| `CG 29 60` | Exclusion Unmanned Aircraft Endorsement | `OPTIONAL_RTC` — refer to company for rating |
| `CG 34 20` | Limited Coverage For Designated Unmanned Aircraft Endorsement | `OPTIONAL_RTC` — refer to company for rating |
| `CG 34 21` | Exclusion Unmanned Aircraft Endorsement | `OPTIONAL_RTC` — refer to company for rating |
| `CG 34 22` | Limited Coverage For Designated Unmanned Aircraft Endorsement | `OPTIONAL_RTC` — refer to company for rating |

None of these forms carry their own rate build-up; the `REFERENCED` forms attach and describe the
coverage rated above, and the `OPTIONAL_RTC` forms are explicitly manual-referral, consistent with
manual C.1: *"For Unmanned Aircraft Exclusion options … refer to company for rating"*
(GATE-370-UNMANNED-AIRCRAFT.md §4 item 7).

---

## State deviations

Nine jurisdictions file drone rules; eight file an identical set (GATE-370-UNMANNED-AIRCRAFT.md §5):

| States | Rules/tables overridden |
|---|---|
| IN, MO, MT, ND, NH, OK, TN, UT | `SetAggregateLimit`, `SetILF`, `unmannedAircraftAggregateLimitLookup`, `LookupGovernmentalUnitsPremisesOperationsIncreasedLimitsFactor` |
| NY | `SetClaimsMadeMultiplier` |

The eight-state set is **one deviation** (a governmental-units increased-limits ILF variant),
replicated eight times, not eight distinct behaviors (§5, §8). NY is a repeat-offender jurisdiction
across this corpus for claims-made overrides (also seen in liquor and railroad).

Not resolved in source docs — the contents of `LookupGovernmentalUnitsPremisesOperationsIncreasedLimitsFactor`
and NY's substitute claims-made selector.

**(engine) Re-scanned 2026-10-02 across every state package on disk.** The eight-state governmental-units
set is unchanged. It is present in each state's 2027-04-01 editions (IN, ND V01–V04; MO, OK, NH, TN
V02+; MT, UT V03+), where `unmannedAircraftAggregateLimitLookup` drops out as in CW. NY's
`SetClaimsMadeMultiplier` override runs through NY 20260801 V01. Because NY has no 2027 package, it
resolves to that edition over CW 20260101 V01 even at 2027-04-01. GA and PR filed indicator-only
overrides in ≤ 2022 editions that are no longer current. **OK is one of the eight**: the engine
run above used OK's `SetILF` override with `GovernmentalSubdivision = "No"`, which falls through to
`LookupILFPremOps`.

Also: `UnmannedAircraftOwnershipAndOperationBIPDRatingModifiers` and
`UnmannedAircraftPrimaryPlaceOfOperationBIPDRatingModifiers` each carry a single state override —
Washington (WA), 1/51 (§5). All other rate tables on this subline are countrywide-only with 0/51
state filings.

---

## Supporting lookups

| Rule | Matrix | Keys | Notes |
|---|---|---|---|
| `LookupUnmannedAircraftLimitedLiabilityBIPDLossCost` | `UnmannedAircraftLimitedLiabilityBIPDLossCost` | State\|CW (0/51), weight ceiling band | 5 rows |
| `LookupUnmannedAircraftLimitedLiabilityPAILossCost` (name inferred from the BI/PD pattern; not stated verbatim in the gate doc) | `UnmannedAircraftLimitedLiabilityPAILossCost` | State\|CW (0/51), weight ceiling band | 2 rows — **name not resolved in source docs**, only the table name is given |
| `LookupPremOpsLCM` | (Prem/Ops LCM table) | — | CW value 1 |
| `LookupPremOpsClaimsMadeMultiplierAllOther` | (Prem/Ops claims-made table, "All Other" variant) | — | NY overrides the calling rule |
| `unmannedAircraftAggregateLimitLookup` | ~~(aggregate limit table)~~ **(engine)** none — string helper appending `" CSL"` | — | deleted in CW 20270401 |
| `LookupILFPremOps` | `ILFPremOps` | **(engine)** State, assignment 3, occurrence, aggregate | 15,857-char rule body; OK 1M/1M → 2.05 |
| `LookupDedFactorPremOpsCSL` / `...BI` / `...PD` | (Prem/Ops deductible tables) | **(engine)** chosen by BIPD / BI+PD / BI / PD deductible inputs (Step 12) | Coverage A only |
| `LookupUnmannedAircraftMinPremium` | `UnmannedAircraftMinPremium` | State, constant `Y` | **(engine)** 0; the lookup trips R19 on every drone policy |
| `LookupGovernmentalUnitsPremisesOperationsIncreasedLimitsFactor` | governmental-units ILF variant | not resolved | 8-state override |

---

## Quick reference — end-to-end, Coverage A (BI/PD)

```
Ceiling      = Convert<int>(round(MaximumTakeoffWeight + 0.499, 0))

LossCost     = lookup UnmannedAircraftLimitedLiabilityBIPDLossCost(weight band)   if Ceiling != 0
             | 0.0                                    (engine)                   otherwise

BaseRate     = round(LossCost x LCM x ClaimsMadeMultiplier, 3)
                                       (LCM = 1 CW; ClaimsMadeMultiplier = Prem/Ops "All Other",
                                        NY overrides the selector)

AdjustedRate = round(BaseRate x OwnershipAndOpMod x PrimaryPlaceOfOpMod x UsageMod, 3)
                                       (any of the three = 0  =>  REFER before use — engine rule,
                                        not an ERC guard; "Unknown" is a filed way to trigger it.
                                        (engine) R19, underwriting mode only, AFTER pricing at 0;
                                        also fires on the 0 min-premium lookup for every drone)

ILF          = ILFPremOps[State, 3, (A,A) if A<O else (O,A)]     (engine; " CSL" appended <= 20261001)

Premium      = round( AdjustedRate x (ILF - DeductibleFactor) x PackageModFactor
             x ExperienceRatingModificationFactor x ExpenseModification x ModToUse , 0)   (engine)
             (CW 20270401: 1 if that is 0 and AdjustedRate > 0)

                                       (basis: each unmanned aircraft, no /1000;
                                        MinPremium = 0 CW)
# engine, OK, 10 lb aerial/owned/suburban, 1M agg: 154.26 -> 154.260 -> 154.260 x 2.05 = 316.233 -> 316
```

## Quick reference — end-to-end, Coverage B (PAI)

```
Ceiling      = Convert<int>(round(MaximumTakeoffWeight + 0.499, 0))

LossCost     = lookup UnmannedAircraftLimitedLiabilityPAILossCost(weight band)    if Ceiling != 0
             | 0.0                                    (engine)                   otherwise

BaseRate     = round(LossCost x LCM x ClaimsMadeMultiplier, 3)

AdjustedRate = round(BaseRate x OwnershipAndOpMod(PAI) x PrimaryPlaceOfOpMod(PAI) x UsageMod(PAI), 3)
                                       (same REFER-on-zero rule as Coverage A)

Premium      = round( AdjustedRate x ILF x PackageModFactor
             x ExperienceRatingModificationFactor x ExpenseModification x ModToUse , 0)   (engine)

                                       (deductible term dropped — (engine) confirmed literal)
# engine, same drone: 87.63 -> 87.630 x 1.2 = 105.156 x 2.05 = 215.5698 -> 216
```

All intermediate rate products carry 3 decimal places per the gate doc's rule descriptions; premium
rounding: **(engine)** 0 dp (`Product DecimalPlaces=0`) in both coverages. Drone terrorism is a
separate group, `GeneralLiabilityUnmannedAircraftTerrorismCoverage`, on CovA + CovB. See
`Terrorism_RatingAlgorithms.md` (engine: 532 → **1** with the OK cap endorsement).

---
