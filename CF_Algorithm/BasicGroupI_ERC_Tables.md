# Basic Group I — Required ERC Tables

**Source ERC package:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01`
**Line:** Commercial Property (CF), Countrywide, edition 06-01-2026, V01
**Derived from:** `CauseOfLoss_Building_RatingAlgorithms.md`
**Documented:** 2026-08-18

This lists every ERC rate table (CW and/or state-filed) required to rate Basic Group I building coverage, resolved by tracing `SetBGIRatesAndFactors` and the Basic Group I premium rules in `CommercialPropertyStructureRules.Rule.xml` down to each `Lookup`'s `MatrixFromConstant`, and verified against the actual files in `CFCW20260601V01\Rate Tables`.

All tables follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern — a state can override any of these with its own row, but if it doesn't, a CW row is required for the lookup to resolve.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `BasicGroupIRate` | Class base rate | State\|CW, ClassCode, ConstructionCode, "Not Applicable", "Building" |
| `RatingTerritoryGroupIFactor` | Territory factor | State\|CW, BasicGroupIRatingTerr |
| `ProtectionClassFactor` | Protection class multiplier — **NC files its own 12-code scale, different from CW's 28 codes; see session findings below** | State\|CW, ProtectionClass |
| `SubStdConditionRate` | Substandard-condition rate addend | State\|CW, condition A–E args |
| `VacantBldgPreviousOrIntendedOccup` | Vacant-building rate addend (feeds `VacantBuildingRate`) | State\|CW, occupancy |
| `SprinklerLeakageNotExcluded` | Specific/Tentative rating factor | State\|CW |
| `SprinklerLeakageExclNonSprinkleredRate` | COL adjustment subtraction — **not used directly, see correction below** | State\|CW |
| `SprinklerLeakageExclSprinkleredFactor` | COL adjustment factor — **only ever non-1.0 for Specific/Tentative rating, never Class, see correction below** | State\|CW |
| `VandalismExclFactor` | COL adjustment factor — **election-gated, not automatic; VacantBuilding hardcodes ClassCode 1180 regardless of actual class; see session findings below** | State\|CW |
| `StdPropPolGroupIFactor` | COL adjustment factor — **policy-level, not location-level; gated purely on PolicyType, see session findings below** | State\|CW, "Y" |
| `LimitationsOnCovForRoofSurfacingFactor` | Roof-surfacing ACV factor | State\|CW |

## Coinsurance / LOI / deductible tables

| Table | Used for |
|---|---|
| `CoinsuranceFactor` | Standard coinsurance factor (80/90/100%) — **also serves the blanket-coinsurance branch (same table, different key); FL files an unreachable 70% row, see session findings below** |
| `LessThan80PctMultiplicativeFactor` | Coinsurance <80% branch — flat 1.5, no state variation |
| `BasicGroupILOIFactorBldg` | Limit-of-insurance factor — **the ERC engine linearly interpolates this natively via the table definition, see session findings below** |
| `DeductibleByLocationFactor` | Deductible-by-location factor — flat 0.995, Yes/No only, doesn't vary by the scheduled amount |
| `DeductibleFactor` | Standard deductible factor — **the dropdown AND the factor table both genuinely vary by state (7 distinct table shapes across 47 states), see session findings below** |
| `Deductible250Factor` | Flat $250 deductible factor — universal, zero state overrides |
| `MultiResidentialPropSpecialCreditHeatFactor` | Multi-res credit component — **CW-only for 44 states; MA and ME each file an empty table (`"Not Applicable"` is the only domain option in those two states, so the credit never triggers there); no other state override, see session findings below** |
| `MultiResidentialPropSpecialCreditControlFactor` | Multi-res credit component — **CT files its own row: 0.5 vs. CW's 0.7 for the "under single supervision" option — a real state deviation, not a copy; MA/ME empty like Heat; see session findings below** |

## Premium-level tables

| Table | Used for |
|---|---|
| `CyberIncidentExclusionFactors` | Cyber exclusion factor, keyed by cause-of-loss group ("Basic Group I") |
| `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors` | Cyber exclusion-with-exceptions factor |

## Statistical / subline tables (reporting only, not rate-affecting)

| Table | Used for |
|---|---|
| `DeductibleStatCode` | Statistical reporting code |
| `SublineBasicGroupI` | Subline code |
| `SublineBasicGroupIExcludingSprinklerLeakage` | Subline when sprinkler leakage excluded |
| `SublineBasicGroupIExcludingVandalism` | Subline when vandalism excluded |
| `SublineBasicGroupIExcludingVandalismAndSprinklerLeakage` | Subline when both excluded |

---

## Not ERC tables

`IRPMFactor`, `PackageModFactor`, and `MultiPremiumAndDispersionCreditFactor` are policy-level user/schedule-rated inputs copied down from the policy level (`SetPackageModFactor` / `SetMultiPremiumAndDispersionCreditFactor` use `rul:Copy`, not `rul:Lookup`) — not filed rate tables.

---

## Verification

All 26 tables above were confirmed present as `<TableName>.RateTable.csv` (with matching `<TableName>Def.RateTableDef.xml`) in `CFCW20260601V01\Rate Tables`, by recursively resolving `RunRule` references from `SetBGIRatesAndFactors` and the Basic Group I premium rules to their leaf `Lookup` calls' `MatrixFromConstant` attribute.

> **Correction, 2026-08-19.** "Confirmed present" above checked file existence only, not whether the
> file carries a data row — a gap surfaced when the Personal Property pass hit the same table and
> checked its content. Verified directly: **`BasicGroupIRate.RateTable.csv` and
> `BasicGroupIIRate.RateTable.csv` are header-only — zero data rows, zero `CW` rows.** Both are shared
> between Building and Personal Property. Practical effect: `LookupBasicGroupIRate` and
> `LookupBasicGroupIIRate` resolve to null at the countrywide level for **both** coverages, for **any**
> class/construction/territory/symbol combination — Basic Group I and Basic Group II base rates are
> entirely unresolvable in this package edition without a state-specific filing layered on top. This
> was not caught by the original verification pass and should be treated as the standing check going
> forward: "table exists" and "table has a usable row" are different claims, and only the second one
> is load-bearing. See `BUILD-LOG.md` Entry 3.

> **Watch-item, 2026-09-03: California splits `BasicGroupIRate` into two district-specific tables.**
> While pulling a countrywide `BGI_BuildingRates.csv` dropdown export, CA turned out to have **no**
> `BasicGroupIRate.RateTable.csv` at all. CA instead carries a user-selected Location-level field,
> `District` (`DomainDistrict.DomainTable.csv`: `"District I"` / `"District II"`, no derivation from
> county/territory — the insured/agent picks it directly), and
> `CommercialPropertyStructureRules.Rule.xml` (~line 1216) branches the class-rate lookup on that field:
> `District I` → `LookupBasicGroupIDistrictIRate` → `BasicGroupIDistrictIRate.RateTable.csv`;
> `District II` → `LookupBasicGroupIDistrictIIRate` → `BasicGroupIDistrictIIRate.RateTable.csv`. Both
> tables carry the same key shape as every other state's `BasicGroupIRate`
> (`StateCode, ClassCode, ConstructionCode, Group, CovType`) — CA just needs two of them plus the extra
> `District` input field. **Any Building-rate table/dropdown pulled "per state" needs to special-case
> CA as a two-table state, not assume the single-table shape every other state uses.**
>
> **Confirmed 2026-09-03: Alaska has the same two-table split, but derives `District` instead of
> asking for it.** AK also has no plain `BasicGroupIRate.RateTable.csv` — it carries
> `BasicGroupIDistrictIRate.RateTable.csv` / `BasicGroupIDistrictIIRate.RateTable.csv` (1,369 lines
> each, same key shape as CA's pair), and `CommercialPropertyStructureRules.Rule.xml` branches the same
> way on a field called `BasicGroupIDistrictTerritory`. The mechanism differs from CA, though: in CA
> the agent picks `District` directly on the Location (`DomainDistrict`, a free user choice). In AK,
> `BasicGroupIDistrictTerritory` is **derived from City** via `DomainDistrictAlaska.DomainTable.csv`
> (e.g. "Greater Anchorage Area" → District II, "Greater Juneau" → District I), with one extra wrinkle:
> for City = "Remainder of State" it further depends on a Yes/No flag keyed off
> `BasicGroupIRatingTerr` (`DomainDistrictAK.DomainTable.csv`, keyed by `CountyAK` — not fully traced
> here). **Net effect for the rating engine is the same as CA — two rate tables, no single
> `BasicGroupIRate` — but the input side differs: CA needs a user-facing dropdown field, AK needs a
> City/County-driven derivation instead.** Still not checked whether Puerto Rico (also missing a plain
> `BasicGroupIRate` file) has a third variant of this same pattern.
>
> **Correction, 2026-09-03: this isn't specific to CA's future editions — its in-force edition has the
> same split.** A separate pass (rebuilding `BGI_BuildingRates.csv` and `State_ERC_CW_Editions.csv`)
> found that CA actually **does** have an edition in force as of the 9/1/2026 cutoff —
> `CF CA 20251201 V01`, filed in an older batch (`20230801v3`) that a `20260601`-only search had
> missed entirely, not one of the future editions (`20261001`/`20261101`) originally checked. Verified
> directly: that in-force edition carries the identical `BasicGroupIDistrictIRate` /
> `BasicGroupIDistrictIIRate` pair and no plain `BasicGroupIRate` — so the two-table split is a
> standing structural fact about CA, not an artifact of only having checked not-yet-effective filings.
>
> **Correction, 2026-09-04: `SprinklerLeakageExclNonSprinkleredRate` is not what actually gets
> subtracted in the COL adjustment.** The rule build-up (`SetSprinklerLeakageExclNonSprinkleredBldgRate`
> in `CommercialPropertyStructureRules.Rule.xml`) multiplies the raw filed rate by
> `LossCostMultiplier` and rounds to 3dp *first* — `SprinklerLeakageExclNonSprinkleredBldgRate =
> ROUND(Rate × LCM, 3)` — and it's that value, not the raw table rate, that
> `SetBasicGroupICauseOfLossAdjustment` subtracts from `BasicGroupIRate`. Same pattern
> `VacantBuildingRate` uses in the same formula, verified directly against both rules. Worth knowing:
> at LCM = 1.0 this rounding step inflates the filed CW rate (0.0006) to 0.001 — a ~67% jump, purely
> from a sub-thousandth rate crossing the 3-decimal rounding boundary, not a data error.
>
> **Correction, 2026-09-04: `SprinklerLeakageExclSprinkleredFactor` can never actually be live for a
> Class-rated building.** Checked the `SprinklerSystem` field's own domain list directly: under
> `RatingType = "Class"` the only options are `None` and `Sprinklered Building, but Not Rated as
> Sprinklered` — the "Rated as Sprinklered; <50%/>50%" options that trigger this factor only exist
> under `RatingType = "Specific"` or `"Tentative"`. Confirmed universal, not Building-specific, via a
> second domain table covering every CovForm variant (Building and PP, Condo, Legal Liability, SPP,
> Tobacco Warehouse) — all show the identical restriction. Not a gap in this pull; a structural fact
> about which rating types even offer the triggering input.

---

## Session findings, 2026-09-04 — ProtectionClass through DeductibleFactor

Full spreadsheets built for each of these live in `Spreadsheet_Rater/CF/Supporting Tables/` — this
section is the pointer/summary; the workbooks are the source of truth for exact values.

**`ProtectionClassFactor`** (`BGI_ProtectionClass_Tables.xlsx`) — filed CW (28 codes: 1–10, 8B,
1X–8X, 1Y–8Y, 10W) × 6 Construction Codes, 168 rows. Checked all 47 states: **North Carolina is the
one real exception** — files its own 12-code scale (1–8, 9, 9E, 9S, 10, no 8B/X/Y/10W) with its own
factor table; overlapping codes carry identical values to CW, so it's the code universe that differs,
not the pricing. Puerto Rico's own file is empty, falls through to CW.

**`VandalismExclFactor`** (`BGI_VandalismExclFactor.xlsx`) — an election, not automatic: fires on a
CPP with a Vandalism Exclusion scheduled, or an SPP on a fire-only cause-of-loss form. Otherwise
`1.0`. Keyed on `ClassCode`, 161 CW rows (131 @ 0.98, 26 @ 0.95, 4 @ 0.85 — matches manual Table
74.A.3.b exactly). **Vacant buildings are hardcoded to ClassCode `1180` regardless of the building's
real classification** — verified directly in the rule, not derived from any field. GA/KS/NY file
functional no-op overrides (identical values, just fewer codes, falls through to CW anyway); PR has 5
genuinely different values.

**`StdPropPolGroupIFactor`** — the one **policy-level** factor in this whole set; everything else here
is per-building. Gated purely on `PolicyType = "Standard Property Policy"` (else `1.0`, no lookup
attempted). Flat `0.98` CW, matches manual Rule 69.D.2 exactly. Checked all 47 states: zero real
overrides.

**`CoinsuranceFactor`** (`BGI_CoinsuranceFactor.xlsx`) — bypassed entirely (`1.0`) when
`ClassCode="1150"` (Builders Risk) or `ValuationType="Functional Valuation"`. Otherwise four branches:
standard 80/90/100% lookup; the *same* table reused for the blanket-coinsurance branch (confirmed —
`LookupBlktCoinsuranceFactor` points at the identical matrix, just a different key); a flat `1.5`
surcharge for 50%/60%/70%/None; else `1.0`. **FL files a real, unreachable 70% row** (factor 1.14) —
FL doesn't override the rule logic itself, so the countrywide branching routes any 70% selection to
the flat-1.5 branch regardless, never to FL's own table row. Filed but dead, same pattern as the
roof-surfacing CT/MA/NH quirk.

**`BasicGroupILOIFactorBldg`** (`BGI_LOIFactor_Building.xlsx`) — **the ERC engine interpolates this
natively.** First read of the rule logic showed a plain exact-key lookup and looked like the CW
manual's interpolation procedure (Rule 70.F.3) was a human-only step the machine-readable filing
didn't automate — that was wrong. The interpolation is declared in the *table definition*
(`BasicGroupILOIFactorBldgDef.RateTableDef.xml`: `Limit` as a Range key, `Factor` as
`InterpolateMode="Linear"`), not the rule. Verified the formula reproduces the manual's own worked
example exactly. 342 rows CW (57 limit bands × 6 Construction Codes, grouped 1-3/4-6 matching the
manual's two-column table). Checked all 47 states: only PR has its own file, and unlike most PR
overrides in this project, **all 342 rows are genuinely different** — a complete separate curve, not
a dead artifact.

**`DeductibleByLocationFactor`** — Rule 33.D (Endorsement CP 03 29), confirmed against the manual text
exactly: flat `0.995` whenever the endorsement is scheduled, `1.0` otherwise. Doesn't vary by the
actual dollar deductible — that's `DeductibleFactor`'s job, applied separately and **multiplicatively
on top**, per the manual's own words ("factors apply multiplicatively"). Per-location, not
policy-level. Checked all 47 states: only FL has an (empty) override.

---

## Session findings, 2026-09-08 — `MultiResidentialPropSpecialCreditFactor`

Traced the full mechanism in `CommercialPropertyStructureRules.Rule.xml`: `SetMultiResidentialPropSpecialCreditFactor`
(line 5586) multiplies two independently-gated sub-factors — Heat (line 5386) and Control (line
5486) — both gated on the same test (`MultipleResidentialPropSpecialCredit ≠ "No"` AND `ClassCodeToUse`
in a fixed 12-code apartment list: 0311–0313, 0321–0323, 0331–0333, 0341–0343). `Factor = Round(Heat ×
Control, 3)` if the gate passes; `1.0` otherwise, for the combined factor and each sub-factor
independently (each has its own `IsNull`-guarded else-branch). This mechanism was previously
undocumented — the ERC-tables list above only named the two component tables, not how they combine.

**Both tables genuinely vary by state — this credit is not flat CW like it first appeared:**

- **44 states** get the plain CW tables: Heat = `No`/`Not Applicable` → 1.0, `Yes` → 0.75; Control =
  `No`/`"...not under single supervision..."` → 1.0, `"...under single supervision, maintenance and
  control"` → 0.7.
