# Premises/Operations — Rating Algorithms

**Source gate:** `docs/gates/GATE-334-PREMISES-OPERATIONS.md` (subline 334)
**Also drawn from:** `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.1–3.2.1, `docs/erc/03-RATING-STRUCTURE.md` §2–5,
`docs/rating-engine/A2-CW-RULE-CATALOG.md`
**Line:** General Liability (GL), Subline `334` — Premises/Operations, part of the composite
coverage "Premises/Operations and Products/Completed Operations" (CGL, Rules 21/23/24).
**Golden case:** `GL_OK 20250601 V01/STC/1. Input.json` → `1. Output.json`, effective 2025-08-01.
**Documented:** 2026-08-20
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — OK golden (OK@2025-08-01, `GL_OK_20250601_V01` over `GL_CW_20231201_V03` → 976), OK ISO STC (OK@2026-08-01 over `GL_CW_20260101_V01` → 996; policy 8,229 = ISO output), OK@2026-10-02 (over `GL_CW_20261001_V01` → 996), OK@2027-04-01 (`GL_OK_20270401_V04` over `GL_CW_20270401_V02` → 965), TX@2027-04-01 (over `GL_CW_20270401_V01` → 895) and CA@2027-04-01 (over `GL_CW_20231201_V02` → 741) rated offline, and every rule in the coverage file diffed across the five CW editions; corrections are marked *(engine-verified 2026-10-02)*.

This began as a **reformat** of a passed gate. On 2026-10-02 the step lists, formulas, rounding
points, edition branches and worked numbers were re-verified against the built engine
(`gl_engine/`, which interprets ISO's own ERC rule XML) and the CW rule XML itself; where the gate
was wrong or out of date the text below now follows the engine and says so. Corpus-wide census
figures (parent counts, the 572-package state-deviation index, the manual citations) are still the
gate's own and were not re-measured.

Unlike the CF Building forms (four cause-of-loss forms rated in parallel), Premises/Operations has
**one rate build-up rated under two edition-scoped rule sets** — the countrywide parent an
implementation resolves to determines which one applies. Diffing every rule in
`GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` shows exactly two variants:
**pre-2027** (`GL_CW_20231201_V03`, `GL_CW_20260101_V01` and `GL_CW_20261001_V01` are identical in
this file) and **CW 2027** (`GL_CW_20270401_V01` and `GL_CW_20270401_V02` are identical in this
file). This document calls them Branch A (pre-2027) and Branch B (CW 2027).
*(engine-verified 2026-10-02)*

**Which branch a quote lands on is a function of the effective date** (decision A3 — the effective
date is a variable, not a constant) and, optionally, a pinned `package_version`. The engine
resolves the state package in force on that date and then its **declared** countrywide parent
(`gl_engine/resolve/resolver.py`), never "the newest CW". As of 2027-04-01: CA → CW 20231201 V02
(Branch A); GA, NJ, NY, WA → CW 20260101 V01 (Branch A); AK, DC, MA, NC, SC, TX, WI, WV → CW
20270401 V01 (Branch B); the other 38 → CW 20270401 V02 (Branch B). As of 2026-10-02 every
jurisdiction is on Branch A (CA → 20231201 V02; NJ, TX, VT → 20231201 V03; OK → 20261001 V01; the
other 46 → 20260101 V01).

---

## Master orchestration

Two ordered `RunRule` chains run in sequence, classification level then coverage level, per
`GATE-334-PREMISES-OPERATIONS.md` §1:

```
Classification level  — GeneralLiabilityClassificationRules.Rule.xml → ErcSetRatesAndFactors
    (42 steps pre-2027 / 40 in CW 20270401 V01 / 39 in CW 20270401 V02; 9 of them feed
     subline 334 in every edition, plus 2 special-combined-minimum steps pre-2027 only;
     see "Classification level" below)

Coverage level         — GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml → ErcSetRatesAndFactors
    (38 steps pre-2027 / 29 steps CW 2027; see "Coverage level — rate build-up" below)

ErcRate — pre-2027 (9 steps)            ErcRate — CW 2027 (4 steps)
    SetFinalRate                            SetFinalRate
    SetMedicalPaymentsCharge                SetAdditionalInterestFactor
    SetAdditionalInterestFactor             SetPremium        (with the $1 floor)
    SetMinimumPremium                       SetPremiumIndicator
    SetMinPremium
    SetSpecialCombinedMinimumPremium
    SetSpecialCombinedMinPremium
    SetPremium
    SetPremiumIndicator

Policy level — GeneralLiabilityPremOpsPremiumToReachMinCoverageRules.Rule.xml
    pre-2027: ErcRate → SetCoveragePremium, SetMinPremium, SetPremium, SetPremiumIndicator
              (a minimum-premium top-up; see "Policy-level minimum premium" below)
    CW 2027:  InitializeRuleSet / SetCoverageOnPolicyIndicator / ErcProcess only — no premium rules
