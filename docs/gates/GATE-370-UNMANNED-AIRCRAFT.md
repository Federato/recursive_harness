# Gate — Unmanned Aircraft (subline 370, Rule 37)

**Filed 2026-08-11. Build-order item 7. Seventh subline gate**, differential against
[334](GATE-334-PREMISES-OPERATIONS.md), [336](GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md),
[335 OCP](GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md), [332](GATE-332-LIQUOR-LIABILITY.md),
[335 Railroad](GATE-335-RAILROAD-PROTECTIVE.md) and [365](GATE-365-WITHDRAWAL-LOED-CYBER.md).

**As-of date: 2026-08-11.** Required, not assumed (N4). Derived against **`GL_CW_20231201_V03`**.

---

## 0. This gate settles N13's oldest open question

The drone sentinel has been on the record since the cross-derivation comparison, and it is the
**one** entry in the zero taxonomy that has never had an in-corpus discriminator. N13 currently
reads:

> `UnmannedAircraftUsageBIPDRatingModifiers` carries `0` for firefighting, crop-spraying and
> internet access — refer-to-company uses — read by `ErcSetRatesAndFactors` **with no guard**.

**Every clause is right, and the count is wrong.** The table carries **five** zeros, not three, and
the two it misses are the ones most likely to be hit in practice.

### The manual decodes it exactly: 24 of 24 cells

`GL-MU-2027-RU-001-C` p.68, **Table 37.E Usage Rating Modifiers**, against ERC's
`UnmannedAircraftUsageBIPDRatingModifiers` and `…UsagePAIRatingModifiers`:

| # | Usage | BI/PD manual | ERC | PAI manual | ERC |
|---|---|---|---|---|---|
| 1 | Aerial photography, surveillance, inspection, survey, data collection, media | 1.00 | `1` | 1.20 | `1.2` |
| 2 | **Firefighting, search and rescue, other emergency services** | **RTC** | **`0`** | 0.90 | `0.9` |
| 3 | **Crop spraying, dispersing of chemicals** | **RTC** | **`0`** | 0.90 | `0.9` |
| 4 | **Internet access, other communication services** | **RTC** | **`0`** | **RTC** | **`0`** |
| 5 | Delivery of goods or merchandise, transport of cargo | 1.50 | `1.5` | 0.90 | `0.9` |
| 6 | Weather and environmental monitoring | 1.25 | `1.25` | 0.90 | `0.9` |
| 7 | Education and research | 1.00 | `1` | 1.00 | `1` |
| 8 | Operator/Pilot training | 1.10 | `1.1` | 1.00 | `1` |
| 9 | **Entertainment, demonstrations, special events, sports (incl. drone racing)** | **RTC** | **`0`** | **RTC** | **`0`** |
| 10 | Towing signs or banners, pulling twine or cable, distribution of materials | 1.25 | `1.25` | 1.00 | `1` |
| 11 | Manufacturing, sales, repair or rental of unmanned aircraft — testing only | 0.80 | `0.8` | 0.80 | `0.8` |
| 12 | **Other usage, not otherwise classified** | **RTC** | **`0`** | **RTC** | **`0`** |

**12 rows × 2 columns, all 24 agree.** Five BI/PD `RTC` ↔ **exactly** the five ERC BI/PD zeros;
three PAI `RTC` ↔ **exactly** the three ERC PAI zeros. **`0` means `RTC` — refer to company —
and nothing else.**

Three things follow that the three-zero version of N13 could not say:

1. **N13 undercounted by two, and the two it missed are the dangerous ones.** *"Entertainment,
   demonstrations, special events, sports"* and — worse — **`Other usage, not otherwise classified`**,
   the catch-all a submission lands on whenever the risk does not fit categories 1–11. **The most
   likely usage value in production is a refer-to-company marker that prices at zero.**
2. **The same usage can be a referral on one coverage and a real factor on the other.** Firefighting
   is `RTC` for bodily injury / property damage and **0.90** for personal & advertising injury. So
   the zero cannot be resolved per-usage; it must be resolved **per usage *and* per coverage**.
