# BGI (Basic Group I) Building Rates — Data Source and Structure

**Purpose:** Class-rated Basic Group I building base rates — the `Rate` value looked up by
`ClassCode` + `ConstructionCode` (+ state) that `BasicGroupIRate` feeds into the Building premium
chain (see `BasicGroupI_ERC_Tables.md`).

**Source table:** `BasicGroupIRate.RateTable.csv` (Bureau Rule 85), pulled from each state's own
filing folder — **not** the Countrywide (`CW`) copy, which is confirmed header-only (0 data rows),
per the standing correction already logged in `BasicGroupI_ERC_Tables.md`. State rates are the only
usable source for this table.

**Output file:** `BGI_BuildingRates.csv` (columns: `StateCode`, `ClassCode`, `ConstructionCode`,
`Rate`) — **27,336 rows** across **44 states**.

## Row filtering

The source table's raw key is `StateCode, ClassCode, ConstructionCode, Group, CovType`. Two
simplifications were applied:

1. **`CovType = "Building"` only** — the source table also carries `PersProp` (Personal Property)
   rows under the same keys; those were dropped since this pull is Building-only.
2. **`Group` column dropped** — confirmed `Group = "Not Applicable"` for every `Building` row in
   every state checked. `Group` (values `A`/`B`/`C`/`YARD`) only varies on `PersProp` rows (e.g.
   commodity-hazard groups for classes `0321`/`0322`, yard-storage classes `1400`/`1650`/`1700`), so
   it carries no information for the Building rate and was safe to drop.

## Edition selected per state — corrected to search ALL snapshot batches

**Correction, 2026-09-03.** The first two passes at this file only looked inside
`C:\Projects\ISO_ERC_Files\CF\20260601\`. That directory is **one filing batch, not a complete
snapshot of every state as of that date** — `C:\Projects\ISO_ERC_Files\CF\` has seven other batch
folders (`20191201`, `20201201`, `20221001`, `20230801v1`–`v4`), and a state's most current edition
can live in any of them; batches accumulate independently per state, not by a shared vintage date.
Re-scanning all eight batches for every state, with the same rule as before — latest effective date
not past the directed cutoff of **9/1/2026**, highest version if that date has multiple versions —
changed the answer for four states and added five states that weren't found at all in the
`20260601`-only pass:

| State | Old (20260601-only) result | Corrected result | Which batch |
|---|---|---|---|
| **CA** | thought to have no in-force edition | `CF CA 20251201 V01` **is in force** | `20230801v3` |
| **MA** | thought to have no in-force edition | `CF MA 20260301 V02` **is in force** | `20230801v4` |
| **MO** | thought to have no in-force edition | `CF MO 20251101 V01` **is in force** | `20230801v2` |
| **NC** | thought to have no in-force edition | `CF NC 20251101 V01` **is in force** | `20230801v3` |
| **FL** | not found at all | `CF FL 20241201 V01` | `20230801v1` |
| **IL** | not found at all | `CF IL 20260701 V02` | `20230801v4` |
| **NJ** | not found at all | `CF NJ 20251001 V02` | `20230801v4` |
| **RI** | not found at all | `CF RI 20260401 V02` | `20230801v4` |
| **VT** | not found at all | `CF VT 20260201 V02` | `20230801v4` |

CA's correction doesn't change its exclusion from this CSV — see below, it's still the District I/II
state — but it does mean the earlier claim "CA has no in-force edition at all" was wrong; it has one,
just not a usable single-table `BasicGroupIRate`.

**Full per-state edition + batch list is in `State_ERC_CW_Editions.csv` and
`State_EffectiveDates.csv`** (the latter also lists every historical edition, not just the current
one, across all eight batches).

## States NOT included

**`AK`, `CA`, `PR`** — no `BasicGroupIRate.RateTable.csv` file exists in any batch/edition for these
three (all eight batches checked, not just `20260601`).

- **`CA` and `AK` are confirmed to be the same root cause**: both split Basic Group I building rating
  into two parallel tables, `BasicGroupIDistrictIRate` and `BasicGroupIDistrictIIRate` (identical key
  shape to every other state's single `BasicGroupIRate`: `ClassCode, ConstructionCode, Group,
  CovType`), selected by a `District` concept — confirmed present in CA's in-force edition
  (`CF CA 20251201 V01`, not just its future `20261001`/`20261101` editions). The two states get to
  "District I / II" differently though — **CA** has the agent pick `District` directly as a Location
  field (`DomainDistrict`); **AK** derives it from City (`DomainDistrictAlaska.DomainTable.csv`), with
  a further Yes/No branch for City = "Remainder of State" keyed off
  `BasicGroupIRatingTerr`/`CountyAK`. See the watch-item note in `BasicGroupI_ERC_Tables.md` and the
  delta note on the Building·BGI view in `cf-rating-chains.html` for the full detail. Neither state's
  district tables are pulled into this CSV yet — they need their own two-table extraction, not a fit
  into this file's single-table-per-state shape.
- **`PR`** — not yet investigated. Could be a third variant of the same District pattern, a
  different rating mechanism entirely, or genuinely absent from this ERC snapshot. Flagged as an open
  question, not assumed to match CA/AK.

## States with NO edition anywhere in this ERC corpus

**`HI`, `ID`, `LA`, `MS`, `WA`** — checked all eight batch folders directly; no `CF <state> ...`
folder exists for any of these five under any batch. This isn't a rate-table gap like CA/AK, it's a
total absence of any CF filing for these states in this ERC corpus. Four of the five (`ID`, `LA`,
`MS`, `WA`) match states already flagged as "pending access" on the circulars side in `BUILD-LOG.md`
— consistent with the same underlying access gap. `HI` is a new gap not previously logged anywhere in
this project.

**Disregarding `PR` per direction received**, this means **46 of the 51 U.S. state+DC jurisdictions**
have at least one CF edition in this corpus; of those, **44 have a usable single-table
`BasicGroupIRate`** (everything except CA/AK, which need the District two-table treatment).

## Row-count variance across states

Most states carry all **104** Class-eligible ClassCodes × 6 ConstructionCodes = 624 Building rows.
Four states file fewer:

| State | ClassCodes filed | Missing vs. the 104-code set |
|---|---|---|
| FL | 99 | `0535, 0574, 0575, 0585, 2205` |
| GA | 99 | `0535, 0574, 0575, 0585, 2205` |
| KS | 99 | `0535, 0574, 0575, 0585, 2205` |
| NY | 99 | `0535, 0574, 0575, 0585, 2205` |

Same 5 codes missing in all four states — read as those occupancies not being filed for Class rating
in FL/GA/KS/NY in this edition, not a data-pull error (each file's row count was checked directly,
not inferred).

## Open caveat: state edition and CW edition are picked independently

The `CW Edition` recorded in `State_ERC_CW_Editions.csv` (`CFCW20260601V01`) is simply the most
current *Commercial Property countrywide* edition on file — it was not re-derived to match whatever
batch each state's own edition happened to come from. In real ISO RaaS terms, a given state's filing
and the countrywide baseline it layers onto are normally published as a matched pair for a given
effective date; here, e.g., VT's current edition comes from batch `20230801v4` while the CW edition
used is from batch `20260601`. Since every table actually consumed by this rater is state-filed data
(the CW `BasicGroupIRate` is confirmed empty regardless of batch), this hasn't caused a data problem
yet — but it's worth knowing if RaaS testing surfaces a mismatch between what this project expects and
what RaaS returns for a given state+date combination.
