# Property build — start here

**Last worked 2026-10-06.** This is the resume point: where things stand, how to
confirm it in two minutes, and what to pick up first.

**Keeping things in sync (standing rule, 2026-10-01).** The task lists are the source of truth. A Stop hook
(`.claude/settings.json` → `scripts/cf/hook_status_sync.py`) checks after every turn that CF-BUILD-STATUS.html, this
page and the deployed page agree with them; on drift it hands the problems back to fix. After any status-page edit, run
`scripts/cf/sync_status_page.py --push` (deployed copy, Federato/Ideation). At gates, 104_ also runs
`check_status_docs.py --no-deployed` and `check_premium_census.py` (premium files the census could miss).

---

## Pick up here (set 2026-10-06, end of day): the ISO Rating Test Console, RC-2 next

**New workstream: the ISO Rating Test Console** ([`TC-PLAN.md`](TC-PLAN.md), from the design brief
`Design brief questionnaire.zip`): seven screens replacing the testing pages `/tester`, `/tests`, `/review`. **13 of 38
tasks; RC-0 and RC-1 done** (commit `75757f0`). All 22 decisions are the user's (D1-D22, in the plan).
* RC-0: decisions, the old pages' parity list ([`TC-02-PARITY.md`](TC-02-PARITY.md)), call rules, GL step values, the
  path census ([`TC-05-PATHS.md`](TC-05-PATHS.md)).
* RC-1, the data layer `console/`: reference store (2,935 ISO answers + 1,060 GL premium rows), staleness, status
  vocabulary, path config (`console/config/paths.json`), path signatures, mismatch categories, roll-up, and **the call
  ledger, live inside `scripts/raas.py`: every ISO call counts toward 250 a day (150 active / 50 refresh / 50 ad hoc);
  the chunk scripts and `/` share the ad hoc 50; past it, `RAAS_OVERRIDE="reason"` (logged).** Tests:
  `tests/verify_console_rc1.py` (50 of 50).
* **Next: RC-2** (TC-14..19): the console shell, `/api/console/readiness`, the Readiness Matrix, "Still to test", the
  Coverage Board, seeded from the evidence held (no calls). Carry: GL has premium-level references only (bodies accrue
  via the ledger); 344 CP answers have no request file.

## Pick up here (set 2026-10-06): chunk 28 GATED, 22 of 22; every planned chunk gated