```

*(engine-verified 2026-10-02: rule lists read from all five CW packages; the OK@2025-08-01 and
OK@2027-04-01 traces execute exactly these sequences. The gate's "29 + 4" was the CW 2027 chain
only — the golden case's own edition runs 38 + 9.)*

**Edition dispatch is part of the orchestration, not an afterthought.** Rule *membership* and the
bodies of `SetFinalILF`, `SetPremium`, `SetMedicalPaymentsFactor`, `SetDeductibleFactor`,
`SetBasicLimitPremium` and `SetClaimsMadeMultiplier` all differ by countrywide parent. The built
engine holds no hand-written calculator per edition: it interprets whichever CW rule XML the
resolver hands it, so the dispatch *is* the resolver (N5). The gate's census of parents in live use
(`GL_CW_20231201_V02` ×146, `GL_CW_20260101_V01` ×114, `GL_CW_20230501_V01` ×77,
`GL_CW_20270401_V01` ×60, `GL_CW_20210801_V01` ×58, `GL_CW_20231201_V03` ×51 (the golden case's
parent), `GL_CW_20231201_V01` ×23, `GL_CW_20230401_V01` ×12, `GL_CW_20220901_V02` ×11,
`GL_CW_20201201_V01` ×10) predates the arrival of `GL_CW_20261001_V01` and `GL_CW_20270401_V02` and
was not re-counted.

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Classification-level prep | `GeneralLiabilityClassificationRules.Rule.xml` | `ErcSetRatesAndFactors` (rule name only — no line cited in source) |
| Coverage-level rate build-up | `GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` | `ErcSetRatesAndFactors`, 38 steps pre-2027 / 29 steps CW 2027 |
| Premium calc (Branch A, pre-2027: CW 20231201 V03 / 20260101 V01 / 20261001 V01) | `GL CW 20260101 V01/Rules/GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` | `ErcRate` (9 steps): `SetFinalRate`, `SetMedicalPaymentsCharge`, `SetMinimumPremium`, `SetMinPremium`, `SetSpecialCombinedMin*`, `SetPremium` |
| Premium calc (Branch B, CW 20270401 V01 / V02) | same file name in the 2027 packages | `ErcRate` (4 steps): `SetFinalRate`, `SetAdditionalInterestFactor`, `SetPremium` (with the `$1` floor), `SetPremiumIndicator` |
| Policy-level minimum-premium top-up (Branch A only) | `GeneralLiabilityPremOpsPremiumToReachMinCoverageRules.Rule.xml` | `ErcRate` → `SetCoveragePremium`, `SetMinPremium`, `SetPremium` |
| Policy total (both branches) | `GeneralLiabilityRules.Rule.xml` | `ErcCalculateTotalPremium`, `CalculateTotalPremium` — sums coverage premiums; not where 334's premium is computed |
| Loss cost table (state-filed) | `PremOpsLossCost.RateTable.csv` | keyed State, Territory, ClassCode |
| ILF table (state-filed) | `ILFPremOps.RateTable.csv` | keyed State, ILF table#, occurrence limit, general aggregate limit — limit values carry a `" CSL"` suffix pre-2027 (`"1,000,000 CSL"`) and none from the 2027-04-01 filings (`"1,000,000"`, OI-96/97) |
| ILF table assignment (state-filed) | `PremOpsIncrdLimitTableAssignment.RateTable.csv` | keyed State, ClassCode |
| Med-pay factor (countrywide) | `MedPayFactor.RateTable.csv` (Branch A, 1,188 rows, keyed CW, ClassCode) / `IncreasedMedPayLimitFactor.RateTable.csv` (Branch B, 20 rows, keyed CW, ClassificationType, med-pay limit `10,000`–`25,000`) | — |
| Deductible factor tables (countrywide) | `DedFactorPremOpsCSL` / `DedFactorPremOpsBI` / `DedFactorPremOpsPD` | 93 rows each, CW only, keyed CW, ILF table#, deductible — identical in both branches |
| Validation guards — **part of the algorithm, not commentary** | `DoMessage*` rules in the coverage-level rule file | e.g. `DoMessageMustEnterPremOpsBIPDDeductibleFactorOverride`, `DoMessagePremOpsBIPDDeductibleFactorCannotExceedILF` |
| Golden-case fixture | `GL_OK 20250601 V01/STC/1. Input.json` → `1. Output.json` | class `50017`, territory `501` |

> Note: as in the CF Structure rules, the validation (`DoMessage*`) rules are easy to mistake for
> commentary because they don't touch `Premium` directly. Per gate doc §7 and §9 (new N15), they
> hold guards — e.g. the "Per Claim" deductible-factor-is-zero sentinel — that the rating chain
> alone does not surface. Porting only `SetBaseRate…SetPremium` silently drops them.

---

## Classification level — rate build-up

Executed as 9 of the steps of `ErcSetRatesAndFactors` in
`GeneralLiabilityClassificationRules.Rule.xml` (42 steps pre-2027, 40 in CW 20270401 V01, 39 in
CW 20270401 V02 — V02 drops `SetCounty`). The gate listed 8; it omitted the classification-level
`SetPremOpsELP` text selector, which the engine trace runs between steps 7 and 8.
*(engine-verified 2026-10-02)*

```
SetSubline
SetClassificationType
SetPremOpsExposureCalc
[SetSpecialCombinedMinPremiumClassIndicatorLookup]   # pre-2027 only — feeds the policy-level
[SetSpecialCombinedMinPremiumClassIndicator]         #   minimum-premium top-up
SetPremOpsHomogeneityIndex
SetPremOpsIncrdLimitTableAssignment
SetFinalPremOpsIncrdLimitTableAssignment
SetFinalPremOpsIncrdLimitTableAssignmentInt
SetPremOpsELP                    # LookupPremOpsELPText: "Rate/Loss Cost Applies" | "Industry" | "Company" | …
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

