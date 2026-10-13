# Property chunk 5, task C5-01 — the golden cases

**Business Income, all four cause-of-loss forms.** Derived 2026-09-18.

**Every number below was read off the filed rows and worked out by hand before
the engine was run.** Where the engine disagreed, the disagreement is recorded
as the finding rather than edited away.

Script: [`scripts/cf/32_chunk5_golden_case.py`](../scripts/cf/32_chunk5_golden_case.py).

---

## The case

The **same Oregon building as chunks 1–4**, with a Business Income record on it.

| | |
|---|---|
| Building | class 0951, Frame, Protection Class 3, territory Portland, limit 100,000 |
| Group II inputs | symbol B, territory `Entire State`, BCEG 4 |
| Business Income | limit 100,000, `CovType` "Business Income With Extra Expense", `TypeOfRisk` "Mercantile and Non-manufacturing" |
| Terms | coinsurance 90%, LCM 1.0 |

**No contents at the location**, so the Building premiums are chunk 1 case A and
chunk 2 — $261 and $32.

### What makes this chunk different before any arithmetic

**Business Income is arithmetically downstream of Building.** Basic Group I
reads the Structure's already-computed `BasicGroupIBaseRate`, and Basic Group II
reads the shared `BasicGroupIIRate` table **with the literal covType `"Bldg"`** —
not a Business Income row, the *Building's* row. The table files only `Bldg` and
`PersProp`; there is no Business Income row to read. Only Broad and Special have
base rates of their own.

### The filed rows this case stands on

| Value | Table | Key |
|---|---|---|
| 0.498 | `BasicGroupIRate` | OR, 0951, 1, Not Applicable, **Building** — read via the Structure, not looked up here |
| 0.85 / 0.9 | `BaseRateAdjustmentFactor` | OR, Basic Group I / Basic Group II |
| 0.55 | `BusnIncomeFactor` | CW, With Extra Expense, Mercantile and Non-manufacturing, 90% |
| 0.028 | `BasicGroupIIRate` | OR, Entire State, B, **Bldg** |
| 0.96 | `BCEGFactor` | OR, Entire State, grade 4 |
| 0.023 | `BroadFormBaseRate` | CW, Frame, **All Other** |
| 0.047 | `SpecialFormIncldgTheftTimeElementBaseRate` | CW, Frame, All Other, Other than Apartments and Condominiums |

---

## Predictions and results

| Form | Base | Rate | Final | **Premium** | |
|---|---|---|---|---|---|
| Basic Group I | 0.498 | 0.203 | 0.112 | **$112** | ✅ exact |
| Basic Group II | 0.028 | 0.024 | 0.013 | **$13** | ❌ predicted $14 |
| Broad | 0.023 | 0.023 | 0.023 | **$23** | ✅ |
| Special | 0.047 | 0.047 | 0.047 | **$47** | ✅ |
| Building Group I | | | | **$261** | ✅ unmoved |
| Building Group II | | | | **$32** | ✅ unmoved |

### Basic Group I — 3 rules

    rate   = r3(0.498 x adj 0.85 x terr 0.499 x protClass 0.96)   = 0.203
    COLadj = r3(0.203 - 0) x 1 x 1 x 1                            = 0.203
    Factor = BusnIncomeFactor[CW, With EE, Mercantile, 90%]       = 0.55
    final  = r3(0.203 x 0.55)                                     = 0.112
    premium = 0.112 x 100,000/100                                 = $112

**Landed exactly on the first run** — but on a formula that was later found to
be ordered differently from the algorithms page. See correction 3.

### Basic Group II — 5 rules

    base   = BasicGroupIIRate[OR, Entire State, B, "Bldg"]        = 0.028
    rate   = r3(r3(0.028 x BCEG 0.96) x adj 0.9)                  = 0.024
    final  = r3(0.024 x Factor 0.55)                              = 0.013  -> $13

### Broad — 2 rules, the shortest chain in the project

    base   = BroadFormBaseRate[CW, Frame, "All Other"]             = 0.023
    rate   = final = 0.023                                                -> $23

`All Other` because the coverage type is *with* extra expense; the table's other
Business Income row is `Business Income Without Extra Expense` at 0.011. **A
two-value covType key where the wrong one is half price.**

### Special — 6 rules

    base   = SpecialFormIncldgTheftTimeElementBaseRate
             [CW, Frame, "All Other", "Other than Apartments and Condominiums"]
                                                                   = 0.047
    COLadj = rate x theft 1.0                                      = 0.047
    final  = a straight copy                                               -> $47

---

## Four corrections

**1 · Basic Group II was predicted at $14 and came back $13 — BCEG applies.**
The prediction was written without it, because the algorithms page's five-way
comparison lists only `BGIIBaseRateAdjustmentFactor` as Business Income's own
multiplier for this form. It inherits Building's BCEG factor as well:
`0.028 × 0.96 × 0.9 = 0.024`, not 0.025. **Corrected on the algorithms page.**

**2 · Each form gates on the cause of loss — for the third coverage running.**
The first draft ran one submission with `CauseOfLoss = Basic` and read Broad and
Special pricing at zero as a defect. It is the gate working, and the cause of
loss is the **Business Income record's own field**, not the structure's. The
pattern has now held for Building, Contents and Business Income, so it should be
assumed rather than rediscovered in chunk 6.

**3 · The base-rate adjustment applies FIRST, not last.** The algorithms page's
quick reference reads `base × terr × protClass × adjustment`; the engine does
`base × adjustment × terr × protClass`. Both give 0.203 on this case, which is
why it passed — class 0074 is the first case that tells them apart (0.059
against 0.058). Found later, by C5-15. **Corrected on the algorithms page.**

**4 · Building's own rate-step rounding is not what chunk 1 recorded**, and this
case could not have shown it. Chunk 1 read the Group I rate step as rounding
after every factor; base 0.498 gives 0.239 either way. At class 0074,
`0.143 × 0.96 × 0.499` is **0.069 rounded once** and 0.068 rounded per factor,
and the engine gives 0.069. **Logged as an open item** — it reaches back into
chunk 1 and may explain the residual mismatches in chunks 4 and 5's sweeps.

---

## What this case cannot show

* **The `Factor` selecting rather than multiplying.** One case electing one
  branch looks identical either way. C5-10.
* **The dependency on Building.** A single class code cannot distinguish
  "reads Building's rate" from "coincidentally the same". C5-15.
* **Anything about the other 44 jurisdictions.** C5-04.

---

## ISO confirmation

All four figures, plus both Building premiums, confirmed in chunk 5's 6-call
run — see [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md).
