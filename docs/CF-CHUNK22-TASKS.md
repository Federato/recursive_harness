# Property chunk 22: task list and status

**Multi-location: the Value Reporting Form and Additional Locations Special
Coinsurance. This is the first chunk whose prices depend on more than one location.**
Tasks set 2026-09-28; chunk 18 is being built in the other terminal, and chunks 19–21 wait.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 22, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`903_chunk22_census.py`](../scripts/cf/903_chunk22_census.py), run 2026-09-28,
3 s, log `results/cf-raas/logs/chunk22_census.log`). It runs the same checks as `902_` (messages in
every rule file, `SetPremium` per in-force edition, form numbers from `Form Pages`, sibling
names). It adds a tenth for this chunk: **the multi-location trail**, meaning every rule file,
countrywide and in the 46 states, that writes or reads a multi-location average-rate field or
runs the additional-locations roll-up.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`.

**Regression, scaled back (user, 2026-10-01: "it takes way too long").** After an RC: **no regression run** unless
`cf_engine` / `gl_engine` changed since the last clean run (`git diff --stat <last clean> HEAD -- cf_engine gl_engine`
empty means the last result carries); the RC's own script is the check. After an engine change: `206_snapshot_regression.py
--check` (~2.5 min, every stored ISO payload) plus the scripts that exercise the changed node. At the gate: `206_ --check`
and `157_ --all` (~5 min); the full `104_ --gate` (~20 min) only if the engine changed during the chunk.

**Order.** After chunk 21. It reads chunk 9's blanket average rates and every coverage's
finished rate (chunks 1–8, 10), and it runs rules in the **main ruleset, which is already built**
(see point 3 below). **No stored ISO policy has more than one location**, so every golden case is a
new live probe.

**Status: GATED 2026-10-01, 9 of 9, 24 of 24** ([`CF-CHUNK22-GATE.md`](CF-CHUNK22-GATE.md)): ISO agrees on everything it rated; "Used" is unpriceable at ISO and ours (OI-119); no engine change; 520 of 546 built (95%). (RC-4 done 2026-10-01, `217_chunk22_rc4.py --live`: 22 state / edition / scale cases + all 46 states ALL AGREE with ISO; no engine change, no regression run). RC-3 done 2026-10-01, `216_chunk22_rc3.py --live`, 4m09s: 45 cases ALL AGREE with ISO, 11,977 premiums field for field, every (level, message) multiset equal; no engine change, no regression run). RC-2 done 2026-10-01, `215_chunk22_rc2.py --live`: 8 priced cases ALL AGREE with ISO, 2,308 premiums field for field, every message equal, plus the predicted "Used" refusal; no engine change, so no regression run). RC-1 done 2026-10-01, `213_chunk22_rc1.py`, all checks pass, 1m47s, no ISO calls).** **OI-119 settled live 2026-10-01 (`214_oi119_probe.py`): ISO refuses every "Used" policy with the same error our engine raises; no engine change.** C22-08 and the MLAR half of C22-09 become refusal cases. Next: chunk 23.

**RC-1 findings (2026-10-01), in plain English first:**

1. **OI-119: "Used" cannot be priced, at ISO or in our engine.** The rule that finds the largest contents limit reads its own running
   value before it exists. ISO refuses with *"No value found in Params (FromParam=maxLimit)"* (probe 2026-10-01); every CW edition has
   the rule and no state rewrites it. Our engine raises the same way. The arithmetic under the readings is kept in `213_` in case ISO fixes it.
2. **Order of writes (C22-02):** contents indicator (copied from the GI's raw input, at InitializeChildRisks) → policy `MultiLocAvgRates` →
   GI `MLARLimit` (before any rate exists) → every contents final rate → GI MLARs → each VR Form row's MLARs → the VR premiums.
3. **One average rate per policy, not per location.** Each VR Form row copies GeneralInformation[1]'s five MLARs unconditionally; a
   submitted MLAR on either record is overwritten. The one override that survives is the GI's `Final…RateTimesValue` (IsNull-guarded).
4. **The average is diluted:** MLARLimit is the LARGER of the reported total and the "max" limit, so one big contents limit pulls
   the average down. Additional Locations' MLAR divides by incidental limit + full values, and its Group II numerator omits the incidental part.
5. **Additional Locations' General Information runs 1 + (contents rows with Provisions) times** per rating (Personal Property re-runs it);
   the totals are IsNull-guarded so the MLARs never change. The two forms keep separate MLARs; with the message ignored BOTH price (a double charge).
6. **The roll-up moves no dollar (C22-03):** nothing in any of the 8 CW editions writes the Provisions record's own `Premium`, so
   `ErcResetPrsnlPropPremium` sums nothing and writes `PrsnlPropPremium` 0, and no in-force edition reads `PrsnlPropPremium`. C22-12 reduces to one field check.
7. **Attach (C22-04):** the VR Form stays only on the five reporting coinsurance values (else it is REMOVED); either form switches the
   ordinary contents premium off. `NewBusnFactor` 0.75 applies to every non-seasonal reporting risk (the rule tests only `SeasonalRisk`).
   A blank GI value does not zero anything (contents fall to "Not Used"); a non-domain contents indicator does.
8. **Tables (C22-06):** every literal key has a row in all 46 states; no state files the five chunk tables; the VR Form's `CoinsuranceFactor`
   is written and never read; `ValRptgFormNewBusnFactor` / `ValRptgSeasonalRiskFactor` are header-only siblings no rule reads; the VR
   form label reads "Value Not Found" on OR (OI-118).
9. **The policy-level `MultiLocAvgRates` and the contents indicator are set independently:** a submitted policy "Used" with no GI survives
   and diverges from the contents ("Not Used"), which the premiums read. The 9 state Personal Property rewrites leave the indicator rule alone.

**Carried from chunk 21 (2026-09-30): the census `903_` now diffs EVERY rule of the family files across the four countrywide editions** (`scripts/cf/_edition_rules.py`, chunk 20's gate item): 19 family files: MO V02 29, V03 4, V04 0 rule differences from 2026 V01. The editions task must judge each one; the census's earlier "identical in all four editions" was a SetPremium-only check. Chunk 21 also found its own edition difference in a PARENT file (MO's sewer caps read `Limit`, not `LimitToUse`): diff the parent files' rules that name this chunk's records too.

---

## In plain English first

- **Value Reporting Form** (CP 13 10): instead of fixing a contents limit, the insured
  reports values each period. On a multi-location risk the insurer can price every location at one
  **multiple-location average rate** (MLAR) rather than each location's own rate. A
  **General Information** record at policy level holds the reporting details and prices
  incidental and newly acquired locations.
- **Additional Locations Special Coinsurance** (CP 13 20): lets smaller extra locations carry a
  special coinsurance arrangement, priced at the same average rates.
- The two forms **cannot be on the same policy** (a message says so). Each writes its own set
  of average rates.

**None of the 16 premium records has ever been priced by ISO**, and none appears on any
stored example policy.

## What the census found, before any task ran

| Family | Premium records | Rate source | Tables read directly (CW rows) | States that rewrite it | Messages (any file) | Editions |
|---|---|---|---|---|---|---|
| **Value Reporting Form** (CP 13 10; Group I, Group II, Broad, Special, EQ + General Information) | 6 | each coverage chooses between its **MLAR**, the **blanket average rate** (chunk 9) and **its own final rate**, keyed on `MultiLocAvgRatesIndicator` and `IncludedInBlkt`. General Information prices **incidental and acquired locations** | 10: incidental locations rate (4), acquired locations rate (1), new business factor (1), seasonal risk factor (1), coinsurance (3; FL), 3 indivisible sublines, 2 peril-exclusion stat-code tables (AR DC) | AL AR DC NY RI (wind / hail excluded indicator only) | **29** (3 shared with CP 13 20): average value only when MLAR is used / new business; alcoholic beverage tax value needs CP 99 10; cause of loss identical across reported records; not with CP 10 29 / 10 45 / 12 30 / 13 20; CP 13 30 needs CP 13 10; General Information required; Public Institutional Plan (AL KS RI); CA CP 10 43 sub-limit | same in all four |
| **Additional Locations Special Coinsurance** (CP 13 20; Provisions per contents row + General Information; Group I, Group II, Broad, Special, EQ) | 10 | the **MLAR** it writes itself × coinsurance factor × limit; General Information uses the **total incidental-locations limit** | `AddlLocSpclCoinsFactor` (1), and the Value Reporting Form's **incidental locations rate** (4) | none | **14** (3 shared): General Information required; not with Agreed Value, blanket, CP 10 29 / 10 45, CP 13 10; cause of loss, coinsurance and EQ identical on every record; CA CP 10 43 | same |

**The multi-location trail (check 10).** Three families of writer, one reader set:

| Where | Writes | Reads |
|---|---|---|
| **Value Reporting General Information** (policy; 169 KB, 56 rules) | the five MLARs, `MLARLimit`, `TotalValueForMLARCalc`, `MaxPrsnlPropLimitForMLARCalc` | `MultiLocAvgRates` |
| **Value Reporting Form** (per contents row; 40 KB) | the five MLARs again | the indicator, its own MLARs |
| **Additional Locations General Information** (policy; 60 KB) | the five MLARs again, `TotalFullValueForMLARCalc` | its own totals |
| **Main ruleset (built)** | `MultiLocAvgRates`: `SetMultipleLocationsAvgRate` sets "Not Used" when no Value Reporting General Information exists, else copies it from record [1] (only when blank) | |
| **Main ruleset (built)** | `ErcResetPrsnlPropPremiumForAdditionalLocations` runs the Additional Locations roll-up for each General Information record | |
| **Personal Property (built)**; 9 states rewrite the file: AK AL AR CA DC FL GA NY RI | `MultiLocAvgRatesIndicator` | `MultiLocAvgRates`, `MLARLimit`, `TotalValueForMLARCalc` |
| **Occupancy (built)** | | `MultiLocAvgRatesIndicator` |
| **Blanket Rating Detail (built, chunk 9)**; CA rewrites | | `MultiLocAvgRates` |

Sibling names checked: only `BuildersRiskReportingForm`, which is chunk 24's. **44 message rules
listed, 41 distinct.** One is Builders Risk's, which leaves **40 in scope**. Three shared ones (terrorism
sub-limit, deductible "Not Applicable", non-owned trailers) are already tested by other chunks.
No date arithmetic, no `Power`, no unregistered element.

**What shapes the plan:**

1. **Three writers of the same five fields.** `BasicGroupIMLAR`, `BasicGroupIIMLAR`, `BroadMLAR`,
   `SpecialMLAR` and `EQMLAR` are each written by the Value Reporting General Information, by the
   Value Reporting Form on each contents row, and by the Additional Locations General
   Information. The forms are mutually exclusive, but the first two are on the same policy. RC-1
   establishes the order of writes and which value each reader sees, on a real tree, before any
   dollar is predicted. This is the standing "same field name ≠ same value" rule at its widest yet.
2. **Three rate sources per Value Reporting coverage.** Each reads its MLAR, the blanket
   average rate or its own final rate. The golden cases put the three at different values so the
   reading chosen decides the dollar.
3. **The chunk reaches into built code.** Two rules in the main ruleset, Personal Property's
   indicator rule (rewritten in 9 states), Occupancy and chunk 9's Blanket Rating Detail all
   touch these fields. Today they sit on "Not Used" (C14-14). Every stored policy must re-rate
   **unchanged**, which the census of built files alone cannot show.
4. **The plan's "resets the Contents premium" is not what the rule says.** The main-ruleset rule
   runs a General Information rule that loops every location's contents rows and writes the **sum
   of their Additional Locations Provisions premiums** into the General Information record's
   `PrsnlPropPremium`. That is a roll-up; the Contents premium itself is not reset. C22-03 traces
   it and C22-12 confirms which reading holds, live.
5. **The General Information file is the largest single rule file in the remaining build.**
   169 KB and 56 rules: incidental and acquired locations, new business, seasonal risk. It gets
   its own hand trace (C22-05) before any golden case.
6. **Averages round.** An average rate across locations is a division; where it rounds, and
   whether the sum or each term rounds first, decides the dollar on a large schedule (C22-20).
7. **Every probe is new.** There is no stored multi-location evidence at all.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C22-01 | **Opening census**: population, formulas, tables, messages by record and by form / wording, sibling names, every edition, state layer, stored evidence, attach points, engine readiness, **and the multi-location trail** | ✅ | **Done 2026-09-28** (`903_chunk22_census.py`, 3 s). Findings above: 16 premium records, none priced by ISO or stored; 40 messages in scope; three writers of the five MLARs; the main ruleset, Personal Property, Occupancy and Blanket Rating Detail touch the fields; identical in all four editions; no unregistered element |
| C22-02 | **Who writes the MLARs, in what order**: on a real two-location tree, trace each of the five MLARs and their totals through all three writers; which value each reader sees, and when; what CP 13 10 + CP 13 20 together would do if the message is ignored. No ISO calls | ✅ | **Done 2026-10-01** (`213_`). Order traced on the engine (finding 2); one MLAR set per policy (3); "Used" raises: **OI-119**, traced under a labelled hypothesis; both forms together price twice (5) |
| C22-03 | **The built touchpoints**: `SetMultipleLocationsAvgRate` (the "Not Used" default vs the copy from record [1]; the blank-only guard), Personal Property's indicator rule and its 9 state rewrites, Occupancy's read, Blanket Rating Detail's read (and CA's rewrite), and the roll-up (sum into `PrsnlPropPremium`, not a reset). **Re-rate all 293 stored policies unchanged** | ✅ | **Done 2026-10-01** (`213_`). Policy field vs contents indicator (9); 9 state rewrites leave the indicator rule alone; the roll-up sums a field nothing writes and nothing reads (6); engine unchanged since 5a35c1f, so the 2026-09-30 293 of 293 carries. Occupancy / Blanket Rating Detail reads go to C22-09 (blanketed) |
| C22-04 | **Attach map and switches**: the Value Reporting Form under each contents row, both General Information records at policy level, Provisions under contents; every on-switch; the three rate sources per Value Reporting coverage and what selects each; blank-input defaults that zero a premium | ✅ | **Done 2026-10-01** (`213_`). Attach and switches (7); rate source "Not Used" + own rate hand = engine on both rows ($146 / $565); blanket source at C22-09, MLAR source behind OI-119 |
| C22-05 | **Value Reporting General Information by hand**: the 56 rules traced: incidental and acquired locations premiums, `NewBusnFactor`, `SeasonalRiskFactor`, the four incidental-locations rate rows, the MLAR arithmetic (`TotalValueForMLARCalc`, `MaxPrsnlPropLimitForMLARCalc`, `MLARLimit`); every step written down and checked against the engine | ✅ | **Done 2026-10-01** (`213_`): incidental + acquired locations by hand on 4 cases, hand = engine ($183, $481, $189, $310); the MLAR arithmetic by hand under both OI-119 readings (0.192 vs 0.038), engine-checked only under the hypothesis. The \"Used\" half is unpriceable at ISO (OI-119, probed live); its arithmetic is recorded, not confirmable |
| C22-06 | **Tables and literals**: all 11 distinct tables' rows and key literals, the `MultiLocAvgRates` values ("Used", "Not Used", …) and where each comes from, FL's coinsurance, AR DC stat-code tables | ✅ | **Done 2026-10-01** (`213_`). Finding 8; FL's own coinsurance table is read only by the dead VR Form factor; AR DC stat-code tables at C22-17 |

### RC-2 · Golden cases (6 tasks), all new live probes · COMPLETE 2026-10-01

Payload typing found on the way (ISO refuses these as strings): `SpecificIns`, `AvgVal`, the incidental / acquired limits, `OverallLimit`, `FullValue` (213_ adds them) and the contents' `FullPrsnlPropValue` (215_). The VR Form's Broad record reads `CyberIncidentExclusionFactorBroad` twice (no COL-exceptions factor): no dollar at factor 1, tested at C22-16.

| # | Task | Status | Notes |
|---|---|---|---|
| C22-07 | **Value Reporting, MLAR not used**: two locations with different rates, each coverage group (Group I, Group II, Broad, Special, EQ) at its own final rate; the baseline; ISO live | ✅ | **Done 2026-10-01** (`215_ --live`): V1 Special and V2 Broad + contents EQ, two locations; hand = evaluator = engine on every record (V1 VR Group I $146 / $565, Special $85 / $247; V2 Broad $12 / $33, EQ $3 / $15); **ISO agrees** 255 / 257 premiums, messages equal |
| C22-08 | **Value Reporting, MLAR used** (OI-119: now a refusal case, ISO and ours): the same two locations with the average rate chosen so it equals neither location's; new-business average value; the alcoholic beverage tax value (CP 99 10); ISO live | ✅ | **Done 2026-10-01** (`215_ --live` U1): "Used" is refused by ISO (*maxLimit*, OI-119) and by our engine, as predicted; new-business average value and CP 99 10 messages move to C22-14 on "Not Used" |
| C22-09 | **Value Reporting, blanketed**: blanket average rate vs MLAR vs own rate on one policy, each at a different value, so precedence decides the dollar; ISO live | ✅ | **Done 2026-10-01** (`215_ --live` B1): rows 1-2 in a Personal Property Only blanket at Monthly Reporting price at the blanket average rate on 0.75 x blanket limit x their share, row 3 at its own rate (Group I $120 / $597 / $261); **ISO agrees** 381 of 381. MLAR-vs-blanket precedence is moot: "Used" is refused (OI-119) |
| C22-10 | **Value Reporting General Information**: incidental and acquired locations, seasonal risk, new business; each factor chosen to move a dollar; ISO live | ✅ | **Done 2026-10-01** (`215_ --live` G1-G3): acquired 60,000 priced ($481 total), acquired exactly 50,000 not ($189 with EQ incidental), seasonal row priced on 0.3 x limit vs 0.75 x limit (Group I $146 / $261); **ISO agrees** on all three |
| C22-11 | **Additional Locations Special Coinsurance**: two and three locations, Provisions on each contents row, General Information on the total incidental limit, EQ; ISO live | ✅ | **Done 2026-10-01** (`215_ --live` A1, A2): two locations at 90% (factor 1.05) and three at 100% with contents EQ; the MLAR follows the rule as written (full value x rate, not / 100; Group II omits the incidental part); **ISO agrees** 260 / 388 premiums, all 10 records each |
| C22-12 | **The roll-up**: the Contents premiums and the General Information `PrsnlPropPremium` before and after Additional Locations is added, predicted under both readings (roll-up vs reset); ISO live | ✅ | **Done 2026-10-01** (A1, A2): ordinary contents premium $0 on every row; GI `PrsnlPropPremium` 0 in ours and **0.0 at ISO**. The roll-up moves no dollar (RC-1 finding 6) |

### RC-3 · Zero cases, messages and names (4 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C22-13 | **Zero cases**: Value Reporting with no General Information; MLAR "Used" on one location; average value on a renewal; blank reported values; Additional Locations with no Provisions, with blanket, with Agreed Value; each switch off; predict both readings, ISO live | ✅ | **Done 2026-10-01** (`216_ --live` Z1-Z10, all agree with ISO): VR Form with no GI prices at its own rate (message, not $0); a contents indicator submitted "Used" on one row prices that row $0 (it reads the GI's MLAR, 0 on "Not Used"); Estimated / blank Average Value move no dollar on "Not Used"; AL GI alone prices on the incidental limit; AL with blanket or Agreed Value still prices (message only); Provisions with no GI $0; VR GI with no surviving VR Form prices its incidental part; OverallLimit 0 zeroes the Provisions |
| C22-14 | **Messages**: all 40, each triggered and silent, especially the "identical on every record" rules (cause of loss, coinsurance, EQ) across locations, the mutual exclusion, and the state versions (AL KS RI, CA); ISO live | ✅ | **Done 2026-10-01** (`216_ --live` M1-M23, all agree, every (level, message) equal): **31 of the 40 fire at their own level**, each also checked silent where it should be (M8a SPP in OR vs M8b KS, M12b, M16 vs M16b, M20). Not fireable on a priced policy: 4 behind OI-119 ("Used" is refused). CA's two CP 10 43 messages go to C22-17; the 3 shared ones were tested in earlier chunks |
| C22-15 | **Shared names**: the five MLARs (three writers), `MultiLocAvgRates` and its indicator, `PrsnlPropPremium`, `LimitToUse`, `CoinsuranceFactor`, `IncludedInBlkt`, `TotalIncLocsLimit`, diffed rather than assumed; whether a submitted MLAR survives any writer | ✅ | **Done 2026-10-01** (`216_ --live` S1-S4, all agree): submitted AL GI `CoinsuranceFactor`, VR GI `TotalIncLocsLimit` and the contents' `LimitToUse` SURVIVE (IsNull guards; S2 $915 vs $183); a submitted AL GI MLAR is OVERWRITTEN (S4 = A1's figures). RC-1 covered the VR MLARs, `MultiLocAvgRates` and `PrsnlPropPremium` |
| C22-16 | **Exclusion records**: the cyber-incident factors in all 16 premium formulas, and the wind / hail excluded indicator, each at a limit where it moves a dollar | ✅ | **Done 2026-10-01** (`216_ --live` X0-X3, W1, all agree): **ISO also reads the VR Form Broad record's plain cyber factor twice** (X1 $130, not $131) and never reads its COL-exceptions factor (X2 unchanged $132); AL Special and every other record take the normal pair (X3); the contents' wind / hail exclusion sets the VR GI indicator 'Yes' and peril stat code 34 at ISO and ours (W1) |

### RC-4 · States, editions and scale (4 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C22-17 | **The state layer**: AL AR DC NY RI's wind / hail indicator and AR DC's peril-exclusion codes; the 9 Personal Property rewrites (AK AL AR CA DC FL GA NY RI) as they touch the indicator; CA's Blanket Rating Detail; the Public Institutional Plan (AL KS RI); ISO live | ✅ | **Done 2026-10-01** (`217_ --live`, 9 cases, all agree with ISO incl. the stat fields): AL sets the VR wind / hail indicator from ITS OWN record (`WindstormOrHailExclusionDirectDamagePrsnlProp`: 'Yes', code 34; the CW record: 'No', 36); AR DC NY RI hard-set 'No' (36; AR / DC from their own tables); CA's two CP 10 43 messages fire with CP 13 10 and CP 13 20 (the contents need their own EQ election for the record to attach); CA's blanketed VR agrees (423 premiums). The 9 Personal Property rewrites: in C22-19. PIP: RC-3 M21-M23 |
| C22-18 | **Editions**: identical in all four; one multi-location probe each on MO (2023 V02), a V03 and a V04 state | ✅ | **Done 2026-10-01** (`217_ --live` E1-E9, all agree): every-rule diff MO V02 29 family + 16 parent rules, CA / NC V03 4 + 13, V04 0 + 3, each judged. MO's "Not Used" formulas equal 2026's (E1); "Used" refused in V02 too (E2, OI-119, line 3343); **V02 removes a blanketed VR Form whose contents sit at 90%** (its attach test reads `BlktCoinsuranceValue` before V02 sets it; 2026 keeps it, E3 / E3b); V02's Break-style indicator gives 'Yes' (E4); V02 / V03 replace the terrorism sub-limit message with "Sub Limit cannot exceed the coverage's limit", incl. its AL full-value variant (E5-E7); IL V04 agrees on both forms (E8, E9) |
| C22-19 | **All 46 states**: a multi-location policy with each family on every state's own package, predicted per state; ISO live | ✅ | **Done 2026-10-01** (`217_ --live --states`, 6 batches): **all 46 states agree**, both forms on one two-location policy, 16 records each predicted by hand, every premium and (level, message). FL needs 208_'s recipe (no earthquake inputs, FL's own special-class description: OI-103 otherwise). One batch hit an ISO read timeout at MN and was re-run |
| C22-20 | **Scale and rounding**: a larger schedule (e.g. 8 locations of mixed rates) where rounding the average vs rounding each term gives different dollars; ISO live | ✅ | **Done 2026-10-01** (`217_ --live` SC1 / SC2): 8 locations of mixed limits; full values found by a search so that rounding each full value x rate (the rule) gives Group I MLAR 0.176 and rounding only the average 0.177. **ISO rounds each term**: Provisions Group I $3,589 total (not $3,610), 1,010 of 1,010 premiums; VR "Not Used" on the same 8 locations 1,005 of 1,005 |

### RC-5 · Confirmation and close-out (4 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C22-21 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; the blanket roll-up (chunk 9); terrorism; stat codes; **the 293 stored policies re-rated unchanged**; ISO live | ✅ | **Done 2026-10-01** (`218_ --live`, `--stored "chunk22_rc*"`): the total moves by the chunk 22 premiums **minus** the contents premiums they switch off **plus** the contents' terrorism change (TerrorismLimitToUse 0.75 x Limit under VR; **the contents' coinsurance factor forced to the 100% row under either form**): **+$38 / -$622, clean tests +$1,991 / -$3,878, predicted before each call and equal at ISO**; every other premium unchanged; no terrorism field on a chunk 22 record; 582 stat values equal on 120 stored responses; the 293 stored policies: C22-22 |
| C22-22 | **Regression** (scaled back 2026-10-01): pin the golden figures in `104_`; `206_ --check` + `157_ --all`; the full `104_ --gate` only if the engine changed in this chunk (e.g. OI-119) | ✅ | **Done 2026-10-01** (scaled back, user): engine unchanged since 5a35c1f, so the 2026-09-30 full run carries; `206_ --check` CLEAN (1,259 requests, 890,791 fields; baseline refreshed); `157_ --all` 293 of 293; `104_ --only 213 215 216 217 218` CLEAN 5 of 5, `215_` pinned to 10 figures |
| C22-23 | **Census close**: count the two families as built in `166_` (504 → 520 of 546, 95%) | ✅ | **Done 2026-10-01** (`166_`): **520 of 546 countrywide premium files built (95%)**, 26 left in 2 families |
| C22-24 | **File `CF-CHUNK22-GATE.md`** | ✅ | **Done 2026-10-01**: `CF-CHUNK22-GATE.md`, **9 of 9** |
