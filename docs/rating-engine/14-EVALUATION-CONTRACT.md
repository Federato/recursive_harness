# 14 — The evaluation contract

**Stage 2, deliverable 1. Written 2026-08-13, before any interpreter code exists.**

This document says what each node of ISO's rule language *means*, so that the interpreter can be
written against a fixed target rather than discovered by trial. E3 deferred it during analysis on
the grounds that it was only needed if we chose to execute ISO's rules rather than re-implement
them. We chose to execute them, so it is now due.

**Everything here is read from the corpus, not from the schema and not from memory.** Four scripts
produce it and each figure below names the one it came from:

| Script | Output | What it establishes |
|---|---|---|
| `scripts/erc/42_node_surface.py` | `out/node_surface.{txt,csv}`, `node_attrs.csv`, `node_children.csv` | every element, attribute, value domain, child and parent in the language |
| `scripts/erc/43_default_block.py` | `out/default_block.txt`, `default_blocks.csv` | the program's true entry point |
| `scripts/erc/44_contract_questions.py` | `out/contract_questions.txt` | the named open semantics, answered or declared open |
| `scripts/erc/23_rule_program.py` | `out/rule_program.txt` | the prior census this one corrects |

**Population: 567 packages, 20,673 rule files, 2,041,679 element occurrences.** The corpus holds 572
package directories; five are byte-identical re-unpacks under a `_MachineReadableContent` wrapper
and are de-duplicated exactly as `gl_engine/erc/discovery.py` does it, so the analysis population
and the engine's population agree by construction.

---

## 0. Three corrections to what we thought we knew

The contract had to begin by re-measuring, and re-measuring moved three numbers. All three had been
carried forward from a derived census rather than from the XML.

**The node count is right, and for a reason we had not checked.** The plan's *"58 node types, 54
executable"* is exactly correct: 58 distinct element names, of which 4 (`Rules`, `Rule`, `MetaData`,
`MetaDataCode`) carry the document rather than the language, leaving **54 language nodes**. That it
matched is worth stating plainly, because the next two did not.

**The prior operator census was missing two of the 54.** `23_rule_program.py` P5 enumerated 52
operators. The two it never saw are **`Default` and `DateAdd`**, and the reason is structural:
`Default` is a child of the document root `Rules`, not of `Rule`, and every census this project ever
ran walked `Rule` elements. `DateAdd` was invisible because it lives inside `Default`. **They are
not rare — both appear in all 567 packages.** §2 is about what they do, and it matters more than the
count.

**The long tail is 9 nodes, not 14.** The plan records *"14 node types appear fewer than 500 times
each"*. Measured from source it is **9 of 54**: `GreaterThanOrEqual` (428), `Length` (370),
`PadLeft` (150), `Max` (98), `Break` (84), `Truncate` (66), `DateCreate` (60), `DateDifference`
(30), `GetList` (2). The plan's *"one appears twice"* is right — that is `GetList`.

> **The pattern is the project's signature one again: measured in one place, stated about
> everything.** A census that walks `Rule` cannot find a node that is not inside a `Rule`, and it
> will report a clean total while blind. This is the same shape as OI-67 and as the split loss-cost
> defect. **It is now the third time, so the rule is promoted:** a census states the element it
> walked and the population it walked over, or it does not get quoted.

### Coverage, re-measured

| Top *n* by occurrence | Share of all language nodes |
|---|---|
| 5 | 53.48% |
| 10 | 74.71% |
| 15 | 87.50% |
| **20** | **94.03%** |
| 30 | 98.65% |
| 40 | 99.76% |

The plan's 94.1% for the top 20 survives at **94.03%**. The architectural decision it justified —
build the language once rather than transliterate 4,461 rules per rulebook — stands unchanged.

---

## 1. The type system

Five types appear, and they are declared on the node rather than inferred:

