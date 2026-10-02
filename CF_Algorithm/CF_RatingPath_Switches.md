# Which selections change the rating path — core coverages

**Written 2026-09-16.** Source: a mechanical scan of every path-selecting rule
(`SetPremium`, `SetCoverageOnPolicyIndicator`, `Set*RatesAndFactors`, `Set*BaseRate`, `Set*Rate`,
`Set*CauseOfLossAdjustment`, `SetFactor`, `Set*ExclFactor`, `Set*ToUse`) in the core rule files for
Building, Contents, Business Income, Special Class and Special Class Business Income — CW 20260601 V01.
Every value below was read out of a `<rul:Test>`; nothing is inferred from a field name.

Companion HTML: `CF_RatingPath_Switches.html`.

> **Reconciled against the built engine on 2026-10-02** (commit `630ba2f`; chunks 1–27 gated).
> Confirmed against each chunk's gate file and ISO-checked golden cases (`docs/CF-CHUNKnn-GATE.md`), the
> rule XML re-read where a claim moved, and the three regressions (`104_ --quick`, `206_ --check`,
> `157_ --all`). Three claims were wrong and are corrected in place (marked *Corrected 2026-10-02*); build
> evidence is marked *Build*. The section "Every path, and where the build stands" lists every path and
> the chunk that built it.

---

## The three kinds of switch

| Kind | What it is | Example |
|---|---|---|
| **Enum value** | a coded field on a record, chosen from a domain list | `CovType = "Legal Liability"` |
| **Election** | an endorsement record exists or doesn't — a Yes/No, not a value | `CommercialPropertyTheftExclusion` |
| **Inherited value** | copied down from a parent record; not selectable on the item itself | Contents' `CovForm`, copied from the occupancy class |

The third kind is the one that bites. A field can be *tested* on the item and still not be *chosen* there.

---

## Master list — every enum tested in a path rule

Ordered by how many distinct values the rules actually test.

| Field | Values tested | Coverages | What it switches |
|---|---|---|---|
| `CovType` | 10 | Bldg, Contents, BI, SCBI | **Different value universe per coverage** — see below |
| `CauseOfLossToUse` | 10 | all five | which form chain rates at all |
| `ClassCodeToUse` | 7 | Bldg, BI | special-cased class codes |
| `TypeOfRisk` | 6 | BI, SCBI | which arm of `TypeOfRiskFactor` |
| `RatingType` | 3 (CA: 4) | Bldg (Contents, OccupClass copy it) | Class / Specific / Tentative; CA adds One-Term Loss Cost |
| `CovForm` | 3 | Contents | the Contents premium branch |
| `PolicyType` | 2 | all five | CPP vs SPP — cascades into three other lists |
| `IncludedInBlkt` | 2 | all five | scheduled vs blanket premium |
| `MUBlktRated` | 2 | all five | multi-unit blanket rating |
| `CoinsuranceToUse` | 2 | BI, SCBI | suppresses `TypeOfRiskFactor` |
| `EQCovIndicator` | 2 | Bldg, Contents, SC, SCBI | whether the EQ chain runs |
| `CauseOfLoss` / `BlktCauseOfLossValue` | 2 | Bldg, Contents | the blanket-vs-item source of cause of loss |
| `BlktTypeOfBlanketRating` | 2 | Bldg | blanket rating method |
| `MultiLocAvgRatesIndicator` | 2 | Contents | multi-location averaging |
| `MaxPeriod` | `"Yes"` | BI, SCBI | first arm of `SetFactor` |
| `MonthlyLimitOfIndemnity` | `<> "Not Applicable"` | BI, SCBI | second arm of `SetFactor` |
| `VacantBuilding` | `"Yes"` | Bldg, Contents, BI | substitutes class code `1180` |
| `SprinklerSystem` | 1 | Bldg, Contents, BI | sprinkler-leakage terms |
| `OpenSides`, `Group`, `BldgClassCode`, `YardPropertyIndicator` | 1 each | varies | classification side-paths |
| `SubStdConditionA–E` | 1 each | Bldg | substandard condition rate |
| `SuperiorRoofingIndicator`, `EQSprinklerLeakageOnly`, `EQCauseOfLossForm`, `FloodCovIndicator` | 1 each | Bldg / Contents | narrow side-paths |
| `PostTRIAExclusion`, `BldgIncludedInOperationalUnit`, `IncludedInBuilding`, `Applicability` | 1 each | varies | terrorism / grouping |

