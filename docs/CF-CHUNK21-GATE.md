# Property chunk 21: the gate

**Sewer backup and the condo unit-owners options: Discharge From Sewer, Drain Or Sump (CP 10 38) on its five
parents, the unit-owners optional coverages (loss assessment and miscellaneous real property, CP 04 18 and the
RI / FL / UT state forms), and Florida's Commercial Units in Residential Condominiums (CP 01 54 / CP 17 96),
in all 46 states.** Filed 2026-09-30. **9 of 9, and all 21 tasks done.**
Task record: [`CF-CHUNK21-TASKS.md`](CF-CHUNK21-TASKS.md).

**In plain English.** Water backing up through sewers and drains, on the building, the contents, special
class property and both kinds of business income; what a commercial condo unit owner can add (their share of
an association's bill, and the bits of the building they own); and Florida's own version for shops in
residential condo buildings. **None of the 12 premium records had ever been priced by ISO.**

Every figure was worked out by hand before it ran, from the record's own filed rule and table (state-aware:
the state's table when it files one with rows, else its countrywide edition's), then checked against ISO
live. **ISO agreed on everything it rated, except three new open items, none of them a premium the engine
computes wrongly on a valid submission:**
- **OI-116**: ISO never attaches Florida's SPP special-class condo record; ours prices its manual premium.
- **OI-117**: a blank text manual premium makes ISO refuse at `Convert`; ours prices $1.
- **OI-118**: form names / numbers only: a state's own `Pages` table hides the countrywide rows in ours.

The counts: RC-1 107 checks (hand = engine on 66 cases); 26 golden cases; 50 zero and message cases; 15 shared-
name and stat-code cases; 61 state, edition and all-46-states policies; the downstream set and 1,648 stat values.
**Every premium and every message ISO returned equals ours, on every case ISO rated.**

**No engine change.** Things the rules do that a submitter must know, each found by running and confirmed by ISO:
- **Sewer has no on-switch: its own limit is the switch.** A sewer record sent with a blank limit still prices
  (**$1** at ISO too: the blank limit is skipped in the product).
