# Property chunk 1 — gate

**2026-09-17. Building, Basic Group I, class-rated, scheduled — Oregon.**

> **Point 9 closed 2026-10-02 (chunk 27 RC-2, `239_chunk27_rc2.py --live`).** Each golden case sent to ISO as the engine rates it, the (level, message) multiset compared: case A 2 = 2, case C 2 = 2, case B 3 = 3 (the contents cases sent with the building's `WindstormOrHailDeductible`; without it ISO refuses, OI-103). Every message is in the register (M-001 CP 03 20, M-002 CP 10 75 / 76, M-005 full value). Nothing unexplained.


Assessed against the eight-point gate in [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md).

> ## Verdict: **PASS on 8 of 8.**
>
> Three golden cases rate to the penny, every intermediate matching a hand-derivation written before
> any code existed. Six zero cases separate four mechanisms that all produce the same premium.
> **44 of 47 jurisdictions rate exactly as predicted from their own filed rows**, with no
> unexplained failures; the three skipped are the District two-table states. The shared-name,
> exclusion-record and hardcoded-literal populations are enumerated rather than sampled.
>
> **Confirmed against ISO's own service, not just our own arithmetic.** Oregon's golden case came
> back identical — $261.00, with both validation messages matching too — and New York, which the
> engine originally refused, now rates at ISO's own $396.
>
> **Five things this gate found are worth more than the pass**, each recorded in full below:
>
> * **Arizona prices every building at zero** without an input the countrywide chain has no term for,
>   and nothing raises.
> * **New York's refusal was a three-valued-logic question**, and settling it confirmed contract
>   §12.3 for *both* lines of business rather than undermining it.
> * **Rounding is proven half-up against ISO**, at both scales — it was an assumption until a case
>   was deliberately built to land on a tie.
> * **18 of 47 jurisdictions do not run the countrywide chain**, so agreement on this risk is not
>   agreement in general.
> * **The literals that pin a lookup mostly arrive as rule arguments, not in `Keys`** — a scan of
>   `Keys` alone finds none of them, including the documented vacant-building trap.

Reproduce:

    python scripts/cf/00_chunk0_checks.py      # chunk 0's four proofs, plus a fifth
    python scripts/cf/01_golden_case.py        # points 1, 2, 8
    python scripts/cf/02_zero_cases.py         # point 4
    python scripts/cf/03_enumerate_states.py   # point 3 -- all 47 jurisdictions
    python scripts/cf/04_shared_names.py       # point 6
    python scripts/cf/05_exclusion_records.py  # point 7
    python scripts/cf/06_raas_newyork.py       # 3 calls to ISO's live service
    python scripts/cf/07_rounding_tie.py       # 2 more -- settles the rounding mode
    python scripts/cf/08_hardcoded_literals.py # point 5

---

## Confirmed against ISO's own service, 2026-09-17

Three calls to ISO's live rating service (`scripts/cf/06_raas_newyork.py`,
`results/cf-raas/`), with every prediction written down **before** the call.

| Call | Engine | ISO | |
|---|---|---|---|
| **Oregon**, golden case A | $261 | **$261.00** | identical, and **both of ISO's validation messages match both of ours** |
| **New York** | *refused, now $396* | **$396.00** | exactly the figure predicted from New York's own rows; the engine now agrees |

**Oregon is the control and it passes exactly.** Chunk 1's chain — base rate, territory, protection
class, coinsurance, LOI, deductible, the rounding nesting at every step, and the premium branch — is
now confirmed against the only authority that matters, not just against our own hand-derivation.

**New York rates at ISO.** So the engine, not the filing, is what stops. See point 3.

ISO's first response also settled the payload contract for free: it accepted the product name
(`Commercial Property <ST>`) and the whole flattened nesting on the first attempt, complaining only
that four decimal fields arrived as strings. Its JSON binding is typed where our data tree is not.

---

## The result

| | A | B | C |
|---|---|---|---|
| What it isolates | the chain | deductible keys on the **location total** | LOI **interpolation** |
| Premium | **$261** | **$263** | **$288** |
| Expected | $261 | $263 | $288 |
| ISO | **$261.00** | not called | not called |

