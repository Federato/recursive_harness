# Owners & Contractors Protective / Principals Protective — Rating Algorithms

**Source ERC packages:** `GL_CW_20230501_V01`, `GL_CW_20231201_V03` (pre-2027 algorithm) and
`GL_CW_20270401_V01` (2027 algorithm)
**Line:** General Liability (GL), Countrywide, Subline Code 335
**Rule:** Manual Rule 46 — "Owners And Contractors Protective Liability Insurance And Principals
Protective Liability Insurance" (`GL-MU-2027-RU-001-C` p.103, cited in
`GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md` § 2)
**Reformatted from:** `docs/gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`
**Documented:** 2026-08-20

This document covers **Owners & Contractors Protective (OCP)** and **Principals Protective**
liability, which share one ERC rule set (subline 335, Rule 46). It does **not** cover Railroad
Protective Liability — same subline code, different rule (Rule 49) — which is out of scope for this
port; see `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.5 for that coverage.

Standalone Coverage Part — not an endorsement to the CGL (per `GATE-335` § 1 and
`03-SUBLINE-COVERAGE-PLAN.md` § 3.2.4). Class-level coverage, no territory dimension, **no
deductibles** (Rule 15 is explicitly excepted, `GL-MU-2027-RU-001-C` p.104), no size-of-risk
mechanism, and — unlike sublines 334 and 336 — **no `PackageModFactor`**.

> **Gate status note.** `GATE-335` reports this gate as **passed with no oracle** — the corpus
> holds one rated output (the Oklahoma golden case) and it carries no OCP coverage; of 516 STC
> submissions, 8 carry an OCP exposure and none has a paired expected output. Every formula below is
> derived from ERC rule/table names and confirmed at six points against the filed manual (`GATE-335`
> § 2), not reproduced against a published premium. The worked example in this document's Quick
> Reference section is a **prediction, not a confirmation** — see `GATE-335` § 8.

---

## Master orchestration

**Which algorithm runs is selected entirely by the resolved parent edition — not by
jurisdiction.** Per `GATE-335` § 0, all 51 jurisdictions publish OCP loss costs today; 43 of them
withdraw the loss-cost table in a single simultaneous program change effective 2027-04-01. So the
same state can run either chain below depending on the risk's effective date.

### CW 2023 and earlier — 21 steps

```
ErcSetRatesAndFactors (11):
    SetLossCost
    SetLossCostOverOneMillion
    SetLossCostOverOneHundred
    SetPrincipalsProtvLiabFactor
    SetELPOverride
    SetELPOverOneMillionOverride
    SetLCM
    SetELP
    SetELPOverOneHundred
    SetELPOverOneMillion
    SetILF

ErcRate (10):
    SetBaseRate
    SetBaseRateOverOneMillion
    SetBaseRateOverOneHundred
    SetFinalRate
    SetFinalRateOverOneMillion
    SetFinalRateOverOneHundred
    SetMinimumPremium
    SetMinPremium
    SetPremium
    SetPremiumIndicator
