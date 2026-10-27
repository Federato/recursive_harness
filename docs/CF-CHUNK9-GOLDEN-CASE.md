# Property chunk 9, task C9-01 — the golden case

**Blanket, Building, Basic Group I, two structures sharing one `BlktIDNum`.**
Derived 2026-09-21. **The first populated blanket submission built anywhere
in this project** (census `67_chunk9_census.py` §4: zero of 924 ISO STC
payloads elect blanket either).

**Every number below was read off the filed rows and worked out by hand
before the engine was run — and the engine disagreed. The disagreement is
this task's finding.**

Script: [`scripts/cf/68_chunk9_golden_case.py`](../scripts/cf/68_chunk9_golden_case.py).

---

## 1 · The case

**Chunk 1's own risk** — Oregon, class code `0951`, Frame, Portland
territory, protection class `3`, Basic Group I, Coinsurance `90%`,
Deductible `1,000` — duplicated into **two structures at one location**,
`IncludedInBlkt="Yes"` on both, one shared `BlktIDNum`. Every rate row
through `BasicGroupICauseOfLossAdjustment` (`0.239`) and
`DeductibleFactorBasicGroupI` (`0.98` / `0.99`) is the exact row chunk 1
already proved (`CF-CHUNK1-GOLDEN-CASE.md` §2, §3) — the only new variable
is the blanket election and the averaging engine it feeds.

| | Structure A | Structure B |
|---|---|---|
| `FullBldgValue` | 100,000 | 200,000 |
| `TotAmtInsurance` (own, undisturbed by blanket) | 100,000 | 200,000 |
| `DeductibleFactorBasicGroupI` [OR] | 0.98 (chunk 1 case A) | 0.99 (chunk 1 case B) |

`CommercialPropertyBlanketRatingTable/CommercialPropertyBlanketRating[1]/
CommercialPropertyBlanketRatingDetailTable/CommercialPropertyBlanketRatingDetail[1]`:
`UnitNumber=100` (both structures' `BlktIDNum`), `Type="Building Only"`,
`TypeOfBlanketRating="Average"`, `Coinsurance="90%"`, `TotalLimit=300000`.

---

## 2 · Two facts that decide the submission's shape, confirmed against the rule XML

Per this chunk's standing rule, the census doc is a lead, not ground truth —
both of these were read directly, not carried over.

### A · `BlktRated="Yes"` on the POLICY is a THIRD gate, and it is destructive

Distinct from `IncludedInBlkt` (structure) and `MUBlktRated` (policy),
`BlktRated` gates `AttachFormBlanketRating`
(`CommercialPropertyRules.Rule.xml`, run at `ErcProcess` step
`ErcDoConditionalMandatoryLogic`, **before** any blanket rate chain runs):

```xml
<rul:Then>  <!-- BlktRated="Yes" AND MUBlktRated="No" -->
  ... create the record if missing ...
</rul:Then>
<rul:Else>
  <rul:Remove AtDataDef="CommercialPropertyBlanketRatingTable/CommercialPropertyBlanketRating"
              RemoveMultiple="true" />
</rul:Else>
```

**Without `BlktRated="Yes"`, ISO's own rule deletes the
`CommercialPropertyBlanketRating` record the submitter supplied** — this
project's `PolicyType` trap (C6-01, and again in chunk 8) for a third time,
one chunk later. Neither the census nor the task's own structural findings
named this field; it surfaced only from reading `AttachFormBlanketRating`
directly.

### B · The Detail record's `TotalFullValueAmount` is DERIVED; `TotalLimit` is not

`SetTotalFullValueAmount` (`CommercialPropertyBlanketRatingDetailRules.Rule.xml`)
sums `FullBldgValue` across every structure with `IncludedInBlkt="Yes"` and
`BlktIDNum` equal to the Detail record's own `UnitNumber` (plus the
Contents/Special-Class/Business-Income equivalents, all `0` here). Supplying
it directly would be silently overwritten — this project's
`ClassCode`/`ClassCodeToUse` trap, generalized to blanket. `TotalLimit` (which
feeds `BlktLimit`), by contrast, is never set by any rule in the
13,458-line Detail file: it is a genuine input, the company's chosen total
blanket limit of insurance.

---

## 3 · The chain, hand-traced before running

```
Structure calc (per structure, rounded to 0dp each, THEN summed):
  A = round(100,000 x 0.239 x 0.98 x LOI_A, 0)
  B = round(200,000 x 0.239 x 0.99 x LOI_B, 0)

BasicGroupIAvgRate = round( (A + B) / TotalFullValueAmount x CoinsuranceFactor(1.0) x BldrsRiskFactor(1.0), 3)

Premium(structure) = round( IRPMFactor(1.0) x MultiPremDispersion(1.0) x PackageMod(1.0)
                             x (BlktLimit/100) x (FullBldgValue/BlktTotalFullValueAmount)
                             x BlktBasicGroupIAvgRate , 0)
                     x CyberBGI(1.0) x CyberCOLExcptnsBGI(1.0)
```

