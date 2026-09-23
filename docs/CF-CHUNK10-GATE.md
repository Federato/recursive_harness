# Property chunk 10 — the gate

**Earthquake, Building's plain percentage-deductible path.** Filed 2026-09-22.

**9 of 9.** Gate Group 1 closed points 1-5 and 8-9; Gate Group 2 closed the
remaining two — points 6 and 7 — the same day. No engine gap found on any of
the 9 points.

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | [`CF-CHUNK10-GOLDEN-CASE.md`](CF-CHUNK10-GOLDEN-CASE.md) / [`85_chunk10_golden_case.py`](../scripts/cf/85_chunk10_golden_case.py) — Building, Basic Group I, one structure, EQ elected on the plain percentage-deductible Endorsement. Every intermediate (`EQBaseRate=0.009`, `EQRate=0.009`, `AdjustedEQRate=0.009`, `EQClassToUse=A1`, `EQDeductibleFactor=0.68`, `FinalEQRate=0.006`) traced to a named rule and table row. **Match, no engine gap** — the first CF chunk in this project's own run where the hand derivation and the engine agreed on the first try. |
| 2 | Every table's row count stated | ✅ | [`86_chunk10_c10-02_tables.py`](../scripts/cf/86_chunk10_c10-02_tables.py) — **all 66 of 66** EQ-named Rate Tables re-confirmed directly (row counts, state filings, header-only/carrying-rows split exactly matching the opening census). Classified into 4 buckets, not 2: 29 in the core chain, 22 in the sub-limit/flat-dollar-deductible chain, 3 out of scope (a different, unbuilt CF coverage — Ordinance or Law — plus one policy-level stat code), 12 dead. A fifth consumer population the census's filename scan could not see (5 OTHER optional coverages with their own independent EQ rider) surfaced here for the first time |
| 3 | Every state is enumerated | ✅ | [`87_chunk10_c10-03_state_census.py`](../scripts/cf/87_chunk10_c10-03_state_census.py) — **47 of 47**, both layers, each re-confirmed exactly against the opening census's own claim (Building 10, Contents 9, Special Class 7, Business Income 5, SC Business Income 0) — with the specific rule(s) each state overrides now named, and the two layers (wrapper-file package existence vs. EQ-engine-rule override) confirmed genuinely different questions, not the same one asked twice |
| 4 | Every `0` tested against its consuming branch | ✅ | [`88_chunk10_c10-04_zero_cases.py`](../scripts/cf/88_chunk10_c10-04_zero_cases.py) — 7 hand-built submissions. Two genuinely distinct tiers of zero confirmed by running: `"No Coverage"`/`"Not Applicable"`/absent all collapse to "Endorsement never created" (`Premium=None`); unfiled `EQClass`/blank `BCEG`/blank `EQSprinklerLeakageOnly` all collapse to a DIFFERENT single outcome ("Endorsement created, computed to `$0`"). A 7th case (`SprinklerSystem` blank) re-confirmed to be NOT a zero case at all — a silently wrong nonzero `$7` |
| 5 | Every hardcoded literal key listed | ✅ | [`89_chunk10_c10-05_hardcoded_literals.py`](../scripts/cf/89_chunk10_c10-05_hardcoded_literals.py) — `EQCovIndicator`'s 4-value domain, the 6 `CovType` literals EQ's `SetPremium` branches on, all checked against the Domain Tables folder directly. One new structural gate found while reading (3 `NotExist` checks re-confirming the 4 `AttachForm*` variants' mutual exclusion one rule downstream of attachment) |
| 6 | Shared-name traps diffed | ✅ | [`92_chunk10_c10-06_shared_names.py`](../scripts/cf/92_chunk10_c10-06_shared_names.py) — the 9 EQ-engine rule names' uneven presence across the 5 parent files is a REAL structural difference in every case, not one hidden C8-05/C8-16-style collision. Special Class and Contents each drop one distinct concept their own table doesn't need (a per-location deductible tier; a class-normalization step); Business Income and SC Business Income drop six via two confirmed mechanisms — an ancestor-copy of the Building/Special-Class structure's already-computed `EQBaseRate`, and a wholesale substitution of the deductible/coinsurance chain by a TIME-ELEMENT factor (`EQFactor`) unique to income coverage |
| 7 | Every exclusion's endorsement record identified | ✅ | [`93_chunk10_c10-07_exclusion_records.py`](../scripts/cf/93_chunk10_c10-07_exclusion_records.py) — **none of the 5 groups files its own record.** `CyberIncidentExclusionFactorEQ`/`...COLExcptnsFactorEQ` are each declared exactly ONCE at the policy-level `CommercialProperty` ancestor, testing a record filed at that same policy level, read identically by all 5 groups' own family-tagged files. Confirmed dynamically on Building and a freshly built Contents submission — both default to the same `1.0` no-op from the same shared field |
| 8 | The edition basis stated | ✅ | [`90_chunk10_c10-08_edition_basis.py`](../scripts/cf/90_chunk10_c10-08_edition_basis.py) — Oregon (the golden case) resolves to `CF_CW_20260601_V01`, the current countrywide edition, at every layer. **3 of the 10 EQ-overriding states sit on an older declared parent — CA, FL, RI** (not just FL, chunk 9's own single data point) — each a whole-book jurisdictional fact predating and unrelated to Earthquake, confirmed internally consistent (no Detail-vs-premium split) by the resolver's own documented two-layer, no-carry-forward design |
| 9 | No unexplained validation message | ✅ | [`91_chunk10_c10-09_message_tally.py`](../scripts/cf/91_chunk10_c10-09_message_tally.py) — **2 messages, 0 unexplained**, for chunk 10's own golden case: both already logged by chunk 9 (M-001 CP 03 20, M-002 CP 10 75/76), neither EQ-caused. All **104** corpus-wide `DoMessage` rules that reference an EQ field or "Earthquake" surveyed by theme and confirmed inapplicable to this submission's own field values, not merely absent from the observed output. **Cross-check against a real ISO fixture** (`STC_CP000020296.json`) found it exercises the FLAT-DOLLAR-DEDUCTIBLE variant with `CauseOfLoss="Special"` and `BCEG="Ungraded"` — confirming the golden case's own shape is the shortest reachable chain, not the most representative one |

---

## Points 6 and 7, closed by Gate Group 2

Gate Group 1 deliberately left C10-06 (shared-name adjudication) and C10-07
(exclusion-record identification per datadef group) open rather than skip
them silently — both surfaced real, unresolved questions in the opening
census. Gate Group 2 ran both to a clean adjudication the same day:

* **C10-06** — the census found the 9 EQ engine rule names are NOT declared
  identically across the 5 parent files (Building 9/9, Special Class 8/9,
  Contents 7/9, Business Income and SC Business Income 3/9 each). Reading
  every group's actual rule bodies (`92_chunk10_c10-06_shared_names.py`),
  not just name presence, found every gap is a REAL structural difference —
  none is the C8-05/C8-16 hidden-collision shape (a different rule, same
  concept, missed by a name-only census). Special Class has no per-location
  deductible-tier concept at all; Contents' own base-rate table is keyed on
  raw `EQClass`/`EQGrade` rather than a normalized class code, so it never
  needed the normalization step; Business Income and SC Business Income
  read their own structure ancestor's already-computed `EQBaseRate`
  directly (an ancestor-copy, the same shape already logged for
  Ded/Territory/SubStd) and replace the deductible/coinsurance chain
  entirely with a time-element factor (`EQFactor`) unique to income
  coverage.
* **C10-07** — `CyberIncidentExclusionFactorEQ`/`...COLExcptnsFactorEQ` were
  confirmed (C10-01) to default to `1.0` absent an exclusion record for
  Building; whether the other 4 groups file their own record was untested.
  `93_chunk10_c10-07_exclusion_records.py` found the question itself
  dissolves on inspection: both factors are declared exactly ONCE, at the
  policy-level `CommercialProperty` ancestor all 5 groups descend from, not
  once per group. There is one record, one rule, one shared value — no
  group files its own, and none needs to. Confirmed by a corpus-wide
  write/read census spanning all 5 groups' own family-tagged files, and by
  two independent dynamic runs (Building, and a freshly built Contents
  submission) landing on the identical shared value.

Both closures found the same underlying shape: EQ's population-uneven
rule/field census (chunk 10's own finding 6, and this project's standing
C8-05/C8-16 shared-name lesson) kept surfacing real, nameable mechanisms —
ancestor copies, a different rating concept, a policy-level rather than
per-coverage exclusion — never a silently-missed duplicate. No engine gap on
either point.

---

## Point 2, reframed rather than just re-counted

The opening census asked "which of the 66 tables sit in the chain vs. are
out of scope," implying a two-way split. Direct consumer-search (not
filename search) found a THIRD population the census's own methodology
structurally could not see: five other optional CF coverages (Ordinance or
Law, Outside Signs, Radio/TV Antennas, Builders Risk Renovations, and the
project-tracked-as-blocked Unmanned Aircraft) each file their own
independent EQ rider, sharing several of the same 66 tables with Building's
own chain without any of those coverages' rule files being named
`*Earthquake*`. This does not change which 66 tables exist or their row
counts — it changes the shape of "who reads them," which the opening
census's filename-first approach (`Rules/*Earthquake*`) was never going to
surface on its own.

---

## Point 8, generalized rather than re-derived from scratch

Chunk 9's own C9-11 found Florida on an older declared countrywide edition
than Oregon and treated it as a one-state finding, because blanket's own
override population never touched CA or RI. EQ's override population is
wider (10 states vs. blanket's handful), so the SAME check, re-run against
EQ's own state list, surfaces two more skewed states the earlier chunk had
no reason to look for. The mechanism is unchanged — the resolver's
documented two-layer, no-carry-forward design, not a defect — but the
population it was tested against grew, and the count grew with it (1 → 3).

---

## What chunk 10's gate has established

**1 · The golden case matched on the first try.** Unlike chunk 9's own
golden case (a real interpreter gap that needed an authorized fix), C10-01
found the engine already correct for the plain percentage-deductible path —
nothing here needed a fix, and nothing here is patched, per this group's own
standing instruction not to touch engine code even if a gap had been found.

**2 · The 66-table population is fully classified, and the classification
surfaced a consumer population the opening census's filename search
structurally could not find** — five other coverages' own independent EQ
riders, sharing tables with Building's chain.

**3 · The state layer holds up exactly as the census claimed**, at both
layers, with the specific overridden rule now named per state rather than
just a count.

**4 · Two genuinely different tiers of "zero" exist on the EQ path**, the
same two-tier shape C9-06 found for blanket — distinguishable by whether the
Endorsement record is created at all, not by the numeric premium alone.

**5 · The hardcoded-literal population is small and fully filed** — every
literal `SetPremium` tests is a legal domain value; the one value it never
tests directly (`"Yes, Not Included in Blanket"`) is the implicit
fall-through default, not a gap.

**6 · The edition-skew finding from chunk 9 generalizes, with a bigger
population turning up more skewed states** — a methodology point as much as
a substantive one: re-running the same check against a wider override
population is itself informative.

**7 · The message set is clean, and the ISO fixture population — unlike
chunk 9's blanket, which had none — gave a real cross-check.** The one real
fixture pulled shows the golden case's own shape (plain form, Basic Group I,
numeric BCEG) is the SHORTEST reachable chain through the EQ engine, not the
most representative submission ISO's own corpus actually files.

**8 · Every EQ-engine rule-name gap across the 5 parent files is a named,
real mechanism, not a hidden collision.** Special Class and Contents each
drop exactly one concept their own table doesn't need; Business Income and
SC Business Income drop six via an ancestor-copy of the structure's own
`EQBaseRate` plus a wholesale substitution of the deductible/coinsurance
chain by income coverage's own time-element factor.

**9 · EQ's Cyber-exclusion factors are a policy-level election, not a
per-coverage one.** Unlike the ordinary chain's own exclusions (each of the
5 groups files its own vandalism/theft/windstorm record), EQ's
`CyberIncidentExclusionFactorEQ`/`...COLExcptnsFactorEQ` are declared once,
at the shared `CommercialProperty` ancestor, and read identically — same
value, same default — by every group.