3. **The mapping is total.** Every ERC zero is an RTC and every RTC is an ERC zero, in both
   directions and both columns. There is no third case to worry about.

### And there is definitively no in-corpus discriminator

Checked exhaustively rather than sampled:

| Check | Result |
|---|---|
| `DoMessage*` rules in `…UnmannedAircraftCovABIPDCoverage` | **0** |
| `DoMessage*` rules in `…UnmannedAircraftCovBPAICoverage` | **0** |
| `DoMessage*` rules in `GeneralLiabilityUnmannedAircraft` | 3 — and none concerns usage |
| The only weight/usage guard in the corpus | `DoMessageWeightOfDroneCheck`: `MaximumTakeoffWeight <= 0` → *"Please enter the Maximum Takeoff Weight to be greater than 0"* |
| Rules referencing `UsageRatingMod` | 2 — both the rating rules that multiply by it |

`AdjustedRate = round(BaseRate × OwnershipAndOpRatingMod × PrimaryPlaceOfOpRatingMod ×
UsageRatingMod, 3)`. **The modifier multiplies with no test of any kind**, and
`SetUsageBIPDRatingModifiers`'s own else-branch writes `0.0` when `Usage` is empty — a sixth path to
a zero premium.

**So the drone case stays the one meaning in the zero taxonomy that needs the manual, and that is
now measured rather than assumed.** Four of the seven meanings have an in-corpus discriminator;
this one provably does not, and the register can stop treating it as unfinished.

**The engine's obligation:** these are a **confirmed-sentinel register entry**, not a scan. Any
of the three rating modifiers resolving to `0` must raise `REFER` before it multiplies. **§7a
corrects the count: 18 cells across three axes, not the 8 this section reached by looking only at
usage.**

---

## 1. The algorithm — CW 2023 V03 / 20260101

Two rate-driven groups: `…UnmannedAircraftCovABIPDCoverage` (bodily injury / property damage) and
`…UnmannedAircraftCovBPAICoverage` (personal & advertising injury), 62 rules across both.

`ErcProcess`: `CoverageOnPolicyIndicator == 0` → `Premium = 0.0`. Else rates and factors → rate.

| # | Rule | What it does |
|---|---|---|
| 1 | `SetAggregateLimit` | via `unmannedAircraftAggregateLimitLookup` |
| 2 | `SetmaximumTakeoffWeightCeiling` | **Empty.** See §2 |
| 3 | `SetLossCost` | `maximumTakeoffWeightCeiling != 0` → `LookupUnmannedAircraftLimitedLiabilityBIPDLossCost`, banded on weight |
| 4 | `SetLCM` | **`LookupPremOpsLCM`** — the Prem/Ops LCM, countrywide, `1` (E15) |
| 5 | `SetClaimsMadeMultiplier` | **`LookupPremOpsClaimsMadeMultiplierAllOther`** |
| 6 | `SetBaseRate` | `round(LossCost × LCM × ClaimsMadeMultiplier, 3)` |
| 7–9 | `SetOwnershipAndOperationBIPDRatingModifiers`, `SetPrimaryPlaceOfOperationBIPDRatingModifiers`, `SetUsageBIPDRatingModifiers` | Three modifiers, 9 / 9 / 12 rows countrywide |
| 10 | `SetAjustedRate` *(sic)* | `round(BaseRate × the three modifiers, 3)` |
| 11 | `SetILF` | 15,857 characters — the largest single rule in any gate so far. `LookupILFPremOps` |
| 12 | `SetDeductibleFactor` | `LookupDedFactorPremOps{CSL,BI,PD}` |
| 13 | `SetPremium` | `AdjustedRate × (ILF − DeductibleFactor) × PackageModFactor × ExperienceRatingModificationFactor × ExpenseModification × ModToUse` (Coverage A); Coverage B drops the deductible term |

**Basis of premium is *each unmanned aircraft*** — a unit count, no ÷1000.

