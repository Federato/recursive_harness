# Railroad Protective Liability — Rating Algorithms

**Source:** `docs/gates/GATE-335-RAILROAD-PROTECTIVE.md` (filed 2026-08-11, as-of date 2026-08-11),
cross-referenced against `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.1 row 6 / §3.1.1 /
§3.2.5, `docs/erc/03-RATING-STRUCTURE.md` §2.1/§2.4, and `docs/rating-engine/A3-ENDORSEMENT-CATALOG.md`
"Rule 49 — Railroad Protective (335)".

**Line:** General Liability (GL), subline code **335** — shared with Owners & Contractors
Protective (OCP; see `GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`). ISO manual rule: **Rule 49**,
`GL-MU-2027-RU-001-C.pdf` p.124–127 (CW 2027 edition); Rule 49 in the CW 2023/2026 edition
(`GL_CW_20231201_V03`) carries the algorithm this document primarily describes.

**Derived against:** `GL_CW_20231201_V03`, the parent the OK golden case declares.

**Documented:** 2026-08-20.

Railroad Protective Liability (coverage form `CG 00 35`) rates **four classes**, all on a
**Total Cost per $1,000** exposure base (Rule 24.F). It is the same subline code as OCP, but a
different rule (49, not 46) and a different rate table family — "two coverages, two rules, one
statistical subline" (gate doc §0 naming note). Unlike OCP, Railroad has **no published loss
cost in any jurisdiction (0/51)**; it rates entirely off the ELP (Estimated Loss Potential)
supplement, and Rule 49.E.1 itself says "Refer to company" for basic-limits rates — the actual
procedure lives in the ELP Supplement, Procedure 5.E (`GL-AK-2020-LC-001-C.pdf` pp.10–11), not
in the rules manual.

This document covers the CW 2023/2026 algorithm (65 rules) and flags the CW 2027 rewrite
(46 rules) at each point where it diverges.

---

## Master orchestration

Per gate doc §2:

```
ErcProcess:
    if CoverageOnPolicyIndicator == 0:
        Premium = 0.0
        stop
    else:
        ErcSetRatesAndFactors
        ErcRate
        ErcSetStatisticalCodes
