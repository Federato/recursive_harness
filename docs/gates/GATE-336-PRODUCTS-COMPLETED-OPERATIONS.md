# Gate — Subline 336, Products/Completed Operations

**Build-order item 2** (`GL-RATING-ENGINE-BUILD-PLAN.md` §8). Presented against the eight-point
per-subline gate in §9.

**Status: PASSED.** Derived end to end from ERC, reproduces the Oklahoma golden case exactly —
`Premium = 6,845.00` — and with 334 closes the policy total to the dollar: **976 + 6,845 + 18 =
7,839**.

**This gate is deliberately differential.** 336 shares the classification machinery, the resolver,
the two inheritance mechanisms and the rounding sites with 334; those are derived in
[`GATE-334-PREMISES-OPERATIONS.md`](GATE-334-PREMISES-OPERATIONS.md) and not restated. What
follows is what **differs**, and everything the gate requires that is specific to 336.

Runnable fixture: [`tests/fixtures/golden-ok-2025.json`](../../tests/fixtures/golden-ok-2025.json),
verified by [`tests/verify_golden.py`](../../tests/verify_golden.py) — **80/80 checks pass**, three
independent layers (fixture vs ISO's output, fixture vs the ERC CSVs, arithmetic re-derived in
`Decimal`).

---

## 0. The finding: `0` is a *published* value that switches the rating path

The golden case rates 336 off the **expected loss potential**, not a loss cost. The reason is a
single cell:

```
ProdsCompldOpsLossCost.RateTable.csv →  "OK","999","50017",0
```

The row **exists**. Its value is `0`. `SetBaseRate` tests `ProdsCompldOpsLossCost == 0.0` and takes
the ELP branch: `BaseRate = round(ELP × LCM, 3) = round(0.82 × 1.0, 3) = 0.82`.

So `0` here is neither a rate nor a missing value nor a refer-to-company sentinel. It is a
**documented path switch**, and it is the *third* distinct meaning of `0` found in this corpus:

| Meaning of `0` | Example | Discriminator |
|---|---|---|
| a genuine factor | `DedFactorPremOpsCSL` "No Deductible" = `0` | the value is correct as read |
| an **unpublished** factor | all 15 "Per Claim" deductible factors (N13, gate 334 §7) | a `DoMessage*` validation rule |
| an **unguarded refer** | drone `>55 lb` band (N13, the original) | **none in ERC** — the manual |
| a **path switch** *(new)* | `ProdsCompldOpsLossCost = 0` → use the ELP | **a named column: `*ELPText`** |

**Read as a rate, this cell produces `BaseRate = 0` → `Premium = 0` — a free products liability
policy on a class ISO prices at $6,845.**

### The discriminator exists, and it is exact

Step 22 concluded that ERC cannot distinguish a sentinel `0` from a real one. **For the loss-cost
tables specifically, that is now false.** Every subline carries a sibling *rating-basis selector*
table — `PremOpsELPText`, `ProdsCompldOpsELPText`, `LiquorELPText`, `OwnersContractorsELPText` —
keyed on (state, class) and holding a **closed vocabulary**:

| Value | Meaning |
|---|---|
| `Rate/Loss Cost Applies` | rate from the published loss cost |
| `Industry` | rate from the industry ELP |
| `Company` | rate from the company ELP |
| `Not Applicable` | the coverage is not offered for this class |

For the golden case: `PremOpsELPText[OK,50017] = "Rate/Loss Cost Applies"` (loss-cost path, 0.095)
and `ProdsCompldOpsELPText[OK,50017] = "Industry"` (ELP path, 0.82). **The selector states what the
rules only imply.**

Tested corpus-wide (`scripts/erc/28_elp_selector.py`, 572 packages):

```
PremOpsELPText          665,927 rows   4 distinct values
ProdsCompldOpsELPText   665,927 rows   4 distinct values
LiquorELPText             4,531 rows   2 distinct values
OwnersContractorsELPText  6,031 rows   3 distinct values

Prem/Ops — selector agrees with `LossCost != 0`:
  agree      620,856
  DISAGREE         0   (0.0000%)
  untestable       0
```

**620,856 checks, zero disagreements.** So:

- **New N17.** The engine reads the rating basis from `*ELPText`, **and asserts it agrees with the
  `LossCost != 0` test the rules branch on.** A disagreement is a load-time hard failure, not a
  warning — it means one of the two is wrong and the premium would be silently off by the whole
  base rate.
