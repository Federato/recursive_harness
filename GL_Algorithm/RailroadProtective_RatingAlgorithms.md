# Railroad Protective Liability — Rating Algorithms

**Source:** `docs/gates/GATE-335-RAILROAD-PROTECTIVE.md` (filed 2026-08-11, as-of date 2026-08-11),
cross-referenced against `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` §3.1 row 6 / §3.1.1 /
§3.2.5, `docs/erc/03-RATING-STRUCTURE.md` §2.1/§2.4, and `docs/rating-engine/A3-ENDORSEMENT-CATALOG.md`
"Rule 49 — Railroad Protective (335)".

**Line:** General Liability (GL), subline code **335** — shared with Owners & Contractors
Protective (OCP; see `GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`). ISO manual rule: **Rule 49**,
`GL-MU-2027-RU-001-C.pdf` p.124–127 (CW 2027 edition); Rule 49 in the CW 2023/2026 edition
(`GL_CW_20231201_V03`) carries the algorithm this document primarily describes.

**Derived against:** `GL_CW_20231201_V03`, the parent the OK golden case declares. The Railroad
rule file is byte-identical across `GL_CW_20231201_V03`, `GL_CW_20260101_V01` and
`GL_CW_20261001_V01`, and across `GL_CW_20270401_V01` / `V02`; CA's parent `GL_CW_20231201_V02`
differs from V03 only in lacking the `IsNull` override guards.

**Documented:** 2026-08-20.
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — ISO's RI, NH and MN Railroad STC submissions (classes 40011 incl. mixed hazard, 40012, 40013 with work trains, 40014) re-dated and rated offline by the kernel at 2026-10-02 (over CW 20260101 V01) and 2027-04-01 (over CW 20270401 V02); every rule body read from XML; table populations censused across all 51 resolved jurisdictions.

Railroad Protective Liability (coverage form `CG 00 35`) rates **four classes**, all on a
**Total Cost per $1,000** exposure base (Rule 24.F). It is the same subline code as OCP, but a
different rule (49, not 46) and a different rate table family — "two coverages, two rules, one
statistical subline" (gate doc §0 naming note). Unlike OCP, Railroad has **no published loss
cost in any jurisdiction (0/51)**; it rates entirely off the ELP (Estimated Loss Potential)
supplement, and Rule 49.E.1 itself says "Refer to company" for basic-limits rates — the actual
procedure lives in the ELP Supplement, Procedure 5.E (`GL-AK-2020-LC-001-C.pdf` pp.10–11), not
in the rules manual.

This document covers the CW 2023/2026 algorithm (65 rules) and flags the CW 2027 rewrite
(46 rules) at each point where it diverges. Which one runs is chosen by the **resolved parent** as
of the risk's effective date (a submission variable, decision A3; `package_version` can pin an
edition): as of 2026-10-02 all 51 jurisdictions run the CW 2023/2026 chain; as of 2027-04-01, 46 run
the CW 2027 chain (AK, DC, MA, NC, SC, TX, WI, WV over `GL_CW_20270401_V01`, 38 over
`GL_CW_20270401_V02`) and 5 — CA (over `GL_CW_20231201_V02`), GA, NJ, NY, WA (over
`GL_CW_20260101_V01`) — still run the CW 2023/2026 chain.

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