```

`ErcSetRatesAndFactors` runs a 26-step chain (numbered #1–26 below) that forks repeatedly by
class code (`40011`, `40012`, `40013`, `40014`) — "the chain forks by class more heavily than
any subline so far" (gate doc §2). There is no single linear "rate build-up then premium" split
the way CF's cause-of-loss forms have; instead, rate build-up and premium computation are
interleaved in one ordered rule list. This document splits the list at the point the gate doc
itself splits it (rules #1–22 build the rate; #23–26 build the premium) for presentation, but the
underlying ERC chain is one sequence.

---

## File map

*Not resolved in source docs* — the gate doc does not cite specific ERC rule-file names or line
numbers for Railroad's rules (unlike the CF template's XML line citations). It gives rule names
and a class/table cross-reference only. Where the gate doc gives a citation, it is a rule name,
a manual page/paragraph, or a table name — reused verbatim in the sections below. No plausible
line numbers are invented here.

| Piece | Source |
|---|---|
| Rate/premium chain, all 26 rules | `GATE-335-RAILROAD-PROTECTIVE.md` §2 (rule list) |
| Manual rule (rating is "refer to company" in-manual) | Rule 49, pp.124–127; `E.1 Basic Limits: "Refer to company."`; `E.2 Increased Limits: "Refer to Rule 56."`; `F. Basis Of Premium: Total Cost.` |
| Actual rating procedure | ELP Supplement Procedure 5.E, `GL-AK-2020-LC-001-C.pdf` pp.10–11 (gate doc §4) |
| Coverage form | `CG 00 35` — Railroad Protective Liability Coverage Form (`A3-ENDORSEMENT-CATALOG.md` "Rule 49") |
| Mandatory multistate endorsement | `IL 00 21` — Nuclear Energy Liability Exclusion Endorsement Broad Form |
| Optional refer-to-company endorsements | `CG 24 01`, `CG 24 02`, `CG 24 04`, `CG 24 14`, `CG 24 53`, `CG 33 71`, `CG 34 21`, `CG 34 22`, `CG 34 31`, `CG 34 48`, `CG 34 49`, `CG 34 96` — all `OPTIONAL_RTC`, Rule 49 §D |
| Contractual liability endorsements (general, not railroad-specific) | `CG 24 17`, `CG 24 27` — Contractual Liability Railroads Endorsement / Limited variant |
| Dedicated state ILF table | Rule 56.B.7, present in all 51 jurisdictions (`03-SUBLINE-COVERAGE-PLAN.md` §3.2.5) |

---

## Railroad Protective — rate build-up

Executed in order (gate doc §2, table rows #1–22 of 26):

```
#1  SetConstructionOpsOwnerFactor
#2  SetLCM
#3  SetConstructionOpsOwnerAdjmtFactor
#4  SetEstimatedContractCostRatio                    (class 40013 only)
#5  SetILF / SetILF40014                             (40014 gets its own ILF)
#6  SetCovForInjuriesToSuprvsrFactor
#7  SetTotalCostWorkTrainsOrOtherRREquipmtAssigned
#8  SetTotalCostWorkTrainsOrOtherRREquipmtBaseRate
#9  SetTotalCostWorkTrainsOrOtherRREquipmtRate
#10 SetTotalCostWorkTrainsOrOtherRREquipmtFinalRate
#11 SetInjurySuprvsrInspOthrEmpCovConstrOpsRROps      (classes 40011, 40012, 40014)
#12 SetBaseELPRR                                      (excludes 40014)
#13 SetBaseELPRR400145orLess                          (mixed-hazard path)
#14 SetBaseELPRR40011                                 (classes 40011/40012)
#15 SetContractCostFactorWOHzd
#16 SetContractCostFactorWithHzd
#17 SetAdjustedBaseELPRR                              (all four classes)
#18 SetBaseELPRR40014                                 (mixed-hazard continuation)
#19 SetPriorToFinalRateMixedHazard
#20 SetPriorToFinalRate40014
#21 SetFinalRate
#22 SetFinalRate40011
```

### Step 1 — Construction Operations/Owner factor
`SetConstructionOpsOwnerFactor` (gate doc §2, #1)

```
ConstructionOpsOwnerFactor = LookupOwnersContractorsLossCost(classCode = "16292")
```

`16292` is **hardcoded in the rule** — it does not vary by the risk's own class code. This reads
**OCP's** loss-cost table, not a Railroad-specific one (gate doc §3). Confirmed against the
manual: Procedure 5.E.1.a states the Basic Limit ELP per $1,000 of Total Cost is *"150% of the
loss cost for Class Code 16292 Construction Operations – Owner"* (gate doc §4) — exact match
including the class code.

### Step 2 — Loss Cost Multiplier
`SetLCM` (gate doc §2, #2)

```
LCM = LookupRailroadLCM
```

Countrywide, **one row, value `1`** — an unsupplied company multiplier (gate doc §5, "E15").

### Step 3 — Construction Operations/Owner adjustment factor
`SetConstructionOpsOwnerAdjmtFactor` (gate doc §2, #3)

Countrywide, one row, value **`1.5`**. Matches Procedure 5.E.1.a's *"150%"* (gate doc §4).

### Step 4 — Estimated contract cost ratio (class 40013 only)
`SetEstimatedContractCostRatio` (gate doc §2, #4)

The ratio of at-hazard contract cost to total contract cost, for class `40013` (state/federal
highway projects). Per Procedure 5.E.2.b: *"applying to the ELP the ratio of the estimated
contract cost of the operations performed on, over or under the insured railroad's property or
within 50 feet … to the total contract cost"* (gate doc §4) — confirmed exact.

### Step 5 — Increased Limits Factor
`SetILF` / `SetILF40014` (gate doc §2, #5)

```
ILF = LookupILFRailroad(...)
```

Class `40014` gets its own ILF rule (`SetILF40014` → `ILF40014`), consistent end-to-end with the
class it names (gate doc §2, naming-trap table). Table: `ILFRailroad`, Rule 56.B.7, 0 rows
countrywide / 51 jurisdictions · 1,836 rows (gate doc §5).

### Step 6 — Supervisors/inspectors coverage factor
`SetCovForInjuriesToSuprvsrFactor` (gate doc §2, #6)

Countrywide, one row, value **`0.1`**. Matches Procedure 5.E.1.a / 5.E.3.c: *"charge an
additional premium of 10%"* for supervisors, inspectors and other employees at the job site
(gate doc §4) — exact match.

### Steps 7–10 — Work-trains charge
`SetTotalCostWorkTrainsOrOtherRREquipmtAssigned` → `…BaseRate` → `…Rate` → `…FinalRate`
(gate doc §2, #7–10)

```
WorkTrainsOrOtherRREquipmtRate = 56.8      # per $1,000 of Total Cost, countrywide, 1 row
```

Matches Procedure 5.E.2.c: *"The $100,000/300,000 Basic Limit ELP per $1,000 of Total Cost is
$56.80"* (gate doc §4) — exact match, and a rare case of a **countrywide dollar rate**
(gate doc §5) rather than a factor — README finding #1 ("no national loss cost publication at
all") is qualified by this rate (gate doc §9).

### Step 11 — Supervisors/inspectors extension
`SetInjurySuprvsrInspOthrEmpCovConstrOpsRROps` (gate doc §2, #11)

Applies to classes `40011`, `40012`, `40014`.

### Step 12 — Base ELP for Railroad (banded)
`SetBaseELPRR` (gate doc §2, #12)

```
BaseELPRR = LookupBaseELPRR(State, ClassCode, NumPassgrFreightTrains)
```

Keyed on **(State, ClassCode, Number of Passenger and Freight Trains Per Day)**, banded into six
train-count tiers. **Excludes class `40014`** — 40014 is derived (150% × OCP class `16292`),
never tabulated (gate doc §4, "18-cell test" note). Matches manual Tables 5.E.2.a, 5.E.3.a,
5.E.3.b: *"Number Of Passenger And Freight Trains Per Day"*, six bands (gate doc §4) — exact
match including the banding.

**Table has exactly 18 rows in every one of the 51 jurisdictions** (3 classes × 6 bands),
**0 rows countrywide** (gate doc §0, §5, §6) — perfectly uniform, and the smallest state-deviation
surface of any subline gated to date.

### Step 13 — Mixed-hazard base (naming trap #1)
`SetBaseELPRR400145orLess` (gate doc §2, #13)

For a **class `40011`** risk with `EstdContractCostWORRHzd > 0` (a project only partly clear of
the tracks), the no-hazard portion is rated on the class-`40014` basis:

```
BaseELPRR400065orLess = round(ConstructionOpsOwnerFactor x ConstructionOpsOwnerAdjmtFactor, 3)
                       = round(OCP loss cost for class 16292 x 1.5, 3)
