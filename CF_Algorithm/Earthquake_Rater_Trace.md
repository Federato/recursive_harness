# Earthquake: trace for the Excel rater (2026-09-24)

Status: **Phase 1 BUILT 2026-09-24** (Building + Contents, CP 10 40 / 10 28 -- see the backlog entry). Rest traced, not built. Analysis only. Sources are read-only reads of the CW 2026 rules
(`ISO_ERC_Files/CF/20260601/CFCW20260601V01/Rules`), the older bases, the state overlays, the STC payloads, the workbook
(read with pyxlsb) and the harness chunk 10 records. Claims marked *(re-verify)* came from one pass and should be re-read before
a build step depends on them.

## Plain English

Earthquake is a separate peril with its own rate. Nothing the rater computes today feeds it except a few shared factors.
Every state files its own earthquake loss costs; the countrywide file has none. The rate depends on:
- the building's earthquake construction class (A1 to E3);
- the earthquake territory, which the user must supply because no rule derives it from ZIP or county;
- a handful of building modifiers;
- the deductible.

The premium is its own line. It is not part of the Building, Contents or BI premiums.

## Where each side stands

| Side | Status |
|---|---|
| Harness engine | Runs EQ through ISO's own rules (chunk 10 closed 2026-09-22, golden case $6). One engine fix: banded lookup with more than one range (`docs/CF-ENGINE-FIX-BANDED-LOOKUP.md`). Open: **OI-103**, where ISO refuses some EQ lookups that the engine rates (AK/WY EQTerr 22 tier, BCEGEQFactor, HeightTerrGroup, BuildingHeightFactor). Golden case never confirmed on live ISO. |
| Excel rater (1.02) | **Not built.** Has only: Schedule location column S `EQTerr` (SC only, `TBL - EQTerr` 538 SC ZIPs, RC-3), `Defaults` row 12 `EQCovIndicator` = "No Coverage", and Cyber exclusion keys for the Earthquake group (all 1.0). `OUT - Diagnostics` row 37 and Release Plan row say "untraced on both sides", which is stale for the harness. |
| Payload (119) | Sends only `EQTerr` (SC). `EQCovIndicator` is "No Coverage" on every record. |

## Rating chain (CW 2026)

`P(n)` = product rounded to n places. The chain lives in the five parent rule files (`SetEQRatesAndFactors`), not in the 97
`*Earthquake*` files. It runs for every structure through `SetBlanketRatesAndFactors`.

**Building** (`CommercialPropertyStructureRules`, `SetEQRatesAndFactors` ~11118)
1. `EQBaseRate` = `EQLossCostBldg[State, EQClass, EQTerr]`. It is 0 when `EQCauseOfLossForm` is Not Applicable or blank.
2. `EQRate` = P3(P3(P3(Base x LCM) x RoofACV) x SoftStory x Sprinklered x Height x BCEG-EQ x MasonryVeneer x BuildersRisk).
   - Soft story: 1.42 (building) / 1.28 (personal property) when `SoftStory` = Yes.
   - Sprinklered: flat 1.06 when `SprinklerSystem` is not "None" and the coverage is not leakage-only.
   - Height: `BuildingHeightFactor[NumStories, EQClass, HeightTerrGroup[EQTerr]]`. Both tables are state-filed with 0 CW rows.
   - BCEG: `BCEGEarthquakeFactor[State, BCEG]`. A blank BCEG gives 0, which zeroes the premium.
   - V02 (MO) uses `BCEGEQFactor[BCEG, EQTerr]` instead.
   - Masonry veneer: 10-50% = 1.10, over 50% = 1.15. The field sits on the endorsement record.
   - Builders risk: class 1150 only.
3. `EQCauseOfLossAdjustment` = P3(EQRate x leakage-only factor). The factor is 0.21 for leakage-only, else 1.
4. `AdjustedEQRate`, by form:
   - CP 10 40 / CP 10 28: x `EQCoinsuranceFactor`, which is the ordinary coinsurance table (80% 1, 90% .95, 100% .90).
   - Leakage-only: x the leakage coinsurance factor (interpolated, 10-100).
   - *(re-verify: the building gives coinsurance below 80% a factor of 1.0, while personal property and Special Class use
     `LessThan80PctMultiplicativeFactor`.)*
5. `EQDeductibleByLocationFactor`: 0.995 for leakage-only, else 1.
6. `EQDeductibleFactor`, by form:
   - CP 10 40: `EQPercentageDeductibleFactor[State, EQDeductibleTier, EQClassToUse, EQDeductible%]`.
     `EQDeductibleTier` = `EarthquakeDeductibleTier[State, EQTerr]` (state-filed in 46 jurisdictions).
     `EQClassToUse` groups the classes: A1 / B1+C1 / D1-D3+E1 / E2+E3.
   - CP 10 28: `EQFlatDeductibleFactor[..., EQDeductible$, EarthquakeTotalPropertyValue band]`. The band total is the
     EQ-elected building + personal property + Special Class full values at the location.
   - CP 10 29: 13 sub-limit flat deductible tables.
   - CP 10 45: state tier tables. About 40 states override these; the CW table returns 0.
   - Leakage-only: the ordinary deductible factor.
