# Territory — inventory and dropdown plan

**Scope:** every place "territory" drives a CF rate — Basic Group I (Building & Contents), Basic Group II, and Special Class Personal Property. Special Class Building has **no** territory dependency at all (`Excel_Rater_Special.md`).

**Method:** for each of the 47 filed states (`Supporting Tables/State_ERC_CW_Editions.csv`), read that state's package `Form Related Fields` table and find what each territory-input column is derived from (`RelatedField`). Where no such row exists, checked the corresponding rate table's row count to tell "single/fixed territory" apart from "something else going on." Scan script: nothing committed yet — ran ad hoc, results below.

---

## The headline finding

CF territory is **not** GL's mechanism. GL resolves 27 states from a raw ZIP code and needs a dropdown only for 4 (CA/FL/NY/TX). CF is the opposite shape: **ZIP lookup is the minority case**, and it only ever shows up on Basic Group II.

| Mechanism | Field | Applies to | Resolved from |
|---|---|---|---|
| BGI territory factor | `Territory` → `RatingTerritoryGroupIFactor` | Building **and** Contents (same field, per `Excel_Rater_BasicGroupI.md:83` — Contents reuses it, not a separate table) | **City**, 28 states / **single fixed value**, 19 states |
| BGII territory | `BasicGroupIIRatingTerr` (a lookup key *into* the base-rate table itself, not a multiplier) | Basic Group II only | **ZIP**, 11 states / **County**, 11 states / **direct-select dropdown, un-derived**, 25 states |
| Special PP territory | `PP_SpecialRatingTerr` → `PrsnlPropTerrMultiplier` | Special Class Personal Property only (Special Building: none) | **County**, 28 states / **single fixed value**, 19 states |
| District (CA/AK only) | `District` (CA, user-picked) / `BasicGroupIDistrictTerritory` (AK, City-derived) | Gates which of two `BasicGroupIRate` tables to use — not itself a territory multiplier | already documented in `BasicGroupI_ERC_Tables.md` |

Three coverage parts, three different resolution bases, no shared dropdown mechanism between them. A state can be City-driven on BGI and ZIP-driven on BGII in the same package (e.g. MA, NY).

---

## State-by-state, per mechanism

### BGI territory factor (Building & Contents) — 47 states

The "City dropdown, 28 states" line from the first pass was too coarse. Pulling actual row counts split it in two:

