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
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — offline `Kernel().rate` runs with CG 04 37 / CG 04 95 schedule records added to the engine base submission at TX@20270401, IL@20270401, IN@20270401, TX@20261002, IL@20261002, NY@20261002 and CA (both dates), plus rule-by-rule XML diffs across CW 20231201 V03 / 20260101 V01 / 20261001 V01 / 20270401 V01 / 20270401 V02.
**Edition scope (A3 -- the effective date is a variable):** both LoED coverage groups exist from CW
**20231201** onward -- they are not new in 2027. Their rule bodies are identical across CW 20231201 V03,
20260101 V01 and 20261001 V01; CW 20270401 V01 changes `SetCoverageOnPolicyIndicator`, `SetILF`,
`SetPremium` (both hosts) and `DoMessageILF` (Prem/Ops host) -- see "Edition differences" below.
**CW 20270401 V02 changes neither LoED coverage file.** Which edition rates is the resolver's call:
as of 2026-10-02 IL/NY and 44 others resolve to CW 20260101 V01, TX/NJ/VT to CW 20231201 V03, OK to
CW 20261001 V01, CA to CW 20231201 V02; at 2027-04-01 IL and 37 others resolve to CW 20270401 V02,
TX and 7 others to V01. `package_version` pins an edition.

Loss Of Electronic Data is rated **twice per risk** -- once hosted on Premises/Operations, once on
Products/Completed Operations -- via two structurally parallel classification-level coverage
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

Each classification-level host group's gate (SetCoverageOnPolicyIndicator, CW 2027):
    Prem/Ops host = 1 iff Subline == "Premises/Operations and Products/Completed Operations"
                    AND one of the three LoED schedule records exists (CG 04 37 / CG 04 71 / CG 04 95)
                    AND LossOfElectronicDataCoverageApplies == "Yes"
    Prod/CompOps  = 1 iff ((Subline == combined AND ProdsCompldOpsExclusion != "Yes")
                           OR Subline == "Products/Completed Operations")
                    AND the same schedule + flag tests
    CW 2023/2026: no Subline test in the gate (the Prem/Ops host's SetILF/SetPremium instead accept
    Subline "Premises/Operations" or the combined subline).
    ErcProcess runs the chain only when the indicator is 1; otherwise Premium = 0.0.

Each classification-level host group's own dispatcher:
    ErcSetRatesAndFactors:
        SetLossOfElectronicDataLimit -> SetILF -> SetDeductibleFactor -> SetFinalILF
        -> SetAdjustedBaseRate -> SetHazardGrade -> SetLossOfElectronicDataFactor
    ErcRate:
        SetFinalRate -> SetPremium -> SetPremiumIndicator
    ErcRunPostUnderwritingLogic:
        DoMessageILF                 <- the refer-to-company message, Step 2 below
    ErcSetStatisticalCodes:
        SetLimitStatCode             <- LookupCyberCoverageLimitStatCode (table CyberCoverageLimitStatCode)

    Engine-observed order (trace, TX@20270401): the Prem/Ops host runs
    ErcSetRatesAndFactors -> ErcRate -> ErcRunPostUnderwritingLogic -> ErcSetStatisticalCodes;
    the Prod/CompOps host's ErcProcess runs ErcRunPostUnderwritingLogic (DoMessageILF) FIRST,
    then the rating steps.
