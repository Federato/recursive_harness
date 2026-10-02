# Owners & Contractors Protective / Principals Protective — Rating Algorithms

**Source ERC packages:** `GL_CW_20230501_V01`, `GL_CW_20231201_V02` (CA's parent),
`GL_CW_20231201_V03`, `GL_CW_20260101_V01`, `GL_CW_20261001_V01` (pre-2027 algorithm) and
`GL_CW_20270401_V01`, `GL_CW_20270401_V02` (2027 algorithm). The OCP rule file is byte-identical
across V03 / 20260101 / 20261001, and across 20270401 V01 / V02; CA's V02 parent differs from V03
only in lacking the `IsNull` "a supplied value is never overwritten" guards.
**Line:** General Liability (GL), Countrywide, Subline Code 335
**Rule:** Manual Rule 46 — "Owners And Contractors Protective Liability Insurance And Principals
Protective Liability Insurance" (`GL-MU-2027-RU-001-C` p.103, cited in
`GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md` § 2)
**Reformatted from:** `docs/gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`
**Documented:** 2026-08-20
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — ISO's AR/WY OCP STC submissions re-dated and rated offline by the kernel at 2023-05-01, 2026-10-02 and 2027-04-01 (AR over CW 20230501 V01 / 20260101 V01 / 20270401 V02; WY over CW 20260101 V01 / 20270401 V02), rule XML read per edition, table populations censused across all 51 resolved jurisdictions.

This document covers **Owners & Contractors Protective (OCP)** and **Principals Protective**
liability, which share one ERC rule set (subline 335, Rule 46). It does **not** cover Railroad
Protective Liability — same subline code, different rule (Rule 49) — which has its own pair of
documents, `RailroadProtective_RatingAlgorithms.md` / `RailroadProtective_ERC_Tables.md` (see also
`docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md` § 3.2.5).

Standalone Coverage Part — not an endorsement to the CGL (per `GATE-335` § 1 and
`03-SUBLINE-COVERAGE-PLAN.md` § 3.2.4). Class-level coverage, no territory dimension, **no
deductibles** (Rule 15 is explicitly excepted, `GL-MU-2027-RU-001-C` p.104), no size-of-risk
mechanism, and — unlike sublines 334 and 336 — **no `PackageModFactor`**.

> **Gate status note.** `GATE-335` reports this gate as **passed with no oracle** — the corpus
> holds one rated output (the Oklahoma golden case) and it carries no OCP coverage; of 516 STC
> submissions, 8 carry an OCP exposure and none has a paired expected output. That is still true:
> nothing below is checked against an ISO-certified OCP premium. **What changed on 2026-10-02:** every
> step, branch and rounding point below was confirmed against the built engine's execution of ISO's
> rule XML (trace of calls, lookups, writes and rounds), and the worked example in the Quick Reference
> is now **reproduced by the engine** (AR STC `STC_GL000074745`, class 15191, AR@2023-05-01 →
> `13,125`), not just predicted. It confirms the engine runs ISO's rules as written; it is still not
> an ISO-arithmetic oracle.

---

## Master orchestration

**Which algorithm runs is selected entirely by the resolved parent edition — not by
jurisdiction.** The engine resolves the state package and its *declared* countrywide parent as of
the risk's effective date (`gl_engine/resolve/resolver.py`; the effective date is a submission
variable, decision A3, and `package_version` can pin an edition). Confirmed with
`python -m gl_engine.cli parents` and the resolver:

| As of | Pre-2027 chain (21 steps) | 2027 chain (12 steps) |
|---|---|---|
| 2026-10-02 | all 51 — 46 over `GL_CW_20260101_V01`, NJ/TX/VT over `GL_CW_20231201_V03`, OK over `GL_CW_20261001_V01`, CA over `GL_CW_20231201_V02` | none |
| 2027-04-01 | 5 — CA (over `GL_CW_20231201_V02`), GA, NJ, NY, WA (over `GL_CW_20260101_V01`) | 46 — AK, DC, MA, NC, SC, TX, WI, WV over `GL_CW_20270401_V01`; 38 others over `GL_CW_20270401_V02` |