| Mode | States | Detail |
|---|---|---|
| **City-only dropdown** (21) | AL AZ CA CO IL IN MA MI MN MO NC NE NH NJ NM OH OK OR TN TX WI | One `Form Related Fields` row (`RelatedField = City`). Domain table is `StateCode, City, DisplayValue, DataValue` — every row a distinct, named place. Row counts are small (2–60 rows; CA is the outlier at 43). Picking the City resolves the territory directly. |
| **City + County dropdown** (7) | FL GA KY MD NY PA VA | **Two** `Form Related Fields` rows for the same field — one `RelatedField = City`, one `RelatedField = County`. The domain table is `StateCode, City[/CityTown], County, DisplayValue, DataValue` and is a full cross-join: every named city × every county in the state, so most rows read `"Balance of State"` / `"Remainder of State"`. Row counts are large (134–1,302) because of that cross-join — the county alone is what actually varies the answer once you're outside a named city. |
| **Single fixed value** (19) | AK AR CT DC DE IA KS ME MT ND NV PR RI SC SD UT VT WV WY | `RatingTerritoryGroupIFactor.RateTable.csv` has exactly one data row, and in **every one of the 19**, `Factor = 1` — the territory factor is a no-op in these states, not just single-valued. Confirmed by row count, not assumed (BUILD-LOG.md Entry 3's standing lesson). |

For the 7 City+County states, the underwriter-facing shape is really: *"is the risk in one of these N named cities? If not, which county?"* — not a flat pick-from-1,302-rows dropdown. GA has only 8 named cities (7 real + "Remainder of State"); KY has 4; NY has ~20; the county list underneath is what's large. This needs to be designed as two chained inputs, not one.

---

## BGI territory selection — execution plan

Scope: just the BGI territory factor (Building & Contents share it). BGII, Special, and District are out of scope for this pass.

### 1. Three-tier data model, not one dropdown mechanism

| Tier | States | Underwriter sees | Resolves via |
|---|---|---|---|
| **Fixed** | 19 | nothing — territory is invisible, no field shown | constant `1` — no lookup needed at all, since every fixed state's filed factor is `1` |
| **City-only** | 21 | one dropdown, state's named-place list (2–60 options) | `VLOOKUP(State\|City, bgi_city_terr, ...)` — same `INDIRECT` + named-range pattern GL already built for CA/FL/NY/TX |
| **City + County** | 7 (FL GA KY MD NY PA VA) | two dropdowns: named-place list (4–43 options, always including a "Remainder/Balance of State" choice), then a full county list | `VLOOKUP(State\|City\|County, bgi_citycounty_terr, ...)` — the filed table is a complete City×County cross-join, so **every** combination has a row; no fallback branch needed once both inputs are chosen |

The Fixed tier needs no sheet at all — worth building the resolved-territory formula so Fixed states skip the lookup entirely rather than hitting a table and getting `1` back every time.

### 2. Sheet design (mirrors GL's `Background` / `Classifications` / `namedterr` split)

- **`Background`** gains a `BGI Territory mode` column (`Fixed` / `City` / `City+County`) per state — same role as GL's `Territory mode` column.
- **`bgi_city_terr`** — one sheet, `Key = State|City`, for the 21 City-only states. Same shape as GL's `namedterr`; same `INDIRECT` + per-state named range (`AL_bgiterr`, `CA_bgiterr`, …) for the dropdown source.
- **`bgi_citycounty_terr`** — one sheet, `Key = State|City|County`, for the 7 composite states. Two named-range families per state: one for the City list (small), one for the County list (the standard county list for that state).
- Resolved-territory cell (per classification column, same position as GL's territory cell) cascades on `BGI Territory mode`: `Fixed → 1`; `City → VLOOKUP(bgi_city_terr)`; `City+County → VLOOKUP(bgi_citycounty_terr)`.
- **One cell serves both Building and Contents** — confirmed in `Excel_Rater_BasicGroupI.md:83`, no separate Contents lookup to design.

### 3. Reuse opportunity worth flagging now

The **County list** the 7 composite states need is very likely the same full county-per-state list Special Class Personal Property's territory (County dropdown, 28 states) and 11 of BGII's states will also need. Worth pulling **one master `State|County` list** and pointing all three mechanisms at it, rather than three separate county pulls — cuts real duplicated work later. Not building it now, just flagging the dependency order: pull once, reference three times.

### 4. Open questions to settle before pulling data (still planning, not building)

1. **Is the second field (County) always shown for the 7 composite states, or only when City = "Remainder/Balance of State"?** GA's data shows the City choice mostly doesn't discriminate on its own — checked GA specifically: only `Atlanta` resolves to its own value regardless of county; every other named city (Albany, Augusta, Columbus, Decatur, Macon, Savannah) resolves purely off County, identically to "Remainder of State." That suggests a progressive-disclosure UI (ask County only when needed) would match the real data better than always showing two dropdowns — but this needs a rule-XML check (`CommercialPropertyStructureRules.Rule.xml`), not an inference from one state's table, before deciding the UI pattern for all 7.
2. **Do the other 6 composite states behave like GA** (one or two "real" named cities, rest driven by county) **or does city genuinely discriminate independently of county somewhere** (e.g. NY: is "New York City" a real override regardless of county, or itself county-dependent)? Needs a per-state check, not an assumption from GA.
3. **CA and AK also carry the separate `District` field** (which `BasicGroupIRate` table to use) alongside their BGI territory factor — these are two unrelated dropdowns on the same state. The plan above only covers the territory *factor*; District is already scoped in `BasicGroupI_ERC_Tables.md` and shouldn't be merged into this mechanism's design.
4. **PR** is confirmed Fixed/factor=1 for BGI territory specifically (separate from the earlier-flagged Special PP gap, which is a different table).

### 5. Suggested build order, once there's a go-ahead

1. Answer open question 1–2 above (rule-XML check on 2–3 of the 7 composite states) — changes whether the UI is "two dropdowns always" or "City, then conditionally County."
2. Pull `bgi_city_terr` (21 states, small, no ambiguity).
3. Pull the master `State|County` list once (feeds this, Special, and BGII later).
4. Pull `bgi_citycounty_terr` (7 states) once the UI pattern from step 1 is settled.
5. Build the `Background` mode column + resolved-territory cascade.

**Done, 2026-09-04 — superseded by a redesign the same day, see below.** First pass executed steps 1–2 and 4–5 as planned: confirmed City+County is unconditionally required in all 7 composite states (no `Condition`/`RequiredCondition` filed), pulled `BGI City Only` (267 rows, 21 states) and `BGI City+County` (5,075 rows, 7 states), and built a walkthrough workbook resolving Building/Contents territory through that City/County chain.

**Redesign: dropdowns now source directly from the filed factor list, not the City/County chain.** Per direction — "the dropdowns should be based on the BGI Territory Factor" — every state's Territory dropdown now pulls straight from `RatingTerritoryGroupIFactor` (pulled in full: 123 rows, all 47 states, not the GA/CA sample from the first pass). One mechanism for all 47 states: pick a territory name off that state's filed list (1–14 options), look up the factor. No City or County input at all. This sidesteps two data-quality issues the resolution-table approach would have inherited: **Virginia is not a City×County cross-join** like GA/KY/MD/PA are — VA's 40 independent cities each pair only with their own name as County, so picking City and County independently can land on an unfiled combination (this surfaced as a real bug in the first pass's example-row generator, since fixed by picking an actually-filed pair). **New York double-files City='Albany'** specifically (against all 62 counties, once to "Albany" and once to "Remainder of State") — checked precisely and it's an Albany-only quirk, not systemic. The City/County tables are kept in the workbook as reference-only sheets (not wired to any formula) since they're still useful for an underwriter who knows the client's city but not the ISO territory name.

**Second finding, same day — the territory factor isn't the whole story.** NY files loss costs (not just a factor) separately for NYC vs. Remainder of State — a genuinely different mechanism from the territory multiplier. Checked all 47 states for this specifically (not inferred from NY alone): **exactly 3 states file two `BasicGroupIRate`-family base-rate tables — AK, CA, NY.** DC has two extra tables that looked like a fourth case but are empty and unreferenced by any rule (confirmed by row count and a rule-file text search) — a dead filing artifact, not a real split, same "table exists ≠ usable" lesson as BUILD-LOG.md Entry 3. Verified each of the 3 against its rule XML: CA is a plain 2-option user-picked dropdown (no derivation); AK is a City dropdown (9 named boroughs + "Remainder of State", the latter needing an unlabeled Yes/No the filing doesn't explain); NY is resolved internally from County alone (5 NYC boroughs → `BasicGroupIRateNYC`, else → `BasicGroupIRate`) via a *different* table (`RatingTerrGroupICode`) than the one behind the territory-factor dropdown — checked specifically whether NY's already-built Territory selection could stand in for this and it can't reliably (the filed table lets "New York City" as a City choice pair with any of NY's 62 counties, not just the 5 real boroughs).

**Simplified per direction — "keep this simple... doesn't need to be super compliant."** Added a `BGI Base Rate Table` mechanism, scoped to just AK/CA/NY (the other 44 states need nothing). CA and AK get direct-select dropdowns (2 and 11 options). NY is simplified to a formula off the already-selected Territory — `Territory = "New York City"` → `BasicGroupIRateNYC`, else → `BasicGroupIRate` — accepting the known inaccuracy documented above (a real County input would be needed for full accuracy) as an acceptable tradeoff for a surface-level tool.

- **Deliverable:** `Spreadsheet_Rater/CF/Supporting Tables/BGI_Territory_Lookups.xlsx` — walkthrough only, not wired into the production `.xlsb`. Sheets: `Walkthrough` (pick-any-state interactive demo, both mechanisms together), `Read Me`, `Background` (47-state reference — no longer drives anything), `BGI Territory Factor` (full 123-row pull, all 47 states, the live dropdown source), `BGI Base Rate Table` (AK/CA options, 13 rows), `BGI City Only (reference)` / `BGI City+County (reference)` (267 / 5,075 rows, not wired to any formula), `All 47 States` (every state's Territory dropdown resolved live).
- **Not done:** wiring any of this into the real `.xlsb`; a compliant (County-based) NY base-rate check; generalizing anything for Special PP/BGII reuse.

---

### BGII territory — 47 states

| Mode | States |
|---|---|
| **ZIP lookup** (11) | CT DE MA MD ME NC NH NJ NY RI VA |
| **County dropdown** (11) | AL CO FL GA IL MT NE NM SC TX WY |
| **Direct-select dropdown** (25) | AZ CA IN KY MI MN MO OH OK OR PA TN WI AK AR DC IA KS ND NV PR SD UT VT WV |

"Direct-select" means the field is a plain `SELECT` bound to its own `DomainBasicGroupIIRatingTerr<ST>` list — not derived from City/County/ZIP at all, the underwriter just picks the territory code/name straight off the list. Checked AZ as a sample: that domain table has exactly one entry (`"Entire State"`), so several of these 25 are trivial one-option dropdowns, not real geography. **Not yet checked individually** which of the 25 are trivial vs. genuinely multi-option — that's list-pulling work, not a new discovery pass.

### Special Class Personal Property territory — 47 states

| Mode | States |
|---|---|
| **County dropdown** (28) | AL AZ CA CO CT FL GA IL IN KS KY MA MD MI MN MO NE NJ NY OH OK OR PA RI TN TX VA WI |
| **Single fixed value** (19) | AK AR DC DE IA ME MT NC ND NH NM NV PR SC SD UT VT WV WY |

PR shows no `PrsnlPropTerrMultiplier.RateTable.csv` at all — Special PP may not be filed in PR; flag for the same "table exists vs. table has a row" check before assuming single-fixed.

---

## What this means for dropdown design

GL's design (`Territory and Terrorism Wireframes.html`) already solved the *shape* of this problem — one resolved-territory cell, several input paths feeding it, `INDIRECT` + per-state named ranges for the dropdown source. That pattern carries over directly, just with three more input bases than GL needed:

| Input basis | GL precedent | CF needs |
|---|---|---|
| Fixed constant | 20 states, `Background` sheet column | BGI: 19 states. Special: 19 states. Same mechanism, different row counts. |
| ZIP lookup | 27 states, existing `premopsterr` sheet | BGII only, 11 states |
| Named dropdown, `INDIRECT` + per-state range | 4 states (`namedterr` sheet, already built) | BGI: 28 **City**-keyed states. BGII: 11 **County**-keyed + up to 25 **direct-select** states. Special: 28 **County**-keyed states. |

The mechanical difference from GL: CF's dropdown-driven states outnumber its ZIP states by roughly 3:1, so the `INDIRECT` + named-range approach becomes the *primary* path, not the exception carved out for four states. Worth deciding up front whether to keep one `namedterr`-style sheet per mechanism (`bgi_terr`, `bgii_terr`, `special_terr`) or one combined sheet keyed on `State|Mechanism|Name` — three sheets is probably cleaner given they key on different geography (City vs. County) and don't share rows.

CA and AK's `District` field is a fourth, separate input (gates which `BasicGroupIRate` table to read, not a multiplier) — CA needs a plain 2-option dropdown, AK derives it from City. Already scoped in `BasicGroupI_ERC_Tables.md`; not re-covered here.

---

## Remaining steps

1. **Pull the actual dropdown source data** — for every City-dropdown (BGI, 28 states), County-dropdown (BGII 11 + Special 28), and direct-select (BGII 25) state, export `DomainBasicGroupIRatingTerritory<ST>` / `DomainSpecialRatingTerr<ST>` / `DomainBasicGroupIIRatingTerr<ST>` into consolidated lookup CSVs — the same shape as GL's `Territory Lookups - CA FL NY TX.xlsx`, just three tables instead of one and ~65 states-worth instead of 4.
2. **Pull the 11-state BGII ZIP→territory maps** the same way GL pulled `premopsterr`.
3. **Check which of the 25 "direct-select" BGII states are trivial** (one option, like AZ) vs. genuinely multi-option — cuts the dropdown-building list down.
4. **Resolve PR's missing `PrsnlPropTerrMultiplier`** — table-exists-but-empty vs. genuinely not filed.
5. **Design the resolved-territory cell** for each of the three mechanisms in the CF workbook, mirroring GL's cascade (mode → resolve → single downstream cell), and wire it into `Excel_Rater_BasicGroupI.md`'s still-open item ("verify the exact PP territory-factor table name").

This is table-pulling and a design doc — no rater changes yet. Say the word when you want the lookup workbook itself built.
