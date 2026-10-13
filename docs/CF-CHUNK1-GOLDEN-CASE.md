# Property chunk 1 — the golden case

**Written 2026-09-17.** The target chunk 1 is built against: Building, Basic Group I, class-rated,
scheduled. Selected and resolved from the ERC corpus before any code exists, so the foundation is
built toward a case we know it has to rate rather than a guess at one.

**Still not an authorization to build.** This is the target.

Companion documents: [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) (the chunk sequence
and the eight-point gate), [`CF-CHUNK0-BUILD-SPEC.md`](CF-CHUNK0-BUILD-SPEC.md) (the foundation).

Every value below was read from the corpus for this document. Nothing is carried over from the
Excel-rater tracing, which is tertiary evidence and was not consulted for any number here.

---

## 1 · The state: Oregon

Chosen by elimination over all 47 rating jurisdictions, not by sampling.

`BasicGroupIRate` is **header-only at countrywide in every edition from 20191201 to 20260601** — 0
data rows, confirmed across all eight edition folders, not just the current one. So chunk 1's very
first lookup already requires a state package. The state choice is therefore load-bearing, and the
disqualifications matter:

| Excluded | Why |
|---|---|
| HI, ID, LA, MS, WA | Absent from the CF corpus outright |
| PR | Out of scope — no RAaS entitlement, never compared |
| AK, CA | No `BasicGroupIRate` at all — `District I`/`District II` two-table split. AK derives the district from City, CA has the agent pick it. Confirmed `ABSENT` in both packages |
| FL | Files neither BGII table; carries a filed-but-unreachable 70% coinsurance row |
| NC | Files its own 12-code `ProtectionClassFactor` scale against CW's 28 |
| CT | Files a genuinely deeper multi-residential credit (0.5 vs CW 0.7) |
| MA, ME | Multi-residential credit filed as a no-op via a restricted domain table |
| NY, GA, KS | File the older 1,308-row base-rate shape rather than the current 1,368 |
| NV, PA, TX, UT | File their own `DeductibleFactor` shapes |

Of what survives, Oregon files the **fewest tables of any candidate** — 43 rate tables, 39 with
rows, against 46–63 for AZ, CO, DE, KY, MT, OK, SC, SD, TN, VA. Fewest state overrides means the
most countrywide fall-through, which is what chunk 1 is supposed to prove. Oregon also has the
**simplest territory table in the corpus** — two rows.

**One package, unambiguous as-of resolution.** `CF OR 20260601 V01` is the only Oregon package in
the current edition folder and the latest effective on or before today; every other Oregon package
sits in an older edition folder.

| | |
|---|---|
| Package identity (from the XSD `targetNamespace`, never the folder) | `CF_OR_20260601_V01` |
| Declared parent (from the `xs:import`) | `CF_CW_20260601_V01` |
| Folder on disk | `CF OR 20260601 V01` over `CFCW20260601V01` |

**Note the folder names disagree with the namespaces in both directions** — spaces in one, no
separators in the other. This is exactly the condition `gl_engine/erc/discovery.py` refuses to trust
a directory name for, and chunk 0 inherits that rule.

---

## 2 · Case A — the primary golden case

A single scheduled, class-rated Building. Every no-op term is set to its no-op deliberately, so the
chain is the shortest one that still exercises every shared mechanism.

### Inputs

> **Corrected 2026-09-17 against the rules that set each field.** Five of these were first written
> as the *derived* field rather than the input ISO actually reads, and four of the five fail
> silently — the rating completes and returns a plausible number, or zero, with no error. Each is
> corrected below with the rule that governs it. The live submission is
> `scripts/cf/01_golden_case.py`.