- This **narrows N13** rather than widening it. Two of the four zero-meanings now have an in-corpus
  discriminator (`DoMessage*` rules; the `*ELPText` selector). Only the drone case still needs the
  manual and the hand-maintained sentinel register.
- It is the same shape as the seven escalations that dissolved in Step 22: **the discriminator was
  in the corpus and nobody had opened the table.**

---

## 1. The algorithm — how 336 differs from 334

`ErcSetRatesAndFactors` runs **35** steps (334: 29) and `ErcRate` **6** (334: 4). Same order, same
`if IsNull` override-guard idiom, same `FirstNonNull(state, "CW")` lookups.

**Steps 336 has that 334 does not:**

| Rule | Effect |
|---|---|
| `SetTerritory` | copies `../../../ProdsCompldOpsTerritory` — **a second, independent territory**, statewide `999` in the golden case, where 334 used `501` |
| `SetSprayPainting` | classification qualifier carried into rating |
| `SetDefenseWithinLimitsBasicLimitMultiplier` | a **fourth** base-rate factor — see §6, switched off in 13 jurisdictions today and 19 across all editions |
| `SetSplitLimitWeightFactorProds{BI,PD,Constant}` | split-limit weights, computed on every quote |
| `SetDedFactorProdsPD250PerClaim` | a named single-cell deductible carve-out |
| `SetProdsCompldOps{BIPD,PD}DeductibleFactorBeforeAdjustment` | a pre-adjustment stage 334 has no equivalent of |
| `SetMinimumPremium` + `SetMinPremium` | **inside `ErcRate`** — 336 computes its own minimum; 334 does not |

**Steps 334 has that 336 does not:** `SetBringYourOwnAlcoholExclusionFactor` (liquor classes
16905/16906), `SetMedicalPaymentsFactor` and `SetMedicalPaymentsCharge` — **medical payments is a
Premises/Operations coverage and does not touch 336 at all.**

### The arithmetic

```
BaseRate  = round( LossCost | ELP  × LCM  [× ClaimsMadeMultiplier]
                                          [× DefenseWithinLimitsBasicLimitMultiplier] , 3)
FinalILF  = round( CSLILF − FinalDeductibleFactor , 3)          # clamped to 0.0 if ≤ 0
FinalRate = round( BaseRate × FinalILF [× SizeOfRiskFinalRelativity]
                            × PackageModFactor × ExperienceRatingModificationFactor
                            × ExpenseModification × ModToUse , 3)
Premium   = round( FinalRate × Exposure[/1000] , 0)
MinPremium= round( MinimumPremium × FinalILF × AdditionalInterestFactor , 0)
```

**`FinalILF` has no medical-payments term in either edition** — so 336 is *not* subject to the
edition split that dominates gate 334 §0. Its chain is the same under CW 2023 V03 and CW 2027 V01.
That is worth stating plainly: **the edition axis is real but not uniform, and must be established
per coverage rather than assumed from 334.**

**The `DefenseWithinLimits` selector is `Exist`, not a value.** `SetBaseRate` branches on
`Exist AtInputDataDef=".../GeneralLiabilityDefenseWithinLimitsProdsCompldOpsTable/…"` — the
*presence of a row*, not a flag. An engine modelling it as a boolean field will never enter the
branch.

### E11 is answered — `AdditionalInterestFactor` **is** consumed

Gate 334 raised E11: the factor is computed on every quote and read by no rule. **336 reads it** —
`MinPremium = round(MinimumPremium × FinalILF × AdditionalInterestFactor, 0)`. So it is a live part
of the program, and 334's chain genuinely does not use it. E11 narrows from *"is this dead?"* to
*"is 334's omission intended?"*, and the engine implements it exactly where ERC reads it and
nowhere else.

---

## 2. Confirmations