## What chunk 10 has NOT established

> **Superseded 2026-09-22.** Of the 7 non-gate tasks this bullet lists as
> untouched, **6 have since closed** — C10-15 through C10-19 (Groups 4 and 5)
> and **C10-21** (the chunks 1–9 regression, closed CLEAN; see the addendum at
> the end of this file). **Only C10-20, the wider 69-fixture sample, is still
> open.** The paragraph below is kept as the record of where the gate stood
> when it was filed, not as current status.

* **C10-15 through C10-21** — 7 non-gate tasks remain untouched: all-5-groups
  reachability on a real submission at the 27-touching-file Special Class
  level (C10-15/C10-18), the Legal Liability and Non-Owned Trailers EQ
  branches (C10-16/C10-17 — Group 3's C10-10 read of Non-Owned Trailers'
  own file already found it mirrors Building's top-level 3-way `Choose` in
  miniature, a lead for C10-17 to pick up), the sub-limit/flat-dollar-
  deductible trace (C10-19), the wider 69-fixture sample (C10-20), and the
  chunks-1–9 regression check (C10-21).
* **ISO RAaS confirmation** — not attempted by any group yet. Chunk 9
  confirmed its own golden case against a live ISO call; chunk 10's golden
  case has not been tried against ISO at all.

### Addendum, filed by Group 3 (C10-10 through C10-14, closed 2026-09-22)

