# Property chunk 8, task C8-01 — the golden cases

**Legal Liability, Building and Contents, all four forms.** Derived 2026-09-18.

**Every number below was read off the filed rows and worked out by hand before
the engine was run.**

Script: [`scripts/cf/59_chunk8_golden_case.py`](../scripts/cf/59_chunk8_golden_case.py).

---

## The case

**Chunk 1–4's own risks**, with the coverage switched to Legal Liability. Every
rate row through the cause-of-loss adjustment is shared, so the numbers below
are the numbers those chunks already produced — taken three steps earlier and
multiplied by two small factors.

    Premium = r0( r0( r0( r0( r0( r3( r3(RATE × LegalLiabilityFactor)
                                     × LegalLiabAddlInsurableIntFactor )
                                 × Limit/100 )
                             × PackageModFactor ) × IRPMFactor )
                     × CyberBGI ) × CyberCOLExcptnsBGI )

---

## Predictions and results

| Form | Rate source | Rate | **Building** ×0.25 | **Contents** ×0.50 |
|---|---|---|---|---|
| Basic Group I | `BasicGroupICauseOfLossAdjustment` | 0.239 / 0.263 | **$60** ✅ | **$132** ✅ |
| Basic Group II | `BasicGroupIICauseOfLossAdjustment` | 0.027 / 0.030 | **$7** ✅ | **$15** ✅ |
| Broad | `BroadRate` | 0.015 / 0.021 | **$4** ✅ | **$11** ✅ |
| Special | **`SpecialRate`** / **`SpecialCauseOfLossAdjustment`** | 0.047 / 0.186 | **$12** ✅ | **$93** ✅ |

**All eight landed on the first clean run**, and **$60 / $7 are ISO-confirmed**
(`60_chunk8_raas_probe.py`).

**Contents is exactly double.** One two-row table — `LegalLiabilityFactor`
keyed `"Bldg"` → 0.25 and `"PersProp"` → 0.50 — and nothing else differs in the
factor chain. C8-12, settled by the golden case.

**The Special forms already show map point 6.** Building reads the raw
`SpecialRate`; Contents reads `SpecialCauseOfLossAdjustment`. Identical here
only because the theft factor defaults to 1.0 — which is exactly why C8-19
exists.

---

## Two things had to be right first, and getting one wrong nearly cost an engine change

### A · `PolicyType` must be set on the POLICY

`AttachFormCommercialPropertyLegalLiabilityCoverageForm` gates on
`PolicyType = "Commercial Property Policy"` **and**
`CovType = "Legal Liability"`. Its `Else` branch is a bare:

```xml
<rul:Remove AtDataDef="…CommercialPropertyLegalLiabilityCoverageForm"
            RemoveMultiple="true" />
```

**Without `PolicyType`, ISO's own rule deletes the coverage-form record the
submitter supplied.** The insurable-interest factor falls to its **0.0**
default and every premium is $0.

**This is C6-01's trap for the second time, one chunk later.** There an absent
`PolicyType` gated two forms shut; here it makes ISO *delete* a record you sent.

#### And the probe that asked about it was broken

The first run of the golden case produced $0 everywhere. The record was present
in the tree *before* `Interpreter.run` and gone *after* it, which reads exactly
like an interpreter dropping a submitted record — **an engine defect, the first
in eight chunks, and one that would have put chunks 1–7 through a full re-run.**

A probe was written to put the question to ISO. **Its ISO payload set
`PolicyType`; its engine submission did not.** The two sides received different
inputs, and the difference looked like the defect.

**Its control passed and proved nothing.** The control was a class-rated
building, which never touches `PolicyType`. **A control that passes without
exercising the variable under test is not a control.**

The engine was right throughout. Recorded in
[`60_chunk8_raas_probe.py`](../scripts/cf/60_chunk8_raas_probe.py) rather than
quietly fixed, because the near-miss is worth more than the answer: this is the
same family as OI-92 and OI-100 — *the input, not the arithmetic* — and the
first instance whose proposed remedy was a change to shared engine code.

### B · `CovForm` must be set on the OCCUPANCY CLASS, not the item

`SetCovForm` is an unguarded `Copy` from `../../CovForm`, so a value set on the
Personal Property record is overwritten and **Contents never enters the Legal
Liability branch at all** — it returns chunk 4's class-rated 223 / 24 / 16 / 137.

**That is point 1 of the traced map, arriving early and by accident**: the gate
is not merely a different field from Building's, it is a different **level**.
Building's `CovType` sits on the item, so two buildings on one location can
disagree; Contents' `CovForm` is inherited, so two contents items under one
occupancy cannot. C8-15 tests both halves deliberately.

---

## What this case cannot show

* **That coinsurance, the LOI factor and the deductible are really discarded.**
  They are absent from the formula, but absent and "present but 1.0" look
  identical on one case. C8-11.
* **Point 6 with money on it** — the theft factor defaults to 1.0 here. C8-19.
* **That blanket is unreachable.** This case is scheduled. C8-14.
* **Anything about the other 46 jurisdictions.** C8-04.
