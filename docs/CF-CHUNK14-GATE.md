# Property chunk 14: the gate

**Policy assembly: the policy total, the policy-level modifiers, statistical
coding, in all 46 states.** Filed 2026-09-24. **9 of 9, and all 22 tasks done.**
Task record: [`CF-CHUNK14-TASKS.md`](CF-CHUNK14-TASKS.md).

**In plain English.** Chunks 1 to 13 priced each coverage. Chunk 14 is the top of
the policy. It adds those premiums into one policy total. It applies the
policy-wide adjustments: the underwriter's schedule credit or debit (IRPM), the
package discount, the multi-premium credit, and the Standard Property Policy's
cheaper, narrower form. And it checks the statistical codes ISO stamps on every
record for the insurer's loss statistics.

Every figure was worked out by hand from the filed rows before it ran, and every
answer was then checked against ISO's live service. **ISO agreed on everything it
rated:**
- all 14,236 premiums and 293 of 293 policy totals in its own example policies;
- all 12,547 statistical codes, compared exactly as text;
- 4,869 modifier values;
- about 150 live policies built for this chunk.

**No engine change was needed.** The chunk did find where ISO refuses a policy that
our engine prices. There are four such places, all logged as OI-103 and pinned as
tests.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `159_chunk14_rc2_total.py`: chunk 7's five-coverage policy plus terrorism and Debris Removal, total **$1,193** derived by hand, plus 8 variants (a negative premium, an override, an uncovered building, two locations, two buildings, and a rounding case where ISO adds whole-dollar premiums: **$586, not $587**). **ISO 9 of 9** field for field |
| 2 | Every table's row count stated | ✅ | Countrywide, the same in every parent edition: `IRPMConversion` 201 (−100% … +100%, one-to-one); `IRPMMaximumDebit` / `Credit` 1 each (±25); `StdPropPolGroupI` / `IIFactor` 1 each (0.98); `TotalRatingModicationStatCode` **199 (keys 1–199 only)**; `MinimumPremium` / `PolMinPremium` **0** (no minimum premium; C14-03). State-filed: NY ±15, MO credit −35; NE files an empty conversion table and empty limits; KS / NY / VT file empty SPP tables. Stat codes: 46 CW tables, 22 state-filed (C14-15) |
| 3 | Every state is enumerated | ✅ | `164_chunk14_c14-18_all_states.py`: **all 46 states**, IRPM at +30 and a Standard Property Policy, each predicted from that state's own rows and rules: engine **92 of 92**, **ISO 92 of 92** (every premium, every stat code, every message). The total in every state: `157_ --all`, 293 of 293. Puerto Rico excluded by standing rule |
| 4 | Every `0` tested against its consuming branch | ✅ | `163_chunk14_c14-19_zero_cases.py`, 11 cases, ISO 11 of 11 as expected. **A "0" means two different things.** A package modification of 0 or a supplied IRPM factor of 0 is kept. A multi-premium user factor of 0 or a CPP IRPM factor of 0 counts as "not given" and becomes 1.0. Blanks default to 1.0; a vacant building ignores the policy's package factor. **ISO refuses a combined modifier of 0 or of 2.00 and above** (the stat-code table's 1–199 bound, predicted and confirmed; 1.988 → code 199 rates) |
| 5 | Every hardcoded literal key listed | ✅ | Every constant compared against `PolicyType`, `VacantBuilding`, `MultiLocAvgRates` and the IRPM category fields is on its Domain Table. `IRPMApplies` compares to "Yes", on its declared common `YesNo` domain (not shipped as a file). **The IRPM categories have narrow domains** (Management ±8, Location ±7, Building Features ±5, Premises ±5, Employees ±3, Protection ±2: at their limits they sum to exactly ±30; NY's twelve also sum to 30; MO's expense reduction runs 0 to −10). The first RC-3 cases used off-domain values; ISO rated them and only the sum matters, but every case was rewritten in-domain and re-run: **ISO 23 of 23 and 92 of 92 again** |
| 6 | Shared-name traps diffed | ✅ | `165_…`: the modifiers are shared names across 5 record types (`MultiPremiumAndDispersionCreditFactor` on policy, structure, contents, business income, special class; `PackageModFactor` policy and structure; `StdPropPolGroupI/IIFactor` on three). **4,869 values by path, 293 of 293 equal to ISO.** `Premium` on every record type: `157_ --all`, **14,236 of 14,236**. Stat fields on 51 names: `161_ --all`, **12,547 of 12,547**, strict |
| 7 | Every exclusion's endorsement record identified | ✅ | C14-01 / C14-04: the total sums **45 record types**; all 41 state overrides of the total only add state records (state forms, KY/IL mine subsidence, AK terrorism forms) with no arithmetic of their own, and all 43 overrides of the Erc wrapper are pass-throughs. The additional-location reset belongs to the Additional Locations Special Coinsurance endorsement, **not built** (coverage inventory) |
| 8 | The edition basis stated | ✅ | Four countrywide parents are in force (2026 V01 for 37 states; 2023 V04, V03, V02). The modifier and stat-code tables are identical in all four. The sweep covered states on every parent (MO on V02, CA/NC on V03, FL/IL/MA/NJ/RI/VT on V04). MO's own package is 2025-11-01 over CW 2023 V02 |
| 9 | No unexplained validation message | ✅ | Every message in the 92 state cases equals ISO's; the IRPM and Standard Property Policy messages are pinned in `160_` (ISO 23 of 23, messages compared). The 293 stored responses carry identical message sets (`154_`, C13-27, in the regression). **OI-112** stays open (an older-edition deductible-form message, no premium effect) |