| `@Type` | Where it appears | Contract |
|---|---|---|
| `string` | everywhere | text; **never coerced to a number** |
| `decimal` | all arithmetic | **`decimal.Decimal`, never float (N10)** |
| `integer` | counts, indicators, keys | exact integer |
| `long` | 26 `Constant`s, 104 `Value`s | exact integer, distinct only in declaration |
| `dateTime` | `EffDate`, `ExpDate`, 1,642 `FirstValue`s | date, no timezone anywhere in the corpus |

**Null is a first-class value and is not zero.** The corpus distinguishes them deliberately: eight
meanings of zero were catalogued during analysis, and `IsNull`/`IsNotNull`/`Exist`/`NotExist` exist
precisely so a rule can ask which it has. **An interpreter that folds null into zero produces a
complete, plausible, wrong premium** — the failure mode stage 1 was built to refuse.

**Null is also not the empty string, and this one was measurable.** *(Q1, script 44)*

> **20,520 `Constant` nodes carry no text. Every single one is `Type="string"`.** No `decimal`,
> `integer`, `long` or `dateTime` `Constant` is ever empty, in any of the 567 packages. 3,324 of
> them *write* to a DataDef.

An empty string-typed `Constant` is **the empty string**. Returning null there would silently change
the behaviour of every `FirstNonNull` that uses one as its fallback — and §4 shows that 89% of them
do.

---

## 2. The entry point — the `Default` block

**This is the finding that changes how stage 3 must be wired, and it was invisible to every prior
analysis.**

`23_rule_program.py` P3 derived the program's entry point by taking the rules that no `RunRule`
anywhere targets, and concluded it was `(GeneralLiabilityRules, ErcProcess)`. That is a true
statement about *rules*. It is not the top of the program.

Every package carries exactly one `Default` block, in `Overall Rating.Rule.xml`:

```xml
<rul:Default>
  <rul:Sequence>
    <rul:Constant Type="integer" ToDataDef="Renewal">0</rul:Constant>
    <rul:Constant Type="string"  ToDataDef="State/Code">CW</rul:Constant>
    <rul:Constant Type="string"  ToDataDef="State/Name">Countrywide</rul:Constant>
    <rul:DateAdd ToDataDef="ExpDate" UnitType="Years">
      <rul:Value Type="dateTime" FromDataDef="EffDate" />
      <rul:Constant Type="integer">1</rul:Constant>
    </rul:DateAdd>
    <!--Assume Policy rather than Quote for a Rating as a Service Request-->
    <rul:Locate AtOutputDataDef="Policy" OutputAction="Append"><rul:Sequence /></rul:Locate>
    <rul:ForEach AtDataDef="GeneralLiabilityTable/GeneralLiability">
      <rul:RunRule FileName="GeneralLiabilityRules" Rule="InitializeRuleSet"        ClearCache="true" />
      <rul:RunRule FileName="GeneralLiabilityRules" Rule="ErcProcess"               ClearCache="true" />
      <rul:RunRule FileName="GeneralLiabilityRules" Rule="ErcCalculateTotalPremium" ClearCache="true" />
    </rul:ForEach>
  </rul:Sequence>
</rul:Default>
```

**An interpreter entered at `ErcProcess` skips five things and reports success.** *(D2–D4, script 43)*

1. `Renewal` defaults to 0
2. `State/Code` and `State/Name` are seeded
3. **`ExpDate` is computed as `EffDate` + 1 year** — nothing else in the corpus computes it
4. a `Policy` node is appended to the output tree, ISO's own comment saying this assumes a policy
   rather than a quote **for a Rating as a Service request** — the same RAaS the harness will later
   diff against
5. **`ErcCalculateTotalPremium` runs after `ErcProcess`** — the total is a separate top-level call,
   not something `ErcProcess` produces

And the loop matters as much as the body: the three calls run **once per `GeneralLiability` row**,
which is where multi-risk submissions are actually iterated.

### It is uniform, which is why it can be a contract

Measured across all 567 packages *(script 43)*:

