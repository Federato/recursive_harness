# Property chunk 18: task list and status

**Valuation and condition modifiers: six families that change how a loss is
valued or what the policy tolerates.** Opened 2026-09-28.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 18, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`185_chunk18_census.py`](../scripts/cf/185_chunk18_census.py), run 2026-09-28,
log `results/cf-raas/logs/chunk18_census.log`), which carries chunk 15's two census checks
(messages in **every** rule file; each premium rule compared in **every countrywide edition a
state stands on**) and chunk 17's third: **messages searched by form number and wording, not only
by record name**.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Status: OPEN 2026-09-28, 1 of 23 tasks** (the census). Next: RC-1, C18-02.

---

## In plain English first

These six change how a claim is valued or what the policy puts up with:
- **Agreed Value**: the insurer agrees the value up front, so no coinsurance penalty applies.
- **Inflation Guard**: the limit grows automatically through the year.
- **Functional Valuation**: an old building is valued at the cost of a functionally equivalent one, not an exact replica.
- **Increase in Rebuilding Expenses Following Disaster**: extra money for the surge in building costs after a catastrophe.
- **Vacancy Permit**: cover continues while a building sits empty (normally it would be cut back).
- **Peak Season**: a higher contents limit for the busy months, dated by period.

**None of their 84 premium records has ever been priced by ISO.** Agreed Value
and Inflation Guard records are on **every** stored example policy (364 buildings,
206 contents rows, 82 Business Income): Business Income created the Watercraft
record automatically in chunk 17, and these look the same. All $0, so RC-1 must
say why before any golden case.

## What the census found, before any task ran

| Family | Premium records | ISO has priced | Tables read directly (CW rows) | States that rewrite it | Messages (any file) | Editions |
|---|---|---|---|---|---|---|
| **Agreed Value** (Building, Contents, BI, Special Class, SCBI, Leased Property) | 30 | 0 (records on all 364 fixtures, always $0) | `AgreedValueFactor` (1), `AgreedValueFactorBusnIncome` (1); reads the **blanket average rates** (chunk 9) | FL (3 `SetPremium`s) | **22, every one found only by form / wording**: not valid with CP 15 01 / 08 / 09 / 20, CP 11 05, CP 13 20, Builders Risk; EQ sub-limit CP 10 29 / 10 45 (×5 coverages); SC's CP 01 10 | **20 files differ in CW 2023 V02** (MO) |
| **Inflation Guard** (Building, Contents, Special Class) | 15 | 0 (on all 364 fixtures) | `InflationGuardBldg` (16) | CA (2 EQ `SetPremium`s) | 0 | same in all four |
| **Functional Valuation** (Building; Personal Property other than stock) | 10 | 0 | `FunctionalValuationFactor` (2; CT files its own), `PostLossOrdinanceOrLawOptionFactor` (1; FL) | CT (switch + total), FL (`SetPremium`), WV (switch) | 4, by wording: KS Public Institutional Plan; SC CP 01 10 | **all 10 differ in CW 2023 V02** (MO) |
| **Increase in Rebuilding Expenses** (CP 04 09) | 10 | 0 | `RebuildingExpensesFactor` (5), `AdditionalExpenseCoveragePercentageConverted` (100); FL files both | FL (switch) | 2: CP 04 09 not valid with the values selected (Building, SC) | same |
| **Vacancy Permit** (CP 04 50; + Molten Material and Radioactive riders) | 14 | 0 | **22**: vacancy factors (8; KS VT), Group I min rate (16; NY), Standard Property Policy vandalism rate (8; DC KS NY), vandalism exclusion (161) and status (157; FL GA KS NY), sprinkler leakage, coinsurance (FL), 10 subline tables (AR DC NY RI) | **9**: AL AR CT DC FL KS NY RI VT (KS NY VT `SetPremium`; the rest sublines, coinsurance, vandalism, sprinkler) | 14: CP 04 50 period dates (from after to; within policy) ×2; not valid with coverage; CP 04 60 / 04 61 same property; excepted-cause checkboxes | same; **date arithmetic** (DateCreate / DateDifference / DatePart) |
| **Peak Season** (CP 12 30; blanket contents) | 5 | 0 | Contents LOI factors (324 / 54 / 54; AL GA NC SC TX file Group II), blanket coinsurance (1) | CA (EQ calcs), FL (rates, `SetRate`) | 12: CP 12 30 period dates, vs CP 13 10 / coverage form, the General Information form required, blanket-only | same; **date arithmetic** |

**What shapes the plan:**

1. **The auto-created $0 records.** Agreed Value and Inflation Guard sit on every
   stored policy at $0. RC-1 finds the switch for each (option, limit, coinsurance,
   blanket) before RC-2 predicts a dollar.
2. **Two families read other finished work.** Agreed Value reads the blanket
   average rates (chunk 9) when the coverage is blanketed, and the coverage's own
   final rate when not. Peak Season is a blanket-contents coverage with its own
   General Information record and dated periods. Both need chunk 9's blanket policy
   as well as the ordinary one.
3. **Dates.** Vacancy Permit and Peak Season price by period: DateCreate /
   DateDifference / DatePart. OI-107 (DateDifference's sign, pinned in chunk 11)
   applies; every period case is predicted in days by hand.
4. **Missouri's edition differs for 30 files.** Agreed Value (20) and Functional
   Valuation (all 10) have a different `SetPremium` in CW 2023 V02. MO gets its own
   golden probe in RC-4, not just a sweep row.
5. **Vacancy Permit is the widest state layer in the chunk.** Nine states rewrite it,
   and it borrows chunk 8's sprinkler-leakage and vandalism machinery (FL GA KS NY
   file their own vandalism tables).
