# Gate — Size-Of-Risk rating (build-order item 8)

**Filed 2026-08-12. Eighth gate**, and the first that is **not** a subline. Differential against
[334](GATE-334-PREMISES-OPERATIONS.md), [336](GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md),
[335 OCP](GATE-335-OWNERS-CONTRACTORS-PROTECTIVE.md), [332](GATE-332-LIQUOR-LIABILITY.md),
[335 Railroad](GATE-335-RAILROAD-PROTECTIVE.md), [365](GATE-365-WITHDRAWAL-LOED-CYBER.md) and
[370](GATE-370-UNMANNED-AIRCRAFT.md).

**As-of date: 2026-08-12.** Required, not assumed (N4). Derived against **`GL_CW_20231201_V03`**,
with every countrywide claim re-checked against **all three declared parents** in force at that
date — `GL_CW_20231201_V02` (California alone), `GL_CW_20231201_V03`, `GL_CW_20260101_V01`.

Measured by [`scripts/erc/35_census_sizeofrisk.py`](../../scripts/erc/35_census_sizeofrisk.py) and
[`scripts/erc/36_manual_sweep.py`](../../scripts/erc/36_manual_sweep.py), both of which require an
enumerated population before they will state a count (habit 8).

---

## 0. The manual has nothing to say about this, and that is the finding

Every gate so far was **differential against a manual rule**: 334 against Rule 56, 370 against
Rule 37 Table 37.E, 332 against Rule 45. Size-of-risk has no such anchor.

> **Corrected the same day — read this before the table.** The first version of this section
> reported *"187 of 1,030 documents have no text layer"* and bounded the claim at 82% of the corpus,
> filing **OI-51** to close the residual with OCR. **That diagnosis was wrong.** Those documents are
> not image-only: this build of `pdftotext` returns **zero bytes** on them and `pypdf` reads them in
> full — `GL-CT-2026-LC-001-C` gives 0 bytes against **218,978**. The project's own
> `scripts/02_extract_dualmode_losscosts.py` had carried that fallback since 2026-08-10;
> `36_manual_sweep.py` did not, and nothing compared the two. **A tool's silence was accepted as the
> corpus's silence** — habit 8 with the *tool*, rather than a query, defining the population. The
> sweep is now dual-mode and **OI-51 is closed as a wrong diagnosis**. The conclusion below is
> unchanged and much better supported.

| | |
|---|---|
| Documents enumerated | **1,030** pdfs under `Commercial Line Manuals/` — every file, not the rules manuals |
| Matching `size[\s-]*of[\s-]*risk` | **0** |
| Carried a text layer, dual-mode | **1,028 of 1,030** |
| Failed both extractors | **2** |

So the claim is nearly unqualified:

> **Of the 1,028 manual documents that can be read, none mentions size-of-risk. Two fail both
> extractors.**

Independently corroborated: the `iso-circular-expert` agent's own text corpus — extracted months
earlier, by a different pipeline — returns **0 of 975**.

*(**The corpus was growing while this was written.** A `Composite Rating` folder appeared during the
session and reached **90** documents, taking the total from 1,030 to **1,120**. The sweep was re-run
at each observed size — **0 of 1,030, 0 of 1,066, 0 of 1,120** — and the by-family breakdown shows
`Composite Rating 0 of 90`. The finding is stable under a moving denominator, which is the only
reason it can be stated at all while the corpus is in motion.)*

**This inverts the evidence hierarchy for item 8.** §1's tier-2 `confirm/` register — manual
citations that confirm an ERC meaning — has **nothing to register here**. Item 8 is the first
rating apparatus in the project that ERC must be trusted on alone, and every sentinel it contains
therefore lands in `escalate/` rather than `confirm/`.

### Two near-misses worth recording, because both are habit 8 again