**Drone borrows Prem/Ops's machinery wholesale** — LCM, claims-made multiplier, ILF and all three
deductible tables. It is a factor-on-host coverage like item 6's, but it borrows *tables* rather
than the host's computed values, so it carries no E18 dependency.

**`LookupPremOpsLCM` is live here.** In the liquor and railroad files the same lookup has no caller
([335-RR §5](GATE-335-RAILROAD-PROTECTIVE.md)). That confirms the E14 reframing exactly: it is
**boilerplate copied into every subline file, live where the subline uses the Prem/Ops LCM and
inert where it does not.** Not a deletion defect anywhere.

---

## 2. Two ERC artifacts worth naming

**`SetmaximumTakeoffWeightCeiling` is an empty rule that is still called**, and it carries a
developer comment shipped in the filed data:

```xml
<rul:Rule Name="SetmaximumTakeoffWeightCeiling" …>
  <rul:Sequence>
    <!--Logic for maximumTakeoffWeightCeiling moved to be inline where used.-->
  </rul:Sequence>
</rul:Rule>
```

A **third** kind of inert artifact, after the uncalled lookups (E14) and the orphan tables
(`RailroadLossCost`, `SublineProductWithdrawal`): a *called* rule with an empty body. Harmless, and
worth an engine assertion that distinguishes *empty because neutralised* (N3 — 13 jurisdictions
disabling Defense-Within-Limits) from *empty because refactored*. **The comment is the only thing
that distinguishes them, and comments are not data.**

**`SetAjustedRate` is misspelled** — and its target DataDef, `AdjustedRate`, is not. That spelling
is why OI-42's fix worked: the scope classifier matches `FromDataDef`, and the *DataDef* was
correct while the *rule* was not. Third misspelling found in ERC after `ProductWithdrawl` (OI-47)
and the stale `Refer To Co.` (E17). **In this corpus, a name is evidence of nothing.**

---

## 3. The weight ceiling, and a precise negative result on E1

```
maximumTakeoffWeightCeiling = Convert<int>( round( MaximumTakeoffWeight + 0.499, 0 ) )
```

A ceiling implemented as a rounded offset. Loss-cost bands, from
`UnmannedAircraftLimitedLiabilityBIPDLossCost` (countrywide, 5 rows):

| Weight `>` | `≤` | BI/PD loss cost | PAI |
|---|---|---|---|
| 0 | 1 | 66.11 | 87.63 (0–55) |
| 1 | 5 | 110.19 | |
| 5 | 15 | 154.26 | |
| 15 | 55 | 220.37 | |
| **55** | `2147483647` | **`0`** | **`0`** |

**E1 (the rounding tie-break) is reachable here and cannot change a premium.** Worked through rather
than asserted: `round(w + 0.499, 0)` is an exact midpoint only when `w = n + 0.001`, giving `n` under
`HALF_EVEN` and `n+1` under `HALF_UP` for even `n`. The band edges are **1, 5, 15, 55**, so the two
candidate ceilings must straddle an edge to matter — and they never do:

| Tie at | Candidates | Bands | Differ? |
|---|---|---|---|
| `w = 4.001` | 4 / 5 | both `(1,5]` | no |
| `w = 14.001` | 14 / 15 | both `(5,15]` | no |
| `w = 54.001` | 54 / 55 | both `(15,55]` | no |
| `w = 5.001` · `15.001` · `55.001` | 6 / 6 · 16 / 16 · 56 / 56 | identical | no |
| `w = 0.001` | 0 / 1 | **no band** / `(0,1]` | **yes** |

**Only a drone weighing 0.001 lb is affected**, and `DoMessageWeightOfDroneCheck` does not catch it
(it tests `<= 0`). So E1 is live in theory and dead in practice on this subline — the band edges at
odd values 1, 5, 15, 55 make the tie-break irrelevant. Recorded because E1 is open and every subline
should say whether it bites; this is the first to be able to say **no, and why**.

**The `>55 lb` band is `0` in both coverages** — the finding that first put the drone case in the
zero taxonomy, confirmed here in the table itself. Under §0 it means **RTC**, consistent with the
manual's *"refer to company"* for everything on this subline.

