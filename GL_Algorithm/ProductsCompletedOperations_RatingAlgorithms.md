# Products/Completed Operations — Rating Algorithms

**Source:** `docs/gates/GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md` (differential gate, PASSED), read
against `docs/gates/GATE-334-PREMISES-OPERATIONS.md` (shared classification machinery, resolver,
inheritance mechanisms, rounding sites — 336 does not restate these, and neither does this
document except where the two sublines diverge).

**Line:** General Liability (GL), Subline 336 — Products/Completed Operations Liability Coverage.
Manual Rule 48.I (`docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.2.2). ERC golden case runs on
state package `GL_OK 20250601 V01`, declared countrywide parent `GL_CW_20231201_V03`. **336's
`FinalILF` formula is identical in every edition** — unlike 334, there is no medical-payments fold,
because 336 has no medical-payments term at all (GATE-336 §1). **The rest of the chain is not
edition-stable** *(engine-verified 2026-10-02 — corrected)*: diffing every rule in
`GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml` gives the same two variants
as 334 — **pre-2027** (`GL_CW_20231201_V03` = `GL_CW_20260101_V01` = `GL_CW_20261001_V01`) and
**CW 2027** (`GL_CW_20270401_V01` = `GL_CW_20270401_V02`). CW 2027 drops the minimum-premium,
split-limit, spray-painting and deductible pre-adjustment rules and **adds a `$1` floor** to
`SetPremium`. Which variant a quote gets is decided by the effective date (decision A3) and an
optional `package_version` pin, through the state package's declared parent — see the
Premises/Operations document for the per-jurisdiction parents at 2026-10-02 and 2027-04-01.

**Documented:** 2026-08-20
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — OK golden (OK@2025-08-01, over `GL_CW_20231201_V03` → 6,845), OK ISO STC (OK@2026-08-01, over `GL_CW_20260101_V01` → 7,215; policy 8,229 = ISO output), OK@2027-04-01 (`GL_OK_20270401_V04` over `GL_CW_20270401_V02` → 7,215), TX@2027-04-01 (over `GL_CW_20270401_V01` → 6,845) and CA@2027-04-01 (over `GL_CW_20231201_V02` → 6,845) rated offline, plus a `$1`-floor probe and a Refer-To-Co. class (54444) in both branches; every rule in the coverage file diffed across the five CW editions. Corrections are marked *(engine-verified 2026-10-02)*.

This began as a reformat of the gates. On 2026-10-02 its step lists, formulas, rounding points,
edition claims and worked numbers were re-verified against the built engine (`gl_engine/`) and the
CW rule XML; the corpus-wide census figures (row-agreement counts, 13/19-jurisdiction DWL
footprint, `N/A` and `Not Applicable` row totals) are still the gate's own and were not re-measured.

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
    ErcSetRatesAndFactors     (35 steps pre-2027 / 28 steps CW 2027 — vs 334's 38 / 29)
    ErcRate                   (6 steps  pre-2027 / 4 steps  CW 2027 — vs 334's 9 / 4)
        pre-2027: SetFinalRate, SetAdditionalInterestFactor, SetMinimumPremium, SetMinPremium,
                  SetPremium, SetPremiumIndicator
        CW 2027:  SetFinalRate, SetAdditionalInterestFactor, SetPremium ($1 floor), SetPremiumIndicator

GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverageRules.Rule.xml   (policy level)
    pre-2027: ErcRate → SetCoveragePremium, SetMinPremium, SetPremium (min-premium top-up)
    CW 2027:  no premium rules
```

*(engine-verified 2026-10-02 — the gate compared 336's pre-2027 chain against 334's CW 2027 chain,
which is why it reported several shared steps as Products-only)*

336's coverage-level chain runs the same order and the same `if IsNull` override-guard idiom as
334's (GATE-334 §1b), with Prod/CompOps-named datadefs in place of PremOps-named ones. **Compared
edition-for-edition**, the genuine differences are few *(engine-verified 2026-10-02 — corrected)*:

**Steps 336 has that 334 does not (both editions):**

| Rule | Effect |
|---|---|
| `SetTerritory` | copies `../../../ProdsCompldOpsTerritory` — a second, independent territory. Statewide `999` in every one of the 51 jurisdictions (`03-SUBLINE-COVERAGE-PLAN.md` §3.2.2, point 1); OK trace writes `Territory = '999'` |
| `SetDefenseWithinLimitsBasicLimitMultiplier` | a fourth base-rate factor; switched off (empty override) in 13 jurisdictions today, 19 across all editions — §6 below |

**Steps 334 has that 336 does not:** `SetBringYourOwnAlcoholExclusionFactor` (liquor classes
16905/16906 only — not a 336 concept), `SetMedicalPaymentsFactor`, and — pre-2027 only —
`SetMedicalPaymentsCharge`, `SetBIILF`/`SetPDILF` and `SetSpecialCombinedMinimumPremium` /
`SetSpecialCombinedMinPremium`; `SetFinalPremOpsIncrdLimitTableAssignmentInt` (336's assignment is
a letter and is never converted).

**Shared by both sublines, pre-2027 only (removed from both in CW 2027)** — previously listed here
as Products-only: `SetSprayPainting`; `SetSplitLimitWeightFactor{Prods,PremOps}{BI,PD,Constant}`
(Products `0.87`/`0.17`/`0.01`, Prem/Ops `0.83`/`0.19`/`0.03` on OK class 50017 — confirmed in the
golden trace); `SetDedFactor{Prods,PremOps}PD250PerClaim`; the `…DeductibleFactorBeforeAdjustment`
pre-adjustment stage; and `SetMinimumPremium` + `SetMinPremium` inside `ErcRate` — **334 computes
its own minimum too** in the pre-2027 editions.

---

## File map

| Piece | File | Anchor |
|---|---|---|
| Classification-level prep (shared) | `GeneralLiabilityClassificationRules.Rule.xml` | `ErcSetRatesAndFactors` — 42-step chain, per-subline steps not individually cited by line in source |
| Rate build-up, coverage level | `GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml` | `ErcSetRatesAndFactors` — 35 steps pre-2027 / 28 CW 2027 (`SetBaseRate`, `SetCSLILF`, `SetFinalILF`, `SetBasicLimitPremium` live here) |
| Premium calc | `GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml` | `ErcRate` — pre-2027 6 steps (`SetFinalRate` → `SetAdditionalInterestFactor` → `SetMinimumPremium` → `SetMinPremium` → `SetPremium` → `SetPremiumIndicator`); CW 2027 4 steps (no minimum rules; `SetPremium` gains the `$1` floor) |
| Policy-level minimum-premium top-up (pre-2027 only) | `GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverageRules.Rule.xml` | `SetCoveragePremium`, `SetMinPremium`, `SetPremium` |
| Rating-basis selector | same file | `LookupProdsCompldOpsELPText` — closed vocabulary, GATE-336 §0 |
| Base rate tables | `ProdsCompldOpsLossCost.RateTable.csv`, `ProdsCompldOpsELPFactor.RateTable.csv` | state-filed, see ERC_Tables doc |
| ILF table assignment + factor | `IncreasedLimitsTableAssignmentProdsCompldOps.RateTable.csv`, `ILFProds.RateTable.csv` | state-filed |
| Minimum premium (pre-2027 only) | `ProdsCompldOpsMinPremium.RateTable.csv` | countrywide only, 3 rows, all `0`; header-only and unread in CW 2027 |
| Coverage form attachment only — **no rating** | form/endorsement catalog, `CG 00 37` / `CG 00 38` Products/Completed Operations Liability Coverage Form | `docs/rating-engine/A2-CW-RULE-CATALOG.md` line 51, `A3-ENDORSEMENT-CATALOG.md` lines 446–447 |
| Defense-Within-Limits endorsement | `CG 34 76` Defense Within Limits Products/Completed Operations Endorsement | `A3-ENDORSEMENT-CATALOG.md` line 494, `OPTIONAL_RTC` |
| Related, factor-derived (not rated independently) | Product Withdrawal (Subline 365) | derived from 336's ILTA via a Product Withdrawal Factor — `03-SUBLINE-COVERAGE-PLAN.md` §3.2.6 |

---

## Products/Completed Operations — rate build-up

Executed by `ErcSetRatesAndFactors` (35 steps pre-2027 / 28 CW 2027) then `ErcRate` (6 / 4 steps)
in `GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml`. The step-by-step list below is
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
§0). New rule **N17** proposed that the engine read `ProdsCompldOpsELPText` and assert agreement
with the `LossCost != 0` test as a load-time hard failure.

