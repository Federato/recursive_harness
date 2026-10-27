# Property chunk 10, task C10-01 — the golden case

**Earthquake, Building, Basic Group I, one structure, the plain
percentage-deductible Endorsement.** Derived 2026-09-22. The first
Earthquake submission rated end to end anywhere in this project.

**Every number below was read off the filed rows and worked out by hand
before the engine was run — and the engine matched exactly.** Unlike
chunk 9's own golden case (a real interpreter gap), this task finds no
engine gap: nothing here needed a fix, and nothing here is patched.

Script: [`scripts/cf/85_chunk10_golden_case.py`](../scripts/cf/85_chunk10_golden_case.py).

---

## 1 · The case

**Chunk 1's own risk, unmodified** — Oregon, class code `0951`, Frame,
Portland territory, protection class `3`, Basic Group I, Coinsurance `90%`,
Deductible `1,000`, Limit `100,000` (`CF-CHUNK1-GOLDEN-CASE.md` case A,
premium `$261`) — with an EQ election added on top of the SAME structure.
No blanket, no sub-limit form, no flat-dollar deductible, no
sprinkler-leakage-only election: the shortest EQ chain that still exercises
the plain percentage-deductible Endorsement chunk 10's opening census (finding
2) identified as the real engine.

| Field | Level | Value |
|---|---|---|
| `EQCauseOfLossForm` | Location | `Earthquake Form (CP 10 40)` |
| `EQTerr` | Location | `1` |
| `EQDeductibleTier` | Location | `1` |
| `EQCovIndicator` | Structure | `Yes, Not Included in Blanket` |
| `EQClass` | Structure | `A1` |
| `EQCoinsurance` | Structure | `90%` |
| `EQDeductible` | Structure | `10%` |
| `EQSprinklerLeakageOnly` | Structure | `Not Applicable` |
| `BCEG` | Structure | `1` |
| `SprinklerSystem` | Structure | `None` |
| `EQSubLimitBlktIndicator` | Property | `No` (domain hygiene, not load-bearing) |

---

## 2 · Structural facts confirmed against the rule XML before running

Per this project's standing rule, the census document is a lead, not ground
truth. All six of the below were read directly from
`CommercialPropertyStructureRules.Rule.xml`,
`CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementRules.Rule.xml`,
and the Domain/Rate Tables — none were carried over from the census script's
own printed summary.

### A · `EQCauseOfLossForm` selects WHICH of four Endorsement files attaches — not a free-text label

`AttachFormCommercialPropertyEarthquakeAndVolcanicEruptionEndorsement`
(`CommercialPropertyStructureRules.Rule.xml`) gates on
`../../EQCauseOfLossForm = "Earthquake Form (CP 10 40)"` specifically. The
three sibling `AttachForm*` rules gate on the other three domain values:

| `EQCauseOfLossForm` | Attaches |
|---|---|
| `Earthquake Form (CP 10 40)` | `CommercialPropertyEarthquakeAndVolcanicEruptionEndorsement` — the plain percentage-deductible form, this case |
| `Earthquake Form (CP 10 28)` | `CommercialPropertyEarthquakeAndVolcanicEruptionCoverageWithFlatDollarDeductibleBldg` |
| `Earthquake Sub-Limit Form (CP 10 45)` | `CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementSubLimitForm` |
| `Earthquake Sub-Limit Form (CP 10 29)` | `CommercialPropertyEarthquakeAndVolcanicEruptionCoverageSubLimitFormWithFlatDollarDeductibleBldg` |

Each `AttachForm*` rule's `Else` branch **removes** the record if it exists
— the same destructive-gate shape chunk 9 found for `BlktRated`. Picking
the wrong `EQCauseOfLossForm` string silently attaches (or fails to attach)
a different form entirely, not a labeling difference.

### B · `EQCovIndicator`'s domain-valid value for this exact case is confirmed, not assumed from the ISO fixture sample

`DomainEQCovIndicatorBldg.DomainTable.csv`, filtered to
`CovTypeBldg="Building"`, `EQCauseOfLossForm="Earthquake Form (CP 10 40)"`,
`EQSubLimitBlktIndicator="No"`, `BlktRated="No"` yields exactly two rows:
`"Yes, Not Included in Blanket"` and `"No Coverage"`. The census's own
sample of 69 real ISO STC payloads (all electing
`"Yes, Not Included in Blanket"`) is corroborated here directly against the
domain table for this specific combination, not just observed as a pattern.

