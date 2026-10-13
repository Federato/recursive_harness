# Property chunk 0 — foundation build spec

**Written 2026-09-17.** Chunk 0 of [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md),
specified file by file. **This is the spec, not the authorization — no code is written until you
say so.**

**Decision recorded 2026-09-17:** the CF build **extends the existing interpreter**, it does not
fork it. The evidence below was gathered after that decision and supports it more strongly than the
argument that produced it.

Source-of-truth order for every claim here and in every chunk that follows:

1. **ERC** — the filed machine-readable corpus. The only thing that *sources* a value.
2. **Commercial Lines Manuals** — confirms, never sources. A manual that disagrees with ERC is a
   finding to write down, not a value to use.
3. **CFRater** — a smoke comparator only, and read through the extracted Supporting Tables `.xlsx`
   and the `Excel_Rater_*` tracing docs in `CF_Algorithm/`. **The live `CFRater1.01.xlsb` is not
   opened.** Nothing in chunks 0–2 needs it, and it already carries ~30 logged divergences
   (`Rater_Simplifications_Backlog.md`) that make it evidence about itself, not about ISO.

---

## 1 · The operator census — run, not planned

Step 0b of the build order, executed. Method: every `<rul:*` element in **all eight** CF edition
folders under `C:\Projects\ISO_ERC_Files\CF`, counted; the same over the GL corpus; the two diffed
against the 51 node names actually registered in `gl_engine/interp/nodes.py`.

Enumerated, not sampled. The population is the corpus, not a search result.

| | Count |
|---|---|
| Distinct `rul:` element names, CF corpus (all editions) | **60** |
| Distinct `rul:` element names, GL corpus | 58 |
| Evaluator names registered in `gl_engine/interp/nodes.py` | 54 |
| In CF, absent from GL | **5** |
| In GL, absent from CF | 3 (`Concat`, `Length`, `PadLeft`) |

> **Corrected 2026-09-17, during the build.** This table first read *51 registered*, and derived it
> as 58 − 7. Both were wrong: the count was taken with a regex that captures only the first name on
> each `@node(...)` decorator, and `@node("Test", "Then", "Else", "Otherwise")` registers four.
> The registry holds **54**, read from `len(EVAL)` rather than from a grep. The four names it does
> not hold are `Rules`, `Rule`, `MetaData` and `MetaDataCode` — containers that hold the program
> rather than being evaluated in it. 58 − 4 = 54, exactly.

The registered set is GL's vocabulary with nothing left over, which is why the diff below is the
whole of the interpreter work. After the five additions the registry holds 59, and every element
name in the CF corpus is handled except those same four containers.

### 1.1 · The five additions

Counted **per edition**, because a corpus-wide total hides whether an element is live or retired:

| Element | 2019 | 2020 | 2022 | 23v1 | 23v2 | 23v3 | 23v4 | 2026 | Needed by |
|---|---|---|---|---|---|---|---|---|---|
| `rul:Power` | 2 | 4 | 2 | 2 | 2 | 2 | 2 | **2** | Chunk 11 (Leasehold) |
| `rul:LastNonNull` | 0 | 3 | 0 | 1 | 0 | 1 | 2 | **3** | Chunk 12 |
| `rul:Custom` | 0 | 0 | 2 | 0 | 2 | 2 | 2 | **2** | Chunk 12 (Builders Risk) |
| `rul:Null` | 12 | 3 | 0 | 20 | 0 | 0 | 0 | **0** | retired |
| `rul:FromList` | 0 | 6 | 2 | 2 | 4 | 4 | 0 | **0** | retired |

> **Corrected 2026-09-17, during the build.** This section first said *"one of these moves earlier
> than the build order assumed — `rul:Null` is in the Structure rules, which is chunk 1, so it has
> to land in chunk 0 or chunk 1 fails on its first golden case."* That was wrong, and wrong in the
> way this project's own rule #1 warns about: the 35 uses were a total across all eight editions,
> and the Structure-rules uses are all in the **20191201 and 20201201** packages. `rul:Null` is
> **retired** — zero occurrences in the entire current edition folder. Chunk 1's golden case never
> reaches it, and it did not.
>
> The claim was checked per edition only because the number looked load-bearing. An aggregate count
> across editions is the same shape of error as an aggregate across states.

`Null` and `FromList` are still handled, because the engine resolves by as-of date and an as-of
before 2022-10 lands on an edition that files them.

**`rul:FromList` is not an operator and is refused, with the reason recorded.** It is a loop-variable
binder: a `ForEach` carrying no `@AtDataDef`, whose first child names a `@Param` and holds a
`GetList` of the values to iterate. Supporting it means extending `ForEach`'s iteration model to a
second source — a change to an evaluator GL shares — and it is retired and reachable only from
Blanket rating (chunk 9). It gets built when that chunk needs it, against that chunk's evidence.

