# Payload generator — RESUME HERE

**Last worked 2026-09-22.** Read this file first. Everything below is decided, not proposed.

**Goal:** generate a rateable ISO payload from `CFRater1.01.xlsb`, call ISO, rate the same payload
through `cf_engine`, and print a three-way comparison — Excel vs ISO vs engine.

---

### ⚠ 2026-09-22 (later): R-8 changed the ground under Steps 1, 3 and 4. Read `CF_R8_Phase6_Record.md` first

- **The rater's input tabs no longer exist.** Risks are entered on `IN - Schedule`, which holds one row per record with
  ID + ParentID, i.e. the long format decision 7 asked for. `Location Inputs` / `Special Class Inputs`
  (Step 1's inventory, Step 3's source cells) are gone.
- **The build target is now `CFRater1.02.xlsb`** (the prototype). 1.01 is frozen.
- **`CF_Payload_Schedule_Map.csv` supersedes the Step 3 source-cell column**: Schedule column → ISO
  record/field → conversion, for all 128 columns. The Step 3 decisions (aliases, verdicts, D-2, Defaults) stand.
- **Step 4 shrinks** to the 12-row `Defaults` sheet, **if** the reader reads the Schedule directly.
  That would change decision 1 (the `Payload Export` sheet) and is the user's call. It's open.

### ✅ 2026-09-22 (end of day): Steps 4-6 built and run against live ISO: read `CF_Payload_Step4-6_Record.md`

The reader reads `IN - Schedule` directly (user decision). `Defaults` sheet built. CLI:
`python scripts/cf/119_payload_three_way.py --without-cyber FL`. Engine = ISO on 33/33 record-forms.
The 7-block composition is accepted by ISO. FL refuses Cyber (filing gap); NY refuses (header-only symbol table).
The Excel-vs-ISO differences are listed there in dollar order. **Everything below this block is history.**

## Status: Step 1 of 6 complete

| Step | What | Owner | Status |
|---|---|---|---|
| 1 | Read-only inventory of the rater's input tabs | me | **DONE** 2026-09-22 |
| 2 | **Harvest** the union field set from 44 stored ISO-accepted requests | me | **DONE** 2026-09-22 — `CF_Payload_Field_Harvest_Step2.md` |
| 3 | Spec the `Payload Export` + `Defaults` sheets, column by column | me | **DONE** 2026-09-22 — `CF_Payload_Sheet_Spec_Step3.html` |
| 4 | Build those two sheets in the workbook | **you** | **NEXT — unblocked.** Spec: `CF_Payload_Sheet_Spec_Step3.html` · Wireframes with real rows/formulas: `CF_Payload_Sheet_Wireframes.html` |
| 5 | Build the CLI: read → JSON → RAaS → `cf_engine` → three-way diff | me | blocked on 4 |
| 6 | Prove it against a case with a known answer | me | blocked on 5 |

**Nothing has been built. No code written. No writes to the workbook, ever — step 4 is yours by design.**

### ⚠ Correction, 2026-09-22 — Step 2 was mis-scoped; it is much smaller than first written

Step 2 originally read "extend the ISO payload spec to Business Income — needs ERC tracing," on the
grounds that `CF_Payload_ClassRated_Bldg_PP_Alabama.md` covers Building + Personal Property only.
**The user challenged this and was right.** `results/cf-raas/` holds **44 stored requests that live
ISO has already accepted**, spanning every coverage in scope:

| Coverage blocks present | Requests | Example |
|---|---|---|
| Structure (Building) | 22 | `AL_chunk3_Special_request.json` |
| Structure + OccupClass + PersonalProperty | 6 | `AK_chunk4_Basic_1item_request.json` |
| **Structure + BusinessIncome** | **6** | `OR_chunk5_Special_plain_request.json` |
| SpecialClass | 6 | `AZ_chunk6_Basic_request.json` |
| SpecialClass + SpecialClassBusnIncome | 4 | `OR_chunk7_Basic_noded_request.json` |

The Business Income block is nine fields, directly under `CommercialPropertyStructure`. So Step 2 is
**harvesting a union field set from payloads ISO has already blessed** — hours, not days.

- **Revised estimate: ~1–2 days total, not 3–4.**
- **v1 can cover everything the rater builds**, Special Class and SC Business Income included. The Q3
  option text implying those cost extra was wrong.
