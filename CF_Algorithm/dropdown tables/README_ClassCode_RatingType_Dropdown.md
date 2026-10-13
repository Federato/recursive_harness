# Class Code → Rating Type Dropdown — Data Source and Structure

**Purpose:** Per-ClassCode determination of which Basic Group I rating type applies — `Class` or
`Specific` — for driving the rating algorithm's rate lookup (Class-rated buildings use
`BasicGroupIRate` keyed by `ClassCode`; Specific/Tentative-rated buildings are rated by individual
building characteristics instead of a class-code table lookup).

**Source table:** `DomainClassDesc.DomainTable.csv` (same source as `BuildingClassCode_Description.csv`)
**Source path:** `C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Domain Tables\DomainClassDesc.DomainTable.csv`

## Method

For each of the 154 unique Class Codes in the source table, collected the full set of `RatingType`
values (`Class`, `Specific`, `Tentative`) that code appears under. There are only three combinations
in the data:

| Combination | # Codes |
|---|---|
| Class + Specific + Tentative | 96 |
| Specific + Tentative (no Class) | 50 |
| Class only | 8 |

**Applied rule (updated per direction received 2026-09-03):** label a code `Class` whenever Class
rating is available for it ("Class-eligible" codes default to Class), regardless of whether
Specific/Tentative are also available for that code. Only label it `Specific` when Class is not an
option at all for that code. This collapses the three raw `RatingType` values into the two-value
output the dropdown needs.

Result: **104 codes → `Class`** (the 96 codes with all three rating types, plus the 8 Class-only
codes), **50 codes → `Specific`** (codes with only Specific/Tentative available, no Class option).

> **Superseded rule.** The original pass used the opposite priority — Specific/Tentative availability
> won over Class, giving 146 `Specific` / 8 `Class`. Reversed per follow-up direction: Class-eligible
> codes now default to `Class` rating instead.

For reference, the 8 codes that are Class-only (no Specific/Tentative option exists for these in this
filing edition, so they were always `Class` under either rule): `0196, 0197, 0198, 0581, 0582, 1150,
1650, 1700`.

**Output file:** `ClassCode_RatingType.csv` (columns: `ClassCode`, `RatingType`) — 154 rows, one per
Class Code, covering the full code universe (not just the 104 Class-ratable codes in
`BuildingClassCode_Description.csv`, since determining this required also seeing the 50 codes that
are Specific/Tentative-only).

## Note on scope vs. the Description dropdown

`BuildingClassCode_Description.csv` (built earlier) only contains the 104 codes that have a `Class`
rating-type row, because that file's purpose is the Class-rated description lookup. This file's
universe is larger (154 codes) because a Rating-Type determination needs to see codes that are
Specific/Tentative-only too. If the two tables are joined in the workbook, the 50
Specific/Tentative-only codes will have a `RatingType` here but no row in the Description table — by
design, since those codes are never Class-rated and so were out of scope for that pull.
