# Gate — State-specific rating coverages (build-order item 11)

**Filed 2026-08-12. Eleventh gate.** Differential against the ten before it.

**As-of date: 2026-08-12.** Required, not assumed (N4). Each coverage derived against its own
jurisdiction's resolved package and that package's declared parent (N5/N6).

Measured by
[`scripts/erc/39_state_specific_align.py`](../../scripts/erc/39_state_specific_align.py) (**4/4**).

---

## 0. The scope was four coverages in three states. It is five in four.

`PHASE-SIZING.md` §5 scoped this item as **MD** lead-hazard liability, **MA** lead-poisoning
endorsement and supplemental cover, and **NY** Special Protective and Highway — *"four coverages in
three states"* — with the note that *"NJ and RI lead coverages were checked and do not rate."*

**Half of that note is wrong. Rhode Island rates.**

The population was re-derived rather than taken from the list: **every DataDefGroup that appears in
no countrywide edition**, computed by differencing 582 countrywide groups against 618 jurisdiction
groups. **449 groups are state-only**, and they classify as:

| | |
|---|---|
| Not premium-writing | **371** |
| `CAPTURE` | **58** |
| `OTHER` | **16** |
| `RATE_DRIVEN` | **4** |

**The four `RATE_DRIVEN` are exactly the four PHASE-SIZING named** — that part held. **Rhode Island
is the fifth, sitting in `OTHER`.**

### Why Rhode Island hid

`25_rating_vs_capture` calls a group `RATE_DRIVEN` when its premium rule reads a DataDef matching
`FinalRate | BaseRate | LossCost | ELP | AdjustedBaseRate | AdjustedRate`. Rhode Island's premium
comes from **`LeadLiabilityRate`**, which matches none of them.

**That is the fourth blind spot in one list:**

| Found | Missing term | Cost |
|---|---|---|
| 2026-08-11 | `AdjustedRate` | both Unmanned Aircraft coverages filed as aggregators |
| 2026-08-12 (terrorism) | a sibling group's `Premium` | four terrorism groups |
| 2026-08-12 (terrorism) | `EndorsementPremium` | the terrorism endorsement group |
| **today** | **`LeadLiabilityRate`** | **a whole state coverage** |

The list encodes an assumption — *a rating path starts from a rate whose DataDef is named like
one* — and ERC has now broken it four different ways. **The headline `18 / 383 / 76` is a floor,
not a measurement**, and every gate that has looked has found another.

### New Jersey, checked and confirmed

NJ files **3** lead groups; **2 write a premium and both read `ManualPremium`** — `Premium =
ManualPremium × PackageModFactor`. Its five lead tables are all `*StatCode`. **NJ genuinely does
not rate lead**, exactly as recorded. The note was half right and is now half corrected.

---

## 1. The five, sized

| State | Coverage | Rules | Populated tables |
|---|---|---|---|
| **MA** | Lead Poisoning Endorsement | **10** | 4/4 |
| **MA** | Supplemental Coverage — Lead Poisoning | **16** | 4/4 |
| **MD** | Liability For Hazards Of Lead | **14** | 4/6 |
| **NY** | Special Protective and Highway | **35** | 4/4 |
| **RI** | Lead Poisoning | **13** | 3/3 |
| | | **88** | |

**88 rules in four states** — smaller than item 6's 150 and larger than item 8's chain, and unlike
either it is **four independent derivations with nothing shared between them.**

**All four states carry the coverage in the manual too**, as an `ADDITIONAL RULE(S)` block in the
state exception pages: `GL-MD-2022-RU-001` Rule A2 *Liability For Hazards Of Lead*,
`GL-MA-2021-RU-003` Rule A1 *Coverage For Lead Poisoning*, `GL-RI-2021-RU-003` Rule A2 *Coverage For
Lead Poisoning*, `GL-NY-2022-RU-001` Rule A3 *Description Of Special Protective And Highway
Liability Coverage*. **That block is the manual-side signature of this item** — a coverage a state
adds that the countrywide manual does not have, and the exact analogue of a DataDefGroup present in
no countrywide edition.

---

## 2. The three lead plans are three different algorithms

They share a subject and nothing else.

| | Filed rate content |
|---|---|
| **MD** | `LiabilityHazardsOfLeadChargeLossCost` — **1 row, a flat `15`**. A per-dwelling-unit charge |
| **MA** | `LeadPoisoningRate` — **1 row, `0.01`** — and `LeadPoisoningCode` — **1 row, `90140`** |
| **RI** | `RILeadComplianceFactors` — **4 rows, keyed on level of hazard**: `Lead Safe 0.01` · `Lead MICI 0.05` · `Lead MVI 0.10` · `Lead MPC 0.10` |

