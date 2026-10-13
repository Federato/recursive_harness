# Property chunk 6, tasks C6-15 to C6-19 — the per-form specifics

2026-09-18. Script:
[`scripts/cf/46_chunk6_perform.py`](../scripts/cf/46_chunk6_perform.py).

Every figure was derived by hand from Oregon's filed rows before the run and
**all of them landed**. Baseline: base 0.07, deductible 0.98, Basic Group I
**$66**.

---

## C6-15 · Coinsurance is computed first, shared by three forms, and branch 3 is a surcharge

| `Coinsurance` | Branch | Factor | **Basic Group I** |
|---|---|---|---|
| 80% | 1 | **1.0** | **$69** |
| 90% | 1 | 0.95 | **$66** |
| 100%, not blanketed | 1 | 0.9 | **$62** |
| **50%** | **3** | **1.5** | **$103** |
| **60%** | **3** | **1.5** | **$103** |

**Insuring to less than 80% of value costs 56% more, not less.**
`LessThan80PctMultiplicativeFactor` files **one countrywide row at 1.5**. Every
coinsurance factor in chunks 1–5 ran at or below 1.0, so this is the first
coinsurance *penalty* in the project — and the first place where a lower
coinsurance percentage raises the premium.

**The table has one row, so 50%, 60% and 70% price identically.** A three-value
distinction the submission can make and the rate cannot.

### One factor, three forms

| Form | at 90% | at 50% |
|---|---|---|
| Basic Group I | $66 | **$103** |
| Broad | $14 | **$22** |
| Special | $44 | **$69** |

Broad and Special define **no coinsurance rule at all**. They read the value
Basic Group I's chain computed **first**, before any base rate — the reverse of
Building, where coinsurance comes after the rate and the cause-of-loss
adjustment.

**Basic Group II is the exception, and it hides a trap.** It has its own rule,
and on 50% it reads a *different* table — `BasicGroupIIFlatCoinsuranceFactor` —
which happens to file **the same 1.5**. Two tables, one number, and nothing in
any premium could tell them apart. If either state-files a different value, the
two forms diverge silently.

---

## C6-16 / C6-17 · Protection class is a key; the factor is dead

    band (a KEY)          = "1 to 4"
    base rate             = 0.07
    rate                  = 0.07      <- base x LCM, exactly
    ProtectionClassFactor = 0.96      <- populated, and nowhere in that product

**0.07 × 0.96 would be 0.067.** The factor is computed and the rate does not
contain it. Protection class reaches the premium as the second key of
`BasicGroupIRateSpecialClass` and nowhere else — C6-10 moved it across three
bands and the base rate moved with it, 0.286 → 0.368 → 0.448.

### The factor is read by nothing

| | |
|---|---|
| Reads of `ProtectionClassFactor` in the whole ruleset | **2** |
| …of those, inside `SetProtectionClassFactor` itself (its own `IsNull` guards) | **2** |
| **Reads by any rate chain** | **0** |

And **Puerto Rico deletes the rule** — `<rul:Sequence />` — and still rates
Group I at **$64**. Deleting a rule that nothing reads changes no premium; it is
the cheapest possible confirmation and Puerto Rico filed it for us.

`SetProtectionClassFactor` runs **last**, after all five `Set*RatesAndFactors`
chains — *after* the point where it could have been used. It also carries a
pinned lookup key (`ConstructionCode = 1`, C6-07) that makes 140 of its 168
filed rows unreachable. **A dead lookup inside a dead factor, computed too late
to matter.**

---

## C6-18 · `BasicGroupIISymbol` is a plain input here

Three datadef groups **derive** the Group II construction symbol:

    CommercialPropertyStructure                 (from construction + storeys)
    CommercialPropertyPersonalProperty          (copies the Structure's)
    CommercialPropertyBuildersRiskRenovations

**`CommercialPropertySpecialClass` is not one of them.** It reads the field and
never writes it — so the algorithms page's open question is answered: it is a
**submitted field on the Special Class item**.

| Symbol | Base rate | **Group II premium** |
|---|---|---|
| AA | 0.015 | **$112** |
| A | 0.016 | **$120** |
| AB | 0.024 | **$178** |
| B | 0.028 | **$209** |

Two consequences:

* **C6-03's case 5 is explained.** Removing the symbol prices Group II at zero
  and nothing recomputes it, while Building's own Group II — which derives its
  symbol — is unmoved in the same run.
* **Chunk 6's payload has to carry a field chunks 1–5 never sent.** A submission
  builder that derives the symbol the Building way will be right for four
  coverages and silently wrong for this one.

---

## C6-19 · The lowest-rate table and the rule that reads it — a biconditional

| | |
|---|---|
| Jurisdictions | 47 |
| File their own `LowestBasicGroupIIRate` | **39** |
| File none | **8** — AR, DC, FL, KS, NY, PR, RI, TX |
| Override `SetBasicGroupIICauseOfLossAdjustment` | **11** — the 8 above plus AL, GA, VT |
| …whose override **still reads** the lowest rate | **3** — AL, GA, VT |
| States whose rule can **reach** the read | **39** |
| **Is the reach-the-read set the same as the files-own set?** | **Yes — exactly** |

**Zero exceptions in 47.** Every state whose rule can still reach
`LowestBasicGroupIIRate` files it; every state that cannot, does not. The
countrywide table being header-only is not a gap — **it is a table nobody reads
countrywide**, because the countrywide rule reaches it only on the wind/hail-
excluded branch and every state that uses that branch files its own rows.

The eleven overrides sort cleanly by whether they kept the wind/hail rebuild:

| Shape | States |
|---|---|
| Keeps the lowest-rate read and the wind/hail factor | **AL, GA, VT** — and all three file the table |
| Drops the read; keeps a wind/hail factor | **TX** |
| Drops the read and the wind/hail branch entirely | **AR, DC, FL, KS, NY, PR, RI** — NY's is 303 characters, the shortest override in the chunk |

**This is the first time in the project that two censuses have been matched
against each other**, and the answer is that a missing table and a rewritten
rule were *one filing decision seen from two sides*. Chunk 5 found the same
rule overridden by ten states and classified them by the size of the override;
this goes one step further and shows the table census predicts the rule census
exactly.

**The standing lesson:** a header-only table is a question, not a defect, and
the answer is usually in the rules rather than in the data. Chunk 2 and chunk 4
both spent effort on header-only tables that turned out to be read by nobody
who mattered.
