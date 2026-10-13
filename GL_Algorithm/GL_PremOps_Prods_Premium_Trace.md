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

**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — every step below was
re-read in `GL CW 20270401 V02` and watched executing in the engine's trace (offline, strict-erc):
Oklahoma at 2027-04-01 (`GL_OK_20270401_V04` over `GL_CW_20270401_V02`) and the Oklahoma ISO
golden case at 2026-08-01 (`GL_OK_20260801_V01` over `GL_CW_20260101_V01`). The worked figures in
§2a are the engine's. All 16 `tests/verify_*` suites pass.

> **Edition scope.** This traces the **2027-04-01 countrywide edition** (V01; V02 is identical
> for these two coverages). The editions in force for policies effective **before** 2027-04-01
> (CW 20231201 V02/V03, 20260101 V01, 20261001 V01) run a longer chain: Prem/Ops 99 rules
> against 86, Products 89 against 81. The differences that move money: **Med Pay** is a separate
> per-class `MedicalPaymentsCharge` added into the Prem/Ops premium (`LookupMedPayFactor`) rather
> than a term inside `FinalILF` (`LookupIncreasedMedPayLimitFactor`); each coverage computes its
> own **`MinPremium`** and the policy-level `…PremiumToReachMinCoverage` records add a top-up
> (§4); BI/PD split-limit weights and `SetBIILF`/`SetPDILF` feed the ILF; and there is **no $1
> floor**. Section-by-section notes below flag where this matters.

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
BaseRate = round( LossCost × LCM , 3 )                 loss cost filed (≠ 0)
BaseRate = round( ELP × LCM , 3 )                      loss cost = 0  → the ELP path
         × ClaimsMadeMultiplier                        when the coverage form is Claims Made
```

**The ELP path is selected by the loss cost being `0`**, not by a company choosing to file
one: `SetBaseRate` tests `LossCost = 0.0` and, if so, uses the ELP instead (the ELP rule itself
returns `0` when the class's `ELPText` says *"Rate/Loss Cost Applies"*). Prem/Ops has the third
branch for classes `16905`/`16906` **when the Amendment of Liquor Liability Exclusion endorsement
is attached** (`LossCost × BringYourOwnAlcoholExclusionFactor × LCM`). Assigned only when
currently null, so a supplied `BaseRate` survives. *Engine:* OK golden, class 50017 — Prem/Ops
loss cost 0.093 → `BaseRate` 0.093; Products loss cost **0**, so ELP 0.82 → `BaseRate` 0.820.
A loss cost that resolves to **null** (no row in the state or CW table) is not a zero — the
kernel refuses the rating (OI-94, `Kernel._refuse_null_loss_cost`).

### Step 2 — `SetFinalRate`

```
FinalRate = round( BaseRate
          × FinalILF                              increased limits (the deductible credit is folded in here)
          × SizeOfRiskFinalRelativity             only when SizeOfRiskRatingApplies = Yes
          × PackageModFactor                      ┐
          × ExperienceRatingModificationFactor    │ all four read from policy level,
          × ExpenseModification                   │ five levels up
          × ModToUse                              ┘
          , 3 )
```

`FinalILF` is itself rounded to 3 places: `CSLILF − FinalDeductibleFactor` for Products; for
Prem/Ops `(CSLILF + MedicalPaymentsFactor − 1) − FinalDeductibleFactor` when the Med Pay limit
is anything but the included `"5,000"` and no Coverage C exclusion is attached, else `CSLILF −
FinalDeductibleFactor`; a result ≤ 0 is written as `0`. When size-of-risk does not apply the
relativity fields are written `0.0` and simply left out of the product — they are **not** a
multiplier of zero.

### Step 3 — `SetBasicLimitPremium`  ← **the sub-premium**

```
BasicLimitPremium = BaseRate
                  × (1 − FinalDeductibleFactor)
                  × SizeOfRiskFinalRelativity      (only when SizeOfRiskRatingApplies = Yes)
                  × PackageModFactor
                  × (Exposure / 1000)
