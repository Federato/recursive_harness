# Property chunk 12: the gate

**The endorsement families: Debris Removal, Ordinance or Law, Utility
Services, Unmanned Aircraft, Green Upgrades, Dependent Properties.** Filed
2026-09-24. **All six families gated 9 of 9, and all 42 tasks done.**

**In plain English.** Chunk 12 adds six add-on coverages that hang off the
core records built in chunks 1–11. Three of them borrow the building's own
rate and take a slice of it (Debris Removal, Ordinance or Law, Green
Upgrades). Three price from their own tables (Utility Services, Unmanned
Aircraft, Dependent Properties). Each family has a hand-derived golden case
that matched on its first run and matches **ISO's live service to the
dollar**. Two of the families have no ISO example at all, so live calls were
their only proof, and they agree on every case (8 of 8 and 12 of 12). Along
the way, three engine defects were found and fixed, all with the user's
authorization and all confirmed against ISO live.

## The nine points, family by family

| # | Gate point | Debris Removal | Ordinance or Law | Utility Services | Unmanned Aircraft | Green Upgrades | Dependent Properties |
|---|---|---|---|---|---|---|---|
| 1 | Golden case rates end to end | ✅ $49 + $6, 21/21 | ✅ $198, 15/15 | ✅ $15 + $4 / $9 + $4, 14/14 | ✅ $187, 10/10 | ✅ $33, 12/12 | ✅ $80 + $12, 7/7 |
| 2 | Every table's row count stated | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | Every state enumerated | ✅ FL, NY | ✅ AK CA FL MN NY VA WV | ✅ FL | ✅ all 46, 4 patterns | ✅ FL | ✅ FL |
| 4 | Every `0` tested against its branch | ✅ 9 cases | ✅ 8 cases | ✅ 7 cases | ✅ 9 cases | ✅ 8 cases | ✅ 8 cases |
| 5 | Every hardcoded literal listed | ✅ 1 dead literal | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6 | Shared-name traps diffed | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 7 | Exclusion records identified | ✅ | ✅ | ✅ | ✅ (theft: see below) | ✅ | ✅ (theft: see below) |
| 8 | Edition basis stated | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9 | No unexplained message; ISO live | ✅ 9 of 12 | ✅ 8 of 8 (K7 re-run 2026-09-24) | ✅ 10 of 11 | ✅ 10 of 10 | ✅ 8 of 9 | ✅ 12 of 12 |

Every "of N" in row 9 that is short of N is either **ISO refusing** a lookup
that finds no row where we rate (OI-103, not a family defect), or the one
real engine difference, OI-109, which has since been fixed. Every golden case
fires only M-001 and M-002, both already logged. The only new message is
Debris Removal's CP 04 15, logged as **M-003**. **0 unexplained across all
six families.**

## The evidence, point by point

| # | Evidence |
|---|---|
| 1 | Golden cases, each derived by hand before its run: `127_` Debris Removal ([record](CF-CHUNK12-DEBRIS-REMOVAL.md)), `130_` Ordinance or Law ([record](CF-CHUNK12-ORDINANCE-OR-LAW.md)), `133_` Utility Services ([record](CF-CHUNK12-UTILITY-SERVICES.md)), `137_` Unmanned Aircraft ([record](CF-CHUNK12-UNMANNED-AIRCRAFT.md)), `139_` Green Upgrades ([record](CF-CHUNK12-GREEN-UPGRADES.md)), `141_` Dependent Properties ([record](CF-CHUNK12-DEPENDENT-PROPERTIES.md)). **Every one matched on its first run, and ISO live gives the same figures.** Before any golden case, Group A ran all 17 ISO fixtures that carry a chunk 12 record through the engine: 17 of 17 rated ([Group A](CF-CHUNK12-GROUP-A.md), C12-03) |
| 2 | Debris Removal: 6 CW rate rows (3 multipliers, 3 flat rates) + minimum limit (CW 25,000, FL 10,000); it keys the **core** LOI tables on the building's limit, never its own. Ordinance or Law: 11 single-row CW tables, MN and FL rows. Utility Services: 9 CW tables; the three time-element NonPublic tables file every rate as 0. Unmanned Aircraft: 36 tables, family tables CW + FL, EQ tables from chunk 10. Green Upgrades: 4 CW tables, no state rows. Dependent Properties: 6 tables, FL rows |
| 3 | Every family was checked across all 46 states and both layers (state rules and state tables). Florida changes all six. Ordinance or Law has the widest spread: **Virginia files 43 state-only files** (a state broad form rated *alongside* the countrywide one), West Virginia 2 (Flood cells), plus AK, CA (public schools $0), MN and NY. Unmanned Aircraft touches all 46, mostly through Earthquake deductible-tier plumbing. Puerto Rico is excluded by standing rule |
| 4 | 49 zero cases across the six families, each tied to its cause. The ones a product owner needs to know about are all **ISO's own behaviour**, confirmed live: a Debris Removal limit under $25,000 gives a **negative premium** (only an error message stands in front of it); a "No Coverage" building **still pays** for Debris Removal; a blank Ordinance or Law choice **still charges Coverage A**; a missing Utility Services limit covers **the whole building limit**; a blank Green Upgrades percentage **nearly doubles** the premium |
| 5 | All compared literals are filed domain values except one: Debris Removal's `CovType != 'Tobacco Sales Warehouses'` is a form name, never a `CovType`, so the gate is always true. Dead and harmless |
| 6 | Every `../` path climbs to the intended record, in all six. Shared field names (Debris Removal 8, Ordinance or Law 2, and the others) hold equal values where they share a table and key, and different values where they don't; no rule reads one for the other. The five attachments of Utility Services and Green Upgrades read identical fields, form for form. The SC Business Income versions of Dependent Properties mirror the Business Income ones (17 of 25 pairs identical; 8 differ only in names and step order) |
| 7 | None of the six files an exclusion record of its own; each inherits through its parent. **Vandalism flows** into Debris Removal ($49 → $47), all three Ordinance or Law parts, and Green Upgrades ($30 → $28). **It doesn't flow** into Utility Services (no cause-of-loss adjustment) or Debris Removal's Special cell (flat 0.01 rate). A Contents windstorm exclusion reaches a drone through its own wind factor ($187 → $59). ISO agrees on every one |
| 8 | Stated per family, across all 5 parent editions. 20260601 and 20230801 V04 are identical for every family. The older editions differ as follows: FL's V01 has **no `IsNull` guards** (it always recomputes, so the "submitted value overrides the filed table" trap doesn't exist there); V03 (CA, NC) and V02 (MO) carry the drone `Break`-in-`Sum` rule that was OI-108 |
| 9 | Live ISO at EffectiveDateTime 2026-09-17 (OI-105) through `129_` and `132_chunk12_family_raas.py`. Engine-built cases: **55 of 55 that ISO rated agree to the dollar**, messages identical. Every fixture ISO rated agrees cell for cell, Earthquake and Increased Period of Restoration cells included. Every refusal is a lookup with no row (Earthquake Structure lookups on 2023 fixture data, an unfiled waiting period, an unfiled percentage): OI-103 data, not a family defect |