**What the built engine does instead** *(engine-verified 2026-10-02)*: it runs ISO's own rules and
nothing more. The classification-level `SetProdsCompldOpsELP` reads `ProdsCompldOpsELPText` into
the classification's `ProdsCompldOpsELP` (`'Industry'` on the golden case) and
`SetFinalProdsCompldOpsELP` looks up the numeric ELP (`0.82`); `SetBaseRate` then branches on
`LossCost == 0` exactly as ERC writes it. There is **no N17 assertion in `gl_engine/`**. In
`GL_OK_20270401_V04` the selector and the `N/A` assignment agree row-for-row (400 / 400), so the
assertion would not have fired there. A missing loss-cost **row** (null, not `0`) is a different
case and is refused (OI-94 — see "Referral triggers").

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
`SetYearInClaimsMade` value. Table and key change by edition: pre-2027
`ProdsCompldOpsClaimsMadeMultipliers` (State, year, ClassCode); CW 2027
`ClaimsMadeMultiplierProdsCompldOps` (State, year, ClassificationType). OK@2027-04-01, year 7 →
year 5 → `0.89` → `BaseRate 0.730`. *(engine-verified 2026-10-02)*

`LCM` — `LookupProdsCompldOpsLCM(state, "Y")`, answered by the countrywide row `"CW","Y",1` in every
edition (no OK row). *(engine-verified 2026-10-02)*

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