So the same state can run either chain below depending on the risk's effective date, and on
2027-04-01 itself five states are still on the pre-2027 chain (the gate doc's "43 withdraw" figure
is superseded by the resolved parents above).

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
Confirmed by rule diff: 58 rules (CW 20260101 V01) → 45 (CW 20270401 V02); 13 removed, 7 changed
(`ErcRate`, `ErcSetRatesAndFactors`, `SetBaseRate`, `SetBaseRateOverOneMillion`, `SetELP`,
`SetOwnersContractorsExposureStatCode`, `SetPremium`).

One dead artifact survives the cut: `LookupPrincipalsProtvLiabFactor` is still present in the CW
2027 rule set but has no caller, because `SetPrincipalsProtvLiabFactor` was deleted (`GATE-335` § 1,
Escalation E14).

---

## File map

| Piece | ERC rule set / rule | Source |
|---|---|---|
| Rate build-up + premium (both editions) | `GeneralLiabilityClassificationOwnersContractorsCoverageRules.Rule.xml` (`ErcProcess` → `ErcSetRatesAndFactors` / `ErcRate` / `ErcSetStatisticalCodes`) | confirmed by engine trace 2026-10-02 |
| Loss cost multiplier | `OwnersContractorsLCM` via `LookupOwnersContractorsLCM`, keyed (State\|CW, `"Y"`) | countrywide, 1 row, value `1` (all editions) |
| Policy-level minimum-premium top-up (pre-2027 only) | `GeneralLiabilityOwnersContractorsPremiumToReachMinCoverageRules.Rule.xml` | 9 rules pre-2027 → 4 at CW 2027 (its `ErcRate`, `SetCoveragePremium`, `SetMinPremium`, `SetPremium`, `SetPremiumIndicator` deleted) |
| Selector + refer message | `GeneralLiabilityClassificationRules.Rule.xml`: `SetOwnersContractorsELP` (writes `OwnersContractorsELP` from `OwnersContractorsELPText`), `DoMessageMustEnterEstimatedLossPotentialFactorOverride` | both editions |
| Loss-cost tables (pre-2027 only) | `OwnersContractorsLossCost`, `...OverOneMillion`, `...OverOneHundred` | state-filed, 8 jurisdictions (`GATE-335` § 5) |
| ELP tables | `OwnersContractorsELP`, `...OverOneMillion`, `...OverOneHundred` | state-filed, all 51 jurisdictions (`GATE-335` § 5) |
| Refer-to-company selector | `OwnersContractorsELPText` | state-filed, all 51, 433 rows (`GATE-335` § 5, § 7) |
| Increased-limits factor | `ILFOwnersContractors` | state-filed (`GATE-335` § 5) |
| Workers Compensation factor (pre-2027, class `15191` only) | `PrincipalsProtvLiabFactor` | countrywide, 1 row: `"CW","Y",0.75` (`GATE-335` § 5) |
| Minimum premium (pre-2027 only) | `PremOpsMinPremium` — **reused from subline 334 (Premises/Operations)**, not an OCP-specific table | countrywide, 3 rows (`GATE-335` § 5) |

> Rule files resolved 2026-10-02 from the engine trace (rule names carry the file as their prefix in
> the trace). Line numbers are not cited; `rule_dump.py <stem> <Rule> <pkg>` prints any rule's tree.

---

## CW 2023 and earlier — rate build-up

Executed in the 21-step order in **Master orchestration** above. Steps grouped by what they
compute (per `GATE-335` § 1, § 4, § 7):

### Step 1 — Published loss cost (state-filed path)
`SetLossCost`, `SetLossCostOverOneMillion`, `SetLossCostOverOneHundred`

Reads `OwnersContractorsLossCost` (+ the two band tables), keyed on **(state, class)** — no
territory (`GATE-335` § 5). Countrywide holds 0 rows for all three tables. **Engine census as of
2026-10-02: every one of the 51 jurisdictions files its own `OwnersContractorsLossCost` (563 rows, 204
non-zero)** — the earlier "8 jurisdictions" figure described the 2027-04-01 cliff, not today. As of
2027-04-01 only the 5 states still on a pre-2027 parent (CA, GA, NJ, NY, WA) declare the table (55
rows, 20 non-zero); the 46 others resolve to the empty CW copy, which the 2027 rules never read.
**Both band tables (`...OverOneMillion`, `...OverOneHundred`) are zero in every row of every state**
at both dates.