| Claim | Manual says | Citation | Verdict |
|---|---|---|---|
| Prod/CompOps is not rated from a published loss cost for OK class 50017 | The loss-cost table prints **`(a)`** in the Prod/CompOps column — *"REFER — consult the ELP"* | `GL-OK-2027-LC-003` p.16, via `iso.py rate OK --class 50017` | **Confirms the ELP path.** ERC encodes the same fact as a `0` cell plus `ELPText = "Industry"`. Two sources, same meaning, different encoding |
| Prod/CompOps split-limit weights, Manufacturing band `50000–59999` | BI `0.87`, PD `0.17`, Constant `0.01` | `GL-MU-2027-RU-001-C` p.33, Split Limits Weight Factors, Products-Completed Operations – All Tables | **Confirms the golden case exactly** — `0.87 / 0.17 / 0.01` |
| Prem/Ops weights, same band | BI `0.83`, PD `0.19`, Constant `0.03` | same page, Premises-Operations – All Tables | **Confirms 334 exactly** (gate 334 §2) |
| Separate ILF tables per subline | *"Separate increased limits tables are applicable for Premises-Operations and Products-Completed Operations."* | same page, Rule 56.D.4 | **Confirms** the two distinct assignment tables and their distinct vocabularies (§5) |

**No disagreement was found between the two sources on the 336 algorithm.** Both split-limit weight
rows match ISO's own rated output, from a source with no access to it — the second such
cross-confirmation in two gates.

> **Method note.** This row was first written up as a *disagreement* (`0.66 / 0.24 / 0.15`), from a
> keyword-search excerpt that truncated two rows above the Manufacturing line — the Mercantile
> values were read as Manufacturing's. Fetching the full page corrected it. The same failure mode as
> the whitespace false-negatives in `README.md`: **in this corpus a partial read looks exactly like
> an answer.** Search to locate the page; read the page to make the claim.

---

## 3. Escalations

| # | Question | Engine behaviour meanwhile |
|---|---|---|
| **E1** | Rounding tie-break | 336 adds four sites — `BaseRate` 3dp, `FinalILF` 3dp, `FinalRate` 3dp, `Premium` 0dp. **None is a tie in the golden case**, proven mechanically: `verify_golden.py` re-runs the whole chain under `ROUND_HALF_EVEN` and gets the identical premium. No evidence gained |
| **E11** | `AdditionalInterestFactor` | 🟡 **narrowed** — it is consumed by 336's `SetMinPremium`. Question is now whether 334's omission is intended, not whether the field is dead |
| ~~**E12**~~ | ~~`PremOpsELP` compared as both string and decimal~~ | ✅ **closed — dissolved on reading.** See below |

### E12 closed — it was never a type inconsistency

Gate 334 flagged `SetMedicalPaymentsCharge` for testing `../PremOpsELP` as a **string** against
`"Rate/Loss Cost Applies"` in one branch arm and `PremOpsELP` as a **decimal** against `0.0` in
another. Reading the classification-level rules shows these are **two different DataDefs at two
levels**, and the `../` prefix says so:

- `../PremOpsELP` — **classification level, string.** Written by `SetPremOpsELP` from
  `LookupPremOpsELPText`. It is the **rating-basis selector** of §0.
- `PremOpsELP` — **coverage level, decimal.** The ELP factor itself.

The rule is testing *"does this class rate off a loss cost?"* and it is doing so correctly, against
the authoritative selector. **The eighth escalation to dissolve on being read rather than answered**
— and, as with the other seven, it had been raised from a name without the sibling table being
opened. My own gate-334 write-up made exactly the error the standing criterion warns about, one
document after restating it.

---

## 4. Inputs consumed, and behaviour when absent

Shares 334's pattern; the 336-specific entries:

| Input | ERC on absence | **Engine** |
|---|---|---|
| `ProdsCompldOpsTerritory` | `Territory = ""` → the loss-cost lookup misses → ELP path | `REFER` |
| `ProdsCompldOpsCovExposure` | `0.0` → `Premium = 0`, and **336 has no `$1` floor in either edition** | `REFER` unless `IfAnyBasisProdsCompldOps = "Yes"` |
| `ProdsCompldOpsCov` | anything but `"Products/Completed Operations"` → `BaseRate = 0.0` via the `Otherwise` arm | validate against the domain |
| `ProdsCompldOpsPremiumBasis` | `""` → the non-÷1000 branch, 1000× high | `REFER` |
| `IfAnyBasisProdsCompldOps` | not `"No"` → `MinPremium = 0.0`, minimum silently not applied | require it |
| `GeneralLiabilityDefenseWithinLimitsProdsCompldOps` row | absent → the DWL multiplier is not applied (correct) | model as **row presence**, never a boolean |

