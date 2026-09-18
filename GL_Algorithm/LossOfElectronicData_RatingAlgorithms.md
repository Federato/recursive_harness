# Loss Of Electronic Data Coverage (CG 04 37 / CG 04 71 / CG 04 95) - Rating Algorithms

**Source ERC package:** countrywide `GL CW 20270401 V01` (`GeneralLiabilityClassificationRules`,
`GeneralLiabilityRules`, and the two LoED coverage-group rule files), cross-checked live/unmodified
against **TX** (`GL_TX 20270401 V01`) and **IL** (`GL_IL 20270401 V05`) -- both file no override
rule file for this coverage and run CW's chain as-is.
**Line:** General Liability (GL), no independent ISO subline code -- rides Premises/Operations
(334) and Products/Completed Operations (336) as dual hosts, one full rating chain per host.
**Manual anchor:** Rule 40 ("Cyber Incident Liability And Loss Of Electronic Data Coverage"),
CW 2027 edition, `Agentic/iso-circular-expert/text/rules/GL-MU-2027-RU-001-C.txt`, lines 3615-4051
(LoED specifically: lines 3656-3768).
**Supersedes, for LoED specifically:** the LoED sections of `ProductWithdrawalCyber_RatingAlgorithms.md`
/ `_ERC_Tables.md` (from `GATE-365-WITHDRAWAL-LOED-CYBER.md`), which left the exact rule-file names,
the literal final-rate/premium formula, and the ILF/deductible table identity unresolved. All three
are resolved below from direct ERC XML tracing. Cyber Incident Liability (Rule 40's sibling
coverage) is unaffected and still lives only in the combined document -- it was not re-derived here.
**Documented:** 2026-09-02.

Loss Of Electronic Data is rated **twice per risk** -- once hosted on Premises/Operations, once on
Products/Completed Operations -- via two structurally identical classification-level coverage
groups that each read their host's own already-computed rate and exposure. This is a genuine
cross-coverage (E18) dependency, the same shape [[Stop Gap|StopGap_RatingAlgorithms.md]] has with
Premises/Operations, except LoED borrows from *either* host depending on which classification is
being rated, not from one fixed host.

---

## Master orchestration

```
GeneralLiabilityClassificationRules.Rule.xml (CW 20270401 V01):
    InitializeRuleSet (lines 155-177): auto-vivifies one
        GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverage       row, and one
        GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverage row,
        per classification -- same auto-vivification pattern as Prem/Ops and Prod/CompOps
        themselves (matches manual step "a. Determine the applicable classification(s). Use
        the same classifications which apply to Premises/Operations and Products/Completed
        Operations risks.")
    CalculateTotalPremium (244-248) / ErcProcess (5805-5809):
        Locate -> RunRule ... CalculateTotalPremium / ErcProcess on each of the two groups

GeneralLiabilityRules.Rule.xml (CW 20270401 V01):
    lines 1276-1293 / 2612-2619 / 25516-25517: a policy-level singleton,
        GeneralLiabilityLossOfElectronicDataPremiumToReachMinCoverage,
        auto-located once per policy, wired into CalculateTotalPremium like every other
        policy-level minimum-premium topper in this corpus
    lines 20965-21271: guard/message rules (DoMessagePleaseAttachLossOfElectronicData,
        DoMessagePleaseAttachCyberIncidentLiabLossOfElectronicData,
        DoMessageRemoveCyberIncidentLiabOrLossOfElectronicData,
        DoMessageOnlyOneCyberIncidentLiabOrLossOfElectronicData) enforce endorsement/flag
        consistency against the submission field LossOfElectronicDataCoverageApplies

Each classification-level host group's own dispatcher:
    ErcSetRatesAndFactors:
        SetLossOfElectronicDataLimit -> SetILF -> SetDeductibleFactor -> SetFinalILF
        -> SetAdjustedBaseRate -> SetHazardGrade -> SetLossOfElectronicDataFactor
    ErcRate:
        SetFinalRate -> SetPremium -> SetPremiumIndicator
    ErcRunPostUnderwritingLogic:
        DoMessageILF                 <- the refer-to-company mechanism, Step 2 below
    ErcSetStatisticalCodes:
        SetLimitStatCode
```

