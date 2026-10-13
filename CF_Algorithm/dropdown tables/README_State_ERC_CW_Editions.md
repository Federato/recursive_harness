# State ERC Edition / CW Edition — the edition ledger for this project

**Purpose:** A single-glance ledger of exactly which ERC edition (state-specific folder) and which
Countrywide (CW) edition every table in this project's `dropdown tables\` was built from, so future
work — or a fresh session — doesn't have to re-derive it from each individual README.

**Output file:** `State_ERC_CW_Editions.csv` (columns: `State`, `ERC Edition`, `SnapshotBatch`,
`CW Edition`) — **47 rows**, one per state (+PR) with at least one CF filing found anywhere in
`C:\Projects\ISO_ERC_Files\CF\`.

## How the ERC Edition column was chosen

**Corrected, 2026-09-03: searches all eight snapshot batches**, not just `20260601`. Same selection
rule as `BGI_BuildingRates.csv` / `State_EffectiveDates.csv`: for each state, the edition **not past
the 9/1/2026 cutoff** with the latest effective date (highest version if that date has more than one)
— searched across `20191201`, `20201201`, `20221001`, `20230801v1`–`v4`, and `20260601`, since a
state's current edition can live in any of them (batches accumulate per state independently, not by a
shared vintage date). The `SnapshotBatch` column records which batch each state's chosen edition
actually came from — for 42 states it's `20260601`, but `CA`, `MA`, `MO`, `NC`, `FL`, `IL`, `NJ`,
`RI`, and `VT` are all pulled from an earlier batch. See `README_BGI_BuildingRates.md` for the full
correction writeup and `README_State_EffectiveDates.md` for the complete per-state effective-date
picture.

## CW Edition

**`CFCW20260601V01`** for every row. This is the only Commercial Property Countrywide edition that
exists inside the `20260601` snapshot directory (`C:\Projects\ISO_ERC_Files\CF\20260601\` has exactly
one `CFCW*` folder) — there was no selection to make here, unlike the per-state column. Note this is
the Commercial Property (CF) countrywide edition specifically; it has no relationship to General
Liability's countrywide editions (`C:\Projects\ISO_ERC_Files\General_Liability\countrywide\`), which
is a different product line entirely and was confirmed out of scope for this ledger.

## Scope note

`C:\Projects\ISO_ERC_Files\CF\` also contains older snapshot directories
(`20191201`, `20201201`, `20221001`, `20230801v1`–`v4`) alongside `20260601`. Every table in this
project, including this ledger, is built exclusively from `20260601` — the older snapshots were not
consulted and this file says nothing about them.