```

### CW 2027 and later — 12 steps

```
SetELPOverride
SetELPOverOneMillionOverride
SetLCM
SetELP
SetELPOverOneMillion
SetILF
SetBaseRate
SetBaseRateOverOneMillion
SetFinalRate
SetFinalRateOverOneMillion
SetPremium
SetPremiumIndicator
```

The 2027 program deletes the entire published loss-cost path (`SetLossCost`,
`...OverOneMillion`, `...OverOneHundred`), the minimum-premium steps (`SetMinimumPremium`,
`SetMinPremium`), and the `OverOneHundred` band entirely. It also removes the class-`15191`
Workers Compensation special case from `SetELP` (class `15191` itself is retired). Per `GATE-335`
§ 1: "**N4 is not a tail case for 335, it is the whole coverage.** Two different algorithms, two
different class lists, two different premium functions, selected by the resolved parent."

One dead artifact survives the cut: `LookupPrincipalsProtvLiabFactor` is still present in the CW
2027 rule set but has no caller, because `SetPrincipalsProtvLiabFactor` was deleted (`GATE-335` § 1,
Escalation E14).

---

## File map

| Piece | ERC rule set / rule | Source |
|---|---|---|
| Rate build-up + premium (both editions) | `GeneralLiabilityClassificationOwnersContractorsCoverageRules` | referenced via `scripts/erc/29_census_336.py --rules GeneralLiabilityClassificationOwnersContractorsCoverageRules`, per `GATE-335` § 6 |
| Loss-cost tables (pre-2027 only) | `OwnersContractorsLossCost`, `...OverOneMillion`, `...OverOneHundred` | state-filed, 8 jurisdictions (`GATE-335` § 5) |
| ELP tables | `OwnersContractorsELP`, `...OverOneMillion`, `...OverOneHundred` | state-filed, all 51 jurisdictions (`GATE-335` § 5) |
| Refer-to-company selector | `OwnersContractorsELPText` | state-filed, all 51, 433 rows (`GATE-335` § 5, § 7) |
| Increased-limits factor | `ILFOwnersContractors` | state-filed (`GATE-335` § 5) |
| Workers Compensation factor (pre-2027, class `15191` only) | `PrincipalsProtvLiabFactor` | countrywide, 1 row: `"CW","Y",0.75` (`GATE-335` § 5) |
| Minimum premium (pre-2027 only) | `PremOpsMinPremium` — **reused from subline 334 (Premises/Operations)**, not an OCP-specific table | countrywide, 3 rows (`GATE-335` § 5) |

> Not resolved in source docs — the gate doc does not give the underlying `.Rule.xml` file name(s)
> or line numbers for any of these rules, unlike the CF source material. Citations above use the
> rule/table names and the gate document's own section numbers, per the reformatting instructions.

---

## CW 2023 and earlier — rate build-up

Executed in the 21-step order in **Master orchestration** above. Steps grouped by what they
compute (per `GATE-335` § 1, § 4, § 7):

### Step 1 — Published loss cost (state-filed path)
`SetLossCost`, `SetLossCostOverOneMillion`, `SetLossCostOverOneHundred`

Reads `OwnersContractorsLossCost` (+ the two band tables), keyed on **(state, class)** — no
territory (`GATE-335` § 5). Countrywide holds 0 rows for all three tables; populated in 8
jurisdictions (CA, FL, GA, MA, NJ, NV, NY, WA) as of the effective dates in this edition family;
absent in the other 43 (`GATE-335` § 0, § 5).

Selector gate: `OwnersContractorsELPText` marks each (state, class) as `"Rate/Loss Cost Applies"`,
`"Industry"`, or `"Company"`. Per `GATE-335` § 7, selector `Rate/Loss Cost Applies` agrees with a
non-zero published loss cost in 433/433 tested rows — the loss cost path is only live where the
selector says so.

### Step 2 — Workers Compensation factor (prerequisite for Step 3, class `15191` only)
`SetPrincipalsProtvLiabFactor`

```
PrincipalsProtvLiabFactor = 0.75      # single countrywide cell, "CW","Y",0.75
```

Confirmed independently against the manual's ELP Supplement: *"15191 Percentage of otherwise
applicable Workers Compensation loss costs: 75%"* (`GL-AK-2020-LC-001-C` p.9, Table 5.C, cited in
`GATE-335` § 2).

### Step 3 — ELP (fallback / class-driven path)
`SetELPOverride`, `SetELPOverOneMillionOverride`, `SetLCM`, `SetELP`, `SetELPOverOneHundred`,
`SetELPOverOneMillion`

`SetELP` branches three ways on class code (`GATE-335` § 1):

```
if OwnersContractorsClassCode = "":
    ELP = 0.0
elif OwnersContractorsClassCode = "15191":
    ELP = PrincipalsProtvLiabFactor x WorkersCompensationRate
else:
    ELP = LookupOwnersContractorsELP(state, class)
```

`WorkersCompensationRate` is a declared submission input field
(`MasterGLCW.DataDef.xsd`, `xs:decimal`, 4 fraction digits) — not an ERC table value (`GATE-335`
§ 1). It is required whenever class `15191` is present, and only in this (pre-2027) edition family.

`OwnersContractorsELP`, `...OverOneMillion`, `...OverOneHundred` are keyed on **(state, class)**
— 0 rows countrywide, populated in all 51 jurisdictions (`GATE-335` § 5).

Selector `Company` marks refer-to-company classes and carries `0` in the ELP table for every one
of them — confirmed 147/147 across all 51 jurisdictions (`GATE-335` § 7). The manual's ELP
Supplement prints `RTC` for exactly those classes (`17982`, `93040`), confirming ERC's `Company`
value means Refer To Company (`GATE-335` § 2, § 7).

### Step 4 — Increased limits factor
`SetILF`

Reads `ILFOwnersContractors`, keyed on **(state, occurrence limit, aggregate limit)** — no
territory, no table-assignment dimension (`GATE-335` § 5). If either limit field is empty, `ILF =
0.0` (`GATE-335` § 4). **Limit vocabulary is `"1,000,000"` / `"2,000,000"`, not `"1,000,000
CSL"`** as used by sublines 334/336 — a shared limit-normalisation helper across sublines will
miss every OCP ILF lookup (`GATE-335` § 4).

