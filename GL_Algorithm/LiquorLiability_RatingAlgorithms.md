# Liquor Liability — Rating Algorithms

**Source gate doc:** `docs/gates/GATE-332-LIQUOR-LIABILITY.md`
**Line:** General Liability (GL), subline 332, ISO Rule 45 *(Liquor Liability Coverage)*
**Derived against:** `GL_CW_20231201_V03` (the parent the OK golden case declares). `GL_CW_20260101_V01` is byte-identical to V03 for this coverage group — two live variants, not three, as of the gate's as-of date 2026-08-11. `GL_CW_20270401_V01` changes several steps (§ "What changes at 2027-04-01" below).
**Manual:** `GL-MU-2027-RU-001-C`, Rule 45, *Liquor Liability Coverage (Subline Code 332)*, pp. 93–103.
**Documented:** 2026-08-20

Liquor Liability is a single coverage/classification group — there is no multi-form split the way
Commercial Property's cause-of-loss forms split. All steps below live in one rule file,
`GeneralLiabilityClassificationLiquorCoverageRules.Rule.xml`, and run as one chain per classification
record.

The headline structural fact: **liquor has no loss-cost path.** `SetBaseRate` has no
`LossCost != 0` branch (compare 334/336, which do); it is unconditionally
`BaseRate = round(ELP x LCM, 3)`. The manual confirms this outright at Rule 45.E, p.95: *"For rates,
refer to company."* ISO publishes no liquor rate, by rule — the whole chain below is an
ELP-driven surrogate, not a filed rate.

---

## Master orchestration

Entry point is `ErcProcess` (per GATE-332-LIQUOR-LIABILITY.md § 1):

```
ErcProcess:
    if CoverageOnPolicyIndicator == 0:
        Premium = 0.0
        stop
    else:
        ErcSetRatesAndFactors
        ErcRate
        ErcSetStatisticalCodes
```

`ErcSetRatesAndFactors` runs steps 1–12 in order; `ErcRate` runs steps 13–16.

```
ErcSetRatesAndFactors:
    1  SetPremiumBasis
    2  SetELPOverride
    3  SetELP
    4  SetDeductibleFactorOverride
    5  SetLCM
    6  SetYearInClaimsMade
    7  SetClaimsMadeMultiplier
    8  SetBaseRate
    9  SetILF
    10 SetDeductibleFactor
    11 SetFinalILF
    12 SetFinalRate

ErcRate:
    13 SetMinimumPremium
    14 SetMinPremium
    15 SetPremium
    16 SetPremiumIndicator
```

Every write in this chain is wrapped in an `IsNull` guard, so a value supplied on the submission is
never overwritten (per GATE-332-LIQUOR-LIABILITY.md § 1).

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Rate build-up + premium, all steps | `GeneralLiabilityClassificationLiquorCoverageRules.Rule.xml` | `ErcSetRatesAndFactors` / `ErcRate` — no line numbers given in source gate doc |
| ELP rate table | `LiquorELP.RateTable.csv` (state-filed, 51/51) | — |
| ELP selector (not consumed by rating) | `LiquorELPText.RateTable.csv` (state-filed, 51/51) | — |
| ILF table | `ILFLiquor.RateTable.csv` (state-filed, 50/51) | Illinois overrides via `ILFLiquorStException` — see State deviations |
| Homogeneity index (purpose not traced in gate doc) | `LiquorHomogeneityIndex.RateTable.csv` (state-filed, 51/51) | Not resolved in source docs — no consuming rule identified |
| Liquor liability grade | `LiquorLiabGrade.RateTable.csv` (CW 7 rows / 16 at 2027; state 41/51) | Confirmed by manual 45.H.1/45.G, not traced to a specific `Set` rule in the gate's algorithm listing |
| Deductible factor | `DedFactorLiquor.RateTable.csv` (CW 21 rows, 0/51 state) | `LookupDedFactorLiquor`, step 10 |
| Loss cost multiplier | `LiquorLCM.RateTable.csv` (CW 1 row, 0/51 state) | `LookupLiquorLCM`, step 5 — see Escalation E15 |
| Minimum premium (shared with Prod/CompOps) | `ProdsCompldOpsMinPremium.RateTable.csv` (CW 3 rows, 0/51 state) | `LookupProdsCompldOpsMinPremium`, step 13, hardcoded `ILTA = "C"` |
| Claims-made multiplier (shared with Prod/CompOps) | `ProdsCompldOpsClaimsMadeMultiplier.RateTable.csv` (CW 5 rows) | `LookupProdsCompldOpsClaimsMadeMultiplier(min(year,5))`, step 7 |
| Class code table (found outside gate doc) | `ClassCodeLiquor` — 2,300 rows | per `docs/rating-engine/03-RATING-STRUCTURE.md` line 335; not traced to a specific step in the gate doc |
| Territory table (found outside gate doc, not in gate's algorithm) | `LiquorLiabTerritory` | per `docs/rating-engine/03-RATING-STRUCTURE.md` line 541 — **not resolved in source docs**: the gate doc's traced rule chain (steps 1–16) has no territory-keyed step, so how/whether this table enters the chain is unresolved |
| Uncalled lookups (ship with the file but have no caller) | `LookupNoDedStatCode`, `LookupPremOpsLCM` | per GATE-332-LIQUOR-LIABILITY.md § 3 (E14/OI-38 pattern) |
| CW 2027 stat-code defect | `GL_CW_20270401_V01`, `SetLiquorExposureStatCode` | per GATE-332-LIQUOR-LIABILITY.md § 4 (OI-43) |

> Note: `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` (§ 3.2.3) additionally describes a
> **Liquor ILF table filed as a separate Rule 56.B table only in IL, MN, UT**, elsewhere flagged as a
> gap. This does not match the gate doc's own direct read of the ERC data (§ 6: `ILFLiquor` populated
> in 50/51 jurisdictions, with Illinois alone overriding under a different table name/key arity). Both
> statements are reproduced here rather than silently reconciled — the gate doc is the more recent,
> directly-verified source (2026-08-11) and should be treated as authoritative where the two disagree.