**Chunk 28 GATED 2026-10-06** ([`CF-CHUNK28-GATE.md`](CF-CHUNK28-GATE.md)): Sets A to G, each engine change
with the user's go; all 34 newer ISO packages in; OI-116 closed and OI-117 to the parking lot (the user's
decisions at the gate). Full gate clean: `206_` (2,074), `157_ --all` 293 of 293, `104_ --gate` 173.
**Chunks 1 to 28 are all gated; the build order has no chunk 29.** What is left is outside the plan: the
Property side of the app (since 2026-10-06, `096f2b0`: `start.bat`, choose Commercial Property, a state; one office
risk rated and compared with ISO; 46 states offline, 46 of 46 equal ISO live once the sample stopped attaching Florida's withdrawn CP 10 75; the engine
side, **OI-133**, fixed and closed (FL's cyber exclusion tables read as filed; `259_` 5 of 5 equal ISO live);
status page "Property in the app"), option (c) of Set G (a neutral shared core, worth it as that app grows), the parking lot (OI-117), and refreshing the corpus when ISO
files newer packages (`242_`, then `255_ --write`; C28-19 refuses any state that falls behind).

## Earlier (set 2026-10-06): chunk 28 at 21 of 22, Sets A to G done

**C28-21 done 2026-10-06 (the user's choice (b))**: the Property steps around a rating moved out of GL's interpreter
into `cf_engine/run_checks.py` (`PropertyRunChecks`, via `CFResolvedBook.run_hooks`); nothing moved (snapshot clean, no
rebaseline; 293 of 293; full regression clean). Then C28-22, the gate (above).

**C28-20 done 2026-10-06: all 34 packages in** (batches `CF/20270101` with countrywide `CF_CW_20270101_V01`,
`CF/20270201`, `CF/20270301`, `CF/20270401`, `CF/20270601`, and IL 20261001 in `CF/20260601`). ISO and ours name the
same package in 46 of 46 states at all 276 dates checked; 287 of 287 cases agree with ISO (`256_`); OI-105 closed.
Full regression clean (170), `157_ --all` 293 of 293, snapshot clean (2,074). Then C28-21 (below the heading above). When ISO files newer packages: `242_`, then `255_ --write`.

## Earlier (set 2026-10-06): C28-19 built

**C28-19 built 2026-10-06** (the user's go, choice (a) refuse): a date on which ISO is known to rate on a package the
corpus lacks refuses before rating (outcome *refused / older package*, both packages named), from
`cf_engine/resolve/iso_packages.json` (`255_ --write`, after every `242_` run). Importing a package lifts it. `257_`
confirms it (276 of 276); `157_ --all` 293 of 293; snapshot 1 request moved by decision (OR 2027-01-01), rebaselined.
Full regression 168 of 170, both explained: `224_`'s Builders Risk census counted the imported IL package's own test case
(now named as imported by C28-20, passes); `tests/verify_tester.py` is timing-flaky under the full run's load (two test
batches stamped the same instant; 81 of 81 alone, 3 of 3 runs), not the engine. Today nothing refuses; from 2027-01-01, 20 states refuse until their packages are in.
**C28-20: 31 of 34 packages in** (2026-10-06: IL's October package; the whole 2027-01-01 batch in `CF/20270101`, 20
states on a new countrywide edition `CF_CW_20270101_V01`): 176 of 176 cases agree with ISO at 2027-01-01 (`256_`); the
OR OI-105 case equals ISO ($97). AK 20270201 then too (`CF/20270201`, 8 of 8). Then the 2027-03-01 batch
(`CF/20270301`, 9 states, 80 of 80 agree with ISO). **Next: the 3 left**: VT 20270301 V01 (not in the March batch),
GA 20270401, KS 20270601. Then C28-21 (optional), C28-22 (gate).

## Earlier (set 2026-10-05): chunk 28 at 18 of 22, Sets A to E done

**Sets A, B, C, D and E done 2026-10-05.** Latest, C28-17 / 18 (Sets B and E, the user's go): a missing input that
zeroes an attached coverage refuses the policy (stricter than ISO, the user's decision), with an outcome field (rated /
refused / refer to company; refer only when a `CompanyMinimumPremium` is supplied). The test policies, which had moved
Oregon's policy to other states without their own territories, now carry each state's real inputs (the user: "we need
to input the correct territory"; `scripts/cf/_state_inputs.py`), and all 26 affected scripts were re-run live: all agree
with ISO. Full gate clean (170); 293 of 293; snapshot rebaselined (195 requests equal to fresh ISO, 96 old silent-zero
requests refused by decision). Original evidence kept in `results/cf-raas-before-c28-17`. Open: OI-117; OI-116 is a
question for ISO ([`CF-CHUNK28-ISO-QUESTION-OI116.md`](CF-CHUNK28-ISO-QUESTION-OI116.md), not yet sent).
**Next: Set F, C28-19, measured and proposed 2026-10-06** ([`CF-CHUNK28-PROPOSAL-F.md`](CF-CHUNK28-PROPOSAL-F.md),
`255_`, no engine change): 34 missing packages, 28 states go onto an older package than ISO's;
CT and NM miss an edition between packages they hold. **Awaits the user's go and choice** (refuse / warn / refer).
**C28-20 under way (the user's decision: import the newer packages)**: `CF IL 20261001 V01` is in (`CF/20260601`), 8 of 8
agree with ISO at 2026-11-01 (`256_`), snapshot clean. **33 packages to go** (IL 20270101 V02 and the 2027 ones, `255_`
lists them); for each: drop it in, `242_ --states XX`, `256_ --state XX --date <after its edition>`.
The full list is on the status page, "Future items: ERC packages to add". Committed 2026-10-06 (the commit after
`542f0e1`); the quick gate was clean (34 scripts) and the snapshot clean (1,812) after the import.

**New PC (2026-10-05).** Everything now lives on F: and the defaults say so: the corpus `F:\ISO_ERC_Files`
(`cf_engine` / `gl_engine` config), RaaS credentials `F:\Will_Dan_Collab_dev\.env` (with `RAAS_ORG_ID` / `RAAS_SHIP_ID`), the
Ideation clone `F:\Ideation`; no environment variables needed (set `PYTHONIOENCODING=utf-8` for the console). The code's
`C:\Projects` references were moved to F: (historical logs and docs left as written). Full gate clean but for
`verify_notebooks` (IPython is not installed here). The status-page push also needs `gh auth login` and
`git config --global --add safe.directory F:/Ideation`.

## Earlier (set 2026-10-02): chunk 27 GATED, chunk 28 OPEN at 4 of 22

**Chunk 27 GATED 2026-10-02, 18 of 18** ([`CF-CHUNK27-GATE.md`](CF-CHUNK27-GATE.md)): every loose end on chunks 1–26
closed with evidence or handed to chunk 28; no engine change; `104_ --quick` clean (34), `206_ --check` clean (1,760),
`157_ --all` 293 of 293. **Chunk 28 OPEN** ([`CF-CHUNK28-TASKS.md`](CF-CHUNK28-TASKS.md), 4 of 22): seven feature sets, **starting
with Set A (refuse where ISO refuses) at the user's choice**, then C, D, B + E, F, G; **every engine change needs the
user's go, one item at a time.** C28-01 census done (`909_`: 12 of 12
open items assigned). **C28-02 done** ([`CF-CHUNK28-REFUSALS.md`](CF-CHUNK28-REFUSALS.md), `245_`): 65 of 66 live refusals
are a `SingleResult` lookup with no row; none of 1,689 rated policies has one (exception: VT's empty EQ tier table).
**C28-03 done**: the rule holds against every competitor; empty state tables split by table (VT vacancy and NY off-premises fall
back to CW, the EQ stub refuses in MA TN VT; `246_`). **C28-04 done**: [`CF-CHUNK28-PROPOSAL-A.md`](CF-CHUNK28-PROPOSAL-A.md), measured (`247_`): ours would
refuse 65 of 66 ISO refusals (66 with the EQ stub exception), 0 new refusals on 1,690 rated requests. **Next session: C28-05, the build** (the user said 2026-10-02 "will build next session"; confirm the go when
starting). Build plan in the proposal's "What the build would also update". Uncommitted since `630ba2f`:
chunk 27 RC-4, its gate, chunk 28's tasks.

## Earlier (set 2026-10-02): chunk 27 RC-4 done

**Chunk 27 RC-4 done 2026-10-02** (15 of 18, no engine change; RC-3 committed `630ba2f`, RC-4 uncommitted).
`241_chunk27_rc4.py --live`, 11 of 11 agree with ISO: the drone's theft exclusion is read from the **contents** record
($187 → $75), Dependent Properties' from the **Business Income** record ($19 → $16); FL Ordinance or Law charges Coverage
A on the whole factor ($288) with no post-loss option, WV's B & C-only forms and flood-only flag price no Coverage A.
OI-101 / 119 / 122 / 124 closed (ISO agrees). OI-105 (`242_`, 276 live calls): same package in all 46 states at
2026-09-17; 34 newer packages missing (IL from 2026-10-01, most from 2027-01-01); policy proposed. OI-112 narrowed
(`243_`: on 2023 editions ISO drops the CP 03 20 cause-of-loss answers whatever is sent; the fields are checkboxes
there). OI-106 bounded (47 of 47 states; ours 135 of 240 form names "Value Not Found"), OI-114 windows, OI-116 two
readings ruled out (`244_`); all handed to chunk 28. **Next: RC-5, the close-out (C27-16..18).**

## Earlier (set 2026-10-02): chunk 27 RC-3 done

**Chunk 27 RC-3 done 2026-10-02** (`scripts/cf/240_chunk27_rc3.py --live`, 16 of 16 agree with ISO, no engine change; 9 of
18). **Chunk 8 is 9 of 9**: CA's Legal Liability zero was the sweep sending no `District` (CA's base rate is a District I /
II table; $57 / $68), FL prices $59 today. Chunk 2's per-state gaps closed: TX multiplies its Group II rate by a flat 0.1
when wind / hail is excluded ($800 → $79); DC and NY read no BCEG; IL maps "Cook County" to its "Cook" rows; MT's symbol
resolves; NY's Group II symbol is a submitted input (without one, $0 at ISO too). Two more OI-103 inputs noted (FL's own
Group II territories; NY's `CompletedBasicGroupIISymbol`). Committed in `630ba2f`.

## Earlier (set 2026-10-02): chunk 27 RC-2 done

**Chunk 27 RC-2 done 2026-10-02** (`scripts/cf/239_chunk27_rc2.py --live`, no engine change; 5 of 18). **Gate point 9 is
closed on chunks 1–8**: every golden case sent to ISO as the engine rates it, the (level, message) multiset equal on all 25
runs. Chunk 7's old "ISO 3, engine 5" compared a hand-built ISO payload with the engine's full tree; the same request
agrees. The one real difference: **OI-126** (ours fires one extra CP 03 20 message on a special class item with no
deductible: our `FirstNonNull` skips a filed "" fallback; messages only, chunk 28). ISO refuses every contents golden case
unless the **building** carries `WindstormOrHailDeductible` (OI-103's class); with it, chunk 8's contents premiums are now
ISO-confirmed. Register M-004..M-006 added. Gate files 1–7 at 9 of 9 (1–2: point 9 noted on their eight-point gates),
chunk 8 at 8 of 9 (point 8 is C27-06). Committed in `1056a15`.

## Earlier (set 2026-10-02): chunk 27 RC-1 done

**Chunk 27 RC-1 done 2026-10-02** (no ISO calls, no engine change; tasks [`CF-CHUNK27-TASKS.md`](CF-CHUNK27-TASKS.md), 2 of 18). The census (`908_`, now UTF-8 safe) refreshed after chunks 18–26: chunks 1–8's open points unchanged. Register: **OI-114 registered as the canonical row, OI-120 merged into it** (a census of every CF package: `<rul:Null/>` in 5, none in force; NC 2023-08 / 2024-02 flood operational-unit rule newly recorded); **OI-118 merged into OI-106**. Stale status-page rows corrected with dates (commit status: through chunk 25; input validation: eight inputs; point 9: owed on chunks 1–8; chunk 27's plan row), chunk 8's ❌ marked fixed by OI-110. An owner for every open item (chunk 27 closes with evidence; OI-99 / 103 / 117 / 123 / 125 / 113 and the design questions go to chunk 28). Chunk 26 and this work are uncommitted. **Next: RC-2, C27-03 (point 9 on chunks 1–6).**

## Earlier (set 2026-10-02): chunk 26 GATED; next, chunk 27

**Chunk 26 (Specific and Tentative rating) GATED 2026-10-02, 9 of 9, 23 of 23** ([`CF-CHUNK26-GATE.md`](CF-CHUNK26-GATE.md)). RC-5 (`scripts/cf/238_chunk26_c26-20_downstream.py --live`): Class → Specific moves the policy total by exactly the core records' differences (+$56 OR, +$701 with the rates doubled, +$68 FL, −$149 SC Group II, −$794 MO), each predicted before its ISO call and **equal at ISO**; nothing else moves; stat values and identification codes equal. Gate checks (no engine change in the chunk): `104_ --quick` CLEAN (34 scripts, every golden case of chunks 1–26), `206_ --check` SNAPSHOT CLEAN (1,697 requests), `157_ --all` 293 of 293. 546 of 546 unchanged; **the second (Specific / Tentative) rating path is built**. Open: OI-124 (CA One-Term BI at 1.0, ISO agrees), OI-125 (occupancy counts, messages only), OI-99 (31 more refusals, chunk 28). **Next: chunk 27 (open gate points on closed chunks, tasks set, `CF-CHUNK27-TASKS.md`); chunk 28's engine decisions each need your go.**

## Earlier (set 2026-10-02): chunk 26 RC-4 done

**Chunk 26 RC-4 done 2026-10-02** (`scripts/cf/237_chunk26_rc4.py --live`; the 46 states with `--states` in four batches; 48 policies, no engine change): **every premium and (level, message) agrees with ISO.** All 46 states on a Specific building, Specific Group II in the 36 that offer it. A submitted roof ACV factor (0.900, IsNull-guarded) made each state's shape show in dollars: the countrywide shape and KY price on 0.270 (OR $326), **FL NY WV and MO ignore the roof factor** (0.300, FL / NY $354). **MO's CW 2023 V02 rules differ and ISO follows them**: no roof factor, and BI on the building's FINAL rate (submitted 0.500 → BI 0.400, $215; the 2026 reading 0.240). Only MO's 4 edition differences name the rating type (V03's 91 do not; V04 none). 19 of 23. **Next: RC-5, C26-20 (downstream and no-move).**

## Earlier (set 2026-10-02): chunk 26 RC-3 done

**Chunk 26 RC-3 done 2026-10-02** (`scripts/cf/236_chunk26_rc3.py --live`, 23 cases, no engine change): every premium equal to ISO, every (level, message) on 22. **A blank `RatingType` prices the building at rate 1.0 ($1,204; Specific $362, Class $287) and BI at 1.0 ($538)**, ISO the same; no specific rate → building and BI $0; blank Group II rating type → Group II $0; the hazard messages fire one below each threshold (Low always) and the specific Group II still prices; FL residential and DC fraternity messages; a submitted copy of the rating type is overwritten, a submitted building `BasicGroupIRate` survives; protection class, territory and fire-safe vault move no Specific dollar. **OI-125 (new, messages only):** ISO's occupancy counts stay 0 even when the occupancy's rating type is submitted; ours counts it and raises "only one apartment…". 15 of 23. **Next: RC-4, C26-16 (the Group I rewrites).**

## Earlier (set 2026-10-02): chunk 26 RC-2 done

**Chunk 26 RC-2 done 2026-10-02** (`scripts/cf/235_chunk26_rc2.py --live`, no engine change): **7 golden cases, all agree with ISO**, every premium and message, each predicted with a competing reading ISO did not match. Specific building Group I $362 (class $287); contents on their OWN rate ($150; $335 at 0.450 where the building's rate gives $223); BI on the building's ($137); Tentative identical plus its form; SC Specific Group II at Severe 10,000 / High 25,001 / Medium 50,001 sq ft ($67 / $37 / $24 vs Class $175 / $90 / $12). **OI-124 (new): CA One-Term Loss Cost leaves BI at rate 1.0 ($538, not $121), and ISO does the same.** Payload note: outside OR set `BasicGroupIIRatingTerr` to a territory the state's Group II rate table files (SC Inland): the class base-rate lookup runs even on Specific Group II and ISO refuses a missing row. 11 of 23. **Next: RC-3, C26-12 (zero cases).**

## Earlier (set 2026-10-02): chunk 26 RC-1 done

**Chunk 26 RC-1 done 2026-10-02** (`scripts/cf/234_chunk26_rc1.py`, no ISO calls, no engine change; `--skip-replay` skips the 3-min replay; tasks [`CF-CHUNK26-TASKS.md`](CF-CHUNK26-TASKS.md), 6 of 23). The 598 stored Specific / Tentative requests are 138 distinct policies, 126 with an ISO response in 16 states: **every one re-rates with every premium equal to ISO** (15,234) and the same messages; hand = engine on all 122 Specific buildings, their contents and BI, and 15 Group II rates. **Contents copy the rating type but price on their own `SpecificGroupIRate`** (none: rate 0); **BI uses the building's**; Tentative = Specific + the Tentative Rate form; FL NY WV MO round the Specific rate once without the roof factor, KY keeps it. 36 states rate Specific Group II (blank → 0.0; FL excludes 21 residential codes; NY has its own shape). **CA's One-Term Loss Cost prices building and contents as Specific but BI falls to 1.0** (probe C26-11). The 31 failed calls are OI-99 cases. **Next: RC-2, C26-07 (building Specific Group I, ISO live).**

## Earlier (set 2026-10-02): chunk 25 GATED; every countrywide coverage built

**Chunk 25 (Flood) GATED 2026-10-02, 9 of 9, 26 of 26** ([`CF-CHUNK25-GATE.md`](CF-CHUNK25-GATE.md)). RC-5 (`scripts/cf/233_chunk25_c25-23_downstream.py --live`): the policy total moves by exactly the flood premiums (+$3,521 OR, +$3,277 with limits halved, +$10,522 NY, +$3,116 AK, +$22,828 MO), predicted before each call and **equal at ISO**; nothing else moves. Gate checks (no engine change in the chunk): `206_ --check` SNAPSHOT CLEAN (1,609 requests), `157_ --all` 293 of 293, chunk 25 scripts registered in `104_` and clean. **546 of 546 countrywide premium files built (100%)**; the state-only list closed (WV's two O&L flood forms built). Open: OI-122 (ISO defect, ISO agrees with ours), OI-123 (MO messages only, engine change needs your go), OI-103 (chunk 28). **Next: chunk 26 (Specific and Tentative rating, tasks set, `CF-CHUNK26-TASKS.md`) or chunk 27 (open gate points, can run any time); chunk 28's engine decisions each need your go.**

## Earlier (set 2026-10-02): chunk 25 RC-4 done

**Chunk 25 RC-4 done 2026-10-02** (`scripts/cf/232_chunk25_rc4.py --live`; the 46 states with `--states` in four batches; 75 policies, no engine change): **every premium agrees with ISO**. All 46 states on a two-location flood policy with a blanket; the county states price a listed county and an all-other one; AK / FL are company-entered premiums; **MO's CW 2023 V02 flood rules differ and ISO follows them** (excess always table 6 at 500,000, contents keep the location's deductible in a blanket, blanket totals per location: each probed against the 2026 reading); WV's CP 10 68 and its two O&L flood forms; Off-Premises' flood factor 1.02 (chunk 17's open item closed). **OI-123 (new, messages only):** MO's package has five empty `NotExist` tests that ISO reads as true; ISO raises a location message ours does not (engine change needs your go). 229_'s hand model now covers the county tables and MO's three V02 rules (RC-1–RC-3 re-run clean). 22 of 26. **Next: RC-5, C25-23 (downstream).**

## Earlier (set 2026-10-02): chunk 25 RC-3 done

**Chunk 25 RC-3 done 2026-10-02** (`scripts/cf/231_chunk25_rc3.py --live`, 41 cases, no engine change): **all agree with ISO**, every premium and the whole (level, message) set. **All 45 countrywide flood message rule instances fired at their own level** and stayed silent at each boundary. Found and ISO-confirmed: **contents and Special Class in a blanket take the blanket detail's deductible, the building always the location's** (a 500,000 detail deductible: blanket $1,273 → $520); a limit $1 over full value and flood on a Builders Risk building fire their messages but still price; "Other Flood Insurance" fires in a state request (the root reading of ancestor::MasterCFCW); nine submitted rates / factors survive, total property value / ITV % to use / excess-to-use are overwritten; CP 10 75 / 10 76 apply 0.999. The 229_ hand model now follows each deductible / excess / total-value rule per record (RC-1 and RC-2 re-run clean). 17 of 26. **Next: RC-4, C25-18 (the county states).**

## Earlier (set 2026-10-02): chunk 25 RC-2 done

**Chunk 25 RC-2 done 2026-10-02** (`scripts/cf/230_chunk25_rc2.py --live`, 2m41s, no engine change): **22 golden cases, all agree with ISO**, every flood record predicted by hand before the call, every premium field for field, every message. All seven rate-modification tables each decide a building dollar ($36 at deductible 500 … $5,758 at 100,000), zones A / X / X500 / D, CRS on / off ($493 / $616); contents at two deductibles; BI combined types, maximum period, SCBI extra expense only; **Special Class, SCBI and the flood blanket priced by ISO for the first time** (blankets $1,273 / $1,731 / $1,952 / excess $7,644); excess over NFIP on three full-value bands; ITV over 100% → $0. **OI-122 answered: ISO prices the operational-unit BI flood rate AS WRITTEN** ($0 with a CRS grade, $531 from the last building without one), exactly as our engine does; an ISO defect, no engine change. 13 of 26. **Next: RC-3, C25-14 (zero cases).**

## Earlier (set 2026-10-02): chunk 25 RC-1 done

**Chunk 25 RC-1 done 2026-10-02** (`scripts/cf/229_chunk25_rc1.py`, no ISO calls, no engine change; `--skip-stored` skips the 3-min stored re-rate). All 293 stored policies re-rate unchanged. **The one stored flood policy is Alaska**, and AK and FL price all six flood records as a company-entered premium (r0(r0(ManualPremium × package mod) × IRPM)): ISO $650 / $440 / $84 = hand = engine. Countrywide: the **deductible picks ONE of seven rate-modification tables** (keyed by ITV % and total property value, interpolated on ITV); the zone keys the loss cost; floor and stories are statistics only (the census's "seven factors" reading was wrong, corrected in the task list). Hand = 174_'s evaluator = engine on 18 rate trees and 4 blankets, every premium and every intermediate value. Special Class / SCBI read their **flood record's own `ConstructionType`**; contents read the building's; excess over NFIP prices only at 750,000 / 1,000,000; tables 5–7 file zeros. **OI-122 (new):** the operational-unit "highest" BI flood base rate never stores its maximum as written, so BI with maximum period in an operational unit prices $0 (no CRS grade: the last building's rate); our engine does the same; two ISO probes set for C25-10. 7 of 26. **Next: RC-2, C25-08 (Building, ISO live).**

## Earlier (set 2026-10-01): chunk 24 GATED; next, chunk 25

**Chunk 24 GATED 2026-10-01, 9 of 9, 25 of 25** ([`CF-CHUNK24-GATE.md`](CF-CHUNK24-GATE.md)). RC-5 (`scripts/cf/228_chunk24_c24-22_downstream.py --live`): the policy total moves by exactly the Builders Risk premiums (+$1,976 OR, +$13,199 at 10 x, +$1,982 FL, +$1,861 NY), predicted before each call and **equal at ISO**; nothing else moves. Gate checks (the engine changed in the chunk: OI-121): the full `104_ --gate` **CLEAN 157 of 157** (stopped once for low memory at 153, the last 4 run separately), `157_ --all` 293 of 293. **540 of 546** countrywide files built (99%); 6 left, all flood. Open: OI-103 (four more refusal cases, chunk 28), two readers not priced (CA O&L increased period, FL Pollutant). **Next: chunk 25 (Flood), tasks set, `CF-CHUNK25-TASKS.md`.**

## Earlier (set 2026-10-01): chunk 24 RC-4 done

**Chunk 24 RC-4 done 2026-10-01** (`scripts/cf/227_chunk24_rc4.py --live`): **all 46 states agree with ISO** on a fuller Builders Risk policy (~200 premiums each, every message): the 16 rewriting states with records derived from their own rule text (FL's older package: no cyber factors, a sinkhole term); the 2023 V02 / V03 editions keep the FIRST of two same-numbered periods, 2026 the LAST (MO 738 / OR 1,214, ISO equal); Business Income (factor 2), antennas' BI and the building-level unmanned aircraft (EQ factor 0.495: $30 vs $60) price with Builders Risk on. Three more blank keys ISO refuses and ours prices (territory, NY's completed symbol): **added to OI-103**. No engine change in RC-4 (OI-121 was RC-2's). 21 of 25. **Next: RC-5, C24-22 (downstream).** The engine changed in this chunk, so the gate runs the full `104_ --gate`.

## Earlier (set 2026-10-01): chunk 24 RC-3 done

**Chunk 24 RC-3 done 2026-10-01** (`scripts/cf/226_chunk24_rc3.py --live`): **48 zero / message / shared-name / exclusion cases, all agree with ISO**, every premium and (level, message). A premium adjustment period after expiration prices **negative**, as written (ISO too); the $500 minimum fires on 250 and is silent at 500; NY's U / V / W both ways (a submitted symbol: NY's own rule is empty); KS / AL / RI's Public and Institutional Plan; the Builders Risk blanket sum and mixed-form messages. Submitted rates, Factor, ProRate and theft rate survive; **a submitted completed-value multiplier is overwritten**. The 2% EQ deductible on class A1 is refused by ISO and priced $0 by ours: **added to OI-103** (chunk 28). No engine change. 17 of 25. **Next: RC-4, C24-18 (the sixteen states).**

## Earlier (set 2026-10-01): chunk 24 RC-2 done

**Chunk 24 RC-2 done 2026-10-01** (`scripts/cf/225_chunk24_rc2.py --live`, 10 cases + 3 probes, all agree with ISO, every premium and message). Every container rate predicted by hand from the tables and the building's built factors (renovations Group II read from the engine, stated). Reporting form Group I $164 / II $321 / Special $94 / Broad $78 / EQ $20; renovations take the **larger** of the Builders Risk and completed-building rates ($454 Frame, $270 Fire Resistive; beside a reporting form renovations price $0 and the reporting form copies their rates); collapse $8 / $187 / $235; materials of others 250 -> $232; theft's deductible moves no dollar. **OI-121 probed and FIXED (your go): ISO pro-rates by plain exclusive days, no leap day removed** (L4 / L5: 0.73 / 0.52 where counting 29 February gives 0.74 / 0.53; the first two probes, L1 / L2, could not disagree and were replaced). The engine reads GetLeapDays as 0 on a one-year term (Property only) and equals ISO on all five probes; `206_ --check` after the change. 13 of 25. **Next: RC-3, C24-14 (zero cases).**

## Earlier (set 2026-10-01): chunk 24 RC-1 done

**Chunk 24 RC-1 done 2026-10-01** (`scripts/cf/224_chunk24_rc1.py`, 2m23s, no ISO calls, no engine change). All 293 stored policies re-rate unchanged. Builders Risk theft agrees hand = evaluator = engine = ISO on all **145** stored responses (one $0 by rounding; **FL prices theft on its own rule**, Group I rate x 0.25). Six test policies price every Builders Risk record three ways: the reporting form's five coverages, renovations (**$0 beside a reporting form**), collapse, materials of others, CP 10 44, and the premium adjustment periods. **OI-121 (new): a premium adjustment period starting after the effective date needs ISO's unpublished `GetLeapDays` function, which our engine refuses**; probe at C24-10. 6 of 25. **Next: RC-2, C24-07 (theft golden case).**

## Earlier (set 2026-10-01): chunk 23 GATED; next, chunk 24

**Chunk 23 GATED 2026-10-01, 9 of 9, 22 of 22** ([`CF-CHUNK23-GATE.md`](CF-CHUNK23-GATE.md)). RC-5 (`scripts/cf/223_chunk23_c23-19_downstream.py --live`): with each state family removed and restored, the policy total moves by exactly the family's premiums (+$192 / +$31 / +$806 / +$3,908 on the fuller policies, +$234 / +$31 / +$1,360 / +$3,902 on the golden ones), predicted before each call and **equal at ISO**; nothing else moves. Gate checks (no engine change): `206_ --check` clean, `157_ --all` 293 of 293, chunk 23 scripts registered in `104_` and clean. **520 of 546** countrywide files; the state-only list closed except WV's two flood files (chunk 25). Open: OI-120 (old editions only). **Next: chunk 24 (Builders Risk), tasks set, `CF-CHUNK24-TASKS.md`.**

## Earlier (set 2026-10-01): chunk 23 RC-4 done

**Chunk 23 RC-4 done 2026-10-01** (`scripts/cf/222_chunk23_rc4.py --live`): every family on a fuller state policy (MA two locations, AK an ordinary second building, CA two buildings, VA three forms on three buildings) **agrees with ISO**; the state-only list is closed (80 files, none unassigned; no in-force premium writer outside `SetPremium`, so 520 of 546 stands); the old packages: MA 2022 relocation prices nothing, but **AK 2020 and VA 2021 DO price, inside `ErcRate`** (the census's "no premium rule" was a SetPremium-only test). **OI-120 (new): pre-2022-10 policies cannot rate in our engine** (a `Null` inside a 2020 countrywide condition); old editions only. No engine change. 18 of 22. **Next: RC-5, C23-19 (downstream).**

## Earlier (set 2026-10-01): chunk 23 RC-3 done

**Chunk 23 RC-3 done 2026-10-01** (`scripts/cf/221_chunk23_rc3.py --live`): 43 zero, message, shared-name and exclusion cases **all agree with ISO**, every (level, message) equal. 30 of the chunk's own message rules fired at their level; AK fee limits under the coverage limits give negative fees (as written, at ISO too); a blank VA CovType switches the broad form's Cov A on and the tenants' off; the countrywide CP 04 26 rule overwrites `PersPropertyIncludedInBlanket`, which VA's CP 04 27 rule reads; VA's tenants' form reads no cyber factor. ISO twice closed the connection mid-run (re-sent; not a difference). No engine change. 15 of 22. **Next: RC-4, C23-16.**

## Earlier (set 2026-10-01): chunk 23 RC-2 done

**Chunk 23 RC-2 done 2026-10-01** (`scripts/cf/220_chunk23_rc2.py --live`, 2 min): 12 golden cases **all agree with ISO** (1,727 premiums, every message): MA heating oil (credit -$17 at its cap, -$9 under it), tenant relocation (the cap is per unit: $30 for 3 units over it), AK fees on Legal Liability (ISO truncates the per-mortgage ratio), CA Limited / Additional EQ (1,234.5 -> $1,235; a blanketed Limited EQ building is unreachable, $0 + ISO's no-EQ-blanket message) and all 41 VA records on three CovTypes (closes chunk 12's open VA priced case). Payloads with Mortgageholders E&O use 200_'s `payload` (its Limit is text). No engine change. 11 of 22. **Next: RC-3, C23-12 (zero cases).**

## Earlier (set 2026-10-01): chunk 23 RC-1 done

**Chunk 23 RC-1 done 2026-10-01** (`scripts/cf/219_chunk23_rc1.py`, 37 s, no ISO calls; tasks [`CF-CHUNK23-TASKS.md`](CF-CHUNK23-TASKS.md), 6 of 22). Every premium record of MA heating oil / tenant relocation, AK attorneys' fees, CA Additional / Limited EQ and VA's 41 Ordinance or Law files: hand = evaluator = engine on 13 trees. MA's stored credit never priced because nothing switched it on (it needs a remediation record on a building); MA's relocation cap is per unit; **AK's fees exist only on Legal Liability** (and the policy fee only with Mortgageholders E&O); CA's later packages fix a typo that moves no dollar; VA files no tables of its own. No engine change, no regression run. **Next: RC-2, C23-07 (MA heating oil, ISO live).**

## Earlier (set 2026-10-01): chunk 22 GATED; next, chunk 23

**Chunk 22, multi-location (Value Reporting Form and Additional Locations Special Coinsurance), GATED 9 of 9 on 2026-10-01, 24 of 24** ([`CF-CHUNK22-GATE.md`](CF-CHUNK22-GATE.md), tasks [`CF-CHUNK22-TASKS.md`](CF-CHUNK22-TASKS.md)). All 16 records ISO had never priced are ISO-confirmed, every figure predicted by hand first: RC-2 8 golden cases, RC-3 45 zero / message / name / exclusion cases, RC-4 the state rewrites, editions, **all 46 states** and an 8-location rounding probe, RC-5 the downstream total (**+$38 / -$622, +$1,991 / -$3,878, equal at ISO**: the forms switch the contents premium off and force the contents' coinsurance factor to the 100% row, which moves terrorism). **"Used" is unpriceable at ISO and ours (OI-119); no engine change.** Regression scaled back: `206_ --check` CLEAN (baseline refreshed, 1,259 requests), `157_ --all` 293 of 293, the chunk 22 entries through `104_` 5 of 5. **520 of 546 countrywide premium files built (95%).** **Next: chunk 23** (state-only coverages; tasks set, `CF-CHUNK23-TASKS.md`).

## Earlier (set 2026-10-01): chunk 22 RC-4 done; next RC-5

**Chunk 22 RC-4 done 2026-10-01** (`scripts/cf/217_chunk22_rc4.py --live`; the 46 states with `--states`, one process per batch of ~11): the state layer (AL reads its own wind / hail record; AR DC NY RI hard-set 'No'; CA's CP 10 43 messages), the editions (MO V02 removes a blanketed VR Form whose contents sit at 90%; V02 / V03 rename the terrorism sub-limit message; "Used" refused in V02 too), **all 46 states** (both forms, 16 records each) and an 8-location rounding probe (**ISO rounds each full value x rate before averaging**: $3,589, not $3,610) **all agree with ISO**. FL needs 208_'s no-earthquake recipe. No engine change, no regression run. 20 of 24. **Next: RC-5, C22-21 (downstream), C22-22 (gate checks: `206_ --check` + `157_ --all`), C22-23 (census), C22-24 (gate).**

## Earlier (set 2026-10-01): chunk 22 RC-3 done

**Chunk 22 RC-3 done 2026-10-01** (`scripts/cf/216_chunk22_rc3.py --live`, 4m09s): 45 cases (10 zero cases, 24 message cases, 4 shared-name overrides, 5 exclusion probes) **all agree with ISO**: every predicted record, 11,977 premiums, every (level, message) multiset. 31 of the 40 in-scope messages fired at their own level (4 sit behind OI-119, CA's 2 go to C22-17, 3 were tested earlier). ISO, like the rule text, applies the VR Form Broad record's plain cyber factor twice ($130 not $131). Submitted AL coinsurance factor, VR incidental total and contents LimitToUse survive; a submitted AL MLAR does not. No engine change, no regression run. 16 of 24. **Next: RC-4, C22-17 (the state layer).**

## Earlier (set 2026-10-01): chunk 22 RC-2 done

**Chunk 22 RC-2 done 2026-10-01** (`scripts/cf/215_chunk22_rc2.py --live`, 51 s): 8 priced multi-location policies (Value Reporting "Not Used" at Special and Broad + EQ, blanketed at Monthly Reporting, General Information incidental / acquired / seasonal, Additional Locations on two and three locations) **all agree with ISO**, 2,308 premiums field for field and every message; "Used" refused as predicted (OI-119). Hand = evaluator = engine on every record first. No engine change, so no regression run (the scaled-back rule). 12 of 24. **Next: RC-3, C22-13 (zero cases).**

## Earlier (set 2026-10-01): chunk 22 RC-1 done

**Chunk 22 RC-1 done 2026-10-01** (`scripts/cf/213_chunk22_rc1.py`, all checks pass, 1m47s, no ISO calls; tasks
[`CF-CHUNK22-TASKS.md`](CF-CHUNK22-TASKS.md), 6 of 24). **OI-119:** the rule that finds the largest contents limit reads its own running value
(`maxLimit`) before binding it. **ISO refuses every Value Reporting policy with average rates "Used"** (`214_oi119_probe.py --live`,
the same error as ours); every CW edition has the rule, so our engine already agrees and needs no change. Other findings:
one average rate per policy, copied to every contents row (a submitted one is overwritten); the Additional Locations
roll-up sums a field nothing writes and nothing reads (moves no dollar); either form switches the ordinary contents
premium off; the Value Reporting Form survives only on the five reporting coinsurance values. **Regression scaled back
(user, 2026-10-01):** no run after an RC unless the engine changed; `206_ --check` after an engine change; at the gate
`206_ --check` + `157_ --all`, and the full `104_ --gate` only if the engine changed in the chunk. **Next: RC-2, C22-07
("Not Used"); the "Used" golden cases become refusal cases.**

## Earlier (set 2026-09-30): chunk 21 GATED; next, chunk 22

**Chunk 21, sewer backup and condo options, GATED 9 of 9 on 2026-09-30, 21 of 21**
([`CF-CHUNK21-GATE.md`](CF-CHUNK21-GATE.md), tasks [`CF-CHUNK21-TASKS.md`](CF-CHUNK21-TASKS.md)): sewer backup on its
five parents, the condo unit-owners options (loss assessment, misc. real property; RI / FL / UT forms), Florida's
commercial units in residential condos. All 12 records ISO had never priced are ISO-confirmed, every figure predicted
by hand first (state-aware): 26 golden cases (25 agree + OI-116), 50 zero / message cases (all 24 messages), 15 name /
stat-code cases, all 46 states + the rewrite / FL / edition probes (61 of 61), the downstream total (+$651 / +$6,405)
and 1,648 stat values. **No engine change.** Regression: snapshot clean (1,127 requests), full gate run CLEAN (140
scripts, full grids, 19m20s), `157_ --all` 293 of 293. **504 of 546 countrywide premium files built (92%).** New open
items, none blocking: **OI-116** (ISO never attaches FL's SPP special-class condo record), **OI-117** (a blank
`Convert` refuses at ISO, we price), **OI-118** (form labels: a state's `Pages` table hides CW rows in ours); OI-103
gained three cases. Carried to chunks 22-26: their censuses now run the every-rule edition diff
(`scripts/cf/_edition_rules.py`); counts noted in each task list. **For live cases outside Oregon** use
`208_`'s `payload(sub, j)` (r11 writes Oregon's scheme) and `211_`'s state-aware `rows()` / `rule()`. **Next: chunk 22**
(multi-location: value reporting and special coinsurance; tasks set, `CF-CHUNK22-TASKS.md`).

## Earlier (set 2026-09-29): chunk 20 GATED; next, chunk 21

**Chunk 20, small coverages with their own tables, GATED 9 of 9 on 2026-09-29, 26 of 26**
([`CF-CHUNK20-GATE.md`](CF-CHUNK20-GATE.md), tasks [`CF-CHUNK20-TASKS.md`](CF-CHUNK20-TASKS.md)): Radioactive, Pier and
Wharf, Fire Department, Tobacco, the four special-limit items, ACP, Food, Mortgageholders, Fungus, Equipment Breakdown.
All 28 records ISO had never priced are ISO-confirmed: 20 golden cases, 62 zero / message cases (all 95 message rules by
level), 29 name / exclusion probes, all 46 states + 27 probes (73 of 73), the downstream total (+$977 / +$5,110) and
1,251 stat values. No engine change. Regression scoped: 6 of 6 CLEAN. **497 of 546 countrywide premium files built
(91%).** **CLOSED 2026-09-30:** OI-115 probed, fixed and closed (ISO skips a single blank `Subtract` operand in either
position; the engine now does, Property only; full regression 134 of 134), the stale blank-comparison comment fixed, the
every-rule edition diff carried into chunk 21's C21-16. Open: OI-103 (now also chunk 19 R1, which prices at Factor 1 where ISO refuses), the VT
empty-table question. **Regression streamlined 2026-09-30:** `104_` runs 6 at a time and samples the slow grids (`--gate` for full grids),
`206_snapshot_regression.py --check` answers "did anything move?" over every stored ISO payload. **Next: chunk 21** (sewer backup and condo options; tasks set, `CF-CHUNK21-TASKS.md`).

## Earlier (set 2026-09-29): chunk 20 OPEN, 22 of 26

**2026-09-29: chunk 20 RC-4 COMPLETE (C20-19 to C20-22), `203_chunk20_rc4.py --live`: all 46 states + 27 probes, ISO
73 of 73** (2,050 predicted records, 11,003 premiums). Run it in batches (`--runs`), one process each: the single
all-states run was stopped by Claude Code for low memory. Every state rewrite probed where it moves a dollar (AL / KS /
RI plan factor 0.85; FL empties the deductible-by-location factor and ignores the Fire Department higher limit; AZ Fire
Department off; VA volunteer fire department and Ordinance-or-Law fungus; NY no cyber factor on Mortgageholders / EB BI;
TX Mortgageholders, NC ACP, AK / NY fungus rating steps empty). **The every-rule edition diff found 6 differences where
the census's SetPremium-only check found 1**; ISO agrees on all 10 edition probes, including that **"50,000 > blank" is
true at ISO as in our engine** (our config comment says a comparison with a blank is false: the comment is stale, the
behaviour is right). **Next: RC-5, C20-23 (downstream), C20-24 (regression), C20-25 (census), C20-26 (gate).** Open:
OI-115 (needs the user's go).

## Earlier (set 2026-09-29): chunk 20 OPEN, 18 of 26

**2026-09-29: chunk 20 RC-3 COMPLETE (C20-15 to C20-18).** `201_chunk20_rc3.py --live`: 12 zero cases and 50 message
cases. Every one of the 95 message rule instances is fired at its own level, and each message is compared with ISO as a
(level, text) pair: ours from the message call's `TableName`, captured in the test; ISO's from the node carrying the
message id. `202_chunk20_c20-17-18.py --live`: 13 guarded-vs-overwritten probes and the four cyber factors. **ISO agrees on
everything except OI-115 (new, recorded, NOT fixed; needs the user's go):** ISO skips a blank FIRST operand of `Subtract`
(a Fire Department charge with no limit: ISO $3, ours $0; probe with Factor 2.0: ISO $17, blank-as-zero −$17, ours $2).
Submission facts: the CP 00 70 location message needs `UnitNumber` > 0; BI's fungus period is overwritten from the
policy fungus record; ACP prices $0 with the building's watercraft exclusion; computed fields submitted as overrides
must be typed as the XSD declares (ISO refuses strings). **Next: RC-4, C20-19 (all 46 states).**

## Earlier (set 2026-09-29): chunk 20 OPEN, 14 of 26

**2026-09-29: chunk 20 RC-2 COMPLETE (C20-06 to C20-14), `200_chunk20_rc2.py --live`: 20 golden cases, ISO 20 of 20
agree** (every premium and message on each policy). Four things the rules do that a submitter must know: **Radioactive
Contamination, unblanketed, prices on the parent coverage's limit, not its own** (its own limit is read only in a blanket
whose detail says "No"); **fungus's incremental charge is 10 × (forms − 1)** on a monoline policy; **EB's waiting-period
record uses the no-waiting-period factor − 1**; **Mortgageholders' `Limit` is text ("25,000")** and
`IncreasedPeriodOfRestoration` is text on the policy fungus record (ISO refuses the wrong type). **Next: RC-3, C20-15
(zero cases), C20-16 (messages), C20-17 / 18.**

## Earlier (set 2026-09-29): chunk 20 OPEN, 5 of 26

**2026-09-29: chunk 20 RC-1 COMPLETE (C20-02 to C20-05), `199_chunk20_rc1.py`.** The four families sitting at $0 on
stored policies are explained (293 of 293 stored responses, ISO $0 = ours $0) and switched on: Fire Department $85,
Tobacco $47 (set `CovForm` on the occupancy), patterns $14, BI fungus. All 28 records price with hand = engine on four
Oregon trees. Submission facts found: **EB ammonia / hazardous switch on only above $25,000**; **EB's BI waiting-period
record needs BI's no-waiting-period endorsement with a `TimePeriod`**; **jewelry needs `ValueIndicator`**; FL switches
off 14 records, AZ Fire Department. Blanket radioactive reads the blanket average rate when the blanket detail's
`RadioactiveContamination` is "Yes" (0.167: $159 / $321 vs own rates $94 / $383). 24 header-only state tables the
engine falls back through (chunk 19's VT question applies). **Next: RC-2, C20-06 (Fire Department, ISO live).**

## Earlier (set 2026-09-29): chunk 19 GATED; next, chunk 20

**Chunk 19, the scheduled property items, GATED 9 of 9 on 2026-09-29, 24 of 24**
([`CF-CHUNK19-GATE.md`](CF-CHUNK19-GATE.md), tasks [`CF-CHUNK19-TASKS.md`](CF-CHUNK19-TASKS.md)): Tenants' Building
Property / Glass, Antennas, Trees, Signs, Brands and Labels, Household, Leased, Temporarily Away, Manufacturers. All
57 records ISO had never priced (and FL's five glass files) are ISO-confirmed: 16 golden cases, 39 zero / message /
name / exclusion cases, the EQ tier layer, the state rewrites, every edition, all 46 states (49 of 49, 10,317
premiums), the downstream total. No engine change. Regression scoped with the user's go: 23 of 23 CLEAN (chunk 19 +
every script the hand-evaluator fix touched). **469 of 546 countrywide premium files built (86%).** Open: the VT
empty-table question (chunk 28), more OI-103 cases, FL / CA earthquake. **Next: chunk 20** (small coverages with their
own tables; tasks set, `CF-CHUNK20-TASKS.md`).

## Earlier (set 2026-09-29): chunk 19 OPEN, 21 of 24

**2026-09-29: chunk 19 C19-20 and C19-21 COMPLETE, 21 of 24.** C19-20 (`196_chunk19_c19-18_states.py --all --live`):
every family in all 46 states + the Public Institutional Plan in AL KS RI, **ISO 49 of 49** (3,098 records, 10,317
premiums). C19-21 (`198_chunk19_c19-21_downstream.py --live`): **Household Personal Property's limit joins the
occupancy's total amount of insurance and lowers the contents' own rate** (chunk 4's LOI lookup: $197 → $192),
so the prediction is the families' hand sum + the contents' hand-evaluated change: total +$1,941 and clean test
+$14,054, both predicted before the call and **equal at ISO**; terrorism untouched; 336 stat values on 81 stored
responses equal. **Next: C19-22 (regression, which also re-checks the Divide / Subtract evaluator fix), C19-23
(census 406 → 469), C19-24 (the gate).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 19 of 24

**2026-09-29: chunk 19 C19-19 COMPLETE, 19 of 24** (`scripts/cf/197_chunk19_c19-19_editions.py --live`). A rule-by-rule
diff of every family file across the four countrywide editions (the census had compared only the premium rules)
finds **4 files differ in CW 2023 V02 (MO)**: the special-class Group I rate is looked up under older option codes
(antennas 62, signs 12 / 13, trees 42; same rates; V02's table has no rows under the 2026 codes, so the probe
discriminates). MO (V02), NC (V03), MA (V04): **ISO agrees on 3 of 3**. **Next: C19-20 (all 46 states).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 18 of 24

**2026-09-29: chunk 19 C19-18 COMPLETE, 18 of 24** (`scripts/cf/196_chunk19_c19-18_states.py --live`): every chunk 19
family in AL AR DC FL GA KS NY RI TX VT MT + OR, plus the Public Institutional Plan in AL KS RI, each record from
that state's own premium rule: **ISO agrees on 15 of 15** (3,152 premiums). FL switches off the countrywide
tenants' and Temporarily Away records and prices glass through its own five files ($76 / $11 / $11); MT's
same-named files price nothing; NY prices Group II from its own territory tables, so its empty symbol tables are
never read. **`174_`'s hand evaluator now applies DecimalPlaces to Divide / Subtract** (GA exposed it: hand $239,
engine and ISO $238): the C19-22 regression re-checks every script that uses it. **Next: C19-19 (editions).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 17 of 24

**2026-09-29: chunk 19 C19-17 COMPLETE, 17 of 24** (`scripts/cf/195_chunk19_c19-17_eq_tiers.py --live`, 8 of 9
agree). The EQ sub-limit records attach from the location's EQ form (CP 10 45 percentage / CP 10 29 flat
dollar) and are removed otherwise; a tier a state does not rewrite reads a countrywide stub (factor 0: CO
Tier 1 prices EQ $0, and ISO agrees); factors interpolate inside the sub-limit band. **Open question: VT files
that stub header-only and ISO REFUSES the policy, while it fell back to the CW rows for VT's header-only
vacancy table (chunk 18) through an identical lookup; our engine falls back in both. Recorded in
`CF-ENGINE-FIX-EMPTY-STATE-TABLES.md`, not fixed (chunk 28 decision).** **Next: C19-18 (the formula rewrites
and FL's own glass files).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 16 of 24

**2026-09-29: chunk 19 RC-3 COMPLETE, 16 of 24** (`scripts/cf/194_chunk19_c19-15-16.py --live`, 12 of 12 agree).
C19-15: every rate / factor / coinsurance factor a family writes is `IsNull`-guarded (a submitted value is used);
the Group II symbol number and every on-switch are overwritten. C19-16: the cyber exclusion moves 23 of the 48
priced records at 10× limits (ISO 210 of 210); vandalism moves Group I only; windstorm collapses Group II to the
lowest rate × symbol 1 × 0.315; EQ sprinkler-leakage-only moves the tenants' EQ forms. **Next: RC-4, C19-17
(the EQ sub-limit deductible tiers for Antennas and Signs).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 14 of 24

**2026-09-29: chunk 19 C19-13 and C19-14 COMPLETE, 14 of 24** (`scripts/cf/193_chunk19_rc3.py --live`): 11 zero
cases and 16 message cases, **27 of 27 agree with ISO** (every premium, the whole message set), plus one predicted
refusal. Zero cases: blank tenants' deductibles price $0 with no message; a sign under $2,500 prices NEGATIVE on
every form (this corrected C19-09's note, which had the $2,500 on three forms only); Temporarily Away EQ on
"Not Applicable" is $0. **Manufacturers on a contents type with no factor row: ISO refuses the policy, we price $0
(OI-103).** Messages: all 21 fire; the "80% in Blanket" one fires on an unblanketed 80% contents row (ISO too);
the habitational class is copied down from the building; AL / RI read the plan flag on the occupancy.
**Next: C19-15 (shared names).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 12 of 24

**2026-09-29: chunk 19 RC-2 COMPLETE, 12 of 24** (`scripts/cf/192_chunk19_rc2.py --live`): 16 golden cases
across all nine families, **ISO agrees on all 16** (every premium and message). C19-11: Household prices on
the residential apartments contents rate; Leased Property on chunk 18's A4 policy gives the same Agreed Value
($20 / $2 / $13) as ISO's stored A4 response. C19-12: Temporarily Away Special $24 (theft covered, 0.2) vs $5
(the contents theft exclusion, 0.1); Manufacturers Stock vs Machinery and Equipment. **Next: RC-3, C19-13
(zero cases, including the blank tenants' deductible and Temporarily Away EQ on "Not Applicable").**

## Earlier (set 2026-09-29): chunk 19 OPEN, 10 of 24

**2026-09-29: chunk 19 C19-09 and C19-10 COMPLETE, 10 of 24** (`scripts/cf/192_chunk19_rc2.py --live`, now 10
golden cases, **ISO agrees on all 10**). Signs: `SignPlacement` decides the regime (detached: own rate metal
0.513 / other 1.188, own symbol 4 / 8; attached: copies the building's rates); EVERY form prices on
(limit − 2,500) ÷ 100 (corrected by C19-13: this first said Broad / Special / EQ only). Brands: rate = the smaller of the 0.053 cap and 0.10 × the contents' final
rate; a submitted contents rate of 0.70 makes the cap bind (Group I $47, not $62). **Next: C19-11 (Household,
Leased Property; Leased must agree with C18-06).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 8 of 24

**2026-09-29: chunk 19 C19-06 to C19-08 COMPLETE, 8 of 24** (`scripts/cf/192_chunk19_rc2.py --live`): 6 golden
cases, every family-own value checked against an independent lookup and every premium predicted before its
ISO call; **ISO agrees on all 6** (41 records, 801 premiums, messages equal). Tenants' glass with no deductible
(1.10 / 1.15) and at $250 (1.05; the EQ form reads the Broad row), scheduled and unscheduled; Antennas:
only Group II tells a broadcasting (AB) from a receiving (B) tower; Trees: Vermont's vehicle factor (1.15)
moves Group II $55 → $64. Outside Oregon, submitted rates must be numbers. **Next: C19-09 (Outside Signs).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 5 of 24

**2026-09-29: chunk 19 RC-1 COMPLETE, 5 of 24** (`scripts/cf/191_chunk19_rc1.py`, 34 checks, no ISO calls).
C19-04: hand = engine on all 233 switched-on nodes over 5 trees; all 63 records price. Payload facts found:
the contents need their OWN earthquake election (`EQCovIndicator`, `EQGrade`, their own EQ endorsement record);
Temporarily Away EQ prices only with the contents' `EQSprinklerLeakageOnly` "No" / "Yes" ("Not Applicable" →
$0, no message); Manufacturers' factor keys on the contents `CovType` and it is OFF when the contents are in a
blanket. C19-05: every table listed; the vehicle exclusion is 1.15 only in CT ME MA NH RI VT; header-only NY
symbol / FL tables fall back to CW (ISO to confirm in C19-17 / 18). **Next: RC-2, C19-06 (golden cases, ISO live).**

## Earlier (set 2026-09-29): chunk 19 OPEN, 3 of 24

**2026-09-29: chunk 19 C19-02 and C19-03 COMPLETE, 3 of 24** (`scripts/cf/191_chunk19_rc1.py`, 27 checks, no
ISO calls). The one stored policy with tenants' records (NM, unscheduled): ISO = ours = hand on all 10. What
switches the tenants' records: which container (scheduled / unscheduled), its `CovType`, its OWN
`CausesOfLoss`, and for earthquake its `EQCovIndicator` AND the building's earthquake election. Scheduled
glass limit = the container's `Limit`; each item its own `Limit`. **FL switches all 20 countrywide tenants'
records and all 5 Temporarily Away records off.** A blank tenants' deductible prices $0 with no message.
All 63 records attach. **Next: C19-04 (borrowed values).**

## Earlier (set 2026-09-29): chunk 18 GATED; next, chunk 19

**Chunk 18, the valuation and condition modifiers, GATED 9 of 9 on 2026-09-29, 23 of 23**
([`CF-CHUNK18-GATE.md`](CF-CHUNK18-GATE.md), tasks [`CF-CHUNK18-TASKS.md`](CF-CHUNK18-TASKS.md)):
Agreed Value, Inflation Guard, Functional Valuation, Rebuilding Expenses, Vacancy Permit, Peak Season.
All 84 records ISO had never priced are ISO-confirmed; all 46 states (49 of 50 agree, KS SPP an ISO
refusal, OI-103); one engine fix (empty state tables, Property only). **406 of 546 countrywide premium
files built (74%).** The regression was scoped with the user's go: chunk 18 scripts CLEAN; the full run
and `157_ --all` carried from 2026-09-28 (no engine change since). **Next: chunk 19** (scheduled
property items, [`CF-CHUNK19-TASKS.md`](CF-CHUNK19-TASKS.md); its Leased Property C19-11 must agree
with C18-06's A4).

## Earlier (set 2026-09-29): chunk 18 OPEN, 21 of 23

**2026-09-29: chunk 18 C18-20 and C18-22 COMPLETE, 21 of 23.** Downstream (`scripts/cf/190_chunk18_c18-20_downstream.py
--live`): the total moves by exactly the hand difference (+$2,520), the clean test +$2,554 was predicted before
its ISO call, chunk 9's blanket +$38 with only its own Agreed Value roll-up fields moving; terrorism untouched;
214 stat values equal. Found live: "Functional Valuation" as the valuation type moves the parents' rates AND
switches the family on; a Leased Property row prices the leased item itself. `166_`: **406 of 546 (74%)**.
Regression: chunk 18 scripts added, `187_` pinned; the full run was **stopped by Claude Code for low system
memory at 36 of 120, all passing**. **Next: rerun `104_ --jobs 4` (fewer jobs if memory is short) and
`157_ --all`, fill the two Confirmation lines in the drafted `CF-CHUNK18-GATE.md`, then gate.**

## Earlier pick-up (set 2026-09-28): chunk 18 OPEN, 19 of 23

**2026-09-28: chunk 18 RC-4 COMPLETE, 19 of 23** (`scripts/cf/189_chunk18_rc4.py --all --live`): 49 of
50 agree with ISO (2,352 predicted records, 8,747 premiums); the 50th is KS's Standard Property Policy,
which ISO refuses (OI-103). **ENGINE FIX (user's go): an empty state table no longer hides the
countrywide rows, Property only** ([`CF-ENGINE-FIX-EMPTY-STATE-TABLES.md`](CF-ENGINE-FIX-EMPTY-STATE-TABLES.md)):
VT's Vacancy Special was $0, ISO $87. Regression 115 of 115, `157_ --all` 293 of 293, all 87 stored
chunk 18 responses unchanged. The portable state policy now carries each state's own contents
territory and submits Group II base rates. CA's two earthquake-only rewrites remain untested.
**Next: RC-5, C18-20.**


**2026-09-28: chunk 18 RC-3 COMPLETE, 15 of 23** (`scripts/cf/188_chunk18_rc3.py --live`): 29 zero /
message / name / exclusion cases, ISO agrees on all 29. A reversed Vacancy period prices negative
(-$50); blank dates must be OMITTED (ISO refuses ""); Functional Valuation on Replacement Cost is
deleted; Value Reporting attaches only on a reporting coinsurance; SC's CP 01 10 attaches on
ValuationLaw "Exemption Does Not Apply". The fixed form-number census (`185_`) found no missed
message. **Next: RC-4, C18-16.**


**2026-09-28: chunk 18 RC-2 COMPLETE, 11 of 23** (`scripts/cf/187_chunk18_rc2.py --live`): 9 golden
cases, ISO agrees on every premium and message. Agreed Value reads the agreed limit (blanketed: the
blanket's AgreedVal average rate); Leased Property Agreed Value switches on from the contents row;
Inflation Guard is a % of the finished premium; the building and contents Functional forms differ;
Rebuilding needs a large amount to price every form; Vacancy discounts only its vandalism part.
ISO types AgreedValueLimit, UnitNumber, BlktIDNum, TotalLimit, FullValue as numbers.
**Next: RC-3, C18-12** (C18-13 first re-runs the fixed form-number message census).


**2026-09-28: chunk 18 RC-1 COMPLETE, 5 of 23** (`scripts/cf/186_chunk18_rc1.py`, all checks pass;
`--skip-stored` skips the 16-min stored re-rate). Every stored policy carries Agreed Value and
Inflation Guard switched off (option No / Not Applicable): ISO $0 = ours on all 293. Switched on:
Agreed Value $10, Inflation Guard 4% $5 (a factor × the building's finished premium). Agreed Value
"Yes" with no agreed limit prices $0 silently. **Functional Valuation attaches only when
`ValuationType` = "Functional Valuation"** (deleted otherwise). Vacancy's pro-rata factor = permit
days / policy days (0.247 by hand); payloads must carry the policy dates. Hand = engine on 53 of
84. TX files `…TX` subline tables no Vacancy file reads (check live in RC-4). **Next: RC-2, C18-06.**


**Chunk 18, valuation and condition modifiers, OPENED 2026-09-28; 1 of 23**
([`CF-CHUNK18-TASKS.md`](CF-CHUNK18-TASKS.md), census `185_chunk18_census.py`): Agreed Value,
Inflation Guard, Functional Valuation, Increase in Rebuilding Expenses, Vacancy Permit, Peak
Season. 84 premium records, **none ever priced by ISO** (Agreed Value and Inflation Guard sit at
$0 on every stored policy); 54 messages, every Agreed Value one found only by form / wording;
30 files differ in MO's CW 2023 V02; Vacancy Permit and Peak Season use date arithmetic;
Vacancy Permit has 9 state rewrites. **Next: C18-02** (why the stored records price $0).
Closing chunk 18 takes the build to 406 of 546 (74%).

**Chunk 19, scheduled property items, TASKS SET 2026-09-28; 1 of 24; starts after chunk 18
gates** ([`CF-CHUNK19-TASKS.md`](CF-CHUNK19-TASKS.md), census `900_chunk19_census.py`): Tenants'
Building Property / Glass, Antennas, Trees, Signs, Brands and Labels, Household, Leased Property,
Temporarily Away, Manufacturers Consequential Loss. 63 premium records + 5 state-only glass
records (FL only; MT files the names without a premium rule); 57 of the 63 never priced by ISO; identical in all four
editions; Antennas and Signs "rewritten" in all 46 states but mostly the EQ sub-limit tier
lookup. Leased Property waits on C18-06. **Census bug found:** `185_`'s form-number regex held
backspace characters, so chunk 18's form search matched nothing from files; re-run it at C18-13.

**Chunk 20, small coverages with their own tables, TASKS SET 2026-09-28; 1 of 26; starts after
chunk 19** ([`CF-CHUNK20-TASKS.md`](CF-CHUNK20-TASKS.md), census `901_chunk20_census.py`, which now
reads form numbers from the package's Form Pages table and flags sibling file names): 30 premium
records (28 + 2 NC-only), none priced by ISO; Fire Department, Tobacco, the furs / jewelry /
patterns / stamps limits and BI fungus sit at $0 on stored policies; Mortgageholders E&O is a
five-layer, policy-level coverage form; 95 distinct messages; one MO edition difference.

**Chunk 21, sewer backup and condo options, TASKS SET 2026-09-28; 1 of 21; starts after chunk
20** ([`CF-CHUNK21-TASKS.md`](CF-CHUNK21-TASKS.md), census `902_chunk21_census.py`): 7 premium
records + 5 FL-only (a manual premium gated on coverage form / type / policy type), none priced
by ISO or on a stored policy; Sewer's 8 tables are one 2-row rate plus codes; loss assessment is
tiered arithmetic (21 rules); the condo options have four form numbers (CW, RI, FL, UT); no cyber
factor anywhere; 26 messages; identical in all four editions.

**Chunk 22, multi-location (value reporting and special coinsurance), TASKS SET 2026-09-28; 1 of
24; starts after chunk 21** ([`CF-CHUNK22-TASKS.md`](CF-CHUNK22-TASKS.md), census
`903_chunk22_census.py`, which adds a multi-location trail): 16 premium records, none priced by ISO
and no stored multi-location policy at all. The five average rates (MLARs) have **three writers**;
the main ruleset, Personal Property (9 state rewrites), Occupancy and chunk 9's Blanket Rating Detail
already touch them, so all 293 stored policies must re-rate unchanged. The plan's "resets the
Contents premium" is a roll-up of Additional Locations premiums onto General Information.

**Chunk 23, state-only coverages, TASKS SET 2026-09-28; 1 of 22; starts after chunk 22**
([`CF-CHUNK23-TASKS.md`](CF-CHUNK23-TASKS.md), census `904_chunk23_census.py`, which enumerates every
in-force state-only premium file and assigns an owner): 80 files, none unassigned. Chunk 23 owns 10
(MA heating oil and tenant relocation, AK attorneys' fees, CA Additional / Limited EQ) and closes
chunk 12's open VA Ordinance or Law priced cases (41 files); none priced by ISO. CA's next packages
change a Limited EQ formula (OI-105). MT's glass files carry no premium rule (chunk 19 corrected).

**Chunk 24, Builders Risk, TASKS SET 2026-09-28; 1 of 25; starts after chunk 23**
([`CF-CHUNK24-TASKS.md`](CF-CHUNK24-TASKS.md), census `905_chunk24_census.py`, which adds a Builders
Risk trail): 20 premium records (the plan card's "adds 17" was wrong); ISO has priced only BR theft
(144 stored responses); materials of others is a manual premium at $0 on all 364; premium adjustment
works on dated reporting periods; 16 states rewrite (not 9), 5 with their own premium rule. Business
Income, blanket, unmanned aircraft, antennas BI, CA O&L and FL Pollutant already read the Builders
Risk factors; 149 stored policies have Builders Risk on, and all 293 must re-rate unchanged.

**Chunk 25, Flood, TASKS SET 2026-09-28; 1 of 26; starts after chunk 24**
([`CF-CHUNK25-TASKS.md`](CF-CHUNK25-TASKS.md), census `906_chunk25_census.py`, which adds a flood
trail): 6 premium records + WV's 2 Ordinance or Law flood forms; ISO priced 3 on one stored policy;
705 KB of rules, 27 tables. Loss cost comes from 37 states' tables, 7 states' county tables, or
nothing at all (AK, FL). Much of flood already lives in built Structure, Location and the main
ruleset. It closes chunk 17's Off-Premises flood factor and takes the count to 546 of 546.

**Chunk 26, Specific and Tentative rating, TASKS SET 2026-09-28; 1 of 23; starts after chunk 25**
([`CF-CHUNK26-TASKS.md`](CF-CHUNK26-TASKS.md), branch census `907_chunk26_census.py`): no new files;
7 CW files / 33 rules; 41 states have their own rating-type rules, 36 rate Specific Group II by
hazard level and floor area, 10 rewrite Group I; CA adds a fourth rating type (One-Term Loss Cost).
**Not zero evidence**: ISO priced 566 Specific and 5 Tentative buildings in stored requests (14
states), so RC-1 replays them first. Contents and occupancy copy the rating type down.

**Chunk 27, open gate points on closed chunks, TASKS SET 2026-09-28; 1 of 18; can run beside any
chunk** ([`CF-CHUNK27-TASKS.md`](CF-CHUNK27-TASKS.md), census `908_chunk27_census.py`, which enumerates
every gate file and open item): point 9 (messages) owed on chunks 1–8, closable for 1–6 from C13-27's
293-response evidence; **chunk 7 has a real gap (ISO 3 messages, engine 5)**; point 8 on chunk 8 (CA / FL
Legal Liability); TX / DC / IL / MT / NY per-state gaps; chunk 12's two leftovers; OI-101, 105, 106, 112
and **OI-114, which has no register row**. The card's "point 2 on chunks 6 and 8" was already passed.
Each item ends closed with evidence or handed to chunk 28; no engine code. **Next: C27-02.**

## Earlier pick-up (set 2026-09-28): chunk 17 GATED; next, chunk 18

**Chunk 17, the Business Income add-ons, GATED 9 of 9 on 2026-09-28, 23 of 23**
([`CF-CHUNK17-GATE.md`](CF-CHUNK17-GATE.md), tasks [`CF-CHUNK17-TASKS.md`](CF-CHUNK17-TASKS.md)):
Ordinary Payroll, Power Heat and Refrigeration, Mining BI, Landlord Rental Value, Watercraft
Buyback, Off-Premises Interruption. All 32 records ISO had never priced are now ISO-confirmed:
10 golden cases, 30 zero / message / exclusion cases, all 46 states + 10 probes (9,039
premiums), downstream total +$1,969 and clean test +$2,643 as predicted. No engine change.
Regression CLEAN for chunks 0–17 (115 scripts); `157_ --all` 293 of 293. **322 of 546
countrywide premium files built (59%).** Open: two more OI-103 cases; Off-Premises' flood
factor waits on chunk 25. **Next: chunk 18** (valuation and condition modifiers: Agreed Value,
Inflation Guard…), easiest-first plan on `CF-BUILD-STATUS.html#remaining`.

**How to run things now (streamlined 2026-09-30):**
- **After any engine change, first:** `206_snapshot_regression.py --check` (~4 min): re-rates all 970 stored ISO
  payloads and lists every premium / rate / factor / switch that moved (601,115 fields). Refresh with `--baseline`
  after an intended change.
- **Regular full run:** `104_` (6 at a time; the six slow exhaustive scripts run a deterministic sample of their
  grids via `scripts/cf/_regress.py`). **At a chunk gate:** `104_ --gate` (full grids).
- `--quick` (golden cases + the current chunk, no GL) after each RC; every long pass prints `[i/n elapsed]` to
  `results/cf-raas/logs/`.
- The engine now caches parsed rule files, the rule directory listing and `book_for` per process: a repeat
  rating takes ~0.15 s (was ~2 s); the snapshot proved it identical. `174_` now caches `book_for`: 612 s -> 129 s run alone,
output identical (2026-09-28). `178_`'s ~11 min is ~100 genuine re-ratings, not discovery.

## Earlier pick-up (set 2026-09-25): chunks 15 and 16 CLOSED; chunk 17 OPEN

**2026-09-28: chunk 17 RC-4 COMPLETE, 19 of 23** (`scripts/cf/183_chunk17_rc4.py --all --live`):
all 46 states + 10 probes, 56 of 56 agree with ISO (1,344 predicted records, 9,039 premiums,
messages equal), every state from its own edition. CT prices no Landlord Group I (empty
`ErcRate`); KS / NY price Landlord Broad and Special on a Standard Property Policy, VT Broad
only; AK drops insurance-to-exposure, AR DC NY RI the wind-hail factor; FL switches
Off-Premises off on residential classes. Passes now stream `[i/n elapsed]` progress to
`results/cf-raas/logs/`; `pkgs()` is cached (2.5 min -> 10 s a policy). **Next: RC-5, C17-20.**

**2026-09-28: chunk 17 RC-3 COMPLETE, 15 of 23** (`scripts/cf/182_chunk17_rc3.py --live`):
30 cases (14 zero, 10 message, 2 submitted-value, 4 exclusion); ISO agrees on all 29 it
rated, whole message sets equal. Blank payroll days price like 0 days (not $0); a blank
Off-Premises extended period is $0 but "Not Applicable" prices; Off-Premises reads no cyber
factor; every family factor keeps a submitted value. Two more OI-103 cases: Watercraft option
"Not Applicable" and FL's EQ building-height table (ISO refuses, we price). 4 Watercraft
messages the census missed now tested. RC-1/RC-2 committed `54f34b3`.

**2026-09-28: chunk 17 RC-2 COMPLETE, 11 of 23** (`scripts/cf/181_chunk17_rc2.py --live`):
10 golden cases, every one of the 32 records priced by ISO for the first time; engine = hand =
ISO on every premium on each policy and every message. ISO confirms Landlord Broad has no loss
cost multiplier, Landlord EQ uses Business Income's EQ limit, Special Class Landlord keys its
base rates on a hardcoded Frame, Mining ignores its own limit outside a blanket. At chunk 10's
EQ class A1 the 0.06 EQ riders round to $0 (a zero case). 

**2026-09-28: chunk 17 RC-1 COMPLETE, 5 of 23** (`scripts/cf/180_chunk17_rc1.py`, all checks
pass, no ISO calls, no engine change). The $0 fixtures: none of the 82 Watercraft fixtures
sets `WaterfrontProperty`; the 3 Mining fixtures pick option None. Found: Business Income
**deletes Mining rows unless its `TypeOfRisk` is Mining**; Special Class BI spells the input
`WaterFrontProperty`; Landlord Broad / Special switch on the Landlord record's **own**
`CauseOfLoss`; a blank Off-Premises extended period prices $0; Watercraft option "Not
Applicable" has no factor row. Hand = engine on 26 of 32 records (the 6 EQ riders need
earthquake: RC-2). Chunks 15–16 are committed (`b84d8f1`).

**Chunk 16, "already matched ISO: gate them", GATED 9 of 9 on 2026-09-25, 23 of 23**
([`CF-CHUNK16-GATE.md`](CF-CHUNK16-GATE.md), tasks [`CF-CHUNK16-TASKS.md`](CF-CHUNK16-TASKS.md)):
BI no waiting period, Extended Period of Indemnity, Civil Authority, Pollutant Clean Up,
Spoilage, Molten Material, state-only Mine Subsidence. ISO agreed on everything it rated:
the 27 never-priced records, 32 zero / message / exclusion cases, all 46 states + 6 probes
(8,342 premiums), and the downstream total (T1 $2,832; clean test T2 predicted first,
$3,183). Regression CLEAN for chunks 0–16 (110 scripts); `157_ --all` 293 of 293. No engine
change. **290 of 546 countrywide premium files built (53%).** Findings worth knowing: Pollutant
Clean Up's location rate is the last building's unless the special class's is higher, and
goes negative below a $10,000 limit; FL and RI truncate Spoilage's limit / 100; Texas computes
a Spoilage factor it never uses; ISO honours a submitted `Factor`. Open, not blocking: one
more OI-103 case (Mortgageholders E&O with no limit).

**Chunk 15, the manual-premium endorsements, GATED 9 of 9 on 2026-09-25, 21 of 21**
([`CF-CHUNK15-GATE.md`](CF-CHUNK15-GATE.md)); OI-114 (`rul:Null` in the 2020 edition) open.

**Chunk 17, Business Income add-ons, OPENED 2026-09-25; 1 of 23** ([`CF-CHUNK17-TASKS.md`](CF-CHUNK17-TASKS.md),
census `179_chunk17_census.py`): Ordinary Payroll, Power Heat and Refrigeration, Mining BI,
Landlord Rental Value, Watercraft Buyback, Off-Premises Interruption. 32 premium records,
**none ever priced by ISO**; Landlord (5 states) and Off-Premises (6 states) carry the state
rewrites; identical in all four editions. **Next: C17-02** (why 82 Watercraft fixtures price $0).
**No engine code without the user's go.**

## Earlier pick-up (set 2026-09-25): the remaining build is planned as chunks 15–28, easiest first

**2026-09-25: every remaining item is now a chunk.** `scripts/cf/166_remaining_coverage_census.py`
sized it: of 546 countrywide premium files, chunks 0–14 own **228 (42%)**; the other 318 fall
into 53 families (none unmapped), plus 75 state-only premium files. Earthquake riders count
with their parent coverage (44 riders on unbuilt coverages are not chunk 10's). The plan,
with every family, file count, state rewrite and ISO evidence held, is on
[`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining):

15 manual-premium endorsements (S) · 16 families already matching ISO on stored responses:
gate them (S) · 17 Business Income add-ons incl. Off-Premises Interruption (M) · 18
valuation and condition modifiers: Agreed Value, Inflation Guard… (M–L) · 19 scheduled
property items (M) · 20 small coverages with their own tables (M) · 21 sewer backup and
condo options (M) · 22 value reporting form and Additional Locations Special Coinsurance
(L) · 23 state-only coverages incl. MA heating oil (M) · 24 Builders Risk (L) · 25 Flood
(XL) · 26 Specific/Tentative rating (L) · 27 open gate points on chunks 1–8 (M) · 28
engine behaviour decisions: OI-103, validation, OI-113 (L, each needs a go).

**Chunk 15 OPENED 2026-09-25; closed 21 of 21 (above)** ([`CF-CHUNK15-TASKS.md`](CF-CHUNK15-TASKS.md),
census `167_chunk15_census.py`): 23 files, one formula (`ManualPremium` × package mod ×
multi-premium credit × IRPM) in 4 variants that round 3, 2 or 1 times; modifiers read
at 7 different `../` depths; 0 tables; one message (Interruption of Computer Operations,
$2,500 minimum); GA/TX/VA empty `ErcRate`, FL forces $0. **RC-1 COMPLETE 2026-09-25,
5 of 21** (`168_chunk15_rc1.py`, all checks pass): every record attaches and rates as
filed; IRPM and package discount always come from the **policy**; the multi-premium
credit from the parent coverage (policy for 4 records), except **Valuable Papers, which
reads the building's**; five records need their own on-switch (Valuable Papers: its
Contents row's `CovType`). **RC-2 COMPLETE 2026-09-25, 10 of 21** (`169_chunk15_rc2.py
--live`): one golden case per variant plus all 23 records on one policy, engine 27 of 27,
ISO 27 of 27, every premium equal, messages identical; ISO confirms Valuable Papers reads
the building's credit. Live payloads need `WindstormOrHailDeductible` set (OI-103).
Messages about these endorsements also sit in parent rule files (C15-13). **RC-3
COMPLETE 2026-09-25, 14 of 21** (`170_chunk15_rc3.py --live`): 22 zero / exclusion /
message cases, engine 22 of 22, ISO 21 of 21 rated, messages identical; ISO refuses a
policy package discount of 0 (added to OI-103). A Contents row's `CovForm` is copied from
its occupancy: set it there. **RC-4 COMPLETE 2026-09-25, 18 of 21** (`171_chunk15_rc4.py
--live`): all 23 records in all 46 states, ISO 46 of 46 (7,836 premiums, every message);
states only switch families off: GA, TX, VA, FL, and MO (its CW 2023 V02 edition has no
Discretionary Payroll premium rule). VA 2021: ISO $927 (the 2020 policy rule overwrites a
supplied IRPM). New OI-114 (`rul:Null` test, old editions only); two more OI-103 cases.
FL payloads need an FL-filed special class (not "Towers - Broadcasting Antennas").
**Next: RC-5, C15-19** (downstream: total, terrorism, stat codes), then regression, gate.
**No engine code without the user's go.**

## Earlier pick-up (set 2026-09-24): chunks 0–14 are all CLOSED; next, the unbuilt coverages

**Every chunk in the plan is closed and committed** (chunk 14, policy assembly, gated 9 of 9
in `1b15ada`; regression CLEAN for chunks 0–14, 100 scripts). The user chose the next
direction on 2026-09-24, in this order:

1. **TOP ITEM: the coverages not yet built.** The value reporting form (drives
   multi-location average rates and the AR/DC peril-exclusion stat codes); the Additional
   Locations Special Coinsurance endorsement (`ErcResetPrsnlPropPremiumForAdditionalLocations`;
   inventory B9); Off-Premises Interruption of Business, vehicles and mobile equipment
   (inventory D8; AK's Option A stat code); MA heating-oil remediation and tenant relocation;
   the Condominium Commercial Unit-Owners Optional Coverages (inventory rows ~260).
   **Start by** reading `CF_Algorithm/Coverage_Inventory_And_Tracking.md` for these families,
   then propose an order and a chunk plan (census first). **No engine code without the
   user's go.**
2. Chunk 4's gate point 9 (messages): likely closable from C13-27's evidence; verify.
3. OI-103 (ISO refuses where we price; a dozen concrete cases now), an engine change: needs a go.
4. OI-113 (minimum premium, refer to company): needs a referral layer.
5. OI-112, OI-106: no premium effect.

### Earlier: chunk 13 closed (2026-09-24), then chunk 14

**Chunk 13, Terrorism / TRIA, gated 2026-09-24, 30 of 30, 9 of 9**
([`CF-CHUNK13-GATE.md`](CF-CHUNK13-GATE.md)). Terrorism is a premium on every coverage,
rolled up to the policy by a disclosure record (25% cap in CA, DC, IL, MD, NY, VA). Golden
case $8 (Oregon) and all five groups ISO-confirmed; all 46 states clean against their own
rows and rules; ISO agreed on every terrorism figure it rated (587 of 587). One engine fix,
OI-111 (named ancestors, the 10th authorized fix). **Regression CLEAN for chunks 0–13, 73 of
73.** Florida now resolves to its V02 package (added by the user, as the records asked):
chunk 6's C6-11 and chunk 11's F2 were re-derived for it. Open, not blocking: OI-112 (a
deductible-form message on older editions, no premium impact), OI-103, OI-106.

**Chunk 14, policy assembly, GATED 2026-09-24; 22 of 22** ([`CF-CHUNK14-TASKS.md`](CF-CHUNK14-TASKS.md),
census `156_chunk14_census.py`). Minimum premium is not in ISO's rating for our 46 states
(empty tables, no reader). **RC-1 COMPLETE 2026-09-24** (`157_`, `158_`, in the regression): every premium (14,236) and the
policy total (293 of 293) equal ISO on the stored responses; state overrides of the total only add
records; negative premiums count, as at ISO. **Minimum premium: a company input, refer to company (user decision; OI-113, backlog).** **RC-2 COMPLETE 2026-09-24** (`159_`): golden policy total $1,193 and 8 variants, ISO 9 of 9; the total adds whole-dollar premiums. **RC-3 COMPLETE 2026-09-24** (`160_`): IRPM (Oregon plus NY, MO, GA, VA, NE, whose caps and messages differ independently), package modification, multi-premium credit, Standard Property Policy (0.98 at the cause-of-loss step; eligibility is messages only), multi-location rates; engine 23 of 23, ISO 23 of 23. MO IRPM with a blank expense category refuses at ISO (OI-103). **RC-4 COMPLETE 2026-09-24** (`161_`, `162_`): all 12,547 stat values on the 293 stored ISO responses equal ours, compared strictly as text; state earthquake codes ISO 4 of 4 live. **RC-5 COMPLETE, chunk 14 GATED 9 of 9 on 2026-09-24** ([`CF-CHUNK14-GATE.md`](CF-CHUNK14-GATE.md)): all 46 states ISO 92 of 92; zero cases 11 of 11 (ISO refuses a combined modifier of 0 or 2.00+, OI-103); full replays clean; regression CLEAN for chunks 0–14 (100 scripts). Live state payloads: `r11.payload` always writes Oregon, so retarget `State` and `ProductName`.
**RC-2 COMPLETE 2026-09-24** (`159_`): golden policy total $1,193 and 8 variants, ISO 9 of 9 field for field; the total adds whole-dollar premiums and counts negatives. Next: RC-3 (C14-10, IRPM). **At every chunk close-out also run `python scripts/cf/157_chunk14_c14-02_total_replay.py --all`** (the regression runs its 46-fixture sample).

### Chunk 12 close-out (2026-09-24)

**Chunk 12 gated 2026-09-24, 42 of 42** ([`CF-CHUNK12-GATE.md`](CF-CHUNK12-GATE.md)):
all six endorsement families 9 of 9, 0 unexplained messages. Ordinance or Law K7
was re-run live after the OI-109 fix and agrees (8 of 8). The regression was re-run
2026-09-24: **CLEAN** for chunks 0–12 and all GL suites.

**Chunk 13, Terrorism / TRIA, OPENED 2026-09-24 at 1 of 30**
([`CF-CHUNK13-TASKS.md`](CF-CHUNK13-TASKS.md), census `143_chunk13_census.py`).
Tasks are in five release-candidate groups, in priority order. **Start at RC-1:
C13-02 (rule order) and C13-03 (replay the 14 stored ISO responses that carry a
terrorism premium).** Both DONE 2026-09-24; C13-03 found **OI-111** (a named
`ancestor::` read as the document root), **fixed with the user's authorization,
the 10th engine fix**: replay 14 of 14, regression clean. **RC-1 COMPLETE 2026-09-24** (C13-04 operand types clean; C13-05 attach map: `TRIAType` drives every terrorism form, `TerrorismIndicator` switches nothing). **RC-2 COMPLETE 2026-09-24**: Oregon golden case $8 (`149_`) and the other four groups + every roll-up record (`150_`), derived by hand and ISO-confirmed live, 14 of 14 policies field for field; Oregon's fire exception and the TRIA proration confirmed. **RC-3 COMPLETE 2026-09-24** (`151_`): TRIA timeline, all five form families, sub-limit, zero cases, override and literals; engine 36 of 36, ISO 34 of 35 live (one refusal: an unfiled territory, OI-103). ISO also charges terrorism when `TerrorismIndicator` is "No". **RC-4 COMPLETE 2026-09-24** (`152_` in the regression, `153_` live): all 46 states, every territory tier, clean against their own rows and rules (290 cases); ISO agrees on every state case it rated (245 of 245). The 25% terrorism cap (CA, DC, IL, MD, NY, VA) caps the policy charge, not the coverage premiums. **Next: RC-5 (C13-23 to C13-30), confirmation and close-out.** Then chunk 14, policy assembly.
Open from the chunk 12 gate, not blocking: priced FL/VA/WV cases, and a theft
exclusion attached to the Contents/BI records for drones and Dependent Properties.

### Chunk 12 history (as of 2026-09-23)

**All six families are closed, gated 9 of 9 and ISO-confirmed live.** Group G,
Dependent Properties: [`CF-CHUNK12-DEPENDENT-PROPERTIES.md`](CF-CHUNK12-DEPENDENT-PROPERTIES.md)
($80 + $12, 12 of 12 live). **One step left:**
1. ~~**C12-41:**~~ done: the regression now covers chunks 0–12 and ran
   **CLEAN** on 2026-09-23 (`python scripts/cf/104_chunk10_c10-21_regression.py`).
2. **C12-42:** file `docs/CF-CHUNK12-GATE.md` (six families, nine points each;
   the evidence is in the seven `CF-CHUNK12-*.md` records), then mark chunk 12
   closed on the status page.

**Engine changes this session (user-authorized, regression clean after each):**
OI-108 (`Sum` finishes before a `Break` ends the loop), and OI-109/OI-110
(Property's `Product` skips a null operand as ISO does, each skip recorded in
`Interpreter.null_skips`; GL untouched).


**Groups E and F closed 2026-09-23.** Unmanned Aircraft
([`CF-CHUNK12-UNMANNED-AIRCRAFT.md`](CF-CHUNK12-UNMANNED-AIRCRAFT.md)): $187
golden, 10 of 10 live. Green Upgrades
([`CF-CHUNK12-GREEN-UPGRADES.md`](CF-CHUNK12-GREEN-UPGRADES.md)): $33 golden,
no fixtures, 8 of 8 live. **Next: Group G, Dependent Properties
(C12-35 to C12-40), then H (fold chunk 12 into the regression, file the
gate).** Nothing from 2026-09-23 is committed yet; the user decides when.


**Groups C and D closed 2026-09-23.** Ordinance or Law
([`CF-CHUNK12-ORDINANCE-OR-LAW.md`](CF-CHUNK12-ORDINANCE-OR-LAW.md)): $198
golden, 7 of 8 live, and the one divergence, **OI-109** (absent B/C limits: ISO $0), since fixed. Utility Services
([`CF-CHUNK12-UTILITY-SERVICES.md`](CF-CHUNK12-UTILITY-SERVICES.md)): $15 + $4
direct damage, $9 + $4 time element, 10 of 11 live. The live comparer for any
family is `132_chunk12_family_raas.py`. **Next: Group E, Unmanned Aircraft
(C12-23 to C12-28)**, OI-108 (fixed 2026-09-23) is in its path.


**Group B, Debris Removal, closed 2026-09-23: gated 9 of 9 and ISO-confirmed
live** ([`CF-CHUNK12-DEBRIS-REMOVAL.md`](CF-CHUNK12-DEBRIS-REMOVAL.md)). Golden
case $49 + $6 = $55 (`127`), gates `128`, live `129` (9 of 12 agree; the 3
refusals are Earthquake lookups in old fixtures, added to OI-103). ISO itself
returns a negative premium for a limit under $25,000 (message M-003), and
charges a "No Coverage" building. **Next: Group C, Ordinance or Law
(C12-11 to C12-16)**, including Virginia's and West Virginia's state-only
forms.


**Group A closed 2026-09-23** ([`CF-CHUNK12-GROUP-A.md`](CF-CHUNK12-GROUP-A.md)).
Family order confirmed as recommended. Nothing ever deletes an endorsement
record; 17 of 17 ISO fixtures with a chunk 12 record rate end to end;
Ordinance or Law is 100 files, not 55 (Virginia's and West Virginia's
state-only forms). **One suspected engine gap, logged, not fixed: OI-108**
(a blanket drone's limit reads 0 in CA, NC and MO). Fixing it is an engine
change and needs the user's go. (Group B has since closed; see above.)

**Opened 2026-09-22.** [`CF-CHUNK12-TASKS.md`](CF-CHUNK12-TASKS.md) ·
[`123_chunk12_census.py`](../scripts/cf/123_chunk12_census.py). 42 tasks in 8 groups:
A (opening: sequence, attach map, operand types, EQ riders), then one six-task
group per family (B Debris Removal, C Ordinance or Law, D Utility Services,
E Unmanned Aircraft, F Green Upgrades, G Dependent Properties), then
H (regression and gate).


**Chunk 11 (Leasehold Interest) is CLOSED 2026-09-22: 24 of 24 tasks, gated 9
of 9** ([`CF-CHUNK11-GATE.md`](CF-CHUNK11-GATE.md)). The golden case matched ISO
live to the digit. Four engine fixes, all user-authorized and ISO-confirmed:
date comparison, the `01/01/0001` sentinel (OI-102), 0^0 (OI-104), and the
`DateDifference` sign (OI-107). Regression clean, 69 of 69.
**Backlog (none blocking):** OI-101 (closes with OI-105), OI-103, OI-105,
OI-106, and the GL ERP check left by OI-107. See the gate's backlog table.

### Chunk 11 history

**Chunks 0–10 are closed. Chunk 11 is OPEN at 21 of 24 tasks (2026-09-22; A–F done).** Earlier status line:
Groups A–D are done.** Group D ([`CF-CHUNK11-GROUP-D.md`](CF-CHUNK11-GROUP-D.md)): shared machinery is
clean. It found that ISO fixed OI-101 in its 2027 edition, that form names don't
resolve project-wide (OI-106, no premium impact), and that OI-104 is easy to
reach (an LI structure with no LI record crashes our engine).
**Earlier (still true):
Groups A (the annuity), B (the four sub-coverages) and C (zero cases, asked
live at ISO) are done.** Group C: [`CF-CHUNK11-ZERO-CASES.md`](CF-CHUNK11-ZERO-CASES.md).
ISO agreed on 11 of 14 and diverged on 3, all predicted. **OI-102 has since been fixed** (a blank date now orders as the earliest date, as at ISO; regression clean). OI-103 and OI-104 remain open.
**Send live ISO calls at 2026-09-17, not 2027**: ISO holds a newer Oregon
edition for 2027 than our local corpus (OI-105). Group B
([`CF-CHUNK11-GROUP-B.md`](CF-CHUNK11-GROUP-B.md)) found that only Tenants
Lease is discounted, and that Special without a Theft Exclusion prices at $0
by ISO's own rule (**OI-101**, owed a live ISO call). The golden case matches
at **$268 BGI + $30 BGII** (`114_chunk11_golden_case.py`,
[`CF-CHUNK11-GOLDEN-CASE.md`](CF-CHUNK11-GOLDEN-CASE.md)). One authorized engine fix:
ordered comparisons now accept two dates
([`CF-ENGINE-FIX-DATE-COMPARE.md`](CF-ENGINE-FIX-DATE-COMPARE.md)). The regression is clean.
**Done 2026-09-22 after Group D:** the one-command regression now covers **chunks 0–11**, and **OI-104 is fixed** (0^0 = 1, as ISO; an LI structure with no LI record now prices $0 instead of crashing). Regression clean.
**Groups E and F done 2026-09-22** ([`CF-CHUNK11-GROUPS-E-F.md`](CF-CHUNK11-GROUPS-E-F.md), 46 states): the inventory is clean, and Florida runs the 2023 chain without injection guards. **OI-107 (our `DateDifference` had the wrong sign; ISO +257, ours −257, confirmed live on Oregon's TRIA field) was fixed the same day with authorization.**
**Left in chunk 11:** C11-09 (messages), C11-22 (ISO golden + rounding tie), C11-24 (close-out regression). The tasks are grouped by
theme on `CF-BUILD-STATUS.html`.

**Two input rules every LI submission needs**, both silent if missed: the
Structure's own `CovType` must be `Leasehold Interest` (plus
`PolicyType = Commercial Property Policy`), or the LI record is deleted; and
`EQCovIndicator` must be `No Coverage`, not blank, or the EQ cell switches on.
[`CF-CHUNK11-TASKS.md`](CF-CHUNK11-TASKS.md) ·
[`106_chunk11_census.py`](../scripts/cf/106_chunk11_census.py)

**Confirm everything is green in one command** (this is new — it used to be a
page of scripts to run by hand):

    python scripts/cf/104_chunk10_c10-21_regression.py

**Four things the chunk 11 census already found, before any task has run:**

* **32 rule files, but only 21 of them rate.** The 11
  `FactorsFor<N>Percent` files (5% through 15%) declare `InitializeRuleSet` /
  `CalculateTotalPremium` / `ErcProcess` and nothing else — printed
  form-attachment markers, no `Lookup`, no `Premium`, no factor.
* **"Its own datadef group" is 32 groups, not 1** — one per file. Gate points
  6 and 7 are per-group questions, so chunk 11 asks them across 32 groups
  against the 5 that chunks 6–10 worked with. **The biggest structural jump
  in the plan so far**, and a counting fact rather than an estimate.
* **The fifth form is Earthquake.** Chunk 10 is a direct input here, not a
  parallel track — the first coverage opened *after* the form it depends on
  was built.
* **Zero ISO fixtures.** Of 364 CF payloads, **0** mention Leasehold
  Interest. This is chunk 9's situation, not chunk 10's: confirmation has to
  come from a **live ISO call**, and that is planned at task 1 rather than
  discovered at task 22.

**The single sharpest thing to be careful about:** the `rul:Power` — the only
one in all 882 countrywide rule files — sits behind an `IsNull` guard on
`DiscFactorRaisedToNumOfMonthsRemainingAtInception`. A submission that
supplies that value directly **bypasses the annuity entirely, and no ISO
comparison catches it, because ISO has the same guard.** That is the standing
"a submission can populate a derived field" trap, in the one chunk whose
exposure is computed rather than entered.

---

### The historical record, chunk by chunk

**Chunk 3 is closed — gated 8 of 9 on 2026-09-18, all 24 tasks done, no engine
code written.** See [`CF-CHUNK3-GATE.md`](CF-CHUNK3-GATE.md).

**Chunk 4 is closed — gated 8 of 9 on 2026-09-18**, **all 32 tasks done** and
still no engine code. See [`CF-CHUNK4-GATE.md`](CF-CHUNK4-GATE.md).

**Chunk 5 is closed — gated 8 of 9 on 2026-09-18**, **all 28 tasks done**
and still no engine code. See [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md).

**Chunk 6 is OPEN — Special Class, building side.** 29 tasks numbered
**C6-01–C6-29** in [`CF-CHUNK6-TASKS.md`](CF-CHUNK6-TASKS.md), derived from the
algorithms doc and from the opening census
([`40_chunk6_census.py`](../scripts/cf/40_chunk6_census.py)). **Chunk 6 is closed: all 29 tasks, gated 8 of 9.**

**Chunk 7 is OPEN — Special Class Business Income.** 28 tasks numbered
**C7-01–C7-28** in [`CF-CHUNK7-TASKS.md`](CF-CHUNK7-TASKS.md), derived from the
algorithms doc and from the opening census
([`49_chunk7_census.py`](../scripts/cf/49_chunk7_census.py)), **which carries
chunk 6's OI-100 correction in from the start** — every state diffed against its
own resolved parent, both package ids printed. **Chunk 7 is closed: all 28 tasks, gated 8 of 9.**

**Chunk 8 is closed: all 26 tasks, gated 7 of 9** —
[`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md). **Two points are held open on
purpose**: point 9 is owed project-wide, and **point 8 is held on CA, FL and
PR**, three jurisdictions that produce no Legal Liability premium for reasons
not yet established. Three unexplained zeros is the shape chunk 6 taught us not
to wave past.

**Chunk 8's headline: the best-prepared input any chunk has started from was
moved by running it.** An eleven-point divergence map, traced from rule XML by a
person — **8 of 11 confirmed, 3 corrected**, plus a stale line, an over-claim
and two things it does not mention:

* **Point 7** — blanket: the conclusion holds, the reason does not. The coverage
  gate writes 0 before the `Choose` the map reasons about is ever reached, and
  the cause is the same empty `BlktCauseOfLossValue` C6-28 and C7-25 found.
  **Three chunks, three coverages, one mechanism.**
* **Point 10** — Builders Risk is not `0.0`. `Premium` is **null**, we refuse,
  and **ISO charges $1**. OI-99's second instance, opposite in direction to
  Florida's.
* **Point 11** — the operand order **is** premium-bearing: $11 nested against
  $12 as a single product, at PackageMod and IRPM of 0.44.
* **Not mentioned at all** — switching the Building to Legal Liability takes
  **Contents'** LOI factor from 0.898 to 1 and its premium from $223 to $248.
  **The fork is not confined to its own premium.**

**And two harnesses nearly published results they had not earned.** A probe
whose ISO payload carried `PolicyType` and whose engine submission did not —
which read as an engine defect and would have put chunks 1–7 through a full
re-run. And a sweep that agreed with itself at $0 forty-six times because it
sent Oregon's territory to every state. Both recorded in place.

**Chunk 9 is CLOSED — Blanket rating, 22 of 22, gated 9 of 9.** Opened and
closed 2026-09-21. [`CF-CHUNK9-TASKS.md`](CF-CHUNK9-TASKS.md),
[`CF-CHUNK9-GOLDEN-CASE.md`](CF-CHUNK9-GOLDEN-CASE.md) and
[`CF-CHUNK9-GATE.md`](CF-CHUNK9-GATE.md) carry the full record. The opening
census overturned its own premise: **zero of the 20 premium files stub the
blanket formula out** — every one carries `IRPMFactor × PackageModFactor ×
Blkt<Form>AvgRate × (item value / BlktTotalFullValueAmount) × (BlktLimit/100)`
already filed. What was missing was the input, traced to `SetNonEQBlanketValues`
and a wholly separate 135-rule averaging engine
(`CommercialPropertyBlanketRatingDetailRules.Rule.xml`) no chunk 1–8 script had
ever opened. **The fix was a real interpreter bug**, not a rating gap:
`ForEach AtInputDataDef` reparented writes onto the iterated Detail record
along with reads — the first engine change since chunk 0, user-authorized,
with every chunk 1–8 script and all 16 GL suites re-verified green after it.
**ISO confirmed the fix live**, to the dollar, for a submission that exists
nowhere in ISO's own 924-payload fixture corpus.

**Chunk 10 is CLOSED — Earthquake, 21 of 21 tasks, gated 9 of 9.** Opened and
closed 2026-09-22. [`CF-CHUNK10-TASKS.md`](CF-CHUNK10-TASKS.md),
[`CF-CHUNK10-GOLDEN-CASE.md`](CF-CHUNK10-GOLDEN-CASE.md) and
[`CF-CHUNK10-GATE.md`](CF-CHUNK10-GATE.md) carry the full record. Three things
worth carrying forward:

* **The second real engine fix in the project**, user-authorized:
  `_lookup_banded` could not read a table with two banded key ranges at once,
  which made the Earthquake sub-limit form (CP 10 29) **unreachable**. A
  corpus-wide scan *before* the fix found the same limitation silently
  blocking **7 live Flood rate-modification tables and 1 Massachusetts
  heating-oil rider** — the fix was scoped by measuring the population, not by
  patching the one table that failed.
  [`CF-ENGINE-FIX-BANDED-LOOKUP.md`](CF-ENGINE-FIX-BANDED-LOOKUP.md).
* **The ISO fixture corpus is 364 Commercial Property payloads, not 924.**
  The 924 figure silently included **560 General Liability payloads**. Any
  fixture claim in this project states 364. C10-20 also found that counting
  one regex match per file misses every repeating record after the first —
  ISO's "69 Earthquake fixtures" are 69 *structures*, and the corpus holds
  **149 electing records**.
* **A golden case can be at 9 of 9 and still be unrepresentative.** Three of
  chunk 10's four golden-case coordinates — Oregon, Basic Group I, and its CP
  10 40 form — are exercised by **zero** of ISO's 69 fixtures. That is not a
  defect in the gate; it is the honest statement of what a gate covers.

**Next: chunk 11, Leasehold Interest** — see the top of this page.

The paragraphs below (chunk 6's opening findings) are historical — kept for
the record of how that chunk was opened.

Three things the census already found:

* **The first coverage that borrows a FULLY RATED rate.** **Eleven** values
  cross the boundary — `BasicGroupIRate` and `EQRate` copied outright, and
  three inputs feeding its own lookups. **No `BasicGroupIBaseRate` anywhere**,
  so unlike chunk 5 it cannot rate until the parent's build-up has *completed*.
* **Special's base rate is pinned to "Other than Apartments and Condominiums"**,
  making the apartment rows permanently unreachable from this group — while
  plain Business Income reaches them on the same physical table. The theft
  factor two steps earlier still varies by `ApartmentCondoIndicator`.
* **Six states delete `SetLowestBasicGroupIIBaseRate` outright** (AR, DC, KS,
  NY, RI, TX) — six of the eight that file no lowest-rate table, so C6-19's
  biconditional gets re-asked on a second coverage.

Three things the census already found, before any task has run:

* **The rating driver is a free-text class DESCRIPTION**, resolved through two
  lookups in series to one of 71 `OptionNN` codes. No construction key at all.
* **Florida is two countrywide editions behind** (`CF_CW_20230801_V01` against
  everyone else's `CF_CW_20260601_V01`), so its class vocabulary is frozen at
  2023. **The private option namespace is New York's** — 63 codes to
  countrywide's 71, 35 of them nowhere countrywide.
* **New York deletes both converter rules** and files both converter tables
  header-only, while still filing 189 Group I rate rows. Either those rows are
  unreachable or the option is a submitted field there. C6-12 decides by running
  it.

Chunk 5 is different in kind again: **Business Income is arithmetically
downstream of Building.** Three of its five forms have no base rate of their own
and read Building's already-computed rate, symbol and territory. It is the first
coverage in the project that cannot be rated without rating another coverage
first — so every chunk 1–3 finding is now load-bearing twice. Its `SetFactor`
picks **exactly one** of four values, and multiplying them would overstate the
premium by a large multiple.

Chunk 4 is different in kind, not just in data: it is the **first chunk that
rates a repeating group** (N Personal Property records per Occupancy Class,
driven by a `ForEach`), `CovForm` rather than `CovType` drives the branch and is
inherited from the occupancy class, and **PP's Special is the opposite of
Building's** — occupancy-keyed with its own territory multiplier, 14 steps
against 9.

The work follows a settled rhythm, and it is worth keeping:

> **Derive the expected numbers by hand from the filed rows FIRST, write them
> down, then run.** Every finding worth having in this project came from a
> prediction disagreeing with the engine — Arizona, the BCEG zero, the Kansas
> wind/hail mechanism, the cumulative forms. Observing what the engine does and
> writing that down proves nothing.

---

## Where the project stands

**Current as of 2026-09-22.**

| | |
|---|---|
| Chunks closed | **11 of 15** (0 through 10); chunk 11 **open at 0 of 24** |
| Chunk 1 — Building Basic Group I | gate **8 of 8**, ISO-confirmed |
| Chunk 2 — Building Basic Group II | gate **8 of 8**, ISO-confirmed |
| Chunk 3 — Broad and Special | gate **8 of 9**, ISO-confirmed; 47 of 47 states |
| Chunk 4 — Contents | gate **8 of 9**, ISO-confirmed; 46 of 47 states; 32 of 32 tasks |
| Chunk 5 — Business Income | gate **8 of 9**, ISO-confirmed; 44 of 47 states; 28 of 28 tasks |
| Chunk 6 — Special Class | gate **8 of 9**; 47 of 47 states; 29 of 29 tasks |
| Chunk 7 — SC Business Income | gate **8 of 9**; 47 of 47 states; 28 of 28 tasks |
| Chunk 8 — Legal Liability | gate **7 of 9** (2 points held open on purpose); 26 of 26 tasks |
| Chunk 9 — Blanket rating | gate **9 of 9**, ISO-confirmed live; 22 of 22 tasks |
| Chunk 10 — Earthquake | gate **9 of 9**; 21 of 21 tasks; **1 engine gap found and fixed** |
| ISO calls made | ~46. The engine has matched every premium; **one handling divergence found** — ISO refuses where we return $0 (OI-99) |
| General Liability | untouched — **16** suites green throughout |

**Two engine changes in eleven chunks, both user-authorized, both written up
in full.** Chunks 1–8 ran on chunk 0's foundation untouched. Chunk 9 fixed
`ForEach AtInputDataDef` reparenting writes as well as reads
([`CF-CHUNK9-GOLDEN-CASE.md`](CF-CHUNK9-GOLDEN-CASE.md) §8); chunk 10 fixed
`_lookup_banded`'s one-range-per-table limit
([`CF-ENGINE-FIX-BANDED-LOOKUP.md`](CF-ENGINE-FIX-BANDED-LOOKUP.md)). **Both
were found by RUNNING a real submission, not by reading rule XML**, and both
had their blast radius measured across the whole corpus before the patch
rather than after.

### Settled, with evidence

| | |
|---|---|
| **Rounding** | `ROUND_HALF_UP`, **proven** against ISO at both scales (3dp rate steps and whole-dollar premium) — not assumed |
| **Null in arithmetic** | `propagate` — null in, null out; comparison with null is false. Two rival hypotheses built and disproven |
| **Null premium guard** | a null written to `Premium` or `ErcCalculatedTotalPremium` is refused |
| **Forms are cumulative** | Broad/Special layer ON TOP of Basic, they do not replace it. ISO confirms all three totals |

---

## Confirm it is all still green

**The golden cases — one line per coverage, with what each must produce.**

| Command | Must produce |
|---|---|
| `python scripts/cf/00_chunk0_checks.py` | the foundation: operators, resolver, edition chain |
| `python scripts/cf/01_golden_case.py` | chunk 1 Building Basic Group I — **$261 / $263 / $288** |
| `python scripts/cf/09_chunk2_golden_case.py` | chunk 2 Building Basic Group II — **$261 + $32** from one submission |
| `python scripts/cf/15_chunk3_golden_case.py` | chunk 3 Building Broad and Special — **$16 / $54**, layering onto Basic's own **293** (= 261 + 32, chunk 2's figure, not printed by this script) to reach **309 / 347** |
| `python scripts/cf/22_chunk4_golden_case.py` | chunk 4 Contents, four forms — **$223 / $24 / $16 / $137**, Building unmoved at 263 / 32 |
| `python scripts/cf/32_chunk5_golden_case.py` | chunk 5 Business Income, four forms — **$112 / $13 / $23 / $47**, Building unmoved at 261 / 32 |
| `python scripts/cf/41_chunk6_golden_case.py` | chunk 6 Special Class, four forms — **$66 / $209 / $14 / $44**, Building unmoved at 261 / 32 |
| `python scripts/cf/50_chunk7_golden_case.py` | chunk 7 Special Class Business Income — **$39 / $123 / $23 / $47**, the item unmoved at 66 / 209 |
| `python scripts/cf/59_chunk8_golden_case.py` | chunk 8 Legal Liability — Building **$60 / $7 / $4 / $12**, Contents **$132 / $15 / $11 / $93** |
| `python scripts/cf/68_chunk9_golden_case.py` | chunk 9 Blanket rating, two dispersed structures — **$255 / $510** |
| `python scripts/cf/85_chunk10_golden_case.py` | chunk 10 Earthquake, Building Basic Group I — **$6** |
| **`python scripts/cf/104_chunk10_c10-21_regression.py`** | **the chunk 0–11 rows above, all at once** (chunks 10–11 added 2026-09-22) — each golden case checked against its documented figure (not just its exit code), plus 25 machinery scripts and all 16 GL suites. Chunk 10's own `85_…` case is deliberately outside it: a regression harness is for what came before the change. `--selftest` proves the harness can fail |

**The machinery each chunk added**, worth running when shared code changes:

| Command | What it holds |
|---|---|
| `python scripts/cf/21_chunk3_special_structure.py` | chunk 3's Special structure — incl. the $11,398 derived-field case |
| `python scripts/cf/23_chunk4_foreach.py` | chunk 4's repeating group — 209 + 105 = 314 |
| `python scripts/cf/35_chunk5_factor.py` | chunk 5's `SetFactor` — **233 not 252**, selection rather than multiplication |
| `python scripts/cf/39_chunk5_crossform.py` | three coverages on one submission, none of them moving |
| `python scripts/cf/04_shared_names.py` | gate point 6 across all **six** chains |
| `python scripts/cf/42_chunk6_zero_cases.py` | chunk 6's six zero cases — incl. Florida's spelling worth zero in Oregon |
| `python scripts/cf/45_chunk6_description_chain.py` | chunk 6's description chain — and the correction to the Florida claim |
| `python scripts/cf/46_chunk6_perform.py` | chunk 6's per-form specifics — the 1.5 coinsurance surcharge, the dead factor, the biconditional |
| `python scripts/cf/47_chunk6_forms.py` | chunk 6's form claims — the narrowed fire gate, Florida's 1.42, construction-blind Broad |
| `python scripts/cf/48_chunk6_crossform.py` | chunk 6's cross-form claims — the blanket branch, and four coverages on one submission |
| `python scripts/cf/51_chunk7_zero_cases.py` | chunk 7's six zero cases — incl. a parent worth $0 carrying a $39 child |
| `python scripts/cf/54_chunk7_borrowed.py` | chunk 7's borrowed rate — eleven values across the boundary, and no base rate |
| `python scripts/cf/55_chunk7_perform.py` | chunk 7's per-form specifics — both apartment dimensions dead, the pin that is live next door |
| `python scripts/cf/56_chunk7_crossform.py` | chunk 7's cross-form claims — the rounding counted, and five coverages on one submission |
| `python scripts/cf/57_chunk7_open_questions.py` | the algorithms page's five open questions — four answered, one left open with a reason |
| `python scripts/cf/61_chunk8_zero_cases.py` | chunk 8's six zero cases — four zeros, four unrelated causes |
| `python scripts/cf/64_chunk8_fork.py` | the fork — two concepts discarded, a third never computed |
| `python scripts/cf/65_chunk8_map.py` | the traced map, point by point |
| `python scripts/cf/66_chunk8_crossform.py` | the map **scored** — 8 of 11 confirmed, 3 corrected — and the cross-coverage LOI leak |
| `python scripts/cf/60_chunk8_raas_probe.py` | the standing engine-vs-ISO check on the Legal Liability form record |
| `python scripts/cf/05_exclusion_records.py` | gate point 7 census, with a per-group chunk 6 section |
| `python scripts/cf/08_hardcoded_literals.py --group CommercialPropertySpecialClass` | gate point 5 for a second datadef group |

**The six sweeps** take a few minutes each and enumerate all 47 jurisdictions:

    python scripts/cf/17_chunk3_enumerate_states.py   # Broad 47/47, Special 47/47
    python scripts/cf/24_chunk4_enumerate_states.py   # Contents 46/47, PR stated
    python scripts/cf/34_chunk5_enumerate_states.py   # Busn Income 44/47, AZ/TX stated
    python scripts/cf/43_chunk6_enumerate_states.py   # Special Class 47/47, AZ/FL/NY at $0
    python scripts/cf/52_chunk7_enumerate_states.py   # SpclClass Busn Income 47/47, the same three inherited
    python scripts/cf/62_chunk8_enumerate_states.py   # Legal Liability 47/47, 43 with a real premium

**All of the above re-run green on 2026-09-22** (C10-21), along with all 16
General Liability suites (`tests/verify_*.py`). **Chunks 6, 7 and 8 are the
only chunks to touch shared code** — `04_shared_names.py` (now reporting eight
chains), `05_exclusion_records.py` (per-group sections) and
`08_hardcoded_literals.py` (a `--group` argument) were extended to take further
datadef groups, and all three still pass for chunks 1–5 unchanged. That was
checked, not assumed.

**Do not re-run these by hand.** `104_chunk10_c10-21_regression.py` runs the
golden cases, the machinery scripts and all 16 GL suites in one command and
checks each golden case against its **documented dollar figure**, not just its
exit code — a script exiting 0 only proves it agreed with itself. It carries
`--selftest`, which plants seven defects and fails if any is reported green.

Everything exits 0. The full set is `scripts/cf/00`–`106`; the General Liability
suites are `tests/verify_*.py` and must stay green — they are the regression net
for every shared-code change.

> **`scripts/cf/` holds two unrelated workstreams that share a number range.**
> The `NN_chunkN_*` files are this engine. The `NN_r1`–`r8`/`m1`/`t1` files
> drive Excel over COM for the separate rater-streamlining project and are
> **not** part of this engine's test surface — RULE #0 applies to them.

**Nothing is committed.** All of `cf_engine/`, `scripts/cf/`, the `docs/CF-*`
files and the `gl_engine/` edits are working-tree only.

---

## Open items — none blocking

| | |
|---|---|
| **Input validation — absent means zero** | Eight inputs now price at zero rather than raising: Arizona's `BasicGroupIReductionCredit`, an unrecognised `ConstructionType`, an absent `BCEG`, a missing `RatingTypeBasicGroupII`, a missing Group II territory, a blank `Deductible` on both chunk 3 forms, and **a construction type that is spelled right but is a rating-type name rather than one of the 25 submission values**. Every one looks like a valid submission and silently produces a cheap policy. A missing `Limit` is the only one that raises |
| **Input validation — a submission can populate a derived field** | **New 2026-09-18, and the mirror image of the above.** Every `IsNull`-guarded rule honours a value that arrived in the payload, so a submitted `SpecialBaseRate=9.999` bypasses the filed table and prices at $11,398. It fails *upward*, and **no ISO comparison catches it** — ISO has the same guards and returns the same number |
| **Building's rate-step rounding is untested at a discriminating rate** | **New 2026-09-18.** Chunk 1 recorded Building's Group I rate step as rounding after every factor, but its golden case (base 0.498) gives 0.239 either way. Class 0074 discriminates: `0.143 x 0.96 x 0.499` is **0.069 rounded once** and 0.068 rounded per factor, and the engine gives 0.069. So the per-factor reading was never actually tested. **Chunks 4 and 5's sweeps both assume per-factor rounding** and match 46 of 47 and 44 of 47 — the residual mismatches may be this. Needs a deliberate tie, the way chunk 1 settled half-up |
| **`SingleResult` with zero hits** | ISO refuses on *some* empty lookups and tolerates others; the distinguishing condition is unknown. Blanket strictness was measured and **disproven** (it breaks VA and VT, which ISO rates). Needs targeted ISO probes, not more corpus reading |
| Per-state gaps | TX's wind/hail shape untraced; DC and IL have no `BCEGFactor` row for their own Group II territory; MT, NY and PR resolve to an empty Group II symbol table |
| Housekeeping | `cf_engine` imports `gl_engine`; the shared core wants a neutral home. **Never bundle that rename with a rating change** |
| GL, optional | whether it adopts `propagate`; whether it wants its own rounding tie (OI-70) |

---

## The three things most worth remembering

1. **The countrywide chain is often the minority behaviour.** 39 of 47
   jurisdictions override `SetBasicGroupIIRate`; 18 of 47 override the Group I
   chain. Re-ask per chunk, never inherit the answer.
2. **Absent means zero, and nothing raises.** This is the recurring failure
   shape in Property, and it is why the zero cases exist in every chunk. Chunk 3
   added the sharpest case: a construction type that is present, spelled right
   and semantically correct, and still prices at zero because it is a rating-type
   name rather than a submission value.
3. **A matching premium proves less than it looks.** Nine cases matched ISO
   before a rounding tie was deliberately constructed, and every one of them was
   consistent with all three rounding modes.
5. **A check that finds SOMETHING needs its denominator tested too.**
   **New 2026-09-22.** Chunk 10's opening census produced a real, believed,
   acted-upon finding — "69 of 924 ISO payloads elect Earthquake" — and it
   was wrong twice over. The 924 silently summed **560 General Liability
   payloads** into a Commercial Property statistic, and the per-file regex
   counted only the first of up to ten electing records. Neither error made
   the finding *absent*; both made it **confidently wrong**, and it survived
   nineteen tasks before C10-20 parsed what the census had only grepped. A
   finding that confirms what you expected gets the least scrutiny and needs
   the most.
4. **A check that finds nothing needs its denominator tested too.** Chunk 3
   found three defects in its own instruments and none in the corpus — gate
   point 6's shared-name check was blind to delegating rules, gate point 7's
   census was blind to theft, and the state sweep's first pass was blind to rule
   overrides. Each returned a clean result that was really an empty search.

---

## Map of the documents

| | |
|---|---|
| [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html) | **every chunk, every task, status — one page**. Edit it here only; it is mirrored to Ideation (`iso-rating-engine/cf-build-status`). After a work session that changed it, run `python scripts/sync_build_status_to_ideation.py` (opens a PR to Ideation's trunk) |
| [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) | the 15-chunk plan and the eight-point gate |
| [`CF-CHUNK0-BUILD-SPEC.md`](CF-CHUNK0-BUILD-SPEC.md) | the foundation, as built |
| [`CF-CHUNK1-GOLDEN-CASE.md`](CF-CHUNK1-GOLDEN-CASE.md) · [`CF-CHUNK1-GATE.md`](CF-CHUNK1-GATE.md) | chunk 1 |
| [`CF-CHUNK2-GOLDEN-CASE.md`](CF-CHUNK2-GOLDEN-CASE.md) · [`CF-CHUNK2-TASKS.md`](CF-CHUNK2-TASKS.md) · [`CF-CHUNK2-GATE.md`](CF-CHUNK2-GATE.md) | chunk 2 |
| [`CF-CHUNK3-TASKS.md`](CF-CHUNK3-TASKS.md) · [`CF-CHUNK3-GATE.md`](CF-CHUNK3-GATE.md) | chunk 3, closed at 8 of 9 |
| [`CF-CHUNK4-GOLDEN-CASE.md`](CF-CHUNK4-GOLDEN-CASE.md) · [`CF-CHUNK4-TASKS.md`](CF-CHUNK4-TASKS.md) · [`CF-CHUNK4-GATE.md`](CF-CHUNK4-GATE.md) | chunk 4, closed at 8 of 9 |
| [`CF-CHUNK5-GOLDEN-CASE.md`](CF-CHUNK5-GOLDEN-CASE.md) · [`CF-CHUNK5-TASKS.md`](CF-CHUNK5-TASKS.md) · [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md) | chunk 5, closed at 8 of 9 |
| [`CF-CHUNK8-TASKS.md`](CF-CHUNK8-TASKS.md) · [`CF-CHUNK8-GOLDEN-CASE.md`](CF-CHUNK8-GOLDEN-CASE.md) · [`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md) | **chunk 8, closed at 7 of 9 — all 26 tasks** |
| [`CF-CHUNK7-TASKS.md`](CF-CHUNK7-TASKS.md) · [`CF-CHUNK7-GOLDEN-CASE.md`](CF-CHUNK7-GOLDEN-CASE.md) · [`CF-CHUNK7-GATE.md`](CF-CHUNK7-GATE.md) | **chunk 7, closed at 8 of 9 — all 28 tasks** |
| [`CF-CHUNK6-TASKS.md`](CF-CHUNK6-TASKS.md) · [`CF-CHUNK6-GOLDEN-CASE.md`](CF-CHUNK6-GOLDEN-CASE.md) · [`CF-CHUNK6-DESCRIPTION-CHAIN.md`](CF-CHUNK6-DESCRIPTION-CHAIN.md) · [`CF-CHUNK6-PER-FORM.md`](CF-CHUNK6-PER-FORM.md) · [`CF-CHUNK6-FORMS.md`](CF-CHUNK6-FORMS.md) · [`CF-CHUNK6-CROSSFORM.md`](CF-CHUNK6-CROSSFORM.md) · [`CF-CHUNK6-GATE.md`](CF-CHUNK6-GATE.md) | **chunk 6, closed at 8 of 9 — all 29 tasks** |
| [`CF-CHUNK9-TASKS.md`](CF-CHUNK9-TASKS.md) · [`CF-CHUNK9-GOLDEN-CASE.md`](CF-CHUNK9-GOLDEN-CASE.md) · [`CF-CHUNK9-GATE.md`](CF-CHUNK9-GATE.md) | **chunk 9, closed at 9 of 9 — all 22 tasks; the `ForEach` engine fix is §8 of the golden case** |
| [`CF-CHUNK10-TASKS.md`](CF-CHUNK10-TASKS.md) · [`CF-CHUNK10-GOLDEN-CASE.md`](CF-CHUNK10-GOLDEN-CASE.md) · [`CF-CHUNK10-GATE.md`](CF-CHUNK10-GATE.md) | **chunk 10, closed at 9 of 9 — all 21 tasks** |
| [`CF-ENGINE-FIX-BANDED-LOOKUP.md`](CF-ENGINE-FIX-BANDED-LOOKUP.md) | chunk 10's engine fix — root cause, scope, population check, regression |
| [`CF-CHUNK11-TASKS.md`](CF-CHUNK11-TASKS.md) | **chunk 11, OPEN at 0 of 24 — Leasehold Interest** |
| [`../CF_Algorithm/CF_Required_Submission_Inputs.md`](../CF_Algorithm/CF_Required_Submission_Inputs.md) | every field the ERC rules treat as a true submission input vs. derived, chunks 1–10. **Check this before building any new golden case** |

Saved ISO requests and responses: `results/cf-raas/`.
