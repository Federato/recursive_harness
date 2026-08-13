# Gate — Railroad Protective Liability (subline 335, Rule 49)

**Filed 2026-08-11. Build-order item 5. Fifth subline gate**, differential against
[334](GATE-334-PREMISES-OPERATIONS.md), [336](GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md),
[335 OCP](GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md) and [332](GATE-332-LIQUOR-LIABILITY.md).

**As-of date: 2026-08-11.** Required, not assumed (N4). Derived against **`GL_CW_20231201_V03`**, the
parent the OK golden case declares (habit 1).

> **Naming, before anything else.** This coverage is **subline code 335 — the same code as
> Owners/Contractors Protective**, which build-order item 3 already gated. `GL-MU-2027-RU-001-C`
> p.103 Rule 46 is *Owners And Contractors Protective … (Subline Code 335)*; p.124 Rule 49 is
> *Railroad Protective Liability (Subline Code 335)*. **Two coverages, two rules, one statistical
> subline** — and that is why railroad reads OCP's rate tables (§3). This gate file is named
> `GATE-335-RAILROAD-PROTECTIVE.md` and the OCP one `GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`;
> neither owns the number. **Direct support for OI-21** — ERC's `Subline` is not the ISO statistical
> subline, and the manual shares codes across rules in at least three places: **325** (Rules 42, 43),
> **335** (Rules 46, 49) and **350** (Rules 47, 53).

---

## 0. Headline

**The strongest cross-source agreement in the project so far: 18 rate cells matching to the cent**
between the ERC packages and the filed ELP Supplement, derived independently and six years apart.
And the largest edition change of any subline: **CW 2027 deletes 22 of 65 rules.**

| | |
|---|---|
| Countrywide rules | **65** (CW 2023/2026) → **46** (CW 2027) |
| State deviations | **2 jurisdictions** (AK, NY), 3 rules each — **the smallest surface of any subline gated** |
| `BaseELPRR` | **18 rows in every one of the 51 jurisdictions.** Perfectly uniform |
| Rating basis | **ELP only** — the selector is `Industry` in all 204 rows, all 51 jurisdictions, every date (§1) |
| Oracle | **None.** The golden case carries railroad with `CoverageOnPolicyIndicator = 0` |

---

## 1. Railroad's rating-basis selector — and a correction to this section

> **Corrected 2026-08-11, hours after this gate was first filed.** This section originally read
> *"N17 has a counterexample and it needs narrowing"*, on the finding that **no `RailroadELPText`
> table exists anywhere in the corpus**. That is true, and the conclusion drawn from it was wrong.
> **Railroad has a selector; it is not named `*ELPText`.** I searched for the selector *by name*,
> found nothing, and reported absence — in the same gate that criticises exactly that reasoning
> twice (§3, §5). The corrected finding below is stronger than the one it replaces, and N17 is
> **restored and widened rather than narrowed.**

**The selector is the `RailroadELP` table itself.** Its value column is named `RailroadELP`, not
`ELPText`, and `LookupRailroadELP` reads it as a **string** into a string DataDef at classification
level — the same shape as `SetLiquorELP` and `SetPremOpsELP`:

```
RailroadELP.RateTable.csv:  "StateCode","ClassCodeRailroad","RailroadELP"
                            "AK","40011","Industry"
```

**Corpus-wide it is `Industry` in all 204 rows, in all 51 jurisdictions, at every as-of date** —
today, the cliff and the end state. **A single-valued selector is the cleanest possible statement
that a subline has exactly one rating path**, and it is better evidence for *railroad is ELP-only*
than the absence of a table ever was. The manual agrees: Rule 49.E.1, p.126, **"Refer to company."**

### Enumerated by content, there are seven selectors, not four

N17 lists four. Sweeping every rate-table column for the closed vocabulary
(`Rate/Loss Cost Applies` · `Industry` · `Company` · `Not Applicable`) instead of matching table
names finds **seven**, as of 2026-08-11:

| Table | Value column | Juris | Rows | Vocabulary in use |
|---|---|---|---|---|
| `PremOpsELPText` | `PremOpsELP` | 51 | 60,593 | all four |
| `ProdsCompldOpsELPText` | `ProdsCompldOpsELP` | 51 | 60,593 | all four |
| `OwnersContractorsELPText` | `OwnersContractorsELP` | 51 | 563 | three |
| `LiquorELPText` | `LiquorELP` | 51 | 362 | `Industry`, `Company` |
| **`RailroadELP`** | **`RailroadELP`** | **51** | **204** | **`Industry` only** |
| **`SpecialProtectiveHighwayELPText`** | **`ELP`** | **1 — NY** | **3** | **`Company` only** |
| **`PremOpsELPTextTerr001`** | `PremOpsELP` | **1 — NY** | 1,191 | all four |

