# Property chunk 7 — the gate

**Special Class Business Income.** Filed 2026-09-18.

**8 of 9.** Point 9 (validation messages) is outstanding on chunks 1–7 alike —
and chunk 7 is the **first chunk where ISO's message count does not match the
engine's**, which sharpens it.

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end, every intermediate traced to a named rule and table row | ✅ | [`CF-CHUNK7-GOLDEN-CASE.md`](CF-CHUNK7-GOLDEN-CASE.md) · `50_chunk7_golden_case.py` — **$39 / $123 / $23 / $47**, the Special Class item unmoved at 66 / 209 |
| 2 | Every table's row count stated; header-only tables explained | ✅ | `49_chunk7_census.py` — 12 tables. **`BasicGroupIIRate` and `LowestBasicGroupIIRate` are header-only countrywide** for the third coverage group running; two more tables have **no consumer in this group at all** |
| 3 | Every state enumerated, not sampled | ✅ | `52_chunk7_enumerate_states.py` — **47 of 47** |
| 4 | Every `0` tested against its consuming branch | ✅ | `51_chunk7_zero_cases.py` — 6 cases |
| 5 | Every hardcoded literal key listed | ✅ | `08_hardcoded_literals.py --group CommercialPropertySpecialClassBusnIncome` — **38 pinned sites, 23 that kill filed rows** |
| 6 | Shared-name traps diffed, not assumed | ✅ | `04_shared_names.py` now reports **seven** chains — 25 shared names, 11 reading different tables |
| 7 | Every exclusion's endorsement record identified per datadef group | ✅ | `05_exclusion_records.py` — vandalism, wind/hail and theft each file a `*SpclClassBusnIncome` record; cyber is policy-level |
| 8 | The edition basis stated | ✅ | As of 2026-09-17 over `CF CW 20260601 V01`; FL still resolves over `CF_CW_20230801_V01`, as chunk 6 established |
| 9 | No unexplained validation message on the golden case | ⬜ | **ISO 3, engine 5** on the Basic call and **ISO 1, engine 4** with the parent's deductible removed — see below |

**ISO confirmation: 5 calls, 5 agreements** — including the one that mattered.

---

## The call that mattered

Remove the Special Class item's `Deductible`:

| | Special Class item | Business Income |
|---|---|---|
| baseline | $66 / $209 | $39 / $123 |
| no deductible | **$0 / $0** | **$39 / $123 — unmoved** |

**ISO agrees on all four figures.** The deductible factor is applied at the
parent's *final-rate* step and Business Income copies `BasicGroupIRate` two
steps earlier — so **a Special Class item worth nothing still carries a $39
Business Income premium**, and nothing anywhere says so.

That is the borrowed-rate reading confirmed by an outside opinion, not just by
our own arithmetic.

---

## Point 9 — the first message-count divergence in the project

Chunk 6's ISO run matched the engine's message count on every one of seven
calls. Chunk 7 does not:

| Call | ISO | engine |
|---|---|---|
| OR Basic | 3 | **5** |
| OR Broad | 3 | **5** |
| OR Special | 4 | **6** |
| OR, parent's deductible removed | **1** | **4** |

**The engine raises more messages than ISO, and the gap widens when the parent
is broken.** Both sides agree on every premium, so this is not a rating
divergence — but it is the first hard evidence that our message set is not
ISO's, and gate point 9 cannot be closed on any chunk until it is explained.
Recorded here rather than investigated, because it reaches back into chunks 1–6.

---

## What chunk 7 established

**1 · The first coverage that borrows a finished rate, confirmed by ISO.**
Basic Group I has no lookup of any kind — `04_shared_names.py` reports
`SetBasicGroupIRate` and `SetFactor` resolving to **no matrix at all** in this
group. Plain Business Income reads the Building's *base* rate and rebuilds;
this one reads the answer.

**2 · Six values cross the boundary, not five.** The opening census said five.
The golden case found a sixth: **`BasicGroupIINumericValue`**, the parent's
numeric multiplier of 8, read across the boundary by Group II's rate step. The
census's pattern only matched names ending in Rate/Symbol/Terr/Factor. **C7-12
was corrected before it started.**

**3 · One missing parent field reaches two child forms by two different
routes.** Removing the item's `ClassDescription` was predicted to take Group I
only — it takes Group II as well, because the description feeds *both* the rate
Group I copies and the numeric value Group II borrows.

**4 · Omitting a field is not the same as saying "Not Applicable".**
`SetFactor`'s second branch tests `MonthlyLimitOfIndemnity != "Not Applicable"`
through `FirstValue FromConstant=""`. An absent field reads as `""`, elects the
branch, and copies a factor nothing computed — **$0 on both Basic forms with
`TypeOfRiskFactor` sitting at a healthy 0.55 one field away.** Chunk 5's record
carried the value explicitly, so chunk 5 never met it.

**5 · Chunk 6's biconditional does NOT hold here, and how it fails is the
finding.** In chunk 6, the states that could reach `LowestBasicGroupIIRate`'s
read were exactly the states that filed it. Here six of the eight non-filers
**delete the rule outright** — and the other two, **FL and PR, leave the rule
alone while filing no table**, so they reach a read with nothing to read.
**A rule inferred from chunk 6 would have called those two defects.**

**6 · The apartment dimension is pinned on BOTH lookups, not one.** The
algorithms page records the Special base rate as pinned to `"Other than
Apartments and Condominiums"` while the theft factor two steps earlier *still
varies* by `ApartmentCondoIndicator`. The literals census shows
`SpecialLeaseHoldTimeElementTheftExclusionFactor.ApartmentCondoIndicator`
**pinned to `"No"` from every site that reads it**. There is no live dimension
feeding a dead key — **both are dead**, and C7-20's premise needs rewriting
before it runs.

**7 · One pin is unreachable here and reachable elsewhere, measured.** The
census reports `SpecialFormIncldgTheftTimeElementBaseRate`'s risk-type column
pinned *"from the pinned site only — the same column is also read live
elsewhere"*. That is C7-19's claim with the measurement attached.

---

## What chunk 7 has NOT established

* **19 of 28 tasks remain** — C7-10 through C7-28, other than the parts C7-13
  and C7-17 settled inside the sweep.
* **Earthquake has not been run** — it has no standalone premium file and
  charges only through Agreed Value. C7-11.
* **The message-count divergence is recorded, not explained.**
* **Puerto Rico can never be ISO-confirmed**, and is the only jurisdiction
  filing its own Broad base rate and leasehold theft factor for this group.
