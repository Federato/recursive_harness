# Property chunk 7, task C7-01 — the golden cases

**Special Class Business Income, four core forms.** Derived 2026-09-18.

**Every number below was read off the filed rows and worked out by hand before
the engine was run.**

Script: [`scripts/cf/50_chunk7_golden_case.py`](../scripts/cf/50_chunk7_golden_case.py).

---

## The case

**Chunk 6's Special Class item**, with a Business Income record hanging off it.

| | |
|---|---|
| Special Class item | `ClassDescription` "Towers - Broadcasting Antennas (Cell, Radio and TV)", limit 100,000, PC 3, symbol B, `Entire State` |
| Business Income record | limit 100,000, `CovType` "Business Income With Extra Expense", `TypeOfRisk` "Mercantile and Non-manufacturing", coinsurance 90% |

**The nesting is three deep and new to the project** — Location → SpecialClass →
SpecialClassBusnIncome — so `../../` from the Business Income record is the
Special Class item, not a Building.

### The filed rows this case stands on

| Value | Table | Key |
|---|---|---|
| 0.07 | — | **the item's own finished `BasicGroupIRate`, copied** |
| 0.028 | `BasicGroupIIRate` | OR, Entire State, B, **`"Bldg"`** |
| **8** | — | **the item's `BasicGroupIINumericValue`, read across the boundary** |
| 0.55 | `BusnIncomeFactor` | CW, With Extra Expense, Mercantile, 90% |
| 0.023 | `BroadFormBaseRate` | CW, **`"Frame"` literal**, All Other |
| 0.047 | `SpecialFormIncldgTheftTimeElementBaseRate` | CW, **`"Frame"`**, All Other, **`"Other than Apartments and Condominiums"` literal** |

---

## Predictions and results

| Form | Rate | Final | **Premium** | |
|---|---|---|---|---|
| Basic Group I | 0.07 | 0.039 | **$39** | ✅ exact |
| Basic Group II | 0.224 | 0.123 | **$123** | ✅ exact |
| Broad | 0.023 | 0.023 | **$23** | ✅ exact |
| Special | 0.047 | 0.047 | **$47** | ✅ exact |
| Special Class Group I / II | | | **$66 / $209** | ✅ unmoved |

**Every predicted rate step landed on the first run.** One thing had to be fixed
before the Basic pair produced anything at all, and it is a finding — see below.

### Basic Group I — 2 rules

    rate   = ../../BasicGroupIRate                        = 0.07   <- a COPY
    COLadj = 0.07 x VandalismExclFactor 1.0               = 0.07
    final  = r3(0.07 x Factor 0.55) = r3(0.0385)          = 0.039
    premium = 0.039 x 100,000/100                         = $39

**There is no lookup of any kind in this chain.** The rate is the parent's
*finished* Basic Group I rate, and the only multiplier before `Factor` is
vandalism. Plain Business Income reads the Building's **base** rate and rebuilds
a parallel formula with its own adjustment factor; this reads the answer.

### Basic Group II — its own lookup, and a borrowed multiplier

    base   = BasicGroupIIRate[OR, Entire State, B, "Bldg"]   = 0.028
    rate   = r3(r3(0.028 x LCM) x ../../BasicGroupIINumericValue 8) = 0.224
    COLadj = a copy (no wind/hail exclusion elected)         = 0.224
    final  = r3(0.224 x 0.55)                                = 0.123  -> $123

**Group II is the one form that borrows an input rather than an answer** — the
parent's symbol and territory key its own lookup — **and it also borrows the
parent's numeric value of 8 outright.** That is a sixth value crossing the
boundary, and the opening census missed it: its pattern only caught names ending
in Rate/Symbol/Terr/Factor. **C7-12 is corrected before it starts.**

### Broad and Special — two rules each, both on literals

    Broad   base = BroadFormBaseRate[CW, "Frame", "All Other"]   = 0.023 -> $23
    Special base = SpecialFormIncldgTheftTimeElementBaseRate
                   [CW, "Frame", "All Other", "Other than Apts"] = 0.047 -> $47

Both final rates are straight copies — no `Factor`, no deductible, no
coinsurance.

### Broad and Special are identical to chunk 5's plain Business Income

**$23 and $47, the same two numbers.** Not a coincidence and not a defect: both
coverages read the same shared tables, and on a Frame risk with extra expense
and a non-apartment classification, the pinned literals land on exactly the rows
plain Business Income computes its way to.

**The pins only bite when the parent is not Frame, or is apartments** — which is
what C7-18 and C7-19 exist to show. This case cannot distinguish a hardcoded
`"Frame"` from a derived one, and says so.

---

## One correction — omitting a field is not the same as saying "Not Applicable"

The first run returned **$0 for both Basic forms** with `TypeOfRiskFactor`
sitting at a perfectly good **0.55** one field away.

`SetFactor` picks by priority, and its second branch tests

    MonthlyLimitOfIndemnity != "Not Applicable"

through `FirstValue FromConstant=""`. **An absent field reads as `""`**, which
is not equal to `"Not Applicable"` — so the branch is **elected**, and it copies
`MonthlyLimitOfIndemnityFactor`, which nothing has computed. `Factor` lands on
**0**, and both Basic premiums are zero with **no message**.

Chunk 5's Business Income record carries `MonthlyLimitOfIndemnity: "Not
Applicable"` explicitly, so chunk 5 never met this. **The trap is that the
"default" answer has to be sent**: there is no branch for "the submitter did not
mention monthly limit of indemnity".

This is a different shape from chunk 6's derived-field traps — nothing is
overwritten here. **A missing optional field silently elects a priced branch.**

---

## What this case cannot show

* **Whether Broad's `"Frame"` and Special's apartment key are really pinned.**
  On this risk a derived key would give the same rows. C7-18, C7-19.
* **The dependency itself.** One rate matching does not prove it was copied
  rather than coincidentally equal. C7-10.
* **Earthquake**, which has no standalone premium file at all. C7-11.
* **Anything about the other 46 jurisdictions.** C7-04.