~22 named `Set*`/`Lookup*` rules per host, from `GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverageRules.Rule.xml`
(1,470 lines) and the structurally identical `...ProdsCompldOpsCoverageRules.Rule.xml`
(1,294 lines), confirmed the same shape with `PremOps` -> `ProdsCompldOps` substitutions
throughout (`SetDeductibleFactor` at line 445; `SetFinalRate`/`SetPremium` at 746-873 in the
Prod/CompOps file).

---

## File map

| Piece | File | Rules |
|---|---|---|
| LoED Prem/Ops host coverage | `GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverageRules.Rule.xml` | ~22 named rules |
| LoED Prod/CompOps host coverage | `GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverageRules.Rule.xml` | ~22 named rules, identical shape |
| Policy-level minimum-premium topper | `GeneralLiabilityLossOfElectronicDataPremiumToReachMinCoverageRules.Rule.xml` (220 lines) | `SetMinPremium`, `SetTotalLossOfElectronicDataPremium`, `SetPremium`, `SetPremiumIndicator` |
| Top-level wiring | `GeneralLiabilityRules.Rule.xml`, `GeneralLiabilityClassificationRules.Rule.xml` | see orchestration above |
| Manual text | `Agentic/iso-circular-expert/text/rules/GL-MU-2027-RU-001-C.txt`, Rule 40, lines 3615-4051 (LoED: 3656-3768) | -- |

All ERC paths above are under `C:\Projects\ISO_ERC_Files\General_Liability\countrywide\GL CW 20270401 V01\Rules\`,
confirmed unmodified (no override file at all) in **TX** (`GL_TX 20270401 V01`, declares CW V01)
and **IL** (`GL_IL 20270401 V05`, declares CW V02) -- the mirror image of California, which files
its own copy of both coverage-group rule files with `SetCoverageOnPolicyIndicator` hard-set to `0`
(`ProductWithdrawalCyber_RatingAlgorithms.md`, "Gate -- coverage on policy").

---

## Rate build-up steps (per classification, per host -- identical shape, host tables/fields swapped)

### Step 1 -- Limit
`SetLossOfElectronicDataLimit` (lines 79-184) copies `LossOfElectronicDataLimit` from whichever
attached endorsement's schedule table exists: CG 04 37's table, CG 04 71's table, or the CG 04 95
combined-endorsement table.

### Step 2 -- Increased Limits Factor (borrows the host's own ILF table)
`SetILF` (185-431):

```
if (LossOfElectronicDataLimit, GeneralAggregateLimit) falls in one of 14 filed
   "no factor exists" combinations (e.g. Limit = $1,000,000 and Aggregate > $10,000,000):
    ILF = ILFOverride                     <- submission-supplied; the refer-to-company branch
elif GeneralAggregateLimit and FinalPremOpsIncrdLimitTableAssignment and Limit are all present:
    ILF = LookupILFPremOps(FinalPremOpsIncrdLimitTableAssignmentInt,
                            LossOfElectronicDataLimit, GeneralAggregateLimit)
else:
    ILF = 0.0
```

`LookupILFPremOps` (1379-1401) reads matrix **`ILFPremOps`** -- **the same ILF table
Premises/Operations' own subline uses** (Rule 23-family), keyed
`(StateCode, IncrdLimitTableAssignment, EachOccurrenceLimit, GeneralAggregateLimit)`,
state-first then CW fallback, using the Loss Of Electronic Data Limit *as* the Each Occurrence
Limit -- exactly as the manual states (B.1.d). **LoED has no ILF table of its own; there is no
"LoED-specific ILF table" to resolve, contrary to what the combined gate left open.** The
Prod/CompOps-hosted sibling calls `LookupILFProds` against matrix `ILFProds`, that host's own
table, same shape.

### Step 3 -- Deductible factor (borrows the host's own computed value)
`SetDeductibleFactor` (433-498) copies `../GeneralLiabilityClassificationPremOpsCoverage/DeductibleFactor`
(or `PremOpsPDDeductibleFactor` for PD-only deductibles) -- again the host's own already-computed
value, not an independent LoED deductible table.

### Step 4 -- Final ILF
`SetFinalILF` (499-552):

```
FinalILF = round(ILF - DeductibleFactor, 3)   if that is > 0
         = 0.0                                 otherwise    (clamped at 0, no negative floor needed)
