# Products/Completed Operations — Required ERC Tables

**Source:** `docs/gates/GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md` §5 (lookups and their layer), §7
(referral triggers), §8 (golden-case trace); cross-referenced against `docs/gates/GATE-334-PREMISES-OPERATIONS.md`
§5 for the shared inheritance pattern, and `docs/erc/03-RATING-STRUCTURE.md` for corpus-wide table
population counts.

**Line:** General Liability (GL), Subline 336 — Products/Completed Operations.

**Source ERC packages:** state package `GL_OK 20250601 V01` (golden case), declared countrywide
parent `GL_CW_20231201_V03`. Row counts in §5 of the gate are measured on the CW `GL CW 20231201
V03` package and the state `GL_OK 20250601 V01` package specifically. Ten distinct countrywide
parents are in live use across 562 state packages corpus-wide (GATE-334 §0); this document does not
assume any one of them is canonical.

**Derived from:** `ProductsCompletedOperations_RatingAlgorithms.md`

**Documented:** 2026-08-20
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — OK golden (OK@2025-08-01) and OK@2026-08-01 / 2027-04-01 rated offline with every Products lookup key and returned row read from the engine trace; CW row counts re-counted in all five CW packages (20231201 V03, 20260101 V01, 20261001 V01, 20270401 V01, 20270401 V02) and OK row counts in `GL_OK_20250601_V01`, `GL_OK_20260801_V01` and `GL_OK_20270401_V04`; the "not resolved" deductible tables were identified from the rule XML.

This began as a port of the gate's table census. On 2026-10-02 the keys, layers and the row counts
in "Verification" were re-counted from the CSVs and checked against the lookups the engine actually
performed, and edition-scoped tables (pre-2027 vs CW 2027) are now marked. Corpus-wide totals
(`N/A` 21,021, `Not Applicable` 261,973, 620,856 selector agreements) remain the gate's.

All tables below follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern established
for 334 and reused unchanged by 336 (GATE-334 §5) — a state can override any of these with its own
row, but if it doesn't, a `CW` row is required for the lookup to resolve.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `ProdsCompldOpsLossCost` | Base rate, loss-cost path | State, `ProdsCompldOpsTerritory` (statewide `999` corpus-wide), ClassCode — a filed `0` switches to ELP; a **null** (no row) is refused by the engine (OI-94) |
| `ProdsCompldOpsELPFactor` | Base rate, ELP path | State, ClassCode |
| `ProdsCompldOpsELPText` | Rating-basis selector (N17) — closed vocabulary: `Rate/Loss Cost Applies`, `Industry`, `Company`, `Not Applicable`. Read by ISO's classification-level `SetProdsCompldOpsELP`; the engine adds no N17 assertion | State, ClassCode |
| `IncreasedLimitsTableAssignmentProdsCompldOps` | ILF table letter (`A`/`B`/`C`), or `Refer To Co.` / `N/A` | State, ClassCode |
| `ILFProds` | `CSLILF` | State, table-letter, Each Occurrence Limit, General Aggregate Limit — limit values `"1,000,000 CSL"` pre-2027, `"1,000,000"` from the 2027-04-01 filings (OI-96/97) |
| `ProdsCompldOpsLCM` | Loss cost multiplier | State, `"Y"` — one CW row `"CW","Y",1` in every edition; OK files none |
| `ProdsCompldOpsClaimsMadeMultipliers` (pre-2027) / `ClaimsMadeMultiplierProdsCompldOps` (CW 2027) | Claims-made year multiplier | State/CW, year (capped at 5), ClassCode (pre-2027) / ClassificationType (CW 2027) |
| `GeneralLiabilityDefenseWithinLimitsProdsCompldOpsTable` | Gates the Defense-Within-Limits multiplier — tested by **row existence**, not by a value | State (row present or absent) — this is an input (submission) table, not a rate table |

## Coinsurance/LOI/deductible tables

Products/Completed Operations has no coinsurance concept (that is a Commercial Property mechanic —
see the CF templates this document format is ported from). The analogous premium-modifying tables
here are limit-of-insurance/increased-limits and deductible:

| Table | Used for |
|---|---|
| `IncreasedLimitsTableAssignmentProdsCompldOps` | see above — repeated here as the ILF assignment table |
| `ILFProds` | see above — repeated here as the ILF factor table |
| `SplitLimitWeightFactorProds{BI,PD,Constant}` (pre-2027 only) | Split-limit weighting (BI/PD/Constant components) when the risk is not CSL-rated. Manufacturing band `50000–59999` confirmed at `0.87` / `0.17` / `0.01` against the manual (GATE-336 §2), vs 334's `0.83` / `0.19` / `0.03` for the same band — a genuinely distinct table, not shared with 334. Both rules are absent from CW 2027 |
| `DedFactorProdsCSL` | Combined BI/PD deductible factor — `SetDeductibleFactor` (CW 2027) / `SetProdsCompldOpsBIPDDeductibleFactorBeforeAdjustment` (pre-2027). Keys CW, table letter, deductible; **CW only, 93 rows**, every edition |
| `DedFactorProdsBI` | BI deductible factor — `SetProdsCompldOpsBIDeductibleFactor`. Same keys; CW only, 93 rows |
| `DedFactorProdsPD` | PD deductible factor — `SetProdsCompldOpsPDDeductibleFactor` (CW 2027) / `…PDDeductibleFactorBeforeAdjustment` (pre-2027). Same keys; CW only, 93 rows. Pre-2027 it is also read at the `"250 Per Claim"` cell by `SetDedFactorProdsPD250PerClaim` (via `LookupDedFactorProdsPDWithArgs`) — there is **no separate `DedFactorProdsPD250PerClaim` table**; that name is a DataDef |

*Resolved 2026-10-02 from the rule XML (previously "not resolved in source docs"):* the
pre-adjustment stage reads `DedFactorProdsCSL` / `DedFactorProdsPD`; the adjusted factor is
`BeforeAdjustment − DedFactorProdsPD250PerClaim` when `SprayPainting = "Yes"` or the class is one of
`10075, 10368, 98303–98307, 98309, 99003, 99004`, else unchanged. The stage exists only pre-2027 and
**is not Products-only** — Premises/Operations has the identical stage over
`DedFactorPremOps{CSL,PD}`. Golden trace: `DedFactorProdsCSL['CW','B','No Deductible'] → 0`.

## Premium-level tables

| Table | Used for |
|---|---|
| `ProdsCompldOpsMinPremium` (pre-2027 only) | `MinimumPremium` input to `SetMinPremium` (`MinPremium = round(MinimumPremium × FinalILF × AdditionalInterestFactor, 0)`) — computed inside `ErcRate`. **334 has the same step** (`PremOpsMinPremium`) in the pre-2027 editions; neither subline has a minimum-premium rule in CW 2027, where this table is header-only. CW only, 3 rows, all `0`, so the pre-2027 policy-level top-up (`GeneralLiabilityProdsCompldOpsPremiumToReachMinCoverage`) is `0` on filed data *(corrected 2026-10-02)* |

## Statistical/subline tables

**Not resolved in source docs.** GATE-336 §6 names statistical-coding *rule* overrides
(`SetCoverageStatCode`, `SetMoldStatCode`, `ErcSetStatisticalCodes`, and related) as part of the
19-jurisdiction override census, but does not name the underlying table(s) those rules look up for
subline 336, the way 334's gate names `DeductibleStatCode` and the four `SublineBasicGroupI...`-
style tables for its own subline. No statistical/subline table names for 336 are given anywhere in
the source docs read for this port.

Seen in the engine trace (2026-10-02, OK@2027-04-01), not in the gate: the statistical pass reads
the countrywide `Subline` table (`"CW", "Products/Completed Operations"` → `336`) along with
`LimitsIdentifier2` and `RatingIdentificationCode`. None affects premium.

## Not ERC tables

Per GATE-334 §1b/§4 (shared machinery, reused by 336 without restatement in GATE-336):
`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse`, and
`AdditionalInterestFactor` are policy-level inputs copied down the tree via `rul:Copy`, not looked
up via `rul:Lookup` — not filed rate tables. (`AdditionalInterestFactor` is read only by the
pre-2027 `SetMinPremium`; nothing reads it in CW 2027.) **Corrected 2026-10-02:** `LCM` *is* sourced
from a table — the engine trace shows `ProdsCompldOpsLCM['CW','Y'] → 1` (OK files no row; the
countrywide row answers), so E9's `1.0` is a filed value, not an engine placeholder.

`ManualPremium` is a user-entered Form Fields / Ratebook Columns input, never written by any rule
(`03-RATING-STRUCTURE.md` §3.4) — not applicable to the rate-driven 336 path specifically, but noted
because 90.7% of the schema's premium-writing tables corpus-wide take this shape and 336 is one of
the minority (16–19 of 477 coverage groups, per the same section) that is genuinely rate-driven
rather than a pass-through.