---

## 4. Manual confirmations

Rule 37, *Description Of Unmanned Aircraft Endorsements*, pp. 66–69. **Subline code 370** is stated
in the paragraph heading, `C. Premium Determination (Subline Code 370)`.

| # | ERC | Manual | Verdict |
|---|---|---|---|
| 1 | 5 BI/PD zeros, 3 PAI zeros in the usage tables | **Table 37.E**, p.68 — RTC in exactly those positions | ✅ **24/24 cells, both columns** |
| 2 | `SetClaimsMadeMultiplier` → `LookupPremOpsClaimsMadeMultiplierAllOther` | **C.2.c**, p.67: *"Claims-made multipliers are found in Rule 23. **Use Premises/Operations All Other** claims-made multipliers"* | ✅ Exact, including which variant |
| 3 | Premium per aircraft, no ÷1000 | **C.2.a**: *"Basis of premium is each unmanned aircraft"* | ✅ |
| 4 | Three modifiers multiplied into `AdjustedRate` | **C.2.d**: multiply the adjusted basic limit rate by the Ownership and Operations, Usage, and Primary Place of Operation modifiers | ✅ Confirms all three and their order |
| 5 | *(not implemented)* | **C.2.d(1)–(3)**: *"If more than one … category applies, assign the category with the **highest** rating modifier"* | ⚠️ **ERC takes a single submitted value per axis and has no max-of-many logic.** See §6 |
| 6 | *(not implemented)* | **C.2.a**: *"Refer to company for **non-owned** unmanned aircraft operated by other parties"* | ⚠️ No ERC discriminator |
| 7 | *(not implemented)* | **C.1**: *"For Unmanned Aircraft **Exclusion** options … refer to company for rating"* | ✅ Consistent — the exclusion groups are `CAPTURE`, not rate-driven |

**And the strongest sentence, C.2:**

> *"All applicable loss costs and modifiers referenced in Paragraphs C.2.b. and C.2.d. and **Tables
> D., E. and F. must be referred to company before using**."*

**Unmanned Aircraft is company-rated in its entirety** — the fourth subline after liquor, railroad
and (per Rule 42/43) electronic data and employee benefits. The published loss costs and modifiers
are reference values requiring a company referral, not filed prices.

**One location disagreement, recorded not resolved.** C.2.b says the basic limit rates are *"shown
in the state company rates/ISO loss costs section of the manual"*, but ERC publishes
`UnmannedAircraftLimitedLiabilityBIPDLossCost` **countrywide, with 0 of 51 states populating it**.
ERC is the source and its placement stands; the manual's pointer describes where a *reader* finds
them, not where the data model puts them.

---

## 5. Layer pattern and state deviations

**Countrywide again, entirely.** Every drone rating table is countrywide-only:

| Table | CW | States |
|---|---|---|
| `UnmannedAircraftLimitedLiabilityBIPDLossCost` | 5 rows | **0/51** |
| `UnmannedAircraftLimitedLiabilityPAILossCost` | 2 rows | **0/51** |
| `UnmannedAircraftUsage{BIPD,PAI}RatingModifiers` | 12 rows each | **0/51** |
| `UnmannedAircraft{OwnershipAndOperation,PrimaryPlaceOfOperation}BIPDRatingModifiers` | 9 rows each | 1/51 — **WA** |
| `UnmannedAircraftMinPremium` | 1 row: **`0`** | 0/51 |

**Fifth consecutive subline where the countrywide layer holds the rating operands.** And
`UnmannedAircraftMinPremium = 0` makes **E16 four for four**.

**Nine jurisdictions file drone rules, and eight of them file the identical set:**

| States | Rules overridden |
|---|---|
| **IN, MO, MT, ND, NH, OK, TN, UT** | `SetAggregateLimit`, `SetILF`, `unmannedAircraftAggregateLimitLookup`, **`LookupGovernmentalUnitsPremisesOperationsIncreasedLimitsFactor`** |
| **NY** | `SetClaimsMadeMultiplier` |