**Rhode Island is the only one of the three that prices risk differentiation.** Its 16,410-character
`SetPremium` branches on class codes `67510` / `67511` and then on
`LeadPredominateStatusOfLeadSafety`, counting units under four separate inputs —
`LeadNumberofUnitsLeadMitigatedBy{IndependentClearanceInspection, VisualInspection,
PresumptiveCompliance}` and lead-safe units. **A tenfold factor range between a lead-safe unit and
an unmitigated one**, which is the largest single-coverage credit spread found in the project.

**The engine owes four separate unit-count inputs for Rhode Island**, and MD and MA are one input
each.

---

## 3. New York Special Protective and Highway prices at zero, by design

The largest of the five — **35 rules**, borrowing OCP's ILF (`LookupILFOwnersContractors`),
Prem/Ops's LCM and minimum premium — and the most elaborate. It is also **not a rateable coverage.**

| Table | Rows | Values |
|---|---|---|
| `SpecialProtectiveHighwayLossCost` | 3 | **`0`, `0`, `0`** |
| `SpecialProtectiveHighwayELP` | 3 | **`0`, `0`, `0`** |
| **`SpecialProtectiveHighwayELPText`** | 3 | **`Company`, `Company`, `Company`** |
| `SpecialProtectiveHighwayHomogeneityIndex` | 3 | `N/A`, `N/A`, `N/A` |

**N17 settles what that means.** The rating-basis selector is a closed four-value vocabulary, and
`Company` means *refer to company* — established in gate 335-RR against the manual's own ELP
Supplement, which prints `RTC` for exactly the classes ERC marks `Company`. **A single-valued
selector means the coverage has exactly one rating path**, and here that path is a referral.

Trace it: `SetBaseRate` tests `LossCost == 0.0` and takes the ELP branch — **N13's third meaning of
`0`, a published zero that switches the rating path** — and the ELP is `0` too. So
`BaseRate = 0` → `FinalRate = round(0 × ILF × PackageModFactor, 3) = 0` → **premium `0`**.

**This is Railroad Protective's shape exactly** (gate 335-RR): a full rating chain, a single-valued
selector, no filed rates, and a manual that hands the rate to the company. **Two of the project's
eighteen rate-driven coverages are structurally elaborate referrals.**

**Consequence for the build order:** NY Special Protective and Highway is **item 11 by structure and
item 12 by behaviour.** Its 35 rules must be implemented — the ILF, limits, minimum premium and
statistical coding all matter — but the rate they consume comes from the carrier, and an engine
that runs the chain on the filed data returns `0` on all three classes. It belongs in the
refer-to-company workflow's population.

---

## 4. What the engine owes

1. **Four independent lead algorithms is the wrong count — three, plus a referral.** MD, MA (two
   coverages sharing tables) and RI are genuinely separate derivations. Nothing composes.
2. **Rhode Island needs four unit-count inputs and a hazard-level input**, and its factor table is
   keyed on the latter. The tenfold spread makes an unvalidated input expensive.
3. **NY Special Protective and Highway must raise `REFER` before it multiplies**, on the N17
   selector rather than on the zero — the selector is the declaration, the zero is the symptom.
   Adding it to the confirmed-sentinel register alongside Railroad.
4. **`LeadLiabilityRate` must be added to the rate-source vocabulary** before any load-time
   classifier is written, along with the three other terms found this week.
5. **These coverages are class-level, not policy-level**, except MD's `…PolLvl` siblings. The
   `ClassLvl` suffix in every one of the four lead group names is load-bearing: they evaluate per
   classification, so they sit inside the same iteration item 6 and item 8 do.

---

## 5. Register

| | |
|---|---|
| **OI-63** *(new)* | `25_rating_vs_capture.RATE_SRC` has now been found short **four times**. The `18 / 383 / 76` split is a floor. A definitive re-measurement should classify by *what the premium rule reads*, not by a name list — and until it runs, every "N coverages rate" figure in the project carries an unstated "at least" |
| **OI-64** *(new)* | NY Special Protective and Highway is a structurally complete rating chain with no filed rates and a `Company` selector on every class. **Second confirmed elaborate referral after Railroad**; belongs in item 12's population |
| **PHASE-SIZING §5** | Corrected: **five coverages in four states, 88 rules**. The NJ half of its note stands; the RI half does not |
| **N13** | Third meaning confirmed on a second coverage: a published `0` loss cost switching to the ELP path — and here the ELP is `0` as well |
| **N17** | Second single-valued `Company` selector, and the second coverage it proves is a referral |

---

## 6. Verification

| | |
|---|---|
| `scripts/erc/39_state_specific_align.py 20260812` | **4/4** |
| `38_rating_plans_align.py` · `37_terrorism_align.py` · `35_census_sizeofrisk.py` · `34_crosscheck.py` | 7/7 · 4/4 · 5/5 · 4/4 |
| `verify_golden.py` · `verify_california.py` · `verify_new_york.py` · `verify_oi50.py` | 80/80 · 11/11 · 10/10 · 7/7 |
| `Agentic/iso-circular-expert/tools/smoke_test.py` | 19/19 |
