# Property chunk 4 — task list and status

**Contents (Personal Property), all four forms.** Opened 2026-09-18.

Built **differentially against chunks 1–3**: most of the chain is shared, and
what differs is what this chunk has to prove. The task list below is derived
from `CF_Algorithm/CauseOfLoss_PersonalProperty_RatingAlgorithms.md` and from
censuses run while opening the chunk — not from an assumption that Contents is
Building with a different table name.

**No engine code is expected.** Chunks 1, 2 and 3 all ran on chunk 0's
foundation unchanged; if chunk 4 needs a new node, that is itself the finding.

**Tracked live.** All 32 tasks are in the session task list as **C4-01 … C4-32**,
numbered to match this page. Dependencies are recorded there rather than left to
memory:

| Task | Cannot start until |
|---|---|
| C4-02 chain runs | C4-01 golden cases |
| C4-03 zero cases | C4-02 |
| C4-04 state sweep | C4-03 **and C4-31** — the sweep must not run before AK/CA/PR are understood, or it repeats chunk 3's skip-as-unrateable mistake |
| C4-10 two records sum | C4-02 |
| C4-11 no leakage · C4-13 the two sums | C4-10 |
| C4-08 ISO confirmation | C4-04 and C4-10 |
| C4-09 gate document | C4-03, 04, 05, 06, 07, 08 |

**All 32 tasks are closed.** Chunk 4 is gated at **8 of 9** — see [`CF-CHUNK4-GATE.md`](CF-CHUNK4-GATE.md); the only outstanding point is gate point 9 (validation messages), which is owed on all four chunks alike.

---

## What is structurally new, before any task

Three things make this chunk different in kind from 1–3, not just in data.

**1 · It rates a collection, not a record.** Building rates one Structure per
building. Personal Property rates **N `CommercialPropertyPersonalProperty`
records per Occupancy Class per Location**, driven by a `ForEach`, each
independently running the full four-chain build-up. **This is the first time
the engine has to rate a repeating group and sum it.** Everything in chunks 1–3
was a single record.

**2 · `CovForm` drives the branch, not `CovType` — and it is inherited.**
`CovForm` comes from the occupancy class, so contents items cannot differ from
one another within a class. That is a submission-shape constraint, not just a
rating one.

**3 · The four chains are different lengths from Building's, and Special is the
opposite of Building's Special.**

| Form | Building | Personal Property |
|---|---|---|
| Basic Group I | 8 steps | **9** — LOI and coinsurance computed *first* |
| Basic Group II | 11 | 11 |
| Broad | 6 | **5** — no deductible-factor rule of its own |
| Special | 9 | **14** — the longest chain in the coverage |

Building's Special is a flat statewide constant with no class, construction,
territory or symbol. **Personal Property's Special is keyed on occupancy
category and risk severity, carries its own territory multiplier, and has two
protective-safeguard credits that no Building form has.**

---

## The state layer, censused before the first case

Every Personal Property base-rate table is **header-only countrywide**. This is
chunk 2's shape again, wider:

| Table | CW rows | States filing rows | Never filed by |
|---|---|---|---|
| `BasicGroupIRate` | **0** | **44 of 47** | **AK, CA, PR** |
| `BasicGroupIIRate` | **0** | 45 of 47 | FL, PR |
| `SpecialPrsnlPropRate` | **0** | 45 of 47 | FL, PR |
| `PrsnlPropTerrMultiplier` | **0** | 46 of 47 | PR |
| `SpecialPrsnlPropTheftExclusionFactor` | **0** | 46 of 47 | PR |
| `BroadFormBaseRate` | 30 | 47 of 47 | — |
| `BasicGroupILOIFactorPersProp` | 324 | 47 of 47 | — |
| `BasicGroupIILOIFactorPersProp` | 54 | 47 of 47 | — |
| `BroadSpecialLOIFactorPrsnlProp` | 54 | 47 of 47 | — |
| `FireSafeVaultFactor` | 1 | 47 of 47 | — |

**AK and CA file `BasicGroupIRate` in no edition of the corpus** — enumerated
across all 415 copies of that file, not inferred from the resolver. Chunk 3
already taught what that probably means, which is why **task 31** exists rather
than a conclusion.

---

## Gate-level tasks

