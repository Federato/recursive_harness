# Property chunk 5 — gate

**Business Income: the `Factor` chain and all four cause-of-loss forms.**
Opened and gated 2026-09-18.

> **Chunk 5 passes 9 of 9** (point 9 closed 2026-10-02 by chunk 27 RC-2; at the gate it was outstanding here and on chunks 1–4
> alike). **No engine code was written** — the fifth coverage in a row on chunk
> 0's foundation, and the first that is arithmetically downstream of another.

| | |
|---|---|
| Golden cases | BGI **$112**, BGII **$13**, Broad **$23**, Special **$47** |
| Jurisdictions | **44 of 47** exact, 1 skipped, 2 diverging with a stated cause |
| ISO calls | **6 this chunk, 6 matches** |
| Building | **unmoved at $261 / $32** in every case |
| Tasks closed | 11 of 28 — all nine gate-level, plus C5-10 and C5-21 |

---

## The eight points

### 1 · A golden case rates end to end — **PASS**

Four, one per form, each gating on the cause of loss — the third coverage
running where that has been true, so it should now be assumed rather than
rediscovered.

    BGI   Building's base 0.498 x terr 0.499 x protClass 0.96 x adj 0.85 = 0.203
          x Factor 0.55                                    = 0.112  -> $112
    BGII  Building's row 0.028 x BCEG 0.96 x adj 0.9        = 0.024
          x Factor 0.55                                    = 0.013  -> $13
    Broad BroadFormBaseRate[CW, Frame, "All Other"]         = 0.023  -> $23
    Spec  SpecialFormIncldgTheft...[CW, Frame, "All Other",
          "Other than Apartments and Condominiums"]         = 0.047  -> $47

**Basic Group I landed exactly on the first run.** Group II was predicted at
$14 and came back $13 — Building's **BCEG factor applies too**, which the
algorithms page's five-way comparison omits. Corrected there.

### 2 · Row counts stated; header-only explained — **PASS**

**Chunk 5 inverts the last three chunks' problem.** The tables are countrywide
and complete:

| Table | CW rows | States with rows |
|---|---|---|
| `BusnIncomeFactor` | **131** | 47 of 47 |
| `MonthlyLimitOfIndemnityFactor` | 60 | 47 of 47 |
| `BroadFormBaseRate` | 30 | 47 of 47 |
| `SpecialFormIncldgTheftTimeElementBaseRate` | 24 | 47 of 47 |
| `MaxPeriodOfIndemnityFactor` | 22 | 47 of 47 |
| `ExtraExpenseFactor` | 4 | 47 of 47 |
| **`BaseRateAdjustmentFactor`** | **0 — header-only** | 46 of 47, PR missing |

One header-only table against chunk 4's five. What is contested here is the
chain, not the data.

### 3 · Every state enumerated — **PASS**

**44 of 47 exact.** PR skipped for an enumerated reason. AZ and TX diverge by
$1 each, **and the cause is the dependency**: neither overrides anything in the
Business Income ruleset, but both have a Building rule that modifies the base
rate before Business Income reads it.

Two corrections the sweep forced:

* **The Business Income rate rounds per step**, not once — Building's shape,
  not Personal Property's. Rounding once is a dollar light in AL, MT, NY and TX.
* **The sweep had to inherit chunk 4's C4-31 routing.** AK, CA and PR get their
  *Building* base rate from differently-named tables, and Business Income reads
  whatever Building computed — so a chunk 4 finding decides chunk 5 premiums.

### 4 · Every `0` tested against its consuming branch — **PASS**

Five cases, and **the headline is a value from ISO's own domain that prices at
zero**: all four `Combined` risk types are filed at **0** for every coinsurance
percentage. They are meant to be a percentage-weighted blend, and without the
`CombinedTypeOfRisk…Pct` fields the placeholder reaches the premium.

**Three routes to a $0 premium with two different values underneath** — a filed
0, a blank-key 0, and a **NULL** from an off-domain risk type. The null does
**not** trigger the null-premium guard: it reaches the premium as $0 rather
than a refusal, so the project's loudest failure mode does not apply here.

### 5 · Every hardcoded literal key listed — **PASS**

20 literals. **`Extra Expense Only` appears in 18 rules** — not just the
`SetFactor` branch test, but the base rate, the Builders Risk factor and the
coinsurance stat code. Chunk 3's lesson at scale: finding one consequence of a
literal does not find the others.

The four `Combined` risk types appear in 4–5 rules each, including the
max-period and monthly-limit branches — so point 4's zero is wider than
`TypeOfRiskFactor`.

### 6 · Shared-name traps diffed, not assumed — **PASS**

**10 ambiguous names**, all resolving to the BusinessIncome half.
**Chunk 3's adjudication predicted this correctly for the second time**, after
chunk 4 — the method now pays forward rather than only recording.

