# Property chunk 19: the gate

**The scheduled property items: Tenants' Building Property / Glass, Radio or Television
Antennas, Outdoor Trees Shrubs and Plants, Outside Signs, Brands and Labels, Household
Personal Property, Leased Property, Specified Property Temporarily Away and Manufacturers
Consequential Loss, in all 46 states.** Filed 2026-09-29. **9 of 9, and all 24 tasks done.**
Task record: [`CF-CHUNK19-TASKS.md`](CF-CHUNK19-TASKS.md).

**In plain English.** Each of these puts one specific thing on the policy with its own
limit: a tenant's glass or improvements, a broadcast tower, the landscaping, an outdoor
sign, the cost of removing brands from salvage, a household's contents, leased equipment,
goods temporarily away, or stock made worthless by a damaged matching part. **57 of the 63
countrywide premium records had never been priced by ISO**, nor had Florida's five own
glass records. Only six unscheduled tenants' records matched a stored ISO policy.

Every figure was worked out by hand before it ran, from the family's own filed table and
rule, and then checked against ISO live. **ISO agreed on everything it rated:**
- 16 golden cases across all nine families, every premium on each policy compared;
- 11 zero cases, 16 message cases (all 21 messages), 6 submitted-value probes and 6 exclusion cases;
- the earthquake sub-limit tier layer (8 of 9; the ninth is an ISO refusal, below);
- the state rewrites, Florida's own glass files, Montana's premium-less ones, the Public Institutional Plan: 15 of 15;
- every edition (Missouri's 2023 V02 differs in 4 files) and **all 46 states: 49 of 49 policies, 3,098 records, 10,317 premiums**;
- the downstream check: the total moves by exactly the predicted amount ($1,941; clean test $14,054, predicted before the call); no terrorism effect; 336 stat values equal.

**No engine change.** Four things the rules do that a submitter must know, each found by
running and confirmed by ISO:
- **Household Personal Property lowers the contents' own premium.** Its limit is added to
  the occupancy's total amount of insurance, on which the contents' limit factors are
  looked up ($197 → $192 at 15,000).
- **The contents need their own earthquake election** (their own `EQGrade` and earthquake
  endorsement record) for Brands, Household, Leased and Temporarily Away to price earthquake;
  **Temporarily Away earthquake needs sprinkler-leakage-only "No" or "Yes"** ("Not
  Applicable" prices $0, no message).
- **A blank tenants' deductible prices $0 with no message.**
- **Signs price on (limit − $2,500) on every form**: a sign under $2,500 prices negative.

**One open question, recorded, not fixed:** Vermont files an earthquake tier table with no
rows. ISO refuses the policy, while our engine falls back to the countrywide row and prices
$0. Yet ISO *did* fall back for Vermont's empty vacancy table in chunk 18, through a
structurally identical lookup in the same package. Written into
[`CF-ENGINE-FIX-EMPTY-STATE-TABLES.md`](CF-ENGINE-FIX-EMPTY-STATE-TABLES.md) for chunk 28.

**Countrywide premium files built: 469 of 546 (86%)**, up from 406.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `192_chunk19_rc2.py --live`, 16 cases on 175_'s Oregon policy. **Tenants'** (T1 / T2): the glass deductible decides the dollar: no deductible 1.10 / 1.15 → glass BGI **$122**; $250 → 1.05 → **$116** (the EQ form reads the Broad row); scheduled items priced one by one. **Antennas** (A1): Group I 0.07 for both tower types, so only Group II (AB 0.024 / B 0.028 × symbol 8) tells them apart. **Trees** (TR1-3): Vermont's vehicle factor 1.15 moves Group II **$55 → $64**. **Signs** (S1 / S2): detached signs use their own rate (metal 0.513 / other 1.188 → **$193**) and symbol (4 / 8); attached ones copy the building's rates. **Brands** (B1 / B2): min(0.053 cap, 0.10 × the contents' rate): the cap binds at **$47** (uncapped $62). **Household** (H1): the residential contents rate. **Leased** (L1): **$392**; its Agreed Value equals ISO's stored chunk 18 A4 response. **Temporarily Away** (TA1 / 2): theft covered **$24** vs excluded $5. **Manufacturers** (M1 / 2): Stock 1.25 vs 1.15. ISO agrees on all 16. Pinned in the regression |
| 2 | Every table's row count stated | ✅ | C19-05 (`191_`): every table the family files read, CW and each state's own, header-only ones named, unread state tables listed (FL `EQSubLimitToSubLimitPercentage` 14 rows, FL non-residential contents rate 12). Key rows: Brands 1.10 / cap 0.053, Manufacturers Stock 1.25 / others 1.15 / Not Applicable 1.00, Temporarily Away 0.1 (theft covered 0.2), `Deductible250Factor` 1.05 / 1.10, glass no-deductible 1.10 / 1.15, vehicle factor **1.00 CW, 1.15 CT ME MA NH RI VT**, 15 flat-deductible tables (912–1,140 rows), tier tables (323 / 304) |
| 3 | Every state is enumerated | ✅ | `196_ --all --live`: **all 46 states**, every family on each state's own package and rule (148 records on a state's rewritten rule), + the Public Institutional Plan in AL KS RI: **ISO 49 of 49**, 10,317 premiums. FL switches off all 20 countrywide tenants' and 5 Temporarily Away records and prices glass through its own five files ($76 / $11 / $11); MT's same-named files price nothing; NY prices antennas' and trees' Group II from its own territory tables (so its empty symbol tables are never read). Puerto Rico excluded by standing rule; FL and CA earthquake out of scope, as in chunks 16–18 |
| 4 | Every `0` tested against its consuming branch | ✅ | C19-13 (`193_`, Z1–Z11 + R1), ISO agrees on all it rated: blank tenants' deductibles → **$0, no message**; glass limit 0 → glass $0; EQ "Yes" without the building's earthquake → $0; an antenna with no limit → that tower $0; trees limit 0 → $0; **a sign at 2,000 → negative** (every form subtracts 2,500); Brands on a contents limit of 0 → $0; Temporarily Away EQ on "Not Applicable" → $0; Manufacturers on "Not Applicable" → $0 with the type message; Household on Broad → Special off; Leased limit 0 → $0 |
| 5 | Every hardcoded literal key listed | ✅ | C19-05: the tenants' `CovType` strings, "Not Applicable" / "250" deductibles, antenna types and heights, sign "Attached" / "Detached" and "Entirely Metal" / "Other", the vandalism / sprinkler cause strings, "Blanket Cause of Loss Applies", the EQ "Yes, Included / Not Included in Blanket" pair, the habitational class list, "All Personal Property", "Stock", "Valuable Papers and Records - Other Than Electronic Data"; per-edition special-class option codes (C19-19) |
| 6 | Shared-name traps diffed | ✅ | C19-04 (hand = engine on 233 nodes, all 63 records) and C19-15 (`194_`): every rate, factor and coinsurance factor a family writes is `IsNull`-guarded (a submitted value is used: four probes); the Group II symbol number and every on-switch are overwritten (two probes). **The contents' class code is copied down from the building** (a class entered lower is overwritten); **AL / RI read the plan flag on the occupancy**. ISO agrees on every probe |
| 7 | Every exclusion's endorsement record identified | ✅ | C19-16 (`194_`): the cyber-incident exclusion on all 63 records at 10× limits (23 move a dollar; ISO 210 of 210); the building's **vandalism** exclusion moves Group I only (trees $978 → $929 through their own factor); **windstorm** collapses Group II to the lowest rate × symbol 1 × 0.315 (trees $520 → $22); earthquake sprinkler-leakage-only moves the tenants' EQ forms $5 → $1; the trees' vehicle exclusion is an input (C19-08) |
| 8 | The edition basis stated | ✅ | C19-19 (`197_`): **every rule** of every family file diffed across the four editions: **4 files differ in CW 2023 V02 (MO)**, the special-class rate looked up under older option codes (antennas 62, signs 12 / 13, trees 42; same rates; V02 has no rows under the 2026 codes, so the probe discriminates). MO / NC / MA agree live; FL RI VT (V04) in C19-18 |
| 9 | No unexplained validation message | ✅ | C19-14 (`193_`, 16 cases): **all 21 messages** triggered, and silent where rated; ISO's message set equals ours on every case. One Legal Liability policy fires six at once; **"Minimum 80% Coinsurance in Blanket" fires on an unblanketed 80% contents row** (its test; ISO too); the trees' per-item message fires whenever no per-item limit is entered |

## What the chunk established, in submission terms

* **Tenants'** is a container on the building: scheduled (glass on the container's own
  `Limit`, each item its own `Limit`) or unscheduled (both limits on the container);
  `CovType` switches glass / other than glass; its **own** `CausesOfLoss` picks Broad vs
  Special; earthquake needs its `EQCovIndicator` **and** the building's election. **Enter
  both deductibles**: blank prices $0.
* **Antennas and Signs** price on the special-class chain. A sign's placement decides the
  regime (attached copies the building's rates); **every sign form subtracts $2,500 from the
  limit**. Their earthquake sub-limit (CP 10 45 / 10 29, set on the **location's** EQ form)
  uses the state's own tier tables, interpolated by sub-limit %; a tier a state does not
  file prices $0.
* **Trees'** vehicle factor applies only with `VehExcl` "No" and only moves money in New England.
* **The contents-side families** read the contents' rates: **give the contents their own
  earthquake election**; Manufacturers keys on the contents type (and is off in a blanket);
  Brands is capped at 0.053; Household adds its limit to the occupancy total.
* **They feed the policy total and the construction / exposure stat codes; terrorism does not
  read them.**

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **Empty-table fallback** | VT's header-only EQ tier stub: ISO refuses, we price $0, though ISO fell back for VT's empty vacancy table (chunk 18). Recorded in `CF-ENGINE-FIX-EMPTY-STATE-TABLES.md` | no; chunk 28 decision |
| **OI-103** | More ISO-refuses / we-price cases: Manufacturers on a contents type with no factor row; the portable policy's detail Group II base rate outside OR; the flat EQ form's stat code with a coverage left on a % deductible; FL's special-class description and FL's own EQ class ("5C") | no; chunk 28 |
| FL / CA earthquake | Their own EQ class schemes: untested, as in chunks 16–18 | no; with chunk 10's state EQ |
| Process gaps found | (1) The census compared only `SetPremium` per edition; the missing check was a rule-by-rule diff of every family file (now in `197_`). (2) `174_`'s hand evaluator ignored `DecimalPlaces` on `Divide` / `Subtract` (fixed; the regression re-checked every script that uses it). (3) Status-page progress labels drifted from their own rows in 14 places (recounted; the recount now runs with every status update) | no |

## Confirmation

* **Regression CLEAN**, 2026-09-29, scoped with your go: **23 of 23, 0 failures** (`104_ --only … --no-gl --jobs 2`, 40m04s, `chunk19_c19-22_regression_scoped.log`): the 8 chunk 19 scripts (`192_` pinned to $122 / $116 / $193 / $64 / $47 / $392 / $24; `191_`, `193_`–`198_` added) and **all 15 registered scripts that use `174_`'s hand evaluator** (chunks 16–18, found by following the imports), which the Divide / Subtract rounding fix touched. The full run is carried from 2026-09-28 (115 of 115) and chunk 18's scoped run: **no engine code has changed since** (`ae81ac7`); the only shared change is that test tool, and every script that uses it was re-run
* **`157_ --all`**: carried from 2026-09-28 (293 of 293), run after the last engine change; not rerun: no engine change since
* **`166_`**: 469 of 546 countrywide premium files built (86%), 77 left in 16 families
