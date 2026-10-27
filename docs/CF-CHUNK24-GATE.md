# Property chunk 24: the gate

**Builders Risk (CP 00 20) with its reporting form (CP 11 05), premium adjustment (CP 11 06), renovations (CP 11 13),
collapse during construction (CP 11 20), theft of building materials (CP 11 21) and materials of others; plus the
stand-alone Theft of Building Materials (CP 10 44).** Filed 2026-10-01. **9 of 9, and all 25 tasks done.** Task record:
[`CF-CHUNK24-TASKS.md`](CF-CHUNK24-TASKS.md).

**In plain English.** Builders Risk insures a building while it is being built or renovated. Its premiums come from the
building's own rate chain (chunks 1-4) times Builders Risk factors: 1.82 for the reporting form, 1.36 / 1.82 for
renovations, which take the LARGER of a Builders Risk rate and the finished building's rate. The premium adjustment form
re-prices each reporting period and pro-rates it by days. **ISO had priced only one of the 20 premium records** (theft, on
145 stored policies); every other figure was a new live probe.

Every figure was worked out before it ran: the hand models of `224_` with every container rate derived by hand from the
filed tables (`225_`); for the 16 states that rewrite a formula, the independent evaluator on that state's own rule text;
renovations Group II's container rate (symbols, BCEG) and the container rates of the states that rewrite them are read from
the engine and checked by ISO (stated, not derived). **ISO agreed on every case it rated**, every premium and (level, message).

**One engine change, with the user's go (OI-121).** The premium adjustment form counts leap days with a host function ISO
ships compiled and does not publish (`GetLeapDays`); the engine refused it. Probed live with dates where the readings must
disagree, ISO pro-rates by plain exclusive days with **no leap day removed** on a one-year term (0.73 / 0.52 where counting
29 February gives 0.74 / 0.53). The engine now reads it so, Property only, one-year terms only; it equals ISO on all five
probes. **The first two probes could not disagree** (chosen on the wrong sign); caught before building and replaced.

**Things the rules do that a submitter must know**, each found by running and confirmed by ISO:
- Builders Risk needs **CovType "Builders Risk" and class 1150**; with a reporting form the building's own limit must be 0.
  CP 00 20 also attaches on any building with renovations; CP 11 06 attaches itself whenever a reporting form exists.
- **Renovations price $0 beside a reporting form**, and the reporting form then copies renovations' rates.
- **A premium adjustment period from expiry prices $0, and one after expiry prices NEGATIVE**, as written, at ISO too.
- Theft's deductible moves no dollar; **FL prices theft on its own rule** (Group I rate x 0.25, no cyber factors).
- Business Income under a class 1150 building takes `BuildersRiskFactor` 2; the building-level unmanned aircraft reads the
  building's Builders Risk EQ factor (0.495 on class A1).
- A submitted reporting-form rate, Factor, ProRate or theft rate survives; **a submitted completed-value multiplier is
  overwritten**. A submitted reporting-form Factor flows into the premium adjustment rates.
