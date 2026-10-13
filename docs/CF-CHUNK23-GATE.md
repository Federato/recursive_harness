# Property chunk 23: the gate

**State-only coverages: MA heating-oil remediation (with its Pollutant Clean Up credit) and tenant relocation, AK
Changes: Attorneys' Fees, CA Limited and Additional Earthquake, and VA's two Ordinance or Law state forms.**
Filed 2026-10-01. **9 of 9, and all 22 tasks done.** Task record: [`CF-CHUNK23-TASKS.md`](CF-CHUNK23-TASKS.md).

**In plain English.** These coverages exist in one state's filing and nowhere else: 10 premium files in MA, AK and
CA, plus VA's 41 Ordinance or Law files that chunk 12 counted but never priced. **None had ever been priced by ISO**,
so every case was a new live probe. The chunk also closed the list of every state-only premium file in force (80,
each with an owning chunk); only WV's two flood files remain, for chunk 25.

Every figure was worked out by hand before it ran, from each state's own filed rules and tables (219_'s hand models,
174_'s independent SetPremium evaluator, and the engine all agreeing first), then checked against ISO live.
**ISO agreed on every case, on every premium and every (level, message).** No engine change was needed.

The counts: RC-1 (`219_`, no ISO); RC-2 12 golden cases (`220_`), 1,727 premiums; RC-3 43 zero / message /
shared-name / exclusion cases (`221_`); RC-4 four fuller state policies plus three old-package probes (`222_`);
RC-5 eight before / after pairs, 16 ISO calls (`223_`).

**Things the rules do that a submitter must know**, each found by running and confirmed by ISO:
- **AK's fees attach only on Legal Liability** (building `CovType` "Legal Liability"; the occupancy's Legal Liability
  form record), **and the policy fee only with a Mortgageholders E&O record**; otherwise the rules remove them. The fee
  limits **below** the coverage limits price **negative** fees, as written, with all three messages.
- **MA's Pollutant Clean Up credit is its own negative record**, switched on only by a heating-oil remediation record
  at the same location, capped (-$17 at the cap, -$9 under it). Tenant relocation is capped **per unit**.
- **A blanketed Limited EQ building is unreachable**: blanket EQ values need an EQ endorsement record, which Limited
  EQ excludes; it prices $0 and ISO raises "Blanket ID number entered contains no EQ blanket coverage".
- **CA Additional EQ is company-entered**, rounded half-up through the modifiers (1,234.5 -> $1,235).
- **A blank VA `CovType` switches the broad form's Cov A on but the tenants' Cov A off.** The broad form reads the
  cyber factor; the tenants' form does not.
- `PersPropertyIncludedInBlanket` is recomputed by the countrywide CP 04 26 rule, so a submitted "Yes" does not
  survive; the other submitted values tested (VA `Factor`, `PostLossFactor`, AK `LimitToUse`, MA base loss cost,
  credit, base premium) do.
- Payload typing: the Mortgageholders limit is text ("25,000"); the families' numeric fields are numbers; a blank
  number is left out.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `220_chunk23_rc2.py --live`, 12 cases, **ISO 12 of 12**, 1,727 premiums, every message: MA remediation $241 / $67, credit -$17 / -$9, relocation $16 / $30 (H1-H3, R1-R2); AK fees $12 / $8 / $11, 74,999 -> $1 (ISO truncates the per-mortgage ratio) (K1-K2); CA Limited EQ $80 / $24 / $21, Additional EQ $1,235, blanketed Limited EQ unreachable as predicted (C1-C2); all 41 VA records on three CovTypes and three causes beside the countrywide form, e.g. broad form Cov B $591 / C $886 (V1-V3). **Closes chunk 12's open "VA priced case"** |
