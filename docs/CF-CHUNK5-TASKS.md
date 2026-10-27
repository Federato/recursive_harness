# Property chunk 5 — task list and status

**Business Income: the `Factor` chain and all four cause-of-loss forms.**
Opened 2026-09-18.

Derived from `CF_Algorithm/CauseOfLoss_BusinessIncome_RatingAlgorithms.md` and
from censuses run while opening the chunk — not from an assumption that
Business Income is Building with different tables.

**No engine code is expected.** Chunks 1–4 all ran on chunk 0's foundation
unchanged. If chunk 5 needs a new node, that is itself the finding.

**Tracked live** as **C5-01 … C5-28**, numbered to match this page. Dependencies
recorded there rather than left to memory:

| Task | Cannot start until |
|---|---|
| C5-02 chain runs | C5-01 golden cases |
| C5-03 zero cases | C5-02 |
| C5-04 state sweep | C5-03, **C5-17** (PR's missing table) **and C5-21** (the ten Group II overrides) |
| C5-10 the four `SetFactor` branches | C5-02 and **C5-12** — the combined-risk tables must be found before the default branch can be trusted |
| C5-08 ISO confirmation | C5-04 and C5-10 |
| C5-09 gate document | C5-03, 04, 05, 06, 07, 08 |

**All 28 tasks are done.** Chunk 5 is gated at **8 of 9** — see [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md); the only outstanding point is gate point 9 (validation messages), owed on all five chunks alike. Everything else is independently startable.

---

## What is structurally new, before any task

**1 · Business Income is arithmetically DOWNSTREAM of Building.** Three of the
five forms — Basic Group I, Basic Group II and Earthquake — have **no base rate
of their own**. They read the *already-computed* `BasicGroupIBaseRate`,
`BasicGroupIISymbolToUse` / `BasicGroupIIRatingTerr` and `EQBaseRate` from the
Structure two to four levels up, and apply a small Business-Income adjustment
factor on top.

**This is the first coverage in the project that cannot be rated without rating
another coverage first.** Chunks 1–4 were independent; chunk 5 is not. A wrong
Building rate silently produces a wrong Business Income premium, and every
chunk 1–3 finding is now load-bearing for a second coverage.

**2 · Coinsurance is not a multiplier here — it is folded into a three-
dimensional factor, and only two of five forms use it.** `SetFactor` picks
**exactly one** of four values in priority order:

    MaxPeriodOfIndemnityFactor      if MaxPeriod = "Yes"
    MonthlyLimitOfIndemnityFactor   elif MonthlyLimitOfIndemnity <> "Not Applicable"
    ExtraExpenseFactor              elif CovType = "Extra Expense Only"
    TypeOfRiskFactor                otherwise

**Multiplying them instead of selecting would overstate the premium by a large
multiple.** Broad and Special never apply `Factor` at all.

**3 · Four rating concepts Building has are simply absent.**

| | Building | Business Income |
|---|---|---|
| Deductible factor | every form | **none anywhere** — the "deductible" is a waiting period built into the rate |
| Limit-of-insurance factor | every form | **none** — the premium multiplies the final rate by `Limit / 100` directly |
| `MultiPremiumAndDispersionCreditFactor` | scheduled branch | **not applied**, though the datadef is populated |
| Legal Liability / Leasehold branches | up to four branches per form | **two** — scheduled or blanket |

**4 · Add-ons charge `(Factor − 1) × Rate × Limit/100`.** Agreed Value and
Extended Period of Indemnity charge only the *incremental* load, never the full
rate again. **Nothing in Building or Contents uses that shape** — their
endorsement factors are always full multipliers.

---

## The state layer — quiet, for the first time since chunk 1

| Table | CW rows | States with rows |
|---|---|---|
| `BusnIncomeFactor` | **131** | 47 of 47 |
| `MonthlyLimitOfIndemnityFactor` | 60 | 47 of 47 |
| `BroadFormBaseRate` | 30 | 47 of 47 |
| `SpecialFormIncldgTheftTimeElementBaseRate` | 24 | 47 of 47 |
| `MaxPeriodOfIndemnityFactor` | 22 | 47 of 47 |
| `ExtraExpenseFactor` | 4 | 47 of 47 |
| `AgreedValueFactor` · `SpecialFormBldrsRiskTimeElementBaseRate` | 1 | 47 of 47 |
| **`BaseRateAdjustmentFactor`** | **0 — header-only** | 46 of 47, **PR missing** |

Rule overrides are equally quiet: `SetFactor`, `SetTypeOfRiskFactor`,
`SetBroadBaseRate` and `SetCoinsuranceToUse` are overridden by **0 of 47**. The
one outlier is **`SetBasicGroupIICauseOfLossAdjustment`, overridden by 10** —
AR, DC, FL, IN, KS, KY, NY, PR, RI, TX.

**So chunk 5 inverts chunk 2 and chunk 4's problem.** The tables are there; what
is not settled is whether the countrywide *chain* holds — and the answer is
re-asked, never inherited.

---

## Gate-level tasks

| # | Task | Status | Evidence |
|---|---|---|---|
| 1 | Golden case, hand-derived before code — one per form | ✅ | `32_chunk5_golden_case.py` — BGI **$112**, BGII **$13**, Broad **$23**, Special **$47**; Building unmoved at 261/32 |
| 2 | Chain runs, and **Building rates first** | ✅ | Confirmed: BGI reads Building's computed base rate, BGII reads the shared table **with the literal covType `"Bldg"`**. **No new interpreter node** — the fifth coverage on chunk 0's foundation |
| 3 | Zero cases | ✅ | `33_chunk5_zero_cases.py` — 5 cases. **A correctly-spelled value from ISO's own domain that prices at zero**: all four Combined risk types are filed at 0 |
| 4 | 47-jurisdiction sweep, each premium predicted | ✅ | `34_chunk5_enumerate_states.py` — **44 of 47 exact**, PR skipped for an enumerated reason, AZ and TX diverging by $1 **through the Building dependency** with the cause stated |
| 5 | Shared-name adjudication — the BusinessIncome half | ✅ | `04_shared_names.py` now reports all five chains — **10 ambiguous names on chunk 5's**, all resolving to the BusinessIncome half. **Chunk 3's adjudication predicted it correctly for the second time** |
| 6 | Exclusion records | ✅ | Theft 5/7, vandalism 5/13, wind/hail 5/19, sprinkler 3/7 — plus **ten terrorism families, each one policy-level record across 5 groups** |
| 7 | Hardcoded literals — the BI set | ✅ | 20 literals. **`Extra Expense Only` appears in 18 rules**, not just the `SetFactor` branch test — it gates the base rate and the Builders Risk factor too. The four Combined risk types appear in 4–5 rules each |
| 8 | ISO confirmation | ✅ | **6 calls, 6 matches** — including **233 for the priority case, where multiplication would give 252**. ISO selects, and by priority |
| 9 | Gate document | ✅ | [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md) — **8 of 9**. Chunk 5 is the first chunk to add **no new validation message** |

## The `Factor` — the chunk's central machinery

| # | Task |
|---|---|
| 10 | ✅ **Exactly one, by priority** — 0.55 / 1.15 / 1.08 / 1.70 alone, and **1.15 when two are elected together** where multiplying would give 1.242. But all three together gives **NULL, not 1.15**: the winning branch is keyed on `CovType` and cannot resolve, and `SetFactor` **does not fall through**. A valid option combination that prices at zero in silence |
| 11 | ✅ **All three keys move it** — `TypeOfRisk` Manufacturing 0.71 → **$144**, `CovType` Without Extra Expense 0.50 → **$102**, coinsurance 80% 0.59 → **$120**. Note the direction: a LOWER coinsurance is a HIGHER factor, the opposite of Building's table |
| 12 | ✅ **Neither table exists — they are DATADEFS read from the submission.** The blend is `r3(r3(MfgPct/100 × Combination1Factor) + (OtherPct/100 × Combination2Factor))`, and **all four fields are submitted**, through `FromConstant="0.0"`. 40%/60% at 0.71/0.55 → **0.614 → $125**. A combined risk is a selection PLUS four submitted numbers, which is why C5-03's case priced at zero |
| 13 | ✅ **`CoinsuranceToUse` follows the BUSINESS INCOME record, not the building.** BI at 80% while the structure stays at 90%: the factor moves 0.55 → 0.59 and **Building stays at $261**. The two coverages can carry different coinsurance on one submission |
| 14 | ✅ **Confirmed by moving it.** Electing max-period gives a Factor of 1.15 — more than double the default — and Basic Group I goes $112 → $233 while **Broad stays at $23 and Special at $47**. The Factor is computed for every form and read by only two |

## Downstream of Building — the new dependency

| # | Task |
|---|---|
| 15 | ✅ **Proven by moving it** — change the BUILDING's class code to 0074 and the Business Income premium follows $112 → **$32**, with nothing in the BI record changed. **And the ordering was wrong on the algorithms page**: `BGIBaseRateAdjustmentFactor` applies FIRST, not last. Both orders give 0.203 on the golden case; 0074 discriminates (0.059 vs 0.058). Corrected |
| 16 | ✅ **Group I and Group II read different ancestor values, and only Group II falls over.** Removing `NumStories` prices BI Group II and Building Group II at zero while both Group I premiums hold at $112 / $261. Chunk 4's C4-19 reaching a third coverage |
| 17 | ✅ **PR deletes the rule, it does not just omit the table.** `SetBGIBaseRateAdjustmentFactor` is overridden with an empty `<rul:Sequence />`. The build order flagged rule-deletion for validation messages (316 rules emptied by some state) — **this is the first time it has been seen on a RATING rule** |
| 18 | ✅ **Every absent-means-zero finding now has a second consumer.** Removing the structure's `ClassCode` prices Building AND Business Income at zero, with the BI `Factor` still a healthy 0.55 and the BI record perfectly well formed. Nothing raises, in either coverage |

## Per-form specifics

| # | Task |
|---|---|
| 19 | ✅ **Two rules, and the covType key halves the rate.** Frame All Other 0.023 → **$23**, Without Extra Expense 0.011 → **$11**, Fire Resistive 0.012 → **$12** and 0.007 → **$7**. `BroadCauseOfLossAdjustment` is never written and the final rate is a straight copy |
| 20 | ✅ Four-way table — construction × covType × risk type. 0.047 → **$47**, apartments 0.029 → **$29**, Without EE 0.033 → **$33**, class 1150 → Builders Risk 0.018 → **$18**. **And `ApartmentCondoIndicator` is DERIVED** from the class code against a hardcoded list of 13; setting it directly does nothing |
| 21 | ✅ **Three shapes, not ten overrides.** AR/DC/NY/RI (529 chars) have **dropped the wind/hail branch entirely**; TX adds a wind/hail exclusion factor; FL/IN/KS/KY/PR add a wind/hail-excluded rate and the LCM. A divergence in content, not formatting |
| 22 | ✅ **Exactly as the build order described it** — the Factor is **0.0, not 1.0**, and the premium is zero. Predicted as a null on the assumption the row was missing; it is a written zero, which is the point |
| 23 | ✅ **A rate chain with nowhere to send its answer.** `FinalEQRate` is produced, there is **no plain Earthquake coverage file**, and all 10 Earthquake premium files are Agreed Value or endorsement variants |

## Cross-form

| # | Task |
|---|---|
| 24 | ✅ **0 of 47 + CW** — enumerated, not asserted. Building applies a deductible factor on every form; Business Income has no such rule anywhere |
| 25 | ✅ **0 of 47 + CW**. The premium multiplies `Limit / 100` with nothing between it and the final rate — so nothing about limit banding carries over from chunks 1–4 |
| 26 | ✅ **Proven by moving it** — a 0.5 credit takes Building Group I $261 → **$131** and leaves Business Income at **$112**. A populated-but-unused datadef is exactly the shape that makes a reader assume it is in the formula |
| 27 | ✅ **Agreed Value charges $11 where the full rate would charge $112** — `0.112 × (1.1 − 1) × 1,000`. Ten times the difference, and Basic Group I is still charged in full alongside it |
| 28 | ✅ **Three coverages on one submission, none of them moving** — Building 263/32, Contents 223/24, Business Income 112/13. **BI is immune to the Contents record**, which follows from 24 and 25: no deductible key and no limit factor, so the location total that moves Building $261 → $263 cannot reach it |

---

## Carried in from chunks 1–4, and live here

| | |
|---|---|
| **Every Building finding is now load-bearing twice** | BI Basic Group I and II read Building's computed rate, so Arizona's reduction credit, the BCEG zero, the construction-type domain and the symbol traps all reach a second coverage |
| **Inherited fields** | chunk 4 found seven. Business Income nests one level deeper still — seven `../` levels to policy factors — so expect more, and check before setting anything per record |
| **A submission can populate a derived field** | chunk 3's hole and chunk 4's mirror both apply |
| **PR has no ISO confirmation and never will** | and it is the only jurisdiction missing `BaseRateAdjustmentFactor` |
| **Gate point 9** | owed on chunks 1, 2, 3 and 4. Chunk 5 should not add a fifth silence |

## Deliberately not in chunk 5

Special Class Business Income (chunk 7) — a complete parallel datadef group,
file-for-file. Blanket (chunk 9) — still a stub, though `CoinsuranceToUse`
touches it. Earthquake proper (chunk 10). Ordinance or Law and the other
endorsement families (chunk 12).
