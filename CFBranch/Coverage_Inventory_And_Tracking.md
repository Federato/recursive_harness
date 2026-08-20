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
| Business Income | `CommercialPropertyBusinessIncome` | `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` | `BusinessIncome_ERC_Tables.md` | Yes — 5 forms (incl. Earthquake) |
| Special Class Business Income | `CommercialPropertySpecialClassBusnIncome` | `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md` | `SpecialClassBusinessIncome_ERC_Tables.md` | Yes — 5 forms (incl. Earthquake) |

These are the only five families in the 97 with a *master* `Set*RatesAndFactors`-orchestrator file
(confirmed separately by grepping for `Name="SetBlanketRatesAndFactors"` across the whole `Rules`
directory — exactly these five files, no others). Every remaining family below is an endorsement or
add-on that modifies or supplements one of these five rather than introducing a sixth independent base
coverage.

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

## What's still not itemized

The corrected sweep found **243 families**, not 97. This document itemizes, by name, the original 97
(Parts A/B1–B10) plus Earthquake and Flood (Part B11) — **roughly 146 families surfaced by the corrected,
unrestricted sweep are not yet individually listed here.** A sample from the corrected family list, to
give a sense of what's in that remainder without claiming to have categorized it: `CannabisExclusion`
(and a `WithHempException` variant, each × 5 attaching coverages), `ChangesFungusWetRotDryRotBacteria`,
`DiscretionaryPayrollExpense`, `IncreasedCostOfLossAndRelatedExpensesForGreenUpgradesEndt`,
`IncreaseInRebuildingExpensesFollowingDisaster`, `LeasedPropertyDetail`,
`ScheduledBuildingPropertyTenantsPolicyBuildingGlass`, `SpecifiedBusnPrsnlPropTempAwayFromPremisesDetail`,
`BuildersRiskCollapseDuringConstruction`, `BuildersRiskTheftOfBuildingMaterialsFixturesMachineryEquipment`,
`BusinessIncomeAndOrExtraExpnCovForY2KComputerRelatedAndOtherElectronicProblems` (yes, still filed),
`BusnPrsnlPropLimitedInternationalCov`. **Finishing this itemization properly is the next step**, not
done in this pass — the full corrected, normalized list is reproducible with the command in the Method
section's correction note above, run without the `*CoverageRules.Rule.xml` restriction.

---

## Summary count

| | Count |
|---|---|
| Core coverages, fully documented (doc + tables + diagrams) | 5 |
| Endorsement/rider families individually itemized in this document, not yet documented | 93 (91 from the original sweep + Earthquake + Flood) |
| Endorsement families partially covered (mechanism described inside a parent doc, not independently traced) | 3 (`BusinessIncomeAgreedVal`, `SpecialClassBusnIncomeAgreedVal`, `BusinessIncomeExtendedPeriodOfIndemnityCoverage`/`SpecialClassBusnIncomeExtendedPeriodOfIndemnityCoverage` treated as one shared caveat) |
| Attach-only dispatch files (excluded from the rating-definition count) | 27+ files → 0 additional coverages, except the Unmanned Aircraft exception above |
| **Families surfaced by the corrected sweep but not yet individually itemized** | **~146** — see "What's still not itemized" above |
| **Total distinct coverage/endorsement families in the package (corrected count)** | **243** |

**Only 5 of 243 real coverage/endorsement families in this package are fully documented — roughly 2%.**
This number is now built on the corrected, unrestricted sweep rather than the original filename-limited
one. Ordinance or Law (18 families) and the Business Income time-element extensions (17 families) remain
the two largest *itemized* undocumented clusters; Earthquake (up to 20 files across its four form
variants and five attaching coverages) is comparably large and was entirely missed until this correction.
The ~146 not-yet-itemized families are an unknown quantity in size — some of the sampled names above
(Cannabis Exclusion × 2 variants × 5 coverages, for instance) suggest more sizeable clusters are still
hiding in that remainder.