| 2 | Every table's row count stated | ✅ | C23-05 (`219_`): MA 8 one-row state tables; AK 2 one-row + `MortgageholdersLimitOfInsPerMortgAmount` 17 rows; CA reads no rate table; **VA files none and reads 9 countrywide one-row tables** (Cov A 1.15, EQ 1.85, post-loss 1.02, six coverage indicators). No family lookup is banded |
| 3 | Every state is enumerated | ✅ | Each family exists in one state, and that state's in-force package is the one rated (C23-06). The list itself: **all 46 in-force packages enumerated** (`904_`, re-run at C23-17): 80 state-only premium files, none unassigned (chunks 12 41, 15 6, 16 9, 19 5, 20 2, 21 5, 23 10, 25 2); `166_` now marks each closed except WV's two flood files (chunk 25) |
| 4 | Every `0` tested against its consuming branch | ✅ | C23-12 (`221_` Z1-Z10, all agree): MA no tanks = base only; the credit with no remediation $0 + the CP 04 44 message; 0 units $0; AK fee limits 0 $0 and **below the coverage limits negative**; CA earthquake off removes the Limited EQ records; Additional EQ 0 $0; VA blank B / C limits $0; pollutant 0 off; blank `CovType` (broad Cov A on, tenants' off) |
| 5 | Every hardcoded literal key listed | ✅ | C23-05: every literal key the rules pass ("Y" constants, the coverage indicators, "Legal Liability", "Yes" / "No" switches, VA's `CovType` values A / B / C / B&C) has a row or a domain value in its state |
| 6 | Shared-name traps diffed | ✅ | C23-14 (S1-S6, MV7b, agree): `Factor`, `LimitToUse`, `ManualPremium`, `PostLossFactor`, the `TotalPremium…CauseOfLossToUse` totals and the containers' totals diffed; six submitted values survive (IsNull guards); **`PersPropertyIncludedInBlanket` is overwritten** by the countrywide CP 04 26 rule |
| 7 | Every exclusion's endorsement record identified | ✅ | C23-15 (X1-X5, agree): the cyber exclusion moves VA's broad form (Cov B $5,876 at 2,000,000) and **not its tenants' form**; CA's Limited EQ unchanged (EQ cyber factor 1.00); AK's and MA's records read none |
| 8 | The edition basis stated | ✅ | C23-06 + C23-18: in force at 2026-09-17 MA 2026-03-01 V02, AK 2026-06-01 V01, CA 2025-12-01 V01, VA 2026-06-01 V01; later MA / AK packages change no family rule; **CA's later packages fix a typo in a redundant clause: no dollar**. Older packages probed at ISO: MA 2022's relocation prices nothing; **AK 2020 and VA 2021 DO price, inside `ErcRate`** (the census's SetPremium-only test was corrected; `check_premium_census.py` now guards it). **OI-120**: pre-2022-10 policies do not rate in our engine (old editions only) |
| 9 | No unexplained validation message | ✅ | C23-13 (`221_` MS, MC1-MC9, MV1-MV8): **30 of the chunk's own message rules fired at their own level** (MA 2, AK 3, CA 15, VA 10) and each was checked silent where it should be. Not fired: VA's two "80% in Blanket" rules. VA's 10 countrywide twins are covered by the multiset on the CP 04 05 / 04 26 cases and chunk 12. **ISO's (level, message) multiset equals ours on every case** |

## What the chunk established, in submission terms

* **MA**: a `RemediationForReleaseOfHeatingOil` record under the building (`NumberOfTanks`,
  `TanksServingAdditionalBuildings`, `AdditionalBuildings`); the location credit record is attached by the rules and
  priced only when a building at that location has remediation and the Pollutant Clean Up record says "Yes";
  `MassachusettsTenantRelocationExpense` under the building (`NumberOfUnits`).
* **AK**: fee records under the building, the contents and the policy (`Limit`), on Legal Liability only; the policy
  fee needs a Mortgageholders E&O record.
* **CA**: the location's `EQCauseOfLossForm` "Limited Earthquake Endorsement (CP 10 43)" and a Limited EQ record per
  building / contents / BI (`Limit`); Additional EQ is a company-entered `ManualPremium`.
* **VA**: the broad form and the tenants' form as containers under the building (`CovType`, the B / C / B&C limits,
  `PostLossOrdinanceOrLawOption`, `PollutantCleanupPremium`); their 41 coverage records are created by the rules.
* **Downstream** (C23-19, `223_`): with each family removed and restored, **the policy total moves by exactly the
  family's premiums** (leaves only; the MA credit as its own negative record): **+$192 / +$31 / +$806 / +$3,908** on
  the fuller policies and **+$234 / +$31 / +$1,360 / +$3,902** on the golden ones, predicted before each call and
  equal at ISO. **Nothing else moves**: every other premium, terrorism and the TRIA disclosure total identical. The
  records the rules attach on their own (AK fees, MA credit, CA Limited EQ) sit at $0 without their inputs. ISO
  returns no stat fields on these records except one on VA's broad form, equal to ours.
* **Gate checks** (C23-20, no engine change in the chunk): `206_ --check` **SNAPSHOT CLEAN** (1,321 stored requests,
  935,948 fields, nothing moved); `157_ --all` **293 of 293** premiums and totals equal to ISO; the chunk 23 scripts
  registered in `104_` (220_ pinned: 241, 67, -17, -9, 16, 30, 12, 8, 11, 80, 24, 21, 1235, 591, 886) and CLEAN, with
  `check_status_docs.py` and `check_premium_census.py`.
* **Census** (C23-21): **520 of 546** countrywide premium files built (no countrywide files in this chunk); the
  state-only list closed except chunk 25's two.

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-120** | Pre-2022-10 policies do not rate in our engine: the 2020 countrywide package has `<rul:Null/>` inside an `And` (ISO's build replaced an invalid path). ISO rates them. Fix sketch (not built, needs your go): treat a null `And` / `Or` operand as false, Property only, after a probe | no; old editions only |
| VA's "80% in Blanket" rules | Two VA message rules not fired in any case | no; message only |