---

## Liquor Liability — rate build-up

Executed in order by `ErcSetRatesAndFactors` (per GATE-332-LIQUOR-LIABILITY.md § 1):

### Step 1 — Premium basis
`SetPremiumBasis`

```
PremiumBasis = ../LiquorPremiumBasis, else ""
```

### Step 2 — ELP override
`SetELPOverride`

```
ELPOverride = ../LiquorELPOverride, else 0.0
```

### Step 3 — Expected loss potential (ELP)
`SetELP`

```
if LiquorClassDescription is non-empty and LiquorClassCode is non-empty:
    ELP = LookupLiquorELP        if ELPOverride == 0.0
        | ELPOverride            otherwise
else:
    ELP = 0.0
```

`LookupLiquorELP` reads matrix `LiquorELP`, a state-filed table (0 rows CW, 51/51 states, 362 rows
total). Companion selector `LiquorELPText` carries exactly two values corpus-wide — `Industry` (251
rows, ELP > 0) and `Company` (111 rows, ELP = 0) — 100% agreement, but `LiquorELPText` is written to
the classification output and **read by no rating rule downstream** (per GATE-332-LIQUOR-LIABILITY.md
§ 0).

### Step 4 — Deductible factor override
`SetDeductibleFactorOverride`

```
DeductibleFactorOverride = ../LiquorDedFactorOverride, else 0.0
```

### Step 5 — Loss cost multiplier
`SetLCM`

```
LCM = LookupLiquorLCM
```

`LiquorLCM` is countrywide, one row, value `1` (per GATE-332-LIQUOR-LIABILITY.md § 3, Escalation E15).
No state overrides anywhere, at any edition. See Escalations, below.

### Step 6 — Year in claims-made
`SetYearInClaimsMade`

```
if LiquorCoverageForm == "Claims Made":
    YearInClaimsMade = policy value
else:
    YearInClaimsMade = 0
```

### Step 7 — Claims-made multiplier
`SetClaimsMadeMultiplier`

```
if LiquorCoverageForm == "Claims Made":
    ClaimsMadeMultiplier = LookupProdsCompldOpsClaimsMadeMultiplier(min(YearInClaimsMade, 5))
else:
    ClaimsMadeMultiplier = 1.0
```

Reuses the Products/Completed Operations claims-made multiplier table — confirmed intentional by
manual 45.J.3, p.102, which directs the reader to "Products/Completed Operations Deductible Discount
Factors … Rule 15., Table 15.E.6."

### Step 8 — Base rate
`SetBaseRate`