Every intermediate — base rate 0.498, rate 0.239, coinsurance 0.95, LOI 1.172/1.150, deductible
0.98/0.99, final rate 0.261/0.263/0.256 — matches the value derived by hand from the rules and rows
in [`CF-CHUNK1-GOLDEN-CASE.md`](CF-CHUNK1-GOLDEN-CASE.md), written before the engine could run.

---

## The eight points

### 1 · A golden case rates end to end, every intermediate traced to a named rule and table row — **PASS**

Three of them. Every value in the chain is read out of the data tree by datadef name, and each has a
named rule (`CommercialPropertyStructureRules.Rule.xml`, line-cited) and a named table row behind
it. Check 4 of `00_chunk0_checks.py` re-derives all ten table values through the engine's own book,
so the hand-derivation and the machine agree independently.

### 2 · Every table the chain touches has its row count stated; header-only explained — **PASS**

All 17, per layer. **Three are header-only at countrywide** and rateable only from a state filing:

| Table | CW | OR |
|---|---|---|
| `BasicGroupIRate` | **0** | 1,368 |
| `RatingTerritoryGroupIFactor` | **0** | 2 |
| `VacantBldgPreviousOrIntendedOccup` | **0** | 106 |

`BasicGroupIRate` is header-only at countrywide in **every edition from 20191201 to 20260601**, not
just the current one. `VacantBldgPreviousOrIntendedOccup` was not on any existing list of zero-row
tables — found by this gate.

**This contradicts the build order, and in our favour.** It puts chunk 2 as *"the chunk that proves
the state-table loader for real."* Chunk 1 proves it three times over.

### 3 · Every state enumerated, not sampled — **PASS**

`scripts/cf/03_enumerate_states.py`. **N = 47**, discovered by walking the corpus (437 packages),
not taken from a list. Five jurisdictions are absent from the corpus entirely and so are not in N:
HI, ID, LA, MS, WA.

Each jurisdiction gets *its own* equivalent of case A — its own territory read out of its own filed
table — and the expected premium is **predicted** from the resolved rows before the engine runs.
Rating 47 states and reporting that 47 numbers came out would be evidence of nothing; the numbers
have to be predicted, and the predictor implements the rate chain directly, so it would not follow
the interpreter into a wrong branch, a mis-ordered key or a dropped factor.

| | n of 47 |
|---|---|
| Rate **exactly as predicted** from their own rows | **44** |
| Skipped — no `BasicGroupIRate` row for class 0951/Frame | 3 (AK, CA, PR — the District two-table states) |
| Unexplained failures | **0** |
| ~~Blocked~~ — New York, now resolved (see below) | 0 |

**Two of these started as mismatches and both turned out to be real findings**, which is the
argument for predicting rather than observing.

**Arizona** overrides `SetBasicGroupIRate` to multiply the base rate by a Location-level
`BasicGroupIReductionCredit` that the countrywide formula has no term for. It is read through
`FirstValue FromConstant="0.0"`, so **absent means zero**: without that input every Arizona building
prices at zero and nothing raises. With it supplied, Arizona matches its prediction exactly ($356).
That is a state-specific instance of gate point 4, found only because a state disagreed with a
prediction.

**New York** was the fourth, and is now resolved. The reason it refused is worth keeping, because
the investigation it forced settled a contract question for both lines of business.
`DoMessageTerrorismPremiumCannotExceed25PercentOfTheTotalNonTerrorismPolicyPremium` — filed in
**exactly one package in the entire corpus**, New York's, as `RuleTypeStateSpecific` — subtracts
policy-level `Premium` with no null guard, while guarding `TerrorismPremium` immediately next to it
with a `FirstValue` fallback. `Premium` is not yet computed when validation runs: the `Default`
block calls `ErcCalculateTotalPremium` *after* `ErcProcess`. So the rule reads a null for every
Property submission in every New York territory. **Either ISO's runtime coerces null to zero in
arithmetic — which contradicts contract §12.3, adopted deliberately for GL — or this filed rule is
defective.**