```

25 named rules per host (`InitializeRuleSet` through the `Lookup*` helpers), from
`GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverageRules.Rule.xml`
(1,470 lines) and the parallel `...ProdsCompldOpsCoverageRules.Rule.xml` (1,294 lines), the same
rule names with `PremOps` -> `ProdsCompldOps` substitutions (`SetDeductibleFactor` at line 445;
`SetFinalRate`/`SetPremium` at 746-873 in the Prod/CompOps file). **The two hosts are not
step-for-step identical:** `SetAdjustedBaseRate` reads different host values (Step 5), and the
ILF lookup keys on different host fields (Step 2).

---

## File map

| Piece | File | Rules |
|---|---|---|
| LoED Prem/Ops host coverage | `GeneralLiabilityClassificationLossOfElectronicDataPremOpsCoverageRules.Rule.xml` | 25 named rules |
| LoED Prod/CompOps host coverage | `GeneralLiabilityClassificationLossOfElectronicDataProdsCompldOpsCoverageRules.Rule.xml` | 25 named rules, same names |
| Policy-level minimum-premium topper | `GeneralLiabilityLossOfElectronicDataPremiumToReachMinCoverageRules.Rule.xml` (220 lines) | `SetMinPremium`, `SetTotalLossOfElectronicDataPremium`, `SetPremium`, `SetPremiumIndicator` |
| Endorsement schedules (input records under `GeneralLiability`) | CG 04 37 = `GeneralLiabilityLossOfElectronicDataFromPhysicalInjuryToTangiblePropLiabCovSubToCyberIncidentExcl`; CG 04 71 = `GeneralLiabilityLossOfElectronicDataPhysicalInjuryToTangiblePropLiabCovSubToCyberIncidentExclDeletionOfBIExcptn`; CG 04 95 = `GeneralLiabilityCyberIncidentLiabCovLossOfEDLCovSubjectToLossOfElectronicDataCyberIncidentOccAggLimits` | each carries `LossOfElectronicDataLimit` (CG 04 95 also the Cyber limits) |
| Top-level wiring | `GeneralLiabilityRules.Rule.xml`, `GeneralLiabilityClassificationRules.Rule.xml` | see orchestration above |
| Manual text | `Agentic/iso-circular-expert/text/rules/GL-MU-2027-RU-001-C.txt`, Rule 40, lines 3615-4051 (LoED: 3656-3768) | -- |

All ERC paths above are under `C:\Projects\ISO_ERC_Files\General_Liability\countrywide\GL CW 20270401 V01\Rules\`,
confirmed unmodified (no override file at all) in **TX** (`GL_TX 20270401 V01`, declares CW V01)
and **IL** (`GL_IL 20270401 V05`, declares CW V02) -- the mirror image of California, which files
its own copy of both coverage-group rule files with `SetCoverageOnPolicyIndicator` hard-set to `0`
(`ProductWithdrawalCyber_RatingAlgorithms.md`, "Gate -- coverage on policy"; engine-confirmed at
CA@20261002 and CA@20270401, both `GL_CA_20241101_V01` over CW 20231201 V02 -- every LoED/Cyber
indicator writes 0).

---

## Rate build-up steps (per classification, per host -- parallel shape, host tables/fields swapped)

### Step 1 -- Limit
`SetLossOfElectronicDataLimit` (lines 79-184) copies `LossOfElectronicDataLimit` from whichever
attached endorsement's schedule record exists, in this order: CG 04 37's record, CG 04 71's record,
then the CG 04 95 combined Cyber/LoED record (names in the File map); otherwise `""`.

### Step 2 -- Increased Limits Factor (borrows the host's own ILF table)
`SetILF` (185-431):

```
if (LossOfElectronicDataLimit, aggregate) falls in one of 13 filed "no factor exists" bands:
       25,000 & agg > 300,000      50,000 & agg > 600,000      100,000 & agg > 1,000,000
      200,000 & agg > 2,000,000   300,000 & agg > 3,000,000    500,000 & agg > 5,000,000
    1,000,000 / 1,500,000 / 2,000,000 / 3,000,000 / 4,000,000 / 5,000,000 & agg > 10,000,000
   10,000,000 & agg > 20,000,000
    ILF = ILFOverride                     <- submission-supplied; the refer-to-company branch
elif aggregate, host IncrdLimitTableAssignment and Limit are all present:
    ILF = LookupILFPremOps(FinalPremOpsIncrdLimitTableAssignmentInt,
                            LossOfElectronicDataLimit, GeneralAggregateLimit)