The eight are a **single deviation replicated**: a *governmental units* increased-limits variant that
the drone ILF must use. One deviation, eight filings — and a differential engine that treats them as
eight separate state rules will implement the same thing eight times.

**New York overrides the claims-made multiplier again.** Third instance: NY neutralised claims-made
liquor with constant stubs (332 §7), files its own Prem/Ops selector shard
(335-RR §1), and here overrides `SetClaimsMadeMultiplier`. **New York is the most-deviating
jurisdiction in the corpus and should get a dedicated differential fixture** alongside California's
(the sole `V02` parent, [`PHASE-SIZING.md`](../PHASE-SIZING.md) §4).

**Edition stability:** 62 rules in CW 2023 V03 and 2026, **66 in CW 2027** with 8 changed, 6 added
and 2 removed. After railroad's 22 deletions and item 6's rewrite, drone is **the least disturbed
subline at the 2027 boundary** — and its rate tables are byte-identical across all three parents in
force at every date.

---

## 6. Escalations and open items

| # | Item | Detail |
|---|---|---|
| ~~**OI-48**~~ | ~~ERC implements no "highest modifier wins" rule~~ — **closed: broker question** (§7a) | Manual C.2.d(1)–(3) requires that where more than one Ownership / Usage / Place category applies, the **highest** modifier is assigned. ERC reads a single submitted value per axis and cannot express multiplicity. Either the submission is required to pre-resolve it — making this a **submission rule, like OCP's `WorkersCompensationRate`** — or the engine must accept a set per axis and take the max, which ERC does not license. **Ask the user.** Note the interaction: if the *highest* rule ran and one applicable category were `RTC`, the correct answer is a referral, not a number |
| **OI-49** | ~~Non-owned unmanned aircraft is a manual-only referral~~ | **Withdrawn as an instance (§7a): ERC does carry the discriminator**, a `0` on the ownership axis against exactly that category. OI-49 reduces to the railroad non-construction case alone |
| **N13** | **Amend the evidence line** | *Five* BI/PD zeros, not three; **plus three PAI zeros**; manual-decoded 24/24; **no in-corpus discriminator, verified exhaustively** |
| **E1** | **First subline able to say the tie-break cannot bite, and why** | §3 |
| **E14**, **E15**, **E16** | Confirmed again | `LookupPremOpsLCM` live here and inert elsewhere; `LCM = 1`; `MinPremium = 0` |

---

## 7. Test result

**No oracle.** The golden case carries no unmanned aircraft premium. **Fifth consecutive subline
without one.**

| Check | Result |
|---|---|
| `tests/verify_golden.py` | **80/80** (unchanged) |
| ERC usage modifiers vs manual Table 37.E | **24 / 24 cells**, both columns, RTC↔`0` exact both ways |
| Referral cells across all three rating axes | **18 of 60** (§7a) — the usage table alone accounts for 8 |
| `DoMessage*` guards on the usage sentinel | **0**, verified across both rate-driven groups |
| E1 tie-break band crossings at realistic weights | **0** — only `w = 0.001 lb` |
| Rate tables populated by any state | **1 of 7** (WA) |
| Distinct state deviations | **2** (a governmental-units ILF variant ×8, NY claims-made ×1) |

---

## 7a. Decided, and a correction to §0 and §4 that the decision uncovered

**OI-48 is answered: the highest-modifier rule is a broker question.** The submission must arrive
with one resolved category per axis; the engine does not take a set and pick a maximum, which ERC
does not license it to do. **Third "missing input" to resolve as a submission requirement**, after
county/place for CA-FL-NY-TX (OI-34) and `WorkersCompensationRate` for OCP.

**The decision is implementable with no assumption, because ERC already licenses the broker's
escape hatch** — and finding that required counting the other two axes, which §0 had not done.

### The sentinel is 18 cells, not 8

§0 counted the **usage** table and stopped. Counting all three rating axes across both coverages:

