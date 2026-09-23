# Payload generator — Step 1: the rater's input surface

> <!-- RC-1 stale-name notice --> **Notice (2026-09-23):** Written before the 2026-09-22 restructure. Sheet names have changed: Policy Inputs → IN - Policy; Bldg / Contents / BI Rating Worksheet → CALC - Bldg / Contents / BI Rating; Special Class Worksheet → CALC - Special Class; CoreScratchpad → CALC - CoreScratchpad. **Location Inputs / IN - Location and Special Class Inputs / IN - Special Class no longer exist**: every record is entered on **IN - Schedule** (one row per record, 40 per block), so input-sheet cell addresses here are out of date, and calc-sheet column C is record 1 of 40. Current state: CF_Algorithm/CF_Rater_RESUME.md.


**Read 2026-09-22**, read-only via `pyxlsb` against `C:\Projects\Spreadsheet_Rater\CF\CFRater1.01.xlsb`.
Excel confirmed not running before the read. No COM, no writes, no `Save`/`Quit`.

Machine-readable companion: **`CF_Payload_Excel_Input_Inventory.csv`** — 127 input fields,
30 section headers, with label cell, first value cell and a sample value for each.

---

## 1. The workbook

26 sheets. Three are input tabs; the rest are calc worksheets, lookup tables and scratchpads.

| # | Sheet | Role |
|---|---|---|
| 1 | `Policy Inputs` | **Input** — policy-level terms + the premium summary |
| 2 | `Location Inputs` | **Input** — everything per building item |
| 3 | `Special Class Inputs` | **Input** — Special Class items |
| 5–9 | `Bldg` / `Contents` / `BI` / `Special Class Worksheet`, `CoreScratchpad` | Calc |
| 4, 10–26 | `BGIITerritory`, `BI Tables`, `ClassCodes`, `ZipCityState`, `ProtClass`, `LCM`, … | Lookup data |

---

## 2. Layout — the shape that matters for the export sheet

**Both item tabs are transposed relative to the payload.** Fields run down column B as labels;
each *item* is a **column**, not a row.

```
Location Inputs
              C        D        E        F     …  L
B4  Location #:    1        2        3        4        10
B5  Building #:    1        1        1        1         1
B6  Item ID:    "1 - 1"  "2 - 1"  "3 - 1"  "4 - 1"  "10 - 1"
B26 Building Class Code:  0311  0311  0311  0311   Select
```

- `Location Inputs` carries **10 item columns** (C–L), rows 4–93.
- `Special Class Inputs` carries **3 item columns** (C–E), rows 4–46.
- `Policy Inputs` is scalar — labels in B and E, values in C and F.

**Consequence for the export sheet:** it transposes. One row per record, reading across the item
columns. This is mechanical, and it is exactly what the long-format design chosen in Q7 expects.

**The `Item ID` scheme is already there** (`B6` on both item tabs, `Location# - Building#`), so the
parent/child join the payload needs is a value the workbook already computes. Nothing to invent.

---

## 3. Findings that change the build

### 3.1 One workbook is **several** ISO requests, not one

The four populated columns are **FL, NY, AK and CA** — four different states in one submission.
ISO's payload carries the state in `SchemeKeys.ProductName` (`"Commercial Property AL"`), one state
per request; there is no `StateCode` field to vary per location.

**So the generator must group items by `State` and emit one payload per state**, then make one RAaS
call per state and sum. This was not in the design discussion and it is the single most consequential
thing the read turned up. It does not make the build harder, but it changes the shape of the output:
*N* payloads and *N* premiums, not one.

### 3.2 One building per location, one occupancy class per building

Row 5 (`Building #`) is `1` in all ten columns, and there is exactly one `Tenants Class Code` /
`Occupancy Category` per column. So today the workbook models **10 locations × 1 building × 1
occupancy class**.

The payload allows *N* buildings per location and *N* occupancy classes per building. The long-format
export sheet can express that whenever the workbook grows into it — but **it confirms directly what
the review inferred**: the multi-occupancy-class shape chunk 4 proved ISO sums is not reproducible
here. Step 6 should include one such case deliberately, and expect Excel to disagree.

