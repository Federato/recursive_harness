# Property chunk 9 — the gate

**Blanket rating, cross-cutting.** Filed 2026-09-21.

**9 of 9.** No point held open. ISO: **1 of 1 confirmed, exactly** — the
first CF chunk to match ISO on both the premium and the message set at once.

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | [`CF-CHUNK9-GOLDEN-CASE.md`](CF-CHUNK9-GOLDEN-CASE.md) — Structure A **$255**, Structure B **$510**, every intermediate (`BasicGroupIAvgRate=0.255`, `BlktBasicGroupILOIFactor` 1.172/1.039, `Detail.TotalFullValueAmount=300000`) traced to a named rule. C9-02/C9-03 traced the chain end to end for the Average AND Highest elections both |
| 2 | Every table's row count stated | ✅ | `70_chunk9_c9-04_tables_and_datadefs.py` — **12 of 12** blanket-only Rate Tables re-confirmed directly; only 2 (`BuildersRiskBlanketFactor`, `CoinsuranceFactorBlkt`) sit in this chunk's chain, the other 10 explained by direct read (stat-reporting, EQ/Flood endorsement-only) rather than assumed out of scope |
| 3 | Every state is enumerated | ✅ | `71_chunk9_c9-05_state_override_census.py` — **47 of 47**, but the census asked is different in kind from chunks 1–8's, and that difference is stated rather than glossed (see below) |
| 4 | Every `0` tested against its consuming branch | ✅ | `72_chunk9_c9-06_three_gates.py` — 3 hand-built submissions, **3 distinct field values** (`None` / `"Not Applicable"` / `""`), and only 2 of the 3 actually zero the premium |
| 5 | Every hardcoded literal key listed | ✅ | `73_chunk9_c9-07_hardcoded_literals.py` — `MUBlktRated`, `IncludedInBlkt` (5 per-form Domain Tables, not one flat switch), `"Leasehold Interest"`, `BlktTypeOfBlanketRating` (`{Average, Highest}`, the full domain), Detail `Type` (4-literal subset of a 6-value domain) — all confirmed against the Domain Tables folder, not inferred from example rows |
| 6 | Shared-name traps diffed | ✅ | `74_chunk9_c9-08_shared_name_collision.py` + `75_chunk9_c9-09_setnoneq_diff.py` — the two dispatcher names are a false alarm (pure routers, nothing to collide over); the real variation is one level down, in `SetNonEQBlanketValues`'s 5 bodies, diffed field-by-field with every difference traced to a confirmed consumer (or confirmed dead) |
| 7 | Every exclusion's endorsement record identified | ✅ | Checked directly for this chunk, not assumed from chunk 8's precedent (see below) — **blanket files none of its own.** `SetBlanketRatesAndFactors` (`CommercialPropertyStructureRules.Rule.xml`, and the Business Income/Special Class/SC Business Income equivalents) `RunRule`s the ordinary per-structure exclusion-factor rules — `SetVandalismExclFactor`, `SetSpecialTheftExclusionIndicator`, `SetOperationalUnitWindstormOrHailExclusionFactor`, `SetLimitationsOnCovForRoofSurfacingCosmeticExclFactor` — unconditionally, for every blanket-elected structure, because it re-runs the entire non-blanket rate chain first |
| 8 | The edition basis stated | ✅ | `77_chunk9_c9-11_edition_basis.py` — Oregon (the golden case) resolves to `CF_CW_20260601_V01` at every layer. Florida is a whole-book skew (its newest package declares `CF_CW_20230801_V01`), not a Detail-engine-vs-premium split — the resolver's documented two-layer design, not a defect |
| 9 | No unexplained validation message | ✅ | `78_chunk9_c9-12_message_tally.py` — **3 messages, 0 unexplained**, for chunk 9's own golden case: 2x CP 03 20 (M-001, cross-referenced), 1x CP 10 75/76 (**logged as M-002**). None of the 4 blanket-specific `DoMessage` rules fire (correctly — none of their conditions are met). **The project-wide backlog for chunks 1–8's own golden cases is untouched by this chunk and remains separately open**, per the same convention chunk 8's gate used |

