# Property chunk 20: the gate

**Small coverages with their own tables: Radioactive Contamination, Pier and Wharf, Fire Department
Service Charge, Tobacco Sales Warehouses, the four special-limit items (furs, jewelry, patterns and dies,
stamps), Additional Covered Property, Food Contamination, Mortgageholders E&O, Fungus / Wet Rot / Dry Rot
changes and Equipment Breakdown, in all 46 states.** Filed 2026-09-29. **9 of 9, and all 26 tasks done.**
Task record: [`CF-CHUNK20-TASKS.md`](CF-CHUNK20-TASKS.md).

**In plain English.** Ten small coverages, each with its own little rate table or formula: contamination by
radioactive material, piers and wharves, a fire-department call-out charge, tobacco stored for sale, raised
limits on furs / jewelry / patterns / stamps, docks and retaining walls, food-contamination closures, errors by
a mortgage lender, mould cover, and machinery breakdown. **None of the 28 countrywide premium records had ever
been priced by ISO**; four of the families sat at $0 on every stored policy because nobody had switched them on.

Every figure was worked out by hand before it ran, from the family's own filed table and rule, and then checked
against ISO live. **ISO agreed on everything it rated, except one engine difference, recorded and not fixed
(OI-115):**
- 20 golden cases across all ten families, every premium on each policy compared;
- 12 zero cases, **50 message cases firing all 95 message rule instances, each matched to the level that raised
  it**, 13 submitted-value probes and the four cyber factors;
- the state rewrites and the edition probes, and **all 46 states: 73 of 73 policies, 2,050 records, 11,003
  premiums**;
- the downstream check: the total moves by exactly the predicted amount ($977; clean test $5,110, predicted
  before the call); terrorism untouched; the blanket roll-up moves only on radioactive; **1,251 stat values on chunk 20 records (sublines, the EB and Food codes) equal on 168 stored ISO responses**.

**No engine change.** Things the rules do that a submitter must know, each found by running and confirmed by ISO:
- **Radioactive Contamination ignores its own limit** unless the building is blanketed and the blanket's
  radioactive option is "No"; otherwise it prices on the parent coverage's limit (and fires "Limit not required").
- **Fungus's per-form charge is 10 × (forms − 1)**; Business Income's fungus period is **overwritten** from the
  policy fungus record.
- **Equipment Breakdown's waiting-period record charges the no-waiting-period factor − 1**; ammonia and hazardous
  substance switch on only **above** $25,000.
- **Tobacco attaches itself** when the occupancy is on the Tobacco Sales Warehouse form; its rate is a band on
  the contents' limit.
- **Mortgageholders' `Limit` is text ("25,000")**; the fungus policy record's period is text; computed fields
  submitted as overrides must carry the XSD's numeric type. ISO refuses the wrong type.
- **Jewelry needs its value indicator**; the "location not valid with CP 00 70" message needs a numbered location.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `200_chunk20_rc2.py --live`, 20 cases on 175_'s Oregon policy (and chunk 9's blanket): **Fire Department** $85 / **$173** through the location's higher limit; **Tobacco** 26 / 53 at the band edges ($23 / $47); **Mortgageholders** at and across every layer ($52 / $104 / $405 / **$606**); **Fungus** $31 / **$25** (10 × (forms − 1)); **special-limit items** with jewelry's base 0 vs 2,500 and stamps' 250; **Radioactive** on the parent's limit, blanket average **$159 / $321** vs own $94 / $383; **Pier / ACP** options 1 and 5; **Food** $17 / $9; **EB** groups 3 and 7, waiting period row − 1. ISO agrees on all 20. Pinned in the regression |
| 2 | Every table's row count stated | ✅ | C20-05 (`199_`): every table each family reads, CW and each state's own: EB premium 195 rows, occupancy group 1,090 (GA KS NY 1,027; FL 0), mortgageholders 85 (TX 0), AK-only mortgage limit 17, Pier / watercraft 6 / 7, fungus period 5, the four base special limits; **24 header-only state tables** named |
| 3 | Every state is enumerated | ✅ | `203_ --all --live` in six batches: **all 46 states**, every family on its own package (the state's rule or its edition's), **ISO 46 of 46**; with the probes 73 of 73, 11,003 premiums. Rewrites: AL / KS / RI plan factor 0.85; FL drops (and never sets) the deductible-by-location factor and ignores the Fire Department higher limit; AZ Fire Department off; VA volunteer fire department and Ordinance-or-Law fungus; NY no cyber factor on Mortgageholders / EB BI; TX Mortgageholders, NC ACP, AK / NY fungus rating steps empty. Puerto Rico excluded by standing rule |
| 4 | Every `0` tested against its consuming branch | ✅ | C20-15 (`201_`, 12 cases): the limit at the base, 0 mortgages, EB BI without the building's EB, items at their base, the 15,000 sub-limit, ammonia at 25,000, pier with no construction, ACP on Broad, Food limits 0: ISO agrees on 10. **The other 2 are OI-115**: a blank Fire Department limit prices **$3 at ISO, $0 ours**; ISO skips a blank first operand of `Subtract` (probe: ISO $17, blank-as-zero −$17, ours $2). Recorded, not fixed; pinned |
| 5 | Every hardcoded literal key listed | ✅ | C20-05: the tobacco form name, the four `Indicator` / higher-limits indicator pairs, jewelry's three value indicators, the six construction options and "Not Applicable", "Bulkheads, Pilings, Piers, Wharves or Docks" / "Retaining Walls", "Policy Limit" / "Separate Limits", the time periods "Eliminated" / "Replaced By 24 Hours", the 25,000 ammonia threshold, the five mortgage layer labels |
| 6 | Shared-name traps diffed | ✅ | C20-04 (hand = engine on four trees and a blanket, all 28 records) and C20-17 (`202_`): rates, factors, `LimitToUse`, `LossCost`, `BaseSpecialLimit` guarded (a submitted value is used); the mortgage layer counts, EB occupancy group and waiting period, the BI fungus period, pier-on-BI's `IncludedInBlkt` and every switch overwritten; Tobacco reads the contents' LCM through; **ACP prices $0 with the building's watercraft exclusion**. ISO agrees on 13 probes |
| 7 | Every exclusion's endorsement record identified | ✅ | C20-18 (`202_`): the four cyber factor names each move a dollar (Fire Department × BGI 0.995, Mortgageholders × its own 0.999, ACP × Special 0.995, EB × 0.999); CP 10 76's COLExcptns factors 0.997 / 0.996 / 0.999, **Mortgageholders unmoved**; the watercraft exclusion zeroes ACP (C20-17). ISO agrees |
| 8 | The edition basis stated | ✅ | C20-21 (`203_`): **every rule** of the 40 family files diffed across the four editions: **6 differences where the census's SetPremium-only check found 1**. The 2023 editions set the Fire Department `LimitToUse` before its base limit, so the higher limit is compared with a blank: **ISO, like ours, reads "50,000 > blank" as true** ($173); MO's pier-on-BI ignores a submitted limit (uses BI's 100,000); MO's fungus excess applies only on "Policy Limit". ISO agrees on all 10 edition probes |
| 9 | No unexplained validation message | ✅ | C20-16 (`201_`): **all 95 message rule instances** (CW, NC, VA, NY, CT, AK, IL, KS, VT) triggered, each checked as a **(level, message) pair** against the node ISO ties it to, and silent where the rule says so. ISO's multiset equals ours on every case |

## What the chunk established, in submission terms

* **Radioactive Contamination** sits on each of the five coverages with a submitted **rate**; unblanketed it
  prices on the coverage's limit (don't send its own), blanketed with the blanket's radioactive option "Yes" on the
  blanket average and the blanketed limit, "No" on its own rate and **its own** limit.
