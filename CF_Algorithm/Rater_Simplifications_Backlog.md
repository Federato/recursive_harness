# Rater Simplifications — Backlog

Standing list of places where the Excel rater knowingly diverges from what ISO filed, because a
simpler build was chosen for now. These are **not** compliance gaps that were missed — each one was
seen, decided, and deferred. The point of this file is that they stay visible instead of becoming
invisible once the formula works.

One row per divergence. Retire a row by fixing it, not by deleting it.

---

## Feature set: separate endorsement records per datadef group

ERC files a **distinct exclusion record on each datadef group**. The rater currently reuses one
Yes/No input across groups, which means a risk cannot elect the exclusion on one coverage and not
the other. Same shape every time, so these are worth doing as one batch.

| # | Coverage | Filed records | What the rater does | What breaks |
|---|---|---|---|---|
| S-1 | Special Class Business Income — **Vandalism** | `CommercialPropertyVandalismExclusion` on the Special Class item **and** `CommercialPropertyVandalismExclusionSpclClassBusnIncome` on the Business Income group | Reuses `'Special Class Inputs'!C26` for both | A risk cannot exclude vandalism on Business Income but not on the building, or the reverse |
| S-2 | Special Class Business Income — **Windstorm/Hail** | `CommercialPropertyWindstormOrHailExclusionSpecialClass` on the item **and** `CommercialPropertyWindstormOrHailExclusionSpclClassBusnIncome` on the Business Income group | Business Income points at the Special Class building's `WindstormOrHailExclFactor` cell | Same: one record drives both. Building excluded ⇒ Business Income excluded, whether or not it was elected. Decided 2026-09-16 — point for now. |
| S-3 | Special Class Business Income — **Theft** | `CommercialPropertyTheftExclusionSpecialClass` on the item **and** `CommercialPropertyTheftExclusionSpclClassBusnIncome` on the Business Income group | Not yet built — logged before it is | Same split. Found 2026-09-16 while tracing Special; the factor tables also differ (0.88 building vs 0.86 Business Income), so this one cannot be pointed even if the gate were shared. |

**Why S-1 and S-2 are safe enough today.** In both of those the *lookup* genuinely is shared — same matrix, same
key, and Business Income reads the key (`BasicGroupIISymbol` / class code) off the building item
anyway. Only the **gate** differs. So the pointed-at value is correct whenever both records agree,
which is the common submission.

**How to fix, when it is worth doing.** Keep the shared lookup block; give each group its own Yes/No
input and wrap the shared lookup in its own `IF`. The table data does not change — only the gate
does. Cheap per coverage; the cost is input-sheet real estate, which is why it is deferred.

**Where else to check before calling this batch done.** The same two-record pattern very likely
exists for the other exclusions and the other Business Income groups (plain Business Income has its
own `...BusnIncome` records too). Sweep the `Exist AtInputDataDef=` gates in each
`*Rules.Rule.xml` rather than assuming this list is complete.

---

## Feature set: known-inaccurate data shortcuts

| # | Item | What the rater does | What breaks |
|---|---|---|---|
| D-1 | CF BGI District-split states (AK, CA, NY) | NY uses a built shortcut; AK uses a ZIP mapping | Both are known-inaccurate, not production-ready |

---

*Added 2026-09-16. Source for S-1: `Excel_Rater_SpecialClassBusinessIncome_VandalismExclFactor_Formulas.html`,
step 6. Source for S-2 and S-3: `CommercialPropertySpecialClassRules.Rule.xml` and
`CommercialPropertySpecialClassBusnIncomeRules.Rule.xml` — `SetWindstormOrHailExclFactor` and
`SetSpecialTheftExclusionIndicator` in each.*

---

## Feature set: filed rules that produce a zero instead of a neutral value

Places where a missing input drives a factor to `0.0` rather than `1.0`, so the premium collapses to
nothing rather than simply not receiving a credit. **These are ISO's filed behaviour, not our
simplifications** — they are logged here so the rater reproduces them deliberately, with a visible check
cell, instead of someone "fixing" them later and quietly changing the premium.

| # | Where | Trigger | Result |
|---|---|---|---|
| Z-1 | Legal Liability, Building and Personal Property | `AddlInsurableIntOption` left **blank**, or no Legal Liability Coverage Form record at all | `LegalLiabAddlInsurableIntFactor = 0.0`, multiplied unconditionally &rarr; **premium of zero**. **Corrected 2026-09-16:** `Option4` *is* "None" and returns 1.00, so a risk with no additional insurable interest is meant to be coded Option4 and gets a neutral factor. This is therefore a **mandatory input** once Legal Liability is selected, not an unfortunate default. Build it as a required field with all four options; keep a check cell for the blank case. |
| Z-2 | Special Class Business Income, vandalism | gate passes but ClassCode is blank | `VandalismExclFactor = 0.0` &rarr; zero rate |
| Z-3 | Business Income, educational institutions | `TypeOfRisk = "Educational Institutions"` with no Changes-Educational-Institutions endorsement or null month count | `ChangesEducationalInstitutionsExtensionOfRecoveryFactor = 0.0`, which makes `TypeOfRiskFactor` zero and drives the BGI/BGII final rate to zero |

**How to apply:** reproduce the `0.0` exactly. Add a check cell that flags a zero factor so it is visible
rather than silent. Do not substitute `1.0` without a circular check confirming ISO's intent.