The ÷1000 set is nine bases in **both** branches, but not the same nine: Admissions, Area,
Gallons, Gross Sales, Payroll, Total Cost, Total Operating Expenses, Vehicles, plus **Passenger
Days** (pre-2027) or **Kilowatt-hours** (CW 2027). The same swap appears in `SetPremium`,
`SetMedicalPaymentsCharge` and `SetBasicLimitPremium`. *(engine-verified 2026-10-02 — XML diff of
`SetPremOpsExposureCalc`, CW 20260101 V01 vs CW 20270401 V02)*
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
`PremOpsIncrdLimitFactor = 2.05`. *(per GATE-334-PREMISES-OPERATIONS.md § 8; engine-verified
2026-10-02, OK@2025-08-01)* Under the 2027-04-01 filings the key loses its `" CSL"` suffix:
`"OK", 3, "1,000,000", "2,000,000", 2.14` (OK@2027-04-01, `GL_OK_20270401_V04`). A submission still
carrying `"1,000,000 CSL"` misses every 2027 ILF row; the engine's variant builder renormalizes the
limit on the payload side (`scripts/variants.py` `_renormalize_limit`, OI-96/97) rather than
special-casing the lookup. In OK this step is a **state override** (`SetPremOpsIncrdLimitFactor`
sourced from the OK package in every edition rated — governmental-subdivision variant).

---

## Coverage level — rate build-up

Executed by `ErcSetRatesAndFactors` in `GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml`
(gate doc §1b). The steps below follow the **CW 2027 order (29 steps)**. Branch A (pre-2027, 38
steps — the golden case's edition) runs the same rules plus nine more, in a slightly different
order *(engine-verified 2026-10-02)*:

```
Branch A only:  SetSprayPainting                                   (after SetClassCode)
                SetBIILF, SetPDILF                                 (around SetCSLILF)
                SetSplitLimitWeightFactorPremOps{BI,PD,Constant}   (OK golden: 0.83 / 0.19 / 0.03)
                SetDedFactorPremOpsPD250PerClaim
                SetPremOpsPDDeductibleFactorBeforeAdjustment
                SetPremOpsBIPDDeductibleFactorBeforeAdjustment
Order shifts:   SetLCM runs after the deductible overrides (CW 2027: right after SetPremiumBasis);
                SetMedicalPaymentsFactor runs before SetCSLILF (CW 2027: after it).
```

### Step 1 — Class code and premium basis
`SetClassCode` copies from the parent classification, else `""`. `SetPremiumBasis` copies
`PremOpsPremiumBasis`, else `""` — an empty premium basis silently falls to the non-÷1000 branch
(1000× overcharge; see "Referral gate" below).
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 1–2 and § 4)*

### Step 2 — Loss cost multiplier
`SetLCM` — `LookupPremOpsLCM(state, "Y")`, only if not already supplied. No state in the runs
filed its own row; the lookup falls through to the filed countrywide row `"CW","Y",1` (one-row
table, both branches), so `LCM = 1` is a real table value, not a placeholder.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 3; engine-verified 2026-10-02)*

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

**A lookup that misses is a different case, and the engine refuses it (OI-94).** When the class
and territory are present but the lookup (state row, then `"CW"` row) finds nothing, ERC's
`FirstNonNull` exhausts and `PremOpsLossCost` is written **null**, not `0`. ISO's own service
rejects the risk at that point; the kernel (`gl_engine/rating/kernel.py`
`_refuse_null_loss_cost`) does the same in every mode — the rating comes back incomplete with
"PremOpsLossCost resolved to null and the risk cannot be rated … (OI-94)" and no premium. A filed
`0` is left alone. Reproduced: TX@2027-04-01 with size-of-risk on → `PremOpsSizeOfRiskLossCost`
misses (TX never filed it) → refused. *(engine-verified 2026-10-02)*

`PremOpsLossCost` golden-case row: `"OK", "501", "50017", 0.095` (OK@2025-08-01); `0.093`
(OK@2026-08-01 and OK@2026-10-02); `0.09` (OK@2027-04-01, `GL_OK_20270401_V04`).
*(per GATE-334-PREMISES-OPERATIONS.md § 8; engine-verified 2026-10-02)*

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
The table and its key change by branch: Branch A reads `PremOpsClaimsMadeMultiplier` keyed
(State, year, **ClassCode**); Branch B reads `ClaimsMadeMultiplierPremOps` keyed (State, year,
**ClassificationType**). Year 7 on OK class 50017 looks up year `5` in both and returns `0.92`.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 13–14; engine-verified 2026-10-02, OK@2026-10-02
and OK@2027-04-01 claims-made runs)*

### Step 9 — Base rate
`SetBaseRate`:

```
BaseRate = round( LossCost [x BringYourOwnAlcoholExclusionFactor] x LCM
                            [x ClaimsMadeMultiplier] , 3)          # when LossCost <> 0
         = round( ELP x LCM [x ClaimsMadeMultiplier] , 3)          # when LossCost = 0
```
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 15 and "The arithmetic")*

