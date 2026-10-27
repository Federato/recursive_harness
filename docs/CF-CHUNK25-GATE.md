# Property chunk 25: the gate

**Flood: the Flood Coverage Endorsement (CP 10 65; WV CP 10 68) on building, contents, special class, business income
and special class business income, the flood blanket, and WV's two Ordinance or Law flood forms.** Filed 2026-10-02.
**9 of 9, and all 26 tasks done.** Task record: [`CF-CHUNK25-TASKS.md`](CF-CHUNK25-TASKS.md). **With it, 546 of 546
countrywide premium files are built (100%) and the state-only list is closed.**

**In plain English.** Flood is priced like the flood market prices it: a loss cost by state (or county) keyed by flood zone
and construction, times **one** rate-modification table picked by the deductible (read by insurance-to-value and the
location's total property value, interpolated inside each ITV band), times a community-rating credit. Cover in excess of the
federal NFIP maximum uses tables 6 / 7 on the record's own full value. Business income uses the building's loss cost times its
business income factor. Several risks can share a flood blanket with its own average rate. **ISO had priced 3 of the 8
premium records, all on one stored Alaska policy**, and Alaska (like Florida) does not rate flood at all: the company enters
the premium. Every countrywide figure in this chunk was a new live probe.

Every figure was worked out before it ran: `229_`'s hand models from the filed tables and rule text (state rows else
countrywide; the county states' county / all-other tables; MO's 2023 V02 rules), checked against 174_'s independent evaluator
and the engine on **every intermediate value**, not only the premium; where a state rewrites `SetPremium` (NY, AK, FL), the
evaluator on the state's own rule. **ISO agreed on every premium of every case it rated** (22 golden, 41 zero / message /
name / exclusion, 75 state / edition / WV / Off-Premises, 10 downstream). **No engine change.**

**Things the rules do that a submitter must know**, each found by running and confirmed by ISO:
- Flood needs `FloodCovIndicator` "Yes" on the location and a **Flood Coverage General Information** record (deductible,
  `FloodZone`, optional `CommunityRatingSystemCRSGrade`); without the record every flood record prices $0.
- **The deductible picks the table** (500 / 1,000 → 1 … 1,000,000 → 7); floor of interest and number of stories feed
  statistics only. ITV above 100% prices $0 (a limit $1 over the value rounds to 100% and still prices). Tables 5–7 file
  factor 0 where the deductible nears the value.
- **Excess over NFIP** prices only at deductibles 750,000 / 1,000,000 and only above the 500,000 NFIP maximum; a blank
  excess indicator prices $0.
- **Special Class and SCBI read the construction on their own flood record** (blank → $0); contents read the building's.
- **In a blanket, contents and Special Class take the blanket detail's deductible; the building keeps the location's.**
  Members price $0; the detail prices at the average of members' full value × flood rate.
- AK and FL: `ManualPremium` on each record (× package mod × IRPM); AK's blanket detail has no premium rule.
- WV: CP 10 68; its O&L flood forms price `ManualPremium` × package × the building's MPDC × IRPM when the O&L record's
  `FloodOnlyLimitation` is "Yes"; `FloodOnlyLimitationOnOrdinanceOrLaw` "Yes" zeroes O&L Coverage A.
- Submitted base rate, record deductible, modification / aggregate / CRS / BI / type-of-risk factors and blanket average rate
  survive; total property value, ITV % to use and excess-to-use are recomputed.
- Payload: limits, full values, `AnnualNetIncome`, `BlanketIDNum` are numbers; building construction uses the long names
  ("Joisted Masonry - Reinforced"); Extra Expense Only needs `ExtraExpenseLimitOnLossPayment`.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `230_chunk25_rc2.py --live`, 22 cases, **ISO 22 of 22**, every premium and message: all seven rate-modification tables each deciding a building dollar ($36 at 500 … $5,758 at 100,000), zones A / X / X500 / D, CRS on / off ($493 / $616), contents $799 / $643, special class $460, BI $343 / $403 / $716, SCBI $286 / $1,059, blankets $1,273 / $1,731 / $1,952 / $7,644, excess $7,644 / $8,534 |