**The other 4 premium groups' own EQ chains are now CONFIRMED, not just
read.** `95_chunk10_c10-11_all_groups_chain.py` built one real submission
per group (Contents, Business Income, Special Class, SC Business Income),
hand-derived the expected premium from filed table rows before running, and
matched exactly for all four (**$5, $5, $6, $5** respectively, ordinary
premiums unmoved). The bullet this addendum replaces — "every point in this
gate that ran a submission ran it against Building only" — no longer holds;
it was true only through the 9-point gate itself, not after this group.

Two NEW silent-but-correctable submission-shape traps surfaced only by
running Contents, neither visible to C10-06's rule-body-only read:
`SetEQClass` is a bare unguarded ancestor-copy from the Structure (a value
set directly on the Personal Property record is overwritten), and four of
Contents' own "local" factor rules (`SoftStoryModificationFactor`,
`EQSprinkleredRiskFactor`, `BldgHeightFactor`, `BCEGEQFactor`) are ALSO
ancestor-copies of the Structure's values. Also confirmed this pass:
`EQClass`/`EQTerr` are live at runtime, not just structurally present
(C10-12); all 12 "dead" EQ tables are genuinely dead by both a
`MatrixFromConstant`-alias check and a corpus-wide transitive-`RunRule`
check, not just a single-hop regex (C10-13); EQ's separation from the
ordinary IRPM/PackageMod/Deductible/Coinsurance/LOI chain holds for all 5
groups' own `SetPremium`, not just Building's (C10-14); and the census's
"thin wrapper" description of the 97-file wrapper population is confirmed
for the majority but is an oversimplification for 9 of 19 files read in
full — Peak Season, Non-Owned Trailers and Value Reporting Form each
re-run a multi-branch `Choose` rather than reading one value; several
riders read INTERMEDIATE EQ factors or compute an INCREMENTAL premium
rather than the terminal rate; and the Earthquake Inception Extension has
no premium logic at all (C10-10). No engine gap on any of the 5 points.