- **The narrower risk that survives:** no stored request combines Building + Contents + Business
  Income + Special Class in a *single* payload, which is exactly what the rater emits. Each block is
  individually ISO-proven; their **composition is not**. Test that first in Step 6.

**Standing lesson — second document-vs-artefact miss in one day** (the first is the stale status page
in "Four corrections" below). Both times a document was behind the thing it described. **The missing
check: before scoping anything as "not yet done," grep the repo for evidence it already happened.**

---

## The eight decisions (settled 2026-09-22, don't re-litigate)

| # | Decision | Choice |
|---|---|---|
| 1 | Data out of the workbook | Hidden **`Payload Export`** sheet, formulas pointing at the input tabs |
| 2 | Workbook access | **Approved** — read-only, `pyxlsb`, no COM, Excel must be closed |
| 3 | v1 coverage | Building + Contents + **Business Income** |
| 4 | Output | JSON → ISO → `cf_engine`, **three-way diff** |
| 5 | Trigger | Python CLI; workbook stays macro-free |
| 6 | Code location | `scripts/cf/` in the harness |
| 7 | Record depth | **Long format, unbounded** — one row per record, ID + ParentID |
| 8 | Defaults | **`Defaults` sheet** in the workbook; Python never invents a value, it fails loudly |

---

## What Step 1 found — read `CF_Payload_Excel_Input_Inventory.md` for detail

1. **3 input tabs, 127 input fields.** `Policy Inputs` (scalar), `Location Inputs` (10 item columns,
   rows 4–93), `Special Class Inputs` (3 item columns, rows 4–46). Machine-readable list in
   `CF_Payload_Excel_Input_Inventory.csv`.
2. **The item tabs are transposed** — fields down column B, one *column* per item. The export sheet
   transposes them. Mechanical.
3. **`Item ID` (`Location# - Building#`) already exists** on both item tabs — the parent/child join the
   payload needs is already computed. Nothing to invent.
4. **⚠ One workbook is *several* ISO requests.** The four populated columns are FL, NY, AK and CA. ISO
   carries state in `SchemeKeys.ProductName`, one state per request. **The generator must group by
   state and emit one payload per state**, then make N calls and sum. Not in the original design;
   doesn't make it harder, but changes the output shape.
5. **One building per location, one occupancy class per building.** Confirms directly what the review
   inferred — the multi-occupancy-class shape chunk 4 proved ISO sums is not reproducible here.
6. **Seven format traps** (T-1…T-7) on top of Entry 35's six. All export-sheet conversions, not logic.
   Coinsurance `0.8`→`"80%"` and Zip float→string are the two that will bite first.

---

## Four corrections made to the review, same day

`Harness_vs_Rater_Review.html` was written from a status page last verified **2026-09-11**. The read
found it stale in four places, all in the same direction — **the rater is further along than its own
status page said**: Specific/Tentative **is** built (and is absent from the *harness*, so that gap runs
the other way), Special Class rates **$1,434**, SC Business Income rates **$406**, and Legal Liability
is a live coverage type. The review is corrected in place with a dated block.

**Standing lesson — process, not content.** The review trusted a status page instead of the artefact,
because Rule #0 made the artefact expensive to check, and the page carried no per-claim staleness
marker. **Any build-status page in this project should date each claim, not just its header.** The
missing automated check: a status page whose claims are older than the artefact's mtime should say so
on its face.

---

## What Step 2 found — read `CF_Payload_Field_Harvest_Step2.md` for detail

- **408 payloads harvested**: our 44 ISO-accepted requests + **364 of ISO's own STC** payloads →
  `CF_Payload_Field_Matrix.csv`, 508 rows.
- **Our payloads are minimal, ISO's are rich.** We send 20 fields on a Structure; ISO sends up to 107.
  Both rate. Safe reading: `ISO only` fields are safe to omit, `ours only` fields are safe to send.
- **The join:** 63 of the rater's 127 inputs map to an ISO field; **64 need a verdict**, but only
  **30** are genuine — the rest are workbook bookkeeping (12), exclusions (11), Cyber detail (3),
  SubStdCondition A–E (5) and Specific/Tentative rates (3).
- **⚠ Structural finding — exclusions are records, not fields.** The rater uses Yes/No inputs; ISO uses
  the *presence* of an endorsement record (`"CommercialPropertyCyberIncidentExclusion": [{}]`). The
  export sheet therefore needs a **records block**, which the Step 1 design sketch did not have. This
  also confirms backlog **S-1/S-2/S-3** are a *payload-fidelity* limit, not only a rating simplification.