else:
    ILF = 0.0
```

The aggregate tested is `GeneralAggregateLimitNumeric` on the Prem/Ops host (only when Subline is
the combined Prem/Ops+Prod/CompOps subline; otherwise 0, so no band fires) and
`ProdsCompldOpsAggregateLimitNumeric` on the Prod/CompOps host.

`LookupILFPremOps` (1379-1401) reads matrix **`ILFPremOps`** -- **the same ILF table
Premises/Operations' own subline uses** (Rule 23-family), keyed
`(StateCode, IncrdLimitTableAssignment, EachOccurrenceLimit, GeneralAggregateLimit)`,
state-first then CW fallback, using the Loss Of Electronic Data Limit *as* the Each Occurrence
Limit -- exactly as the manual states (B.1.d). **LoED has no ILF table of its own; there is no
"LoED-specific ILF table" to resolve, contrary to what the combined gate left open.** The
Prod/CompOps-hosted sibling calls `LookupILFProds` against matrix `ILFProds`, keyed on
`FinalProdsCompldOpsIncrdLimitTableAssignment` (a letter, e.g. `B`) and `ProdsCompldOpsAggregateLimit`.
Engine run, TX@20270401: `ILFPremOps ['TX', 3, '200,000', '2,000,000'] -> 1.28` and
`ILFProds ['TX', 'B', '200,000', '2,000,000'] -> 1.23` (both TX-filed rows).

**Edition branch -- the " CSL" suffix.** In CW 20231201/20260101/20261001 `SetILF` builds the key as
`Concat(LossOfElectronicDataLimit, " CSL")` and the aggregate key carries the payload's `"2,000,000 CSL"`
(engine run TX@20261002: `ILFPremOps ['TX', 3, '200,000 CSL', '2,000,000 CSL'] -> 1.28`). CW 2027
drops the concat and keys on the bare limit (OI-96/97; the engine's base payloads are renormalised
payload-side in `scripts/variants.py`, not by the rules).

### Step 3 -- Deductible factor (borrows the host's own computed value)
`SetDeductibleFactor` (433-498) writes field **`DedFactor`**:

```
DedFactor = host DeductibleFactor           if PremOpsBIPDDeductible != "No Deductible"
          = host PremOpsPDDeductibleFactor  elif PremOpsPDDeductible  != "No Deductible"
          = 0.0                             otherwise
```

(Prod/CompOps host: `ProdsCompldOpsBIPDDeductible` / `ProdsCompldOpsPDDeductible` and that host's
`DeductibleFactor` / `ProdsCompldOpsPDDeductibleFactor`.) Again the host's own already-computed value,
not an independent LoED deductible table.

### Step 4 -- Final ILF
`SetFinalILF` (499-552):

```
FinalILF = round(ILF - DedFactor, 3)   if that is > 0
         = 0.0                          otherwise    (clamped at 0)
