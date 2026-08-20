# Owners & Contractors Protective / Principals Protective — Required ERC Tables

**Source ERC packages:** `GL_CW_20230501_V01`, `GL_CW_20231201_V03` (pre-2027 algorithm) and
`GL_CW_20270401_V01` (2027 algorithm)
**Line:** General Liability (GL), Countrywide, Subline Code 335, Rule 46
**Derived from:** `OwnersContractorsProtective_RatingAlgorithms.md`, and originally
`docs/gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`
**Documented:** 2026-08-20

This lists every ERC table required to rate OCP / Principals Protective coverage, resolved from
the lookups and rule chain traced in `GATE-335` §§ 1, 4, 5, 6, and confirmed against the manual at
`GATE-335` § 2. Unlike the CF source material this document is ported from, `GATE-335` does not
carry file-level `.RateTable.csv` verification against the raw ERC package directory — table row
counts and jurisdiction counts below are as reported in the gate document, not independently
re-verified here. See **Verification** below.

Most tables in this subline follow the two-pass `FirstNonNull(state row, "CW" row)` lookup
pattern used elsewhere in ERC, but for OCP nearly every rate-bearing table is **state-only** — the
countrywide row is empty for all of them except `PrincipalsProtvLiabFactor` and
`PremOpsMinPremium` (`GATE-335` § 5).

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `OwnersContractorsLossCost` | Published loss cost, base tier | State, ClassCode |
| `OwnersContractorsLossCostOverOneMillion` | Published loss cost, over-$1M tier | State, ClassCode |
| `OwnersContractorsLossCostOverOneHundred` | Published loss cost, over-100-unit tier (legacy classes `27111`/`27112` only) | State, ClassCode |
| `OwnersContractorsELP` | Expected loss potential, base tier | State, ClassCode |
| `OwnersContractorsELPOverOneMillion` | Expected loss potential, over-$1M tier | State, ClassCode |
| `OwnersContractorsELPOverOneHundred` | Expected loss potential, over-100-unit tier (legacy classes only) | State, ClassCode |
| `OwnersContractorsELPText` | Refer-to-company / rate-basis selector (`"Rate/Loss Cost Applies"`, `"Industry"`, `"Company"`) | State, ClassCode |
| `ILFOwnersContractors` | Increased limits factor | State, OccurrenceLimit, AggregateLimit |
| `PrincipalsProtvLiabFactor` | Workers-Compensation-derived ELP factor for class `15191` (pre-2027 only) | `"CW","Y"` (single countrywide cell, no state override found) |

Loss-cost and ELP tables carry **zero countrywide rows** — they resolve only from a state-specific
row, or not at all. The loss-cost tables are populated in 8 jurisdictions (CA, FL, GA, MA, NJ, NV,
NY, WA) and absent in the other 43; the ELP and ILF tables are populated in all 51 (`GATE-335`
§ 0, § 5).

`WorkersCompensationRate`, which `PrincipalsProtvLiabFactor` multiplies against for class `15191`,
is **not an ERC table** — see **Not ERC tables** below.

---

## Coinsurance / LOI / deductible tables

**Not applicable to this subline.** *"B. Exceptions To Section I – General Rules … 2. Rule 15.
Deductibles does not apply."* (`GL-MU-2027-RU-001-C` p.104, cited in `GATE-335` § 2). ERC confirms
this exactly — the OCP rule set has no deductible rules or deductible tables at all, where
sublines 334 and 336 each have five (`GATE-335` § 2). There is no limit-of-insurance factor table
either — OCP uses the increased-limits factor (`ILFOwnersContractors`) in its place, and there is
no coinsurance concept in this coverage part.

---

## Premium-level tables

| Table | Used for | Layer |
|---|---|---|
| `PremOpsMinPremium` | Minimum premium (pre-2027 only) — **reused from subline 334 (Premises/Operations)**, not an OCP-specific table | countrywide, 3 rows |

There is no `PackageModFactor` table or equivalent for this subline — `GATE-335` § "1. The
algorithm" states explicitly that OCP has no `PackageModFactor`, unlike sublines 334 and 336. There
is also no cyber-exclusion or IRPM-style factor documented for OCP in the gate source.

---

## Statistical / subline tables

| Table / rule | Used for |
|---|---|
| `SetMoldStatCode` | Statistical mold coding, no premium effect. Overridden by AK and NY; all other jurisdictions run the countrywide rule (`GATE-335` § 6) |

> Not resolved in source docs — `GATE-335` § 6 names the rule `SetMoldStatCode` but does not give
> the underlying table name it reads from (if any). No other statistical/subline table is named
> for this subline in the source docs.

---

## Not ERC tables

`WorkersCompensationRate` is a **declared submission input field** (`MasterGLCW.DataDef.xsd`, type
`xs:decimal`, 4 fraction digits) — supplied per risk by the submission, not looked up from an ERC
rate table. It feeds `SetELP`'s class-`15191` branch (`ELP = PrincipalsProtvLiabFactor x
WorkersCompensationRate`), pre-2027 only. Per `GATE-335` § 1: *"the Workers Compensation 'external
dependency' is neither missing nor external ... a submission requirement, not a corpus gap."*

---

## Verification

`GATE-335` § 5 reports the layer (countrywide / state-only) and row-presence for each table above,
resolved by tracing the rule chain (`SetLossCost`, `SetELP`, `SetILF`, etc.) down to each lookup's
target matrix — the same method the CF source documents use, but `GATE-335` does not additionally
cross-check each table's `.RateTable.csv` file existence and row count against the raw
`CFCW.../Rate Tables`-style directory the way the CF Basic Group I ERC Tables document does. This
document inherits that same level of verification (rule-trace only) and does not add a fresh
file-system check.

Three corpus-wide consistency tests are reported in `GATE-335` § 7, run across the latest edition
of all 51 jurisdictions (433 (state, class) rows in `OwnersContractorsELPText`):

| Test | Result |
|---|---|
| selector `"Rate/Loss Cost Applies"` agrees with a non-zero published loss cost | 433 / 433 agree, 0 disagree |
| selector `"Company"` agrees with `ELP == 0` | 147 / 147 agree, 0 disagree |
| selector `"Industry"` agrees with `ELP <> 0` | 246 / 254 agree — all 8 exceptions are class `15191`, whose ELP is legitimately 0 in the table because it is computed from `WorkersCompensationRate` instead |

State-deviation census (`scripts/erc/29_census_336.py --rules
GeneralLiabilityClassificationOwnersContractorsCoverageRules`, `GATE-335` § 6): 49 of 51
jurisdictions are pure countrywide across all 562 packages in the corpus; the only overrides are
`SetILF` (NY) and `SetMoldStatCode` (AK, NY).

**No oracle exists for this subline.** `GATE-335` § 8 states plainly: *"this gate is not validated
against ISO arithmetic."* One rated output exists in the corpus (the Oklahoma golden case) and it
carries no OCP coverage. Of 516 STC submissions, 8 carry an `OwnersContractorsExposure` and none
has a paired expected output; those 8 are recorded in `GATE-335` § 8 as the seed set for a future
regression fixture. Every table-row count and jurisdiction count in this document should be
treated as **derived and unvalidated** until that fixture exists.