`LOI_A`/`LOI_B` are `BlktBasicGroupILOIFactor` — a **blanket-specific** LOI
factor, distinct from the item's own `BasicGroupILOIFactor`, keyed off
`BlktTotalLOIToUse = round(FullBldgValue/BlktTotalFullValueAmount x BlktLimit, 0)`
and looked up in the SAME table chunk 1 used
(`BasicGroupILOIFactorBldg.RateTable.csv`, `CW`, `ConstructionCode=1`):

| Structure | `BlktTotalLOIToUse` | Band | Factor (chosen at the band's `_From` edge — no interpolation) |
|---|---|---|---|
| A | 100,000 | `[100000,125000)` | **1.172** |
| B | 200,000 | `[200000,225000)` | **1.039** |

### Hand-derived prediction

```
StructureCalc A = round(100,000 x 0.239 x 0.98 x 1.172, 0) = 27,451
StructureCalc B = round(200,000 x 0.239 x 0.99 x 1.039, 0) = 49,168
BasicGroupIAvgRate = round((27,451+49,168) / 300,000, 3)  = 0.255
Premium A = round(300,000/100 x 100,000/300,000 x 0.255, 0) = $255
Premium B = round(300,000/100 x 200,000/300,000 x 0.255, 0) = $510
```

---

## 4 · What actually ran

| | Predicted | Engine | |
|---|---|---|---|
| `Detail.TotalFullValueAmount` | 300,000 | **300,000** | matches |
| `Detail.BasicGroupIAvgRate` | 0.255 | **0.236** | **mismatch** |
| `Structure A.BlktTotalFullValueAmount` | 300,000 | **0** | **mismatch** |
| `Structure A/B.BlktBasicGroupIAvgRate` | 0.255 | **0** | **mismatch** |
| `Structure A Premium` | $255 | **$0** | **mismatch** |
| `Structure B Premium` | $510 | **$0** | **mismatch** |

**The Detail record's own aggregation is exactly right.** The averaging
engine's `SetTotalFullValueAmount` (summing across structures via
`ForEach @AtDataDef`, values only, no in-loop writes to the outer scope)
produced precisely the hand-summed `300,000`. Everything that goes wrong
does so downstream of a single mechanism.

---

## 5 · The root cause: `ForEach` does not distinguish `@AtDataDef` from `@AtInputDataDef`

`gl_engine/interp/nodes.py::_for_each`:

```python
path = el.attrib.get("AtDataDef") or el.attrib.get("AtInputDataDef")
...
for item in tree.select(path, fr.data):
    inner = fr.at(item)          # reparents BOTH reads and writes
    ...
```

`SetNonEQBlanketValues` and `SetNonEQBlanketRatesAndFactors`
(`CommercialPropertyStructureRules.Rule.xml`, both `DataDefGroup=
"CommercialPropertyStructure"`) walk
`../../../../CommercialPropertyBlanketRatingTable/.../
CommercialPropertyBlanketRatingDetail` with **`ForEach AtInputDataDef=...`**,
and their bodies write bare `ToDataDef`s — `BlktCauseOfLossValueTemp`,
`BlktTotalFullValueAmountTemp`, `BlktBasicGroupIAvgRateTemp` — meaning "the
structure this whole rule is bound to." Under this engine, those writes land
on the ITERATED Detail record instead, because `_for_each` treats
`@AtInputDataDef` exactly like `@AtDataDef`.

**Direct proof, read off the tree after the run** — the Detail record ends
up carrying four fields that belong on `CommercialPropertyStructure` and are
never declared anywhere in the DataDef under
`CommercialPropertyBlanketRatingDetail`:

```
Detail.BlktCauseOfLossValueTemp     = 'Basic Group I'   (a self-referential
                                                          no-op: Detail.CauseOfLoss
                                                          is also 'Basic Group I')
Detail.BlktTotalFullValueAmountTemp = '300000'
Detail.BlktLimitTemp                = '300000'
Detail.BlktBasicGroupIAvgRateTemp   = '0.236'
```

Meanwhile the STRUCTURE's own `BlktTotalFullValueAmount` and `BlktLimit`
never leave their pre-walk default of `0`.

### The cascade — one miswrite, two visible symptoms

1. **`BlktBasicGroupILOIFactor` falls to its `1.0` fallback.**
   `SetBlktTotalLOIToUse` requires `BlktTotalFullValueAmount > 0`; stuck at
   `0`, it sets `BlktTotalLOIToUse := 0`. `SetBlktBasicGroupILOIFactor`
   requires `BlktTotalLOIToUse > 0`; that gate also fails, so the table
   lookup never runs and the factor keeps its literal `1.0` default instead
   of the filed `1.172` / `1.039` this case was built to exercise.
   Recomputing `BasicGroupIStructureCalc` with `LOI=1.0` for both structures
   reproduces the engine's numbers exactly:
   `round(100000x0.239x0.98x1.0,0)=23,422`,
   `round(200000x0.239x0.99x1.0,0)=47,322`, sum `70,744`,
   `70,744/300,000` rounded to 3dp `= 0.236`. **The averaging engine's own
   arithmetic is right — it is being fed the wrong LOI factor because of
   the ForEach bug two rules upstream.**