Three were missed by the naming convention: railroad's is named after its table, New York's Special
Protective & Highway one exists in a single jurisdiction, and New York **shards its Prem/Ops
selector by territory** — OI-20's pattern, applied to a selector rather than a loss cost.

**So N17 is not falsified. It is understated, and the enumeration method was the defect.** Proposed
amendment: *every rate-driven coverage carries a selector; enumerate them by the closed vocabulary,
never by table name; a single-valued selector means the coverage has one rating path.*

**And it delivers an item-11 finding early:** `SpecialProtectiveHighwayELPText` is **`Company` in all
three of its rows**, so New York's Special Protective and Highway coverage — added to build-order
item 11 during phase sizing — is **entirely refer-to-company**.

Product Withdrawal shows the last variation: it has **no selector of its own and borrows its
host's**. `SetProductWithdrawalELP` calls `LookupProdsCompldOpsELPText`, so the Prod/CompOps rating
basis decides the dependent coverage's basis — which is what *factor-on-host* means in data.

---

## 2. The algorithm — CW 2023 V03 / 20260101

`ErcProcess`: `CoverageOnPolicyIndicator == 0` → `Premium = 0.0`, stop. Else `ErcSetRatesAndFactors`
→ `ErcRate` → `ErcSetStatisticalCodes`.

Railroad rates **four classes**, and the chain forks by class more heavily than any subline so far.

| # | Rule | What it does |
|---|---|---|
| 1 | `SetConstructionOpsOwnerFactor` | **`LookupOwnersContractorsLossCost(classCode = "16292")`** — hardcoded. Reads **OCP's** loss-cost table (§3) |
| 2 | `SetLCM` | `LookupRailroadLCM` — **countrywide, one row, value `1`** (E15) |
| 3 | `SetConstructionOpsOwnerAdjmtFactor` | Countrywide, one row, **`1.5`** |
| 4 | `SetEstimatedContractCostRatio` | Class `40013`: the ratio of at-hazard contract cost to total contract cost |
| 5 | `SetILF` / `SetILF40014` | `LookupILFRailroad`; class `40014` gets its own ILF |
| 6 | `SetCovForInjuriesToSuprvsrFactor` | Countrywide, one row, **`0.1`** |
| 7–10 | `SetTotalCostWorkTrainsOrOtherRREquipmtAssigned` → `…BaseRate` → `…Rate` → `…FinalRate` | Work-trains charge. Countrywide rate **`56.8`** per $1,000 |
| 11 | `SetInjurySuprvsrInspOthrEmpCovConstrOpsRROps` | Supervisors/inspectors extension, classes `40011`, `40012`, `40014` |
| 12 | `SetBaseELPRR` | `LookupBaseELPRR(class)` keyed on **(State, ClassCode, `NumPassgrFreightTrains`)** — banded by trains per day. Excludes `40014` |
| 13 | `SetBaseELPRR400145orLess` | The **mixed-hazard** path — see below |
| 14 | `SetBaseELPRR40011` | Classes `40011`/`40012` |
| 15–16 | `SetContractCostFactorWOHzd` / `…WithHzd` | The two halves of a mixed-hazard project |
| 17 | `SetAdjustedBaseELPRR` | All four classes |
| 18 | `SetBaseELPRR40014` | Mixed-hazard continuation |
| 19–20 | `SetPriorToFinalRateMixedHazard` / `SetPriorToFinalRate40014` | The weighted average |
| 21–22 | `SetFinalRate` / `SetFinalRate40011` | |
| 23–26 | `SetTotPremiumPriorToInjuryToSuprvsrCovPremium`(`40011`) → `SetCovForInjuriesToSuprvsrInspOtherEmpOfTheInsdPremium` → `SetWorkTrainsOrOtherRREquipmtPremium` → `SetMinimumPremium` → `SetMinPremium` → `SetPremium` | |

### The mixed-hazard path, and a naming trap

For a **`40011`** risk with `EstdContractCostWORRHzd > 0` — a project partly clear of the tracks —
the no-hazard portion is rated on the **`40014`** basis:

```
BaseELPRR400065orLess = round(ConstructionOpsOwnerFactor × ConstructionOpsOwnerAdjmtFactor, 3)
                      = round(OCP loss cost for class 16292 × 1.5, 3)
```

**Read the rule names carefully, because they do not mean what they appear to:**

| Rule | Tests class | Writes DataDef |
|---|---|---|
| `SetBaseELPRR400145orLess` | **`40011`** | `BaseELPRR400065orLess` |
| `SetBaseELPRR40014` | **`40011`** | `BaseELPRR40006` |
| `SetPriorToFinalRate40014` | **`40011`** | `PriorToFinalRate40006` |
| `SetFinalRate40011` | **`40012`** | `FinalRate40011` |
| `SetILF40014` | `40014` ✓ | `ILF40014` ✓ |

The **rule** names refer to the *rate basis being applied*, not the risk's class — coherent once
understood. The **DataDef** names are not: they carry **`40006`**, which in
`ClassificationType.RateTable.csv` is *"Miscellaneous"*, an unrelated classification. Only
`SetILF40014` is consistent end to end.

**This is N11 at its purest** — *rules are keyed semantically, never by printed number* — and here
the printed number is wrong in the *data-definition* names too, not just the rule names. An engine
that maps `BaseELPRR40006` to a class code produces nonsense. Nothing is broken in ERC; the labels
are simply not identities.

### What changes at 2027-04-01 — the largest edition change of any subline

**65 rules → 46. Twenty-two deleted, three added, seven changed.**

| Deleted (22) | Effect |
|---|---|
| `LookupOwnersContractorsLossCost` | **The loss-cost path is gone** |
| All 6 `…WorkTrains…` rules + `LookupWorkTrainsOrOtherRREquipmtRate` | **Work-trains charge withdrawn**; the CW table goes to 0 rows |
| All 4 supervisors rules + `LookupCovForInjuriesToSuprvsr…` | **Supervisors/inspectors extension withdrawn**; CW table to 0 rows |
| `SetMinPremium`, `SetMinimumPremium`, `LookupMinPremiumRR` | **Minimum premium withdrawn**; CW table to 0 rows |
| `SetPriorToFinalRateMixedHazard`, `SetPriorToFinalRate40014`, `SetAdjustedBaseELPRR`, `SetBaseELPRR40011`, `SetBaseELPRR400145orLess`, `SetFinalRate40011` | **The mixed-hazard machinery is gone** |

| Added (3) | Effect |
|---|---|
| **`LookupOwnersContractorsELP`** | Replaces the OCP **loss cost** with the OCP **ELP** |
| `SetBaseRate`, `SetBaseRate40014` | `BaseRate = round(BaseELPRR × LCM, 3)` — **the same shape as liquor** |

`SetFinalRate` absorbs the deleted logic, growing 2,303 → **10,942** characters and branching on all
four class codes as string literals.

**Railroad's 2027 change is a direct consequence of OCP's.** Gate 335 (OCP) established that the
`OwnersContractorsLossCost` table is withdrawn in 43 jurisdictions on 2027-04-01. Railroad reads that
table, so it had to move — and it moved to the ELP. **A subline gate found the cause; this gate
found the second victim.** Neither is visible from inside the other, which is the case for
differential gating.

---

## 3. Railroad reads OCP's tables, and has an orphan of its own

**`RailroadLossCost.RateTable.csv` exists in all ten countrywide editions, has 0 rows in every one,
has 0 rows in all 51 jurisdictions, and is referenced by no rule anywhere in the corpus.**

Checked by scanning every rule file in every countrywide package for the string `RailroadLossCost`:
**zero hits.** A table that exists, is empty, and has no reader.

This is **N7 taken one step further than it currently goes**. N7 says *presence ≠ population*, and
OI-20 added *empty ≠ absent data*. Railroad adds a third: **a populated-looking name may have no
purpose at all.** An engine that inferred "railroad has a loss-cost table, therefore a loss-cost
path" would build a branch ERC does not have — the loss cost railroad actually reads is **OCP's**:

```
ConstructionOpsOwnerFactor = LookupOwnersContractorsLossCost(classCodeOwnersContrctrs = "16292")
```

`16292` is hardcoded in the rule. §4 confirms the manual specifies exactly that class.

---

## 4. Manual confirmations — including 18 exact rate cells

**Rule 49 spans pp. 124–127 and is nearly silent on rating.** `E.1 Basic Limits: "Refer to company."`
`E.2 Increased Limits: "Refer to Rule 56."` `F. Basis Of Premium: Total Cost.` `G.` lists four
classes. `H.` gives eight generic steps.