1. **A truncated list was allowed to define a population.** An earlier draft said *"every
   unsearchable document is a loss-cost circular"* — read off the sweep's printed list, **which
   truncates at 40**, and the first 40 are alphabetical. The real split was 103 rules manuals to 83
   loss-cost manuals. Fixed by making the script print a by-family breakdown every run.
2. **Then the whole category turned out not to exist** — see the correction above. The by-family
   breakdown was an honest fix to a number that should never have been produced.

**Neither was caught by re-reading the claim.** The first was caught by making the script say more;
the second by an unrelated task — ingesting the terrorism manuals — putting a second extractor's
output next to this one's.

---

## 1. The algorithm — CW 2023 V03 / 20260101

Size-of-risk is **not a subline**. It is a **rating mode** that alters two existing coverage
groups: `GeneralLiabilityClassificationPremOpsCoverage` and
`GeneralLiabilityClassificationProdsCompldOpsCoverage`. It has no coverage group, no `ErcProcess`
and no premium of its own.

**20 setter rules** in the countrywide package touch it — 10 per subline, exactly symmetric. Taking
Prem/Ops (Products/Completed Operations is the same chain with `ProdsCompldOps` substituted and its
own `Territory` in place of `PremisesOperationsTerritory`):

| # | Rule | What it does |
|---|---|---|
| 1 | `SetPremOpsLossCost` | **Branches on the flag.** `Yes` → `LookupPremOpsSizeOfRiskLossCost`; otherwise → `LookupPremOpsLossCost`. **A different table, not a different factor** |
| 2 | `SetPremOpsSizeOfRiskRelativityTableAssignment` | `LookupPremOpsSizeOfRiskRelativityTableAssignment`, keyed *(State, ClassCode)* → a table number (`101`…, `501`…) |
| 3 | `SetPremOpsExposureTimesThousand` | Quantises the exposure — see §4 |
| 4 | `SetPremOpsSizeOfRiskPreliminaryRelativity` | `LookupPremOpsSizeOfRiskRelativity`, keyed *(State, table number, quantised exposure)*. **Linearly interpolated** — see §3 |
| 5 | `SetPremOpsSizeOfRiskMinimumRelativity` | `LookupPremOpsSizeOfRiskMinimumRelativity`, keyed *(State, ClassCode)* |
| 6 | `SetPremOpsSizeOfRiskMaximumRelativity` | `LookupPremOpsSizeOfRiskMaximumRelativity`, keyed *(State, ClassCode)* |
| 7 | `SetPremOpsSizeOfRiskFinalRelativity` | `Choose`: prelim < min → **min**; prelim > max → **max**; otherwise → **prelim**. A two-sided clamp |
| 8 | `SetBasicLimitPremium` | Multiplies the final relativity in — **only on the `Yes` branch** |
| 9 | `SetMedicalPaymentsCharge` | Multiplies it in again, on its own `Yes` branch |
| 10 | `SetRatingIDStatCode` | The flag is a **lookup key**, not a condition — see §6 |

Plus **four dependent rules outside the two host groups**: `SetAdjustedBaseRate` in Loss Of
Electronic Data (Prem/Ops and Prods) and Cyber Incident Liability (Prem/Ops and Prods), each
reading `../GeneralLiabilityClassificationPremOpsCoverage/PremOpsSizeOfRiskFinalRelativity` across
the group boundary. **That is E18, and item 8 is the reason item 6 could not be built first.**

`AdjustedBaseRate = round(LossCost × LCM [× ClaimsMadeMultiplier] × SizeOfRiskFinalRelativity ×
FinalILF, 4)`.

`BasicLimitPremium = round(BaseRate × (1 − FinalDeductibleFactor) × SizeOfRiskFinalRelativity ×
PackageModFactor × exposure[÷1000 by basis], 0)`.

---

## 2. Size-of-risk swaps the loss cost table; it does not bolt a factor on the end

This is the structural finding, and it is what makes item 8 a build-order item rather than a
modifier in item 6.

