# VacantBuildingRate / VacantBldgPreviousOrIntendedOccup — Data Source and Structure

**Purpose:** Vacant building surcharge rate — the `Rate` value looked up by `StateCode` +
`ClassCode` that feeds `VacantBuildingRate` in the Structure premium chain when
`VacantBuilding = "Yes"`. Unlike `SubStdConditionRate`, this is **not** a straight table lookup —
`VacantBuildingRate` = `VacantBldgPreviousOrIntendedOccup` (this table's `Rate`) **×**
`LossCostMultiplier` (`rul:Product`, `CommercialPropertyStructureRules.Rule.xml`, rule
`SetVacantBuildingRate`, line 5713). The lookup itself is rule `LookupVacantBldgPreviousOrIntendedOccup`
(line 25517), keyed on the *previous or intended occupancy's* `ClassCode`, not the building's own
occupancy — see "What the key actually represents" below.

Metadata ties this to `BureauRuleNumber85G5` (`VacantBldgPreviousOrIntendedOccupDef.RateTableDef.xml`).
**Same caveat as `SubStdConditionRate`: not independently verified against a manual.** The one CF
manual on hand (`CF-MU-2022-LC-001-C.pdf`) has no "vacant"/"Vacant" text anywhere in its extracted
content, so this citation (Rule 85, subsection G.5) is plausible — Rule 85 in that manual genuinely
is "Basic Group I Class Rates," and G.5 could be an unreprinted subsection of it in the Loss Cost
notice — but unconfirmed. Don't treat it as verified without the full Rules-text manual (see
`Agentic\cf-circular-expert\AGENT.md`'s open question about whether that manual exists in this
corpus at all).

**Source table:** `VacantBldgPreviousOrIntendedOccup.RateTable.csv`, pulled from each state's own
filing folder using the project's standing edition-selection ledger (`State_ERC_CW_Editions.csv`).
**Not** the Countrywide (`CW`) copy — confirmed **header-only (0 rows) in every CW edition checked**,
`CF CW 20191201 V01` through `CFCW20260601V01` — same "state rates are the only usable source"
pattern as `BasicGroupIRate`. Unlike `SubStdConditionRate`, this isn't a stale-CW-value trap (CW was
never populated at all, not populated-then-abandoned), so there's no risk of silently picking up a
wrong CW number — a missing state simply means no lookup source exists, full stop.

**Output file:** `VacantBldgPreviousOrIntendedOccup.csv` (columns: `StateCode`, `ClassCode`, `Rate`)
— **4,849 rows** across **46 jurisdictions (45 states + DC)**. **Puerto Rico is excluded on
standing direction** — see `project_pr_out_of_scope` memory: PR is never included in this
project's outputs, not even for completeness, regardless of whether usable PR data exists in the
source corpus. (PR did have real data here — 85 rows, lower rate than the mainland — but it's
omitted per that standing rule, not because the data was unusable.)

## Coverage — a genuinely different shape from SubStdConditionRate

**No exclusion buckets this time.** Every non-PR state in `State_ERC_CW_Editions.csv` has a
non-empty table — no `NO-FILE` states (unlike `CA`/`FL`/`UT` for sub-standard conditions), no
`EMPTY` states (unlike `DC`/`IL`/`KY`/`NJ`/`NY`). This charge is universally adopted across the
whole corpus, at least in this ERC snapshot.

## Rate pattern

Only **two distinct rate values appear in the included dataset**: `0` and `0.015`.

- **`0.015`** — the flat rate for eligible class codes, in every included jurisdiction.
- **`0`** — a genuine per-class-code exclusion (that occupancy class doesn't get a vacancy charge
  at all), not a missing-data placeholder.

(Puerto Rico's own rate, `0.011`, was confirmed lower than the mainland's — same pattern as
`SubStdConditionRate`'s PR row — but PR is excluded from this project's outputs on standing
direction, so it's omitted here rather than documented as a variant.)

**The set of `0`-rated class codes is identical across 41 of the 46 included jurisdictions**
(verified by diffing each state's zero-rate class-code list against Alabama's). The four
exceptions — **`FL`, `GA`, `KS`, `NY`** — differ only because they file fewer class codes in total
(99–101 rows vs. the standard 106), not because their exclusion logic differs; the same
missing-class-code footprint already documented for `BasicGroupIRate` in
`README_BGI_BuildingRates.md` (FL/GA/KS/NY missing `0535, 0574, 0575, 0585, 2205`).

## What the key actually represents — read the rule carefully

The lookup's `ClassCode` key is **`ClassCodeToUse`, the vacant building's *previous or intended*
occupancy class** — not necessarily its current/nominal occupancy. `SetVacantBldgPreviousOrIntendedOccup`
(line 5685) only runs the lookup when `VacantBuilding = "Yes"` **and** `ClassCodeToUse` is populated;
otherwise the rate is forced to `0.0`. Confirm what feeds `ClassCodeToUse` in this context before
wiring a dropdown to it — it may need its own "previous/intended occupancy" input distinct from
whatever selects the building's normal `ClassCode` elsewhere in the workbook.

## ClassCode labels — reuse the existing dropdown, with one gap flagged

`ClassCode` here is the same class-code space as `BuildingClassCode_Description.csv` (already in
this folder) — no new label table was built. One gap found while cross-checking: Alabama's vacant
table includes class code **`1180`**, which does **not** appear in
`BuildingClassCode_Description.csv` at all. Not investigated further — flagged as an open question
below rather than guessed at.

## Open questions

- Whether `BureauRuleNumber85G5` is a real, correctly-numbered citation — see caveat above.
- What class code `1180` is (present in the vacant-rate table, absent from the Building Class Code
  dropdown) — check if it's a valid code missing from that dropdown's source pull, or a data
  anomaly in this one state's filing.
- What actually populates `ClassCodeToUse` when `VacantBuilding = "Yes"` — needed before this table
  can be wired into a working dropdown/derivation in the rater.