```

### Step 5 -- Adjusted base rate (reads the host's computed values -- E18)
`SetAdjustedBaseRate` (553-812), branching on `SizeOfRiskRatingApplies`,
`PremOpsProdsCoverageForm == "Claims Made"`, and whether `PremOpsLossCost == 0`:

```
AdjustedBaseRate = round(
    (host PremOpsLossCost | host PremOpsELP)
  x host LCM
  [x host ClaimsMadeMultiplier]                  # only when Claims Made and Size-Of-Risk does not apply
  [x host PremOpsSizeOfRiskFinalRelativity]       # only when SizeOfRiskRatingApplies == "Yes"
  x FinalILF
, 4)
```

Every factor on the right except `FinalILF` is read directly from
`../GeneralLiabilityClassificationPremOpsCoverage/...` -- the sibling coverage group's **computed**
output, not a table. This confirms `GATE-365`'s E18 finding exactly.

### Step 6 -- Hazard grade
`SetHazardGrade` (813-843) -> `LookupHazardGrade(ClassCode)` reads matrix
**`LossOfElectronicDataPremOpsHazardGrade`** (Prod/CompOps host:
`LossOfElectronicDataProdsCompldOpsHazardGrade`). The table def carries
`MetaDataCode: BureauRuleNumber40F` and cites circulars `CircularLIGL2023089`,
`CircularLIGL2025210` -- directly tying the ERC table to manual Table 40.F. **1,163 rows** at
CW 2027 (both hazard-grade tables), state-first/CW-fallback; no state override found anywhere in
the 51-jurisdiction 2027 tree.

### Step 7 -- Coverage factor
`SetLossOfElectronicDataFactor` (844-921) selects, by which endorsement schedule is populated,
`LookupLossOfElectronicDataFactorCG0437` or `...CG0471`, reading matrix
`LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}`, keyed
`(StateCode, HazardGrade)`, 4 rows, CW-only in every state checked.

---

## Premium

### Step 8 -- Final rate
`SetFinalRate` (930-952 PremOps host / 746-768 ProdsCompldOps host):

```
FinalRate = round(
    AdjustedBaseRate x LossOfElectronicDataFactor
  x PackageModFactor x ExperienceRatingModificationFactor
  x ExpenseModification x ModToUse
, 4)
```

**This is the exact literal formula the combined gate left unresolved.** It is not Product
Withdrawal's shape: no `PremiumDiscountCharge` term, and the round is to **4** decimal places, not
3.

### Step 9 -- Premium
`SetPremium` (953-1057 PremOps host / 769-873 ProdsCompldOps host):

```
if premium base is one of the nine /1000 bases
   (Admissions, Area, Gallons, Gross Sales, Kilowatt-hours, Payroll, Total Cost,
    Total Operating Expenses, Vehicles):
    calculatedPremium = round(FinalRate x (CovExposure / 1000), 0)
else:
    calculatedPremium = round(FinalRate x CovExposure, 0)

Premium = 1.0                 if calculatedPremium == 0 and CovExposure > 0    # $1 minimum
        = calculatedPremium   otherwise
```

`SetPremiumIndicator` (1058-1079): `PremiumIndicator = 1` iff `Premium != 0`.

Manual anchor for Steps 8-9: Rule 40.B.1.f-i (adjust rate by ILF/deductible, multiply by
Table 40.C/D factor, multiply by exposure, combine across sublines).

### Refer-to-company, concretely implemented
`SetILF`'s first branch (Step 2) fires when the (Limit, Aggregate) pair falls into one of 14 filed
"refer" combinations -- the manual's Rule 56 cross-reference reading "Refer to the state
exceptions." In that branch `ILF = ILFOverride`, a submission-supplied field, not a computed
lookup. `DoMessageILF` (1085-1281) then fires a real validation error -- *"The ILF for The Loss of
Electronic data Limit and the General Aggregate Limit is refer to company, please enter the ILF
override"* -- only when that same 14-band condition holds and `ILFOverride == 0`. Same class of
mechanism as [[Stop Gap|StopGap_RatingAlgorithms.md]]'s `ManualPremium`: refer-to-company resolves
to a required submission field plus a guard, not an unimplemented gap.

### Minimum premium -- manual says refer, ERC computes it (currently a no-op)
Manual text (B.1.j): *"Determine the application of any minimum premium. Refer to company for
minimum premium."* ERC nonetheless computes a real minimum-premium top-up mechanically, via the
policy-level `GeneralLiabilityLossOfElectronicDataPremiumToReachMinCoverageRules.Rule.xml`:

```
TotalLossOfElectronicDataPremium = sum over every classification x location of
    (PremOps LoED Premium if != 0) + (ProdsCompldOps LoED Premium if != 0)

