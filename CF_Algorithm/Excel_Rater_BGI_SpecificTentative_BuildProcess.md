# Build Process — Basic Group I Specific/Tentative Rating

**Written:** 2026-09-14. **Source:** `Excel_Rater_BasicGroupI.md` §9 (traced 2026-09-04), which remains
the authoritative reference — this document restates it as an ordered build procedure, it doesn't add new
findings.

**Status:** analysis only, nothing built yet. Per standing project rule, nothing in this document gets
entered into the live workbook until you say go.

---

## 1. What this is, in plain English

Basic Group I is the only Commercial Fire form that gives an underwriter a second way to rate a building
or its contents. The normal way — **Class rating** — looks up a rate from ISO's class/construction tables
based on the building's occupancy and construction. **Specific/Tentative rating** skips that lookup
entirely and instead uses a rate someone else has already decided on and typed in — no table, no
class code, no construction code. Basic Group II, Broad, and Special don't have this second path at all;
Class rating is their only option, confirmed directly from the source rule comparison table.

Think of it as an escape hatch: for a small number of risks, ISO lets the rate come from outside its own
tables. The workbook needs a fork in the road — "which kind of rate am I using for this building?" — and
then two different ways of computing `Rate` depending on the answer.

## 2. The rating grid — every Building factor, Class vs. Specific/Tentative

This is the question to answer before building anything: **of every factor that feeds a Class-rated
Building's `FinalRate`, which ones still apply when the building is Specific/Tentative-rated, and which
ones don't?** Building only for now — Contents follows the same method but isn't gridded out yet.

The source doc (`Excel_Rater_BasicGroupI.md` §9) gives one explicit formula for the Specific/Tentative
`Rate` step and says everything after `Rate` is "unchanged." It does **not** individually confirm, factor
by factor, whether the class/construction-side factors it silently drops are meant to be excluded or were
just never mentioned. Per your instruction: **where the source doesn't clearly state a rate or factor
applies, this grid assumes it's neutralized — `1.0` for a multiplicative factor, `0` for an additive
addend** — rather than assumed carried over. That's a stated assumption, not a confirmed ISO rule, and
it's called out per row below.

