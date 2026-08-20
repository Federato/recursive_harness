# Railroad Protective Liability — Required ERC Tables

**Source:** `docs/gates/GATE-335-RAILROAD-PROTECTIVE.md` §§0, 3, 5, 6, cross-referenced against
`docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.1/§3.1.1/§3.2.5 and
`docs/erc/03-RATING-STRUCTURE.md` §2.4.

**Line:** General Liability (GL), subline code 335 (Railroad Protective, Rule 49) — shares its
subline code with, but reads some tables from, Owners & Contractors Protective (Rule 46).

**Derived from:** `RailroadProtective_RatingAlgorithms.md` (this pair's companion document).

**Documented:** 2026-08-20.

This lists every ERC rate table (CW and/or state-filed) that the Railroad rating algorithm
touches, as resolved by the gate doc's own tracing of the rule chain and its layer-pattern table
(§5). Unlike the CF ERC_Tables template, the gate doc does not report a `FirstNonNull(state,
CW)` two-pass lookup pattern for every table — for several Railroad tables the layer pattern is
**inverted**: the countrywide row carries the structural constant, and the state layer alone
carries the class-specific numbers (gate doc §5). Each row below states which pattern applies
where the gate doc says so, and flags "not resolved" where it doesn't.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `RailroadELP` | Rating-basis selector — value column `RailroadELP`, string `"Industry"` in all 204 rows across all 51 jurisdictions, every as-of date. Single-valued: Railroad has exactly one rating path | State, `ClassCodeRailroad` |
| `BaseELPRR` | Estimated Loss Potential by class and train-count band; excludes class `40014` | State, ClassCode, `NumPassgrFreightTrains` (6 bands) |
| `OwnersContractorsLossCost` | **OCP's table, read by Railroad.** `SetConstructionOpsOwnerFactor` hardcodes `classCode = "16292"` regardless of the risk's own class | State \| CW, `classCodeOwnersContrctrs = "16292"` |
| `ILFRailroad` | Increased Limits Factor, Rule 56.B.7 | State, limit selection (exact key structure not resolved in source docs) |
| `RailroadLCM` | Loss Cost Multiplier | State \| CW — CW carries 1 row, value `1`; 0/51 states file their own |
| `ConstructionOpsOwnerAdjmtFactor` | Fixed adjustment applied to the OCP loss cost (Step 3) | State \| CW — CW carries 1 row, value `1.5`; 0/51 states |
| `WorkTrainsOrOtherRREquipmtRate` | Work-trains charge, dollars per $1,000 Total Cost | State \| CW — CW carries 1 row, value `56.8`; 0/51 states. **Withdrawn CW 2027** |
| `CovForInjuriesToSuprvsrInspctrsOtherEmpsOfTheInsd` | Supervisors/inspectors extension factor | State \| CW — CW carries 1 row, value `0.1`; 0/51 states. **Withdrawn CW 2027** |
| `RailroadHomogeneityIndex` | Not resolved in source docs — gate doc §5 lists this table's row counts (0 CW / 51×969 state) but does not name the rule that reads it or its purpose |

## Coinsurance / LOI / deductible tables

Not applicable to this subline. Railroad Protective is rated on Total Cost per $1,000 with no
coinsurance, limit-of-insurance, or deductible mechanic described anywhere in the gate doc or the
cross-referenced rating-structure docs — unlike CF's Building forms, Railroad has no
building-value or blanket-limit concept. The gate doc's rule list (§2) contains no
coinsurance/LOI/deductible rule names for Railroad.

## Premium-level tables

| Table | Used for | Keys / rows |
|---|---|---|
| `MinPremiumRR` | Minimum premium | State \| CW — CW carries 1 row, value `0`; 0/51 states. **Withdrawn CW 2027** |

*Not resolved in source docs* — no CyberIncidentExclusion-equivalent, IRPM, package-mod, or
multi-premium-discount factor is mentioned anywhere in the gate doc for Railroad; if such
policy-level factors apply to this subline they are not documented in the source material read
for this reformat.

## Statistical / subline tables (reporting only, not rate-affecting)

| Table | Used for |
|---|---|
| `PolicyLimitsRailroadStatCode` | Statistical reporting code — 9 rows countrywide, 0/51 states |

## Not ERC tables

**`RailroadLossCost`** exists as a `RateTable.csv` in all 10 countrywide package editions and has
**0 rows in every edition and every jurisdiction (0/51 states, 0 CW)**. Scanning every rule file
in every countrywide package for the string `RailroadLossCost` returns **zero hits** — no rule
anywhere in the corpus reads it (gate doc §3). This is not a filed rate table in any operative
sense: it is a table that exists, is permanently empty, and has no reader. It is listed here,
rather than in the rate-build-up section above, precisely because it plays no role in rating
despite its name suggesting otherwise (gate doc §3, "a populated-looking name may have no
purpose at all").

`LookupPremOpsLCM` is present in the Railroad rule file in all 10 editions but is **never
called** — the same dead lookup found copy-pasted into the Liquor Liability rule file
(gate doc §5). Not a table itself, but flagged here as a dead reference worth knowing about when
tracing what actually drives the rate.

---

## Layer pattern — full table (from gate doc §5)

| Table | Countrywide | States (as of today) |
|---|---|---|
| `BaseELPRR` | 0 rows | 51/51 · exactly 18 rows each (918 total) |
| `RailroadELP` | 0 rows | 51/51 · 204 |
| `ILFRailroad` | 0 rows | 51/51 · 1,836 |
| `RailroadHomogeneityIndex` | 0 rows | 51/51 · 969 |
| `OwnersContractorsLossCost` | 0 rows | 51/51 · 563 → 8/51 · 88 at the 2027-04-01 cliff |
| `RailroadLossCost` | 0 rows | 0/51 — and no reader anywhere in the corpus |
| `RailroadLCM` | 1 row: `1` | 0/51 |
| `ConstructionOpsOwnerAdjmtFactor` | 1 row: `1.5` | 0/51 |
| `WorkTrainsOrOtherRREquipmtRate` | 1 row: `56.8` | 0/51 |
| `CovForInjuriesToSuprvsrInspctrsOtherEmpsOfTheInsd` | 1 row: `0.1` | 0/51 |
| `MinPremiumRR` | 1 row: `0` | 0/51 |
| `PolicyLimitsRailroadStatCode` | 9 rows | 0/51 |

**The pattern is inverted relative to a typical filed-rate table**: class-specific numbers
(`BaseELPRR`, `ILFRailroad`, the ELP selector) are state-supplied with zero countrywide rows,
while structural/company factors (`RailroadLCM`, `ConstructionOpsOwnerAdjmtFactor`,
`WorkTrainsOrOtherRREquipmtRate`, the supervisors factor, `MinPremiumRR`) are countrywide
single-row constants with no state ever overriding them. The gate doc identifies this as the same
inversion found in Liquor Liability, generalizing it to "a property of ELP-rated coverages" (gate
doc §5) rather than a Railroad-specific quirk.

**One value is not a factor but a published countrywide dollar rate:** `WorkTrainsOrOtherRREquipmtRate
= 56.8` is a rate per $1,000 of exposure, not a multiplier, and the manual confirms it to the
cent (Procedure 5.E.2.c). This is called out separately because it partially contradicts a
prior project finding that "there is no national ILF table and no national loss cost publication
at all" — true of loss costs, false of this rate (gate doc §5).

---

## State deviations

Only **AK and NY** file a `GeneralLiabilityClassificationRailroadCoverage` rule — the smallest
state-deviation surface of any subline gated to date (gate doc §6). Each overrides exactly three
rules; two are boilerplate (`InitializeRuleSet`, `ErcProcess`). The only substantive override is
`SetMoldStatCode`, a statistical-coding rule that changes no premium. `BaseELPRR` has exactly 18
rows in all 51 jurisdictions — no state adds or drops a row from that table.

---

## Verification

**18-cell cross-source check.** Alaska's ERC `BaseELPRR` table (`GL_AK_20260801_V02`) checked
cell-by-cell against Procedure 5.E of the filed ELP Supplement `GL-AK-2020-LC-001-C.pdf`
(pp.10–11) — a 2026 machine-readable package against a 2020 filed PDF, six years apart. All 18
cells (3 classes × 6 train-count bands) match to the cent; class `40014` is correctly absent from
both, since it is derived rather than tabulated (gate doc §4). This is recorded in the gate doc as
the first cell-by-cell (rather than structural) cross-source rate confirmation in the project.

**Orphan-table check.** `RailroadLossCost.RateTable.csv` was confirmed present (0 rows) in all 10
countrywide package editions and all 51 jurisdictions, and confirmed to have zero readers by
scanning every rule file in every countrywide package for the literal string
`RailroadLossCost` (gate doc §3).

**Uncalled-lookup check.** `LookupPremOpsLCM` was confirmed present but never invoked in the
Railroad rule file across all 10 editions (gate doc §5).

**No end-to-end premium oracle.** The golden case (`GL_CW_20231201_V03`) carries Railroad with
`CoverageOnPolicyIndicator = 0` and `Premium = 0.0` — this confirms only the entry gate, not any
rate table's values in a live premium calculation. `tests/verify_golden.py`: 80/80, unchanged
(gate doc §8). Railroad is the third subline gated without a positive-premium oracle, after OCP
and Liquor Liability.

---

## Open items carried from the gate doc

- **OI-45** (new): non-construction Railroad operations are a manual-only refer-to-company
  trigger (Procedure 5.E.1.b, 5.E.3.d) with **no ERC-side discriminator** — the engine will rate
  any submitted class code without detecting this condition (gate doc §7, §9).
- Table key structures for `ILFRailroad` and `RailroadHomogeneityIndex` beyond what is stated
  above are *not resolved in source docs*.
