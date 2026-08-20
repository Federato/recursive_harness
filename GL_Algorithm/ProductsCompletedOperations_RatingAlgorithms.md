# Products/Completed Operations — Rating Algorithms

**Source:** `docs/gates/GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md` (differential gate, PASSED), read
against `docs/gates/GATE-334-PREMISES-OPERATIONS.md` (shared classification machinery, resolver,
inheritance mechanisms, rounding sites — 336 does not restate these, and neither does this
document except where the two sublines diverge).

**Line:** General Liability (GL), Subline 336 — Products/Completed Operations Liability Coverage.
Manual Rule 48.I (`docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.2.2). ERC golden case runs on
state package `GL_OK 20250601 V01`, declared countrywide parent `GL_CW_20231201_V03`. **336's
premium chain is identical under `GL_CW_20231201_V03` and `GL_CW_20270401_V01`** — unlike 334,
there is no medical-payments edition split, because 336 has no medical-payments term at all
(GATE-336 §1). Ten distinct countrywide parents are in live use across 562 state packages
(GATE-334 §0); this document does not assume any one of them beyond noting that 336's chain is
edition-stable.

**Documented:** 2026-08-20

Products/Completed Operations rates the products-liability and completed-operations hazard of a
Commercial General Liability policy. It shares classification, the resolver, the two inheritance
mechanisms (package-level rule override by name, and row-level `state → "CW"` fallback within a
table), and the rounding sites with subline 334 (Premises/Operations) — those are derived in
GATE-334 and reused here by reference. What follows is 336's own rate build-up and premium
calculation, presented as a full chain but written up **relative to 334** wherever the two are
structurally identical, per GATE-336's own differential method.

---

## Master orchestration

Two ordered `RunRule` sequences, outer then inner, same shape as 334 (GATE-334 §1):

```
GeneralLiabilityClassificationRules.Rule.xml
    ErcSetRatesAndFactors     (42 steps total, shared across every subline;
                                only the Prod/CompOps-feeding steps are listed below)

GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml
    ErcSetRatesAndFactors     (35 steps — vs 334's coverage-level 29)
    ErcRate                   (6 steps  — vs 334's 4)
```

336's coverage-level chain runs the same order and the same `if IsNull` override-guard idiom as
334's (GATE-334 §1b), with Prod/CompOps-named datadefs in place of PremOps-named ones, **plus**
seven steps 334 does not have, **minus** two steps 334 does have. Per GATE-336 § "The algorithm —
how 336 differs from 334":

**Steps 336 has that 334 does not:**

| Rule | Effect |
|---|---|
| `SetTerritory` | copies `../../../ProdsCompldOpsTerritory` — a second, independent territory. Statewide `999` in every one of the 51 jurisdictions (`03-SUBLINE-COVERAGE-PLAN.md` §3.2.2, point 1) |
| `SetSprayPainting` | classification qualifier carried into rating |
| `SetDefenseWithinLimitsBasicLimitMultiplier` | a fourth base-rate factor; switched off (empty override) in 13 jurisdictions today, 19 across all editions — §6 below |
| `SetSplitLimitWeightFactorProds{BI,PD,Constant}` | split-limit weights, computed on every quote |
| `SetDedFactorProdsPD250PerClaim` | a named single-cell deductible carve-out |
| `SetProdsCompldOps{BIPD,PD}DeductibleFactorBeforeAdjustment` | a pre-adjustment stage 334 has no equivalent of |
| `SetMinimumPremium` + `SetMinPremium` | run **inside `ErcRate`** — 336 computes its own minimum; 334 does not |

**Steps 334 has that 336 does not:** `SetBringYourOwnAlcoholExclusionFactor` (liquor classes
16905/16906 only — not a 336 concept), `SetMedicalPaymentsFactor` and `SetMedicalPaymentsCharge` —
medical payments is a Premises/Operations coverage and does not touch 336 at all.

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Classification-level prep (shared) | `GeneralLiabilityClassificationRules.Rule.xml` | `ErcSetRatesAndFactors` — 42-step chain, per-subline steps not individually cited by line in source |
| Rate build-up, coverage level | `GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml` | `ErcSetRatesAndFactors` — 35 steps |
| Premium calc | `GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml` | `ErcRate` — 6 steps (`SetBaseRate` → `SetCSLILF`/split-limit path → `SetFinalILF` → `SetFinalRate` → `SetBasicLimitPremium` → `SetPremium`/`SetMinimumPremium`/`SetMinPremium`) |
| Rating-basis selector | same file | `LookupProdsCompldOpsELPText` — closed vocabulary, GATE-336 §0 |
| Base rate tables | `ProdsCompldOpsLossCost.RateTable.csv`, `ProdsCompldOpsELPFactor.RateTable.csv` | state-filed, see ERC_Tables doc |
| ILF table assignment + factor | `IncreasedLimitsTableAssignmentProdsCompldOps.RateTable.csv`, `ILFProds.RateTable.csv` | state-filed |
| Minimum premium | `ProdsCompldOpsMinPremium.RateTable.csv` | countrywide only, 3 rows |
| Coverage form attachment only — **no rating** | form/endorsement catalog, `CG 00 37` / `CG 00 38` Products/Completed Operations Liability Coverage Form | `docs/rating-engine/A2-CW-RULE-CATALOG.md` line 51, `A3-ENDORSEMENT-CATALOG.md` lines 446–447 |
| Defense-Within-Limits endorsement | `CG 34 76` Defense Within Limits Products/Completed Operations Endorsement | `A3-ENDORSEMENT-CATALOG.md` line 494, `OPTIONAL_RTC` |
| Related, factor-derived (not rated independently) | Product Withdrawal (Subline 365) | derived from 336's ILTA via a Product Withdrawal Factor — `03-SUBLINE-COVERAGE-PLAN.md` §3.2.6 |

---

## Products/Completed Operations — rate build-up

Executed by `ErcSetRatesAndFactors` (35 steps) then `ErcRate` (6 steps) in
`GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml`. The step-by-step list below is
GATE-336's own arithmetic reconstruction (§1), not a restatement of all 35+6 individual rule names
— the gate doc gives the deltas from 334 in full (table above) but does not enumerate every shared
step by number for 336, the way it does for 334's 1b chain. Where a step is structurally identical
to 334's, this is stated rather than invented.

### Step 1 — Rating basis: loss cost or ELP (N17)
Per GATE-336 § "The finding: `0` is a *published* value that switches the rating path"

`ProdsCompldOpsLossCost` is looked up first. A row can genuinely exist and hold `0.0` — not a
missing value, not a "refer to company" sentinel, but a **documented path switch**. `SetBaseRate`
tests `ProdsCompldOpsLossCost == 0.0`:

```
if ProdsCompldOpsLossCost != 0.0:
    rate_source = ProdsCompldOpsLossCost          # loss-cost path
else:
    rate_source = ProdsCompldOpsELP               # ELP path
```

The engine does not need to infer this from the `0` alone. A sibling selector table,
`ProdsCompldOpsELPText`, is keyed on (state, class) and holds a closed vocabulary — `Rate/Loss Cost
Applies`, `Industry`, `Company`, `Not Applicable` — and **states outright** which path applies.
Tested corpus-wide across 572 packages, the selector agrees with the `LossCost != 0` branch test
**620,856 / 620,856 times, zero disagreements** (`scripts/erc/28_elp_selector.py`, per GATE-336
§0). New rule **N17**: the engine reads `ProdsCompldOpsELPText` and asserts agreement with the
`LossCost != 0` test; a disagreement is a load-time hard failure, not a warning.

### Step 2 — Territory
Per GATE-336 § "Steps 336 has that 334 does not"

`SetTerritory` copies `../../../ProdsCompldOpsTerritory` — a territory field independent of 334's
Premises/Operations territory. Its value is **statewide `999` in all 51 jurisdictions** measured
(`03-SUBLINE-COVERAGE-PLAN.md` §3.2.2, `03-RATING-STRUCTURE.md` line 585). Unlike 334, Prod/CompOps
loss cost is not territory-varying in practice, though the field and the lookup key exist.

### Step 3 — Base rate
Per GATE-336 § "The arithmetic"

```
BaseRate = round( LossCost | ELP
                   × LCM
                   [× ClaimsMadeMultiplier]
                   [× DefenseWithinLimitsBasicLimitMultiplier]
                 , 3)
```

`ClaimsMadeMultiplier` — explicit for 336 (Rule 48.D.6, Table 48.D.6), same claims-made-year-capped
lookup shape as 334's `SetClaimsMadeMultiplier` (GATE-334 §1b step 14), keyed on the
`SetYearInClaimsMade` value.

`DefenseWithinLimitsBasicLimitMultiplier` — a fourth base-rate factor 334 has no equivalent of.
**Its selector is `Exist`, not a value**: `SetBaseRate` branches on `Exist
AtInputDataDef=".../GeneralLiabilityDefenseWithinLimitsProdsCompldOpsTable/…"` — the presence of a
row, not a boolean flag. An engine modelling it as a boolean field never enters the branch. See
State deviations below for the 13/19-jurisdiction empty-override pattern.

### Step 4 — Increased-limits factor
Per GATE-336 §1, §5, and the classification-level steps (parallel to GATE-334 §1a)

The classification level resolves `IncreasedLimitsTableAssignmentProdsCompldOps` (a class → ILF
table-letter lookup, or `Refer To Co.` / `N/A`), then the coverage level copies it down and looks up
`ILFProds` to produce `CSLILF`.

**Typing trap, source-cited (GATE-336 §5).** 334's increased-limits table assignment is
**numeric-as-string** (`1`/`2`/`3`) with an explicit `SetFinalPremOpsIncrdLimitTableAssignmentInt`
conversion rule. **336's is alphabetic** (`A`/`B`/`C`) and **has no `…Int` conversion rule at all.**
A single shared `TableAssignment` type across both sublines fails on 336; the golden case value
`"B"` proves it. Non-values in 336's vocabulary: `N/A` (coverage not offered for the class — 21,021
rows, 35% of the table) and `Refer To Co.` (same degraded-referral shape as 334's).

Split-limit inputs (not exercised by the CSL golden case) go through
`SetSplitLimitWeightFactorProds{BI,PD,Constant}`, confirmed against the manual at
`0.87`/`0.17`/`0.01` for the Manufacturing band `50000–59999` (GATE-336 §2) — vs 334's `0.83` /
`0.19` / `0.03` for the same band, a genuine per-subline weighting, not a shared table.

### Step 5 — Deductible
Per GATE-336 § "Steps 336 has that 334 does not"

```
SetProdsCompldOps{BIPD,PD}DeductibleFactorBeforeAdjustment   # 336-only pre-adjustment stage
SetDedFactorProdsPD250PerClaim                                # a named single-cell carve-out
```

`FinalDeductibleFactor` is combined from the BI/PD components the same way as 334's
`SetFinalDeductibleFactor` (GATE-334 §1b step 21): combined ⇒ the combined factor; split BI+PD ⇒
sum; one side only ⇒ that side; else `0.0`. GATE-336 does not give the full branch detail for the
336-specific pre-adjustment stage beyond naming the two rules above — **not resolved in source
docs: the exact shape of `SetProdsCompldOps{BIPD,PD}DeductibleFactorBeforeAdjustment`'s branching is
not reproduced in GATE-336; only its existence and name are given.**

### Step 6 — Final ILF
Per GATE-336 § "The arithmetic"

```
FinalILF = round( CSLILF − FinalDeductibleFactor , 3)      # clamped to 0.0 if ≤ 0
```

**No medical-payments term in either edition.** This is the point of divergence from 334: 334's
`FinalILF` gains a `[+ MedicalPaymentsFactor − 1]` bracketed term under `GL_CW_20270401_V01` only
(GATE-334 §0); 336 never does, in any edition. 336's chain is edition-stable where 334's is not
(GATE-336 §1, "the edition axis is real but not uniform, and must be established per coverage
rather than assumed from 334").

### Step 7 — Final rate
Per GATE-336 § "The arithmetic"

```
FinalRate = round( BaseRate × FinalILF
                    [× SizeOfRiskFinalRelativity]
                    × PackageModFactor
                    × ExperienceRatingModificationFactor
                    × ExpenseModification
                    × ModToUse
                  , 3)
```

Same shape as 334's `SetFinalRate` (GATE-334 §1b step ErcRate-1), including the size-of-risk branch
that only applies when `SizeOfRiskRatingApplies = "Yes"`.

### Step 8 — Basic limit premium and premium
Per GATE-336 §1, §8

```
BasicLimitPremium = round( BaseRate × (1 − FinalDeductibleFactor) × FinalILF-adjacent-branch..., 0)
Premium           = round( FinalRate × Exposure[/1000] , 0)
```

**336 has no `$1` floor in either edition** — GATE-336 §4 flags this explicitly: `0.0` exposure →
`Premium = 0` with no floor, unlike 334's CW 2027 floor of `$1` when exposure `> 0`
(GATE-334 § "The $1 floor — CW 2027 only").

### Step 9 — Minimum premium
Per GATE-336 §1, "E11 is answered"

```
MinPremium = round( MinimumPremium × FinalILF × AdditionalInterestFactor , 0)
```

Computed **inside `ErcRate`**, unlike 334 which has no minimum-premium step at all. This also
answers 334's open question E11 (`AdditionalInterestFactor` computed and never consumed): **336
reads it.** GATE-334's E11 narrows from "is this dead?" to "is 334's omission intended?" — the field
is live exactly where ERC's own rule set reads it, and 334 genuinely does not.

---

## Products/Completed Operations — premium

`GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml`, `ErcRate` chain (see Step 8–9
above for the formulas). There is no multi-branch premium structure comparable to CF's
scheduled-building / Legal Liability / blanket split — 336 rates one coverage form
(`CG 00 37`/`CG 00 38`) with one premium path per risk. The "gates" below are the conditions under
which the chain resolves to a real number rather than `0`, `REFER`, or `NOT_OFFERED`.

### Gate — subline and classification validity
Per GATE-336 §4

```
if ProdsCompldOpsCov != "Products/Completed Operations":
    BaseRate = 0.0        # the Otherwise arm — engine: validate against the domain
```

`ProdsCompldOpsCovExposure` must not exceed `PremOpsCovExposure` —
`DoMessageProductsCompletedOperationsExposureCannotBeGreaterThanPremisesOperationsExposure`, a
cross-subline validation living in the classification rules (GATE-336 §4). A `DoMessage*` guard,
not a rating rule — per N15 (GATE-334 §4), these are part of the algorithm, not commentary.

### Gate — rating basis (N17)
See Step 1 above. Branch on `ProdsCompldOpsLossCost != 0.0` (loss-cost path) vs `== 0.0` (ELP
path), cross-checked against `ProdsCompldOpsELPText`.

### Branch A — Loss Cost path
`ProdsCompldOpsLossCost != 0.0`:

```
BaseRate = round(ProdsCompldOpsLossCost × LCM [× ClaimsMadeMultiplier]
                  [× DefenseWithinLimitsBasicLimitMultiplier], 3)
```

### Branch B — ELP path
`ProdsCompldOpsLossCost == 0.0`, `ProdsCompldOpsELPText != "Not Applicable"`:

```
BaseRate = round(ProdsCompldOpsELP × LCM [× ClaimsMadeMultiplier]
                  [× DefenseWithinLimitsBasicLimitMultiplier], 3)
```

The Oklahoma golden case runs this branch: `LossCost = 0.0` (published, not missing), `ELPText =
"Industry"`, `ELP = 0.82` → `BaseRate = round(0.82 × 1.0, 3) = 0.82` (GATE-336 §8).

### Branch C — not offered
`ProdsCompldOpsELPText == "Not Applicable"` → `NOT_OFFERED`, never `0`, per GATE-336 §7 point 2.
21,021 of the ILTA table's rows carry `N/A` for this reason — 35% of the table.

### Referral triggers
Per GATE-336 §7 — every path that must not silently produce a number:

1. **`IncreasedLimitsTableAssignmentProdsCompldOps = "Refer To Co."`** — same degraded-referral
   mechanism as 334: if the override substitute is absent, the assignment is empty, the ILF lookup
   misses, and the premium becomes `0`. Present in **all 51 jurisdictions, exactly 2 class codes
   each** (in Oklahoma: `54444` and `94444`, the catch-all "not otherwise classified" codes) — "a
   standing, universal referral on the classes most likely to be selected for an unusual risk."
2. **`Assignment = "N/A"`** — 21,021 rows, 35% of the table. Not offered for that class. 334 has no
   equivalent value in its own ILTA table.
3. **`ELPText = "Not Applicable"`** — 261,973 rows in `ProdsCompldOpsELPText`. Must agree with (2)
   per N17.
4. **`FinalILF ≤ 0` → clamped to `0.0`.** ERC clamps rather than errors.
5. **`ProdsCompldOpsCovExposure` exceeding `PremOpsCovExposure`** — cross-subline validation, §4
   above.

---

## Products/Completed Operations vs Premises/Operations — side by side

Both sublines share the classification rule set, the resolver, and the two inheritance mechanisms
(GATE-336 opening). The table below is built entirely from the two gates' own delta lists —
GATE-334 §1/§0/§7 and GATE-336 §1/§0/§4/§5/§6.

| | Premises/Operations (334) | Products/Completed Operations (336) |
|---|---|---|
| Coverage-level chain length | 29 steps + `ErcRate` 4 | 35 steps + `ErcRate` 6 |
| Territory | `PremisesOperationsTerritory`, varies by risk | `ProdsCompldOpsTerritory`, statewide `999` in all 51 states |
| Claims-made adjustment | present | present, and Rule 48.D.6 makes it explicit with its own table |
| Defense-Within-Limits multiplier | none | 4th base-rate factor, gated on **row presence**, not a flag |
| Split-limit weights (Mfg `50000–59999`) | BI `0.83` / PD `0.19` / Constant `0.03` | BI `0.87` / PD `0.17` / Constant `0.01` |
| Medical payments | separate factor/charge, edition-scoped (CW2023 vs CW2027) | **none — not a 336 concept at all** |
| `FinalILF` edition split | yes — CW2027 folds med-pay in, CW2023 does not | **no — identical formula in both editions** |
| Minimum premium | not computed in the premium chain | computed inside `ErcRate` (`SetMinimumPremium`/`SetMinPremium`) |
| `AdditionalInterestFactor` | computed, never consumed (E11, open) | computed **and consumed** in `MinPremium` — narrows 334's E11 |
| `$1` floor on zero premium | CW2027 only | **none in either edition** |
| Liquor-exclusion factor | `SetBringYourOwnAlcoholExclusionFactor`, classes 16905/16906 | none |
| ILTA vocabulary | numeric-as-string `1`/`2`/`3`, `SetFinalPremOpsIncrdLimitTableAssignmentInt` converts | alphabetic `A`/`B`/`C`, **no `…Int` conversion rule exists** |
| ILTA non-value | `Refer To Co.` only | `Refer To Co.` **and** `N/A` (coverage not offered) |
| ELP-selector table | `PremOpsELPText` | `ProdsCompldOpsELPText` — same closed vocabulary, same N17 discipline |
| Rating-basis discriminator | selector agrees with `LossCost != 0` in tested rows | same, corpus-wide: 620,856 / 620,856 agree, zero disagreements |
| DWL empty-override footprint | not applicable | 13 jurisdictions today (19 across all editions); 6 have retired it (CA FL GA KY VA WA) — edition drift, live N4 case |
| Own base-rate algorithm override | MA, NY, TX | inherits GATE-334's finding — not separately re-measured in GATE-336 |

---

## Supporting lookups

Per GATE-336 §4, §5, §7. Full table population/row-count data lives in the ERC_Tables companion
document.

| Rule / lookup | Purpose | Layer |
|---|---|---|
| `LookupProdsCompldOpsLossCost` | Base rate, loss-cost path | state only (0 CW rows) |
| `LookupProdsCompldOpsELP` (via `ProdsCompldOpsELPFactor`) | Base rate, ELP path | state only (0 CW rows) |
| `LookupProdsCompldOpsELPText` | Rating-basis selector (N17) | state only (0 CW rows) |
| `LookupIncreasedLimitsTableAssignmentProdsCompldOps` | ILF table letter (A/B/C) or Refer To Co./N-A | state only |
| `LookupILFProds` | `CSLILF`, keyed state, table-letter, occurrence limit, aggregate limit | state only (0 CW rows) |
| `SetSplitLimitWeightFactorProds{BI,PD,Constant}` | split-limit weighting when not CSL | — (values confirmed at 0.87/0.17/0.01 for Mfg band) |
| `LookupProdsCompldOpsMinPremium` | `MinimumPremium` input to `SetMinPremium` | **countrywide only**, 3 rows |
| `GeneralLiabilityDefenseWithinLimitsProdsCompldOpsTable` (row existence) | gates the DWL multiplier | row-presence check, not a value lookup |

Every lookup in this ruleset follows 334's two-pass pattern: try the state-specific row keyed on
`/*/State/Code`, then fall back to a `CW` row (`FirstNonNull`) — GATE-334 §5, reused unchanged by
336.

---

## Quick reference — end-to-end, Oklahoma golden case

Class `50017`, territory `999` (statewide), Gross Sales `5,000,000`, `1,000,000 / 2,000,000 CSL`,
occurrence form, no deductible, no size-of-risk. Reproduces GATE-336 §8 exactly, `Premium =
6,845.00`.

```
ILTA           = lookup IncreasedLimitsTableAssignmentProdsCompldOps(OK, 50017)        = "B"

LossCost       = lookup ProdsCompldOpsLossCost(OK, 999, 50017)                         = 0.0   (published zero)
ELPText        = lookup ProdsCompldOpsELPText(OK, 50017)                               = "Industry"   -> ELP path
ELP            = lookup ProdsCompldOpsELPFactor(OK, 50017)                             = 0.82

DWL multiplier = 1.0   (not overridden in OK; no DWL row present)

BaseRate       = round(ELP x LCM x DWL, 3)
               = round(0.82 x 1.0 x 1.0, 3)                                            = 0.82

CSLILF         = lookup ILFProds(OK, "B", "1,000,000 CSL", "2,000,000 CSL")            = 1.67
FinalILF       = round(CSLILF - FinalDeductibleFactor, 3)
               = round(1.67 - 0.0, 3)                                                  = 1.67

FinalRate      = round(BaseRate x FinalILF x PackageMod x ExperienceMod
                        x ExpenseMod x ModToUse, 3)
               = round(0.82 x 1.67 x 1 x 1 x 1 x 1, 3)                                 = 1.369

BasicLimitPremium = round(BaseRate x (1 - FinalDeductibleFactor) x 1.0 x (5,000,000/1000), 0)
               = round(0.82 x 1.0 x 1.0 x 5000, 0)                                     = 4,100

MinimumPremium = lookup ProdsCompldOpsMinPremium(CW)                                   = 0.0
MinPremium     = round(MinimumPremium x FinalILF x AdditionalInterestFactor, 0)
               = round(0 x 1.67 x 1.0, 0)                                              = 0

Premium        = round(FinalRate x Exposure, 0)
               = round(1.369 x 5000, 0)                                                = 6,845
```

All intermediate rate products round to 3 decimal places; `Premium` and `MinPremium` round to 0.

**Policy reconciliation** (with subline 334 and terrorism, GATE-336 §8):

```
334 Premises/Operations             976.00
336 Products/Completed Operations 6,845.00
Terrorism (Prem/Ops 2 + Prod/CompOps 16)  18.00
ErcCalculatedTotalPremium         7,839.00
```
