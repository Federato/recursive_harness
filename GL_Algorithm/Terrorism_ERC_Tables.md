# Terrorism (Certified Acts / TRIA) — Required ERC Tables

**Source gate doc:** `docs/gates/GATE-TERRORISM.md`
**Line:** General Liability (GL), Rule 55 *(Terrorism Premium Determination)*
**Derived from:** `Terrorism_RatingAlgorithms.md`
**Documented:** 2026-08-20

Terrorism has no filed base rate, so this list does not follow the usual "base rate → adjustment →
premium" table shape the other GL/CF sublines use. Instead it multiplies **finished sibling
premiums** by an exposure-class factor, so the tables below are almost entirely
**premium-level/factor tables**, not rate-build-up tables. Per GATE-TERRORISM.md § 1, the
countrywide package carries **20 terrorism tables total**; only the subset traced explicitly in the
gate doc is listed by name below — the remainder is flagged rather than guessed.

---

## Rate-build-up tables (state-or-CW keyed)

**Not applicable to this coverage in the usual sense.** There is no base rate, ELP, or loss-cost
table — terrorism's only "rate-shaped" inputs are the exposure-class tables below, which resolve a
classification (Above Average / Average) rather than a dollar rate.

| Table | Used for | Keys |
|---|---|---|
| `TerrorismExposureClassesPremises` | Resolves exposure class for the Prem/Ops path | ClassCode; CW plus LA/NJ/NY overrides |
| `TerrorismExposureClassesProducts` | Resolves exposure class for the Products/Completed Ops path | ClassCode |
| `TerrorismExposureClassesOtherSublines` | Fixed exposure class for the All Other Sublines path | none — 1-row constant, always `Average Exposure Class` |

---

## Limit-of-insurance (sub-limit ILF) tables

| Table / rule | Used for | Keys |
|---|---|---|
| `SetTerrorismILF` | Computes `TerrorismILF` per PEV001 A.1.c.(1)/(2) two-case limit selection | policy per-occurrence limit, terrorism aggregate limit |

**Not resolved in source docs:** the gate doc names the computed value `TerrorismILF` and the rule
`SetTerrorismILF`, and confirms the two-case selection logic against the manual, but does not cite
the underlying rate table name or its full key list beyond the limit arguments used in the
selection.

There is no coinsurance table and no deductible table for this coverage — not applicable.

---

## Premium-level tables

| Table | Used for | Keys | CW value |
|---|---|---|---|
| `CertifiedActsOfTerrorismExposureClassFactor` (Premises variant) | Prem/Ops exposure-class multiplier | State, `PolicyEffectiveWhileTRIAInEffectIndicator`, ExposureClass [, Territory in 15 states] | Above Average `.009`, Average `.004` |
| `CertifiedActsOfTerrorismExposureClassFactor` (Products variant) | Products/Completed Ops exposure-class multiplier | same shape | not independently re-confirmed by value in the gate doc |
| `CertifiedActsOfTerrorismNuclBioChemRadioFactor` | Conditional NBCR multiplier | — | `0.58` (manual A.1.b) |
| State-suffixed exposure-class factor tables (CA, CO, CT, FL, IL, MA, MD, MI, NJ, NY, OR, PA, TX, VA, WA) | Territory-rated replacement for the CW factor pair | State, TRIA indicator, ExposureClass, **Territory** | 15 distinct values, `.004`–`.133` |
| `…FactorOtherManhattan` (NY) | Manhattan-specific exposure-class factor | 5-key, includes borough | `.038`–`.098` |
| `…FactorRemainderOfTerritory001` / `…FactorCA` (CA) | California territory split | Territory | not given |

---

## Statistical/subline tables

**Not resolved in source docs.** GATE-TERRORISM.md does not trace a statistical-code or subline
reporting table specific to terrorism; none of the 20-table population enumerated in § 1 is
identified in the gate as a stat-code table.

---

## Not ERC tables

| Field | Why it isn't a rate table |
|---|---|
| `CertifiedActsofTerrorismExposureClassFactor` (lowercase "of") | A **user-entered input DataDef**, distinct from the capitalized table-driven field of nearly the same name. 0 writers in any edition currently in force; validated only by a `DoMessage*` rule requiring `0 < factor <= 0.004` when no class on the policy is Above Average. Not a lookup table (per GATE-TERRORISM.md § 6) |
| `EndorsementPremium` | User-entered input to the endorsement-only path, not a filed rate |
| Sibling `Premium` and `FinalILF` values (Prem/Ops, Products/CompldOps, All Other Sublines, Unmanned Aircraft classification groups) | Outputs of other coverage groups' own rating chains, consumed here — not terrorism's own tables |
| `DomainYear200{3,4,5}Terrorism*Factor*` (10 tables) | Obsolete-year domain stubs, 0 rows each, deleted by the 2022 notice's own description ("obsolete years and outdated federal share percentages") — schema artifacts, not a rating path (per GATE-TERRORISM.md § 7) |

---

## Verification

Per GATE-TERRORISM.md § 3a and § 10:

| Check | Result |
|---|---|
| `scripts/erc/37_terrorism_align.py 20260812` | 5/5 (was 4/4; check 3a — the 15-state territory override — added by the correction in § 3a) |
| `Agentic/iso-circular-expert/tools/smoke_test.py` | 17/17 (15 + 2 terrorism-specific) |
| `scripts/erc/40_referral_census.py` probe 6 | found the 15-state territory override that a straight countrywide-vs-manual check missed |
| `scripts/erc/35_census_sizeofrisk.py 20260812` | 5/5 |
| `scripts/erc/34_crosscheck.py 20260812` | 4/4 |
| `tests/verify_golden.py` | 80/80 |

**Open finding carried from the rating-algorithms doc:** the countrywide table check that produced
the "confirmed against manual" result in an earlier draft of the gate covered only the countrywide
package, and 15 of 51 jurisdictions actually zero that table and redirect elsewhere (§ 3a). Any
future verification pass on these tables should check "does a state override this to zero rows and
redirect" as a standing step, not just "does the countrywide row match the manual."

---
