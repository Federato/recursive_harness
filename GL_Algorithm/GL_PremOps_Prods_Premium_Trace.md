# Premises/Operations and Products/Completed Operations — full premium trace

**What this traces:** for GL's two core coverages, every premium value computed along the way,
and which of them survive into the account total.

**The headline:** each coverage computes **two** premium figures, and **only one of them is
money.** The other travels all the way to policy level and is never added to anything.

**Source:** `GL CW 20270401 V01` —
`GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` and
`GeneralLiabilityClassificationProdsCompldOpsCoverageRules.Rule.xml`.
**Companion:** `GL_Premium_Map.md` (the whole line), `GL_Premium_Tree.html` (navigable).

**Written:** 2026-09-17.

---

## 1. The two coverages are structurally identical

Both sit at depth 3, both are leaves, and both carry the same seven rules. Every difference
between them is a substituted field name:

| | Premises/Operations | Products/Completed Operations |
|---|---|---|
| Loss cost | `PremOpsLossCost` | `ProdsCompldOpsLossCost` |
| Company ELP | `PremOpsELP` | `ProdsCompldOpsELP` |
| Exposure | `../PremOpsCovExposure` | `../ProdsCompldOpsCovExposure` |
| Size-of-risk | `PremOpsSizeOfRiskFinalRelativity` | `ProdsCompldOpsSizeOfRiskFinalRelativity` |
| Minimum premium lookup | `LookupPremOpsMinPremium`, `LookupSpecialCombinedMinPremium` | `LookupProdsCompldOpsMinPremium` |

Prem/Ops carries one extra rule — `LookupSpecialCombinedMinPremium` — and one extra base-rate
branch for class codes `16905` / `16906`, which apply a
`BringYourOwnAlcoholExclusionFactor`. Otherwise the two files are the same program.

---

## 2. The chain, in order

### Step 1 — `SetBaseRate`

```
BaseRate = LossCost × LCM
```

or, where a company files its own expected loss premium, `ELP × LCM`. Prem/Ops has the third
branch for the alcohol-exclusion classes. Assigned only when currently null, so a supplied
`BaseRate` survives.

### Step 2 — `SetFinalRate`

```
FinalRate = BaseRate
          × FinalILF                              increased limits (the deductible credit is folded in here)
          × SizeOfRiskFinalRelativity
          × PackageModFactor                      ┐
          × ExperienceRatingModificationFactor    │ all four read from policy level,
          × ExpenseModification                   │ five levels up
          × ModToUse                              ┘
```

### Step 3 — `SetBasicLimitPremium`  ← **the sub-premium**

```
BasicLimitPremium = BaseRate
                  × (1 − FinalDeductibleFactor)
                  × SizeOfRiskFinalRelativity      (only when SizeOfRiskRatingApplies = Yes)
                  × PackageModFactor
                  × (Exposure / 1000)
```

**Note what is absent: `FinalILF`, the experience mod, the expense mod and `ModToUse`.** This
is deliberate — it is the *basic limits* premium, the figure before increased limits and before
the account's own modifications. It is a different quantity from the premium, not an
intermediate step toward it.

### Step 4 — `SetPremium`  ← **the money**

```
Premium = round( FinalRate × Exposure / 1000 , 0 )
```

for the nine per-thousand bases (Admissions, Area, Gallons, Gross Sales, Kilowatt-hours,
Payroll, Total Cost, Total Operating Expenses, Vehicles); otherwise `FinalRate × Exposure`
undivided. Rounded to **whole dollars at the coverage**, not at the total.

> **A floor almost nobody knows about.** If the calculation produces **0** while exposure is
> **greater than 0**, the rule writes `Premium = 1.0`. A real exposure can never rate to
> nothing — it rates to one dollar. This matters because the roll-up treats 0 as "no coverage"
> (§3), so the floor is what keeps a real-but-tiny risk visible.

### Step 5 — `SetPremiumIndicator`

```
PremiumIndicator = 1 if Premium ≠ 0, else 0
```

### Gate — `SetCoverageOnPolicyIndicator`

`1` only when the policy's `Subline` is *Premises/Operations and Products/Completed
Operations*. If the subline says otherwise, the whole coverage is off before any of the above
matters.

---

