# Chunk 11, Group D: shared machinery (C11-06, 07, 14, 15, 21)

**Predictions written 2026-09-22, before the run.** Script:
[`119_chunk11_groupD_shared_machinery.py`](../scripts/cf/119_chunk11_groupD_shared_machinery.py).
Base: the golden case (`114_…`): Tenants Lease **$268 BGI / $30 BGII**.

## In plain English first

Leasehold Interest borrows a lot from the building record it sits on (its
rates, its cause of loss, its earthquake rate) and from the policy (the
schedule-rating and package multipliers, and the cyber exclusion). This
group checks three things:
- that borrowing never goes the wrong way, so Leasehold Interest never
  overwrites the building's own values;
- that the multipliers it claims to use really move its price;
- that the ones it claims not to use (coinsurance, limit, deductible,
  blanket) really don't.

## Already in hand before this group

* **ISO agrees with every Leasehold Interest rating field** on three live
  cases (golden, Special without and with a Theft Exclusion, all at
  2026-09-17). The only differences are float precision in four unrounded
  intermediates (ours carries more digits; both round to the same 4-place
  factors) and the date format.
* **Found in passing: ISO fixed OI-101 in its 2027 edition.** At
  2027-01-01, ISO's Special-without-theft factor is **1.0** and the Special
  premium is **$53**, not $0. OI-101 is real only in the 2026 edition we
  hold, and it will go away with OI-105.
* **Found in passing: form names don't resolve (OI-106).** Our
  `ErcFormName`/`ErcFormNumber` are "Value Not Found" where ISO returns
  "Leasehold Interest Coverage Form" / "CP 00 60 06 95". It's project-wide,
  not LI-specific: 14 of 20 form records in these runs miss. The cause is in
  `gl_engine/resolve/book.py`: a state file that declares a table replaces
  countrywide's **wholesale** (rule N3). Oregon's `Pages.FormPage.csv` holds
  6 Oregon rows, so every lookup keyed `"CW"` misses. ISO evidently falls
  through to the countrywide rows. No premium impact.

## Predictions

### C11-06: shared names across 32 groups

* **Static.** The LI parent file declares rule names that also exist in the
  Structure file with **different bodies and tables**: at least
  `SetBroadRate`, `SetSpecialRate`, `SetSpecialTheftExclusionFactor`,
  `SetSpecialCauseOfLossAdjustment`, `SetEQCauseOfLossAdjustment` and
  `SetCauseOfLoss`. **Every `RunRule` in the 32 LI files names its
  `FileName`**, so a same-named rule in another file can't be executed by
  mistake. Predicted: 0 `RunRule`s without a `FileName`.
* **Dynamic.** On the golden case, the **Structure's** copies of those
  same-named fields (`BroadRate`, `SpecialRate`,
  `SpecialTheftExclusionFactor`, `SpecialCauseOfLossAdjustment`,
  `EQCauseOfLossAdjustment`, `CauseOfLoss`) equal ISO's Structure values
  exactly: **0.0, 0.0, 1.0, 0.0, 0.0, "Basic"**. The LI record's own copies
  are different values (e.g. LI `BroadRate` 0.023, LI
  `SpecialTheftExclusionFactor` 0.0), so each group writes its own record.

### C11-07: exclusion records per group

* **Cyber exclusion is policy-level and shared.** A
  `CommercialPropertyCyberIncidentExclusion` record on the policy sets
  `CyberIncidentExclusionFactorBGI` = **0.995**
  (`CyberIncidentExclusionFactors[CW]("Basic Group I")`). LI reads it 7
  levels up. Predicted: BGI round(268 × 0.995) = round(266.66) = **267**,
  BGII round(30 × 0.995) = round(29.85) = **30**. `…COLExcptnsFactorBGI`
  stays **1.0** (a separate mechanism).
* **Theft exclusion is structure-level.** The LI record reads the
  **Structure's** `SpecialTheftExclusionIndicator`, which is set by a Theft
  Exclusion record on the Structure (Group B S3: $46 at 2026-09-17, matched
  ISO). So `SpecialLeaseHoldTimeElementTheftExclusionFactor` is an
  LI-owned table **gated by a Structure-owned record**: neither per-group nor
  policy-level.

