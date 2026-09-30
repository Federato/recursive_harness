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

**Status: TASKS SET 2026-09-28, 1 of 25** (the census). Next, once chunk 23 is gated: RC-1, C24-02.

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

### RC-1 · Evidence and plumbing (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C24-01 | **Opening census**: population, formulas, tables, messages by record and by form / wording, sibling names, every edition, state layer, stored evidence, attach points, engine readiness, **and the Builders Risk trail** | ✅ | **Done 2026-09-28** (`905_chunk24_census.py`, 3 s). Findings above: 20 premium records, 1 priced by ISO (144 responses); 36 messages; 16 states rewrite (5 `SetPremium`s); identical in all four editions; date arithmetic in premium adjustment; built code reads the BR factors |
| C24-02 | **The stored evidence**: reproduce Builders Risk theft on all 144 priced responses and explain the 5 at $0; why materials of others is $0 on 364; the 3 Basic-cause fixtures end to end; which built readers (C24-03's trail) the 149 Builders Risk policies exercise. No ISO calls | ⬜ | |
| C24-03 | **The built touchpoints**: who writes `BuildersRiskFactor`, `BldrsRiskFactor`, `BuildersRiskEQFactor` and `BldrsRiskTotReptgFormLimit` (Structure, Business Income, Blanket Rating Detail, with their state rewrites), what each reader sees with Builders Risk on and off, class 1150's coverage-type rule; **all 293 stored policies re-rated unchanged** | ⬜ | gate 6 |
| C24-04 | **Attach map and switches**: the Builders Risk forms on Structure, the premium adjustment and renovations detail records, the sub-contractors coverage and exclusion records (no premium: confirm), every on-switch, blank-input defaults | ⬜ | gate 2 (with C24-06) |
| C24-05 | **Premium adjustment by hand**: reporting periods, `FormAnnualPremium`, `AnnualPremiumOfPrecedingReportingPeriod`, `ProRate`, the DateCreate / DateDifference / DatePart steps (OI-107), each written down in days and checked against the engine | ⬜ | |
| C24-06 | **Tables and literals**: the 8 Builders Risk tables (collapse options, completed-value multiplier rows, EQ factor rows), the empty countrywide theft factor and FL's, and every state-filed table under any name (Group II symbols MT NY; construction; deductibles) | ⬜ | gates 2, 5 |

### RC-2 · Golden cases (7 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C24-07 | **Builders Risk theft**: reproduce a stored response, then a new limit and deductible; ISO live | ⬜ | gate 1 |
| C24-08 | **Reporting form**: five coverage groups, not blanketed and blanketed (blanket average vs own rate discriminated), a blanket limit equal to the sum of reporting limits; ISO live | ⬜ | |
| C24-09 | **Renovations**: both completed-value multiplier rows, the coinsurance modifier, five groups; ISO live | ⬜ | |
| C24-10 | **Premium adjustment**: two reporting periods with dates chosen so the day count decides a dollar, five groups plus the blanket manual premium; ISO live | ⬜ | |
| C24-11 | **Collapse during construction**: each of the three options on Broad and Special; ISO live | ⬜ | |
| C24-12 | **Materials of others and CP 10 44**: the manual premium through the modifiers; theft of building materials on an ordinary building with its theft deductible factor; ISO live | ⬜ | |
| C24-13 | **Builders Risk earthquake**: the EQ riders on renovations, reporting and premium adjustment, with EQ factor rows chosen to move a dollar; ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C24-14 | **Zero cases**: each limit blank; reporting form with building limit not 0; a period of zero days and a reversed period; the empty theft factor outside FL; materials of others with no manual premium; each switch off; predict both readings, ISO live | ⬜ | gate 4 |
| C24-15 | **Messages**: all 36, triggered and silent: the form-with-Builders-Risk rules, class 1150, the $500 minimum deductible at 499 / 500, the blanket reporting-limit sum, NY's U / V / W both ways, Public Institutional Plan (AL KS RI); ISO live | ⬜ | gate 9 |
| C24-16 | **Shared names**: `BuildersRiskFactor` vs `BldrsRiskFactor`, `BuildersRiskEQFactor`, the building chain's rates as Builders Risk reads them, `Limit` / `LimitToUse`, `ManualPremium`, `ProRate`, diffed rather than assumed; whether a submitted value survives | ⬜ | gate 6 |
| C24-17 | **Exclusion records**: cyber-incident factors in all 20 formulas; VT's vandalism, the wind / hail exclusion and theft exclusion (CP 10 44 not valid with it), each at a limit where the factor moves a dollar | ⬜ | gate 7 |

### RC-4 · States, editions and the built readers (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C24-18 | **The sixteen states**: FL (premium adjustment `SetPremium`), KS NY VT (renovations), TX (renovations EQ), and the base-rate rewrites in AK AL AR CA DC GA IL KY MT NJ RI; each predicted from the state's own rule and tables; ISO live | ⬜ | |
| C24-19 | **Editions**: identical in all four; one probe each on MO (2023 V02), a V03 and a V04 state | ⬜ | gate 8 |
| C24-20 | **All 46 states**: every family on every state's own package, predicted per state; ISO live | ⬜ | gate 3 |
| C24-21 | **The built readers with Builders Risk on**: Business Income (and its 11 state rewrites), blanket rating, unmanned aircraft, antennas' BI, CA Ordinance or Law, FL Pollutant Clean Up, each priced on a Builders Risk building; ISO live | ⬜ | |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C24-22 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; terrorism; stat codes, class code and subline; **the 293 stored policies re-rated unchanged**; ISO live | ⬜ | |
| C24-23 | **Regression**: add the chunk 24 scripts and pin the golden figures; full run CLEAN for chunks 0–24 (`--jobs 4`); `157_ --all` | ⬜ | |
| C24-24 | **Census close**: count the two families as built in `166_` (520 → 540 of 546, 99%) | ⬜ | |
| C24-25 | **File `CF-CHUNK24-GATE.md`** | ⬜ | 20 countrywide premium files |