**`ProdsCompldOpsCovExposure` must not exceed `PremOpsCovExposure`** —
`DoMessageProductsCompletedOperationsExposureCannotBeGreaterThanPremisesOperationsExposure`, a
cross-subline validation living in the classification rules. A second N15 instance: a guard that a
coverage-by-coverage port would drop.

---

## 5. Lookups and their layer

Same split as 334, measured on the same two packages:

| Table | Countrywide | Oklahoma | Layer |
|---|---|---|---|
| `ProdsCompldOpsLossCost` | **0 rows** | 1,188 | **state only** |
| `ILFProds` | **0 rows** | 432 | **state only** |
| `ProdsCompldOpsELPFactor` | **0 rows** | 1,188 | **state only** |
| `ProdsCompldOpsELPText` | **0 rows** | 1,188 | **state only** |
| `IncreasedLimitsTableAssignmentProdsCompldOps` | absent | 1,188 | **state only** |
| `ProdsCompldOpsMinPremium` | 3 | absent | **countrywide only** |

Four more header-only countrywide tables in a live rating path (N7).

**A typing trap.** 334's increased-limits table assignment is **numeric-as-string** (`1`, `2`, `3`)
and is converted by `SetFinalPremOpsIncrdLimitTableAssignmentInt`. **336's is alphabetic** — `A`,
`B`, `C` — and **has no `…Int` conversion rule at all.** One `TableAssignment` type across both
sublines will fail on 336, and the golden case (`"B"`) proves it immediately. The two vocabularies:

| | Values | Non-values |
|---|---|---|
| **334** `PremOpsIncrdLimitTableAssignment` | `1` `2` `3` | `Refer To Co.` |
| **336** `IncreasedLimitsTableAssignmentProdsCompldOps` | `A` `B` `C` | `N/A`, `Refer To Co.` |

---

## 6. State deviations — enumerated and quantified

Two counts, and they are **not interchangeable** (`scripts/erc/29_census_336.py`):

| Scope | Overrides anything | Pure countrywide |
|---|---|---|
| **Latest edition per jurisdiction** — what an engine rating *today* must handle | **17** | **34** |
| **Across all 562 packages** — what an engine rating *as of a past date* must handle | **22** | **29** |

Excluding `InitializeRuleSet`/`ErcProcess` plumbing and statistical coding, the premium-affecting
picture is **one deviation, adopted as a block:**

| Rules overridden | Latest edition | All editions | Effect |
|---|---|---|---|
| `SetDefenseWithinLimitsBasicLimitMultiplier` **+** `SetBaseRate` **+** `SetCSLILF`, together | **13** — AK AR AZ CT LA MT ND NJ NV NY PR SD VT | **19** — plus CA FL GA KY VA WA | **Defense-Within-Limits is switched off.** The DWL override is byte-identical everywhere it appears; `SetBaseRate` has 2 distinct bodies currently (4 across editions) |
| `SetCoverageStatCode` | 6 — CT MA MI NC NY VA | 6 | statistical coding only |
| `SetMoldStatCode` | 2 — AK NY | 2 | statistical coding only |
| `SetYearInClaimsMade`, `SetClaimsMadeMultiplier` | 1 — NY | 1 | own claims-made chain (as in 334) |

### The override is empty, and that is the point

```xml
<rul:Rule Name="SetDefenseWithinLimitsBasicLimitMultiplier"
          MetadataCodes="RuleTypeOverridden">
    <rul:Sequence />
</rul:Rule>
```

**A deliberate no-op** — byte-identical in every jurisdiction that carries it. This sharpens N3:
*override is by name and wholesale* — and **the wholesale replacement may be empty.** An engine that
treats an empty or absent rule body as "fall through to the parent" would apply the
Defense-Within-Limits multiplier in 13 jurisdictions that filed it away. **An empty override means
"this does not apply here", never "nothing was filed."**

### And it drifts by edition — a live N4 case

**Six jurisdictions have retired the override: CA, FL, GA, KY, VA and WA.** Virginia carried it in
`GL_VA_20210901_V01` and it is absent from `GL_VA_20230501_V01` onward — verified edition by
edition. So rating a Virginia risk effective in 2022 must apply the empty override; effective in
2025 it must not. This is N4 (*as-of, never "latest"*) with a premium attached, on the second
subline examined.

