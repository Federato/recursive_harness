# Property chunk 6, task C6-08 — ISO confirmation

**Seven calls, each testing a different structural claim.** 2026-09-18.

Script: [`scripts/cf/44_chunk6_raas.py`](../scripts/cf/44_chunk6_raas.py).
Requests and responses saved under `results/cf-raas/`.

## Result — **7 of 7 agree**

| Call | Predicted | ISO | |
|---|---|---|---|
| OR Basic | BGI **$66** + BGII **$209** | 66.0 / 209.0 | ✅ |
| OR Broad | **$14** | 14.0 | ✅ |
| **OR Broad, Fire Resistive** | **$14 — unmoved** | 14.0 | ✅ |
| OR Special | **$44** | 44.0 | ✅ |
| FL Basic | $0 — **and ISO refuses** | HTTP 400 | ✅ as predicted |
| AZ Basic | **$0** | 0.0 | ✅ |
| NY Basic | BGI **$0** + BGII **$55** | 0.0 / 55.0 | ✅ |

**Message counts matched the engine's on every call** — 3/3, 3/3, 3/3, 4/4, 3/3,
3/3.

---

## What each call settled

### The Group II numeric value of 8 is real — $209 confirmed

The chunk's largest single claim. `SpecialClassBasicGroupIINumber` is keyed on
the **raw** class description and multiplies the base rate outright:
`0.028 × 1.0 × 8 = 0.224`. ISO returns **209.0**. If this had been wrong, every
Special Class Group II premium in the project would have been wrong.

### Broad really is construction-blind — the call that mattered

The same item re-sent as **Fire Resistive** returns **14.0 again**. Building's
Broad moves 0.015 → 0.010 on that identical change; Special Class's does not
move at all, because `LookupBroadFormBaseRate` keys on a hardcoded `"Frame"`.
ISO confirms the literal is a literal (C6-22, settled ahead of its own task).

### Basic Group I and II are not gated on the cause of loss — confirmed by ISO

The Broad call's total is **$289** and the Special call's is **$319**, each
being the Basic pair's **$275** plus that form's own premium. Both Basic
premiums compute on a `Broad` submission and on a `Special` one. The pattern
that held for three chunks running — *each form gates on the cause of loss* —
**does not hold here, and ISO agrees it does not** (C6-26, settled early).

### Arizona's reduction credit is confirmed, not contradicted

ISO returns `BasicGroupIBaseRate = 0.07` and **no Group I premium at all**,
while Group II rates normally at $335. Exactly our reading: Arizona's rewritten
rate step multiplies by `BasicGroupIReductionCredit`, a Location field read
through `FromConstant="0.0"`, and the payload does not carry it.

### New York's deletions are a complete, self-consistent override

Group I **$0**; Group II **$55** on base 0.063 with **no numeric multiplier at
all**. New York files the converter header-only, deletes
`SetBasicGroupIISymbolNum` *and* `SetBasicGroupIINumericValue`, **and rewrites
`SetBasicGroupIIRate` so it never reads them.** Not a filing with a hole in it —
a different chain. (C6-13.)

---

## The one divergence — ISO refuses where we return $0

Florida returned **HTTP 400**, naming the failure precisely:

    Error running Lookup Rule at line 11898 in RuleSet
    CommercialPropertySpecialClassRules (Project CF CW 20230801 V04):
    Matrix: SpecialClassDescriptionConvertedOption,
    Project: CF FL 20241201 V02,
    Keys: CW, Towers - Broadcasting Antennas (Cell, Radio and TV).
    No results have been returned.

**The mechanism is confirmed** — Florida's own project, this description absent,
the countrywide fallback pass also empty. **The handling is not.** ISO treats a
`rul:Lookup` that finds no row as an **error**; our interpreter lets the guarded
rule fall through to its `Otherwise` and writes **0.0**.

Both are readings of the same filing and **only ISO's is authoritative**.
Recorded as **OI-99** rather than patched into the engine mid-chunk, because the
change is not local: chunk 6's zero cases, chunk 4's and chunk 5's absent-means-
zero findings, and every `Otherwise → 0.0` in the corpus sit on the same
question.

Two incidental details worth keeping:

* **Florida's package is `CF FL 20241201 V02`** — an older edition than the
  countrywide `20260601 V01` the rules came from. The 400 names both.
* **ISO's own error came from `CF CW 20230801 V04`** — a *third* edition again.
  The ruleset, the state data and the rate tables are not all one vintage.

---

## Two method findings from building this run

**1 · A weak matcher turned an agreement into a finding.** The first draft
confirmed a zero by "no non-zero premium anywhere in the response" and reported
**Arizona as a disagreement** — when Arizona agreed exactly, its Group I being
zero and its Group II legitimately carrying $335. Fixed by reading each form's
own `CommercialPropertySpecialClass<Form>Coverage/Premium`. **A harness that
manufactures findings is worse than one that misses them**, because the false
one gets written down.

**2 · Setting Group II's territory on the item did nothing.** New York priced
Group II at zero with a perfectly valid territory in the payload: the field is
resolved on the **Location** and copied down. The same trap chunk 3 hit sending
Oregon's "Portland" to CA and AK — this time the value was right and the
*level* was wrong.

---

## Puerto Rico, again

PR is excluded — the RAaS subscription does not cover it (OI-86). PR is also the
**only jurisdiction filing a complete 213-row Special Class rate table of its
own**. The state with the most distinctive filing in this chunk is the one that
can never be checked, and that has to be said wherever a PR premium is shown.