Selector gate: `OwnersContractorsELPText` marks each (state, class) as `"Rate/Loss Cost Applies"`,
`"Industry"`, or `"Company"`. Engine census, 563 rows as of 2026-10-02: `Rate/Loss Cost Applies` 204
(all with a non-zero loss cost and zero ELP), `Industry` 255 (204 with ELP > 0, plus the 51 class-`15191`
rows whose ELP is legitimately 0), `Company` 104 (all ELP 0, loss cost 0) — the loss cost path is
only live where the selector says so.

**Engine behaviour (OI-94):** a class missing from the state's loss-cost table writes a *null*
`LossCost`; the kernel refuses the risk rather than rating it ("LossCost resolved to null and the
risk cannot be rated … (OI-94)"). Confirmed AR@2026-10-02 with class `27113` (a 2027-only class).

### Step 2 — Workers Compensation factor (prerequisite for Step 3, class `15191` only)
`SetPrincipalsProtvLiabFactor`

```
PrincipalsProtvLiabFactor = 0.75      # single countrywide cell, "CW","Y",0.75
```

Confirmed independently against the manual's ELP Supplement: *"15191 Percentage of otherwise
applicable Workers Compensation loss costs: 75%"* (`GL-AK-2020-LC-001-C` p.9, Table 5.C, cited in
`GATE-335` § 2). Engine: `PrincipalsProtvLiabFactor` misses the state and resolves `["CW","Y"] → 0.75`;
for any class other than `15191` the rule writes `0.0` without a lookup. CW 2027 keeps the table
name but with 0 rows.

### Step 3 — ELP (fallback / class-driven path)
`SetELPOverride`, `SetELPOverOneMillionOverride`, `SetLCM`, `SetELP`, `SetELPOverOneHundred`,
`SetELPOverOneMillion`

`SetELP` branches three ways on class code (`GATE-335` § 1):

```
if OwnersContractorsClassDescription = "":          # the outer gate is the DESCRIPTION
    ELP = 0.0
elif ELPOverride <> 0:
    ELP = ELPOverride
elif OwnersContractorsClassCode = "":
    ELP = 0.0
elif OwnersContractorsClassCode = "15191":
    ELP = PrincipalsProtvLiabFactor x WorkersCompensationRate   if WorkersCompensationRate present
        | 0.0                                                    otherwise (silent)
else:
    ELP = LookupOwnersContractorsELP(state, class)
```

`WorkersCompensationRate` is a declared submission input field
(`MasterGLCW.DataDef.xsd`, `xs:decimal`, 4 fraction digits) — not an ERC table value (`GATE-335`
§ 1). It is read at **policy level**, from
`GeneralLiability/GeneralLiabilityPrincipalsProtectiveLiabCovTable/GeneralLiabilityPrincipalsProtectiveLiabCov[1]/WorkersCompensationRate`
(one rate per policy, not per classification). It is required whenever class `15191` is present,
and only in this (pre-2027) edition family; absent, the class rates at ELP `0.0` with no message.

`OwnersContractorsELP`, `...OverOneMillion`, `...OverOneHundred` are keyed on **(state, class)**
— 0 rows countrywide, populated in all 51 jurisdictions (`GATE-335` § 5).

Selector `Company` marks refer-to-company classes and carries `0` in the ELP table for every one
of them — 104/104 as of 2026-10-02 (150/150 as of 2027-04-01) across all 51 jurisdictions (engine
census; the gate doc's 147/147 was an earlier snapshot). The manual's ELP Supplement prints `RTC`
for exactly those classes (`17982`, `93040`), confirming ERC's `Company` value means Refer To
Company (`GATE-335` § 2, § 7).

**The selector is not inert:** ISO's `GeneralLiabilityClassificationRules.DoMessageMustEnterEstimatedLossPotentialFactorOverride`
raises *"Must enter Estimated Loss Potential Override"* when `Subline = "Owners and Contractors"`,
`OwnersContractorsELP = "Company"`, `MiscIfAnyBasis = "No"` and no `OwnersContractorsELPOverride`
is supplied. The rating still completes at ELP `0` (premium `0` pre-2027). In `underwriting` mode the
engine's referral register turns that message into **R29** (Company-rated class with no carrier
override). Confirmed AR@2026-10-02, class `17982`: premium `0`, message raised, R29 referral.
A supplied `OwnersContractorsELPOverride` both clears the message and replaces the ELP.