**The rating procedure is in the ELP Supplement, not the rules manual** — Procedure 5.E of the
loss-cost notices (`GL-AK-2020-LC-001-C` pp.10–11). Every countrywide operand ERC carries is there:

| ERC | Manual (Procedure 5.E) | Verdict |
|---|---|---|
| `ConstructionOpsOwnerAdjmtFactor = 1.5`, applied to `LookupOwnersContractorsLossCost("16292")` | **5.E.1.a**: *"the $100,000/300,000 Basic Limit ELP per $1,000 of Total Cost is **150%** of the loss cost for **Class Code 16292** Construction Operations – Owner"* | ✅ **Exact, including the class code** |
| `CovForInjuriesToSuprvsrInspctrsOtherEmpsOfTheInsd = 0.1` | **5.E.1.a / 5.E.3.c**: *"charge an additional premium of **10%**"* for supervisors, inspectors and other employees at the job site | ✅ **Exact** |
| `WorkTrainsOrOtherRREquipmtRate = 56.8` | **5.E.2.c**: *"The $100,000/300,000 Basic Limit ELP per $1,000 of Total Cost is **$56.80**"* | ✅ **Exact** |
| `BaseELPRR` keyed on `NumPassgrFreightTrains` | **Tables 5.E.2.a, 5.E.3.a, 5.E.3.b**: *"Number Of Passenger And Freight Trains Per Day"*, six bands | ✅ **Exact, including the banding** |
| `SetEstimatedContractCostRatio` (class `40013`) | **5.E.2.b**: *"applying to the ELP the ratio of the estimated contract cost of the operations performed on, over or under the insured railroad's property or within 50 feet … to the total contract cost"* | ✅ **Exact** |
| `SetPriorToFinalRateMixedHazard`, `ContractCostFactorWOHzd` / `WithHzd` | **5.E.4** *Special Rating Procedure*: projects *"part of which are subject to an actual railroad train hazard and part of which are not"* → *"weighted average"* | ✅ **Exact** |
| `Premium = FinalRate × TotalCost ÷ 1000` | **Rule 49.G**: *"Total Cost — **per $1,000 of total cost**"*, all four classes | ✅ Confirms the ÷1000 |
| Class codes `40011`–`40014` | **Rule 49.G**, p.126 | ✅ **Set-exact** against ERC's four hardcoded branches |
| *"For operations other than construction, refer to company"* | **5.E.1.b, 5.E.3.d** | ✅ A refer trigger the rules manual does not mention |

### The 18-cell test

Alaska's ERC `BaseELPRR` table, from `GL_AK_20260801_V02`, against Procedure 5.E of
`GL-AK-2020-LC-001-C` — **a 2026 machine-readable package versus a 2020 filed PDF**:

| Class | 5 or less | 6–20 | 21–40 | 41–60 | 61–100 | Over 100 |
|---|---|---|---|---|---|---|
| **40011** | 2.88 | 4.80 | 6.40 | 8.32 | 11.20 | 13.92 |
| **40012** | 2.40 | 4.00 | 5.60 | 7.20 | 9.60 | 12.00 |
| **40013** | 4.80 | 7.68 | 10.40 | 13.60 | 18.40 | 23.20 |

**All 18 cells identical**, and `40014` is correctly **absent** from the table in both — the manual
derives it (150% × OCP 16292) rather than tabulating it, and ERC's `SetBaseELPRR` excludes `40014`
for exactly that reason.

**This is the first time a rate *value* has been confirmed cell-by-cell across the two corpora.**
Every prior confirmation was structural — a formula shape, a vocabulary, a class list. Eighteen
matching numbers from two independently-captured sources six years apart is the strongest evidence
this project has produced that the ERC extraction is faithful.

### Habit 6 caught a wrong finding before it was written

I first searched the **multistate rules manual** for the work-trains rate and the supervisors
extension, found nothing across all four editions, and was about to record: *"ERC implements rating
machinery the filed manual does not describe"* — the inverse of every prior disagreement, and a
striking claim.

**It was wrong.** The machinery is fully specified, to the cent, in the **ELP Supplement** — a
different document in the same corpus. Rule 49 says *"refer to company"* for basic-limits rates
precisely **because** the ELPs live in the loss-cost notices.

*"Search to locate a page; read the page to make the claim"* — and the corollary this adds:
**absence from the document you searched is not absence from the corpus.** Third time habit 6 has
changed an answer, after gate 336 §2 and the liquor page citation (which resolved to Rule 42,
eleven pages before Rule 45).

