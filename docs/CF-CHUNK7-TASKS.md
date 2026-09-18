# Property chunk 7 — task list and status

**Special Class Business Income: the borrowed rate and all five forms.**
Opened 2026-09-18.

Derived from `CF_Algorithm/CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md`
and from the census run while opening the chunk
([`49_chunk7_census.py`](../scripts/cf/49_chunk7_census.py)) — not from an
assumption that it is either plain Business Income or Special Class Building
with different tables.

**No engine code is expected.** Chunks 1–6 all ran on chunk 0's foundation
unchanged. If chunk 7 needs a new node, that is itself the finding.

**Tracked live** as **C7-01 … C7-28**, numbered to match this page.

**All 28 tasks are done.** Gate-level; C7-10–C7-14 ([`CF-CHUNK7-BORROWED-RATE.md`](CF-CHUNK7-BORROWED-RATE.md)); C7-15–C7-21 ([`CF-CHUNK7-PER-FORM.md`](CF-CHUNK7-PER-FORM.md)); C7-22–C7-27 ([`CF-CHUNK7-CROSSFORM.md`](CF-CHUNK7-CROSSFORM.md)); C7-28 ([`CF-CHUNK7-OPEN-QUESTIONS.md`](CF-CHUNK7-OPEN-QUESTIONS.md)). **Chunk 7 is gated at 8 of 9.** **Chunk 7 is gated at 8 of 9** ([`CF-CHUNK7-GATE.md`](CF-CHUNK7-GATE.md)).