```
if LiquorCoverageForm == "Occurrence":
    BaseRate = round(ELP x LCM, 3)
elif LiquorCoverageForm == "Claims Made":
    BaseRate = round(ELP x LCM x ClaimsMadeMultiplier, 3)
else:
    BaseRate = 0.0
```

**No loss-cost branch exists in this rule at all** — the defining structural fact of liquor rating
(per GATE-332-LIQUOR-LIABILITY.md § 0).

### Step 9 — Increased limits factor (ILF)
`SetILF`

```
if LiquorClassDescription, EachCommonCauseLimit, and AggregateLimit are all non-empty:
    ILF = LookupILFLiquor
else:
    ILF = 0.0
```

`LookupILFLiquor` reads matrix `ILFLiquor`, keyed on `(State, EachCommonCauseLimit, AggregateLimit)`.
**Illinois overrides this to read `ILFLiquorStException` (5 rows) keyed on `AggregateLimit` alone** —
a different table name *and* a different key arity (per GATE-332-LIQUOR-LIABILITY.md § 6).

### Step 10 — Deductible factor
`SetDeductibleFactor`

```
if LiquorClassDescription and LiquorDeductible are both non-empty:
    DeductibleFactor = LookupDedFactorLiquor    if no override
                      | DeductibleFactorOverride otherwise
else:
    DeductibleFactor = 0.0
```

`DedFactorLiquor` publishes 21 deductible options countrywide, **all with factor `0`** — confirmed
deliberate by manual 45.J.3, p.102: deductible discount factors "must be referred to the company
before using." See § "Refer-to-company triggers" below for the guard-coverage gap.

### Step 11 — Final ILF
`SetFinalILF`

```
FinalILF = round(ILF - DeductibleFactor, 3)
```

### Step 12 — Final rate
`SetFinalRate`

```
FinalRate = round(
    BaseRate
  x FinalILF
  x PackageModFactor
  x ExperienceRatingModificationFactor
  x ExpenseModification
  x ModToUse
, 3)
```

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse` are
policy-level inputs; per GATE-332-LIQUOR-LIABILITY.md § 5, if any is absent it resolves to `0.0` via
`FirstValue`, which zeroes `FinalRate` — "a missing policy modifier zeroes the premium."

---

## Liquor Liability — premium

Executed by `ErcRate` (per GATE-332-LIQUOR-LIABILITY.md § 1):

### Minimum premium (steps 13–14)
`SetMinimumPremium`:

```
if Subline == "Liquor":
    MinimumPremium = LookupProdsCompldOpsMinPremium(ILTA = "C")    # hardcoded
else:
    MinimumPremium = 0.0
```

`ProdsCompldOpsMinPremium` publishes `A/B/C = 0, 0, 0` countrywide, no state overrides — the minimum
premium is structurally zero for every liquor risk today (Escalation E16). CW 2027 deletes both
`SetMinimumPremium` and `SetMinPremium` outright and empties the table.

`SetMinPremium`:

```
if Subline == "Liquor" and MiscIfAnyBasis == "No":
    MinPremium = round(MinimumPremium x FinalILF, 0)
else:
    MinPremium = 0.0
```

### Gate — `SetPremium` (step 15)

Three nested guards, all-or-nothing:

```
SetPremium:
    if Subline != "Liquor":
        Premium = 0.0
    elif PremiumBasis is empty or PremiumBasis == "Refer To Co.":
        Premium = 0.0                    # a referral, not a price
    else:
        # fall through to Branch A or B below
