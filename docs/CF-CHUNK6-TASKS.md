# Property chunk 6 — task list and status

**Special Class: the class-description chain and all four cause-of-loss forms.**
Opened 2026-09-18.

Derived from `CF_Algorithm/CauseOfLoss_SpecialClass_RatingAlgorithms.md` and
from the census run while opening the chunk
([`40_chunk6_census.py`](../scripts/cf/40_chunk6_census.py)) — not from an
assumption that Special Class is Building with a different key.

**No engine code is expected.** Chunks 1–5 all ran on chunk 0's foundation
unchanged — and **chunk 6 now does too** (C6-02). Nothing new was built.

**Tracked live** as **C6-01 … C6-29**, numbered to match this page.

| Task | Cannot start until |
|---|---|
| C6-02 chain runs | C6-01 golden cases |
| C6-03 zero cases | C6-02 |
| C6-04 state sweep | C6-03, **C6-11** (Florida's edition gap), **C6-12** (New York's deleted converters) and **C6-19** (the eight states with no lowest-rate table) |
| C6-10 the description→option→rate chain | C6-01 |
| C6-08 ISO confirmation | C6-04 |
| C6-09 gate document | C6-03, 04, 05, 06, 07, 08 |

**All 29 tasks are done.** — all nine gate-level tasks, the class-description chain ([`CF-CHUNK6-DESCRIPTION-CHAIN.md`](CF-CHUNK6-DESCRIPTION-CHAIN.md)) C6-15–C6-19 ([`CF-CHUNK6-PER-FORM.md`](CF-CHUNK6-PER-FORM.md)) C6-20–C6-23 ([`CF-CHUNK6-FORMS.md`](CF-CHUNK6-FORMS.md)) and C6-24–C6-29 ([`CF-CHUNK6-CROSSFORM.md`](CF-CHUNK6-CROSSFORM.md)). **Chunk 6 is gated at 8 of 9** ([`CF-CHUNK6-GATE.md`](CF-CHUNK6-GATE.md)); the only outstanding point is 9 (validation messages), owed on all six chunks alike. The 20 coverage-specific tasks remain and are independently startable — **C6-22 and C6-26 were settled early by the ISO run** and need writing up rather than testing.

---

## What is structurally new, before any task runs

**1 · The rating driver is a free-text class DESCRIPTION, not a class code.**
Basic Group I's base rate is looked up on `SpecialClassDescConvertedOption` —
itself the result of mapping the submitted `ClassDescription` through
`SpecialClassDescriptionConvertedOption` to one of 71 filed `OptionNN` codes.
**Two lookups in series, and the first one is on a long English string.** Group
II does the same thing through a second, separate table
(`SpecialClassBasicGroupIINumber`). There is no `ConstructionCode` key in Group
I's base rate at all.

**2 · Protection class is a KEY here, not a factor.** It is folded into the
Group I base-rate lookup. `ProtectionClassFactor` is still computed — last, after
every chain has run — and then **never read by any rate chain**. The first
orphaned factor found in the project that is not merely unused but computed
after the point where it could have been used.

**3 · Nine rating concepts Building has are simply absent.** LOI factor, roof
surfacing (ACV and cosmetic), BCEG, sprinkler leakage, substandard and vacant
rate addends, `MultiResidentialPropSpecialCreditFactor`, the `CovType` taxonomy,
and the Legal Liability branch. Every premium file has **two** branches —
blanket or scheduled.

**4 · Basic Group I and II are never gated on the cause of loss.**
`SetCoverageOnPolicyIndicator` is **hard-coded to 1** in both files. Broad and
Special use an exact `CauseOfLossToUse` match, as everywhere else. The pattern
that has held for three chunks running — "each form gates on the cause of loss"
— is **half false here**, and that is exactly the shape a fourth chunk would
inherit without checking.

**5 · Broad's base rate is construction-blind.** `LookupBroadFormBaseRate` keys
on the hard-coded literal `"Frame"`. Building's reads the item's actual
construction and moves 0.015 → 0.010. A Special Class fire-resistive item pays
the frame rate.

---

## The state layer — the loudest since chunk 2

| Table | CW rows | States declaring their own |
|---|---|---|
| `BasicGroupIRateSpecialClass` | 213 | 3 — **FL 204, NY 189, PR 213** |
| `SpecialClassDescriptionConvertedOption` | 71 | 2 — **FL 68, NY 0 (header-only)** |
| `SpecialClassBasicGroupIINumber` | 71 | 3 — FL 68, **NY 0, PR 0 (header-only)** |
| `BasicGroupIIRate` | **0 — header-only** | 45; **FL and PR file none either** |
| `LowestBasicGroupIIRate` | **0 — header-only** | 39; **AR, DC, FL, KS, NY, PR, RI, TX file none** |
| `SpecialBuildingRate` | **0 — header-only** | 45; FL and PR file none |
| `BroadFormBaseRate` | 30 | 1 — PR |
| `SpecialBldgTheftExclusionFactor` | 1 | 30 |
| `BasicGroupIIFlatCoinsuranceFactor` | 1 (**1.5 — a surcharge**) | 2 — FL, PR |
| `DeductibleFactor` | 240 | 45 |
| `Deductible250Factor` | 4 | **0 of 47** |
| `ProtectionClassFactor` | 168 | 2 — NC, PR |

