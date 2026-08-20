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

All tables below follow the two-pass `FirstNonNull(state row, "CW" row)` lookup pattern established
for 334 and reused unchanged by 336 (GATE-334 §5) — a state can override any of these with its own
row, but if it doesn't, a `CW` row is required for the lookup to resolve.

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `ProdsCompldOpsLossCost` | Base rate, loss-cost path | State, `ProdsCompldOpsTerritory` (statewide `999` corpus-wide), ClassCode |
| `ProdsCompldOpsELPFactor` | Base rate, ELP path | State, ClassCode |
| `ProdsCompldOpsELPText` | Rating-basis selector (N17) — closed vocabulary: `Rate/Loss Cost Applies`, `Industry`, `Company`, `Not Applicable` | State, ClassCode |
| `IncreasedLimitsTableAssignmentProdsCompldOps` | ILF table letter (`A`/`B`/`C`), or `Refer To Co.` / `N/A` | State, ClassCode |
| `ILFProds` | `CSLILF` | State, table-letter, Each Occurrence Limit, General Aggregate Limit |
| `GeneralLiabilityDefenseWithinLimitsProdsCompldOpsTable` | Gates the Defense-Within-Limits multiplier — tested by **row existence**, not by a value | State (row present or absent) |

## Coinsurance/LOI/deductible tables

Products/Completed Operations has no coinsurance concept (that is a Commercial Property mechanic —
see the CF templates this document format is ported from). The analogous premium-modifying tables
here are limit-of-insurance/increased-limits and deductible:

| Table | Used for |
|---|---|
| `IncreasedLimitsTableAssignmentProdsCompldOps` | see above — repeated here as the ILF assignment table |
| `ILFProds` | see above — repeated here as the ILF factor table |
| `SplitLimitWeightFactorProds{BI,PD,Constant}` | Split-limit weighting (BI/PD/Constant components) when the risk is not CSL-rated. Manufacturing band `50000–59999` confirmed at `0.87` / `0.17` / `0.01` against the manual (GATE-336 §2), vs 334's `0.83` / `0.19` / `0.03` for the same band — a genuinely distinct table, not shared with 334 |
| `DedFactorProdsPD250PerClaim` | A named single-cell deductible carve-out feeding `SetDedFactorProdsPD250PerClaim` |
| *(unnamed in source)* | `SetProdsCompldOps{BIPD,PD}DeductibleFactorBeforeAdjustment` reads a pre-adjustment deductible factor. **Not resolved in source docs — GATE-336 names the rule but not the underlying table(s) it looks up.** |

## Premium-level tables

| Table | Used for |
|---|---|
| `ProdsCompldOpsMinPremium` | `MinimumPremium` input to `SetMinPremium` (`MinPremium = round(MinimumPremium × FinalILF × AdditionalInterestFactor, 0)`) — computed inside `ErcRate`, a step 334 has no equivalent of |

## Statistical/subline tables

**Not resolved in source docs.** GATE-336 §6 names statistical-coding *rule* overrides
(`SetCoverageStatCode`, `SetMoldStatCode`, `ErcSetStatisticalCodes`, and related) as part of the
19-jurisdiction override census, but does not name the underlying table(s) those rules look up for
subline 336, the way 334's gate names `DeductibleStatCode` and the four `SublineBasicGroupI...`-
style tables for its own subline. No statistical/subline table names for 336 are given anywhere in
the source docs read for this port.

## Not ERC tables

Per GATE-334 §1b/§4 (shared machinery, reused by 336 without restatement in GATE-336):
`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse`, and
`AdditionalInterestFactor` are policy-level inputs copied down the tree via `rul:Copy`, not looked
up via `rul:Lookup` — not filed rate tables. `LCM` is held at `1.0` by decision (GATE-334 §4, "E9"),
not sourced from a table in the golden-case trace.

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
| `IncreasedLimitsTableAssignmentProdsCompldOps` | absent | 1,188 | **state only** |
| `ProdsCompldOpsMinPremium` | 3 | absent | **countrywide only** |

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
- `ProdsCompldOpsELPText = "Not Applicable"` — 261,973 rows. Asserted (N17) to agree with the `N/A`
  ILTA rows above; not independently re-verified in this port.

**End-to-end reproduction:** the Oklahoma golden case
(`tests/fixtures/golden-ok-2025.json`, `tests/verify_golden.py`) reproduces `Premium = 6,845.00`
against ISO's own output, **80/80 checks pass across three independent layers** — fixture vs ISO's
output, fixture vs the ERC CSVs, and the arithmetic re-derived in `Decimal` (GATE-336 header, §8).
Every table row consumed by the golden case is cited by name and by the exact key tuple in the
"Quick reference" section of the companion `ProductsCompletedOperations_RatingAlgorithms.md`.

**Not independently re-verified in this port:** whether the four header-only countrywide tables
above ever carry a `CW` row in any of the other 561 packages in the corpus (334's sibling correction
in the CF template was itself found only when a second, unrelated pass — Personal Property —
happened to hit the same table). GATE-336 does not report running that check for 336's own tables;
flagging it as an open item for a future pass, not as a finding of this document.
