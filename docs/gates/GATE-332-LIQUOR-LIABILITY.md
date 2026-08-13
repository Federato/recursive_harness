# Gate — Liquor Liability (subline 332)

**Filed 2026-08-11. Build-order item 4. Fourth subline gate, written differentially** against
[334](GATE-334-PREMISES-OPERATIONS.md), [336](GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md) and
[335](GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md) — shared machinery is cited, not re-derived.

**As-of date: 2026-08-11.** Required, not assumed (N4). Every count below is over the **51 packages
in force on that date** unless a row is explicitly labelled `2027-04-01`. The three countrywide
parents in force are `GL_CW_20231201_V02`, `…V03` and `GL_CW_20260101_V01`; **V03 and 20260101 are
byte-identical for this coverage group**, so today's liquor algorithm has **two** live variants, not
three ([`PHASE-SIZING.md`](../PHASE-SIZING.md) §4).

Derived against **`GL_CW_20231201_V03`** — the parent the OK golden case declares (habit 1), read
from its XSD import, not the newest package.

---

## 0. The prediction, and the result

This is the first gate to **test a prediction on the record** rather than discover its finding.
Step 31 predicted, from `LiquorELPText` carrying only `Industry` and `Company`:

> liquor is *entirely* ELP-or-refer, with no loss-cost path even in principle.

**Confirmed, three ways, and the third is stronger than the prediction.**

| Evidence | Result |
|---|---|
| **The vocabulary** | `LiquorELPText` carries exactly two values corpus-wide: `Industry` ×251, `Company` ×111 — **362 rows, 51 of 51 jurisdictions, no `Rate/Loss Cost Applies`, no `Not Applicable`.** At 2027-04-01 the table doubles to 744 rows and stays two-valued (`Industry` 470 / `Company` 274) |
| **The table inventory** | **No `Liquor*LossCost` table exists in any jurisdiction at any edition.** Liquor's rate tables are `LiquorELP` (51), `LiquorELPText` (51), `LiquorHomogeneityIndex` (51), `ILFLiquor` (50), `LiquorLiabGrade` (41) |
| **The rule** | **`SetBaseRate` has no loss-cost branch at all.** In 334/336 it branches on `LossCost != 0`; here it is unconditionally `BaseRate = round(ELP × LCM, 3)` |

The third is the real result. **The prediction was that no class would say `Rate/Loss Cost Applies`;
the finding is that there is no branch that would consume it if one did.** N17's selector is
*written* for liquor and **read by no rating rule** — `SetLiquorELP` populates it into the
classification output and nothing downstream tests it.

**And the manual says so outright.** `GL-MU-2027-RU-001-C` **p.95**, Rule 45.E *Company Rates*,
in full:

> **"For rates, refer to company."**

So the ELP path is not a fallback that happens to be the only one populated. **ISO publishes no
liquor rate, by rule.**

That sentence is **not unique to liquor** — it is a standard ISO paragraph, appearing three times in
this manual: Rule 42 (Electronic Data Liability), Rule 43 (Employee Benefits Liability) and Rule 45.
Checked rather than assumed, because a one-line confirmation this decisive is worth knowing the
generality of. **"Company rates" is a recognised ISO coverage category**, and liquor is one of three
GL members of it. Two of those three — 325 and 332 — are already in the build order; the engine
needs one *company-rated* strategy, not a liquor special case.

### The N17 test still passes, on a different axis

With no `LossCost` branch to agree with, N17's usual test is undefined here. The available test is
whether the selector agrees with the **ELP value**:

| `LiquorELPText` | ELP rate | Rows | Agreement |
|---|---|---|---|
| `Industry` | **> 0** | 251 | 251 / 251 |
| `Company` | **= 0** | 111 | 111 / 111 |

**362 agreements, 0 disagreements**, all 51 jurisdictions. Fourth corpus-wide corroboration of N17
after Prem/Ops (620,856), Prod/CompOps and OCP (433/433, 147/147) — and the first on a subline with
no loss-cost path, which makes it the cleanest statement of what the selector actually means:
**`Company` = refer to company = published ELP of `0`.**

---

## 1. The algorithm — CW 2023 V03 / 20260101

Every step cites `GeneralLiabilityClassificationLiquorCoverageRules.Rule.xml` in the resolved
countrywide parent unless stated.