**`rul:Custom` is not a node and should not be written as one.** It is a foreign-function call into
a .NET assembly:

```
<rul:Custom Type="integer" AssemblyName="Mscl.RuleBook.Runtime"
            Namespace="Mscl.RuleBook.Runtime.RuleSet.Custom.DateFunctions"
            ClassName="DateFunctionManager" MethodName="GetLeapDays"
            ResultMode="SingleResult">
```

All 10 uses call the same method — `GetLeapDays`, and nothing else in either corpus. That is a host
function the engine would have to *reimplement*, and reimplementing a leap-day count from its name
is exactly the kind of guess this project's contract forbids. **Recommendation: defer.** Register
`Custom` as known-and-refused so it raises a named error instead of an "unknown node", and open it
as a backlog item scoped to Builders Risk. It blocks nothing before chunk 12.

### 1.2 · The shared-element divergence check — clean

Additions are safe on their own terms: GL's corpus contains none of those five elements, so
registering them cannot change a GL rating. The actual risk is a **shared** element that means
something different in CF — this project's own "same name is a question" rule, applied to the rule
language instead of to datadefs.

Checked by diffing the attribute vocabulary of each shared element between the two corpora:

| Element | Result |
|---|---|
| `Round`, `Convert`, `Locate`, `Product`, `Choose`, `FirstNonNull`, `ForEach` | Identical attribute sets in both corpora |
| `Lookup` | **CF carries `ToDataDef`; GL never does** — the only difference found |
| `ResultMode` values | `FirstResult`, `SingleResult` in both. No CF-only value |
| `OutputAction` values | `Append` in both. No CF-only value |

**The `Lookup` difference needs no code.** `ToDataDef` is applied generically for *every* node in
`gl_engine/interp/interpreter.py`, after the evaluator returns. A CF `Lookup` that writes its result
to a datadef already works.

> **This check passed and was still not enough — corrected 2026-09-17.** It concluded *"the
> interpreter change is five new evaluators and no change to any existing one."* Building chunk 1
> found **three** further CF/GL divergences, none of which an attribute-vocabulary diff could ever
> have surfaced, because none of them is expressed in an attribute:
>
> | Found | Evidence | Where GL stands |
> |---|---|---|
> | A key `Range` is not always the LAST key column | CF: 19 table names declare one mid-list — `DeductibleFactor` is `StateCode, Deductible, Range(Limit), CauseOfLossDeductible` | GL: 0 of 218 definitions. The band was read as `keys[-1]` |
> | `Type="boolean"` is a sixth declared type | CF files it 9,228 times; only `true`/`false` | GL files `long` (1,101) and never `boolean`. CF never files `long` |
> | `And`/`Or` may take a `ForEach` operand — a quantifier over the iteration | CF: 317 `Or`, 52 `And` | GL: 0 of 58,752. A `Multi` in a condition was a hard failure |
>
> Each was caught by a raise rather than by a wrong number, which is the doctrine working. But the
> first one is the warning: `DeductibleFactor`'s trailing key is the string `'Basic Group I'`, so
> misreading the third key as the fourth threw. **On a table whose trailing key happened to be
> numeric it would have matched the wrong band and returned a plausible factor.** The lesson is that
> a diff of attributes is not a diff of semantics, and structure — declaration order, operand
> arity, type universe — has to be diffed too.

So the interpreter change is: **five new evaluators, two of them deliberate refusals, plus three
corrections to shared code where a GL-only measurement had been written down as a property of the
language.** Every one of those three is guarded by a measurement showing GL cannot reach it, and the
full GL suite is green.

### 1.3 · A documented trap that is not one

`CF-RATING-ENGINE-BUILD-PLAN.md` records, as a non-negotiable, *"CF's multiply operator is
`rul:Product`, not `rul:Multiply` — a naming difference from whatever GL's engine assumes."*

**GL uses `rul:Product` too**, 51 registered nodes include `Product`, and `rul:Multiply` exists in
neither corpus. The August finding was real as a correction to a bad grep; it is not a CF-vs-GL
difference, and it should stop being carried as a reason to doubt interpreter reuse. Correcting it
here rather than silently, because it is cited in two documents.

---

## 2 · The work, file by file

### 2.1 · Shared interpreter (touches `gl_engine/`)

**As built**, not as first specified — the last three rows were not foreseen:

| File | Change | Risk to GL |
|---|---|---|
| `gl_engine/interp/nodes.py` | `+5` `@node` evaluators: `Null`, `Power`, `LastNonNull`, and `Custom`/`FromList` refusing | None — all five absent from GL's corpus |
| `gl_engine/interp/interpreter.py` | The unknown-node error hardcoded *"the language has 54"*; now read from `len(EVAL)` | None |
| `gl_engine/interp/nodes.py` | `And`/`Or` accept a `ForEach` operand as a quantifier | None — GL files 0 of 58,752 |
| `gl_engine/interp/values.py` | `boolean` added to `TYPES`, with `true`/`false` the only accepted spellings and `to_text` rendering ISO's spelling rather than Python's | None — GL files 0 |
| `gl_engine/erc/tables.py` | `TableDef.key_items` records ISO's DECLARED key order, ranges interleaved | None — GL declares ranges last in 218 of 218, so the order is unchanged for it |
| `gl_engine/interp/interpreter.py` | The banded lookup matches keys positionally against `key_items` instead of assuming the band is last | None, same reason |
| `gl_engine/resolve/resolver.py` | `MIN_ASOF` and the floor's stated reason become class attributes so a second line can subclass instead of copying 176 lines | None — GL's values are the defaults |
| `tests/verify_interp.py` | A3 asserted the registry matched the GL census EXACTLY. Now: every evaluator is in the census **or** in a named CF list. New A4 asserts the five are genuinely absent from GL | The assertion is strictly narrower in one way and wider in another; it still fails on an invented evaluator |

**No dialect flag was needed.** Every divergence turned out to be a case GL's corpus does not
contain, so the correct fix was to make the shared code read ISO's declaration rather than a GL
measurement. A flag would have preserved the wrong reading on the GL side.

### 2.2 · New `cf_engine/` package

Mirrors `gl_engine/`, importing the shared interpreter rather than copying it.

| File | Does | Notes |
|---|---|---|
| `cf_engine/config.py` | `CORPUS_ROOT` = `CF_ERC_ROOT` env var, default `C:\Projects\ISO_ERC_Files\CF`; the CF `MIN_ASOF`; excluded dirs | The CF root holds a stray `.xlsx` at top level — excluded by predicate, not by name |
| `cf_engine/erc/discovery.py` | Package discovery, identity from XSD `targetNamespace` | Port GL's two rules verbatim (N6; a search predicate must not define a population) |
| `cf_engine/resolve/resolver.py` | Subclasses GL's `EditionResolver`, overriding only the corpus and the date floor | 20 lines instead of a copied 176; see 2.3 on the carry-forward |
| `cf_engine/resolve/book.py` | Rulebook composition **+ the header-only detector** | Both reused from `gl_engine` unchanged — `rating_table()` already refuses an empty table where a premium depends on it, which *is* the detector |
| ~~`cf_engine/domain/territory.py`~~ | ~~County/place resolver~~ | **Not built — not needed.** See below |
| `cf_engine/schema/fields.py` | submission shape | **No longer blocked — the field set is now known from two coverages.** See [`CF_Algorithm/CF_Payload_ClassRated_Bldg_PP_Alabama.md`](../CF_Algorithm/CF_Payload_ClassRated_Bldg_PP_Alabama.md): the shape is derived from ISO's own STC payloads and validated across all 7 Alabama cases, covering class-rated Building *and* Personal Property. Still deferred as *work*, but the reason for deferring it is gone |
| ~~`cf_engine/rating/kernel.py`~~, ~~`cli.py`~~ | ~~premium chain driver~~ | Deferred: `scripts/cf/01_golden_case.py` drives the interpreter directly. Promote it when a second coverage needs the same driver |

**The territory resolver was specified and turned out not to be a component at all.**
`BasicGroupIRatingTerr` is a **submission input**: `LookupRatingTerritoryGroupIFactor` reads it
directly, and `SetBasicGroupIRatingTerrFactor` only guards on it being non-empty. No rule derives
it. What is county/place-shaped is the *domain table* constraining which territory an agent may pick
for a given City — `DomainBasicGroupIRatingTerritoryOR` maps Eugene and Remainder of State to
"Balance of State" and Portland to "Portland" — which is validation and UI, not a rating step.

So the build order is right that GL's ZIP resolver does not transfer, and wrong that a replacement
is needed. **Chunk 0 is one component smaller than specified**, and the reason is written down
rather than the component quietly dropped.

**Confirmed independently 2026-09-17 from ISO's own test payloads.** Every territory field is
*supplied* in the STC request — `BasicGroupIRatingTerr`, `BasicGroupIIRatingTerr`,
`SpecialRatingTerr`, `EQTerr`, `TerrorismTerritory`, `GeographicWindHazardLevelTerritory`. ISO's
Alabama fixtures pair `ZipCode "08003"` (a New Jersey ZIP) with `City "Birmingham"` and
`County "Autauga"` — Birmingham is in Jefferson County — and rate anyway. Geography that
inconsistent can only rate if the territory fields are taken at face value. Nothing derives
territory from an address.

### 2.3 · The edition chain is not what the folder names suggest

