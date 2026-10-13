# Sub-Standard Condition Code Dropdown — Data Source and Structure

**Purpose:** Lets a user pick a sub-standard condition by its plain-English label and derive the
single-letter code (`A`–`E`) that keys `SubStdConditionRate.csv` and the
`SubStdConditionA`…`E` "Yes"/"No" fields in `CommercialPropertyStructure`
(`CommercialPropertyStructureRules.Rule.xml`). Companion to `SubStdConditionRate.csv` /
`README_SubStdConditionRate.md`, which previously flagged what A–E mean as an open question —
resolved here.

**Source:** `Form Fields\Fields.FormField.csv` (path:
`C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\Form Fields\Fields.FormField.csv`), rows
for `SubStdConditionA` through `SubStdConditionE` (`CommercialPropertyStructure` DataDefGroup).
This is a form-field UI label/description table, not a rate table or metadata entry — the earlier
search of `Metadata\RateTables.Metadata.xml` and the DataDef XSD found no description there,
which is why this was originally logged unresolved.

**Output file:** `SubStdConditionCode_Label.csv` (columns: `SubStandardCondition`, `Label`,
`Description`) — 5 rows, one per condition.

| Code | Label | Description |
|---|---|---|
| A | Heating and Cooking | Unsafe arrangement of heating including chimneys, stovepipes and gas vents and unsafe arrangement of cooking devices. |
| B | Wiring | Unsafe or inadequate electric wiring, non-standard extensions, overloading, overfusing. |
| C | Conversion | Subdivision or conversion of original living spaces into multiple units with overcrowded occupancy. |
| D | Physical Condition and Housekeeping | Building not in good repair, roof or chimneys deteriorating, wood surfaces unpainted or decaying, garages or porches not well maintained and yards, basements, hallways or attics not kept clean and free from rubbish and litter. |
| E | Exposure | For adjoining properties of an exceptionally hazardous nature. |

Genuine 1:1 lookup both directions, same as `ConstructionCode_Description.csv` — either
`Label → SubStandardCondition` (for a dropdown) or `SubStandardCondition → Label` (for display)
works cleanly.

## Why the rate pattern splits the way it does

This resolves the two-tier rate split noted in `README_SubStdConditionRate.md`: **A, C, D**
(Heating/Cooking, Conversion, Physical Condition and Housekeeping) share the higher rate tier;
**B, E** (Wiring, Exposure) share the lower tier. Not arbitrary — it groups by condition type, and
now that the labels are known, that grouping reads as internally consistent (structural/occupancy
conditions vs. wiring/exposure conditions), though the underlying bureau rationale for exactly
that split still isn't documented anywhere in this corpus.

## Not covered

`Fields.FormField.csv` carries many other columns (validation flags, glossary references, display
order, etc.) not pulled here — only `Label` (the short field label) and `Description` (the long
form-help text) were extracted, since those are the two useful for a dropdown + a
tooltip/reference. Row 2429–2433 in the source file if this needs re-verifying.