`SetPremOpsLossCost` — the **first** rating step, before LCM, before the ILF — reads
`PremOpsSizeOfRiskLossCost` when the flag is `Yes` and `PremOpsLossCost` when it is not. **Two
different filed loss cost tables, with different keys.** The relativity that follows is a second,
independent change to the same chain.

Consequences the architecture has to carry:

1. **Size-of-risk is not composable as a post-multiplier.** An engine that computes the ordinary
   premium and then applies a relativity gets the wrong loss cost and therefore the wrong premium.
2. **The two tables are keyed alike but populated differently** — both *(State, Territory, Class)*,
   and §9 shows 188 classes carry a `0` in the size-of-risk table.
3. **The mode is per-policy, not per-coverage.** `SizeOfRiskRatingApplies` sits at policy level
   (`../../../../../`), so it switches the loss cost source for **every** Prem/Ops and
   Products/Completed Operations classification on the policy at once.

---

## 3. Linear interpolation — the first in the project, and it is real

`PremOpsSizeOfRiskRelativityDef.RateTableDef.xml` declares:

```xml
<rt:Range Name="Relativity" RangeKeyCol="PremOpsExposureTimesThousand"
          InterpolateMode="Linear" Type="decimal">
  <rt:ValueCol Name="Relativity_From" />
  <rt:ValueCol Name="Relativity_ToLessThan" />
</rt:Range>
```

The relativity is **not looked up**. It is interpolated across the exposure band:

```
frac       = (key − Exposure_From) / (Exposure_ToLessThan − Exposure_From)
Relativity = round(Relativity_From + frac × (Relativity_ToLessThan − Relativity_From), 4)
```

**How rare this is, enumerated rather than asserted:**

| | |
|---|---|
| Rate table definitions across all 61 packages (10 countrywide + 51 resolved jurisdictions) | **4,551** |
| Carrying an `InterpolateMode` value range | **16** |
| Of those 16, size-of-risk relativity | **16** |

**Every interpolated table in the corpus is a size-of-risk relativity table, and no jurisdiction
ships one of its own** — the 16 are `PremOpsSizeOfRiskRelativity` and
`ProdsCompldOpsSizeOfRiskRelativity` in the 8 countrywide packages that populate them.

**It does real work, so it cannot be simplified to a step function:**

| | Prem/Ops | Prods/CompldOps |
|---|---|---|
| Rows | 8,330 | 4,214 |
| Rows where `Relativity_From ≠ Relativity_ToLessThan` | **8,148 of 8,330** | **4,074 of 4,214** |
| Distinct band widths | 15 (1,000 → 250,000,000) | 15 |
| Distinct assignment tables | 85 | 43 |

**The open-ended top band is safe, and that was checked rather than assumed.** 85 of 85 Prem/Ops
and 43 of 43 Prods top bands run `[500,000,000, 2⁶³)` with `Relativity_From == Relativity_ToLessThan`,
so interpolating across an effectively infinite band cannot collapse the relativity toward the
lower edge. **If a future edition ever files an unequal pair on the `2⁶³` band, the interpolation
formula silently returns `Relativity_From` for every large risk** — that is a load-time assertion
the engine owes, not a runtime check.

**`2⁶³ = 9,223,372,036,854,775,808` is a filed sentinel for "no upper bound".** A first pass at
counting band alignment reported *"8,245 of 8,330 edges are multiples of 1,000"*; the 85 exceptions
were all the sentinel. Re-enumerated excluding it: **0 of 8,330 real edges is misaligned.**

---

## 4. The exposure key is quantised, and the quantisation is the interpolation's input

`SetPremOpsExposureTimesThousand`, on the `Yes` branch, splits on premium basis:

| Premium basis | Key |
|---|---|
| `Admissions` · `Area` · `Gallons` · `Gross Sales` · `Passenger Days` · `Payroll` · `Total Cost` · `Total Operating Expenses` · `Vehicles` — **9 values** | `long(long(exposure) ÷ 1000) × 1000` — **integer division, floored to the nearest 1,000** |
| anything else | `long(exposure) × 1000` |
| flag not `Yes` | `0` |

