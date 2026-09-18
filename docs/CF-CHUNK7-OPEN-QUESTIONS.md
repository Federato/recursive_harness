# Property chunk 7, task C7-28 — the algorithms page's five open questions

2026-09-18. Script:
[`scripts/cf/57_chunk7_open_questions.py`](../scripts/cf/57_chunk7_open_questions.py).

**Four answered with evidence, one left open with a reason.** None left as it
was.

---

## Q1 · The hard-coded "Other than Apartments and Condominiums" key

> *…this permanently blocks the "Apartments and Condominiums" rows … even when a
> theft-exclusion factor lookup two steps earlier still varies by
> `ApartmentCondoIndicator`. Whether this is an intentional ISO simplification
> or an authoring inconsistency could not be resolved.*

**ANSWERED — and half the question rested on a false premise.**

Electing apartments every way available (parent class 0311, indicator `"Yes"` on
the record) leaves the base rate at **0.047** and the theft factor at **0.86**.
**The theft factor does not vary.** Both lookups are pinned.

So there is **no inconsistency to explain**: the apartment concept is switched
off in this group at *both* sites, which reads as a deliberate simplification
rather than an authoring slip. Corrected on the algorithms page in two places
(C7-19, C7-20).

---

## Q2 · The theft-factor values, never cross-checked against plain Business Income

> *…if the plain-BI and Special-Class-BI passes are reading the exact same
> physical CSV file, the values should match; this was not independently
> re-verified.*

**ANSWERED — the values were never the issue.**

| | |
|---|---|
| The table | 2 countrywide rows — `Yes` **0.96**, `No` **0.86** |
| **This group's key** | a **constant** `"No"` |
| **Plain Business Income's key** | **`../../ApartmentCondoIndicator`** — the Building's, live |

**Same physical table, same two rows, two different key strategies.** Plain
Business Income can reach both rows; this group can reach one.

The question asked whether the *values* agree. They do, trivially — it is one
file. **What it should have asked is whether both groups can reach them**, and
the answer is no.

---

## Q3 · `BasicGroupIIRate` and `LowestBasicGroupIIRate` header-only

> *…Basic Group II base rate is unresolvable at the countrywide level for this
> coverage group. Any rater built off this document needs a state-specific
> override.*

**ANSWERED and quantified** (C7-16):

| | CW rows | States filing their own |
|---|---|---|
| `BasicGroupIIRate` | **0** | 45 of 47 |
| `LowestBasicGroupIIRate` | **0** | 39 of 47 |

Confirmed, and the consequence is now measured rather than warned about: **Group
II is unresolvable at countrywide for three coverage groups** — Building, plain
Business Income and this one — and the two jurisdictions filing neither table
(FL, PR) reach a read with nothing to read (C7-17).

---

## Q4 · The two untraced endorsement files — **STILL OPEN, deliberately**

| Bytes | File |
|---|---|
| 7,523 | `…SpecialClassBusnIncomeInterruptionOfComputerOperationsCoverageRules.Rule.xml` |
| 10,002 | `…SpecialClassBusnIncomeWatercraftExclusionBuybackCoverageRules.Rule.xml` |

Both exist; neither is traced.

**Out of scope by the build order, not by oversight.** Endorsement families are
chunk 12, and tracing them here would price coverage this chunk has no golden
case for. Left open **with a reason**, which is what the gate asks for — an open
question closed by assertion is worse than one left open.

---

## Q5 · The unopened `…SpecialClassBusnIncomeCoverageRules.Rule.xml`

> *…it likely mirrors `CommercialPropertyBusinessIncomeCoverageRules`' role but
> this was not verified.*

**ANSWERED — and it does not.**

| | |
|---|---|
| Rules in the file | `InitializeRuleSet`, `CalculateTotalPremium`, `SetCoverageOnPolicyIndicator`, `ErcProcess` |
| Matrices named | **none** |
| `SetCoverageOnPolicyIndicator` | a bare `<rul:Constant>0</rul:Constant>` |
| At run time | indicator **0**, premium **0** |

It is not a dispatch or attach file. It is a **record-level coverage shell whose
own gate is hard-coded to 0**, so it never prices — and it carries a
`CalculateTotalPremium` that its own indicator switches off. The premium for this
coverage is produced entirely by the four per-form files.

**Another computed-and-never-used shape** — the fifth across chunks 6 and 7,
after `ProtectionClassFactor`, the unfilled Builders Risk table,
`BaseRateAdjustmentFactor` (filed by 46 states, read by none here) and
Earthquake's rate with nowhere to charge it.

Every one of those was found by asking *who reads this?* rather than *is this
filed?* — and none of them would have been found by rating a golden case.

---

## What the five say together

Two of the five were **not answerable as asked**: Q1 and Q2 both embedded a
premise about what varies, and in both cases the premise was wrong. The
questions were right to be asked and wrong in their framing, which is the
strongest argument for writing open questions down at all — a question carries
its assumptions into the next pass unless someone runs it.