### Step 4 — Increased limits factor
`SetILF`

Reads `ILFOwnersContractors`, keyed on **(state, `OwnersContractorsEachOccurrenceLimit`,
`OwnersContractorsAggregateLimit`)** — both policy-level fields; no territory, no table-assignment
dimension (`GATE-335` § 5). The rule is gated on `OwnersContractorsClassDescription` and both limits
being non-empty, else `ILF = 0.0` (`GATE-335` § 4). **Limit vocabulary is `"1,000,000"` /
`"2,000,000"`, not `"1,000,000 CSL"`** as used by sublines 334/336 pre-2027 — and it stays that way at
CW 2027. The 2027-04-01 filing's dropping of the `" CSL"` suffix (OI-96/97, renormalized payload-side
by `scripts/variants.py` `_renormalize_limit`) therefore does not touch OCP: the AR lookup key is
`['AR', '1,000,000', '2,000,000']` at 2023-05-01, 2026-10-02 and 2027-04-01 alike (factor `1.75` →
`1.88` → `2.04`).

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
`OwnersContractorsELP` and their `OverOneMillion` and `OverOneHundred` counterparts. Both inputs are
read through `FirstValue(…, 0.0)`, so inside ISO's rule a null loss cost behaves as `0` and falls to
the ELP branch — the engine's OI-94 refusal (Step 1) stops that before a premium is reported.

> **Data finding (engine-confirmed, both editions):** every `...OverOneMillion` and
> `...OverOneHundred` loss-cost and ELP cell is `0` in all 51 states, so `BaseRateOverOneMillion` /
> `BaseRateOverOneHundred` are always `0` and the exposure above the breakpoint contributes nothing.
> WY@2026-10-02, class `16291`, exposure `$10,000,000` → `0.473 x 1,000 = 473`; the other $9M rates at
> `0`. ISO's tables say so; the engine does not second-guess it, and no referral fires.

### Step 6 — Final rate
`SetFinalRate`, `SetFinalRateOverOneMillion`, `SetFinalRateOverOneHundred`

```
FinalRate = round(BaseRate x ILF x ExperienceRatingModificationFactor
                          x ExpenseModification x ModToUse, 3)
```

Applied identically to the base band and each `OverOneMillion` / `OverOneHundred` band, per
`GATE-335` § 1.

> Resolved from rule XML 2026-10-02: `ExperienceRatingModificationFactor`, `ExpenseModification`
> and `ModToUse` are policy-level (`GeneralLiability`) values read through `FirstValue(…, 0.0)` — the
> policy rules compute them (all `1` on the ISO STC submissions rated). An absent one is `0` and
> zeroes `FinalRate`. There is no `PackageModFactor` or `ScheduleRatingModificationFactor` term.

### Step 7 — Minimum premium
`SetMinimumPremium`, `SetMinPremium`

```
MinPremium = round(MinimumPremium x ILF, 0)
```

Reads `PremOpsMinPremium` — **reused from subline 334**, not an OCP-specific table — keyed on
(State|CW, hardcoded `"2"`); CW row `["CW","2"] → 0` on every rated state, so `MinPremium = 0` today.
**No `AdditionalInterestFactor`**, unlike subline 336's minimum premium (`GATE-335` § 1). Silently not
applied (`MinPremium = 0.0`) when `Subline <> "Owners and Contractors"` (`GATE-335` § 4) **or when the
classification's `MiscIfAnyBasis <> "No"`**. `MinPremium` does not feed `SetPremium` — see the
premium section for where it is applied.

---

## CW 2027 and later — rate build-up