Both arms produce a multiple of 1,000, always. The bands are aligned to multiples of 1,000 (§3), so
the key never lands mid-step of a 1,000-wide band — but bands widen to 250,000,000, and inside those
the key lands at 1/250,000th, 2/250,000th … of the way across. **The interpolation is live for
every band wider than 1,000, which is most of them.**

**Two traps for the engine:**

1. **`Convert Type="long"` truncates toward zero; it does not round.** An exposure of `4,999`
   under `Gross Sales` gives a key of `4,000`, not `5,000`. Under N10 this must be a `Decimal`
   floor, never a float cast.
2. **The nine-value list is a filed enumeration, not "the bases that are money".** `Vehicles` is a
   unit count and is in the ÷1000 arm; a basis absent from the list is multiplied by 1,000 instead.
   Hardcoding "divide when the basis is monetary" gets `Vehicles` wrong in one direction and any
   future basis wrong in the other. **The same nine-value list appears again in `SetBasicLimitPremium`
   to decide the ÷1000, and the two must be read as one list from one place.**

---

## 5. The clamp, and where a `0` can and cannot reach

`SetPremOpsSizeOfRiskFinalRelativity` is a three-way `Choose` with no null handling of its own,
because each input has already been defaulted to `0.0`.

**The good news first, and it is unusual for this project: the sentinel is guarded.** Every one of
the ten setters, and both consumers (`SetBasicLimitPremium`, `SetMedicalPaymentsCharge`), tests
`SizeOfRiskRatingApplies == "Yes"` before the relativity is read *or* multiplied. So the
`Else → 0.0` default that runs when size-of-risk does **not** apply can never reach a premium.
**Contrast gate 370**, where the drone modifiers multiply unguarded.

**The bad news: the guard is on the flag, not on the value.** When the flag *is* `Yes` and the data
is missing, the zeros multiply:

| Failure | Preliminary | Min | Max | Final | Effect |
|---|---|---|---|---|---|
| Class code has no relativity table assignment | `0.0` (guard `assignment != ""` fails) | `0.0` | `0.0` | **`0.0`** | **BasicLimitPremium = 0** |
| Exposure quantises to `0` (exposure < 1,000 on a ÷1000 basis) | `0.0` (guard `exposure > 0` fails) | real | real | **min** | premium at the floor |
| Relativity tables empty in the parent edition | `0.0` | `0.0` | `0.0` | **`0.0`** | **BasicLimitPremium = 0** |

Row 2 is the clamp doing its job — a sub-1,000 exposure floors to the filed minimum relativity,
which is almost certainly intended. **Rows 1 and 3 are silent zero premiums**, and row 1 has a live
instance (§10).

**And there is no discriminator anywhere in the corpus.** Enumerated, not sampled:

| | |
|---|---|
| `DoMessage*` validation rules in the countrywide package | **110** — **0** reference size-of-risk |
| `DoMessage*` rules across all 51 resolved jurisdiction packages | **278** — **0** reference size-of-risk |

**Same verdict as gate 370: this sentinel is a `escalate/` register entry, not a scan.** N13's
defence applies — any size-of-risk relativity resolving to `0` while the flag is `Yes` must raise
`REFER` before it multiplies.

---

## 6. `SizeOfRiskRatingApplies` is a fourth submission requirement — and its domain is filed in an odd place

> **Corrected 2026-08-12, later the same day.** This section said the flag has *"no writer: 0 rules
> in the corpus assign it."* **That was measured on the countrywide package only** — habit 8 with
> the parent package, rather than a query, defining the population. Re-measured across all **61**
> packages: **2 writers**, and they matter. See §6a.

The flag is a **policy-level input with no countrywide writer**: 0 of the countrywide package's
rules assign it, and it does not appear in any of its **417** domain tables.

