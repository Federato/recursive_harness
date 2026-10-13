# Property chunk 8, tasks C8-03 to C8-05

2026-09-18. Scripts:
[`61_chunk8_zero_cases.py`](../scripts/cf/61_chunk8_zero_cases.py),
[`62_chunk8_enumerate_states.py`](../scripts/cf/62_chunk8_enumerate_states.py),
[`04_shared_names.py`](../scripts/cf/04_shared_names.py).

---

## C8-03 · Zero cases — four zeros, four unrelated causes, one answer

Baseline: Building Legal Liability Basic Group I **$60**.

| # | Case | Result |
|---|---|---|
| 1 | no coverage-form record | **$0** — factor 0.25 / **0.0** |
| 2 | no `PolicyType` on the policy | **$0** — factor 0.25 / **0.0** |
| 3 | `CovType = "Leasehold Interest"` | **refuses** |
| 4 | Builders Risk + a Reporting Form record | **refuses** |
| 5 | no `Limit` | **refuses** |
| 6 | `CovForm` on the **item** | **$223** |

### Two identical zeros from opposite causes

Case 1: `AttachForm…` **appends** an empty record, nothing carries
`AddlInsurableInt`, the option is blank, and the setter's `Else` writes 0.0.
Case 2: the same rule **deletes the record the submitter sent**. Same $0,
opposite mechanisms, and nothing in the answer distinguishes them. Case 2 is the
one that nearly cost an engine change.

### Two cases were predicted at $0 and both refuse — and both correct the map

**Case 3 — the map is right about the wrong scope.** It says Leasehold Interest
returns 0.0 *in this file*, and it does. But a submission is not a file: the
CovType also activates the Leasehold Interest rate chain — **the only
`rul:Power` in the package** — and with no leasehold data it reaches
`Power(0, 0)`. The engine declines to invent an answer. **That zero cannot be
exercised from chunk 8 at all**; it belongs to chunk 11.

**Case 4 — the map is simply wrong.** The outer `If` has **no `Else`**, so when
it fails nothing is written and `Premium` is **null**, not 0.0. The
null-premium guard refuses. **Unwritten and zero are different things**, which
is exactly why this project has that guard. Whether ISO returns 0 or a 400 is
OI-99's question, and C8-08 will ask it.

### And the case that isn't a zero is the dangerous one

`CovForm` on the item instead of the occupancy class returns **$223** — a real,
plausible Contents premium from the class-rated branch. **The four loud zeros
are safer than that one number.**

---

## C8-04 · The sweep — 47 of 47, and the first version was worthless

| | |
|---|---|
| Match their own prediction | **47 of 47** |
| Producing a real premium | **43** |
| Producing none | **4** — AZ, CA, FL, PR |

**The sweep's target is the fork, not the rate chain.** Chunks 1–3 already swept
the shared rate chain across all 47; re-deriving it would test the same
arithmetic twice while hiding what chunk 8 is about. So each state's own
`BasicGroupICauseOfLossAdjustment` is read from the run and the Legal Liability
premium predicted from it.

### The first version reported 47 of 47 and proved nothing

It sent Oregon's `BasicGroupIRatingTerr = "Portland"` to all 47. That territory
exists only in Oregon, so **46 states produced no Group I rate at all** and the
sweep agreed with itself at **$0** forty-six times.

**A sweep whose answer is zero almost everywhere is an empty search wearing a
pass** — the same failure gate points 6 and 7 hit in chunk 3, and the second
time in chunk 8 that a harness nearly published a result it had not earned.

The fix pins `BasicGroupIRatingTerrFactor` to **1.0** on the location in every
jurisdiction. The factor is `Copy`d down from the location rather than looked up
from the item, so supplying it removes the one input that cannot cross state
lines and leaves each state's **own** base rate, protection class and
cause-of-loss adjustment driving the answer.

**These are not premiums any state would charge** — they are 47 genuine
cause-of-loss adjustments put through one countrywide fork, which is what C8-04
is for. Stated rather than glossed.

**Four states still produce nothing.** Arizona is understood — the rewritten
rate step multiplies by `BasicGroupIReductionCredit`, a location field
defaulting to 0.0 (chunk 6, C6-04). **CA, FL and PR are not yet explained** and
are carried into C8-09 rather than counted as confirmations.

---

## C8-05 · Shared names — 7 shared, **0 reading different tables**, and a blind spot

| | |
|---|---|
| Names defined in more than one datadef group | **7** |
| …of those, reading different rate tables | **0** |

The quietest shared-name result of any chunk — and the reason is the finding.

**`SetLegalLiabilityFactor` and `SetLegalLiabFactor` never collide, because they
are different names.** Each is defined in exactly one datadef group: the first
in `CommercialPropertyStructure`, the second in
`CommercialPropertyPersonalProperty`. A scan that asks *"does one name read two
tables?"* returns nothing.

**Gate point 6 is structurally blind to this shape.** It catches *one name, many
tables*. Legal Liability's trap is the inverse — **two names, one idea** — and
no amount of shared-name scanning will surface it. The traced map caught it
(point 2) because a person compared two files side by side.

That is worth recording as a limit of the gate rather than a pass of it: **C8-05
passes, and passing did not test the thing that would actually hurt.** C8-16
tests it directly.
