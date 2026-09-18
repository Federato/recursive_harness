# Property chunk 6, tasks C6-10 to C6-14 — the class-description chain

2026-09-18. Script:
[`scripts/cf/45_chunk6_description_chain.py`](../scripts/cf/45_chunk6_description_chain.py).

**This page corrects a claim chunk 6 made and published before it was checked.**
See "The correction" below; it is the most important thing on the page.

---

## C6-10 · Two lookups in series, moved one at a time

Baseline: `Towers - Broadcasting Antennas (Cell, Radio and TV)` → `Option34a`,
protection class 3 → band `"1 to 4"` → base 0.07 → **$66**.

| Change | Option | Band | Base | **Premium** |
|---|---|---|---|---|
| — | Option34a | 1 to 4 | 0.07 | **$66** |
| description → `Aircraft Stored in the Open` | **Option2** | 1 to 4 | 0.286 | **$267** |
| protection class 3 → **6** | Option2 | **5 to 8** | 0.368 | **$343** |
| protection class 3 → **9** | Option2 | **9 to 10** | 0.448 | **$417** |
| **protection class removed** | Option2 | **9 to 10** | 0.448 | **$417** |

Both keys move the rate on their own, which is what "two lookups in series"
has to mean before it means anything. Protection class spreads the same class of
property by **56%** with no factor anywhere in the chain.

### The last row was predicted at $0 and came back $417

Predicted: an absent `ProtectClass` blanks `ProtectionClassToUse`, the base-rate
gate fails, the premium is zero — the shape every other missing field in this
chunk has.

**It is the opposite.** The Location resolves an absent protection class to
**`"9 to 10"`, the worst band**, and the premium goes **up 56%**. Every other
absent field in chunk 6 costs coverage; this one charges for it. The prediction
was wrong and the disagreement is the finding.

### And the deductible band question is settled

C6-01 and C6-03 both had to leave open whether `TotAmtInsuranceToUse` follows
the **item** or the **location**, because with one 100,000 item the two readings
give the same factor. **A second Special Class item separates them:**

    item's own total  100,000 -> band 50k-175k -> 0.98 -> $267
    location total    200,000 -> band 175k-500k -> 0.99 -> $269

The engine returns **$267** and `TotAmtInsuranceToUse = 100000`.
`SetTotAmtInsurance` copies `Limit` when the item is not blanketed, and the band
keys on that copy. **It is the item's own limit.**

---

## The correction — Florida is not a private namespace, it is an old edition

**What chunk 6 published on 2026-09-18, before checking:**

> Florida files a private option namespace. FL's codes are `Option1`,
> countrywide's are `Option1a` — **not one code in common**. FL files 68
> descriptions: 57 shared, **11 of its own**, and it drops 6 countrywide ones.

**Every quantified part of that is wrong**, and it was wrong because the opening
census diffed **all 47 jurisdictions against one countrywide table** — whichever
jurisdiction happened to sort first.

| | |
|---|---|
| Florida's resolved parent | **`CF_CW_20230801_V01`** |
| Oregon's, New York's, almost everyone's | `CF_CW_20260601_V01` |
| Option codes Florida files outside its own parent's set | **0** |
| Shared descriptions Florida maps to a different code | **0** |
| Descriptions its own parent does not file | **3** |
| Descriptions it drops from its own parent | **6** |
| The same table diffed against the **2026** parent | 11 — **8 of them an artefact** |

**Florida shares every option code with its own parent and remaps none of them.**
There is no private namespace. What Florida is, is **two countrywide editions
behind**: its vocabulary is frozen at 2023, before ISO renamed the antenna
classes to add `Cell` and added EV charging stations, freestanding solar arrays
and wind turbines.

The three descriptions Florida "adds" are the **old names of classes countrywide
renamed**:

    Towers - Broadcasting Antennas (Radio and TV)      <- CW now: "(Cell, Radio and TV)"
    Towers - Receiving Antennas (Radio and TV)         <- CW now: "(Cell, Radio and TV)"
    Towers - Windmills                                 <- CW now: two "Wind Towers - ..." classes

