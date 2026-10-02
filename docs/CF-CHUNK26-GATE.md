# Property chunk 26: the gate

**Specific and Tentative rating: the second way to rate the core coverages, with a rate published for one building in
place of the class tables; California's One-Term Loss Cost; and Specific Group II in the 36 states that offer it.**
Filed 2026-10-02. **9 of 9, and all 23 tasks done.** Task record: [`CF-CHUNK26-TASKS.md`](CF-CHUNK26-TASKS.md). The chunk
adds no premium file: **546 of 546** countrywide premium files built, unchanged.

**In plain English.** A Class-rated building's Group I rate comes from ISO's class tables (base rate, territory, protection
class…). A **Specific** building carries a rate published for that exact building; **Tentative** is the same thing while the
published rate is pending. The engine already ran ISO's rule files for both; this chunk proved them. **The evidence already
agreed**: the 126 distinct stored Specific / Tentative policies (16 states) re-rate with every premium equal to ISO. Every new
figure was worked out before it ran (the rates by hand from each state's own rule, each premium by 174_'s evaluator on the
state's own premium rule) and each case carried a competing reading that ISO could have matched instead; **it never did.**
**No engine change.**

**Things the rules do that a submitter must know**, each found by running and confirmed by ISO:
- The building's `RatingType` is **copied** to the occupancy and the contents (a submitted copy is overwritten). **Contents
  price on their OWN `SpecificGroupIRate`** (none of their own → Group I $0, silently); **BI uses the building's.**
- Specific / Tentative replace the whole class chain: base rate, territory, protection class and the contents' fire-safe
  vault factor move no Specific dollar. FL NY WV and MO (CW 2023 V02) **leave the roof ACV factor out** of the Specific
  formula; KY rounds once and keeps it; MO's BI reads the building's FINAL rate.
- **A blank `RatingType` prices at rate 1.0** (building $1,204 where Specific gives $362; BI $538). No `SpecificGroupIRate`
  on a Specific building → building AND BI Group I $0.
- **Specific Group II** needs `RatingTypeBasicGroupII` "Specific" and `SpecificGroupIIRate`; blank → Group II $0 on
  building, contents and BI, silently. Floor-area messages (Severe < 10,000, High < 25,001, Medium < 50,001 sq ft; Low never)
  fire but **do not stop the specific premium**. The class Group II base-rate lookup still runs: the location's
  `BasicGroupIIRatingTerr` must be one the state's rate table files (ISO refuses a missing row).
- **CA One-Term Loss Cost** prices the building and contents as Specific; BI falls to rate 1.0 ($538) at ISO too (OI-124).
- Tentative also attaches the Tentative Rate form record; nothing reads a `TentativeRate` field.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `235_chunk26_rc2.py --live`, 7 cases, **ISO 7 of 7**, every premium and message: Specific building Group I $362 (class $287), contents $150 on their own rate (class $197) and $335 at 0.450 (the building's rate: $223), BI $137 on the building's; Tentative identical plus its form; SC Specific Group II at the three thresholds $67 / $37 / $24 (Class $175 / $90 / $12); CA One-Term BI $538 (Specific reading $121) |
| 2 | Every table's row count stated | ✅ | C26-06: `DomainClassCodeBldg` 146 Specific / Tentative codes (Class-only: 0196–0198, 0581, 0582, 1150, 1650, 1700), occupancy 142, `DomainCovForm` 26 rows keyed by policy type and rating type, FL GA KS NY CA own domains; the identification-code tables (Class 2 / schedule 1; FL MO SC's Group II states their own letters) |
| 3 | Every state is enumerated | ✅ | C26-19 (`237_ --live --states`): **all 46 states agree with ISO** on a Specific building, Specific Group II in the 36 that offer it; a submitted roof factor makes each state's formula shape show in dollars |
| 4 | Every `0` tested against its consuming branch | ✅ | C26-12 (`236_` Z1–Z6): no specific rate (building and BI $0), contents with no own rate ($0), a Class-only class code (rated as written), blank Group II type ($0 ×3), blank `RatingType` (rate 1.0), `RatingType` on the Special Class (ignored) |
| 5 | Every hardcoded literal key listed | ✅ | C26-06 / C26-13: "Class" / "Specific" / "Tentative" / "One-Term Loss Cost", the hazard levels and floor areas (10,000 / 25,001 / 50,001), FL's 21 residential class codes, DC's three boarding descriptions, the apartment class codes (0300, 0311–0313): each traced to its rule |
| 6 | Shared-name traps diffed | ✅ | C26-03 / 04 / 14: `RatingType` on the building vs its copies (overwritten), `SpecificGroupIRate` on the building vs the contents (independent), a submitted `BasicGroupIRate` (survives, BI unaffected), `TentativeRate` (never read) vs Builders Risk's `TentativeGroupIRate` (its own) |
| 7 | Every exclusion's endorsement record identified | ✅ | C26-15: the class-only factors (protection class, territory, fire-safe vault, the seven occupancy counts) proven to drop out on a Specific building while each moves a Class dollar; OI-125 for the occupancy counts' messages |
| 8 | The edition basis stated | ✅ | C26-18: of the every-rule edition differences only MO's (CW 2023 V02) 4 name the rating type: its Specific formula (no roof factor) and BI (the building's final rate) probed against the 2026 reading in dollars, **ISO follows V02**; its two conditional-mandatory differences do not touch the branch; V03 (NC, 91 differences) and V04 (IL, none) price as 2026 |
| 9 | No unexplained validation message | ✅ | C26-13 (`236_`): all 11 message rules fired at their level one below each threshold and silent at it (both wordings, Low, FL, DC); ISO's (level, message) multiset equals ours everywhere except K4d's occupancy-count message, **explained: OI-125** |