- **Personal Property sewer has no deductible of its own: it borrows the Building sewer record's factor**, else 1.
- **The No Waiting Period endorsement zeroes sewer business income** (the rule multiplies by BaseFactor − 1).
- **`LossAssessmentLimit` is a list value** ("1,000" / "5,000" / "10,000" / "Over 10,000" + the amount); "10000"
  prices $0. **A blank loss assessment deductible zeroes it** (misc. real property's blank deductible is 1).
- **The options container creates its loss assessment record whether sent or not, and it switches on unless its
  limit is exactly "0": misc. real property alone must send loss assessment "0"**, or ISO refuses (OI-103).
- **The contents' `CovForm` is always copied from the occupancy**; a contents CovForm sent alone is overwritten.
- **Florida never prices sewer** (its parents never call the records, its tables are empty stubs); **Florida's
  loss assessment has no sub-limit**; **AL / KS / RI price misc. real property with the public institutional plan
  factor and no deductible**; **KS / NY loss assessment use an SPP's own cause of loss**.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `208_chunk21_rc2.py --live`, 26 cases on 175_'s Oregon policy and the portable FL policy: **sewer** all five at 25,000 $167 / $167 / $164 / $17 / $17, deductible 250 / 5,000 $186 / $186 / $130, PP alone **$170**, the limits case $332 / $68 / $197 / $69 / $28, No Waiting Period **$0** on BI; **loss assessment** every tier, band and cause ($3 … $26) and ISO's own edges (12,000 priced, 17,500 $0 with its message, sub-limit 11,500 ignored, 5,500 accepted); **misc. real property** $93 / $223 / $102 / $196; **FL** $98 / **$244** (one rounding) / $171 / $98 / $0. **ISO agrees 25 of 26**; FC5 is OI-116. Predicted by the hand models = the SetPremium evaluator = the engine |
| 2 | Every table's row count stated | ✅ | C21-05 (`207_`): sewer's 6 CW tables (1 prices: `DischargeFromSewerDrainOrSump` 2 rows, PD 0.77 / BI 0.07; 5 code tables of 1 row); `LossAssessmentRate` 15, `LossAssessmentSubLimitRate` 9, `LossAssessmentLimitConverted` 4, `MiscRealPropRate` 1, `Deductible250Factor` 4, `DeductibleFactor` CW 240 (most states 462, FL 240), the peril-exclusion stat codes 8 / 16 (AR DC 4 / 8), the public institutional plan factor (AL KS RI 1). **FL files 7 empty stubs** (the 6 sewer tables and the sub-limit rate) |
| 3 | Every state is enumerated | ✅ | C21-17 (`211_ --live`): **all 46 states**, the five sewer records + loss assessment + misc. real property on each state's own package, predicted per state: **ISO 46 of 46**, every premium (120-141 per policy) and message; with the rewrite, FL and edition probes **61 of 61**. CA NY sewer 158 (own deductible tables); FL sewer unpriced, loss assessment 6; AL KS RI misc. real property 93 |
| 4 | Every `0` tested against its consuming branch | ✅ | C21-10 (`209_`, 11 cases): sewer limit blank ($1 at ISO too) / 0 / at the parent's limit; loss assessment "0"; a sub-limit with no limit; the FL records on the wrong form, on an SPP, with a blank manual premium: **ISO agrees on 9; the other 2 refuse as predicted**: neither limit (OI-103) and the blank text manual premium (**OI-117**) |
| 5 | Every hardcoded literal key listed | ✅ | C21-05: every literal and caller-passed key in every in-force package has a row (0 problems): "PD" / "BI", "Other Cause Of Loss", "All Other", "250" / "Not Applicable", the tier strings and "Over 10,000", "Upto5000" / "From6000To10000" / "Over10000", misc. real property's "Y", the peril-exclusion Yes / No keys; the dropdown values of `LossAssessmentLimit` all keyed ("Over 10,000" guarded out of the converted-limit lookup). The switch literals: "Commercial Property Policy" / "Standard Property Policy", "Condominium Commercial Unit Owners Coverage", "Condominium Association", class codes 0331-0343 |
| 6 | Shared-name traps diffed | ✅ | C21-12 (`210_`): every write in the chunk's files is IsNull-guarded (a submitted rate / factor stands); `ManualPremium`, `CovType`, `PolicyType` and the occupancy's `CovForm` are inputs; the contents' `CovForm` is copied unconditionally; parents' `LimitToUse` guarded. `Rate` and `DeductibleFactor` mean different things on each record (C21-03). **ISO agrees 6 of 6** with submitted values standing ($215, $49, $3, $176, the cap at 50,000, the special class band) |
| 7 | Every exclusion's endorsement record identified | ✅ | C21-13 (`210_`): no chunk rule file in any package mentions cyber. The options container's peril-exclusion stat code from its four exclusion indicators: **ISO agrees 8 of 8** (OR Special 36 / 34, Broad 08 / 07; AL's own record; AR ignores the wind / hail record; DC). AR with wind / hail "Yes" submitted: its table replaces CW's and ISO refuses, as predicted |
| 8 | The edition basis stated | ✅ | C21-16: **every rule** of the 8 family files across the four editions: **0 differences**. The same diff on the parent files found one: **MO (2023 V02) tests the parent's `Limit`, not `LimitToUse`, in four of the five sewer caps** (ISO agrees 3 of 3: MO silent, MO special class fires, OR fires). The every-rule diff is now `_edition_rules.py`, run by the censuses for chunks 22-26 |
| 9 | No unexplained validation message | ✅ | C21-11 (`209_`): **all 24 of the chunk's own messages** (the census's other 2 are Green Upgrades' wording) triggered and silent, 39 cases: the five sewer caps (100,001 / 100,000), the three loss assessment checks one either side, CW / RI / FL / UT "requires either" and "only valid", FL's six CP 01 54, GA's two CP 17 01: **ISO's message set equals ours on every case** |

## What the chunk established, in submission terms

* **Sewer** (`DischargeFromSewerDrainOrSumpNotFloodReltd*`) sits under each of the five coverages with
  `DischargeLimitPD` / `DischargeLimitBI` (xs:int); its limit is the only switch; it must not exceed the parent's
  `LimitToUse` (the parent's `Limit` in MO) or a message fires. Not rated in Florida.
* **The unit-owners options** are one container under the contents (`LossAssessmentLimit` from the list, the
  "Over 10,000" amount, the sub-limit, `LossAssessmentDeductible`, `MiscRealPropLimit`); both coverage records are
  created by the container. Send loss assessment "0" when it is not wanted.
* **Florida's condo records** carry a manual premium (text on the CPP special-class record); the CPP records price
  only on the unit-owners form / Condominium Association and a Commercial Property Policy; the SPP records are
  ISO's auto-attach forms.
* **They feed the policy total and their own stat codes (sewer sublines and codes, the container's exclusion
  indicators and peril-exclusion code, the exposure amount); terrorism does not read them** (C21-18: +$651 /
  +$6,405 exactly, 1,648 stat values equal on 153 stored responses).

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-116** | ISO never attaches FL's SPP special-class condo record (CP 17 96); ours prices it. Unexplained: the test's three inputs are sent; probes with Yes / Y / YES; no STC payload has an SPP case. Next: ask ISO | no; pinned as a known difference |
| **OI-117** | `Convert` of a blank string to a number: ISO refuses, ours reads blank and prices ($1 on FL's CPP special class). Engine change: needs the user's go; census every blank-able `Convert` first | no; pinned |
| **OI-118** | A state's `Pages` table replaces CW's in ours, so CW form names / numbers read "Value Not Found"; ISO reads the CW rows (unlike rate tables). Labels only, never a premium; add form numbers to the snapshot once fixed | no; pinned |
| **OI-103** | Three more cases where ISO refuses and we rate: the options container with a blank loss assessment limit (MRZ, Z7), and AR's stat-code table replacing CW's (T8) | no; chunk 28 |
| Process gaps found | (1) **Payloads for other states:** `r11.payload` writes Oregon's State and product; non-Oregon requests must be re-keyed (`208_`'s `payload(sub, j)`), or a Florida policy is priced on Oregon's scheme (it refused here). (2) **The portable policy outside Oregon** needs a state's own special class (FL), no EQ class it doesn't file (FL), and its own `EQTerr` kept (SC's BCEG factor keys on it even without earthquake). (3) **Form numbers were never compared** before C21-17: OI-118 hid in every earlier chunk; the snapshot check should carry them. (4) **Every-rule edition diffs must include the parent files** that hold a chunk's messages (MO's caps) — noted in chunks 22-26 | no |

## Confirmation

* **Regression CLEAN**, 2026-09-30, the full gate run: **140 scripts, full grids** (`104_ --gate --jobs 4`, 19m20s,
  `results/cf-raas/logs/c21_gate_regression.log`); `208_` pinned to 167 / 164 / 17 / 170 / 332 / 68 / 197 / 69 / 28 /
  26 / 223 / 244 / 293; `207_`, `209_`-`212_` added as machinery
* **Snapshot `206_ --check` CLEAN** (1,127 stored requests, 704,869 fields); baseline refreshed with the 157 new
  chunk 21 requests
* **`157_ --all`**: 293 of 293 stored ISO policies equal on every premium (14,236) and on the policy total
* **`166_`**: 504 of 546 countrywide premium files built (92%), 42 left in 4 families