2. **`SetPremium`'s blanket branch gates on
   `Convert(BlktTotalFullValueAmount) > 0.0` and its `Else` is a bare
   `Premium := 0.0`.** The copy from `Detail.TotalFullValueAmount` (which DID
   compute correctly) never reaches the structure, so this gate fails on
   both structures and `SetPremium` takes the zero branch. That is the whole
   explanation for `$0` / `$0` — not a starved formula, a starved COPY.

---

## 6 · What this proves about reachability

**Blanket rating IS wired into the ordinary `Interpreter.run` entry point —
this is itself a finding, since the census flagged the 621K-character Detail
engine as "untouched by any chunk 1–8 script" without asking whether it was
reachable.** Traced end to end: `Overall Rating.Rule.xml`'s `Default` block
→ `CommercialPropertyRules.ErcProcess` → (step `ErcSetBlanketLimit`, before
any per-structure rate) `CommercialPropertyBlanketRatingRules.
SetBlanketTotalFullValue` → `CommercialPropertyBlanketRatingDetailRules.
SetTotalFullValueAmount` (aggregates); → (step `ErcSetBlanketRatesAndFactors`)
`CommercialPropertyStructureRules.SetBlanketRatesAndFactors`, which runs the
**entire** per-structure rate chain (`SetBGIRatesAndFactors` etc. — this
rule's name is misleading; C9-08's shared-name generalization) regardless of
blanket election; → (step, ForEach) `CommercialPropertyBlanketRatingRules.
ErcProcess` → Detail's `ErcDoBlanketRating` (`SetCounters`,
`ErcSetRiskLevelAverageAndHighestRates`, `SetFinalCalculations` —
`BasicGroupIAvgRate` computed here); → (step `SetRiskLevelBlanketRates`)
copies the averaged rate back onto each structure; → (later, ForEach
locations) `CommercialPropertyStructureBuildingBasicGroupICoverageRules.
SetPremium` reads it. **Every link exists and fires, through the plain
submission-shaped entry point chunks 1–8 already used — no separate
top-level invocation is needed.** The one link that misfires is the
Structure↔Detail copy identified in §5, an existing-node bug, not a missing
wire.

---

## 7 · What this case cannot show

* **The five validation messages** (`Invalid blanket type for Blanket ID
  number entered` x2, the deductible-by-location form message x2, the
  peak-season form message) — not investigated here; C9-10/C9-12's job.
* **`BlktTypeOfBlanketRating="Highest"`**, the EQ path, or any other
  coverage form. C9-03/C9-15/C9-16/C9-17.

---

## 8 · Fixed, 2026-09-21, user-authorized

**The fix reproduces $255/$510 exactly — no second disagreement behind the
first, at least for this case.** `Frame` (`gl_engine/interp/interpreter.py`)
gained a `write_root` field, default `None` meaning "same as `data`". A
`ForEach AtInputDataDef` loop now calls `fr.at(item, keep_write_root=True)`:
reads inside the body resolve against `item` (unchanged — that is the whole
point of the loop), but a bare `ToDataDef` resolves against
`frame.write_target` (`write_root` if set, else `data`), which stays pinned
to whatever was active before the loop. `write_root` propagates through
`with_params` and `in_rule` so it survives `WithArgs` and cross-file
`RunRule` calls made from inside the loop, and through nested
`AtInputDataDef` loops (this rule has two, and the fix was checked against
both). `ForEach AtDataDef` is unchanged — it still rebinds writes along with
reads, which is what chunk 4's repeating-group `ForEach` (C4-10) and every
other `AtDataDef` loop in the corpus needs. `Locate` is untouched: its own
job is already "relocate the write target," so `fr.at(target)` with the
default (full rebind) is correct there regardless of which attribute name it
carries.

**Re-run of `68_chunk9_golden_case.py`:**

```
Detail.BasicGroupIAvgRate              =      0.255   (was 0.236)
Structure A.BlktTotalFullValueAmount   =     300000   (was 0)
Structure A Premium                    =        255   (was 0)
Structure B Premium                    =        510   (was 0)
```

**Regression, run in full:** every `scripts/cf/*.py` chunk 1–8 script and all
16 `tests/verify_*.py` General Liability suites re-run green — the first
engine change since chunk 0, and the first time either regression net was
asked to catch a real interpreter edit rather than confirm one wasn't needed.
Two CF scripts exit non-zero on a bare invocation for reasons unrelated to
this fix and unrelated to blanket rating: `07_diagnose_message.py` requires
CLI arguments (exit 2, argparse usage), and `63_chunk8_raas.py` makes a live
ISO RAaS call with no network/credentials available here (`--dry-run`
confirms the harness itself is unaffected).
