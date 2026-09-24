# Property chunk 13: the gate

**Terrorism / TRIA, on all five coverage groups, in all 46 states.** Filed
2026-09-24. **9 of 9, and all 30 tasks done.** Task record:
[`CF-CHUNK13-TASKS.md`](CF-CHUNK13-TASKS.md).

**In plain English.** Terrorism isn't a coverage of its own. It's an extra
premium on every coverage the policy has (building, contents, business income,
special class and its business income), backed by a federal program, TRIA, that
has an expiry date. Each coverage works out its own terrorism premium from a
loss cost its state files by territory, the exclusion or limitation forms the
policy carries, and the share of the year before and after TRIA expires. A
policy-level "disclosure" record then adds those premiums up, and in six states
caps the total at 25% of the rest of the policy.

Every step was derived by hand from the filed rows before it ran, and every
answer the engine gives was checked against ISO's live service. **ISO agreed on
every terrorism figure it rated**: 587 of 587 live responses, 294 of them ISO's
own example payloads. On the way, the chunk found
and (with the user's authorization) fixed **one engine defect, OI-111**: a
"go up to the record called X" path went to the top of the document instead,
which priced California's capped terrorism at $0 against ISO's $153.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `149_chunk13_golden_case.py`: chunk 2's Oregon building, Multnomah County, **$8**, derived by hand; plus the Oregon fire exception ($1, $8 where the CW rule gives $0) and TRIA proration ($9, $58). 38 of 38 figures; **ISO 5 of 5** field for field. `150_…`: contents $8, business income $5, special class $8, SCBI $5, and every roll-up record ($34 / $37 / $24 / $38 / $5); 53 figures; **ISO 9 of 9** |
| 2 | Every table's row count stated | ✅ | `152_…` C13-16. Six tables: `TerrorismTerritoryTier`, `TerrorismLossCost`, `TerrorismNBCExclFactor`, `TerrorismSubLimitFactor` are header-only countrywide and filed by the states (46, 46, 44, 44); `TerrorismFireExcptnFactor` by 17 states; two single-row stat-code tables. Gaps: FL (program year 3 only; no NBC or sub-limit rows), NY (no NBC or sub-limit rows), each routed around by the state's own rules |
| 3 | Every state is enumerated | ✅ | `152_…` C13-22: **all 46 states, every territory tier (106), 290 cases, CLEAN** against each state's own rows and rules. `153_…` C13-19/20: every form choice in the 12 states that rewrite terrorism, **ISO 145 of 145**. Puerto Rico excluded by standing rule |
| 4 | Every `0` tested against its consuming branch | ✅ | `151_…` C13-13 and the $0 edges of C13-10 to C13-12: TRIAType blank; certified-acts answer blank; no territory; post-TRIA with no exclusion answer; sub-limit under 5% or above the limit; no sub-limit entered; override with no premium. **ISO agrees on every one**; an unfiled territory is refused at ISO and $0 here (OI-103) |
| 5 | Every hardcoded literal key listed | ✅ | `151_…` C13-15: every constant compared against `TRIAType`, `CoverageForCertifiedActs`, `PostTRIAExclusion`, `TRIAConditionalExclusion`, `ConditionalExclusionRatingOption` and `TerrorismTerritory` is in the Domain Tables; none off-domain |
| 6 | Shared-name traps diffed | ✅ | `154_…` C13-25: every terrorism field on every record, **12,251 values across 293 stored ISO responses, all equal to ISO**, including the 26 field names carried on more than one record type (`CoverageStatCode`, `PostTRIAExclFactor`, `TerrorismSubLimitPct` …). Form names and numbers set aside (OI-106) |
| 7 | Every exclusion's endorsement record identified | ✅ | C13-26: 17 terrorism record types; the 13 forms and PostTRIA are **policy-level**, and every coverage group reads them at exactly the depth that reaches the policy (building and special class `../`×4, BI and SCBI ×6, contents ×8); the 3 `…Detail` records are inert. No coverage files its own terrorism exclusion. Attach and removal: `148_…` C13-05, 168 answer combinations × 2 |
| 8 | The edition basis stated | ✅ | C13-22: four parents in force (2026 V01 for 37 states; 2023 V04 for FL, IL, MA, NJ, RI, VT; V03 for CA, NC; V02 for MO). They differ only by three inert `…Detail` files; the sweep ran every one clean |
| 9 | No unexplained validation message | ✅ | `154_…` C13-27: **293 of 293 stored ISO responses carry an identical message set**, and 289 of 294 rated ISO fixtures (C13-23); the other 5 are one deductible-form message on older editions, not terrorism, with every premium equal to ISO. **Its cause is not yet traced**, so it is logged as **OI-112** rather than claimed as explained; every terrorism message matches ISO |

## Engine changes (user-authorized, confirmed against ISO)

| | Defect | Fix | Evidence |
|---|---|---|---|
| **OI-111** | `ancestor::Name` resolved to the document root; CF names real records with it (30,512 paths) | nearest ancestor-or-self tagged Name, the root only if none (GL unchanged by construction) | CA's 25% cap: $0 → **$153**, = ISO; replay 14 of 14; regression clean for chunks 0–12 and all GL suites; `145_…` pins it |

## What the chunk established, in submission terms

* **`TRIAType` drives everything.** Blank, and no terrorism form attaches;
  submitted forms are removed without a message. **`TerrorismIndicator`
  switches nothing off**, at ISO as here ("No" is still charged).
* **Each coverage prices its own terrorism; the policy is charged the roll-up.**
  In CA, DC, IL, MD, NY and VA the roll-up is capped at 25% of the rest of the
  policy, so the coverage premiums and the policy charge differ.
* **A terrorism sub-limit above the building's limit prices terrorism at $0**
  (the factor applies only between 5% and 100%). Business Income ignores the
  sub-limit altogether.
* **One day left before TRIA expiry counts as expired** (1/365 rounds to 0.00),
  so the whole premium is charged at the post-TRIA rate. ISO does the same.
* **The override replaces the rating, per coverage, and is itself prorated.**
* **State behaviour**: Oregon's fire exception applies to IL 09 53 in 12
  states; CT, MA and VA keep it off IL 09 53; AZ applies it only to residential
  property under four units; FL and NY never charge post-TRIA; FL charges only
  IL 09 52.
* **ISO wants `TerrorismSubLimit`, `TerrorOverridePremium` and
  `BasicGroupIRatingTerrFactor` as JSON numbers**, and refuses a blank
  `WindstormOrHailDeductible` on contents and an out-of-state building
  territory (both OI-103 shape).

## Backlog: not blocking this gate

| Item | What it is |
|---|---|
| **OI-103** | ISO refuses a lookup with no row where we price: here an unfiled terrorism territory, an out-of-state building territory, a blank windstorm deductible |
| **OI-112** | On older-edition states ISO clears three cause-of-loss answers on the multiple-deductible form and fires a message we don't (5 fixtures); message only, all 177 premiums equal ISO |
| **OI-106** | Form names and numbers read "Value Not Found" (912 values here); no premium impact |
| **Building inputs** | CO/IN/OK need a wind-hazard county and SC a BCEG-EQ grade before ISO rates the portable building there; not terrorism |
| **No EffDate** | Our engine refuses at `DateAdd`; ISO always has an effective date, so it can't be compared |
| **OI-111 edge** | The "-or-self" case (a rule running on the policy that names the policy) is the reading ISO confirmed here, but no case exercises it directly |

**Regression** (C13-29): `104_chunk10_c10-21_regression.py` now covers **chunks 0–13**.
**Close-out run 2026-09-24: CLEAN, 73 of 73 scripts** (every golden case at its documented
figures, every machinery script, all 16 GL suites). A first run failed 3, all explained and
fixed: `145_` (my harness) and chunk 6's `45_` / chunk 11's `120_`, which pinned Florida's
old V01 package; the user added V02 (the edition ISO rates on) the same day, and both were
re-derived from the V02 files.