### Addendum, filed by Group 4 (C10-15 through C10-18, closed 2026-09-22)

**The reachability map is now closed for every angle this gate's own "What
chunk 10 has NOT established" section named.** C10-15's remaining open
angle — EQ's own BLANKET branch, deliberately left untested by both the
golden case and C10-11 — is now run for real (a 2-structure Building
blanket, $6/$12, genuinely dispersed) and shares the exact base-rate chain
the plain golden case proved. Two traps found only by running: a
single-structure blanket computes the same premium by hand but ISO's own
validation layer refuses it (*"Blanket Rating requires 2 or more risks to
be valid"*) — the same OI-99 shape the golden case's own gate already
logged, now with a concrete minimum-viable-case number attached; and a
second Detail-level field, `EQCauseOfLossIncludedInBlkt`, gates two
messages neither the census nor any prior chunk-10 task named.

**Legal Liability's EQ branch (C10-16) is confirmed to SHARE fields with
chunk 8's own ordinary chain, not duplicate them.** `LegalLiabilityFactor`/
`LegalLiabAddlInsurableIntFactor` are written by exactly one rule each,
unconditional of any EQ election, and EQ's own `SetPremium` reads them
directly — run for real on the SAME structure as chunk 8's own $60 case:
EQ premium $2, ordinary $60 unmoved, no collision.

**Non-Owned Trailers (C10-17) is resolved as a CONTENTS-side coverage, not
a Building-side one** — a fact neither the census nor C10-10's own read of
this file (which flagged the 3-way `Choose` shape but not the attachment
point) established. It reads Contents' own EQ chain, not Building's or its
own, and gates on a real filed threshold ($5,000 CW) no other EQ file in
the population has.

**Special Class's 27 files (C10-18) are confirmed to split across TWO
sibling premium groups (Special Class and SC Business Income), not one** —
8 core, 19 wrapper, 5 of the 19 carrying their own small non-EQ-named
factor lookup on top of the shared value.

No engine gap on any of the 4 points.

### Addendum, filed by Group 5 (C10-19, closed 2026-09-22) — a real engine
### gap found, THEN FIXED same day, user-authorized; the gate itself stays
### filed at 9/9 (C10-19 is a non-gate cross-cutting task)

**The plain flat-dollar-deductible path (CP 10 28) is confirmed to work
and to be genuinely distinct from C10-01's own plain percentage-deductible
path** — same base risk, hand-derives and runs to **$8** (vs. $6),
diverging only at `SetEQDeductibleFactor`'s Lookup source (a 5-key table
that adds a derived `EarthquakeTotalPropertyValue` range dimension the
percentage path never touches). `EQCoinsuranceFactor`/`AdjustedEQRate` are
confirmed shared identically across all four `EQCauseOfLossForm` variants
— no variant skips coinsurance.