---

## Point 3, reframed rather than forced

Chunks 1–8 asked "does this ONE coverage's premium sweep across all 47
states?" Blanket has no premium sweep of its own — it is a modifier five
different `SetPremium` rules read, and C9-05's census confirmed **zero of
47 states override the value-setting rules in any of the 5 groups.** The
one real override found (Special Class's dispatcher, AL/KS) is additive and
does not touch the averaging mechanism. **A 47-state premium sweep for
blanket would be re-running chunks 1–8's own sweeps with `IncludedInBlkt`
flipped** — the same rate chain, already enumerated by five different
chunks' own point-3 evidence. C9-05's override census is the right
substitute because it asks the question blanket actually introduces
(does any state rewrite the AVERAGING machinery?) rather than a question
chunk 9 doesn't add anything new to.

## Point 7, checked directly rather than assumed from chunk 8

Chunk 8's Legal Liability inherited its exclusion records because it rates
in the SAME datadef group as Building/Contents — a structural argument that
does not automatically transfer to blanket, which is a genuinely separate
rule file family (`CommercialPropertyBlanketRating*`). Reading
`SetBlanketRatesAndFactors`'s body directly (not assuming the chunk-8
pattern holds) found the actual mechanism: this rule's own name is
misleading (C9-08/`CF-CHUNK9-GOLDEN-CASE.md` §6) — it does not set blanket
rates at all. It re-runs the ENTIRE ordinary per-structure rate chain,
exclusion factors included, for every structure regardless of blanket
election, before the averaging engine ever sees a number. So blanket
inherits by re-execution, not by shared scope — a different mechanism from
chunk 8's, arriving at the same "files none of its own" answer.

---

## ISO — 1 of 1 confirmed, exactly

C9-13's original question was whether ISO confirmation is even possible for
blanket at all, given census §6 (`67_chunk9_census.py`, re-run directly for
this gate) confirms **0 of 924 STC payloads** elect `IncludedInBlkt="Yes"`
or carry any `CommercialPropertyBlanketRating*` record — ISO's own fixture
corpus has never demonstrated a blanket submission either.

That answers the FIXTURE question, not the CONFIRMATION question. Chunk 8
answered its own open cases (blanket-elected on Legal Liability, Builders
Risk with a reporting form — neither in STC either) by hand-building a RAaS
payload and calling ISO's live rating service directly
(`63_chunk8_raas.py`). The same thing is possible here, and it was tried:
[`79_chunk9_c9-13_raas.py`](../scripts/cf/79_chunk9_c9-13_raas.py) translates
C9-01's golden case (two structures, one `BlktIDNum`, `IncludedInBlkt="Yes"`
on both, `BlktRated="Yes"`/`MUBlktRated="No"` on the policy, a
`CommercialPropertyBlanketRating`/`Detail` record with `TotalLimit=300000`)
from the engine's internal Node-tree submission shape into the flat RAaS
JSON shape `raas.py` already sends.

**Correction to an assumption this chunk's own golden-case doc made**:
`CF-CHUNK9-GOLDEN-CASE.md` §8 states the regression run's RAaS script
"makes a live ISO RAaS call with no network/credentials available here."
That is not what happened when it was tried directly for this gate —
**the call succeeds; network and credentials are available in this
environment.** The doc's claim was not re-verified before being repeated
here; this gate corrects it by direct trial rather than by trusting the
prior write-up. One payload-shape lesson surfaced on the way: ISO's schema
requires `UnitNumber` as an integer, not the numeral string the engine's
own `str(BLKT_ID)` habit (carried over from every other chunk's payload
builder) produced — first call refused 400 on a type mismatch, fixed by
passing the int.