```

**Naming trap:** despite the rule name containing `400145`, this rule **tests class `40011`**
and **writes to DataDef `BaseELPRR400065orLess`** — neither number in the rule name or DataDef
name is the class being tested. Per gate doc §2: "the rule names refer to the rate basis being
applied, not the risk's class." This is documented as **N11 at its purest** — the printed number
is unreliable in both rule names and DataDef names; only `SetILF40014` → `ILF40014` is
consistent end to end.

### Step 14 — Base ELP, classes 40011/40012
`SetBaseELPRR40011` (gate doc §2, #14)

Applies to classes `40011` and `40012`.

### Steps 15–16 — Mixed-hazard contract cost factors
`SetContractCostFactorWOHzd` / `SetContractCostFactorWithHzd` (gate doc §2, #15–16)

The two halves of a mixed-hazard project: the without-hazard portion and the with-hazard
portion. Per Procedure 5.E.4, *Special Rating Procedure*, for projects *"part of which are
subject to an actual railroad train hazard and part of which are not"* → *"weighted average"*
(gate doc §4) — exact match.

### Step 17 — Adjusted Base ELP
`SetAdjustedBaseELPRR` (gate doc §2, #17)

Applies to all four classes.

### Step 18 — Mixed-hazard continuation (naming trap #2)
`SetBaseELPRR40014` (gate doc §2, #18)

**Naming trap, continued:** despite the name containing `40014`, this rule **tests class
`40011`** and writes DataDef `BaseELPRR40006`. `40006` is *"Miscellaneous"* in
`ClassificationType.RateTable.csv` — an unrelated classification (gate doc §2). An engine that
maps `BaseELPRR40006` to class `40006` would produce nonsense; it is a mixed-hazard-path
DataDef name, not an identity.

### Steps 19–20 — Weighted average
`SetPriorToFinalRateMixedHazard` / `SetPriorToFinalRate40014` (gate doc §2, #19–20)

`SetPriorToFinalRate40014` also tests class `40011` and writes `PriorToFinalRate40006` — same
naming-trap pattern as step 18.

### Steps 21–22 — Final rate
`SetFinalRate` / `SetFinalRate40011` (gate doc §2, #21–22)

`SetFinalRate40011` tests class `40012` and writes `FinalRate40011` — a third instance of the
naming trap (rule name references `40011`, tested class is `40012`).

---

## Railroad Protective — premium

### Gate
`ErcProcess` (gate doc §2): `CoverageOnPolicyIndicator == 0` → `Premium = 0.0`, stop. Otherwise
the 26-step chain above runs, then:

```
#23 SetTotPremiumPriorToInjuryToSuprvsrCovPremium     (class 40011)
#24 SetCovForInjuriesToSuprvsrInspOtherEmpOfTheInsdPremium
#25 SetWorkTrainsOrOtherRREquipmtPremium
#26 SetMinimumPremium / SetMinPremium
    SetPremium