| | |
|---|---|
| Packages carrying exactly one `Default` block | **567 of 567** |
| Distinct files carrying it | **1** — always `Overall Rating.Rule.xml` |
| Distinct call sequences | **1** |
| Distinct iteration targets | **1** — `GeneralLiabilityTable/GeneralLiability` |
| Distinct seed shapes | **52** — one per jurisdiction, differing only in `State/Code` and `State/Name` |
| Jurisdictions whose seed shape changed across editions | **0 of 52** |

**Contract.** Execution begins at the `Default` block of the resolved package's
`Overall Rating.Rule.xml`. The engine does not accept an entry point as a parameter, and it does not
start at `ErcProcess`. **If a resolved package has no `Default` block, the engine fails — it does
not fall back to a rule.**

---

## 3. Sequencing, and the shape of a rule

| Node | Occurrences | Contract |
|---|---|---|
| `Rule` | — | a named body in a file, addressed as (file, name); `@Type` gives its return type, `none` meaning it returns nothing and runs for effect |
| `Sequence` | 182,751 | evaluate children **left to right, all of them**; the value is the last child's if any. Observed width **0 to 438** — an empty `Sequence` is legal and is a no-op |
| `Break` | 84 | **semantics not yet pinned — see below** |

**`Break` is the one node in the tail whose meaning the corpus does not make obvious.** Its parents
are **`Sum` (68), `Sequence` (14), `GetList` (2)** — so the dominant use, 68 of 84, is inside an
arithmetic aggregation rather than inside a loop, which is not what the name suggests. It is a leaf
(0 children) and appears in 58 of 567 packages.

**Contract, for now: `Break` is a hard failure.** It is 0.004% of the language, it is in the
9-node tail, and none of the eleven acceptance walkthroughs reach it. Guessing that it means
"terminate the enclosing aggregation" would be a guess about arithmetic, which is the worst place to
hold one. Recorded as **OI-74**.

`Sequence` nests inside `Rule`, `Then`, `Else`, `Locate`, `Otherwise`, `Default` and itself.

---

## 4. Values and null

### `Constant`
342,916 occurrences, **18.4% of the whole language and the single most common node.** Leaf: never
has children. Text payload is the value; absent text means the empty string (§1). `@ToDataDef`
present on 25,536 makes it a write.

### `Value`
Reads a DataDef by path. `@AllowNullReturn="true"` on **7,557 nodes — always exactly that value,
never `false`** *(script 42, N3)*.

**Contract.** Without `@AllowNullReturn`, a `Value` that resolves to nothing is an error the
interpreter raises. With it, the null is returned and the caller is expected to handle it. *(Q4)*
The nulls are concentrated where you would expect a coverage to be genuinely absent —
`GeneralLiabilityClassification*` (947), `GeneralLiabilityRules` (867), the two classification
coverage files (760 and 739), `GeneralLiabilityUnmannedAircraft*` (680 and 665) and
`GeneralLiabilityTerrorism` (552). By type: 4,629 decimal, 1,647 string, 1,281 integer.

### `FirstValue` — **the four-way precedence collapses to two**

`@Order="DataDefInputParamConstant"` declares a precedence over four sources: DataDef, then Input,
then Param, then Constant. P5 listed working out that precedence as a thing an implementer must pin
down. **The corpus settles it.** *(Q2, script 44)*

| Attribute | Present on |
|---|---|
| `FromDataDef` | **171,189 of 171,189 (100%)** |
| `FromConstant` | **171,189 of 171,189 (100%)** |
| `FromInput` | **0** |
| `FromParam` | **0** |
| Distinct source combinations filed | **1** — `(FromDataDef, FromConstant)` |

`@Order` itself carries **one value corpus-wide**.

**Contract.** `FirstValue` returns the DataDef value if it is non-null, otherwise the constant.
**`FromInput` and `FromParam` are not implemented, and encountering either is a hard failure rather
than a guess** — the engine must never invent a precedence it has never seen exercised.

`@FromConstant` values are themselves telling: `(empty)` 94,152, `0` 47,172, `0.0` 28,223 and
`01/01/0001` 1,642 — the last being the dateTime zero, which is a sentinel and **not a date to
compute with.**