New York overrides `SetILF` with its own increased-limits treatment (`GATE-335` § 6) — the only
premium-affecting state override found for this subline.

### Step 5 — Base rate
`SetBaseRate`, `SetBaseRateOverOneMillion`, `SetBaseRateOverOneHundred`

```
BaseRate = round(LossCost x LCM, 3)     when LossCost <> 0
         = round(ELP      x LCM, 3)     when LossCost = 0
```

Per `GATE-335` § 1: "and the same for the OverOneMillion / OverOneHundred bands, each from its own
loss-cost / ELP table." Six rate sources feed one coverage: `OwnersContractorsLossCost` /
`OwnersContractorsELP` and their `OverOneMillion` and `OverOneHundred` counterparts.

### Step 6 — Final rate
`SetFinalRate`, `SetFinalRateOverOneMillion`, `SetFinalRateOverOneHundred`

```
FinalRate = round(BaseRate x ILF x ExperienceRatingModificationFactor
                          x ExpenseModification x ModToUse, 3)
```

Applied identically to the base band and each `OverOneMillion` / `OverOneHundred` band, per
`GATE-335` § 1.

> Not resolved in source docs — `ExperienceRatingModificationFactor`, `ExpenseModification`, and
> `ModToUse` are named in the formula but the gate doc does not describe their sources or how they
> differ from one another; treat them as pass-through policy-level factors until a source document
> resolves them.

### Step 7 — Minimum premium
`SetMinimumPremium`, `SetMinPremium`

```
MinPremium = round(MinimumPremium x ILF, 0)
```

Reads `PremOpsMinPremium` — **reused from subline 334**, not an OCP-specific table. **No
`AdditionalInterestFactor`**, unlike subline 336's minimum premium (`GATE-335` § 1). Silently not
applied (`MinPremium = 0.0`) when `Subline <> "Owners and Contractors"` (`GATE-335` § 4).

---

## CW 2027 and later — rate build-up

Executed in the 12-step order in **Master orchestration** above. `SetLossCost` and its two band
variants, `SetPrincipalsProtvLiabFactor`, `SetELPOverOneHundred`, `SetMinimumPremium`, and
`SetMinPremium` are all deleted. What remains is purely ELP-driven, with one breakpoint and no
minimum premium (`GATE-335` § 1).

### Step 1 — ELP
`SetELPOverride`, `SetELPOverOneMillionOverride`, `SetLCM`, `SetELP`, `SetELPOverOneMillion`

The class-`15191` Workers Compensation branch is removed (class `15191` is retired by 2027); every
class resolves via `LookupOwnersContractorsELP(state, class)` or the `Company` refer-to-company
selector (`GATE-335` § 1). The `27111`/`27112` classes that drove the 100-unit breakpoint are also
retired, replaced by a single class `27113` with no special basis (`GATE-335` § 0).

### Step 2 — Increased limits factor
`SetILF` — same rule and same `ILFOwnersContractors` table as the pre-2027 edition.

### Step 3 — Base rate
`SetBaseRate`, `SetBaseRateOverOneMillion`

```
BaseRate = round(ELP x LCM, 3)
```

Loss cost no longer exists as a source — `LossCost` is never non-zero in this edition, so the
`BaseRate` formula collapses to the ELP branch only.

### Step 4 — Final rate
`SetFinalRate`, `SetFinalRateOverOneMillion` — same formula shape as the pre-2027 edition (Step 6
above), applied to the base band and the `OverOneMillion` band only (no `OverOneHundred` band in
this edition).

### No minimum premium
`SetMinimumPremium` and `SetMinPremium` are both deleted (`GATE-335` § 1). Premium is not floored.

---

## OCP / Principals Protective — premium

Rule 5 (standard Premium Computation) does not apply to this subline: *"1. Rule 5. Premium
Computation does not apply."* (`GL-MU-2027-RU-001-C` p.104, cited in `GATE-335` § 2). OCP has its
own piecewise premium function instead, common in shape to both edition families.

### Gate — coverage on policy
`SetPremium`'s outer test fails when `OwnersContractorsClassCode` is blank → `Premium = 0.0`
(`GATE-335` § 4). `SetELP` and `SetILF` gate separately on `OwnersContractorsClassDescription` —
**a different field than the code.** A submission carrying the code but not the description gets a
loss cost/ELP and no ILF, so `FinalRate = BaseRate x 0`, producing a **zero premium rather than an
error** (`GATE-335` § 4).

