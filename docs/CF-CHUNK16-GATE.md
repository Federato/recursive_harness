# Property chunk 16: the gate

**The rated Business Income options and the small property adds, plus
state-only Mine Subsidence, in all 46 states.** Filed 2026-09-25. **9 of 9,
and all 23 tasks done.** Task record: [`CF-CHUNK16-TASKS.md`](CF-CHUNK16-TASKS.md).

**In plain English.** ISO's own example policies already switched these
coverages on, and chunk 14 matched them, but those examples only reached 16 of
43 premium records. This chunk proved the other 27 and the rest of each gate.
Most of the families are Business Income add-ons that price as a slice of the
Business Income rate chunks 5 and 7 built: a longer indemnity period, no
waiting period, a longer civil-authority period. Two are small location or
contents coverages with their own tables (pollutant clean-up, spoilage). One
is a factor on the Group I rate (molten material). Mine Subsidence works
differently in each of its five states.

Every figure was worked out by hand before it ran, from the family's own filed
table and rule, and then checked against ISO live. **ISO agreed on everything
it rated:**
- the golden cases, including every never-priced record: RC-2's policies, each with every premium on the policy compared;
- 12 zero cases, 16 message cases, the shared-name probe and 3 exclusion cases, messages included;
- **all 46 states** and 6 probes: 52 policies, 1,372 predicted records, 8,342 premiums, every message;
- the downstream check: the total moves by exactly the families' premiums, including a clean test (T2) predicted before its call; no terrorism effect; 508 stat values equal.

**No engine change was needed.** Four of my predictions were wrong, and each
is recorded with its explanation, found after the engine or ISO answered:
- Pollutant Clean Up's "highest" rate is the last building's;
- the rate is the special class's when that is higher;
- Texas applies its Spoilage factor only in a catastrophe area;
- the first total check left out the earthquake forms.

The engine and ISO agreed on each of these.

**Countrywide premium files built: 290 of 546 (53%)**, up from 251.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `175_chunk16_rc2.py`, on chunk 7's five-coverage Oregon policy with chunk 15's modifiers and chunk 10's earthquake election. **Extended Period of Indemnity**, 270 days: **$33 / $3 / Broad $7 / EQ $2**. The Special Class BI forms, **no waiting period** and **Civil Authority**, including Radius as a manual premium at $1,013. **Pollutant Clean Up**, two buildings: **$22** (the $60 reading when the buildings are swapped). **Molten Material** on five coverages. **Spoilage**, Florists: **$513**. **Mine Subsidence** in its five states: IL **$31** / **$46**, KY **$21**, IN **$250 / $75 / $180 / $40**, OK **$960**, WV **$310**. The engine equals the hand figure on every record, and **ISO agrees on every policy**. Pinned in the regression |
| 2 | Every table's row count stated | ✅ | C16-05. **Countrywide:** time period 2, `ExtendedPeriodFactor` 11, Civil Authority 3, Pollutant rate 5 / deductible 5 / code 1 / by-location 1 / stat 24, Spoilage class 16 / rate 18 / selling price 1 / code 1 / subline 1, Molten 1 / subline 1. **State-filed, under any name:** FL time period; AK and FL EPI; CA, FL and MA Civil Authority; FL, GA, KS and NY Spoilage class; `SpoilageAddlFactor` in AL FL GA NC SC TX VA (3 rows each; KS and RI header-only); MA's Pollutant discount; AL, KS and RI Public Institutional Plan; Mine Subsidence IL 450 + 1 + 1, KY 294 + 1, IN and WV header-only (manual premium) |
| 3 | Every state is enumerated | ✅ | `177_chunk16_rc4.py --live`: **all 46 states**, 28 records each, predicted from each state's own rule and tables. **Engine 46 of 46, ISO 46 of 46**, and six probes: TX catastrophe area, AL Public Institutional Plan, RI, and the FL / RI / GA truncation probes. Puerto Rico is excluded by standing rule. The earthquake forms are proven in Oregon only; state EQ territories are chunk 10's |
| 4 | Every `0` tested against its consuming branch | ✅ | `176_`, Z1–Z12, ISO 12 of 12. EPI blank or "Not Applicable" → **$0**. A Business Income limit of 0 → **$0**. BI earthquake "No Coverage" → **EQ form $0**. A blank time period → **factor 0 → $0**. A blank Civil Authority period → rate forms **$0**, while Radius **stays $1,013**. Pollutant limit $10,000 → **$0**; at **$5,000 the premiums go negative** (−$2 / −$5), and ISO returns the same. A blank Pollutant deductible → **$0**. A blank Spoilage description → **$0**. IL "No Coverage" → **$0** |
| 5 | Every hardcoded literal key listed | ✅ | C16-05: "Not Applicable", "", "No Coverage", the "Yes, Included / Not Included in Blanket" EQ switch, the cause-of-loss form names, the $10,000 Pollutant threshold, "Eliminated" / "Replaced By 24 Hours", the Spoilage cause and maintenance-agreement keys, and each Mine Subsidence state's construction and option keys |
| 6 | Shared-name traps diffed | ✅ | C16-04 and C16-15. All 43 premium files were placed on a real tree, and every borrowed path resolved **in its loop context** to an owner record, never a Table wrapper. Molten Material's Business Income forms read **both** Business Income's `Factor` and their own. `Factor`, `BaseFactor`, `LimitToUse`, `Rate` and `SellingPriceFactor` are each `IsNull`-guarded, so a submitted value survives, and **ISO honours it too** (S1: $109, equal). `Premium` and `CoverageOnPolicyIndicator` are overwritten |
| 7 | Every exclusion's endorsement record identified | ✅ | C16-16. The cyber-incident exclusion is a **policy record**. Each peril group's factor is **0.995**, and the Business Income forms read their parent's "…ToUse" copies. At a $1,000,000 BI limit: **$332 without, $330 with**, and engine and ISO agree (X1 at $33 could not discriminate and is recorded as such) |
| 8 | The edition basis stated | ✅ | C16-19. Four countrywide parents are in force (2026 V01; 2023 V02 / V03 / V04), and every state priced from its own edition's files. **Missouri (2023 V02) has no Special Class or Special Class BI Molten Material**: it is not priced there, and ISO agrees. V02's different EPI BI EQ formula sits with earthquake, outside the sweep |
| 9 | No unexplained validation message | ✅ | C16-14, M1–M13 (16 cases). CP 15 56; CP 04 07 ×2, each narrower than first guessed; CP 04 40 ×2; CP 10 60 on five coverages, with its building and deductible checks; Mine Subsidence's IL, IN (county eligibility), OK and WV messages. **ISO raises every predicted message, and its message sets equal ours** on every chunk 16 case, including all 46 states |