### `FirstNonNull` — **and it can genuinely exhaust**

Returns the first non-null child. The plan asks directly: *what does it do when everything is null?*

**It is not hypothetical.** *(Q3, script 44)*

| Last child (what decides exhaustion) | Count |
|---|---|
| `Constant` — a total fallback, can never be null | 32,601 |
| `Lookup` | 3,920 |
| `RunRule` | 48 |
| `Convert` | 20 |
| `Round` | 16 |

**32,601 of 36,605 (89.06%) end in a `Constant` and cannot exhaust. The other 4,004 can — and they
appear in 327 of 567 packages.** Arity is 2 or 3 children, never more, never one.

**Contract.** An exhausted `FirstNonNull` **returns null and does not raise.** The reason is the
89%: ISO's own idiom is to append a total fallback when it wants a guaranteed value — very often the
literal string `Value Not Found`. Where it omits the fallback, it is deliberately allowing the null
to travel, and `@AllowNullReturn` exists downstream to receive it. **The engine records an exhausted
`FirstNonNull` in the trace**, because a null arriving at an arithmetic node is where this becomes a
defect, and that is where it must be caught.

### `Exist` / `NotExist` / `IsNull` / `IsNotNull`
`Exist` (8,105) and `NotExist` (10,216) are leaves testing a path's presence in the tree. `IsNull`
(12,061) and `IsNotNull` (17,832) take exactly one child and test its evaluated value. **Presence
and nullity are different questions and the corpus asks both** — a path can exist holding null.

---

## 5. Conditionals

Structure measured from `node_children.csv`, not assumed:

| Node | Children | Contract |
|---|---|---|
| `If` | `Test` 71,484 · `Then` 71,484 · `Else` **41,809** | `Test` and `Then` are mandatory and paired; **`Else` is optional and absent 41% of the time**. An `If` with no `Else` whose test is false yields null, not zero |
| `Test` | exactly 1 | evaluates to a boolean |
| `Then` / `Else` | exactly 1 | the branch value |
| `Choose` | `When` 12,346 · `Otherwise` 4,816 | evaluate each `When` in order, take the first whose `Test` is true; **`Otherwise` is optional** and its absence with no match yields null |
| `When` | `Test` + `Then`, exactly | same pairing as `If` |

`Test` most often holds `And` (34,401), then `IsNull` (11,944), `Equal` (9,385), `NotExist` (8,651),
`Or` (6,060), `NotEqual` (6,038).

**Comparison and boolean nodes.** `Equal` (82,096) and `NotEqual` (36,213) take exactly 2 children.
So do `GreaterThan` (6,928), `LessThan` (1,032), `LessThanOrEqual` (652) and `GreaterThanOrEqual`
(428). **`And` (37,945) and `Or` (12,933) are variadic — observed at 2 to 76 and 2 to 26 children.**

**Contract.** `And` and `Or` **short-circuit**, left to right. This is a decision, not a reading: the
corpus cannot show it, because nothing in the language has a side effect inside a boolean. It is
recorded here so that if a future filing puts a `RunRule` under an `And`, the behaviour is already
written down rather than discovered.

---

## 6. Arithmetic and rounding

| Node | Occurrences | Arity | Contract |
|---|---|---|---|
| `Sum` | 9,995 | 1 to 419 | add all children; over a `ForEach` (18,918 of its children) it is the aggregation idiom |
| `Product` | 7,608 | 2 to 10 | multiply all children, then apply `@DecimalPlaces` |
| `Subtract` | 1,045 | 2 | left minus right |
| `Divide` | 1,034 | 2 | left over right, then `@DecimalPlaces`. **Division by zero is a hard failure** |
| `Max` | 98 | 2 | larger of two |
| `Round` | 582 | 1 | round the child to `@DecimalPlaces` |
| `Truncate` | 66 | 1 | toward zero |
| `Count` | 1,713 | leaf | cardinality of a path |

### The rounding decision — **OPEN, and it stays open**