- **Composition risk now measured:** the rater emits **7** coverage blocks; the widest payload ISO has
  ever accepted is **4**. `BusinessIncome`, `SpecialClass` and `SpecialClassBusnIncome` have never
  co-occurred with the Building+Contents set. **Step 6 must open with the 7-block payload.**

---

## What Step 3 produced — `CF_Payload_Sheet_Spec_Step3.html` is the build sheet for Step 4

- **2 sheets, 9 blocks, ~90 export columns, 12 `Defaults` rows.** Column-by-column spec with the source
  cell for every one. Build `Defaults` first (10 minutes, unblocks reader testing).
- **The `Defaults` sheet is 12 rows, not 165.** Most of Step 2's "no rater source" fields *do* have a
  source under a different name (`District`, `BasicGroupIISymbol`, `VacantBuilding`, `SprinklerSystem`,
  `SubStdConditionA–E`, `SpecificGroupIRate`, 16 in total — alias fixes only).
- **⚠ Step 2's "safe reading" was too loose and is corrected.** "`ISO only` fields are safe to omit" holds
  *only when the rater's value is the neutral one*. Our 44 payloads never sent `VacantBuilding` because
  those cases didn't use it — the rater's own data has `Vacancy = Yes`. **Corrected rule: export every
  field the rater can source, whatever its evidence class.** Evidence class decides what we *default*,
  not what we *send*.
- **Block 9 (RECORDS) is new** — exclusions are emitted as empty endorsement records, so S-1/S-2/S-3 get
  **two `Elected` cells per Special Class exclusion** now, even though both point at one input today.
  Closing the backlog later becomes an input change, not a re-spec.
- **The 30 verdicts:** 16 resolved by alias · 12 are bookkeeping, not sent · 8 omitted for v1 (no ISO
  field found in 408 payloads — **flagged, must be checked against `MasterCFCW.DataDef.xsd`** before
  that's settled; absence from a corpus is not absence from the schema) · **1 needs the user**.

### ✅ `FullBldgValue` — settled 2026-09-22, Step 4 is unblocked

The user asked whether the scratchpad already computes this. **It computes something adjacent, not this**
— `CoreScratchpad!B138 "TOTAL LIMIT"` = 1,190,000 = Building 675,000 + Contents 515,000, which feeds the
**DeductibleFactor** lookup. It totals *limits*, not insurable *value*. ISO keeps the two apart
deliberately (its AL sample: `Limit` 500,000 vs `FullBldgValue` 550,000).

**The finding that settled it:** across all 127 inputs the rater has four `*Limit` fields and **no value
field anywhere** — it already assumes limit = value.

**Decision: `FullBldgValue = Limit`, `FullSpecialClassValue = Special Class Building Limit`.** Not
because it is correct, but because **the payload must reproduce the rater's assumptions exactly** — a
truer value in the payload than the workbook holds would manufacture a three-way-diff disagreement caused
by the generator rather than by the rater. Logged as **D-2** in `Rater_Simplifications_Backlog.md`. Fix
the rater first (add the input rows), and the payload follows.

---

## Open questions to settle before Step 5

- **Do Special Class items join the Building payload or ride separately?** Both tabs key on `Item ID`
  and carry `State`, but the linkage fields (`Limit Included in Building?`, `Linked Building Item ID`)
  are `No`/`N/A` in all three populated columns — the linked case is untested data.
- **Dropdown domains** for the `Defaults` sheet live in `PolicyDropdowns`, `ClassCodes`,
  `ConstructionCodes`, `Derivations`. Step 1 captured current values, not the validation lists.
- **Step 2 may surface choices the ERC files don't settle** — expect at least one question during the
  Business Income spec extension.

---

## How to restart cold

1. Read this file, then `CF_Payload_Excel_Input_Inventory.md`.
2. Confirm Excel is closed before any workbook read: `Get-Process EXCEL`.
3. Existing pieces the build will call, all working: `scripts/raas.py` (live ISO, OAuth),
   `scripts/diff_payload.py`, `scripts/rate_all_payloads.py`, `cf_engine/` (chunks 1–9 gated),
   `CF_Algorithm/sample_payloads/AL_class_rated_bldg_pp_special.json` (a known-good payload),
   `CF_Payload_ClassRated_Bldg_PP_Alabama.md` (the spec), `CF_Payload_Completion_Tracker.md`.
4. Say **"go, step 2"** to continue.

*Nothing gets built until you say go.*