> **Answered in part, 2026-09-17, against ISO's service.** ISO returns **$396.00** for the New York
> case — *exactly* the figure predicted from New York's own rows — with **no terrorism message**.
>
> So the "filed rule is defective" explanation is **dead**: ISO's own engine completes where ours
> stops. The engine is what needs to change, not the filing.
>
> **What remains open is the mechanism, and it is worth being precise about**, because the two
> candidates have very different blast radii:
>
> * **null coerced to zero in arithmetic** — then contract §12.3 is wrong for this corpus, and that
>   applies to General Liability too. Large.
> * **ISO's `Premium` is already populated when validation runs** — then it is our *rule ordering*
>   that differs, §12.3 stands, and the fix is narrow.
>
> A third call was designed to separate them and **did not**, for a reason worth more than the call:
> `TerrorOverridePremium` sets `TerrorismPremium` on the **structure**, while the rule reads it at
> the **policy** level — and enumerating both packages shows **no rule anywhere writes
> `TerrorismPremium` in the `CommercialProperty` datadef group**. Zero writers countrywide, zero in
> New York. So the rule's first operand is *always* null-guarded to `0`, the test is always
> `0 > (Premium − 0) × 0.25`, and it is false whether `Premium` is `0` or `396`. **The message can
> never fire for any submission.** The rule is dead code as filed, which is why it cannot
> distinguish the two hypotheses.
>
> **Resolved 2026-09-17. New York now rates, to ISO's own figure.** Three hypotheses were built and
> measured rather than argued, each behind the same switch (`Interpreter(null_arithmetic=...)`):
>
> | Mode | New York | Verdict |
> |---|---|---|
> | `refuse` — contract §12.3 as written | *refuses* | the starting point |
> | `zero` — coerce null to 0 | **$0** | **disproven** |
> | `propagate` — null in, null out; comparison with a null is false | **$396** | **matches ISO exactly** |
>
> **Coercion failed instructively.** It completes the rating and returns zero, and the trace says
> why:
>
> ```
> lookup-miss:   BasicGroupILOIFactorBldg[Factor] keys=['NY', 100000, 1]
> null-coerced:  null reached arithmetic and became 0
> ```
>
> ISO writes every state-to-countrywide fallback as
> `FirstNonNull(Round(Lookup(state)), Round(Lookup('CW')))`, and the state lookup is *designed* to
> miss. Refusing lets `FirstNonNull` abandon branch one and reach countrywide — that is OI-88,
> already paid for once on the GL side. Coercing turns the miss into a perfectly good `0`,
> `FirstNonNull` accepts it, and **the countrywide row is never read.** That idiom is everywhere in
> both corpora, so a coercing engine would price vast numbers of risks at zero. ISO plainly does
> not. **Contract §12.3 is therefore confirmed by its own counter-test, and the worry that GL might
> have been affected all along is closed: it has not been.**
>
> **The ordering hypothesis turned out to be unfalsifiable**, and that is worth recording. Looking
> for evidence for it found that **exactly one rule in the entire corpus reads policy-level
> `Premium`** — New York's — and that rule can never fire, because nothing anywhere writes
> `TerrorismPremium` at the policy level, so its first operand is always `0`. No ISO response can
> distinguish "their `Premium` was populated" from "they handled the null". Reordering ISO's own
> rule sequence on no evidence would have been exactly the move this project forbids.
>
> **Propagation is what survives**, and it is the only one of the three consistent with everything
> observed: New York's rule becomes `0 > null` → false → no message → $396, *and* the fallback idiom
> still works because a null still lets `FirstNonNull` fall through. It is also the ordinary
> semantics of comparable three-valued systems — weak evidence, but not none.
>
> **Measured blast radius: nothing else moved.** Twelve GL suites green under `propagate`, including
> the ones comparing against ISO's own oracles; Property's three golden cases and six zero cases
> unchanged; the state sweep unchanged except New York, which now rates.
>
> **The residual risk was stated, and then closed.** `refuse` failed loudly the moment a null
> reached arithmetic; `propagate` lets nulls flow — which is what ISO does, and what the fallback
> idiom needs — but a null could then reach a premium and vanish, because `Sum` skips null operands
> by design. A coverage that resolved to nothing would simply not be added up, and the policy would
> come out cheaper with nothing raised anywhere.
>
> **The null-premium guard (2026-09-17) moves the loudness from "any arithmetic" to "the money".**
> Nulls flow freely through intermediate steps; writing one into `Premium` or
> `ErcCalculatedTotalPremium` is refused, naming the datadef and pointing at the trace.
>
> The guarded set is **named, not matched**. A substring test on "Premium" was the obvious
> implementation and is wrong: the corpora write `PremiumIndicator` (a 0/1 flag, 21,386 writes
> across both lines), `MultiPremiumAndDispersionCreditFactor`, `PremiumBasis` and
> `PremiumDiscountCharge`. Guarding those would refuse ordinary content — the same shape of error as
> letting a search predicate define a population, which this project has paid for once already.
>
> **Measured: the guard is inert on every path currently exercised** — twelve GL suites, Property's
> three golden cases, six zero cases and all 47 jurisdictions, with nothing refused. That is not
> evidence it works, so `verify_interp` B27–B29 demonstrate it directly: B27 a null written to
> `Premium` is refused, **B28 the same program with the guard off writes an empty premium and raises
> nothing — the hazard itself, demonstrated rather than asserted**, and B29 `PremiumIndicator` is
> deliberately not guarded.
>
> Worth noting why it is inert: ISO guards its own premium inputs heavily with
> `FirstValue FromConstant="0.0"`, so a null reaching a premium is rare rather than impossible. The
> guard costs nothing and covers the case ISO's own guards miss.
>
> General Liability is deliberately **not** switched; its default stays `refuse` until someone wants
> to make that change on GL's own evidence. Locked in by `verify_interp` B23–B29.