Executed in the 12-step order in **Master orchestration** above. `SetLossCost` and its two band
variants, `SetPrincipalsProtvLiabFactor`, `SetELPOverOneHundred`, `SetMinimumPremium`, and
`SetMinPremium` are all deleted. What remains is purely ELP-driven, with one breakpoint and no
minimum premium — but with a **`$1` floor** in `SetPremium` (below) (`GATE-335` § 1; engine-confirmed).

### Step 1 — ELP
`SetELPOverride`, `SetELPOverOneMillionOverride`, `SetLCM`, `SetELP`, `SetELPOverOneMillion`

The class-`15191` Workers Compensation branch is removed (class `15191` is retired by 2027); every
class resolves via `LookupOwnersContractorsELP(state, class)` or the `Company` refer-to-company
selector (`GATE-335` § 1). `SetELP`'s outer gate moves from `OwnersContractorsClassDescription` to
`OwnersContractorsClassCode` (rule diff); `SetILF` still gates on the description. The `27111`/`27112` classes that drove the 100-unit breakpoint are also
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

### No minimum premium — but a `$1` floor
`SetMinimumPremium` and `SetMinPremium` are both deleted (`GATE-335` § 1), and the policy-level
`GeneralLiabilityOwnersContractorsPremiumToReachMinCoverage` loses its rating rules. `SetPremium`
instead writes `Premium = 1.0` whenever the unrounded computed premium is exactly `0` and
`OwnersContractorsExposure > 0` (see premium section).

> **Engine finding.** A class that is retired or unfiled in the resolved 2027 state table (e.g.
> `15191`/`15192` in AR or WY at 2027-04-01) writes `ELP = None`; the 2027 chain has no `LossCost` node,
> so the kernel's OI-94 refusal (which only inspects `*LossCost` nodes) does not fire, no referral
> fires, and the classification is priced at the `$1` floor. Confirmed AR@2027-04-01 (STC
> `STC_GL000074745` re-dated): classes `15191`, `15192` → `1` each. A `Company` class at 2027 (AR
> `27113`) also lands on `$1`, but there ISO's message fires and `underwriting` mode raises R29.

---

## OCP / Principals Protective — premium

Rule 5 (standard Premium Computation) does not apply to this subline: *"1. Rule 5. Premium
Computation does not apply."* (`GL-MU-2027-RU-001-C` p.104, cited in `GATE-335` § 2). OCP has its
own piecewise premium function instead, common in shape to both edition families.

### Gate — coverage on policy
`ErcProcess` runs only when `CoverageOnPolicyIndicator` is set. `SetPremium`'s outer test is
`IsNotNull(OwnersContractorsClassCode)` — absent → `Premium = 0.0` (`GATE-335` § 4). `SetELP` and `SetILF` gate separately on `OwnersContractorsClassDescription` —
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

> Confirmed from `SetPremium` XML and an engine run (2026-10-02): `Units` is the same
> `OwnersContractorsExposure` field, read as a unit count; the over-100 term is
> `FinalRateOverOneHundred x (Exposure - 100)` with no divisor, and the sum is rounded once to 0 dp.
> AR@2026-10-02, class `27111`, exposure 150: `LossCost 0.18 → BaseRate 0.180 → FinalRate
> round(0.18 x 1.88, 3) = 0.338 → Premium round(0.338 x 100 + 0 x 50, 0) = 34`.

### Minimum premium (pre-2027 only) — a policy-level top-up, not a `max`
The classification `Premium` is **never** floored by `MinPremium` (`SetPremium` does not read it).
The minimum is applied once per policy by a separate coverage,
`GeneralLiabilityOwnersContractorsPremiumToReachMinCoverage` (rule XML, confirmed by engine run):

```
CoveragePremium = sum of every classification's OCP Premium
MinPremium      = max over classifications of their MinPremium
Premium (top-up) = MinPremium - CoveragePremium   if MinPremium > CoveragePremium
                 | 0.0                            otherwise
    # only when PackagePolicy = "" and multistate = "" and at least one classification has
    # MiscIfAnyBasis = "No" and at least one has OwnersContractorsExposure <> 0; else 0.0
```

With `PremOpsMinPremium = 0` today the top-up is always `0` (AR@2026-10-02: `CoveragePremium
14,368`, top-up `0`). CW 2027 deletes this coverage's rating rules.

