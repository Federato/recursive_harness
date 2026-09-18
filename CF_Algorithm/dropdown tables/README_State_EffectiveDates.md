# State Effective Dates — for lining up ISO RaaS test calls with this data

**Purpose:** Every filed edition (effective date + version) found for every state, across every CF
snapshot batch in `C:\Projects\ISO_ERC_Files\CF\`, so ISO RaaS test calls can be pointed at the same
edition this project's rate data was pulled from — RaaS will return different rates/rules depending
on the effective date passed in.

**Output file:** `State_EffectiveDates.csv` (columns: `StateCode`, `EffectiveDate`, `Version`,
`SnapshotBatch`, `EditionFolder`, `InForceAsOf_2026-09-01`, `IsCurrentEdition`,
`UsedInBGI_BuildingRates`) — **430 rows across 47 states** (every state+PR with at least one CF
filing found anywhere in the corpus).

**Corrected, 2026-09-03: this now scans all eight snapshot batches, not just `20260601`.** The first
pass only looked in `C:\Projects\ISO_ERC_Files\CF\20260601\`, which is one filing batch, not a
complete cross-state snapshot — batches accumulate per state independently
(`20191201`, `20201201`, `20221001`, `20230801v1`–`v4`, `20260601`). Rescanning all eight found
in-force editions for four states wrongly believed to have none (CA, MA, MO, NC — their true current
editions live in older batches, not `20260601`), and found five states with no presence in `20260601`
at all but a real filing elsewhere (FL, IL, NJ, RI, VT). See `README_BGI_BuildingRates.md` for the
full correction table.

**Cutoff date: `9/1/2026`**, per direction — "current edition" means the latest effective date that
is not past 9/1/2026.

## Columns

- **`SnapshotBatch`** — which of the eight batch folders this row's edition lives in. Needed because,
  unlike `EditionFolder`, the batch is not derivable from the state/date alone — the same state can
  have editions spread across several batches.
- **`EffectiveDate` / `Version`** — parsed directly from the folder name (`CF <State> <YYYYMMDD>
  V<NN>`).
- **`InForceAsOf_2026-09-01`** — `Yes` if that specific row's effective date is on or before the
  cutoff, `No - future` otherwise. A state can have several `Yes` rows (superseded past editions) and
  several `No - future` rows (upcoming filings) at once.
- **`IsCurrentEdition`** — `Yes` marks the single row selected as "the" edition for that state (latest
  effective date not past the cutoff; if no such date exists, the earliest future one). Exactly one
  `Yes` per state.
- **`UsedInBGI_BuildingRates`** — `Yes` marks the `IsCurrentEdition` row for the 44 states that are
  actually pulled into `BGI_BuildingRates.csv`. Blank for `CA`/`AK` (District-split, not pulled into
  that file) and `PR` (not investigated).

## States genuinely absent from this file entirely

**`HI`, `ID`, `LA`, `MS`, `WA`** have zero rows here — no CF filing found in any of the eight batches
for any of these five. See `README_BGI_BuildingRates.md` for detail; four of the five were already
known "pending access" states from the circulars-tracking side of this project.

## What this does NOT tell you

- `AK` and `CA` need a `District I`/`District II` input to test Basic Group I building rates at all
  (see `README_BGI_BuildingRates.md` and `BasicGroupI_ERC_Tables.md`) — this file only tells you which
  *edition/date* to hit, not that extra input requirement.
- The Countrywide (`CW`) edition used alongside these state editions (`CFCW20260601V01`, see
  `State_ERC_CW_Editions.csv`) was picked independently, not matched to each state's own batch — see
  the caveat at the end of `README_BGI_BuildingRates.md`.