| # | Factor | Class-rated role | Specific/Tentative — Building | Why |
|---|---|---|---|---|
| — | `SpecificGroupIRate` | *(doesn't exist on this path)* | **used as the rate itself** | Replaces `BaseRate` outright — see the open question in §3. Not a "factor," the substitute for the whole lookup. |
| 1 | `BaseRate` (class/construction lookup) | looked up from `BasicGroupIRate` | **not used** | Specific/Tentative rating exists specifically to bypass this lookup — confirmed, not assumed (`SetBasicGroupIBaseRate` only runs `if RatingType = "Class"`). |
| 2 | `LCM` (loss cost multiplier) | multiplies `BaseRate` | **1.0× is wrong — LCM still applies**, named explicitly in the Specific/Tentative formula | Confirmed — appears directly in the §9 formula. |
| 3 | `SubStdConditionRate` | added to `BaseRate × LCM` | **assumed 0** (no addend) | Omitted from the §9 formula with no explanation — assumed neutralized per your instruction, not confirmed excluded by the source. |
| 4 | `VacantBuildingRate` | added to `BaseRate × LCM` | **assumed 0** (no addend) | Same — omitted, assumed neutralized, not confirmed. |
| 5 | `TerritoryFactor` | multiplies the addend sum | **assumed 1.0** | Omitted from the §9 formula. Territory ordinarily prices *where* the building is, which has no obvious reason to stop mattering just because the rate source changed — but the source doc doesn't say either way, so per your instruction this defaults to 1.0 until confirmed. |
| 6 | `ProtectionClassFactor` | multiplies the addend sum | **assumed 1.0** | Same reasoning and same caveat as `TerritoryFactor` — omitted, not confirmed, defaulted to 1.0. |
| 7 | `RoofSurfacingACVFactor` | multiplies the addend sum | **still applies**, named explicitly in the §9 formula | Confirmed. |
| 8 | `SprinklerLeakageNotExcludedFactor` | *(not part of Class-rated `Rate` at all — different table from row 9)* | **applies**, named explicitly in the §9 formula | Confirmed. Don't confuse this with row 9's similarly-named table — they're different ERC tables feeding different steps. |
| 9 | `SprinklerLeakageExclNonSprinkleredBldgRate` (subtracted in `COLAdj`) | `ROUND(Rate − this, 3)` | **still applies, unchanged** | §9 explicitly says `COLAdj` downstream is unchanged and "reads the same" inputs regardless of rating type. |
| 10 | `SprinklerLeakageExclSprinkleredFactor` | multiplies `COLAdj` | **still applies, unchanged** | Same explicit statement as row 9. |
| 11 | `VandalismExclFactor` | multiplies `COLAdj` | **still applies, unchanged** | Same. |
| 12 | `StdPropPolGroupIFactor` | multiplies `COLAdj` | **still applies, unchanged** | Same. |
| 13 | `CoinsuranceFactor` | lookup, skipped if `ClassCode = "1150"` or Functional Valuation | **still applies, unchanged** — same skip condition | §9 says everything after `Rate` is unchanged; no separate Specific/Tentative rule touches this step. |
| 14 | `LOIFactor` | `LookupBasicGroupILOIFactorBldg(Limit, ...)` | **still applies, unchanged** | Same. |
| 15 | `DeductibleFactor` | `Choose` on `Deductible` | **still applies, unchanged** | Same. |
| 16 | `DeductibleByLocationFactor` | multiplies `FinalRate` | **still applies, unchanged** | Same. |
| 17 | `MultiResidentialPropSpecialCreditFactor` | multiplies `FinalRate` | **still applies, unchanged** | Same. |

**Reading this grid:** rows 3–6 are the ones your instruction actually changes the treatment of. Rows 1
and 8–17 are things the source document confirms one way or the other (either "this is exactly what
replaces the lookup" or "this is exactly what stays unchanged"); rows 3–6 are the genuine gaps — factors
the Class-rated formula uses that the Specific/Tentative formula's text simply doesn't mention. Two of
them (`SubStdConditionRate`, `VacantBuildingRate`) are *additive* addends, so "neutralize" means drop them
to `0`, not `1.0` — multiplying by `1.0` wouldn't remove them from a sum. `TerritoryFactor` and
`ProtectionClassFactor` are multiplicative, so neutralizing means `1.0`.

**One more open branch, not in the grid above:** if `RatingType` is set to something other than `Class`,
`Specific`, or `Tentative`, Building's own `Rate` formula collapses to a flat `1.0` before any of this
even runs — that's the third, `Otherwise` branch confirmed in §9, distinct from the neutralization
question this grid is answering.

## 3. Before you build anything: the one open question

**`SpecificGroupIRate` — the rate itself — is not populated by any rule in either coverage's traced
source document.** No `Set` rule, no `Lookup` rule, nothing. This isn't a table someone forgot to count;
the source docs never say where the number comes from at all.

The best-supported guess is that it's a rate an underwriter or MGA schedules by hand for that specific
risk — that's what "specific" and "tentative" mean as insurance terms — but that is an inference from the
name and industry convention, not a confirmed fact. **Treat this as unresolved until someone checks the
actual ISO rule XML.** The build below treats it as a user-entered field for that reason, not a
`Rate_Tables` lookup — but flag it visibly in the workbook so nobody mistakes "we typed it in" for "we
looked it up."

## 4. Build order

Build in this order — each step only makes sense once the one before it exists.

### Step 1 — Add the rate-type switch to `Locations_Buildings`

`RatingType` already exists on this tab (see `Excel_Rater_Overview.md` §4), but up to this point it's
been an unused placeholder. This build is what actually turns it into a working enum:

| Value | Meaning |
|---|---|
| `Class` | the path already built — class/construction lookup |
| `Specific` | this path — pre-set rate |
| `Tentative` | this path — pre-set rate, same formula as `Specific` |
| anything else (Building only) | falls through to a flat `1.0` — this is a real branch in ISO's own rule, not an error state |

### Step 2 — Add the two rate-entry columns to `Locations_Buildings`

| Column | Feeds | Notes |
|---|---|---|
| `Bldg_SpecificGroupIRate` | Building's Specific/Tentative `Rate` formula | user-entered; add a cell comment citing the open question in §3 above |
| `PP_SpecificGroupIRate` | Contents' Specific/Tentative `Rate` formula | separate column from Building's — a building's Building and Contents specific rates don't have to match |

### Step 3 — Confirm the sprinkler-leakage table row exists

Both formulas below multiply by a sprinkler-leakage factor. Before wiring the formula, check:

| Table | Confirmed? |
|---|---|
| `SprinklerLeakageNotExcluded` (Building) | present by the original sweep, **not independently row-counted** — verify the CW row before relying on it |
| `SprinklerLeakageNotExcludedFactor` (Contents) | confirmed with a real CW row in `PersonalProperty_ERC_Tables.md` — the more reliable of the two |

If Building's row turns out missing when checked, that blocks this build for Building specifically —
don't assume it's there because Contents' sibling table is.

### Step 4 — Add the second `Rate` branch on `Calc_Building_BGI`

This is step 2 of that tab's chain (right after `BaseRate`, which the Class-rated path already computes
but this path ignores). Add it as an explicit `if/elif/else`, not a separate hidden column:

```
Rate =
    if RatingType = "Class":
        <the Class-rated formula already built — Excel_Rater_BasicGroupI.md §4 step 2>
    elif RatingType in ("Specific", "Tentative"):
        Bldg_SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor × RoofSurfacingACVFactor
    else:
        1.0
```

Everything after `Rate` in that tab's chain — `COLAdj`, `CoinsuranceFactor`, `LOIFactor`, `AdjustedRate`,
`DeductibleFactor`, `FinalRate` — is already built and needs **no changes**. It just reads whichever
`Rate` this new branch produced, the same as it already reads the Class-rated `Rate` today.

### Step 5 — Add the second `Rate` branch on `Calc_Contents_BGI`

Same idea, step 4 of that tab's chain, but note two differences from Building:

- The gate is broader: `RatingType <> "Class"` (not just the two named values) routes here — any value
  that isn't `"Class"` falls into this branch.
- **No roof factor**, and **no `1.0` catch-all** — the source doc doesn't give Contents an equivalent
  fallback branch, so don't add one that isn't there.

```
Rate =
    if RatingType = "Class":
        <the Class-rated formula already built — Excel_Rater_BasicGroupI.md §5 step 4>
    else:   # RatingType <> "Class" — covers "Specific", "Tentative", and anything else
        PP_SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor
```

As with Building, everything downstream (`COLAdj` through `FinalRate`) is already built and unchanged.

### Step 6 — Nothing changes in `Premium_Summary`

The premium formulas in §6 of `Excel_Rater_BasicGroupI.md` read `Calc_Building_BGI.FinalRate` and
`Calc_Contents_BGI.FinalRate` regardless of which rating path produced them. No new formula is needed
there — this is exactly why the branch belongs inside the `Rate` step rather than as a parallel premium
calculation.

## 5. What Class-rated and Specific/Tentative-rated share, side by side

| | Building | Contents |
|---|---|---|
| Skips | class/construction lookup, territory/protection-class factors, substandard/vacancy addends | class/construction lookup, `FireSafeVaultFactor`, `ProtectionClassFactor`, substandard addend |
| Uses instead | `SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor × RoofSurfacingACVFactor` | `SpecificGroupIRate × LCM × SprinklerLeakageNotExcludedFactor` |
| Everything after `Rate` | unchanged, same formulas as Class-rated | unchanged, same formulas as Class-rated |

## 6. Test cases to build alongside the formula

Per this project's standing practice, don't build the branch without example rows to prove it against:

1. A building with `RatingType = "Class"` — confirms the new `if` doesn't disturb the existing path.
2. A building with `RatingType = "Specific"` and a `Bldg_SpecificGroupIRate` entered — confirms the new
   branch fires and downstream steps (COL adjustment, LOI, deductible) still apply correctly.
3. A building with `RatingType = "Tentative"` — should produce the identical result to the `"Specific"`
   row above with the same inputs, since Building's formula treats them identically.
4. A building with some other/blank `RatingType` value — Building should fall to `Rate = 1.0`; Contents
   (no catch-all) should still run its Specific/Tentative formula, since its gate is "not Class," not "is
   Specific or Tentative." This divergence is the one case most likely to get built wrong by copying
   Building's logic onto Contents — call it out explicitly in review.
5. A `Specific`-rated building with a non-trivial `TerritoryFactor` and `ProtectionClassFactor` on the
   Class-rated row for the *same* class/construction/location — i.e. pick a test building where those two
   factors are visibly not `1.0` when Class-rated, then flip it to `Specific` with the same location data
   and confirm the workbook actually drops them (per the §2 grid) rather than silently carrying them
   through from a stale formula reference. This is the row most likely to get built wrong quietly, since
   nothing in the formula text stops a careless copy-paste from including a `TerritoryFactor` cell
   reference that happens to still resolve to a number.

## 7. How to configure this once built

1. On `Locations_Buildings`, find the row for the building in question and set `RatingType` to `Class`,
   `Specific`, or `Tentative`.
2. If you set it to `Specific` or `Tentative`, fill in `Bldg_SpecificGroupIRate` and/or
   `PP_SpecificGroupIRate` with the rate you were given for that risk — these are typed in by hand, not
   looked up, because ISO's own rules don't say where this number comes from (see §3).
3. Leave everything else on the row exactly as you would for a Class-rated building — deductible,
   coinsurance, limit, and all the other columns still apply the same way.
4. Check `Calc_Building_BGI` / `Calc_Contents_BGI` for that row: `Rate` should now reflect the
   Specific/Tentative formula instead of the class lookup, and every column after it should populate
   normally.
5. If the resulting premium looks wrong, the first thing to check is whether `SpecificGroupIRate` was
   filled in correctly — this workbook cannot detect a wrong hand-entered rate the way it might catch a
   bad table lookup.

## Remaining steps

1. Verify the four assumed-neutralized rows in the §2 grid (`SubStdConditionRate`, `VacantBuildingRate`,
   `TerritoryFactor`, `ProtectionClassFactor`) against ISO's actual rule XML — the grid currently defaults
   them to 0/1.0 because the source doc's §9 formula simply omits them, not because any rule confirms
   they're meant to drop out.
2. Verify the open question in §3 — check ISO's rule XML directly for any rule that sets
   `SpecificGroupIRate`, rather than relying on the "user-entered" inference.
3. Verify Building's `SprinklerLeakageNotExcluded` CW row (§4) — it's confirmed present but not
   independently row-counted, unlike Contents' sibling table.
4. Once Building's grid is confirmed, build the same factor-by-factor grid for Contents — deferred here
   per your instruction to focus on Building first.
5. Nothing gets built into the live workbook until you say go.