### `$1` floor (CW 2027 only)
```
Premium = 1.0                       if unrounded (Branch A sum) = 0 and OwnersContractorsExposure > 0
        | round(Branch A sum, 0)    otherwise
```

### Premium indicator
`SetPremiumIndicator` — writes `PremiumIndicator = 1` on every rated classification observed (it
carries no premium effect).

---

## CW 2023 vs CW 2027 — side by side

| | CW 2023 and earlier | CW 2027 and later |
|---|---|---|
| Total steps | 21 (11 + 10) | 12 |
| Published loss-cost path | present (`SetLossCost` + 2 bands) | **deleted entirely** |
| Marginal tiers | two breakpoints: `$1,000,000` and `100 units` | one: `$1,000,000` |
| `OverOneHundred` band | present (loss cost, ELP, base rate, final rate) | **deleted** |
| Workers Compensation input (class `15191`) | `ELP = PrincipalsProtvLiabFactor x WorkersCompensationRate` | **removed** — class `15191` retired, `SetELP` no longer references it |
| Minimum premium | `SetMinimumPremium` + `SetMinPremium`, reading `PremOpsMinPremium`, applied as a policy-level top-up coverage | **both deleted**; top-up coverage's rating rules deleted |
| Zero-premium floor | none — premium can be `0` | `Premium = 1.0` when computed premium is `0` and exposure > 0 |
| `SetELP` outer gate | `OwnersContractorsClassDescription` | `OwnersContractorsClassCode` |
| Rule count (rule file) | 58 | 45 |
| Class codes hardcoded in `SetPremium` | `27111`, `27112` | **none** |
| Class list | `15191`, `15192`, `27111`, `27112`, plus unchanged classes | `27113` replaces the two `271xx` classes; `15191`/`15192` retired |
| `LookupPrincipalsProtvLiabFactor` | called by `SetPrincipalsProtvLiabFactor` | **present but uncalled** — vestigial (`GATE-335` § 1, Escalation E14) |
| Loss-cost jurisdictions | 51 of 51 (engine census 2026-10-02: 563 rows, 204 non-zero) | 5 of 51 still declare it at 2027-04-01 (CA, GA, NJ, NY, WA — the states still on a pre-2027 parent, so they still read it); moot for the 46 on the 2027 chain |
| Who runs it on 2027-04-01 | CA, GA, NJ, NY, WA | the other 46 |

Source: `GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md` § 0, § 1; edition rows re-derived from the
engine's resolver and rule diff on 2026-10-02.

---

## Supporting lookups

| Rule / Table | Keys | Layer | Notes |
|---|---|---|---|
| `OwnersContractorsLossCost` (+ `OverOneMillion`, `OverOneHundred`) | state, class | state only, 0 rows CW | 51/51 · 563 rows as of 2026-10-02 (204 non-zero; bands all `0`); 5/51 · 55 rows as of 2027-04-01 |
| `OwnersContractorsELP` (+ `OverOneMillion`, `OverOneHundred`) | state, class | state only, 0 rows CW | 51/51 · 563 rows (204 non-zero) as of 2026-10-02; 51/51 · 424 rows (249 non-zero) as of 2027-04-01; bands all `0` |
| `OwnersContractorsELPText` | state, class | state only | selector: `Rate/Loss Cost Applies` / `Industry` / `Company`; 563 rows as of 2026-10-02 (204 / 255 / 104), 424 as of 2027-04-01 (20 / 254 / 150). Read by `SetOwnersContractorsELP` and the R29 message rule |
| `OwnersContractorsLCM` | `"CW","Y"` | countrywide only, 1 row | value `1` — the unsupplied company multiplier (register R18, a CONFIG item) |
| `ILFOwnersContractors` | state, occurrence limit, aggregate limit | state only, 0 rows CW | limit strings `"1,000,000"` / `"2,000,000"`, not the `...CSL` vocabulary used elsewhere (`GATE-335` § 4, § 5) |
| `PrincipalsProtvLiabFactor` | `"CW","Y"` | countrywide only, 1 row | value `0.75`; feeds class `15191` ELP; pre-2027 only (`GATE-335` § 5) |
| `PremOpsMinPremium` | State\|CW, hardcoded `"2"` | countrywide only, 3 rows | value `0` at key `"2"`; reused from subline 334; pre-2027 only (`GATE-335` § 5) |
| `LookupPrincipalsProtvLiabFactor` | — | — | dead in CW 2027 — no caller after `SetPrincipalsProtvLiabFactor` was deleted (`GATE-335` § 1) |