- NY: the Group II symbol and the completed-building symbol are **submitted** (NY's rule is empty); an ordinary building
  must send its completed symbol as "Not Applicable".
- Payload: dates as MM/DD/YYYY; the unmanned aircraft's `LimitOfInsurance` is a number; valid construction types are the
  long names ("Fire Resistive - Reinforced Masonry - Other Than Light Steel").

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `225_chunk24_rc2.py --live`, 10 cases, **ISO 10 of 10**, every premium and message: reporting form 400,000 Group I $164, II $321, Special $94, Broad $78, EQ $20; renovations $454 (Frame) / $270 (Fire Resistive), beside a reporting form $0 and the reporting form's Special $145; collapse $8 / $187 / $235; materials of others $232; theft $5, the stored fixture at 120,000 $11; premium adjustment periods $36 / $48 ...; CP 10 44 on both deductible paths. Every container rate predicted by hand |
| 2 | Every table's row count stated | ✅ | C24-06: collapse rates 3 (Option1 / 2 = 5, Option3 0.002), BR EQ factor 9 (FL 15), renovations coinsurance modifier 1 (0.75), completed-value multiplier 2 (1.82 / 1.36), reporting form factor 1 (1.82), BR class code 1150, theft rate 0.009, Special BR rate 0.015, CP 10 44 rate 0.009, BI Builders Risk factor 2, BR time element base 0.018; **the countrywide theft factor table is empty and only FL runs it (0.25)** |
| 3 | Every state is enumerated | ✅ | C24-18 / C24-20 (`227_ --live`): **all 46 states agree with ISO** on a fuller policy (~200 premiums each, every message); the 16 rewriting states' records derived from their own rule text (FL 28, NY 3, KS TX VT 2, AR CA DC RI 1) |
| 4 | Every `0` tested against its consuming branch | ✅ | C24-14 (`226_` Z1-Z11, all agree): no limit on theft, reporting form, renovations; a period from / after expiry ($0 / negative); NewValue 0; materials of others with no manual premium and switched off; collapse with no option and on Basic; CP 10 44 with no Special deductible and "Not Applicable"; EQ "No Coverage" |
| 5 | Every hardcoded literal key listed | ✅ | C24-06: the "Y" constants, Option1-3, the EQ classes, "100%" coinsurance, the two completed-value options, class 1150, "Bldg" / "BldrRisk" broad-form keys: each has a row |
| 6 | Shared-name traps diffed | ✅ | C24-03 / C24-16: `BuildersRiskFactor` (Business Income, under the building) vs `BldrsRiskFactor` (blanket detail, Type "Builders Risk"); the renovations BR rate reads the BUILDING's territory factor and the completed rate the LOCATION's; submitted values survive except the completed-value multiplier; ISO agrees on S1-S4 |
| 7 | Every exclusion's endorsement record identified | ✅ | C24-17: both cyber exclusions move every Builders Risk record at large limits; the wind / hail exclusion moves renovations Group II; CP 10 44 with a theft exclusion fires its message |
| 8 | The edition basis stated | ✅ | C24-19: the only family differences are the preceding-period rule in the 2023 V02 (MO) and V03 (CA, NC) parents, which keep the FIRST of two same-numbered periods where 2026 keeps the LAST: probed (MO 738 / OR 1,214), ISO equal; V04 none |
| 9 | No unexplained validation message | ✅ | C24-15 (`226_`): every Builders Risk message triggered and silent where it should be (the five "only valid with Builders Risk" forms, the SPP rules, the $500 minimum at 250 / 500, class 1150, the blanket sum and mixed forms, NY U / V / W both ways, KS / AL / RI Public and Institutional Plan, CP 10 44's four, the period's covered causes); ISO's (level, message) multiset equals ours on every case |

## What the chunk established, in submission terms

* **The building**: CovType "Builders Risk", class 1150; with a reporting form, Limit 0.
* **Reporting form**: a record under the building with its `Limit`; five coverage records are created (Broad / Special
  switch on the cause). **Premium adjustment** periods under CP 11 06 (`UnitNumber`, `NewValue`, `ComputedFromDate`).
* **Renovations**: a record with `Limit`, `ConstructionType`, `RatingType` "Class" (and `EQClass` for EQ).
* **Collapse**: `CollapseOptionConverted` Option1 / 2 / 3. **Theft**: `Limit`. **Materials of others**: `Indicator` "Yes"
  and `ManualPremium`. **CP 10 44**: `Limit`, `SpecialDed`.
* **Downstream** (C24-22, `228_`): the policy total moves by exactly the Builders Risk premiums, **+$1,976 / +$13,199 (10 x) /
  +$1,982 (FL) / +$1,861 (NY)**, predicted before each call and equal at ISO; every other premium, terrorism included,
  unchanged; the family stat values equal.
* **Gate checks** (C24-23, the engine changed in the chunk): the full `104_ --gate` **CLEAN, 157 of 157** (153 in the first run, which was stopped for low memory, and the 4 left run separately: 224_ and three GL suites); `157_ --all` **293 of 293** premiums and totals equal to ISO; `206_ --check` clean after the OI-121 change (1,352 requests); the chunk 24 scripts registered in `104_` (225_ pinned: 164, 321, 94, 78, 20, 454, 270, 145, 8, 187, 235, 232, 11, 36, 48)
* **Census** (C24-24): **540 of 546** countrywide premium files built (99%); 6 left, all flood (chunk 25).

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-121** | GetLeapDays on a one-year Property term is 0 (fixed with the user's go); other term lengths still refused (unprobed) | no |
| **OI-103** | Four more cases where ISO refuses a blank or missing key and ours prices: the 2% EQ deductible on class A1, the Group II territory (AK AL AR), NY's completed symbol. Chunk 28 decides | no |
| Readers not priced | CA's Ordinance or Law increased period and FL's Pollutant Clean Up read the Builders Risk factors; not priced in this chunk (state-only files of chunks 12 / 16) | no |