7. `FinalEQRate` = P3(P3(Adjusted x DedByLoc) x EQDedFactor).
8. Premium (on the endorsement record) = P0(P0(P0(FinalEQRate x Limit/100) x CyberEQ) x CyberCOLExcpEQ).
   No IRPM, package mod, ordinary deductible or LOI. Sub-limit forms use the sub-limit Limit.

**Personal property**
- `EQLossCostPrsnlProp[State, EQClass (the building's), EQTerr, EQGrade 1-4]`.
- Height, sprinklered and BCEG are copied from the building (BCEG 1.0 for YARD).
- Leakage-only uses the building's EQRate x a grade factor (.21 / .315 / .42).
- Otherwise the same as the building.

**Business Income**
- The building's EQBaseRate x LCM x the building's modifiers.
- COL adjustment = P3(StoryMod x P3(BldrsRisk x P3(EQRate x SL))).
- x the ordinary BI `Factor`.
- Max-period / monthly / EE-only coverage uses the location's highest BI EQ base rate.

**Special Class:** `EQLossCostBldg` x LCM with no modifiers, then coinsurance and deductible. **SC BI:** the SC `EQRate` x the BI factor.

**Blanket:** only CP 10 40 / CP 10 28 items "Included in Blanket".
- Average = sum(FullValue x COLAdj x DedByLoc x EQDed) / TotalFullValue x the blanket's coinsurance factor.
- Highest = the maximum of those rates.
- Each item's limit = its share of the blanket EQ limit.
- Sub-limit blanket premium is computed but never rated (empty `ErcProcess`).

## Inputs the rater would need

| Level | Field | Values |
|---|---|---|
| Policy | EQSubLimitBlktIndicator | Yes / No |
| Location | EQCauseOfLossForm | Not Applicable, CP 10 40, CP 10 28, CP 10 45, CP 10 29 |
| Location | EQTerr | state-filed list; user supplies it (manual territory) |
| Structure | EQCovIndicator | Yes Included in Blanket / Yes Not Included / No Coverage / Not Applicable |
| Structure | EQClass | A1 B1 C1 D1 D2 D3 E1 E2 E3 |
| Structure | EQDeductible | 5-40% (2% only for class 1150 with C1), or $500-$1,000,000 depending on form |
| Structure | EQSprinklerLeakageOnly (+ its coinsurance), SoftStory, masonry veneer %, FullBldgValue | |
| Structure (reused) | BCEG, SprinklerSystem, NumStories, Coinsurance | already on the Schedule |
| Personal property | EQCovIndicator, EQGrade 1-4, EQSprinklerLeakageOnly | |
| Special Class | EQClass (constrained by `DomainEQClassSpecialClass`) | |

## Gates and traps

- A form record is attached only when `EQCovIndicator` starts with "Yes" and matches the location form. The four forms are
  mutually exclusive.
- The ordinary cause of loss is not a gate.
- Silent zeros: blank BCEG, blank leakage-only flag, tier 0, blank NumStories (BI story factor).
- A blank SprinklerSystem silently applies 1.06.
- About 104 EQ validation messages.

## State variation

- Every rated state files EQ loss costs, including CA. PR is out of scope.
- **TX:** its own deductible formula (1 - (Ded - Base) x Discount), an additional-hazard factor and a Rule 73 adjustment.
- **CA:** Limited EQ endorsement for residential lessors.
- **NY:** BI sub-limit overrides.
- **AL / KS / RI:** public-institutional factor.
- **CA FL GA KY MA MT SC VT:** roof-tank hazard factor.
- **GA / MT:** own class-to-use and height rules.
- **DC / NY / WV:** `SetEQRate` overrides.
- **Bases:** V04 = 2026 for every EQ rule; V03 differs only in blanket messages; V02 (MO) uses `BCEGEQFactor[BCEG, EQTerr]`.

## STC evidence

69 of 365 CF payloads elect EQ, in 28 states: CP 10 28 x65, CP 10 45 x3, CP 10 40 x1 (the only leakage-only case). No blanket EQ.
Clean CP 10 28 with personal property: `20230801v4/CF UT 20260401 V01/STC/STC_CP000020296.json`.

## Corrections to chunk 10 records *(re-verify, then fix in `docs/`)*

- `EarthquakeDeductibleTier` is empty only in CW; it is not empty everywhere.
- The sub-limit STC fixtures are CP 10 45, not CP 10 29.
- `BCEGEQFactor` is filed by 44 states, not 3.
- The state override census is far wider than 10 states.