`ILFProds` limit keys follow the same filing change as 334's: `"1,000,000 CSL"` pre-2027 (golden:
`OK, B, 1,000,000 CSL, 2,000,000 CSL → 1.67`), `"1,000,000"` from the 2027-04-01 filings
(`OK, B, 1,000,000, 2,000,000 → 1.76`, `GL_OK_20270401_V04`; OI-96/97). In OK the classification-level
`SetProdsCompldOpsIncrdLimitFactor` is a state override, as 334's is. *(engine-verified 2026-10-02)*

Split-limit inputs (not exercised by the CSL golden case) go through
`SetSplitLimitWeightFactorProds{BI,PD,Constant}` — **pre-2027 editions only** (removed in CW 2027,
together with 334's equivalent), confirmed against the manual at `0.87`/`0.17`/`0.01` for the
Manufacturing band `50000–59999` (GATE-336 §2) — vs 334's `0.83` / `0.19` / `0.03` for the same
band, a genuine per-subline weighting, not a shared table. Both triples are written on every
pre-2027 quote, including the CSL golden case. *(engine-verified 2026-10-02)*

### Step 5 — Deductible
Per GATE-336 § "Steps 336 has that 334 does not"

```
pre-2027 only (334 has the identical stage — not Products-only):
SetDedFactorProdsPD250PerClaim                                # DedFactorProdsPD @ "250 Per Claim"
SetProdsCompldOpsBIPDDeductibleFactorBeforeAdjustment         # LookupDedFactorProdsCSL(table letter, deductible)
SetDeductibleFactor                                           # adjusted (below)
SetProdsCompldOpsBIDeductibleFactor                           # LookupDedFactorProdsBI
SetProdsCompldOpsPDDeductibleFactorBeforeAdjustment           # LookupDedFactorProdsPD
SetProdsCompldOpsPDDeductibleFactor                           # adjusted (below)

CW 2027:
SetDeductibleFactor  = override | LookupDedFactorProdsCSL    # no pre-adjustment, no carve-out
SetProdsCompldOps{BI,PD}DeductibleFactor = LookupDedFactorProds{BI,PD}
```

**The pre-adjustment shape, now read from the XML** *(engine-verified 2026-10-02 — previously
"not resolved")*: a non-zero override wins. Otherwise, when `SprayPainting = "Yes"` or the class is
one of `10075, 10368, 98303–98307, 98309, 99003, 99004`, the factor is `0.0` at "No Deductible" and
`BeforeAdjustment − DedFactorProdsPD250PerClaim` for any other deductible; for every other class it
is the before-adjustment factor unchanged. The PD side follows the same pattern. All three
`DedFactorProds{CSL,BI,PD}` tables are 93 CW rows keyed (CW, table letter, deductible); the golden
trace reads `['CW','B','No Deductible'] → 0`.

`FinalDeductibleFactor` is combined from the BI/PD components the same way as 334's
`SetFinalDeductibleFactor` (GATE-334 §1b step 21): combined ⇒ the combined factor; split BI+PD ⇒
sum; one side only ⇒ that side; else `0.0`.

### Step 6 — Final ILF
Per GATE-336 § "The arithmetic"

```
FinalILF = round( CSLILF − FinalDeductibleFactor , 3)      # clamped to 0.0 if ≤ 0
```

**No medical-payments term in either edition.** This is the point of divergence from 334: 334's
`FinalILF` gains a `[+ MedicalPaymentsFactor − 1]` bracketed term under the CW 2027 parents
(`GL_CW_20270401_V01` and `V02`) only (GATE-334 §0); 336 never does, in any edition — `SetFinalILF`
is the one rule in this file that is byte-identical across all five CW editions checked. The rest of
336's chain is **not** edition-stable (see Steps 5, 8, 9) — GATE-336 §1's own caution ("the edition
axis is real but not uniform, and must be established per coverage rather than assumed from 334")
applies within 336 too. *(engine-verified 2026-10-02)*

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
BasicLimitPremium = round( BaseRate × (1 − FinalDeductibleFactor)
                           [× ProdsCompldOpsSizeOfRiskFinalRelativity] × PackageModFactor
                           × Exposure[/1000] , 0)

pre-2027:  Premium = round( FinalRate × Exposure[/1000] , 0)          # Subline must be Prods or combined
CW 2027:   p = round( FinalRate × Exposure[/1000] , 0)                 # combined subline only
           Premium = 1.0  if p = 0 and ProdsCompldOpsCov <> "Included" and ProdsCompldOpsCovExposure > 0
                   = p    otherwise
```

*(engine-verified 2026-10-02 — corrected.)* **336 has a `$1` floor under CW 2027**, the same shape as
334's plus a `ProdsCompldOpsCov <> "Included"` guard. GATE-336 §4's "no floor in either edition" is
true only of the pre-2027 editions. Reproduced: OK@2027-04-01 with exposure `1` →
`FinalRate 1.443`, product rounds to `0`, `Premium = 1.0`; the same submission at OK@2026-10-02 →
`Premium 0`. The ÷1000 basis set is nine bases in both editions, swapping Passenger Days
(pre-2027) for Kilowatt-hours (CW 2027), as in 334. Golden case: `BasicLimitPremium 4,100`
(`AnnualBasicLimitsCoPremiumProdCompldOps`), a reporting quantity as in 334.

### Step 9 — Minimum premium (pre-2027 only)
Per GATE-336 §1, "E11 is answered"

```
MinimumPremium = LookupProdsCompldOpsMinPremium(table letter)            # CW, 3 rows, all 0
MinPremium     = round( MinimumPremium × FinalILF × AdditionalInterestFactor , 0)
                 # only when ../IfAnyBasisProdsCompldOps = "No", else 0
```

Computed **inside `ErcRate`** in the pre-2027 editions — **and 334 has the same step there**
(`SetMinimumPremium`/`SetMinPremium`, plus a special-combined pair). Neither subline has any
minimum-premium rule under CW 2027. `MinPremium` is not read by `SetPremium`; it feeds the pre-2027
policy-level `GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverage` top-up
(`max(0, MinPremium − Σ class Premium)` under the same package/multistate/`IfAnyBasis` gate as
334's), which is `0` on filed data (golden: `CoveragePremium 6,845`, `MinPremium 0`).
*(engine-verified 2026-10-02 — corrected)*

E11 restated: `AdditionalInterestFactor` is read by **both** sublines' `SetMinPremium` pre-2027, and
by **neither** under CW 2027. The open question is therefore whether CW 2027's removal of the
minimum-premium rules (and with them the only consumer of the factor) is intended — not a
334-vs-336 asymmetry.

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

**The built engine does not implement this branch** *(engine-verified 2026-10-02 — finding)*. It
follows ERC's rules, which have no not-offered outcome: on OK class `10015` (`ILTA = "N/A"`,
`ELPText = "Not Applicable"`, loss cost `0`, ELP `0`) the assignment is blanked, `BaseRate = 0.000`
and the subline prices at **`0` pre-2027** (OK@2026-10-02) and **`$1` under CW 2027**
(OK@2027-04-01 — the new floor fires because `ProdsCompldOpsCov` is not `"Included"`), with no
message and **no referral in either `strict-erc` or `underwriting` mode** (the register has no
entry for `N/A` / `Not Applicable`). `gl_engine/domain/cell.py` defines a `NOT_OFFERED`
disposition, but the rating path does not use it.

### Referral triggers
Per GATE-336 §7 — every path that must not silently produce a number:

1. **`IncreasedLimitsTableAssignmentProdsCompldOps = "Refer To Co."`** — same degraded-referral
   mechanism as 334: if the override substitute is absent, the assignment is empty, the ILF lookup
   misses, and the premium becomes `0` (pre-2027) or `$1` (CW 2027 floor). Present in **all 51
   jurisdictions, exactly 2 class codes each** (in Oklahoma: `54444` and `94444`, the catch-all
   "not otherwise classified" codes) — "a standing, universal referral on the classes most likely
   to be selected for an unusual risk." These classes are also `ELPText = "Company"`, so ISO's own
   rules add "Must enter Estimated Loss Potential Override for Products/Completed Operations".
   *(engine-verified 2026-10-02, OK class 54444: total `0` at OK@2026-10-02, `4` at OK@2027-04-01;
   in `underwriting` mode the referral register raises `R03` (refer sentinel) and `R29`
   (ELP-override message))*
2. **`Assignment = "N/A"`** — 21,021 rows, 35% of the table. Not offered for that class. 334 has no
   equivalent value in its own ILTA table.
3. **`ELPText = "Not Applicable"`** — 261,973 rows in `ProdsCompldOpsELPText`. Must agree with (2)
   per N17.
4. **`FinalILF ≤ 0` → clamped to `0.0`.** ERC clamps rather than errors.
5. **`ProdsCompldOpsCovExposure` exceeding `PremOpsCovExposure`** — cross-subline validation, §4
   above.
6. **A loss cost that resolves to null** (no state row and no `CW` row — e.g. size-of-risk on in a
   jurisdiction that never filed `…SizeOfRiskLossCost`) — the engine refuses the rating in every
   mode (OI-94, `gl_engine/rating/kernel.py`); TX@2027-04-01 with size-of-risk on reports both
   `PremOpsLossCost` and `ProdsCompldOpsLossCost` null. A filed `0` (the OK golden case) is not
   refused. *(engine-verified 2026-10-02)*

Of these, the engine acts on 1 (`underwriting` mode, R03/R29) and 6 (always). 2 and 3 price at
`0` / `$1` without a referral — see Branch C.

---

## Products/Completed Operations vs Premises/Operations — side by side

Both sublines share the classification rule set, the resolver, and the two inheritance mechanisms
(GATE-336 opening). The table below is built entirely from the two gates' own delta lists —
GATE-334 §1/§0/§7 and GATE-336 §1/§0/§4/§5/§6.

*(Rows marked † were corrected 2026-10-02 against the engine and the rule XML of all five CW
editions; the gate had compared 336's pre-2027 chain with 334's CW 2027 chain.)*

| | Premises/Operations (334) | Products/Completed Operations (336) |
|---|---|---|
| Coverage-level chain length † | pre-2027 38 + `ErcRate` 9; CW 2027 29 + 4 | pre-2027 35 + `ErcRate` 6; CW 2027 28 + 4 |
| Territory | `PremisesOperationsTerritory`, varies by risk | `ProdsCompldOpsTerritory`, statewide `999` in all 51 states |
| Claims-made adjustment | present | present, and Rule 48.D.6 makes it explicit with its own table |
| Defense-Within-Limits multiplier | none | 4th base-rate factor, gated on **row presence**, not a flag |
| Split-limit weights (Mfg `50000–59999`) † | BI `0.83` / PD `0.19` / Constant `0.03` — pre-2027 only | BI `0.87` / PD `0.17` / Constant `0.01` — pre-2027 only |
| Medical payments | separate factor/charge pre-2027; folded into `FinalILF` in CW 2027 | **none — not a 336 concept at all** |
| `FinalILF` edition split | yes — CW 2027 folds med-pay in, pre-2027 does not | **no — identical formula in every edition** |
| Minimum premium † | pre-2027: `SetMinimumPremium`/`SetMinPremium` + special-combined pair in `ErcRate`; CW 2027: none | pre-2027: `SetMinimumPremium`/`SetMinPremium` in `ErcRate`; CW 2027: none |
| `AdditionalInterestFactor` † | read by `SetMinPremium` pre-2027; unread in CW 2027 (E11) | same — read pre-2027, unread in CW 2027 |
| `$1` floor on zero premium † | CW 2027 only, when `PremOpsCovExposure > 0` | CW 2027 only, when `ProdsCompldOpsCovExposure > 0` and `ProdsCompldOpsCov <> "Included"` |
| Deductible pre-adjustment / PD 250 Per Claim carve-out † | pre-2027 only | pre-2027 only |
| Spray painting qualifier † | pre-2027 only | pre-2027 only |
| Liquor-exclusion factor | `SetBringYourOwnAlcoholExclusionFactor`, classes 16905/16906 | none |
| ILTA vocabulary | numeric-as-string `1`/`2`/`3`, `SetFinalPremOpsIncrdLimitTableAssignmentInt` converts | alphabetic `A`/`B`/`C`, **no `…Int` conversion rule exists** |
| ILTA non-value | `Refer To Co.` only | `Refer To Co.` **and** `N/A` (coverage not offered) |
| ELP-selector table | `PremOpsELPText` | `ProdsCompldOpsELPText` — same closed vocabulary; N17 proposed but not implemented in the engine † |
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
| `SetSplitLimitWeightFactorProds{BI,PD,Constant}` (pre-2027 only) | split-limit weighting when not CSL | — (values confirmed at 0.87/0.17/0.01 for Mfg band; written on the golden trace) |
| `LookupProdsCompldOpsLCM` | `LCM` | **countrywide only** — one row `"CW","Y",1` |
| `LookupProdsCompldOpsClaimsMadeMultipliers` | `ClaimsMadeMultiplier` | `ProdsCompldOpsClaimsMadeMultipliers` (State, year, ClassCode) pre-2027 / `ClaimsMadeMultiplierProdsCompldOps` (State, year, ClassificationType) CW 2027; CW rows |
| `LookupDedFactorProds{CSL,BI,PD}` | deductible factors (and, pre-2027, the PD `250 Per Claim` cell) | **countrywide only**, 93 rows each, keyed CW, table letter, deductible |
| `LookupProdsCompldOpsMinPremium` (pre-2027 only) | `MinimumPremium` input to `SetMinPremium` | **countrywide only**, 3 rows, all `0`; header-only in CW 2027 |
| `GeneralLiabilityDefenseWithinLimitsProdsCompldOpsTable` (row existence) | gates the DWL multiplier | row-presence check, not a value lookup |

Every lookup in this ruleset follows 334's two-pass pattern: try the state-specific row keyed on
`/*/State/Code`, then fall back to a `CW` row (`FirstNonNull`) — GATE-334 §5, reused unchanged by
336.

---

## Quick reference — end-to-end, Oklahoma golden case

Class `50017`, territory `999` (statewide), Gross Sales `5,000,000`, `1,000,000 / 2,000,000 CSL`,
occurrence form, no deductible, no size-of-risk. Reproduces GATE-336 §8 exactly, `Premium =
6,845.00` — and the engine reproduces every value below on OK@2025-08-01 (`GL_OK_20250601_V01` over
`GL_CW_20231201_V03`, pre-2027 branch). *(engine-verified 2026-10-02)*

```
ILTA           = lookup IncreasedLimitsTableAssignmentProdsCompldOps(OK, 50017)        = "B"

LossCost       = lookup ProdsCompldOpsLossCost(OK, 999, 50017)                         = 0.0   (published zero)
ELPText        = lookup ProdsCompldOpsELPText(OK, 50017)                               = "Industry"   -> ELP path
ELP            = lookup ProdsCompldOpsELPFactor(OK, 50017)                             = 0.82

DWL multiplier = 1.0   (not overridden in OK; no DWL row present)

LCM            = lookup ProdsCompldOpsLCM(OK, "Y") -> CW row                           = 1

BaseRate       = round(ELP x LCM, 3)        # no DWL row → the non-DWL arm; no factor applied
               = round(0.82 x 1, 3)                                                    = 0.820

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

**Policy reconciliation** (with subline 334 and terrorism, GATE-336 §8; engine-verified 2026-10-02):

```
334 Premises/Operations             976.00
336 Products/Completed Operations 6,845.00
Terrorism (Prem/Ops 2 + Prod/CompOps 16)  18.00
ProdsCompldOpsPremiumToReachMin top-up      0     (pre-2027 policy-level rule; MinPremium 0)
ErcCalculatedTotalPremium         7,839.00
```

## Quick reference — the same risk under later editions

*(engine-verified 2026-10-02)*

```
                       OK@2026-08-01 (ISO STC)     OK@2027-04-01
packages               GL_OK_20260801_V01 over     GL_OK_20270401_V04 over
                       GL_CW_20260101_V01 (pre-27) GL_CW_20270401_V02 (CW 2027)
ELP                    0.82                        0.82
BaseRate               0.820                       0.820
CSLILF (ILFProds B)    1.76  ("… CSL" keys)        1.76  (suffix-free keys)
FinalILF               1.760                       1.760
FinalRate              round(0.82x1.76,3) = 1.443  1.443
BasicLimitPremium      4,100                       4,100
MinPremium             0 (computed)                — (rule absent)
Premium                7,215                       7,215  ($1 floor available, not triggered)
Policy total           8,229 = ISO output          8,198 (Prem/Ops 965)
```

The two editions agree on this risk because nothing that changed (minimums, split limits,
deductible pre-adjustment, the floor) is exercised by it. TX@2027-04-01 (`GL_CW_20270401_V01`) and
CA@2027-04-01 (`GL_CW_20231201_V02`) both rate 336 at `6,845` (ILF `1.67`).