6. **Messages hide from the record-name search.** All 22 Agreed Value messages
   and all 4 Functional Valuation messages name the form or the wording, not the
   record. The census found them only because of chunk 17's lesson.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C18-01 | **Opening census**: population, formulas, tables, messages by record **and by form / wording** in every file, every edition, state layer, stored evidence, attach points, engine readiness | ✅ | **Done 2026-09-28** (`185_chunk18_census.py`, 16 s). Findings above: 84 premium records, 0 priced by ISO; 33 tables; 54 message rules; 17 state rewrites (11 states); 30 files differ in CW 2023 V02; date nodes in Vacancy Permit and Peak Season; no unregistered element |
| C18-02 | **The $0 fixtures**: why Agreed Value and Inflation Guard price $0 on all 364 / 206 / 82 / 28 stored policies (auto-created? which input switches each on); which input turns each family on, flipped one at a time. No ISO calls | ⬜ | |
| C18-03 | **Attach map and switches**: every record's parent (including Leased Property's Agreed Value and Peak Season's General Information / Limit detail records), each container's own rules, every on-switch shape, every blank-input default that zeroes a premium | ⬜ | gate 2 (with C18-05) |
| C18-04 | **Borrowed values**: every path to another record resolved on a real tree in its loop context (final rates, **blanket average rates**, LOI factors, the coinsurance and vandalism / sprinkler factors, the modifiers); hand = engine on every record, on the ordinary **and** the blanket policy | ⬜ | gate 6 |
| C18-05 | **Tables and literals**: every table's rows and key literals, and every state-filed table under any name (CT FL functional valuation; FL rebuilding; the vacancy and vandalism tables of DC FL GA KS NY VT; AL GA NC SC TX contents LOI) | ⬜ | gates 2, 5 |

### RC-2 · Golden cases (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C18-06 | **Agreed Value**: all five forms on Building, Contents, BI, Special Class and SCBI, not blanketed and blanketed (the average-rate reading discriminated), plus Leased Property; ISO live | ⬜ | gate 1 |
| C18-07 | **Inflation Guard**: Building, Contents and Special Class at two percentages from `InflationGuardBldg`; ISO live | ⬜ | |
| C18-08 | **Functional Valuation**: Building and Personal Property other than stock, both factor rows and the post-loss ordinance option; ISO live | ⬜ | |
| C18-09 | **Increase in Rebuilding Expenses**: Building and Special Class, percentages from the 100-row converted table (chosen so the conversion decides a dollar); ISO live | ⬜ | |
| C18-10 | **Vacancy Permit**: Building and Contents with both riders (Molten Material, Radioactive), a period predicted in days by hand, with and without vandalism and sprinkler-leakage exclusions; Standard Property Policy vandalism rate; ISO live | ⬜ | |
| C18-11 | **Peak Season**: blanket contents with a General Information record and a dated period, each LOI factor looked up by hand; ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C18-12 | **Zero cases**: each option / percentage / limit blank or "Not Applicable"; zero-length and reversed periods; a period outside the policy term; Agreed Value on a coverage without coinsurance; EQ riders without earthquake; each switch off; predict both readings, ISO live | ⬜ | gate 4 |
| C18-13 | **Messages**: all 54 found (22 Agreed Value, 4 Functional, 2 Rebuilding, 14 Vacancy, 12 Peak Season), each triggered and silent, the period-date messages at their boundaries; ISO live | ⬜ | gate 9 |
| C18-14 | **Shared names**: `Factor`, `Rate`, `LimitToUse`, the blanket average-rate fields, `CoinsuranceFactor`, the vacancy and vandalism fields, `CoverageOnPolicyIndicator`, diffed rather than assumed; who writes each; whether a submitted value survives | ⬜ | gate 6 |
| C18-15 | **Exclusion records**: cyber-incident factors in every formula; Vacancy Permit's vandalism and sprinkler-leakage exclusions (chunk 8's records) and which record drives each, tested at a limit where the factor moves a dollar | ⬜ | gate 7 |

### RC-4 · States and editions (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C18-16 | **Vacancy Permit's nine states**: KS NY VT `SetPremium`; AL AR DC RI sublines; CT coinsurance; FL vandalism; each state's own tables (DC FL GA KS NY VT); ISO live | ⬜ | |
| C18-17 | **The other rewrites**: FL Agreed Value (3), CA Inflation Guard EQ (2), CT FL WV Functional Valuation, FL Rebuilding switch, CA FL Peak Season; each predicted from the state's own rule and tables; ISO live | ⬜ | |
| C18-18 | **Editions**: **MO (CW 2023 V02) golden probes for Agreed Value and Functional Valuation**, whose formulas differ; one probe each on a V03 and a V04 state | ⬜ | gate 8 |
| C18-19 | **All 46 states**: every family on every state's own package (ordinary and blanket policy), predicted per state; ISO live | ⬜ | gate 3 |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C18-20 | **Downstream**: the policy total moves by exactly the families' premiums, with a clean test predicted before its ISO call; terrorism; stat codes; the blanket roll-up (chunk 9) unmoved except by the families; ISO live | ⬜ | |
| C18-21 | **Regression**: add the chunk 18 scripts and pin the golden figures; full run CLEAN for chunks 0–18 (`--jobs 4`); `157_ --all` | ⬜ | |
| C18-22 | **Census close**: count the six families as built in `166_` (322 → 406 of 546, 74%) | ⬜ | |
| C18-23 | **File `CF-CHUNK18-GATE.md`** | ⬜ | 84 countrywide premium files |