Golden case: `round(0.095 x 1.0, 3) = 0.095`. *(per GATE-334-PREMISES-OPERATIONS.md § 8;
engine-verified 2026-10-02)* Rule body identical in both branches. TX overrides `SetBaseRate`
(TX@2027-04-01 writes `0.087`).

### Step 10 — CSL ILF
`SetCSLILF` — **copies** `../PremOpsIncrdLimitFactor` from the classification level (Step 8 above);
no lookup at this level. Branch A additionally writes `BIILF` and `PDILF` (`SetBIILF`/`SetPDILF`,
both `2.05` on the golden case) for split-limit rating; Branch B has neither rule.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 16; engine-verified 2026-10-02)*

### Step 11 — Medical payments factor
`SetMedicalPaymentsFactor` differs by branch *(engine-verified 2026-10-02 — corrected)*:

```
Branch A:  if no med-pay exclusion (class or location) and ClassCode non-empty:
               MedicalPaymentsFactor = LookupMedPayFactor(CW, ClassCode)       # table MedPayFactor
           else:
               MedicalPaymentsFactor = 0.0          # not 1.0 — harmless, because the charge
                                                    # (Branch A premium) is gated on the same test

Branch B:  if no med-pay exclusion and ClassificationType non-empty
              and MedPay Limit non-empty and MedPay Limit <> "5,000":
               MedicalPaymentsFactor = LookupIncreasedMedPayLimitFactor(CW, ClassificationType, Limit)
           else:
               MedicalPaymentsFactor = 1.0
```

Golden-case (Branch A) row: `"CW", "50017", 1.003`. OK@2027-04-01 (Branch B) row:
`"CW", "Manufacturing Or Processing", "10,000", 1.007` (`IncreasedMedPayLimitFactor`, 20 rows,
limits 10,000 / 15,000 / 20,000 / 25,000 by five classification types).
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 17 and § 8; engine-verified 2026-10-02)*

### Step 12 — BI/PD deductible factors
`SetPremOps{BI,PD}DeductibleFactor` — `LookupDedFactorPremOps{BI,PD}` (keys CW, ILF table#,
deductible). In Branch A the PD side goes through a pre-adjustment stage first:
`SetDedFactorPremOpsPD250PerClaim` → `SetPremOpsPDDeductibleFactorBeforeAdjustment` →
`SetPremOpsPDDeductibleFactor`, and likewise `SetPremOpsBIPDDeductibleFactorBeforeAdjustment` feeds
`SetDeductibleFactor`. The adjustment: when `SprayPainting = "Yes"` or the class is one of
`10075, 10368, 98303–98307, 98309, 99003, 99004` and a deductible is chosen, the factor is
`BeforeAdjustment − DedFactorPremOpsPD250PerClaim`; otherwise it is the before-adjustment factor
unchanged. Branch B has no pre-adjustment stage, no `SprayPainting` and no class carve-out.
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, steps 18–19; engine-verified 2026-10-02 — the
pre-adjustment stage was previously described as Products-only)*

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

The `DeductibleFactor` lookup branch above is the Branch B shape; in Branch A the non-override arm
copies `PremOpsBIPDDeductibleFactorBeforeAdjustment` (adjusted as in Step 12) instead of looking up
directly. *(engine-verified 2026-10-02)*

**Sentinel.** Every "Per Claim" deductible factor in the countrywide table is `0` while every
corresponding "Per Occurrence" row carries a real factor (`0.008`, `0.015`, `0.022`, `0.029`, … on
table 1). Confirmed unchanged in CW 20260101 V01 and CW 20270401 V02: 45 "Per Claim" rows, all `0`.
Guarded only by validation rule `DoMessageMustEnterPremOpsBIPDDeductibleFactorOverride`, not by the
rating chain itself. *(per GATE-334-PREMISES-OPERATIONS.md § 7 item 2; engine-verified 2026-10-02)*

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
`BasicLimitPremium` is `475`, its subline premium `976`).
*(per GATE-334-PREMISES-OPERATIONS.md § 1b, step 29 and § 8; engine-verified 2026-10-02 —
`BasicLimitPremium = 475` and `AnnualBasicLimitsCoPremiumPremOps = 475` on OK@2025-08-01, `450` on
OK@2027-04-01)*

---

## Coverage level — premium

`ErcRate`, Branch A: `SetFinalRate` → `SetMedicalPaymentsCharge` → `SetAdditionalInterestFactor` →
`SetMinimumPremium` → `SetMinPremium` → `SetSpecialCombinedMinimumPremium` →
`SetSpecialCombinedMinPremium` → `SetPremium` → `SetPremiumIndicator`.
`ErcRate`, Branch B: `SetFinalRate` → `SetAdditionalInterestFactor` → `SetPremium` →
`SetPremiumIndicator`. *(engine-verified 2026-10-02)*

### Gate — referral triggers
No rule in either edition raises an explicit gate flag; these are the points where ERC's own data
or rules degrade a referral into a silently-computed number instead (gate doc §7). The engine now
acts on two of them itself — see "What the engine adds" after the list.