That looked at first like a free string — `xs:string`, `length = 15`, compared literally to `"Yes"`,
so `"yes"`, `"Y"` or an empty value would silently turn size-of-risk off. **Checking before
claiming found the domain, filed somewhere else entirely.**

`SetRatingIDStatCode` is the one place the flag is a **lookup key** rather than a condition, and
`RatingIdentificationCode.RateTable.csv` enumerates it exhaustively — **4 rows, 2 of 2 values**:

| StateCode | ExperienceOrScheduleRated | SizeOfRiskRatingApplies | Code |
|---|---|---|---|
| CW | Yes | No | `1` |
| CW | Yes | Yes | `2` |
| CW | No | Yes | `8` |
| CW | No | No | `9` |

**So the filed domain is `{Yes, No}` and it is closed** — carried by a rate table because ERC has
no domain table for it. Three things follow:

1. **This is the fourth input that is a question for the broker**, after county/place for CA-FL-NY-TX
   (OI-34), `WorkersCompensationRate` for OCP, and the three drone axes (OI-48). The pattern named at
   Step 39 holds a fourth time: **what looked like missing data was a question ERC already knows how
   to ask.**
2. **N14 applies and needs a source.** "Validate every enumerated input against its domain table"
   has no domain table here — the engine must validate against the **stat code table's key column**.
3. **The one asymmetry in the corpus is correct, and it took reading the table to know that.**
   Of **30** comparisons of the flag across the countrywide package, **28 test `== "Yes"` and 2 test
   `!= ""`** — both outliers being `SetRatingIDStatCode`, in both sublines. That is not a defect:
   the stat code is keyed on the flag, so `No` is a legitimate key and a presence test is the right
   guard. **A count of 28-vs-2 looked like a filed inconsistency and was not one.**

### 6a. California and New York switch size-of-risk off by rule

Enumerated across all 61 packages — 10 countrywide and 51 resolved jurisdictions — **2,160 rules
mention `SizeOfRiskRatingApplies` and exactly 2 write it:**

```
CA · SetSizeOfRiskRatingApplies:  <rul:Constant Type="string" ToDataDef="SizeOfRiskRatingApplies">No</rul:Constant>
NY · SetSizeOfRiskRatingApplies:  <rul:Constant Type="string" ToDataDef="SizeOfRiskRatingApplies">No</rul:Constant>
```

**Identical constant stubs, in the two jurisdictions and nowhere else.** So in California and New
York **size-of-risk rating is disabled by rule, whatever the submission says** — the broker input is
overwritten before it is read. Both also override `ErcSetRatesAndFactors`, and neither ships a
size-of-risk loss cost, which is now explained rather than merely observed.

**This splits §7's sixteen cleanly, and the split is the difference between safe and dangerous:**

| | Jurisdictions | Behaviour on `SizeOfRiskRatingApplies = "Yes"` |
|---|---|---|
| **Disabled by rule** | **2** — CA, NY | The stub writes `No`; the ordinary loss cost path runs. **Correct, and safe** |
| **Silently unpriceable** | **14** — AR DE FL GA IL KY LA MA MN NM NV PR SC TX | **0 size-of-risk rules overridden** — they inherit the whole countrywide chain and simply have no loss costs. `PremOpsLossCost` is never assigned. **Must refer** |

**The engine's obligation narrows accordingly:** the resolve-time referral in §12 item 6 applies to
**14 of 51**, not 16, and CA and NY need no special handling because ERC already does it. **It also
confirms that the constant-stub override is a filed idiom, not an accident** — N3's third form,
after the empty body and the neutralising stub that gate 332 found in New York's claims-made liquor.

**A missing or off-domain flag loses the statistical rating identification code as well as the
rating mode** — `RatingIDStatCode` is left null, with no message. That is a reporting defect, not a
premium defect, and it is the engine's to guard.

---