### C · `EQCoinsuranceFactor` shares the ORDINARY `CoinsuranceFactor` table — not a distinct EQ-only rate

`LookupEQCoinsuranceFactor`'s `Lookup` carries
`MatrixDef="CoinsuranceFactorDef" MatrixFromConstant="CoinsuranceFactor"` —
the exact same `MatrixDef` chunk 1's own `SetCoinsuranceFactor` reads. `EQCoinsurance="90%"`
resolves through the `[CW]` fallback to `0.95`, the identical row chunk 1
already proved (`CF-CHUNK1-GOLDEN-CASE.md` §2, step 4). This narrows the
opening census's finding 4 ("EQ shares zero multipliers with the ordinary
chain"): that finding is about `IRPMFactor`/`PackageModFactor`/
`MultiPremiumAndDispersionCreditFactor`, confirmed absent from the
Endorsement's own `SetPremium` by direct read — but `EQCoinsuranceFactor` is
a genuine, table-level share with the ordinary chain, hiding behind an
EQ-prefixed field and rule name. A same-table share the field-name prefix
disguises, not a wholly separate 57-name population in every case.

### D · Three no-op traps, none of them named by the census, all found only by reading each `Set*` rule's own `Else`/`Otherwise` branch

1. **`BCEGEQFactor` defaults to `0.0`, not `1.0`, when `BCEG` is blank.**
   `SetBCEGEQFactor` gates its `LookupBCEGEarthquakeFactor` call on
   `BCEG != ""`; the `Else` is a bare `Constant 0.0`. `SetEQRate` multiplies
   `BCEGEQFactor` into `EQRate` unconditionally — an unset `BCEG` zeroes the
   entire EQ chain silently, no error, no zero-quantity message. The same
   shape as chunk 1's own flagged-but-untested "two zeros that collapse the
   premium" (LOI factor at `Limit=0`, both cyber factors at their `0.0`
   `FirstValue` fallback) — a third one, EQ-specific, confirmed here by
   reading the rule rather than assumed.
   `BCEG="1"` resolves through `BCEGEarthquakeFactor[OR]("1")` = `1.0`, a
   genuine no-op — a DIFFERENT table from the near-namesake `BCEGEQFactor`
   (header-only at CW, unfiled at OR), the census's own finding 5
   shared-name-adjacent trap, confirmed load-bearing on this exact case: had
   the wrong table been read, the same input would have produced no row at
   all rather than a wrong one.
2. **`EQSprinklerLeakageOnly` blank satisfies neither of
   `SetEQDeductibleFactor`'s two `When` branches, and the outer `Choose` has
   no `Otherwise`.** A blank value leaves `EQDeductibleFactor` `IsNull`
   forever, which starves `SetFinalEQRate`'s product of its `0.0`
   `FromConstant` fallback — premium zero, no message. The fix is not a
   convenient default: `DomainEQSprinklerLeakageOnlyBuilding` confirms that
   for `EQCovIndicatorBldg="Yes, Not Included in Blanket"` and
   `SprinklerSystemBldg="None"`, the ONLY filed `DataValue` is
   `"Not Applicable"` — the domain-correct value and the value that avoids
   the starved factor are the same string.
3. **`SprinklerSystem` blank is read as "has a sprinkler," not "no
   sprinkler."** `SetEQSprinkleredRiskFactor` guards its lookup on
   `NotEqual(SprinklerSystem, "None")`. An unset field satisfies
   `NotEqual(blank, "None")` — blank is not literally the string `"None"` —
   so the rule takes the LOOKUP branch, not its own `1.0` no-op `Else`. The
   table (`CW`, keyed on the hardcoded constant `"Y"` regardless of the
   actual `SprinklerSystem` value) returns `1.06`. Leaving the field unset
   does not silently no-op; it silently adds a factor the submission never
   asked for. `SprinklerSystem="None"` (a valid `DomainSprinklerSystemBldg`
   row for `RatingType="Class"`) is required to reach the genuine `1.0`.