---

## 5. Layer pattern — inverted again, and this time with a published dollar rate

| Table | Countrywide | States (as of today) |
|---|---|---|
| `BaseELPRR` | **0 rows** | 51/51 · **918 rows (exactly 18 each)** |
| `RailroadELP` | 0 rows | 51/51 · 204 |
| `ILFRailroad` | 0 rows | 51/51 · 1,836 |
| `RailroadHomogeneityIndex` | 0 rows | 51/51 · 969 |
| `OwnersContractorsLossCost` | 0 rows | 51/51 · 563 → **8/51 · 88 at the cliff** |
| **`RailroadLossCost`** | **0 rows** | **0/51 — and no reader (§3)** |
| `RailroadLCM` | **1 row: `1`** | 0/51 |
| `ConstructionOpsOwnerAdjmtFactor` | **1 row: `1.5`** | 0/51 |
| `WorkTrainsOrOtherRREquipmtRate` | **1 row: `56.8`** | 0/51 |
| `CovForInjuriesToSuprvsrInspctrsOtherEmpsOfTheInsd` | **1 row: `0.1`** | 0/51 |
| `MinPremiumRR` | **1 row: `0`** | 0/51 |
| `PolicyLimitsRailroadStatCode` | 9 rows | 0/51 |

Same inversion as liquor: **class-specific numbers state-supplied, structural factors countrywide** —
so this is the pattern for ELP-rated sublines, not a liquor peculiarity.

**But `WorkTrainsOrOtherRREquipmtRate = 56.8` goes further than anything liquor had.** That is not a
factor or a placeholder. **It is a dollar rate per $1,000 of exposure, published countrywide**, and
the manual confirms it to the cent. README finding #1 — *"There is no national ILF table and no
national loss cost publication at all"* — is **true of loss costs and false of this**. The engine
must be able to read a rating operand from the countrywide layer, not only an algorithm.

**E15 and E16 both generalise beyond liquor.** `RailroadLCM = 1` is the same unsupplied company
multiplier; `MinPremiumRR = 0` is the same structurally-zero minimum premium. Two sublines each,
which is enough to treat them as properties of ELP-rated coverages rather than one-offs.

**`LookupPremOpsLCM` is uncalled here too**, in all ten editions — the *same* dead lookup found in
the liquor file. It is not three independent instances of E14; it is **one dead lookup copy-pasted
across subline rule files.** That is a cheaper explanation and it strengthens the reframing: treat
uncalled lookups as inert boilerplate.

---

## 6. State deviations — the smallest surface yet

**Two jurisdictions file any `GeneralLiabilityClassificationRailroadCoverage` rule: AK and NY.** Each
overrides three, and two of those are boilerplate (`InitializeRuleSet`, `ErcProcess`). The only
substantive override in the whole country is **`SetMoldStatCode`**, a statistical-coding rule — it
changes no premium.

**`BaseELPRR` has exactly 18 rows in all 51 jurisdictions.** Three classes × six train bands, with no
state adding or dropping a row. After 334's 71 state rules across 19 jurisdictions and item 6's
178 across 42, railroad is **a countrywide algorithm with countrywide structure and state-supplied
rate values, and nothing else.**

For phase sizing this makes railroad the cheapest remaining rating subline by a wide margin, and the
build-order note *"no base rate; banded on trains/day at 100/300 limits"* is confirmed exactly —
`$100,000/300,000 Basic Limit` is the ELP tables' stated basis in the manual.

---

## 7. Refer-to-company triggers

| # | Trigger | Mechanism | Guarded? |
|---|---|---|---|
| 1 | **All basic-limits rates** — Rule 49.E.1 | none in ERC | ❌ Manual-only, same as liquor |
| 2 | **Operations other than construction** (5.E.1.b, 5.E.3.d) | none found in ERC | ❌ **No in-corpus discriminator.** ERC rates whatever class code is submitted |
| 3 | `LCM == 1` — the unsupplied company multiplier | none | ❌ E15 |
| 4 | Class code outside `40011`–`40014` | falls through every branch → `FinalRate = 0` | ⚠️ Silent zero |
| 5 | `RailroadClassCode` or `RailroadClassDescription` empty | → `BaseELPRR = 0` | ⚠️ Silent zero |