---

## The big five, in detail

### 1. `PolicyType` — Commercial Property Policy vs Standard Property Policy

The widest-reaching switch in the line. Tested in all five coverages, and it **cascades**:

- **The cause-of-loss list changes.** CPP offers Basic / Broad / Special (+ blanket). SPP offers a set of
  fire combinations instead.
- **The `CovForm` list changes.** `DomainCovForm` is keyed State + PolicyType + RatingType. Legal Liability
  is offered on **CPP only** — it is absent from every SPP row.
- **`StdPropPolGroupIFactor` / `StdPropPolGroupIIFactor` apply** only on an SPP — on the **building,
  contents and Special Class** (0.98 each, in the rate chain, not on the premium). *Corrected 2026-10-02:*
  this said "only on the building side"; the CW rule files for Structure, PersonalProperty and SpecialClass
  each set both factors (chunk 14, gate point 6). **KS, NY and VT file no SPP factor**, so an SPP there
  prices like a CPP (chunk 14).
- **Vandalism's gate flips shape.** On a CPP it fires on an endorsement election; on an SPP it fires on a
  qualifying cause of loss instead, ignoring the endorsement entirely.

### 2. `RatingType` — Class / Specific / Tentative

Three values, tested on Building, Contents and Business Income. Selects an entirely different base-rate
source: a class-code lookup versus a user-supplied specific or tentative rate.

**Confirmed absent on Special Class and Special Class Business Income** — `RatingType`,
`SpecificGroupIRate` and `TentativeRate` appear zero times in either ruleset (chunk 26: a `RatingType` sent
on a Special Class item is ignored). In the countrywide rules **only Basic Group I** has a
Specific/Tentative path; Broad and Special are class-only everywhere.

*Corrected 2026-10-02 — Group II is not class-only in the states.* **36 states** carry
`RatingTypeBasicGroupII`; "Specific" prices Group II from a submitted `SpecificGroupIIRate`
(blank → Group II $0 on building, contents and BI, silently). *Build, chunk 26 (gated 2026-10-02, ISO
agreed on every premium):*

- **`RatingType` is chosen on the building only.** The occupancy class and the contents **copy** it (an
  inherited value: a submitted copy is overwritten).
- **Contents price on their OWN `SpecificGroupIRate`**; with none they rate $0. **BI uses the building's.**
- Specific / Tentative replace the whole class chain (base rate, territory, protection class drop out):
  building Group I **$362** where Class gives **$287**. Tentative prices exactly as Specific and attaches
  the Tentative Rate form; no rule reads a `TentativeRate` field.
- **A blank `RatingType` prices at rate 1.0** ($1,204), at ISO too. FL, NY, WV and MO leave the roof ACV
  factor out of the Specific formula.
- **California's One-Term Loss Cost** prices building and contents as Specific; BI falls to rate 1.0 —
  ISO does the same (OI-124).

### 3. `CovType` — the same field name, four different value universes

This is the trap worth the most care. `CovType` is tested in four coverages and the legal values do not
overlap.

| Coverage | Values tested in path rules |
|---|---|
| **Building** | `Building`, `Builders Risk`, `Improvements and Betterments`, `Condominium Association`, **`Legal Liability`**, **`Leasehold Interest`** |
| **Contents** | `Valuable Papers and Records - Other Than Electronic Data` |
| **Business Income** | `Business Income Without Extra Expense`, `Extra Expense Only`, `Not Applicable` |
| **SC Business Income** | same three as Business Income |

