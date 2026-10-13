# R-8 Phase 4: Building, Business Income and Special Class migrated

**2026-09-22.** `CFRater1.02.xlsb`. `CFRater1.01.xlsb` was never opened.

| | Script | Backup | Gate |
|---|---|---|---|
| 4a Building | `scripts/cf/112_r8_phase4a_building.py` (`r8_building_translate.py`) | `Backups/CFRater1.02_pre-R8-4a_*.xlsb` | **passed**, re-verified after reopen |
| 4b Business Income | `scripts/cf/113_r8_phase4b_bi.py` (`r8_child_translate.py`) | `Backups/CFRater1.02_pre-R8-4b_*.xlsb` | **passed**, re-verified after reopen |
| 4c Special Class / SC BI | `scripts/cf/115_r8_phase4c_special_class.py` (`r8_sc_translate.py`); live probe `114_r8_sc_symbol_probe.py` | `Backups/CFRater1.02_pre-R8-4c_*.xlsb` | **passed**, re-verified after reopen |

Premiums after 4a/4b: **7183 / 8022 / 2699 / 1434 / 406 / 19744**, unchanged. After 4c, **by decision (W-8)**: **7183 / 8022 / 2699 / 1633 / 457 / 19994**.

---

## In plain English

Building and Business Income now work the way Contents has since Phase 2. Each column
is one record in `IN - Schedule`, and each coverage reads its inputs from there instead
of from `IN - Location`. Each coverage holds up to **40 records**, where the old limit was 10. An 11th
building or BI record entered **only on the Schedule** now prices, and it prices
exactly like the record it was copied from.

## 4a: Building

- `CALC - Bldg Rating` and the **110 CoreScratchpad rows** Building depends on are now
  keyed to the Schedule BUILDING block (column k = row 47+k). Building fields come from
  the building's own row. Location fields come through a new **LocIdx** key
  (CoreScratchpad row 285), which matches the building's ParentLoc to LOCATION.ID. Keys: rows 283-285.
- Building never reads occupancy, contents or BI inputs (checked by closure trace), so
  no other key was needed.
- `IN - Schedule` BUILDING gained column **AI `ConstrDesc`**, derived from ConstrCode
  (it was the only derived `IN - Location` field Building needed, row 61).
- Bldg Rating Source/Check moved M:N → AQ:AR, and the `OUT - Diagnostics` B5/C5 formulas were repointed.
- Contents' building- and location-level reads moved from `IN - Location` to the
  Schedule (2,560 cells). **Rows 87/90 (watchman, burglary alarm) still read
  `IN - Location`**, because the Schedule has no field for them yet. That's a Phase 5 item.
- The rest of CoreScratchpad (BI part, Special Class part, `IN - Location` derivations,
  the legacy Contents rows) is **untouched and still 10 columns wide**.

**Verified:** premiums unchanged, and every value unchanged on CoreScratchpad, Bldg Rating,
Contents, BI and Special Class. **Moving:** a +100k Schedule limit moved each of the
four active buildings (1224→1405, 940→1074, 1308→1407, 3711→3732). Location 2's protection
class moved building 2 (940→1111). **A building 11 copied from building 2 and
entered only on the Schedule priced at 940, the same as building 2**, and the Building total went
7183→8123. Recalc time went from 0.8s to 0.9s.

## 4b: Business Income

- `CALC - BI Rating` column k = the Schedule BUSINESS INCOME row 176+k. Keys: rows 79-81
  (BIID, Active, ParentCol).
- **20 CoreScratchpad rows (186-209)** read BI-level inputs, so they have per-record copies at
  BI rows 83-102.