1. `PremOpsIncrdLimitTableAssignment = "Refer To Co."` with no override supplied → assignment empty
   → `…Int = 0` → ILF lookup misses. On the classes that carry it (OK: `54444`, `94444`) the
   `PremOpsELPText` selector is also `"Company"`, so the loss cost and ELP are both `0` and
   `BaseRate = 0.000` before the ILF matters; ISO's own `DoMessage` rule adds "Must enter Estimated
   Loss Potential Override for Premises/Operations". Premium `0` (Branch A) or `$1` (Branch B, via
   the floor below). *(engine-verified 2026-10-02: class 54444, OK@2026-10-02 total `0`;
   OK@2027-04-01 total `4` = Prem/Ops `1` + Prods `1` + terrorism `1 + 1`)*
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

**What the engine adds (not ISO rules — the rating layer).** *(engine-verified 2026-10-02)*

- **Null loss cost → refusal (OI-94), every mode.** See Step 4. A missed loss-cost lookup is an
  unratable risk, not a `0`-rated one; the kernel returns an incomplete rating with no premium.
- **Referral register, `underwriting` mode only** (`gl_engine/rating/referrals.py`). On the
  item-1 case above (OK class 54444) it raises `R03` (ISO's `Refer To Co.` sentinel arrived in a
  rated value) and `R29` (ISO's own "Must enter Estimated Loss Potential Override" message is in
  `rating.messages` — a Company-rated class priced at the filed `0`). In the default `strict-erc`
  mode the same submission prices at `0` / `$1` exactly as ISO's rules do, with the message
  surfaced but no referral.