Every `@DecimalPlaces` in the corpus *(Q6, script 44)*:

| Node | Places in use |
|---|---|
| `Divide` | 0 (348) · 3 (37) · **8 (30)** |
| `Product` | 0 (5,284) · 3 (1,267) · 4 (120) |
| `Round` | 0 (238) · 2 (22) · 3 (290) · 4 (32) |

The 8-decimal case found on 12 August is real and lives on `Divide`. **No node anywhere declares a
rounding *mode*.** Half-up, half-even and truncate are indistinguishable in the content, and they
differ on exactly the inputs a rating engine hits constantly — a half-cent.

**Contract.** The mode is a single engine-wide setting, defaulting to **`ROUND_HALF_UP`**, and it is
**recorded in the trace on every rounded value**. It is not guessed per node and it is not hidden.
**This is the first thing the RAaS comparison in Phase 2 should be pointed at**, because a mode
mismatch produces small, systematic, everywhere differences — which is precisely what that
comparison is good at finding and what reading the files never will.

---

## 7. Lookup

`Lookup` (54,716) takes exactly one child, a `Keys` (54,716). `Keys` holds 2 to 10 children:
`Constant` (120,206), `Value` (30,832), `FirstValue` (7,803), `RunRule` (1,152).

`@ResultMode` *(Q7, script 44)*:

| Mode | Occurrences | Packages |
|---|---|---|
| `FirstResult` | 49,324 | **567 of 567** |
| `SingleResult` | 5,392 | 368 of 567 |

**Contract.** `SingleResult` matching more than one row is **a hard failure** — it is ISO asserting
uniqueness, and a violated assertion is a defect in our table loading or in the filing, either of
which must surface. `FirstResult` returns the first match **in filed row order**, and the engine
preserves that order from the CSV rather than sorting. Where the declared key is not unique (3.79%
of tables, measured in `10_key_uniqueness.py`), `FirstResult` is order-dependent and **the trace
records that a non-unique key was hit**, so a wrong answer is attributable rather than mysterious.

A `Lookup` that matches nothing returns null — which is what feeds the 3,920 exhaustible
`FirstNonNull`s in §4.

---

## 8. Dispatch

`RunRule` (173,204) is the third most common node in the language. `@Type` is `none` on 100,527 —
**most calls are for effect, not for a value.**

**`@ClearCache` is `true` on all 173,204 nodes that carry it.** *(script 42, N3)* P5 listed *"what
is cached and for how long"* as unspecified. **There is nothing to specify: the corpus never once
asks for a cached call.**

> **Contract. The interpreter does not memoise rule calls, at all.** This is a correctness decision
> before it is a performance one — rules write to a shared tree, so a cached call is only sound if
> nothing it touched has changed, and ISO evidently does not want us assuming that. If a future
> filing carries `ClearCache="false"`, that is **a hard failure**, not a silent optimisation.

Dispatch is three-way *(Q5, script 44)*:

| Kind | Occurrences |
|---|---|
| Sibling file, same package | 67,693 |
| Same file | 54,244 |
| **Parent package, via `@ProjectName`** | **51,267** |

`@ProjectName` names **10 distinct countrywide packages** — `GL CW 20260101 V01` (28,697),
`GL CW 20231201 V03` (11,782), `GL CW 20231201 V02` (3,839) and seven more. **This is N5 and N2
meeting in the content:** a state package calls into the countrywide parent *it declares*, by name,
and stage 1 already resolves exactly that parent.

**Contract (N2).** A call carrying `@ProjectName` dispatches to the declared parent package. **The
parent's own rules resolve within the parent and must not re-enter the state package** — the
4,598 call-super rules make an accidental recursion easy and non-obvious. The interpreter carries an
explicit current-package frame and **a parent-directed call cannot be re-parented**. Depth is
bounded and exceeding the bound is a hard failure, because the corpus's own call graph is acyclic
(measured in `23_rule_program.py` P4, 0 back-edges) and a cycle therefore means the engine is wrong,
not the content.

