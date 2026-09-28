# Property chunk 17: the gate

**The Business Income add-ons: Ordinary Payroll Limitation, Power Heat and
Refrigeration Deduction, Mining Properties BI, Landlord as Additional Insured
(Rental Value), Watercraft Exclusion Buyback and Off-Premises Interruption of
Business, in all 46 states.** Filed 2026-09-28. **9 of 9, and all 23 tasks
done.** Task record: [`CF-CHUNK17-TASKS.md`](CF-CHUNK17-TASKS.md).

**In plain English.** These six are options on a Business Income policy. Two
narrow the cover: ordinary payroll paid for fewer days, and the power and
heating bills a closed business saves. Four add a slice of cover: a
landlord's lost rent, a mine's shutdown, a boat accident, and a vehicle
breakdown away from the premises. **None of their 32 premium records had ever
been priced by ISO** in our stored responses. The 82 stored examples that
carried the Watercraft record all priced $0, because none of them said the
property was on the waterfront. So every record needed its own test case.

Every figure was worked out by hand before it ran, from the family's own filed
table and rule, and then checked against ISO live. **ISO agreed on everything
it rated:**
- 10 golden cases pricing all 32 records, every premium on each policy compared;
- 14 zero cases, 10 message cases, 2 submitted-value probes and 4 exclusion cases, messages included (29 of 29 rated; the 30th ISO refuses, as predicted);
- **all 46 states** and 10 probes: 56 policies, 1,344 predicted records, 9,039 premiums, every message;
- the downstream check: the total moves by exactly the families' premiums ($1,969), including a clean test predicted before its call ($2,643); no terrorism effect; 866 stat values equal.

**No engine change was needed.** Two of my predictions were wrong, each found
after the engine answered and each confirmed by ISO:
- I sent a bare "Fire Resistive" building, which has no conversion row. The
  building needs the full value, e.g. "Fire Resistive - Other Than Reinforced
  Masonry - Other Than Light Steel".
- Business Income **derives** the Special theft risk type from the building
  class and overwrites the value submitted. A Florida apartment building
  (class 0311) gets the apartment rate.

**Countrywide premium files built: 322 of 546 (59%)**, up from 290.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `181_chunk17_rc2.py --live`, on chunk 7's five-coverage Oregon policy with chunk 15's modifiers and chunk 10's earthquake election. **Landlord** (L1–L4): BGI **$77**, Broad **$7** (no loss cost multiplier, LCM 1.3 on the parent), EQ **$6** (Business Income's EQ limit, not the landlord's), SCBI Special **$19** (hardcoded Frame). **Ordinary Payroll** (P1): 0 days $63 / $10 / EQ $5; 90 days $10 / $35 / EQ $5. **Power-heat** (H1): 6 records. **Mining** (M1, a Mining risk): $121 / $55 / $220 / **$253**. **Watercraft** (W1): $9 / **$13**. **Off-Premises** (O1, O2): Collision **$982**, OTC **$343**; SCBI $102 / $35. Engine = hand on every record; **ISO agrees on all 10 policies**. Pinned in the regression |
| 2 | Every table's row count stated | ✅ | C17-05. **Countrywide:** payroll 3 (0 / 90 / 180 days: 1.12 / 1.06 / 1.00), power-heat 1 (1.06), Mining 6 ("None" = 0), `BusnIncomeFactor` 131, `BroadFormBaseRate` 30, Special time-element base rate 24, Watercraft factor 6 + conversion 7, Off-Premises loss cost 6, waiting period 3, extended BI 13, insurance-to-exposure 4 + stat 4, endorsements 3, 7 coverage / stat-code tables of 1. **State-filed, under any name:** FL `BusnIncomeFactor` and Special base rate; AK extended BI (13), AK insurance-to-exposure factor and stat code **header-only**; AR DC RI endorsement factors (2), NY's **header-only**. `OrdinaryPayrollExclusionFactor` is header-only and read by no rule |
| 3 | Every state is enumerated | ✅ | `183_chunk17_rc4.py --all --live`: **all 46 states**, 24 records each, predicted from each state's own rule, tables and edition. **Engine 56 of 56, ISO 56 of 56**, including 10 probes: Standard Property Policy in OR / KS / NY / VT, wind-hail exclusion in OR / AR / DC / NY / RI, and FL on a residential class. Puerto Rico is excluded by standing rule. The earthquake riders are proven in Oregon only; state EQ territories are chunk 10's |
| 4 | Every `0` tested against its consuming branch | ✅ | `182_`, Z1–Z14, ISO 13 of 13 rated. 180 payroll days → **$0**, but **blank days price like 0 days** (0.12). Mining option None or blank → **$0**. Watercraft option blank → **$0**; "Not Applicable" → ISO **refuses** (OI-103). A blank Off-Premises extended period → **$0**, but "Not Applicable" prices (1.00). Collision "No" → Collision $0 only. Landlord on a BI limit of 0 still prices (own limit), except EQ. Landlord coinsurance blank → BGI / BGII / EQ **$0**, Broad priced. BI earthquake "No Coverage" → EQ riders **$0**. At EQ class A1 the 0.06 riders **round to $0** |
| 5 | Every hardcoded literal key listed | ✅ | C17-05 and C17-13. "Not Applicable", "", "None" / "No Coinsurance", "No Coverage", "Standard Property Policy", "Special" / "Broad", "Option A" / "Option B", "72 Hours", "Mining", the EQ "Yes, Included / Not Included in Blanket" pair, FL's residential class codes (0074–0079, 0196–0198, 0311–…), and SCBI Landlord's hardcoded **"Frame"** and **"Other than Apartments and Condominiums"**. Literal misses: Watercraft "Not Applicable" (no factor row) and a blank extended period |
| 6 | Shared-name traps diffed | ✅ | C17-04 and C17-14. All 32 records placed on a real tree; every borrowed path resolved in its loop context to an owner record. **Special Class BI spells the waterfront input `WaterFrontProperty`** (BI: `WaterfrontProperty`). **The Landlord record carries its own `CauseOfLoss`**, which switches Broad / Special, separate from Business Income's, which gates the Special base rate. Mining's own `Limit` is ignored outside a blanket. All 19 family rates and factors are `IsNull`-guarded: a submitted `Factor` (0.5) or `BaseFactor` (1.3) is used, and **ISO does the same** |
| 7 | Every exclusion's endorsement record identified | ✅ | C17-15. The cyber-incident exclusion is a **policy record** (0.995 per peril group, EQ 1.00): at a $1,000,000 landlord limit it moves BGI **$1,290 → $1,284**, BGII $147 → $146, Broad $108 → $107. **Off-Premises reads no cyber factor.** The windstorm-or-hail exclusion on Business Income moves Off-Premises OTC **$343 → $325** (× 0.95), and not in AR DC NY RI, which drop the factor. Watercraft's exclusion (CP 10 35) switches the buyback off. ISO agrees on all |
| 8 | The edition basis stated | ✅ | C17-18. Every premium file is identical in all four countrywide editions (2026 V01; 2023 V02 / V03 / V04), and every state priced from its own edition's files in the 46-state sweep (MO V02; CA NC V03; FL RI MA VT V04). VT's V04 `SetSpecialBaseRate` keeps the Standard Property Policy test that KS and NY drop |
| 9 | No unexplained validation message | ✅ | C17-13, M1–M8s (10 cases). CP 15 10 / CP 15 11 vs Extra Expense Only and the 50% coinsurance minimum (BI and SCBI texts); CP 15 06 vs cause of loss (fires on Basic, silent on Special); FL's CP 15 06 vs residential class. **The form-number search found 4 Watercraft messages the census's record-name search missed**, and each fires and agrees. **ISO's message sets equal ours** on every chunk 17 case, including all 46 states |