`CovType` is declared on `Structure`, `OccupClass` **and** `PersonalProperty`, and **no rule assigns it** on
any of them — it is a submission input, entered per record. So two buildings at one location can differ.

### 4. `CovForm` — the Contents switch, chosen one level up

Contents does not branch on `CovType`. It branches on `CovForm`, and `SetCovForm` is a plain
`Copy ../../CovForm` — which resolves to **`CommercialPropertyOccupClass`**. The choice is made once per
occupancy class and every contents item inherits it.

Three values are tested, all as exclusions from the class-rated branch:

| Value | Effect |
|---|---|
| `Legal Liability Coverage Form` | its own premium branch |
| `Tobacco Sales Warehouse Coverage Form` | excluded from the class-rated branch; rates on its own path |
| `Class Rated Building Only, No Personal Property Coverage` | excluded — there is no contents premium |

### 5. `CauseOfLossToUse` — which form chains fire

Ten values tested. On a CPP: `Broad`, `Special` (and Basic implicitly). On an SPP: the fire combinations —
`Fire`, `Fire and Allied Lines`, `Fire and Vandalism`, `Fire and Sprinkler Leakage`,
`Fire, Vandalism and Allied Lines`, `Fire, Sprinkler Leakage and Allied Lines`,
`Fire, Vandalism and Sprinkler Leakage`, plus `Not Applicable`.

Basic Group I and II rate regardless; Broad and Special each rate only when the cause of loss names them.
The value itself comes from `BlktCauseOfLossValue` when the item is blanketed, and the item's own
`CauseOfLoss` when it is not — so `IncludedInBlkt` silently changes where this value is read from.

---

## Elections — 49 endorsement records tested in path rules

An election is not an enum. The rule asks whether a record **exists**, so a blank is not a neutral value.

The four core exclusions each file **a separate record per coverage** — the pattern behind backlog items
S-1, S-2 and S-3:

| Exclusion | Building | Contents | Business Income | Special Class | SC Business Income |
|---|---|---|---|---|---|
| Theft | `TheftExclusion` | `TheftExclusionPrsnlProp` | `TheftExclusionBusnIncome` | `TheftExclusionSpecialClass` | `TheftExclusionSpclClassBusnIncome` |
| Vandalism | `VandalismExclusion` | `VandalismExclusionPrsnlProp` | `VandalismExclusionBusnIncome` | `VandalismExclusionSpecialClass` | `VandalismExclusionSpclClassBusnIncome` |
| Windstorm/Hail | `WindstormOrHailExclusion` | `…PrsnlProp` | `…BusnIncome` | `…SpecialClass` | `…SpclClassBusnIncome` |
| Sprinkler Leakage | `SprinklerLeakageExclusion` | `…PrsnlProp` | `…BusnIncome` | — | — |

Others that steer a core path: `BuildersRiskReportingForm` (Building — zeroes the ordinary premium),
`ValueReportingForm` and `AdditionalLocationsSpecialCoinsuranceProvisions` (Contents — suppress the
coverage-on-policy indicator), `LimitationsOnCovForRoofSurfacing` (Building), `AlcoholicBeveragesTaxExclusion`
(Contents), the eight Earthquake endorsement variants, and eleven terrorism records.

---

## Worked example — how `Legal Liability` produces a different path

The selection is one enum value. What follows from it is a different premium formula, two factors that exist
nowhere else, and three things that silently stop applying.