### Branch A — standard classes (breakpoint $1,000,000, divisor 1000)
Applies to every class except the two legacy classes in Branch B:

```
Premium = round(
    FinalRate x min(Exposure, 1000000) / 1000
  + FinalRateOverOneMillion x max(0, Exposure - 1000000) / 1000
, 0)
```

### Branch B — legacy classes `27111` / `27112` (breakpoint 100 units, no divisor)
**Pre-2027 only** — these two class codes are hardcoded directly in `SetPremium` (`GATE-335` § 0,
§ 1). Retired entirely by the 2027 program; no equivalent branch exists in the CW 2027 chain.

```
Premium = round(
    FinalRate x min(Units, 100)
  + FinalRateOverOneHundred x max(0, Units - 100)
, 0)
```

> Not resolved in source docs — the gate doc gives the breakpoint (100 units) and confirms no
> divisor applies, and states the formula shape mirrors Branch A, but does not spell out the
> Branch B formula symbol-for-symbol the way it does for the general case. The formula above is
> constructed by substituting the stated breakpoint/divisor pair into the general piecewise
> pattern given in `GATE-335` § 1; treat the exact variable name (`Units` vs `Exposure`) as
> unconfirmed.

### Minimum premium override (pre-2027 only)
```
Premium = max(Premium, MinPremium)     # applied when Subline = "Owners and Contractors"
```
> Not resolved in source docs — `GATE-335` § 1 gives the `MinPremium` formula (Step 7 above) but
> does not state explicitly whether it is a floor (`max`) or an add-on to `Premium`. `max` is the
> conventional reading of "minimum premium" and is used here as the best-supported interpretation,
> not a literal quote.

### Premium indicator
`SetPremiumIndicator` — no detail beyond the rule name given in source docs.

---

## CW 2023 vs CW 2027 — side by side

| | CW 2023 and earlier | CW 2027 and later |
|---|---|---|
| Total steps | 21 (11 + 10) | 12 |
| Published loss-cost path | present (`SetLossCost` + 2 bands) | **deleted entirely** |
| Marginal tiers | two breakpoints: `$1,000,000` and `100 units` | one: `$1,000,000` |
| `OverOneHundred` band | present (loss cost, ELP, base rate, final rate) | **deleted** |
| Workers Compensation input (class `15191`) | `ELP = PrincipalsProtvLiabFactor x WorkersCompensationRate` | **removed** — class `15191` retired, `SetELP` no longer references it |
| Minimum premium | `SetMinimumPremium` + `SetMinPremium`, reading `PremOpsMinPremium` | **both deleted** |
| Class codes hardcoded in `SetPremium` | `27111`, `27112` | **none** |
| Class list | `15191`, `15192`, `27111`, `27112`, plus unchanged classes | `27113` replaces the two `271xx` classes; `15191`/`15192` retired |
| `LookupPrincipalsProtvLiabFactor` | called by `SetPrincipalsProtvLiabFactor` | **present but uncalled** — vestigial (`GATE-335` § 1, Escalation E14) |
| Loss-cost jurisdictions | 51 of 51 (as of today, per `GATE-335` § 0 correction) | 8 of 51 — but moot, since the loss-cost path doesn't exist in this edition |

Source: `GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md` § 0, § 1.

---

## Supporting lookups

| Rule / Table | Keys | Layer | Notes |
|---|---|---|---|
| `OwnersContractorsLossCost` (+ `OverOneMillion`, `OverOneHundred`) | state, class | state only, 0 rows CW | 8 jurisdictions publish; absent in 43 (`GATE-335` § 5) |
| `OwnersContractorsELP` (+ `OverOneMillion`, `OverOneHundred`) | state, class | state only, 0 rows CW | populated in all 51 (`GATE-335` § 5) |
| `OwnersContractorsELPText` | state, class | state only | selector: `Rate/Loss Cost Applies` / `Industry` / `Company`; 433 rows across 51 jurisdictions (`GATE-335` § 5, § 7) |
| `ILFOwnersContractors` | state, occurrence limit, aggregate limit | state only, 0 rows CW | limit strings `"1,000,000"` / `"2,000,000"`, not the `...CSL` vocabulary used elsewhere (`GATE-335` § 4, § 5) |
| `PrincipalsProtvLiabFactor` | `"CW","Y"` | countrywide only, 1 row | value `0.75`; feeds class `15191` ELP; pre-2027 only (`GATE-335` § 5) |
| `PremOpsMinPremium` | — | countrywide only, 3 rows | reused from subline 334; pre-2027 only (`GATE-335` § 5) |
| `LookupPrincipalsProtvLiabFactor` | — | — | dead in CW 2027 — no caller after `SetPrincipalsProtvLiabFactor` was deleted (`GATE-335` § 1) |

