# Gate — Subline 334, Premises/Operations

**Build-order item 1** (`GL-RATING-ENGINE-BUILD-PLAN.md` §8). Presented against the eight-point
per-subline gate in §9.

**Status: PASSED.** The algorithm is derived end to end from ERC, confirmed at four points by the
filed manual, and reproduces the Oklahoma golden case exactly — `Premium = 976.00`, with every
intermediate value traced to a named rule and a named table row.

**Doctrine:** ERC is the source. The manual confirms and never sources. Nothing is assumed. Every
step below cites the ERC file it came from; every confirmation cites a PDF, notice and page.

---

## 0. The finding that changes the build

**The 334 algorithm is not one algorithm. It is two, and the edition decides which.**

The premium chain in §6 of the build plan was written from the countrywide 2027 edition. The
golden case runs on `GL_OK 20250601 V01`, whose XSD names `GL_CW_20231201_V03` as its parent — and
that edition computes medical payments **differently**:

| | CW 2023 V03 (and earlier) | CW 2027 V01 |
|---|---|---|
| `FinalILF` | `round(CSLILF − FinalDeductibleFactor, 3)` | `round(CSLILF + MedicalPaymentsFactor − 1 − FinalDeductibleFactor, 3)` |
| Med-pay | separate `MedicalPaymentsCharge`, rounded to 0dp, **added inside** `SetPremium` | folded into the ILF; **no `SetMedicalPaymentsCharge` rule exists** |
| `SetPremium` | `round(FinalRate × Exposure[/1000] + MedicalPaymentsCharge, 0)` | `round(FinalRate × Exposure[/1000], 0)` |

The two are **algebraically identical** — the fold distributes to exactly the separate charge,
because `BaseRate = LossCost × LCM × ClaimsMadeMultiplier` is common to both. They differ **only in
where rounding lands**, and that is enough to move the answer:

| | CW 2023 V03 | CW 2027 V01 |
|---|---|---|
| `FinalILF` | `2.05` | `round(2.05 + 1.003 − 1, 3) = 2.053` |
| `FinalRate` | `round(0.095 × 2.05, 3) = 0.195` | `round(0.095 × 2.053, 3) = 0.195` |
| med-pay charge | `round(0.095 × 0.003 × 5000, 0) = 1` | — (inside the rate) |
| **Premium** | **976** | **975** |

**Same risk, same published numbers, $1 apart.** Not a defect in either edition — a consequence of
rounding at 3dp before multiplying by exposure. It means an engine that implements "the" 334
algorithm and swaps rate tables per edition will be wrong for one of them.

**Consequences for the build:**

- **The rating algorithm is edition-scoped, not just the rate tables.** `rating/sublines/` cannot
  hold one `premops.py`; it must dispatch on the resolved countrywide parent. The resolver already
  produces that parent (N5) — it must now also select the calculator.