```
SELECT               Building : CovType  = "Legal Liability"        (on the building item)
                     Contents : CovForm  = "Legal Liability Coverage Form"
                                           (on the OCCUPANCY CLASS - all contents inherit it)

RATE CHAIN           unchanged. Base rate, territory, protection class and the
                     cause-of-loss adjustment all run exactly as class-rated.

THE FORK             a Choose branch inside SetPremium - not in the rate chain.

                     class-rated : premium starts from FinalBasicGroupIRate
                     legal liab. : premium starts from BasicGroupICauseOfLossAdjustment
                                   ^ three steps earlier

WHAT STOPS APPLYING  coinsurance, the LOI factor, the deductible factors
                     (all computed upstream, then ignored)
                     MultiPremiumAndDispersionCreditFactor

WHAT STARTS APPLYING LegalLiabilityFactor          Bldg 0.25 / PersProp 0.50
                     AddlInsurableInterestFactor   Option1 1.25 · Option2 1.25
                                                   Option3 1.00 · Option4 ("None") 1.00

ALSO CHANGES         blanket: electing it ZEROES the coverage ($0 at the engine
                     and at ISO - chunk 8 gate; corrected 2026-10-02 from
                     "becomes unreachable")

PER FORM             BGI  -> BasicGroupICauseOfLossAdjustment
                     BGII -> BasicGroupIICauseOfLossAdjustment
                     Broad-> BroadRate                     (raw; no COL adjustment exists)
                     Spec -> Building: SpecialRate                 (drops the theft credit)
                             Contents: SpecialCauseOfLossAdjustment (keeps it)
```

That last line is the only premium-bearing Building/Contents difference other than the 0.25 / 0.50 factor.

*Build, chunk 8 (gate 9 of 9 after chunk 27).* Golden case Building **$60 / $7 / $4 / $12**, Contents
**$132 / $15 / $11 / $93** (BGI / BGII / Broad / Special), all ISO-confirmed — Contents only once the
**building** carries `WindstormOrHailDeductible` (ISO refuses without it; ours prices: OI-103, chunk 28).
The Special-form split moves money: theft excluded, Contents falls $93 → $37 while Building stays $12.
`LegalLiabilityFactor`'s key is pinned by literal, so each coverage can reach only its own row.
**California needs the location's `District`** (District I $57, II $68); without it Group I is $0 (chunk 27).

---

## Which drivers apply where

| Driver | Building | Contents | Business Income | Special Class | SC Business Income |
|---|---|---|---|---|---|
| `PolicyType` | yes | yes | yes | yes | yes |
| `IncludedInBlkt` | yes | yes | yes | yes | yes |
| `CauseOfLossToUse` | yes | yes | yes | yes | yes |
| `RatingType` | yes | yes | yes | **absent** | **absent** |
| `CovType` | yes | narrow | yes (own values) | — | yes (own values) |
| `CovForm` | — | **yes** | — | — | — |
| Legal Liability | yes | yes | **absent** | **absent** | **absent** |
| `TypeOfRisk` / `MaxPeriod` / `MonthlyLimit` | — | — | yes | — | yes |
| `VacantBuilding` | yes | yes | yes | — | — |
| `SubStdConditionA–E` | yes | — | — | — | — |

---

## Every path, and where the build stands (2026-10-02)

Every path above is built in the engine and its premiums are ISO-confirmed in all 46 states (Puerto
Rico excluded). **546 of 546 countrywide premium files built.**