---

## Verification

**Row-population census (GATE-336 §5), measured on `GL CW 20231201 V03` and `GL_OK 20250601 V01`:**

| Table | Countrywide | Oklahoma | Layer |
|---|---|---|---|
| `ProdsCompldOpsLossCost` | **0 rows** | 1,188 | **state only** |
| `ILFProds` | **0 rows** | 432 | **state only** |
| `ProdsCompldOpsELPFactor` | **0 rows** | 1,188 | **state only** |
| `ProdsCompldOpsELPText` | **0 rows** | 1,188 | **state only** |
| `IncreasedLimitsTableAssignmentProdsCompldOps` | **0 rows** (header only — present, not absent) | **1,196** (the gate reported 1,188; re-counted 2026-10-02) | **state only** |
| `ProdsCompldOpsLCM` | 1 (`"CW","Y",1`) | absent | **countrywide only** |
| `DedFactorProdsCSL` / `BI` / `PD` | 93 each | absent | **countrywide only** |
| `ProdsCompldOpsMinPremium` | 3 (all `0`) | absent | **countrywide only** |

**Re-counted 2026-10-02.** The figures above hold for CW 20231201 V03, 20260101 V01 and 20261001 V01,
and for `GL_OK_20250601_V01` and `GL_OK_20260801_V01`. Under the 2027-04-01 filings
(`GL_CW_20270401_V01`/`V02`, `GL_OK_20270401_V04`): OK `ProdsCompldOpsLossCost`, `ELPFactor`,
`ELPText` and the ILTA table 1,163 each; `ILFProds` **216** (limit keys lose the `" CSL"` suffix);
CW `ProdsCompldOpsMinPremium` header-only; the four CW header-only tables are still header-only. In
`GL_OK_20270401_V04`, 400 classes carry ILTA `N/A` and the same 400 carry `ELPText = "Not
Applicable"` — exact agreement.

**Four header-only countrywide tables sit in a live rating path** — `ProdsCompldOpsLossCost`,
`ILFProds`, `ProdsCompldOpsELPFactor`, `ProdsCompldOpsELPText` all resolve to zero rows at the
countrywide level. Reading any of them as populated (rather than checking row counts) would silently
produce a `0.0` lookup result. This is the same class of finding as the CF sibling document's
`BasicGroupIRate`/`BasicGroupIIRate` header-only correction — "table exists" and "table has a usable
row" are different claims, and only the second is load-tested here: the Oklahoma golden case
resolves every one of the four against the **state** package, never the countrywide one.

**Referral-trigger population (GATE-336 §7):**

- `IncreasedLimitsTableAssignmentProdsCompldOps = "Refer To Co."` — present in all 51 jurisdictions,
  exactly 2 class codes each (Oklahoma: `54444`, `94444`).
- `IncreasedLimitsTableAssignmentProdsCompldOps = "N/A"` — 21,021 rows, **35%** of the table.
- `ProdsCompldOpsELPText = "Not Applicable"` — 261,973 rows. Proposed (N17) to be asserted against
  the `N/A` ILTA rows above; the built engine does not assert it, and prices such a class at `0`
  (pre-2027) or `$1` (CW 2027 floor) with no referral — OK class `10015`, engine-verified
  2026-10-02. Agreement re-checked for `GL_OK_20270401_V04` only (400 / 400).

**End-to-end reproduction:** the Oklahoma golden case
(`tests/fixtures/golden-ok-2025.json`, `tests/verify_golden.py`) reproduces `Premium = 6,845.00`
against ISO's own output, **80/80 checks pass across three independent layers** — fixture vs ISO's
output, fixture vs the ERC CSVs, and the arithmetic re-derived in `Decimal` (GATE-336 header, §8).
Re-run through the built engine on 2026-10-02: `6,845` (policy `7,839`) at OK@2025-08-01, and
`7,215` from the same tables' 2026 and 2027 OK editions (`ILFProds B` = `1.76`).
Every table row consumed by the golden case is cited by name and by the exact key tuple in the
"Quick reference" section of the companion `ProductsCompletedOperations_RatingAlgorithms.md`.

**Not independently re-verified in this port:** whether the four header-only countrywide tables
above ever carry a `CW` row in any of the other 561 packages in the corpus (334's sibling correction
in the CF template was itself found only when a second, unrelated pass — Personal Property —
happened to hit the same table). GATE-336 does not report running that check for 336's own tables;
flagging it as an open item for a future pass, not as a finding of this document.
