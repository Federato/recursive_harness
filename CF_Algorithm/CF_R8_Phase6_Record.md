# R-8 Phase 6: the payload spec collapsed onto `IN - Schedule`

**2026-09-22.** No workbook writes. Script: `scripts/cf/117_r8_phase6_payload_map.py`.
Output: **`CF_Payload_Schedule_Map.csv`** (128 rows, one per Schedule column).

---

## What Phase 6 turned out to be

The R-8 plan said Phase 6 would "collapse the Payload Export sheet". **That sheet was never
built.** The payload generator stopped after Step 3 (spec written). Step 4, building
`Payload Export` + `Defaults`, was assigned to the user and hasn't been done
(`CF_Payload_Generator_RESUME.md`). So there was nothing to delete.

What collapsed is **the spec**. `CF_Payload_Sheet_Spec_Step3.html` specified ~90 export columns
whose main job was to **transpose** the old one-column-per-item input tabs into one row per record,
with ID and ParentID. Its own build instructions say "location 1 reads column C, location 2 reads
column D". After Phase 5, `IN - Schedule` **is** that shape. What the spec still owns is only the
mapping from each field to ISO's, and that mapping is now written down against the Schedule.

## The map: `CF_Payload_Schedule_Map.csv`

| Kind | Count | Meaning |
|---|---|---|
| sent | **69** | Schedule column → ISO field, with any alias and format conversion |
| record | **16** | exclusion inputs; a "Yes" emits an empty endorsement record `[{}]` |
| not sent | **23** | derived or bookkeeping, or omitted for v1 as Step 3 decided (flagged "check DataDef") |
| key/filter | **20** | ID / ParentID (the join) and Active (emit only active records) |

Every block names its ISO record and its parent block, so the nesting rebuilds by joining on
ParentID. **Nothing in the map is a cell address.** It carries the Step 1 format traps (T-1 coinsurance
0.8 → "80%", T-2 zip as text, T-3 state → ProductName and one payload per state, T-4 BCEG class,
T-5 construction type only), the Step 3 aliases, and the D-2 decision (FullBldgValue = Limit).

### Five columns Step 3 never mapped, resolved against the 408 harvested payloads

| Schedule column | Verdict |
|---|---|
| OCCUPANCY CLASS.CovForm | **sent** as `CommercialPropertyOccupClass.CovForm` (ISO sends it in 57% of its own payloads). It selects the Legal Liability form, so omitting it would change the rating |
| BUSINESS INCOME / SC BI.ExtraExpenseSchedule | **sent** as `ExtraExpenseLimitOnLossPayment` (alias) |
| SPECIAL CLASS.ContentsCoins | not sent: ISO's SpecialClass carries a single `Coinsurance` |
| SPECIAL CLASS.ProtClass | not sent: ISO's SpecialClass has **no** ProtectClass and inherits the Location's. **The rater prices on the item's own (5 vs the location's 4): backlog W-10** |

### What R-8 bought the payload, beyond the transpose

- **S-1 / S-2 / S-3 are no longer a payload limit.** Special Class and SC BI now carry
  separate exclusion inputs, so the RECORDS block can elect each ISO record independently. Step 3's
  "two Elected cells pointing at one input" workaround is no longer needed.
- **Multi-record shapes are expressible**: several buildings per location, several occupancies and
  contents per building. Step 1 noted the old tabs couldn't express these, and they are exactly what Step 6's composition
  test needs.

## What is left of payload generator Step 4

| Step 3 planned | Now |
|---|---|
| `Payload Export`: 9 blocks, ~90 formula columns, transposing | **not needed, if the reader reads `IN - Schedule` directly** (see the open decision) |
| `Defaults`: 12 rows | still needed. Decision 8 stands: Python never invents a value and fails loudly |
| RECORDS block | the 16 `record` rows in the map |
| Format conversions in cell formulas | the `conversion` column in the map |

## Open decision (settled decision 1 would change)

Decision 1 (2026-09-22) was a hidden `Payload Export` sheet whose formulas point at the input tabs.
With the input tabs now in payload shape, that sheet would be a **second copy of the Schedule** that
can drift from it. The alternative is for the Step 5 reader to read `IN - Schedule` directly, applying
the map in code. **Not changed here: it's the user's decision.**

## Stale docs, superseded by this record

- `CF_Payload_Excel_Input_Inventory.*` (Step 1) and the source-cell column of
  `CF_Payload_Sheet_Spec_Step3.html` describe `Location Inputs` / `Special Class Inputs` cells, and
  those sheets no longer exist. **The map supersedes both for source locations.** The Step 2 field
  harvest and the Step 3 decisions (aliases, verdicts, D-2, Defaults) still stand.
