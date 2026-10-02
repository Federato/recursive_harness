# Property chunk 8 — the gate

**Legal Liability, Building and Contents.** Filed 2026-09-18.

**8 of 9** (point 9 closed 2026-10-02 by chunk 27 RC-2). **Point 8 is held open on
purpose** — see below (chunk 27 C27-06).

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | [`CF-CHUNK8-GOLDEN-CASE.md`](CF-CHUNK8-GOLDEN-CASE.md) — Building **60 / 7 / 4 / 12**, Contents **132 / 15 / 11 / 93** |
| 2 | Every table's row count stated | ✅ | `58_chunk8_census.py` — three tables, **2 / 4 / 4 countrywide rows, 0 of 47 states filing any of them** |
| 3 | Every state enumerated | ✅ | [`CF-CHUNK8-GATE-3-5.md`](CF-CHUNK8-GATE-3-5.md) — **47 of 47**, 43 with a real premium |
| 4 | Every `0` tested against its consuming branch | ✅ | Same doc — 6 cases, **two of them refusing where $0 was predicted** |
| 5 | Every hardcoded literal key listed | ✅ | `08_hardcoded_literals.py` — **`LegalLiabilityFactor.CovType` pinned to `"Bldg"`, 1 of 2 filed values unreachable from every site**; `CovType` tested against `Legal Liability` 26 times, `Leasehold Interest` 31, `Builders Risk` 30 |
| 6 | Shared-name traps diffed | ✅ | **7 shared, 0 reading different tables — and passing did not test the thing that would hurt.** See below |
| 7 | Every exclusion's endorsement record identified | ✅ | `05_exclusion_records.py` — **Legal Liability files none of its own.** It is a *branch* of Building and Contents, not a coverage beside them, so it inherits both sides' records wholesale |
| 8 | The edition basis stated | ⬜ | **Held open.** Three jurisdictions (CA, FL, PR) produce no Legal Liability premium and the reason is not yet established — see below |
| 9 | No unexplained validation message | ✅ | **2026-10-02** (`239_chunk27_rc2.py --live`, C27-05): Building Basic / Broad / Special 2 = 2 each; Contents 3 = 3, 3 = 3, 4 = 4 (the contents cases sent with the building's `WindstormOrHailDeductible`; without it ISO refuses, OI-103); every message in the register (M-001, M-002, M-004, M-005, M-006 the Legal Liability deductible) |

**ISO:** 3 of 5 confirmed, 1 payload-blocked, **1 divergence**.

---

## Point 8 is held open, deliberately

The sweep found **four** jurisdictions producing no premium. Arizona is
understood — its rewritten rate step multiplies by `BasicGroupIReductionCredit`,
a location field defaulting to 0.0 (C6-04). **CA, FL and PR are not
understood.**

Three unexplained zeros is exactly the shape chunk 6 taught us not to wave
past: there, three states produced nothing for three *unrelated* reasons, and
each mattered. Closing point 8 without them would be recording a number instead
of a fact. **The gate stays at 7 of 9 until they are named.**

---

## The ISO run — 3 confirmed, 1 blocked, 1 divergence

| Case | Engine | ISO |
|---|---|---|
| Building Basic Group I / II | 60 / 7 | **60 / 7** ✅ |
| Building Broad | 4 | **4** ✅ |
| Building Special | 12 | **12** ✅ |
| Blanket elected | **0** | **0** ✅ — *and both contradict the map* |
| Builders Risk + reporting form | **refuses** | **rates, $1** ❌ → **fixed 2026-09-23 (OI-110): ours now rates $1, as ISO** (marked 2026-10-02, chunk 27 C27-02) |
| Contents Basic Group I | 132 | *payload refused — unconfirmed* |

### ISO rates where we refuse — OI-99's second instance, in the opposite direction

The outer `If` has no `Else`, so `Premium` is never written and our
null-premium guard fires. **ISO returns a number.** The traced map said `0.0`;
ISO says **$1**, so the map was right that it rates and wrong about what.

**OI-99 now has two instances pointing opposite ways**: Florida, where ISO
refused and we returned $0; and this, where ISO rates and we refuse. Neither
was patched. Together they say the same thing — **our null/zero handling is not
ISO's, in both directions** — and that is a decision to make deliberately, not
an edit to make twice.

### The blanket case: both agree, and both contradict the map

Predicted **$60** on the map's own argument — a Legal Liability item marked
`IncludedInBlkt = "Yes"` still matches branch 2 and rates as scheduled. **It is
$0, on both sides.** The branch *is* matched; the premium is nevertheless zero.

**Blanket is not merely unreachable here — electing it zeroes the coverage.**
Engine and ISO agree exactly, which is what makes this a finding about the map
rather than about either of them. C8-14 will find the mechanism.

### Contents is unconfirmed, and said so

ISO refuses the Contents payload on a blank-key lookup of
`WindstormOrHailDeductibleAsNumber` — a known payload requirement chunk 4
already recorded. Supplying the field on the Personal Property record did not
clear it. **Our $132 stands on our own arithmetic only**, and is listed that way
rather than counted.

**Confirmed 2026-10-02 (chunk 27 C27-05).** The lookup reads `../../../../WindstormOrHailDeductible`, which from the
Personal Property record is the **building** (the Table wrappers count), so a copy on the contents could never clear it.
With the building's `WindstormOrHailDeductible` "1,000", ISO rates all three Contents cases and **every premium (58 of
58) and message agrees**: the $132 is ISO-confirmed. As built (no building value) ISO still refuses: OI-103's class.

---

## Point 6 passed without testing the thing that would hurt

`SetLegalLiabilityFactor` and `SetLegalLiabFactor` never collide **because they
are different names** — one per datadef group. A scan asking *"does one name
read two tables?"* returns nothing.

**Gate point 6 is structurally blind to the inverse: two names, one idea.** The
traced map caught it because a person compared two files side by side. Recorded
as a limit of the gate rather than a pass of it.

---

## What chunk 8 has established

**1 · The fork is real and three steps early.** Every rate row through the
cause-of-loss adjustment is shared; the premium then starts from that
adjustment, multiplies by two small factors, and never touches coinsurance, the
LOI factor or the deductible. C8-11 proves the discarding rather than reading
it.

**2 · Contents is exactly double** — one two-row table, and **each row is
unreachable from the other side**, pinned by literal.

**3 · The quietest state layer of any chunk.** 0 of 47 file any of the three
tables; only FL and PR rewrite any of the eight premium files.

**4 · Two documents were corrected by running them.** The map's Builders Risk
`0.0` and its blanket-still-rates argument are both wrong, and the second one
is wrong in a way both engine and ISO agree on.

**5 · Two harnesses nearly published results they had not earned** — a probe
whose sides received different submissions, and a sweep that agreed with itself
at zero 46 times. Both are recorded in place.

## What chunk 8 has NOT established

* **17 of 26 tasks remain**, including every point of the map checked
  deliberately rather than in passing.
* **CA, FL and PR's zeros**, which hold point 8 open.
* **Contents against ISO.**
* **The blanket mechanism** — why a matched branch still pays nothing.
