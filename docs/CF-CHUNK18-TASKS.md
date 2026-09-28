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

**Status: OPEN, 15 of 23 tasks** (RC-1 to RC-3 complete 2026-09-28; `188_chunk18_rc3.py --live`: 29 zero / message / name / exclusion cases, ISO agrees on all 29). Next: RC-4, C18-16 (Vacancy Permit's nine states).

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
| C18-02 | **The $0 fixtures**: why Agreed Value and Inflation Guard price $0 on all 364 / 206 / 82 / 28 stored policies (auto-created? which input switches each on); which input turns each family on, flipped one at a time. No ISO calls | ✅ | **Done 2026-09-28** (`186_chunk18_rc1.py`). All **293** stored responses carrying Agreed Value / Inflation Guard: ISO $0 = ours $0. Why: on every one, `AgreedValueOption` is No / Not Applicable and `InflationGuard` Not Applicable (the records are always on the policy, switched off). Flipped on the OR policy: Agreed Value Yes → Building BGI **$10**; Inflation Guard 4% → **$5**, 28% → **$37** (0.14 × the building's $261); **Agreed Value Yes with no `AgreedValueLimit` → $0, no message**; Inflation Guard "Blanket Inflation Guard Value Applies" unblanketed → $0 |
| C18-03 | **Attach map and switches**: every record's parent (including Leased Property's Agreed Value and Peak Season's General Information / Limit detail records), each container's own rules, every on-switch shape, every blank-input default that zeroes a premium | ✅ | **Done 2026-09-28**. All 84 attach as the census found. **Functional Valuation attaches only when the parent's `ValuationType` is "Functional Valuation" and is DELETED otherwise** (Structure / PersonalProperty `AttachForm…`), as Mining was. Agreed Value switches on `AgreedValueOption` (unblanketed) or `BlktAgreedVal` (blanketed) and prices from the coverage's final rate × `AgreedValueLimit` or the blanket's `…AvgRateAgreedVal` × `LimitToUse`; Inflation Guard on `InflationGuard` / `BlktInflationGuard`, priced as a factor × the **coverage record's finished premium** (or the Additional Locations special coinsurance record's, or the EQ endorsements'); Rebuilding on `EQCovOnlyIndicator`; Vacancy and Functional forms by cause; the Vacancy riders on the Molten Material / Radioactive records' existence. Blank-input zeros: Rebuilding's converted percentage, Peak Season's averaged rates and LOI factors |
| C18-04 | **Borrowed values**: every path to another record resolved on a real tree in its loop context (final rates, **blanket average rates**, LOI factors, the coinsurance and vandalism / sprinkler factors, the modifiers); hand = engine on every record, on the ordinary **and** the blanket policy | ✅ | **Done 2026-09-28**. **53 of 84 records priced, hand = engine on every one** (three trees, Basic / Broad / Special). **Vacancy Permit's pro-rata factor 0.247 = 90 days ÷ 365, by hand**, from `PermitPeriodFrom` / `To` and the policy's `EffectiveDt` / `ExpirationDt` (the payload must carry them). Not priced here: 17 EQ riders (no earthquake on the policy), 4 Vacancy riders (need the Molten Material / Radioactive records), 5 Leased Property records (chunk 11's leasehold parent not built), and a few forms at $0 with the switch on: RC-2's inputs |
| C18-05 | **Tables and literals**: every table's rows and key literals, and every state-filed table under any name (CT FL functional valuation; FL rebuilding; the vacancy and vandalism tables of DC FL GA KS NY VT; AL GA NC SC TX contents LOI) | ✅ | **Done 2026-09-28**. Tables and rows as the census (Agreed Value 1.05 / BI 1.10; Inflation Guard 2%→0.01 … 28%→0.14; Functional 1.30 / 1.25, post-loss 1.02; Rebuilding 0.10 / BGII 0.15; Vacancy CPP 0.13 / SPP 0.40, Broad 0.04, Special 0.053, EQ 0.006, other causes 0.10, BGII min 0.006). **TX files its own subline tables (`…TX`) that no Vacancy file reads**: sibling-table trap, check TX's Vacancy stat codes live in C18-16 / 19. DC's `VacancyPermitBasicGroupIRate` is header-only and unread |

### RC-2 · Golden cases (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C18-06 | **Agreed Value**: all five forms on Building, Contents, BI, Special Class and SCBI, not blanketed and blanketed (the average-rate reading discriminated), plus Leased Property; ISO live | ✅ | **Done 2026-09-28** (`187_chunk18_rc2.py --live`, A1-A4). All Agreed Value forms predicted, engine = hand, **ISO agrees** on every premium and message. Unblanketed (A1 Special, A2 Broad): 0.05 × the coverage's final rate × the **agreed limit** (80,000, not the 100,000 coverage limit): building BGI **$10**; BI / SCBI use **1.10** (BI BGI $9). Blanketed (A3, chunk 9's blanket, detail `AgreedVal` Yes): the blanket's `…AvgRateAgreedVal` × `LimitToUse`: **$13 / $25** on the two buildings. Leased Property (A4): **switched on by the CONTENTS row's `AgreedValueOption`** (the detail copies it over its own), 0.05 × the contents' final rate × the item limit: $20 / $2 / $13. The EQ riders stay off without an EQ sub-limit form (RC-3). ISO types `AgreedValueLimit`, `UnitNumber`, `BlktIDNum`, `TotalLimit` as numbers · gate 1. **Chunk 19's Leased Property (C19-11) reads `AgreedValueFactor`: its golden case must agree with this one** |
| C18-07 | **Inflation Guard**: Building, Contents and Special Class at two percentages from `InflationGuardBldg`; ISO live | ✅ | **Done 2026-09-28** (I1). A factor × **the coverage record's finished premium**: building 6% (0.03) $9, contents 20% (0.10) $20, special class 12% (0.06); 12 of 12 predicted, ISO agrees 123 of 123 |
| C18-08 | **Functional Valuation**: Building and Personal Property other than stock, both factor rows and the post-loss ordinance option; ISO live | ✅ | **Done 2026-09-28** (F1). **The two forms differ**: the building keeps 1.30 and prices (1.30 × post-loss 1.02 − 1) × rate × limit ($79); the contents stores round3(1.25 − 1) = 0.25 ($52). ISO agrees 135 of 135 |
| C18-09 | **Increase in Rebuilding Expenses**: Building and Special Class, percentages from the 100-row converted table (chosen so the conversion decides a dollar); ISO live | ✅ | **Done 2026-09-28** (R1, 25% of 1,000,000). Adjustment × form factor (BGI 0.10, BGII 0.15, Special 0.10, EQ 0.10) × the amount (value × converted %) / 100: building $55 / $10 / $12 / $3, special class $16 / $75 / $12 / $3; ISO agrees. At 7% of 100,000, Group II and Special round to $0 |
| C18-10 | **Vacancy Permit**: Building and Contents with both riders (Molten Material, Radioactive), a period predicted in days by hand, with and without vandalism and sprinkler-leakage exclusions; Standard Property Policy vandalism rate; ISO live | ✅ | **Done 2026-09-28** (V1). Pro-rata = permit days / policy days (building 90 → 0.247, contents 181 → 0.496, by hand = engine); **the package discount applies to the vandalism part only**; building BGI $152, contents BGI $246. ISO agrees 139 of 139. Payloads must carry the policy's `EffectiveDt` / `ExpirationDt` |
| C18-11 | **Peak Season**: blanket contents with a General Information record and a dated period, each LOI factor looked up by hand; ISO live | ✅ | **Done 2026-09-28** (P1). (premium at the total limit − at the base limit) × the season's pro-rata (60 days → 0.164): BGI $8, Special $4; ISO agrees 130 of 130 (without a blanket General Information record; RC-3 tests its message). ISO types `FullValue` as a number |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C18-12 | **Zero cases**: each option / percentage / limit blank or "Not Applicable"; zero-length and reversed periods; a period outside the policy term; Agreed Value on a coverage without coinsurance; EQ riders without earthquake; each switch off; predict both readings, ISO live | ✅ | **Done 2026-09-28** (`188_chunk18_rc3.py --live`, Z1-Z12). ISO agrees on all 12. Agreed Value Yes with **no agreed limit → $0, no message**; No → $0; Inflation Guard Not Applicable / blank / "Blanket … Applies" unblanketed → $0; **Functional Valuation on Replacement Cost property is deleted** (no record); post-loss option No → building 1.30 − 1 ($74, not the 1.326 reading); Rebuilding % blank → $0; Vacancy period blank or zero days → $0; **a reversed Vacancy period prices NEGATIVE** (−30 days → −0.082 → BGI **−$50**, with the From-after-To message); Peak Season period blank or limit 0 → $0. **A blank date must be omitted: ISO refuses an empty string** ("not a valid DateTime") · gate 4 |
| C18-13 | **Messages**: all 54 found (22 Agreed Value, 4 Functional, 2 Rebuilding, 14 Vacancy, 12 Peak Season), each triggered and silent, the period-date messages at their boundaries; ISO live | ✅ | **Done 2026-09-28** (M1-M11, M8b). The census's form-number search was fixed first (`185_`: the regex held literal backspaces; forms now also from each package's Form Pages table, with a check that each family finds one): **no chunk 18 message had been missed** (2 new hits are earthquake-form messages, false positives via Peak Season's EQ forms; Agreed Value and Inflation Guard have no form of their own). Every message case fires and agrees with ISO, whole message sets equal: Agreed Value vs CP 15 01 / 08 / 09 / 20, CP 13 20, Builders Risk renovations; CP 04 50 vs coverage, CP 04 60, the excepted-cause checkboxes, the period dates; CP 12 30 vs CP 13 10 (**Value Reporting attaches only on a reporting-frequency coinsurance**), the coverage form (**set on the occupancy**), the period dates; KS Public Institutional Plan; **SC CP 01 10 attaches itself on ValuationLaw "Exemption Does Not Apply"** · gate 9. **First re-run the message census with the form-number search fixed**: `185_`'s regex held literal backspaces (`\x08`) where `\b` belongs, so it never matched (the 22 Agreed Value messages were found by wording alone). Use `r"\b(?:CP|IL) \d\d \d\d\b"`, take form numbers also from the package's Form Pages table (`901_chunk20_census.py`'s `form_pages()`), and add a denominator check (the form search must find at least one form per family) |
| C18-14 | **Shared names**: `Factor`, `Rate`, `LimitToUse`, the blanket average-rate fields, `CoinsuranceFactor`, the vacancy and vandalism fields, `CoverageOnPolicyIndicator`, diffed rather than assumed; who writes each; whether a submitted value survives | ✅ | **Done 2026-09-28** (S1, S2). A submitted Agreed Value `Factor` 1.20 is used (0.20: building BGI **$39**); a submitted Vacancy pro-rata 0.5 is used (BGI **$307**). Both `IsNull`-guarded, and **ISO does the same** · gate 6 |
| C18-15 | **Exclusion records**: cyber-incident factors in every formula; Vacancy Permit's vandalism and sprinkler-leakage exclusions (chunk 8's records) and which record drives each, tested at a limit where the factor moves a dollar | ✅ | **Done 2026-09-28** (X0-X2). Cyber-incident exclusion at an agreed limit of 1,000,000: Agreed Value BGI **$121 → $120**; ISO agrees. X2 (Inflation Guard + the exclusion) agrees but **cannot discriminate**: at $9 a second 0.995 would not move a dollar, so whether Inflation Guard applies it again is untested (its formula reads no cyber factor, only the finished premium) · gate 7 |

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