Two things the census gave that were not asked for: **`SetFactor` reads no
matrix at all** — it is a selector, not a lookup — and `SetBGIRatesAndFactors`
reaches only `BaseRateAdjustmentFactor`, independent confirmation that Basic
Group I does no base-rate lookup of its own.

### 7 · Every exclusion's endorsement record identified — **PASS**

Theft 5 records / 7 groups, vandalism 5 / 13, wind/hail 5 / 19, sprinkler
leakage 3 / 7 — ours being the `…BusnIncome` half of each. Plus **ten terrorism
families, each filing one policy-level record across 5 groups**: the third
confirmation that the gate's "one record per coverage" premise does not hold
universally.

### 8 · The edition basis stated — **PASS**

`OR@20260917` over `CF_CW_20260601_V01`, as chunks 1–4. The sweep resolves each
jurisdiction's own chain.

### 9 · No unexplained validation message — **DONE 2026-10-02** (chunk 27 C27-03)

`239_chunk27_rc2.py --live`: Basic, Broad, Special 2 = 2 each at ISO; both in the register (M-001, M-002). The original note, kept:

Owed on all five chunks. **Chunk 5 adds no new message** — every run returns
the same two or three seen throughout (`CP 03 20`, `CP 10 75/76`, and the theft
deductible message on Special). That is the first chunk to add none.

---

## ISO confirmation — 6 calls, 6 matches

| Case | Engine | **ISO** |
|---|---|---|
| OR Basic | BI 112 / 13, Building 261 / 32 | **all four** |
| OR Broad | BI 23 | **23** |
| OR Special | BI 47 | **47** |
| `MaxPeriod = Yes` | 233 | **233** |
| `MonthlyLimitOfIndemnity = 1/3` | 219 | **219** |
| **both elected** | **233** | **233** |

**The last row is the one that matters.** If `SetFactor` multiplied instead of
selecting, the premium would be $252. ISO returns 233 — it selects, and it
selects by priority.

---

## What the build found that the plan did not

**`SetFactor` is a priority selector with no recovery.** Electing max-period,
monthly limit and extra-expense-only together was predicted at $233 and came
back **$0**. The MaxPeriod branch still wins on priority — but
`MaxPeriodOfIndemnityFactor` is itself keyed on `CovType` and files no
`Extra Expense Only` row, so the winning branch cannot resolve, the Factor is
null, and the premium is zero. **It does not fall through to the next branch.**
A valid combination of filed options can therefore price at zero in silence.
That is a different failure from the multiplication the build order warned
about, and nothing in the corpus documents it.

**A datadef name that is not the table's column name.** The extra-expense
factor reads `ExtraExpenseLimitOnLossPayment`; the table's key column is called
`ExtraExpnLimitOnLossPymts`. Supplying the column name leaves the factor at 0
and the premium at zero, silently — and the column name is what anyone reading
the rate table would reach for first.

**`TypeRiskCombination1Factor` and `2Factor` are datadefs, not rate tables.**
The algorithms page calls them tables, which is why neither exists in the
corpus. C5-12 answered early, by the zero cases.

**The dependency carries state-layer complexity with it.** Business Income
reads Building's *computed* base rate, so AK's District split, CA's District
field, PR's own table and AZ's reduction credit all decide Business Income
premiums — without any of them appearing in the Business Income ruleset.

---

## What is still owed

1. **Gate point 9**, on all five chunks.
2. **Input validation** — now four requirements: the missing input that prices
   at zero; the submission that populates a derived field (chunk 3); the
   submission that sets an inherited field per item (chunk 4); and **the valid
   option combination whose chosen branch cannot resolve** (this chunk).
3. **C5-11 to C5-20 and C5-22 to C5-28** — the form specifics, none of them
   gate conditions.
4. **AZ and TX's $1 divergence**, pending C5-15.
5. **PR has no ISO confirmation and never will**, and is the only jurisdiction
   missing `BaseRateAdjustmentFactor`.

## What is deliberately not here

Special Class Business Income (chunk 7) — a complete parallel datadef group.
Blanket (chunk 9), though `CoinsuranceToUse` touches it. Earthquake proper
(chunk 10). The endorsement families (chunk 12).

---

## Reproducing it

    python scripts/cf/32_chunk5_golden_case.py        # four forms
    python scripts/cf/33_chunk5_zero_cases.py         # 5 zero cases
    python scripts/cf/34_chunk5_enumerate_states.py   # 44 of 47
    python scripts/cf/35_chunk5_factor.py             # the four Factor branches
    python scripts/cf/04_shared_names.py              # point 6, all five chains
    python scripts/cf/05_exclusion_records.py         # point 7 census

All exit 0 as of 2026-09-18.