#### The override census — the part that qualifies the "43"

**18 of 47 jurisdictions override at least one chunk 1 chain rule.** The countrywide chain
documented in `CauseOfLoss_Building_RatingAlgorithms.md` is not the chain in those 18.

| Rules overridden | Jurisdictions |
|---|---|
| `SetBasicGroupIRate` | AZ, CA, DC, FL, IL, KY, NJ, NY, PR, WV |
| `SetBasicGroupICauseOfLossAdjustment` | AL, FL, KS, NY, RI, VT |
| `SetCoinsuranceFactor` | AL, CT, KS, NY, PR, RI |
| `SetBasicGroupIBaseRate` | AK, CA, NY, PR |
| `SetProtectionClassFactor` | NY, PR |
| `SetFinalBasicGroupIRate` | FL, VA |
| `SetDeductibleFactorBasicGroupI` | FL |
| `SetAdjustedBasicGroupIRate` | SC |
| `SetSubStdConditionRate` | KY |

**An override that agrees with the countrywide prediction is not a no-op — it agrees *for this
risk*.** A different class, limit or election may reach the branch that differs, exactly as
Arizona's did. This census is the population chunk 2 and every later chunk have to re-ask.

### 4 · Every `0` tested against its consuming branch — **PASS**

`scripts/cf/02_zero_cases.py`, five cases plus the baseline. Each moves one input and asserts the
whole chain, because four of them produce the *same* premium by four different mechanisms and only
the chain tells them apart.

| Case | base | LOI | final | premium | The mechanism |
|---|---|---|---|---|---|
| baseline | 0.498 | 1.172 | 0.261 | **261** | reference |
| Z1 `Limit = 0` | 0.498 | **0** | 0 | **0** | `SetBasicGroupILOIFactor` assigns `0.0` outright. The zero enters at step 4, not step 1 |
| Z2 unknown `ConstructionType` | **0** | **0** | 0 | **0** | resolves to construction code 0, failing both gates. **Does not raise** |
| Z3 blank `ClassCode` | **0** | 1.172 | 0 | **0** | base-rate gate only — distinguishable from Z2 *only* by the LOI factor |
| Z4 blank `CauseOfLoss` | 0.498 | 1.172 | **0.261** | **0** | see below |
| Z5 cyber exclusion elected | 0.498 | 1.172 | 0.261 | **260** | the inverse test: 261 × 0.995 = 259.695 → 260 |

