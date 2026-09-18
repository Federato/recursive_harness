# Property build — start here

**Last worked 2026-09-18.** This is the resume point: where things stand, how to
confirm it in two minutes, and what to pick up first.

---

## Pick up here

**Chunk 3 is closed — gated 8 of 9 on 2026-09-18, all 24 tasks done, no engine
code written.** See [`CF-CHUNK3-GATE.md`](CF-CHUNK3-GATE.md).

**Chunk 4 is closed — gated 8 of 9 on 2026-09-18**, **all 32 tasks done** and
still no engine code. See [`CF-CHUNK4-GATE.md`](CF-CHUNK4-GATE.md).

**Chunk 5 is closed — gated 8 of 9 on 2026-09-18**, **all 28 tasks done**
and still no engine code. See [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md).

**Chunk 6 is OPEN — Special Class, building side.** 29 tasks numbered
**C6-01–C6-29** in [`CF-CHUNK6-TASKS.md`](CF-CHUNK6-TASKS.md), derived from the
algorithms doc and from the opening census
([`40_chunk6_census.py`](../scripts/cf/40_chunk6_census.py)). **Chunk 6 is closed: all 29 tasks, gated 8 of 9.**

**Chunk 7 is OPEN — Special Class Business Income.** 28 tasks numbered
**C7-01–C7-28** in [`CF-CHUNK7-TASKS.md`](CF-CHUNK7-TASKS.md), derived from the
algorithms doc and from the opening census
([`49_chunk7_census.py`](../scripts/cf/49_chunk7_census.py)), **which carries
chunk 6's OI-100 correction in from the start** — every state diffed against its
own resolved parent, both package ids printed. **Chunk 7 is closed: all 28 tasks, gated 8 of 9.**