Premium (topper) = MinPremium - TotalLossOfElectronicDataPremium   if MinPremium > Total
                  = 0.0                                             otherwise
```

`LookupLossOfElectronicDataMinPremium` reads matrix `LossOfElectronicDataMinPremium`, **1 row,
`('CW', 'Y', 0)`** -- filed at exactly **$0** at CW, and no state in the entire 2027 corpus
overrides it. **The mechanism is real and always reachable, but a structural no-op today** because
the filed value is $0 everywhere. If any state ever files a nonzero `MinPremium`, the topper would
fire automatically rather than referring -- flagged, not silently reconciled with the manual's
refer-to-company text.

---

## State deviations

**Rate tables and hazard grades: zero deviation.** All eight LoED rate tables
(`LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}`, both hazard-grade tables,
`LossOfElectronicDataMinPremium`) were checked for a state-filed copy across all 51 jurisdictions'
newest 2027-04-01 packages -- none exists. Every state, including TX and IL, resolves these eight
tables to CW unmodified. `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` line 59 records "Rule
40: not deviated as '40'" for state-deviation-count purposes -- confirmed directly.

**Rule-body deviation: a real, algorithmic 8-state surface.** **IN, MO, MT, ND, NH, OK, TN, UT**
each file their own override copy of `GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverageRules.Rule.xml`,
but only 4-5 rules deep (`InitializeRuleSet`, `SetILF`, `SetLimitStatCode`, `ErcProcess`, and ND
additionally `DoMessageILF`) -- everything else falls through to CW. The deviation: these states
add a `GovernmentalSubdivision` branch CW's own `SetILF` does not have -- when
`GovernmentalSubdivision == "Yes"`, the aggregate limit used to key the ILF lookup switches from
`GeneralAggregateLimit` to a separate field, `GeneralAggregateLimitGovernmentalSubdivision`, and
`SetLimitStatCode` mirrors the same branch for the stat-code lookup. Read directly from
`GL_IN 20270401 V04`'s copy, lines 245-301 and 371-416; the other seven states carry
byte-length-matched (not individually re-diffed) copies of the same file. Not resolved in source
docs: whether the 7 siblings are byte-identical to IN's, and whether a manual provision (e.g. a
general Rule 23/25 governmental-risk carve-out) documents this branch anywhere outside Rule 40's
own text -- none was located there.

No state-specific Rules-notice text deviation for Rule 40/LoED was searched exhaustively beyond
the CW notice, given zero rate-table or manual-anchor deviation was found anywhere else that would
motivate the search.

---

## Supporting lookups

| Rule | Matrix | Keys | Notes |
|---|---|---|---|
| `LookupILFPremOps` | `ILFPremOps` | `StateCode`, `IncrdLimitTableAssignment`, `EachOccurrenceLimit`, `GeneralAggregateLimit` | Prem/Ops' own host ILF table (Rule 23-family), reused directly -- not LoED-specific |
| `LookupILFProds` | `ILFProds` | same shape, Prod/CompOps assignment | Prod/CompOps' own host ILF table |
| `LookupHazardGrade` | `LossOfElectronicData{PremOps,ProdsCompldOps}HazardGrade` | `StateCode`, `ClassCode` | 1,163 rows CW 2027; ties to manual Table 40.F via `BureauRuleNumber40F` metadata |
| `LookupLossOfElectronicDataFactorCG0437` / `CG0471` | `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}` | `StateCode`, `HazardGrade` | 4 rows, CW-only in every state checked |
| `LookupLossOfElectronicDataMinPremium` | `LossOfElectronicDataMinPremium` | `StateCode`, constant `'Y'` | 1 row, CW = $0, no state override |
| (domain) | `DomainLossOfElectronicDataLimit` | -- | 13 rows, $25,000-$10,000,000 -- exactly the band boundaries `SetILF`'s refer-condition tests against |

---

## Quick reference -- end-to-end, Loss Of Electronic Data (either host)

```
Limit          = LossOfElectronicDataLimit                          [from attached CG 04 37 / CG 04 71 / CG 04 95 schedule]