`ErcSetRatesAndFactors` runs **21** rules (#1–21 below) and `ErcRate` runs **10** (#22–31), in
the order the engine executes them (trace, RI@2026-10-02). The chain forks repeatedly by class
code (`40011`, `40012`, `40013`, `40014`) — "the chain forks by class more heavily than any subline
so far" (gate doc §2) — but every rule runs for every class; the forks are inside the rules. The
gate doc's "26-step `ErcSetRatesAndFactors`" with the split at #22/#23 does not match the rule
file: `SetILF40014` is its own step, and the two final-rate rules are the first two of `ErcRate`,
not the end of `ErcSetRatesAndFactors`.

---

## File map

Rule files resolved 2026-10-02 from the engine trace and the CW packages. Line numbers are not
cited; `rule_dump.py GeneralLiabilityClassificationRailroadCoverage <Rule> <pkg>` prints any rule.

| Piece | Source |
|---|---|
| Rate/premium chain (31 rules in the two Erc lists; 65 in the file) | `GeneralLiabilityClassificationRailroadCoverageRules.Rule.xml` — confirmed by engine trace 2026-10-02 |
| Selector / homogeneity / limits written to the classification | `GeneralLiabilityClassificationRules.Rule.xml`: `SetRailroadELP` (from `RailroadELP`), `SetRailroadHomogeneityIndex`, `SetRailroadEachOccurrenceLimit`, `SetRailroadAggregateLimit`, and two Railroad validation messages (`DoMessageEstimatedContractCostRatio…`, `DoMessageEstimatedContractCostWithoutRailroadTrainHazardCannotExceedExposureAmount`) |
| Policy-level minimum-premium top-up (pre-2027) | `GeneralLiabilityRailroadPremiumToReachMinCoverageRules.Rule.xml` (9 rules → 4 at CW 2027) |
| Manual rule (rating is "refer to company" in-manual) | Rule 49, pp.124–127; `E.1 Basic Limits: "Refer to company."`; `E.2 Increased Limits: "Refer to Rule 56."`; `F. Basis Of Premium: Total Cost.` |
| Actual rating procedure | ELP Supplement Procedure 5.E, `GL-AK-2020-LC-001-C.pdf` pp.10–11 (gate doc §4) |
| Coverage form | `CG 00 35` — Railroad Protective Liability Coverage Form (`A3-ENDORSEMENT-CATALOG.md` "Rule 49") |
| Mandatory multistate endorsement | `IL 00 21` — Nuclear Energy Liability Exclusion Endorsement Broad Form |
| Optional refer-to-company endorsements | `CG 24 01`, `CG 24 02`, `CG 24 04`, `CG 24 14`, `CG 24 53`, `CG 33 71`, `CG 34 21`, `CG 34 22`, `CG 34 31`, `CG 34 48`, `CG 34 49`, `CG 34 96` — all `OPTIONAL_RTC`, Rule 49 §D |
| Contractual liability endorsements (general, not railroad-specific) | `CG 24 17`, `CG 24 27` — Contractual Liability Railroads Endorsement / Limited variant |
| Dedicated state ILF table | Rule 56.B.7, present in all 51 jurisdictions (`03-SUBLINE-COVERAGE-PLAN.md` §3.2.5) |

---

## Railroad Protective — rate build-up

Executed in order (engine trace RI@2026-10-02, `GL_RI_20260301_V02` over `GL_CW_20260101_V01`;
rule order read from `ErcSetRatesAndFactors` / `ErcRate` in the rule file):

```
ErcSetRatesAndFactors (21):
#1  SetConstructionOpsOwnerFactor
#2  SetLCM
#3  SetConstructionOpsOwnerAdjmtFactor
#4  SetEstimatedContractCostRatio                    (class 40013 only)
#5  SetILF                                           (the risk's own class)
#6  SetILF40014                                      (every class: ILF looked up AS class 40014)
#7  SetCovForInjuriesToSuprvsrFactor
#8  SetTotalCostWorkTrainsOrOtherRREquipmtAssigned
#9  SetWorkTrainsOrOtherRREquipmtBaseRate
#10 SetWorkTrainsOrOtherRREquipmtRate
#11 SetWorkTrainsOrOtherRREquipmtFinalRate
#12 SetInjurySuprvsrInspOthrEmpCovConstrOpsRROps      (classes 40011, 40012, 40014)
#13 SetBaseELPRR                                      (table for 40011-40013; derived for 40014)
#14 SetBaseELPRR400145orLess                          (40011 mixed-hazard path)
#15 SetBaseELPRR40011                                 (tests 40012 + supervisors Included)
#16 SetContractCostFactorWOHzd
#17 SetContractCostFactorWithHzd
#18 SetAdjustedBaseELPRR                              (all four classes)
#19 SetBaseELPRR40014                                 (40011 mixed-hazard continuation)
#20 SetPriorToFinalRateMixedHazard
#21 SetPriorToFinalRate40014

ErcRate (10):
#22 SetFinalRate
#23 SetFinalRate40011                                 (tests 40012 + supervisors Included)
#24 SetTotPremiumPriorToInjuryToSuprvsrCovPremium
#25 SetTotPremiumPriorToInjuryToSuprvsrCovPremium40011
#26 SetCovForInjuriesToSuprvsrInspOtherEmpOfTheInsdPremium
#27 SetWorkTrainsOrOtherRREquipmtPremium
#28 SetMinimumPremium
#29 SetMinPremium
#30 SetPremium
#31 SetPremiumIndicator
```

The gate doc's `SetTotalCostWorkTrainsOrOtherRREquipmt{BaseRate,Rate,FinalRate}` names do not exist
in the rule file; the rules are `SetWorkTrainsOrOtherRREquipmt{BaseRate,Rate,FinalRate}`. Formulas
below are read from the CW 20260101 V01 rule XML; every `round(…, n)` is the rule's own
`DecimalPlaces`, and every operand is read through `FirstValue(…, 0)` (absent → `0`).

### Step 1 — Construction Operations/Owner factor
`SetConstructionOpsOwnerFactor` (#1)

```
ConstructionOpsOwnerFactor = LookupOwnersContractorsLossCost(State|CW, classCode = "16292")
                             (only when RailroadClassCode is non-empty, else 0.0)
```

`16292` is **hardcoded in the rule** — it does not vary by the risk's own class code. This reads
**OCP's** loss-cost table, not a Railroad-specific one (gate doc §3). Confirmed against the
manual: Procedure 5.E.1.a states the Basic Limit ELP per $1,000 of Total Cost is *"150% of the
loss cost for Class Code 16292 Construction Operations – Owner"* (gate doc §4) — exact match
including the class code. Engine: RI, NH, MN @2026-10-02 all resolve `['<ST>', '16292'] → 0.24`.
In CW 2027 the rule reads `LookupOwnersContractorsELP` instead (RI/NH/MN@2027-04-01 → `0.162`).

### Step 2 — Loss Cost Multiplier
`SetLCM` (#2)

```
LCM = LookupRailroadLCM          # (State|CW, "Y")
```

Countrywide, **one row, value `1`** — an unsupplied company multiplier (gate doc §5, "E15"; the
referral register treats `LCM = 1` as a CONFIG item, R18, not a per-rating referral).

### Step 3 — Construction Operations/Owner adjustment factor
`SetConstructionOpsOwnerAdjmtFactor` (#3)

Countrywide, one row, value **`1.5`**. Matches Procedure 5.E.1.a's *"150%"* (gate doc §4).

### Step 4 — Estimated contract cost ratio (class 40013 only)
`SetEstimatedContractCostRatio` (#4)

```
EstimatedContractCostRatio = ../EstimatedContractCostRatio    if RailroadClassCode = "40013"
                           | 0.0                              otherwise
```

**It is a submitted classification input, copied — not computed by the rule.** Per Procedure
5.E.2.b: *"applying to the ELP the ratio of the estimated contract cost of the operations performed
on, over or under the insured railroad's property or within 50 feet … to the total contract cost"*
(gate doc §4). ISO's `DoMessageEstimatedContractCostRatioRailroadOperationsMustBeEnteredForTheClassificationSelected`
validates its presence.

### Step 5 — Increased Limits Factors
`SetILF` (#5) / `SetILF40014` (#6)

```
ILF      = LookupILFRailroad(State|CW, RailroadClassCode, RailroadEachOccurrenceLimit, RailroadAggregateLimit)
ILF40014 = LookupILFRailroad(State|CW, "40014",          RailroadEachOccurrenceLimit, RailroadAggregateLimit)
           (both 0.0 when RailroadClassDescription, the class code or either limit is empty)
```

**`SetILF40014` runs for every class**, not just 40014 — it supplies the ILF for the no-hazard
portion of a 40011 mixed-hazard risk. Table: `ILFRailroad`, Rule 56.B.7, keyed (State, ClassCode,
each-occurrence limit, aggregate limit); 0 rows countrywide / 51 jurisdictions · 1,836 rows (engine
census, both dates). Railroad limits carry no `" CSL"` suffix in any edition (lookup key
`['RI', '40011', '1,000,000', '3,000,000']` at both dates), so the 2027 renormalization (OI-96/97)
does not apply. RI@2026-10-02: `ILF 1.96` (40011/40012/40013), `ILF40014 1.68`.

### Step 6 — Supervisors/inspectors coverage factor
`SetCovForInjuriesToSuprvsrFactor` (#7)

Countrywide, one row, value **`0.1`**. Matches Procedure 5.E.1.a / 5.E.3.c: *"charge an
additional premium of 10%"* for supervisors, inspectors and other employees at the job site
(gate doc §4) — exact match.

### Steps 7–10 — Work-trains rate
`SetTotalCostWorkTrainsOrOtherRREquipmtAssigned` → `SetWorkTrainsOrOtherRREquipmtBaseRate` →
`…Rate` → `…FinalRate` (#8–11)

```
TotalCostWorkTrainsOrOtherRREquipmtAssigned = submitted classification value, else 0
WorkTrainsOrOtherRREquipmtBaseRate  = 56.8          # per $1,000 of Total Cost, countrywide, 1 row
WorkTrainsOrOtherRREquipmtRate      = round(56.8 x LCM, 3)
WorkTrainsOrOtherRREquipmtFinalRate = round(WorkTrainsOrOtherRREquipmtRate x ILF, 3)   # the class's own ILF
```

Matches Procedure 5.E.2.c: *"The $100,000/300,000 Basic Limit ELP per $1,000 of Total Cost is
$56.80"* (gate doc §4) — exact match, and a rare case of a **countrywide dollar rate**
(gate doc §5) rather than a factor — README finding #1 ("no national loss cost publication at
all") is qualified by this rate (gate doc §9). Engine: `111.328` at ILF 1.96, `95.424` at ILF 1.68.
The rate is computed for every class but only **charged for class 40013** (see premium).

### Step 11 — Supervisors/inspectors election
`SetInjurySuprvsrInspOthrEmpCovConstrOpsRROps` (#12)

```
InjurySuprvsrInspctrsOtherEmpsCovConstrctnOpsRROps = ../InjurySuprvsrInspctrsOtherEmpsCov   for 40011, 40012, 40014
                                                   | ""                                     otherwise
```

### Step 12 — Base ELP for Railroad
`SetBaseELPRR` (#13)

```
if RailroadClassDescription = "":                    BaseELPRR = 0.0
elif RailroadClassCode <> "40014":
    BaseELPRR = LookupBaseELPRR(State, ClassCode, NumPassgrFreightTrains)   if trains band given
              | 0.0                                                         otherwise
else (40014):
    BaseELPRR = round(ConstructionOpsOwnerAdjmtFactor x ConstructionOpsOwnerFactor, 3)
                                                     if ../RailroadELP = "Industry"
              | 0.0                                  otherwise
```

Keyed on **(State, ClassCode, Number of Passenger and Freight Trains Per Day)**, banded into six
train-count tiers. The **table** excludes class `40014`; the **rule** does not — it derives 40014's
ELP as 150% × OCP class `16292` (gate doc §4, "18-cell test" note), gated on the classification's
`RailroadELP` selector (written from the `RailroadELP` table by `GeneralLiabilityClassificationRules.SetRailroadELP`;
`"Industry"` in every row). NH@2026-10-02, class 40014: `round(1.5 x 0.24, 3) = 0.360`. Matches manual
Tables 5.E.2.a, 5.E.3.a, 5.E.3.b: *"Number Of Passenger And Freight Trains Per Day"*, six bands
(gate doc §4) — exact match including the banding.

**Table has exactly 18 rows in every one of the 51 jurisdictions** (3 classes × 6 bands),
**0 rows countrywide** (gate doc §0, §5, §6; engine census 918 rows at both 2026-10-02 and
2027-04-01) — perfectly uniform, and the smallest state-deviation surface of any subline gated to
date. **At 2027-04-01 every cell is exactly half its 2026 value** (AK `GL_AK_20270401_V01`, all 18;
RI, NH, MN observed the same).

### Step 13 — Mixed-hazard base (naming trap #1)
`SetBaseELPRR400145orLess` (#14)

For a **class `40011`** risk with `EstdContractCostWORRHzd > 0` (a project only partly clear of
the tracks), the no-hazard portion is rated on the class-`40014` basis:

```
BaseELPRR400065orLess = round(ConstructionOpsOwnerFactor x ConstructionOpsOwnerAdjmtFactor, 3)
                       = round(OCP loss cost for class 16292 x 1.5, 3)          # else 0.0
```

**Naming trap:** despite the rule name containing `400145`, this rule **tests class `40011`**
and **writes to DataDef `BaseELPRR400065orLess`** — neither number in the rule name or DataDef
name is the class being tested. Per gate doc §2: "the rule names refer to the rate basis being
applied, not the risk's class." This is documented as **N11 at its purest** — the printed number
is unreliable in both rule names and DataDef names; only `SetILF40014` → `ILF40014` is
consistent end to end.

### Step 14 — Base ELP at the 40011 rate, for 40012 with supervisors
`SetBaseELPRR40011` (#15)

```
BaseELPRR40011 = round(LookupBaseELPRR(State, "40011", NumPassgrFreightTrains), 3)
                 if RailroadClassCode = "40012" and InjurySuprvsr…ConstrctnOpsRROps = "Included"
               | 0.0 otherwise
```

Not "classes 40011/40012" as the gate summary put it: it fires **only for 40012 with the
supervisors election**, and looks up the **40011** row — the supervisors charge on a 40012 risk is
10% of what the risk would cost at the 40011 rate (premium step #25–26).

### Steps 15–16 — Mixed-hazard contract cost factors
`SetContractCostFactorWOHzd` / `SetContractCostFactorWithHzd` (#16–17)

```
ContractCostFactorWOHzd   = round(EstdContractCostWORRHzd / RailroadExposure, 8)
ContractCostFactorWithHzd = round((RailroadExposure - EstdContractCostWORRHzd) / RailroadExposure, 8)
                            (both 0.0 when RailroadExposure = 0)
```

The two halves of a mixed-hazard project: the without-hazard portion and the with-hazard
portion. Per Procedure 5.E.4, *Special Rating Procedure*, for projects *"part of which are
subject to an actual railroad train hazard and part of which are not"* → *"weighted average"*
(gate doc §4) — exact match. Engine RI@2026-10-02 (exposure 15,000, `EstdContractCostWORRHzd` 10):
`0.00066667` / `0.99933333`. ISO's `DoMessageEstimatedContractCostWithoutRailroadTrainHazardCannotExceedExposureAmount`
guards `WORRHzd <= Exposure`.

### Step 17 — Adjusted Base ELP
`SetAdjustedBaseELPRR` (#18)

```
40011, 40014 : AdjustedBaseELPRR = round(BaseELPRR x LCM, 3)
40013        : AdjustedBaseELPRR = round(BaseELPRR x EstimatedContractCostRatio x LCM, 3)
40012        : AdjustedBaseELPRR = round(BaseELPRR x ContractCostFactorWithHzd x LCM, 3)  if EstdContractCostWORRHzd > 0
                                 | round(BaseELPRR x LCM, 3)                              otherwise
other        : 0.0
```

(A 40012 risk's no-hazard portion is simply dropped, not re-rated at 40014.)

### Step 18 — Mixed-hazard continuation (naming trap #2)
`SetBaseELPRR40014` (#19)

```
BaseELPRR40006 = round(BaseELPRR400065orLess x LCM, 3)   if class 40011 and EstdContractCostWORRHzd > 0
               | 0.0                                      otherwise
```

**Naming trap, continued:** despite the name containing `40014`, this rule **tests class
`40011`** and writes DataDef `BaseELPRR40006`. `40006` is *"Miscellaneous"* in
`ClassificationType.RateTable.csv` — an unrelated classification (gate doc §2). An engine that
maps `BaseELPRR40006` to class `40006` would produce nonsense; it is a mixed-hazard-path
DataDef name, not an identity. (CW 2027 renames the DataDef to `BaseELPRR40014`.)

### Steps 19–20 — Weighted average
`SetPriorToFinalRateMixedHazard` / `SetPriorToFinalRate40014` (#20–21), class 40011 with
`EstdContractCostWORRHzd > 0` only (else `0.0`):

```
PriorToFinalRateMixedHazard = round(AdjustedBaseELPRR x ILF      x ContractCostFactorWithHzd, 3)
PriorToFinalRate40006       = round(BaseELPRR40006    x ILF40014 x ContractCostFactorWOHzd, 3)
```

`SetPriorToFinalRate40014` also tests class `40011` and writes `PriorToFinalRate40006` — same
naming-trap pattern as step 18.

### Steps 21–22 — Final rate
`SetFinalRate` / `SetFinalRate40011` (#22–23, the first two rules of `ErcRate`)

```
Mods = ExperienceRatingModificationFactor x ExpenseModification x ScheduleRatingModificationFactor
       # policy-level; NOT ModToUse / PackageModFactor as OCP and Liquor use

FinalRate      = round((PriorToFinalRateMixedHazard + PriorToFinalRate40006) x Mods, 3)
                                                     if class 40011 and EstdContractCostWORRHzd > 0
               | round(AdjustedBaseELPRR x ILF x Mods, 3)        otherwise (all classes)
FinalRate40011 = round(BaseELPRR40011 x ILF x Mods, 3)           if class 40012 and supervisors Included
               | 0.0                                             otherwise
```

`SetFinalRate40011` tests class `40012` and writes `FinalRate40011` — a third instance of the
naming trap (rule name references `40011`, tested class is `40012`).

---

## Railroad Protective — premium

### Gate
`ErcProcess` (gate doc §2): `CoverageOnPolicyIndicator == 0` → `Premium = 0.0`, stop. Otherwise
the chain above runs, then the rest of `ErcRate` (#24–31):

```
TotPremiumPriorToInjuryToSuprvsrCovPremium      = round(FinalRate x RailroadExposure / 1000, 0)
TotPremiumPriorToInjuryToSuprvsrCovPremium40011 = round(FinalRate40011 x RailroadExposure / 1000, 0)
                                                  (40012 + supervisors Included; else 0.0)
CovForInjuriesToSuprvsrInspOtherEmpOfTheInsdPremium
    = round(TotPremiumPriorToInjury…Premium      x 0.1, 0)   40011 or 40014, supervisors Included
    | round(TotPremiumPriorToInjury…Premium40011 x 0.1, 0)   40012, supervisors Included
    | 0.0                                                     otherwise (incl. all 40013)
WorkTrainsOrOtherRREquipmtPremium = round(WorkTrainsOrOtherRREquipmtFinalRate
                                          x TotalCostWorkTrainsOrOtherRREquipmtAssigned / 1000, 0)

SetPremium  (only when Subline = "Railroad"; else 0.0):
    40013  : Premium = TotPremiumPriorToInjury…Premium + WorkTrainsOrOtherRREquipmtPremium
    others : Premium = TotPremiumPriorToInjury…Premium + CovForInjuriesToSuprvsr…Premium
```

Confirmed against Rule 49.G: *"Total Cost — per $1,000 of total cost"*, applied to all four
classes (gate doc §4) — confirms the ÷1000. Note the base premium is rounded to whole dollars
**before** the add-ons are computed and summed.

### Branch — classes 40011 / 40012 (no hazard split)
Standard path: `FinalRate` feeds `TotPremiumPriorToInjury…Premium` directly, plus the
supervisors/inspectors add-on when elected. For 40012 the add-on is 10% of the premium **at the
40011 rate** (`FinalRate40011`). The work-trains add-on is **not** charged to 40011/40012/40014
(the gate summary said it was).

### Branch — class 40011, mixed hazard
When `EstdContractCostWORRHzd > 0`: the no-hazard portion routes through the class-`40014` basis
(steps 13/18, `ILF40014`), the hazard portion through the class's own `AdjustedBaseELPRR` and
`ILF`, each weighted by its contract-cost factor (steps 15–16/19–20); their sum is `FinalRate`.

### Branch — class 40013
`AdjustedBaseELPRR` carries the submitted `EstimatedContractCostRatio` (step 4); no supervisors
add-on; the work-trains premium **is** added.

### Branch — class 40014
`BaseELPRR` = 150% of OCP class `16292`'s loss cost (step 12, `RailroadELP = "Industry"` gate),
rated with the class's own `ILF` (which for 40014 is the same cell as `ILF40014`).

### Minimum premium
`SetMinimumPremium` reads `MinPremiumRR` (State|CW, `"Y"`) — countrywide, **one row, value `0`**
(gate doc §5, "E16") — when `Subline = "Railroad"`; `SetMinPremium = round(MinimumPremium x ILF, 0)`
when also `MiscIfAnyBasis = "No"`. As with OCP, `MinPremium` is **not** applied inside `SetPremium`;
it feeds the policy-level `GeneralLiabilityRailroadPremiumToReachMinCoverage` top-up
(`max(0, max MinPremium − Σ Premium)`), which is structurally `0` today and loses its rating rules at
CW 2027.

### Refer-to-company triggers (not gated in ERC)
Per gate doc §7, re-checked against the engine 2026-10-02:

| # | Trigger | ERC discriminator | Engine (`underwriting` mode) |
|---|---|---|---|
| 1 | All basic-limits rates (Rule 49.E.1) | None — manual-only | no referral |
| 2 | Operations other than construction (Procedure 5.E.1.b, 5.E.3.d) | **None** — ERC rates whatever class code is submitted (recorded as **OI-45**, "known unguarded referral") | no referral |
| 3 | `LCM == 1` (unsupplied company multiplier) | None | R18 is a CONFIG item, not raised per rating |
| 4 | Class code outside `40011`–`40014` | Falls through every branch → `FinalRate = 0` → `Premium = 0` (CW 2023/2026) / **`Premium = 1.0`** (CW 2027 `$1` floor) | no referral, no OI-94 refusal (no `*LossCost` node in this chain) |
| 5 | `RailroadClassCode` / `RailroadClassDescription` empty | → `BaseELPRR = 0` (silent zero; `$1` at CW 2027) | no referral |

R29 never fires for Railroad: ISO's `DoMessageMustEnterEstimatedLossPotentialFactorOverride` has
OCP, Liquor and Product Withdrawal branches but no Railroad branch, and `RailroadELP` is
`"Industry"` in all 204 rows. **That is correct, not a gap** (OI-131 closed 2026-10-14): there is no
Company-rated Railroad class for R29 to refer.

---

## Comparison — CW 2023/2026 vs CW 2027 edition

The largest edition change of any subline gated so far: **65 rules → 46**, effective 2027-04-01
(gate doc §2; re-confirmed by rule diff CW 20260101 V01 → CW 20270401 V02: 22 removed, 3 added —
`LookupOwnersContractorsELP`, `SetBaseRate`, `SetBaseRate40014` — 7 changed). CW 2027's
`ErcSetRatesAndFactors` is 12 rules (`SetConstructionOpsOwnerFactor, SetLCM,
SetConstructionOpsOwnerAdjmtFactor, SetEstimatedContractCostRatio, SetILF, SetILF40014,
SetBaseELPRR, SetBaseELPRR40014, SetBaseRate, SetBaseRate40014, SetContractCostFactorWOHzd,
SetContractCostFactorWithHzd`) and `ErcRate` is 3 (`SetFinalRate, SetPremium, SetPremiumIndicator`).
On 2027-04-01 it runs in 46 jurisdictions; CA, GA, NJ, NY and WA stay on the CW 2023/2026 chain.

| | CW 2023/2026 | CW 2027 |
|---|---|---|
| Rule count | 65 | 46 (22 deleted, 3 added, 7 changed) |
| Rate source for construction-ops/owner factor | `LookupOwnersContractorsLossCost` (loss cost) | `LookupOwnersContractorsELP` (ELP) — **new rule added** |
| Work-trains charge | `WorkTrainsOrOtherRREquipmtRate = 56.8`, 6 rules | **Withdrawn**; CW table goes to 0 rows |
| Supervisors/inspectors extension | 4 rules, `CovForInjuriesToSuprvsr...` | **Withdrawn**; CW table to 0 rows |
| Minimum premium | `SetMinPremium`, `SetMinimumPremium`, `MinPremiumRR` table | **Withdrawn**; CW table to 0 rows |
| Mixed-hazard machinery | `SetPriorToFinalRateMixedHazard`, `SetPriorToFinalRate40014`, `SetAdjustedBaseELPRR`, `SetBaseELPRR40011`, `SetBaseELPRR400145orLess`, `SetFinalRate40011` | **All gone** |
| Base rate rule | (absorbed into ELP chain) | `SetBaseRate`, `SetBaseRate40014` — `BaseRate = round(BaseELPRR x LCM, 3)`, `BaseRate40014 = round(BaseELPRR40014 x LCM, 3)`, same shape as Liquor |
| `SetBaseELPRR` | 40014 derived only when `RailroadELP = "Industry"` | 40014 derived unconditionally; other classes need a trains band |
| Mixed-hazard DataDef | `BaseELPRR40006` / `PriorToFinalRate40006` | `BaseELPRR40014` (the `40006` naming trap is gone) |
| `SetFinalRate` | 2,303 characters | **10,942 characters**, branches on all four class codes as string literals: 40011 mixed → `round((BaseRate x ILF x WithHzd + BaseRate40014 x ILF40014 x WOHzd) x Mods, 3)`; 40012 mixed → `round(BaseRate x WithHzd x ILF x Mods, 3)`; 40013 → `round(BaseRate x EstimatedContractCostRatio x ILF x Mods, 3)`; else `round(BaseRate x ILF x Mods, 3)`; unknown class → `0` |
| `SetPremium` | `round(FinalRate x TotalCost/1000, 0)` + add-ons, only when `Subline = "Railroad"` | `round(FinalRate x TotalCost/1000, 0)`, **`1.0` if that is `0`** (no exposure test, no `Subline` gate) |
| `BaseELPRR` values | AK 40011 "5 or Less" `2.88` … | **every cell halved** (AK `1.44` …; RI, NH, MN the same) |

**Cause and effect across gates:** Railroad's 2027 rewrite is a direct consequence of OCP's. OCP
withdraws its `OwnersContractorsLossCost` table on 2027-04-01 in the 46 jurisdictions that move to a
CW 2027 parent (engine census; the gate doc said 43); Railroad reads that table (Step 1 above), so it
had to move to OCP's ELP instead (gate doc §2, §9). Engine: `16292` loss cost `0.24` (2026) →
ELP `0.162` (2027) in RI, NH and MN.

---

## Supporting lookups

| Table | Used for | Countrywide rows | State rows (as of today) |
|---|---|---|---|
| `RailroadELP` | Rating-basis selector, string value `"Industry"` in all rows; copied to the classification by `SetRailroadELP` and read by `SetBaseELPRR`'s 40014 branch (pre-2027 only) | 0 | 51/51 · 204 |
| `BaseELPRR` | ELP by (State, ClassCode, trains/day); the table excludes 40014 | 0 | 51/51 · exactly 18 each (918 total) at both 2026-10-02 and 2027-04-01 (2027 values halved) |
| `ILFRailroad` | Increased Limits Factor, Rule 56.B.7, keyed (State, ClassCode, each-occurrence limit, aggregate limit) | 0 | 51/51 · 1,836 |
| `RailroadHomogeneityIndex` | Written to the classification by `GeneralLiabilityClassificationRules.SetRailroadHomogeneityIndex`; no premium effect | 0 | 51/51 · 969 |
| `OwnersContractorsLossCost` | Read by Step 1 (`LookupOwnersContractorsLossCost`, hardcoded class `16292`) — OCP's table, not Railroad's own | 0 | 51/51 · 563 as of 2026-10-02 → 5/51 · 55 as of 2027-04-01 (CA, GA, NJ, NY, WA, which still run this chain) |
| `OwnersContractorsELP` | CW 2027 Step 1 (`LookupOwnersContractorsELP`, class `16292`) | 0 | 51/51 · 424 as of 2027-04-01 |
| `RailroadLossCost` | **Orphan.** Exists in all 10 CW editions (and in CW 20261001 V01 / 20270401 V02, re-checked 2026-10-02), 0 rows in every edition and every jurisdiction, referenced by **no rule anywhere in the corpus** (confirmed by scanning every rule file for the string) | 0 | 0/51 |
| `RailroadLCM` | Loss Cost Multiplier | 1 row, value `1` | 0/51 |
| `ConstructionOpsOwnerAdjmtFactor` | Step 3 factor | 1 row, value `1.5` | 0/51 |
| `WorkTrainsOrOtherRREquipmtRate` | Step 7–10 dollar rate | 1 row, value `56.8` | 0/51 |
| `CovForInjuriesToSuprvsrInspctrsOtherEmpsOfTheInsd` | Step 6 factor | 1 row, value `0.1` | 0/51 |
| `MinPremiumRR` | Minimum premium | 1 row, value `0` | 0/51 |
| `PolicyLimitsRailroadStatCode` | Statistical reporting | 9 rows | 0/51 |

`LookupPremOpsLCM` is present but **uncalled** in the Railroad rule file in all 10 editions — the
same dead lookup copy-pasted from the Liquor file (gate doc §5; re-confirmed in CW 20260101 V01 and
CW 20270401 V01: defined, no `RunRule` reference).

---

## State deviations

Only **two jurisdictions** (AK, NY) file any `GeneralLiabilityClassificationRailroadCoverage`
rule — the smallest state-deviation surface of any subline gated. Each overrides three rules,
two of which are boilerplate (`InitializeRuleSet`, `ErcProcess`). The one substantive override
countrywide is `SetMoldStatCode`, a statistical-coding rule that changes no premium (gate doc
§6). `BaseELPRR` itself has exactly 18 rows in all 51 jurisdictions with no state adding or
dropping a row. Re-confirmed 2026-10-02 against the state packages the engine resolves as of
2026-10-02 and 2027-04-01: AK and NY override only `SetMoldStatCode` (plus the two boilerplate rules).

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
is derived (150% × OCP class `16292`) rather than tabulated (gate doc §4). **Re-confirmed through the
engine 2026-10-02:** AK as of 2026-10-02 still resolves `GL_AK_20260801_V02` and returns exactly
these 18 values. AK as of 2027-04-01 resolves `GL_AK_20270401_V01`, whose 18 cells are each **exactly
half** of the above (40011: 1.44, 2.4, 3.2, 4.16, 5.6, 6.96; 40012: 1.2, 2, 2.8, 3.6, 4.8, 6;
40013: 2.4, 3.84, 5.2, 6.8, 9.2, 11.6) — the 2020 ELP Supplement no longer describes the 2027 table.

No ISO oracle exists for an end-to-end Railroad premium: the golden case carries Railroad with
`CoverageOnPolicyIndicator = 0` / `Premium = 0.0`, confirming only the entry gate
(gate doc §8). The engine now rates ISO's own Railroad STC submissions end to end at both editions
(worked numbers in the Quick references below); those confirm the engine executes ISO's rules as
written, not that the premiums match ISO.

---

## Quick reference — end-to-end, class 40011/40012 (no mixed hazard, single-hazard project)

```
ConstructionOpsOwnerFactor = LookupOwnersContractorsLossCost(State|CW, "16292")       # OCP table (ELP at CW 2027)
LCM                        = LookupRailroadLCM                                        # CW: 1
BaseELPRR         = LookupBaseELPRR(State, ClassCode, NumPassgrFreightTrains)         # banded, 18-row table
ILF               = LookupILFRailroad(State, ClassCode, EachOccLimit, AggLimit)
AdjustedBaseELPRR = round(BaseELPRR x LCM, 3)
Mods              = ExperienceRatingModificationFactor x ExpenseModification x ScheduleRatingModificationFactor
FinalRate         = round(AdjustedBaseELPRR x ILF x Mods, 3)

TotPremium        = round(FinalRate x TotalCost / 1000, 0)
SuprvsrPremium    = round(TotPremium x 0.1, 0)                         40011, supervisors Included
                  | round(TotPremium40011 x 0.1, 0)                    40012, supervisors Included, where
                      TotPremium40011 = round(FinalRate40011 x TotalCost / 1000, 0)
                      FinalRate40011  = round(LookupBaseELPRR(State, "40011", trains) x ILF x Mods, 3)
                  | 0
Premium           = TotPremium + SuprvsrPremium                        (Subline = "Railroad"; no work-trains charge)
                    # minimum premium: policy-level top-up, MinPremiumRR = 0 today

# Engine, RI@2026-10-02 (GL_RI_20260301_V02 over GL_CW_20260101_V01), class 40012, 5-or-less trains,
#   exposure 150,000: BaseELPRR 2.4 → 2.400; ILF 1.96 → FinalRate round(4.704, 3) = 4.704
#   Premium = round(4.704 x 150, 0) = 706        (RI@2027-04-01: BaseELPRR 1.2 → FinalRate 2.352 → 353)
```

## Quick reference — end-to-end, class 40011 mixed-hazard project

```
EstdContractCostWORRHzd > 0   -->  project is partly clear of the tracks

WOHzd   = round(EstdContractCostWORRHzd / TotalCost, 8)
WithHzd = round((TotalCost - EstdContractCostWORRHzd) / TotalCost, 8)

# No-hazard portion, rated on the class-40014 basis:
BaseELPRR400065orLess = round(ConstructionOpsOwnerFactor x 1.5, 3)
BaseELPRR40006        = round(BaseELPRR400065orLess x LCM, 3)
PriorToFinalRate40006 = round(BaseELPRR40006 x ILF40014 x WOHzd, 3)

# Hazard portion, on the class's own basis:
AdjustedBaseELPRR           = round(LookupBaseELPRR(State, "40011", trains) x LCM, 3)
PriorToFinalRateMixedHazard = round(AdjustedBaseELPRR x ILF x WithHzd, 3)

FinalRate = round((PriorToFinalRateMixedHazard + PriorToFinalRate40006) x Mods, 3)
Premium   = round(FinalRate x TotalCost / 1000, 0) + supervisors add-on as above

# Engine, RI@2026-10-02, exposure 15,000, WORRHzd 10, 5-or-less trains:
#   WOHzd 0.00066667, WithHzd 0.99933333; BaseELPRR 2.88; ILF 1.96, ILF40014 1.68
#   PriorToFinalRateMixedHazard = round(2.880 x 1.96 x 0.99933333, 3) = 5.641
#   PriorToFinalRate40006       = round(0.360 x 1.68 x 0.00066667, 3) = 0.000
#   FinalRate 5.641 → Premium = round(5.641 x 15, 0) = 85
# CW 2027 (RI@2027-04-01) folds this into one rounding:
#   FinalRate = round((1.440 x 1.96 x 0.99933333 + 0.243 x 1.68 x 0.00066667) x Mods, 3) = 2.821 → 42
```

## Quick reference — end-to-end, class 40013 (highway projects)

```
EstimatedContractCostRatio = submitted ratio (copied; ISO validates it is present)   # Procedure 5.E.2.b
BaseELPRR         = LookupBaseELPRR(State, "40013", NumPassgrFreightTrains)
AdjustedBaseELPRR = round(BaseELPRR x EstimatedContractCostRatio x LCM, 3)
FinalRate         = round(AdjustedBaseELPRR x ILF x Mods, 3)
WorkTrainsPremium = round(round(round(56.8 x LCM, 3) x ILF, 3) x TotalCostWorkTrainsOrOtherRREquipmtAssigned / 1000, 0)
Premium           = round(FinalRate x TotalCost / 1000, 0) + WorkTrainsPremium
                    (no supervisors/inspectors add-on for 40013)

# Engine, MN@2026-10-02 (GL_MN_20260701_V01 over GL_CW_20260101_V01), 6-20 trains, ratio 0.5,
#   exposure 100,000, work trains 2,000: BaseELPRR 7.68 → Adjusted 3.840; ILF 1.96 → FinalRate 7.526
#   Premium = round(7.526 x 100, 0) + round(111.328 x 2, 0) = 753 + 223 = 976
# MN@2027-04-01 (over CW 20270401 V02): BaseELPRR 3.84; FinalRate = round(3.840 x 0.5 x 1.96, 3) = 3.763
#   Premium = 376 (work trains withdrawn)
```

## Quick reference — end-to-end, class 40014 (no railroad-hazard exposure)

```
BaseELPRR = round(1.5 x OwnersContractorsLossCost(16292), 3)     # derived in SetBaseELPRR, not tabulated;
                                                                 # requires RailroadELP = "Industry" pre-2027
ILF       = LookupILFRailroad(State, "40014", …)                 # same cell as ILF40014
FinalRate = round(round(BaseELPRR x LCM, 3) x ILF x Mods, 3)
Premium   = round(FinalRate x TotalCost / 1000, 0)
          + round(that x 0.1, 0)                                 # supervisors Included

# Engine, NH@2026-10-02 (GL_NH_20260601_V01 over GL_CW_20260101_V01), exposure 1,500,000:
#   BaseELPRR round(1.5 x 0.24, 3) = 0.360; ILF 1.68 → FinalRate round(0.6048, 3) = 0.605
#   Premium = round(0.605 x 1,500, 0) = 908;  with supervisors Included: 908 + 91 = 999
# NH@2027-04-01: ConstructionOpsOwnerFactor = OCP ELP(16292) 0.162 → BaseELPRR 0.243 → FinalRate 0.408 → 612
```

## Engine behaviours that apply to Railroad

- **Edition is a variable** (A3): the effective date picks the parent per jurisdiction (edition note
  at the top); `package_version` pins one. 2027-04-01 is not a single cliff for all 51 states.
- **CW 2027 `$1` floor**: `SetPremium` writes `Premium = 1.0` whenever the rounded premium is `0` —
  with no exposure test, unlike OCP and Liquor. RI@2027-04-01, class 40011, exposure 100:
  `FinalRate 0.408 x 0.1 = 0.04 → 0 → Premium 1`; an unknown class code also lands on `1`.
- **OI-94 does not cover Railroad**: the chain writes no `*LossCost` node, so a missing
  `OwnersContractorsLossCost`/`ELP` row for `16292` or a missing `BaseELPRR` row reads as `0`
  (or `$1` at CW 2027) rather than refusing.
- **Referrals**: R29 cannot fire (no Company selector, no message branch); R03 / R14 / R16 do not
  touch Railroad values. In practice `underwriting` mode raises nothing on a Railroad risk.
