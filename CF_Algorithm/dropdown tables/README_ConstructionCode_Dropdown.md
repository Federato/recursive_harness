# Construction Code Dropdown — Data Source and Structure

**Purpose:** Source data for the Construction Type/Code dropdown in the rater workbook (feeds the
`ConstructionCode` key used by `BasicGroupIRate`, `BasicGroupIIRate`, and other rate tables keyed on
construction).

**Source table:** `ConstructionCode.RateTable.csv`
**Source path:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Rate Tables\ConstructionCode.RateTable.csv`
**Bureau rule:** `BureauRuleNumber15B` (per `ConstructionCodeDef.RateTableDef.xml`)
**Row count confirmed:** 8 lines (1 header + 6 data rows + 1 trailing blank) — Countrywide (`CW`) only,
no state overrides found or needed; this is one of ISO's universal, non-state-varying tables.

## What was pulled

The table is a straight 1:1 map from `ConstructionTypeToUse` (text) to `Value` (the numeric
`ConstructionCode` used everywhere else in the rating chain, e.g. as a key column in `BasicGroupIRate`):

| ConstructionCode | Description |
|---|---|
| 1 | Frame |
| 2 | Joisted Masonry |
| 3 | Non-Combustible |
| 4 | Masonry Non-Combustible |
| 5 | Modified Fire Resistive |
| 6 | Fire Resistive |

**Output file:** `ConstructionCode_Description.csv` (columns: `ConstructionCode`, `Description`)

This one is a genuine 1:1 lookup both directions — unlike the Building Class Code table, there's no
many-to-one ambiguity here. Either `ConstructionCode → Description` or `Description → ConstructionCode`
works cleanly as a dropdown/derivation pair.

## Not covered

`DomainConstructionCode.DomainTable.csv` (same CW package) was checked first and is empty (header row
only, zero data rows) — it appears to be an unused/placeholder domain table for this edition, not the
active source. `ConstructionCode.RateTable.csv` is the table actually referenced by the rating rules
and is the one used here.
