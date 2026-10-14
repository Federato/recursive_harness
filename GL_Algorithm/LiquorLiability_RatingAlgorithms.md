# Liquor Liability — Rating Algorithms

**Source gate doc:** `docs/gates/GATE-332-LIQUOR-LIABILITY.md`
**Line:** General Liability (GL), subline 332, ISO Rule 45 *(Liquor Liability Coverage)*
**Derived against:** `GL_CW_20231201_V03` (the parent the OK golden case declares). `GL_CW_20260101_V01` is byte-identical to V03 for this coverage group — two live variants, not three, as of the gate's as-of date 2026-08-11. `GL_CW_20270401_V01` changes several steps (§ "What changes at 2027-04-01" below). Since then two CW editions arrived and were checked 2026-10-02: `GL_CW_20261001_V01` (OK's parent as of 2026-10-02) is byte-identical to V03/20260101 for the liquor rule file, and `GL_CW_20270401_V02` is byte-identical to `GL_CW_20270401_V01`. CA's parent `GL_CW_20231201_V02` differs from V03 only in lacking the `IsNull` override guards.
**Manual:** `GL-MU-2027-RU-001-C`, Rule 45, *Liquor Liability Coverage (Subline Code 332)*, pp. 93–103.
**Documented:** 2026-08-20
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — ISO's AL and IL Liquor STC submissions re-dated and rated offline by the kernel (strict and `underwriting` mode) at 2026-10-02 (AL over CW 20260101 V01; IL over CW 20260101 V01) and 2027-04-01 (over CW 20270401 V02), plus Company-class, claims-made, refer-basis and 2027-vocabulary variants; rule XML diffed per edition; tables censused across all 51 resolved jurisdictions.

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