> **Method note.** The first pass at this section reported 18 current / 19 all-editions, from an
> ad-hoc scan that selected, per jurisdiction, the newest package **that contained the rule file** —
> which is precisely the set biased toward jurisdictions that still have the override. The correct
> selection is the newest package, full stop. Same defect as N4 itself, committed while documenting
> N4: **"latest" must be defined over the whole population, not over the matches.**

---

## 7. Refer-to-company triggers

Inherits 334's list where the machinery is shared. 336-specific:

1. **`IncreasedLimitsTableAssignmentProdsCompldOps = "Refer To Co."`** — same degraded-referral
   mechanism as 334 §7.1: the override substitutes, and if absent the assignment is empty, the ILF
   lookup misses, and the premium becomes `0`. Measured across the latest edition of all 51:
   **102 rows in each of the 334 and 336 assignment tables — present in every one of the 51
   jurisdictions, exactly 2 class codes each.** In Oklahoma they are **`54444`** and **`94444`**, the
   catch-all "not otherwise classified" codes. **This is not an exotic path; it is a standing,
   universal referral on the classes most likely to be selected for an unusual risk.**
2. **`Assignment = "N/A"`** — 21,021 rows, **35% of the 336 table.** Coverage not offered for that
   class. `NOT_OFFERED`, never `0`. 334 has no equivalent value.
3. **`ELPText = "Not Applicable"`** — 261,973 rows in `ProdsCompldOpsELPText`, the selector's own
   not-offered marker. Must agree with (2); an assertion, per N17.
4. **`FinalILF ≤ 0` → `0.0`** — clamped, as in 334. Refer.
5. **Prod/CompOps exposure exceeding Prem/Ops exposure** — validation rule, §4.

---

## 8. Test result — the Oklahoma golden case

Same policy as gate 334; the 336 half. Class `50017`, territory **`999`** (statewide), Gross Sales
`5,000,000`, `1,000,000 / 2,000,000 CSL`, occurrence form, no deductible, no size-of-risk.

| Step | Rule | Derivation | Value | ISO |
|---|---|---|---|---|
| ILF table | `LookupIncreasedLimitsTableAssignmentProdsCompldOps` | `"OK","50017","B"` | `B` | `B` ✓ |
| loss cost | `LookupProdsCompldOpsLossCost` | `"OK","999","50017",0` — **published zero** | `0.0` | `0.0` ✓ |
| basis | `LookupProdsCompldOpsELPText` | `"OK","50017","Industry"` → **ELP path** | `Industry` | — |
| `ProdsCompldOpsELP` | `LookupProdsCompldOpsELPFactor` | `"OK","50017",0.82` | `0.82` | `0.82` ✓ |
| `DefenseWithinLimits…` | not overridden in OK; no DWL row | | `1.0` | `1.0` ✓ |
| `BaseRate` | `SetBaseRate`, ELP arm | `round(0.82 × 1.0, 3)` | `0.82` | `0.82` ✓ |
| `CSLILF` | `LookupILFProds` | `"OK","B","1,000,000 CSL","2,000,000 CSL",1.67` | `1.67` | `1.67` ✓ |
| `FinalILF` | `SetFinalILF` | `round(1.67 − 0.0, 3)` | `1.67` | `1.67` ✓ |
| `FinalRate` | `SetFinalRate` | `round(0.82 × 1.67 × 1 × 1 × 1 × 1, 3)` = `round(1.3694, 3)` | `1.369` | `1.369` ✓ |
| `BasicLimitPremium` | `SetBasicLimitPremium` | `round(0.82 × (1 − 0) × 1.0 × 5000, 0)` | `4,100` | `4,100.00` ✓ |
| `MinimumPremium` | `LookupProdsCompldOpsMinPremium` | CW table → `0` | `0.0` | `0.0` ✓ |
| `MinPremium` | `SetMinPremium` | `round(0 × 1.67 × 1.0, 0)` | `0` | `0.0` ✓ |
| **`Premium`** | `SetPremium` | `round(1.369 × 5000, 0)` | **`6,845`** | **`6,845.00`** ✓ |

**Policy total reconciles exactly:**

| | |
|---|---|
| 334 Premises/Operations | `976.00` |
| 336 Products/Completed Operations | `6,845.00` |
| Terrorism (Prem/Ops `2` + Prod/CompOps `16`) | `18.00` |
| **`ErcCalculatedTotalPremium`** | **`7,839.00`** ✓ |