| # | Task | Status | Evidence |
|---|---|---|---|
| 1 | Golden case, hand-derived before code — one per form, four forms | ✅ | `22_chunk4_golden_case.py` — BGI **$223**, BGII **$24**, Broad **$16**, Special **$137**, Building unmoved at 263/32. **Five corrections**, see [`CF-CHUNK4-GOLDEN-CASE.md`](CF-CHUNK4-GOLDEN-CASE.md) |
| 2 | Chain runs; **does the `ForEach` over multiple PP records work at all** | ✅ | `23_chunk4_foreach.py` — four chains over a repeating group, **no new interpreter node** |
| 3 | Zero cases | ✅ | `25_chunk4_zero_cases.py` — 7 cases. **Z2: one blank field zeroes Contents and RAISES Building to $275** |
| 4 | 47-jurisdiction sweep, each premium predicted | ✅ | `24_chunk4_enumerate_states.py` — **46 of 47**, PR skipped for an enumerated reason |
| 5 | Shared-name adjudication — **the other half of every name chunks 1–3 adjudicated** | ✅ | `04_shared_names.py` — **17 names, all the PersProp half of chunks 1–3's adjudication** |
| 6 | Exclusion records | ✅ | `05_exclusion_records.py` — theft 5/7, vandalism 5/13, wind/hail 5/19, sprinkler 3/7; terrorism is policy-level |
| 7 | Hardcoded literals — the PP set, which is its own | ✅ | 31 literals — `1150` **excluded** here where Building routes it; 1751/1752; YARD; Valuable Papers in 7 rules |
| 8 | ISO confirmation | ✅ | **6 ISO calls, 6 matches** — including the two-item sum and both District states. And ISO **refused** 4 payloads our engine rates |
| 9 | Gate document | ✅ | [`CF-CHUNK4-GATE.md`](CF-CHUNK4-GATE.md) — **8 of 9** |

---

## The collection problem — new machinery

| # | Task |
|---|---|
| 10 | ✅ **Two PP records both rate and sum** — $209 + $105 = $314, ISO-confirmed. **The LOI factor is the OCCUPANCY's, not the item's**: both take 0.842 off a 150,000 occupancy total, so two small items do not price as one large one |
| 11 | ✅ **No leakage** — two items differing only in `CovType` get their own vault factors (1.0 / 0.5) and rates. **The first draft varied the class code and produced a perfect false positive**, because that field is inherited |
| 12 | ✅ **Seven inherited-or-ignored fields, not one** — `CovForm`, `BldgClassCode`, `RatingType`, `OccupCategoryRiskSeverity`, `TheftDeductible`, the item's `Deductible`, and the class code chain item ← occupancy ← structure. A per-item value is accepted and silently discarded |
| 13 | ✅ **Occupancy-level rollups feed the deductible keys.** `OccupTotalLOIToUse`, `OccupSpecialTotAmtInsurance` and the two `...TotAmtInsurance` sums are computed across the whole occupancy class. **Separated, and branch 1 demonstrably reads the including-theft sum** — `26_chunk4_special_sums.py`. CP 10 33 on the structure drives them apart (200,000 vs 100,000); with a 2,500 theft deductible the factor is **0.89, not 0.92**, and the premium **$125, not $129**. Four dollars is the entire observable difference |

## Basic Group I — the Contents differences

| # | Task |
|---|---|
| 14 | ✅ **`FireSafeVaultFactor`** — 0.50 in a vault prices $223 → **$110**, almost exactly half; 0.0 when not class-rated (zero case Z1b) |
| 15 | ✅ **The group letter is DERIVED, not submitted** — class 0321 → group **A** → 0.457 → **$185**. A 17,000-character occupancy rule picks the letter from the class code alone, and a `Group` supplied in the payload is overwritten |
| 16 | ✅ **YARD substitutes the construction code** — class 1400 on a FRAME building: non-combustible passes code **3** → 0.059 → **$25**; combustible passes code 1 → 0.607 → **$246**. The building's own construction is discarded |
| 17 | ✅ **Class 1150 is excluded** — base 0.0, premium **$0**, where Building routes it to the Builders Risk rows. Belt-and-braces: Oregon files **no PersProp rows for 1150 at all** |
| 18 | ✅ **Two fallbacks in one rule** — class 1751 takes **1.0** and prices at $69 (at 0.96 it would be $66); a missing protection class takes **0.0** and prices at zero. **And the algorithms page had the YARD condition backwards** — corrected |

## Basic Group II — mostly inherited, and that is the claim

