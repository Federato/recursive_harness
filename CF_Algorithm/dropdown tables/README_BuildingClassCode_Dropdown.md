# Building Class Code Dropdown — Data Source and Structure

**Purpose:** Source data for a Basic Group I (BGI) building-class dropdown in the rater workbook,
including which rating method (`Class` vs. `Specific`) applies to each code.

**Source table:** `DomainClassDesc.DomainTable.csv`
**Source path:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Domain Tables\DomainClassDesc.DomainTable.csv`
**Table metadata code:** `DomainTableClassDesc` / `BureauRuleNumberClassificationTable` (per `DomainClassDescDef.DomainTableDef.xml`)
**Row count confirmed:** 2,281 lines (1 header + 2,280 data rows) in the source file.

**Output file:** `BuildingClassCode_Description.csv` (columns: `ClassCode`, `Description`, `RatingType`)
— 882 rows, covering all **154 unique Class Codes**.

## What was pulled and how RatingType was derived

The source table is keyed on `StateCode, RatingType, ClassCodeBldg`, with three `RatingType` values —
`Class`, `Specific`, `Tentative` — the three Basic Group I rating methods. For each ClassCode, the
descriptions are identical across whichever rating types it appears under, so the row set was built
as follows:

1. For each ClassCode, collect the set of `RatingType`s it appears under. Only three combinations
   exist in the data:

   | Combination | # Codes |
   |---|---|
   | Class + Specific + Tentative | 96 |
   | Specific + Tentative (no Class) | 50 |
   | Class only | 8 |

2. Derive a single `RatingType` label per code (**as directed, updated**): `Class` whenever Class
   rating is available for that code (the code is "Class-eligible"), regardless of whether
   Specific/Tentative are also available; `Specific` only when Class is not an option at all.
   Result: **104 codes → `Class`** (the 96 Class+Specific+Tentative codes plus the 8 Class-only
   codes), **50 codes → `Specific`** (the Specific+Tentative-only codes, which have no Class option).

   > **Superseded rule.** An earlier pass used the opposite priority (Specific/Tentative availability
   > wins over Class), giving 146 `Specific` / 8 `Class`. That was reversed per direction received
   > after this file was first built — Class-eligible codes now default to `Class`.
3. Pull that code's descriptions from `Class` rows if available, else `Specific`, else `Tentative`
   (all three carry the same description set per code, so this is just picking one source, not
   merging different data).

## Important structural note — Description is many-to-one with ClassCode

A single `ClassCode` covers many distinct occupancy descriptions rated identically (e.g. ClassCode
`0570` covers 33 different occupancies — hatcheries, florists, pet stores, paint stores, etc.). Of the
154 codes, **most map to multiple descriptions** (this was 87 of 104 when only the Class-rated subset
was considered; the fuller 154-code set follows the same pattern).

Descriptions themselves are unique — every description maps to exactly one ClassCode.

**Practical implication for the dropdown:** a lookup driven by *Description* (`Description` →
`ClassCode`, `RatingType`) is a clean one-to-one `VLOOKUP`/`XLOOKUP`. A lookup driven by *ClassCode*
(`ClassCode` → `Description`) is inherently one-to-many — a simple `VLOOKUP` will silently return only
the first matching description for any code that has more than one. `RatingType`, by contrast, is
1:1 per ClassCode regardless of direction (every row for a given code carries the same `RatingType`).

## Not covered

This pull is Basic Group I (Building) only, Countrywide (`CW`) baseline. It does not include:
- Basic Group II class codes/descriptions (separate table, not pulled here)
- State-specific overrides to this list (CW is the fallback; AL, checked earlier, has no state-level
  override — not all states were checked)
- Special Class codes (Basic Group I "Special" rating uses a different classification track and no
  code/description table)

## Superseded file

`ClassCode_RatingType.csv` (built in the prior pass, `ClassCode`/`RatingType` only, same 154-row
universe) is now redundant with this file's `RatingType` column — kept on disk but no longer needed
if this combined file is used.