Worth stating before anyone writes the resolver: the CF corpus's **edition folders do not equal
package editions**. `CF/20260601/` contains `CF AK 20260601 V01` *and* `CF AK 20261101 V02` — a
package dated five months after the folder it sits in. A resolver keyed on the folder will
mis-order AK, CA, CT, IA, IN, AL, AR and others.

The resolution order is the package's own declared identity and declared parent, the same way
`gl_engine/erc/discovery.py` already refuses to trust a directory name. There is a second effect the
folder layout has that GL's does not: the Property corpus is laid out root / **edition batch** /
package, and the same package appears in several batches, so de-duplicating by package id is
load-bearing rather than tidy-up. Without it several jurisdictions are counted more than once.

**The carry-forward layer is not built, and was not needed.** The build order supposes a third
layer — *a table absent from the current edition is still in force from the last edition that filed
it* — on the strength of every CF spreadsheet performing that scan by hand. Check 3 of
`scripts/cf/00_chunk0_checks.py` tests the premise directly: all 17 tables the chunk 1 chain reads
resolve inside the resolved state package or its **declared** parent. None needed an older edition.

So the premise stays **unproven rather than built on**. ISO's packages state their parentage
explicitly (N5) and two layers is what they declare; resolving a value from an edition ISO did not
say to read is the same class of move as falling back to the newest countrywide package, which N5
already forbids. If a rating is later found to need a table in neither layer, *that* is the evidence
for a third layer, and it should be built then, against that case.

---

## 3 · How chunk 0 is proved

Chunk 0 has **no gate of its own** — the build order is explicit about that, and it stays true. It
is proved by chunk 1's eight-point gate. What chunk 0 owes before chunk 1 starts is narrower, and
all four are now run by `scripts/cf/00_chunk0_checks.py`:

| | Owed | Status |
|---|---|---|
| 1 | Every one of the 60 CF element names evaluates or raises a **named** error | **PASS** — 56 operators registered, 4 structural containers, `Custom` and `FromList` refusing by name |
| 2 | The header-only detector fires on a known header-only table and names it | **PASS** — `BasicGroupIRate` at countrywide, refused with the package named; the Oregon override resolves with 1,368 rows |
| 3 | The resolver resolves a state over its **declared** parent, and the chunk 1 chain is reachable within those layers | **PASS** — `CF_OR_20260601_V01` over `CF_CW_20260601_V01`, all 17 chain tables present |
| 4 | The GL suite is still green and demonstrably unaffected | **PASS** — twelve suites, 359 checks |

> Check 3 was specified as *"reproduces an edition carry-forward that a built spreadsheet already did
> by hand."* It became a test of whether carry-forward is needed at all, because building the
> resolver made the question answerable. It is not needed for this chain — see 2.3.

A **fifth** check was added that the spec did not ask for: every table value the chunk 1 golden case
depends on, re-derived through the engine's own book rather than by reading files. Checks 1–3 prove
the machinery loads and refuses correctly while saying nothing about whether the numbers chunk 1
expects are actually there — and those numbers were resolved by hand. All ten agree, including the
interpolated LOI factor and the Oregon deductible row that has to beat countrywide's.

---

## 4 · Not in chunk 0, stated so it is not assumed

- **No rating.** No premium comes out of chunk 0. The first number is chunk 1's golden case.
- **No `rul:Custom` implementation** — refused by name, backlogged, scoped to Builders Risk.
- **No blanket branch.** Chunk 9, and nothing above it is *finished* until it lands.
- **No CF/GL UI switch, no separate results subtree, no CF ISO call budget.** Item 4 of the August
  proposal, still unauthorized, and not needed to prove the architecture.
- **Five jurisdictions are absent from the CF corpus outright** — HI, ID, LA, MS, WA. Chunk 0 must
  report that as absence, not resolve around it.
- **No validation-message evaluation.** CF files **1,621 `DoMessage` rules** across 48 jurisdictions
  and a submission can **rate correctly and still return errors** — there is one severity, not three.
  Chunk 0 produces no premium, so it raises no messages; but chunk 1's golden case will, and gate
  point 9 of the build order now requires each one to be designed out or logged. The rule inventory
  (`CF_Algorithm/CF_Validation_Messages.xlsx`) and the diagnostic
  (`scripts/cf/07_diagnose_message.py`) exist already and are **read-only** — neither evaluates a
  rule. A **pre-flight validator that does** is the natural follow-on and is explicitly unauthorized,
  for the same reason as the rest of this spec.

---

## 5 · Evidence

Counts in §1 are reproducible from the corpus:

```bash
# distinct rul: elements, all CF editions
grep -rhoE '<rul:[A-Za-z]+' "C:/Projects/ISO_ERC_Files/CF" --include='*.xml' \
  | sed 's/<rul://' | sort | uniq -c | sort -rn

# registered evaluators
grep -oE '@node\("[A-Za-z]+"' gl_engine/interp/nodes.py | sed 's/@node("//;s/"//' | sort
```
