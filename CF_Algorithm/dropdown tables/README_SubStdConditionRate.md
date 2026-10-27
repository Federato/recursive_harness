# SubStdConditionRate — Data Source and Structure

**Purpose:** Sub-Standard Condition surcharge rate — the `Rate` value looked up by `StateCode` +
`SubStandardCondition` (A–E) + `ConstructionCode` that feeds `SubStdConditionRate` (= SUM of the
rates for every condition A–E flagged "Yes" on the risk) in the Structure premium chain. See
`CommercialPropertyStructureRules.Rule.xml`, rules `LookupSubStdConditionRate` /
`SetSubStdConditionRate` / `SetSubStdCondition{A-E}Rate`.

Metadata ties this field to `BureauRuleNumberLCRule85SubStandardConditionCharges` ("LC_Rule 85
Sub-Standard Condition Charges"), but **that citation could not be confirmed** — the multistate
loss-cost manual on hand (`CF-MU-2022-LC-001-C.pdf`) has no "sub-standard"/"substandard" text
anywhere, and its own Rule 85 is "BASIC GROUP I CLASS RATES," an unrelated topic. Treat the rule
number as unverified provenance, not a citation you can hand to someone else.

**Source table:** `SubStdConditionRate.RateTable.csv`, pulled from each state's own filing folder
using this project's standing edition-selection ledger (`State_ERC_CW_Editions.csv` — the
in-force `ERC Edition`/`SnapshotBatch` per state, not just whatever happens to be in the
`20260601` snapshot batch). **Not** the Countrywide (`CW`) copy — see "CW table is stale" below.

**Output file:** `SubStdConditionRate.csv` (columns: `StateCode`, `SubStandardCondition`,
`ConstructionCode`, `Rate`) — **1,140 rows** across **38 states** (30 rows each: 5 conditions ×
6 construction codes). **Puerto Rico is excluded on standing direction** — see
`project_pr_out_of_scope` memory: PR is never included in this project's outputs, not even for
completeness, regardless of whether usable PR data exists in the source corpus.

## What "SubStandardCondition" A–E actually mean

**Resolved — see `SubStdConditionCode_Label.csv` / `README_SubStdConditionCode_Dropdown.md`.**
The DataDef itself only defines `SubStdConditionA`…`E` as plain 3-character Yes/No flags
(`DataDefs\MasterCFCW.DataDef.xsd`) with no description, but `Form Fields\Fields.FormField.csv`
(a UI form-field table, not metadata or a rate table — easy to miss) carries a label and
description for each: A = Heating and Cooking, B = Wiring, C = Conversion, D = Physical Condition
and Housekeeping, E = Exposure. That also explains the two-tier rate split below — A/C/D share one
tier, B/E share the other, and now that the labels are known that grouping is legible rather than
arbitrary.

## Row filtering

None needed beyond selecting the in-force edition per state — the source table's key
(`StateCode, SubStandardCondition, ConstructionCode`) already matches the output 1:1, with one
column (`Rate`) and no extraneous rows to drop (unlike `BasicGroupIRate.RateTable.csv`, this
table has no `CovType`/`Group` columns to filter).

## Edition selected per state

Used the project's existing canonical ledger, `State_ERC_CW_Editions.csv` — **not** a fresh
`20260601`-only scan. That ledger already resolved, per state, the in-force `ERC Edition` (latest
effective date not past the 9/1/2026 cutoff, highest version at that date) and which of the eight
snapshot batches (`20191201`, `20201201`, `20221001`, `20230801v1`–`v4`, `20260601`) it lives in.
Re-deriving that selection here would have risked disagreeing with every other table in this
project — see `README_BGI_BuildingRates.md` for why the naive single-batch scan is wrong.

## States NOT included, and why — three distinct buckets

1. **No file in any edition — the state never adopted this charge.**
   **`CA`, `FL`, `UT`.** Confirmed both via the current ledger's in-force edition *and* by
   checking every historical batch back to 2019 for FL/UT (CA's absence matches its known
   District I/II split pattern from `BasicGroupIRate` — worth checking if CA also splits
   sub-standard conditions by district before assuming it simply has none; not yet investigated).
2. **File exists but is empty (header row, 0 data rows) — deliberate exclusion.**
   **`DC`, `IL`, `KY`, `NJ`, `NY`.** This is not the same as "no file" — the state structurally
   adopted the field and then explicitly zeroed it out. Read as "this state does not charge for
   sub-standard conditions," not as "fall back to CW."
3. **Everything else has real, non-CW, state-keyed data** — see next section.

That's 38 usable states out of the 47 in the ledger (3 no-file + 5 empty + PR excluded on
standing direction, not investigated = 9 excluded).

## CW table is stale — do not use it

The Countrywide (`CW`) copy of this table (`CFCW20260601V01\Rate Tables\`) still shows
**0.321 / 0.16 / 0.076 / 0.04** (by construction tier), values that have been byte-identical
across every CW edition on file since `CF CW 20191201 V01`. Individual states began filing their
own, lower override starting with CW base cycle `20230801v2` (first seen: `CF AL 20250201 V01`).
**Every one of the 38 states in the output file now uses this newer rate, not the CW rate** — the
lookup rule (`LookupSubStdConditionRate`) only falls back to `CW` when a state has no row of its
own, and none of the 38 do. If you see `0.321`-family values anywhere downstream, that's the
stale CW fallback leaking in, not real state data.

## Rate pattern — all 38 states share one schedule

| Construction | A / C / D | B / E |
|---|---|---|
| 1–3 | 0.313 | 0.156 |
| 4 | 0.156 | 0.074 |
| 5–6 | 0.074 | 0.039 |

Confirmed by normalizing every state's 30 rows (dropping the `StateCode` column) and diffing: all
38 jurisdictions share the identical pattern. (Puerto Rico's own schedule was found to be lower
across the board, but PR is excluded from this project's outputs on standing direction — see
above — so it's omitted here rather than documented as a variant.)

## Open questions

- Whether CA's absence is a true "no charge" or another District I/II split table, per the
  `BasicGroupIRate` precedent — not yet checked.
- Whether the `LC_Rule 85` citation is simply stale/mis-numbered or points at a manual edition not
  in this corpus — see `SubStdConditionRate_REFERENCE.md` in the ERC files project for the fuller
  investigation writeup (`C:\Projects\ISO_ERC_Files\CF\20260601\CFCW20260601V01\`).