None of these three would raise an exception, a validation message, or an
obviously-wrong number — each produces a plausible, silently incorrect
result, which is exactly why they are worth naming explicitly rather than
discovering by trial and error.

### E · What no-ops correctly with nothing extra supplied

Confirmed by reading each rule's own `Else`/`Otherwise` branch, not assumed
from the field name: `EQSubLimitPercent` (`0`, no sub-limit table present),
`PctOfMasonryVeneerEQFactor`, `BuildersRiskEQFactor`, `BldgHeightFactor`
(gated on `NumStories`, left unset), `SoftStoryModificationFactor`,
`LimitationsOnCovForRoofSurfacingACVFactor`, `EQDeductibleByLocationFactor`,
and both `CyberIncidentExclusionFactorEQ` /
`CyberIncidentExclusionCOLExcptnsFactorEQ` (Property-level, same
"defaults to 1.0 absent an exclusion record" mechanism chunk 1 already
proved for the ordinary chain's own cyber factors, confirmed here to be a
literal re-run of the identical pattern one level up the tree).

---

## 3 · The chain, hand-traced before running

Rules from `CommercialPropertyStructureRules.Rule.xml` (`SetEQRatesAndFactors`
and its callees) and
`CommercialPropertyEarthquakeAndVolcanicEruptionEndorsementRules.Rule.xml`
(`SetPremium`).

| Step | Rule | Table row | Value |
|---|---|---|---|
| 1 · Base rate (loss cost) | `SetEQBaseRate` → `LookupEQLossCostBldg` | `EQLossCostBldg` **[OR]** `"OR","A1","1"` | **0.009** |
| 2 · EQ rate | `SetEQRate` | × LossCostMultiplier(1.0) × 6 no-op factors (D above) | **0.009** |
| 3 · COL adjustment | `SetEQCauseOfLossAdjustment` | × `EQSprinklerLeakageOnlyBldgFactor`(1.0 no-op) | **0.009** |
| 4 · Coinsurance | `SetEQCoinsuranceFactor` → `LookupEQCoinsuranceFactor` | `CoinsuranceFactor` **[CW]** `"CW","90%"` (shared table, C above) | **0.95** |
| 4 · Adjusted rate | `SetAdjustedEQRate` | round(0.009 × 0.95, 3) | **0.009** |
| 5 · Deductible-by-location | `SetEQDeductibleByLocationFactor` | no-op (`EQSprinklerLeakageOnly != "Yes"`) | **1.0** |
| 5 · Class-to-use | `SetEQClassToUse` → `LookupEQClassToUse` | `EQClassToUse` **[CW]** `"CW","A1","A1"` | **A1** |
| 5 · Deductible factor | `SetEQDeductibleFactor` → `LookupEQPercentageDeductibleFactor` | `EQPercentageDeductibleFactor` **[OR]** `"OR",1,"A1","10%"` | **0.68** |
| 5 · Final rate | `SetFinalEQRate` | round(round(0.009 × 1.0, 3) × 0.68, 3) | **0.006** |
| 6 · Cyber ×2 | `SetCyberIncidentExclusionFactorEQ`/`...COLExcptnsFactorEQ` (`CommercialPropertyRules`) | no exclusion record → else-branch constant | **1.0**, **1.0** |
| 7 · Premium | Endorsement `SetPremium`, Building/Improvements/Condo/BuildersRisk branch | round(round(round(0.006 × 100,000/100, 0) × 1.0, 0) × 1.0, 0) | **$6** |

### The rounding, and why it is unambiguous here

Every intermediate rounding step in this chain lands clear of a tie —
`0.00855 → 0.009` (the digit after the cutoff is `5` followed by more
non-zero digits, so it is strictly above the midpoint `0.0085`, not
exactly on it) and `0.00612 → 0.006` round the same way under half-up or
banker's rounding. Unlike chunk 1's own case, which flagged rounding mode
as an open item precisely because none of its three cases landed on a tie
either, this case does not close that item — it is simply not the case that
settles it.

**Expected EQ Premium: $6. Expected ordinary Basic Group I premium,
unmoved: $261.**

---

## 4 · What actually ran