## What the chunk established, in submission terms

* **Ordinary Payroll and Power-heat are slices of Business Income's final
  rate:** (factor − 1) × the parent's rate × its limit. So 180 payroll days
  (1.00) prices $0, and a blank number of days prices as 0 days. Send
  `NumOfDays` as a number: ISO refuses it as a string.
* **Mining needs a Mining risk.** Business Income creates the Mining container
  when `TypeOfRisk` is Mining and **deletes it otherwise**. The rate is by
  option and cause, × the loss cost multiplier, on the parent's limit.
* **Landlord Rental Value runs its own rate chain on its own limit and
  coinsurance.** The Broad form reads no loss cost multiplier. The EQ form uses
  Business Income's EQ limit. On a special class, the base rates are always
  Frame / "Other than Apartments". **Set the Landlord record's own
  `CauseOfLoss`**: it decides Broad vs Special. CT does not price Group I. KS
  and NY price Broad and Special on a Standard Property Policy; VT Broad only.
* **Watercraft buyback** needs waterfront "Yes" (spelled `WaterFrontProperty`
  on Special Class BI), the Special cause, no CP 10 35, and a construction
  option other than "Not Applicable". Business Income creates the record on
  every policy.
* **Off-Premises is its own small rating plan:** loss cost × extended period ×
  waiting period × insurance-to-exposure (Option B) × EQ / flood / wind-hail
  factors (OTC only) × limit ÷ 100. **Send an extended period**: blank prices
  $0. AK drops insurance-to-exposure, AR DC NY RI drop wind-hail, and FL
  switches it off on residential classes.
* **They feed the policy total and five stat-code fields; terrorism does not
  read them.**

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-103** | Two more cases where ISO refuses and we price: Watercraft option "Not Applicable" (`WatercraftExclBuybackFactor` has no row), and FL's EQ building-height table for chunk 10's EQ inputs (`BldgHeightFactor`) | no; engine behaviour decision (chunk 28) |
| Flood factor untested | Off-Premises OTC's flood factor (1.02) needs the flood endorsement, which is chunk 25 | no; chunk 25 |
| Process gap found | Long passes gave no progress, and 177_'s `pkgs()` re-discovered the whole ERC corpus on every call (2.5 min a policy, 98% discovery). The check that was missing: every pass prints `[i/n elapsed]` to a log under `results/cf-raas/logs/`, and a profile of one unit runs before any sweep. Now in 183_ / 184_; `book_for` is cached in 180_ / 182_ / 183_ | no |

## Confirmation

* **Regression CLEAN for chunks 0–17**, 2026-09-28: 115 of 115 scripts, the General Liability suites included, 0 failures (`104_chunk10_c10-21_regression.py --jobs 4`, with `181_` pinned to $77 / $982 / $343 / $253 / $13 / $63 and `180_`, `182_`–`184_` added). Claude Code stopped the run twice for low system memory, not a test failure: 111 of 115 passed in the first run, and the 4 left passed in a second run (`regression_chunks0-17.log`, `…_rest.log`). The runner now runs 4 scripts at a time and has a quick tier (`--quick`) for use after each RC
* **`157_ --all`**: all 293 of 293 stored ISO policies, 14,236 premiums and every policy total equal (10m21s, `chunk17_157_all.log`)