```

```
Premium = FinalRate x TotalCost / 1000
```

Confirmed against Rule 49.G: *"Total Cost — per $1,000 of total cost"*, applied to all four
classes (gate doc §4) — confirms the ÷1000.

### Branch — classes 40011 / 40012 (no hazard split)
Standard path: `FinalRate` (or `FinalRate40011` for `40012`) feeds `Premium` directly, plus the
supervisors/inspectors premium add-on (step 24, classes `40011`/`40012`/`40014` only) and the
work-trains premium add-on (step 25).

### Branch — class 40011, mixed hazard
When `EstdContractCostWORRHzd > 0`: the no-hazard portion routes through the class-`40014` basis
(step 13/18), the hazard portion through the class-`40011`/`40012` basis, and steps 15–16/19
compute the weighted average that becomes `PriorToFinalRateMixedHazard`.

### Branch — class 40013
Uses `SetEstimatedContractCostRatio` (step 4) applied to the ELP; no mixed-hazard split (that
mechanic is 40011-only per the gate doc's rule list).

### Branch — class 40014
Derived, not tabulated: `BaseELPRR40014` (mixed-hazard machinery aside) = 150% of OCP class
`16292`'s loss cost, per its own `SetILF40014`.

### Minimum premium
`SetMinimumPremium` / `SetMinPremium` reads `MinPremiumRR` — countrywide, **one row, value `0`**
(gate doc §5) — a structurally-zero minimum premium (gate doc §5, "E16").

### Refer-to-company triggers (not gated in ERC)
Per gate doc §7:

| # | Trigger | ERC discriminator |
|---|---|---|
| 1 | All basic-limits rates (Rule 49.E.1) | None — manual-only |
| 2 | Operations other than construction (Procedure 5.E.1.b, 5.E.3.d) | **None** — ERC rates whatever class code is submitted (recorded as **OI-45**, "known unguarded referral") |
| 3 | `LCM == 1` (unsupplied company multiplier) | None |
| 4 | Class code outside `40011`–`40014` | Falls through every branch → `FinalRate = 0` (silent zero) |
| 5 | `RailroadClassCode` / `RailroadClassDescription` empty | → `BaseELPRR = 0` (silent zero) |

---

## Comparison — CW 2023/2026 vs CW 2027 edition

The largest edition change of any subline gated so far: **65 rules → 46**, effective 2027-04-01
(gate doc §2).

| | CW 2023/2026 | CW 2027 |
|---|---|---|
| Rule count | 65 | 46 (22 deleted, 3 added, 7 changed) |
| Rate source for construction-ops/owner factor | `LookupOwnersContractorsLossCost` (loss cost) | `LookupOwnersContractorsELP` (ELP) — **new rule added** |
| Work-trains charge | `WorkTrainsOrOtherRREquipmtRate = 56.8`, 6 rules | **Withdrawn**; CW table goes to 0 rows |
| Supervisors/inspectors extension | 4 rules, `CovForInjuriesToSuprvsr...` | **Withdrawn**; CW table to 0 rows |
| Minimum premium | `SetMinPremium`, `SetMinimumPremium`, `MinPremiumRR` table | **Withdrawn**; CW table to 0 rows |
| Mixed-hazard machinery | `SetPriorToFinalRateMixedHazard`, `SetPriorToFinalRate40014`, `SetAdjustedBaseELPRR`, `SetBaseELPRR40011`, `SetBaseELPRR400145orLess`, `SetFinalRate40011` | **All gone** |
| Base rate rule | (absorbed into ELP chain) | `SetBaseRate`, `SetBaseRate40014` — `BaseRate = round(BaseELPRR x LCM, 3)`, same shape as Liquor |
| `SetFinalRate` | 2,303 characters | **10,942 characters**, branches on all four class codes as string literals |

**Cause and effect across gates:** Railroad's 2027 rewrite is a direct consequence of OCP's. OCP
withdraws its `OwnersContractorsLossCost` table in 43 jurisdictions on 2027-04-01 (per
`GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`); Railroad reads that table (Step 1 above), so it
had to move to OCP's ELP instead (gate doc §2, §9).

---

## Supporting lookups

| Table | Used for | Countrywide rows | State rows (as of today) |
|---|---|---|---|
| `RailroadELP` | Rating-basis selector, string value `"Industry"` in all rows | 0 | 51/51 · 204 |
| `BaseELPRR` | ELP by (State, ClassCode, trains/day), excludes 40014 | 0 | 51/51 · exactly 18 each (918 total) |
| `ILFRailroad` | Increased Limits Factor, Rule 56.B.7 | 0 | 51/51 · 1,836 |
| `RailroadHomogeneityIndex` | Not resolved in source docs — table is listed in the layer-pattern table (gate doc §5) with no rule name or purpose given | 0 | 51/51 · 969 |
| `OwnersContractorsLossCost` | Read by Step 1 (`LookupOwnersContractorsLossCost`, hardcoded class `16292`) — OCP's table, not Railroad's own | 0 | 51/51 · 563 → 8/51 · 88 at the 2027 cliff |
| `RailroadLossCost` | **Orphan.** Exists in all 10 CW editions, 0 rows in every edition and every jurisdiction, referenced by **no rule anywhere in the corpus** (confirmed by scanning every rule file for the string) | 0 | 0/51 |
| `RailroadLCM` | Loss Cost Multiplier | 1 row, value `1` | 0/51 |
| `ConstructionOpsOwnerAdjmtFactor` | Step 3 factor | 1 row, value `1.5` | 0/51 |
| `WorkTrainsOrOtherRREquipmtRate` | Step 7–10 dollar rate | 1 row, value `56.8` | 0/51 |
| `CovForInjuriesToSuprvsrInspctrsOtherEmpsOfTheInsd` | Step 6 factor | 1 row, value `0.1` | 0/51 |
| `MinPremiumRR` | Minimum premium | 1 row, value `0` | 0/51 |
| `PolicyLimitsRailroadStatCode` | Statistical reporting | 9 rows | 0/51 |

`LookupPremOpsLCM` is present but **uncalled** in the Railroad rule file in all 10 editions — the
same dead lookup copy-pasted from the Liquor file (gate doc §5).

---

## State deviations

Only **two jurisdictions** (AK, NY) file any `GeneralLiabilityClassificationRailroadCoverage`
rule — the smallest state-deviation surface of any subline gated. Each overrides three rules,
two of which are boilerplate (`InitializeRuleSet`, `ErcProcess`). The one substantive override
countrywide is `SetMoldStatCode`, a statistical-coding rule that changes no premium (gate doc
§6). `BaseELPRR` itself has exactly 18 rows in all 51 jurisdictions with no state adding or
dropping a row.

---

## Verification — the 18-cell test

Alaska's ERC `BaseELPRR` table (`GL_AK_20260801_V02`) checked cell-by-cell against Procedure 5.E
of `GL-AK-2020-LC-001-C.pdf` — a 2026 machine-readable package versus a 2020 filed PDF, six
years apart:

| Class | 5 or less | 6–20 | 21–40 | 41–60 | 61–100 | Over 100 |
|---|---|---|---|---|---|---|
| 40011 | 2.88 | 4.80 | 6.40 | 8.32 | 11.20 | 13.92 |
| 40012 | 2.40 | 4.00 | 5.60 | 7.20 | 9.60 | 12.00 |
| 40013 | 4.80 | 7.68 | 10.40 | 13.60 | 18.40 | 23.20 |

**All 18 cells identical**, and `40014` is correctly absent from the table in both sources — it
is derived (150% × OCP class `16292`) rather than tabulated (gate doc §4). No oracle exists for
an end-to-end Railroad premium: the golden case carries Railroad with
`CoverageOnPolicyIndicator = 0` / `Premium = 0.0`, confirming only the entry gate
(gate doc §8; `tests/verify_golden.py` 80/80 unchanged).

---

## Quick reference — end-to-end, class 40011/40012 (no mixed hazard, single-hazard project)

```
ConstructionOpsOwnerFactor = LookupOwnersContractorsLossCost(classCode = "16292")   # OCP table
LCM                        = LookupRailroadLCM                                       # CW: 1
ConstructionOpsOwnerAdjmtFactor = 1.5                                                # CW constant