**A second case, actually attempting the sub-limit + flat-dollar-deductible
form (CP 10 29), surfaced a real, reproducible ENGINE GAP** —
[`103_chunk10_c10-19_sublimit_flatdeductible.py`](../scripts/cf/103_chunk10_c10-19_sublimit_flatdeductible.py).
All 13 `EQSubLimit*FlatDeductibleFactor` tables (confirmed on 4 of the 13
by direct header read, the same shape on all of them) carry a
DOUBLE-banded-range key — `EQSubLimitPct_From/ToLessThan` AND
`TotalPropertyValue_From/ToLessThan` simultaneously — which the
interpreter's own `_lookup_banded` (`gl_engine/interp/interpreter.py`)
explicitly refused, raising `InterpretError` and citing its own
documented one-range-per-table contract. **The CP 10 29 sub-limit path was
confirmed CURRENTLY UNREACHABLE end to end through this engine** — not
merely untested, and not a one-table quirk: every one of the 13 tables the
build order's own "sub-limit and flat-dollar-deductible variants" callout
points at shares this exact blocking shape. Per this group's own standing
instruction at the time, this was reported, not patched.

**User-authorized fix, 2026-09-22 — the gap above is now CLOSED.**
`_lookup_banded` (`gl_engine/interp/interpreter.py`) was generalized to
handle any number of key ranges: exactly one range, named by a
`ValueCols/rt:Range@RangeKeyCol` attribute, interpolates; every other range
is a plain containment filter, resolved by name rather than position. A
corpus-wide scan (independent of the count above) confirms the population
is exactly 28 table names with 2 key ranges (13 `EQSubLimit*
FlatDeductibleFactor`, 7 live `PropertyRateModificationFactors1`-`7`, 1 live
`HeatingOilTankServingResidentialPropertiesIndicator`, and 7 confirmed-dead
`PropertyRateModificationFactor1`-`7` left untouched). This task's own CP 10
29 case (`103_chunk10_c10-19_sublimit_flatdeductible.py`) now runs to
completion — `EQDeductibleFactor=1.376`, `Premium=$6`, hand-derived against
the filed CSV and matched exactly. Full regression: 16/16 GL `verify_*.py`
suites and 107/120 CF `scripts/cf/*.py` scripts exit clean, with all 13
non-zero exits confirmed pre-existing (CLI-usage, a documented
engine/ISO disagreement report, and a stray-Excel-process COM environment
issue on scripts that target `CFRater1.02.xlsb`, never the forbidden
`CFRater1.01.xlsb`) and unrelated to this change. Full write-up:
[`CF-ENGINE-FIX-BANDED-LOOKUP.md`](CF-ENGINE-FIX-BANDED-LOOKUP.md).

This changes what chunk 10's own "What has NOT established" section (above)
should say about C10-19: it is no longer simply untouched, and no longer an
open engine limitation either — it is CLOSED and FIXED. The golden case's
own $6 (C10-01), this task's own $8 (CP 10 28), and now the sub-limit case's
own $6 (CP 10 29) are three of the four `EQCauseOfLossForm` variants
confirmed to rate correctly through this engine; the fourth (CP 10 45, the
percentage-based sub-limit form, reading a wholly different 6-table family)
remains untested by this task and is an open item for whoever next touches
Earthquake sub-limits.

---

### Addendum, filed by C10-21 (closed 2026-09-22) — the chunks 1–9 regression