```

The `Subline == "Liquor"` guard is dropped entirely in CW 2027 (per GATE-332-LIQUOR-LIABILITY.md
§ "What changes at 2027-04-01").

### Branch A — divisor bases

Applies when `PremiumBasis` is one of `Admissions`, `Area`, `Gallons`, `Gross Sales`,
`Passenger Days`, `Payroll`, `Total Cost`, `Total Operating Expenses`, `Vehicles`:

```
Premium = round(FinalRate x LiquorExposure / 1000, 0)
```

### Branch B — unit bases

Otherwise (any other non-empty, non-referral `PremiumBasis`):

```
Premium = round(FinalRate x LiquorExposure, 0)
```

### Premium indicator (step 16)
`SetPremiumIndicator` — per GATE-332-LIQUOR-LIABILITY.md § 1, structurally identical to the other
sublines' indicator pattern (no separate detail given in the gate doc).

---

## What changes at 2027-04-01

Per GATE-332-LIQUOR-LIABILITY.md § 1:

| Change | Detail |
|---|---|
| Minimum premium withdrawn | `SetMinPremium` and `SetMinimumPremium` deleted; `ProdsCompldOpsMinPremium` goes to 0 rows. `ErcRate` drops to `SetPremium` → `SetPremiumIndicator` |
| `$1` floor arrives | If calculated premium rounds to `0` but `LiquorExposure > 0` → `Premium = 1.0` (same floor 334/335 found in CW 2027) |
| Premium-basis vocabulary replaced | 9 generic bases → 2 rateable (`Gross Sales of Alcoholic Beverages`, `Gross Sales of Food and Beverages`, both ÷1000) plus `Each License` / `Each Licensed Location` / `Each Self-serve Station` (×units) and `Refer to Company` |
| `Subline == "Liquor"` guard dropped | from `SetPremium` |
| `SetELP` loosens | drops the `LiquorClassDescription` condition; keys on `LiquorClassCode` alone |
| Rule count | 48 rules, not 50; 5 of the surviving 48 have different bodies |

**Known CW 2027 defect (OI-43).** `SetLiquorExposureStatCode` in `GL_CW_20270401_V01` still tests the
pre-2027 vocabulary (`"Gross Sales"`, `"Each"`, `"Refer To Co."`), none of which can match 2027 data.
Net effect: the divisor falls to 1 instead of 1000 on the two Gross Sales bases, so the reported
statistical exposure is 1,000x too large. **Premium is unaffected** — `SetPremium` was updated to the
new vocabulary in the same edition; only the statistical-code rule was not (per
GATE-332-LIQUOR-LIABILITY.md § 4). Reported as an observation on ISO's filed artifact, not corrected
in the engine.

---

## State deviations

Only 8 of 51 jurisdictions file any `GeneralLiabilityClassificationLiquorCoverage` rule — CT, IA, IL,
MA, MI, MN, NC, NY (31 rules total; per GATE-332-LIQUOR-LIABILITY.md § 7):

| Rule overridden | States |
|---|---|
| `InitializeRuleSet`, `ErcProcess` | all 8 |
| `SetCoverageStatCode` | 6 |
| `SetILF` | 2 |
| `LookupILFLiquor`, `LookupILFLiquorWithSubLimit`, `LookupPolicyLimitsLiquorStatCode`, `SetLimitStatCode` | IL |
| `SetYearInClaimsMade`, `SetClaimsMadeMultiplier`, `SetBaseRate` | NY |

**New York disables claims-made liquor.** `SetBaseRate` requires `LiquorCoverageForm == "Occurrence"`
and returns `0.0` otherwise; `SetYearInClaimsMade` and `SetClaimsMadeMultiplier` are replaced by
constant stubs (`0` and `1.0`). A claims-made liquor submission in NY silently produces
`BaseRate = 0` → `Premium = 0`, with no message or referral.

---

## Refer-to-company triggers

Per GATE-332-LIQUOR-LIABILITY.md § 8:

| # | Trigger | Mechanism | Guarded in ERC? |
|---|---|---|---|
| 1 | `LiquorELPText == "Company"` → published ELP of `0` | N17 selector, 111 rows | Yes — in-corpus discriminator |
| 2 | `PremiumBasis == "Refer To Co."` / `"Refer to Company"` | explicit test in `SetPremium` | Yes, but edition-scoped (Escalation E17 — the sentinel string changes at the 2027 cliff) |
| 3 | Any liquor deductible | all 21 `DedFactorLiquor` factors are `0`; Rule 45.J.3 requires referral | Partially — see below |
| 4 | `LCM == 1` | the unsupplied company multiplier | No discriminator (Escalation E15) |
| 5 | Rule 45.E — all liquor rates | none in ERC | Manual-only |

**Deductible guard gap (OI-44).** `DoMessageMustEnterLiquorDeductibleFactorOverride` fires for only
10 of the 21 zero deductible options — every "Per Claim" option. The other 11 (all ten "Per Common
Cause" options, plus "No Deductible") are zero and unguarded. "No Deductible" is legitimately zero;
the other ten are not. A liquor risk written with, say, "5,000 Per Common Cause" receives a
deductible factor of `0` with no error message — priced as though it had no deductible.

---

## Escalations

Per GATE-332-LIQUOR-LIABILITY.md § 3:

| # | Issue | Engine treatment |
|---|---|---|
| E15 | `LiquorLCM = 1` is a placeholder for a company input, not a rate — one CW row, no state override at any edition | Treat a resolved `LCM` of exactly `1` as REFER, not as a factor |
| E16 | The liquor minimum premium is structurally zero (`ProdsCompldOpsMinPremium` = 0/0/0 CW, no state overrides) | Apply `0` as ERC writes it; do not substitute the manual's policywriting minimum (Rule 45.I.9) — that would be tier-2 sourcing |
| E17 | The refer sentinel's spelling is edition-scoped — `"Refer To Co."` pre-2027, `"Refer to Company"` in CW 2027, both live simultaneously at the 2027-04-01 cliff | No global sentinel constants; resolve every sentinel string from the same package as the rule that tests it |

---

## Inputs consumed, and what happens when one is absent

Per GATE-332-LIQUOR-LIABILITY.md § 5:

| Input | Level | Absent → |
|---|---|---|
| `CoverageOnPolicyIndicator` | coverage | `0` → `Premium = 0.0`, no rating |
| `Subline` | policy | ≠ `"Liquor"` → `Premium = 0.0` (CW 2023 only; guard dropped in 2027) |
| `LiquorClassCode` | classification | empty → `ELP = 0.0` → `BaseRate = 0` |
| `LiquorClassDescription` | classification | empty → `ELP = 0.0`, `ILF = 0.0`, `DeductibleFactor = 0.0`. Dropped from `SetELP` in 2027 |
| `LiquorPremiumBasis` | classification | empty → `Premium = 0.0`. Refer values → `Premium = 0.0` (a referral, not a price) |
| `LiquorExposure` | classification | absent → `0` via `FirstValue` → `Premium = 0` |
| `LiquorCoverageForm` | policy | absent → `BaseRate = 0.0`. Must be `Occurrence` or `Claims Made` |
| `EachCommonCauseLimit`, `AggregateLimit` | policy | either empty → `ILF = 0.0` → `FinalRate = 0` |
| `LiquorDeductible` | classification | empty → `DeductibleFactor = 0.0` |
| `YearInClaimsMade` | policy | absent on claims-made → `0` → multiplier `1.0` (first-year pricing silently applied) |
| `LiquorELPOverride`, `LiquorDedFactorOverride` | classification | `0.0` → use the table |
| `MiscIfAnyBasis` | classification | ≠ `"No"` → `MinPremium = 0.0` |
| `PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse` | policy | absent → `0.0` via `FirstValue` → `FinalRate = 0` |

Eight distinct absent-input paths reach `Premium = 0` with no message — the largest silent-zero
surface of any subline gated to date, a direct consequence of liquor having no second (loss-cost)
route to a premium.

---

## Manual confirmations

Per GATE-332-LIQUOR-LIABILITY.md § 2, all from `GL-MU-2027-RU-001-C` Rule 45, pp. 93–103. None of
these sources a value; each confirms something already present in ERC:

| # | ERC artifact | Manual | Verdict |
|---|---|---|---|
| 1 | No liquor loss-cost table anywhere; `BaseRate = ELP x LCM` | 45.E, p.95: "For rates, refer to company." | Confirms the whole rating chain — ISO publishes no liquor rate by rule |
| 2 | `DedFactorLiquor` all-21-zero | 45.J.3, p.102: deductible factors "must be referred to the company before using" | The zeros are deliberate |
| 3 | Liquor reuses `ProdsCompldOpsMinPremium` and `...ClaimsMadeMultiplier` | 45.J.3, p.102 directs to Rule 15, Table 15.E.6 | Cross-subline reuse is intended |
| 4 | `Premium = FinalRate x Exposure / 1000` on Gross Sales bases | 45.G, p.96: "Gross Sales of Alcoholic Beverages — per $1,000 gross sales" | Confirms the ÷1000 |
| 5 | `Refer to Company` as a premium-basis value | 45.G, p.96, class 50941: "Premium Base: Refer to company" | Confirms a refer marker occupying a data field |
| 6 | 16 new class codes at the cliff | 45.G, pp.96–101 lists exactly 50941–50957 | Set-exact |
| 7 | `LiquorLiabGrade = 0` x16 countrywide | 45.H.1, p.101: Grade 0 = "no cause of action against one who supplies … liquor" | A genuine zero |
| 8 | CW grades all `0`; 41 states file their own | 45.G, p.96, every class: "Liquor Liability Grade: Refer to state exceptions" | CW zeros are placeholders |
| 9 | `SetFinalILF = ILF - DeductibleFactor`; premium = rate x units | 45.I.5–I.6, pp.101–102 | Confirms the chain shape |

**Not in ERC's liquor chain at all.** Rule 45.I.9, p.102 describes a policy-level "policywriting
minimum premium" (use the greater of computed premium or the policywriting minimum). ERC's
`MinPremium` is classification-level and computes to `0`. These are different objects — the manual's
policywriting minimum belongs to policy assembly, out of scope here.

---

## Supporting lookups

| Rule | Matrix | Keys | Note |
|---|---|---|---|
| `LookupLiquorELP` | `LiquorELP` | State, `LiquorClassCode`/`LiquorClassDescription` (exact key list not given in gate doc) | State-filed only, 0 CW rows |
| `LookupLiquorLCM` | `LiquorLCM` | State\|CW | CW value `1`, no state overrides |
| `LookupILFLiquor` | `ILFLiquor` | State, `EachCommonCauseLimit`, `AggregateLimit` | Illinois override: `ILFLiquorStException`, keyed on `AggregateLimit` alone |
| `LookupDedFactorLiquor` | `DedFactorLiquor` | State\|CW | CW: 21 options, all `0` |
| `LookupProdsCompldOpsMinPremium` | `ProdsCompldOpsMinPremium` | `ILTA` (hardcoded `"C"`) | CW: 3 rows, all `0` |
| `LookupProdsCompldOpsClaimsMadeMultiplier` | `ProdsCompldOpsClaimsMadeMultiplier` | `min(YearInClaimsMade, 5)` | CW: 5 rows, shared with Products/Completed Operations |
| `LookupNoDedStatCode` | — | — | Ships with the file, no caller (per GATE-332-LIQUOR-LIABILITY.md § 3) |
| `LookupPremOpsLCM` | `PremOpsLCM` | — | Ships with the file, no caller; table content identical in shape to `LiquorLCM` per § 6 |

Every lookup in this ruleset follows the same two-pass `FirstNonNull(state row, "CW" row)` pattern
(per GATE-332-LIQUOR-LIABILITY.md § 6, "N16, confirmed a fourth time").

---

## Quick reference — end-to-end

```
ELP           = lookup LiquorELP(State, ClassCode, ClassDescription)   if ELPOverride == 0
              | ELPOverride                                            otherwise
              | 0.0    if ClassDescription or ClassCode blank

