# Property chunk 3 — gate

**Building: Broad and Special.** Opened 2026-09-17, gated 2026-09-18.

> **Chunk 3 passes 8 of 9, with point 9 outstanding on this chunk and on
> chunks 1 and 2 alike.** No engine code was written for it — the third
> coverage in a row to run on chunk 0's foundation unchanged.

| | |
|---|---|
| Golden cases | Broad **$16**, Special **$54**, both exact on the first run |
| ISO calls | **7 this chunk, 7 matches** — and the message counts matched too |
| Jurisdictions | **47 of 47** on both forms, none skipped |
| Engine code written | **none** |
| Tasks closed | **23 of 24** (task 9 is this document) |

---

## The eight points

### 1 · A golden case rates end to end, every intermediate traced — **PASS**

Two of them, one per form, because each gates its base rate on
`CauseOfLossToUse`. Every step traced to a named rule and a named table row in
[`CF-CHUNK3-TASKS.md`](CF-CHUNK3-TASKS.md); both hand-derived before the run and
both exact on the first attempt.

    Broad    0.015 base -> 0.015 rate -> 1.237 LOI -> 0.017 adjusted -> 0.016 final -> $16
    Special  0.047 base -> 0.047 rate -> 0.047 COL -> 1.237 LOI -> 0.056 adjusted -> 0.054 final -> $54

ISO confirms both, and confirms they **layer on top of Basic** rather than
replacing it — $293 / $309 / $347 for the three cause-of-loss selections,
coverage by coverage and on the policy total.

### 2 · Row counts stated; header-only explained — **PASS**

| Table | Rows | Note |
|---|---|---|
| `BroadFormBaseRate` | 30 CW | two-tier by construction; `PersProp` and BI rows belong to later chunks |
| `SpecialBuildingRate` | **header-only CW** | 45 of 47 file their own; **FL and PR override the rule instead** |
| `SpecialBuildersRiskRate` | 1 CW row (0.015) | resolves in **47 of 47** |
| `BroadSpecialLOIFactorBldg` | 57 CW | **shared by both forms**; only PR files its own |
| `DeductibleFactor` | 462 (OR) | state-filed in 45 of 47 |
| `SpecialBldgTheftExclusionFactor` | CW | the 0.88 credit |
| `LimitationsOnCovForRoofSurfacingFactor` | 3 CW | **one row unreachable** — see point 5 |
| `DeductibleByLocationFactor` | 1 CW row (0.995) | shared; Broad has no rule of its own |

The header-only table is the chunk's central fact and it is explained rather
than noted: **it is the entire reason FL and PR file an overriding
`SetSpecialBaseRate` and the other 45 do not.** The Builders Risk path, which
has a countrywide row, needed an override from nobody.

### 3 · Every state enumerated, not sampled — **PASS**

**47 of 47 on both forms, nothing skipped**, each premium predicted from that
jurisdiction's own filed rows before the engine ran.
[`CF-CHUNK3-STATE-SWEEP.md`](CF-CHUNK3-STATE-SWEEP.md).

The first pass skipped FL and PR as "no rate filed" and **that was wrong** —
the engine rated Florida at $38 anyway. Both rate Special through their own
overriding rule reading a differently-named table, which a search on the
countrywide table name cannot see.

Override census, re-asked for this chunk and **the opposite of chunk 2's**:

| | Chunk 2 | Chunk 3 |
|---|---|---|
| States overriding the base-rate rule | **39 of 47** | **3 of 47** (AL, FL, PR) |
| States overriding any chain rule | most | 0–3 |

AL, KS and RI override rules and still match a countrywide-shaped prediction:
an override is not automatically a divergence. Only FL and PR change the
arithmetic.

### 4 · Every `0` tested against its consuming branch — **PASS**

Five cases, both forms. [`CF-CHUNK3-ZERO-CASES.md`](CF-CHUNK3-ZERO-CASES.md).

Two predictions were wrong and both corrections are carried:

* **Special's deductible fall-through** was documented as having no
  `Otherwise`. The filed XML has one, identical to Broad's. Our own algorithms
  page was wrong — corrected there, along with a branch test written as `And`
  where the rule files an `Or`.