- BI still borrows the parent building's computed rate, which is ISO's structure, so it
  still carries **W-4** (BI follows the Building's wind/hail election). Preserved.
- BI Source/Check moved M:N → AQ:AR, and Diagnostics B7/C7 were repointed.

**Verified:** everything unchanged. **Moving:** a +100k Schedule limit moved each active
BI record (1181→1609, 475→626, 725→900, 318→379). Location 2's protection class
reached BI record 2 through the parent chain (475→566). **A BI record 11 copied from
record 2 priced at 475, the same as its twin.**

## Found by the survey

**CoreScratchpad was not column-consistent: 81 cells in 9 rows.** In each of these rows, columns
D-L held a different formula from column C, not C shifted across. It looks like drag-fill drift.

| Row | What | How D-L differ | Status |
|---|---|---|---|
| 7 | ClassRate | Table column drifted (G, H, I… not F) | **Dead row**: nothing reads it (Bldg Rating row 3 does its own lookup) |
| 9-12 | Sub-standard condition keys | Wrong input rows (class code, description…) | **Standardised to column C in 4a** (in Building's chain). No premium moves today; sub-standard is "No" on items 2-10 |
| 57 | BGII County | Missing the state prefix, so it can't resolve a County-keyed state | Not in Building's chain; still drifted. Logged W-7 |
| 126 | Contents group indicator | Table columns drifted | Legacy Contents row, not read by the new Contents. Logged W-7 |
| 184 | BI Yard indicator | Reads CS3, not IL26 | Same value. Harmless |
| 216 | SC deductible factor | Table columns drifted | Only item 1 is active. Logged W-7 |

## 4c: the decision Special Class needs

**Special Class item k reads building k.** Its state (CoreScratchpad row 2), LCM
(Bldg Rating row 4), the state prefix on its own keys (CS 220-222) and its **Group II base
rate key** (CS 59/72) all come from "building k". Once columns become records with
parents, "building k" means nothing to a Special Class item.

- **State, LCM, BGII territory:** the Special Class item has its own location (zip,
  state, territory on `IN - Special Class`). Resolving through its location is
  unambiguous and gives today's values (item 1 is at location 1, FL, Inland).
- **Group II construction symbol:** ISO keys `LookupBasicGroupIIRate` on the Special
  Class item's **own `BasicGroupIISymbol`** (countrywide `CommercialPropertySpecialClassRules.Rule.xml`;
  no rule copies it from a building). The rater uses building 1's symbol, **AB**. Item 1's
  own symbol is **B** (`IN - Special Class` row 31). **So today's Special Class premium
  is probably keyed on the wrong symbol.** The lookup is live, because item 1's wind/hail exclusion is "No".
  Logged as **W-8**. Fixing it changes today's Special Class premium.

## 4c: Special Class and SC Business Income (decided 2026-09-22: use the item's own symbol, per ISO)

**Live ISO confirmation first** (`114_r8_sc_symbol_probe.py`). Chunk 6's Oregon Special Class
request was re-sent with only the item's `BasicGroupIISymbol` changed. ISO returned a Group II base rate of
**0.028 for B and 0.024 for AB** ($275 → $244), so ISO reads the item's own symbol. Florida,
where the rater's item sits, can't be checked directly: ISO refuses FL Special Class Basic
(chunk 6).

What changed:
- `CALC - Special Class` rows 1-87: column k = Schedule SPECIAL CLASS row 219+k. Rows 88-158:
  column k = Schedule SC BUSINESS INCOME row 262+k. Keys at rows 161-163 (SCID, Active,
  LocIdx) and 166-168 (SCBIID, Active, SCParentCol). The CoreScratchpad Special Class rows have
  per-record copies: **24 for SC (rows 171-194) and 24 for SC BI (rows 196-219)**.
- The "building k" reads are replaced: state and LCM now come from the item's own location, and the Group II
  key is state + the location's BGII territory + the **item's own symbol**. TOTAL LIMIT is the
  linked building's (only when the limit is included in a building). The cyber factors are read from Bldg Rating column C
  (they're policy-level).
- **The Schedule's SC BI Limit and both Active flags now mirror `IN - Special Class` row 20**,
  the SC BI limit the rater actually prices on. Phase 1 had mirrored **row 42**, which nothing
  reads (W-9). No premium effect.
- Special Class Source/Check moved M:N → AQ:AR, and 2 Diagnostics formulas were repointed.

**Verified:**
- Building/Contents/BI unchanged, and every value on their sheets and CoreScratchpad unchanged.
  Inactive SC slots price zero.
- **Isolation proof:** with the item's symbol set to building 1's "AB" in memory, **every value
  of the active item and both SC premiums return exactly to the pre-4c figures.** So the only
  behavioural change is the symbol, as decided. The rows that moved are the Group II chain (26-47)
  and SC BI's reuse of it (109-127).
- **Premiums:** Special Class **1434 → 1633**, SC BI **406 → 457**, Total **19744 → 19994**.
- **Moving:** SC limit +100k (1633→1952). SC BI limit +100k (457→671). Location 1's state
  FL→GA reaches the SC item (1633→1150). **An 11th SC item and its SC BI, entered only on the
  Schedule, priced exactly like their twins** (1633 / 457, SCParentCol 11).

**Noted, not changed:**
- `IN - Special Class` row 30 (the item's own "BGII Territory") is **no longer read**. ISO
  copies the territory from the Location, so the location's value is now used. It's the same value today
  (Inland).
- Rows 32 and 50 read `'IN - Policy'!C3` as a *relative* reference, so in columns D-L they
  read an empty cell (drift). Every column now reads C3. Only item 1 is active, so there is no premium effect.

## Phase 4 complete: where R-8 stands

Every coverage now reads `IN - Schedule` and holds 40 records: Contents (Phase 2), Building,
BI, Special Class and SC BI. What still reads `IN - Location` / `IN - Special Class` directly:
the **CoreScratchpad rows nobody uses any more** (legacy Contents/BI/SC helpers, still 10 wide),
`IN - Location`'s own derivations (District, BGII territory, severity, contents group), and
Contents rows 87/90 (watchman, burglary). That's **Phase 5**'s list.