**Rule deletions, on rating rules, in four places.** Chunk 5 found the first
rating rule any state empties to `<rul:Sequence />`. Chunk 6 finds four more:

| Rule | Deleted by |
|---|---|
| `SetSpecialClassDescConvertedOption` | **NY** |
| `SetBasicGroupIISymbolNum` | **NY, PR** |
| `SetSpecialTheftExclusionFactor` | **PR** |
| `SetProtectionClassFactor` | **PR** |
| `SetBasicGroupIINumericValue` | **NY** |

Everything else is ordinary override traffic: `SetBasicGroupIICauseOfLossAdjustment`
by 11 (AL, AR, DC, FL, GA, KS, NY, PR, RI, TX, VT — the same shape chunk 5 found
at 10), `SetBasicGroupIINumericValue` by 7, `SetBasicGroupICauseOfLossAdjustment`
by 6, `SetCoinsuranceFactor` by 5, and nothing at all on
`SetBasicGroupIBaseRate`, `SetAdjustedBasicGroupIRate`,
`SetDeductibleFactorBasicGroupI`, `SetAdjustedBroadRate`,
`SetDeductibleFactorBroad` or `SetDeductibleFactorSpecial`.

---

## Gate-level tasks

| # | Task | Status | Evidence |
|---|---|---|---|
| 1 | Golden case, hand-derived before code — one per form | ✅ | [`41_chunk6_golden_case.py`](../scripts/cf/41_chunk6_golden_case.py) — BGI **$66**, BGII **$209**, Broad **$14**, Special **$44**; Building unmoved at 261/32. **Every predicted intermediate landed on all four forms — the first chunk needing no rate-step correction.** See [`CF-CHUNK6-GOLDEN-CASE.md`](CF-CHUNK6-GOLDEN-CASE.md) |
| 2 | Chain runs, on chunk 0's foundation, with no new interpreter node | ✅ | **No new node.** A sixth coverage on the same machinery — and the first that is not inside a building record: Special Class hangs off the **Location**, a sibling of the Structure |
| 3 | Zero cases — including an absent and a misspelled `ClassDescription` | ✅ | [`42_chunk6_zero_cases.py`](../scripts/cf/42_chunk6_zero_cases.py) — 6 cases, all matching first run. **A description ISO itself files in Florida prices at zero in Oregon**, and an absent `Deductible` takes all four forms at once. See [`CF-CHUNK6-ZERO-CASES.md`](CF-CHUNK6-ZERO-CASES.md) |
| 4 | 47-jurisdiction sweep, each premium predicted from that state's own rows | ✅ | [`43_chunk6_enumerate_states.py`](../scripts/cf/43_chunk6_enumerate_states.py) — **47 of 47**, the first complete sweep since chunk 3. **Three jurisdictions correctly produce no premium at all** (AZ, FL, NY) and **none of the three is a missing rate**. See [`CF-CHUNK6-STATE-SWEEP.md`](CF-CHUNK6-STATE-SWEEP.md) |
| 5 | Shared-name adjudication — the SpecialClass half | ✅ | `04_shared_names.py` now reports all six chains — **39 shared names, 13 reading different tables**. **Chunk 3's prediction held a third time.** And `SetBasicGroupIISymbolNum` is the sharpest reuse in the project: **five coverages, five different tables, one rule name** |
| 6 | Exclusion records — Special Class files its **own** records | ✅ | `05_exclusion_records.py` gained a per-group chunk 6 section. Vandalism, wind/hail and theft each file a `*SpecialClass` record; **cyber files one record at the POLICY level** and reaches all four premium files — the terrorism shape again |
| 7 | Hardcoded literals — the Special Class set | ✅ | `08_hardcoded_literals.py --group CommercialPropertySpecialClass` — **36 pinned sites, 14 that kill filed rows**. **Broad's `"Frame"` makes 5 of 6 construction values unreachable from every site**, and `ProtectionClassFactor` is a dead lookup inside a factor nothing reads. **`PolicyType` is tested 20 times** — the census where C6-01's trap would have been caught first |
| 8 | ISO confirmation | ✅ | [`44_chunk6_raas.py`](../scripts/cf/44_chunk6_raas.py) — **7 calls, 7 agreements**, message counts matching on every one. **The $209 numeric-value-of-8 confirmed**, and **Broad confirmed construction-blind** (Fire Resistive returns $14 again). **One divergence: ISO REFUSES where we return $0** — logged as **OI-99**. See [`CF-CHUNK6-ISO-CONFIRMATION.md`](CF-CHUNK6-ISO-CONFIRMATION.md) |
| 9 | Gate document | ✅ | [`CF-CHUNK6-GATE.md`](CF-CHUNK6-GATE.md) — **8 of 9**. Point 9 (validation messages) is owed on all six chunks alike. **Point 8 sharpened**: ISO's own error named three different editions in one call, so the edition basis is not one date |