```

### Step 5 -- Adjusted base rate (reads the host's computed values -- E18)
`SetAdjustedBaseRate`, Prem/Ops host (553-812), branching on `SizeOfRiskRatingApplies` (and
`PremOpsSizeOfRiskFinalRelativity` being non-null), `PremOpsProdsCoverageForm == "Claims Made"`, and
whether `PremOpsLossCost == 0`:

```
AdjustedBaseRate = round(
    (host PremOpsLossCost, or host PremOpsELP when PremOpsLossCost == 0)
  x host LCM
  [x host ClaimsMadeMultiplier]                  # only when Claims Made
  [x host PremOpsSizeOfRiskFinalRelativity]       # only when SizeOfRiskRatingApplies == "Yes" and the relativity is non-null
  x FinalILF
, 4)
```

Every factor on the right except `FinalILF` is read directly from
`../GeneralLiabilityClassificationPremOpsCoverage/...` -- the sibling coverage group's **computed**
output, not a table. This confirms `GATE-365`'s E18 finding exactly.

**The Prod/CompOps host is shorter** (565-620) -- it reads the host's finished `BaseRate`, which
already carries the loss cost/ELP and LCM, and has no Claims-Made branch:

```
AdjustedBaseRate = round(
    host ProdsCompldOps BaseRate
  [x host ProdsCompldOpsSizeOfRiskFinalRelativity]   # only when SizeOfRiskRatingApplies == "Yes"
  x FinalILF
, 4)
```

Engine run, TX@20270401: Prem/Ops `round(0.087 x 1 x 1.280, 4) = 0.1114`; Prod/CompOps
`round(0.82 x 1.230, 4) = 1.0086`.

### Step 6 -- Hazard grade
`SetHazardGrade` (813-843) -> `LookupHazardGrade(ClassCode)` reads matrix
**`LossOfElectronicDataPremOpsHazardGrade`** (Prod/CompOps host:
`LossOfElectronicDataProdsCompldOpsHazardGrade`). The table def carries
`MetaDataCode: BureauRuleNumber40F` and cites circulars `CircularLIGL2023089`,
`CircularLIGL2025210` -- directly tying the ERC table to manual Table 40.F. **1,163 rows** at
CW 2027 (both hazard-grade tables; **1,188** at CW 20231201/20260101/20261001), state-first/CW-fallback;
no state override found anywhere in the 51-jurisdiction 2027 tree. NY's 2024 packages carry header-only
(0-row) copies; the engine's state-then-CW lookup falls through to CW (NY@20261002:
`['NY','50017']` miss -> `['CW','50017'] -> '1'`).

### Step 7 -- Coverage factor
`SetLossOfElectronicDataFactor` (844-921) selects by which endorsement schedule exists:
CG 04 37 **or CG 04 95** -> `LookupLossOfElectronicDataFactorCG0437`; CG 04 71 ->
`...CG0471`, reading matrix `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}`,
keyed `(StateCode, HazardGrade)`, 4 rows, CW-only in every state checked. A blank `HazardGrade`
falls to the `Otherwise` branch, `LossOfElectronicDataFactor = 0.0`.

---

## Premium

### Step 8 -- Final rate
`SetFinalRate` (930-952 PremOps host / 746-768 ProdsCompldOps host), written only if `FinalRate`
is still null (a submission-supplied `FinalRate` wins):

```
FinalRate = round(
    AdjustedBaseRate x LossOfElectronicDataFactor
  x PackageModFactor x ExperienceRatingModificationFactor
  x ExpenseModification x ModToUse
, 4)
```

**This is the exact literal formula the combined gate left unresolved.** It is not Product
Withdrawal's shape: no `PremiumDiscountCharge` term, and the round is to **4** decimal places, not
3. With factors of 0.001-0.007 the 4-dp round is coarse: TX@20270401 Prem/Ops
`0.1114 x 0.001 = 0.0001114 -> 0.0001`.

### Step 9 -- Premium
`SetPremium` (953-1057 PremOps host / 769-873 ProdsCompldOps host), CW 2027:

```
(Prem/Ops host: computed only when Subline is the combined subline; otherwise 0)
if premium base is one of the nine /1000 bases
   (Admissions, Area, Gallons, Gross Sales, Kilowatt-hours, Payroll, Total Cost,
    Total Operating Expenses, Vehicles):
    calculatedPremium = round(FinalRate x (CovExposure / 1000), 0)
else:
    calculatedPremium = round(FinalRate x CovExposure, 0)

Premium = 1.0                 if calculatedPremium == 0 and CovExposure > 0    # $1 minimum
        = calculatedPremium   otherwise
