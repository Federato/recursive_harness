# Property chunk 22: the gate

**Multi-location: the Value Reporting Form (CP 13 10) with its General Information record, and Additional
Locations Special Coinsurance (CP 13 20) with its General Information and Provisions records, in all 46 states.**
Filed 2026-10-01. **9 of 9, and all 24 tasks done.** Task record: [`CF-CHUNK22-TASKS.md`](CF-CHUNK22-TASKS.md).

**In plain English.** The first chunk whose prices depend on more than one location. Value Reporting lets an
insured report contents values instead of fixing a limit; its General Information record also prices incidental and
newly acquired locations. Additional Locations Special Coinsurance prices extra locations at an average rate built
from all of them. **None of the 16 premium records had ever been priced by ISO, and no stored policy had more
than one location**, so every case was a new live probe.

Every figure was worked out by hand before it ran, from the records' own filed rules and tables (215_'s hand model,
174_'s independent SetPremium evaluator, and the engine all agreeing first), then checked against ISO live.
**ISO agreed on everything it rated.** The one thing it would not rate, it refuses for the same reason we do:
- **OI-119**: a Value Reporting policy with multiple-location average rates **"Used" is unpriceable at ISO**. The rule
  that finds the largest contents limit reads its own running value before binding it; ISO answers *"No value found
  in Params (FromParam=maxLimit)"* and so does our engine. Every countrywide edition 2019-2026 carries the rule; no
  state rewrites it. **No engine change** (the user's go was given and not needed).

The counts: RC-1 (`213_`, no ISO); RC-2 9 golden cases (8 priced + the "Used" refusal), 2,308 premiums; RC-3 45
zero / message / shared-name / exclusion cases, 11,977 premiums; RC-4 22 state, edition and scale cases plus **all 46
states**; RC-5 four before / after pairs (8 policies, 2,006 premiums) and 582 stat values on 120 stored responses.
**Every premium and every (level, message) ISO returned equals ours, on every case ISO rated.**

**Things the rules do that a submitter must know**, each found by running and confirmed by ISO:
- **Either form switches the contents' ordinary premium off** and carries it instead, and **forces the contents'
  coinsurance factor to the 100% row** (0.90), whatever coinsurance is entered: the contents' terrorism moves with it.
- **The Value Reporting Form survives only on the five reporting coinsurance values** (Daily ... Policy Year Reporting,
  on the contents or their blanket); on anything else it is removed.
- **On "Not Used", each location prices at its own final rate on 0.75 x its limit** (`NewBusnFactor` applies to every
  non-seasonal risk: the rule tests only `SeasonalRisk`); a seasonal location prices on 0.3 x its limit. Blanketed
  rows use the blanket average rate on 0.75 x the blanket limit x their share of full value.
- **One average rate per policy**: every VR Form row copies General Information [1]'s five MLARs, and a submitted MLAR
  is overwritten. The Additional Locations MLARs follow the rule as written (full value x rate, not / 100; Group II
  omits the incidental part), and **ISO rounds each full value x rate before averaging** ($3,589 on 8 locations, not
  $3,610).
- **The Additional Locations roll-up moves no dollar**: it sums a Provisions `Premium` no rule writes, and no in-force
  edition reads the result (`PrsnlPropPremium` 0 at ISO).
- **The VR Form's Broad record applies the plain cyber factor twice** (ISO too: $130 not $131) and never reads the
  ensuing-causes factor.
- **Incidental locations are always charged; acquired locations only above 50,000** (exactly 50,000: $0).
- Payload typing: `AvgVal`, `SpecificIns`, the incidental / acquired limits, `OverallLimit`, `FullValue`,
  `FullPrsnlPropValue` and `TerrorismSubLimit` are numbers; **a blank number must be left out**, not sent empty.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `215_chunk22_rc2.py --live`, two locations (contents 100,000 / 500,000) on 175_'s Oregon policy: **VR "Not Used"** Group I $146 / $565, Group II $16 / $53, Special $85 / $247, General Information $183 (V1); Broad $12 / $33 and EQ $3 / $15 (V2); **blanketed** $120 / $597 beside an own-rate $261 (B1); **General Information** $481 (acquired 60,000) / $189 (exactly 50,000) / seasonal $261 (G1-G3); **Additional Locations** Provisions $348 / $174 and General Information $17 / $2 / $9 at 90% (A1), three locations at 100% with EQ (A2). **ISO 8 of 8**, 2,308 premiums, every message; **"Used" refused at ISO and ours** (U1, OI-119) |
| 2 | Every table's row count stated | ✅ | C22-06 (`213_`): `ValRptgIncLocsRate` 4 (Basic 0.891, Broad 0.026, Special 1.187, Earthquake 0.056), `ValRptgAcqrdLocsRate` 1 (0.528), `NewBusnFactor` 1 (0.75), `SeasonalRiskFactor` 1 (0.3), `AddlLocSpclCoinsFactor` 1 (1.05), `CoinsuranceFactor` CW 3 (FL 4), the three indivisible sublines 1 each, the peril-exclusion stat codes 8 / 16 (AR DC 4 / 8). **Identical in all 46 states.** Two header-only siblings (`ValRptgFormNewBusnFactor`, `ValRptgSeasonalRiskFactor`) no rule reads; the VR Form's own `CoinsuranceFactor` is written and never read |
| 3 | Every state is enumerated | ✅ | C22-19 (`217_ --live --states`, 6 batches): **all 46 states**, both forms on one two-location policy, 16 records each predicted by hand: **ISO 46 of 46**, every premium (265-301 per policy) and (level, message). FL needs 208_'s no-earthquake recipe (OI-103 otherwise) |
| 4 | Every `0` tested against its consuming branch | ✅ | C22-13 (`216_` Z1-Z10, all agree): VR Form with no General Information prices at its own rate (message, not $0); a contents indicator submitted "Used" on one row prices that row **$0** (the GI's MLAR, 0 on "Not Used"); Estimated / blank Average Value move nothing on "Not Used"; AL General Information alone prices on the incidental limit; AL with blanket or Agreed Value still prices (message only); **Provisions with no General Information $0**; VR GI with no surviving VR Form prices its incidental part; **OverallLimit 0 zeroes the Provisions** |
| 5 | Every hardcoded literal key listed | ✅ | C22-06: every literal key the rules pass ("Basic" / "Broad" / "Special" / "Earthquake", "Y", "100%", the indivisible-subline "Y", the peril-exclusion Yes / No tuples) has a row in every state. Switch literals: `MultiLocAvgRates` "Used" / "Not Used" (the domain's two values); the five reporting coinsurance values (exactly the domain's); "90%" for the AL factor; "Yes, Not Included in Blanket" / "Yes, Included in Blanket" for EQ |
| 6 | Shared-name traps diffed | ✅ | C22-02 / C22-15: the five MLARs have three writers on three different records (VR GI, each VR Form row, AL GI), traced in write order on the engine; a submitted MLAR is overwritten on all three; submitted AL `CoinsuranceFactor` (S1), VR GI `TotalIncLocsLimit` (S2, $915 vs $183) and the contents' `LimitToUse` (S3) **survive** (IsNull guards); the policy `MultiLocAvgRates` and the contents' indicator are set independently. **ISO agrees 4 of 4** |
| 7 | Every exclusion's endorsement record identified | ✅ | C22-16 / C22-17: the cyber exclusion moves every chunk 22 record at large limits, **the VR Broad record reading its plain factor twice** (ISO $130); the contents' wind / hail exclusion sets the VR GI indicator and peril stat code (34 / 36); **AL reads its own record** (`WindstormOrHailExclusionDirectDamagePrsnlProp`), **AR DC NY RI hard-set "No"**: ISO agrees on every stat field |
| 8 | The edition basis stated | ✅ | C22-18 (`217_` E1-E9): every rule of the 19 family files and the parent rules naming them, across the four editions: **MO 2023 V02** 29 + 16, **CA / NC V03** 4 + 13, **V04** 0 + 3, each judged and probed. V02's "Not Used" equals 2026's; V02 refuses "Used" too; **V02 removes a blanketed VR Form whose contents sit at 90%** (it reads `BlktCoinsuranceValue` before setting it); V02 / V03 rename the terrorism sub-limit message ("Sub Limit cannot exceed the coverage's limit", with an AL full-value variant). **ISO agrees on all** |
| 9 | No unexplained validation message | ✅ | C22-14 (`216_` M1-M23) + C22-17: **33 of the 40 in-scope messages fired at their own level** and each was checked silent where it should be (OR vs KS on the SPP form; CP 13 30 with / without CP 13 10; the EQ 80% rule with / without the VR Form). The other 7: 4 can fire only on a "Used" policy, which ISO refuses (OI-119); 3 shared ones were tested in earlier chunks. **ISO's (level, message) multiset equals ours on every case** |

## What the chunk established, in submission terms

* **Value Reporting**: the General Information record at policy level (`MultiLocAvgRates`, the incidental and
  acquired limits, `CauseOfLoss`, `EQCauseOfLoss`); a VR Form under each contents row (`AvgVal`, `SpecificIns`,
  `SeasonalRisk`) with the contents on a reporting coinsurance value; its five coverage records are created by the
  form. Send "Not Used": "Used" is refused (OI-119).
* **Additional Locations**: the General Information record at policy level (`Coinsurance` 90% / 100%,
  `OverallLimit`, the incidental limits, `CauseOfLoss`, `EQCovIndicator`); a Provisions record under each contents
  row with its `FullValue` (not below the contents' limit). The forms are mutually exclusive (a message; both price
  if it is ignored).
* **Downstream** (C22-21): the policy total moves by the chunk 22 premiums **minus** the contents premiums they
  switch off, **plus** the contents' terrorism change: +$38 / -$622 (and +$1,991 / -$3,878 at 10 x), predicted
  before each call and equal at ISO; every other premium unchanged; no terrorism field on a chunk 22 record; 582 stat
  values equal on 120 stored responses.

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-119** | "Used" is unpriceable at ISO (self-referencing `maxLimit`, every CW edition); ours refuses identically. Next: report to ISO; a business decision on whether "Used" is offered | no; engine agrees |
| **OI-118** | The VR Form's label reads "Value Not Found" on OR (a state `Pages` table hides CW rows). Labels only | no; carried |
| **OI-103** | Florida's portable policy needs its earthquake inputs dropped (ISO refuses an unfiled EQ class where we rate) | no; chunk 28 |
| Process gaps found | (1) **The census's multi-location trail looked only for the MLAR fields**, so it missed the built rules that test for the forms themselves: PP `SetCoinsuranceFactor` (forced 100% row), `SetLimitToUse` and `SetTerrorismLimitToUse` (terrorism on 0.75 x Limit). The trail check should list every built rule that tests `Exist(...ValueReportingForm / ...Provisions)`, not only the fields named. (2) **Payload types were found by ISO refusals** (3 rounds): the RC-1 tables task should read each new record's xs:int / xs:decimal fields from the XSD into `r11.NUMERIC` up front, and the payload builder should drop blanks. (3) **Message checks matched by substring**, so one message's text inside another's gave a false "unexpected"; the checker should match whole messages | no |

## Confirmation

* **Regression, scaled back (user, 2026-10-01):** the engine is unchanged since the chunk 21 gate (`git diff
  5a35c1f HEAD -- cf_engine gl_engine` empty), so the 2026-09-30 full gate run (140 scripts) carries. Run at this
  gate: **`206_ --check` CLEAN** (1,259 stored requests, 890,791 fields, nothing moved; baseline refreshed with the 132
  new chunk 22 requests); **`157_ --all`** 293 of 293 stored ISO policies equal on every premium (14,236) and on the
  total; the five chunk 22 entries through `104_` (`--only 213 215 216 217 218`): **CLEAN, 5 of 5** (2m50s), `215_`
  pinned to 146 / 565 / 247 / 183 / 481 / 189 / 597 / 348 / 174 / 267, `213_`, `216_`, `217_` (sampled), `218_` added as
  machinery
* **`166_`**: **520 of 546 countrywide premium files built (95%)**, 26 left in 2 families