| Field | Value | Note |
|---|---|---|
| `State/Code` | `OR` | Seeded by Oregon's own `Default` block, not supplied |
| `RatingType` | `Class` | Gate on step 1; Specific/Tentative is confirmed unbuilt project-wide |
| **`ClassCode`** | `0951` | **Not `ClassCodeToUse`** — `SetClassCodeToUse` is a straight `Copy` from `ClassCode`, so supplying the derived field is overwritten by a blank source, the base-rate gate fails, and the premium is **zero with no error** |
| **`ConstructionType`** | `Frame` | **Not `ConstructionCode`** — the code is looked up from the type's text (`ConstructionCode.RateTable.csv`: Frame 1 … Fire Resistive 6). So "construction code 1" is a Frame building |
| `CovType` | `Building` | Selects premium Branch A |
| **`BasicGroupIRatingTerr`** | `Portland` | A submission input, **not derived from City**. The City→territory domain table is a dropdown constraint |
| **`ProtectClass`**, on the **Location** | `3` | **Not `ProtectionClass` on the structure** — `SetProtectionClassFactor` reads `../../ProtectClass`. Set in the wrong place the factor stays `1.0` and the premium is wrong by 4% rather than failing |
| `Coinsurance` | `90%` | 80% resolves to 1.000 and would hide a failed lookup |
| `Limit` | `100,000` | |
| `FullBldgValue` | `100,000` | Not rate-affecting on this branch; silences one ISO validation message |
| **`CauseOfLoss`** | `Basic Group I` | **Not `CauseOfLossToUse`** — that is `Copy`'d from `CauseOfLoss` when not blanketed. Blank ⇒ `CoverageOnPolicyIndicator = 0` ⇒ premium zero |
| `Deductible` | `1,000` | Filed with a comma. Not `250`, which routes to a different table |
| `LossCostMultiplier` | `1.0` | Company input, not filed |
| `IncludedInBlkt` | `No` | Blanket is chunk 9 |
| `IRPMFactor` (policy), `PackageModFactor`, `MultiPremiumAndDispersionCreditFactor` | `1.0` | Schedule inputs, not filed tables |
| ~~`TotAmtInsurance`~~ | — | **Derived, not supplied.** `SetTotAmtInsurance` sums `StructureLimitToUse + OccupancyTotAmtInsuranceSum + SpecialClassRiskTotAmtInsurance`. See case B |
| Vacancy, substandard condition, sprinkler leakage, vandalism exclusion, roof-surfacing limitation, deductible-by-location endorsement, cyber exclusion, Standard Property Policy, multi-residential credit | none / not elected | Each resolves to its no-op (`0.0` addend or `1.0` factor) |

### The chain, with every value traced

Rules from `CommercialPropertyStructureRules.Rule.xml` in `CFCW20260601V01`; line numbers are that
file's.

| Step | Rule | Table row | Value |
|---|---|---|---|
| 1 · Base rate | `SetBasicGroupIBaseRate` (7545) | `BasicGroupIRate` **[OR]** `"OR","0951",1,"Not Applicable","Building"` | **0.498** |
| 2 · Territory | `LookupRatingTerritoryGroupIFactor` | `RatingTerritoryGroupIFactor` **[OR]** `"OR","Portland"` | **0.499** |
| 2 · Protection class | via `SetBasicGroupIRate` | `ProtectionClassFactor` **[CW]** `"CW","3",1` | **0.96** |
| 2 · Rate | `SetBasicGroupIRate` (7599) | — | **0.239** |
| 3 · COL adjustment | `SetBasicGroupICauseOfLossAdjustment` (7698) | all three factors no-op | **0.239** |
| 4 · Coinsurance | `SetCoinsuranceFactor` (7717) | `CoinsuranceFactor` **[CW]** `"CW","90%"` | **0.95** |
| 4 · LOI | `SetBasicGroupILOIFactor` (7907) | `BasicGroupILOIFactorBldg` **[CW]** `"CW",100000,125000,1,1.172,1.128` | **1.172** |
| 4 · Adjusted rate | `SetAdjustedBasicGroupIRate` (8104) | — | **0.266** |
| 5 · Deductible | `SetDeductibleFactorBasicGroupI` (8126) | `DeductibleFactor` **[OR]** `"OR","1,000",50000,175000,"Basic Group I"` | **0.98** |
| 5 · Final rate | `SetFinalBasicGroupIRate` (8234) | — | **0.261** |
| 6 · Cyber ×2 | `SetCyberIncidentExclusionFactorBGI` (`CommercialPropertyRules` 2210) | no exclusion record → else-branch constant | **1.0**, **1.0** |
| 7 · Premium | Branch A, `...BasicGroupICoverageRules` line 111 | — | **$261** |

### The arithmetic, and why the rounding is not obvious

`rul:Product` carries `DecimalPlaces` **on every level of a nested product**, so rounding happens at
each level — not once at the end, and not after each individual multiplication. Read from the rule's
actual nesting, because the three readings give different answers and only one is right:

```
Step 2   inner  round(0.498 × 1.0, 3)                  = 0.498     base × LCM
         sum    0.498 + 0.0 + 0.0                      = 0.498     + substandard + vacancy
         mid    round(0.498 × 0.499 × 0.96, 3)         = 0.239     ONE product, three factors
         outer  round(0.239 × 1.0, 3)                  = 0.239     × roof-surfacing
Step 3          round(0.239 − 0.0, 3) × 1.0 × 1.0 × 1.0 = 0.239
Step 4   inner  round(0.239 × 0.95, 3)                 = 0.227
         outer  round(0.227 × 1.172, 3)                = 0.266
Step 5   inner  round(0.266 × 1.0, 3)                  = 0.266     × deductible-by-location
         outer  round(0.266 × 0.98 × 1.0, 3)           = 0.261     × deductible × multi-res
Step 7          round(1.0 × 1.0 × 1.0 × 0.261 × (100,000 / 100), 0) = 261
                261 × 1.0 × 1.0                        = 261
```

**Expected premium: $261.**

The middle product of step 2 is the one that matters. Rounding territory and protection class
*together* gives `0.239`; rounding them *sequentially* gives `0.238`, and that difference survives
all the way to the premium. An engine that gets the nesting wrong produces a plausible number, not
a crash — which is the whole reason this case is resolved before the code is written.

---

## 3 · Case B — the location-total trap, isolated

Identical to Case A but with **$100,000 of contents at the same structure**, `Limit` unchanged at
100,000, so ISO's own `SetTotAmtInsurance` totals the location to 200,000. Contents are not rated —
this is still chunk 1; they exist only to move the key.

> **Corrected 2026-09-17.** This case first said "set `TotAmtInsurance` = 200,000", which cannot be
> done: the field is derived. Driving it with real contents is the honest version of the test
> anyway — it proves ISO's own summation feeds the deductible key, not just that the lookup reads
> whatever it is handed. Two further inputs are needed to make the contents count:
> `CommercialPropertyPersonalProperty` must carry `IncludedInBlkt = "No"` or `SetLimitToUse` never
> fires and the contents total zero.

Verified directly in the rule rather than assumed: `SetDeductibleFactorBasicGroupI` passes
`TotAmtInsurance` as the `limit` argument to `LookupDeductibleFactor`, while the LOI branch passes
the coverage's own `Limit`. The two keys are different datadefs and this case makes them different
*values*.

| | Case A | Case B |
|---|---|---|
| LOI key (`Limit`) | 100,000 → **1.172** | 100,000 → **1.172** (unchanged) |
| Deductible key (`TotAmtInsurance`) | 100,000 → `(50000, 175000]` → **0.98** | 200,000 → `(175000, 500000]` → **0.99** |
| Final rate | 0.261 | **0.263** |
| **Premium** | **$261** | **$263** |

An engine that keys the deductible off the Building limit returns $261 for both. One number apart,
one mechanism isolated.

---

## 4 · Case C — interpolation

Identical to Case A but `Limit` = `TotAmtInsurance` = **112,500** — the exact midpoint of the LOI
band `[100000, 125000)`.

`BasicGroupILOIFactorBldgDef.RateTableDef.xml` declares `Limit` as a `Range` key and `Factor` as a
`Range` value with `InterpolateMode="Linear"`. **The interpolation lives in the table definition,
not in any rule** — an engine that treats the table as an exact-key lookup will either miss or
return the band's lower factor, and both failures look like working code.

```
1.172 + (112,500 − 100,000) / (125,000 − 100,000) × (1.128 − 1.172) = 1.150
round(0.239 × 0.95, 3) = 0.227  →  round(0.227 × 1.150, 3) = 0.261
round(0.261 × 0.98, 3) = 0.256  →  0.256 × 1,125 = 288
```

**Expected premium: $288.** Reading the band's lower factor instead of interpolating gives $293.

---

## 5 · What each case catches

| Failure | Caught by |
|---|---|
| Interpreter never learns `rul:Product` nesting semantics | A — wrong at step 2, propagates |
| `rul:Null` unimplemented | A — 26 of its 35 corpus uses are in this file |
| Header-only CW table silently resolving to zero | A — `BasicGroupIRate` at CW is header-only; a zero base rate yields $0 |
| State layer never consulted | A — CW has no base-rate row at all, so it cannot rate |
| State layer consulted but CW wins | A — deductible 0.96 (CW) vs 0.98 (OR) → $255 not $261 |
| Territory resolved as ZIP, or not derived from City | A — territory factor 0.499 vs a default 1.0 |
| Deductible keyed off the Building limit | **B** |
| Range-key interpolation not implemented | **C** |
| Premium rounded once at the end rather than per product level | A, C |