### Branch A — pre-2027 (CW 20231201 V03, 20260101 V01, 20261001 V01, and earlier)
(This is the golden case's edition — parent `GL_CW_20231201_V03` — and, as of 2026-10-02, every
jurisdiction's.)

```
FinalILF = round( CSLILF - FinalDeductibleFactor , 3)            # clamped to 0.0 if <= 0

FinalRate = round( BaseRate x FinalILF [x SizeOfRiskFinalRelativity]
                            x PackageModFactor x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse , 3)

MedicalPaymentsCharge =                                           # SetMedicalPaymentsCharge
    if med-pay excluded (class or location)      : 0
    if GeneralLiabilityMedPayCoverage/Limit <> "10,000" : 0
    if PremOpsLossCost <> 0 and ../PremOpsELP = "Rate/Loss Cost Applies":
        round( PremOpsLossCost [x SizeOfRiskFinalRelativity] x LCM x ClaimsMadeMultiplier
               x (MedicalPaymentsFactor - 1) x PackageModFactor x ExperienceRatingModificationFactor
               x ExpenseModification x ModToUse x Exposure[/1000] , 0)
    elif PremOpsELP <> 0:
        same, with PremOpsELP in place of PremOpsLossCost
    else: 0

MinimumPremium        = LookupPremOpsMinPremium(table#)           # 0 if no ILF table assignment
MinPremium            = round( MinimumPremium x FinalILF x AdditionalInterestFactor , 0)
                                                                  # when ../IfAnyBasis = "No", else 0
SpecialCombinedMinPremium = round( SpecialCombinedMinimumPremium x FinalILF
                                   x AdditionalInterestFactor , 0) # combined subline, IfAnyBasis = "No"

Premium = round( FinalRate x Exposure[/1000] + MedicalPaymentsCharge , 0)
```

*(engine-verified 2026-10-02 — corrected.)* The med-pay charge is built from the **unrounded loss
cost × LCM × claims-made multiplier**, not from `BaseRate`, and only fires at the `10,000` med-pay
limit. `MinPremium` and `SpecialCombinedMinPremium` are computed on the coverage but **not** read by
`SetPremium`; they feed the policy-level top-up below. Every countrywide minimum in the measured
packages is `0` (`PremOpsMinPremium` 3 rows, `SpecialCombinedMinPremium` 1 row), so on filed data
the top-up is `0`. No `$1` floor exists in this branch — a zero-computing premium stays `0`
(OK@2026-10-02 with exposure `1`: Premium `0`).
*(per GATE-334-PREMISES-OPERATIONS.md § 0 and "The arithmetic")*

**Policy-level minimum premium (Branch A only).**
`GeneralLiabilityPremOpsPremiumToReachMinCoverage.ErcRate`:
`CoveragePremium = Σ class Premium`, `MinPremium = max(class MinPremium)`, and — only when the
policy's `PackagePolicy` and `multistate` fields are both present and blank, at least one class has `IfAnyBasis = "No"` and a
non-zero exposure, and a class carries `SpecialCombinedMinPremiumClassIndicator = 1` —
`Premium = max(0, MinPremium − CoveragePremium)`; otherwise `0`. Golden case: `CoveragePremium 976`,
`MinPremium 0`, top-up `0`. In CW 2027 this record holds no premium rules at all.
*(engine-verified 2026-10-02, OK@2025-08-01 trace; rule XML CW 20260101 V01 vs 20270401 V02)*

**Note on `SetMedicalPaymentsCharge` (Branch A) — E12 restated.** The gate read this as one
DataDef compared two ways. The XML shows **two different DataDefs**: the first arm tests
`../PremOpsELP` — the classification-level **text** selector (`"Rate/Loss Cost Applies"`, written
by the classification-level `SetPremOpsELP`) — and the second tests the coverage-level
`PremOpsELP`, a **decimal** ELP. Both are read as ERC writes them; no normalization is needed.
*(per GATE-334-PREMISES-OPERATIONS.md § 3, E12; engine-verified 2026-10-02 — the golden trace writes
`PremOpsELP = 'Rate/Loss Cost Applies'` on the classification and `PremOpsELP = 0` on the coverage)*

### Branch B — CW 2027 (CW 20270401 V01 and V02)
No `SetMedicalPaymentsCharge`, `SetMinimumPremium`, `SetMinPremium` or `SetSpecialCombinedMin*`
rule exists in this edition; medical payments folds into the ILF instead:

```
FinalILF = round( CSLILF + MedicalPaymentsFactor - 1 - FinalDeductibleFactor , 3)
               # only when med-pay is not excluded AND MedPay Limit <> "5,000";
               # otherwise round( CSLILF - FinalDeductibleFactor , 3)
           # clamped to 0.0 if <= 0

FinalRate = round( BaseRate x FinalILF [x SizeOfRiskFinalRelativity]
                            x PackageModFactor x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse , 3)

Premium = round( FinalRate x Exposure[/1000] , 0)

if Premium = 0 and PremOpsCovExposure > 0:
    Premium = 1.0                      # the $1 floor — undocumented in the manual, CW 2027 only
```

The `$1` floor is confirmed in the engine: OK@2027-04-01 with exposure `1` (Gross Sales) →
`FinalRate 0.193 × 0.001` rounds to `0` → `Premium = 1.0`. *(engine-verified 2026-10-02)*
`SetPremium` also only rates when `../Subline = "Premises/Operations and Products/Completed
Operations"`; Branch A also accepted `"Premises/Operations"` alone.

Close to algebraically identical to Branch A: the fold distributes the `(MedicalPaymentsFactor − 1)`
term over the same base. They differ in where rounding lands (and Branch A's charge uses the
unrounded loss cost rather than `BaseRate`), and that moves the answer: on the golden case's
inputs Branch B's arithmetic gives `FinalILF = round(2.05 + 1.003 − 1, 3) = 2.053`,
`FinalRate = round(0.095 × 2.053, 3) = 0.195`, `Premium = 975` against Branch A's `976`. This is
arithmetic on the golden inputs, not an engine run — no filed package pairs the 2025 OK tables with
a CW 2027 parent, and Branch B also changes the med-pay table (`1.007` for the same class at
10,000). The real OK@2027-04-01 engine run is in the quick reference below (`965`).
*(per GATE-334-PREMISES-OPERATIONS.md § 0; re-derived 2026-10-02)*

Also under CW 2027: the ÷1000 divisor set swaps **Passenger Days** for **Kilowatt-hours** (nine
bases in both branches — the gate's "ten vs nine" was wrong). *(engine-verified 2026-10-02)*

### Premium indicator
`SetPremiumIndicator`: `PremiumIndicator = 1` when `Premium <> 0`. Identical in both editions.
*(per GATE-334-PREMISES-OPERATIONS.md § 8)*

### `AdditionalInterestFactor` — edition-dependent consumer
`SetAdditionalInterestFactor` writes it (input, else `1.0`). **In Branch A it is read** by
`SetMinPremium` and `SetSpecialCombinedMinPremium` (`MinimumPremium × FinalILF ×
AdditionalInterestFactor`) — it is not a premium multiplier, but it is not dead either. **In
Branch B nothing reads it**: both minimum-premium rules are gone. Open item E11 therefore narrows
to "CW 2027 only". The engine implements exactly what each edition's XML does — no extra multiplier.
*(per GATE-334-PREMISES-OPERATIONS.md § 1 and § 3, E11; engine-verified 2026-10-02 — corrected)*

---

## Pre-2027 vs. CW 2027 — side by side

| | Branch A — pre-2027 (CW 20231201 V03, 20260101 V01, 20261001 V01) | Branch B — CW 2027 (CW 20270401 V01, V02) |
|---|---|---|
| Coverage chain | 38 steps + `ErcRate` 9 | 29 steps + `ErcRate` 4 |
| `FinalILF` | `round(CSLILF - FinalDeductibleFactor, 3)` | `round(CSLILF + MedicalPaymentsFactor - 1 - FinalDeductibleFactor, 3)` unless med-pay excluded or limit `5,000` |
| Med-pay factor | `MedPayFactor` (CW, ClassCode); `0.0` when excluded | `IncreasedMedPayLimitFactor` (CW, ClassificationType, Limit); `1.0` when excluded / `5,000` / blank |
| Med-pay | separate `MedicalPaymentsCharge` (loss cost-based, `10,000` limit only), 0dp, added inside `SetPremium` | folded into the ILF; **no `SetMedicalPaymentsCharge` rule exists** |
| `SetPremium` | `round(FinalRate x Exposure[/1000] + MedicalPaymentsCharge, 0)` | `round(FinalRate x Exposure[/1000], 0)` |
| Zero-premium floor | none — stays `0` | floored at `$1` when `PremOpsCovExposure > 0` |
| Minimum premium | `SetMinimumPremium`/`SetMinPremium` + special-combined pair on the coverage; policy-level top-up `max(0, Min − Σ)` | **none** — rules removed, policy record holds no premium rules |
| `AdditionalInterestFactor` | read by `SetMinPremium` / `SetSpecialCombinedMinPremium` | read by nothing (E11) |
| Split limits | `SetBIILF`/`SetPDILF` + `SetSplitLimitWeightFactorPremOps{BI,PD,Constant}` | **absent** |
| Deductible | pre-adjustment stage + PD 250 Per Claim carve-out (spray painting / 10 named classes) | direct `DedFactorPremOps{CSL,BI,PD}` lookup |
| Claims-made table | `PremOpsClaimsMadeMultiplier` (State, year, ClassCode) | `ClaimsMadeMultiplierPremOps` (State, year, ClassificationType) |
| ÷1000 premium-basis set | 9 bases incl. Passenger Days | 9 bases incl. Kilowatt-hours (Passenger Days dropped) |
| ILF limit keys | `"1,000,000 CSL"` | `"1,000,000"` (OI-96/97) |
| Elevator/escalator inspection charge (Rule 51 / subline 334) | present, additive premium under classification step G | **absent from the rule list** |
| Golden-case premium (class 50017, territory 501, Gross Sales 5,000,000) | **976** (engine) | **975** (arithmetic on the same inputs; see Branch B) |
| OK engine runs | 976 @2025-08-01; 996 @2026-08-01 and @2026-10-02 | 965 @2027-04-01 |

*(per GATE-334-PREMISES-OPERATIONS.md § 0 and `A2-CW-RULE-CATALOG.md` row 51; every row except the
Rule 51 row engine-verified or XML-diffed 2026-10-02)*

---

## Supporting lookups

| Rule | Matrix | Keys | Layer |
|---|---|---|---|
| `LookupPremOpsLossCost` | `PremOpsLossCost` | State, Territory, ClassCode | **state only** — 0 CW rows |
| `LookupILFPremOps` | `ILFPremOps` | State, ILF table#, occurrence limit, general aggregate limit | **state only** — 0 CW rows |
| `LookupPremOpsIncrdLimitTableAssignment` | `PremOpsIncrdLimitTableAssignment` | State, ClassCode | **state only** — 0 CW rows |
| `LookupPremOpsHomogeneityIndex` | `PremOpsHomogeneityIndex` | State, ClassCode | state |
| `LookupPremOpsELP` | `PremOpsELP` | State, ClassCode | state |
| `LookupMedPayFactor` (Branch A) | `MedPayFactor` | CW, ClassCode | **countrywide only** — 1,188 rows (header-only in CW 2027) |
| `LookupIncreasedMedPayLimitFactor` (Branch B) | `IncreasedMedPayLimitFactor` | State/CW, ClassificationType, med-pay limit | **countrywide only** — 20 rows; replaces `MedPayFactor` |
| `LookupDedFactorPremOpsCSL` / `...BI` / `...PD` | `DedFactorPremOpsCSL` / `BI` / `PD` | State, table#, deductible | **countrywide only** — 93 rows each, both branches |
| `LookupPremOpsClaimsMadeMultiplier` | `PremOpsClaimsMadeMultiplier` (Branch A) / `ClaimsMadeMultiplierPremOps` (Branch B) | State, year (capped at 5), ClassCode (A) / ClassificationType (B) | CW rows resolve in OK |
| `LookupPremOpsLCM` | `PremOpsLCM` | State, `"Y"` | **countrywide** — one row `"CW","Y",1`; the golden case's `1.0` is this filed row (engine-verified), not an engine placeholder |
| `LookupPremOpsELPText` (classification level) | `PremOpsELPText` | State, ClassCode | **state only** — the rating-basis selector, same vocabulary as Products' |
| `LookupBringYourOwnAlcoholExclusionFactor` | BYOA exclusion table | class codes `16905`/`16906` + `GeneralLiabilityAmndmtOfLiquorLiabExcl` presence | not further specified in source |
| `LookupPremOpsSizeOfRiskLossCost` | size-of-risk loss cost table | not detailed | — |
| `LookupPremOpsSizeOfRiskRelativity` | size-of-risk relativity table | class-keyed | — |
| `LookupPremOpsMinPremium` (Branch A only) | `PremOpsMinPremium` | table# | **countrywide only** — 3 rows, all `0`; header-only and unread in CW 2027 |
| `LookupSpecialCombinedMinPremium` (Branch A only) | `SpecialCombinedMinPremium` | `"Y"` | **countrywide only** — 1 row, `0` |
| `LookupClassificationType` | `ClassificationType` | ClassCode | **countrywide only** — 1,188 rows pre-2027, 1,163 in CW 2027 |

Every `Lookup` in this ruleset follows the same two-pass pattern documented for CF —
`FirstNonNull(state row, "CW" row)` — but ERC expresses it as `FirstNonNull` of two `Lookup` calls
against the *same table*, first keyed on `/*/State/Code` then on the literal `"CW"`. A single
resolved table therefore carries both state and countrywide rows, falling back row by row — this is
a second inheritance mechanism distinct from overriding a whole table by name at the package layer.
*(per GATE-334-PREMISES-OPERATIONS.md § 5)*

---

## State deviations

Gate census, not re-measured on 2026-10-02 (spot-checked only: OK's `SetPremOpsIncrdLimitFactor`
and TX's `SetBaseRate` overrides are both live in the engine trace at 2027-04-01; KY's
`SetBIILF`/`SetPDILF` override rules that also exist in the Branch A countrywide file, so the KY
row describes a replacement, not an addition). Measured across all 572 packages / 51
jurisdictions, indexing every `rul:Rule Name` in each
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

## Quick reference — end-to-end, Branch A / pre-2027 (Oklahoma golden case)

OK@2025-08-01, `GL_OK_20250601_V01` over `GL_CW_20231201_V03`; every bracketed value below is the
engine trace's own write *(engine-verified 2026-10-02)*.

```
LossCost   = lookup PremOpsLossCost(State, Territory, ClassCode)          [OK/501/50017: 0.095]
LCM        = lookup PremOpsLCM(State, "Y")  -> falls back to CW row        [CW/Y: 1]
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

MedicalPaymentsCharge = round(LossCost x LCM x CMM x (MedPayFctr - 1) x mods x Exposure[/1000], 0)
                         # MedPay limit 10,000                    [round(0.095x1x1x0.003x5000,0)=1]

MinimumPremium = lookup PremOpsMinPremium(CW, 3)                          [0]
MinPremium = round(MinimumPremium x FinalILF x AdditionalInterestFactor, 0) [0]

Premium    = round(FinalRate x Exposure[/1000] + MedicalPaymentsCharge, 0)
                                                                            [round(0.195x5000+1,0) = 976]

Policy: PremOpsPremiumToReachMin top-up = 0 (MinPremium 0 <= CoveragePremium 976)
        Prem/Ops 976 + Prods 6,845 + terrorism 2 + 16 = 7,839
```

Every value above reproduces the ISO published output exactly, and the engine reproduces it.
*(per GATE-334-PREMISES-OPERATIONS.md § 8; engine-verified 2026-10-02)*

The same Branch A arithmetic on ISO's 2026 OK STC example (OK@2026-08-01, `GL_OK_20260801_V01`
over `GL_CW_20260101_V01`) — and on the engine base at OK@2026-10-02 (`GL_OK_20261001_V01` over
`GL_CW_20261001_V01`) — gives `LossCost 0.093`, `CSLILF 2.14` (`"1,000,000 CSL"`), `FinalILF 2.140`,
`FinalRate 0.199`, `MedicalPaymentsCharge 1`, `BasicLimitPremium 465`, **`Premium 996`**. ISO's
published output for that example totals **`8,229`** (Prem/Ops 996, Prods 7,215, terrorism 18), and
the engine reproduces it on `Engine_Payloads/OK/submission.json` (eff 2026-08-01, terrorism
"No"). ISO's sample *input* says terrorism "Yes" while its output says "No" (known mismatch,
`tests/verify_stage3.py` F3); rated literally, that input gives `8,244` (terrorism 4 + 29).
*(engine-verified 2026-10-02)*

