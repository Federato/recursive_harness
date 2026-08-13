# OI-40 — every load-bearing count, re-measured as of a date

**Filed 2026-08-11.** Closes **OI-40**, opened in Step 30 when the as-of defect was found in gate
335. Reproduce with:

```
python scripts/erc/32_asof_recount.py 20260811 20270401 99999999
```

The as-of date is a **required** argument. There is no default, and `99999999` — the end state —
is named explicitly rather than reached by omission. Output of the run behind this document is
kept at `scripts/erc/out/asof_recount.txt`.

---

## 0. What was being tested, and why

[`RECONCILIATION.md`](RECONCILIATION.md) §1 established that *"latest package per jurisdiction"*
describes a **future** state: the corpus holds **82 state packages effective after today**. Four
load-bearing figures had been measured that way and never re-tested. Until they were, none of them
could size a phase or seed a class list.

Method, per N4/N5/N6 and habit 1:

- each jurisdiction resolves to the latest package effective **on or before** the as-of date;
- the countrywide layer resolves to the parent the resolved state package **declares**, read from
  the XSD import — never to the newest countrywide package;
- identity comes from the XSD `targetNamespace`, never the directory name.

567 packages across 52 namespaces are discovered this way, which reconciles with N6.

---

## 1. Verdicts

| Figure | As recorded | Today (2026-08-11) | 2027-04-01 | End state | Verdict |
|---|---|---|---|---|---|
| **F1** Territory scheme | 27 ZIP · 20 single · 4 county/place | **27 · 20 · 4** | 27 · 20 · 4 | 27 · 20 · 4 | ✅ **Unaffected.** Stable at every date the corpus covers |
| **F2** Countrywide table population (N7) | 138 of 272 header-only | **111 of 266** | 138 of 272 | 138 of 272 | ❌ **End-state figure.** N7's evidence is a 2027 number |
| **F3** Prem/Ops class inventory | 238 pre-only · 204 2027-only · 959 both | **1,197, one list** | 238 · 204 · 959 | 238 · 204 · 959 | ⚠️ **Correct, but only from 2027-04-01.** Today there is no split |
| **F4** Rating vs capture | 16 · 383 · 78 | **18 · 356 · 84** | 18 · 376 · 82 | 18 · 376 · 82 | ⚠️ **Split**, and separately **two short** — see §5. The rate-driven *set* holds at every date; `383/78` is a union over all editions ever filed |
| **F5** Gate-cited layer tables | CW `0 rows`, state populated | same | same | same | ✅ **Unaffected**, in all ten countrywide editions |

Two figures survive, two need their tense fixed, and one — F4 — splits into a part that survives
and a part that does not.

**F4 then failed a second, unrelated test.** Its rate-driven count was **two short** — a defect in
the classifier, not in the dating. Found after this document was first filed, while enumerating the
remaining gates; recorded in §5 rather than quietly patched.

---

## 2. F1 — territory resolves the same way at every date

**The phase 3 exit criterion stands.** Build plan §12 requires *"All 51 resolve — 27 ZIP, 20
constant, 4 by submitted county"*, and that is true as of today, as of the cliff, and in the end
state. It is also true at 2023-06-01, 2024-06-01 and 2025-06-01. Phase 3 is correctly specified and
`ERC-TER-001` needs no change.

Two things had to be got right before the figure could be trusted:

**The classifier had to be rebuilt, because none existed.** `22_territory.py` measures territory
*columns and codes*; the three-scheme classification in `knowledge/territory.json` was added by
hand on 2026-08-10 and no script reproduced it. It is now derived in code, from the files.

**Delaware is filed under a fifth table name.** The first pass classified DE as `UNRESOLVED` and
returned **19** single-territory jurisdictions, not 20. DE carries no
`DomainPremisesOperationsTerr`; its constant `001` is in `DomainPremOpsTerritory`. Five distinct
table names carry the premises/operations rating territory across the corpus
(`DomainPremisesOperationsTerr` ×238, `DomainPremOpsTerr` ×47, `DomainTerritoryAssignmentPremOps`
×26, `DomainPremOpsTerritory` ×12, `DomainPremisesOperationsTerritory` ×7). A classifier keyed to
the commonest name loses a state silently — **habit 1's failure mode, in a new place: the name was
read instead of the directory.**

Verified beforehand rather than assumed: **the countrywide layer carries
`DomainPremisesOperationsTerr` and `DomainTerritoryCodeByZipCode` as header-only stubs in all ten
countrywide editions.** Territory lives only in the state layer, so a state package alone decides
its scheme.

### The corpus has an as-of floor

| As of | Jurisdictions resolving |
|---|---|
| 2021-06-01 | **9** of 51 |
| 2022-06-01 | 50 of 51 (WI absent) |
| **2022-09-01 onward** | **51 of 51** |

