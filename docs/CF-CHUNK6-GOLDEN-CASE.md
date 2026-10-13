# Property chunk 6, task C6-01 — the golden cases

**Special Class, all four cause-of-loss forms.** Derived 2026-09-18.

**Every number below was read off the filed rows and worked out by hand before
the engine was run.** Where the engine disagrees, the disagreement is recorded
as the finding rather than edited away.

Script: [`scripts/cf/41_chunk6_golden_case.py`](../scripts/cf/41_chunk6_golden_case.py).

---

## The case

The **same Oregon location as chunks 1–5**, with a Special Class item on it.

| | |
|---|---|
| Building | class 0951, Frame, Protection Class 3, territory Portland, limit 100,000 — chunk 1 case A |
| Special Class item | `ClassDescription` **"Towers - Broadcasting Antennas (Cell, Radio and TV)"**, limit 100,000 |
| Group II inputs on the item | `BasicGroupIISymbol` **B**, `BasicGroupIIRatingTerr` **Entire State** |
| Terms | coinsurance 90%, deductible 1,000, LCM 1.0, `IncludedInBlkt` No, `IncludedInBuilding` No |

### What makes this chunk different before any arithmetic

**Special Class hangs off the LOCATION, not the Structure.** Contents live under
`Structure → OccupClass`; Business Income lives under the Structure. Special
Class is a **sibling of the Structure** on `CommercialPropertyLocation`. It is
the first coverage in the project that is not inside a building record.

**The base rate keys on prose, through two lookups in series:**

    ClassDescription  --SpecialClassDescriptionConvertedOption-->  Option34a
    Option34a + ProtectionClassToUse  --BasicGroupIRateSpecialClass-->  0.07

There is **no construction key** in Group I's base rate at all, and protection
class is a **key**, not a factor.

### The filed rows this case stands on

| Value | Table | Key |
|---|---|---|
| `Option34a` | `SpecialClassDescriptionConvertedOption` | CW, "Towers - Broadcasting Antennas (Cell, Radio and TV)" |
| 0.07 | `BasicGroupIRateSpecialClass` | CW, Option34a, **"1 to 4"** |
| **8** | `SpecialClassBasicGroupIINumber` | CW, the same description string |
| 0.028 | `BasicGroupIIRate` | OR, Entire State, B, **Bldg** |
| 0.015 | `BroadFormBaseRate` | CW, **"Frame"** — a hardcoded literal, Bldg |
| 0.047 | `SpecialBuildingRate` | **OR**, "Y" — countrywide files no row |
| 0.95 | `CoinsuranceFactor` | CW, 90% |
| 0.98 / 0.98 / 0.97 | `DeductibleFactor` | OR, "1,000", 50,000–175,000, Basic Group I / Basic Group II / Other Cause Of Loss |

`TotAmtInsuranceToUse` resolves to the item's **own limit**: `SetTotAmtInsurance`
copies `Limit` when the item is not blanketed, and `SetTotAmtInsuranceToUse`
copies that through when `IncludedInBuilding` is not "Yes". So the band is
50,000–175,000, not the location total.

---

## Predictions and results

| Form | Base | Rate | Adjusted | Final | **Premium** | |
|---|---|---|---|---|---|---|
| Basic Group I | 0.07 | 0.07 | 0.067 | 0.066 | **$66** | ✅ exact |
| Basic Group II | 0.028 | **0.224** | 0.213 | 0.209 | **$209** | ✅ exact |
| Broad | 0.015 | 0.015 | 0.014 | 0.014 | **$14** | ✅ exact |
| Special | 0.047 | 0.047 | 0.045 | 0.044 | **$44** | ✅ exact |
| Building Group I | | | | | **$261** | ✅ unmoved |
| Building Group II | | | | | **$32** | ✅ unmoved |

**Every predicted intermediate landed, on all four forms** — the first chunk in
the project where no rate step needed correcting. Both half-up ties resolved
upward as derived. Chunk 0's foundation ran unchanged: **no new interpreter
node**, a sixth coverage on the same machinery (C6-02).

One thing had to be fixed before the run would produce Broad or Special at all,
and it is a finding, not a typo — see below.

### Basic Group I — 7 rules

    coins  = CoinsuranceFactor[CW, 90%]                      = 0.95   (computed FIRST)
    base   = BasicGroupIRateSpecialClass[CW, Option34a, "1 to 4"]  = 0.07
    rate   = r3(0.07 x LCM 1.0)                              = 0.07
    COLadj = 0.07 x VandalismExcl 1.0 x StdPropPolGpI 1.0    = 0.07
    adj    = r3(0.07 x 0.95) = r3(0.0665)                    = 0.067   <- a half-up tie
    dedF   = DeductibleFactor[OR, 1,000, 50k-175k, Basic Group I]  = 0.98
    final  = r3(0.067 x dedByLoc 1.0 x 0.98) = r3(0.06566)   = 0.066
    premium = round(100,000/100 x 0.066 x 1 x 1 x 1, 0)      = $66