## Quick reference — end-to-end, Branch B / CW 2027

OK@2027-04-01, `GL_OK_20270401_V04` over `GL_CW_20270401_V02`, class 50017, territory 501, Gross
Sales 5,000,000, `1,000,000 / 2,000,000`, med-pay 10,000 *(engine-verified 2026-10-02)*:

```
LossCost   = lookup PremOpsLossCost(State, Territory, ClassCode)          [OK/501/50017: 0.09]
LCM        = lookup PremOpsLCM(State, "Y")  -> CW row                     [1]
BaseRate   = round(LossCost x LCM [x ClaimsMadeMultiplier], 3)            [0.090]

CSLILF     = lookup ILFPremOps(State, table#, occLimit, aggLimit)         [OK,3,"1,000,000","2,000,000": 2.14]
MedPayFctr = lookup IncreasedMedPayLimitFactor(CW, ClassificationType, MedPayLimit)
                                                  [CW, Manufacturing Or Processing, 10,000: 1.007]

FinalILF   = round(CSLILF + MedPayFctr - 1 - FinalDeductibleFactor, 3)   # clamped to 0.0 if <= 0
                                                                          [2.147]
FinalRate  = round(BaseRate x FinalILF [x SizeOfRiskFinalRelativity] x PackageModFactor
                    x ExperienceRatingModificationFactor x ExpenseModification x ModToUse, 3)
                                                                          [round(0.09x2.147,3)=0.193]
BasicLimitPremium = round(BaseRate x (1-FinalDeductibleFactor) x Exposure/1000, 0)   [450]

Premium    = round(FinalRate x Exposure[/1000, nine bases — Kilowatt-hours in, Passenger Days out], 0)
                                                                          [round(0.193x5000,0) = 965]
if Premium = 0 and PremOpsCovExposure > 0:
    Premium = 1.0                                                        # CW 2027 floor

Policy: Prem/Ops 965 + Prods 7,215 + terrorism = 8,198 (no minimum-premium top-up exists)
```

The same chain under `GL_CW_20270401_V01` (TX@2027-04-01, `GL_TX_20270401_V01`): TX's own
`SetBaseRate` → `0.087`, `CSLILF 2.05`, `MedPayFctr 1.007`, `FinalILF 2.057`, `FinalRate 0.179`,
**`Premium 895`**. *(engine-verified 2026-10-02)*

---