State deviations (`GATE-335` § 6, via `scripts/erc/29_census_336.py --rules
GeneralLiabilityClassificationOwnersContractorsCoverageRules`): **49 of 51 jurisdictions are pure
countrywide** across all 562 packages in the corpus. The only two overriding rules:

| Rule | Jurisdictions | Effect |
|---|---|---|
| `SetILF` | NY | own increased-limits treatment |
| `SetMoldStatCode` | AK, NY | statistical coding only, no premium effect |

---

## Quick reference — end-to-end, CW 2023 standard class

```
LossCost   = lookup OwnersContractorsLossCost(state, class)         # 0 unless one of 8 jurisdictions
ELP        = 0.0                                     if class code blank
           | PrincipalsProtvLiabFactor x WorkersCompensationRate    if class = 15191
           | lookup OwnersContractorsELP(state, class)              otherwise

BaseRate   = round(LossCost x LCM, 3)    if LossCost <> 0
           | round(ELP x LCM, 3)         if LossCost = 0

ILF        = lookup ILFOwnersContractors(state, occLimit, aggLimit)

FinalRate  = round(BaseRate x ILF x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse, 3)
                            (same for the OverOneMillion band, from its own tables)

Premium    = round(FinalRate x min(Exposure, 1000000) / 1000
                  + FinalRateOverOneMillion x max(0, Exposure - 1000000) / 1000, 0)

MinPremium = round(PremOpsMinPremium x ILF, 0)     # applied when Subline = "Owners and Contractors"
Premium    = max(Premium, MinPremium)              # best-supported reading — see note above
```

## Quick reference — end-to-end, CW 2023 class 15191 (Workers-Compensation-derived)

```
ELP        = PrincipalsProtvLiabFactor x WorkersCompensationRate    # 0.75 x submitted WC rate
BaseRate   = round(ELP x LCM, 3)          # LossCost is 0 for class 15191 — no published rate
FinalRate  = round(BaseRate x ILF x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse, 3)
Premium    = round(FinalRate x min(Exposure, 1000000) / 1000
                  + FinalRateOverOneMillion x max(0, Exposure - 1000000) / 1000, 0)

# Worked example (AR, GATE-335 § 8 — derived, not confirmed against ISO arithmetic):
#   ELP       = 0.75 x 1000.0 = 750.000
#   BaseRate  = round(750.0 x 1.0, 3) = 750.000        (LCM = 1.0)
#   FinalRate = round(750.0 x 1.75, 3) = 1312.500       (ILF = 1.75)
#   Premium   = round(1312.5 x 10, 0) = 13,125          (exposure 10,000, /1000)
```

## Quick reference — end-to-end, CW 2023 legacy classes 27111 / 27112

```
BaseRate   = round(LossCost x LCM, 3)  |  round(ELP x LCM, 3)
FinalRate  = round(BaseRate x ILF x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse, 3)
             (and identically for the OverOneHundred band)

Premium    = round(FinalRate x min(Units, 100)
                  + FinalRateOverOneHundred x max(0, Units - 100), 0)
             # breakpoint is 100 units, not $1,000,000; no /1000 divisor — see Branch B note above
```

## Quick reference — end-to-end, CW 2027 and later

```
ELP        = 0.0                                     if class code blank
           | lookup OwnersContractorsELP(state, class)   otherwise
                                          (no class-15191 WC branch — class retired)

BaseRate   = round(ELP x LCM, 3)          # loss-cost path deleted; never non-zero in this edition

ILF        = lookup ILFOwnersContractors(state, occLimit, aggLimit)

FinalRate  = round(BaseRate x ILF x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse, 3)
                            (and identically for the OverOneMillion band)

Premium    = round(FinalRate x min(Exposure, 1000000) / 1000
                  + FinalRateOverOneMillion x max(0, Exposure - 1000000) / 1000, 0)

             # no minimum-premium step in this edition
```

All intermediate rate products (`BaseRate`, `FinalRate`, and their bands) carry 3 decimal places;
the `Premium` and `MinPremium` products carry 0. Rounding direction (`HALF_UP` vs `HALF_EVEN`) is
an open question raised in `GATE-335` § 3 (Escalation E1) — a real AR submission hits an exact
3-decimal-place midpoint (`0.95 x 1.75 = 1.6625`), and the two rounding conventions diverge at the
third decimal place even though they happened to produce the same premium at that exposure.

---