LCM           = lookup LiquorLCM(State|CW)                             [CW = 1, a placeholder]

ClaimsMadeMult = lookup ProdsCompldOpsClaimsMadeMultiplier(min(YearInClaimsMade,5))  if Claims Made
              | 1.0                                                    if Occurrence

BaseRate      = round(ELP x LCM, 3)                                    if Occurrence
              | round(ELP x LCM x ClaimsMadeMult, 3)                   if Claims Made
              | 0.0                                                    otherwise

ILF           = lookup ILFLiquor(State, EachCommonCauseLimit, AggregateLimit)
              | 0.0    if ClassDescription, EachCommonCauseLimit, or AggregateLimit blank

DeductibleFactor = lookup DedFactorLiquor(State|CW)   [CW: all 21 options = 0]
              | override                              if DeductibleFactorOverride != 0
              | 0.0                                   if ClassDescription or LiquorDeductible blank

FinalILF      = round(ILF - DeductibleFactor, 3)

FinalRate     = round(BaseRate x FinalILF x PackageMod x ExperienceRatingMod
                       x ExpenseMod x ModToUse, 3)

MinPremium    = round(lookup ProdsCompldOpsMinPremium(ILTA="C") x FinalILF, 0)
                if Subline == "Liquor" and MiscIfAnyBasis == "No"
              | 0.0   otherwise

Premium       = 0.0                                    if Subline != "Liquor"
              | 0.0                                    if PremiumBasis blank or "Refer To Co."
              | round(FinalRate x LiquorExposure / 1000, 0)   if PremiumBasis in divisor-basis set
              | round(FinalRate x LiquorExposure, 0)          otherwise
```

Everything above is exactly what the gate doc traced for CW 2023 V03 / CW 2026 V01. At 2027-04-01,
apply the deltas in "What changes at 2027-04-01" above (minimum premium removed, `$1` floor added,
`Subline` guard dropped, premium-basis vocabulary replaced).

---
