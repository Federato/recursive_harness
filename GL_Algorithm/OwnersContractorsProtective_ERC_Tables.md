# Owners & Contractors Protective / Principals Protective — Required ERC Tables

**Source ERC packages:** `GL_CW_20230501_V01`, `GL_CW_20231201_V02`/`V03`, `GL_CW_20260101_V01`,
`GL_CW_20261001_V01` (pre-2027 algorithm) and `GL_CW_20270401_V01`/`V02` (2027 algorithm)
**Line:** General Liability (GL), Countrywide, Subline Code 335, Rule 46
**Derived from:** `OwnersContractorsProtective_RatingAlgorithms.md`, and originally
`docs/gates/GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md`
**Documented:** 2026-08-20
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — every table below observed in engine lookup traces (AR/WY OCP STCs rated at 2023-05-01, 2026-10-02, 2027-04-01) and its layer/row population censused through the engine's resolver across all 51 jurisdictions as of 2026-10-02 and 2027-04-01.

This lists every ERC table required to rate OCP / Principals Protective coverage, resolved from
the lookups and rule chain traced in `GATE-335` §§ 1, 4, 5, 6, and confirmed against the manual at
`GATE-335` § 2. Row and jurisdiction counts were **re-derived on 2026-10-02** from the tables the
engine actually resolves (state package over its declared CW parent, as of the date shown); where
they differ from the gate document the engine figure is given. See **Verification** below.

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
| `PrincipalsProtvLiabFactor` | Workers-Compensation-derived ELP factor for class `15191` (pre-2027 only) | `"CW","Y"` (single countrywide cell `0.75`, no state override; CW 2027 keeps the table with 0 rows) |
| `OwnersContractorsLCM` | Loss cost multiplier (missing from the gate doc's list; read by `SetLCM`) | `"CW","Y"` — 1 countrywide row, value `1`, no state override, all editions |

Loss-cost and ELP tables carry **zero countrywide rows** — they resolve only from a state-specific
row, or not at all. **Engine census:** as of 2026-10-02 the loss-cost, ELP, ELP-text and
homogeneity tables are each populated in all 51 jurisdictions (563 rows; 204 non-zero loss costs,
204 non-zero ELPs) and `ILFOwnersContractors` in all 51 (3,672 rows). As of 2027-04-01 the
loss-cost tables are declared only by the 5 states still on a pre-2027 parent (CA, GA, NJ, NY, WA;
55 rows, 20 non-zero) and the ELP family by all 51 (424 rows, 249 non-zero). The gate doc's
"8 jurisdictions" was a 2027-cliff figure, not a current one. **Every `...OverOneMillion` and
`...OverOneHundred` cell is `0` in every state at both dates.**

A class missing from the state's `OwnersContractorsLossCost` makes the engine refuse the risk
(OI-94, null `LossCost`); a class missing from the 2027 `OwnersContractorsELP` is **not** refused
and prices at the `$1` floor (see the algorithm doc's engine finding).

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
| `PremOpsMinPremium` | Minimum premium (pre-2027 only) — **reused from subline 334 (Premises/Operations)**, not an OCP-specific table. Keyed (State\|CW, hardcoded `"2"`) → `0`. Applied through the policy-level `GeneralLiabilityOwnersContractorsPremiumToReachMinCoverage` top-up, not inside the classification premium | countrywide, 3 rows; 0 rows at CW 2027 |

There is no `PackageModFactor` table or equivalent for this subline — `GATE-335` § "1. The
algorithm" states explicitly that OCP has no `PackageModFactor`, unlike sublines 334 and 336. There
is also no cyber-exclusion or IRPM-style factor documented for OCP in the gate source.

---

## Statistical / subline tables

| Table / rule | Used for |
|---|---|
| `SetMoldStatCode` | Statistical mold coding, no premium effect. Overridden by AK and NY; all other jurisdictions run the countrywide rule (`GATE-335` § 6; re-confirmed against the packages resolved 2026-10-02 and 2027-04-01) |
| `PolicyLimitsOwnersContractorsStatCode` | Limit stat code, keyed (State\|CW, occurrence limit, aggregate limit); CW `["1,000,000","2,000,000"] → "73"` (engine trace) |
| `OwnersContractorsHomogeneityIndex` | Written to the classification by `GeneralLiabilityClassificationRules.SetOwnersContractorsHomogeneityIndex` (e.g. AR `15191` → `"3/A"`); no premium effect. 51/51 · 563 rows (2026-10-02), 424 (2027-04-01) |

> `SetMoldStatCode` calls `LookupMoldNAStatCode` (engine trace); its table is statistical only.

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
target matrix. **On 2026-10-02 this was re-done through the engine:** each table was observed in a
live lookup trace (state-then-CW `FirstNonNull`, with the package that answered), and its layer and
rows were counted from the tables the resolver actually returns for all 51 jurisdictions (N3: a
state declaration wins even when empty).

The three consistency tests, re-run by the engine on the resolved tables:

| Test | `GATE-335` § 7 (earlier snapshot, 433 rows) | Engine, 2026-10-02 (563 rows) | Engine, 2027-04-01 (424 rows) |
|---|---|---|---|
| `"Rate/Loss Cost Applies"` ⇔ non-zero loss cost | 433 / 433 | 204 / 204 | 20 / 20 (the 5 pre-2027 states) |
| `"Company"` ⇔ `ELP == 0` | 147 / 147 | 104 / 104 | 150 / 150 |
| `"Industry"` ⇔ `ELP <> 0` | 246 / 254 (8 × class `15191`) | 204 / 255 (51 × class `15191`, ELP computed from `WorkersCompensationRate`) | 249 / 254 (5 × `15191` in the pre-2027 states) |

State-deviation census (`scripts/erc/29_census_336.py --rules
GeneralLiabilityClassificationOwnersContractorsCoverageRules`, `GATE-335` § 6): 49 of 51
jurisdictions are pure countrywide across all 562 packages in the corpus; the only overrides are
`SetILF` (NY) and `SetMoldStatCode` (AK, NY).

**No ISO oracle exists for this subline.** `GATE-335` § 8 states plainly: *"this gate is not validated
against ISO arithmetic."* One rated output exists in the corpus (the Oklahoma golden case) and it
carries no OCP coverage. Of 516 STC submissions, 8 carry an `OwnersContractorsExposure` and none
has a paired expected output. The table counts above are now engine-measured rather than
gate-reported, and the engine rates those STCs end to end (AR STC → `13,125` for class 15191 at
2023-05-01, matching `GATE-335` § 8's derivation), but the premiums remain unvalidated against ISO.
