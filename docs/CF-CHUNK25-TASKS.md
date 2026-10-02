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

**Status: GATED 2026-10-02, 26 of 26, 9 of 9** ([`CF-CHUNK25-GATE.md`](CF-CHUNK25-GATE.md); RC-1–RC-5 `229_`–`233_`, every premium ISO agreed on; no engine change). **546 of 546 countrywide premium files built (100%)**; the state-only list closed. Open: OI-122 (ISO defect, ISO agrees with ours), OI-123 (MO messages only).

## RC-1 findings (2026-10-02), in plain English first

**Flood is priced from a loss cost, then ONE adjustment table picked by the deductible, then the community discount.**
The census read it as "loss cost × seven factors (zone, floor, stories…)". That was wrong: the flood zone is a key of
the loss cost, floor and stories feed statistics only, and the deductible chooses **one** of the seven
rate-modification tables (500 / 1,000 → table 1 … 1,000,000 → table 7). That table is keyed by the deductible,
insurance-to-value % and the location's total flood property value, and it interpolates inside each 1-point ITV band.

| What | Finding |
|---|---|
| **The stored policy** (C25-02) | `STC_CP000015648` is an **Alaska** policy. AK (and FL) replace all six flood premium rules with **manual premium × package mod × IRPM** and empty the rate, stat-code and location rules. ISO $650 / $440 / $84 = hand = engine. So "AK and FL file no loss cost" is answered from the rule text: they don't rate flood at all, the company enters the premium (C25-19 still confirms it live) |
| **Building / Contents / Special Class** (C25-05) | rate = r3(r3(r3(loss cost × LCM) × annual aggregate) × table factor); × CRS factor (r3) only when the location carries a CRS grade; premium r0 through package mod, IRPM and the two flood cyber factors. Contents use the **Contents** loss-cost row and the **building's** construction; Special Class uses the Building row and **its flood record's own `ConstructionType`** (blank → $0) |
| **Excess over NFIP** | only deductibles 750,000 / 1,000,000 have a factor (tables 6 / 7, keyed on the record's **own full value**, and only above the 500,000 NFIP maximum); any other deductible prices $0. **Tables 5–7 file factor 0** in 16 (deductible, value-band) cells from some ITV upward: $0 by the table, not a missing row |
| **Insurance-to-value** | above 100% (limit > full value) the factor is 0 → $0; a blank `ExcessOverMaxNFIPIndicator` is neither primary nor excess → $0; blank zone → $0; blank deductible → $0 on the three property records (BI / SCBI still price) |
| **BI / SCBI** | Building loss-cost row × LCM × aggregate × BI factor (MaxPeriod / Monthly / Extra Expense factor, else the type-of-risk factor; combined types weight two `BusnIncomeFactor` rows). **No** modification table, excess factor or community rating |
| **OI-122 (new; answered in RC-2)** | BI flood with maximum period / monthly limit / extra expense only, in an **operational unit**, takes the location's "highest" building base rate. The rule that finds it sets its running maximum to 0 and then only stores a new one if the stored one is blank, so as written it **never moves off 0**: BI prices **$0** with a CRS grade; with no grade every comparison equals 0 and the **last** building's rate is taken (0.472, not the highest 0.637). Our engine does exactly this. **ISO agrees (C25-10, O1 $0 / O2 $531 where the intended reading gives $716)**: an ISO defect, no engine change |
| **Blanket** (C25-06) | average rate = r3(Σ members' r0(full value × their flood rate) ÷ Σ 100% values); members price $0 themselves; excess blankets count only members above the NFIP maximum; BI counts its `AnnualNetIncome`. Two, three and BI-member blankets and an excess blanket: hand = engine |
| **Touchpoints** (C25-03) | Location `FloodTotalPropertyValue` (unblanketed full values only), Structure `OperationalUnitFloodBaseRate`, the cyber flood factors and `FloodAttachmentIndicatorCode` all as read; 9 states rewrite a touchpoint rule (AK FL MA NC NJ NY SC TX VA) |
| **RC-3 (C25-14..17)** | **Contents and Special Class in a blanket take the blanket detail's deductible; the building always takes the location's** (M8: a 500,000 detail deductible zeroes the contents' rate, the blanket falls from $1,273 to $520; ISO agrees). A limit $1 over full value fires the message but ITV rounds to 100% and the record **still prices** ($607 / $876 / $526). Flood on a Builders Risk building fires three messages and **still prices** ($493 …). `FloodCovIndicator` No zeroes the total property value. "Other Flood Insurance" fires in a state request (ancestor::MasterCFCW/Policy reads as the root, as for stat codes; ISO agrees). Submitted base rate, record deductible, modification factor, adjusted rate, CRS factor, BI factor, type-of-risk factor, aggregate factor and blanket average rate **survive**; total property value, ITV % to use and excess-to-use are **overwritten**. Floor / stories move no dollar. CP 10 75 and 10 76 apply 0.999 (X1 $5,758 → $5,752) |
| **RC-4 (C25-18..22)** | **All 46 states agree with ISO** on a two-location flood policy (five records + a building / contents blanket). The 7 county states price a listed county from the county table and any other from the all-other one (MA Special Class $1,105 vs $830). **AK and FL price every flood record as a company-entered premium** ($0 when blank; AK's blanket detail has no premium rule). **MO's CW 2023 V02 rules differ and ISO follows them**: excess over NFIP always reads table 6 at the 500,000 row (building $57,536 where the 2026 rules give $45,239), contents keep the location's deductible in a blanket (blanket $8,029 vs $3,437), and a blanket's total property value counts only the record's own location ($12,203 vs $12,827); V03 (NC) and V04 (IL) price as 2026. **WV** uses CP 10 68 (form numbers equal), prices its two O&L flood forms as manual premium × package × MPDC × IRPM ($278 / $140) when the O&L record is flood-only, and zeroes O&L Coverage A when `FloodOnlyLimitationOnOrdinanceOrLaw` is Yes. **Off-Premises' flood factor is 1.02 with a BI flood record** (OTC $275 → $281), in OR AK AR DC NY RI: chunk 17's open item closed. **OI-123**: MO's package has five empty `NotExist` tests; ISO reads them true and fires a location message ours does not (messages only) |
| **County states** (C25-07) | the rule names the counties (MA 3, NC 8, NJ 1, NY 5, SC 2, TX 4, VA counties and cities) and picks a county table for them, an all-other table otherwise; **neither table has a county column** |

**Carried from chunk 21 (2026-09-30): the census `906_` now diffs EVERY rule of the family files across the four countrywide editions** (`scripts/cf/_edition_rules.py`, chunk 20's gate item): 8 family files: MO V02 66, V03 37, V04 5 rule differences from 2026 V01. The editions task must judge each one; the census's earlier "identical in all four editions" was a SetPremium-only check. Chunk 21 also found its own edition difference in a PARENT file (MO's sewer caps read `Limit`, not `LimitToUse`): diff the parent files' rules that name this chunk's records too.

---

## In plain English first

The Flood Coverage Endorsement (CP 10 65; WV's own version is CP 10 68) adds flood to a building,
its contents, a special class item, business income or special class business income. It's rated
like the flood insurance market does it. There's a **loss cost** by state or county (keyed by flood
zone and construction), adjusted by **one** of seven **rate modification** tables, chosen by the
deductible and read by insurance-to-value and total property value (*corrected 2026-10-02, RC-1:
the census said seven factors for zone, floor and stories; floor and stories are statistics only*),
a **community rating** credit, and whether the cover sits **in
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
| C25-02 | **The stored policy** (`STC_CP000015648`): Building, Contents and BI flood reproduced, hand = engine = ISO, every factor named; the location record. No ISO calls | ✅ | **Done 2026-10-02** (`229_`). An **AK** policy: AK prices flood as r0(r0(ManualPremium × package mod) × IRPM) on all six records; ISO $650 / $440 / $84 = hand = engine; AK empties the rate rules (no flood rate is computed), the location record's ProcessCall (no CRS factor, deductible number or NFIP maximum) and the three built touchpoints (`SetFloodTotalPropertyValue`, `SetHighestBusnIncomeFloodBaseRate`, `SetOperationalUnitFloodBaseRate`) |
| C25-03 | **The built touchpoints**: Structure's loss-cost lookup and base rate, Location's totals and highest BI base rate, Personal Property / Special Class initialisation, BI's cyber-flood factor, the main ruleset's flood indicators, each with its state rewrites; **all 293 stored policies re-rated unchanged** | ✅ | gate 6. **Done 2026-10-02** (`229_`): all 293 re-rate unchanged; `FloodTotalPropertyValue` = unblanketed full values only; `OperationalUnitFloodBaseRate` per building in the unit; **`HighestBusnIncomeFloodBaseRate` never stores its maximum as written (OI-122)**; every parent runs its flood records; cyber flood factors and `FloodAttachmentIndicatorCode` written; touchpoint rewrites in AK FL MA NC NJ NY SC TX VA listed per rule |
| C25-04 | **Attach map and switches**: the location record, the endorsement on five coverage records, the blanket at policy level and its detail, the General Information requirement; every on-switch; blank-input defaults | ✅ | gate 2 (with C25-07). **Done 2026-10-02** (`229_`): `FloodCovIndicator` Yes keeps / attaches the location record (an empty one if none is sent: every flood record $0), No removes it; `FloodCovEndtBlktIndicator` Yes / No keeps / removes the blanket; a member left `IncludedInBlkt` Yes with no blanket prices $0; six blank inputs each predicted (zone, deductible, full value, `IncludedInBlkt`, excess indicator, SC flood construction) |
| C25-05 | **The flood rate by hand**: loss cost, the 7 rate-modification factors (which keys each reads), community rating, deductible conversion, insurance-to-value, excess over the NFIP maximum, annual aggregate; BI's business income and type-of-risk factors; each step written down and checked against the engine | ✅ | **Done 2026-10-02** (`229_`, 18 trees): hand = 174_'s evaluator = engine on every premium **and every intermediate value** (ITV%, TPV, table factor, base, aggregate, rate, adjusted rate; BI coinsurance, type-of-risk and BI factor). All seven tables (T1, T3–T8), no CRS grade, ITV 50% / 100% / > 100%, aggregate 0.999, excess at 750,000 and 1,000,000 (and a contents value under the NFIP maximum, and deductible 100,000 → $0), combined type of risk, maximum period, extra expense only, the operational unit (OI-122) |
| C25-06 | **The flood blanket by hand**: total full value, 100% values per level, NFIP maximum building / contents amounts, the average rate, coinsurance level, deductible; checked against the engine | ✅ | **Done 2026-10-02** (`229_`, K1–K4): two risks $1,273, three risks with aggregate 0.999 $1,731, with BI $1,952, an excess blanket counting only the building above the NFIP maximum $7,644; hand = evaluator = engine on levels, totals, average rate and premium |
| C25-07 | **Tables and literals**: all 27 tables' rows and keys, the two-range keys of the 7 rate-modification tables (bands and edges), the empty countrywide loss cost and the 37 state filings, the 7 states' county tables and their all-other fallback | ✅ | gates 2, 5. **Done 2026-10-02** (`229_`): 27 tables listed; CW loss cost header-only, 37 states file it (none of AK FL or the county states); each table holds exactly the deductibles the rule sends it, ITV bands contiguous 1 → open; tables 5–7's filed zeros are monotonic; floor / stories / NFIP zone feed stat codes only; the county states name their counties in the rule, not the table; the literals `Y`, `Building`, `Content` and the type-of-risk names have rows |

### RC-2 · Golden cases (6 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-08 | **Building**: a zone, floor and stories chosen so each rate-modification band decides a dollar, with and without community rating; ISO live | ✅ | gate 1. **Done 2026-10-02** (`230_` B1–B8): every rate-modification table 1–7 decides the building dollar (deductible 500 → $36 … 100,000 → $5,758), zones A / X / X500 / D, CRS grade 5 vs none ($493 vs $616); ISO agrees on every premium and message |
| C25-09 | **Contents**: the same risk's contents, and a deductible that moves a dollar; ISO live | ✅ | **Done 2026-10-02** (`230_` B1–B8, C1): the same risks' contents (Contents loss-cost row, the building's construction), and deductible 25,000 vs 10,000 inside table 3 ($643 vs $799); ISO agrees |
| C25-10 | **Business Income and SCBI**: the business income factor and type-of-risk combinations; ISO live | ✅ | **Done 2026-10-02** (`230_` I1, I2, O1, O2): combined manufacturing / mercantile BI $403, SCBI rental without EE $286, maximum period $716, SCBI extra expense only $1,059; **OI-122: ISO $0 (CRS grade) and $531 (no grade, the last building) = as written = ours**; the intended $716 is not what ISO does |
| C25-11 | **Special Class**: never priced by ISO; construction matched to its BI; ISO live | ✅ | **Done 2026-10-02** (`230_` S1, and every B case): Special Class first priced by ISO; it reads its flood record's own construction (Frame $460 on a Joisted Masonry building), SCBI likewise (Masonry Non-Combustible $254); ISO agrees |
| C25-12 | **Flood blanket**: two and three risks, the average rate, a case capped by the NFIP maximum; ISO live | ✅ | **Done 2026-10-02** (`230_` K1–K4): two risks $1,273, three at aggregate $1,731, with BI $1,952, excess blanket counting only the building above the NFIP maximum $7,644; the blanket detail first priced by ISO; ISO agrees |
| C25-13 | **Excess over NFIP and insurance-to-value**: cover in excess of the NFIP maximum vs primary, and insurance-to-value either side of a percentage band; ISO live | ✅ | **Done 2026-10-02** (`230_` E1–E4): excess at 750,000 on three full-value bands ($7,644 / $8,534 / $3,934), 1,000,000 with contents under the NFIP maximum ($0), ITV 50% / 100% / above 100% ($427 / $876 / $0), aggregate 0.999 ($492); ISO agrees |

### RC-3 · Zero cases, messages and names (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-14 | **Zero cases**: deductible at or above value; limit above full value; no General Information; a blanket with one risk; blank zone, floor or stories; flood under Builders Risk; each switch off; predict both readings, ISO live | ✅ | gate 4. **Done 2026-10-02** (`231_` Z1–Z10): deductible ≥ total value (table 6's filed 0, 3 messages), limits 1 over full value (still priced at 100%), no General Information (5 messages, $0), flood on with no record, a one-risk blanket, blank zone, floor / stories (no dollar), flood on Builders Risk (3 messages, still priced), on No Coverage (3 messages), IncludedInBlkt blank ($0); ISO agrees on every premium and message |
| C25-15 | **Messages**: all 46, each triggered and silent, the value and deductible limits at the boundary, and WV's CP 10 68 versions; ISO live | ✅ | gate 9. **Done 2026-10-02** (`231_` M1–M14, 25 cases): **all 45 countrywide flood message rule instances fired at their own level and silent at the boundary** (limit = value, deductible = TPV / TPV + 1, excess deductible = value, blanket limit = total, equal inception dates, insurer entered); ISO agrees on the whole (level, message) set every time. WV's CP 10 68 versions are C25-20's |
| C25-16 | **Shared names**: `FloodAdjustedRate`, `BlanketAverageRate` (vs chunk 9's), `IncludedInBlkt`, `FloodCovFactor`, the deductible fields, the flood cyber factors and their `…ToUse` copies, `OperationalUnitFloodBaseRate`, diffed rather than assumed; whether a submitted value survives | ✅ | gate 6. **Done 2026-10-02** (`231_` S1–S3): nine IsNull-guarded fields keep a submitted value (base rate, record deductible, modification factor, adjusted rate, CRS factor, BI factor, type of risk, aggregate, blanket average rate: S1 $971 / $455 / $293 / $622 / $499); total property value, ITV % to use, excess-to-use are overwritten (B1's dollars); ISO agrees |
| C25-17 | **Exclusion records**: the flood cyber-incident factors (written in the main ruleset, 5 state rewrites) in all 6 formulas, and BI's `…ToUse` variant, each at a limit where the factor moves a dollar | ✅ | gate 7. **Done 2026-10-02** (`231_` X1–X4): CP 10 75 → `CyberIncidentExclusionFactorFlood` 0.999, CP 10 76 → the COL flood and BI flood factors 0.999 (both from the table); every flood premium and the blanket move ($5,758 → $5,752); SCBI extra expense only copies the extra-expense flood factor; ISO agrees |

### RC-4 · States, editions and the open items (5 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-18 | **The county states**: MA NC NJ NY SC TX VA, each with a county in the table and one falling to all-other; NY's `SetPremium` rewrites; ISO live | ✅ | **Done 2026-10-02** (`232_` S-MA … S-VA): each county state's location 1 in a listed county, location 2 in another (VA counties and cities): the county vs all-other tables (32 of 48 rows differ) moved every unblanketed record and the blanket; NY's six SetPremium rewrites (no cyber factors) = hand; ISO agrees on every premium and message |
| C25-19 | **AK and FL: no loss cost**: what the engine and ISO do with flood in the two states that file every flood table but the loss cost (price, zero or refuse); predicted both ways; ISO live | ✅ | **Done 2026-10-02** (`232_` S-AK, S-FL, Z-AK, Z-FL): AK and FL price all six flood records as r0(r0(ManualPremium × package mod) × IRPM) ($0 when blank); AK's blanket detail has no premium rule (ErcRate emptied), FL's is manual; ISO agrees |
| C25-20 | **WV**: CP 10 68 in place of CP 10 65, with CP 04 13 / 04 28; the two Ordinance or Law flood manual premiums; WV's O&L reading the flood-only limitation; ISO live | ✅ | **Done 2026-10-02** (`232_` W1–W3): CP 10 68 on every WV flood record (ISO's form numbers equal ours); O&L flood $278 and tenants' O&L flood $140 = r0(r0(r0(manual × package) × the building's MPDC) × IRPM), on only with `FloodOnlyLimitation` Yes; O&L Coverage A $0 when `FloodOnlyLimitationOnOrdinanceOrLaw` Yes; the CP 10 68 message with no building flood record; ISO agrees |
| C25-21 | **Editions and all 46**: identical in the four editions, with one probe each on MO (2023 V02), a V03 and a V04 state; then every state's own package, predicted per state; ISO live | ✅ | gates 3, 8. **Done 2026-10-02** (`232_`): the every-rule edition diff read rule by rule; MO's (V02) excess factor, blanket deductible and per-location total property value probed against the 2026 reading (EX / ED / ET, three readings that differ in dollars): **ISO follows MO's V02 rules** on all three; NC (V03) and IL (V04) price as 2026; then all 46 states: every premium equal, messages equal except MO's **OI-123** (empty `NotExist`, messages only) |
| C25-22 | **Off-Premises Interruption's flood factor**: chunk 17's open item priced with flood on, on its own and its detail records (AK AR DC NY RI rewrites); ISO live | ✅ | **Done 2026-10-02** (`232_` O- / ON- in OR AK AR DC NY RI): `FloodCovFactor` = 1.02 with a BI flood record, 1.0 without; OTC $275 → $281 in OR; each state's own OTC rule; ISO agrees on all 12 (chunk 17's open item closed) |

### RC-5 · Confirmation and close-out (4 tasks)

| # | Task | Status | Notes |
|---|---|---|---|
| C25-23 | **Downstream**: the policy total moves by exactly the flood premiums, with a clean test predicted before its ISO call; terrorism; stat codes and the with / without NFIP sublines; **the 293 stored policies re-rated unchanged**; ISO live | ✅ | **Done 2026-10-02** (`233_ --live`): the policy total moves by exactly the flood premiums, +$3,521 (OR) / +$3,277 (limits halved, the clean test) / +$10,522 (NY) / +$3,116 (AK) / +$22,828 (MO), predicted before each call and equal at ISO; every other premium, terrorism included, unchanged; the flood stat values equal; the 293 stored policies unchanged (C25-24) |
| C25-24 | **Regression**: add the chunk 25 scripts and pin the golden figures; full run CLEAN for chunks 0–25 (`--jobs 4`); `157_ --all` | ✅ | **Done 2026-10-02** (no engine change in the chunk, so the scaled-back gate): `206_ --check` SNAPSHOT CLEAN (1,609 requests, 1,200,103 fields); `157_ --all` 293 of 293; the chunk 25 scripts registered in `104_` and clean (230_ pinned: 493 616 36 5758 799 643 460 343 403 286 716 1059 531 1273 1731 1952 7644 8534) |
| C25-25 | **Census close**: count Flood as built in `166_` (540 → **546 of 546, 100%**); re-run `904_`'s ownership list: the state-only list empty | ✅ | **Done 2026-10-02** (`166_`): **546 of 546** countrywide premium files built (100%), 0 remaining; `904_`: no unassigned state-only file, chunk 25's two WV files built; the state-only list closed |
| C25-26 | **File `CF-CHUNK25-GATE.md`** | ✅ | **Done 2026-10-02**: [`CF-CHUNK25-GATE.md`](CF-CHUNK25-GATE.md), 9 of 9 |