**Arguments.** `WithArgs` (6,506, 2 to 303 children) wraps a call; `Arg` (74,585) holds exactly one
child. Args are evaluated **before** the call, in order, in the caller's frame. **`Arg` most often
holds a `RunRule` (45,945)** — arguments are frequently themselves calls, which is why evaluation
order has to be stated rather than left to the implementation.

---

## 9. Iteration and the output tree

`ForEach` (49,604) iterates `@AtDataDef`, or `@AtInputDataDef` on 0.18% of nodes. It holds `RunRule`
(54,029), `FirstValue` (3,692), **`ForEach` (3,494 — it nests)**, `If` (2,948).

**Contract.** Iteration is in filed document order. The loop variable is a frame, not a global.
Nesting is supported to arbitrary depth. **A `ForEach` over an absent or empty path executes zero
times and is not an error** — that is how an absent coverage is meant to disappear.

The output-tree nodes are where an interpreter can quietly corrupt state:

| Node | Occurrences | Contract |
|---|---|---|
| `Locate` | 18,381 | positions subsequent writes at `@AtOutputDataDef`. `@OutputAction` is **`Append` on all 9,011 that carry it**; absent on the other 51%, which means *position at the existing node*. Holds a `Sequence` (17,024) evaluated in that position |
| `Remove` | 7,304 | leaf. **`@RemoveMultiple` is `true` on all 7,304** — removal is always all-matching, never first-matching |
| `Copy` | 2,122 | leaf; copies a subtree |
| `Guid` | 4,347 | leaf; **`@ToDataDef` is `ErcMessageTableId` on all 4,347 occurrences.** Its only job in this corpus is to identify a message row |

**`Guid` is the one node whose output cannot be reproducible**, and it is the only source of
non-determinism in the language. Because it writes nothing but a message-row identity, **the engine
generates them from a seeded, per-run counter rather than a random source**, so that two runs of the
same submission produce byte-identical traces and the Phase 2 RAaS diff is not full of false
positives.

---

## 10. Strings, dates, conversion

| Node | Occurrences | Contract |
|---|---|---|
| `Concat` | 1,317 | exactly 2 children, string join |
| `Length` | 370 | 1 child, string length. Only 20 packages |
| `PadLeft` | 150 | exactly 3 children. `@ToDataDef` is always a stat code — `LCMStatCode` (70), `ExposureStatCode` (70), `RatingModificationFactorStatCode` (10). **This is fixed-width statistical reporting, not arithmetic** |
| `Convert` | 1,525 | 1 child, retype to `@Type`. Nests inside itself (330) |
| `DatePart` | 800 | 1 child. `@UnitType` ∈ {`Months` 420, `Years` 320, `Days` 60} |
| `DateAdd` | 567 | 2 children. **`@ToDataDef` is `ExpDate` and `@UnitType` is `Years` on all 567** — it exists to do one job, §2 |
| `DateCreate` | 60 | exactly 3 children — year, month, day |
| `DateDifference` | 30 | 2 children, `@UnitType` always `Days` |
| `GetList` | 2 | the whole tail. Holds a `Constant` and a `Break`, in 2 packages |

---

## 11. The decisions, in one table