### C11-14: absent at run time, not just in the XML

Each of these is predicted to leave the premium at **$268 / $30**: Structure
`Coinsurance 80%`; `Limit 500,000` (LOI); `Deductible 5,000`;
`IncludedInBlkt Yes`; and all four together. `IncludedInBlkt Yes` is the one
to watch: it's out of domain for a Leasehold Interest structure
(`DomainIncludedInBlktBldg` allows only `No`), and it redirects
`CauseOfLossToUse` to `BlktCauseOfLossValue`. Whatever it does is a finding.

### C11-15: IRPM and package modification really apply

| Case | Change | BGI | BGII |
|---|---|---|---|
| a | policy `IRPMFactor 1.10` | round(268 × 1.1) = **295** | **33** |
| b | policy `PackageModFactor 0.90` | round(268 × 0.9) = **241** | **27** |
| c | both | round(241 × 1.1) = **265** | round(27 × 1.1) = **30** |
| d | **Structure** `PackageModFactor 0.50` (not the policy's) | **268** | **30**, because LI reads the policy-level factor |
| e | EQ elected + both | **265**, and EQ stays **10** | **30** |

Case (e) is the inverse of Earthquake, run: IRPM/PackageMod move the four
ordinary forms and **not** the EQ cell, whose `SetPremium` has no slot for
them. (a) also depends on the submitted `IRPMFactor` surviving:
`SetIRPMFactor` only writes it when null.

### C11-21: the Earthquake cell reads chunk 10's chain and never collides

With EQ elected (Group B S5 inputs), run **with and without** the LI record.
Predicted: every `EQ`-prefixed field on the Structure is **identical** in the
two runs (EQCauseOfLossAdjustment **0.009**), the LI record's own
`EQCauseOfLossAdjustment` = **0.009** (a copy), and the Tenants EQ premium
is **$10**.

## Result (2026-09-22)

**Every prediction held**: 6 shared-name checks, the cyber exclusion ($267 /
$30, factor 0.995), all 5 absent-at-run-time variants ($268 / $30), all 5
multiplier cases (295/33, 241/27, 265/30, a Structure-level PackageMod
ignored, EQ unmoved at $10), and the EQ no-collision check (21 EQ-prefixed
Structure fields identical whether LI's cells are on or off).

* **C11-06.** Six rule names are shared between the LI parent and the
  Structure file, **all with different bodies**. `SetSpecialTheftExclusionFactor`
  is the notable one: LI reads `SpecialLeaseHoldTimeElementTheftExclusionFactor`,
  the Structure reads its own building table. **No execution collision is
  possible**: all `RunRule`s in the 32 LI files name their `FileName`. Each
  group writes its own record. On the golden case the Structure's copies are
  0.0 / 0.0 / 1.0 / 0.0 / 0.0 / "Basic", **identical to ISO's Structure**,
  while LI's own copies differ (e.g. `BroadRate` 0.023).
* **C11-07.** The cyber exclusion is **policy-level and shared**: LI reads
  the same `CommercialProperty`-level factor the Building forms read. Only
  LI's movement ($268 → $267) was measured here. The theft exclusion is **structure-level**.
  No LI group files an exclusion record of its own.
* **C11-14.** Coinsurance, limit, deductible and blanket flag are all inert
  for LI at run time, even out of domain (`IncludedInBlkt Yes`).
* **C11-15.** IRPM and PackageMod move the four ordinary forms. They're read
  from the **policy**, so a Structure-level PackageMod is ignored, and they
  don't touch the EQ cell.
* **C11-21.** The EQ cell copies the Structure's `EQCauseOfLossAdjustment`
  (0.009) and changes nothing on the Structure.

**One finding from running, not predicted: OI-104 is far more reachable than
C11-04 thought.** A `CovType = Leasehold Interest` structure submitted
**without** an LI record doesn't lose the coverage. The Structure's attach
rule **auto-creates an empty LI record**, whose blank rate and dates give
0^0, and **our engine refuses the whole submission**. ISO computes 0^0 = 1
and would price it at $0. So an incomplete LI submission crashes here and
prices at ISO. It still fails safe, but it no longer takes an unusual input
to reach it.