**Entry — `ErcProcess`.** If `CoverageOnPolicyIndicator == 0` → `Premium = 0.0` and **stop**. Else
`ErcSetRatesAndFactors` → `ErcRate` → `ErcSetStatisticalCodes`.

**`ErcSetRatesAndFactors`, in order:**

| # | Rule | What it does |
|---|---|---|
| 1 | `SetPremiumBasis` | `PremiumBasis ← ../LiquorPremiumBasis`, else `""` |
| 2 | `SetELPOverride` | `ELPOverride ← ../LiquorELPOverride`, else `0.0` |
| 3 | `SetELP` | Requires **both** `LiquorClassDescription` and `LiquorClassCode` non-empty. Then `ELP ← LookupLiquorELP` if `ELPOverride == 0.0`, else the override. **Otherwise `ELP = 0.0`** |
| 4 | `SetDeductibleFactorOverride` | `DeductibleFactorOverride ← ../LiquorDedFactorOverride`, else `0.0` |
| 5 | `SetLCM` | `LCM ← LookupLiquorLCM` — **countrywide, one row, value `1`** (§3, E15) |
| 6 | `SetYearInClaimsMade` | Copies the policy value **only if** `LiquorCoverageForm == "Claims Made"`, else `0` |
| 7 | `SetClaimsMadeMultiplier` | Claims-made only: `LookupProdsCompldOpsClaimsMadeMultiplier(min(year, 5))`. **Else `1.0`** |
| 8 | `SetBaseRate` | Occurrence: `round(ELP × LCM, 3)`. Claims-made: `round(ELP × LCM × ClaimsMadeMultiplier, 3)`. No `LiquorCoverageForm` → `0.0` |
| 9 | `SetILF` | Requires `LiquorClassDescription`, `EachCommonCauseLimit` and `AggregateLimit` all non-empty → `LookupILFLiquor`. **Otherwise `0.0`** |
| 10 | `SetDeductibleFactor` | Requires `LiquorClassDescription` and `LiquorDeductible` non-empty → `LookupDedFactorLiquor` if no override, else the override. **Otherwise `0.0`** |
| 11 | `SetFinalILF` | `round(ILF − DeductibleFactor, 3)` |
| 12 | `SetFinalRate` | `round(BaseRate × FinalILF × PackageModFactor × ExperienceRatingModificationFactor × ExpenseModification × ModToUse, 3)` |

**`ErcRate`:**

| # | Rule | What it does |
|---|---|---|
| 13 | `SetMinimumPremium` | `Subline == "Liquor"` → `LookupProdsCompldOpsMinPremium(ILTA = "C")` — **hardcoded `"C"`**. Else `0.0` |
| 14 | `SetMinPremium` | `Subline == "Liquor"` **and** `MiscIfAnyBasis == "No"` → `round(MinimumPremium × FinalILF, 0)`. Else `0.0` |
| 15 | `SetPremium` | See below |
| 16 | `SetPremiumIndicator` | — |

**Step 15, `SetPremium`**, is three nested guards:

1. `Subline == "Liquor"`, else `Premium = 0.0`;
2. `PremiumBasis` non-empty **and `!= "Refer To Co."`**, else `Premium = 0.0`;
3. if `PremiumBasis` ∈ {`Admissions`, `Area`, `Gallons`, `Gross Sales`, `Passenger Days`, `Payroll`,
   `Total Cost`, `Total Operating Expenses`, `Vehicles`} →
   `Premium = round(FinalRate × LiquorExposure / 1000, 0)`;
   **else** `Premium = round(FinalRate × LiquorExposure, 0)`.

**Every write is wrapped in an `IsNull` guard**, so a value supplied on the submission is never
overwritten. This is the same guard family whose *absence* distinguishes `GL_CW_20231201_V02` from
V03 ([`PHASE-SIZING.md`](../PHASE-SIZING.md) §4) — a reminder that California, the sole V02
jurisdiction, runs a materially different rule set.

### What changes at 2027-04-01