## 7. Who ships size-of-risk — 35 of 51, and the 16 that do not are unpriceable

**No countrywide parent carries a single size-of-risk loss cost row: 3 of 3 have 0.** The algorithm
is countrywide, the loss costs are the jurisdiction's — N8, again, and stricter than usual, because
here the countrywide fallback row does not exist either.

| | |
|---|---|
| Jurisdictions resolved as of 2026-08-12 | **51 of 51** |
| Shipping size-of-risk loss cost **rows** | **35** |
| Shipping none | **16** — AR CA DE FL GA IL KY LA MA MN NM NV NY PR SC TX |

**In those 16, a submission with `SizeOfRiskRatingApplies = "Yes"` has no loss cost at all.** Both
arms of the `FirstNonNull` (state row, then `"CW"` row) miss, so `PremOpsLossCost` is never
assigned — not zero, *absent*. **This is the one place in item 8 where the failure is loud rather
than silent**, and the engine must convert it to a `REFER` at resolve time rather than letting a
null propagate into `SetBaseRate`.

**It is not a coincidence that CA, FL, NY and TX are among them** — the four OI-34
county/place jurisdictions — but 16 is not 4, and no claim is made that the two sets are related.

---

## 8. The binding lives in the **setter**, not the table name — New Jersey and Ohio

This is the trap the Step 38 handoff predicted, and it is worse than the handoff said.

| | |
|---|---|
| Shipping jurisdictions | **35** |
| Sharding one subline's loss cost across more than one table name | **2** — NJ (`PremOps × 15`), OH (`PremOps × 10`) |
| Overriding a loss-cost **setter** | **2 of 2** — the same two, `SetPremOpsLossCost` |
| Overriding a size-of-risk **lookup** rule | **0** |

**New Jersey does not override `LookupPremOpsSizeOfRiskLossCost`.** It overrides
`SetPremOpsLossCost` and replaces the single call with a hand-written `Choose` over
`PremisesOperationsTerritory` dispatching to 15 territory-specific lookup rules,
`LookupPremOpsSizeOfRiskLossCost501` … `517`. Ohio does the same with 10.

```
Choose
  When SizeOfRiskRatingApplies == "Yes" ─ Choose
                                            When Terr == "501" → LookupPremOpsSizeOfRiskLossCost501
                                            …  15 territories, NO Otherwise
  When Terr == "501" → LookupPremOpsLossCost001        ← the ordinary path, same 15 territories
  …
  Otherwise → PremOpsLossCost = 0.0
```

**So three bindings that an engine might reasonably use are all wrong:**

| Binding | Why it fails |
|---|---|
| concept → **table name** | NJ's table is `…LossCostTerr501`, not `…LossCost` |
| concept → **lookup rule name** | NJ defines 15 new names and overrides none of the parent's |
| concept → **setter rule**, resolved in the jurisdiction package | **correct** — this is the only one that survives all 35 |

**The asymmetry inside NJ's own rule is worth naming.** The size-of-risk `Choose` has **no
`Otherwise`**; the ordinary one falls through to `0.0`. Both enumerate the same 15 territories
(`501`–`509`, `511`–`513`, `515`–`517`; `510` and `514` are absent from both, and from NJ's
territory scheme). So an unknown territory leaves `PremOpsLossCost` **null** on the size-of-risk
path and **`0.0`** on the ordinary one. **Under this project's rules the size-of-risk branch is the
safer of the two** — a null is a loud failure, a `0.0` is N13's silent one — and the engine should
not "fix" the missing `Otherwise` by copying the neighbour.

**A numbering collision to guard against:** NJ's shard suffixes (`501`…`517`) are **territories**,
while the Products/Completed Operations relativity **table assignments** are also numbered `501`…
Two different `501` in one subsystem.

---

## 9. 188 classes carry a `0` size-of-risk loss cost, and the set is identical in every state