- **CT** files its own `MultiResidentialPropSpecialCreditControlFactor` only (no Heat override) — the
  single-supervision discount is **0.5**, not CW's 0.7. A real, deeper discount, not a copy-forward.
  CT's dropdown domain is unrestricted (same 3 options as CW), so this is a genuine pricing deviation,
  same pattern as `DeductibleFactor`'s state-shape variance.
- **MA and ME both effectively disable the credit**, but by restricting the *domain table*
  (`DomainMultiResidentialPropSpecialCredits`) rather than the rate table: MA's dropdown only offers
  `"No"`; ME's only offers `"Not Applicable"`. Both states' Heat and Control rate-table files are
  present but empty (header row only, zero data rows) — consistent with the domain restriction, since
  the gate can never pass with either state's only available dropdown value. The credit is filed as
  a no-op in these two states, not simply unfiled.
- Confirmed via full-package grep: no other state (of 47) files any override for either table, across
  every ERC edition from `20191201` through the current `20260601` — CT/MA/ME is a stable three-state
  group across editions, not a one-time filing quirk.

Spreadsheet build guide for this factor: `Excel_Rater_MultiResCredit_Walkthrough.html` (nine-step
wireframe, placeholder cell addresses pending confirmation against the live `BldgBGIRating` tab).