* **A missing `Limit` raises** rather than pricing at zero. It is the only one
  of the now-eight known missing inputs that fails loudly, because it reaches
  the premium as a null rather than as a factor of zero.

### 5 · Every hardcoded literal key listed — **PASS**

Chunk 1's census covers the whole Building coverage. Chunk 3 adds three
specifics, and two of them are the point:

* **`"1150"` is a Builders Risk switch with at least two independent
  consequences.** `SetBroadBaseRate`/`SetSpecialBaseRate` route to the
  `BldrRisk` rows, and `SetCoinsuranceFactor` **separately** hardcodes the same
  literal and returns 1.0 instead of the coinsurance factor. Finding one
  consequence does not find the other. Broad class 1150 is **$15**, not the $14
  the base rate alone predicts; Special is **$18**.
* **`"Paragraph B"` makes a filed row unreachable.**
  `SetLimitationsOnCovForRoofSurfacingACVFactor` tests
  `Applicability != "Paragraph B"` before looking anything up and its `Else`
  assigns a flat 1.0 — so the filed `Paragraph B → 0.99` row cannot be produced
  by any submission.
* **Florida files 21 class codes inside its own `SetSpecialBaseRate`** to split
  residential from non-residential. No other jurisdiction has that dimension.

### 6 · Shared-name traps diffed, not assumed — **PASS**

Nine ambiguous names on this chain, **9 of 9 adjudicated**.
[`CF-CHUNK3-SHARED-NAMES.md`](CF-CHUNK3-SHARED-NAMES.md).

**The check itself was broken and had to be fixed first.** It read only the
tables named directly inside a rule, and ISO's `Set*` rules delegate via
`RunRule` — so the two *documented* trap cases, defined in 16 and 6 datadef
groups, each reported zero tables and could never have been flagged. Made
transitive, the chunk 1 chain goes from 1 ambiguous name to 6, chunk 2 from 1 to
4, chunk 3 from 1 to 9, the corpus from 9 to 83.

`SetSpecialBaseRate` turns out to be **wider than documented**: 16 datadef
groups reading **five** different tables. Ours reads `SpecialBuildingRate` plus
`SpecialBuildersRiskRate`. Chunks 4, 5, 6 and 7 each execute a different one.

### 7 · Every exclusion's endorsement record identified — **PASS**

Theft is chunk 3's exclusion: **5 distinct records across 7 datadef groups**,
ours being `CommercialPropertyTheftExclusion` (CP 10 33), a child of the
**structure**. Elected, it prices $54 → **$47**, ISO-confirmed, and Broad does
not move. [`CF-CHUNK3-EXCLUSION-RECORDS.md`](CF-CHUNK3-EXCLUSION-RECORDS.md).

**The census was missing theft entirely** until it was extended — the record
test lives in a `*Indicator` rule, not the `*Factor` rule. Point 7 would have
passed on a census omitting the one family this chunk needed.

And a correction to the gate's own premise: **not every exclusion is
per-coverage.** Cyber Incident Exclusion files **one** record at the **policy**
level, feeding ten coverage-specific factor rules. For cyber, a single
policy-wide control is what ISO filed; a per-coverage one would be the
divergence.

### 8 · The edition basis stated — **PASS**

`OR@20260917` resolving `CF_OR_20260601_V01` over `CF_CW_20260601_V01`, the same
basis as chunks 1 and 2. The sweep resolves each jurisdiction's own chain; FL
lands on `CF_FL_20241201_V01` over `CF_CW_20230801_V01`, an older pair, and
rates correctly there — which is the edition chain doing its job rather than an
anomaly.

### 9 · No unexplained validation message — **NOT DONE**

Owed on chunks 1, 2 and 3 alike. What this chunk adds is the strongest evidence
yet that it will pass: **ISO's message count matched the engine's on all seven
calls** — 2/2, 3/3, 1/1, 2/2, 3/3, 3/3, 2/2.

Two facts for whoever closes it:

* **Attaching CP 10 33 silences a message** (3 → 2) as well as cutting the
  rate. The mirrored-pair behaviour the gate's own note warns about.
* **Florida cites `CP 03 22` where countrywide cites `CP 03 20`** for the same
  check. A register keyed on form number rather than rule name splits one entry
  into two.

---

## What the build found that the plan did not

**Three instrument defects in two days, and none in the corpus.** Gate point 6's
check was blind to delegating rules; gate point 7's census was blind to theft;
the state sweep's first pass was blind to rule overrides. Each returned a clean
result that was really an empty search. The habit that caught all three is the
same one: predict a specific number, and treat the disagreement as the finding.

**A construction type that is spelled right and prices at zero.**
`ConstructionType` is a 25-value submission domain that maps onto the six rating
types, and `Frame` is the only one of the six that is also a valid input.
Submitting `"Joisted Masonry"` — the name the rate table itself is keyed on —
misses the domain lookup and prices the whole chain at zero. Eighth member of
the absent-means-zero family, and the first where the input is present,
correctly spelled and semantically right.

**A filed endorsement that can never change a Broad building premium.** Every
Broad base rate filed anywhere in the corpus absorbs both surviving
roof-surfacing factors at three decimals — 0 of 6. It is magnitude, not the rule
boundary: Special applies the identical factor to 0.047 and moves $54 → $52.

**A submission can populate a derived field, and that is a new risk family.**
Every `IsNull`-guarded rule honours a value that arrived in the payload — the
guard cannot distinguish "already set by an earlier rule" from "supplied by the
submitter". A submitted `SpecialBaseRate = 9.999` bypasses the filed table and
prices at **$11,398** with nothing raised. This is the **mirror image** of
everything found so far: it fails upward as readily as downward, and **no ISO
comparison would catch it** — ISO has the same guards and returns the same
number. The one rule the task list flagged as suspicious,
`SetSpecialCauseOfLossAdjustment`, is the only step that cannot be overridden
this way. The unguarded rule is the safe one.

---

## What is still owed

1. **Gate point 9**, on this chunk and retroactively on chunks 1 and 2.
2. **Input validation**, now two distinct requirements: reject a missing input
   that would price at zero, **and** reject a submission that populates a
   derived field. The second is new as of this chunk and needs a schema answer
   the engine does not have.
3. **Telling `SpecialTotAmtInsurance` from
   `SpecialIncludingTheftTotAmtInsurance` numerically** — both equal the
   building limit until Contents exists. Chunk 4.
4. **Puerto Rico has no external confirmation and never will** (OI-86), and it
   is the jurisdiction with the most unusual Special reading in the corpus.
   Must be stated wherever a PR premium is presented.
5. **The state-layer shared-name check.** `04_shared_names.py` compares across
   datadef groups within one package; FL and PR prove the same trap exists
   across the state layer, and nothing checks for it.

## What is deliberately not here

No blanket branch (chunk 9, still a stub everywhere). No Legal Liability
(chunk 8). No Contents, no Business Income. No `PersProp` rows from the tables
this chunk read, though they were seen in passing. No comparison against
`CFRater1.01.xlsb`.

---

## Reproducing it

    python scripts/cf/15_chunk3_golden_case.py        # $16 / $54, and the layering
    python scripts/cf/16_chunk3_zero_cases.py         # 5 cases x 2 forms
    python scripts/cf/17_chunk3_enumerate_states.py   # 47 of 47, both forms
    python scripts/cf/18_chunk3_theft_exclusion.py    # $54 -> $47
    python scripts/cf/20_chunk3_broad_structure.py    # tasks 10-14
    python scripts/cf/21_chunk3_special_structure.py  # tasks 17, 19, 20
    python scripts/cf/04_shared_names.py              # point 6, all three chunks
    python scripts/cf/05_exclusion_records.py         # point 7 census
    python scripts/cf/19_chunk3_raas_sweep.py         # 7 ISO calls

All exit 0 as of 2026-09-18. The General Liability suites (`tests/verify_*.py`)
remain the regression net for every shared-code change; nothing shared was
touched in this chunk.