### Terrorism rated — the recorded gap is narrower than stated

The remaining `18.00` is terrorism, and **ERC supplied the factors**: exposure-class factor `0.004`
(premises and products), NBCR factor `0.58`, `TerrorismILF 0.94` — none of them in the input, which
carried `TerrorismCoverage: "No"` and an exposure-class factor of `0.0`.

`README.md` lists the Terrorism Supplement as genuinely absent, with the effect *"Terrorism premium
cannot be computed."* **On this evidence that is too strong.** Terrorism is build-order item 9 and
is not adjudicated here — but the claim is now marked as needing a population audit before it is
repeated, which is what the build plan already schedules for item 9.

---

## 9. Corrections filed

| Document | Was | Now |
|---|---|---|
| §4, new **N17** | — | **The rating basis is declared, not inferred.** Read `*ELPText`; assert it agrees with the `LossCost != 0` branch test. 620,856/620,856 agree today; a disagreement is a load-time hard failure |
| §4, N13 | four zero-meanings, no discriminator | **Two of the four now have an in-corpus discriminator** — `DoMessage*` rules, and the `*ELPText` selector. Only the drone case still needs the manual |
| §4, N3 | *"override is by name, wholesale — never a row patch"* | Add: **the wholesale replacement may be empty.** 13 jurisdictions currently disable Defense-Within-Limits with `<rul:Sequence />`. Empty ≠ absent ≠ inherit |
| §4, N4 | 83 future-dated packages | Add a live case: **six jurisdictions (CA FL GA KY VA WA) retired the DWL override.** VA carried it in 2021; absent from 2023 on. Same jurisdiction, different answer by effective date |
| §6 | one premium chain | The **edition split is per coverage.** 336's chain is identical under CW 2023 and CW 2027; 334's is not. Establish it per coverage, never inherit the finding |
| §5/§6 | `TableAssignment` | **334 is numeric (`1`/`2`/`3`, with an `…Int` conversion); 336 is alphabetic (`A`/`B`/`C`, with none).** Distinct types |
| §7, E11 | open — computed and never read | 🟡 **narrowed** — consumed by 336's `SetMinPremium` |
| §7, E12 | open — type inconsistency | ✅ **closed.** Two different DataDefs at two levels; `../PremOpsELP` is the rating-basis selector. **Eighth escalation to dissolve on reading** |
| §11, testing | golden case available | **Now runnable**: `tests/verify_golden.py`, 80/80, three layers |
| `README.md` | *"Terrorism premium cannot be computed"* | Too strong — ERC supplied every terrorism factor in the golden case. Audit at build-order item 9 before repeating |

---

## 10. Verdict

**Gate passed**, and the differential format worked: 336 took a fraction of 334's effort because the
shared machinery was already derived, while still surfacing four things 334 could not have shown —
the published-zero path switch, the selector that disambiguates it, the empty override, and the
edition drift in Virginia.

**The four habits from gate 334 all paid out again:**

1. *Resolve the declared parent* — established that 336, unlike 334, has **no** edition split.
2. *Read the `DoMessage*` rules* — surfaced the cross-subline exposure validation.
3. *Count table rows* — four more header-only countrywide tables.
4. *Test every `0` against its consuming branch* — found the fourth meaning of `0`, and the column
   that resolves it.

**Two more to carry forward:**

5. **When two sublines share a mechanism, diff them rather than deriving twice.** The
   `TableAssignment` typing trap and the absent `MedicalPaymentsCharge` are both invisible from
   inside either subline alone.
6. **Search to locate a page; read the page to make the claim.** A keyword excerpt truncated two
   rows above the one I needed and produced a confident, wrong disagreement (§2). Caught before it
   was filed, but only by re-fetching. In this corpus a partial read is indistinguishable from an
   answer — the same defect as the whitespace false-negatives already recorded in `README.md`.

**Next:** build-order item 3, OCP / Principals Protective (335) — the first coverage where **both
the loss-cost and ELP paths must exist at once**, and the first real test of N17 outside the two
sublines that established it.

> Gate 335 has since been written. The build plan's *"published in 15 jurisdictions, withdrawn in
> 36"* turned out to be **8 / 43, and an edition split rather than a jurisdiction split** — see
> [`GATE-335`](GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md) §0.
