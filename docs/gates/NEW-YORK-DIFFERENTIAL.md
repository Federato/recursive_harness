# New York — the most-deviating jurisdiction

**Filed 2026-08-12 (Step 44).** Not a gate — New York is a *jurisdiction*. The second of the two
differential fixtures the gates have carried as owed work since Step 38, and runnable:
[`tests/verify_new_york.py`](../../tests/verify_new_york.py), **10/10**.

**As-of date: 2026-08-12.** Resolved package `GL_NY_20260801_V01`, declared parent
`GL_CW_20260101_V01` (N5/N6).

---

## 1. The size of it

| | Rank | |
|---|---|---|
| **New York** | **1 of 51** | **698 override rules across 134 files** |
| Vermont | 2 | 267 |
| Illinois / Texas | 3= | 239 |
| *median of 51* | | *124* |

**2.6× the next jurisdiction and 5.6× the median.** Three gates recorded a New York finding in
passing; none measured the surface. Two of those passing records turn out to be narrower than the
truth, and one turns out to be a false alarm.

---

## 2. New York does not write claims-made General Liability, and says so three ways

Gate 332 found that New York replaces liquor's `SetYearInClaimsMade` and `SetClaimsMadeMultiplier`
with constant stubs, and concluded that *a claims-made liquor risk silently prices at `0`*.

**That was one third of it.** Measured across the package:

| Mechanism | Extent |
|---|---|
| `SetClaimsMadeMultiplier` stubbed to a constant `1.0` | **5 coverage groups** — Prem/Ops, Products/Completed Operations, Liquor, Unmanned Aircraft Cov A and Cov B |
| `SetYearInClaimsMade` stubbed to `0` | **3 groups** |
| Claims-made multiplier **tables** overridden to **0 rows** | **4 of 4** — `PremOpsClaimsMadeMultiplier`, `…AllOther`, `ProdsCompldOpsClaimsMadeMultiplier`, `…Multipliers` |
| Liquor `SetBaseRate` replaced with an occurrence-only rule | 1 |
| **Other jurisdictions doing any of this** | **0 of 50** |

The countrywide originals are real rates: `PremOpsClaimsMadeMultiplier` is **5,940 rows** with
values from **0.34 to 0.98**. New York withdraws all of them.