**Z4 is the one worth reading twice.** The entire rate chain computes correctly — a final rate of
0.261, the same as the passing case — and the premium is still zero, because
`SetCoverageOnPolicyIndicator` gates on `CauseOfLossToUse`. A fully-built rate sitting next to a
zero premium is exactly the shape a silent defect takes. It is ISO's own rule and not a defect, but
nothing except this test says so.

**Z5 is the inverse and matters as much.** Both cyber factors are read through
`FirstValue … FromConstant="0.0"`, so a rule that never ran would zero the premium rather than leave
it alone. Z5 proves the factor is live and applied.

**Z2 is the finding.** An unrecognised construction type does not raise — it resolves to code 0 and
prices at zero. A typo in a submission field is indistinguishable from a deliberate zero, which
makes it the strongest argument in this gate for schema validation on the input side.

### 5 · Every hardcoded literal key listed — **PASS**

`scripts/cf/08_hardcoded_literals.py`, across the **whole Building coverage** (every rule whose
datadef group starts `CommercialPropertyStructure`), not just the chain chunk 1 walks.

**147 literal pins at 69 distinct sites.** The countrywide `CW` literal is excluded by name — that
is ISO's two-pass fallback idiom, not a pin, and reporting thousands of them would bury the handful
that matter.

**31 of the 147 arrive as a rule ARGUMENT, not in `Keys`** — and that is where the ones that bite
live. ISO's idiom is a thin `LookupX` rule whose keys read `FromParam`, called by a `RunRule`
supplying the literal:

```xml
<rul:RunRule Rule="LookupVandalismExclusionFactor">
  <rul:Arg Param="classCode"><rul:Constant Type="string">1180</rul:Constant>
```

A scan that reads only `Keys` sees a live parameter and reports nothing. The first version of this
script did exactly that and found **zero** of them — the documented vacant-building trap included.

#### What is actually pinned

Reported **by column**, not by site, because several sites pinning *different* values of the same
column between them reach everything. `SubStdConditionRate` is pinned to A, B, C, D and E at five
call sites and there is no finding at all; 40 columns are like that (37 are single-row tables where
pinning the only value removes nothing).

The 15 that do remove something:

| Table . column | pinned to | unreachable | scope |
|---|---|---|---|
| `VandalismExclFactor.ClassCode` | `1180` | 160 of 161 (99%) | pinned site only |
| `DeductibleStatCode.Deductible` | `No Deductible` | 22 of 23 (96%) | pinned site only |
| `CoinsuranceStatCode.Coinsurance` | `No Coinsurance` | 9 of 10 (90%) | pinned site only |
| `BasicGroupIISymbolAdditionalClasses.ConstructionCode` | `1` | 5 of 6 (83%) | pinned site only |
| `BasicGroupIISymbolAdditionalClasses.ClassificationCode` | `OpenSides` | 5 of 6 (83%) | pinned site only |
| **`BasicGroupIRate.Group`** | `Not Applicable` | 4 of 5 (80%) | **every site** |
| `BroadFormBaseRate.CovType` | `Bldg`, `BldrRisk` | 3 of 5 (60%) | pinned site only |
| `LimitationsOnCovForRoofSurfacingFactor.Limitation` | `Paragraph B` | 2 of 3 (67%) | pinned site only |
| **`SprinklerLeakageExclSprinkleredFactor.CovType`** | `Bldg` | 1 of 2 (50%) | **every site** |
| **`BasicGroupIRate.CovType`**, `BasicGroupIIRate`, `LowestBasicGroupIIRate`, `LegalLiabilityFactor`, `FloodLossCost`, `SoftStoryModificationFactors` — all `.CovType` | `Bldg` / `Building` | 1 of 2 each | **every site** |

**The scope column is the part not to skip.** "Pinned site only" means the same column is *also*
read live somewhere else, so the table is dead **from that branch**, not dead. `VandalismExclFactor`
is the clearest case: vacant buildings are priced as class `1180` whatever they actually are, while
every other branch passes the building's real class. Claiming "160 of 161 rows are unreachable"
without that qualifier would be false.