Earliest state edition is 2020-12-01; the last jurisdiction to appear is **Wisconsin on
2022-09-01**. **Full 51-state as-of coverage begins 2022-09-01** — before that the resolver cannot
answer, and must say so rather than fall back to the earliest available edition. This is a new
load-time boundary, recorded as **OI-41**.

---

## 3. F2 — N7's evidence is a 2027 number

**N7's rule is untouched; its evidence is dated.** *"138 of 272"* was measured in
`GL CW 20270401 V01`, which does not take effect for eight months.

| Countrywide edition | Rate tables | Header-only | Populated |
|---|---|---|---|
| `GL_CW_20201201_V01` | 236 | 108 | 128 |
| `GL_CW_20231201_V03` | 266 | **111** | 155 |
| `GL_CW_20260101_V01` — **in force today** | **266** | **111** | 155 |
| `GL_CW_20270401_V01` — from the cliff | 272 | **138** | 134 |

**The proportion of empty countrywide tables jumps from 42% to 51% at the 2027 edition**, and the
table count rises by six. The 2027 edition is not merely renumbered: it withdraws countrywide
content. **N7's evidence line should read `111 of 266` today and `138 of 272` from 2027-04-01.**
This also closes the sweep **OI-19** asked for — all ten editions are now measured.

### A second edition error, independent of the as-of one

At **no** date is there a single "the countrywide layer".

| As of | Declared countrywide parents in force |
|---|---|
| **Today** | `GL_CW_20231201_V02` (1 state) · `GL_CW_20231201_V03` (4) · `GL_CW_20260101_V01` (46) |
| 2027-04-01 | `GL_CW_20231201_V02` (1) · `GL_CW_20260101_V01` (7) · `GL_CW_20270401_V01` (43) |

Today the newest countrywide package *is* `GL_CW_20260101_V01`, so resolving as-of and resolving by
declaration agree for 46 of 51 states — **and disagree for five**. Those five are only caught by
habit 1. On 2027-04-01 the two methods disagree for eight. **The ingestion layer must hold several
countrywide editions simultaneously**; there is no date at which one suffices.

---

## 4. F3 — the class-code split does not exist yet

**Today: 1,197 Premises/Operations class codes, one list, no split.** All 51 jurisdictions are on
the pre-2027 basis, so there is nothing to reconcile.

| As of | In force | pre-2027 basis | 2027 basis | pre-only | 2027-only | both |
|---|---|---|---|---|---|---|
| **Today** | **1,197** | 1,197 | 0 | — | — | — |
| 2027-04-01 | 1,401 | 1,197 | 1,163 | **238** | **204** | **959** |
| End state | 1,401 | 1,197 | 1,163 | 238 | 204 | 959 |

The recorded 238/204/959 is **arithmetically correct and describes 2027-04-01 onward**. Stated in
the present tense it is wrong: a class list seeded from it today would carry 204 codes no
jurisdiction has adopted and would have dropped 238 that are all still in force.

`31_migration_asof.py` prints these three numbers **after** its per-date loop, from whichever date
ran last — so with default arguments it silently reports the end state under no date label at all.
`32_asof_recount.py` reports them per date.

---

## 5. F4 — the rate-driven set holds across dates; the 383/78 does not, and the count was two short

**The headline scope number survives the as-of test as a set, not just as a count — and then fails
a different test.**

| Measurement | Groups | RATE_DRIVEN | CAPTURE | Aggregators |
|---|---|---|---|---|
| All 572 package directories (as recorded) | 477 | **18** | **383** | **76** |
| As of today — 54 packages | 458 | **18** | 356 | 84 |
| As of 2027-04-01 — 54 packages | 476 | **18** | 376 | 82 |
| End state — 54 packages | 476 | **18** | 376 | 82 |

`25_rating_vs_capture.py` re-ran and reproduced its recorded figure over 572 directories exactly, so
the two measurements are sound and answer different questions. The recorded figure is a **union over
every edition ever filed**, including retired ones — which is the right question for *"what must the
engine ever be able to rate?"* and the wrong one for *"what is in force?"*.

**The rate-driven groups are the identical set at all four measurements** — today, the cliff, the
end state, and the all-editions union. Verified by set comparison, not by matching counts.

### Amended later the same day: the set was 16 and should have been 18

Filed here rather than silently corrected, because it is the same *kind* of defect this document
exists to catalogue. **It is not an as-of defect** — everything above about date-stability holds.

`25_rating_vs_capture.py` decides *rate-driven* by matching the premium-writing rule body against a
list of rate-shaped source names: `FinalRate`, `BaseRate`, `LossCost`, `ELP`, `AdjustedBaseRate`.
**`AdjustedRate` was not on the list.** Two coverages compute

