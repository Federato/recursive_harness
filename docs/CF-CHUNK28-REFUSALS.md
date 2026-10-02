# Property chunk 28, C28-02: every ISO refusal on record, beside what ISO tolerates

Built 2026-10-02 by `scripts/cf/245_chunk28_c28-02_refusals.py` (`--refused`: every `*_refusal.json` and every request with no saved response, re-sent live at its own date; `--tolerated`: every stored request ISO rated, run through ours). Data: `results/cf-raas/chunk28_c28-02_refusals.json`, `chunk28_c28-02_tolerated.json`. Analysis only, no engine change.

## In plain English

When ISO's rules look up a table row that isn't there, ISO sometimes stops and refuses the whole policy; our engine never stops, it carries on with a blank and usually prices something (often $0). This table lists every time we've seen ISO refuse, and checks it against every policy ISO did price.

**The pattern is almost exact.** Of the 66 refusals that still reproduce live, **65 are a lookup filed as `SingleResult` (exactly one row expected) that finds no row**, and our engine records the very same failed lookup in every one. Across the **1,689** stored requests ISO **rated**, our engine never once misses on a `SingleResult` lookup; its 672,950 misses there are all `FirstResult` (the designed "try the state's row, then countrywide's" pattern). So a working rule is: **ISO refuses when a `SingleResult` lookup matches no row.** The one exception (Vermont's empty earthquake sub-limit tier table) is the open empty-state-table question, below. C28-03 has to test the rule with probes where it and its competitors disagree before anything is proposed.

## The refusals that reproduce live (66, at 2026-09-17)

| Table ISO failed on | Cases | Package filing the table (CW = countrywide) | Example keys (ISO) | Ours | Ours saw the same miss |
|---|---|---|---|---|---|
| `EarthquakeDeductibleTier` | 17 | AK GA IN NH NV SC WY | CW, 22 | prices 17 | 17 of 17 |
| `BuildingHeightFactor` | 16 | NH NV SC VT WY | CW, 9-20, 3C, 2 | prices 16 | 16 of 16 |
| `WindstormOrHailDeductibleAsNumber` | 7 | OR | CW,  | prices 7 | 7 of 7 |
| `TotalRatingModicationStatCode` | 4 | CW | CW, 0 (Constant Line 7431, Value Line 7432 FromParam=rateMod | prices 4 (3 at $0 total) | 4 of 4 |
| `BCEGEQFactor` | 3 | SC | CW, 1, 13 | prices 3 | 3 of 3 |
| `HeightTerrGroup` | 3 | VT | CW, 22 | prices 3 | 3 of 3 |
| `LeaseholdInterestAnnuityConstant` | 2 | CW | CW, 10.5% | prices 2 (2 at $0 total) | 2 of 2 |
| `BCEGFactor` | 2 | OR | CW, Inland, 1 | prices 2 | 2 of 2 |
| `LossAssessmentRate` | 2 | CW | CW, , Special | prices 2 (1 at $0 total) | 2 of 2 |
| `IncreasedCostOfLossPercentConverted` | 1 | CW | CW, 25% | prices 1 | 1 of 1 |
| `UtilityServicesTimeElementWaitingPeriodFactor` | 1 | CW | CW, 36 hours | prices 1 (1 at $0 total) | 1 of 1 |
| `TerrorismTerritoryTier` | 1 | OR | CW, Lane County | prices 1 | 1 of 1 |
| `IRPMConversion` | 1 | CW | CW, (Constant Line 258, Value Line 259 FromParam=pctText) | prices 1 | 1 of 1 |
| `EQPercentageDeductibleFactor` | 1 | TX | CW, 2, A1, 7% | prices 1 | 1 of 1 |
| `WatercraftExclBuybackFactor` | 1 | CW | CW, Not Applicable | prices 1 | 1 of 1 |
| `VacancyPermitFactors` | 1 | KS | CW, Standard Property Policy, Earthquake (Constant Line 2251 | prices 1 | 1 of 1 |
| `EQSubLimitDeductibleTierCWTable` | 1 | VT | CW, Y (Constant Line 24847, Constant Line 24848) | prices 1 | 1 of 1 |
| `ManufacturersConsequentialLossAssumptionFactor` | 1 | CW | CW, Personal Property | prices 1 | 1 of 1 |
| `PerilExclusionIndicatorBasicAndSpecialStatCode` | 1 | AR | CW, No, No, Yes, No | prices 1 | 1 of 1 |

Cases (request files) per table are in the JSON; e.g. `EarthquakeDeductibleTier` and `BuildingHeightFactor` come from chunk 12's ISO fixtures (F-numbers) and chunk 10 / 16 probes.

## Recorded refusals that cannot be re-sent (20)

* **17** whose request file was later **overwritten by the corrected re-send** (refusal at 10:28, request and response at 10:30 the same day): chunk 12's drone U0–U8 (`WindstormOrHailDeductibleAsNumber`, keys CW + blank: the contents' building deductible), OI-108's CA / MO (`BCEGFactor` CW Inland 1), GA (`EarthquakeDeductibleTier` CW 22), NC (`GeographicWindHazardLevel` NC Burke). The recorded text is the evidence; each names a countrywide-keyed lookup with no row, the same shape as the live ones, **not re-verified** (the refused requests are gone).
* **3** with no request on file: FL chunks 6 and 7 (`SpecialClassDescriptionConvertedOption`), OR chunk 8 contents (`WindstormOrHailDeductibleAsNumber`, reproduced by chunk 27's contents cases above).

## The other refusals

| Kind | Cases | Ours | Note |
|---|---|---|---|
| `Convert` of a blank string to a number | 1 (chunk 21 Z11) | prices | OI-117; not a lookup, a separate rule |
| A parameter read before it is bound (`maxLimit`) | 4 (OI-119 P1 P2, chunk 22 U1 E2) | **refuses too** | ISO and ours agree (OI-119, closed) |
| Payload format (the request view: a field sent as text where ISO wants a number) | 17 (chunk 12 Ordinance K / C / V, chunk 13 RC-3) | prices | a payload defect, not an engine question; each rated once re-sent correctly |

## What ISO tolerates (1,689 rated requests)

* **0** `SingleResult` misses in ours. **672,950** `FirstResult` misses across 301 tables: the designed fall-throughs (a state row tried first, then countrywide).
* Ours raised on 4 of the 1,689 (VA 2021, AK, MA, VA old-edition probes): OI-114's `<rul:Null/>`, not a lookup.

## The exception: Vermont's empty earthquake tier (C19-17 E7)

ISO refused on `EQSubLimitDeductibleTierCWTable` (keys CW, Y). Vermont files that table **with no rows**; our engine treats an empty state table as absent and reads countrywide's rows (chunk 18, 2026-09-28), so it finds a row and never misses. ISO evidently reads the empty Vermont table and fails. This is the open "empty state table: countrywide or nothing?" question (memory: table resolution), which C28-03 must settle alongside the `SingleResult` rule.

## C28-03: the rule, tested against its competitors (2026-10-02)

Scripts: `245_` (the two halves above), `246_chunk28_c28-03_empty_tables.py` (`--live`: 4 probes sent; `--scan`: 1,690
rated requests), and the lookup-layout census below. Analysis only; no engine change.

**Plain English.** Our candidate, "ISO refuses when a must-find-one lookup finds nothing", survives every test we could
build, and every competing explanation is ruled out or turns out to be the same rule. The only loose end is what an
**empty** state table means, and there ISO is not consistent across tables.

### The main rule: a `SingleResult` lookup with no row refuses the policy

| Competing rule | What it predicts that differs | Evidence | Verdict |
|---|---|---|---|
| **R1. Any `SingleResult` no-row refuses** | — | 65 of 66 live refusals are exactly this; 0 such misses in 1,690 rated requests | **holds** |
| R2. Any no-row lookup refuses, whatever its mode | the rated requests would contain no misses at all | 672,950 `FirstResult` misses in the 1,690 rated requests | **refuted** |
| R3. Refuse only when the missing value feeds a premium (arithmetic) | stat-code lookups never refuse | ISO refused on `TotalRatingModicationStatCode` and `PerilExclusionIndicatorBasicAndSpecialStatCode`, each writing only a text stat code | **refuted** |
| R4. Refuse when the *last* lookup tried misses, whatever its mode | a last-position `FirstResult` miss refuses | In the 51 in-force packages every `FirstResult` lookup (13,530) has a fallback after it, and every `SingleResult` (8,520) is last or alone: **R4 and R1 pick the same lookups**, no probe can separate them | **equivalent to R1** |
| R5. A `SingleResult` miss with a fallback **after** it uses the fallback | refusal skipped at those sites | 11 such sites in CW 2026; none can be made to miss from an input (constant keys, or a band covering every value) | **not reachable; moot** |

### The open half: an empty state table

Our engine treats a state table filed with a header and no rows as not filed and reads countrywide's rows (since
2026-09-28). ISO does not do one thing:

| Table (empty in the state) | Its lookup's keys | ISO | Evidence |
|---|---|---|---|
| VT `VacancyPermitFactors` | CW + submitted values | **uses countrywide's rows** | C18-16, **re-sent today: rated** |
| NY `OffPremEndtsModifyingCovdCOLFactor` | CW + a submitted value | **uses countrywide's rows** (1.02) | chunk 25 O-NY, rated, every premium equal (found by `--scan`) |
| MA / TN / VT `EQSubLimitDeductibleTierCWTable` | **all constants** ("CW", "Y") | **refuses** | `246_ --live` Q-MA, Q-TN, Q-VT, today |

Ruled out: "the state's empty table counts only when its **definition** differs from countrywide's" (NY's off-premises
definition differs and ISO still fell back). Consistent with all five data points, **not yet tested**: *a lookup whose keys
are all constants is settled against the state's own table, empty or not*. Every other all-constant empty table we tried
is not reached by our builders (FL `SecondaryLocationDependenciesFactor`: FL rewrites the rule; KS / NY / VT
`StdPropPolGroupIFactor`: the lookup is never called; NY sign symbol: NY rewrites it). The remaining all-constant candidates
are NY's (BCEG stat code on a special class, fungus rates, mold stat code, sub-standard rating codes). **Proposal input:**
keep the fallback for data-keyed lookups (2 of 2), and treat the earthquake stub as ISO does (3 of 3); whether to
generalise to every all-constant lookup is a choice to make with the evidence above, not a fact.