The **every site** rows are the genuinely closed doors. Most are the Building/Contents split —
`CovType` pinned to `Bldg` because these are the Building rules, and the Contents rows are reached
from the Contents rules instead. That is expected, and now recorded rather than assumed.

#### Branch literals

Separately, **322 distinct (field, literal) pairs across 1,145 comparisons** decide which path a
risk takes — `IncludedInBlkt == Yes` (39), `CovType == No Coverage` (37), `RatingType == Class`
(21), and so on. These do not make rows unreachable; they are the switches. Chunk 1 exercised a
handful, and every later chunk walks the rest, so the list is the map rather than a finding.

### 6 · Shared-name traps diffed, not assumed — **PASS**

`scripts/cf/04_shared_names.py`. The whole population, not the two known cases: **2,119 distinct
rule names across 882 countrywide rule files**, with the rate tables each definition actually reads
taken from the `MatrixFromConstant` of every `Lookup` in its own body.

| | count |
|---|---|
| Chunk 1 chain names defined in more than one datadef group | 28 |
| …of those, reading **different** rate tables | **1** |
| Everywhere else: names in more than one group | 865 |
| …of those, reading different rate tables | 9 |

The one on chunk 1's chain is `LookupBasicGroupILOIFactor`, defined in nine datadef groups: five
Building-side groups read `BasicGroupILOIFactorBldg`, four Personal-Property-side groups read
`BasicGroupILOIFactorPersProp`. That is correct rather than a trap — the name is scoped by datadef
group — **and the gate's point is that a shared name is a question, so the answer is written down**
in the script's `ADJUDICATED` table rather than assumed. The script fails if an ambiguous chain name
has no recorded answer, or if the answer stops matching the corpus. Verified independently: golden
case C interpolates 1.150 out of `BasicGroupILOIFactorBldg`.

**Chunk 4 will execute the other branch of this very name**, which is why it is worth having on
record now rather than rediscovering there.

### 7 · Every exclusion's endorsement record identified per datadef group — **PASS**

`scripts/cf/05_exclusion_records.py`. **18 exclusion families, 86 (family, datadef group) pairs**,
each with the `AtInputDataDef` its `Exist` gate actually tests.

| Family | datadef groups | **distinct** endorsement records |
|---|---|---|
| Windstorm or Hail | 17 | **5** |
| Vandalism | 11 | **5** |
| Sprinkler Leakage | 5 | **3** |
| Cyber Incident | 1 | 1 |
| The eleven terrorism families | 5 each | 1 each |

**Property does not file one exclusion record per policy — it files one per coverage.** A building's
vandalism exclusion is a different record from the contents', which is different again from business
income's, Special Class's and Special Class Business Income's.

The consequence for anything collecting these as inputs: a single "vandalism excluded?" control fed
to every coverage is a **simplification**. It may be the right product decision; it is not what ISO
filed, and this gate's requirement is that it be logged (S-1/S-2/S-3 in
`Rater_Simplifications_Backlog.md`) rather than left implicit.

Chunk 1 elects no exclusion, which is why its golden cases say nothing here. This census is what
replaces that silence.

### 8 · The edition basis stated; any table from an older edition says so — **PASS**

`CF_OR_20260601_V01` over its **declared** parent `CF_CW_20260601_V01`, as-of 20260917. Identity and
parentage read from each package's XSD `targetNamespace` and `xs:import`, never from the folder —
which matters here, because on disk those are `CF OR 20260601 V01` and `CFCW20260601V01` and neither
spelling matches its namespace.

**No table came from an older edition, and none needed to.** All 17 resolve within the two declared
layers, so the build order's edition-carry-forward premise is untested rather than relied on.

---

## What the build found that the plan did not

Five things, each caught by a raise rather than a wrong number — which is the doctrine working, but
four of the five are worth reading as warnings rather than as wins.

