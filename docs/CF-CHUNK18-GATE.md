# Property chunk 18: the gate

**The valuation and condition modifiers: Agreed Value, Inflation Guard,
Functional Valuation, Increase in Rebuilding Expenses Following Disaster,
Vacancy Permit and Peak Season, in all 46 states.** Filed 2026-09-29. **9 of 9,
and all 23 tasks done.** Task record: [`CF-CHUNK18-TASKS.md`](CF-CHUNK18-TASKS.md).

**In plain English.** These six change how a claim is valued or what the
policy puts up with. The insurer can agree the value up front (Agreed Value),
the limit can grow through the year (Inflation Guard), an old building can be
valued at the cost of a modern equivalent (Functional Valuation), extra money
can cover the jump in building costs after a disaster (Rebuilding Expenses),
cover can continue while a building stands empty (Vacancy Permit), and a shop
can carry more stock in its busy months (Peak Season). **None of their 84
premium records had ever been priced by ISO.** Agreed Value and Inflation Guard
sat on every stored example policy at $0, because every one had the option
switched off. So every record needed its own test case.

Every figure was worked out by hand before it ran, from the family's own filed
table and rule, and then checked against ISO live. **ISO agreed on everything
it rated:**
- 9 golden cases pricing the six families on the ordinary and the blanket policy, every premium on each policy compared;
- 12 zero cases, 12 message cases, 2 submitted-value probes and 3 exclusion cases, messages included;
- **all 46 states** and 4 Standard Property Policy probes: 49 of 50 policies agree, 2,352 predicted records, 8,747 premiums, every message (the 50th is KS's Standard Property Policy, which ISO refuses: OI-103);
- the downstream check: the total moves by exactly the families' premiums ($2,520), including a clean test predicted before its call ($2,554) and chunk 9's blanket ($38); no terrorism effect; the blanket roll-up unmoved except its own Agreed Value fields; 214 stat values equal.

**One engine change, made with your go (RC-4):** Vermont files the vacancy
factor table with a header and no rows. Our engine took the empty table as
final and priced Vacancy Special at $0; ISO falls back to the countrywide rows.
Fixed for Property only ([`CF-ENGINE-FIX-EMPTY-STATE-TABLES.md`](CF-ENGINE-FIX-EMPTY-STATE-TABLES.md)),
and all 87 stored chunk 18 ISO responses re-rate identically after it.

**Two of my downstream predictions were wrong (C18-20), each found when the
engine and ISO answered, and each explained:**
- **"Functional Valuation" as the valuation type is two things at once.** It
  changes the building's and contents' own rates (building Group I $1,923 →
  $2,032), and it is the family's switch: the Functional Valuation records
  attach and price on it alone ($724 before the post-loss option). The first
  run was $866 off because of this.
- **A Leased Property row prices the leased item itself** ($713 at 200,000):
  that is chunk 11 / 19's own record, not this chunk's.

Both now sit in the "before" policy, and the total moves by exactly the hand
difference. My script's first draft also had a name bug that made two of its
own checks empty; the fix asserts the names before they are used.

**Countrywide premium files built: 406 of 546 (74%)**, up from 322.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `187_chunk18_rc2.py --live`, on chunk 7's five-coverage Oregon policy with chunk 15's modifiers and chunk 10's earthquake election, dated 09/17/2026 – 09/17/2027. **Agreed Value** (A1–A4): (factor − 1) × the coverage's final rate × the **agreed** limit: building BGI **$10**, BI BGI $9 (factor 1.10); blanketed on chunk 9's blanket **$13 / $25**; Leased Property $20 / $2 / $13. **Inflation Guard** (I1): a factor × the coverage's finished premium: building 6% $9, contents 20% $20. **Functional Valuation** (F1): building (1.30 × 1.02 − 1) **$79**, contents 0.25 **$52**. **Rebuilding** (R1, 25% of 1,000,000): building **$55** / $10 / $12 / $3. **Vacancy Permit** (V1): building 90 days (0.247) **$152**, contents 181 days (0.496) **$246**. **Peak Season** (P1): 60 days (0.164) $8 / $4. Engine = hand on every record; **ISO agrees on all 9 policies**. Pinned in the regression |
| 2 | Every table's row count stated | ✅ | C18-05. **Countrywide:** `AgreedValueFactor` 1 (1.05), `AgreedValueFactorBusnIncome` 1 (1.10), `InflationGuardBldg` 16 (2% → 0.01 … 28% → 0.14), `FunctionalValuationFactor` 2 (1.30 / 1.25), post-loss 1 (1.02), `RebuildingExpensesFactor` 5, converted percentage 100, `VacancyPermitFactors` 8, Group I minimum rate 16, SPP vandalism rate 8, vandalism exclusion 161 / status 157, 10 subline tables of 1, Peak Season's contents LOI factors 324 / 54 / 54. **State-filed, under any name:** CT functional valuation, FL post-loss / rebuilding / converted percentage / vandalism rate (149), FL GA KS NY vandalism status, KS VT vacancy factors (**VT's header-only**, the engine fix), NY Group I minimum rate, DC KS NY SPP vandalism rate, AL GA NC SC TX contents LOI. **TX files `SublineBasicGroupIExcludingSprinklerLeakageTX` that no Vacancy file reads**; DC's `VacancyPermitBasicGroupIRate` is header-only and unread |
| 3 | Every state is enumerated | ✅ | `189_chunk18_rc4.py --all --live`: **all 46 states**, 48 records each, predicted from each state's own rule, tables and edition. **Engine 50 of 50, ISO 49 of 50**: the 50th is KS's Standard Property Policy, which ISO refuses (KS files its own factors with no SPP earthquake row) and we price: added to OI-103. Probes: Standard Property Policy in OR / KS / NY / DC. Puerto Rico is excluded by standing rule. **CA's two rewrites are earthquake-only and untested** (no CA earthquake setup is built, as in chunks 16–17) |
| 4 | Every `0` tested against its consuming branch | ✅ | `188_`, Z1–Z12, ISO agrees on all 12. Agreed Value "Yes" with **no agreed limit → $0, no message**; Inflation Guard "Not Applicable", blank, or "Blanket … Applies" unblanketed → $0; Functional Valuation on Replacement Cost property is **deleted** (no record); post-loss option "No" → 1.30 − 1 ($74); Rebuilding percentage blank → $0; Vacancy period blank or zero days → $0; **a reversed Vacancy period prices NEGATIVE** (−30 days → −0.082 → BGI **−$50**, with the From-after-To message); Peak Season period blank or limit 0 → $0. **A blank date must be omitted: ISO refuses an empty string** |
| 5 | Every hardcoded literal key listed | ✅ | C18-05 (`186_`, per family). "Yes" / "No", "Not Applicable", "", "Blanket Inflation Guard Value Applies", "Yes, Included / Not Included in Blanket", "Replacement Cost", "Functional Valuation", "90%" / "100%", "No Coverage", "Commercial Property Policy" / "Standard Property Policy", the vacancy excepted-cause values ("Fire", "Fire and Vandalism", "Fire and Allied Lines", "Fire, Vandalism and Allied Lines", "Fire and Sprinkler Leakage", "Fire, Vandalism and Sprinkler Leakage"), "Broad" / "Special". Literal misses: the reversed period (priced negative, as ISO does), and a blank date (ISO refuses) |
| 6 | Shared-name traps diffed | ✅ | C18-04 and C18-14. All 84 records placed on real trees (ordinary and blanket); every borrowed path resolved to an owner record, 53 priced with hand = engine. **Leased Property's Agreed Value copies the CONTENTS row's `AgreedValueOption` over its own**. The blanketed Agreed Value reads the blanket's `…AvgRateAgreedVal` × `LimitToUse`, not the coverage's rate. A submitted Agreed Value `Factor` (1.20) and Vacancy pro-rata (0.5) are used, `IsNull`-guarded, **and ISO does the same** |
| 7 | Every exclusion's endorsement record identified | ✅ | C18-15. The cyber-incident exclusion (a policy record) moves Agreed Value BGI **$121 → $120** at an agreed limit of 1,000,000; ISO agrees. Vacancy Permit's vandalism and sprinkler-leakage parts are chunk 8's records, tested in V1 and the nine-state sweep (**the package discount applies to the vandalism part only**). Inflation Guard reads no cyber factor, only the finished premium: whether it applies the factor a second time is **untested** (at $9 a second 0.995 moves no dollar) |
| 8 | The edition basis stated | ✅ | C18-18. **MO's CW 2023 V02 differs for 30 files** (Agreed Value 20, Functional Valuation all 10): MO has its own golden probes and agrees. Every state priced from its own edition in the sweep (MO V02; CA NC V03; FL RI MA VT V04) |
| 9 | No unexplained validation message | ✅ | C18-13, M1–M11 and M8b. The form-number search was fixed first (the census's regex held literal backspaces): **no chunk 18 message had been missed**. Agreed Value vs CP 15 01 / 08 / 09 / 20, CP 13 20, Builders Risk renovations; CP 04 50 vs coverage, CP 04 60, the excepted-cause checkboxes, the period dates; CP 12 30 vs CP 13 10 (**Value Reporting attaches only on a reporting-frequency coinsurance**), the coverage form, the period dates; KS Public Institutional Plan; SC CP 01 10. **ISO's message sets equal ours** on every chunk 18 case, including all 46 states |

## What the chunk established, in submission terms

* **Agreed Value** prices (factor − 1) × the coverage's final rate × **`AgreedValueLimit`**
  (send it as a number; without it the premium is $0 and no message says so).
  Blanketed, it reads the blanket's average rate and `LimitToUse`, switched by the
  blanket detail's `AgreedVal`. Leased Property follows the **contents** row's option.
* **Inflation Guard** is a factor × the coverage's finished premium, by percentage.
* **Functional Valuation is switched on by the parent's `ValuationType`**, which
  also changes the parent's own rates. The building adds the post-loss ordinance
  option (1.02); the contents stores 0.25.
* **Rebuilding Expenses** = form factor × (value × converted percentage) ÷ 100.
  Small amounts round to $0 on Group II and Special.
* **Vacancy Permit and Peak Season price by period**: permit days ÷ policy days,
  to three places. **The payload must carry the policy's `EffectiveDt` /
  `ExpirationDt`**; a blank date must be left out, not sent empty; a reversed
  period prices negative.
* **They feed the policy total and one stat field (`ExposureStatAmount`);
  terrorism does not read them; the blanket roll-up moves only in its own Agreed
  Value fields.**

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-103** | Two more cases where ISO refuses and we price: KS's Standard Property Policy (its own vacancy factors have no SPP earthquake row), and a contents territory another state does not file (Oregon's "Multnomah" outside Oregon; ours prices $0) | no; engine behaviour decision (chunk 28) |
| CA earthquake rewrites untested | Inflation Guard EQ and Peak Season EQ calcs: no CA earthquake setup is built | no; with chunk 10's state EQ territories |
| Inflation Guard × cyber exclusion | Whether Inflation Guard applies the cyber factor a second time is not discriminated at $9 | no; needs a larger premium probe |
| Leased Property parent | Chunk 19's Leased Property (C19-11) reads `AgreedValueFactor`; its golden case must agree with A4 here | no; chunk 19 |
| Process gap found | The downstream "before" policy assumed that a family's switch never touches its parent. The check that was missing: T0's priced records are listed and predicted like T1's, and an engine-only total check runs before any ISO call. Now in `190_` | no |

## Confirmation

* **Regression CLEAN**, 2026-09-29, scoped with your go: the four chunk 18 scripts not yet run in the runner (`186_`, `188_`, `189_`, `190_`) pass, 4 of 4, 0 failures (`104_ --only … --no-gl --jobs 2`, 20m08s, `chunk18_c18-21_regression_scoped.log`). `187_` passed with its pinned figures ($10 / $13 / $25 / $79 / $52 / $55 / $152 / $246) in the full run of the same day, which Claude Code stopped for low system memory at 36 of 120, all passing (not a test failure). **The full run is carried from 2026-09-28**: 115 of 115 after the last engine change (`ae81ac7`, the empty-state-table fix); **no engine code has changed since** (`git diff` on `cf_engine/`, `gl_engine/` empty)
* **`157_ --all`**: carried from 2026-09-28, run after that engine fix: all 293 of 293 stored ISO policies, every premium and policy total equal. Not rerun: no engine change since