## Engine changes (all user-authorized, all confirmed against ISO live)

| | Defect | Fix | Evidence |
|---|---|---|---|
| **OI-108** | A `Break` inside a `Sum` left the loop before the `Sum` returned. A blanket drone's limit read 0 instead of 99,000 in CA, NC and MO (older editions only) | the `Sum` finishes its iteration, then the `Break` stops the loop | `135_chunk12_oi108_raas.py`: CA, NC, MO and GA **8 of 8 identical to ISO** |
| **OI-109 / OI-110** | A null operand in a premium `Product` stopped the engine; ISO leaves it out of the product | Property's `Product` skips the null and records it in `Interpreter.null_skips`; GL untouched. (A first change that wrote $0 instead was wrong, caught by probes that could tell the two apart, and corrected the same day) | $1 / $3 / $5 live probes; Unmanned Aircraft Z4 equals ISO; Ordinance or Law K7 re-run live 2026-09-24 and now agrees (A $39 + $5, B and C $0); chunk 5's Combined-risk case, a hidden difference until then, now matches ($256 + $30) |

**Regression** (C12-41): `104_chunk10_c10-21_regression.py` now covers
**chunks 0–12**: the six golden cases at their documented figures, the seven
gate scripts, and all GL suites. `--selftest` passes.
**Close-out re-run 2026-09-24: CLEAN** (every chunk 0–12 golden case at its
documented figures, every machinery script and all 16 GL suites exit 0).

## Held honestly: proven from the rules, not by a priced run

These pass their gate points by reading the filed rules. They aren't
wrong, but no priced case has been run for them yet:

* **Florida and the state-only mechanisms.** Florida's Debris Removal minimum
  and no-Contents rule, and Ordinance or Law in CA, FL, VA and WV, are read
  from the filed rules. The Oregon golden buildings don't rate in those
  states, and no ISO fixture comes from them. Florida's Debris Removal
  minimum limit and exposure were confirmed on the engine.
* **Theft exclusion on the drone and on Dependent Properties.** Both probes
  were attached at the building and didn't reach the Contents or Business
  Income theft factor. The factor is wired, but it hasn't been tested with a
  correctly attached exclusion.

## Findings that change how these coverages must be submitted

* **Every family honours a submitted calculated field.** A submitted
  `MinimumLimit`, factor or rate passes the `IsNull` guard and overrides the
  filed table (Debris Removal Z8/Z9, Ordinance or Law K8, Utility Services
  Z7, drones Z9, Green Upgrades Z3, Dependent Properties Z3). ISO has the
  same guards, so no comparison catches it. Florida's older edition is the
  exception.
* **ISO's messages are the only guard** on a negative Debris Removal premium
  (limit under $25,000). A system that ignores them would bill a credit.
* **Drones rate only on the Special form.** On Basic or Broad they are $0.
* **Coverage C needs Replacement Cost valuation**, or ISO fires a filed
  error.
* **Dependent Properties' rate is always submitted.** No rule computes it,
  and with several dependent properties the highest rate wins.
* **Earthquake riders don't all reuse chunk 10.** Utility Services and some
  Dependent Properties riders price Earthquake from their own tables, and
  drones re-run chunk 10's lookups on their own record (C12-04).

## Backlog: not blocking this gate

| Item | What it is |
|---|---|
| **OI-103** | A lookup that finds no row: ISO refuses, we price. Chunk 12 added many data points: `EarthquakeDeductibleTier` ×2, `BuildingHeightFactor`, `BCEGEQFactor`, `HeightTerrGroup`, an unfiled waiting period, an unfiled Green Upgrades percentage, and a blank windstorm deductible on the Special form. Needs targeted probes to find ISO's rule |
| **OI-105** | ISO serves a newer 2027 Oregon edition than our corpus holds. Live comparisons stay at 2026-09-17 until it's ingested |
| **Theft on drones and Dependent Properties** | Re-probe with the exclusion attached to the Contents and Business Income records (see "Held honestly") |
| **FL / VA / WV priced cases** | A golden building that rates in those states, to price the state mechanisms end to end |