| # | Question | Verdict | Basis |
|---|---|---|---|
| C1 | Where does execution begin? | **ANSWERED** — the `Default` block of `Overall Rating.Rule.xml`, not `ErcProcess` | 567 of 567 packages, one shape |
| C2 | `FirstValue` four-way precedence | **ANSWERED** — two-way; `FromInput`/`FromParam` never filed, so unimplemented and a hard failure | 171,189 of 171,189 |
| C3 | `RunRule` caching | **ANSWERED** — never cache; `ClearCache="false"` is a hard failure | 173,204 of 173,204 `true` |
| C4 | Empty `Constant` — null or empty string? | **ANSWERED** — empty string; only ever `string`-typed | 20,520 of 20,520 |
| C5 | `Remove` multiplicity | **ANSWERED** — always all-matching | 7,304 of 7,304 `true` |
| C6 | `FirstNonNull` exhaustion | **CONSTRAINED** — returns null, does not raise, and is traced | 4,004 of 36,605 can exhaust, in 327 packages |
| C7 | `Lookup` non-unique key under `FirstResult` | **CONSTRAINED** — filed row order, and the trace records the collision | 3.79% of tables |
| C8 | `Locate` positioning | **CONSTRAINED** — `Append` where declared, position-at-existing otherwise | 9,011 declared of 17,916 |
| C9 | Parent dispatch and recursion (N2) | **CONSTRAINED** — explicit package frame, no re-parenting, bounded depth | 51,267 cross-package calls, 10 parents, acyclic |
| C10 | **Rounding mode** | **OPEN** — engine-wide `ROUND_HALF_UP`, traced on every rounded value, first target of the RAaS diff | no mode declared anywhere |
| C11 | `And`/`Or` short-circuit | **OPEN but inert** — short-circuit, left to right; nothing in the corpus can observe the difference | decision, recorded against future filings |
| C12 | `Break` | **OPEN** — hard failure; 68 of 84 occurrences are inside `Sum`, which the name does not explain | OI-74 |

**Four questions P5 called unspecified turned out to have exactly one answer in the content.** The
language ISO *declares* is materially larger than the language ISO *uses*, and the difference is
where an interpreter would otherwise have had to guess.

---

## 12. What the engine refuses to do

Carried forward from stage 1, whose whole purpose was refusing to guess:

1. **An unknown node type is a hard failure.** All 54 are enumerated; a 55th means ISO filed
   something new and the engine must stop rather than skip it.
2. **An unknown attribute value is a hard failure** — `ClearCache="false"`, a `FirstValue` with
   `FromInput`, a fifth `@Type`, a rounding place not in {0,2,3,4,8}.
3. **Null reaching arithmetic is a hard failure**, not a coerced zero.
4. **`SingleResult` matching more than one row is a hard failure.**
5. **Division by zero is a hard failure.**
6. **A missing `Default` block is a hard failure.**

Every one of these is a case where the alternative is a complete, plausible, wrong premium.

---

## 13. What this changes about the build

**Stage 2 gets smaller and stage 3 gets a correction.**

Smaller, because C2, C3, C4 and C5 remove four of the guesses the interpreter was expected to
carry, and the long tail is 9 nodes rather than 14.

Corrected, because **§2 moves the entry point.** The kernel in stage 3 was specified as
*submission → resolved packages → execute → premium*, and "execute" was going to mean `ErcProcess`.
It has to mean the `Default` block, which brings `ExpDate`, the `Policy` node, the per-risk loop and
`ErcCalculateTotalPremium` inside the engine's responsibility rather than the caller's.

**The order of implementation follows the coverage curve.** The top 20 nodes are 94.03% of the
corpus and are the first target; the 9-node tail is last, and `GetList`, at 2 occurrences in 2
packages, may reasonably be left as a hard failure until something needs it.

---

## 14. Open items raised by this document

| Item | |
|---|---|
| **OI-70** | The rounding mode is undeterminable from the content (C10). Resolvable only against RAaS or an ISO clarification. First target of the Phase 2 diff |
| **OI-71** | `23_rule_program.py` P5's operator census is missing `Default` and `DateAdd`; any figure quoting "52 operators" is superseded by the 54 here |
| **OI-72** | The plan's "14 node types under 500 occurrences" is 9. Correct where quoted |
| **OI-73** | Five packages are unpacked twice under a `_MachineReadableContent` wrapper. Byte-identical, and both the engine and these scripts de-duplicate — recorded so no future count reports 572 |
| **OI-74** | `Break`'s semantics are undetermined. 68 of 84 occurrences are inside `Sum`, not inside a loop. Hard failure until something needs it |

---

**Next:** `gl_engine/interp/` — the node evaluators, written against this contract, top 20 first.
The eleven coverage walkthroughs are the acceptance target, and the contract above is what they are
checked against.