BaseELPRR       = LookupBaseELPRR(State, ClassCode, NumPassgrFreightTrains)          # banded, 18-row table
ILF             = LookupILFRailroad(...)                                             # or ILF40014 for class 40014
SuprvsrFactor   = 0.1                                                                 # CW constant

WorkTrainsRate  = 56.8   # per $1,000 Total Cost, CW constant (withdrawn CW 2027)

AdjustedBaseELPRR = f(BaseELPRR, LCM, ...)
FinalRate         = AdjustedBaseELPRR x ILF   (FinalRate40011 for class 40012)

Premium = FinalRate x TotalCost / 1000
        + CovForInjuriesToSuprvsrInspOtherEmpOfTheInsdPremium   (classes 40011/40012/40014)
        + WorkTrainsOrOtherRREquipmtPremium                     (withdrawn CW 2027)
        subject to MinPremiumRR (= 0, CW; withdrawn CW 2027)
```

## Quick reference — end-to-end, class 40011 mixed-hazard project

```
EstdContractCostWORRHzd > 0   -->  project is partly clear of the tracks

# No-hazard portion, rated on the class-40014 basis:
BaseELPRR400065orLess = round(ConstructionOpsOwnerFactor x ConstructionOpsOwnerAdjmtFactor, 3)
                       = round(OwnersContractorsLossCost(16292) x 1.5, 3)

