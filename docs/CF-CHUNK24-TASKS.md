# Property chunk 24: task list and status

**Builders Risk: insurance for a building under construction or renovation, with its
own reporting form, premium adjustment and theft covers; plus the stand-alone Theft of
Building Materials.** Tasks set 2026-09-28; chunk 18 is being built in the other terminal,
and chunks 19–23 wait.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 24, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`905_chunk24_census.py`](../scripts/cf/905_chunk24_census.py), run 2026-09-28,
3 s, log `results/cf-raas/logs/chunk24_census.log`). It runs the same checks as `903_` (messages in
every rule file, `SetPremium` per in-force edition, form numbers from `Form Pages`, sibling
names), plus a tenth for this chunk: **the Builders Risk trail**, meaning every rule file *outside*
the family that writes or reads a Builders Risk field.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Order.** After chunk 23. It builds on the Building rate chain (chunks 1–4), blanket (9), EQ (10),
and it feeds fields that chunks 5, 9, 12 and 19's records already read (the trail below).

**Status: GATED 2026-10-01, 25 of 25, 9 of 9** ([`CF-CHUNK24-GATE.md`](CF-CHUNK24-GATE.md); RC-5 done the same day: downstream equal at ISO on 4 pairs, the full gate regression CLEAN 157 of 157, `157_ --all` 293 of 293, 540 of 546; one engine change, OI-121, with the user's go). RC-4 done 2026-10-01, `227_chunk24_rc4.py --live`: the 16 rewriting states, the edition probe, all 46 states and the built readers ALL AGREE with ISO; blank-key refusals added to OI-103; no engine change). RC-3 done 2026-10-01, `226_chunk24_rc3.py --live`: 48 zero / message / shared-name / exclusion cases ALL AGREE with ISO, every premium and (level, message); the 2% EQ deductible on class A1 added to OI-103; no engine change). RC-2 done 2026-10-01, `225_chunk24_rc2.py --live`: 10 golden cases ALL AGREE with ISO, every premium and message; the OI-121 probes settle ISO's ProRate; **engine fix OI-121 with the user's go**, `206_ --check` after it). RC-1 done 2026-10-01, `224_chunk24_rc1.py`, all checks pass, 2m23s, no ISO calls; no engine change; OI-121 opened). Next: chunk 25.

**Carried from chunk 21 (2026-09-30): the census `905_` now diffs EVERY rule of the family files across the four countrywide editions** (`scripts/cf/_edition_rules.py`, chunk 20's gate item): 31 family files: MO V02 5, V03 5 (Builders Risk premium adjustment), V04 0 rule differences from 2026 V01. The editions task must judge each one; the census's earlier "identical in all four editions" was a SetPremium-only check. Chunk 21 also found its own edition difference in a PARENT file (MO's sewer caps read `Limit`, not `LimitToUse`): diff the parent files' rules that name this chunk's records too.

---

## In plain English first

- **Builders Risk** (CP 00 20) insures a building while it goes up. Its options:
  - a **reporting form** (CP 11 05): values are reported as construction proceeds;
  - a **premium adjustment form** (CP 11 06): the premium is recalculated each reporting period,
    on dates;
  - **renovations** (CP 11 13): an existing building being renovated, priced on a
    completed-value multiplier;
  - **collapse during construction** (CP 11 20), **theft of building materials, fixtures,
    machinery and equipment** (CP 11 21), and **building materials of others** (a company-entered
    premium);
  - earthquake riders on the renovations, reporting and premium adjustment forms;
  - separate or sub-contractors coverage and exclusion (CP 11 15, CP 11 14), and the Standard
    Property Policy changes (CP 11 99): forms with no premium of their own.
- **Theft of Building Materials (not Builders Risk)** (CP 10 44): the same theft cover on an
  ordinary building.

**ISO has priced one of the 20 premium records**: Builders Risk theft of building materials, with a
non-zero premium on 144 of the 149 stored policies that carry it. Materials of others is on all 364
stored buildings, always $0 (a manual premium no one entered). The rest have never been priced.

## What the census found, before any task ran

The Builders Risk pattern also matches the non-BR theft file, so the plan's "19 + 1" is **20 files
in all**. The card's "adds 17 files" was wrong; the summary's "+20 → 540" stands.

| Family | Premium records | How it prices | Own tables (CW rows) | Stored evidence |
|---|---|---|---|---|
| **Reporting form** (Group I, II, Broad, Special, EQ) | 5 | the coverage's rate **or the blanket average** × `BldrsRiskReportingFormFactor` × limit | reporting form factor (1) | none |
| **Premium adjustment** (Group I, II, Broad, Special, EQ, **Blanket**) | 6 | **pro rata** of this period's annual premium against the preceding period's, with **date arithmetic** (DateCreate / DateDifference / DatePart); Blanket is a manual premium | reads the building chain through its detail rules | none |
| **Renovations** (Group I, II, Broad, Special, EQ) | 5 | the building's rates × limit, with a completed-value multiplier and a coinsurance modifier | completed-value multiplier (2), coinsurance modifier (1), EQ factor (9; FL) | none |
| **Collapse during construction** | 1 | Broad / Special rate × a collapse option | collapse rate (3) | none |
| **BR theft of materials, fixtures, machinery, equipment** | 1 | theft rate × limit × loss cost multiplier | theft rate (1; FL), theft factor (**0 rows countrywide**; FL files it) | **144 of 149 stored responses priced** |
| **Materials and supplies of others** | 1 | **manual premium** | none | **on all 364 buildings, $0** |
| **Theft of building materials (not BR)** (CP 10 44) | 1 | rate × limit × theft deductible factor | rate (1; FL) | none |

All told: 35 tables read directly (the building chain's LOI, Group II symbol, construction and
deductible tables with their state filings, and the eight Builders Risk tables above).
**Identical in all four editions.** No unregistered element; `Power` unused.

**Sixteen states rewrite a family file** (the plan said 9): AK AL AR CA DC FL GA IL KS KY MT NJ NY RI
TX VT. Most rewrite the Builders Risk base rates in the renovations and premium adjustment detail
rules. **`SetPremium` itself is rewritten in FL** (premium adjustment), **KS NY VT** (renovations), and
**TX** (renovations EQ). VT adds vandalism, and MT and NY have their own Group II symbol rules.

**Messages: 43 listed, 37 distinct.** One is chunk 20's Fire Department rule, which leaves **36**. They
include the form rules (CP 11 05, 11 13, 11 14, 11 15, 11 20, 11 21, CP 10 44: each valid only with
Builders Risk, or with the right cause of loss or coverage), class 1150 requiring Builders Risk, a $500 minimum
deductible, blanket reporting limits summing to the blanket limit, NY's U / V / W Group II
symbols, and the Public Institutional Plan (AL KS RI).

**The Builders Risk trail (check 10): built code that reads Builders Risk fields.**

| Built file | Writes | Reads | States rewriting |
|---|---|---|---|
| **Structure** (chunk 1) | `BuildersRiskEQFactor`; attaches the Builders Risk forms | | AL DC FL KS NY RI VT WV |
| **Business Income** (chunk 5) | `BuildersRiskFactor` (via `SpecialFormBldrsRiskTimeElementBaseRate`) | both factors | AR CA DC FL IN KS KY NY RI TX WV |
| **Blanket Rating Detail** (chunk 9) | `BldrsRiskFactor`, `BldrsRiskTotReptgFormLimit` | limits | |
| **Unmanned aircraft BI / detail** (chunk 12) | | both factors | DC NY |
| **Radio / TV antennas BI** (chunk 19) | | `BuildersRiskFactor` | AR DC FL KS NY RI |
| **Ordinance or Law increased period** (CA), **Pollutant Clean Up** (FL) | | the factors | CA, FL |
| **Main ruleset** | | the blanket reporting-form total | |

**What shapes the plan:**

1. **Builders Risk switches on factors other coverages already read.** Business Income, blanket
   rating, unmanned aircraft, antennas' BI, CA's Ordinance or Law and FL's Pollutant Clean Up all read
   `BuildersRiskFactor` / `BldrsRiskFactor` / `BuildersRiskEQFactor`, and 11 states rewrite Business
   Income's use of them. **149 stored policies already have Builders Risk on** (they carry the theft
   record), so the built readers have some real evidence with it on; the other 144 do not. RC-1
   re-rates all 293 unchanged and sorts which readers those 149 actually exercise. RC-4 prices the
   rest **with** Builders Risk on.
2. **The premium adjustment form works on dates and on another period's premium.** It pro-rates by
   reporting period (DateDifference: OI-107's sign applies) and reads the preceding period's annual
   premium. Every period is predicted in days by hand.
3. **There's real evidence, but it's narrow.** Theft of materials is priced on 144 stored responses
   (5 of 149 at $0 need explaining); the plan's "only 3 Basic-cause fixtures" are among them. Materials of
   others is a manual premium sitting at $0 on all 364.
4. **Two Builders Risk factor names** (`BuildersRiskFactor` in Business Income, `BldrsRiskFactor` in
   blanket rating), plus the EQ factor written by Structure. Same idea, different writers. The shared-names
   task diffs them.
5. **Sixteen states, five with their own `SetPremium`.** That's the widest state layer since chunk 19.
6. **One countrywide table is empty**: the BR theft factor has 0 rows countrywide and only FL files it.
   The absent-means-zero case is written into the zero cases.
7. **Class 1150 and the Group II symbols U / V / W** tie Builders Risk to the class and symbol logic
   chunks 2 and 6 built (NY enforces the symbols both ways).

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (6 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C24-01 | **Opening census**: population, formulas, tables, messages by record and by form / wording, sibling names, every edition, state layer, stored evidence, attach points, engine readiness, **and the Builders Risk trail** | ✅ | **Done 2026-09-28** (`905_chunk24_census.py`, 3 s). Findings above: 20 premium records, 1 priced by ISO (144 responses); 36 messages; 16 states rewrite (5 `SetPremium`s); identical in all four editions; date arithmetic in premium adjustment; built code reads the BR factors |
| C24-02 | **The stored evidence**: reproduce Builders Risk theft on all 144 priced responses and explain the 5 at $0; why materials of others is $0 on 364; the 3 Basic-cause fixtures end to end; which built readers (C24-03's trail) the 149 Builders Risk policies exercise. No ISO calls | ✅ | **Done 2026-10-01** (`224_`, all 293 stored responses re-rated, every premium equal to ISO): **145 stored responses carry BR theft** (the census's 149 fixtures = 145 + 2 Puerto Rico + KY + MT never stored), hand = evaluator = engine = ISO on all 145; **one at $0, not five**: STC_CP000020685, Limit 1,000 x 0.009 rounds to $0. **FL prices theft on its own rule**: the building's Group I rate x FL's factor 0.25 x Limit / 100, no cyber factors. Materials of others: $0 on all 293 stored buildings because no fixture enters a manual premium. **Two** stored Basic-cause Builders Risk policies (IL, IN), not three: the plan's third, STC_CP000020234 (NY), has no theft record and was never stored. The 145 Builders Risk policies exercise none of the built readers (no BI factor other than 1, no Builders Risk blanket, no antennas BI, no unmanned aircraft): RC-4 must price them |
| C24-03 | **The built touchpoints**: who writes `BuildersRiskFactor`, `BldrsRiskFactor`, `BuildersRiskEQFactor` and `BldrsRiskTotReptgFormLimit` (Structure, Business Income, Blanket Rating Detail, with their state rewrites), what each reader sees with Builders Risk on and off, class 1150's coverage-type rule; **all 293 stored policies re-rated unchanged** | ✅ | gate 6 · **Done 2026-10-01** (`224_`): Structure writes `BuildersRiskEQFactor` from `BldrsRiskEQFactor` on class 1150 (EQ class A1: 0.495) and 1.0 otherwise; **Business Income sits under the building**, so its `BuildersRiskFactor` follows the building's class 1150 (`BldrsRiskFactorBusnIncome` 2) and is 1.0 under an ordinary building (the occupancy's `ClassCodeToUse` becomes 1150 too); Blanket Rating Detail sets `BldrsRiskFactor` only for blanket Type "Builders Risk" and sums the reporting-form limits of its members; all 293 stored policies re-rate unchanged |
| C24-04 | **Attach map and switches**: the Builders Risk forms on Structure, the premium adjustment and renovations detail records, the sub-contractors coverage and exclusion records (no premium: confirm), every on-switch, blank-input defaults | ✅ | gate 2 (with C24-06) · **Done 2026-10-01** (`224_` T1-T6, hand = evaluator = engine on every record): CP 00 20 attaches on CovType "Builders Risk" **or** whenever a renovations record exists (an ordinary building); CP 11 99 replaces it on a Standard Property Policy; **CP 11 06 attaches itself whenever a reporting form exists**; the reporting form creates its five coverages (Broad / Special switch on the cause); **renovations price $0 whenever the building also has a reporting form**; collapse options 1 / 2 price on the cause rate x (5 - 1), option 3 on 0.002 x LCM; materials of others needs Indicator "Yes"; CP 11 14 / 11 15 carry no premium. Oregon figures: reporting form 400,000 Group I $164, II $321, Special $94, EQ $20, Broad $78; collapse $8 / $187 / $235; theft $5; materials of others 100 -> $93; renovations Special $89; CP 10 44 $2 |
| C24-05 | **Premium adjustment by hand**: reporting periods, `FormAnnualPremium`, `AnnualPremiumOfPrecedingReportingPeriod`, `ProRate`, the DateCreate / DateDifference / DatePart steps (OI-107), each written down in days and checked against the engine | ✅ | **Done 2026-10-01** (`224_`): two periods (500,000 then 650,000) from the effective date: FormAnnualPremium, the preceding premium (period 1 reads the reporting form's coverage premium, period 2 the previous period's FormAnnualPremium) and the premium by hand = engine on every group (e.g. Group I $36 then $48). **ProRate is 1.0 only when a period starts on or before the effective date; a later start calls ISO's host function `DateFunctionManager.GetLeapDays`, which our engine refuses by design: OI-121 (new)**. The policy dates come from the request (`EffDate` at the root; `ExpDate` = + 1 year), as the request conversion does |
| C24-06 | **Tables and literals**: the 8 Builders Risk tables (collapse options, completed-value multiplier rows, EQ factor rows), the empty countrywide theft factor and FL's, and every state-filed table under any name (Group II symbols MT NY; construction; deductibles) | ✅ | gates 2, 5 · **Done 2026-10-01** (`224_`): collapse rates Option1 / Option2 **5**, Option3 0.002; BR EQ factor 9 rows (FL 15); renovations coinsurance modifier 0.75; completed-value multiplier **1.82 with a reporting form / 1.36 without**; reporting form factor 1.82; BR class code 1150; theft rate 0.009; Special BR rate 0.015; CP 10 44 rate 0.009; BI Builders Risk factor 2; Special BR time element base rate 0.018. **The countrywide theft factor table is empty and nothing countrywide reads it; only FL runs it (0.25)**. Every literal key has a row |

### RC-2 · Golden cases (7 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C24-07 | **Builders Risk theft**: reproduce a stored response, then a new limit and deductible; ISO live | ✅ | gate 1 · **Done 2026-10-01** (`225_ --live` G1, TS, all agree with ISO): BR theft $5 on 50,000 (0.009 x LCM x Limit / 100, through the modifiers); the stored fixture STC_CP000016738 re-sent with a new limit 120,000 and deductible 2,500 prices **$11** at ISO and ours: **the deductible moves no dollar** (it sets stat codes only) |
| C24-08 | **Reporting form**: five coverage groups, not blanketed and blanketed (blanket average vs own rate discriminated), a blanket limit equal to the sum of reporting limits; ISO live | ✅ | **Done 2026-10-01** (G1, G2, E1, agree): reporting form 400,000 Group I $164, II $321, Special $94, Broad $78, EQ $20; every rate predicted from the building's own adjustment x LOI x 1.82 (Group I 0.042 = r3(r3(0.025 x 0.922) x 1.82)). The blanketed reporting form waits for RC-3 / RC-4 (blanket Type "Builders Risk" machinery) |
| C24-09 | **Renovations**: both completed-value multiplier rows, the coinsurance modifier, five groups; ISO live | ✅ | **Done 2026-10-01** (N1-N3, agree): renovations price the LARGER of a Builders Risk rate (class 1150 base x 1.36 / 1.82) and the completed building's rate (x 0.9 x 0.75 / 1.0). Frame 300,000 without a reporting form: completed rate wins Group I (0.157 vs 0.033) -> $454, Special 0.031 -> $89, BR wins EQ -> $24; Fire Resistive: Group I 0.093 -> $270. **Beside a reporting form the BR rate wins Group I (0.042 vs 0.021), renovations price $0 and the reporting form copies renovations' rates** (Special $145). The BR rate reads the BUILDING's territory factor, the completed rate the LOCATION's (equal here). Group II's container rate is read from the engine and ISO-checked, not derived (stated) |
| C24-10 | **Premium adjustment**: two reporting periods with dates chosen so the day count decides a dollar, five groups plus the blanket manual premium; ISO live | ✅ | **Done 2026-10-01** (P1, agree): two periods from the effective date (500,000 / 650,000): Group I $36 / $48, II $61 / $83, Special $19 / $27, EQ $5 / $8; period LOI factors banded by hand. **OI-121 probed at ISO and FIXED** (the user's go): DateDifference is second - first (OI-107), so the rule reads (n + L) / (tot + L); **L1 / L2 could not disagree** (both readings round to 0.80 / 0.51: chosen on the wrong sign, corrected the same day); **L4 / L5 do**: on a 2023-24 term containing 29 February ISO answers 0.73 / 0.52 where counting it gives 0.74 / 0.53, and the 2026 control 0.50 rules out an inclusive count. So GetLeapDays is 0 on a one-year term; the engine now reads it so (Property only, other terms still refused) and **equals ISO on all five probes, 105 of 105 premiums each** |
| C24-11 | **Collapse during construction**: each of the three options on Broad and Special; ISO live | ✅ | **Done 2026-10-01** (G1-G3, agree): collapse option 3 $8 (0.002 x LCM), option 1 on Broad $187 (BroadRate x (5 - 1)), option 2 on Special $235 (Special adjustment x (5 - 1)) |
| C24-12 | **Materials of others and CP 10 44**: the manual premium through the modifiers; theft of building materials on an ordinary building with its theft deductible factor; ISO live | ✅ | **Done 2026-10-01** (G1, M1, agree): materials of others 250 manual -> **$232** (x the building's MPDC 0.95, r0 each step); CP 10 44 40,000 on ordinary buildings, Special deductible 250 (Deductible250Factor) and 1,000 (DeductibleFactor 'Other Cause Of Loss'): $3 each, 201 premiums equal |
| C24-13 | **Builders Risk earthquake**: the EQ riders on renovations, reporting and premium adjustment, with EQ factor rows chosen to move a dollar; ISO live | ✅ | **Done 2026-10-01** (E1, N1-N3, agree): two Builders Risk buildings, EQ class A1 (BR EQ factor 0.495) -> reporting EQ $20, C1 (1.0) -> $60; renovations EQ (A1) $24 with the BR rate winning; the premium adjustment EQ periods in P1 |

### RC-3 · Zero cases, messages and names (4 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C24-14 | **Zero cases**: each limit blank; reporting form with building limit not 0; a period of zero days and a reversed period; the empty theft factor outside FL; materials of others with no manual premium; each switch off; predict both readings, ISO live | ✅ | gate 4 · **Done 2026-10-01** (`226_ --live` Z1-Z11, all agree with ISO, every premium and message): theft with no limit $0; reporting form with no limit $0 on all five; a building limit beside a reporting form fires "When CP 11 05 is attached the entry for Building Limit should be 0" (the building's LOI does not key on that limit: rates unchanged); **a period from the expiration date prices $0 (ProRate 0) and one AFTER expiration prices NEGATIVE** (-$9 / -$15 / -$5 / -$1), as written, at ISO too; NewValue 0 $0; materials of others with no manual premium $0, and switched off (Indicator No) $0 despite a manual 250; collapse with no option $0, on the Basic cause $0 + its message; renovations with no limit $0; CP 10 44 with no Special deductible $0 (factor 0), "Not Applicable" prices on the building's Special deductible factor ($3); EQ "No Coverage" $0. The countrywide theft factor table stays empty and unread (C24-06) |
| C24-15 | **Messages**: all 36, triggered and silent: the form-with-Builders-Risk rules, class 1150, the $500 minimum deductible at 499 / 500, the blanket reporting-limit sum, NY's U / V / W both ways, Public Institutional Plan (AL KS RI); ISO live | ✅ | gate 9 · **Done 2026-10-01** (M1-M13c, NY1-NY3, KS1, AL1, RI1, all agree, every (level, message) equal): the five "only valid with Builders Risk Coverage" forms on an ordinary building and silent on a Builders Risk one; CP 11 20 / 11 21 on a Standard Property Policy; collapse on Basic; **the $500 minimum fires on a 250 deductible and is silent at 500** (the deductible is a list: 499 cannot be sent); class 1150 on CovType Building; renovations on No Coverage; Agreed Value with renovations and with CP 11 05; a Builders Risk building with no limit and no reporting form; the 2% EQ deductible off class 1150 (EQ class C1) and silent on 1150; CP 10 44 on Broad / on a Builders Risk building / on a Standard Property Policy; CP 10 44's Special deductible below the theft deductible; a period's covered causes differing from the building's (and silent when equal); the Builders Risk blanket limit not equal to the reporting limits' sum (and silent at the sum), and a blanket mixing CP 11 05 with none; **NY's U / V / W both ways** (NY's symbol is a submitted value: its own rule is empty); KS / AL / RI Public and Institutional Plan (two messages each). **First sent on EQ class A1, the 2% deductible was refused by ISO** (no `EQPercentageDeductibleFactor` row) **while ours priced the EQ endorsement $0**: added to OI-103 |
| C24-16 | **Shared names**: `BuildersRiskFactor` vs `BldrsRiskFactor`, `BuildersRiskEQFactor`, the building chain's rates as Builders Risk reads them, `Limit` / `LimitToUse`, `ManualPremium`, `ProRate`, diffed rather than assumed; whether a submitted value survives | ✅ | gate 6 · **Done 2026-10-01** (S1-S4, agree): a submitted reporting-form Group I rate 0.1 and Factor 2.0 **survive** (IsNull guards), and the submitted Factor flows into the premium adjustment form's rates too (it reads the reporting form's Factor); a submitted ProRate 0.5 survives (halves each period); **a submitted CompletedValueMultiplier is overwritten** (no IsNull guard: renovations unchanged); a submitted BuildersRiskTheftRate 0.02 survives ($10). `BuildersRiskFactor` (Business Income, under the building) and `BldrsRiskFactor` (blanket detail, Type "Builders Risk" only) are separate writers (C24-03) |
| C24-17 | **Exclusion records**: cyber-incident factors in all 20 formulas; VT's vandalism, the wind / hail exclusion and theft exclusion (CP 10 44 not valid with it), each at a limit where the factor moves a dollar | ✅ | gate 7 · **Done 2026-10-01** (X1-X3, agree): both cyber exclusions at large limits move every Builders Risk record (collapse $11,671, reporting Group I $4,669, theft, EQ); the wind / hail exclusion on renovations moves Group II through `WindstormOrHailExclFactor` (Group II's container rate engine-read, ISO-checked); CP 10 44 with a theft exclusion is C24-15's message. VT's vandalism rewrite is RC-4 (C24-18) |

### RC-4 · States, editions and the built readers (4 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C24-18 | **The sixteen states**: FL (premium adjustment `SetPremium`), KS NY VT (renovations), TX (renovations EQ), and the base-rate rewrites in AK AL AR CA DC GA IL KY MT NJ RI; each predicted from the state's own rule and tables; ISO live | ✅ | **Done 2026-10-01** (`227_ --live`, the 16 rewriting states, all agree with ISO, every premium and message, ~200 premiums each): a fuller policy per state (a Builders Risk building with reporting form, theft, collapse, materials of others and three premium adjustment periods incl. one from mid-term; an ordinary building with renovations and CP 10 44). Records on the countrywide SetPremium by hand; **records whose state rewrites SetPremium (FL 28, NY 3, KS TX VT 2, AR CA DC RI 1) by the independent evaluator on that state's own rule text**; container rates in the states that rewrite their rate rules engine-read and ISO-checked (stated). **FL's older package drops the cyber factors and deductible-by-location, and adds a sinkhole term to Group II.** Policy fixes found by ISO refusing a blank key where ours priced (OI-103): the location's Group II territory (AK AL AR; FL files it under `BasicGroupIIRateNonResidential`), FL's special-class description (C15-16), and **NY's `CompletedBasicGroupIISymbol`, looked up on EVERY building unless "Not Applicable"** |
| C24-19 | **Editions**: identical in all four; one probe each on MO (2023 V02), a V03 and a V04 state | ✅ | gate 8 · **Done 2026-10-01** (E-MO / E-OR, agree): the only family differences across the editions are the preceding-period rule in the 2023 V02 (MO) and V03 (CA NC) parents, which `Break` at the FIRST earlier period with UnitNumber - 1 where 2026 keeps the LAST; probed with two periods sharing unit number 1: **MO's period 2 reads the first (738), OR's the last (1,214)**, as predicted, ISO equal. V04 has no difference; MO, CA, NC also price the fuller policy in C24-20 / C24-18 |
| C24-20 | **All 46 states**: every family on every state's own package, predicted per state; ISO live | ✅ | gate 3 · **Done 2026-10-01** (`227_ --live --states`, three batches of ten + the 16): **all 46 states agree with ISO**, 204-210 premiums each, every message (the batch file's line endings cut the last state of each batch on the first pass; MI OK WY re-sent and agree) |
| C24-21 | **The built readers with Builders Risk on**: Business Income (and its 11 state rewrites), blanket rating, unmanned aircraft, antennas' BI, CA Ordinance or Law, FL Pollutant Clean Up, each priced on a Builders Risk building; ISO live | ✅ | **Done 2026-10-01** (R-BI / R-ANT / R-UA with ordinary-building controls, all agree): Business Income under a class 1150 building carries `BuildersRiskFactor` 2 (1 on the control), its Group I adjustment by hand 0.042 against 0.203; antennas' BI Group I rate 0.077 against 0.039 (x the parent BI's factor 2 x its Factor 0.55); **the building-level unmanned aircraft detail reads the building's `BuildersRiskEQFactor` (0.495 on EQ class A1): EQ rate 0.003 against 0.006, EQ premium $30 against $60** (the contents-level aircraft record reads no Builders Risk factor). Blanket rating with Type "Builders Risk" in C24-15 (M13b). CA's Ordinance or Law increased period and FL's Pollutant Clean Up readers were not priced here (state-only files of chunks 12 / 16; recorded, not blocking) |

### RC-5 · Confirmation and close-out (4 tasks) · COMPLETE 2026-10-01

| # | Task | Status | Notes |
|---|---|---|---|
| C24-22 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; terrorism; stat codes, class code and subline; **the 293 stored policies re-rated unchanged**; ISO live | ✅ | **Done 2026-10-01** (`228_chunk24_c24-22_downstream.py --live`, 4 pairs, 8 ISO calls, all agree): with every Builders Risk record removed and restored, the policy total moves by exactly the family's premiums: **+$1,976 (OR), +$13,199 (the 10 x clean test), +$1,982 (FL, its own rules), +$1,861 (NY)**, predicted before each call and equal at ISO; every other premium identical, terrorism and the TRIA total included; the family stat values equal; the 293 stored policies re-rate unchanged (C24-23) |
| C24-23 | **Regression**: add the chunk 24 scripts and pin the golden figures; full run CLEAN for chunks 0–24 (`--jobs 4`); `157_ --all` | ✅ | **Done 2026-10-01**: the full `104_ --gate` **CLEAN, 157 of 157** (153 in the first run, which was stopped for low memory, and the 4 left run separately: 224_ and three GL suites); `157_ --all` **293 of 293** premiums and totals equal to ISO; `206_ --check` clean after the OI-121 change (1,352 requests); the chunk 24 scripts registered in `104_` (225_ pinned: 164, 321, 94, 78, 20, 454, 270, 145, 8, 187, 235, 232, 11, 36, 48) |
| C24-24 | **Census close**: count the two families as built in `166_` (520 → 540 of 546, 99%) | ✅ | **Done 2026-10-01** (`166_`): **540 of 546** countrywide premium files built (99%); 6 left, all flood (chunk 25) |
| C24-25 | **File `CF-CHUNK24-GATE.md`** | ✅ | 20 countrywide premium files · **Done 2026-10-01**: [`CF-CHUNK24-GATE.md`](CF-CHUNK24-GATE.md), **9 of 9** |