| Change | Detail |
|---|---|
| **Minimum premium withdrawn** | `SetMinPremium` and `SetMinimumPremium` are **deleted**, and `ProdsCompldOpsMinPremium` goes from 3 rows to **0**. `ErcRate` drops to `SetPremium` → `SetPremiumIndicator` |
| **The `$1` floor arrives** | If the calculated premium rounds to `0` but `LiquorExposure > 0` → `Premium = 1.0`. Same floor 334 and 335 found in CW 2027 |
| **The premium-basis vocabulary is replaced** | 9 generic bases → **2 rateable** (`Gross Sales of Alcoholic Beverages`, `Gross Sales of Food and Beverages`, both ÷1000) plus `Each License` / `Each Licensed Location` / `Each Self-serve Station` (×units) and `Refer to Company` |
| **The `Subline == "Liquor"` guard is dropped** from `SetPremium` |
| **`SetELP` loosens** | Drops the `LiquorClassDescription` condition; keys on `LiquorClassCode` alone |
| **48 rules, not 50**; 5 of the surviving 48 have different bodies |

---

## 2. Manual confirmations

Nine, all from `GL-MU-2027-RU-001-C` Rule 45, *Liquor Liability Coverage (Subline Code 332)*,
which spans **pp. 93–103**. **None sources a value; each confirms something already in ERC.**

Page numbers were taken by locating each string **inside the Rule 45 span** and reading the page,
not by searching the manual and trusting the first hit — the first search for *"For rates, refer to
company"* returned **p.86**, which is Rule 42, eleven pages before Rule 45 begins. Habit 6, and it
would have produced a confident wrong citation.

| # | ERC artifact | Manual | Verdict |
|---|---|---|---|
| 1 | No liquor loss-cost table anywhere; `BaseRate = ELP × LCM` | **45.E, p.95: *"For rates, refer to company."*** | ✅ **Confirms the whole gate.** ISO publishes no liquor rate by rule |
| 2 | `DedFactorLiquor` — all 21 options `0` | **45.J.3, p.102: deductible discount factors *"must be referred to the company before using"*** | ✅ The zeros are **deliberate**, not a publication gap |
| 3 | Liquor reuses `ProdsCompldOpsMinPremium` and `…ClaimsMadeMultiplier` | **45.J.3, p.102** directs the reader to *"Products/Completed Operations Deductible Discount Factors … Rule 15., Table 15.E.6."* | ✅ Confirms the cross-subline reuse is intended |
| 4 | `Premium = FinalRate × Exposure ÷ 1000` on Gross Sales bases | **45.G, p.96**: *"Gross Sales of Alcoholic Beverages **– per $1,000 gross sales**"* | ✅ Confirms the ÷1000, which ERC states only as an integer constant |
| 5 | `Refer to Company` as a **premium-basis value** | **45.G, p.96**, class 50941: *"Premium Base: Refer to company"* | ✅ Confirms a refer marker occupying a data field, not an error state |
| 6 | 16 new class codes at the cliff | **45.G, pp.96–101** lists exactly **50941–50957** | ✅ **Set-exact** against ERC's 16 new codes (§10) |
| 7 | `LiquorLiabGrade = 0` ×16 countrywide | **45.H.1, p.101: Grade 0 = *"no cause of action against one who supplies … liquor"*** | ✅ **A genuine zero.** Sixth meaning, and the first that is unambiguously a real value |
| 8 | CW grades are all `0`; 41 states file their own | **45.G, p.96**, every class: *"Liquor Liability Grade: Refer to state exceptions"* | ✅ The countrywide zeros are placeholders, and the manual says so |
| 9 | `SetFinalILF = ILF − DeductibleFactor`; premium = rate × units | **45.I.5–I.6, pp.101–102** | ✅ Confirms the chain shape |

**Rule 45.I.9, p.102** — *"Use the premium developed in Paragraph I.8. or the policywriting
**minimum premium**, whichever is greater"* — describes a **policy-level** minimum. ERC's `MinPremium` is
classification-level and computes to `0` today (§3, E16). These are different objects; the manual's
policywriting minimum is **not in ERC's liquor chain at all**. Recorded, not resolved: it belongs to
build-order item 13, policy assembly.

---

## 3. Escalations