## 3. What survives, and what does not

**`Premium` survives. `BasicLimitPremium` does not — but it still travels.**

### The money track

```
Premium  (coverage, depth 3)
   │   CalculateTotalPremium: contribute Premium only if
   │   PremiumIndicator = 1 AND Premium ≠ 0, else contribute 0
   ▼
GeneralLiabilityClassification.ErcCalculatedTotalPremium      depth 2
   │   summed with its 18 sibling children — Terrorism, Liquor, Pollution,
   │   Cyber Prem/Ops and Prods, Loss of Electronic Data, Railroad,
   │   Owners & Contractors, Underground Storage Tank, Snowplow,
   │   Unmanned Aircraft, Med Pay Exclusion C, and the classification's own Premium
   ▼
GeneralLiabilityLocation.ErcCalculatedTotalPremium            depth 1
   ▼
GeneralLiability.ErcCalculatedTotalPremium                    depth 0  ← THE ACCOUNT TOTAL
```

Three summations from coverage to account. Nothing re-reads a stored subtotal — each level
passes its value up as a `RunRule` return, so the stored `ErcCalculatedTotalPremium` at each
level is an output for the caller, not an input to the level above.

### The statistical track

`BasicLimitPremium` is read **nine times** — five times inside Prem/Ops, four inside
Prods/Completed Ops, and **four times at policy level**, by exactly two rules:

| Rule (on `GeneralLiability`) | Writes |
|---|---|
| `SetAnnualBasicLimitsCoPremiumPremOps` | `AnnualBasicLimitsCoPremiumPremOps` |
| `SetAnnualBasicLimitsCoPremiumProdCompldOps` | `AnnualBasicLimitsCoPremiumProdCompldOps` |

Both read `BasicLimitPremium` and the `Subline`, and write a policy-level annual basic-limits
figure. **Neither feeds `CalculateTotalPremium`.** The basic-limits premium reaches the top of
the policy and lands in its own field, for statistical and company reporting — it is never
added to what the insured pays.

**So the answer to "which sub-premiums persist": one does, and it persists into a parallel
figure rather than into the total.**

---

## 4. Minimum premium — looked up, and nothing more

Both coverages own minimum-premium lookups: `LookupPremOpsMinPremium`,
`LookupProdsCompldOpsMinPremium`, and Prem/Ops's `LookupSpecialCombinedMinPremium`. Two related
datadefs exist on every record — `PremiumToReachMin` and `TotPremiumPriorToMin`.

**Measured across the corpus: both are written 0 times and read 0 times.** `MinPremium` itself
is written 4 times and read 10, but every reader is a different coverage —
`…CyberIncidentLiabilityPremiumToReachMinCoverage`,
`…LossOfElectronicDataPremiumToReachMinCoverage`,
`…LimitedProductWithdrawalExpenseEndtPremiumToReachMinCoveragePolLvl`.

**Neither Prem/Ops nor Prods/Completed Ops applies a minimum to its own premium.** The lookups
resolve a value that those two coverages never consume. Minimum-premium enforcement for this
pair, if it is wanted, is not in the filed content.

---

## 5. Summary

| Value | Where computed | Survives to the account total? |
|---|---|---|
| `BaseRate` | coverage | no — a rate, consumed by `FinalRate` and `BasicLimitPremium` |
| `FinalRate` | coverage | no — a rate, consumed by `Premium` |
| **`BasicLimitPremium`** | coverage | **no** — reaches policy level as `AnnualBasicLimitsCoPremium…`, a reported figure |
| **`Premium`** | coverage | **yes** — the only value that becomes money, via three summations |
| `PremiumIndicator` | coverage | not a premium — the gate that decides whether `Premium` counts |
| `MinPremium` | coverage | no — resolved, never applied by these two coverages |
| `PremiumToReachMin`, `TotPremiumPriorToMin` | — | never written, never read |

---

## 6. Limits

- **Countrywide.** Six states rewrite `SetPremium` on GL, all of them Terrorism, so neither
  coverage traced here is affected — but state packages were not re-traced rule by rule.
- **Structural.** Read from rule XML; no premium was computed and no path exercised live.
- **Conditions flattened.** Each rule's branches are summarised; a live rating takes one path
  through them, not all.