| | Predicted | Engine |
|---|---|---|
| `EQBaseRate` | 0.009 | **0.009** |
| `EQRate` | 0.009 | **0.009** |
| `EQCauseOfLossAdjustment` | 0.009 | **0.009** |
| `EQCoinsuranceFactor` | 0.95 | **0.95** |
| `AdjustedEQRate` | 0.009 | **0.009** |
| `EQClassToUse` | A1 | **A1** |
| `EQDeductibleFactor` | 0.68 | **0.68** |
| `FinalEQRate` | 0.006 | **0.006** |
| Endorsement `Premium` | $6 | **$6** |
| Ordinary BGI `Premium` (regression) | $261 | **$261** |

**Every value matches exactly.** No disagreement, no root-cause section
needed — stated plainly rather than manufactured, per this task's own
instructions.

Two ISO validation messages fire, both already logged as open items by
chunk 1's own gate (§7.5 there) and not new to this case: *"CP 03 20 must be
attached when fixed dollar amount deductible for each location are
different…"* and *"Either CP 10 75 or CP 10 76 must be attached"*. Neither
affects the premium; a message-clean submission remains a separate exercise
(C10-09).

---

## 5 · What this case proves about reachability

**The Earthquake engine is wired into the ordinary `Interpreter.run` entry
point, through the same `SetBlanketRatesAndFactors` sequence chunk 9 already
found runs unconditionally for every structure regardless of blanket
election** — `SetEQCauseOfLossForm`, `SetEQTerr`, `SetEQDeductibleTier`,
`SetBCEGEQFactor`, `SetEQClassToUse` and `SetEQRatesAndFactors` all fire from
inside that same misleadingly-named rule, on a structure with
`IncludedInBlkt="No"`. No separate top-level invocation, no special-casing
of the EQ path, and no interpreter change was needed to reach a nonzero,
hand-matching premium. This confirms the opening census's finding 2 (the
real engine lives in the 5 parent files, not the 97-file population) end to
end for Building specifically, and confirms finding 3 (`EQClass`/`EQTerr`
are pure submission inputs) with the added precision that `EQClass` is a
STRUCTURE-level input with no copy-down rule at all, while `EQTerr` (and
`EQDeductibleTier`, `EQCauseOfLossForm`) are LOCATION-level inputs copied
down to the structure by a plain `Copy` rule — a distinction the census's
corpus-wide `ToDataDef` grep collapsed into one finding but which matters
for where a real submission has to place each field.

---

## 6 · What this case cannot show

* **The other 4 premium groups' own EQ chains** (Contents, Business Income,
  Special Class, SC Business Income) — C10-11's job, not this one. This
  case traces Building only.
* **The flat-dollar-deductible and sub-limit variants** (`EQCauseOfLossForm`
  = CP 10 28, CP 10 45, CP 10 29) — different `AttachForm*` rules, different
  tables, C10-19's job.
* **Blanket EQ** (`EQCovIndicator="Yes, Included in Blanket"`,
  `BlktEQAvgRate`) — a third premium formula inside the same `SetPremium`
  `Choose`, untested here by design (this case is deliberately orthogonal to
  chunk 9's blanket work, per this task's own instructions).
* **Legal Liability's EQ branch** (the `SetPremium` `When` keyed on
  `CovType="Legal Liability"`, reading `LegalLiabilityFactor` and
  `LegalLiabAddlInsurableIntFactor` instead of the plain building formula)
  — C10-16's job.
* **Every `0` tested against its consuming branch** (`EQCovIndicator="No
  Coverage"`, `="Not Applicable"`, and a populated indicator with
  `EQClass`/`EQTerr` unmatched in the table) — C10-04's job. This case
  deliberately elects coverage and picks matching, filed rows throughout.
* **State enumeration** — one state only. C10-03's job.
* **The two open ISO validation messages** — not investigated for cause
  here, C10-09's job, same as chunk 1's own unresolved §7.5.
* **A message-clean submission compared against ISO RAaS** — not attempted;
  out of scope for a hand-derivation gate.

---

## 7 · Result

**Match, run 2026-09-22.** `python scripts/cf/85_chunk10_golden_case.py`
exits 0. Every intermediate and both premiums (`$6` Earthquake, `$261`
ordinary Basic Group I, unmoved) match the hand derivation exactly. No
engine gap found, no engine code touched.