| # | Issue | Evidence | What the engine does meanwhile |
|---|---|---|---|
| **E15** *(new)* | **`LiquorLCM = 1` is a placeholder for a company input, not a rate.** One countrywide row, `CW / Y / 1`, no state override anywhere, at any edition. An LCM is the carrier's loss-cost multiplier; ISO cannot supply it, and Rule 45.E says *refer to company*. Taken at face value, `BaseRate = ELP × 1 = ELP` — **a pure ISO expected-loss figure with no company markup, which is not a price** | `LiquorLCM` 1 row CW, 0 rows in 51 states; `PremOpsLCM` identical | **Treat a resolved `LCM` of exactly `1` as `REFER`, not as a factor.** Escalated because ERC provides no discriminator between "the LCM really is 1" and "supply one" |
| **E16** *(new)* | **The liquor minimum premium is structurally zero.** `ProdsCompldOpsMinPremium` publishes `A/B/C = 0, 0, 0` countrywide; no state overrides; `SetMinimumPremium` hardcodes ILTA `"C"`. So `MinPremium = 0 × FinalILF = 0` for every liquor risk. CW 2027 deletes both rules and empties the table — **consistent with the value never having been published** | 3 rows, all `0`; 0/51 states | Apply `0` as ERC writes it, and **do not** substitute the manual's policywriting minimum (45.I.9) — that would be tier-2 sourcing |
| **E17** *(new)* | **The refer sentinel's spelling is edition-scoped.** `SetPremium` tests `"Refer To Co."` in all nine pre-2027 editions and `"Refer to Company"` in CW 2027. **At 2027-04-01 both strings are live in the corpus simultaneously** — the 8 unmigrated jurisdictions carry the old spelling, the 43 migrated ones the new | Domain values at the cliff: `Refer To Co.` ×2, `Refer to Company` ×1 | **No global sentinel constants.** Every sentinel string is resolved from the same package as the rule that tests it. A single hardcoded spelling is wrong for 8 or 43 jurisdictions |

**E14 is no longer an isolated case.** The liquor file ships **two lookups with no caller** —
`LookupNoDedStatCode` and `LookupPremOpsLCM` — joining `LookupPrincipalsProtvLiabFactor` (OCP,
CW 2027). Three instances across three sublines. **Recommend E14/OI-38 be reframed from *"is this a
deletion defect?"* to *"ERC routinely ships uncalled lookups; treat an uncalled lookup as inert."***

---

## 4. A defect in ERC's own 2027 edition

**Found by reading the file, and it is not a premium error.**
`SetLiquorExposureStatCode` in `GL_CW_20270401_V01` makes **three string comparisons against the
pre-2027 vocabulary**, none of which can ever match 2027 data:

| Test in CW 2027 | 2027 values that exist | Consequence |
|---|---|---|
| `PremiumBasis == "Gross Sales"` → divisor `1000`, else `1` | `Gross Sales of Alcoholic Beverages`, `Gross Sales of Food and Beverages` | **Never matches. Divisor falls to 1, so the reported exposure is 1,000× too large** on exactly the two bases `SetPremium` divides by 1,000 |
| `PremiumBasis == "Each"` → blank stat code | `Each License`, `Each Licensed Location`, `Each Self-serve Station` | Never matches; a numeric code is padded and reported where a blank is intended |
| `PremiumBasis == "Refer To Co."` → blank stat code | `Refer to Company` | Never matches; a referred risk reports an exposure figure |

**The premium is correct and the statistical report is not.** `SetPremium` was updated to the new
vocabulary in the same edition and the same file; `SetLiquorExposureStatCode` was not. It is an
incomplete rename, and it is **the first defect this project has found inside a filed ISO artifact
rather than inside its own reading of one**.

Reported as an observation, not corrected: under the doctrine ERC is the source, and the engine
implements the rules as filed. **Recorded as OI-43** so it can be raised with ISO rather than
silently patched — and because an engine that "fixes" it would disagree with RAaS.

---

## 5. Inputs consumed, and what happens when one is absent