`ErcSetRatesAndFactors` runs steps 1–12 in order; `ErcRate` runs steps 13–16 (confirmed by engine
trace, AL@2026-10-02). Which edition runs is chosen by the resolved parent as of the effective date
(a submission variable, decision A3; `package_version` pins one): all 51 jurisdictions run this chain
as of 2026-10-02; as of 2027-04-01, 46 run the CW 2027 variant (8 over `GL_CW_20270401_V01`, 38 over
`V02`) and CA, GA, NJ, NY, WA still run this one.

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
never overwritten (per GATE-332-LIQUOR-LIABILITY.md § 1) — except under CA's parent
`GL_CW_20231201_V02`, whose versions of `SetBaseRate`, `SetILF`, `SetDeductibleFactor`,
`SetFinalILF`, `SetFinalRate` and the minimum-premium rules lack the guards (rule diff 2026-10-02).

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Rate build-up + premium, all steps | `GeneralLiabilityClassificationLiquorCoverageRules.Rule.xml` | `ErcSetRatesAndFactors` / `ErcRate` — no line numbers given in source gate doc |
| ELP rate table | `LiquorELP.RateTable.csv` (state-filed, 51/51) | — |
| ELP selector (not consumed by the rate chain; consumed by ISO's refer message) | `LiquorELPText.RateTable.csv` (state-filed, 51/51) | `GeneralLiabilityClassificationRules.SetLiquorELP` writes it to the classification; `DoMessageMustEnterEstimatedLossPotentialFactorOverride` reads it (→ engine R29) |
| ILF table | `ILFLiquor.RateTable.csv` (state-filed, 50/51) | Illinois overrides via `ILFLiquorStException` — see State deviations |
| Homogeneity index | `LiquorHomogeneityIndex.RateTable.csv` (state-filed, 51/51) | `GeneralLiabilityClassificationRules.SetLiquorHomogeneityIndex` — written to the classification, no premium effect |
| Liquor liability grade | `LiquorLiabGrade.RateTable.csv` (CW 7 rows / 16 at 2027; 44 states declare it, 41 with rows) | `GeneralLiabilityClassificationRules.SetLiquorLiabGrade` (engine trace: AL `70412` → `5`, `50911` → `0`) — written to the classification, **not read by the liquor rate chain** |
| Deductible factor | `DedFactorLiquor.RateTable.csv` (CW 21 rows, 0/51 state) | `LookupDedFactorLiquor`, step 10 |
| Loss cost multiplier | `LiquorLCM.RateTable.csv` (CW 1 row, 0/51 state) | `LookupLiquorLCM`, step 5 — see Escalation E15 |
| Minimum premium (shared with Prod/CompOps) | `ProdsCompldOpsMinPremium.RateTable.csv` (CW 3 rows, 0/51 state) | `LookupProdsCompldOpsMinPremium`, step 13, hardcoded `ILTA = "C"` |
| Claims-made multiplier (shared with Prod/CompOps) | `ProdsCompldOpsClaimsMadeMultiplier.RateTable.csv` (CW 5 rows) | `LookupProdsCompldOpsClaimsMadeMultiplier(min(year,5))`, step 7 |
| Class code domain (found outside gate doc) | `DomainClassCodeLiquor.DomainTable.csv` (+ `DomainClassDescriptionByClassCodeLiquor`) — a **domain** (validation) table, not a rate table | Resolved 2026-10-02: no rate table named `ClassCodeLiquor` exists in any resolved package; nothing in steps 1–16 reads it |
| Territory (found outside gate doc) | `LiquorLiabTerritory` | Resolved 2026-10-02: a DataDef field only — no rate table by that name in any resolved package, and no step reads it |
| Uncalled lookups (ship with the file but have no caller) | `LookupNoDedStatCode`, `LookupPremOpsLCM` | per GATE-332-LIQUOR-LIABILITY.md § 3 (E14/OI-38 pattern) |
| CW 2027 stat-code defect | `GL_CW_20270401_V01`, `SetLiquorExposureStatCode` | per GATE-332-LIQUOR-LIABILITY.md § 4 (OI-43) |

> Note: `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` (§ 3.2.3) additionally describes a
> **Liquor ILF table filed as a separate Rule 56.B table only in IL, MN, UT**, elsewhere flagged as a
> gap. This does not match the gate doc's own direct read of the ERC data (§ 6: `ILFLiquor` populated
> in 50/51 jurisdictions, with Illinois alone overriding under a different table name/key arity). Both
> statements are reproduced here rather than silently reconciled — the gate doc is the more recent,
> directly-verified source (2026-08-11) and should be treated as authoritative where the two disagree.
> **Engine census 2026-10-02 agrees with the gate doc:** `ILFLiquor` is populated in 50/51 resolved
> states (3,531 rows) at both 2026-10-02 and 2027-04-01; IL rates through `ILFLiquorStException`, and MN
> overrides `SetILF` through `LookupILFLiquorWithSubLimit`.

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

`LookupLiquorELP` reads matrix `LiquorELP`, keyed (State\|CW, `LiquorClassCode`), a state-filed
table (0 rows CW, 51/51 states, 362 rows total as of 2026-10-02; 771 as of 2027-04-01). Companion
selector `LiquorELPText` carries exactly two values corpus-wide — `Industry` (251 rows, ELP > 0) and
`Company` (111 rows, ELP = 0) — 100% agreement (engine census 2026-10-02; 485 / 286 as of
2027-04-01, still 100%). `LiquorELPText` is read by no step of the **rate chain**, but it is not
inert: ISO's `GeneralLiabilityClassificationRules.DoMessageMustEnterEstimatedLossPotentialFactorOverride`
raises *"Must enter Estimated Loss Potential Override"* when `Subline = "Liquor"`,
`LiquorELP = "Company"`, `MiscIfAnyBasis = "No"` and no `LiquorELPOverride` is supplied. The rating
still completes at ELP `0`; in `underwriting` mode the engine turns the message into referral
**R29**. Confirmed AL@2026-10-02, class `58166` (Company): premium `0`, R29 raised.

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
Factors … Rule 15., Table 15.E.6." Engine AL@2026-10-02, claims-made year 2: `['CW', 2] → 0.64`,
`BaseRate = round(1.72 x 1 x 0.64, 3) = 1.101`. NY declares its own empty copy of the table
(consistent with its claims-made stubs, below).

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

