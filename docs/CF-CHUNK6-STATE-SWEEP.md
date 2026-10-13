# Property chunk 6, task C6-04 — the 47-jurisdiction sweep

**Special Class, Basic Group I, every jurisdiction predicted from its own filed
rows before the engine ran.** 2026-09-18.

Script: [`scripts/cf/43_chunk6_enumerate_states.py`](../scripts/cf/43_chunk6_enumerate_states.py).

## Result — **47 of 47**

Every jurisdiction matches its own prediction. The first sweep since chunk 3 to
land complete, and the first ever where **three jurisdictions correctly produce
no premium at all**.

| | |
|---|---|
| Exact | **47 of 47** |
| $66 — the countrywide chain | 43 |
| $64 — PR, on its own filed rows | 1 |
| **$0 — cannot reach a rate** | **3: AZ, FL, NY** |

The case is the chunk 6 golden case: a broadcasting tower, limit 100,000,
coinsurance 90%, deductible 1,000, protection class 3 — **$66 in Oregon**.

---

## What is new about this sweep

Chunks 1–5 asked *does this state file a rate*. Chunk 6 has to ask **can this
state reach a rate at all**, because the key itself is filed per state:

    ClassDescription  --SpecialClassDescriptionConvertedOption-->  OptionNN
    OptionNN + ProtectionClassToUse  --BasicGroupIRateSpecialClass-->  rate

Three jurisdictions declare the converter table themselves, and **a declared
table wins by name even when it is empty** (contract N3).

---

## The three zeros, and none of them is a missing rate

### FL — the description does not exist in Florida

Florida declares its own converter with **68 rows** and the golden case's class
is one of **six countrywide descriptions Florida drops**: EV charging stations,
freestanding solar arrays, cell antennas, and wind turbines — every modern
class.

**Corrected 2026-09-18 by C6-11.** This page first said Florida files 11
descriptions of its own in a private option namespace. **It does not.** Florida
resolves over `CF_CW_20230801_V01` — **two countrywide editions behind** —
and against its own parent it adds 3 descriptions, drops 6, and files **zero**
option codes outside its parent's set. The "11" came from diffing Florida
against the 2026 countrywide table; 8 of the 11 are an artefact of comparing
across editions. See [`CF-CHUNK6-DESCRIPTION-CHAIN.md`](CF-CHUNK6-DESCRIPTION-CHAIN.md).

So Florida files a complete 204-row rate table whose keys are its own parent's
keys — just an older parent's. The class the golden case rates was **renamed**
countrywide after Florida's edition, and Florida still files the old name.

### NY — the converter is header-only and the rule that reads it is deleted

New York declares `SpecialClassDescriptionConvertedOption` with **zero rows**
and empties `SetSpecialClassDescConvertedOption` to `<rul:Sequence />` — while
still filing **189 Group I rate rows** keyed on `Option1a`-style codes. Whether
those rows are unreachable or the option is a *submitted* field in New York is
C6-12's question; either way, the option cannot be derived there.

### AZ — the rate step is rewritten around a location field that defaults to zero

Arizona overrides `SetBasicGroupIRate`:

    BasicGroupIRate = r3( r3(BasicGroupIBaseRate x ../../BasicGroupIReductionCredit)
                          x LossCostMultiplier )

`BasicGroupIReductionCredit` is read through `FromConstant="0.0"` and lives on
the **Location**, not on the Special Class item. Absent therefore means **zero,
not "no reduction"** — and the entire Group I rate collapses, with the base rate
sitting correctly at 0.07 one step upstream.

Proven by moving it rather than asserted:

| `BasicGroupIReductionCredit` | Premium |
|---|---|
| absent | **$0** |
| 1.0 | **$66** |
| 0.9 | **$59** |

**Chunk 5 met this same Arizona credit through the Building dependency**, where
it cost a dollar and was logged as a stated divergence. Here its absence costs
the whole premium. The same state field, twice, at two very different prices —
and nothing in the Special Class payload hints that it is required.

---

## What the three have in common

**No validation message from any of them.** A correctly-formed submission for a
real ISO class returns $0 in three jurisdictions, for three unrelated reasons,
in silence. Chunk 6's zero cases found the same shape inside one state; the
sweep finds it across the map.

## What this sweep does not settle

* **Basic Group II, Broad and Special per state.** Group I is the form whose key
  is state-filed, so it is the one the sweep prices. The other three forms are
  covered by C6-19 through C6-23.
* **Whether New York's 189 rows are reachable by submission.** C6-12.
* **Florida's full divergence, in both directions.** C6-11.