**Result: ISO rates the submission and returns exactly `$255` / `$510`,
total `$765` — the fixed engine's numbers, to the dollar.** The validation
messages match too: ISO's response carries the identical 3 messages C9-12
found (2x CP 03 20, 1x CP 10 75/76), nothing else. This is the first CF
chunk to confirm both the premium AND the message set against ISO's own
service in one call, for a submission that exists nowhere in ISO's own
fixture corpus. Response saved at
[`results/cf-raas/OR_chunk9_blanket_response.json`](../results/cf-raas/OR_chunk9_blanket_response.json).

**What this does and does not prove.** It confirms the Average election,
Building Basic Group I, two structures, against a live ISO call — the
exact shape of C9-01's golden case, nothing more. It says nothing about
`TypeOfBlanketRating="Highest"`, any other coverage form, or the EQ path
(C9-15/C9-16/C9-17's job) — those remain unconfirmed by ISO or otherwise.

---

## What chunk 9 has established

**1 · "Branch B is a stub" was wrong as a description of the code.** Every
one of the 20 `SetPremium` rules across all 5 premium groups carries a
complete, already-filed blanket formula. What was missing was input, not
code — confirmed by census §7 and proven by C9-01's fix.

**2 · The three-chunk mystery (C6-28/C7-25/C8-14) had a name, and now has a
cause proven by running it.** `SetNonEQBlanketValues` is the only rule that
ever populates `BlktCauseOfLossValue`, and it has three distinct ways to
leave it short — none of them a broken rule, all of them an unfed one
(C9-06 proved the three are genuinely different values, not one mistaken
for three).

**3 · One real interpreter gap, found and fixed with authorization.**
`ForEach @AtInputDataDef` reparented writes exactly like `@AtDataDef`,
which no chunk before this one had triggered — `SetNonEQBlanketValues`'s
temp-field writes landed on the Detail record instead of the structure.
Fixed in `gl_engine/interp/interpreter.py`/`nodes.py`; all 8 prior CF
chunks and all 16 GL suites re-verified green after it. This is the first
engine change since chunk 0.

**4 · Blanket inherits exclusion handling by re-execution, not by shared
scope** — a different mechanism from chunk 8's Legal Liability (same
datadef group) reaching the identical "files none of its own" answer
(point 7 above).

**5 · The state layer stayed quiet.** 0 of 47 states override either
value-setting rule in any of the 5 groups; the one real override (AL/KS,
Special Class dispatcher) is a pure addition.

**6 · ISO confirms exactly**, on the first live attempt this chunk actually
made — correcting a stale "no network available" assumption on the way.

## What chunk 9 has NOT established

* **C9-15 through C9-17** — Building's three "by elimination" forms
  (Basic I, Basic II, Broad) reaching the blanket formula have only been
  read on paper, not run; whether the explicit-`When`, elimination and
  plain-`Else` mechanisms produce the SAME premium for the same inputs is
  untested; SC Business Income's 2-`When` shape is unexplained.
* **C9-18 through C9-20** — `MultiPremiumAndDispersionCreditFactor`'s
  liveness on the blanket path specifically, the `IRPMFactor`/
  `PackageModFactor` level count across all 20 files (only 1 read by
  hand), and cross-coverage leakage from a blanket election onto a
  sibling item are all unasked.
* **C9-21 through C9-22** — the three shared instruments
  (`04_shared_names.py`, `05_exclusion_records.py`,
  `08_hardcoded_literals.py`) have not been re-run against the seventh
  DataDefGroup this golden case newly populated
  (`CommercialPropertyBlanketRatingDetail`), and chunks 1–8's existing
  golden cases have not been re-run to confirm they are unmoved by the
  interpreter fix beyond the one bulk regression pass already recorded in
  `CF-CHUNK9-GOLDEN-CASE.md` §8.
* **19 of 20 premium files, and the Highest path's full validation.** This
  gate closes the CORE MECHANISM — Building Basic Group I, the Average
  election, one golden case, now ISO-confirmed. It does not close the
  other 19 premium files' own blanket branches or the Highest election
  end to end; that is C9-15/C9-16/C9-17's job, not proven here.