| # | Task |
|---|---|
| 19 | ✅ **The Copies are a genuine share, not a duplicate** — `28_chunk4_bgii.py`. Removing `NumStories` (a structure field, 4 levels up) or the Group II territory (a location field, **6 levels up**) prices **both** coverages' Group II at zero, silently. Chunk 2's Z1/Z2 reached through inheritance |
| 20 | ✅ **`GroupIINumericValue[CW, 0580, 1] = 4`** multiplies the base rate before every other factor: Contents $24 → **$93**, Building $32 → **$127** (chunk 2's measured figure). Different source field names, same structure `ClassCode` underneath, so they move together |

## Broad — the shortest chain in the project

| # | Task |
|---|---|
| 21 | ✅ **The ancestor cannot be null** — Building's own rule ends in an `Otherwise` worth 0.0, so a blank building deductible gives Contents a **zero, not a null**: the premium collapses silently instead of being refused. **The missing rule is safe only because of a guarantee in another datadef group.** And the factor never materialises on the Contents record at all, so a trace cannot show it |
| 22 | ✅ **0 of 47 + CW** — enumerated, not asserted. Absent outright, and nothing substitutes |
| 23 | ✅ **0.021 → $16 and 0.011 → $8**, against Building's $17 and $12 on the same building. The fire-resistive tier doubled as a **rounding probe**: $8 confirms the adjusted-rate step rounds ONCE, as Basic Group I does; per-factor rounding would give $9 |

## Special — the longest chain, and the least like Building's

| # | Task |
|---|---|
| 24 | ✅ Offices 0.153 → $137, Residential 0.178 → **$159**, Motels 0.121 → **$109**, blank → **$0**. Oregon files eight categories between 0.069 and 0.316 — **a 4.6× spread Building's single flat 0.047 cannot express** |
| 25 | ✅ Multnomah **1.214** against Remainder of State **1.000** → $137 vs **$113**: the same risk is 21% dearer in Portland, and Building's Special has no equivalent lever. Blank → **0.0**, collapsing the rate |
| 26 | ✅ **0.4 for Offices against Building's flat 0.88** — $137 → **$54**. Oregon files the PP credit between 0.2 (Contractors) and 0.6: a 60% reduction where Building gets 12%. The two coverages are not scaled versions of each other |
| 27 | ✅ 0.90 on the structure's schedule → $137 → **$123**. **The one place so far where a submitter-supplied factor is what ISO intends.** The gate needs `TypeOfWatchmanSrvc` as well as the factor — supply the factor alone and the credit stays 1.0: **a discount silently not given** |
| 28 | ✅ **One record, three effects.** The exclusion's limit replaces the item's (100,000 → 60,000) **and** shrinks the occupancy sums, raising the LOI 0.790 → 0.94 and moving the deductible 0.98 → 0.97. Final rate 0.137 → 0.161. $137 → **$97**, not the $82 a pure exposure change would give |

## Cross-form

| # | Task |
|---|---|
| 29 | ✅ **The premise was wrong — it is all FOUR forms, and what differs is WHERE.** Basic Group I, Group II and Special zero the *adjustment* and leave the rate intact (0.263 / 0.03 / 0.186); **Broad zeroes the RATE itself**, because it has no cause-of-loss step to put the carve-out in. Same $0 premium, different thing visible in a trace. Seven rules carry the literal PP-side, including Earthquake (chunk 10) and the two theft-limitation rules (chunk 12) |
| 30 | ✅ **Between chunk 2 and chunk 3** — `SetBasicGroupIRate` 8 of 47, `SetBGIRatesAndFactors` 6, `SetBasicGroupIBaseRate` 4 (AK, CA, NY, PR), and **0 of 47** for the Broad base rate, the vault factor and the territory multiplier |
| 31 | ✅ **All three override the rule** — and there are **three different district mechanisms for two districts**: AK picks by territory against four literals, CA by a `District` field six levels up, PR has no district and keys the base rate on `ProtectClass`. ISO confirms both District readings (CA 208, AK 224). *Extending the shared-name check across the state layer is still not done* |
| 32 | ✅ **Building never moved** — $263 / $32 in every chunk 4 case. **Except where it should**: a blank `ProtectClass` takes Contents to zero and raises Building to $275 |

---

## Carried in from chunk 3, and live here

| | |
|---|---|
| **A submission can populate a derived field** | Every `IsNull`-guarded rule honours a supplied value. Task 27 is the first place ISO *intends* that; everywhere else it is a hole |
| **`ConstructionType` is a 25-value domain** | Not the six rating names. PP's Broad reads `ConstructionTypeToUse` the same way Building's does |
| **`SetSpecialBaseRate` reads five different tables** | PP's is `SpecialPrsnlPropRate`. Adjudicated in chunk 3, executed here |
| **Class `1150` has at least two independent consequences** | And PP treats it as an exclusion where Building treats it as a route |
| **PR has no ISO confirmation and never will** | It is also the only jurisdiction missing *every* PP base-rate table |

## Deliberately not in chunk 4

Earthquake (chunk 10, and PP has its own EQ chain). Legal Liability (chunk 8),
though the PP premium files carry its branch. Blanket (chunk 9) — still a stub.
Business Income (chunk 5). Theft limitations
(`SetThefLimitationsRatesAndFactors`), sublimits, agreed value, inflation guard
and vacancy — endorsements, chunk 12.