**Trigger 2 is the notable one.** The manual refers non-construction railroad operations to the
company; ERC carries no test for it and will happily rate them from the class table. Recorded as
**OI-45** — the engine cannot detect it from ERC alone, and the doctrine forbids sourcing the rule
from the manual, so the honest position is that this is a **known unguarded referral**.

---

## 8. Test result

**No oracle.** The golden case carries railroad with `CoverageOnPolicyIndicator = 0` and
`Premium = 0.0`, confirming the entry guard and nothing else. **Third subline gated without one**,
after OCP and liquor.

| Check | Result |
|---|---|
| `tests/verify_golden.py` | **80/80** (unchanged) |
| AK `BaseELPRR` vs ELP Supplement Procedure 5.E | **18 / 18 cells exact** |
| ERC class branches vs Rule 49.G | **4 / 4 set-exact** |
| `RailroadLossCost` readers, corpus-wide | **0** |
| `BaseELPRR` row count uniformity | **18 in all 51** |
| Uncalled lookups | 1 (`LookupPremOpsLCM`, all 10 editions) |

---

## 9. What this gate changes

| Claim on record | Status |
|---|---|
| **N17** — *"Every subline carries a sibling selector"* | ✅ **Upheld and widened.** Enumerated by *content* rather than table name there are **seven**, not four — railroad's is the `RailroadELP` table itself, `Industry` in all 204 rows. **A single-valued selector is the cleanest statement that a coverage has one rating path.** Product Withdrawal has none of its own and borrows Prod/CompOps's |
| **N7 / OI-20** | **Extended a third time**: `RailroadLossCost` exists, is empty everywhere, and **no rule reads it** |
| **N11** | **Sharpened**: the printed number is unreliable in **DataDef** names too — `BaseELPRR40006` serves class `40011`, and `40006` is *"Miscellaneous"* |
| **E15** (`LCM = 1`) and **E16** (zero minimum premium) | **Generalised** — both appear in liquor and railroad. Properties of ELP-rated sublines |
| **E14** (uncalled lookups) | **Cheaper explanation**: `LookupPremOpsLCM` is the *same* dead lookup in both files, copy-pasted |
| **README #1** — *"no national loss cost publication at all"* | ⚠️ **Qualified.** `WorkTrainsOrOtherRREquipmtRate = $56.80` is a countrywide dollar rate, manual-confirmed |
| Build order item 5 — *"No base rate; banded on trains/day at 100/300 limits"* | ✅ **Confirmed exactly** |
| Gate 335 (OCP) — *"both paths needed by effective date"* | **Extended to a second coverage.** Railroad reads OCP's loss cost and had to switch to OCP's ELP in 2027 |
| **OI-21** — *"ERC `Subline` ≠ ISO statistical subline"* | ✅ **Confirmed from the manual**: codes 325, 335 and 350 each cover two rules |

**New:** **OI-45** (non-construction railroad operations are a manual-only referral with no ERC
discriminator).

---

## 10. Findings

- **The strongest evidence in the project is 18 numbers.** Every previous cross-source confirmation
  was structural. Eighteen rate cells matching to the cent, between a 2020 PDF and a 2026 package,
  is a different kind of evidence — it tests the *extraction*, not the *reading*.
- **A gate's conclusions can be caused by another gate's subject.** Railroad's entire 2027 rewrite
  exists because OCP's loss-cost table was withdrawn. Gate 335 found the withdrawal and could not
  have found this consequence; this gate found the consequence and could not have explained it
  without 335. **That is the argument for gating in a fixed order rather than in parallel.**
- **I made the exact error this gate documents, in this gate.** §3 and §5 both criticise inferring a
  fact from a table's name; §1 originally did it — searched for `RailroadELPText`, found nothing,
  and reported that N17 had a counterexample. The selector was there under a different name. **The
  fix was to enumerate by content, which then found three selectors nobody had counted** and turned
  a narrowing of N17 into a widening. *A finding of absence is only as good as the method that
  looked.*
- **Absence from the document you searched is not absence from the corpus.** The work-trains rate is
  missing from all four editions of the rules manual and present, to the cent, in the ELP
  Supplement. Had I stopped at the first search I would have filed a confident, wrong disagreement
  claiming ERC invents rating machinery.
- **Railroad is the cheapest rating subline remaining** — 2 deviating jurisdictions, 3 overridden
  rules, one uniform 18-row table — and the 2027 edition makes it cheaper still by deleting a third
  of it. **The 2023 and 2027 railroads are close to different coverages**, so the two-calculator
  requirement is not a convenience here; it is the whole design.