**Chunk 8 is closed: all 26 tasks, gated 7 of 9** —
[`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md). **Two points are held open on
purpose**: point 9 is owed project-wide, and **point 8 is held on CA, FL and
PR**, three jurisdictions that produce no Legal Liability premium for reasons
not yet established. Three unexplained zeros is the shape chunk 6 taught us not
to wave past.

**Chunk 8's headline: the best-prepared input any chunk has started from was
moved by running it.** An eleven-point divergence map, traced from rule XML by a
person — **8 of 11 confirmed, 3 corrected**, plus a stale line, an over-claim
and two things it does not mention:

* **Point 7** — blanket: the conclusion holds, the reason does not. The coverage
  gate writes 0 before the `Choose` the map reasons about is ever reached, and
  the cause is the same empty `BlktCauseOfLossValue` C6-28 and C7-25 found.
  **Three chunks, three coverages, one mechanism.**
* **Point 10** — Builders Risk is not `0.0`. `Premium` is **null**, we refuse,
  and **ISO charges $1**. OI-99's second instance, opposite in direction to
  Florida's.
* **Point 11** — the operand order **is** premium-bearing: $11 nested against
  $12 as a single product, at PackageMod and IRPM of 0.44.
* **Not mentioned at all** — switching the Building to Legal Liability takes
  **Contents'** LOI factor from 0.898 to 1 and its premium from $223 to $248.
  **The fork is not confined to its own premium.**

**And two harnesses nearly published results they had not earned.** A probe
whose ISO payload carried `PolicyType` and whose engine submission did not —
which read as an engine defect and would have put chunks 1–7 through a full
re-run. And a sweep that agreed with itself at $0 forty-six times because it
sent Oregon's territory to every state. Both recorded in place.

**Next: chunk 9, blanket rating** — the widest remaining gap, and the one chunks
6, 7 and 8 have each now hit from a different side.

Three things the census already found:

* **The first coverage that borrows a FULLY RATED rate.** **Eleven** values
  cross the boundary — `BasicGroupIRate` and `EQRate` copied outright, and
  three inputs feeding its own lookups. **No `BasicGroupIBaseRate` anywhere**,
  so unlike chunk 5 it cannot rate until the parent's build-up has *completed*.
* **Special's base rate is pinned to "Other than Apartments and Condominiums"**,
  making the apartment rows permanently unreachable from this group — while
  plain Business Income reaches them on the same physical table. The theft
  factor two steps earlier still varies by `ApartmentCondoIndicator`.
* **Six states delete `SetLowestBasicGroupIIBaseRate` outright** (AR, DC, KS,
  NY, RI, TX) — six of the eight that file no lowest-rate table, so C6-19's
  biconditional gets re-asked on a second coverage.

Three things the census already found, before any task has run:

* **The rating driver is a free-text class DESCRIPTION**, resolved through two
  lookups in series to one of 71 `OptionNN` codes. No construction key at all.
* **Florida is two countrywide editions behind** (`CF_CW_20230801_V01` against
  everyone else's `CF_CW_20260601_V01`), so its class vocabulary is frozen at
  2023. **The private option namespace is New York's** — 63 codes to
  countrywide's 71, 35 of them nowhere countrywide.
* **New York deletes both converter rules** and files both converter tables
  header-only, while still filing 189 Group I rate rows. Either those rows are
  unreachable or the option is a submitted field there. C6-12 decides by running
  it.

Chunk 5 is different in kind again: **Business Income is arithmetically
downstream of Building.** Three of its five forms have no base rate of their own
and read Building's already-computed rate, symbol and territory. It is the first
coverage in the project that cannot be rated without rating another coverage
first — so every chunk 1–3 finding is now load-bearing twice. Its `SetFactor`
picks **exactly one** of four values, and multiplying them would overstate the
premium by a large multiple.

Chunk 4 is different in kind, not just in data: it is the **first chunk that
rates a repeating group** (N Personal Property records per Occupancy Class,
driven by a `ForEach`), `CovForm` rather than `CovType` drives the branch and is
inherited from the occupancy class, and **PP's Special is the opposite of
Building's** — occupancy-keyed with its own territory multiplier, 14 steps
against 9.

The work follows a settled rhythm, and it is worth keeping:

> **Derive the expected numbers by hand from the filed rows FIRST, write them
> down, then run.** Every finding worth having in this project came from a
> prediction disagreeing with the engine — Arizona, the BCEG zero, the Kansas
> wind/hail mechanism, the cumulative forms. Observing what the engine does and
> writing that down proves nothing.

---

## Where the project stands

| | |
|---|---|
| Chunks built | **8 of 15**; chunks 6 and 7 at gate **8 of 9**, chunk 8 at **7 of 9** |
| Chunk 1 — Building Basic Group I | gate **8 of 8**, ISO-confirmed |
| Chunk 2 — Building Basic Group II | gate **8 of 8**, ISO-confirmed |
| Chunk 3 — Broad and Special | gate **8 of 9**, ISO-confirmed; 47 of 47 states |
| Chunk 4 — Contents | gate **8 of 9**, ISO-confirmed; 46 of 47 states; 32 of 32 tasks |
| Chunk 5 — Business Income | gate **8 of 9**, ISO-confirmed; 44 of 47 states; 28 of 28 tasks |
| ISO calls made | ~46. The engine has matched every premium; **one handling divergence found** — ISO refuses where we return $0 (OI-99) |
| General Liability | untouched — 12 suites green throughout |

**No engine code has been written since chunk 0.** Chunks 1 to 5 all ran on
the same foundation. The shared interpreter gained five nodes and three
corrections early on and nothing since.

### Settled, with evidence

| | |
|---|---|
| **Rounding** | `ROUND_HALF_UP`, **proven** against ISO at both scales (3dp rate steps and whole-dollar premium) — not assumed |
| **Null in arithmetic** | `propagate` — null in, null out; comparison with null is false. Two rival hypotheses built and disproven |
| **Null premium guard** | a null written to `Premium` or `ErcCalculatedTotalPremium` is refused |
| **Forms are cumulative** | Broad/Special layer ON TOP of Basic, they do not replace it. ISO confirms all three totals |

---

## Confirm it is all still green

**The golden cases — one line per coverage, with what each must produce.**

| Command | Must produce |
|---|---|
| `python scripts/cf/00_chunk0_checks.py` | the foundation: operators, resolver, edition chain |
| `python scripts/cf/01_golden_case.py` | chunk 1 Building Basic Group I — **$261 / $263 / $288** |
| `python scripts/cf/09_chunk2_golden_case.py` | chunk 2 Building Basic Group II — **$261 + $32** from one submission |
| `python scripts/cf/15_chunk3_golden_case.py` | chunk 3 Building Broad and Special — **$16 / $54**, layering on Basic to 293 / 309 / 347 |
| `python scripts/cf/22_chunk4_golden_case.py` | chunk 4 Contents, four forms — **$223 / $24 / $16 / $137**, Building unmoved at 263 / 32 |
| `python scripts/cf/32_chunk5_golden_case.py` | chunk 5 Business Income, four forms — **$112 / $13 / $23 / $47**, Building unmoved at 261 / 32 |
| `python scripts/cf/41_chunk6_golden_case.py` | chunk 6 Special Class, four forms — **$66 / $209 / $14 / $44**, Building unmoved at 261 / 32 |
| `python scripts/cf/50_chunk7_golden_case.py` | chunk 7 Special Class Business Income — **$39 / $123 / $23 / $47**, the item unmoved at 66 / 209 |
| `python scripts/cf/59_chunk8_golden_case.py` | chunk 8 Legal Liability — Building **$60 / $7 / $4 / $12**, Contents **$132 / $15 / $11 / $93** |

**The machinery each chunk added**, worth running when shared code changes:

| Command | What it holds |
|---|---|
| `python scripts/cf/21_chunk3_special_structure.py` | chunk 3's Special structure — incl. the $11,398 derived-field case |
| `python scripts/cf/23_chunk4_foreach.py` | chunk 4's repeating group — 209 + 105 = 314 |
| `python scripts/cf/35_chunk5_factor.py` | chunk 5's `SetFactor` — **233 not 252**, selection rather than multiplication |
| `python scripts/cf/39_chunk5_crossform.py` | three coverages on one submission, none of them moving |
| `python scripts/cf/04_shared_names.py` | gate point 6 across all **six** chains |
| `python scripts/cf/42_chunk6_zero_cases.py` | chunk 6's six zero cases — incl. Florida's spelling worth zero in Oregon |
| `python scripts/cf/45_chunk6_description_chain.py` | chunk 6's description chain — and the correction to the Florida claim |
| `python scripts/cf/46_chunk6_perform.py` | chunk 6's per-form specifics — the 1.5 coinsurance surcharge, the dead factor, the biconditional |
| `python scripts/cf/47_chunk6_forms.py` | chunk 6's form claims — the narrowed fire gate, Florida's 1.42, construction-blind Broad |
| `python scripts/cf/48_chunk6_crossform.py` | chunk 6's cross-form claims — the blanket branch, and four coverages on one submission |
| `python scripts/cf/51_chunk7_zero_cases.py` | chunk 7's six zero cases — incl. a parent worth $0 carrying a $39 child |
| `python scripts/cf/54_chunk7_borrowed.py` | chunk 7's borrowed rate — eleven values across the boundary, and no base rate |
| `python scripts/cf/55_chunk7_perform.py` | chunk 7's per-form specifics — both apartment dimensions dead, the pin that is live next door |
| `python scripts/cf/56_chunk7_crossform.py` | chunk 7's cross-form claims — the rounding counted, and five coverages on one submission |
| `python scripts/cf/57_chunk7_open_questions.py` | the algorithms page's five open questions — four answered, one left open with a reason |
| `python scripts/cf/61_chunk8_zero_cases.py` | chunk 8's six zero cases — four zeros, four unrelated causes |
| `python scripts/cf/64_chunk8_fork.py` | the fork — two concepts discarded, a third never computed |
| `python scripts/cf/65_chunk8_map.py` | the traced map, point by point |
| `python scripts/cf/66_chunk8_crossform.py` | the map **scored** — 8 of 11 confirmed, 3 corrected — and the cross-coverage LOI leak |
| `python scripts/cf/60_chunk8_raas_probe.py` | the standing engine-vs-ISO check on the Legal Liability form record |
| `python scripts/cf/05_exclusion_records.py` | gate point 7 census, with a per-group chunk 6 section |
| `python scripts/cf/08_hardcoded_literals.py --group CommercialPropertySpecialClass` | gate point 5 for a second datadef group |

**The six sweeps** take a few minutes each and enumerate all 47 jurisdictions:

    python scripts/cf/17_chunk3_enumerate_states.py   # Broad 47/47, Special 47/47
    python scripts/cf/24_chunk4_enumerate_states.py   # Contents 46/47, PR stated
    python scripts/cf/34_chunk5_enumerate_states.py   # Busn Income 44/47, AZ/TX stated
    python scripts/cf/43_chunk6_enumerate_states.py   # Special Class 47/47, AZ/FL/NY at $0
    python scripts/cf/52_chunk7_enumerate_states.py   # SpclClass Busn Income 47/47, the same three inherited
    python scripts/cf/62_chunk8_enumerate_states.py   # Legal Liability 47/47, 43 with a real premium

**All of the above re-run green on 2026-09-18**, along with all 16 General
Liability suites (`tests/verify_*.py`). **Chunks 6, 7 and 8 are the only chunks to
touch shared code** — `04_shared_names.py` (now reporting eight chains),
`05_exclusion_records.py` (per-group sections) and `08_hardcoded_literals.py`
(a `--group` argument) were extended to take further datadef groups, and all
three still pass for chunks 1–5 unchanged. That was checked, not assumed.

**No engine code has been written in eight chunks.** Chunk 8 produced the first
serious candidate for one — and the candidate turned out to be a probe whose two
sides received different submissions, not a defect.

Everything exits 0. The full set is `scripts/cf/00`–`66`; the General Liability
suites are `tests/verify_*.py` and must stay green — they are the regression net
for every shared-code change.

**Nothing is committed.** All of `cf_engine/`, `scripts/cf/`, the `docs/CF-*`
files and the `gl_engine/` edits are working-tree only.

---

## Open items — none blocking

| | |
|---|---|
| **Input validation — absent means zero** | Eight inputs now price at zero rather than raising: Arizona's `BasicGroupIReductionCredit`, an unrecognised `ConstructionType`, an absent `BCEG`, a missing `RatingTypeBasicGroupII`, a missing Group II territory, a blank `Deductible` on both chunk 3 forms, and **a construction type that is spelled right but is a rating-type name rather than one of the 25 submission values**. Every one looks like a valid submission and silently produces a cheap policy. A missing `Limit` is the only one that raises |
| **Input validation — a submission can populate a derived field** | **New 2026-09-18, and the mirror image of the above.** Every `IsNull`-guarded rule honours a value that arrived in the payload, so a submitted `SpecialBaseRate=9.999` bypasses the filed table and prices at $11,398. It fails *upward*, and **no ISO comparison catches it** — ISO has the same guards and returns the same number |
| **Building's rate-step rounding is untested at a discriminating rate** | **New 2026-09-18.** Chunk 1 recorded Building's Group I rate step as rounding after every factor, but its golden case (base 0.498) gives 0.239 either way. Class 0074 discriminates: `0.143 x 0.96 x 0.499` is **0.069 rounded once** and 0.068 rounded per factor, and the engine gives 0.069. So the per-factor reading was never actually tested. **Chunks 4 and 5's sweeps both assume per-factor rounding** and match 46 of 47 and 44 of 47 — the residual mismatches may be this. Needs a deliberate tie, the way chunk 1 settled half-up |
| **`SingleResult` with zero hits** | ISO refuses on *some* empty lookups and tolerates others; the distinguishing condition is unknown. Blanket strictness was measured and **disproven** (it breaks VA and VT, which ISO rates). Needs targeted ISO probes, not more corpus reading |
| Per-state gaps | TX's wind/hail shape untraced; DC and IL have no `BCEGFactor` row for their own Group II territory; MT, NY and PR resolve to an empty Group II symbol table |
| Housekeeping | `cf_engine` imports `gl_engine`; the shared core wants a neutral home. **Never bundle that rename with a rating change** |
| GL, optional | whether it adopts `propagate`; whether it wants its own rounding tie (OI-70) |

---

## The three things most worth remembering

1. **The countrywide chain is often the minority behaviour.** 39 of 47
   jurisdictions override `SetBasicGroupIIRate`; 18 of 47 override the Group I
   chain. Re-ask per chunk, never inherit the answer.
2. **Absent means zero, and nothing raises.** This is the recurring failure
   shape in Property, and it is why the zero cases exist in every chunk. Chunk 3
   added the sharpest case: a construction type that is present, spelled right
   and semantically correct, and still prices at zero because it is a rating-type
   name rather than a submission value.
3. **A matching premium proves less than it looks.** Nine cases matched ISO
   before a rounding tie was deliberately constructed, and every one of them was
   consistent with all three rounding modes.
4. **A check that finds nothing needs its denominator tested too.** Chunk 3
   found three defects in its own instruments and none in the corpus — gate
   point 6's shared-name check was blind to delegating rules, gate point 7's
   census was blind to theft, and the state sweep's first pass was blind to rule
   overrides. Each returned a clean result that was really an empty search.

---

## Map of the documents

| | |
|---|---|
| [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html) | **every chunk, every task, status — one page** |
| [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) | the 15-chunk plan and the eight-point gate |
| [`CF-CHUNK0-BUILD-SPEC.md`](CF-CHUNK0-BUILD-SPEC.md) | the foundation, as built |
| [`CF-CHUNK1-GOLDEN-CASE.md`](CF-CHUNK1-GOLDEN-CASE.md) · [`CF-CHUNK1-GATE.md`](CF-CHUNK1-GATE.md) | chunk 1 |
| [`CF-CHUNK2-GOLDEN-CASE.md`](CF-CHUNK2-GOLDEN-CASE.md) · [`CF-CHUNK2-TASKS.md`](CF-CHUNK2-TASKS.md) · [`CF-CHUNK2-GATE.md`](CF-CHUNK2-GATE.md) | chunk 2 |
| [`CF-CHUNK3-TASKS.md`](CF-CHUNK3-TASKS.md) · [`CF-CHUNK3-GATE.md`](CF-CHUNK3-GATE.md) | chunk 3, closed at 8 of 9 |
| [`CF-CHUNK4-GOLDEN-CASE.md`](CF-CHUNK4-GOLDEN-CASE.md) · [`CF-CHUNK4-TASKS.md`](CF-CHUNK4-TASKS.md) · [`CF-CHUNK4-GATE.md`](CF-CHUNK4-GATE.md) | chunk 4, closed at 8 of 9 |
| [`CF-CHUNK5-GOLDEN-CASE.md`](CF-CHUNK5-GOLDEN-CASE.md) · [`CF-CHUNK5-TASKS.md`](CF-CHUNK5-TASKS.md) · [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md) | chunk 5, closed at 8 of 9 |
| [`CF-CHUNK8-TASKS.md`](CF-CHUNK8-TASKS.md) · [`CF-CHUNK8-GOLDEN-CASE.md`](CF-CHUNK8-GOLDEN-CASE.md) · [`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md) | **chunk 8, closed at 7 of 9 — all 26 tasks** |
| [`CF-CHUNK7-TASKS.md`](CF-CHUNK7-TASKS.md) · [`CF-CHUNK7-GOLDEN-CASE.md`](CF-CHUNK7-GOLDEN-CASE.md) · [`CF-CHUNK7-GATE.md`](CF-CHUNK7-GATE.md) | **chunk 7, closed at 8 of 9 — all 28 tasks** |
| [`CF-CHUNK6-TASKS.md`](CF-CHUNK6-TASKS.md) · [`CF-CHUNK6-GOLDEN-CASE.md`](CF-CHUNK6-GOLDEN-CASE.md) · [`CF-CHUNK6-DESCRIPTION-CHAIN.md`](CF-CHUNK6-DESCRIPTION-CHAIN.md) · [`CF-CHUNK6-PER-FORM.md`](CF-CHUNK6-PER-FORM.md) · [`CF-CHUNK6-FORMS.md`](CF-CHUNK6-FORMS.md) · [`CF-CHUNK6-CROSSFORM.md`](CF-CHUNK6-CROSSFORM.md) · [`CF-CHUNK6-GATE.md`](CF-CHUNK6-GATE.md) | **chunk 6, closed at 8 of 9 — all 29 tasks** |

Saved ISO requests and responses: `results/cf-raas/`.