| | |
|---|---|
| Size-of-risk loss cost cells across the 35 shipping jurisdictions | **167,442** |
| Cells equal to `0` | **45,812 (27.4%)** |
| Distinct class codes carrying a `0`, per jurisdiction | **188 of 1,188 (15.8%)** |
| Jurisdictions where that 188-class set is **identical** | **all of them** (KS is 189 — see §10) |

The 27.4% cell figure is inflated by territory count (a state with 11 territory blocks repeats each
class 11 times); **the load-bearing number is 188 of 1,188 classes, and it is a countrywide
statement expressed 35 times.**

**This is a new entry in the zero taxonomy and its meaning is not yet established.** It is one of:
a class ISO will not size-of-risk rate; a class whose size-of-risk loss cost is genuinely zero; or
a placeholder. **The manual cannot arbitrate it (§0) and no `DoMessage*` guard exists (§5)** — so
under the evidence hierarchy it is an escalation, **E19**, not a decision. What can be stated:
these 188 classes **do** have relativity table assignments and min/max relativities, so the zero is
in the loss cost alone, and the resulting premium is `0` rather than a referral.

---

## 10. One filed defect — Kansas classes 10211 / 10212

`KS PremOpsSizeOfRiskLossCost` has **2,376 rows = 2 territories × 1,188 classes**, but **1,189
distinct class codes**:

| Territory | Class | Loss cost |
|---|---|---|
| `501` | `10211` | `0` |
| `502` | `10212` | `0` |

Every other class appears in both territory blocks; these two appear in one each. **`10212` is not
in any declared parent's `PremOpsSizeOfRiskRelativityTableAssignment`** — checked against all three
(`GL_CW_20231201_V02`, `V03`, `GL_CW_20260101_V01`), whose 1,188-class sets are identical, and
against KS's own package, which overrides no size-of-risk table or rule.

**So a Kansas territory-502 risk on class `10212` with the flag set takes §5's row 1: no assignment
→ preliminary, min and max all `0` → final `0` → basic limit premium `0`.** The practical impact is
nil because the loss cost is `0` anyway, and the two paths to zero are independent.

**This is an ISO filing inconsistency to raise upstream, not to patch** — the OI-43 precedent.
Recorded as **OI-52**. It is 1 of 70 (jurisdiction, subline) size-of-risk loss cost tables; the
other **69 of 70** have every class code assigned.

---

## 11. Two countrywide editions strip the apparatus, and one of them is coming

Measured across all **10** countrywide packages, not the three in force:

| Package | TableAssignment | Relativity | Minimum | Maximum | LossCost |
|---|---|---|---|---|---|
| `GL CW 20201201 V01` · `20210801 V01` · `20220901 V02` | 0 | 0 | 0 | 0 | 0 |
| `20230401 V01` · `20230501 V01` · `20231201 V01` · **`20231201 V02`** · **`20231201 V03`** · **`20260101 V01`** | 2,376 | 12,544 | 2,376 | 2,376 | 0 |
| **`GL CW 20270401 V01`** | **0** | **12,544** | **0** | **0** | 0 |

**The 2027-04-01 edition keeps the relativity tables and drops the assignment, minimum and maximum
tables.** Under §5 that is failure row 3 for every risk: no assignment → preliminary `0`, and no
min/max to clamp it back up → **final relativity `0` → basic limit premium `0`, silently, for every
size-of-risk risk in every jurisdiction that migrates.**

**Whether that is a withdrawal of size-of-risk rating or an incomplete filing cannot be settled
from the corpus** — the same three-way ambiguity as §9, and the manual is silent (§0). Recorded as
**OI-53**, and it is **dated**: it binds when the first jurisdiction declares `GL_CW_20270401_V01`
as its parent. As of 2026-08-12, **0 of 51 do**.