**The mechanism chunk 6 reported was right and the diagnosis was wrong.** The
golden case genuinely cannot rate in Florida, ISO genuinely refuses it, and the
reason is an edition gap rather than a filing style. The census script now diffs
each state against **its own resolved parent** and says so when the editions
differ.

**The standing lesson:** a state-vs-countrywide diff is only meaningful against
*that state's* countrywide layer. Comparing across editions manufactures
differences, and it manufactured them in exactly the place this chunk was about
to draw a headline.

---

## C6-11 / C6-12 · The private namespace is New York's

| | |
|---|---|
| New York option codes | **63** |
| Countrywide option codes | **71** |
| Codes only New York files | **35** |
| Countrywide codes New York lacks | **43** |
| Shared | **28** |
| Is the golden case's `Option34a` in New York? | **no** |

New York files `Option12a`, `Option12b1`, `Option26a2`, `Option27b3` where
countrywide files `Option12`, `Option26`, `Option27a`. **A countrywide option
code submitted into New York misses** — which is exactly what happened on the
first run of this task, and why the claim now attached to New York had to be
taken off Florida.

---

## C6-12 · New York's 189 filed rows ARE reachable

| Case | Base | **Premium** |
|---|---|---|
| NY, `SpecialClassDescConvertedOption = "Option1a"` submitted | 0.43 | **$393** |
| NY, nothing submitted | 0 | **$0** |

    r3(0.43 x coins 0.95) = 0.409   x   CW deductible 0.96   ->   0.393   ->   $393

**An emptied rule cannot overwrite what the submission supplies.** New York's
`SetSpecialClassDescConvertedOption` is `<rul:Sequence />`, so the field survives
exactly as sent. **The deleted rule is not a dead end — it is how ISO says the
field is an input in New York.**

But the code has to be New York's own, and **nothing in the corpus maps a
description to one**: NY's converter table is header-only. The 189 rows are
reachable only by a caller that already knows New York's private vocabulary from
somewhere outside the ERC package.

The difference between **$393 and $0** in New York is one field no other
jurisdiction wants, with no message either way.

---

## C6-13 · Three coordinated edits, in two states

Neither New York nor Puerto Rico has a "hole" where the Group II numeric value
should be. Each makes **three edits that agree with each other**:

| | NY | PR |
|---|---|---|
| `SpecialClassBasicGroupIINumber` | header-only | header-only |
| `SetBasicGroupIISymbolNum` | emptied | emptied |
| `SetBasicGroupIIRate` | **rewritten to drop the term** | **rewritten to drop the term** |
| Group II premium | **$55** | **$0** |

Oregon multiplies its base rate by **8**; these two have no such concept at all.
Puerto Rico then prices Group II at zero for a **separate** reason — it files no
Group II base rate, state or countrywide.

### And the numeric value cannot be supplied, for two opposite reasons

| | Submitted `BasicGroupIISymbolNum = 2` |
|---|---|
| OR | **$209, unchanged** — the live rule overwrites it from the lookup |
| NY | **$55, unchanged** — the rate rule never reads it |

**The same submitted field is ignored in two states for opposite reasons** — and
C6-12 showed the converted *option* going the other way in one of them. A
deleted rule makes a field an input; a live unguarded rule makes it a decoy.
Nothing in the payload distinguishes the two.

---

## C6-14 · Near-miss spellings

| Spelling | Premium |
|---|---|
| `Towers - Broadcasting Antennas (Cell, Radio and TV)` | **$66** |
| `Towers - Broadcasting Antennas (Radio and TV)` — Florida's | $0 |
| all lower case | $0 |
| one trailing space | $0 |
| `&` for `and` | $0 |
| one doubled space | $0 |
| an en dash for the hyphen | $0 |

**Seven spellings, one worth $66 and six worth nothing, and the engine reports
no difference between them.** The en-dash case is the one to worry about: a word
processor makes that substitution by itself.

ISO's own list runs to 100 characters with abbreviations like `Undrgrd` and
`Incldg`. This is the fourth absent-means-zero family in the project and the
only one where the input is prose.
