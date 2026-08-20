# Liquor Liability — Required ERC Tables

**Source gate doc:** `docs/gates/GATE-332-LIQUOR-LIABILITY.md`
**Line:** General Liability (GL), subline 332, ISO Rule 45
**Derived from:** `LiquorLiability_RatingAlgorithms.md`
**As-of date:** 2026-08-11 (per gate doc), covering the 51 packages in force on that date across
three countrywide parents (`GL_CW_20231201_V02`, `...V03`, `GL_CW_20260101_V01` — V03 and 20260101 are
byte-identical for this coverage group)
**Documented:** 2026-08-20

This lists every ERC rate table (CW and/or state-filed) required to rate Liquor Liability, resolved
from GATE-332-LIQUOR-LIABILITY.md's trace of `ErcSetRatesAndFactors` / `ErcRate` in
`GeneralLiabilityClassificationLiquorCoverageRules.Rule.xml` down to each `Lookup`'s target table, and
the gate doc's own row-count verification against the corpus.

Every lookup here follows the two-pass `FirstNonNull(state row, "CW" row)` pattern **except where
noted** — liquor is the first subline the source project found where several rating operands
(deductible, LCM, minimum premium, claims-made multiplier) live **only** at the countrywide layer,
with zero state rows, inverting the usual pattern (per GATE-332-LIQUOR-LIABILITY.md § 6).

---

## Rate-build-up tables (state-or-CW keyed)

| Table | Used for | Keys |
|---|---|---|
| `LiquorELP` | Expected loss potential (surrogate base rate — there is no filed loss cost) | State (0 CW rows, 51/51 states, 362 rows) |
| `LiquorELPText` | Classification-output selector (`Industry` / `Company`); **written but not read by any rating rule** | State (0 CW rows, 51/51 states, 362 rows) |
| `LiquorLCM` | Loss cost multiplier — a placeholder for the company's markup, not a rate (Escalation E15) | State\|CW (CW: 1 row, value `1`; 0/51 states) |
| `ILFLiquor` | Increased limits factor | State, `EachCommonCauseLimit`, `AggregateLimit` (0 CW rows, 50/51 states, 3,531 rows) |
| `ILFLiquorStException` | Illinois's ILF override — different table name **and** different key arity | State (IL only), `AggregateLimit` alone (5 rows) |
| `DedFactorLiquor` | Deductible factor — all 21 options `0` by design (referral, per manual 45.J.3) | State\|CW (CW: 21 rows; 0/51 states) |
| `ProdsCompldOpsClaimsMadeMultiplier` | Claims-made year multiplier (shared with Products/Completed Operations) | `min(YearInClaimsMade, 5)` (CW: 5 rows) |
| `LiquorLiabGrade` | Liquor liability hazard grade (Rule 45.H) | State\|CW (CW: 7 rows, 16 at 2027; 41/51 states, 292 rows) — no consuming `Set` rule identified in the gate's traced algorithm; see Verification |

## ILF / deductible tables

Liquor has no coinsurance or limit-of-insurance concept in the property sense used elsewhere in this
project — the equivalent mechanism is the increased-limits factor and deductible factor above, netted
together in `SetFinalILF`:

```
FinalILF = round(ILF - DeductibleFactor, 3)
```

Both source tables (`ILFLiquor`, `DedFactorLiquor`) are listed under "Rate-build-up tables" above
rather than broken out separately, since the gate doc treats them as part of the same chain rather
than a distinct coverage-modifier layer.

## Premium-level tables

| Table | Used for |
|---|---|
| `ProdsCompldOpsMinPremium` | Minimum premium, keyed on hardcoded `ILTA = "C"` (shared with Products/Completed Operations). CW: 3 rows, all `0` — structurally zero for every liquor risk today (Escalation E16); table and both consuming rules deleted at CW 2027 |

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, and `ModToUse` are
consumed by `SetFinalRate` but the gate doc describes their absent-value behavior as resolving via
`FirstValue` (§ 5) — the same behavior CF's building doc documents for `rul:Copy` policy-level inputs,
not a table `Lookup`. Treated as **Not ERC tables** below on that basis, though the gate doc does not
independently confirm the underlying rule body the way the CF doc does with cited line numbers.

## Statistical/subline tables

| Table | Used for | Note |
|---|---|---|
| (unnamed) | Liquor exposure/coverage statistical code output | **Not resolved in source docs** — GATE-332-LIQUOR-LIABILITY.md § 4 documents a defect in `SetLiquorExposureStatCode` (CW 2027 tests the pre-2027 `PremiumBasis` vocabulary and never matches) but does not name the target table the stat code is written to |
| `ClassCodeLiquor` | Liquor class code table, 2,300 rows | per `docs/rating-engine/03-RATING-STRUCTURE.md` line 335; not traced to a specific rule/step in the gate doc's algorithm — included here as a fact found outside the gate doc, flagged accordingly |

