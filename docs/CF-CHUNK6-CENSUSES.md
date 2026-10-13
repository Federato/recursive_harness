# Property chunk 6, tasks C6-05 to C6-07 — the three censuses

Gate points 6, 7 and 5, run for the `CommercialPropertySpecialClass` datadef
group. 2026-09-18. All three run from the shared gate scripts, extended rather
than duplicated:

    python scripts/cf/04_shared_names.py                                      # C6-05
    python scripts/cf/05_exclusion_records.py                                 # C6-06
    python scripts/cf/08_hardcoded_literals.py --group CommercialPropertySpecialClass   # C6-07

---

## C6-05 · Shared names — 39 shared, **13 reading different tables**

### Chunk 3's prediction pays forward a third time

`SetBasicGroupIBaseRate` resolves in four datadef groups:

| Group | Table |
|---|---|
| `CommercialPropertyStructure` | `BasicGroupIRate` |
| `CommercialPropertyPersonalProperty` | `BasicGroupIRate` |
| **`CommercialPropertySpecialClass`** | **`BasicGroupIRateSpecialClass`** |
| `CommercialPropertyOutdoorTreesShrubsAndPlants` | `BasicGroupIRateSpecialClass` |

**Exactly what chunk 3's adjudication predicted**, and the third chunk in a row
where that prediction has held before the chunk was opened.

### The sharpest name-reuse in the project

`SetBasicGroupIISymbolNum` — **five coverages, five different tables, one rule
name**, and not one of them is shared:

    Outdoor Trees        -> OutdoorTreeBasicGroupIISymbol
    Outside Signs        -> OutsideSignsBasicGroupIISymbol
                            OutsideSignsBasicGroupIISymbolOtherThanMetal
    Radio/TV Antennas    -> RadioOrTelevisionAntennasBasicGroupIISymbol
    Radio/TV BI or EE    -> RadioOrTelevisionAntennasBasicGroupIISymbol
    Special Class        -> SpecialClassBasicGroupIINumber

### Two names where Special Class and Building share the SAME table

This is the opposite of the `BLDG_PERSPROP` split and worth naming separately,
because "shared name" has meant "different table" in every previous chunk:

| Rule | Structure | Special Class |
|---|---|---|
| `SetSpecialTheftExclusionFactor` | `SpecialBldgTheftExclusionFactor` | **the same table** |
| `SetSpecialBaseRate` | `SpecialBuildersRiskRate`, `SpecialBuildingRate` | **`SpecialBuildingRate` only** |

The second line is C6-23's claim, visible structurally: Building reaches a
Builders Risk table from this rule and **Special Class does not** — there is no
class-1150 branch here.

### And `BasicGroupIRateSpecialClass` has four consumers, not one

Special Class, Outdoor Trees, Outside Signs and Radio/TV Antennas all read it.
A change to that table moves three coverages outside chunk 6.

### Three names that read no matrix at all in our group

`SetBasicGroupIRate`, `SetBroadRate` and `SetSpecialRate` are pure arithmetic
here (`base × LCM`) while other groups look something up under the same name —
`DebrisRemovalRate`, `MiningPropertiesBusnIncomeRate`,
`LeaseholdInterestBroadSpecialRate`, `PollutantCleanUpAndRemovalRate`. Nothing
is shared but the string.

---

## C6-06 · Exclusion records — Special Class files its own, and cyber does not

| Family | Distinct records | Groups | **Special Class's own record** |
|---|---|---|---|
| Vandalism | 5 | 13 | `CommercialPropertyVandalismExclusionSpecialClass` |
| Windstorm or Hail | 5 | 19 | `CommercialPropertyWindstormOrHailExclusionSpecialClass` |
| Theft | 5 | 7 | `CommercialPropertyTheftExclusionSpecialClass` |
| Cyber Incident | 1 | 1 | **not elected in this group** |
| Cyber + ensuing COL exceptions | 1 | 1 | **not elected in this group** |

**Three of the five families file a Special-Class-specific record** — electing
Building's vandalism, wind/hail or theft exclusion does nothing here, and vice
versa. The engine already dispatches by datadef group, so this is confirmation
rather than a defect; the point of the census is that a product wiring one
"theft excluded?" control to every coverage is a **simplification**, and one
that has to be logged rather than assumed.

**Cyber is the opposite shape.** One record, at the **policy** level
(`CommercialProperty`), and Special Class's four premium files each apply
`CyberIncidentExclusionFactor<Form>` and `CyberIncidentExclusionCOLExcptnsFactor<Form>`
outside the rounded product. Same shape chunk 5 found for the ten terrorism
families: **a policy-level election reaching every coverage's premium.**

---

## C6-07 · Hardcoded literals — 36 pinned sites, **14 that kill filed rows**

| Table . column | Pinned to | Filed rows unreachable |
|---|---|---|
| **`BroadFormBaseRate` . `ConstructionTypeToUse`** | **`Frame`** | **5 of 6 values (83%)**, from every site in the group |
| `BroadFormBaseRate` . `CovType` | `Bldg` | 4 of 5 (80%) |
| `ProtectionClassFactor` . `ConstructionCode` | `1` | 5 of 6 (83%) |
| `BasicGroupIIRate` . `CovType` | `Bldg` | 1 of 2 |
| `LowestBasicGroupIIRate` . `CovType` | `Bldg` | 1 of 2 |
| `Deductible250Factor` . `CauseOfLoss` | `Basic` / `Broad` / `Special` | 1 of 4 |
| `DeductibleFactor` . `CauseOfLossDeductible` | `Basic Group I` / `Basic Group II` / `Other Cause Of Loss` | none — the sites pin all three |
| `BldgCodeEffectivenessGradeStatCode` | `Ungraded` / `Not Graded` | 11 of 12 — statistical coding, not rating |

**The `"Frame"` pin is C6-22's structural proof.** `BroadFormBaseRate` carries
six construction values and Special Class can reach exactly one of them, from
every site in the group. A fire-resistive scheduled item pays the frame rate,
and the filed fire-resistive row is published and unusable on this path.

**`ProtectionClassFactor` is a dead lookup inside a dead factor** — pinned to
construction code `1`, making 140 of 168 filed rows unreachable, on a factor
C6-17 expects to find is never read by any rate chain.

**`BasicGroupIIRate` and `LowestBasicGroupIIRate` are pinned to `"Bldg"`** —
Special Class reads the *Building's* row of a shared table, exactly as Business
Income did in chunk 5. There is no Special Class row to read.

### Branch literals — 150 distinct pairs, 479 comparisons

The most-tested are `IncludedInBlkt == Yes` (22), `PremiumIndicator == 1` (19),
`Premium == 0` (19), `CoverageOnPolicyIndicator == 0` (17) and
`CauseOfLossToUse == Special` (15).

**`PolicyType` is tested 20 times** — 13 against `Commercial Property Policy`
and 7 against `Standard Property Policy`. It is the field whose absence priced
Broad and Special at zero in C6-01, and this census is where that would have
been caught first.

---

## What the three say together

All three censuses point at the same place: **Special Class's rating identity
lives in its keys, not its rates.** The rate tables are largely shared with
Building; what differs is which row can be reached — a class *description*
instead of a class code, a pinned `"Frame"`, a pinned `"Bldg"`, and a
protection class folded into the key rather than applied as a factor.