## What the chunk established, in submission terms

* **The total adds whole-dollar premiums**, negatives included. ISO applies **no
  minimum premium**; per the user's decision, a minimum is a company input with
  a "refer to company" outcome (OI-113, backlog).
* **A supplied factor always wins.** IRPM, package modification and the
  multi-premium credit are computed only when blank.
* **IRPM's cap and its warning are separate rules**, and states change them
  independently:
  - **NY:** ±15 on its own twelve categories, plus a second warning that adds a
    percentage to a factor.
  - **MO:** a −35 credit limit and a seventh category, whose blank answer ISO
    refuses.
  - **GA:** caps at 25 but warns at 15.
  - **VA:** no warning.
  - **NE:** IRPM off.
* **The Standard Property Policy's 0.98** is applied in the rate chain, not to
  the premium. Its eligibility rules only raise messages. **KS, NY and VT don't
  offer it**, and a Standard Property Policy there prices like a normal one.
* **The combined modifier has to be between 0.01 and 1.99**, or ISO refuses the
  policy on its statistical code.
* **Statistical codes are exact text.** A state's own row comes first, then the
  countrywide row. FL's earthquake classes are its own. TX's "97" deductible codes
  can't be reached, because no premium factor exists for those percentages.
* **Building inputs some states require:** CO and IN need a county for wind
  hazard, OK needs "Entire State", and SC needs an earthquake territory (it prices
  every SC building). Without them ISO refuses.

## Backlog: not blocking this gate

| Item | What it is |
|---|---|
| **OI-103** | ISO refuses a lookup with no row where we price. This chunk adds four cases: MO IRPM with a blank expense category; a combined modifier of 0 or of 2.00+; TX earthquake deductibles off the 5% grid |
| **OI-113** | Minimum premium: a company input, refer to company; the Property engine has no referral layer yet |
| **OI-112** | An older-edition deductible-form message, no premium effect; cause not traced |
| **OI-106** | Form names and numbers read "Value Not Found"; no premium impact |
| **Unbuilt coverages** | Value reporting form (multi-location average rates, peril-exclusion stat codes), Additional Locations Special Coinsurance, Off-Premises Interruption, MA heating-oil remediation and tenant relocation, Condominium Unit-Owners Optional Coverages. Their stat codes and totals come with them |

**Regression** (C14-21): `104_chunk10_c10-21_regression.py` now covers **chunks
0–14**, with `157_` to `165_` added. The full-population replays (`157_ --all`,
`161_ --all`, `165_ --all`) ran clean on 2026-09-24 and are run at every chunk
close-out and edition change.