```
Premium = AdjustedRate × (ILF − DeductibleFactor) × PackageModFactor × ExperienceMod × …
```

and were filed as aggregators for that reason alone: **`GeneralLiabilityUnmannedAircraftCovABIPDCoverage`**
and **`GeneralLiabilityUnmannedAircraftCovBPAICoverage`**, 116 packages each. Re-run corpus-wide over
the same 572 directories with `AdjustedRate` added, **exactly two groups move**: `18 · 383 · 76`.

`GeneralLiabilityCompositeRating` also reads a rate-shaped name but is genuinely an aggregator —
`Premium = FinalCompositeRatingPremium − TotalClassificationsPremium` — so it stays in the 76. Read,
not pattern-matched.

**How it was found:** by asking why build-order item 7, *Unmanned Aircraft*, appeared in the build
order as a rating subline but owned no rate-driven group. The list of remaining gates and the list
of rate-driven groups disagreed, and the build order was right.

**What it means for N13.** The drone `0`-above-55-lb sentinel is the project's oldest confirmed
sentinel, and it sits on a path that the scope measurement had classified as *not rating*. The
sentinel register and the rating inventory were describing the same coverage and disagreeing about
whether it rates.

The rate-driven set is therefore **18**, and it includes the four state-specific coverages
(`…MarylandChangesLiabilityForHazardsOfLead…`, `…MassachusettsChangesLeadPoisoning…`,
`…MassachusettsChangesSupplementalCovLeadPoisoning…`, `…SpecialProtectiveHighwayCoverage`).

The capture side moves: 18 groups exist only in the end state, and 6 change verdict between today
and 2027 (four `OTHER → CAPTURE`, two `CAPTURE → OTHER`, all Texas/Oklahoma changes and exclusion
endorsements). **Phase 16, the capture harness, is sized 383 and should be sized 383 —** it must
handle every group the engine may meet — **but the in-force count on any given day is smaller, and
the phase-16 exit criterion should say which it means.**

---

## 6. F5 — the gates' table claims are edition-independent

All twelve countrywide rating tables the three gates cited as *"0 rows (header only)"* are
header-only in **every one of the ten countrywide editions**, 2020-12-01 through 2027-04-01. No
gate claim needed revising.

Their state-side row counts *are* dated, and one is worth correcting: gate 335 records
`OwnersContractorsELPText` as **433 rows across all 51**. That is the end state. **Today it is 563
rows across all 51** — the 2027 filings shrink it. The gate's corpus-wide N17 agreement test
(433/433) was run on end-state data; the conclusion holds, the row count is a 2027 figure.

### Four jurisdictions file loss costs under per-territory table names — and this was already known

Found while re-testing N7, stable at every as-of date — **and then found again in the register.**
**OI-20 recorded it on the comparison pass** and marked it *"sampled, not corpus-wide"*. It is now
measured corpus-wide and as-of, which is what OI-20 asked for, so this **closes OI-20** rather than
opening anything.

| Jurisdiction | Base table | Suffixed tables | Rows carried |
|---|---|---|---|
| CA | `PremOpsLossCost` header-only | 11 | 13,068 |
| NJ | `PremOpsLossCost` header-only | 15 | 17,805 |
| NJ | `PremOpsSizeOfRiskLossCost` header-only | 15 | 17,805 |
| NY | `PremOpsLossCost` header-only | 21 | 23,820 |
| OH | `PremOpsLossCost` header-only | 10 | 11,880 |
| OH | `PremOpsSizeOfRiskLossCost` header-only | 10 | 11,880 |

**`PremOpsLossCost` is populated in only 47 of 51 jurisdictions.** In CA, NJ, NY and OH the rows
are filed under `PremOpsLossCost<ST>Terr<nnn>` — one table per territory, **66,573 rows in total,
invisible to a reader that knows only the base name, and indistinguishable from a legitimately
empty table.** It does not track the territory scheme: CA and NY are county/place jurisdictions but
OH resolves by ZIP and NJ is one of the 27 ZIP-table states.

This is N7 with a sharper edge — *presence ≠ population*, **and absence of population ≠ absence of
data**. The load-time assertion *"no empty table in a rating path"* would fire on all four of these
and be wrong every time. **OI-20 closed**, and N7's statement extended to cover it.

OI-20 also predicted *"NY additionally ships an empty `PremOpsLossCost` shadow that a name-based
resolver would faithfully overlay to nothing."* Confirmed, and it is not only NY: **all four** leave
the base table present and empty. Under N3 — override by name, wholesale, and the replacement may be
empty — that empty state table is a *correct* wholesale override of an already-empty countrywide
table. The data was never in the base table at either layer.

---

