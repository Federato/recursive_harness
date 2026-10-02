# CF Coverage Inventory — What Requires Rating Definition, and What's Documented

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Source manual corpus:** `Commercial Line Manuals\CF\CW\` (six countrywide Rules notices, extracted to
`Recursive_Harness_2.0\Agentic\cf-circular-expert\text\rules\`)
**Built:** 2026-08-19
**Scope of this pass:** identification and tracking only — no new algorithm docs, no new tables docs,
no new diagrams. Do not treat a "No" in the Documented column as a task list; it is inventory, per
direction.

---

## Method

**ERC side.** A coverage "requires rating definition" if it has its own `CommercialProperty*
CoverageRules.Rule.xml` file that defines a `SetPremium` rule — that is the concrete signal ERC uses
for "this produces a chargeable premium in its own right," the same signal every coverage documented
so far was found through. Swept the full `Rules` directory:

```
grep -lE '"SetPremium"' *CoverageRules.Rule.xml   →  369 of 396 CoverageRules files
```

Normalized away the cause-of-loss-form suffixes (`BasicGroupI`, `BasicGroupII`, `Broad`, `Special`,
`Earthquake`) and the coverage-type suffixes (`AgreedVal`, `InflationGuard`, `PrsnlProp`,
`BusnIncome`, `SpclClassBusnIncome`) that every already-documented coverage also carries, to collapse
the 369 files down to **97 distinct coverage/endorsement families**. This is the same normalization
this project's own agents have been doing by hand in every pass so far (e.g. recognizing
`CommercialPropertyStructureBuildingBasicGroupICoverageRules.Rule.xml` and its Basic-Group-II/Broad/
Special siblings as "one coverage, four forms") — just automated for a first sweep across the whole
package.

**This is a first-pass sweep, not a verified inventory.** The normalization is regex-based and has at
least one known cosmetic artifact (a bare `"Structure"` line that is really
`StructureAgreedValEarthquake` with both suffixes stripped in one pass — folded into `StructureAgreedVal`
below rather than listed twice). Treat family boundaries as approximate until someone actually traces
each one; several plausibly-single families above may split into two once read closely, the way
"Business Income" turned out to need a plain and a Special-Class-attached variant.

**Manual side.** Cross-referenced against `Agentic/cf-circular-expert/knowledge/rule_index.json` —
itself explicitly partial (roughly 35 of an estimated 85+ manual rule numbers). A manual rule number is
listed only where the cross-reference is reasonably confident; most rows have none yet, because the
rule index doesn't cover that range. This is not evidence the manual is silent on those coverages —
only that this project hasn't read that part of the TOC yet.

> ### Correction, 2026-08-19 (same day, later pass) — the original sweep undercounted by more than half
>
> The first version of this document glob-matched only `*CoverageRules.Rule.xml`. Asked directly "what
> about earthquake and flood," a check turned up that **neither has a `*CoverageRules.Rule.xml` file at
> all** — ISO named this whole family `*EndorsementRules.Rule.xml` / `*Rules.Rule.xml` instead (e.g.
> `CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementRules.Rule.xml`,
> `CommercialPropertyFloodCoverageEndorsementRules.Rule.xml` — no `"Coverage"` immediately before
> `"Rules"`). The original glob silently skipped every file shaped that way.
>
> Re-swept with no filename restriction at all — every `.xml` file in `Rules\` checked for a
> `SetPremium` rule:
>
> ```
> grep -lE '"SetPremium"' *.xml   →  546 files total (369 CoverageRules.Rule.xml + 177 other-shaped)
> ```
>
> After the same normalization, **546 files collapse to 243 distinct families, not 97.** The original
> count was missing more than half the package. Earthquake and Flood are both real, and both entirely
> absent from the first version of this document — not folded into another family, not miscategorized,
> just never found. **Part B11 below adds them properly.** The other ~140 newly-surfaced families are
> not yet individually listed in this document — see "What's still not itemized" at the end for the
> honest scope of what this correction does and doesn't fix.
>
> The lesson worth keeping, in this project's own voice: a single filename pattern, however well it
> matched every already-documented coverage, is a hypothesis about ISO's naming convention — not a
> guarantee of it. This is the same shape of miss `BUILD-LOG.md` Entry 3 already recorded once (checking
> file existence without checking file content); here it was checking one naming pattern without
> checking whether ISO used a second one. Worth a standing habit: **when a search returns zero results
> for something you'd expect to exist, that is a prompt to widen the search, not a reportable absence.**

**Excluded from the count:** files matched by `*CoverageRules.Rule.xml` with no `SetPremium` rule (27
of the 396) — these are dispatch/attach-only files, the parent record that decides *which* per-form
coverage file to invoke, not a rating computation themselves. Listed separately in Part C for
completeness, since a couple of them turned out to matter (see the Unmanned Aircraft note).

---

## Part A — Core datadef groups: fully documented (5 of 5)

| Coverage | ERC datadef group | Algorithm doc | Tables doc | Diagrams in `cf-rating-chains.html` |
|---|---|---|---|---|
| Building / Structure | `CommercialPropertyStructure` | `CauseOfLoss_Building_RatingAlgorithms.md` | `BasicGroupI_ERC_Tables.md` | Yes — 4 forms |
| Personal Property | `CommercialPropertyPersonalProperty` | `CauseOfLoss_PersonalProperty_RatingAlgorithms.md` | `PersonalProperty_ERC_Tables.md` | Yes — 4 forms |
| Special Class | `CommercialPropertySpecialClass` | `CauseOfLoss_SpecialClass_RatingAlgorithms.md` | `SpecialClass_ERC_Tables.md` | Yes — 4 forms |
| Business Income | `CommercialPropertyBusinessIncome` | `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` **+ 6 granular sub-docs, 2026-09-11** (`Excel_Rater_BusinessIncome_BasicGroupI/II/Broad/Special.html`, `...FactorDecisionTree.html`, `...AlgorithmGrid_AllForms.html`) | `BusinessIncome_ERC_Tables.md` **+ 9 Supporting Tables workbooks** (`Spreadsheet_Rater\CF\Supporting Tables\`, all-8-batch per-state checked) | Yes — 5 forms (incl. Earthquake) |
| Special Class Business Income | `CommercialPropertySpecialClassBusnIncome` | `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md` | `SpecialClassBusinessIncome_ERC_Tables.md` | Yes — 5 forms (incl. Earthquake) |

These are the only five families in the 97 with a *master* `Set*RatesAndFactors`-orchestrator file
(confirmed separately by grepping for `Name="SetBlanketRatesAndFactors"` across the whole `Rules`
directory — exactly these five files, no others). Every remaining family below is an endorsement or
add-on that modifies or supplements one of these five rather than introducing a sixth independent base
coverage.

> **Correction, 2026-09-11 — a stale cross-reference caught while re-checking this doc.**
> `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` (this same coverage's own algorithm doc, one row up)
> contains a line reading "Special Class Business Income (existence only — not traced in depth)." That
> line is stale — `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md` is a real, complete
> 53KB document, same 2026-08-19 build date, likely written *after* that note and never looped back to
> remove it. Treat the Business Income doc's own "not traced" comment as outdated; this table's "Yes"
> is correct. Not fixed in place in that doc as part of this pass — flagged here so a future reader
> doesn't get confused by the contradiction.

> **A second correction, same pass — "Rating basis" is a real cross-cutting dimension this document
> doesn't track at all.** Everything above and below is organized by *coverage/endorsement family*.
> Orthogonal to that: every core coverage in Part A supports (or is supposed to support) multiple
> **rating bases** — Class Rated, Specific Rated, Tentative Rated, and Blanket Rated, plus Agreed Value
> as a valuation-basis overlay (already tracked as its own family, B1). None of these are separately
> itemized as their own rows anywhere in this document, because they're not separate ERC coverage
> families — they're branches *inside* each family's own rate build-up. A 2026-09-11 live-rater audit
> (`Excel_Rater_AllRatingPaths_BuildStatus.html`, `BUILD-LOG.md` Entries 28-29) found **Specific/
> Tentative rating confirmed unbuilt in `CFRater1.01.xlsb` for every form, every coverage** — a single
> project-wide gap inside otherwise-complete Class-rated paths, not a documentation gap in this
> inventory (the *algorithm* for Specific/Tentative is documented, e.g. `Excel_Rater_BasicGroupI.md` §9
> — it's the workbook build that's missing). Blanket Rated is a similar story: every algorithm doc
> written so far explicitly flags its own blanket-rated branch as "not built this pass." Worth adding a
> dedicated "rating basis" cross-reference table to this document in a future pass rather than relying
> on readers to notice the pattern across many separate docs.

> **2026-10-02 — the rating ENGINE's Specific / Tentative path is built and ISO-confirmed (Property chunk 26,
> `docs/CF-CHUNK26-GATE.md`).** This is the engine (`cf_engine`), not the Excel rater: the rater's gap above is
> unchanged. In the engine, Specific and Tentative Group I (building, contents, BI), California's One-Term Loss
> Cost, and Specific Group II in the 36 states that offer it were traced from the rule text, predicted by hand,
> and matched by ISO live in all 46 states and every countrywide edition (MO's 2023 V02 differs and ISO follows
> it); the 126 distinct stored Specific / Tentative policies re-rate with every premium equal to ISO. Facts a
> rater build would need: contents price on their OWN `SpecificGroupIRate` (none → $0), BI on the building's;
> FL NY WV and MO (V02) leave the roof ACV factor out of the Specific formula; a blank `RatingType` prices at
> rate 1.0; CA One-Term leaves BI at 1.0 (OI-124). It adds no countrywide premium file: 546 of 546 unchanged.

---

## Part B — Endorsement/rider families with their own rating definition: not yet documented (92)

Grouped by theme for readability; every family below produced at least one `SetPremium` rule, so each
is a real "not yet documented" item, not a placeholder.

### B1 — Valuation and inflation add-ons (10)

| Family | Attaches to | Manual rule (if known) | Documented |
|---|---|---|---|
| `StructureAgreedVal` (incl. the Earthquake variant) | Building | — | No |
| `StructureInflationGuard` | Building | — | No |
| `PersonalPropertyAgreedVal` | Personal Property | — | No |
| `PersonalPropertyInflationGuard` | Personal Property | — | No |
| `SpecialClassAgreedVal` | Special Class | — | No |
| `SpecialClassInflationGuard` | Special Class | — | No |
| `BusinessIncomeAgreedVal` | Business Income | 51 (Business Income Coverage Options, unconfirmed exact sub-item) | Partially — the Agreed Value *mechanism* (incremental `(Factor-1)×Rate` surcharge) is described in the Business Income algorithm doc, but the coverage's own rate build-up was not traced as its own document |
| `SpecialClassBusnIncomeAgreedVal` | Special Class Business Income | — | Partially — same caveat as above |
| `FunctionalBuildingValuation` | Building | — | No |
| `FunctionalPersonalPropertyValuationOtherThanStock` | Personal Property | — | No |

### B2 — Business Income / time-element extensions (17)

| Family | Attaches to | Documented |
|---|---|---|
| `BusinessIncomeExtendedPeriodOfIndemnityCoverage` | Business Income | Partially — mechanism described (same incremental-surcharge shape as Agreed Value), not independently traced |
| `SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage` | Special Class Business Income | Same caveat |
| `BusinessIncomeChangesBeginningOfThePeriodOfRestorationNoWaitingPeriod` | Business Income | No |
| `BusnIncomeChangesBeginningOfThePerOfRestrtnNoWaitingPer` (Special Class variant) | Special Class Business Income | No |
| `BusinessIncomeFromDependentPropertiesBroadForm` | Business Income | No |
| `BusinessIncomeFromDependentPropertiesLimitedForm` | Business Income | No |
| `BusinessIncomeInterruptionOfComputerOperations` | Business Income | No |
| `SpecialClassBusnIncomeInterruptionOfComputerOperations` | Special Class Business Income | No |
| `BusinessIncomeLandlordAsAdditionalInsuredRentalValue` | Business Income | No |
| `BusinessIncomeWatercraftExclusionBuyback` | Business Income | No |
| `SpecialClassBusnIncomeWatercraftExclusionBuyback` | Special Class Business Income | No |
| `CivilAuthorityIncreasedCoveragePeriod` (+ `Radius` variant) | Business Income | No |
| `CivilAuthorityIncreasedCoveragePeriodSpclClassBusnIncomeRadius` | Special Class Business Income | No |
| `ExtraExpenseFromDependentPropertiesDetail` (+ Special Class variant) | Business Income | No |
| `MiningProperties` / `MiningPropertiesBusinessIncome` | Building / Business Income | No |
| `EquipmentBreakdownCauseOfLossBusnInc` (+ `WaitingPeriod` variant) | Business Income | No |
| `PowerHeatAndRefrigerationDeduction` | Business Income | No |

### B3 — Ordinance or Law family (18)

The manual's Rule 71-adjacent numbering isn't confirmed for this family yet (only rules up to ~73 plus
scattered appendix numbers were read in the Entry 7 pass), but the ERC side is a large, self-contained
cluster: separate Coverage A (demolition), B (increased cost of construction), C (loss to undamaged
portion), and combined B-and-C rate/premium files, **each further split across Basic Group I, Basic
Group II, and Earthquake** for the "Tenants' Interest in Improvements and Betterments" variant:

| Family | Documented |
|---|---|
| `OrdinanceOrLawCovACoverage` | No |
| `OrdinanceOrLawCovBCoverage` | No |
| `OrdinanceOrLawCovCCoverage` | No |
| `OrdinanceOrLawCovBAndCCoverage` | No |
| `OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBettermentsCovA` (+ BGI/BGII/EQ variants) | No |
| `OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBettermentsCovB` (+ BGI/BGII/EQ variants) | No |
| `OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBettermentsCovC` (+ BGI/BGII/EQ variants) | No |
| `OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBettermentsCovBandC` (+ BGI/BGII/EQ variants) | No |
| `OrdinanceOrLawIncreasedPeriodOfRestoration` | No |

This is the single largest undocumented cluster by file count in the whole package.

### B4 — Leasehold Interest family (4)

Manual rule 65 ("Leasehold Interest Coverage," CF-78–CF-84) covers this family — the strongest manual
cross-reference found outside the Rule 71 Broad-form match from Entry 7.

| Family | Documented |
|---|---|
| `LeaseholdInterestCoverageFormBonusPaymentsCoverage` | No |
| `LeaseholdInterestCoverageFormImprovementsCoverage` | No |
| `LeaseholdInterestCoverageFormPrepaidRentCoverage` | No |
| `LeaseholdInterestCoverageFormTenantsLeaseCoverage` | No |

### B5 — Utility Services family (5)

| Family | Documented |
|---|---|
| `UtilityServicesDirectDamageBldgDetail` | No |
| `UtilityServicesDirectDamagePrsnlPropDetail` | No |
| `UtilityServicesDirectDamageSpecialClassDetail` | No |
| `UtilityServicesTimeElementDetail` | No |
| `UtilityServicesTimeElementSpclClassBusnIncomeDetail` | No |

### B6 — Builders Risk family (4, plus one attach-only — see Part C)

| Family | Documented |
|---|---|
| `BuildersRiskPremiumAdjustmentFormDetail` | No |
| `BuildersRiskPremiumAdjustmentFormDetailBlanket` | No |
| `BuildersRiskRenovations` | No |
| `BuildersRiskReportingForm` | No |

### B7 — Vacancy Permit family (5)

| Family | Documented |
|---|---|
| `VacancyPermit` | No |
| `VacancyPermitMoltenMaterial` | No |
| `VacancyPermitPrsnlPropMoltenMaterial` | No |
| `VacancyPermitPrsnlPropRadioactiveContamination` | No |
| `VacancyPermitRadioactiveContamination` | No |

### B8 — Debris Removal family (2)

| Family | Documented |
|---|---|
| `DebrisRemovalAdditionalInsurance` | No |
| `DebrisRemovalAdditionalInsuranceSpecialClass` | No |

### B9 — Special coinsurance / additional locations (2)

| Family | Documented |
|---|---|
| `AdditionalLocationsSpecialCoinsuranceGeneralInformation` | No |
| `AdditionalLocationsSpecialCoinsuranceProvisions` | No |

Worth flagging: several already-documented coverages' premium *gates* explicitly test for the
existence of this record (e.g. Personal Property's Basic Group I coverage gate is `NotExist
(SpecialCoinsuranceProvisions)`), so this family isn't purely standalone — it interacts with coverage
gates already documented elsewhere. Anyone tracing it should re-check those gates too.

### B10 — Named/scheduled small-class and single-purpose endorsements (17)

| Family | Documented |
|---|---|
| `BrandsAndLabels` | No |
| `OutdoorTreesShrubsAndPlants` | No |
| `OutsideSignsDetail` | No |
| `RadioOrTelevisionAntennasDetail` | No |
| `RadioOrTelevisionAntennasBusinessIncomeOrExtraExpense` | No |
| `NonOwnedTrailers` | No |
| `CondominiumCommercialUnitOwnersOptionalCovLossAssmt` | No |
| `CondominiumCommercialUnitOwnersOptionalCovMiscRealProp` | No |
| `ManufacturersConsequentialLossAssumption` | No |
| `OrdinaryPayrollLimitationOrExclusion` | No |
| `PeakSeasonLimitOfInsuranceDetail` | No |
| `PollutantCleanUpAndRemovalAdditionalAggregateLimitOfInsuranceLocation` | No |
| `HouseholdPersonalPropertyCoverageDetail` | No |
| `PersonalPropertyTobaccoSalesWarehouses` | No |
| `Spoilage` | No |
| `ValuablePapersAndRecsOTElectronicData` | No (note: the *carve-out* this coverage triggers in Personal Property's own COL adjustment — zeroing the rate when `CovType = "Valuable Papers and Records"` — **is** already documented, in `CauseOfLoss_PersonalProperty_RatingAlgorithms.md`; only this endorsement's own independent rating is not) |
| `ValueReportingForm` | No |
| `PostTRIA` | No (terrorism-related; likely interacts with the TRIA/terrorism chain noted in passing in the Business Income doc's master-orchestration section, not traced) |

---

## Part C — Attach-only / dispatch files: explicitly out of scope for "rating definition"

These 27 `*CoverageRules.Rule.xml` files have no `SetPremium` rule of their own. Most are the
parent-record dispatcher for a family already listed in Parts A/B (e.g.
`CommercialPropertyBusinessIncomeCoverageRules.Rule.xml` decides which per-form Business Income
coverage record applies; the per-form files that actually rate are the ones counted in Part A). Listed
here for completeness, not as additional undocumented coverages:

`BusinessIncome`, `BusinessIncomeAgreedVal`, `BusinessIncomeExtendedPeriodOfIndemnity`,
`BusinessIncomeChangesFungusWetRotDryRotBacteriaCoverage` (×3, one per COL form),
`BuildersRiskSeparateOrSubContractors`, `HouseholdPersonalProperty`, `NonOwnedTrailers`,
`OrdinanceOrLaw`, `OrdinanceOrLawCovA`, `PersonalProperty`, `PersonalPropertyAgreedVal`,
`PersonalPropertyInflationGuard`, `PersonalPropertyPrsnlProp`,
`RadioOrTelevisionAntennasBusinessIncomeOrExtraExpenseEarthquake`, `SpecialClass`,
`SpecialClassAgreedVal`, `SpecialClassBusnIncome`, `SpecialClassBusnIncomeAgreedVal`,
`SpecialClassBusnIncomeExtendedPeriodOfIndemnity`, `SpecialClassInflationGuard`, `StructureAgreedVal`,
`StructureBldg`, `StructureInflationGuard`, `TotPremium`, `YourBusinessPersonalPropertySeparationOf`.

**One exception worth flagging, not excluding.** `LimitedCoverageForUnmannedAircraftScheduledAndOrBlanket`
has no `SetPremium` in its own top-level `CoverageRules.Rule.xml`, but a *separate* rule file —
`CommercialPropertyLimitedCoverageForUnmannedAircraftScheduledAndOrBlanketCoverage{Detail,BusnIncomeDetail,
PrsnlPropDetail,SpecialClassDetail,SpclClassBusnIncomeDetail}Rules.Rule.xml` (five variants, one per
attaching coverage) — does define its own `Set*RatesAndFactors`-style chain (confirmed by the earlier
broad-net grep for orchestrator patterns). This is a real, undocumented rating definition; it's just
split across files in a way the `SetPremium`-only sweep alone would have missed. **Added to the
tracking table below as its own line rather than folded into Part C.**

| Family | Documented |
|---|---|
| Limited Coverage For Unmanned Aircraft (5 attaching-coverage variants, own rate chain in `*Detail*Rules.Rule.xml`) | No |

---

## Part B11 — Earthquake and Flood coverage/endorsement families (added in the correction pass)

Both are real, independent, multi-variant endorsement clusters, entirely missed by the original sweep.
Neither is documented.

### Earthquake and Volcanic Eruption Endorsement

Four distinct endorsement *forms*, each attaching separately to Building, Personal Property, Special
Class, Business Income, and Special Class Business Income (up to 20 files total):

| Form variant | What it appears to add (from filename only — not traced) | Documented |
|---|---|---|
| `EarthquakeAndVolcanicEruptionEndorsement` | The base earthquake/volcanic-eruption endorsement | No |
| `EarthquakeAndVolcanicEruptionEndorsementSubLimitForm` | A sub-limited version (matches the CP 10 45 / CP 10 29-style sub-limit machinery already noted, in passing, inside the Business Income algorithm doc's Earthquake section) | No |
| `EarthquakeAndVolcanicEruptionCoverageWithFlatDollarDeductible` | Flat-dollar (rather than percentage) earthquake deductible | No |
| `EarthquakeAndVolcanicEruptionCoverageSubLimitFormWithFlatDollarDeductible` | Both of the above combined | No |

**Important scope note, so this isn't misread against work already done.** The *Earthquake cause-of-loss
form* inside Special Class, Business Income, and Special Class Business Income — `SetEQRatesAndFactors`,
`FinalEQRate`, the Agreed-Value-only premium asymmetry — **is already documented**, as one of the four-
or-five cause-of-loss chains within those coverages' own algorithm docs. What's newly identified here is
different: a **standalone endorsement** that attaches earthquake coverage to a policy in the first place
(and governs sub-limiting and deductible structure), which is a separate rating question from "given
that earthquake coverage exists, how does the Special Class item's own Earthquake chain compute a rate."
The relationship between this endorsement and the already-documented `SetEQRatesAndFactors` chains (e.g.
does this endorsement's own premium feed into the EQ chain, or run alongside it) has **not** been traced.

Also present, not yet checked for its own `SetPremium`: `CommercialPropertyEarthquakeInceptionExtensionRules.Rule.xml` — likely a policy-term/inception-date rule for earthquake coverage, not itself a rating file, but unverified.

### Flood Coverage Endorsement

| Form variant | Attaches to | Documented |
|---|---|---|
| `FloodCoverageEndorsement` | Building, Personal Property, Special Class, Business Income, Special Class Business Income (5 variants) | No |
| `FloodCovEndtBlanketRatingDetail` | Blanket-rated flood premium detail | No |

**A related but distinct item, easy to confuse by name:** `DischargeFromSewerDrainOrSumpNotFloodReltd`
(2 variants) is explicitly *not* the flood endorsement — the name states the opposite, a sewer/drain/sump
backup coverage carved out from flood. Listed separately so it doesn't get merged into the Flood family
by a future pass working from names alone.

Also present, apparently support/detail files without their own independent `SetPremium` (not confirmed
either way — flagged, not asserted): `CommercialPropertyFloodCovEndtBlanketRatingRules.Rule.xml`,
`CommercialPropertyFloodCovEndtLocationRules.Rule.xml`.

---

## Part D — the ~146 remainder, now named (2026-09-11)

Reproduced the corrected sweep's exact method (`grep -lE '"SetPremium"' *.xml` across the whole `Rules`
directory — **546 files**, confirmed identical to the original count) and re-ran the same
suffix-stripping normalization independently, without access to the original script. Result: **230
distinct normalized families** total (vs. the original pass's 243 — expected drift, different regex,
same "approximate boundaries" caveat the Method section already carries). Diffed against every family
name already itemized in Parts A/B/B11/C above: **145 did not match**, almost exactly the "~146"
estimate this document has carried since 2026-08-19. Two of those are normalization artifacts (`Structure`
/ `StructureBuilding`, over-stripped duplicates of the already-documented Building family in Part A,
excluded below) — **143 genuinely new family names**, grouped by theme the same way Parts B1-B10 are.

**Caveat carried forward unchanged from the Method section: these are names, not traced coverages.**
Nobody has opened any of these 143 rule files to confirm what they actually price or how. A handful
below are flagged as *likely* already conceptually covered by an existing Part B row under a looser
name (e.g. `CivilAuthorityIncreasedCoveragePeriodRadius` vs. B2's "`CivilAuthorityIncreasedCoveragePeriod`
(+ `Radius` variant)") — kept as their own lines here because they're real, distinct file-level names the
diff surfaced, not because they're confirmed to be separate coverages.

### D1 — Cannabis Exclusion (9)

Plain and "With Hemp Exception" variants, each across Building/Business Income/Personal Property/Special
Class Business Income (Special Class itself uses a bare name with no coverage suffix).

`CannabisExclusionBuilding`, `CannabisExclusionBusinessIncome`, `CannabisExclusionPersonalProperty`,
`CannabisExclusionSpecialClassBusinessIncome`, `CannabisExclusionWithHempException` (Special Class),
`CannabisExclusionWithHempExceptionBuilding`, `CannabisExclusionWithHempExceptionBusinessIncome`,
`CannabisExclusionWithHempExceptionPersonalProperty`,
`CannabisExclusionWithHempExceptionSpecialClassBusinessIncome`

### D2 — Increased Cost Of Loss And Related Expenses For Green Upgrades Endorsement (21)

The single largest newly-named cluster — one file per coverage (Building/Business Income/Personal
Property/Special Class/Special Class Business Income) per cause-of-loss form (BGI/BGII/Broad/Special/
Earthquake), 5×5 minus 4 not filed = 21 files, all one family conceptually, listed as the raw
coverage×form matrix since no single collapsed name captures it cleanly:

`IncreasedCostOfLossAndRelatedExpensesForGreenUpgradesEndtBldg{BasicGroupI,BasicGroupII,Broad,Special,Earthquake}Cov`,
`...BusInc{same 5}Cov`, `...PersProp{same 5}Cov`, `...SpecialClass{same 5}Cov`,
`...SpclClassBusnIncome{same 5}Cov`

### D3 — Increase In Rebuilding Expenses Following Disaster (10)

Plain and Special-Class variant, each across BGI/BGII/Broad/Special/Earthquake:

`IncreaseInRebuildingExpensesFollowingDisaster{BasicGroupI,BasicGroupII,Broad,Special,Earthquake}Cov`,
`IncreaseInRebuildingExpensesFollowingDisasterSpecialClass{same 5}Cov`

### D4 — Scheduled / Unscheduled Building Property, Tenants Policy (20)

Glass vs. Other-Than-Glass, Scheduled vs. Unscheduled, each across BGI/BGII/Broad/Special/Earthquake —
a real 2×2×5 matrix, no coverage this size was previously itemized in this document:

`ScheduledBuildingPropertyTenantsPolicyBuildingGlass{5 COL forms}Cov`,
`ScheduledBuildingPropertyTenantsPolicyDetailBuildingPropertyOtherThanGlass{5 COL forms}Cov`,
`UnscheduledBuildingPropertyTenantsPolicyBuildingGlass{5 COL forms}Cov`,
`UnscheduledBuildingPropertyTenantsPolicyBuildingPropertyOtherThanGlass{5 COL forms}Cov`

### D5 — Leased Property Detail (10)

Plain and Agreed Value variant, each across BGI/BGII/Broad/Special/Earthquake:

`LeasedPropertyDetail{5 COL forms}Cov`, `LeasedPropertyDetailAgreedValue{5 COL forms}Cov`

### D6 — Ordinance or Law, Tenants' Interest in Improvements and Betterments — file-level variants (12)

**Cross-reference, not a new coverage:** Part B3 above already lists this family conceptually
(`OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBettermentsCovA` "(+ BGI/BGII/EQ variants)"
etc.). This sweep's normalization didn't collapse the BGI/BGII/EQ suffix on these four specific file
names the way it did elsewhere, surfacing the literal 4 coverages × 3 forms = 12 file names individually.
Listed here for completeness of the file-level count, not as 12 additional undocumented families beyond
what B3 already flags: `OrdinanceOrLawCoverageForTenantsInterestInImprovementsAndBettermentsCov{A,B,C,BandC}{BGI,BGII,EQ}`.

### D7 — Specified Business Personal Property Temporarily Away From Premises (5)

`SpecifiedBusnPrsnlPropTempAwayFromPremisesDetail{5 COL forms}Cov`

### D8 — Off-Premises Interruption of Business — Vehicles and Mobile Equipment (4)

Collision vs. Other-Than-Collision, plain and Special Class Business Income variant — first appeared in
chat as a Form Pages entry (see BUILD-LOG.md Entry 28's endorsement list), now confirmed to have its own
`SetPremium` rating definition, not just a form-page listing:

`OffPremInterruptionOfBusnVehsMobileEquipmtBusnIncDetail{Collision,OTC}`,
`OffPremInterruptionOfBusnVehsMobileEquipmtSpclClassBusnIncomeDetail{Collision,OTC}`

### D9 — Food Contamination (4)

Additional Advertising vs. Food Only, plain and Special Class Business Income variant:

`FoodContaminationBusinessInterruptionAndExtraExpense{AddlAdv,FoodOnly}Cov`,
`FoodContaminationBusinessInterruptionAndExtraExpenseSpclClassBusnIncome{AddlAdv,FoodOnly}Cov`

### D10 — Limited Coverage For Unmanned Aircraft — Drone / EQ split (10)

**Refines, doesn't replace, the existing Part C exception.** Part C above already flags this family as
"5 attaching-coverage variants, own rate chain" (Building/Business Income/Personal Property/Special
Class/Special Class Business Income). This sweep found each of those 5 actually splits into two —
a Drone sub-form and an EQ sub-form — 10 file-level variants, not 5. Correct Part C's count in a future
pass: `LimitedCoverageForUnmannedAircraftScheduledAndOrBlanketCoverage{Detail,BusnIncomeDetail,PrsnlPropDetail,SpecialClassDetail,SpclClassBusnIncomeDtl}{Drone,EQ}Cov`

### D11 — Equipment Breakdown, additional variants (4)

Part B2 already itemizes `EquipmentBreakdownCauseOfLossBusnInc` (+ `WaitingPeriod` variant) for Business
Income. These are Building-side variants not previously listed:
`EquipmentBreakdownCauseOfLossBldg{AmmoniaContamination,EB,HazardousSubstanceOtherThanAmmonia}Cov`,
plus confirming Business Income's own `EquipmentBreakdownCauseOfLossBusnIncWaitingPeriod` file exists
distinctly from the plain `EquipmentBreakdownCauseOfLossBusnInc` B2 already names.

### D12 — Radioactive Contamination / Molten Material, standalone (2 families, 10 files)

Part B7 already itemizes `VacancyPermitRadioactiveContamination` and `VacancyPermitMoltenMaterial` — the
Vacancy-Permit-gated versions. These are the general, non-vacancy-gated versions, each filed once per
attaching coverage (5 files apiece): `RadioactiveContamination`, `MoltenMaterial`.

### D13 — Personal Property Special Cause-of-Loss, scheduled valuable-item classes (4)

`PersonalPropertySpecialCOLFursFurGarmentsAndGarmentsTrimmedWithFur`,
`PersonalPropertySpecialCOLJewelryWatchesPearlsBullionGoldSilverPlatinumAndOtherPreciousMetals`,
`PersonalPropertySpecialCOLPatternsDiesMoldsAndForms`,
`PersonalPropertySpecialCOLStampsTicketsAndLettersOfCredit`

### D14 — Small remainder families (17)

`PierAndWharfAdditionalCoveredCausesOfLoss` (+ `Struct` variant, 2 families),
`ElectronicCommerceLossOfBusinessIncomeCov`, `ElectronicCommerceLossOfDataCov` (2),
`ZzDisclosureOfPremiumEstimatedPremiumCertifiedActsTerrorismPursuantTerrorismAct2002`,
`ZzDisclosureOfPremiumThrough123105CertifiedActsTerrorismPursuantTerrorismAct2002`,
`ZzDisclosurePursuantToTerrorismRiskInsAct2002` (3 — terrorism/TRIA disclosure, likely $0-premium
administrative records rather than real rating, unconfirmed),
`BusnIncomeFromDependentPropertiesLimitedInternationalCov`,
`ExtraExpenseFromDependentPropertiesLimitedInternationalCov` (2 — International sub-variant of the
already-itemized B2 Dependent Properties family), `PropInProcessOfMfrByOthersLimitedInternationalCov`,
`AdditionalCoveredPropertyDetail` (+ `SpecialClassDetail` variant, 2), `LocationFireDepartmentCharge`,
`LocationNewlyAcquiredLocationTimeElement`, `MortgageholdersErrorsAndOmissionsCoverageForm`,
`NewlyAcquiredOrConstructedPropertyIncreasedLimit`, `OccupClassTemporarilyInPortableStorageUnits`,
`StructureBuildersRiskBuildingMaterialsAndSuppliesOfOthers`,
`TheftOfBuildingMaterialsAndSuppliesOtherThanBuildersRisk`, `ValueReportingFormGeneralInformation`.
Two entries here (`CivilAuthorityIncreasedCoveragePeriodRadius`,
`ExtraExpenseFromDependentPropertiesSpclClassBusnIncomeDetail`) are likely near-duplicates of existing
B2 rows under a slightly different derived name — flagged, not removed, pending a closer read.

---

## Correction, 2026-09-11 — Business Income's Earthquake chain was already documented; a BUILD-LOG entry overstated the gap

`BUILD-LOG.md` Entry 28 (2026-09-11) described Business Income's Earthquake rate chain as "confirmed to
exist... not opened in the rater" and grouped it with genuinely untraced items. That's accurate about
the **live-rater build status** (never checked against `CFRater1.01.xlsb`) but overstates the
**documentation** gap — `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` §"Earthquake — rate build-up"
and §"Earthquake — premium: the Agreed Value asymmetry" (lines 528-642) already trace the full 8-step
chain, the Agreed-Value-only premium mechanism, and the surcharge shape shared with Extended Period of
Indemnity — read directly, in detail, during this same session. What's genuinely still open: (1) the
**standalone Earthquake endorsement** that attaches EQ coverage in the first place (Part B11 above — a
different question from "given EQ coverage exists, how does the rate compute," never traced); (2)
whether any of this is **built in the live rater** (unchecked); (3) the same level of standalone
HTML/granular treatment Basic Group I/II/Broad/Special got this session (not done for Earthquake).
Recorded here so a future pass trusts this document's "documented" column over a session summary's
looser framing.

---

## What's still not itemized

**Update 2026-09-11: this section is now resolved — see Part D above.** The corrected sweep found
**~243 families**, not 97; as of the original 2026-08-19 pass, ~146 of those were not individually named
anywhere in this document. Part D (added 2026-09-11) names 143 of them, independently re-deriving the
sweep and diffing against everything already itemized above. A few names from the original sample list
here turned out to belong to families already covered elsewhere once actually checked
(`DiscretionaryPayrollExpense`, `ChangesFungusWetRotDryRotBacteria`,
`BuildersRiskCollapseDuringConstruction`,
`BuildersRiskTheftOfBuildingMaterialsFixturesMachineryEquipment`,
`BusinessIncomeAndOrExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems`,
`BusnPrsnlPropLimitedInternationalCov` did not appear in Part D's diff — likely already matched against
an existing Part B row by the stricter normalization used this pass; not independently re-verified,
flagged for a future pass rather than asserted either way). **Naming is done. Tracing is not** — every
family in Part D is still a name, not a read rule file.

---

## Summary count

| | Count |
|---|---|
| Core coverages, fully documented (doc + tables + diagrams) | 5 |
| Endorsement/rider families individually itemized in this document, not yet documented (Parts B1-B10) | 93 (91 from the original sweep + Earthquake + Flood) |
| Endorsement families partially covered (mechanism described inside a parent doc, not independently traced) | 3 (`BusinessIncomeAgreedVal`, `SpecialClassBusnIncomeAgreedVal`, `BusinessIncomeExtendedPeriodOfIndemnityCoverage`/`SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage` treated as one shared caveat) |
| Attach-only dispatch files (excluded from the rating-definition count) | 27+ files → 0 additional coverages, except the Unmanned Aircraft exception above |
| **Remainder families, now individually named (Part D, added 2026-09-11)** | **143** — named, not traced; see Part D above |
| **Total distinct coverage/endorsement families in the package** | **~241-243** (5 + 93 + 143, ±2 for the normalization-artifact/near-duplicate caveats noted in Part D) |

**Still only 5 of ~243 real coverage/endorsement families in this package are fully documented — roughly
2%.** Naming Part D's 143 families (2026-09-11) did not reduce this number — none of them have been
traced, only identified. Ordinance or Law (18 families) and the Business Income time-element extensions
(17 families) remain the two largest *itemized-and-at-least-partially-understood* undocumented clusters.
Within Part D, Green Upgrades (21 files) and the Scheduled/Unscheduled Tenants Policy Building Property
family (20 files) are now the two largest individually-named-but-untraced clusters — bigger than
Ordinance or Law once file count is the measure, though neither has had even a first read yet the way
Ordinance or Law's structure has been sketched from filenames alone.