| Found | Why it matters |
|---|---|
| **A key `Range` is not always the last key column.** CF files 19 table names with one mid-list; GL: 0 of 218 | `DeductibleFactor`'s trailing key is the string `'Basic Group I'`, so this threw. **On a table whose trailing key happened to be numeric it would have matched the wrong band and returned a plausible factor** |
| **`Type="boolean"` is a sixth declared type.** CF files it 9,228 times, GL never; GL files `long`, CF never | The evaluation contract's "five types" was a measurement of one corpus that read as a property of the language |
| **`And`/`Or` accept a `ForEach` operand** — a quantifier over the iteration. CF: 369 sites; GL: 0 of 58,752 | Same shape of error: a condition form the language always had, that one corpus happened never to use |
| **`rul:Null` is retired, not chunk 1's problem.** The chunk 0 spec said it had to land or chunk 1 would fail | The 35 occurrences were a total across eight editions; all the Structure-rules ones are pre-2022. An aggregate across editions is the same error as an aggregate across states |
| **No territory resolver is needed.** `BasicGroupIRatingTerr` is a submission input, not a derivation | Chunk 0 is one component smaller than specified |

And two silent-failure modes, both hit while building the submission and both now documented in the
golden-case inputs table: supplying `ClassCodeToUse` instead of `ClassCode`, or `ProtectionClass` on
the structure instead of `ProtectClass` on the location. The first yields a premium of **zero** with
no error; the second yields a premium **4% too high** with no error. Neither is an engine defect —
both are the engine faithfully executing ISO's rules against an input that names the derived field
rather than the source one.

---

## What is still owed before chunk 1 is finished

1. **Gate points 3, 6 and 7** — the enumeration half: all 47 jurisdictions rather than one, the
   shared-name diff, and the per-datadef-group exclusion records.
2. **Input validation.** Z2 is the argument: an unrecognised `ConstructionType` prices at zero
   rather than raising, so a typo and a deliberate zero are indistinguishable. This is the schema
   layer chunk 0 deferred, and it now has a concrete reason to exist.
3. **A message-clean submission.** Three ISO validation messages fire on every case. The premium is
   right regardless, but RAaS returns these in `RatingMessages`, and any comparison that ignores
   them compares half the response.
4. ~~**The rounding mode.**~~ **RESOLVED 2026-09-17 — half-up, proven against ISO.**
   `scripts/cf/07_rounding_tie.py` searched 58,656 class/limit/deductible combinations in Oregon for
   cases where the three modes disagree, and asked ISO two of them:

   | Case | half-up | half-even | truncate | **ISO** |
   |---|---|---|---|---|
   | ties at the **premium** (0 dp) — class 0074, limit 50,000, ded 500 | **$39** | $38 | $37 | **$39.00** |
   | ties at a **rate step** (3 dp) — class 0582, limit 52,500, ded 1,000 | **$65** | $64 | $64 | **$65.00** |

   Two scales on purpose: the chain rounds to 3 decimals at every `rul:Product` in the rate build-up
   and to 0 at the premium, and a case tying at one scale says nothing about the other. Both answer
   half-up.

   **Why nothing before this settled it.** Every earlier match — nine Property cases, 47
   jurisdictions, Oregon against ISO — is consistent with *all three* modes, because not one lands
   on a tie. A matching premium is not evidence about rounding unless the case was built to produce
   one. GL's OI-70 is strong-evidence-by-association but stays open: it is GL's to close with a GL
   tie.

5. ~~**A null that reaches a premium.**~~ **Closed** — the null-premium guard, see point 3.

6. **Whether General Liability should adopt `propagate` too.** It is unaffected in every path
   measured, so there is no pressure — but two lines running different null policies is a state to
   choose deliberately, not to drift into.

6. **Arizona's `BasicGroupIReductionCredit`** is now supplied by the sweep, but nothing yet stops a
   real submission omitting it and pricing at zero. That is the same argument as Z2: input
   validation.

## What is deliberately not here

No `cf_engine/rating/kernel.py`, no schema validation, no CLI, no CF results subtree, no UI. The
golden case drives the interpreter directly from a script. Promoting that to a kernel is worth doing
when a second coverage needs the same driver — not before, and not bundled with a rating change.

Also not here: any comparison against `CFRater1.01.xlsb`. It is tertiary evidence, it carries ~30
logged divergences of its own, and a mismatch against it would need adjudicating before it meant
anything. It is not a gate condition.