`LookupILFLiquor` reads matrix `ILFLiquor`, keyed on `(State|CW, EachCommonCauseLimit, AggregateLimit)`
(policy-level fields). **Illinois overrides this to read `ILFLiquorStException` (5 rows) keyed on
`AggregateLimit` alone** — a different table name *and* a different key arity (per
GATE-332-LIQUOR-LIABILITY.md § 6; engine IL@2026-10-02: `['IL', '200,000'] → 0.97`). **Minnesota also
overrides `SetILF`**, via its own `LookupILFLiquorWithSubLimit`. Liquor limit values carry no `" CSL"`
suffix in any edition (AL key `['AL', '1,000,000', '2,000,000']` at both 2026-10-02 and 2027-04-01;
factor `1.85` → `1.98`), so the 2027 suffix change (OI-96/97) does not reach this lookup.

### Step 10 — Deductible factor
`SetDeductibleFactor`

```
if LiquorClassDescription and LiquorDeductible are both non-empty:
    DeductibleFactor = LookupDedFactorLiquor    if no override
                      | DeductibleFactorOverride otherwise
else:
    DeductibleFactor = 0.0
```

`DedFactorLiquor` (keyed State\|CW, `LiquorDeductible`) publishes 21 deductible options
countrywide, **all with factor `0`** — confirmed deliberate by manual 45.J.3, p.102: deductible
discount factors "must be referred to the company before using." See § "Refer-to-company triggers"
below for the guard-coverage gap.

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
`FirstValue`, which zeroes `FinalRate` — "a missing policy modifier zeroes the premium." (Confirmed
in rule XML; unchanged at CW 2027.)

**Engine worked example** (AL STC `STC_GL000092157` re-dated, AL@2026-10-02, `GL_AL_20260701_V01`
over `GL_CW_20260101_V01`), class `70412` Clubs, Occurrence, No Deductible, Gross Sales 200,000:
`ELP 1.72 → BaseRate 1.720; ILF 1.85, DeductibleFactor 0 → FinalILF 1.850; FinalRate
round(1.72 x 1.85, 3) = 3.182; Premium round(3.182 x 200,000 / 1000, 0) = 636`. The other three
classes on that submission rate `95`, `621`, `2,915`.

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
premium is structurally zero for every liquor risk today (Escalation E16; engine lookup
`['CW', 'C'] → 0`). CW 2027 deletes both `SetMinimumPremium` and `SetMinPremium` outright and
empties the table.