**CLEAN. Nothing chunks 1–9 established moved under the `_lookup_banded`
fix.** Run as a reproducible, self-testing harness
([`104_chunk10_c10-21_regression.py`](../scripts/cf/104_chunk10_c10-21_regression.py))
rather than a hand sweep — because
[`CF-ENGINE-FIX-BANDED-LOOKUP.md`](CF-ENGINE-FIX-BANDED-LOOKUP.md) §5's own
regression claim ("every earlier chunk's own golden-case script all re-ran to
their previously-recorded figures") was prose with nothing behind it that
anyone could re-run. It is now a command.

**51 scripts, three independent checks each**, because exit code alone only
proves a script agreed with itself:

1. **Exit code 0.**
2. **A failure-marker scan of the output** (`MISMATCH`, `RAISED`,
   `Traceback`, `<< expected`) — so a script that *reports* a disagreement
   without exiting non-zero is still caught. This project has been bitten by
   the inverse (`63_chunk8_raas.py` exits non-zero by design); the reverse
   blind spot is the one a bare exit-code sweep has.
3. **For the 10 golden cases, every dollar figure recorded BEFORE today**
   (from `CF-START-HERE.md` and `CF-CHUNK9-GOLDEN-CASE.md`), matched as a
   standalone token. This is what makes it a regression and not a smoke test:
   it pins each script to the number written down previously, not to whatever
   a fresh run happens to be internally consistent about.

**Result** — all 10 chunk 0–9 golden cases reproduce every documented figure
(261/263/288 · 261+32 · 16/54 layering to 309/347 · 223/24/16/137 ·
112/13/23/47 · 66/209/14/44 · 39/123/23/47 · 60/7/4/12 and 132/15/11/93 ·
255/510); all 25 machinery scripts and all 16 GL `verify_*.py` suites clean.

**Two harness defects found and fixed before the result was trusted — both
would have been false alarms, and both are worth recording:**

* **`CF-START-HERE.md`'s own chunk-3 line is misleading.** It reads "16 / 54,
  layering on Basic to **293** / 309 / 347". **293 is not a chunk-3 figure at
  all — it is the Basic-only subtotal, 261 + 32, which is chunk 2's number.**
  `15_chunk3_golden_case.py` correctly prints only the two cumulative totals
  it is responsible for (309 and 347). The first run flagged 293's absence as
  a regression; reading the script's own output is what settled it.
* **The three zero-case scripts legitimately print `RAISED`.** A predicted
  raise — the null-premium guard firing on an absent `Limit`, contract 12.3 —
  **is their finding**, not a failure. Rather than granting them a blanket
  amnesty, the marker was replaced for those three by a *positive*
  requirement: each must still print its own "All 7 cases match their
  derivation" line. All three do, and the `--selftest` proves the replacement
  actually bites (a zero-case script that raises and then *omits* the
  match-line is still caught).

**The harness tests its own denominator.** `--selftest` plants 7 defects — a
non-zero exit, a `MISMATCH`, a missing documented figure, a **substring
near-miss (`1261` and `261.5` must NOT satisfy `261`)**, a zero-case script
missing its match-line, and two clean cases that must pass — and fails if any
is reported green. This is CF-START-HERE.md's own standing lesson ("a check
that finds nothing needs its denominator tested too") applied to the
regression check itself, which is the one check in the project that has
never had it applied before.

**Scope is printed, not silently narrowed.** The harness prints what it does
NOT run and why: the 47-state sweeps (minutes each, touch no banded lookup,
green 2026-09-18), the 6 live-ISO RaaS scripts (a regression of *our* engine
must not depend on a network round trip), `07_diagnose_message.py` (requires
CLI arguments), and the separate Excel-COM rater-streamlining workstream
(not this engine's test surface, and RULE #0 applies).

**Correction filed in the same turn:** `CF-CHUNK10-TASKS.md` and
`CF-BUILD-STATUS.html` both said "17 of 21 tasks" when C10-01 through C10-19
were already all ✅ — the real figure was 19 before this task, and is **20 of
21 now**. Only **C10-20** remains.

---

### Addendum, filed by C10-20 (closed 2026-09-22) — chunk 10 is CLOSED, 21 of 21

**The census's own fixture arithmetic was wrong in three places, and C10-20
found all three by parsing what the census had only regexed**
([`105_chunk10_c10-20_fixture_sample.py`](../scripts/cf/105_chunk10_c10-20_fixture_sample.py)).
It does not sample. It reads all 364 CF payloads.

**1 · The denominator is not 924.** `C:/Projects/ISO_ERC_Files` holds **560
General Liability payloads alongside 364 Commercial Property ones**, and the
census scanned the root and summed them. `EQCovIndicator` is a CF field, so
the census's "364 of 924 carry the field at all" **is not a coverage
statistic — it is the CF payload count restated**. The 560 GL payloads could
never have carried it. The real election rate is **69 of 364 = 19%**, not
7.5% of 924.

**2 · "69" counts Structures, not the corpus.** The census matched ONE
`EQCovIndicator` per file with `re.search`, which returns the first hit. A CF
payload carries the field on up to **10 different record types**. The
headline survives by luck — the Structure record happens to come first — but
the corpus holds **149 electing records**, not 69. The 80 the regex could not
see: 66 Personal Property, 11 Business Income, 1 Special Class, 2 auxiliary
riders.

**3 · Two different fields share the name `EQCovIndicator`.** The 4 premium
groups use the 4-value domain C10-05 adjudicated against
`DomainEQCovIndicatorBldg`. The auxiliary riders — Utility Services, Radio/TV
Antennas, Outside Signs, the Tenants-Policy building-glass record — carry a
plain **`Yes`/`No`** domain instead. C10-05's adjudication is correct and
never claimed to cover these; they are part of the 5-coverage consumer
population C10-02 found the filename census structurally could not see. The
census's "all 69 sampled say `Yes, Not Included in Blanket`" is true of the
premium groups and false of the corpus.

#### What the 69 electing structures actually exercise

| Dimension | Reality |
|---|---|
| States | **28 of 47** elect on at least one structure — not the census's "at least 8". The **19 that never do include CA, FL, NY, OR, PR, TX** |
| `CovType` | **Building, 69 of 69.** Nothing else, ever |
| `CauseOfLoss` | **Special 68, Broad 1 — zero Basic Group I** |
| Form variant | **CP 10 28 flat-dollar ×65 · CP 10 29 sub-limit ×3 · CP 10 40 plain ×1 · CP 10 45 ×0** |
| `EQTerr` | filed on the **Location**, not the Structure; **57 of 69 sit at territory "1"** |
| `EQDeductible` | a flat dollar amount in 65 of 69 (`5,000` ×29, `2,500` ×24, `1,000` ×10) |

#### The result that matters

**Three of the golden case's four coordinates are exercised by ZERO
fixtures** — Oregon (0 of 69), Basic Group I (0 of 69), and its plain CP 10
40 form (1 of 69) — and the combination by none. C10-09 suspected exactly
this ("the golden case's own shape is the SHORTEST reachable chain, not the
most representative one"); C10-20 quantifies it. **The gate stands at 9 of 9
on a submission shape ISO's own corpus never sends.** That is not a defect in
the gate — a golden case is chosen to be traceable by hand — but it is the
honest statement of what 9 of 9 covers.

**C10-19's fix was load-bearing for real ISO traffic.** CP 10 29, which was
confirmed *unreachable through this engine* until this morning, has **3 real
ISO fixtures** (MT, WY×2). The fix closed a path ISO actually ships
submissions for, not a theoretical one.

**Two gaps the corpus cannot close, recorded rather than papered over:**

* **EQ blanket has no fixture, ever.** `"Yes, Included in Blanket"` appears
  **0 times in 364 payloads**. C10-15 reached that branch on a hand-built
  2-structure case and proved it rates ($6/$12), but chunk 9's "no ISO
  fixture, ever" problem is **inherited by EQ's blanket branch specifically**.
  The census's claim that chunk 10 "does not face chunk 9's problem" holds
  for the plain chain and fails here.
* **The high-hazard states are the thinnest evidence in the book.**
  California files 8 CF payloads and elects Earthquake in **0**; Alaska 6 and
  1. Whatever the 69 prove, they do not prove that the jurisdictions where
  Earthquake actually matters rate correctly.

**One self-correction, recorded in the script itself:** a first pass read
`EQTerr` off the Structure record and concluded it was never populated by any
fixture — which, given C10-12 proved `EQTerr` moves the premium from $6 to
$20, would have been a serious finding. It is filed one level up, on the
Location, and is populated on all 69. Wrong level, not missing data.

**Chunk 10 closes here: 21 of 21 tasks, gated 9 of 9, one engine gap found
and fixed.**