## The class-description chain — the chunk's central machinery

| # | Task |
|---|---|
| 10 | ✅ **Both keys move the rate on their own** — description → Option2 takes the base 0.07 → 0.286 (**$267**), and the protection-class band takes it 0.286 → 0.368 → 0.448 (**$343 / $417**), a 56% spread with no factor in the chain. **Removing the protection class was predicted at $0 and came back $417**: an absent band resolves to `9 to 10`, the WORST one, so the premium goes UP — the only absent field in chunk 6 that charges rather than costs. **And the deductible band is settled**: a second item on the location separates the two readings and the answer is the ITEM's own limit (**$267**, not $269) |
| 11 | ✅ **Florida is not a private namespace — it is an OLD EDITION, and this page said otherwise before checking.** FL resolves over `CF_CW_20230801_V01`; almost everyone else over `CF_CW_20260601_V01`. Against **its own** parent: **3** descriptions added, **6** dropped, **0** option codes outside its parent's set, **0** remapped. The "11 Florida-only descriptions" first published here came from diffing against the 2026 table — **8 of the 11 were an artefact of comparing across editions**. The three it adds are the **old names** of classes countrywide renamed |
| 12 | ✅ **The 189 rows ARE reachable — by submitting the option, which the deleted rule cannot overwrite.** NY `Option1a` → base 0.43 → **$393**; nothing submitted → **$0**. **A deleted rule is how ISO says a field is an INPUT.** And **the private namespace is New York's**: 63 codes to countrywide's 71, **35 of them nowhere countrywide**, `Option34a` absent — so a countrywide code submitted into NY misses, and NY's own converter is header-only, so nothing in the corpus can produce one |
| 13 | ✅ **Three coordinated edits, twice.** NY and PR each file the number table header-only, empty `SetBasicGroupIISymbolNum`, **and rewrite `SetBasicGroupIIRate` so it never reads the term.** Not a hole — a different chain. NY still rates Group II at **$55**; PR prices **$0** for a separate reason (no Group II base rate anywhere). **And the value cannot be supplied either**: submitted, OR overwrites it and NY never reads it — the same field ignored for opposite reasons |
| 14 | ✅ **Seven spellings: one worth $66, six worth nothing, no reported difference.** Case, a trailing space, `&` for `and`, a doubled space, **an en dash for the hyphen** — the one a word processor makes by itself — and Florida's own filed spelling |

## Per-form specifics