- **N12 as written is edition-specific.** "Medpay folds into the ILF additively — `ILF' = medpay +
  ILF − 1`" is true of CW 2027 and false of CW 2023 V03, which was the edition the golden case
  actually ran on. Restated in §2 below.
- **§6 of the build plan is right about `+ MedicalPaymentsCharge` and wrong to state it
  universally.** Correction filed in §9.
- **10 distinct countrywide parents are in live use** across the 562 state packages
  (`GL_CW_20231201_V02` ×146 · `GL_CW_20260101_V01` ×114 · `GL_CW_20230501_V01` ×77 ·
  `GL_CW_20270401_V01` ×60 · `GL_CW_20210801_V01` ×58 · `GL_CW_20231201_V03` ×51 ·
  `GL_CW_20231201_V01` ×23 · `GL_CW_20230401_V01` ×12 · `GL_CW_20220901_V02` ×11 ·
  `GL_CW_20201201_V01` ×10). The edition axis is not a tail case.

This is the answer to the question the gate was written to ask — *is the gate format sufficient to
build from?* It is, and it earned its keep on the first subline: **reading the golden case's
declared parent rather than the newest countrywide package is what surfaced this.** Ten more
coverages follow the same template and each must be read against its own parent.

---

## 1. The algorithm

Two ordered sequences run, outer then inner. Both are `RunRule` chains — the order is ERC's, not
a reconstruction.

### 1a. Classification level — `GeneralLiabilityClassificationRules.Rule.xml` → `ErcSetRatesAndFactors`

Only the steps that feed 334 are listed; the rule runs 42 steps covering every subline.

| # | Rule | What it does |
|---|---|---|
| 1 | `SetSubline` | Subline text → `334` |
| 2 | `SetClassificationType` | `LookupClassificationType` — class code → type (Mercantile / Manufacturing / …) |
| 3 | `SetPremOpsExposureCalc` | Exposure ÷ 1000, truncated to `long`, for the nine ÷1000 premium bases; raw otherwise |
| 4 | `SetPremOpsHomogeneityIndex` | `LookupPremOpsHomogeneityIndex` — class → index |
| 5 | `SetPremOpsIncrdLimitTableAssignment` | `LookupPremOpsIncrdLimitTableAssignment` — class → ILF table number, **or the literal string `Refer To Co.`** |
| 6 | `SetFinalPremOpsIncrdLimitTableAssignment` | If the assignment is `Refer To Co.`, take `PremOpsIncrdLimitTableAssignmentOverride` instead; else pass through |
| 7 | `SetFinalPremOpsIncrdLimitTableAssignmentInt` | `Convert` to integer; **`0` when the assignment is null or empty** |
| 8 | `SetPremOpsIncrdLimitFactor` | `LookupILFPremOps` on (state, table#, occurrence limit, general aggregate limit). `0.0` if the subline is not Prem/Ops+Prod/CompOps or any key is empty |

### 1b. Coverage level — `GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` → `ErcSetRatesAndFactors` (29 steps, verbatim order)

| # | Rule | Result |
|---|---|---|
| 1 | `SetClassCode` | copy from parent classification, else `""` |
| 2 | `SetPremiumBasis` | copy `PremOpsPremiumBasis`, else `""` |
| 3 | `SetLCM` | `LookupPremOpsLCM` (state, `"Y"`) — only if not already supplied |
| 4 | `SetBringYourOwnAlcoholExclusionFactor` | `LookupBringYourOwnAlcoholExclusionFactor` |
| 5 | `SetPremOpsLossCost` | **requires non-empty class code AND non-empty `PremisesOperationsTerritory`.** Then `LookupPremOpsSizeOfRiskLossCost` if size-of-risk applies, else `LookupPremOpsLossCost`. **Otherwise `0.0`** |
| 6 | `SetPremOpsELPOverride` | copy, else `0.0` |
| 7 | `SetPremOpsELP` | if override is `0.0` and class code non-empty → `LookupPremOpsELP`; else the override; else `0.0` |
| 8–9 | `SetFinalPremOpsIncrdLimitTableAssignment[Int]` | coverage-level copies of 1a.6–7 |
| 10–12 | `SetPremOps{BI,BIPD,PD}DeductibleFactorOverride` | copy user overrides, else `0.0` |
| 13 | `SetYearInClaimsMade` | copy when the form is `Claims Made`, else `0` |
| 14 | `SetClaimsMadeMultiplier` | `LookupPremOpsClaimsMadeMultiplier(year)`, **year capped at 5**; `1.0` on the occurrence form |
| 15 | `SetBaseRate` | see below |
| 16 | `SetCSLILF` | **copy `../PremOpsIncrdLimitFactor`** from 1a.8 — no lookup at this level |
| 17 | `SetMedicalPaymentsFactor` | `LookupMedPayFactor` (CW 2023) / `LookupIncreasedMedPayLimitFactor` (CW 2027); `1.0` when med-pay is excluded at class or location level |
| 18–19 | `SetPremOps{BI,PD}DeductibleFactor` | `LookupDedFactorPremOps{BI,PD}` |
| 20 | `SetDeductibleFactor` | override if non-zero, else `LookupDedFactorPremOpsCSL` (state, table#, deductible), else `0.0` |
| 21 | `SetFinalDeductibleFactor` | combined ⇒ `DeductibleFactor`; split BI+PD ⇒ **sum**; one side only ⇒ that side; else `0.0` |
| 22 | `SetFinalILF` | **edition-dependent — see §0** |
| 23 | `SetPremOpsSizeOfRiskRelativityTableAssignment` | class → table, only when `SizeOfRiskRatingApplies = "Yes"` |
| 24 | `SetPremOpsExposureTimesThousand` | `long(exposure ÷ 1000) × 1000` for the ÷1000 bases; `long(exposure) × 1000` otherwise; `0` when size-of-risk does not apply |
| 25 | `SetPremOpsSizeOfRiskPreliminaryRelativity` | `LookupPremOpsSizeOfRiskRelativity`, **rounded 4dp** |
| 26–27 | `SetPremOpsSizeOfRisk{Minimum,Maximum}Relativity` | class-keyed bounds |
| 28 | `SetPremOpsSizeOfRiskFinalRelativity` | clamp: `< min → min`, `> max → max`, else preliminary |
| 29 | `SetBasicLimitPremium` | `round(BaseRate × (1 − FinalDeductibleFactor) [× SizeOfRiskFinalRelativity] × PackageModFactor × Exposure[/1000], 0)` |

Then `ErcRate` (4 steps): `SetFinalRate` → `SetAdditionalInterestFactor` → `SetPremium` →
`SetPremiumIndicator`.

### The arithmetic

```
BaseRate  = round( LossCost [× BringYourOwnAlcoholExclusionFactor] × LCM
                            [× ClaimsMadeMultiplier] , 3)          # when LossCost ≠ 0
          = round( ELP × LCM [× ClaimsMadeMultiplier] , 3)         # when LossCost = 0

