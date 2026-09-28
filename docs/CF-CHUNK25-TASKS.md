# Property chunk 25: task list and status

**Flood: flood cover added by endorsement, for every coverage group, with its own
blanket rating. It is the largest family in the corpus and the last countrywide
coverage.** Tasks set 2026-09-28; chunk 18 is being built in the other terminal, and chunks 19–24 wait.

Derived from the remaining-build plan on [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html#remaining)
(chunk 25, sized by [`166_remaining_coverage_census.py`](../scripts/cf/166_remaining_coverage_census.py))
and the opening census ([`906_chunk25_census.py`](../scripts/cf/906_chunk25_census.py), run 2026-09-28,
4 s, log `results/cf-raas/logs/chunk25_census.log`). It runs the same checks as `905_` (messages in
every rule file, `SetPremium` per in-force edition, form numbers from `Form Pages`, sibling
names), plus a tenth for this chunk: **the flood trail**, meaning every rule file outside the family
that writes or reads a flood field.

**A census slip, caught and fixed.** The first run's pattern `Flood` also matched chunk 21's sewer
files, whose names end `…NotFloodReltd` ("not flood related"). That made 11 premium files, not 6. The
pattern is now anchored to the endorsement's own names, and the sibling-name check lists the sewer
files as such. The same sibling check also shows that 20 of the 66 messages it found are Business
Income coverage-form rules (CP 00 30 / 00 32 / 00 50), which the Form Pages table ties to the flood BI
record. They're excluded below, leaving **46 flood messages**.

**Standing rules carried in.** Analysis and gates only: no engine code without the user's go.
"All states" means the **46**; Puerto Rico is excluded. Live ISO comparisons at **2026-09-17**
(OI-105). Live payloads set `WindstormOrHailDeductible` (OI-103), use a special-class description
the state files (C15-16) and the full building construction value (C17-06). Every figure is
predicted by hand from the family's own filed table and rule **before** it runs (175_'s
evaluator and method), and each probe is chosen so the competing readings give different dollars.
Every pass prints `[i/n elapsed]` progress to `results/cf-raas/logs/`; the quick regression tier
runs after each RC, the full one at the gate.

**Order.** After chunk 24. It builds on Structure, Location, the contents and special class records,
Business Income (chunks 1–7) and blanket (9), and it closes two items left open: chunk 17's
Off-Premises flood factor and WV's two Ordinance or Law flood forms (chunk 23's list).

**Status: TASKS SET 2026-09-28, 1 of 26** (the census). Next, once chunk 24 is gated: RC-1, C25-02.

---

## In plain English first