### 3.3 Blanket is genuinely absent on Building and Contents

`Special Class Inputs` has `Included in Blanket:` (B13). `Location Inputs` has **no blanket field at
all**. Consistent with the review — blanket remains the widest gap.

---

## 4. Four corrections to the 2026-09-22 review

The review was written from `Excel_Rater_AllRatingPaths_BuildStatus.html`, whose last direct read was
**2026-09-11**. The workbook has moved since. All four corrections run the same direction — the rater
is **further along** than its own status page says.

| # | The review said | The workbook shows |
|---|---|---|
| 1 | Specific/Tentative rating is unbuilt project-wide | **Built.** `Rating Type` (B28) offers `Specific`; dedicated Specific/Tentative rate rows exist for Building (B44), Contents (B46) and Business Income (B48), and column C is a live `Specific` risk |
| 2 | Special Class — Broad and Special "not built into the live workbook" | **Built and rating.** `Policy Inputs!I6` = **$1,434** |
| 3 | Special Class Business Income — "traced only, nothing in the workbook" | **Built and rating.** `Policy Inputs!I7` = **$406** |
| 4 | Legal Liability — "formulas written, never built into calc columns" | **Built.** `Building Coverage Type` = `Legal Liability` in column C, with the `Additional Insurable Interest Option` input (B92) and its decoded description (B93) |

`Harness_vs_Rater_Review.html` has been corrected in place with a dated block rather than silently
edited.

**The process gap this exposes:** the review trusted a status page rather than the artefact, because
Rule #0 made the artefact expensive to check. The status page carried no staleness marker. Any future
build-status page in this project should record the date of its last direct read *next to each claim*,
not once in the header — a claim's age is part of the claim.

---

## 5. Mapping traps found in the actual data

Seven, on top of the six already known from `BUILD-LOG.md` Entry 35. All are format conversions in
the export sheet, not logic.

| # | Field | Rater holds | ISO wants |
|---|---|---|---|
| T-1 | Coinsurance | `0.8` (number) | `"80%"` (string) |
| T-2 | Zip Code | `32809.0` (float) | `"35203"` (string, no decimal) |
| T-3 | State | `"FL"` in a field | no such field — folds into `ProductName` |
| T-4 | BCEG | `"1"` … `"4"` | two fields: `BCEG` + `BCEGClass` (`"Ungraded"` / `"Not Graded"`) |
| T-5 | Construction | both `Construction Code` (2.0) and `Construction Type` ("Joisted Masonry - Reinforced") | send `ConstructionType` only; ISO derives the code |
| T-6 | Deductible | `"2,500"` (string, comma) | `"2,500"` — **matches, no conversion** |
| T-7 | Percentages (Type 1/2) | `1.0` / `0.0` | maps into the shared BI `Factor`; needs the Q3 spec extension |

T-5 is worth a second look: the rater holds *both* halves, and the `Construction Type` strings are
ISO's long-form domain values verbatim. That is the harder direction to get right and it is already
right.

---

## 6. What Step 1 did not answer

- **Business Income field mapping.** `Type of Risk`, `Max Period of Indemnity`, `Monthly Limit of
  Indemnity` and `Extra Expense Loss Payment Schedule` (B36–B41) are present and populated, but BI is
  not in the ISO payload spec yet — that is Step 2 and it needs ERC tracing, not a read.
- **Whether the Special Class items belong in the same payload as the Building items.** Both tabs key
  on `Item ID` and both carry a `State`, but the linkage field (`Limit Included in Building?`,
  `Linked Building Item ID`, B21–B22) is `No` / `N/A` in all three populated columns, so the linked
  case is untested data. Needs resolving before Step 5.
- **Dropdown domains.** The read captured current *values*, not the full validation lists. Step 3
  needs those to write the `Defaults` sheet; they live in `PolicyDropdowns`, `ClassCodes`,
  `ConstructionCodes` and `Derivations`.

---

*Step 1 of 6. Next: Step 2 — extend the ISO payload spec to Business Income.*