**No territory factor, no protection-class factor, no LOI factor, no roof
factor, no substandard or vacant addend.** Building's Group I applies five
things this chain does not have.

### Basic Group II — 10 rules, and the numeric value is the whole story

    numeric = SpecialClassBasicGroupIINumber[CW, the description]  = 8
    base    = BasicGroupIIRate[OR, Entire State, B, "Bldg"]        = 0.028
    rate    = r3(0.028 x LCM 1.0 x 8)                              = 0.224
    COLadj  = 0.224 x StdPropPolGpII 1.0                           = 0.224
    coins   = 90% is not in (50,60,70,None), so copy the shared    = 0.95
    adj     = r3(0.224 x 0.95) = r3(0.2128)                        = 0.213
    dedF    = DeductibleFactor[OR, 1,000, 50k-175k, Basic Group II] = 0.98
    final   = r3(0.213 x 1.0 x 0.98) = r3(0.20874)                 = 0.209
    premium = 1,000 x 0.209                                        = $209

**Group II is three times Group I on the same item.** The numeric value is a
straight multiplier of 8 — a broadcasting tower is eight times the wind hazard
of the base symbol — where Building's equivalent is 1 on almost every risk. It
is also the largest single multiplier found anywhere in six chunks. No BCEG
factor here, unlike Building's Group II.

### Broad — 5 rules, construction-blind

    base   = BroadFormBaseRate[CW, "Frame" (LITERAL), "Bldg"]  = 0.015
    rate   = r3(0.015 x 1.0)                                   = 0.015
    adj    = r3(0.015 x 0.95) = r3(0.01425)                    = 0.014
    dedF   = DeductibleFactor[OR, 1,000, 50k-175k, Other Cause Of Loss] = 0.97
    final  = r3(0.014 x 1.0 x 0.97) = r3(0.01358)              = 0.014
    premium = 1,000 x 0.014                                    = $14

The `"Frame"` is a hardcoded constant in the rule, not the item's construction.
C6-22 proves it by changing the construction and watching nothing happen.

### Special — 9 rules

    theftF = 1.0                                (no theft-exclusion record)
    base   = SpecialBuildingRate[OR, "Y"]       = 0.047   <- CW files NO row
    rate   = r3(0.047 x 1.0)                    = 0.047
    COLadj = 0.047 x 1.0                        = 0.047
    adj    = r3(0.047 x 0.95) = r3(0.04465)     = 0.045   <- a second half-up tie
    dedF   = 0.97
    final  = r3(0.045 x 1.0 x 0.97) = r3(0.04365) = 0.044
    premium = 1,000 x 0.044                     = $44

The base rate is read from the **same table, with the same key shape, as
Building's Special form** — and countrywide files no row in it. Oregon does.
Chunk 3 found that gap on Building; this is its second consumer.

---

## One correction — `PolicyType` is derived, four levels up

The first run priced **Broad and Special at zero** with `PolicyType` set on the
Special Class item, exactly as the algorithms page describes the gate.

`SetPolicyType` in the `CommercialPropertySpecialClass` group copies from
`../../../../PolicyType` — the **policy** record — with **no `IsNull` guard**.
A value supplied on the item is overwritten with blank, and both Broad's and
Special's base rates gate shut and price at zero with no message.

**This is the fifth derived-field trap in four chunks**, after chunk 3's
`SpecialBaseRate` (guarded, so the submission wins), chunk 4's
`OccupCategoryRiskSeverity` and `CauseOfLoss`, and chunk 5's
`ApartmentCondoIndicator`. It is the first one whose real home is **four levels
above** the coverage being rated — on the policy, not on the item, the building
or the location. Nothing in the payload for this coverage hints at it.

The fix is one line at the policy level. The lesson is the one chunk 4 already
wrote down and this makes standing: **before treating a zero as a missing rate,
find who else writes the field.**

---

## What this case is built to settle

**Two half-up ties, on purpose.** `0.0665 → 0.067` and `0.04465 → 0.045` both
sit exactly on the rounding boundary. Chunk 0's `ROUND_HALF_UP` has been
exercised before, but never twice in one case on two different forms.

**Building must not move.** Special Class is a sibling of the Structure, not a
child of it, so its 100,000 limit should not reach Building's `TotAmtInsurance`
and should not change Building's deductible factor. **Predicted $261 / $32** —
chunk 1 case A and chunk 2, unchanged. If Building moves to $263 instead, the
location total does include Special Class and the chunk 1 deductible finding
reaches a fourth coverage.

## What this case cannot show

* **Whether the deductible band follows the item or the location.** With a
  100,000 limit the item's own band (50k–175k) and the location total's band
  (200k, 175k–500k) give 0.98 / 0.98 / 0.97 against 0.99 / 0.98 / 0.98 — and
  after rounding, three of the four premiums are identical either way. A
  discriminating limit is C6-03's job.
* **Anything about the other 46 jurisdictions.** C6-04.
* **Whether Florida or New York can rate this at all.** C6-11 and C6-12.