---

## 6 · What these three cases deliberately do not test

Stated so nobody reads a green gate as more than it is:

- **Every no-op term is set to its no-op.** Substandard condition, vacancy, sprinkler leakage,
  vandalism, Standard Property Policy, roof surfacing, multi-residential credit and both cyber
  factors are all `0.0` or `1.0` here. Gate item 4 — *every `0` tested against its consuming
  branch* — is **not** satisfied by these three cases and needs its own set.
- **Two zeros that collapse the premium are live in this chain and untested:** `SetBasicGroupILOIFactor`
  assigns `BasicGroupILOIFactor = 0.0` outright when `Limit = 0` or `ConstructionCode = 0`, and both
  cyber factors default to `0.0` if their rule never runs, because the premium reads them through
  `FirstValue ... FromConstant="0.0"`.
- **Only one state.** Gate item 3 — every state enumerated, "n of N" — is a separate exercise. These
  cases prove the mechanism; they do not prove the corpus.
- **One class code, one construction code, one territory, one deductible.**
- **No Legal Liability, no blanket, no Specific/Tentative rating** — chunks 8, 9, and confirmed
  unbuilt respectively.
- **No CFRater comparison.** Tertiary, and it carries logged divergences that would need
  adjudicating before a mismatch meant anything. Not a gate condition.

---

## 6a · Result

**All three rate, and every intermediate matches the hand-derivation exactly.** Run with
`python scripts/cf/01_golden_case.py`; the gate is written up in
[`CF-CHUNK1-GATE.md`](CF-CHUNK1-GATE.md).

| | A | B | C |
|---|---|---|---|
| `TotAmtInsurance` (derived) | 100,000 | **200,000** | 112,500 |
| Base rate `[OR]` | 0.498 | 0.498 | 0.498 |
| Rate — × territory × protection class | **0.239** | 0.239 | 0.239 |
| Coinsurance `[CW]` | 0.95 | 0.95 | 0.95 |
| LOI `[CW]` | 1.172 | 1.172 | **1.150** interpolated |
| Adjusted rate | 0.266 | 0.266 | 0.261 |
| Deductible `[OR]` | 0.98 | **0.99** | 0.98 |
| Final rate | 0.261 | 0.263 | 0.256 |
| **Premium** | **$261** | **$263** | **$288** |

The step-2 rounding analysis holds: 0.239, not the 0.238 a sequential reading gives.

---

## 7 · Open items, to close during the build

1. **Rounding mode is unspecified.** None of the three cases lands on a tie, so all three pass under
   half-up or banker's — they cannot distinguish the two. The engine's mode must be set from ISO's
   contract, not inferred from these cases passing.
2. ~~**`LookupBasicGroupILOIFactor`'s key is threaded through a parameter.**~~ **Closed.** Case B
   settles it: the location total moves to 200,000 while the LOI factor stays 1.172, so the LOI key
   is the coverage's own `Limit` and not the total. Case C confirms the value.
3. **`DomainBasicGroupIRatingTerrOregon.DomainTable.csv` has zero rows** while
   `DomainBasicGroupIRatingTerritoryOR.DomainTable.csv` has three and is the one in force. A
   header-only sibling under a near-identical name is exactly what chunk 0's detector exists for, and
   exactly the shape of this project's "check all tables before calling a factor blank" rule.
4. ~~**`CyberIncidentExclusionCOLExcptnsFactorBGI`'s else-branch default.**~~ **Closed.** Both cyber
   factors resolve to `1.0` with no exclusion record; had either defaulted to the `0.0` its
   `FirstValue` declares, all three premiums would be zero.

5. **New, and open: three ISO validation messages fire on every case.** *"CP 03 20 must be attached
   when fixed dollar amount deductible for each location are different…"*, *"Either CP 10 75 or
   CP 10 76 must be attached"*, and on case B *"Full Value cannot be lower than the Limit"*. The
   premium is correct regardless — these are ISO's own form-attachment validations, and the golden
   case does not schedule forms. **A message-clean submission is a different exercise** and worth
   doing before anything is compared against ISO's live service, because RAaS returns these in
   `RatingMessages` and a diff that ignores them is comparing half the response.