**`DeductibleFactor`** (`BGI_DeductibleFactor.xlsx`) — the biggest surprise in this set: **both the
underwriter-facing dropdown and the factor table genuinely vary by state**, unlike almost everything
else reviewed this session (which defaults to CW with occasional exceptions). 43 states offer 16
deductible options up to $1,000,000; CA, FL, NY, PR offer only 10, capped at $75,000 (no state-level
domain override, falls through to CW). Of the 43-option states, 39 file byte-identical data (the
"Common" table); NV, PA, TX, UT file genuinely different tables. Row-count differences among those
(103/154/63/103 vs the Common table's 154) turned out to be **coarser filing granularity, not missing
coverage** — every deductible still spans the full limit range, just with fewer intermediate
breakpoints. A `Deductible="250"` election routes to a separate universal flat table
(`Deductible250Factor`, matches manual Table 33.C exactly, zero state overrides).

**A correction made mid-session, worth restating as a general caution**: an early pull of CA's
`DeductibleFactor` used the wrong edition (a future, not-yet-in-force filing) and wrongly showed CA
offering deductibles up to $1,000,000. Redone against CA's actual in-force edition
(`State_ERC_CW_Editions.csv`) — CA has no override at all. This is the same CA-edition trap flagged
earlier in this file's own "Watch-item, 2026-09-03" note — worth checking `State_ERC_CW_Editions.csv`
directly before trusting any ad hoc directory glob for CA specifically.
