# Property chunk 6, task C6-03 — the zero cases

**Every zero tested against its consuming branch.** Derived 2026-09-18, by hand
from the filed rows, before the run.

Script: [`scripts/cf/42_chunk6_zero_cases.py`](../scripts/cf/42_chunk6_zero_cases.py).
**All six cases matched their derivation on the first run.**

Baseline: Basic Group I **$66** · Basic Group II **$209** · Broad **$14** ·
Special **$44** · Building **$261 / $32**.

---

| # | Field removed | BGI | BGII | Broad | Special | Building |
|---|---|---|---|---|---|---|
| 0 | — | 66 | 209 | 14 | 44 | 261 / 32 |
| 1 | `ClassDescription` | **0** | **0** | 14 | 44 | 261 / 32 |
| 2 | *(Florida's spelling)* | **0** | **0** | 14 | 44 | 261 / 32 |
| 3 | `Deductible` | **0** | **0** | **0** | **0** | 261 / 32 |
| 4 | `Limit` | \<refused\> | | | | |
| 5 | `BasicGroupIISymbol` | 66 | **0** | 14 | 44 | 261 / 32 |
| 6 | `PolicyType` *(on the policy)* | 66 | 209 | **0** | **0** | 261 / 32 |

---

### 1 · One missing field takes half the premium, and the other half looks healthy

`ClassDescription` drives both Basic forms — Group I through the converted
option, Group II through the raw string. Broad keys on a hardcoded `"Frame"`
and Special on a flat statewide constant, so **neither notices it is missing**.
An item with no class description still returns $58 of premium across two
forms. A reader checking "does it rate" sees a number and moves on.

### 2 · A description ISO itself files — in another state

`"Towers - Broadcasting Antennas (Radio and TV)"` is a **real filed string in
Florida's package**. Countrywide files `"...(Cell, Radio and TV)"` and Florida
drops that one. So each spelling is correct in exactly one place and worth zero
in the other, with **no validation message either way**.

This is the fourth absent-means-zero family in the project and the first where
the input is prose: the failure mode is not a typo but *sourcing the vocabulary
from the wrong jurisdiction*. C6-11 enumerates the full Florida divergence.

### 3 · The widest single-field blast radius in six chunks

All four deductible rules end in an `Otherwise` worth **0.0**, not 1.0. Absent
`Deductible` therefore means "charge nothing", not "apply no discount" — and it
takes **all four forms at once**. Building is untouched because it carries its
own deductible field on the Structure.

### 4 · No `Limit` is refused, not rated

`InterpretError: Product wrote a NULL to 'Premium'` — the null-premium guard,
contract §12.3, doing exactly what chunk 3 recorded for Building. A premium is
money; absent is not zero.

### 5 · Group II alone falls over

`BasicGroupIISymbol` has **no setter anywhere in the Special Class ruleset**
(C6-18) — Building derives its own from construction and storeys, and Building's
Group II is unmoved at $32 in the same run. Nothing recomputes the Special Class
symbol, so removing it prices Group II at zero and leaves Group I at $66.

### 6 · The derived-field trap, as a zero case

Broad and Special gate on `PolicyType`, which lives **four levels above the
item** on the policy record. Basic Group I and II do not gate on it at all and
hold at 66 / 209. And setting it *on the item* does not help: `SetPolicyType` is
unguarded and overwrites it with blank (see
[`CF-CHUNK6-GOLDEN-CASE.md`](CF-CHUNK6-GOLDEN-CASE.md)).

---

## What the six cases say together

**Three different fields produce a zero premium, at three different scopes** —
the item (`ClassDescription`, `BasicGroupIISymbol`), the deductible key, and the
policy (`PolicyType`) — and **not one of them fires a validation message**. The
only input that produces a refusal is the one that empties the premium formula
itself.

## What these cases cannot show

* **Whether the deductible band follows the item or the location.** A 100,000
  limit gives the same factor under both readings. A discriminating limit is
  C6-10's job.
* **The blanket path.** `FullSpecialClassValue` replaces `Limit` when
  `IncludedInBlkt` is "Yes"; every case here is scheduled. C6-28.