**This also corrects OI-04.** That item recorded *"the `Maximum`/`Minimum` relativity and
`TableAssignment` tables are 0 rows countrywide; source unknown"* — an undated claim, true of the
2020–2022 editions and of 2027-04-01, and **false of all three parents in force**, where they carry
1,188 rows each. The rows were never missing; the claim had no as-of date. **OI-40's discipline,
applied one item later than it should have been.**

---

## 12. What the engine owes

1. **A `SizeOfRisk` rating mode, not a factor.** It selects the loss cost source in
   `SetPremOpsLossCost` / `SetProdsCompldOpsLossCost` and contributes a relativity at
   `SetBasicLimitPremium`, `SetMedicalPaymentsCharge` and the four dependent `SetAdjustedBaseRate`
   rules. Both effects, or neither.
2. **A linear-interpolating range lookup** — a new table capability, used by 16 of 4,551 table
   definitions and by nothing else. `Decimal` throughout (N10), `round(…, 4)` at the end.
3. **A load-time assertion that every `2⁶³` top band has `Relativity_From == Relativity_ToLessThan`.**
   Currently 128 of 128; if it ever fails, interpolation silently under-rates every large risk.
4. **Exposure quantisation from the filed nine-basis list, read once and shared** by
   `*ExposureTimesThousand` and `SetBasicLimitPremium`. Floor, not round.
5. **A confirmed-sentinel entry (N13):** a `0` final relativity while the flag is `Yes` is a
   `REFER`, because 0 of 388 `DoMessage*` rules will catch it.
6. **A resolve-time referral for the 14 jurisdictions that inherit the chain and have no loss
   costs**, raised before rating rather than as a null-propagation failure. **California and New
   York are not among them** — they disable the mode by rule (§6a).
7. **Binding by resolved setter rule**, never by table or lookup name — the only binding that
   survives NJ and OH.
8. **Validation of `SizeOfRiskRatingApplies` against `{Yes, No}`**, sourced from
   `RatingIdentificationCode`'s key column, and a `RatingIDStatCode` that is never silently null.
9. **Item 8 unblocks item 6.** `PremOpsSizeOfRiskFinalRelativity` is E18's cross-group read; Loss
   Of Electronic Data and Cyber cannot be built until it exists.

---

## 13. Register changes

| | |
|---|---|
| **E19** *(new)* | The 188-class zero size-of-risk loss cost — meaning unestablished, manual silent, no guard (§9) |
| ~~**OI-51**~~ | **Withdrawn the same day.** The 187 "image-only" documents were a `pdftotext` failure, not missing text. Dual-mode: **1,028 of 1,030** readable, 2 fail. Superseded by **OI-55**, the real corpus gap (§0) |
| **OI-52** *(new)* | Kansas `10211`/`10212` class-code inconsistency — raise upstream, do not patch (§10) |
| **OI-53** *(new)* | `GL_CW_20270401_V01` strips assignment/min/max; binds when a jurisdiction adopts it (§11) |
| **OI-04** | **Corrected and closed.** Its open clause was an undated count that is false of all three parents in force (§11) |
| **OI-20** | Confirmed a second time, in a sharper form: the sharding is in the **setter**, not the table (§8) |
| **N13** | Eighth meaning of `0` added (§9); the size-of-risk guard pattern recorded as the **guarded** counterexample to 370 (§5) |
| **N14** | Needs a source when no domain table exists — here, a rate table's key column (§6) |

---

## 14. Verification

| | |
|---|---|
| `scripts/erc/35_census_sizeofrisk.py 20260812` | **5/5 checks pass** |
| `scripts/erc/36_manual_sweep.py` | 1,030 of 1,030 documents classified, dual-mode; 1,028 readable |
| `scripts/erc/34_crosscheck.py 20260812` | 4/4 |
| `tests/verify_golden.py` | 80/80 |

**Two habit-8 catches inside this gate itself**, both by a script rather than by re-reading:
the truncated unsearchable-document list (§0), and the `2⁶³` sentinel inflating a band-alignment
count (§3). Neither was found by inspection.