```

**Edition branch.** CW 20231201/20260101/20261001 `SetPremium` has **no $1 minimum**, its /1000 list
carries `Passenger Days` instead of `Kilowatt-hours`, and the Prem/Ops host accepts Subline
"Premises/Operations" or the combined subline.

`SetPremiumIndicator` (1058-1079): `PremiumIndicator = 1` iff `Premium != 0`.

Manual anchor for Steps 8-9: Rule 40.B.1.f-i (adjust rate by ILF/deductible, multiply by
Table 40.C/D factor, multiply by exposure, combine across sublines).

### Refer-to-company, concretely implemented
`SetILF`'s first branch (Step 2) fires when the (Limit, Aggregate) pair falls into one of **13** filed
"refer" bands -- the manual's Rule 56 cross-reference reading "Refer to the state
exceptions." In that branch `ILF = ILFOverride`, a submission-supplied field, not a computed
lookup. `DoMessageILF` (1085-1281) then fires a real validation error -- *"The ILF for The Loss of
Electronic data Limit and the General Aggregate Limit is refer to company, please enter the ILF
override"* -- only when that same band condition holds and `ILFOverride == 0`. Same class of
mechanism as [[Stop Gap|StopGap_RatingAlgorithms.md]]'s `ManualPremium`: refer-to-company resolves
to a required submission field plus a guard, not an unimplemented gap.

**Engine behaviour.** A band hit without `ILFOverride` copies a null `ILF`, and the engine refuses to
coerce it: the rating stops **INCOMPLETE** (*"null reached arithmetic ... at Subtract"*, in
`SetFinalILF`) before `DoMessageILF` can run -- in both `strict-erc` and `underwriting` modes. **Since
2026-10-14 (OI-129, B-09) that stop is a named refusal** (`...Coverage.ILFOverride is required`, quoting ISO's
message). ISO's own service (IL@20270401, 2 calls) prices LoED $0 there, `FinalILF 0`, and returns that
message as an error; with the override it matches the engine exactly ($8,387). Note the bands bite at ordinary limits: a $100,000 LoED limit under a
standard $2,000,000 general aggregate is a refer (IL@20270401, reproduced). Supplying
`ILFOverride` on each host's coverage record rates normally (IL@20270401: `ILF = 1.1` / `1.05` copied).

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
overrides it. **The mechanism is real and computes in every edition (2023, 2026 and 2027 -- unlike
the 2027 Prem/Ops and Prod/CompOps toppers, it is not stubbed inert), but is a structural no-op
today** because the filed value is $0 everywhere. If any state ever files a nonzero `MinPremium`,
the topper would fire automatically rather than referring -- flagged, not silently reconciled with
the manual's refer-to-company text.

**Engine discrepancy in the total.** The engine writes `TotalLossOfElectronicDataPremium = 5` where the
two host premiums are 1 and 5 (TX@20270401, IL@20270401, IL@20261002, TX@20261002, IN@20270401 all
reproduce it): the ERC body is `Sum(ForEach(ForEach(If PremOps..., If ProdsCompldOps...)))`, and the
engine's `ForEach` yields only the **last** child's value per iteration, dropping the Prem/Ops term.
Harmless while `MinPremium` is $0; would under-state the total (and over-state the topper) if a state
filed a minimum. Recorded as an engine finding, not changed here.

---

## Edition differences (rule level)

| Rule | CW 20231201 V03 / 20260101 V01 / 20261001 V01 | CW 20270401 V01 = V02 |
|---|---|---|
| `SetCoverageOnPolicyIndicator` | schedule + `LossOfElectronicDataCoverageApplies` only | adds the Subline test (and `ProdsCompldOpsExclusion` on the Prod/CompOps host) |
| `SetILF` | key = `Limit + " CSL"`; Prem/Ops band test on Subline Prem/Ops or combined | key = bare limit; band test on the combined subline only |
| `SetPremium` | no $1 minimum; /1000 list incl. Passenger Days | $1 minimum; /1000 list incl. Kilowatt-hours |
| `DoMessageILF` (Prem/Ops) | -- | subline condition aligned with `SetILF` |
| topper `SetTotalLossOfElectronicDataPremium` | param renamed only | -- |

---

## State deviations

**Rate tables and hazard grades: zero deviation.** All eight LoED rate tables
(`LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}`, both hazard-grade tables,
`LossOfElectronicDataMinPremium`) were checked for a state-filed copy across all 51 jurisdictions'
newest 2027-04-01 packages -- none exists. Every state, including TX and IL, resolves these eight
tables to CW unmodified. `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` line 59 records "Rule
40: not deviated as '40'" for state-deviation-count purposes -- confirmed directly.

**Rule-body deviation: a real, algorithmic 8-state surface.** **IN, MO, MT, ND, NH, OK, TN, UT**
each file their own override copy of **both** LoED host files
(`...LossOfElectronicDataPremOpsCoverageRules.Rule.xml` and `...ProdsCompldOpsCoverageRules.Rule.xml`)
in every one of their 2027-04-01 packages, but only 4-5 rules deep (`InitializeRuleSet`, `SetILF`,
`SetLimitStatCode`, `ErcProcess`, and ND additionally `DoMessageILF`) -- everything else falls
through to CW. The deviation: these states add a `GovernmentalSubdivision` branch CW's own `SetILF`
does not have -- when `GovernmentalSubdivision == "Yes"`, the aggregate limit used to key the ILF
lookup switches from `GeneralAggregateLimit` to a separate field,
`GeneralAggregateLimitGovernmentalSubdivision`, and `SetLimitStatCode` mirrors the same branch for
the stat-code lookup. Read directly from `GL_IN 20270401 V04`'s copy, lines 245-301 and 371-416;
engine-confirmed that IN@20270401 runs `SetILF` from `GL_IN_20270401_V04` on both hosts with the
lookup falling to CW V02. The other seven states carry byte-length-matched (not individually
re-diffed) copies. Not resolved in source docs: whether the 7 siblings are byte-identical to IN's,
and whether a manual provision documents this branch outside Rule 40's own text.

No state-specific Rules-notice text deviation for Rule 40/LoED was searched exhaustively beyond
the CW notice, given zero rate-table or manual-anchor deviation was found anywhere else that would
motivate the search.

---

## Supporting lookups

| Rule | Matrix | Keys | Notes |
|---|---|---|---|
| `LookupILFPremOps` | `ILFPremOps` | `StateCode`, `FinalPremOpsIncrdLimitTableAssignmentInt`, LoED Limit (as `EachOccurrenceLimit`), `GeneralAggregateLimit` | Prem/Ops' own host ILF table (Rule 23-family), reused directly -- not LoED-specific; pre-2027 the limit key carries " CSL" |
| `LookupILFProds` | `ILFProds` | `StateCode`, `FinalProdsCompldOpsIncrdLimitTableAssignment`, LoED Limit, `ProdsCompldOpsAggregateLimit` | Prod/CompOps' own host ILF table |
| `LookupHazardGrade` | `LossOfElectronicData{PremOps,ProdsCompldOps}HazardGrade` | `StateCode`, `ClassCode` | 1,163 rows CW 2027 / 1,188 earlier; ties to manual Table 40.F via `BureauRuleNumber40F` metadata |
| `LookupLossOfElectronicDataFactorCG0437` / `CG0471` | `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}` | `StateCode`, `HazardGrade` | 4 rows, CW-only in every state checked; CG 04 95 uses the CG0437 table |
| `LookupLossOfElectronicDataMinPremium` | `LossOfElectronicDataMinPremium` | `StateCode`, constant `'Y'` | 1 row, CW = $0, no state override |
| `LookupCyberCoverageLimitStatCode` | `CyberCoverageLimitStatCode` | `StateCode`, limit, aggregate | 130 rows CW; stat code only (e.g. `'60'`) |
| (domain) | `DomainLossOfElectronicDataLimit` | -- | 13 rows, $25,000-$10,000,000 -- exactly the 13 band limits `SetILF`'s refer-condition tests |

---

## Worked example (engine run)

TX@20270401 (`GL_TX_20270401_V01` over CW 20270401 V01), engine base submission (class 50017, Gross
Sales exposure 5,000,000 on both hosts, $1M/$2M limits, no deductibles) plus
`LossOfElectronicDataCoverageApplies = "Yes"` and a CG 04 37 record with `LossOfElectronicDataLimit = "200,000"`:

| Step | Prem/Ops host | Prod/CompOps host |
|---|---|---|
| ILF | `ILFPremOps` TX table 3 -> 1.28 | `ILFProds` TX table B -> 1.23 |
| DedFactor / FinalILF | 0.0 / 1.280 | 0.0 / 1.230 |
| AdjustedBaseRate | 0.1114 | 1.0086 |
| HazardGrade / factor | '1' / 0.001 (CG0437) | '1' / 0.001 (CG0437) |
| FinalRate | 0.0001 | 0.0010 |
| Premium | round(0.0001 x 5,000) = 1 | 5 |

Policy total 7,746 (= 7,740 base + 6). Same chain IL@20270401 (CW V02): Prem/Ops 1, Prod/CompOps 5;
IL@20261002 (CW 20260101 V01, " CSL" keys): Prem/Ops 1, Prod/CompOps 5. A CG 04 95 record
(IL@20270401) rates LoED identically through the CG0437 factor table.

---

## Quick reference -- end-to-end, Loss Of Electronic Data (either host)

```
Gate           = SetCoverageOnPolicyIndicator: schedule present AND LossOfElectronicDataCoverageApplies == "Yes"
                 [2027: + Subline test per host]