FinalILF  = round( CSLILF [+ MedicalPaymentsFactor − 1] − FinalDeductibleFactor , 3)
            # the bracketed term exists in CW 2027 only; clamped to 0.0 if ≤ 0

FinalRate = round( BaseRate × FinalILF [× SizeOfRiskFinalRelativity]
                            × PackageModFactor × ExperienceRatingModificationFactor
                            × ExpenseModification × ModToUse , 3)

Premium   = round( FinalRate × Exposure[/1000] [+ MedicalPaymentsCharge] , 0)
```

`[× SizeOfRiskFinalRelativity]` appears **only** in the `SizeOfRiskRatingApplies = "Yes"` branch.
`[/1000]` applies to nine premium bases: Admissions, Area, Gallons, Gross Sales, Kilowatt-hours,
Payroll, Total Cost, Total Operating Expenses, Vehicles (CW 2023 also lists Passenger Days;
**CW 2027 drops it** — a second edition difference, in the divisor set).

`BringYourOwnAlcoholExclusionFactor` enters the base rate **only** for class codes `16905` and
`16906` **and** only when a `GeneralLiabilityAmndmtOfLiquorLiabExcl` row exists.

### The $1 floor — CW 2027 only

`SetPremium` (CW 2027) ends:

> if the calculated premium is `0` **and** `PremOpsCovExposure > 0`, then `Premium = 1.0`.

Undocumented in the manual and absent from CW 2023. It matters more than its size: it means a
**broken rating path returns `$1`, not `$0`.** The N13 failure mode is therefore not always a
visible zero — under CW 2027 it is a plausible-looking dollar. A "no free policies" assertion keyed
on `Premium == 0` would not have caught it.

### `AdditionalInterestFactor` is computed and never consumed

`SetAdditionalInterestFactor` writes it (input, else `1.0`; the golden case emits `1.0`) but no
rule in either edition's PremOps rule set reads it in the premium chain. Recorded as an
observation, **not implemented as a multiplier** — inventing a use for it would be exactly the
assumption the doctrine forbids. Raised as an open item.

---

## 2. Confirmations — where the manual was consulted

| Claim | Manual says | Citation | Verdict |
|---|---|---|---|
| Med-pay adjusts the ILF as `MedPayFactor + ILF − 1` | *"Add the factor in Paragraph D.2.b. to the Increased Limits Factor in Paragraph D.2.a. and subtract 1."* Worked example: *"1.020 + 1.95 − 1 = 1.97"* | `GL-MU-2027-RU-001-C` p.32, Rule 56.D.2 | **Confirms CW 2027 exactly.** The 2027 ERC formula is the manual's formula, verbatim |
| The adjusted ILF then absorbs the deductible | *"This adjusted Increased Limits Factor is subject to adjustment to reflect any deductibles and any other applicable rate modification(s)."* | same page | **Confirms** `− FinalDeductibleFactor` and its position after the med-pay fold |
| Split-limit weight factors by class band | Manufacturing/Processing `50000–59999` → BI `0.83`, PD `0.19`, Constant `0.03` | `GL-MU-2027-RU-001-C` p.33, Table 23.D.5.c.#1 | **Confirms** the golden case's `SplitLimitWeightFactorPremOps{BI,PD,Constant}` = `0.83 / 0.19 / 0.03` for class `50017`. Two independent sources, identical numbers |
| ILF tables are state-supplied, not countrywide | *"Refer to the state exceptions."* | `GL-MU-2027-RU-001-C` p.67, on Rule 56 | **Confirms** the measured table population in §5 |
| Med-pay above $25,000 each person refers | *"For medical payments limits above $25,000 each person, refer to company."* | `GL-MU-2027-RU-001-C` p.32 | **Confirms** a referral trigger ERC expresses only as a closed domain |

**No disagreement was found between the two sources on the 334 algorithm.**

One apparent disagreement is an edition difference, not a conflict: the manual notice
`GL-OK-2027-LC-003` publishes `.090` for OK / territory 501 / class 50017, while the ERC package
`GL_OK 20250601 V01` publishes `0.095`. Different filings, two years apart. The manual confirms the
**shape** — state × territory × class → a pre-LCM Premises/Operations loss cost — and the value
difference is the corpus working correctly. It is recorded here so that a future reader does not
re-open it as a defect.

---

## 3. Escalations

| # | Question | Engine behaviour meanwhile |
|---|---|---|
| **E1** | Rounding tie-break mode | Unchanged. 334 rounds at four sites — `BaseRate` 3dp, `FinalILF` 3dp, `FinalRate` 3dp, `Premium` and `MedicalPaymentsCharge` 0dp. **None is a tie in the golden case** (§8), so it yields no evidence either way. Configurable; every site flagged in the trace |
| **E11** *(new)* | `AdditionalInterestFactor` is set on every 334 quote and read by no rule. Is it consumed downstream, retired, or a defect in the published rule set? | Carried in the trace, **never multiplied**. Zero premium effect today |
| **E12** *(new)* | `SetMedicalPaymentsCharge` (CW 2023) branches on `../PremOpsELP` compared as a **string** to `"Rate/Loss Cost Applies"` in one arm and as a **decimal** to `0.0` in another — two types for one DataDef | Both arms implemented as ERC writes them. Flagged for the harness rather than normalised, since normalising is an assumption |

`E4` (`Status` A/C/D) does not arise in the 334 path. `E7`/N13 arises materially — see §7.

---

## 4. Inputs consumed, and behaviour when absent

**Required — absence changes the rating path, silently, under ERC's own rules:**

| Input | Where read | ERC on absence | **Engine** |
|---|---|---|---|
| `ClassCode` | classification | `""` → loss cost `0.0` → **ELP path** | `REFER` |
| `PremisesOperationsTerritory` | location | not tested → loss cost `0.0` → **ELP path** | `REFER` |
| `PremOpsCovExposure` | classification | `0.0` → premium `0`, and no `$1` floor | `REFER` unless `IfAnyBasis = "Yes"` |
| `PremOpsPremiumBasis` | classification | `""` → falls to the **non-÷1000** branch, so premium is 1000× too high | `REFER` |
| `PremOpsProdsEachOccurrenceLimit`, `GeneralAggregateLimit` | policy | `""` → ILF `0.0` → premium `0` | `REFER` |
| `Subline` | policy | anything but `Premises/Operations and Products/Completed Operations` → premium `0` | validate against the domain |

The first two are the important ones. **A missing class code or territory does not error in ERC — it
switches the risk onto the expected-loss-potential path.** Nothing in the rule set marks the
transition. An engine that ports `SetPremOpsLossCost` faithfully inherits a silent path switch on
absent input, which is precisely the failure class this project exists to prevent.

**Optional, with ERC-declared defaults — implement the default, do not require the input:**

`LCM` → `1.0` by decision (E9) · `PackageModFactor`, `ExperienceRatingModificationFactor`,
`ExpenseModification`, `ModToUse` → `1.0` (rule-computed, E5/E10) · `PremOpsELPOverride`,
`PremOps{BI,PD,BIPD}DeductibleFactorOverride` → `0.0` · `YearInClaimsMade` → `0` ·
`SizeOfRiskRatingApplies` → not `"Yes"` disables the whole size-of-risk branch ·
`AdditionalInterestFactor` → `1.0` · `GeneralLiabilityMedPayCoverage/Limit` → absent means no
med-pay adjustment.

---

## 5. Lookups and their layer — measured, not assumed

Row counts are from the CW `GL CW 20231201 V03` package and the state `GL_OK 20250601 V01` package.

| Table | Countrywide | Oklahoma | Layer |
|---|---|---|---|
| `PremOpsLossCost` | **0 rows** (header only) | **3,564** | **state only** |
| `ILFPremOps` | **0 rows** (header only) | **432** | **state only** |
| `PremOpsIncrdLimitTableAssignment` | **0 rows** (header only) | **1,196** | **state only** |
| `PremOpsHomogeneityIndex` | — | 1,188 | state |
| `PremOpsELP` | — | 1,188 | state |
| `MedPayFactor` | 1,188 | absent | **countrywide only** |
| `DedFactorPremOpsCSL` / `BI` / `PD` | 93 each | absent | **countrywide only** |
| `PremOpsMinPremium` | 3 (all `0`) | absent | **countrywide only** |
| `ClassificationType` | populated | absent | **countrywide only** |

This is finding #1 of the README, measured on the primary rating path: **the countrywide layer holds
the method and the modifiers; every number that varies by risk is state-supplied.** The three
header-only countrywide tables are live N7 instances in the primary path — reading them as
populated yields a `0` loss cost, a `0` ILF, and the ELP path.

**A second inheritance mechanism exists, and it is not N3.** Every lookup rule in 334 is a
`FirstNonNull` of two `Lookup` calls against the *same* table: first keyed on `/*/State/Code`, then
keyed on the literal `"CW"`. So a single resolved table carries both state rows and countrywide
rows, and falls back **row by row**. This is distinct from N3 (override a whole table by name at the
package layer) and both are in play at once. An implementation that models only N3 will miss the
countrywide default rows inside a state table.

---

## 6. State deviations — enumerated and quantified

Measured across all **572 packages / 51 jurisdictions** by indexing every `rul:Rule Name` in each
package's `GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml`
(`scripts/erc/26_census_334.py`).

**32 of 51 jurisdictions carry no Premises/Operations rule override at all** — AL AR AZ CO DC DE FL
GA IA ID IL KS LA MD ME MN MS NE NM NV OR PA PR RI SC SD VA VT WA WI WV WY. They rate on the
countrywide algorithm with state tables.

**19 override something.** Only **8 of those overrides touch premium**; the rest are statistical
coding:

| Rule overridden | Jurisdictions | Effect |
|---|---|---|
| `SetPremOpsLossCost` + `LookupPremOpsLossCost` | **CA NJ NY OH** | Loss-cost table is **partitioned** — `LookupPremOpsLossCost002…017` (CA/NJ/OH) and `LookupPremOpsLossCostNYTerr002…024` (NY, 20 territory-keyed tables). A dispatch layer, not a different formula |
| `LookupPremOpsSizeOfRiskLossCost501…517` | **NJ OH** | Same partitioning for the size-of-risk loss cost |
| `SetBaseRate` | **MA NY TX** | Own base-rate algorithm |
| `SetBringYourOwnAlcoholExclusionFactor` | **MA TX** | Own liquor-exclusion factor |
| `SetBIILF`, `SetPDILF`, `LookupILFElevatorContractor` | **KY** | Separate BI/PD increased-limits treatment and an **elevator-contractor ILF table** found nowhere else |
| `SetMedicalPaymentsCharge`, `SetYearInClaimsMade`, `SetClaimsMadeMultiplier` | **NY** | Own med-pay charge and claims-made chain |
| `SetPremOpsIncrdLimitFactor` *(classification level)* | **OK** | Governmental-subdivision ILF variant, gated on `GovernmentalSubdivision = "Yes"` |
| `SetLimitStatCode`, `SetCoverageStatCode`, `SetMoldStatCode`, `ErcSetStatisticalCodes`, `SetLimitStatCodeGov{BI,PD}` | AK CT IN MA MI MO MT NC ND NH NY OK TN UT | **Statistical coding only — no premium effect** |

`InitializeRuleSet` and `ErcProcess` are overridden by all 19 and are plumbing, not rating.

**Implication for phase sizing:** the 334 calculator is one countrywide algorithm, four table-
dispatch shims (CA NJ NY OH), five genuine algorithm variants (MA NY TX KY OK), and a statistical-
coding layer for fourteen. Not "some states differ."

---

## 7. Refer-to-company triggers

Every path in 334 that must not produce a number.

**Declared by ERC in its own data or rules:**

1. **`PremOpsIncrdLimitTableAssignment = "Refer To Co."`** — the ILF table-assignment table can
   carry the literal string. `SetFinalPremOpsIncrdLimitTableAssignment` then substitutes
   `PremOpsIncrdLimitTableAssignmentOverride`. **If the override is absent, the assignment is null →
   `…Int = 0` → the ILF lookup misses → the premium is `0` (CW 2023) or `$1` (CW 2027).** A
   declared referral degrades into a number. The engine raises `REFER` at the marker and never
   reaches the lookup.
2. **Every "Per Claim" deductible factor is `0` in the countrywide table** — `"CW",3,"250 Per
   Claim",0` … `"100,000 Per Claim",0`, while every corresponding "Per Occurrence" row carries a
   real factor (`0.005`, `0.01`, `0.013`, `0.018`, …). The factors are unpublished, encoded as `0`,
   and ERC's own guard is a **validation rule, not a rating rule**:
   `DoMessageMustEnterPremOpsBIPDDeductibleFactorOverride` — *"Must enter Prem Ops BI and PD
   Deductible Factor Override"* — fires when the deductible is any of the 15 Per Claim values and
   the override is `0.0`.

   **This is a second confirmed instance of N13, on the primary rating path.** It differs from the
   drone case in direction: `FinalILF = CSLILF − FinalDeductibleFactor`, so an unguarded `0`
   withholds the deductible credit and **overcharges** rather than producing a free policy. It is
   just as silent. Both go in the sentinel register.

   The guard lives in `DoMessage*` rules, which an implementation porting only the rating chain
   would never call. **The validation rules are part of the algorithm, not commentary.**
3. **`DoMessagePremOpsBIPDDeductibleFactorCannotExceedILF`** — *"The Prem Ops BI and PD Deductible
   Factor cannot exceed the Increased Limits Factor"*, tested as
   `PremOpsBIPDDeductibleFactorOverride > PremOpsIncrdLimitFactor`. Plus the BI-only and PD-only
   variants, and the matching Prods/CompldOps trio.
4. **`FinalILF ≤ 0` → `FinalILF = 0.0`** — ERC clamps rather than errors. A deductible factor that
   swallows the ILF yields premium `0` / `$1`. The engine refers.
5. **Med-pay limit above $25,000 each person** — manual, Rule 56 (`GL-MU-2027-RU-001-C` p.32). ERC
   expresses this only as the absence of a domain row.
6. **Personal-and-advertising-injury limit ≠ occurrence limit** — manual, same page, *"refer to
   company."* ERC does not model a separate P&AI limit at all.

**Implicit — absence of an input silently reroutes (§4):** empty class code or territory → the ELP
path; empty premium basis → the non-÷1000 branch, 1000× high. Both become `REFER`.

**Not a referral, verified:** `PremOpsSizeOfRiskFinalRelativity = 0.0` when
`SizeOfRiskRatingApplies ≠ "Yes"`. Read as a sentinel this would zero every premium. It is
legitimate — `SetFinalRate` and `SetBasicLimitPremium` each have a **separate branch that omits the
factor entirely** in that case. Checked by opening the rule, not inferred from the value. This is
the discrimination N13 says cannot be made from the data alone, made from the rules.

---

## 8. Test result — the Oklahoma golden case

`GL_OK 20250601 V01/STC/1. Input.json` → `1. Output.json`. Effective `2025-08-01`. Parent resolved
from the XSD `xs:import`: **`GL_CW_20231201_V03`**.

Risk: class `50017` (Abrasives Mfg.), territory `501`, Gross Sales `5,000,000`, occurrence
`1,000,000 CSL`, general aggregate `2,000,000 CSL`, med-pay `10,000`, occurrence form, no
deductible, no size-of-risk, no experience rating, `PackageModFactor 1.0`.

| Step | Rule | Derivation | Value | ISO output |
|---|---|---|---|---|
| ILF table | `LookupPremOpsIncrdLimitTableAssignment` | `PremOpsIncrdLimitTableAssignment.RateTable.csv` → `"OK","50017","3"` | `3` | `3` ✓ |
| `LCM` | decision E9 | held at `1.0` | `1.0` | `1.0` ✓ |
| `PremOpsLossCost` | `LookupPremOpsLossCost` | `PremOpsLossCost.RateTable.csv` → `"OK","501","50017",0.095` | `0.095` | `0.095` ✓ |
| `BaseRate` | `SetBaseRate` | `round(0.095 × 1.0, 3)` | `0.095` | `0.095` ✓ |
| `CSLILF` | `LookupILFPremOps` | `ILFPremOps.RateTable.csv` → `"OK",3,"1,000,000 CSL","2,000,000 CSL",2.05` | `2.05` | `2.05` ✓ |
| `MedicalPaymentsFactor` | `LookupMedPayFactor` | CW `MedPayFactor.RateTable.csv` → `"CW","50017",1.003` | `1.003` | `1.003` ✓ |
| `FinalDeductibleFactor` | `SetFinalDeductibleFactor` | no deductible | `0.0` | `0.0` ✓ |
| `FinalILF` | `SetFinalILF` **(CW 2023)** | `round(2.05 − 0.0, 3)` | `2.05` | `2.05` ✓ |
| `FinalRate` | `SetFinalRate` | `round(0.095 × 2.05 × 1 × 1 × 1 × 1, 3)` = `round(0.19475, 3)` | `0.195` | `0.195` ✓ |
| `BasicLimitPremium` | `SetBasicLimitPremium` | `round(0.095 × (1 − 0) × 1.0 × 5,000,000/1000, 0)` | `475` | `475.00` ✓ |
| `MedicalPaymentsCharge` | `SetMedicalPaymentsCharge` | `round(0.095 × 1 × 1 × (1.003 − 1) × 1 × 1 × 1 × 1 × 5000, 0)` = `round(1.425, 0)` | `1` | `1.0` ✓ |
| **`Premium`** | `SetPremium` | `round(0.195 × 5000 + 1, 0)` | **`976`** | **`976.00`** ✓ |
| `PremiumIndicator` | `SetPremiumIndicator` | premium ≠ 0 | `1` | `1` ✓ |
| `MinPremium` | `LookupPremOpsMinPremium` | CW table, table 3 → `0` | `0.0` | `0.0` ✓ |
| `SizeOfRisk*` | branch not taken | `SizeOfRiskRatingApplies = "No"` | `0.0` | `0.0` ✓ |

**Every published value reproduced. No residual.**

One correction to the record, which had stood unchallenged across three documents:

- **`475.00` is a basic-limits figure, not the Premises/Operations premium.** The 334 premium is
  **`976.00`**. `475.00` is the policy-level `AnnualBasicLimitsCoPremiumPremOps`, equal here to the
  coverage-level `BasicLimitPremium` — a reported quantity that **no rule in the premium chain
  consumes.** It is not an intermediate of `Premium`.

  `PROCESS_LOG.md` Step 21 records it correctly, under its own field name. **`GL-RATING-ENGINE-BUILD-PLAN.md`
  §6 shortens it to `PremOps 475.00`**, which reads as the subline premium and is the number a
  reader would test against. Corrected in §9.

**E1 is unchanged, and the case was re-checked rather than assumed.** The chain rounds at four
sites and **none of them lands on a midpoint**: `0.19475 → 0.195` at 3dp is not a tie
(`0.19475 > 0.1945`, so every rounding mode agrees), and `1.425 → 1` at 0dp is not a tie either.
The golden case therefore does not discriminate between tie-break modes, exactly as the build plan
records. E1 stays open with no evidence gained.

### Manual cross-check

Independent of ERC, `iso.py` was run against the filed PDFs. Two results already appear in §2: the
med-pay `+ ILF − 1` formula with its worked example, and the split-limit weight factors `0.83 /
0.19 / 0.03` for the `50000–59999` band — the latter matching the golden case output exactly, from
a source that had no access to it. `iso.py rate OK --class 50017` returns `.090` from the 2027
notice against ERC's 2025 `0.095`: an edition difference, resolved in §2.

---

## 9. Corrections filed against the build plan

| Document | Was | Now |
|---|---|---|
| §6, premium chain | `Premium = round(FinalRate × Exposure + MedicalPaymentsCharge)` | Correct for CW 2023 and earlier. **CW 2027 has no `MedicalPaymentsCharge`** — the term is folded into `FinalILF`. Chain is edition-scoped |
| §6 | `FinalRate = BaseRate × FinalILF × …` | Add: `Premium` divides exposure by 1000 for nine premium bases (ten in CW 2023 — `Passenger Days` was dropped); and CW 2027 floors a zero premium at `$1` when exposure > 0 |
| §4, N12 | *"medpay folds into the ILF additively — `ILF' = medpay + ILF − 1`"* | True of CW 2027 and of the 2027 manual. **False of CW 2023 V03**, which charges separately. Restate as edition-scoped, and note the two are algebraically equal but round differently — worth ~$1/line |
| §4, N13 | one confirmed sentinel (drone `>55 lb`) | **two.** Add: all 15 "Per Claim" deductible factors are `0` countrywide while every "Per Occurrence" is real. Guarded only by a `DoMessage*` validation rule |
| §4, new N15 | — | **`DoMessage*` validation rules are part of the algorithm.** Several of ERC's guards live only there; porting the rating chain alone silently drops them |
| §5, architecture | `rating/sublines/` one module per subline | One module per **(subline, countrywide edition family)**. 10 distinct CW parents are in live use |
| §6, golden case line | `PremOps 475.00` | `AnnualBasicLimitsCoPremiumPremOps 475.00` (basic limits, consumed by no rule); **the 334 `Premium` is `976.00`** |
| §7, E1 | tie-break mode unstated; *"golden case does not hit a midpoint"* | **Confirmed, not changed.** All four 334 rounding sites re-checked against the golden case; none is a tie. E1 gains no evidence and remains open for RAaS |
| §7, new E11/E12 | — | `AdditionalInterestFactor` computed but unread; `PremOpsELP` compared as both string and decimal |
| §5, resolver | override by name (N3) | **Plus row-level `state → "CW"` fallback inside a single table.** Two inheritance mechanisms, both live |

---

## 10. Verdict

**Gate passed.** The algorithm is fully derived, the golden case reproduces exactly, the state
deviations are enumerated and counted, and every referral path is named.

**The gate format is sufficient to build from** — and it was worth running first. Items 4, 6 and 7
each forced a measurement that changed the plan: the silent path switch on absent input, the
32/19 split with only 8 premium-affecting overrides, and the second N13 sentinel. Item 8 caught an
error that had been repeated across three documents.

**Carry into the remaining ten coverages:**

1. **Resolve the golden case's declared parent before reading any countrywide rule.** Reading the
   newest package instead of the named one is what nearly hid the edition split.
2. **Read the `DoMessage*` rules alongside the rating rules.** They hold guards the rating chain
   does not.
3. **Count table rows before trusting a lookup.** Three of 334's countrywide tables are header-only.
4. **Test every `0` against its consuming branch.** One of the three zeros in 334 is legitimate, one
   is an unpublished factor, one is a degraded referral — and they are indistinguishable in the data.