The Flood Coverage Endorsement (CP 10 65; WV's own version is CP 10 68) adds flood to a building,
its contents, a special class item, business income or special class business income. It's rated
like the flood insurance market does it. There's a **loss cost** by state or county, adjusted
by seven **rate modification** tables (flood zone, floor of interest, number of stories and so on),
a **community rating** credit, a deductible, insurance-to-value, and whether the cover sits **in
excess of the federal flood program (NFIP)** maximum. Several risks can be put in a **flood
blanket**, which has its own average rate. WV also has two Ordinance or Law forms for flood, priced
as company-entered premiums.

**ISO has priced 3 of the 8 premium records** (Building, Contents and Business Income, all on one
stored policy, `STC_CP000015648`). The other five have never been priced: Special Class, SCBI, the
blanket detail, and WV's two forms.

## What the census found, before any task ran

| Family | Premium records | How it prices | Tables | States that rewrite it | Messages | Editions |
|---|---|---|---|---|---|---|
| **Flood Coverage Endorsement** (Building, Contents, Special Class, BI, SCBI) | 5 | limit × `FloodAdjustedRate`: loss cost × 7 rate-modification factors × community rating × deductible × insurance-to-value × annual aggregate (BI: × business income factor and type-of-risk factors); 38–51 rules per file | **27**: flood loss cost (**0 rows countrywide**, 37 states file it), 7 rate-modification tables (132–264 rows each, the two-range key chunk 10's fix made readable), BI factor (131), community rating (12 + class code 11), flood zone (25), floor of interest (10), stories (9), deductible conversion (13), max NFIP amount (2), codes and sublines. **AK and FL file their own copy of all of them** | **10**: MA NC NJ NY SC TX VA price by **county** (their own loss-cost tables); **NY rewrites `SetPremium` on all six** premium files; AK FL rewrite the blanket and location rules; WV swaps in its own form CP 10 68 | **46** (below) | same in all four |
| **Flood blanket** (`FloodCovEndtBlanketRatingDetail`) | 1 | limit × its own `BlanketAverageRate` (32 rules: total full value, 100% values per level, max NFIP building / contents amounts) | as above | AK NY WV | in the 46 | same |
| **WV Ordinance or Law flood** (state-only) | 2 | **manual premium** through the modifiers | none | WV only | 0 | same |

**Rules: 705 KB across the 8 countrywide flood files** (the plan said 641 KB). The Building, Contents
and Special Class files are about 125 KB each. **Loss cost has three sources:** 37 states file
`FloodLossCost`; 7 (MA NC NJ NY SC TX VA) look up county tables with an all-other-county fallback;
**AK and FL file no flood loss cost table at all**, although they file every other flood table.

**Messages (46).** They cover: the General Information record required with CP 10 65 / 10 68; a
blanket needing at least 2 risks and at least one coverage; the deductible below each value and below
total property value; the limit at or below full value (and the blanket's 100% values); coinsurance
level ≤ 12; construction identical across special class and its BI; matching inception dates;
"Other Flood Insurance" fields; not under Builders Risk; and WV's CP 10 68 versions of each (plus
CP 04 13 / 04 28 required with it).

**The flood trail (check 10): built code that writes or reads flood fields.**

| Built file | What it does with flood | States rewriting |
|---|---|---|
| **Structure** (chunk 1) | `LookupFloodLossCost`, writes `OperationalUnitFloodBaseRate`; reads flood zone, excess-over-NFIP, blanket indicator | AK FL MA NC NJ NY SC TX VA WV |
| **Location** (chunk 1) | writes `FloodTotalPropertyValue`, `HighestBusnIncomeFloodBaseRate`; reads community rating, flood zone | AK FL NC NJ NY TX VA WV |
| **Personal Property / Special Class** | initialise flood rating; SC checks construction matches | AK FL (SC) |
| **Business Income / SCBI** | write the BI cyber-flood factor `…FloodToUse` | NY |
| **Main ruleset** | writes the flood cyber-incident factors and `FloodAttachmentIndicator…` | AK FL KS NY VT |
| **Off-Premises Interruption** (chunk 17) | writes and reads `FloodCovFactor` (**chunk 17's open item**) | AK AR DC NY RI (detail) |
| **WV Ordinance or Law** (chunk 12, state files) | reads `FloodOnlyLimitation…` | WV |

**What shapes the plan:**

1. **Much of Flood already lives in built code.** The flood loss-cost lookup and base rate sit in
   **Structure**, the property totals and highest BI base rate in **Location**, and the cyber factors
   in the main ruleset, all rewritten in up to 10 states. Today no stored policy but one has flood
   on. RC-1 proves all 293 re-rate unchanged, and RC-1's trace starts in Structure, not in the flood
   files.
2. **Three loss-cost sources, and two states with none.** State tables (37), county tables with an
   all-other fallback (7), and **nothing at all in AK and FL**, which file every other flood table.
   What AK and FL price, or refuse, is a question to settle, not assume (C25-19).
3. **Seven two-range rate-modification tables.** Chunk 10's banded-lookup fix made them readable. Each
   golden case lands values inside, at the edge of, and outside a band.
4. **The blanket has its own arithmetic.** An average rate from 100% values per coverage level, capped
   by NFIP maximum amounts, with its own deductible and coinsurance rules. That's 81 KB in one file.
5. **There is real evidence, but it's thin.** One stored policy has Building, Contents and BI flood
   priced by ISO; it's reproduced first. Special Class, SCBI and the blanket have never been priced.
6. **It closes two open items.** Off-Premises Interruption's flood factor (chunk 17) and WV's two
   Ordinance or Law flood forms (chunk 23's list). With them, the countrywide count reaches **546 of
   546** and the state-only list is empty.

---

## Task groups, in priority order

### RC-1 · Evidence and plumbing (7 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-01 | **Opening census**: population, formulas, tables, messages by record and by form / wording, sibling names, every edition, state layer, stored evidence, attach points, engine readiness, **and the flood trail** | ✅ | **Done 2026-09-28** (`906_chunk25_census.py`, 4 s). Findings above: 6 CW + 2 WV premium records, 3 priced by ISO on one policy; 27 tables; 46 messages; 10 states; identical in all four editions; flood logic already in Structure, Location and the main ruleset |
| C25-02 | **The stored policy** (`STC_CP000015648`): Building, Contents and BI flood reproduced, hand = engine = ISO, every factor named; the location record. No ISO calls | ⬜ | |
| C25-03 | **The built touchpoints**: Structure's loss-cost lookup and base rate, Location's totals and highest BI base rate, Personal Property / Special Class initialisation, BI's cyber-flood factor, the main ruleset's flood indicators, each with its state rewrites; **all 293 stored policies re-rated unchanged** | ⬜ | gate 6 |
| C25-04 | **Attach map and switches**: the location record, the endorsement on five coverage records, the blanket at policy level and its detail, the General Information requirement; every on-switch; blank-input defaults | ⬜ | gate 2 (with C25-07) |
| C25-05 | **The flood rate by hand**: loss cost, the 7 rate-modification factors (which keys each reads), community rating, deductible conversion, insurance-to-value, excess over the NFIP maximum, annual aggregate; BI's business income and type-of-risk factors; each step written down and checked against the engine | ⬜ | |
| C25-06 | **The flood blanket by hand**: total full value, 100% values per level, NFIP maximum building / contents amounts, the average rate, coinsurance level, deductible; checked against the engine | ⬜ | |
| C25-07 | **Tables and literals**: all 27 tables' rows and keys, the two-range keys of the 7 rate-modification tables (bands and edges), the empty countrywide loss cost and the 37 state filings, the 7 states' county tables and their all-other fallback | ⬜ | gates 2, 5 |

### RC-2 · Golden cases (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-08 | **Building**: a zone, floor and stories chosen so each rate-modification band decides a dollar, with and without community rating; ISO live | ⬜ | gate 1 |
| C25-09 | **Contents**: the same risk's contents, and a deductible that moves a dollar; ISO live | ⬜ | |
| C25-10 | **Business Income and SCBI**: the business income factor and type-of-risk combinations; ISO live | ⬜ | |
| C25-11 | **Special Class**: never priced by ISO; construction matched to its BI; ISO live | ⬜ | |
| C25-12 | **Flood blanket**: two and three risks, the average rate, a case capped by the NFIP maximum; ISO live | ⬜ | |
| C25-13 | **Excess over NFIP and insurance-to-value**: cover in excess of the NFIP maximum vs primary, and insurance-to-value either side of a percentage band; ISO live | ⬜ | |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-14 | **Zero cases**: deductible at or above value; limit above full value; no General Information; a blanket with one risk; blank zone, floor or stories; flood under Builders Risk; each switch off; predict both readings, ISO live | ⬜ | gate 4 |
| C25-15 | **Messages**: all 46, each triggered and silent, the value and deductible limits at the boundary, and WV's CP 10 68 versions; ISO live | ⬜ | gate 9 |
| C25-16 | **Shared names**: `FloodAdjustedRate`, `BlanketAverageRate` (vs chunk 9's), `IncludedInBlkt`, `FloodCovFactor`, the deductible fields, the flood cyber factors and their `…ToUse` copies, `OperationalUnitFloodBaseRate`, diffed rather than assumed; whether a submitted value survives | ⬜ | gate 6 |
| C25-17 | **Exclusion records**: the flood cyber-incident factors (written in the main ruleset, 5 state rewrites) in all 6 formulas, and BI's `…ToUse` variant, each at a limit where the factor moves a dollar | ⬜ | gate 7 |

### RC-4 · States, editions and the open items (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-18 | **The county states**: MA NC NJ NY SC TX VA, each with a county in the table and one falling to all-other; NY's `SetPremium` rewrites; ISO live | ⬜ | |
| C25-19 | **AK and FL: no loss cost**: what the engine and ISO do with flood in the two states that file every flood table but the loss cost (price, zero or refuse); predicted both ways; ISO live | ⬜ | |
| C25-20 | **WV**: CP 10 68 in place of CP 10 65, with CP 04 13 / 04 28; the two Ordinance or Law flood manual premiums; WV's O&L reading the flood-only limitation; ISO live | ⬜ | |
| C25-21 | **Editions and all 46**: identical in the four editions, with one probe each on MO (2023 V02), a V03 and a V04 state; then every state's own package, predicted per state; ISO live | ⬜ | gates 3, 8 |
| C25-22 | **Off-Premises Interruption's flood factor**: chunk 17's open item priced with flood on, on its own and its detail records (AK AR DC NY RI rewrites); ISO live | ⬜ | |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-23 | **Downstream**: the policy total moves by exactly the flood premiums, with a clean test predicted before its ISO call; terrorism; stat codes and the with / without NFIP sublines; **the 293 stored policies re-rated unchanged**; ISO live | ⬜ | |
| C25-24 | **Regression**: add the chunk 25 scripts and pin the golden figures; full run CLEAN for chunks 0–25 (`--jobs 4`); `157_ --all` | ⬜ | |
| C25-25 | **Census close**: count Flood as built in `166_` (540 → **546 of 546, 100%**); re-run `904_`'s ownership list: the state-only list empty | ⬜ | |
| C25-26 | **File `CF-CHUNK25-GATE.md`** | ⬜ | 6 countrywide premium files + WV's 2 |