| Table | Rows | `0` cells |
|---|---|---|
| `UnmannedAircraftUsageBIPDRatingModifiers` | 12 | **5** |
| `UnmannedAircraftUsagePAIRatingModifiers` | 12 | **3** |
| `UnmannedAircraftOwnershipAndOperationBIPDRatingModifiers` | 9 | **3** |
| `UnmannedAircraftOwnershipAndOperationPAIRatingModifiers` | 9 | **3** |
| `UnmannedAircraftPrimaryPlaceOfOperationBIPDRatingModifiers` | 9 | **2** |
| `UnmannedAircraftPrimaryPlaceOfOperationPAIRatingModifiers` | 9 | **2** |
| | **60** | **18** |

**Nearly a third of the drone rating grid is a referral marker**, and all 18 multiply unguarded into
`AdjustedRate`. The eight distinct categories fall into three kinds:

| Kind | Categories | Cells |
|---|---|---|
| **Uses ISO will not price** | Firefighting · Crop spraying · Internet access · Entertainment/special events/racing · Other usage NOC | 8 |
| **A condition, not a hazard** | **Non-owned unmanned aircraft operated by other parties** | 2 |
| **The submission did not say** | **`Not Applicable`** ×4 · **`Unknown`** ×4 | **8** |

### `Unknown` is a published category, and it is what makes the broker answer safe

**ISO ships `Unknown` and `Not Applicable` as domain values on all three axes, and prices both as
`0` — refer to company.** So a broker who cannot resolve which of several categories applies has a
**filed, licensed way to say so**: submit `Unknown` and the risk refers.

That is the whole reason OI-48 can be answered "broker question" without inventing anything. The
engine does not need max-of-set logic and does not need to guess; **the ambiguity the manual's
highest-wins rule exists to resolve already has a filed representation.** The requirement on the
submission is therefore precise:

> One category per axis. If more than one applies, send the one the manual's highest-wins rule
> selects. **If any applicable category is a referral category, send that one** — a referral
> outranks any number, and "highest" is undefined across a number and an `RTC`. If it cannot be
> resolved, send **`Unknown`**, which is a filed value and refers.

### And OI-49 loses half its case — the discriminator exists

**§4 recorded *"non-owned unmanned aircraft operated by other parties"* as a manual-only referral
with no ERC discriminator** (Rule 37.C.2.a), and filed it as OI-49(b).

**That was wrong.** `UnmannedAircraftOwnershipAndOperationBIPDRatingModifiers` and its PAI twin
each carry a `0` against the row **"Non-owned unmanned aircraft operated by other parties"**. ERC
expresses the referral exactly, in the same sentinel form as the usage cases.

**Same mistake as §0's undercount, one table over:** I checked the axis the finding was about and
did not check the neighbouring axes. **OI-49 reduces to one instance** — the railroad
non-construction case — which remains genuinely manual-only.

---

## 8. Findings

- **The project's oldest open sentinel is closed as a question and confirmed as a hazard.** It was
  raised by comparing two sources; it is settled by comparing them again, cell for cell. **`0` = RTC,
  in 8 of 24 positions, with no in-corpus discriminator — verified exhaustively, not sampled.**
- **N13 undercounted the sentinel by two, and the two it missed matter most.** `Other usage, not
  otherwise classified` is the catch-all. **A register of confirmed sentinels is only as good as its
  last recount** — the entry had been carried unchanged since the comparison pass.
- **The same value means different things in adjacent columns.** Firefighting is `RTC` for BI/PD and
  `0.90` for PAI. Any sentinel register keyed on *(table, value)* is wrong; it must be keyed on
  *(table, column, row)*.
- **E1 can be closed per-subline even while it stays open globally.** Working the band edges against
  the tie rule gives a definite *no* for drone. That is a cheaper answer than waiting for RAaS, and
  the other sublines deserve the same treatment.
- **Eight states filing one deviation is one deviation.** The state-rule counts in phase sizing
  count filings, not distinct behaviours — the same conflation, one level down, as the item-6
  substring error.