| 2 | Every table's row count stated | ✅ | C25-07 (`229_`): all 27 tables listed with CW and state row counts; CW `FloodLossCost` header-only, 37 states file it; each rate-modification table holds exactly the deductibles the rule sends it, ITV bands contiguous; AK FL file their own copies |
| 3 | Every state is enumerated | ✅ | C25-18 / 19 / 21 (`232_ --live`): **all 46 states agree with ISO** on a two-location flood policy with a blanket (every premium); the 7 county states on a listed and an all-other county; NY's six rewrites; AK / FL manual premiums (and $0 blank) |
| 4 | Every `0` tested against its consuming branch | ✅ | C25-14 (`231_` Z1–Z10): deductible ≥ value (filed 0), limit over value, no General Information, flood on with no record, one-risk blanket, blank zone, floor / stories, Builders Risk, No Coverage, blank `IncludedInBlkt`; plus RC-1's six blank inputs |
| 5 | Every hardcoded literal key listed | ✅ | C25-07: `Y` (annual aggregate), `Building` / `Content` (NFIP maximum), `Building` / `Contents` (loss cost rows), the type-of-risk names, `Flood Coverage` (Off-Premises), `500,000` (MO's excess row): each has a row |
| 6 | Shared-name traps diffed | ✅ | C25-03 / C25-16: `FloodAdjustedRate` per record; `BlanketAverageRate` (flood detail) vs chunk 9's; `FloodTotalPropertyValue` (location, unblanketed only) vs each record's `TotalPropertyValue`; `OperationalUnitFloodBaseRate` / `HighestBusnIncomeFloodBaseRate` (OI-122); nine submitted values survive, three are overwritten; ISO agrees |
| 7 | Every exclusion's endorsement record identified | ✅ | C25-17 (`231_` X1–X4): CP 10 75 → `CyberIncidentExclusionFactorFlood`, CP 10 76 → the COL flood and BI flood factors (0.999), BI's `…FloodToUse` (extra expense only copies the EE factor); every flood premium and the blanket move; ISO agrees |
| 8 | The edition basis stated | ✅ | C25-21: the every-rule diff of the 8 family files read rule by rule; **MO's CW 2023 V02** excess factor (table 6 at 500,000 whatever the deductible), blanket contents deductible (location's) and per-location blanket total probed against the 2026 reading in dollars (EX / ED / ET): **ISO follows V02**; NC (V03) and IL (V04) price as 2026; the remaining V02 / V03 differences touch only multi-detail blankets, EE-only blanket members or messages (stated, not exercised) |
| 9 | No unexplained validation message | ✅ | C25-15 (`231_`, 25 message cases): **all 45 countrywide flood message rule instances fired at their own level** and silent at each boundary; WV's CP 10 68 versions in C25-20; ISO's (level, message) multiset equals ours everywhere except MO's extra location message, **explained: OI-123** (an empty `NotExist` in ISO's MO build) |

## What the chunk established, in submission terms

* **Location**: `FloodCovIndicator` "Yes" and the General Information record (`Deductible`, `FloodZone`, optional CRS grade,
  `FloodEffDate`); the county states read the location's `County` (VA also `City`).
* **Each flood record** under its coverage: `Limit`, `IncludedInBlkt` ("No" or "Yes" + `BlanketIDNum`),
  `ExcessOverMaxNFIPIndicator`, optional `AnnualAggregateLimit`; Special Class / SCBI also `ConstructionType`; BI in a
  blanket `AnnualNetIncome`; AK / FL `ManualPremium`.
* **Blanket**: `FloodCovEndtBlktIndicator` "Yes" at the policy, a detail per blanket (`UnitNumber`, `Limit`, `Deductible`,
  the coverage flags, `ExcessOverMaxNFIPIndicator`, optional `AggLimit`).
* **Downstream** (C25-23, `233_`): the policy total moves by exactly the flood premiums, **+$3,521 (OR) / +$3,277 (limits
  halved) / +$10,522 (NY) / +$3,116 (AK) / +$22,828 (MO)**, predicted before each call and equal at ISO; every other premium,
  terrorism included, unchanged; the flood stat values equal.
* **Gate checks** (C25-24, no engine change in the chunk): `206_ --check` **SNAPSHOT CLEAN** (1,609 stored ISO requests,
  1,200,103 fields, nothing moved); `157_ --all` **293 of 293** premiums and totals equal to ISO; the chunk 25 scripts
  registered in `104_` and clean (230_ pinned: 493, 616, 36, 5758, 799, 643, 460, 343, 403, 286, 716, 1059, 531, 1273, 1731,
  1952, 7644, 8534; 229_, 231_, 232_, 233_ as machinery).
* **Census** (C25-25): **546 of 546** countrywide premium files built (100%), 0 remaining; `904_`'s ownership list has no
  unassigned file and chunk 25's two WV files are built; the state-only list is closed.
* **Closed on the way**: chunk 17's Off-Premises flood factor (1.02 with a BI flood record, C25-22, ISO live in six states).

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-122** | The operational-unit "highest" BI flood base rate never stores its maximum (BI $0, or the last building's rate); **ISO does the same**, so it stays as an ISO defect, no engine change | no |
| **OI-123** | MO's (CW 2023 V02) package has five empty `NotExist` tests; ISO reads them as true and raises *"When Flood Coverage applies form CP 10 65 needs to be attached to at least one risk"* on every MO flood location; ours does not. Messages only; one GA message has the same pattern. Engine change needs the user's go | no |
| Not exercised | V02 / V03 rule differences that need two blanket details, EE-only blanket members, or a submitted value on a non-matching blanket member | no |