| Task | Cannot start until |
|---|---|
| C7-02 chain runs | C7-01 golden cases |
| C7-03 zero cases | C7-02 |
| C7-04 state sweep | C7-03, **C7-13** (what the parent's failures do here) and **C7-17** (the six states that delete the lowest-rate rule) |
| C7-10 the borrowed rate | C7-01 |
| C7-08 ISO confirmation | C7-04 |
| C7-09 gate document | C7-03, 04, 05, 06, 07, 08 |

**The census is already run and carries chunk 6's correction in from the
start**: every state is diffed against **its own resolved parent**, with both
package ids printed. Chunk 6's opening census read one countrywide table for
all 47 jurisdictions and published a finding that was 8/11 artefact (OI-100).

---

## What is structurally new, before any task runs

**1 · This is the first coverage that borrows a FULLY RATED rate.** Business
Income reads the Building's `BasicGroupIBaseRate` — the value *before*
territory, protection class and the addends — and rebuilds a parallel formula on
top. Special Class Business Income reads **`../../BasicGroupIRate`**: the
Special Class item's *finished* Basic Group I rate, and adds nothing at the rate
step at all.

**SIX values cross the boundary** - the opening census said five, and C7-01
found the sixth:

    BasicGroupIRate           <- the FINISHED rate  (Basic Group I)
    EQRate                    <- the FINISHED rate  (Earthquake)
    BasicGroupIISymbol        <- an input, for its OWN lookup
    BasicGroupIIRatingTerr    <- an input, for its OWN lookup
    EQTerr
    BasicGroupIINumericValue  <- the parent's multiplier of 8, read outright

**Corrected 2026-09-18.** The census's pattern only matched names ending in
Rate/Symbol/Terr/Factor, so it missed `BasicGroupIINumericValue` entirely - and
that value is why removing the parent's `ClassDescription` takes *two* child
forms rather than one.

**No `BasicGroupIBaseRate` anywhere.** Chunk 5's dependency was "a wrong
Building rate silently produces a wrong Business Income premium". Chunk 7's is
tighter: **it cannot be rated until the parent's rate build-up has fully
completed**, not merely its base-rate step.

**2 · Two forms are keyed on literals, and one of them blanks a dimension the
same table still uses.** Broad always reads the `"Frame"` row; Special always
reads the `"Other than Apartments and Condominiums"` row. So **the apartment
rows of `SpecialFormIncldgTheftTimeElementBaseRate` are permanently unreachable
from this coverage group** — while plain Business Income reaches them on the
same physical table, which the literals census measures directly (*"from the
pinned site only; the same column is also read live elsewhere"*).

**Corrected 2026-09-18:** the algorithms page says the theft-exclusion factor
two steps earlier *still varies* by `ApartmentCondoIndicator` — a live dimension
feeding a dead key. **It does not.** The census shows that lookup **pinned to
`"No"` from every site that reads it**. Both are dead, and C7-20's premise needs
rewriting before it runs.

**3 · Fewer multipliers than either parent, and the census measures it.**

| | here | Special Class Building |
|---|---|---|
| `StdPropPolGroupIFactor` | **0** | 5 |
| `BaseRateAdjustmentFactor` | **0** | 0 |
| `BuildersRiskFactor` · `LOIFactor` · `MultiResidentialPropSpecialCreditFactor` | **0** | 0 |

Basic Group I's whole cause-of-loss adjustment is `rate × VandalismExclFactor` —
**one multiplier**, against plain Business Income's subtract-then-round plus
three factors.

**4 · Earthquake is a real fifth form with no standalone premium file.** It
borrows `EQRate` wholesale and charges **only through Agreed Value**. Chunk 5
found the same asymmetry on plain Business Income; this is its second instance,
and the pair is what makes it a pattern rather than a quirk.

**5 · 25 of 47 jurisdictions file their own rules file for this group** — the
highest state participation of any chunk so far.

---

## The state layer

| Table | CW rows | States declaring their own |
|---|---|---|
| `BasicGroupIIRate` | **0 — header-only** | 45 (all but FL, PR) |
| `LowestBasicGroupIIRate` | **0 — header-only** | 39 (all but AR, DC, FL, KS, NY, PR, RI, TX) |
| `BroadFormBaseRate` | 30 | 1 — PR |
| `SpecialFormIncldgTheftTimeElementBaseRate` | 24 | 2 — FL, PR |
| `SpecialLeaseHoldTimeElementTheftExclusionFactor` | 2 | 1 — PR |
| `BusnIncomeFactor` | 131 | 1 — FL |
| `MaxPeriodOfIndemnityFactor` · `MonthlyLimitOfIndemnityFactor` · `ExtraExpenseFactor` | 22 / 60 / 4 | 1 each — FL |
| `AgreedValueFactor` | 1 | **0 of 47** |
| `SpecialFormBldrsRiskTimeElementBaseRate` | 1 | **0 of 47** — **and this group never names it** |
| `BaseRateAdjustmentFactor` | **0** | **46** — *and this group never names it either* |

**Two tables with no consumer in this group, filed by 0 and 46 states.** The
Builders Risk time-element rate has no 1150 branch to reach it here, and
`BaseRateAdjustmentFactor` belongs to plain Business Income — which is the
table 46 jurisdictions file and this coverage never reads.

**Rule deletions, again on rating rules.** `SetLowestBasicGroupIIBaseRate` is
emptied to `<rul:Sequence />` by **six** states — AR, DC, KS, NY, RI, TX — which
are **six of the eight** that file no `LowestBasicGroupIIRate`. Chunk 6 found
the same relationship expressed by *rewriting* the rule; here six states delete
it outright, and FL and PR (the other two non-filers) override
`SetBGIIRatesAndFactors` instead. **C6-19's biconditional gets re-asked on a
second coverage.**

`SetSpecialTheftExclusionFactor` is deleted by PR, exactly as in chunk 6.
Otherwise: `SetBasicGroupIICauseOfLossAdjustment` overridden by 8,
`SetLowestBasicGroupIIBaseRate` by 6, `SetBGIIRatesAndFactors` by 3, and
**nothing at all** on `SetBasicGroupIRate`, `SetFactor`, `SetTypeOfRiskFactor`,
`SetCoinsuranceToUse`, the whole Broad chain or `SetEQRate`.

---

## Gate-level tasks

| # | Task | Status | Evidence |
|---|---|---|---|
| 1 | Golden case, hand-derived before code — one per form | ✅ | [`50_chunk7_golden_case.py`](../scripts/cf/50_chunk7_golden_case.py) — **$39 / $123 / $23 / $47**, item unmoved at 66/209. **Every rate step landed first run.** One correction: **omitting `MonthlyLimitOfIndemnity` is not the same as saying "Not Applicable"** — the absent field elects a priced branch and both Basic forms return $0. See [`CF-CHUNK7-GOLDEN-CASE.md`](CF-CHUNK7-GOLDEN-CASE.md) |
| 2 | Chain runs, on chunk 0's foundation, with no new interpreter node | ✅ | **No new node.** A seventh coverage on the same machinery, and the first at **three levels of nesting** — Location → SpecialClass → SpecialClassBusnIncome |
| 3 | Zero cases — including a parent that cannot rate | ✅ | [`51_chunk7_zero_cases.py`](../scripts/cf/51_chunk7_zero_cases.py) — 6 cases. **Removing the parent's `ClassDescription` was predicted to take one child form and takes two**; removing the parent's `Deductible` prices the ITEM at zero and **leaves the child at $39** |
| 4 | 47-jurisdiction sweep, each premium predicted from that state's own rows | ✅ | [`52_chunk7_enumerate_states.py`](../scripts/cf/52_chunk7_enumerate_states.py) — **47 of 47**. AZ, FL and NY produce no Group I premium, **all three inherited from chunk 6 and none of them a Business Income defect** |
| 5 | Shared-name adjudication — the SpecialClassBusnIncome half. **Chunk 3's adjudication has now paid forward three times**; this is its fourth test | ✅ | `04_shared_names.py` now reports **seven** chains — 25 shared names, 11 reading different tables. **`SetBasicGroupIRate` and `SetFactor` resolve to NO MATRIX at all** in this group, which is the borrowed-rate claim seen from the census side |
| 6 | Exclusion records — vandalism and wind/hail reach this group; does it file its own? | ✅ | Vandalism, wind/hail and theft each file a `*SpclClassBusnIncome` record; **cyber is one policy-level record** reaching every premium file — the same shape as chunks 5 and 6 |
| 7 | Hardcoded literals — **two base rates are pure literals here**, which is where the census expects the interesting rows | ✅ | **38 pinned sites, 23 that kill filed rows.** Broad's `"Frame"` (5 of 6 unreachable) and Special's `"Frame"` plus the apartment key — **and the apartment column is pinned "from the pinned site only; the same column is read live elsewhere"**, which is C7-19's claim with a measurement attached |
| 8 | ISO confirmation | ✅ | **5 calls, 5 agreements** — including the one that mattered: parent at **$0/$0** while Business Income holds at **$39/$123**. FL refused with a 400, OI-99 reached through a *parent* that cannot rate |
| 9 | Gate document — and an answer to each of the algorithms page's five open questions | ✅ | [`CF-CHUNK7-GATE.md`](CF-CHUNK7-GATE.md) — **8 of 9**. **The first chunk where ISO's message count does not match the engine's** (ISO 3 / engine 5), which sharpens point 9 rather than closing it |

## The borrowed rate — the chunk's central machinery

| # | Task |
|---|---|
| 10 | ✅ **The borrow, proven by moving it.** Parent class → Aircraft takes its rate 0.07 → 0.286 and the premium **$39 → $157**; parent LCM 2.0 takes it to 0.14 and **$77** — with nothing in the Business Income record changed. **The parent's LCM reaches the child and the parent's deductible does not**, because the copy happens after the one and before the other |
| 11 | ✅ **A rate chain with nowhere to send its answer, for the second time.** No plain Earthquake coverage file exists; the only two premium files are Agreed Value and Extended Period of Indemnity. Chunk 5 found the same asymmetry on plain Business Income — **two instances make it a pattern** |
| 12 | ✅ **ELEVEN, and the count was wrong twice.** The census said five (a regex filtered to Rate/Symbol/Terr/Factor), the golden case found six by hand, an unfiltered regex finds **eleven** — and `BasicGroupIBaseRate` is named **zero** times. **A filtered enumeration is not an enumeration.** Also: the child's own LCM is **inert in Group I and five-fold in Group II** ($39 unchanged / $123 → $616) |
| 13 | ✅ **Three jurisdictions where a well-formed Business Income record prices at zero**, for three reasons that all belong to a different coverage — FL, NY, AZ, inherited whole from chunk 6. Settled inside the sweep |
| 14 | ✅ **Read by two forms, ignored by three.** Mercantile 0.55 → $39, Manufacturing 0.71 → $50, MaxPeriod **1.15 → $81**, Extra Expense Only **1.7 → $119** — and with max-period elected **Broad holds at $23 and Special at $47**. Only **FL** files its own `BusnIncomeFactor`. And the extra-expense branch keys on `ExtraExpenseLimitOnLossPayment`, **not** the column name `ExtraExpnLimitOnLossPymts` — the second time in the project a column name was mistaken for a field name, silently |

## Per-form specifics

| # | Task |
|---|---|
| 15 | ✅ **One multiplier, and it keys on the PARENT.** `rate × VandalismExclFactor` and nothing else — and the factor keys on the *parent's* `ClassCode`, one of the eleven borrowed values, so the same exclusion is worth 0.95 on class 0951 and 0.98 on 0311 ($37 / $38). **Each absence has a different contrast and the census only drew one**: `StdPropPolGroupIFactor` is 0 here *and* 0 in plain Business Income (5 in Special Class Building), while `BuildersRiskFactor` and sprinkler leakage are 10 and 86 in plain Business Income and 0 in both Special Class groups |
| 16 | ✅ **Unresolvable at countrywide for the third coverage group running.** `BasicGroupIIRate` 0 CW rows / 45 states, `LowestBasicGroupIIRate` 0 / 39 — the same two empty tables Building and plain Business Income read |
| 17 | ✅ **Chunk 6's biconditional does not survive a second coverage.** Six states **delete** the rule (AR, DC, KS, NY, RI, TX) — six of the eight non-filers — and **FL and PR go a third way**, leaving the rule alone while filing no table, so they reach a read with nothing to read. A rule inferred from chunk 6 would have called those two defects |
| 18 | ✅ **Construction pinned and covType live, in the SAME lookup.** Fire Resistive on the parent leaves the base at 0.023 and the premium at **$23**; `CovType` Without Extra Expense moves it to 0.011 and **$11**. Plain Business Income reads the Fire Resistive rows and prices the same risk at $12. **Moving only construction would have concluded the lookup ignores its keys** |
| 19 | ✅ **Pinned here, live next door.** The apartment rows (0.029 / 0.016) are unreachable from this group — the literals census says the pin applies *"from the pinned site only; the same column is read live elsewhere"* — and that elsewhere is plain Business Income on **the same physical table**, pricing the apartments version at **$29** against this group's $47 |
| 20 | ✅ **The algorithms page's open question answered, and half of it was wrong.** It records the theft factor as still varying by `ApartmentCondoIndicator`. **It does not** — that lookup keys the column on a hard-coded `"No"`, so the `Yes` row (0.96) is unreachable too. **Both dimensions are dead**: moving the indicator and the parent's class code moves neither the theft factor (0.86 throughout) nor the base rate (0.047). Corrected on the algorithms page in two places |
| 21 | ✅ **Class 1150 is inert here for the third coverage group in two chunks.** `SpecialFormBldrsRiskTimeElementBaseRate` is named **0** times in this ruleset and **6** in plain Business Income's; the table files 1 countrywide row and **0 states file their own**. Parent class 1150 → premium **$47, unchanged** |

## Cross-form claims

| # | Task |
|---|---|
| 22 | ✅ **0 countrywide and 0 across all 47** for all four, scanned in the main ruleset and every premium file. **Each absence has a different lineage and the opening census only drew one comparison** — `StdPropPolGroupIFactor` is absent from plain Business Income too, so it is inherited rather than dropped |
| 23 | ✅ **46 of 47 file it (all but PR), countrywide is header-only, and this ruleset names it 0 times** — against 19 in plain Business Income's. **A filed table is not evidence of a live path**: it belongs to the coverage that *rebuilds* a rate this one simply *copies* |
| 24 | ✅ **Counted, not read.** This group carries **4 `rul:Round` on every form**; the parent it hangs off carries **0 on all four**; and **plain Business Income is inconsistent with itself** (Basic Group II 0, the others 4). **This group follows plain Business Income and normalises its inconsistency — the copy is tidier than the original** |
| 25 | ✅ **The same two fields, on a different coverage.** `BlktTotalFullValueAmount` → 0 and `BlktCauseOfLossValue` → blank; `BlktLimit` and the average rate survive; premium **$0**. A caller supplying all four blanket values now gets a silent zero **twice over**, once at each level |
| 26 | ✅ **Building 263/32, Contents 223/24, Business Income 112/13, Special Class 66/209, Special Class Business Income 39/123** — five coverages, four nesting levels, one submission, each unchanged from its own chunk |
| 27 | ✅ **Checked — and the map was right where our own census was wrong.** 30 value-shaped claims, **21 consistent, 0 contradicted, 9 not decidable and stated as such**. The map lists `BasicGroupIINumericValue` among the copied values — **the one C7-12's census filtered out and the golden case had to rediscover by hand** |
| 28 | ✅ **Four answered with evidence, one left open with a reason.** **Two of the five were not answerable as asked** — Q1 and Q2 both embedded a premise about what varies, and both premises were wrong. Q5's file turned out **not** to be a dispatch file: it is a coverage shell whose own gate is hard-coded to **0**, the fifth computed-and-never-used shape across chunks 6 and 7. Q4 (two endorsement files) stays open for chunk 12, deliberately. See [`CF-CHUNK7-OPEN-QUESTIONS.md`](CF-CHUNK7-OPEN-QUESTIONS.md) |

---

## What chunk 7 inherits and must re-ask

* **OI-99 — ISO refuses where we return $0.** Chunk 7 will produce zeros through
  a *parent* that cannot rate, which is a new route to the same question.
* **OI-100 — diff each state against its own parent.** Built into the census
  from the start this time.
* **Building's rate-step rounding** is still open from chunk 5 and untouched by
  chunk 6.
* **Chunk 3's shared-name adjudication** has now predicted correctly for chunks
  4, 5 and 6. C7-05 is its fourth test.