Limit          = LossOfElectronicDataLimit                          [from CG 04 37 / CG 04 71 / CG 04 95 schedule]

ILF            = ILFOverride                                        if (Limit, aggregate) hits one of 13 filed "refer" bands
                                                                    [engine: null override -> refused by name, OI-129]
               | LookupILFPremOps|Prods(host table assignment, Limit[+" CSL" pre-2027], host aggregate)   [host's own ILF table]
               | 0.0

DedFactor      = host DeductibleFactor | host PDDeductibleFactor | 0.0   [host's own value, not an independent table]

FinalILF       = round(ILF - DedFactor, 3)  if > 0  else 0.0

AdjustedBaseRate (Prem/Ops) = round((host LossCost | host ELP if LossCost == 0) x host LCM
                                    [x ClaimsMadeMultiplier] [x SizeOfRiskFinalRelativity] x FinalILF, 4)
AdjustedBaseRate (Prods)    = round(host BaseRate [x SizeOfRiskFinalRelativity] x FinalILF, 4)

HazardGrade    = LookupHazardGrade(ClassCode)   -> LossOfElectronicData{PremOps,ProdsCompldOps}HazardGrade
                 [1,163 rows CW 2027 / 1,188 earlier; a blank grade gives factor 0.0]

LoEDFactor     = LookupLossOfElectronicDataFactorCG0437 (CG 04 37 or CG 04 95) | CG0471 (CG 04 71), by HazardGrade

FinalRate      = round(AdjustedBaseRate x LoEDFactor x PackageModFactor
                       x ExperienceRatingModificationFactor x ExpenseModification x ModToUse, 4)

Premium        = round(FinalRate x Exposure/1000, 0)   [9 filed /1000 bases]
               | round(FinalRate x Exposure, 0)         [otherwise]
               | 1.0  if that rounds to 0 and Exposure > 0                  [$1 minimum, 2027 only]

PolicyMinPremiumTopper = max(0, MinPremium[CW=$0] - sum(all PremOps+ProdsCompldOps LoED Premiums))
                          -- structural no-op today; filed value is $0 in all 51 jurisdictions
                          -- engine sums only the Prod/CompOps term (see Minimum premium)
```

Rounding: `AdjustedBaseRate` and `FinalRate` to 4 decimal places; `FinalILF` to 3; `Premium` to 0.

---

## Findings

- **The combined gate's three open items are resolved.** Exact rule-file names, the literal
  `SetFinalRate`/`SetPremium` arithmetic, and the ILF/deductible table identity are all confirmed
  from live ERC XML in two states (TX, IL), neither of which overrides this coverage -- and now
  reproduced by offline engine runs (worked example above).
- **LoED has no ILF or deductible table of its own** -- it borrows its host subline's (Prem/Ops or
  Prod/CompOps) own already-filed ILF table and already-computed deductible factor outright, using
  the LoED limit as the Each Occurrence Limit substitute. This is a stronger table-borrow than
  Stop Gap's, which borrows Prem/Ops' ILF table but keeps its own rate factor.
  ([[Stop Gap|StopGap_RatingAlgorithms.md]] Step 1.)
  Compare to [[UnmannedAircraft_RatingAlgorithms.md]] Master orchestration, which borrows tables
  but not computed values.
- **Correction (2026-10-02):** the two hosts are not identical in `SetAdjustedBaseRate` -- the
  Prod/CompOps host multiplies the host's finished `BaseRate`, not loss cost x LCM, and has no
  Claims-Made branch. There are 13 refer bands, not 14. CG 04 95 rates through the CG0437 factor
  table. LoED/Cyber exist from CW 20231201, not only 2027.
- **Manual/ERC agree exactly** on all four rate-factor tables (Table 40.C/40.D vs
  `LossOfElectronicData{PremOps,ProdsCompldOps}Factor{CG0437,CG0471}`) across two live states, no
  override anywhere.
- **Manual says refer-to-company for minimum premium; ERC computes a real topper that is a
  structural no-op** because the filed CW value is $0 everywhere in the 2027 corpus. ERC stands as
  the mechanism of record.
- **Engine findings (not changed here):** (1) a refer-band limit without `ILFOverride` halts the
  rating INCOMPLETE rather than surfacing `DoMessageILF` or a referral code -- in `underwriting` mode
  too; (2) `TotalLossOfElectronicDataPremium` drops the Prem/Ops term (engine `ForEach` keeps only the
  last child's value per iteration).
- **CW 20270401 V02 vs V01:** no change to either LoED coverage file. The only Rule-40-adjacent change
  is the CG 04 95 schedule's `DoMessageCyberIncidentAggregateLimit` guard (now split into a combined-
  subline "Aggregate Limit" check and a Prod/CompOps "Products Completed Operation Aggregate Limit"
  check) and the removal of `DoMessageCannotattachCG4035WithCG0425CG0495ToTheSamePolicy` from
  `GeneralLiabilityRules` -- guards only, no premium effect.
- **A genuine 8-state deviation** (IN, MO, MT, ND, NH, OK, TN, UT) adds a `GovernmentalSubdivision`
  branch to the ILF lookup on both hosts, absent from CW and from any Rule-40 manual text located --
  worth a person's confirmation before treating as settled.
- **Correction to an earlier assumption:** `ElectronicDataLiabilityClassCode` is not a LoED table
  -- it belongs to the unrelated, fully refer-to-company Rule 42 "Electronic Data Liability"
  coverage, has zero rows and zero readers in the CW rule tree, and should not appear in this
  coverage's table list.
- **Unlisted class code, resolved structurally:** every class with a filed IL 2027 Prem/Ops loss cost
  is present in the hazard-grade table, so the case is unreachable for ratable classes; if a lookup
  did miss, `HazardGrade` is blank, `SetLossOfElectronicDataFactor` takes its `Otherwise` branch
  (factor 0.0), and the 2027 `$1` minimum applies -- not a coded `"1"` default.
- `gl_engine` code: zero hits for `LossOfElectronicData` or `LoED` -- consistent with this
  project's architecture (jurisdictional/coverage content lives in ERC, not Python). Same finding
  as [[Stop Gap|StopGap_RatingAlgorithms.md]] Findings.