## What the chunk established, in submission terms

* **The Business Income options are slices of Business Income's final rate:**
  (factor − 1) × the parent's rate × its limit. The factor comes from the
  option's own table: extended period days, the waiting-period choice, or the
  civil-authority days. **Civil Authority's Radius form is a manual premium**,
  entered by the company, on chunk 15's formula.
* **Pollutant Clean Up prices only the limit above $10,000.** A limit under
  $10,000 gives a **negative premium**, and ISO agrees. Its location rate is the
  **last** building's Group I rate, **unless the special class's is higher**.
  List the buildings knowing that.
* **Spoilage** runs description → class → rate × selling-price factor × limit
  ÷ 100. **FL and RI truncate** the limit ÷ 100. **Seven states add a factor
  for "both causes"**, and Texas only in a catastrophe area, where its premium
  still does not use it.
* **Molten Material is a factor on the Group I rate chain** on five coverages.
  It is $0 on the Special cause of loss. The Public Institutional Plan (AL, KS,
  RI) moves it by 0.85.
* **Mine Subsidence is five mechanisms.** IL and KY price from tables. IN, OK
  and WV take a company-entered premium, and OK's goes through the modifiers.
  The policy record's `Premium` is the sum over buildings.
* **They feed the policy total and the three stat-code fields; terrorism does
  not read them.**

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-103** | One more case where ISO refuses and we price: a Mortgageholders E&O record with no limit (its rate lookup has no row) | no; engine behaviour decision (chunk 28) |
| Submitted derived fields | Here ISO honours a submitted `Factor`, like our engine (S1). This is evidence for the open item, not a new defect | no |
| Process gap found | My hand evaluator left out loop context and two operators (`Convert`, `IsNotNull`) at first. Each was caught because a hand figure disagreed with the engine and the operand trace was read. The check that would have caught it sooner: an evaluator-coverage test listing every `rul:` element in the families' files against the evaluator's handlers before any prediction runs | no |

## Confirmation

* **Regression CLEAN for chunks 0–16**, 2026-09-25: 110 scripts and the General Liability suites, 0 failures (`104_chunk10_c10-21_regression.py`, with `175_` pinned to $33 / $22 / $60 / $513 / $46 / $960 and `174_`, `176_`–`178_` added).
* **`157_ --all`**: all 293 of 293 stored ISO policies, every premium and total equal.