## What the chunk established, in submission terms

* **Building**: `RatingType` "Specific" / "Tentative" (CA also "One-Term Loss Cost"), `SpecificGroupIRate`; for Group II in
  the 36 states `RatingTypeBasicGroupII` "Specific", `SpecificGroupIIRate`, `SquareFootageOfBuilding`, and the location's
  `GeographicWindHazardLevelTerritory` and a filed `BasicGroupIIRatingTerr`.
* **Contents**: their own `SpecificGroupIRate` (and `SpecificGroupIIRate`); the rating type is copied, not sent.
* **Downstream** (C26-20, `238_`): Class → Specific moves the policy total by exactly the core records' differences,
  **+$56 (OR) / +$701 (rates doubled, the clean test) / +$68 (FL) / −$149 (SC Group II) / −$794 (MO)**, each predicted before
  its ISO call and equal at ISO; every other premium, terrorism included, unchanged; stat values and identification codes
  equal (Class 2 → Specific 1 in OR, H → G in FL MO and SC).
* **Gate checks** (C26-21, no engine change in the chunk): `104_ --quick` **CLEAN** (34 scripts: every golden case of chunks
  1–26, chunks 1–8's figures included, and the chunk 26 scripts); `206_ --check` **SNAPSHOT CLEAN** (1,697 stored requests,
  1,258,654 fields, nothing moved); `157_ --all` **293 of 293**. Registered in `104_`: 235_ pinned (362, 150, 335, 137, 67,
  37, 24, 354, 146, 538), 234_ (the replay of the stored evidence), 236_, 237_, 238_.
* **Census** (C26-22): 546 of 546 unchanged; the second rating path recorded as built on the status page and in
  `CF_Algorithm/Coverage_Inventory_And_Tracking.md` (engine only: the Excel rater's Specific gap is unchanged).

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-124** | CA One-Term Loss Cost leaves BI's Group I at rate 1.0; **ISO does the same**: a filing gap a submitter must know | no |
| **OI-125** | The seven "only one … occupancy record per building" counts are 0 at ISO even when the occupancy's rating type is submitted; ours counts it (messages only); engine change needs the user's go | no |
| **OI-99** | 31 stored failed calls on Specific policies (missing rows elsewhere: Special Class, wind hazard, BCEG EQ, FL cyber) that ours prices; chunk 28 | no |