## 7. Observation for the next gate — Liquor Liability (332)

Not a gate finding; recorded so the 332 gate can test it rather than rediscover it.

The Step 31 prediction is that liquor is entirely ELP-or-refer, from `LiquorELPText` carrying only
`Industry` and `Company`. **The table inventory corroborates it independently: there is no liquor
loss-cost table in the corpus at all.** Across all 51 as-of-today packages the liquor rate tables
are `LiquorELP` (51), `LiquorELPText` (51), `LiquorHomogeneityIndex` (51), `ILFLiquor` (50) and
`LiquorLiabGrade` (44). No name matching `Liquor*LossCost` exists in any jurisdiction at any
edition.

`LiquorELPText` also **doubles** at the cliff — 362 rows today, 744 from 2027-04-01 — so the 332
gate must state its as-of date before quoting any liquor count.

---

## 8. What this changes

| Claim on record | Status |
|---|---|
| Build plan §12, phase 3 exit: *"All 51 resolve — 27 ZIP, 20 constant, 4 by submitted county"* | ✅ **Confirmed as-of.** No change |
| `ERC-TER-001` | ✅ **Confirmed as-of.** No change |
| N7: *"138 of 272 countrywide rate tables are header-only"* | ⚠️ **Re-dated** to *"111 of 266 today; 138 of 272 from 2027-04-01"* |
| OI-19: *"verified for one edition only"* | ✅ **Sweep done**, all ten editions. Ready to close |
| README #4: *"retiring 238 class codes and introducing 204"* | ⚠️ **Already correctly tensed** ("On 2027-04-01…"). Adding the 1,197-today figure makes it concrete |
| Build plan §3/§13, README #5: *"16 · 383 · 78"* | ⚠️ **Re-framed** as an all-editions union, **and corrected to `18 · 383 · 76`** — the classifier omitted `AdjustedRate` (§5). Date-stability of the set is confirmed |
| Gates 334/336/335 §5 countrywide `0 rows` | ✅ **Confirmed across all ten countrywide editions** |
| Gate 335: `OwnersContractorsELPText` *"433 rows"* | ⚠️ **End-state figure.** 563 today |
| *"the countrywide parent"* (singular, anywhere) | ❌ **Never singular.** Three parents in force today, three at the cliff |

**Closed:** **OI-40** (this audit) · **OI-19** (the ten-edition sweep it asked for) · **OI-20**
(sharded loss-cost tables, now measured corpus-wide and as-of instead of sampled).
**New:** **OI-41** — the corpus has an as-of floor of 2022-09-01.

---

## 9. What this pass says about the method

**The as-of defect was one instance of a wider one.** Of the five figures re-tested, only two were
wrong *because of the as-of date*. The Delaware miss, the three countrywide parents in force on a
single day, and the four jurisdictions filing loss costs under suffixed names are all the same
error in different clothing: **a name was trusted where a file should have been read.** N4 is a
special case of the standing criterion, not a separate rule.

**Two of the four figures were right, and that is worth saying plainly.** OI-40 was opened on the
assumption that everything measured with "latest" was suspect. Territory was not, and the
rate-driven set was not — verified as a set, at four different dates. The audit was still worth
running: it is what turned *"probably unaffected"* into *"measured"*, and it found three things
nobody was looking for.

**And "measured" is not "correct".** The rate-driven set passed every as-of test in this document
and was still two groups short, because both the original measurement and the re-test shared a
classifier whose rate-source list was incomplete. That is exactly the failure named in
[`RECONCILIATION.md`](RECONCILIATION.md) §1 — *"both sources agree" is not the same as "both sources
are right"* — reproduced here by re-testing a figure with the same instrument that produced it.
**A re-test that reuses the original method can only find dating errors, never method errors.** The
two Unmanned Aircraft coverages were found by a different route entirely: comparing the build order
against the rate-driven list and asking why they disagreed.

**The rediscovery count is now six, and two of them are in this document.** After the territory
definitions, the reproducibility gap, the rating plans and the migration framing:

- **`knowledge/territory.json`'s own `_note`** records that the scheme classification was
  *"CORRECTED 2026-08-10"* — by hand, with no script behind it. That note was the warning that a
  phase-3 exit criterion had no reproducible derivation, and it was read today only because it was
  in the way.
- **OI-20 already held the sharded-table finding**, complete with the NY empty-shadow prediction,
  and marked itself *"sampled, not corpus-wide"*. It was re-derived from the files before the
  register was read.

The pattern is stable enough to name: **this project's fastest source of new findings is its own
back-catalogue of unfinished ones.** Both were items that said, in writing, that they were
incomplete. A pass over every `AUDIT`-status item asking only *"has the sweep this asked for
actually been run?"* would likely be cheaper than the gate that rediscovers each one.