| Input | Level | Absent → |
|---|---|---|
| `CoverageOnPolicyIndicator` | coverage | `0` → `Premium = 0.0`, no rating. **Confirmed by the golden case** |
| `Subline` | policy | ≠ `"Liquor"` → `Premium = 0.0` (CW 2023 only; the guard is gone in 2027) |
| `LiquorClassCode` | classification | empty → `ELP = 0.0` → `BaseRate = 0` → **free policy** |
| `LiquorClassDescription` | classification | empty → `ELP = 0.0`, `ILF = 0.0`, `DeductibleFactor = 0.0`. **Three separate steps gate on a description string.** Dropped from `SetELP` in 2027 |
| `LiquorPremiumBasis` | classification | empty → `Premium = 0.0`. `"Refer To Co."` / `"Refer to Company"` → `Premium = 0.0` **and this is a referral, not a price** |
| `LiquorExposure` | classification | absent → `0` via `FirstValue` → `Premium = 0` |
| `LiquorCoverageForm` | policy | absent → `BaseRate = 0.0`. Must be `Occurrence` or `Claims Made` |
| `EachCommonCauseLimit`, `AggregateLimit` | policy | either empty → `ILF = 0.0` → `FinalRate = 0` |
| `LiquorDeductible` | classification | empty → `DeductibleFactor = 0.0` (correct: no deductible, no credit) |
| `YearInClaimsMade` | policy | absent on a claims-made form → `0` → multiplier `1.0`, i.e. **first-year pricing is silently applied** |
| `LiquorELPOverride`, `LiquorDedFactorOverride` | classification | `0.0` → use the table. **Both are the company's hook**, per Rule 45.E and 45.J.3 |
| `MiscIfAnyBasis` | classification | ≠ `"No"` → `MinPremium = 0.0` |
| `PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse` | policy | absent → `0.0` via `FirstValue` → **`FinalRate = 0`.** A missing policy modifier zeroes the premium |

**Eight distinct absent-input paths reach `Premium = 0` with no message.** That is the largest
silent-zero surface of any subline gated so far, and it is the direct consequence of liquor having
no loss-cost path: there is no second route to a premium when the first yields nothing.

---

## 6. Lookups and their layer — the layer pattern is inverted

**This is the first subline whose rating operands live countrywide.** In 334, 336 and 335 the
countrywide rate tables are header-only and the states carry every number (N7, gates 334 §5, 336 §5,
335 §5). Liquor splits:

| Table | Countrywide | State (as of 2026-08-11) |
|---|---|---|
| `LiquorELP` | **0 rows** | 51/51 · 362 rows |
| `LiquorELPText` | **0 rows** | 51/51 · 362 rows |
| `ILFLiquor` | **0 rows** | 50/51 · 3,531 rows (**IL** — see below) |
| `LiquorHomogeneityIndex` | **0 rows** | 51/51 · 362 rows |
| `DedFactorLiquor` | **21 rows** | **0/51** |
| `LiquorLCM` | **1 row** | **0/51** |
| `ProdsCompldOpsMinPremium` | **3 rows** | **0/51** |
| `ProdsCompldOpsClaimsMadeMultiplier` | **5 rows** | **0/51** |
| `LiquorLiabGrade` | **7 rows** (16 in 2027) | 41/51 · 292 rows |

**The class-specific numbers are state-supplied; the structural factors are countrywide.** That is
consistent with N8 rather than a violation of it — the countrywide operands are the *deductible*,
*claims-made*, *minimum-premium* and *LCM* factors, none of which is a loss cost. But it does
qualify README finding #1: the countrywide layer holds *almost* none of the numbers, and liquor is
where the exception lives.

**Every lookup is `FirstNonNull` of a state-keyed then a literal-`"CW"`-keyed call on one table** —
N16, confirmed a fourth time.

### Illinois files its ILF under a different name **and a different key**

**`ILFLiquor` is populated in 50 of 51 jurisdictions. Illinois ships no such table.** It overrides
`LookupILFLiquor` to read **`ILFLiquorStException`** (5 rows) instead — and that table is keyed on
**`AggregateLimit` alone**, where the countrywide lookup keys on
`(State, EachCommonCauseLimit, AggregateLimit)`.

This is **OI-20's pattern outside loss costs**: the data exists under a different table name, the
expected name is absent, and an engine keyed to the name sees nothing. Illinois adds a second twist
— **the key arity differs**, so even name-resolution is not enough; the override supplies the keys
as well as the table. Resolve the lookup **rule**, never the table name.

---

## 7. State deviations — small, and one of them is a coverage withdrawal

**Only 8 of 51 jurisdictions file any `GeneralLiabilityClassificationLiquorCoverage` rule:**
**CT, IA, IL, MA, MI, MN, NC, NY** — 31 rules in total. The deviation surface is the second-smallest
of the four sublines gated so far (OCP has 4 rules in 2 states).

| Rule overridden | States |
|---|---|
| `InitializeRuleSet`, `ErcProcess` | all 8 |
| `SetCoverageStatCode` | 6 |
| `SetILF` | 2 |
| `LookupILFLiquor`, `LookupILFLiquorWithSubLimit`, `LookupPolicyLimitsLiquorStatCode`, `SetLimitStatCode` | IL |
| `SetYearInClaimsMade`, `SetClaimsMadeMultiplier`, `SetBaseRate` | NY |