**Read together, ISO is saying one thing three times: New York does not write claims-made GL.** The
belt-and-braces is the interesting part — an engine that missed the empty tables would still be
caught by the stub, and vice versa. **But an engine that falls through an empty state table to the
countrywide row (N16's row-wise fallback) applies a 2–66% discount New York has withdrawn.** N16
and N3 pull in opposite directions here, and N3 wins: the override is at the *package* layer, so
there is no countrywide row to fall through to.

**This corrects gate 332's scope, not its finding.** The liquor conclusion stands; it is one of five
coverages, not one of one.

---

## 3. The terrorism gate is not holed — checked, and it holds

New York overrides **174 of the 602** rules in `GeneralLiabilityTerrorismEndorsementCoverage` and
adds **4**. Against a gate filed the day before, that looked like the largest unexamined hole in the
project.

**It is not a hole. `SetPremium` is not among the 174.**

New York inherits the countrywide premium rule unchanged:

```
Premium = round(EndorsementPremium × CertifiedActsofTerrorismExposureClassFactor, 0)
```

What the 174 overrides do is rebuild the **roll-up** that produces `EndorsementPremium` — one
`Set…TotalPremium` rule per endorsement — because New York's endorsement inventory differs. The 4
additions are two New York forms and their premium terms: **binding arbitration** and **non-binding
arbitration**.

**So New York changes the *input* to the terrorism formula, not the formula.** The gate's §1 premium
source table is correct for all 51 jurisdictions. Recorded because the alternative — assuming 174
overrides in a just-gated group must be a defect — would have been wrong in the expensive direction.

---

## 4. Rating switched off for 83 endorsements

| | |
|---|---|
| Empty-body overrides | **151 of 698** |
| …of which `ErcRate` | **83** |
| …whose countrywide original is non-trivial | **130 of 151** |
| Constant-stub overrides (neutralised without being empty) | **98** |

**`ErcRate` is an endorsement group's rating entry point.** Overriding it with `<rul:Sequence />`
leaves the endorsement attachable and its premium capturable, and removes its ability to rate.
**New York does that 83 times** — the largest instance of N3's *empty ≠ absent ≠ inherit* in the
corpus.

**The 98 constant stubs are the harder class**, and the reason N3 carries its second clause: a check
that looks for empty bodies finds the 151 and misses these. They include the claims-made pair (§2),
`SetSizeOfRiskRatingApplies → "No"`, and six `SetCoverageOnPolicyIndicator` stubs that switch whole
coverages off.

---

## 5. What was already known, now pinned

- **Loss costs and the rating-basis selector are both sharded by territory.** 95 rate tables, **71
  populated**, of which **21 carry a `Terr<nnn>` suffix** — including `PremOpsELPTextTerr001`. The
  base `PremOpsLossCost` is present and **empty** (N3/OI-20). Sharding the *selector* rather than
  just the rates is rare: N17 records it as one of seven, and New York is the only instance.
- **Class `91600` is New York's alone.** Its `TerrorismExposureClassesPremises` carries **106**
  above-average classes against countrywide's 105, and `91600` is the difference — matching the
  manual's 142-class table, which countrywide ERC cannot (gate terrorism §4). New York rates it: it
  appears in **20+** of NY's own loss-cost territory shards.

---

## 6. Deliberately deferred to build-order item 11

**Special Protective and Highway** — **36 New York rules and 4 rate tables**
(`…ELP`, `…ELPText`, `…HomogeneityIndex`, `…LossCost`), and **0 countrywide tables**. A rate-driven
coverage that exists in no countrywide edition, carrying its own N17 selector.

It is analysed here only far enough to assert that it is New York's alone and that it rates.
**Deriving it belongs to item 11**, where it sits with the MD and MA lead coverages; doing it now
would duplicate that work against a coverage no other jurisdiction shares.

*(An earlier note put this at "11 tables". That counted `*Def.RateTableDef.xml` schema siblings and
domain tables alongside the rate tables. **4 rate tables** is the figure, and the fixture asserts
the names rather than the count.)*

---

## 7. What the engine owes

1. **Resolve claims-made per package, never per corpus.** In New York the multiplier is `1.0` by
   rule and the tables are empty by override; N16's countrywide row-fallback must not fire, because
   N3's package-layer override removed the table, not the row.
2. **`ErcRate` is overridable to nothing, and that is a filed decision.** An endorsement whose
   `ErcRate` is empty in the resolved package captures and does not rate. 83 of them in one state.
3. **Neutralising stubs are not empty bodies.** Any load-time check for "disabled in this state"
   must catch both forms — 151 empty and 98 stubs in New York alone.
4. **The terrorism formula is countrywide; its input is not.** Build `EndorsementPremium` from the
   resolved package's roll-up set, which in New York includes two forms no other package has.
5. **A jurisdiction may rate a class the countrywide rating population excludes** — `91600` — so
   the class population is a property of the resolved package, not of the parent.

---

## 8. Register

| | |
|---|---|
| **OI-59** *(new)* | New York withdraws claims-made GL across **5 coverage groups**, by rule and by empty table, and is alone in 51. Gate 332 recorded the liquor third only; its conclusion stands, its scope did not |
| **OI-60** *(new)* | New York empties `ErcRate` for **83 endorsements**. Each needs a capture-not-rate disposition in item 13's harness |
| **Gate terrorism** | **Confirmed against New York, not amended.** `SetPremium` is inherited; the 174 overrides rebuild the input |
| **N3** | Corroborated at scale: 151 empty + 98 stub overrides in one package, 130 of the empties replacing a non-trivial parent body |
| **N17** | New York remains the only jurisdiction sharding its rating-basis **selector** |
| **Owed work** | This closes New York. **OI-50 is the last of the three.** |