* **Fire Department** needs `FireIncreaseLimitApplyOnPolicyIndicator` "Yes" and a limit above the 1,000 base; the
  location's higher-limits record raises it (not in FL); VA has a volunteer variant; AZ never rates it.
* **The special-limit items** price only the limit above their base (jewelry's depends on the value indicator);
  they need the Special cause and are invalid with the theft exclusion or a non-Special blanket.
* **Mortgageholders** is a policy-level form priced by mortgage-count layers; no locations, no blanket, no TRIA;
  `Limit` is text.
* **Fungus** is a policy record plus BI records that feed it; the period lives on the policy record.
* **Equipment Breakdown** needs its occupancy category and group (keyed with the building's class); the building
  premium is a flat band amount; BI's waiting period comes from BI's no-waiting-period endorsement.
* **They feed the policy total and their own stat codes; terrorism does not read them; the blanket roll-up reads
  only radioactive.**

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-115** (new) | ISO skips a blank first operand of `Subtract`; ours blanks the result (Fire Department with no limit: ISO $3, ours $0). Candidate fix: Property's `Subtract` skips a null as `Product` does, with the full regression | no; needs the user's go |
| Stale engine comment | `cf_engine/config.py` says a comparison with a blank is false; the engine (and ISO, C20-21) read the blank as 0 | no; a comment |
| **OI-103** | ISO-refuses / we-price cases carried from chunks 15-19 | no; chunk 28 |
| Empty-table fallback | The VT question from chunk 19; chunk 20 reads 24 header-only state tables, all falling back as ISO does in every case run | no; chunk 28 |
| Process gaps found | (1) **The census still compares only `SetPremium` across editions**: the every-rule diff (now in `203_`, as `197_` for chunk 19) found 5 more differences; it belongs in the census template. (2) Payload typing: computed fields and two text-typed fields refused by ISO until typed from the XSD; the payload builder should type every field from the XSD, not a hand list. (3) The all-states run exceeded memory in one process; it now runs in batches | no |

## Confirmation

* **Regression CLEAN**, 2026-09-29, scoped as for chunks 18 and 19: **6 of 6, 0 failures** (`104_ --only 199_ 200_ 201_ 202_ 203_ 204_ --no-gl --jobs 2`, 5m46s, `chunk20_c20-24_regression_scoped.log`): `200_` pinned to $85 / $173 / $23 / $606 / $25 / $159 / $321 / $44; `199_`, `201_`-`204_` added (MACHINERY entries may now carry arguments). The full run is carried from 2026-09-28 (115 of 115): **no engine code has changed since** (`ae81ac7`), and no shared test helper changed in chunk 20 except the regression runner itself, which this run exercises
* **`157_ --all`**: carried from 2026-09-28 (293 of 293), run after the last engine change; not rerun: no engine change since
* **`166_`**: 497 of 546 countrywide premium files built (91%), 49 left in 6 families