**New York does not write claims-made liquor, and says so in three rules at once.** Its `SetBaseRate`
requires `LiquorCoverageForm == "Occurrence"` and returns `0.0` for anything else; its
`SetYearInClaimsMade` and `SetClaimsMadeMultiplier` are replaced by **constant stubs** (`0` and
`1.0`) that neutralise the claims-made path.

This is **N3 with a different mechanism than 336 found.** Gate 336's thirteen jurisdictions disable
Defense-Within-Limits with a *literal empty* `<rul:Sequence />`; New York disables claims-made
liquor with a *constant*. Both are wholesale replacements; only the second is visible to a check
that looks for empty bodies. **An override is neutralising if its body is empty *or* if it writes a
constant that cannot vary** — and the second form is the one a naive "is this rule empty?" scan
misses. My own first pass at this gate flagged NY by body length and would have reported it as an
empty override; reading the body corrected it.

**And it is silent.** A claims-made liquor submission in New York produces `BaseRate = 0` →
`Premium = 0`, with no message and no referral. **A coverage form the state does not offer prices at
zero rather than declining** — N1's territory, and the seventh distinct meaning of a zero in this
corpus.

---

## 8. Refer-to-company triggers

| # | Trigger | Mechanism | Guarded? |
|---|---|---|---|
| 1 | `LiquorELPText == "Company"` → published ELP of `0` | The N17 selector, 111 rows | ✅ In-corpus discriminator |
| 2 | `PremiumBasis == "Refer To Co."` / `"Refer to Company"` | Explicit test in `SetPremium` | ✅ Explicit, but **edition-scoped** (E17) |
| 3 | **Any liquor deductible** — all 21 factors are `0`, and Rule 45.J.3 requires a company referral | `LookupDedFactorLiquor` | ⚠️ **Partially.** See below |
| 4 | `LCM == 1` — the unsupplied company multiplier | none | ❌ **No discriminator** (E15) |
| 5 | Rule 45.E — all liquor rates | none in ERC | ❌ Manual-only |

### The guard is narrower than the defect it guards

`DoMessageMustEnterLiquorDeductibleFactorOverride` (N15 — a validation rule carrying part of the
algorithm) fires when the deductible factor override is absent. Measured against the table:

| | Count |
|---|---|
| Deductible options published countrywide | **21** |
| …with factor `0` | **21** |
| …covered by the `DoMessage` guard | **10** — every *"Per Claim"* option |
| **Zero and unguarded** | **11** — all ten *"Per Common Cause"* options, plus `No Deductible` |

`No Deductible` is legitimately `0`. **The other ten are not.** A liquor risk written with, say,
*"5,000 Per Common Cause"* receives a deductible factor of `0`, no error message, and is **charged
as though it had no deductible** — the insured pays full price for coverage they have agreed to
share. Identical in every one of the three countrywide parents in force, and **no state overrides
either the table or the guard.**

**334 found this pattern and the guard matched the defect exactly** — all 15 *"Per Claim"* factors
zero, all guarded. **Here the guard covers less than half of it**, and the manual (45.J.3) says
*all* liquor deductible factors must be referred, not just the per-claim ones. So the engine should
refer on all 21, which is ERC's data (`0`) plus the manual's confirmation of what that `0` means —
tier-2 confirming, not sourcing. **Recorded as OI-44.**

---

## 9. Test result

**No oracle exists.** The OK golden case carries liquor with `CoverageOnPolicyIndicator = 0` and
`Premium = 0.0`, which exercises exactly one branch — the entry guard in `ErcProcess` — and
**confirms it**. No rated liquor output exists in the corpus. Second subline gated without an
oracle, after OCP.

| Check | Result |
|---|---|
| `tests/verify_golden.py` | **80/80** (unchanged — no liquor assertions added; there is nothing to assert against) |
| N17 on liquor, corpus-wide as-of | **362 / 362**, 0 disagreements |
| ERC 2027 class set vs manual Rule 45.G | **16 / 16 set-exact** |
| Deductible zero/guard gap | **11 unguarded**, identical in all 3 parents in force |
| Uncalled lookups | 2 (`LookupNoDedStatCode`, `LookupPremOpsLCM`) |

---

## 10. The class cliff, measured as-of

