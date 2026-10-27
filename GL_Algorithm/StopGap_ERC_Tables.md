# Stop Gap - Employers Liability Coverage - Required ERC Tables

**Source ERC package:** state-filed Rule A2 -- no ISO subline code, no countrywide rating package
**Line:** General Liability (GL), state-only Additional Rule A2, filed in 5 monopolistic-fund
jurisdictions -- ND, OH, PR, WA, WY
**Derived from:** `StopGap_RatingAlgorithms.md`, reformatted from
`docs/gates/GATE-STOPGAP-EMPLOYERS-LIABILITY.md`
**Documented:** 2026-09-02
**Reconciled against the built engine:** 2026-10-02 (commit `630ba2f`) — every table re-read from the newest ≤ 2026 and 2027 package of each state, every lookup observed in offline engine runs (ND, OH, WY, PR at 2026-10-02 and 2027-04-01; WA at 2027-04-01), and `StopGapRate` row-counted in all 12 CW editions; corrections are marked **(engine)**.

This lists every ERC rate table named in GATE-STOPGAP-EMPLOYERS-LIABILITY.md, resolved by tracing
the classification-level `ErcRate` override chain (`SetStopGapIncrdLimitFactor` ->
`SetStopGapFactor` -> `SetStopGapFinalRate` -> `SetStopGapPremium`) and the policy-level
`SetPremium` aggregator, confirmed directly against the raw ERC package tree at
`C:\Projects\ISO_ERC_Files\General_Liability\{ND,OH,PR,WA,WY}\` -- **not** against the project's
precomputed knowledge base, which omits this coverage entirely (see "Verification" below).

**Every rate-bearing table on this coverage is state-only.** The countrywide layer carries a
header-only, 0-row `StopGapRate` table at every edition checked (20261001 V01, 20270401 V01,
20270401 V02) and nothing else -- there is no countrywide fallback for the factor lookup.
**(engine)** Now checked exhaustively: header-only in **all 12** CW editions on disk (20201201 V01
through 20270401 V02).

---

## Rate-build-up tables (state-only)

| Table | Used for | Keys |
|---|---|---|
| `StopGapRate` (via `LookupStopGapRate`) | Stop Gap rate factor -- 0.03 (Manufacturing/Processing, Contracting/Servicing) or 0.02 (Buildings/Premises, Mercantile, Miscellaneous) | `StateCode`, `ClassificationType` -- 5 rows per state, **5/5 of the named states populated, 0/51 countrywide**. **(engine)** Key spellings change at the 2027 filings: "Manufacturing or Processing" → "Manufacturing Or Processing", "Buildings or Premises - Office or Residential Occupancy or Leased to Others" → "Buildings Or Premises". WA (no 2027 package) keeps the old spelling. Engine hits in all five states |
| `ILFPremOps` (via `LookupILFPremOpsWithArgs`) | Increased Limits Factor, borrowed from Prem/Ops and called with Stop Gap's own submitted limits | ~~keys not resolved~~ **(engine)** State, `assignment` (the classification's `FinalPremOpsIncrdLimitTableAssignmentInt`; 3 in every run), each-occurrence = `LimitBodilyInjuryByAccident`, aggregate = `LimitBodilyInjuryByDiseaseAggregate`, both from `PolLvl[1]`, with the limit spelling as filed (`"500,000 BI"` ≤ 2026, `"500,000"` 2027). Engine at 500,000: ND 1.53 / 1.64 (2026 / 2027), OH 1.51 / 1.51, WY 1.56 / 1.56, PR 1.53 / 1.58, WA 1.56. **A miss writes null and prices Stop Gap at $0** |
| (Premises/Operations classification coverage, via `GeneralLiabilityClassificationPremOpsCoverage/BaseRate`) | Base rate multiplied by the Stop Gap factor | Not a lookup table -- an already-computed sibling-coverage value read directly off the same classification node (the E18 cross-coverage dependency) |
| (Premises/Operations exposure, via `PremOpsExposureCalc`) | Units of exposure multiplied by the Stop Gap final rate | Not a lookup table -- an already-computed sibling-coverage value, same classification node |

All state tables in this section follow the two-pass `FirstNonNull(state row, "CW" row)` pattern
used elsewhere in this corpus, but **the CW pass can never succeed here** -- `StopGapRate` is 0
rows countrywide at every edition checked, confirmed directly rather than assumed
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 5).

---

## Coinsurance / LOI / deductible tables

Not applicable to this coverage -- General Liability rating has no coinsurance or limit-of-
insurance concept, and Stop Gap carries no deductible mechanism of its own (it inherits nothing
comparable to drone's borrowed Prem/Ops deductible tables). The manual's only limit-shaped
mechanic is the two Bodily Injury limit fields that gate the algorithmic vs. refer-to-company
branch (see Premium-level tables, below).

---

## Premium-level tables

| Table | Used for | Notes |
|---|---|---|
| `DomainStopGapBIByAccidentOrByDisease` | Legal values for `LimitBodilyInjuryByAccident`, `LimitBodilyInjuryByDiseaseEachEmployee`, `LimitBodilyInjuryByDiseaseAggregate` | 13 whole-dollar bands, $25,000-$10,000,000 (ND); not re-checked for OH/WA/WY/PR -- **not resolved in source docs** whether the band set is identical across all five. **(engine)** The same 13 bands in WA 20260101 V02. Values carry a `" BI"` suffix ("500,000 BI") in ND 20261001 V01 and WA; the suffix is **dropped** in ND 20270401 V04 ("500,000"). Engine runs confirm OH/WY/PR follow the same split |
| `PackageModFactor`, `ExperienceRatingModificationFactor`, `ModToUse` | Premium-level multipliers in `SetStopGapFinalRate` (and `PackageModFactor` in Branch B) | ~~Not resolved~~ **(engine)** Policy-level values read with `FirstValue FromDataDef=../../../../<name>` off `GeneralLiability`; not rate tables. 1 in every engine run |
| `ManualPremium` | Submission-supplied premium used in the refer-to-company branch (limits differ) | **Not a lookup table at all** -- a plain input DataDef the submission must populate for Branch B to produce a non-zero premium. No ERC computation feeds it. **(engine)** ND, 1,000,000 vs 500,000 limits: ManualPremium 250 → Premium 250; absent → 0, with **no referral raised** |

---

## Statistical / subline tables

| Table | Used for | Keys |
|---|---|---|
| `StopGapStatCode` (via `LookupStopGapStatCode`) | Statistical reporting code per classification | `StateCode`, `ClassificationType` -- 5 rows in ND, mapping the same 5 classification types onto exactly 2 codes: `92400` (Manufacturing Or Processing, Contracting Or Servicing) and `92405` (the other three) |
| `StopGapManProcContServRiskStatCode` | Declared, unread | 0 rows in ND -- no rule reads this table (checked by name against the full `SetStopGap*`/`LookupStopGap*` rule set) |
| `StopGapRisksOtherThanManProcContServRiskStatCode` | Declared, unread | 0 rows in ND -- same as above |

Not resolved in source docs -- row counts for `StopGapStatCode` and the two orphan tables in
OH/WA/WY/PR; only ND was checked directly for this section. **(engine) Resolved:**
- `StopGapStatCode` has 5 rows in OH 20270401 V04, WA 20260101 V02, WY 20270401 V03 and PR 20270401 V04.
- The two orphan tables are 0 rows in OH and are **absent** (no CSV) in WA, WY and PR.
- All five states define and call `SetStopGapStatCode` → `LookupStopGapStatCode`; the engine writes 92400 for class 50017.

`StopGapStatCode` is the only stat table with rows.

---

## Not ERC tables

`PackageModFactor`, `ExperienceRatingModificationFactor`, and `ModToUse` are policy-level inputs
by their names and by analogy to the CF documentation's treatment of `IRPMFactor`/`PackageModFactor`
(confirmed via `rul:Copy`, not `rul:Lookup`, in the CF corpus). **That confirmation does not exist
for this GL coverage** -- neither this gate nor `GATE-370-UNMANNED-AIRCRAFT.md`, which names the
same four fields, states the ERC mechanism behind them. Flagged here as likely-not-ERC-tables by
analogy only.

`ManualPremium` is unambiguously not an ERC table -- it is a plain submission-level input field
consumed directly by the policy-level `SetPremium` rule's refer-to-company branch, with no lookup
or computation feeding it anywhere in the traced Stop Gap chain
(GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 2).

~~Not resolved in source docs -- confirm the ERC mechanism.~~ **(engine) Settled:** policy-level
`FirstValue` reads, not lookups. See Premium-level tables above.

---

## Verification

**This coverage was located entirely by reading the raw ERC package tree, not by trusting a
derived index.** The project's precomputed knowledge base
(`Agentic/iso-erc-expert/knowledge/jurisdictions.json`) lists `resolved_sublines` for ND, OH, PR,
WA, and WY, and **Stop Gap does not appear in any of the five lists.** That absence was checked
and traced to its cause rather than accepted at face value: the knowledge extraction's pattern
appears to key on `GeneralLiabilityClassification<Name>CoverageRules`-shaped file names, and Stop
Gap's rule file is named
`GeneralLiabilityStopGapEmployersLiabilityCoverageEndorsementPolLvlRules` -- a policy-level
("PolLvl") shape the extraction pattern does not match. **The tables and rules documented above
were confirmed present by direct filesystem search and direct XML/CSV reading, not by the
knowledge base tool.** (GATE-STOPGAP-EMPLOYERS-LIABILITY.md Section 0.)

What was verified directly, per table:

- `StopGapRate`: read in full (all 5 rows) for **all five** states (ND, OH, WA, WY, PR) at the
  newest package on disk for each -- **25/25 cells match the manual's two-bucket table** (Section
  4 of the gate doc).
- `StopGapStatCode`: read in full for **ND only** -- 5 rows, maps onto the same two-bucket
  boundary a second, independent way.
- `StopGapManProcContServRiskStatCode`, `StopGapRisksOtherThanManProcContServRiskStatCode`:
  confirmed 0 rows for **ND only**; not re-checked for the other four states.
- Countrywide `StopGapRate`: confirmed 0 rows at **three** countrywide editions (20261001 V01,
  20270401 V01, 20270401 V02) -- not exhaustive across every countrywide edition on disk.
- WV (negative control, not one of the five rating states): confirmed to carry only
  `StopGapStatCodeDef`/`StopGapStatCode`, at every edition from 2021-08-01 through 2027-04-01, with
  no Rules file and no `StopGapRate` table -- corroborates rather than narrows the five-state scope.

*As originally produced (2026-09-02):* no second reading pass was performed; the counts were read
once, directly from the files named. A second pass was made on 2026-10-02 (below).

**(engine) Second pass, 2026-10-02.** The second reading pass and an execution pass:
- All five states were rated offline with a PolLvl record (500,000 × 3, class 50017). Stop Gap premium:
  ND 15 / 15, OH 10 / 10, WY 30 / 25, PR 50 / 55 (2026-10-02 / 2027-04-01); WA 15 at 2027-04-01.
- Every `StopGapRate` and `ILFPremOps` lookup hit, provided the limit spelling matched the resolved
  edition.
- Sending the pre-2027 `" BI"` spelling to ND 20270401 V04 made the ILF lookup miss, and Stop Gap rated
  at $0 with no referral.
- The countrywide `StopGapRate` is header-only in all 12 CW editions.
