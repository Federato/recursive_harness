# Property chunk 28, C28-08..10: proposal for OI-125, OI-112 and OI-114 (Set C, messages match ISO)

**Status: BUILT 2026-10-05, all three with the user's go (C28-09 as "don't read them on 2023-parent states").** Measured before any code changed. **One correction in the build:** OI-125 was first built statically ("a field some rule can write"); that moved 15 requests ISO agrees with, so it was replaced by the measured reading exactly (a look-ahead pass records which submitted values a rule actually writes in the run). Each item below is
measured on every stored request ISO rated (1,690+) and, where a probe could add anything, sent to ISO live.

## In plain English

* **OI-125.** When a request sends a value for a field ISO's rules fill in themselves later, ISO acts as if the value
  was never sent; ours reads it until the rule overwrites it. Only one message differs today (an "only one apartment
  per building" count).
* **OI-112.** On the nine states still rated on the 2023 countrywide editions, ISO's request reader throws away three
  answers on the multiple-deductible form (CP 03 20), whatever is sent, so ISO always asks "please select at least one
  covered cause of loss". Ours keeps them and stays silent.
* **OI-114.** ISO's 2019 / 2020 builds left an empty placeholder inside an "and" test. Ours refuses the whole policy
  there; ISO rates it. Today four back-dated policies cannot be rated by ours at all.

## OI-125 (C28-08): a submitted value for a field the rules overwrite is not read

| Reading | Rule | Measured (`251_`, two passes per stored request ISO rated) |
|---|---|---|
| now | a submitted value is read until a rule overwrites it | K4d raises one message ISO doesn't |
| **R1** | a submitted value for a field a rule later writes is not read at all (as if never sent) | **1,688 of 1,692** stored requests submit at least one such value (25 fields: `ExpDate`, `RatingType`, `BldgClassCode`, `BasicGroupIIRatingTerr`, `PolicyType`, … `IRPMFactor`, `PackageModFactor`, `IncludedInBlkt`, `Premium`); with every one hidden until its write: (level, message) equal to ISO 1,686 → **1,687** (K4d fixed), **0 broken, 0 premiums moved** (the 4 that raise are OI-114's) |

The ordering reading ("ISO copies the rating type before counting") is refuted by K4c (it would count 2; ISO counts 0).
A submitted value a rule never overwrites (an `IsNull`-guarded field such as `SpecialBaseRate`) is read as today, at
ISO too (chunk 26), and R1 leaves it alone by construction.

## OI-112 (C28-09): three CP 03 20 answers are dropped on the 2023 editions

Evidence: `243_` live, MA (CW 2023 V04 parent): ISO drops `AllCoveredCausesOfLoss` sent as "Yes", "True", "1", "Y",
**and as the JSON booleans `true` and `false`** (2026-10-05): the echo is empty, the message fires, 124 of 124 premiums
equal; OR (2026) keeps "Yes" and is silent. The 5 ISO fixtures on 2023 parents (CA MA MO NC NC) sent all six answers
and ISO echoed only `WindstormOrHail`, `AllCoveredCausesOfLossExceptWindstormOrHail` and
`…ExceptWindstormOrHailAndTheft`: **it keeps three checkbox answers on the same record and drops exactly
`AllCoveredCausesOfLoss`, `AllCoveredCausesOfLossExceptTheft` and `Theft`.** Nothing in the corpus explains which: all
six have identical form-field and DataDef declarations, no rule writes or removes any of them, and no state redefines
the record. So "drop every checkbox field" is refuted, and the change has to name the three.

**Proposed:** on a book whose parent is CW 2023 V02, V03 or V04, a submitted value of those three fields on
`CommercialPropertyMultipleDeductibleFormFixedDollarDeductibles` is not read (as if never sent). The alternative is to
leave it, documented as an ISO-side behaviour the corpus cannot account for.

## OI-114 (C28-10): a `<rul:Null/>` operand of `And` / `Or` is false

| Reading | Measured (`252_`, the 4 stored back-dated requests that raise today, each with ISO's response) |
|---|---|
| now | all 4 refuse ("a condition evaluated to NoneType") |
| **false** | **4 of 4 equal to ISO**: every premium (154, 111, 116, 150 of each) and every (level, message) |
| true | identical to false |

No probe separates the two on the margin clause rule: its `And` also holds `Equal(<Null/>, "Yes")`, false under any
reading. Proposed: **false**, the conventional reading and the one the engine already gives a comparison with null.
Packages affected: CW 20191201 and 20201201 (in force in 43 states until 2024-09), FL 20191201, NC 20230801 / 20240201;
none in force at 2026-09-17.

## The changes (Property only; GL untouched), each with its own go

1. **OI-125:** a read of a submitted value returns null when a rule writes that field later in the run (`R1`).
   *Built how:* a pre-pass over the program lists the fields written unguarded per record; reads of a still-submitted
   value of such a field return null until the first write.
2. **OI-112:** the three answers above are not read on 2023-parent books.
3. **OI-114:** a `Null` operand of `And` / `Or` counts as false.

## After each build (C28-11)

`206_ --check` (predicted: messages move only on the requests named above; no premium), `157_ --all` 293 of 293, the
full `104_ --gate`, and the item's own script re-run with the change built in.