| Path / switch | Built in | Gate evidence (ISO) |
|---|---|---|
| Basic Group I / Group II (`CauseOfLossToUse` set at all) | chunks 1, 2 | $261 / $32 golden; TX × 0.1 when wind/hail excluded; NY's Group II symbol is a **submitted input** (chunk 27) |
| Broad / Special — cumulative on top of Basic | chunk 3 | $16 / $54 → $309 / $347 |
| Contents (`CovForm` from the occupancy) | chunk 4 | $223 / $24 / $16 / $137 |
| Business Income (`TypeOfRisk`, `MaxPeriod`, `MonthlyLimitOfIndemnity`) | chunk 5 | $112 / $13 / $23 / $47 |
| Special Class, SC Business Income | chunks 6, 7 | $66 / $209 / $14 / $44; $39 / $123 / $23 / $47 |
| Legal Liability (`CovType` / `CovForm`) | chunk 8 | above |
| Blanket (`IncludedInBlkt`; `BlktTypeOfBlanketRating` Average vs Highest, both live) | chunk 9 | $255 / $510 |
| Earthquake (`EQCovIndicator`, the EQ endorsement variants) | chunk 10 | $6 golden |
| `CovType = Leasehold Interest` | chunk 11 | 9 of 9 |
| Endorsement families (Debris, O&L, Utility, UAS, Green, Dependent Properties) | chunk 12 | 9 of 9 |
| Terrorism (`PostTRIAExclusion` and the TRIA records) | chunk 13 | $8 golden; 587 of 587 |
| `PolicyType` SPP, IRPM, package mod, the policy total | chunk 14 | 293 of 293 totals |
| Manual-premium endorsements, BI options, BI add-ons | chunks 15–17 | 9 of 9 each |
| Agreed Value, Inflation Guard, Vacancy Permit, Peak Season | chunk 18 | 9 of 9 |
| Scheduled items, small coverages (incl. Tobacco Sales Warehouse), sewer / condo options | chunks 19–21 | 9 of 9 each |
| `ValueReportingForm`, `AdditionalLocationsSpecialCoinsuranceProvisions`, `MultiLocAvgRatesIndicator` | chunk 22 | 9 of 9; either form switches the ordinary contents premium off |
| State-only coverages (MA, AK, CA, VA) | chunk 23 | 9 of 9 |
| `CovType = Builders Risk`, `BuildersRiskReportingForm` | chunk 24 | 9 of 9; with a reporting form the building's own limit must be 0 |
| Flood (`FloodCovIndicator` + the Flood General Information record) | chunk 25 | 9 of 9 |
| `RatingType` Specific / Tentative, `RatingTypeBasicGroupII` | chunk 26 | 9 of 9 |

**Still open — chunk 28 (engine behaviour decisions; none built, each needs the user's go):**

- **Refuse where ISO refuses (set A).** ISO refuses a request when a `SingleResult` lookup finds no row (65
  of 66 live refusals: an unfiled territory or class, a blank key such as the building's
  `WindstormOrHailDeductible`, FL's Group II territory, NY's `CompletedBasicGroupIISymbol`); **ours prices
  them, often at $0** (OI-99, OI-103, OI-117).
- **Silent zero-price inputs (set B).** A blank `Deductible` on Broad / Special, no BCEG, no
  `RatingTypeBasicGroupII`, no Group II territory, an unknown `ConstructionType`, AZ's reduction credit: each
  prices $0 rather than raising — mostly at ISO too, so this is a validation layer, not a rating change.
- **Minimum premium (set E).** ISO rates none; a minimum is a company input with a refer-to-company
  outcome (OI-113).

## What this means for the input sheet

1. **`CovType` needs a different dropdown per coverage.** One shared list is wrong — the four value
   universes do not overlap.
2. **Contents' form selector belongs at the occupancy class**, not on the contents item. One dropdown drives
   every contents item beneath it.
3. **`PolicyType` has to be set before anything else is selectable** — it changes the cause-of-loss list,
   the `CovForm` list, and whether the Std Prop Pol factors exist.
4. **Elections are Yes/No records, not enum values.** A blank is not neutral: the missing-record default is
   `0.0` in several places, which zeroes a premium rather than declining a credit.
5. **Each coverage needs its own election column** for theft, vandalism, wind/hail and sprinkler leakage.
   Sharing one input across coverages is the S-1/S-2/S-3 simplification, and it is logged as such.
6. **`RatingType` is a building input only** (added 2026-10-02, chunk 26): the occupancy and contents copy
   it. Contents still need their own `SpecificGroupIRate` when the building is Specific.
7. **Some switches only work with a companion input** (added 2026-10-02): CA Legal Liability needs the
   location's `District`; Contents at ISO need the building's `WindstormOrHailDeductible`; NY needs a
   submitted Group II symbol; Flood needs its General Information record. Without them the engine
   prices (often $0) where ISO refuses or also prices $0.

---

*Scanned mechanically, then each headline claim re-read in the rule XML. Counts are of values actually
tested in a path rule, not of values a domain table offers — a domain may list options no rule branches on.*