`MinPremium` is **not** read by `SetPremium`. It feeds the policy-level
`GeneralLiabilityLiquorPremiumToReachMinCoverage`, which adds `max(0, max MinPremium − Σ classification
Premium)` (only when `PackagePolicy`/`multistate` are blank and some classification has
`MiscIfAnyBasis = "No"`); that top-up is `0` today (AL@2026-10-02: `CoveragePremium 4,267`, top-up
`0`) and its rating rules are deleted at CW 2027.

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
| `$1` floor arrives | If calculated premium rounds to `0` but `LiquorExposure > 0` → `Premium = 1.0` (same floor 334/335 found in CW 2027). **The floor also catches the referral paths:** a blank or `"Refer to Company"` basis computes `0` and, with exposure > 0, is priced at `1.0` — not `0` as in CW 2023/2026 (engine AL@2027-04-01, class `50941`: `Premium 1`, R03 + R29 raised in `underwriting` mode) |
| Premium-basis vocabulary replaced | 9 generic bases → 2 rateable (`Gross Sales of Alcoholic Beverages`, `Gross Sales of Food and Beverages`, both ÷1000) plus `Each License` / `Each Licensed Location` / `Each Self-serve Station` (×units) and `Refer to Company` |
| `Subline == "Liquor"` guard dropped | from `SetPremium` |
| `SetELP` loosens | drops the `LiquorClassDescription` condition; keys on `LiquorClassCode` alone |
| `SetILF`, `SetDeductibleFactor` regate | their outer test moves from `LiquorClassDescription` to `LiquorClassCode` (rule diff; missing from the gate's list) |
| Old vocabulary under the new rule | a pre-2027 basis such as `"Gross Sales"` is neither rateable 2027 basis, so it falls to the **×units** branch (no ÷1000) — a 1,000× premium if the class still had an ELP. In practice the retired classes have no 2027 ELP row and land on the `$1` floor (AL@2027-04-01, all four ISO-STC classes: `1` each) |
| Rule count | 48 rules, not 50; 5 of the surviving 48 have different bodies (`ErcRate`, `SetDeductibleFactor`, `SetELP`, `SetILF`, `SetPremium` — rule diff 2026-10-02) |

**Engine worked example, CW 2027** (AL@2027-04-01, `GL_AL_20270401_V06` over `GL_CW_20270401_V02`):
class `50943`, basis `Gross Sales of Alcoholic Beverages`, exposure 200,000 →
`ELP 1.72; ILF 1.98 → FinalILF 1.980; FinalRate round(3.4056, 3) = 3.406; Premium round(3.406 x 200, 0) = 681`.

> **Engine finding.** A class that is retired or unfiled in the resolved 2027 state table writes
> `ELP = None` and is priced at the `$1` floor. Liquor has no `*LossCost` node, so the kernel's OI-94
> refusal cannot fire, and no referral fires either (IL@2027-04-01, class `50911`: premium `1`).

**Known CW 2027 defect (OI-43).** `SetLiquorExposureStatCode` in `GL_CW_20270401_V01` (and in the byte-identical `V02`) still tests the
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
| `SetILF` | 2 (IL, MN) |
| `LookupILFLiquor`, `LookupPolicyLimitsLiquorStatCode`, `SetLimitStatCode` | IL |
| `LookupILFLiquorWithSubLimit` | MN |
| `SetYearInClaimsMade`, `SetClaimsMadeMultiplier`, `SetBaseRate` | NY |

Re-confirmed 2026-10-02 against the state packages the engine resolves as of 2026-10-02 and
2027-04-01 (identical at both dates). The gate's table put `LookupILFLiquorWithSubLimit` under IL; it
is Minnesota's.

**New York disables claims-made liquor.** `SetBaseRate` requires `LiquorCoverageForm == "Occurrence"`
and returns `0.0` otherwise; `SetYearInClaimsMade` and `SetClaimsMadeMultiplier` are replaced by
constant stubs (`0` and `1.0`). A claims-made liquor submission in NY silently produces
`BaseRate = 0` → `Premium = 0`, with no message or referral.

---

## Refer-to-company triggers

Per GATE-332-LIQUOR-LIABILITY.md § 8:

| # | Trigger | Mechanism | Guarded in ERC? | Engine, `underwriting` mode (2026-10-02) |
|---|---|---|---|---|
| 1 | `LiquorELPText == "Company"` → published ELP of `0` | N17 selector, 111 rows | Yes — ISO's ELP-override message | **R29** raised (AL `58166`) |
| 2 | `PremiumBasis == "Refer To Co."` / `"Refer to Company"` | explicit test in `SetPremium` | Yes, but edition-scoped (Escalation E17 — the sentinel string changes at the 2027 cliff) | **R03** raised (the sentinel reaches the rated tree); premium `0` pre-2027, `1` at CW 2027 |
| 3 | Any liquor deductible | all 21 `DedFactorLiquor` factors are `0`; Rule 45.J.3 requires referral | Partially — see below | **R14** — but over-broad, see below |
| 4 | `LCM == 1` | the unsupplied company multiplier | No discriminator (Escalation E15) | R18 is a CONFIG entry; never raised per rating |
| 5 | Rule 45.E — all liquor rates | none in ERC | Manual-only | none |

**Deductible guard gap (OI-44).** `DoMessageMustEnterLiquorDeductibleFactorOverride` fires for only
10 of the 21 zero deductible options — every "Per Claim" option. The other 11 (all ten "Per Common
Cause" options, plus "No Deductible") are zero and unguarded. "No Deductible" is legitimately zero;
the other ten are not. A liquor risk written with, say, "5,000 Per Common Cause" receives a
deductible factor of `0` with no error message — priced as though it had no deductible.

> **Engine finding (R14 over-fires).** The engine's R14 detector (`gl_engine/rating/referrals.py`
> `d_zero_rating_factor`) raises on *any* lookup whose table name contains `Liquor` and returns `0` —
> including `DedFactorLiquor['CW', 'No Deductible'] → 0`, the one legitimate zero, and a Company
> class's `LiquorELP → 0`. Every liquor risk rated with "No Deductible" (all of ISO's liquor STCs)
> is therefore referred under R14 in `underwriting` mode (AL and IL @2026-10-02 and @2027-04-01). The
> register's own wording targets only the ten unguarded "Per Common Cause" cells. **Fixed 2026-10-14
> (OI-131, B-10):** R14 now reads `DedFactorLiquor` only and skips "No Deductible"; a Per Common Cause
> deductible still refers. A Company class's zero ELP is left to R29, which reads ISO's own message.

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
| `LiquorPremiumBasis` | classification | empty → `Premium = 0.0`. Refer values → `Premium = 0.0` (a referral, not a price). **CW 2027: both become `1.0` when `LiquorExposure > 0`** |
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
route to a premium. Under CW 2027 every one of them with `LiquorExposure > 0` lands on `Premium =
1.0` instead of `0` — still silent, now non-zero. None is refused by the engine (OI-94 only inspects
`*LossCost` nodes).

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
| `LookupLiquorELP` | `LiquorELP` | State\|CW, `LiquorClassCode` (rule XML) | State-filed only, 0 CW rows |
| `LookupLiquorLCM` | `LiquorLCM` | State\|CW | CW value `1`, no state overrides |
| `LookupILFLiquor` | `ILFLiquor` | State, `EachCommonCauseLimit`, `AggregateLimit` | Illinois override: `ILFLiquorStException`, keyed on `AggregateLimit` alone |
| `LookupDedFactorLiquor` | `DedFactorLiquor` | State\|CW, `LiquorDeductible` | CW: 21 options, all `0` |
| `LookupProdsCompldOpsMinPremium` | `ProdsCompldOpsMinPremium` | `ILTA` (hardcoded `"C"`) | CW: 3 rows, all `0` |
| `LookupProdsCompldOpsClaimsMadeMultiplier` | `ProdsCompldOpsClaimsMadeMultiplier` | `min(YearInClaimsMade, 5)` | CW: 5 rows, shared with Products/Completed Operations |
| `LookupNoDedStatCode` | — | — | Ships with the file, no caller (per GATE-332-LIQUOR-LIABILITY.md § 3) |
| `LookupPremOpsLCM` | `PremOpsLCM` | — | Ships with the file, no caller; table content identical in shape to `LiquorLCM` per § 6 |