ILF            = ILFOverride                                        if (Limit, GenAggLimit) hits one of 14 filed "refer" bands
               | LookupILFPremOps|Prods(IncrdLimitTableAssignment, Limit, GenAggLimit)   [host's own ILF table]
               | 0.0

DedFactor      = host's PremOpsPDDeductibleFactor / DeductibleFactor  [host's own value, not an independent table]

FinalILF       = round(ILF - DedFactor, 3)  if > 0  else 0.0

AdjustedBaseRate = round(
    (host LossCost | host ELP) x host LCM
    [x host ClaimsMadeMultiplier] [x host SizeOfRiskFinalRelativity]
    x FinalILF
  , 4)

HazardGrade    = LookupHazardGrade(ClassCode)   -> LossOfElectronicData{PremOps,ProdsCompldOps}HazardGrade
                 [1,163 rows CW 2027; not resolved in source docs whether an unlisted class code
                  falls through to a coded "1" default the way the manual's prose implies, or to null]

LoEDFactor     = LookupLossOfElectronicDataFactorCG0437|CG0471(HazardGrade)   [4 rows CW, keyed by attached form]

FinalRate      = round(AdjustedBaseRate x LoEDFactor x PackageModFactor
                       x ExperienceRatingModificationFactor x ExpenseModification x ModToUse, 4)

Premium        = round(FinalRate x Exposure/1000, 0)   [9 filed /1000 bases]
               | round(FinalRate x Exposure, 0)         [otherwise]
               | 1.0  if that rounds to 0 and Exposure > 0                  [$1 minimum]

PolicyMinPremiumTopper = max(0, MinPremium[CW=$0] - sum(all PremOps+ProdsCompldOps LoED Premiums))
                          -- structural no-op today; filed value is $0 in all 51 jurisdictions
```

Rounding: `AdjustedBaseRate` and `FinalRate` to 4 decimal places; `Premium` to 0.

---

## Findings

- **The combined gate's three open items are resolved.** Exact rule-file names, the literal
  `SetFinalRate`/`SetPremium` arithmetic, and the ILF/deductible table identity are all confirmed
  from live ERC XML in two states (TX, IL), neither of which overrides this coverage.
- **LoED has no ILF or deductible table of its own** -- it borrows its host subline's (Prem/Ops or
  Prod/CompOps) own already-filed ILF table and already-computed deductible factor outright, using
  the LoED limit as the Each Occurrence Limit substitute. This is a stronger table-borrow than
  Stop Gap's, which borrows Prem/Ops' ILF table but keeps its own rate factor.
  ([[Stop Gap|StopGap_RatingAlgorithms.md]] Step 1.)
  Compare to [[UnmannedAircraft_RatingAlgorithms.md]] Master orchestration, which borrows tables
  but not computed values.
- **Manual/ERC agree exactly** on all four rate-factor tables (Table 40.C/40.D vs
  `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}`) across two live states, no
  override anywhere.
- **Manual says refer-to-company for minimum premium; ERC computes a real topper that is a
  structural no-op** because the filed CW value is $0 everywhere in the 2027 corpus. ERC stands as
  the mechanism of record.
- **A genuine 8-state deviation** (IN, MO, MT, ND, NH, OK, TN, UT) adds a `GovernmentalSubdivision`
  branch to the ILF lookup, absent from CW and from any Rule-40 manual text located -- worth a
  person's confirmation before treating as settled.
- **Correction to an earlier assumption:** `ElectronicDataLiabilityClassCode` is not a LoED table
  -- it belongs to the unrelated, fully refer-to-company Rule 42 "Electronic Data Liability"
  coverage, has zero rows and zero readers in the CW rule tree, and should not appear in this
  coverage's table list.
- **Open, not chased further:** whether a class code absent from the hazard-grade table falls
  through to `HazardGrade = "1"` (as the manual's prose implies) or to null / a `LossOfElectronicDataFactor`
  of 0 -- resolving this needs either a live `Kernel().rate(...)` test with an unlisted class code,
  or a person's confirmation.
- `gl_engine` code: zero hits for `LossOfElectronicData` or `LoED` -- consistent with this
  project's architecture (jurisdictional/coverage content lives in ERC, not Python). Same finding
  as [[Stop Gap|StopGap_RatingAlgorithms.md]] Findings.
