# Premises/Operations — Rating Algorithms

**Source gate:** `docs/gates/GATE-334-PREMISES-OPERATIONS.md` (subline 334)
**Also drawn from:** `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.1–3.2.1, `docs/erc/03-RATING-STRUCTURE.md` §2–5,
`docs/rating-engine/A2-CW-RULE-CATALOG.md`
**Line:** General Liability (GL), Subline `334` — Premises/Operations, part of the composite
coverage "Premises/Operations and Products/Completed Operations" (CGL, Rules 21/23/24).
**Golden case:** `GL_OK 20250601 V01/STC/1. Input.json` → `1. Output.json`, effective 2025-08-01.
**Documented:** 2026-08-20

This is a **reformat** of a passed gate, not new research. Every fact, formula, citation and open
item below comes from the gate document; nothing has been re-derived from ERC XML directly. Where
the gate doc did not give an ERC file+line citation (it cites rule names and step order, not XML
line numbers — unlike the CF source material this template was built from), that limitation is
noted rather than papered over with an invented line number.

Unlike the CF Building forms (four cause-of-loss forms rated in parallel), Premises/Operations has
**one rate build-up rated under two edition-scoped formulas** — the countrywide parent an
implementation resolves to (10 distinct parents in live use) determines which one applies. This
document treats "CW 2023 V03 and earlier" and "CW 2027 V01" as the two branches, in place of the
per-form branches a CF-style document would have.

---

## Master orchestration

Two ordered `RunRule` chains run in sequence, classification level then coverage level, per
`GATE-334-PREMISES-OPERATIONS.md` §1:

```
Classification level  — GeneralLiabilityClassificationRules.Rule.xml → ErcSetRatesAndFactors
    (8 of the rule's 42 total steps feed subline 334; see "Classification level" below)

Coverage level         — GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml → ErcSetRatesAndFactors
    (29 steps, verbatim order; see "Coverage level — rate build-up" below)

ErcRate (4 steps)
    SetFinalRate
    SetAdditionalInterestFactor
    SetPremium
    SetPremiumIndicator
```

**Edition dispatch is part of the orchestration, not an afterthought.** `SetFinalILF` and
`SetPremium` differ by countrywide parent (§0 of the gate doc) — an implementation cannot hold one
`premops.py`; it must select the calculator per the resolved countrywide parent, the same resolver
that already produces that parent for table lookups (N5). Ten distinct parents are in live use
across 562 state packages: `GL_CW_20231201_V02` ×146, `GL_CW_20260101_V01` ×114,
`GL_CW_20230501_V01` ×77, `GL_CW_20270401_V01` ×60, `GL_CW_20210801_V01` ×58,
`GL_CW_20231201_V03` ×51 (the golden case's parent), `GL_CW_20231201_V01` ×23,
`GL_CW_20230401_V01` ×12, `GL_CW_20220901_V02` ×11, `GL_CW_20201201_V01` ×10.

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Classification-level prep | `GeneralLiabilityClassificationRules.Rule.xml` | `ErcSetRatesAndFactors` (rule name only — no line cited in source) |
| Coverage-level rate build-up | `GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` | `ErcSetRatesAndFactors`, 29 steps |
| Premium calc (edition CW 2023 and earlier) | `GL CW 20260101 V01/Rules/GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` | `SetBaseRate`, `SetFinalRate`, `SetBasicLimitPremium`, `SetPremium` |
| Premium calc (edition CW 2027) | `GL CW 20270401 V01/Rules/GeneralLiabilityRules.Rule.xml` | `ErcCalculateTotalPremium`, `CalculateTotalPremium` |
| Loss cost table (state-filed) | `PremOpsLossCost.RateTable.csv` | keyed State, Territory, ClassCode |
| ILF table (state-filed) | `ILFPremOps.RateTable.csv` | keyed State, ILF table#, occurrence limit, general aggregate limit |
| ILF table assignment (state-filed) | `PremOpsIncrdLimitTableAssignment.RateTable.csv` | keyed State, ClassCode |
| Med-pay factor (countrywide) | `MedPayFactor.RateTable.csv` (CW 2023) / increased med-pay limit factor table (CW 2027) | keyed CW, ClassCode |
| Deductible factor tables (countrywide) | `DedFactorPremOpsCSL` / `DedFactorPremOpsBI` / `DedFactorPremOpsPD` | 93 rows each, CW only |
| Validation guards — **part of the algorithm, not commentary** | `DoMessage*` rules in the coverage-level rule file | e.g. `DoMessageMustEnterPremOpsBIPDDeductibleFactorOverride`, `DoMessagePremOpsBIPDDeductibleFactorCannotExceedILF` |
| Golden-case fixture | `GL_OK 20250601 V01/STC/1. Input.json` → `1. Output.json` | class `50017`, territory `501` |

> Note: as in the CF Structure rules, the validation (`DoMessage*`) rules are easy to mistake for
> commentary because they don't touch `Premium` directly. Per gate doc §7 and §9 (new N15), they
> hold guards — e.g. the "Per Claim" deductible-factor-is-zero sentinel — that the rating chain
> alone does not surface. Porting only `SetBaseRate…SetPremium` silently drops them.

---

## Classification level — rate build-up

Executed as 8 of the 42 steps of `ErcSetRatesAndFactors` in
`GeneralLiabilityClassificationRules.Rule.xml` (gate doc §1a):

```
SetSubline
SetClassificationType
SetPremOpsExposureCalc
SetPremOpsHomogeneityIndex
SetPremOpsIncrdLimitTableAssignment
SetFinalPremOpsIncrdLimitTableAssignment
SetFinalPremOpsIncrdLimitTableAssignmentInt
SetPremOpsIncrdLimitFactor
```

### Step 1 — Subline
`SetSubline` sets the subline text to `"334"`.
*(per GATE-334-PREMISES-OPERATIONS.md § 1a)*

### Step 2 — Classification type
`SetClassificationType` calls `LookupClassificationType`: class code → type (Mercantile /
Manufacturing / …).
*(per GATE-334-PREMISES-OPERATIONS.md § 1a)*

### Step 3 — Exposure calc
`SetPremOpsExposureCalc`:

```
if PremiumBasis in the nine ÷1000 bases:
    PremOpsExposureCalc = truncate(Exposure / 1000, long)
else:
    PremOpsExposureCalc = Exposure          # raw
```
*(per GATE-334-PREMISES-OPERATIONS.md § 1a, step 3)*

### Step 4 — Homogeneity index
`SetPremOpsHomogeneityIndex` — `LookupPremOpsHomogeneityIndex`: class → index. State-only table
(§5) — no countrywide rows exist.
*(per GATE-334-PREMISES-OPERATIONS.md § 1a, step 4 and § 5)*

### Step 5 — ILF table assignment
`SetPremOpsIncrdLimitTableAssignment` — `LookupPremOpsIncrdLimitTableAssignment`: class → ILF
table number, **or the literal string `"Refer To Co."`**.
*(per GATE-334-PREMISES-OPERATIONS.md § 1a, step 5)*

### Step 6 — Final table assignment (Refer To Co. override)
`SetFinalPremOpsIncrdLimitTableAssignment`:

```
if PremOpsIncrdLimitTableAssignment = "Refer To Co.":
    FinalPremOpsIncrdLimitTableAssignment = PremOpsIncrdLimitTableAssignmentOverride
else:
    FinalPremOpsIncrdLimitTableAssignment = PremOpsIncrdLimitTableAssignment
```

If the override is absent when the referral fires, the assignment resolves to null. See
"Referral gate" below. *(per GATE-334-PREMISES-OPERATIONS.md § 1a, step 6 and § 7 item 1)*

### Step 7 — Final table assignment as integer
`SetFinalPremOpsIncrdLimitTableAssignmentInt` — `Convert` to integer; **`0` when the assignment is
null or empty.**
*(per GATE-334-PREMISES-OPERATIONS.md § 1a, step 7)*

### Step 8 — ILF factor lookup
`SetPremOpsIncrdLimitFactor` — `LookupILFPremOps(state, table#, occurrence limit, general
aggregate limit)`. **`0.0`** if the subline is not Prem/Ops+Prod/CompOps or any key is empty.
*(per GATE-334-PREMISES-OPERATIONS.md § 1a, step 8)*

`ILFPremOps` golden-case row: `"OK", 3, "1,000,000 CSL", "2,000,000 CSL", 2.05` →
`PremOpsIncrdLimitFactor = 2.05`. *(per GATE-334-PREMISES-OPERATIONS.md § 8)*

---

## Coverage level — rate build-up

Executed as 29 verbatim-order steps of `ErcSetRatesAndFactors` in
`GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` (gate doc §1b):

### Step 1 — Class code and premium basis
`SetClassCode` copies from the parent classification, else `""`. `SetPremiumBasis` copies
`PremOpsPremiumBasis`, else `""` — an empty premium basis silently falls to the non-÷1000 branch
(1000× overcharge; see "Referral gate" below).
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 1–2 and § 4)*

### Step 2 — Loss cost multiplier
`SetLCM` — `LookupPremOpsLCM(state, "Y")`, only if not already supplied.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 3)*

### Step 3 — Bring-your-own-alcohol exclusion factor
`SetBringYourOwnAlcoholExclusionFactor` — `LookupBringYourOwnAlcoholExclusionFactor`. Enters the
base rate **only** for class codes `16905`/`16906` **and** only when a
`GeneralLiabilityAmndmtOfLiquorLiabExcl` row exists.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 4 and "The arithmetic")*

### Step 4 — Loss cost
`SetPremOpsLossCost`:

```
if ClassCode non-empty and PremisesOperationsTerritory non-empty:
    PremOpsLossCost = LookupPremOpsSizeOfRiskLossCost(...)   if size-of-risk applies
                     | LookupPremOpsLossCost(...)            otherwise
else:
    PremOpsLossCost = 0.0
```

A missing class code or territory does not error — it silently routes the risk onto the
expected-loss-potential (ELP) path instead. Nothing in the rule set marks the transition.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 5 and § 4)*

`PremOpsLossCost` golden-case row: `"OK", "501", "50017", 0.095`.
*(per GATE-334-PREMISES-OPERATIONS.md § 8)*

### Step 5 — ELP
`SetPremOpsELPOverride` copies a user override, else `0.0`. `SetPremOpsELP`:

```
if PremOpsELPOverride = 0.0 and ClassCode non-empty:
    PremOpsELP = LookupPremOpsELP
else:
    PremOpsELP = PremOpsELPOverride, else 0.0
```
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 6–7)*

### Step 6 — Coverage-level ILF table assignment
`SetFinalPremOpsIncrdLimitTableAssignment[Int]` — coverage-level copies of the classification-level
Steps 6–7 above.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 8–9)*

### Step 7 — Deductible overrides
`SetPremOps{BI,BIPD,PD}DeductibleFactorOverride` — copy user overrides, each else `0.0`.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 10–12)*

### Step 8 — Claims-made
`SetYearInClaimsMade` copies when the form is `Claims Made`, else `0`. `SetClaimsMadeMultiplier` —
`LookupPremOpsClaimsMadeMultiplier(year)`, **year capped at 5**; `1.0` on the occurrence form.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 13–14)*

### Step 9 — Base rate
`SetBaseRate`:

```
BaseRate = round( LossCost [x BringYourOwnAlcoholExclusionFactor] x LCM
                            [x ClaimsMadeMultiplier] , 3)          # when LossCost <> 0
         = round( ELP x LCM [x ClaimsMadeMultiplier] , 3)          # when LossCost = 0
```
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 15 and "The arithmetic")*

Golden case: `round(0.095 x 1.0, 3) = 0.095`. *(per GATE-334-PREMISES-OPERATIONS.md § 8)*

### Step 10 — CSL ILF
`SetCSLILF` — **copies** `../PremOpsIncrdLimitFactor` from the classification level (Step 8 above);
no lookup at this level.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 16)*

### Step 11 — Medical payments factor
`SetMedicalPaymentsFactor` — `LookupMedPayFactor` (CW 2023 and earlier) or
`LookupIncreasedMedPayLimitFactor` (CW 2027); `1.0` when med-pay is excluded at class or location
level. Golden-case (CW 2023) row: `"CW", "50017", 1.003`.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 17 and § 8)*

### Step 12 — BI/PD deductible factors
`SetPremOps{BI,PD}DeductibleFactor` — `LookupDedFactorPremOps{BI,PD}`.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 18–19)*

### Step 13 — Deductible factor and final deductible factor
`SetDeductibleFactor`:

```
DeductibleFactor = override            if override non-zero
                  | LookupDedFactorPremOpsCSL(state, table#, deductible)
                  | 0.0
```

`SetFinalDeductibleFactor`:

```
FinalDeductibleFactor = DeductibleFactor                                    # combined form
                       = PremOpsBIDeductibleFactor + PremOpsPDDeductibleFactor  # split BI+PD
                       = whichever of BI/PD is present                      # one side only
                       = 0.0                                                # otherwise
```
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 20–21)*

**Sentinel.** Every "Per Claim" deductible factor in the countrywide table is `0` while every
corresponding "Per Occurrence" row carries a real factor (`0.005`, `0.01`, `0.013`, `0.018`, …).
Guarded only by validation rule `DoMessageMustEnterPremOpsBIPDDeductibleFactorOverride`, not by the
rating chain itself. *(per GATE-334-PREMISES-OPERATIONS.md § 7 item 2)*

### Step 14 — Final ILF (edition-dependent)
`SetFinalILF` — see "Coverage level — premium" below; formula differs by countrywide parent.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 22 and § 0)*

### Step 15 — Size of risk
```
SetPremOpsSizeOfRiskRelativityTableAssignment   # class -> table, only if SizeOfRiskRatingApplies = "Yes"
SetPremOpsExposureTimesThousand                 # long(exposure/1000) x 1000 for the /1000 bases;
                                                 # long(exposure) x 1000 otherwise; 0 if size-of-risk N/A
SetPremOpsSizeOfRiskPreliminaryRelativity        # LookupPremOpsSizeOfRiskRelativity, rounded 4dp
SetPremOpsSizeOfRiskMinimumRelativity            # class-keyed bound
SetPremOpsSizeOfRiskMaximumRelativity            # class-keyed bound
SetPremOpsSizeOfRiskFinalRelativity              # clamp(preliminary, min, max)
```

`PremOpsSizeOfRiskFinalRelativity = 0.0` when `SizeOfRiskRatingApplies <> "Yes"` is **not** a
sentinel — `SetFinalRate` and `SetBasicLimitPremium` each have a separate branch that omits the
factor entirely in that case, verified by reading the rule rather than inferring from the value.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 23–28 and § 7, "Not a referral, verified")*

### Step 16 — Basic limit premium
`SetBasicLimitPremium`:

```
BasicLimitPremium =
  round(
      BaseRate
    x (1 - FinalDeductibleFactor)
    [x SizeOfRiskFinalRelativity]
    x PackageModFactor
    x Exposure[/1000]
  , 0)
```

**This is not the subline premium.** It is the policy-level `AnnualBasicLimitsCoPremiumPremOps`
figure, consumed by no rule in the premium chain — a reporting quantity, easily mistaken for the
subline's `Premium` (an error that stood uncorrected across three prior documents; the golden case
is `976.00`, not `475.00`).
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 29 and § 8)*

---

## Coverage level — premium

`ErcRate`: `SetFinalRate` → `SetAdditionalInterestFactor` → `SetPremium` → `SetPremiumIndicator`.

### Gate — referral triggers
No rule in either edition raises an explicit gate flag; these are the points where ERC's own data
or rules degrade a referral into a silently-computed number instead (gate doc §7):

1. `PremOpsIncrdLimitTableAssignment = "Refer To Co."` with no override supplied → assignment null
   → `…Int = 0` → ILF lookup misses → premium `0` (CW 2023) or `$1` (CW 2027, via the floor below).
2. Every "Per Claim" deductible factor is `0` countrywide — see Step 13 above.
3. `DoMessagePremOpsBIPDDeductibleFactorCannotExceedILF` — tested as
   `PremOpsBIPDDeductibleFactorOverride > PremOpsIncrdLimitFactor` (plus BI-only, PD-only, and the
   matching Prods/CompldOps trio).
4. `FinalILF <= 0` → clamped to `0.0` rather than erroring.
5. Med-pay limit above $25,000 each person — manual only (Rule 56.D.2, `GL-MU-2027-RU-001-C` p.32);
   ERC expresses this only as the absence of a domain row.
6. Personal-and-advertising-injury limit ≠ occurrence limit — manual only, same page; ERC does not
   model a separate P&AI limit at all.
7. Empty class code or territory (Step 4 above) → ELP path; empty premium basis (Step 1 above) →
   non-÷1000 branch, 1000× high.

*(per GATE-334-PREMISES-OPERATIONS.md § 7)*

### Branch A — CW 2023 V03 and earlier
(This is the golden case's edition — parent `GL_CW_20231201_V03`.)

```
FinalILF = round( CSLILF - FinalDeductibleFactor , 3)

FinalRate = round( BaseRate x FinalILF [x SizeOfRiskFinalRelativity]
                            x PackageModFactor x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse , 3)

MedicalPaymentsCharge = round( BaseRate x ... x (MedicalPaymentsFactor - 1) x ... x Exposure , 0)
                         # separate SetMedicalPaymentsCharge rule; added inside SetPremium

Premium = round( FinalRate x Exposure[/1000] + MedicalPaymentsCharge , 0)
```

No `$1` floor exists in this edition — a zero-computing premium stays `0`.
*(per GATE-334-PREMISES-OPERATIONS.md § 0 and "The arithmetic")*

**Note on `SetMedicalPaymentsCharge` (CW 2023):** it branches on `../PremOpsELP` compared as a
**string** to `"Rate/Loss Cost Applies"` in one arm and as a **decimal** to `0.0` in another arm —
two comparison types against one DataDef. Both arms are implemented as ERC writes them; flagged as
open item E12, not normalized. *(per GATE-334-PREMISES-OPERATIONS.md § 3, E12)*

### Branch B — CW 2027 V01
No `SetMedicalPaymentsCharge` rule exists in this edition; medical payments folds into the ILF
instead:

```
FinalILF = round( CSLILF + MedicalPaymentsFactor - 1 - FinalDeductibleFactor , 3)
           # clamped to 0.0 if <= 0

FinalRate = round( BaseRate x FinalILF [x SizeOfRiskFinalRelativity]
                            x PackageModFactor x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse , 3)

Premium = round( FinalRate x Exposure[/1000] , 0)

if Premium = 0 and PremOpsCovExposure > 0:
    Premium = 1.0                      # the $1 floor — undocumented in the manual, CW 2027 only
```

Algebraically identical to Branch A — `BaseRate = LossCost x LCM x ClaimsMadeMultiplier` is common
to both, and the fold distributes to exactly the separate charge. They differ **only in where
rounding lands**, and that moves the answer: on the golden case's inputs, Branch A yields `976`,
Branch B yields `975` — one dollar apart on the same published risk.
*(per GATE-334-PREMISES-OPERATIONS.md § 0)*

Also under CW 2027: the ÷1000 divisor set drops **Passenger Days** (nine bases instead of ten).
*(per GATE-334-PREMISES-OPERATIONS.md § 0 and "The arithmetic")*

### Premium indicator
`SetPremiumIndicator`: `PremiumIndicator = 1` when `Premium <> 0`. Identical in both editions.
*(per GATE-334-PREMISES-OPERATIONS.md § 8)*

### `AdditionalInterestFactor` — computed and never consumed
`SetAdditionalInterestFactor` writes it (input, else `1.0`) but no rule in either edition's
premium chain reads it. Recorded as observation only, **not implemented as a multiplier** —
open item E11. *(per GATE-334-PREMISES-OPERATIONS.md § 1 and § 3, E11)*

---

## CW 2023-and-earlier vs. CW 2027 — side by side

| | CW 2023 V03 and earlier | CW 2027 V01 |
|---|---|---|
| `FinalILF` | `round(CSLILF - FinalDeductibleFactor, 3)` | `round(CSLILF + MedicalPaymentsFactor - 1 - FinalDeductibleFactor, 3)` |
| Med-pay | separate `MedicalPaymentsCharge`, 0dp, added inside `SetPremium` | folded into the ILF; **no `SetMedicalPaymentsCharge` rule exists** |
| `SetPremium` | `round(FinalRate x Exposure[/1000] + MedicalPaymentsCharge, 0)` | `round(FinalRate x Exposure[/1000], 0)` |
| Zero-premium floor | none — stays `0` | floored at `$1` when `PremOpsCovExposure > 0` |
| ÷1000 premium-basis set | 10 bases (includes Passenger Days) | 9 bases (Passenger Days dropped) |
| Elevator/escalator inspection charge (Rule 51 / subline 334) | present, additive premium under classification step G | **absent from the rule list** |
| Golden-case premium (class 50017, territory 501, Gross Sales 5,000,000) | **976** | **975** |

*(per GATE-334-PREMISES-OPERATIONS.md § 0 and `A2-CW-RULE-CATALOG.md` row 51)*

---

## Supporting lookups

| Rule | Matrix | Keys | Layer |
|---|---|---|---|
| `LookupPremOpsLossCost` | `PremOpsLossCost` | State, Territory, ClassCode | **state only** — 0 CW rows |
| `LookupILFPremOps` | `ILFPremOps` | State, ILF table#, occurrence limit, general aggregate limit | **state only** — 0 CW rows |
| `LookupPremOpsIncrdLimitTableAssignment` | `PremOpsIncrdLimitTableAssignment` | State, ClassCode | **state only** — 0 CW rows |
| `LookupPremOpsHomogeneityIndex` | `PremOpsHomogeneityIndex` | State, ClassCode | state |
| `LookupPremOpsELP` | `PremOpsELP` | State, ClassCode | state |
| `LookupMedPayFactor` (CW 2023) | `MedPayFactor` | CW, ClassCode | **countrywide only** — 1,188 rows |
| `LookupIncreasedMedPayLimitFactor` (CW 2027) | not further specified in source | — | edition-specific, replaces `MedPayFactor` |
| `LookupDedFactorPremOpsCSL` / `...BI` / `...PD` | `DedFactorPremOpsCSL` / `BI` / `PD` | State, table#, deductible | **countrywide only** — 93 rows each |
| `LookupPremOpsClaimsMadeMultiplier` | claims-made multiplier table | year (capped at 5) | not further specified in source |
| `LookupPremOpsLCM` | LCM table | State, `"Y"` | not further specified; held at `1.0` in the golden case by decision E9 |
| `LookupBringYourOwnAlcoholExclusionFactor` | BYOA exclusion table | class codes `16905`/`16906` + `GeneralLiabilityAmndmtOfLiquorLiabExcl` presence | not further specified in source |
| `LookupPremOpsSizeOfRiskLossCost` | size-of-risk loss cost table | not detailed | — |
| `LookupPremOpsSizeOfRiskRelativity` | size-of-risk relativity table | class-keyed | — |
| `LookupPremOpsMinPremium` | `PremOpsMinPremium` | table# | **countrywide only** — 3 rows, all `0` |
| `LookupClassificationType` | `ClassificationType` | ClassCode | **countrywide only** |

Every `Lookup` in this ruleset follows the same two-pass pattern documented for CF —
`FirstNonNull(state row, "CW" row)` — but ERC expresses it as `FirstNonNull` of two `Lookup` calls
against the *same table*, first keyed on `/*/State/Code` then on the literal `"CW"`. A single
resolved table therefore carries both state and countrywide rows, falling back row by row — this is
a second inheritance mechanism distinct from overriding a whole table by name at the package layer.
*(per GATE-334-PREMISES-OPERATIONS.md § 5)*

---

## State deviations

Measured across all 572 packages / 51 jurisdictions, indexing every `rul:Rule Name` in each
package's `GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml`. **32 of 51 jurisdictions
carry no override at all** (AL AR AZ CO DC DE FL GA IA ID IL KS LA MD ME MN MS NE NM NV OR PA PR RI
SC SD VA VT WA WI WV WY) — they rate on the countrywide algorithm with state tables. **19 override
something; only 8 of those touch premium:**

| Rule overridden | Jurisdictions | Effect |
|---|---|---|
| `SetPremOpsLossCost` + `LookupPremOpsLossCost` | CA NJ NY OH | Loss-cost table partitioned into per-territory sub-tables — a dispatch layer, not a different formula |
| `LookupPremOpsSizeOfRiskLossCost501…517` | NJ OH | Same partitioning for the size-of-risk loss cost |
| `SetBaseRate` | MA NY TX | Own base-rate algorithm |
| `SetBringYourOwnAlcoholExclusionFactor` | MA TX | Own liquor-exclusion factor |
| `SetBIILF`, `SetPDILF`, `LookupILFElevatorContractor` | KY | Separate BI/PD increased-limits treatment plus an elevator-contractor ILF table found nowhere else |
| `SetMedicalPaymentsCharge`, `SetYearInClaimsMade`, `SetClaimsMadeMultiplier` | NY | Own med-pay charge and claims-made chain |
| `SetPremOpsIncrdLimitFactor` (classification level) | OK | Governmental-subdivision ILF variant, gated on `GovernmentalSubdivision = "Yes"` |
| statistical coding rules | AK CT IN MA MI MO MT NC ND NH NY OK TN UT | No premium effect |

*(per GATE-334-PREMISES-OPERATIONS.md § 6)*

---

## Quick reference — end-to-end, CW 2023 and earlier (Oklahoma golden case)

```
LossCost   = lookup PremOpsLossCost(State, Territory, ClassCode)          [OK/501/50017: 0.095]
LCM        = lookup PremOpsLCM(State, "Y")                                [held 1.0]
BaseRate   = round(LossCost x LCM [x ClaimsMadeMultiplier], 3)            [0.095]

ILFTable   = lookup PremOpsIncrdLimitTableAssignment(State, ClassCode)    [OK/50017: 3]
CSLILF     = lookup ILFPremOps(State, table#, occLimit, aggLimit)         [OK,3,1M,2M: 2.05]
MedPayFctr = lookup MedPayFactor(CW, ClassCode)                           [CW/50017: 1.003]

FinalDeductibleFactor = 0.0                                               [no deductible]
FinalILF   = round(CSLILF - FinalDeductibleFactor, 3)                     [2.05]

FinalRate  = round(BaseRate x FinalILF x PackageModFactor
                    x ExperienceRatingModificationFactor x ExpenseModification x ModToUse, 3)
                                                                            [round(0.095x2.05,3)=0.195]

BasicLimitPremium = round(BaseRate x (1-FinalDeductibleFactor) x PackageModFactor
                           x Exposure[/1000], 0)                          [475 — NOT the subline premium]

MedicalPaymentsCharge = round(BaseRate x (MedPayFctr - 1) x Exposure, 0)  [round(0.095x0.003x5000,0)=1]

Premium    = round(FinalRate x Exposure[/1000] + MedicalPaymentsCharge, 0)
                                                                            [round(0.195x5000+1,0) = 976]
```

Every value above reproduces the ISO published output exactly. *(per GATE-334-PREMISES-OPERATIONS.md § 8)*

## Quick reference — end-to-end, CW 2027

```
LossCost   = lookup PremOpsLossCost(State, Territory, ClassCode)
LCM        = lookup PremOpsLCM(State, "Y")
BaseRate   = round(LossCost x LCM [x ClaimsMadeMultiplier], 3)

CSLILF     = lookup ILFPremOps(State, table#, occLimit, aggLimit)
MedPayFctr = lookup IncreasedMedPayLimitFactor(...)

FinalILF   = round(CSLILF + MedPayFctr - 1 - FinalDeductibleFactor, 3)   # clamped to 0.0 if <= 0

FinalRate  = round(BaseRate x FinalILF [x SizeOfRiskFinalRelativity] x PackageModFactor
                    x ExperienceRatingModificationFactor x ExpenseModification x ModToUse, 3)

Premium    = round(FinalRate x Exposure[/1000, nine bases — Passenger Days dropped], 0)

if Premium = 0 and PremOpsCovExposure > 0:
    Premium = 1.0                                                        # CW 2027 floor
```

On the golden case's inputs this yields `975` — one dollar below the CW 2023 result, from the same
underlying loss cost and ILF, purely from where rounding lands.
*(per GATE-334-PREMISES-OPERATIONS.md § 0)*

---