| As of | Liquor classes in force | Detail |
|---|---|---|
| **2026-08-11** | **17** | `50881 50882 50911 58151 58161 58165 58166 58168 58191 58198 59211 59212 70113 70114 70411 70412 70413` |
| **2027-04-01** | **23** | 16 new (`50941`–`50957`) + **7 legacy survivors** |
| Retired at the cliff | **10** | |
| Introduced | **16** | Exactly the manual's Rule 45.G list |
| Carried over | **7** | `50911 58161 58165 58166 58168 59211 70412` |

The 23 is not a contradiction of the manual's 16. **The seven extras are exactly the seven rows of
the CW 2026 `LiquorLiabGrade` table** — the legacy classes still in force in the 8 jurisdictions
that have not migrated on 2027-04-01. The corpus holds both class bases at once on that date,
precisely as the class-basis cliff predicts
([`RECONCILIATION.md`](RECONCILIATION.md) §1). **A liquor class list is only meaningful with a date
and a jurisdiction attached.**

**Liquor's cliff is more total than Prem/Ops'.** Prem/Ops keeps 959 of 1,401 codes across the
boundary; liquor keeps **7 of 23**, and only because some states have not moved yet. For the 43
migrated jurisdictions the liquor class list is **replaced outright**.

---

## 11. What this gate changes

| Claim on record | Status |
|---|---|
| Build order item 4: *"No published base rate anywhere; ELP-driven or refer"* | ✅ **Confirmed**, and strengthened — the manual says *"For rates, refer to company"* and there is no loss-cost branch to take |
| Step 31's prediction (N17) | ✅ **Confirmed on the vocabulary, the inventory and the rule.** First gate to test a stated prediction |
| N17 | **Corroborated a fourth time**, and on the case with no loss-cost path — which pins `Company` = *refer to company* |
| N16 | **Confirmed a fourth time**; every liquor lookup is state-row-then-`"CW"`-row |
| N7 / OI-20 | **Generalised**: Illinois files its ILF under `ILFLiquorStException` **with a different key arity** |
| N13's zero taxonomy | **Two more meanings**: a manual-confirmed *genuine* zero (hazard grade 0), and a *coverage-not-offered* zero (NY claims-made) |
| N3 | **Extended**: a wholesale override may neutralise with a **constant**, not only with an empty body |
| README #1 — *"the countrywide layer holds almost none of the numbers"* | ⚠️ **Qualified.** For liquor the countrywide layer holds the deductible, LCM, minimum-premium and claims-made factors |
| E14 / OI-38 — *"a lookup with no caller"* | **Third and fourth instances.** Reframe as a corpus habit, not a defect |

**New:** **E15** (LCM placeholder) · **E16** (structural zero minimum premium) · **E17**
(edition-scoped sentinel spelling) · **OI-43** (the CW 2027 stat-code rename defect) · **OI-44**
(the deductible guard gap).

---

## 12. Findings

- **The prediction held, and testing it was still worth the gate.** The prediction was about a
  vocabulary; the gate found that the *branch* is absent, that the *manual says so in one sentence*,
  and five things nobody predicted. **A confirmed prediction is a floor on what a gate returns, not
  a ceiling** — the argument for continuing to gate rather than assuming.
- **Liquor is the first subline where the countrywide layer carries rating operands**, and three of
  the four it carries are `0` or `1` placeholders standing in for a company input. **A subline can
  be fully specified and still not be rateable from the corpus alone.**
- **The `0` taxonomy is now seven meanings and its usefulness is falling.** Enumerating meanings has
  stopped paying; what pays is the discriminator. Four of seven now have one in-corpus, and the
  liquor deductible case shows a discriminator can exist and still **under-cover the defect by half**.
  The next zero found should be recorded by *its discriminator's coverage*, not by adding an eighth
  meaning.
- **A sentinel is not a constant.** `"Refer To Co."` became `"Refer to Company"`, both are live in
  the corpus on 2027-04-01, and ISO's own 2027 edition renamed it in one rule and not in another.
  Every string an engine compares against is edition-scoped data.
- **ERC's 2027 liquor statistical coding is wrong by a factor of 1,000**, from an incomplete rename
  inside a single file. Found by reading a rule that had nothing to do with premium, in a gate whose
  headline conclusion was already settled. **§9 asks for statistical codes; this is the first time
  that section earned its place.**