Every lookup in this ruleset follows the same two-pass `FirstNonNull(state row, "CW" row)` pattern
(per GATE-332-LIQUOR-LIABILITY.md § 6, "N16, confirmed a fourth time"; visible in every engine trace
as a state `lookup-miss` followed by the CW hit for the CW-only tables).

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

TopUp         = max(0, max(MinPremium) - sum(Premium))  # separate policy-level coverage; 0 today
```

Everything above is exactly what the gate doc traced for CW 2023 V03 / CW 2026 V01, and what the
engine executes for CW 2023 V03 / 2026 V01 / 20261001 V01 (AL@2026-10-02 worked example in Step 12).
At 2027-04-01, apply the deltas in "What changes at 2027-04-01" above (minimum premium removed, `$1`
floor added — including on refer/blank bases with exposure — `Subline` guard dropped, premium-basis
vocabulary replaced, `SetELP`/`SetILF`/`SetDeductibleFactor` gated on the class code):

```
Premium (CW 2027) = 1.0                                         if computed premium = 0 and LiquorExposure > 0
                  | round(FinalRate x LiquorExposure / 1000, 0)  if basis is "Gross Sales of Alcoholic Beverages"
                                                                   or "Gross Sales of Food and Beverages"
                  | round(FinalRate x LiquorExposure, 0)         other non-blank, non-"Refer to Company" basis
                  | 0                                            otherwise (exposure 0)
```

---