## Not ERC tables

`PackageModFactor`, `ExperienceRatingModificationFactor`, `ExpenseModification`, `ModToUse` — per
GATE-332-LIQUOR-LIABILITY.md § 5, these are policy-level inputs; when absent they resolve to `0.0` via
`FirstValue` rather than failing a table lookup, consistent with the "Not ERC tables" treatment CF's
building doc gives `IRPMFactor`/`PackageModFactor`/`MultiPremiumAndDispersionCreditFactor`. Not
independently re-verified against rule XML in this pass (the gate doc does not cite line numbers).

## Uncalled lookups

`LookupNoDedStatCode` and `LookupPremOpsLCM` ship inside the liquor rule file but have no caller
anywhere in the traced chain (per GATE-332-LIQUOR-LIABILITY.md § 3). `LookupPremOpsLCM` points at a
table, `PremOpsLCM`, that the gate doc describes as "identical" in shape to `LiquorLCM` (§ 6) but does
not otherwise detail. Per the gate doc's own conclusion (E14/OI-38, generalized a third and fourth
time here): **treat an uncalled lookup as an inert artifact of the ERC package, not a defect to chase.**

## Not resolved / open items carried from the gate doc

- **`LiquorHomogeneityIndex`** (state-filed, 51/51, 362 rows) — appears in the gate doc's table
  inventory (§ 6) but no `Set` rule in the traced algorithm (§ 1) consumes it. Not resolved in source
  docs.
- **`LiquorLiabTerritory`** — found only outside the gate doc, at
  `docs/rating-engine/03-RATING-STRUCTURE.md` line 541 ("one of the geographic-keyed table columns").
  The gate doc's own traced rate chain (steps 1–16) has no territory-keyed step. Not resolved in
  source docs whether/how this table enters liquor rating.
- **Liquor ILF filing footprint discrepancy.** `docs/rating-engine/03-SUBLINE-COVERAGE-PLAN.md`
  (§ 3.2.3) states the Liquor ILF table is filed as a separate Rule 56.B table only in IL, MN, UT,
  elsewhere a gap — this does not match the gate doc's direct read of `ILFLiquor` (50/51 states
  populated, only Illinois overriding under a different name). Both are reproduced; the gate doc, as
  the more recent and directly-verified source, is treated as authoritative for this doc's tables
  above.

---

## Verification

The gate doc's own verification (per GATE-332-LIQUOR-LIABILITY.md §§ 6, 9, 10) checked row presence
and row counts directly against the corpus rather than file existence alone:

```
LiquorELP                              -- 0 CW rows, 51/51 states, 362 rows total
LiquorELPText                          -- 0 CW rows, 51/51 states, 362 rows; two values only
                                            (Industry x251, Company x111); doubles to 744 at 2027-04-01
ILFLiquor                              -- 0 CW rows, 50/51 states, 3,531 rows (IL exception)
LiquorHomogeneityIndex                 -- 0 CW rows, 51/51 states, 362 rows
DedFactorLiquor                        -- 21 rows CW, 0/51 states, all factor = 0
LiquorLCM                              -- 1 row CW (value 1), 0/51 states
ProdsCompldOpsMinPremium               -- 3 rows CW (all 0), 0/51 states; deleted at CW 2027
ProdsCompldOpsClaimsMadeMultiplier     -- 5 rows CW
LiquorLiabGrade                        -- 7 rows CW (16 at CW 2027), 41/51 states, 292 rows
```

No `Liquor*LossCost` table exists in any jurisdiction at any edition (per GATE-332-LIQUOR-LIABILITY.md
§ 0) — confirmed both by table-inventory search and by the absence of a loss-cost branch in
`SetBaseRate`.

**N16 confirmed a fourth time:** every liquor lookup that resolves at all follows
`FirstNonNull(state row, "CW" row)` on a single table — except the four CW-only tables above
(`DedFactorLiquor`, `LiquorLCM`, `ProdsCompldOpsMinPremium`, `ProdsCompldOpsClaimsMadeMultiplier`),
which have no state rows to fall back from.

**Class cliff, measured as-of** (per GATE-332-LIQUOR-LIABILITY.md § 10): 17 liquor classes in force
2026-08-11; 23 in force 2027-04-01 (16 new codes 50941–50957, exactly matching manual Rule 45.G, plus
7 legacy survivors carried over in the 8 jurisdictions not yet migrated); 10 retired at the cliff.

**No rated test oracle exists.** The project's golden case carries liquor with
`CoverageOnPolicyIndicator = 0` and `Premium = 0.0`, exercising only the entry guard — no rated liquor
output has been verified end-to-end in the source project as of this doc's date (per
GATE-332-LIQUOR-LIABILITY.md § 9).

---