| # | Task |
|---|---|
| 15 | ✅ **Four branches, and branch 3 is a SURCHARGE.** 80% → 1.0 → **$69**, 90% → 0.95 → **$66**, 100% → 0.9 → **$62**, and **50%/60% → 1.5 → $103**. `LessThan80PctMultiplicativeFactor` files one countrywide row at 1.5, so insuring to less than 80% costs **56% more**, not less — the first coinsurance penalty in the project. **One factor serves three forms**: at 50% Broad goes $14→$22 and Special $44→$69. Group II is the exception and reads a *different* table filing the same 1.5 — two tables, one number, nothing in a premium could tell them apart |
| 16 | ✅ **The proof is arithmetic**: `BasicGroupIRate` = 0.07 = base × LCM exactly, while `ProtectionClassFactor` sits at **0.96** on the same record — 0.07 × 0.96 would be 0.067. Protection class reaches the premium as the second lookup key and nowhere else; C6-10 moved it across three bands and the base rate followed 0.286 → 0.368 → 0.448 |
| 17 | ✅ **Read by nothing.** 2 reads in the whole ruleset, **both inside its own `IsNull` guards** — 0 by any rate chain. **PR deletes the rule and still rates Group I at $64.** It runs LAST, after all five chains, and carries a pinned key (`ConstructionCode = 1`) that kills 140 of its 168 rows: **a dead lookup inside a dead factor, computed too late to matter** |
| 18 | ✅ **Answered: it is a submitted field.** Three datadef groups derive the Group II symbol — Structure, PersonalProperty, BuildersRiskRenovations — and **SpecialClass is not one of them**. AA/A/AB/B give **$112 / $120 / $178 / $209**. This explains C6-03's case 5, and means chunk 6's payload carries a field chunks 1–5 never sent: a builder that derives it the Building way is right for four coverages and silently wrong for this one |
| 19 | ✅ **A biconditional, zero exceptions in 47.** 39 states file `LowestBasicGroupIIRate`; **the same 39 are exactly those whose rule can still reach the read**. The 8 non-filers (AR, DC, FL, KS, NY, PR, RI, TX) are all inside the 11 overriders, and the 3 overriders that kept the read (AL, GA, VT) all file the table. **The header-only countrywide table is not a gap — it is a table nobody reads countrywide.** First time two censuses have been matched against each other |
| 20 | ✅ **Two strings, not Building's four** — and the two that are missing are the two naming sprinkler leakage, which Special Class has no concept of. `Fire and Sprinkler Leakage` **zeroes a Building's Group II ($32 → $0) and leaves a Special Class item's at $209**: one submission field, two coverages, opposite answers |
| 21 | ✅ **Florida is the discriminator.** Countrywide both tables file 1.5, so nothing in an Oregon premium could tell them apart; **FL files `BasicGroupIIFlatCoinsuranceFactor` at 1.42** and leaves `LessThan80PctMultiplicativeFactor` countrywide — so the two Basic forms take different surcharges from one apparent concept. Group II at 50% costs **$329** against 90%'s $209. **PR declares both tables header-only** — no coinsurance surcharge at all, expressed as two empty tables |
| 22 | ✅ **$14 at Frame and $14 at Fire Resistive, while Building moves $16 → $12** on the identical change. **The first draft proved nothing**: it sent six construction strings copied out of the rate table's key column, four of which `ConstructionTypeToUse` never resolves to — a test that sends an unrecognised string and reports "unchanged" cannot tell construction-blindness from a bad input. **And Building's FR was predicted at $11 and is $12**: the chain rounds at 3dp every step, so a two-thirds rate does not give a two-thirds premium |
| 23 | ✅ **`SpecialBuildersRiskRate` is named 6 times in the Structure ruleset and 0 times here.** Class **1150 does nothing** — base stays 0.047, premium stays **$44**. And `SpecialBuildingRate` is header-only countrywide, so **FL and PR cannot price the Special form at all** — the same two states, the same table and the same silence chunk 3 found on Building, now reached through a second coverage |

## Cross-form claims

| # | Task |
|---|---|
| 24 | ✅ **0 countrywide files and 0 across all 47 jurisdictions**, scanned in the main ruleset and all four premium files — against Building, which names one. Special Class multiplies the final rate by `Limit/100` with nothing in between |
| 25 | ✅ **Same treatment, same answer** — 0 of 5 countrywide files, 0 across 47. Building multiplies it into every form's final rate; scheduled Special Class property does not get it |
| 26 | ✅ **Half the inherited pattern is false.** `SetCoverageOnPolicyIndicator` has **no `Test` at all** in the Basic Group I and II files; Broad and Special have one. A `Broad` submission and a `Special` submission both return Basic **$66 / $209**. **ISO confirmed it independently** in C6-08 — the Broad call's total was $289, the Basic pair's $275 *plus* $14 |
| 27 | ✅ **The algorithms page had it backwards, and is now corrected in six places.** All four Special Class premium files are nested `Product DecimalPlaces="0"` with **zero `rul:Round`** — Building's *Special-form* convention on every form. Building's own Basic/Broad files carry 6 `rul:Round` each. **The premium rounds to 0 dp at six nested levels**, so every factor after the first multiplies an already-rounded dollar figure — and the cyber factors are *inside* the nest, not outside |
| 28 | ✅ **Predicted $100, got $0 — and the reason is the finding.** The branch IS taken (`FinalBasicGroupIRate` is still 0.066, computed and never read), but **two of the four blanket inputs are overwritten**: `BlktTotalFullValueAmount` → 0 and `BlktCauseOfLossValue` → blank, both written by `SetNonEQBlanketValues` from policy-level blanket records. **The two it discards are exactly the two the formula cannot do without** — a silent $0 with half the submitted inputs thrown away. Sixth derived-field trap in the chunk; chunk 9 now has a named starting point |
| 29 | ✅ **Building 263/32, Contents 223/24, Business Income 112/13, Special Class 66/209** — all on one submission, each unchanged from its own chunk. Special Class is a **sibling** of the Structure, so its limit never reaches Building's `TotAmtInsurance`. The isolation check at four coverages; chunk 5 ran it at three |

---

## What chunk 6 inherits and must re-ask

* **Building's rate-step rounding is still an open question** (per-factor vs once) and Special Class's chains are shorter, so they may discriminate where Building's did not. Carry it into C6-01.
* **A submission can populate a derived field** when the rule is guarded, and an unguarded rule discards one. C6-12 is that question asked by a state rather than by us.
* **Chunk 3's shared-name adjudication predicted this chunk's Group I table.** C6-05 is its third test.