# Hazard portion, rated on the class-40011/40012 basis:
BaseELPRR40011 = LookupBaseELPRR(State, "40011", NumPassgrFreightTrains)

ContractCostFactorWOHzd, ContractCostFactorWithHzd  = the two weighting factors (Procedure 5.E.4)

PriorToFinalRateMixedHazard = weighted average of the two rates using the two contract-cost factors

FinalRate = f(PriorToFinalRateMixedHazard, ILF)

Premium = FinalRate x TotalCost / 1000 + (supervisors/inspectors, work-trains add-ons as above)
```

## Quick reference — end-to-end, class 40013 (highway projects)

```
ConstructionOpsOwnerFactor = LookupOwnersContractorsLossCost(classCode = "16292")
EstimatedContractCostRatio = at-hazard contract cost / total contract cost      # Procedure 5.E.2.b

BaseELPRR = LookupBaseELPRR(State, "40013", NumPassgrFreightTrains)

AdjustedBaseELPRR = f(BaseELPRR, EstimatedContractCostRatio, LCM)
FinalRate         = AdjustedBaseELPRR x ILF

Premium = FinalRate x TotalCost / 1000
        (no supervisors/inspectors add-on — class 40013 not listed in Step 11's scope)
```

## Quick reference — end-to-end, class 40014 (no railroad-hazard exposure)

```
BaseELPRR40014  # not tabulated; derived —
             = round(OwnersContractorsLossCost(16292) x 1.5, 3)   # same formula as the
                                                                    # 40011 mixed-hazard no-hazard portion
ILF40014 = LookupILFRailroad(...)   # class 40014's own ILF rule

FinalRate = BaseELPRR40014 x ILF40014

Premium = FinalRate x TotalCost / 1000
        + CovForInjuriesToSuprvsrInspOtherEmpOfTheInsdPremium   (class 40014 included, Step 11)
```

---

*Not resolved in source docs — the gate doc does not give: the exact `Choose`/branch pseudocode
for `SetFinalRate`, `SetAdjustedBaseELPRR`, or the weighted-average formula in
`SetPriorToFinalRateMixedHazard`; the exact rounding/decimal-place convention used at each step
(the CF template's `round(expr, dp)` notation is not available for Railroad because the gate doc
does not report it); or the purpose of the `RailroadHomogeneityIndex` table beyond its row
counts. These would require reading the ERC rule XML directly, which is out of scope for this
reformat (the source material read for this document is the gate doc and the three supporting
docs named in the header, not the ERC package itself).*
