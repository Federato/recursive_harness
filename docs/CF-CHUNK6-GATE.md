# Property chunk 6 — the gate

**Special Class, building side.** Filed 2026-09-18.

**8 of 9.** Point 9 (validation messages) is outstanding on chunks 1–6 alike and
is a project-level item, not a chunk 6 one.

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end, every intermediate traced to a named rule and table row | ✅ | [`CF-CHUNK6-GOLDEN-CASE.md`](CF-CHUNK6-GOLDEN-CASE.md) · `41_chunk6_golden_case.py` — **$66 / $209 / $14 / $44**, Building unmoved at 261/32. **Every predicted intermediate landed on all four forms** |
| 2 | Every table's row count stated; header-only tables explained | ✅ | `40_chunk6_census.py` — 13 tables. **Three are header-only countrywide**: `BasicGroupIIRate`, `LowestBasicGroupIIRate`, `SpecialBuildingRate`. `Deductible250Factor` is declared by **0 of 47** |
| 3 | Every state enumerated, not sampled — "n of N", N from the corpus | ✅ | [`CF-CHUNK6-STATE-SWEEP.md`](CF-CHUNK6-STATE-SWEEP.md) — **47 of 47** |
| 4 | Every `0` tested against its consuming branch | ✅ | [`CF-CHUNK6-ZERO-CASES.md`](CF-CHUNK6-ZERO-CASES.md) — 6 cases, all matching first run |
| 5 | Every hardcoded literal key listed | ✅ | [`CF-CHUNK6-CENSUSES.md`](CF-CHUNK6-CENSUSES.md) — **36 pinned sites, 14 that kill filed rows**; 150 branch literals |
| 6 | Shared-name traps diffed, not assumed | ✅ | Same doc — **39 shared names, 13 reading different tables**; chunk 3's prediction held a third time |
| 7 | Every exclusion's endorsement record identified per datadef group | ✅ | Same doc — vandalism / wind-hail / theft each file a `*SpecialClass` record; cyber files one at the **policy** level |
| 8 | The edition basis stated; any table from an older edition says so | ✅ | See below — and ISO's own error message named **three different editions in one call** |
| 9 | No unexplained validation message on the golden case | ⬜ | 3–4 messages per case, **matched by ISO exactly**; still owed on all six chunks |

**ISO confirmation:** [`CF-CHUNK6-ISO-CONFIRMATION.md`](CF-CHUNK6-ISO-CONFIRMATION.md)
— **7 calls, 7 agreements**, message counts matching on every one.

---

## Point 8 — the edition basis, and what ISO revealed about it

Everything above is rated at **as-of 2026-09-17**, resolving the countrywide
package **`CF CW 20260601 V01`** with each state's own layer over it.

**ISO's Florida refusal named three editions in a single sentence:**

    Error running Lookup Rule at line 11898 in RuleSet
    CommercialPropertySpecialClassRules (Project CF CW 20230801 V04):
    Matrix: SpecialClassDescriptionConvertedOption, Project: CF FL 20241201 V02

The **ruleset** came from `CF CW 20230801 V04`, the **data** from
`CF FL 20241201 V02`, and our own basis is `CF CW 20260601 V01`. Three vintages
in one rating. New York's package is `CF NY 20260801 V01` — *newer* than the
countrywide basis. **The edition basis is not one date, and stating a single one
would be wrong.**

Florida's converter being two editions behind is the mechanical reason it still
files `"Towers - Broadcasting Antennas (Radio and TV)"` where countrywide files
`"...(Cell, Radio and TV)"` — **the state's vocabulary is frozen at its own
filing date** (C6-11).

---

## What chunk 6 established

**1 · The rating driver is prose.** Two lookups in series turn a 100-character
class description into a rate, and there is no construction key in Group I at
all. Protection class is folded into the key rather than applied as a factor,
and `ProtectionClassFactor` is computed *after* every chain that could read it
and then never read.

**2 · Three jurisdictions cannot rate a class that rates countrywide**, for
three unrelated reasons, **and none of them is a missing rate**: Florida drops
it from its own converter, New York files the converter header-only and deletes
the rule, Arizona rewrites the rate step around a Location field defaulting to
zero. ISO confirmed all three.

**3 · The cause-of-loss gate does not hold for the Basic forms.** Three chunks
established "each form gates on the cause of loss";
`SetCoverageOnPolicyIndicator` here is **hard-coded to 1** for Basic Group I and
II. ISO's Broad and Special totals carry the Basic pair inside them.

**4 · `PolicyType` is derived four levels up.** The fifth derived-field trap in
four chunks, and the first whose home is the **policy** rather than the item,
the building or the location. It is tested 20 times in this group's branch
literals — the literals census is where it would have been caught first.

**5 · A new divergence class: ISO refuses where we return zero.** Logged as
**OI-99**. Not local to chunk 6 — every `Otherwise → 0.0` in the corpus sits on
the same question.

---

## Closed 2026-09-18 — all 29 tasks

The coverage-specific tasks are written up in
[`CF-CHUNK6-DESCRIPTION-CHAIN.md`](CF-CHUNK6-DESCRIPTION-CHAIN.md) (C6-10–14),
[`CF-CHUNK6-PER-FORM.md`](CF-CHUNK6-PER-FORM.md) (C6-15–19),
[`CF-CHUNK6-FORMS.md`](CF-CHUNK6-FORMS.md) (C6-20–23) and
[`CF-CHUNK6-CROSSFORM.md`](CF-CHUNK6-CROSSFORM.md) (C6-24–29).

**Three things chunk 6 published and then had to correct:**

1. **Florida's "private option namespace" did not exist** — the opening census
   diffed across countrywide editions. **OI-100.** The private namespace turned
   out to be New York's.
2. **The rounding convention was recorded backwards** on the algorithms page:
   Special Class carries Building's *Special-form* `Product`-only convention on
   **all four** forms. Corrected in six places (C6-27).
3. **The construction-blindness test, as first written, proved nothing** — it
   sent strings `ConstructionTypeToUse` never resolves to. Redone against
   values pinned legal by Building moving (C6-22).

## What chunk 6 has NOT established

* **Basic Group II, Broad and Special per state.** The 47-jurisdiction sweep
  prices **Group I**, the form whose key is state-filed.
* **The blanket branch cannot be priced from the item.** C6-28 ran it — the
  first execution of that branch in the project — and found that
  `SetNonEQBlanketValues` overwrites the denominator and the cause of loss from
  policy-level blanket records. It takes its zero arm and stays there. Pricing
  it is chunk 9.
* **Puerto Rico can never be confirmed**, and files the most distinctive Special
  Class data in the corpus.
* **Building's rate-step rounding** is still the open question chunk 5 raised.
  Chunk 6's chains are shorter and did not discriminate it either.
