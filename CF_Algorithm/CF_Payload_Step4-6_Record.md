# Payload generator Steps 4-6: built, and first run against live ISO

**2026-09-22.** User decision the same day: **the reader reads `IN - Schedule` directly**
(decision 1's `Payload Export` sheet is dropped; see `CF_R8_Phase6_Record.md`).

| Step | What | Where |
|---|---|---|
| 4 | `Defaults` sheet, 12 rows, premiums unchanged | `scripts/cf/118_payload_defaults_sheet.py` |
| 5 | CLI: pyxlsb read → one payload per state → live ISO + `cf_engine` + the rater's own premiums, compared **per record per form** | `scripts/cf/119_payload_three_way.py` |
| 6 | First live run | `results/cf-payload/20260922-150647/` (every request, response and the comparison) |

    python scripts/cf/119_payload_three_way.py --without-cyber FL

---

## In plain English

You can now run the workbook's risk against ISO and our engine with one command. It builds the ISO
request straight from the Schedule and shows, for each building, contents, BI and Special Class
record and each form, three numbers: **Excel, ISO and our engine**. The first run said three things:

1. **Our engine matches ISO exactly, on every record and form ISO would price** (33 of 33 across
   Florida, Alaska and California).
2. **ISO will price everything the rater holds in one request.** Seven coverage blocks together had
   never been sent before, and ISO accepted them.
3. **The rater disagrees with ISO in specific, repeatable places.** Those are listed below, with
   dollar amounts attached.

## Results (Excel / ISO / engine)

| State | ISO | Excel vs ISO | Engine vs ISO |
|---|---|---|---|
| **CA** | rated | 6 of 9 match; **Contents Special -189**, two ±1 | **9 / 9** |
| **AK** | rated | 2 of 9 match; **Basic Group I low by 113-139 on Building, Contents and BI**; Contents Special +15; three -1 | **9 / 9** |
| **FL** | rated, **without Cyber** (below) | 1 of 15 match. The Legal Liability item: **ISO prices Building BGII, all Contents forms and BI BGII at 0; Excel charges 651 / 556 / 885 / 191 / 640**. Special Class BGI +54 | **15 / 15** |
| **NY** | **refused** (below) | no answer | engine priced it (ISO refuses) |

Totals: Excel 19,994 · ISO 15,417 (FL, AK, CA) · engine 17,484 (includes NY).

## ISO refusals: both on ISO's side, not ours

- **Florida and Cyber.** With the Cyber Incident Exclusion elected, ISO fails:
  `CyberIncidentExclusionFactors, Project CF FL 20241201 V02, Keys: CW, Basic Group I. No results`.
  **Florida's filing has no Cyber factor row for Basic Group I**, so ISO can't rate a Florida policy
  with that exclusion. The rater applies Cyber in every state. `--without-cyber FL` drops the records so
  the rest can be compared. Excel then reads about 0.8% low against ISO for that reason alone.
- **New York, Group II symbol.** `BasicGroupIIRate, Project CF NY 20260801 V01, Keys: CW, III, "", Bldg`.
  ISO derives the Structure's symbol itself (`LookupBasicGroupIIConstructionSymbol`, from
  ConstructionType + NumStories) and ignores the one we send. **New York's own
  `BasicGroupIIConstructionSymbol` table is filed header-only (0 rows)** and overlays the
  countrywide one, so no New York building can get a symbol. This is the same shape as chunk 6's
  header-only NY converter. Our engine priced NY anyway, which adds a case to the open "ISO refuses
  where we tolerate" question.

## Payload fixes found by the first run

- **Legal Liability Additional Insurable Interest:** ISO keys on the **description**, not the option
  code. "Option1" was refused; the CLI now sends the description
  (`AdditionalInsurableIntOption.RateTable.csv`).
- **Wind/hail deductible "Not Applicable"** is sent as the flat deductible. That is the rater's own
  reading, established in R-8 Gate 2.
- `SprinklerSystem` is blank ("Select") on 3 buildings and is omitted. That's listed on every run and
  never guessed.

## What the differences probably are (hypotheses, not verdicts)

- **FL Legal Liability zeros (≈ $2,900).** The rater charges every form on a Legal Liability risk.
  ISO charges Basic Group I and Special on the building and **nothing on its contents**. Most likely
  the Legal Liability form doesn't carry those groups at all. Same neighbourhood as W-1 / Z-1.
  **Largest single difference; first to trace.**
- **AK Basic Group I low by ~16%** on all three coverages at once. That points at one shared factor,
  probably the AK District base rate (**D-1**: "AK's ZIP mapping is known-inaccurate").
- **Contents Special: CA -189, AK +15.** The contents Special chain, possibly **W-6** (the Special
  deductible banded on the record's own limit, not the location total).
- **Special Class BGI +54 (FL).** Possibly **W-10** (the rater prices on the item's own protection
  class 5 where ISO uses the location's 4).
- **The ±1s:** the rounding-order family (Fix B covered BGI Contents only).

## FL Legal Liability zeros: resolved (2026-09-22, later), all three were payload errors

| Zero | Cause | Fix |
|---|---|---|
| Building / BI Group II | payload sent `RatingTypeBasicGroupII = "Specific"` (Step 3 Defaults #10: "= RatingType"). The rater rates Group II from the class tables | send `"Class"` |
| All Contents forms | ISO's contents AII factor reads a **separate** `CommercialPropertyLegalLiabilityCoverageFormOccupClass` record on the Occupancy Class; absent, so factor 0.0 (Z-1) | emit it from the building's option |
| Contents / BI Group I base 0 | under Specific rating ISO reads `SpecificGroupIRate` on the PP and BI records too; Step 3 had marked them "omit v1" | send the rater's Contents / BI specific rates |

After the fixes, **engine = ISO on 15 / 15 FL record-forms**. What remains is a **real rater difference: W-11**. On the
Legal Liability item Excel is low (Building BGII 651 vs 999, Contents BGII 885 vs 1082, BI BGII 640 vs 862,
Contents Special 191 vs 340 = W-1).

## Alaska Group I: resolved (2026-09-22), the gap was the district, not the math

ISO chooses Alaska's District I/II table from the **ISO rating area** (`City` + `BasicGroupIDistrictTerritory`
→ `RatingTerrGroupICodeAK`), never from `District`. The payload had sent the postal city ("Haines"), so ISO fell
to District II (0.116 vs the rater's District I 0.097). The payload now reproduces the rater's own district
(Remainder of State + Yes/No). **AK Building and Contents Group I then match ISO exactly (704, 611).** Whether
Haines really *is* District I is backlog **D-1a**: the rater has no input for ISO's rating area.

## Next

Trace the differences in dollar order: FL Legal Liability, then AK Group I, then Contents Special,
then SC BGI, then the ±1s. Each fix gets re-verified by re-running this command.