State deviations (`GATE-335` § 6, via `scripts/erc/29_census_336.py --rules
GeneralLiabilityClassificationOwnersContractorsCoverageRules`): **49 of 51 jurisdictions are pure
countrywide** across all 562 packages in the corpus. Re-checked against the packages the engine
resolves as of 2026-10-02 and 2027-04-01 — unchanged. The only two overriding rules:

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

MinPremium = round(PremOpsMinPremium x ILF, 0)     # when Subline = "Owners and Contractors" and MiscIfAnyBasis = "No"
TopUp      = max(0, max(MinPremium) - sum(Premium))  # separate policy-level coverage, not a per-class max
```

## Quick reference — end-to-end, CW 2023 class 15191 (Workers-Compensation-derived)

```
ELP        = PrincipalsProtvLiabFactor x WorkersCompensationRate    # 0.75 x submitted WC rate
BaseRate   = round(ELP x LCM, 3)          # LossCost is 0 for class 15191 — no published rate
FinalRate  = round(BaseRate x ILF x ExperienceRatingModificationFactor
                            x ExpenseModification x ModToUse, 3)
Premium    = round(FinalRate x min(Exposure, 1000000) / 1000
                  + FinalRateOverOneMillion x max(0, Exposure - 1000000) / 1000, 0)

# Worked example (AR STC_GL000074745, GATE-335 § 8) — REPRODUCED by the engine, not an ISO oracle:
#   AR@2023-05-01, GL_AR_20230501_V01 over GL_CW_20230501_V01, WorkersCompensationRate = 1000
#   ELP       = 0.75 x 1000.0 = 750.00
#   BaseRate  = round(750.00 x 1, 3) = 750.000          (LCM = 1, OwnersContractorsLCM CW)
#   FinalRate = round(750.0 x 1.75, 3) = 1312.500       (ILF = 1.75, AR 1,000,000/2,000,000)
#   Premium   = round(1312.5 x 10, 0) = 13,125          (exposure 10,000, /1000)
# Same submission AR@2026-10-02 (GL_AR_20260101_V01 over GL_CW_20260101_V01): ILF = 1.88,
#   FinalRate = 1410.000, Premium = 14,100.  At AR@2027-04-01 (over CW 20270401 V02) class 15191
#   is retired: ELP = None, Premium = 1 (the $1 floor) — see the engine finding above.
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

Premium    = 1.0   if the sum above is exactly 0 and Exposure > 0      # the CW 2027 $1 floor

# Worked example (WY STC_GL000083607 re-dated) — engine run WY@2027-04-01,
#   GL_WY_20270401_V03 over GL_CW_20270401_V02, class 16291, exposure 10,000,000:
#   ELP 0.231, LCM 1 → BaseRate 0.231; ILF 1.97 → FinalRate round(0.45507, 3) = 0.455
#   Premium = round(0.455 x 1,000 + 0.000 x 9,000, 0) = 455
#   (WY@2026-10-02, pre-2027 chain: LossCost 0.24 → 0.240 → FinalRate 0.473 → Premium 473)
```

All intermediate rate products (`BaseRate`, `FinalRate`, and their bands) carry 3 decimal places;
the `Premium` and `MinPremium` products carry 0. Rounding direction (`HALF_UP` vs `HALF_EVEN`) is
an open question raised in `GATE-335` § 3 (Escalation E1) — a real AR submission hits an exact
3-decimal-place midpoint (`0.95 x 1.75 = 1.6625`), and the two rounding conventions diverge at the
third decimal place even though they happened to produce the same premium at that exposure. The
engine rounds `ROUND_HALF_UP` by default (`Kernel(rounding=…)`); at today's AR ILF of `1.88` the same
class gives `0.95 x 1.88 = 1.786` exactly, so the midpoint no longer arises there.

---