```

Rounded to whole dollars, written only when the policy `Subline` is *Premises/Operations and
Products/Completed Operations* (otherwise `0`), and undivided by 1,000 for the bases that are not
per-thousand — the same split `SetPremium` makes.

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
> (§3), so the floor is what keeps a real-but-tiny risk visible. **The floor is new in the
> 2027-04-01 edition** — the CW 20231201–20261001 `SetPremium` rules have no such branch, so
> before that date a tiny exposure does round to 0 (engine: a $21 Products premium's terrorism
> charge, 21 × 0.004 = 0.084, is **1** at 2027-04-01 and **0** at 2026-10-02).
>
> Before 2027-04-01 `SetPremium` also adds the Prem/Ops coverage's `MedicalPaymentsCharge`
> (see *Edition scope*).

### Step 5 — `SetPremiumIndicator`

```
PremiumIndicator = 1 if Premium ≠ 0, else 0
```

### Gate — `SetCoverageOnPolicyIndicator`

Prem/Ops: `1` only when the policy's `Subline` is *Premises/Operations and Products/Completed
Operations*. Products: `1` for that subline unless `ProdsCompldOpsExclusion = Yes`, and also for
the *Products/Completed Operations* subline on its own. If the gate is `0`, `ErcProcess` writes
`Premium = 0` and none of the steps above runs.

### 2a. The chain, executed — engine figures

Oklahoma, class 50017 (*Abrasives Mfg.*, Manufacturing or Processing), $5,000,000 gross sales on
both coverages, 1,000,000 CSL / 2,000,000 aggregate, Med Pay $10,000, no deductible, no
size-of-risk, all mods 1.0:

| Step | Prem/Ops @ 2027-04-01 | Products @ 2027-04-01 | Prem/Ops @ 2026-08-01 (ISO golden) |
|---|---|---|---|
| Loss cost / ELP | 0.09 | 0 → ELP 0.82 | 0.093 |
| `BaseRate` (× LCM 1) | 0.090 | 0.820 | 0.093 |
| `CSLILF` | 2.14 | 1.76 | 2.14 |
| `MedicalPaymentsFactor` | 1.007 | — | 1.003* |
| `FinalILF` | 2.147 | 1.760 | 2.140 |
| `BasicLimitPremium` | 450 | 4,100 | 465 |
| `FinalRate` | 0.19323 → **0.193** | 1.4432 → **1.443** | 0.19902 → **0.199** |
| `Premium` | **965** | **7,215** | **996** (995 + `MedicalPaymentsCharge` 1) |

\* In the 2026 edition the factor is per class (`MedPayFactor`, CW row for 50017) and is not in
the ILF; it produces a `MedicalPaymentsCharge` of **1** that `SetPremium` adds instead. Products is
**7,215** in both editions. Packages: `GL_OK_20270401_V04` over `GL_CW_20270401_V02`;
`GL_OK_20260801_V01` over `GL_CW_20260101_V01`. The 2026 column is ISO's own Oklahoma example:
every figure in it, and the account total **8,229**, equals ISO's `Payloads/OK/1. Output.json`
(engine run on `Engine_Payloads/OK/submission.json`, which carries `TerrorismCoverage = "No"` as
ISO's output does — ISO's sample *input* says `"Yes"`, a known mismatch handled in
`tests/verify_stage3.py` F3).

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
resolve a value that those two coverages never consume — and in the engine's 2027-04-01 runs
they are not even invoked: `ErcRate` no longer calls them. The policy-level
`GeneralLiabilityPremOpsPremiumToReachMinCoverage` and `…ProdsCompldOps…` records are **switched
off** in this edition (`SetCoverageOnPolicyIndicator` writes `0` unconditionally, so `ErcProcess`
forces their `Premium` to `0` — a caller-supplied top-up is wiped; engine-tested). Minimum-premium
enforcement for this pair, on this edition, is not in the filed content and cannot be routed
through ISO's roll-up.

**Before 2027-04-01 it is.** In CW 20231201 V02/V03, 20260101 V01 and 20261001 V01 each coverage
runs `SetMinimumPremium` → `SetMinPremium` (Products: `round(MinimumPremium × FinalILF ×
AdditionalInterestFactor, 0)`), and the policy-level records compute `CoveragePremium` = Σ of
that coverage's classification premiums, `MinPremium` = the largest classification minimum, and
`Premium` = `MinPremium − CoveragePremium` when the minimum is higher (subject to the rule's own
package/multistate/exposure conditions), else `0` — a real, ISO-computed top-up. *Engine:* OK @
2026-08-01, `CoveragePremium` 996 / 7,215, `MinPremium` 0 (the CW minimum tables hold 0 for these
keys), top-up 0.

---

## 5. Summary

| Value | Where computed | Survives to the account total? |
|---|---|---|
| `BaseRate` | coverage | no — a rate, consumed by `FinalRate` and `BasicLimitPremium` |
| `FinalRate` | coverage | no — a rate, consumed by `Premium` |
| **`BasicLimitPremium`** | coverage | **no** — reaches policy level as `AnnualBasicLimitsCoPremium…`, a reported figure |
| **`Premium`** | coverage | **yes** — the only value that becomes money, via three summations |
| `PremiumIndicator` | coverage | not a premium — the gate that decides whether `Premium` counts |
| `MinPremium` | coverage | 2027 edition: no — never applied. Earlier editions: compared at policy level, the shortfall added as a top-up |
| `PremiumToReachMin`, `TotPremiumPriorToMin` | — | never written, never read |

---

## 6. Limits

- **Countrywide.** Six states rewrite `SetPremium` on GL, all of them Terrorism, so neither
  coverage traced here is affected. State packages were not re-traced rule by rule; the engine
  applies whatever a state overrides automatically.
- **Evaluated, not just structural (since 2026-10-02).** §2a's figures are engine output. The
  2026-08-01 column equals ISO's own priced output; the 2027-04-01 figures are the engine's and
  have **not yet been confirmed against ISO's live service** (`docs/PRD-GL-RATING-ENGINE.md` §8,
  C8). The engine's wider ISO agreement — 50 of 50 standard risks (`scripts/erc/out/phase2.csv`)
  and 184 of 184 varied risks in 11 jurisdictions (BUILD-LOG Entry 24) — is on pre-2027 editions.
- **Conditions flattened.** Each rule's branches are summarised; a live rating takes one path
  through them, not all.
