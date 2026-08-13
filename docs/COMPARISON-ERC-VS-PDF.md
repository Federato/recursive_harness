# Two Derivations of the Same Program — ISO GL, PDF Manuals vs ERC Packages

> **Reconciliation note, 2026-08-11.** This document was derived before the ERC work and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](gates/RECONCILIATION.md) (items R1, R2, R3, R4, R6, R7). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

An independent comparison of **Derivation A** (`docs/rating-engine/`, from 975 PDF notices in
`Commercial Line Manuals\GL\`) and **Derivation B** (`docs/erc/`, from 567 ERC packages in
`C:\Projects\ISO_ERC_Files\General_Liability\`).

I have no stake in either. B was produced in clean-room isolation from A, the PDF corpus and
the two bridge spreadsheets, and named no expected finding in its instructions. A came first
and is self-documented as fallible (`09-GAPS-AND-OPEN-QUESTIONS.md` §9.6); B corrected itself
once between report 1 and report 2 (`02-EDITIONS-AND-INTEGRITY.md` §4).

---

## 0. What I read, and what I checked myself

**Derivation A, read in full:** `README.md`, `00-OVERVIEW.md`, `02-CW-BASE-RULEBOOK.md`,
`05-LOOKUP-TABLES.md`, `09-GAPS-AND-OPEN-QUESTIONS.md`, `11-RATING-ARCHITECTURE.md`,
`12-VERSIONING-AND-EDITIONS.md`, `13-LOSS-COSTS-AND-ELP.md`, and §8 of
`BUILD-PLAN-PLAIN-ENGLISH.md`. Not read: `01`, `03`, `04`, `06`, `07`, `08`, `10`, `A1`–`A4`,
`dataset.json`, `index.html`.

**Derivation B, read in full:** all six documents, `01`–`06`.

**Checked myself against the ERC corpus** (read-only; nothing written to
`C:\Projects\ISO_ERC_Files\`), using the packages directly plus B's own intermediate
`scripts\erc\out\territory_by_juris.csv`:

| # | Check | Result |
|---|---|---|
| C-1 | Jurisdictions shipping a ZIP→territory mapping | 27, **set-identical** to A's 27 |
| C-2 | Numeric territory codes per jurisdiction | histogram **identical** to A's |
| C-3 | Countrywide ILF / loss-cost / ELP table population | **0 data rows** in every countrywide edition |
| C-4 | Countrywide rate tables that are empty stubs | **138 of 272** in `GL CW 20270401 V01` |
| C-5 | Countrywide factor values vs A's transcribed tables | **exact match** on Tables 23.D.3, 40.C, 40.D, 40.E, 44.A.5.a.(5), and the Unmanned Aircraft charges |
| C-6 | Class-code churn `GL_CW_20260101_V01` → `GL_CW_20270401_V01` | **229 retired, 204 introduced** — A's exact figures |
| C-7 | `OwnersContractorsLossCost` presence per jurisdiction | 51/51 as of 2026-08-10; **8/51** in the latest (2027) packages |
| C-8 | ILTA encoding | digit and letter held in **two separate tables**, `Refer To Co.` sentinel present |
| C-9 | State package payload (AL 2027) | 27 tables, **exactly** A's state-operand set; no Liquor or Railroad loss cost |
| C-10 | Per-territory loss-cost sharding | CA, NJ, NY, OH use `PremOpsLossCost<JJ>Terr<nnn>`; NY also ships an **empty** `PremOpsLossCost` shadow |
| C-11 | Hawaii | absent from the ERC corpus, as from the PDF corpus |

Throughout: *"A states"* / *"B states"* is a report claim; *"I verified"* is my own run against
a corpus; *"I infer"* is neither.

---

## 1. Agreements

Ranked by how much independent weight each carries. For each I say whether the two are making
**the same claim** or merely similar-sounding ones — the distinction matters more than the
agreement.

### 1.1 The countrywide layer holds the algorithm and none of the money — SAME CLAIM, and now triply confirmed

**A states** (`00-OVERVIEW.md` §0.1, finding 1): CW Rule 56.B reads verbatim *"The increased
limits tables are displayed in the state exceptions."* There is no countrywide ILF table in
`GL-MU-2027-RU-001-C.pdf`, and no countrywide loss cost notice exists at all (0 of 472 files
are `MU`). A calls this *"the single most consequential architectural fact in the corpus"*
(`11-RATING-ARCHITECTURE.md` §11.9).

**B states** (`03-RATING-STRUCTURE.md` §4.2), reached from a completely different direction —
by cross-tabulating which tables every state overrides: *"loss costs, ELPs, homogeneity indices
and increased-limit factors are always state-supplied; the algorithm that consumes them is
always countrywide."* The 24 universally-overridden tables are exactly `ProdsCompldOpsLossCost`,
`ILFProds`, the ELP family, the homogeneity indices and the ILTAs.

**This is the same claim.** A read it from a rule's prose; B measured it from override
frequency across 51 jurisdictions.

**I verified it a third way, and the ERC encoding is stronger than either report says.** In
`countrywide/GL CW 20270401 V01/Rate Tables/`, `ILFPremOps.RateTable.csv`,
`ILFProds.RateTable.csv`, `PremOpsLossCost.RateTable.csv`, `ProdsCompldOpsLossCost.RateTable.csv`
and `PremOpsELP.RateTable.csv` all contain **a header line and zero data rows**. The same holds
in `GL CW 20260101 V01` and `GL CW 20231201 V02`. Every state package ships populated
counterparts (AL 2027: `ILFPremOps` 216 rows; NJ: 432). **138 of the 272 countrywide rate tables
are empty schema stubs.**

So ERC does not merely leave the numbers to the states — it declares the countrywide slot and
leaves it deliberately blank. That is Rule 56.B rendered as data.

### 1.2 The 27 ZIP-table jurisdictions — SAME CLAIM, exact set identity

**A states** (`05-LOOKUP-TABLES.md` §5.4.1): three territory-resolution schemes — ZIP table
(27), county/city (4: CA, FL, NY, TX), entire state (20) — with 23,719 ZIP rows in the latest
notices. This was A's *corrected* position after the G2 error (§9.6).

**B states** (`03-RATING-STRUCTURE.md` §5.2): *"Only 27 of 52 jurisdictions ship a ZIP→territory
mapping. In the other 25 the territory must be supplied by the user or determined outside ERC."*

**I verified the sets are identical.** From `territory_by_juris.csv`, the jurisdictions with
`n_zip_rows > 0` are AL, AZ, CO, CT, GA, IA, IL, IN, KS, KY, LA, MA, MD, MI, MN, MO, NE, NJ, OH,
OK, OR, PA, RI, TN, VA, WA, WI — **exactly** A's 27, with zero symmetric difference. CA, FL, NY
and TX have zero ZIP rows and territory codes that are county and place names
(`Alameda County Remainder`, `Broward County`, `Miami / Dade County`) — A's county/city scheme,
same four jurisdictions.

This is the single most impressive agreement in the exercise. A derived it from Territory Pages
in PDFs after having got it wrong once; B derived it from domain-table key columns without
knowing A existed. Two error-prone paths converging on the same 27-member set is strong
evidence both parses are right.

**Note also that B under-called its own finding.** B wrote that in the other 25 jurisdictions
"the territory must be supplied by the user or determined outside ERC — the corpus does not say
which." A answers it: 20 of those 25 are single-territory (`ENTIRE STATE … 001`, so there is
nothing to resolve) and 4 use county/city definitions.

> ### Verified and extended, 2026-08-10
>
> This paragraph was right, and it was **not carried forward** — `OPEN-ITEMS.md` OI-15 instead
> subtracted 4 from 25 and recorded "21 remain", and the build plan and PRD inherited that.
> Re-measured directly against ERC, prompted by a user hypothesis that such states simply
> default to `001` or `002`:
>
> - **20 single-territory jurisdictions confirmed** — AK, AR, DC, DE, ID, ME, MS, MT, NC, ND,
>   NH, NM, NV, PR, SC, SD, UT, VT, WV, WY. `PremOpsTerr` holds exactly one value across all
>   1,163–1,188 class codes. **19 use `001`; NC uses `002`** — the lone exception.
> - **The 4 county/place jurisdictions carry their tables in ERC too**, not only in the manuals
>   as this section implies: CA (11 codes / 21 place names), FL (5 / 8), NY (20 / 66),
>   TX (8 / 15). So no cross-source dependency exists for territory.
> - **The residue is zero.** All 51 jurisdictions resolve territory from ERC alone.
>
> This also explains B's "all 52 are multi-territory, minimum 4": that figure pooled distinct
> values across *every* geographic column. Verified `AK PremOpsTerr={001}`,
> `ProdsCompldOpsTerr={999}` — the "4" was `001` + `999` + two others.
>
> What remains is an **input** requirement, not a data gap: those four jurisdictions key on
> county/place, so an address must be resolved to one (OI-34).

### 1.3 Territory domains, jurisdiction by jurisdiction — SAME CLAIM, identical histogram

**A states** (`13-LOSS-COSTS-AND-ELP.md` §13.8) a full distribution: 20 jurisdictions with 1
territory, 9 with 2, 7 with 3, 5 with 4, 1 with 5, 1 with 7, 2 with 8, 1 with 9, 1 with 10,
2 with 11, 1 with 15, 1 with 20. Named: NY 20, NJ 15, CA 11, PA 11, OH 10, MA 9, CT 8, TX 8,
IL 7, FL 5.

**I verified against ERC** by counting distinct three-digit territory codes (excluding the
statewide sentinel `999`): NY 20, NJ 15, CA 11, PA 11, OH 10, MA 9, CT 8, TX 8, IL 7, FL 5, and
the full histogram `{1:20, 2:9, 3:7, 4:5, 5:1, 7:1, 8:2, 9:1, 10:1, 11:2, 15:1, 20:1}` — a
**perfect match**, including the shape of the tail.

A independent cross-check falls out of the row counts: every state `PremOpsLossCost` table has
exactly `classes × territories` rows (PA 12,793 = 1,163 × 11; TX 9,304 = 1,163 × 8; MA 10,692 =
1,188 × 9; IL 8,141 = 1,163 × 7; FL 5,940 = 1,188 × 5). A's territory counts and A's class
counts jointly predict ERC's row counts to the row.

A's own cross-corpus check (Rules `CG-T` pages vs loss-cost grids, 51/51 exact) is now a
*three*-corpus agreement.

### 1.4 Products/Completed Operations is not territory-rated — SAME CLAIM

**A states** (§13.8): Prod/CompOps is written to reserved statewide territory `999` in all 51
jurisdictions, so the key is `(class, 336, 999)` and *"a single composite key with a constant
would be wrong."*

**B states** (`03` §5.2): *"`ProdsCompldOpsTerr` has exactly ONE value corpus-wide: `999`.
Products/completed operations is keyed on territory but the key is degenerate."*

Same claim, same constant, opposite directions of discovery — A from a grid page header, B from
a value-vocabulary sweep of 45 million cells.

### 1.5 Class codes: 1,163 or 1,188, and a 229/204 revision — SAME EVENT, and B supplies the mechanism

**A states** (§13.4, §13.7): per-jurisdiction class totals are 1,163 or 1,188 (NJ 1,187,
NY 1,181); the 2027 filing **retires 229 class codes and introduces 204**; three independent
tests select the same 15/36 jurisdiction split.

**I verified in ERC**: `ClassificationType.RateTable.csv` holds **1,188** rows in
`GL CW 20260101 V01` and **1,163** in `GL CW 20270401 V01`; the set difference is **exactly 229
retired and 204 introduced**. NJ's latest package carries **1,187** — A's number to the code.
AL (2027 basis) carries 1,163; CA (older basis) 1,188.

Two derivations, two file formats, and the same three integers. B itself never ran this test —
B explicitly declined row-level cross-edition diffs (`02` §7) — so this is A's finding confirmed
against B's corpus rather than by B. See §2.3 for the one place the two genuinely differ.

### 1.6 The OCP/Principals-Protective loss-cost withdrawal — SAME EVENT

**A states** (§13.7): 390/390 notices through 2026 publish the OCP/PP loss cost table; only 22
of 58 2027 notices do. *"An engine that binds the OCP/PP loss cost table at build time will
silently lose Owners & Contractors Protective rating … the premium does not error, it changes."*

**I verified in ERC**: resolving each jurisdiction's package **as of 2026-08-10**, all 51 ship
`OwnersContractorsLossCost.RateTable.csv`. Resolving to the **latest** (2027-effective)
packages, only **8** still do — CA, FL, GA, MA, NJ, NV, NY, WA — the same 8 that still import a
pre-2027 countrywide package. AL's 2027 package ships `OwnersContractorsELP` and no
`OwnersContractorsLossCost`.

B never noticed this. It is a purely temporal finding and B did not diff table *contents*
across editions.

### 1.7 Liquor and Railroad Protective have no published loss cost — SAME CLAIM

**A states** (§13.3): Liquor Liability (332) **0/51** published loss costs, Railroad Protective
**0/51**; both are ELP-driven or refer-to-company. A flags this as a rating-mode correction to
its own §3.1.

**I verified in ERC**: the complete rate-table payload of `GL AL 20270401 V04` is 27 tables —
`PremOpsLossCost`, `ProdsCompldOpsLossCost`, the ELP/homogeneity families, `ILFLiquor`,
`ILFRailroad`, `ILFPremOps`, `ILFProds`, `ILFOwnersContractors`, both ILTAs, `LiquorLiabGrade`,
`ProductWithdrawalExpensesAndLiabilityIncrdLimitFactor`. There is `LiquorELP` (16 rows) and
`RailroadELP` (4 rows) and **no `LiquorLossCost` and no `RailroadLossCost` anywhere in the
corpus**. ERC ships increased-limit factors for coverages it ships no base rate for — exactly
A's picture.

B never asked which sublines lack a base rate. Its §2.1 subline inventory counts *presence*, not
*rateability*.

### 1.8 Countrywide factor tables, cell for cell — SAME VALUES

A transcribed several genuinely-countrywide tables from the CW manual. I checked each against
`countrywide/GL CW 20270401 V01/Rate Tables/`:

| A's table | A's values | ERC table | Match |
|---|---|---|---|
| 23.D.3 Increased Medical Payments | 1.007 / 1.011 / 1.014 / 1.016 and 1.011 / 1.017 / 1.022 / 1.026 | `IncreasedMedPayLimitFactor` (20 rows, 5 class groups × 4 limits) | **exact** |
| 40.C LoED `CG 04 37` | 0.0010 / 0.0030 / 0.0050 / 0.0070 | `LossOfElectronicDataPremOpsFactorCG0437` | **exact** |
| 40.D LoED `CG 04 71` | 0.0008 / 0.0024 / 0.0040 / 0.0056 | `LossOfElectronicDataPremOpsFactorCG0471` | **exact** |
| 40.E Cyber `CG 04 25` | 0.0010 / 0.0040 / 0.0070 / 0.0100 | `CyberIncidentLiabilityPremOpsFactors` | **exact** |
| 44.A.5.a.(5) Product Withdrawal | Expense 0.25/0.19/0.13, Liability 0.13/0.10/0.07 | `ProductWithdrawalExpensesFactor`, `ProductWithdrawalLiabilityFactor` | **exact** |
| Unmanned Aircraft charges | 66.11 / 110.19 / 154.26 / 220.37, PAI 87.63 | `UnmannedAircraftLimitedLiabilityBIPDLossCost`, `…PAILossCost` | **exact** |

This is the closest thing to ground truth available here: A read these off pages with a
documented history of silent misalignment defects (`13` §13.9), and every digit survives.

### 1.9 The ILTA composite code — SAME MECHANISM, and ERC states it structurally

**A states** (`02-CW-BASE-RULEBOOK.md` Rule 15, and `11` §11.9) that a state ILTA token like
`2B` is a composite: the digit selects the Premises/Operations table (1–3) and the letter selects
the Products/Completed-Operations table (A–C). A flags that this decoding *"is not stated in one
place in the manual — it is the join of Rule 15.D.2 with the state ILTA pages."*

**I verified in ERC**: the two halves live in two separate tables.
`PremOpsIncrdLimitTableAssignment` (AL, 1,163 rows) has values `1`/`2`/`3`; 
`IncreasedLimitsTableAssignmentProdsCompldOps` has `A`/`B`/`C`/`N/A`. Both carry the literal
sentinel `Refer To Co.`

A inferred the decomposition from prose; ERC ships it pre-decomposed. Neither derivation states
the correspondence, because neither could see both.

### 1.10 Refer-to-company is a first-class outcome, not an error — SAME CLAIM, different evidence

**A states**: `(a)` occupies 17.1% of loss-cost grid cells; five whole coverages (EDL, EBL,
Pollution, UST, Abuse) are specified except for price; referrals can be *input-conditional*
(Product Withdrawal Participation Percentage / Cut-off Date).

**B states** (`04` §1.3): three distinct triggers — the DOC `Refer to Company` sheet (5,300 rows,
591 form numbers), the `Refer To Co.` cell sentinel (1,153 cells), and an unpriced capture table.
*"The engine must treat 'refer to company' as a first-class outcome, not an error."*

**These are the same design conclusion from disjoint evidence.** They are *not* the same
measurement: A's 17.1% is a rate-cell statistic that has no ERC counterpart, and B's 5,300 DOC
rows have no PDF counterpart. Do not add them together.

### 1.11 Composition, not inheritance — SAME ARCHITECTURE

Both independently conclude that a jurisdiction is not a set of deltas over a usable base:
A because the base cannot rate (`12` §12.2), B because a state package is not independently
usable and 10.88% of state lookups hit a table that exists in both layers *and always differs*
(`03` §1.4). Both conclude: load countrywide, overlay the state by name, never merge rows.

B's version is quantitatively far stronger (0 identical shadows out of 374 contested lookups;
36 byte-identical of 21,694 overlaps). A's is stronger on *why* — the base is incomplete by
design, not merely overridden.

### 1.12 Smaller agreements

- **Hawaii is absent.** A: no `GL-HI-*` file in either corpus, 51 jurisdictions. B: 52
  jurisdiction codes = 51 + `CW`. I verified: no `HI` directory. Both treat it as a filing fact,
  not a download gap. Agreed and now three-way.
- **Effective dating must be as-of, not latest.** A (`12` §12.4) and B (`04` R4, 83
  future-effective packages) reach the same rule independently.
- **Numbers must never be coerced.** A: `–`, `(a)`, `Incl.`, `RTC` must stay typed, *"empty is
  not zero and `(a)` is not zero."* B: 16 sentinel tokens, limits are compound strings
  (`"1,000,000 CSL"` ≠ `"1,000,000"`), store every cell as text. Same principle, different
  vocabularies, neither corpus's tokens appear in the other.
- **Homogeneity/Reliability indices exist and are state-supplied.** A from ELP Procedures 3–4;
  B lists `PremOpsHomogeneityIndex` among the 24 universally-overridden tables.

---

## 2. Divergences, and how I adjudicate them

### 2.1 "8 sublines" vs "11 sublines" — vocabulary, not conflict

A counts **8** (`02` §2.4): the ISO *subline codes* 334, 336, 325, 332, 335, 350, 365, 370, and
explicitly warns that *"subline code is therefore not a primary key for a rating plan —
`(subline, coverage)` is"* because 335, 350 and 325 each carry two coverages.

B counts **11** (`03` §2.1): the resolved values of the `Subline` domain table — coverage-level
names, which split A's doubled codes apart (Owners and Contractors / Railroad; Pollution /
Underground Storage Tank) and add `Special Protective And Highway` (NY only) and standalone
`Premises/Operations`.

**Adjudication: not a disagreement.** B's 11 is close to A's `(subline, coverage)` pairs. But
one asymmetry is real: I verified the countrywide `DomainSubline.DomainTable.csv` has **9**
values and does **not** include Unmanned Aircraft, which A assigns subline code 370 and which
ERC rates through `UnmannedAircraft*` tables outside the subline taxonomy. So ERC's `Subline`
field is a *policy-structure* enumeration, not the statistical subline code. **Neither
derivation says this**, and anyone joining the two on "subline" will mis-join.

### 2.2 Is `ILFProds` "countrywide with state overrides" or "state-only"?

B classifies `ILFProds`, `ProdsCompldOpsLossCost` etc. as **universally-overridden** — i.e. the
countrywide parent has one and all 51 states replace it (`03` §4.2). A says flatly there is **no
countrywide ILF table**.

**Adjudication: A is right on substance; B's classification is technically true and materially
misleading.** I verified the countrywide `ILFPremOps`, `ILFProds`, `PremOpsLossCost`,
`ProdsCompldOpsLossCost` and `PremOpsELP` all have **zero data rows**. There *is* a countrywide
table; it contains nothing. B measured override relationships at the level of table *names* and
never measured table *population*, so 138 empty countrywide stubs are counted as content
throughout B's analysis — including in "a median of **485** tables exist only countrywide"
(`02` §1.4) and "resolved coverages ≥ 215 per jurisdiction" (`06` A-RS-02). Those figures
overstate the resolved content by an unmeasured margin.

This is a genuine defect in B, and it is the kind only cross-reading exposes: B's method
(structural measurement, no domain knowledge admitted) had no reason to ask whether a table was
empty, because emptiness is not a structural anomaly.

### 2.3 The vintage split: A's 15/36 vs ERC's 8/43

A reports 15 jurisdictions on the pre-2027 rate basis and 36 migrated, with three tests agreeing.

I resolved ERC the same way: taking each jurisdiction's **latest** package, 8 remain on a
pre-2027 countrywide parent (CA, FL, GA, MA, NJ, NV, NY, WA) and 43 are on
`GL_CW_20270401_V01`. Overlap with A's 15 is only 6 (CA, GA, MA, NJ, NY, WA).

**Adjudication: neither is wrong; the membership is a snapshot artifact and the *mechanism* is
what agrees.** Both corpora contain the same filing (229 retired / 204 new class codes, OCP loss
cost withdrawn, §1.5–1.6). They differ in which jurisdictions' 2027 filings had landed in each
download. Resolving ERC **as of 2026-08-10** puts *zero* jurisdictions on the 2027 basis and
51/51 still publishing the OCP loss cost — consistent with A's own statement that every notice
through 2026 carries it.

**Where ERC settles something A could not:** A modelled this as a state loss-cost filing rolling
out state by state, because there is no countrywide loss-cost notice to attribute it to. ERC
shows the class-code revision is a **countrywide** content change (`GL_CW_20260101_V01` →
`GL_CW_20270401_V01`), which each jurisdiction adopts by importing the newer countrywide package.
The state-by-state appearance is the adoption schedule, not the change itself. That is a
correction to A's framing in `12` §12.5.1 ("class-code revision" listed as a *rate-stream* change
type) — it belongs to the countrywide stream.

**Practical consequence:** any "15/36"-style membership list is valid only as of a stated date
and a stated corpus snapshot. Neither derivation says so; both present the split as a fact about
the program.

### 2.4 Effective dating: A's biggest weakness, and ERC's real answer is not the one A predicted

A records its most consequential defect as D4/D6: **264 of 503** Rules PDFs and 57 of 472 loss
cost PDFs are dated by *edition-date proximity only*, flagged *"Low — positional guess"*. A's
`12` §12.8 calls this the thing that *"needs reconciliation … before any premium is trusted"*.

A's §8 prediction: *"ERC is understood to carry effective dates as structured metadata."*

**B falsifies the mechanism and confirms the outcome.** B searched all 2,865 `*.Metadata.xml`
for `EffectiveDate|ReleaseDate` as file-level elements: **0 hits** (`01` §2.2). B's report 1
then over-generalised to "identity lives only in the directory name", and B's report 2 corrected
itself: the XSD `targetNamespace` yields the complete `(jurisdiction, edition, version)` triple
for **567/567** packages from file content alone, corroborated by five further channels with
**0** disagreements (`02` §4).

**Adjudication: A's expectation was right in effect and wrong in mechanism.** ERC does supply
unambiguous, machine-readable edition identity at 100% coverage — not from a metadata field but
from a namespace URI. A's single largest quality gap is closed by B's corpus. This is the most
important asymmetry in the whole comparison.

### 2.5 Rounding: A has it, B calls it the top blocker

B ranks rounding as *"the most material gap … `@DecimalPlaces` is declared 7,682 times and the
rounding rule is stated nowhere"* (`06` §3.1), and concludes *"no premium this engine produces
can be asserted as correct to the cent."*

A quotes the manual: Rule 56.A.4 defines increased-limits interpolation and its rounding
verbatim — *"all fractions in the third decimal place shall be considered as an additional unit
in the second decimal place"* — i.e. **round half-up at 2dp**; Section I Rule 5 covers general
rounding.

**Adjudication: no conflict; B is silent where A is not.** The PDF manual states a rounding
convention that the ERC packages do not carry. Note the scopes are not identical: A's citation
governs ILF interpolation, while B's 7,682 `@DecimalPlaces` occurrences span `Product` and
`Round` at four stages of the premium chain. So the PDF **narrows** B's blocker rather than
eliminating it — a plausible reading is that ISO's convention is half-up throughout, and A's
citation is direct evidence for it, but that inference is mine and is not stated in either
source.

### 2.6 Interpolation: two different interpolations, easily confused

A: interpolation is an **ILF** procedure (Rule 56.A.4), defined and mandatory.

B: `InterpolateMode="Linear"` appears **18 times corpus-wide**, only on
`PremOpsSizeOfRiskRelativity` / `ProdsCompldOpsSizeOfRiskRelativity`; and the DOC `Not Supported`
sheet says of `Rule 15.D.7 Deductible Discount Factors`: *"Interpolation procedure to be used in
determining deductible discount…"*

**Adjudication: these are three different interpolations** — ILF (PDF, defined), size-of-risk
relativity (ERC, declared but with unstated boundary/rounding semantics), deductible discount
(ERC declares it *not supported*). A reader who merges them will conclude ERC implements ILF
interpolation. It does not: ERC ships ILF tables as flat keyed lookups on
`(EachOccurrenceLimit, GeneralAggregateLimit)` strings — I verified AL's `ILFPremOps` has 216
rows of exact limit pairs, with no interpolation machinery. **An ERC-only build cannot rate a
limit not present in the table, and neither derivation says so.**

### 2.7 Where ERC publishes numbers the manual declares refer-to-company

Rule 37.C.2 opens: *"All applicable loss costs and modifiers referenced in Paragraphs C.2.b. and
C.2.d. and Tables D., E. and F. must be referred to company before using."* A therefore records
the Rule 37.D/E/F modifier values as **not published** (`11` §11.11).

I verified that ERC **publishes all three**: `UnmannedAircraftOwnershipAndOperationPAIRatingModifiers`
(9 rows, 0.4–1.0), `UnmannedAircraftUsagePAIRatingModifiers` (12 rows, 0.8–1.2),
`UnmannedAircraftPrimaryPlaceOfOperationPAIRatingModifiers` (9 rows, 0.6–1.3).

**Two hazards nobody has flagged.** First, `0` is used as a sentinel in these tables:
`Non-owned unmanned aircraft operated by other parties` → `0`, `Not Applicable` → `0`,
`Unknown` → `0`, and `>55 lbs` → `0` in the base charge table where the manual says `RTC`. A
consumer that multiplies naively produces a **$0 premium** where the manual requires a referral.
Second, A's manual-derived tie-break — *"If more than one … category applies, assign the category
with the highest rating modifier"*, a `MAX` not a product — is a rule that the ERC tables do not
express. **The PDF is required to use the ERC data correctly here.**

### 2.8 Territory numbering families

A states territory numbers occupy two disjoint families, `001`–`024` and `501`–`517`, *"never
mixed within a jurisdiction."* I verified that in ERC, NJ's latest package ships
`PremOpsLossCostNJTerr001`…`Terr017` **and** `PremOpsSizeOfRiskLossCostTerr501`…`Terr517` — the
same territories under both numberings, offset by 500. A's claim holds for what the loss-cost
*grid pages* print; it does not hold for ERC's internal table naming. Minor, but a join key
built on A's statement will fail on ERC.

### 2.9 A structural variant neither derivation found

Four jurisdictions do not ship a single `PremOpsLossCost` table. CA, NJ and OH shard it into
one table per territory (`PremOpsLossCostNJTerr001`, `PremOpsLossCost001`, …), selected by a
state-overridden rule in `GeneralLiabilityClassificationPremOpsCoverageRules.Rule.xml` that
hard-codes the fifteen table names. NY does both — it ships 20 sharded tables *and* an **empty**
`PremOpsLossCost.RateTable.csv` that shadows the (also empty) countrywide one.

This falls straight through B's model: B's §3.2 lookup-dimension analysis treats
`PremOpsLossCost` as keyed on `PremOpsTerr`, and B's resolver rules (`04` §2.4) would faithfully
overlay NY's empty table over the countrywide empty table and find no loss costs at all. B's
100.000% reference-closure result does not catch it, because the sharded tables *are* referenced
and *do* resolve — B simply never asked whether the tables a rating path needs are populated.

**This is the strongest argument in this document for not building on either source alone.**

---

## 3. What each source uniquely provides

### Only the PDFs have

| Content | Why it matters |
|---|---|
| **Rule prose and its imperatives** | Attachment constraints (*"do not attach more than one…"*), rule-suspension lists (Rule 45.B, 44.A.4), the `MAX` tie-break for drone modifiers, the ILTA decoding. These are rating logic that ERC's rules may or may not implement, and that ERC's data does not state. |
| **The rounding and interpolation conventions** | Rule 56.A.4, Rule 5. B's top-ranked blocker. |
| **Edition renumbering** | 21 of ~50 rules renumbered in CW 2027, with **number reuse** (Rule 22 changes meaning entirely). A calls it the highest-severity correctness risk; see §4. |
| **Regulator-facing provenance** | Every number traces to a filed page with a circular and filing reference. |
| **The three-valued loss-cost grid** | `–` (not offered, 18.6%) vs `(a)` (refer, 17.1%) vs numeric — an eligibility gate (Rule 48.F.1) that has no direct ERC counterpart. |
| **Semantics for structures ERC only encodes** | e.g. that `CG 28 07` / `CG 31 15` *convert* the OCP coverage form rather than adding to it. |

### Only the ERC packages have

| Content | Why it matters |
|---|---|
| **100%-reliable edition identity** | `targetNamespace` → `(jurisdiction, edition, version)` for 567/567. Closes A's D4/D6, its largest defect. |
| **An explicit state→countrywide dependency edge** | One `xs:import` per package, graph exactly closed, 0 disagreements across 51,983 rule-level `ProjectName` references. A can only infer which CW edition a state notice was written against — and records that as its highest-value unfinished ingestion task (`12` §12.8). |
| **Executable rating logic** | 114,726 `<Rule>` elements, a 52-operator expression language, a DAG of depth 8, two entry points. A has the algorithm as *prose steps*; B has it as *code*. |
| **The premium dataflow, derived mechanically** | 73,990 edges; `FinalRate = Product(BaseRate, FinalILF, PackageModFactor, ExperienceRatingModificationFactor, ExpenseModification, ModToUse[, SizeOfRiskFinalRelativity])`. |
| **The tables A did not extract** | Tables 40.F/40.G hazard grades (1,163 rows each), Rule 15 deductible discount factors (`DedFactorPremOpsBI/CSL/PD`, 93 rows each), the classification table (1,163 rows), claims-made multipliers (25 rows), Rule 37.D/E/F modifiers. A lists all of these as "not extracted" (`09` §9.4) or "not published" (`11` §11.11). |
| **The corpus's own scope declaration** | 5,300 `Refer to Company` rows, 395 `Not Supported` rows, 1,113 `Special Consideration` rows. Nothing in the PDFs states what an automated implementation cannot do. |
| **The forms/UI/statistical surface** | 1,596 ISO form numbers, 30,449 input fields with XPath applicability conditions, 1,490 statistical-code tables. |
| **Sample transactions** | 517 STC inputs and the single `1. Output.json` in `OK/GL_OK 20250601 V01` — the only rated output example anywhere. |
| **The hard scope truth** | Only **19 of 420** premium-writing tables actually rate; **381 (90.7%)** compute `Premium = Product(ManualPremium, PackageModFactor)`. |

That last row deserves emphasis. **B's §1.1 finding is the single most important thing either
derivation says about scope, and A has no way to see it.** A's `11-RATING-ARCHITECTURE.md`
carefully specifies five archetypes across seventeen coverages and concludes the engine is
"priceable in all 51 jurisdictions". B shows that ISO's own machine-readable implementation
prices the class-rated core and treats ~380 endorsement tables as premium pass-throughs. Those
statements are compatible — A means the *manual* specifies enough to price Prem/Ops and
Prod/CompOps, which is true — but a sponsor reading A alone will form a much larger expectation
of automated coverage than ISO's own product delivers.

---

## 4. Questions one derivation treated as central and the other never asked

This asymmetry is informative about the sources, not about the analysts.

| Question | A | B | What it tells you |
|---|---|---|---|
| **Are rule numbers stable identifiers?** | Central — finding #2, *"the project's highest-severity correctness risk"*, drives the entire `rule_key` design in `12` | **Never asked.** ERC carries `BureauRuleNumbers` metadata and DOC citations like `Rule 36.C.14.a`, but nothing forces the question | ERC addresses rules by *name* (`SetFinalRate`), never by printed number. The hazard is an artifact of documents, and ERC has already solved it — which is itself a strong argument for ERC as the execution substrate |
| **What can this content *not* do?** | Asked as "what is missing from the corpus" (G1–G9) | Central — the DOC exception register, and §1.1's 4.5%/90.7% split | The PDFs are a *specification* and never state implementation limits; ERC is an *implementation* and must |
| **Is a rating semantically complete?** | Assumed: if the algorithm and operands are present, it prices | Explicitly separated: *"referential completeness is not semantic sufficiency"* (`04` §2.8) | Only an executable corpus can raise the distinction |
| **What does `Status` A/C/D mean?** | Does not exist in the PDFs | An entire section, five falsified hypotheses, still unresolved | Pure ERC artifact |
| **Are editions cumulative or deltas?** | Assumed cumulative; the versioning model is about *rules*, not content snapshots | Tested against 515 consecutive pairs; 92.7–98.3% carry-over; 600 of 600 "dropped" tables still present in the parent | PDFs are self-evidently cumulative documents; a package tree is not |
| **What is the exact class-code and territory content?** | Central (§13.4, §13.8) | Measured incidentally as key vocabularies | |
| **Which coverages have no base rate?** | Central (§13.3, and a correction to A's own §3.1) | Never asked | B counted subline *presence*; rateability requires knowing what a loss cost is |
| **Is the countrywide table empty?** | N/A — a PDF absence is visible | Never asked | The blind spot of §2.2 |
| **Rounding mode** | Answered from the manual | Ranked the #1 blocker | The complementarity in one line |

---

## 5. What a build should rest on

**Recommendation: build on ERC as the execution substrate, and treat the PDF corpus as the
normative specification, the semantic dictionary and the independent audit channel. Neither
alone is sufficient, and the failure modes of using either alone are now concrete, not
hypothetical.**

### 5.1 ERC is the substrate

Not because it is "better data" but for three specific reasons the comparison established:

1. **Edition resolution is solved.** 567/567 identity from content, one explicit `xs:import`
   naming the exact countrywide parent, 0 disagreements across 51,983 rule references. A's
   single largest defect — 264 PDFs dated by positional guess — simply does not arise. Since a
   wrong edition selection produces a *plausible wrong premium*, this alone decides the question.
2. **Extraction risk is gone.** A's highest-risk defect is a silent `pdftotext -layout`
   misalignment on loss-cost grids that produces valid-looking wrong numbers. B parsed 51,987
   XML files and 33,669 CSVs with `PROBLEMS: 0`.
3. **The rules are executable.** A DAG, two entry points, a 52-operator language and the actual
   dataflow into `Premium`. A's nine-step prose has to be re-implemented and its fidelity argued;
   ERC's rules can be interpreted and then *checked* against the prose.

### 5.2 The PDFs are not a fallback — they are load-bearing in four defined roles

- **Semantic dictionary.** ERC declares `@DecimalPlaces` 7,682 times and never says how to round;
  Rule 56.A.4 does. ERC ships the drone modifier tables and never says the tie-break is `MAX`;
  Rule 37.D does. ERC ships two ILTA columns and never says they are one printed token. ERC ships
  `0` where the manual says `RTC`.
- **Scope and eligibility.** The `–` marker (18.6% of loss-cost cells) is a hard eligibility gate
  under Rule 48.F.1 with no clean ERC equivalent; the rule-suspension lists (Paragraph B of every
  Section III rule) are prose that determines which general rules run.
- **Independent verification.** The §1.8 cell-level agreements, the §1.2 27-jurisdiction set
  identity and the §1.3 territory histogram are only possible because the two are separately
  produced. A's own `BUILD-PLAN-PLAIN-ENGLISH.md` §8 predicted that a single-feed build *"loses
  that independence — an error in the feed would appear consistent."* This comparison is the
  demonstration that the prediction was right and that the check is cheap.
- **Regulatory provenance.** Every number traceable to a filed page.

### 5.3 Where the two together close a gap neither closes alone

| Gap | Closed by |
|---|---|
| **Rounding and interpolation semantics** | PDF supplies the convention; ERC supplies the 7,682 sites it applies to |
| **Which countrywide edition a state notice was written against** (A's highest-value unfinished ingestion task) | ERC's `xs:import`, 100% coverage |
| **The 138 empty countrywide tables and the 4 sharded-loss-cost jurisdictions** | Only visible by asking a PDF-derived question ("where do the numbers live?") of the ERC tree |
| **Hazard-grade, deductible-discount and classification tables A never extracted** | ERC ships them; the PDF validates a sample |
| **Realistic scope expectations** | ERC's 19-of-420 finding; the PDFs alone imply far broader automation |
| **Terrorism, CGLES/Composite/Size-of-Risk, WC loss costs** | **Neither.** Absent from both. A's G4/G6/G9 have no ERC counterpart (ERC has `CompositeRatingExposureIndicatorCode` and terrorism *territory* tables but no rating plan) |

### 5.4 Concrete build posture

1. **Ingest ERC** exactly as `05-DATA-MODEL-AND-INGESTION.md` specifies, with three additions
   this comparison forces: record **row counts per table** and fail loudly on an empty table on a
   required rating path; resolve loss-cost tables by *pattern* (`PremOpsLossCost*`) not exact name;
   and never coerce a modifier `0` to a multiplier without checking it against the manual's
   refer-to-company blocks.
2. **Ingest the PDF-derived layer as a semantics overlay**, keyed by `rule_key` and table name,
   carrying: rounding policy, interpolation procedure, attachment constraints, rule suspensions,
   eligibility gates, tie-break rules, and the refer-to-company blocks. This is small, high-value
   and mostly already written in A's `11-RATING-ARCHITECTURE.md`.
3. **Make the cross-check a CI gate**, not a one-off: territory domains, class-code sets, ILF
   table shapes, countrywide factor values, ILTA assignments. All five agreed exactly here; a
   future disagreement means an ingestion regression on one side.
4. **Do not carry A's rule-number machinery into the ERC path.** It solves a problem ERC does not
   have. Keep it only for parsing the PDFs.
5. **Report scope honestly**: 19 rateable coverage tables plus a full policy model, a statistical
   coding engine, and a capture-and-refer surface for the rest.

---

## 6. Confidence assessment

### Established by two independent derivations — treat as settled

| Claim | Basis |
|---|---|
| The countrywide layer holds the algorithm and no rating operands | A (Rule 56.B + 0 CW loss-cost notices), B (24 universally-overridden tables), verified (138/272 empty CW tables) |
| Exactly 27 jurisdictions have a ZIP→territory mapping, and they are the same 27 | Set-identical, independently derived |
| Territory domains per jurisdiction | Identical histogram; row counts reconcile as classes × territories |
| Products/CompOps is written to statewide territory `999` and is not territory-rated | Same constant, both sides |
| Composition (CW + state overlay, wholesale table replacement, no row merging) | A architecturally, B with 374/374 contested lookups differing |
| Class-code universe of 1,163 (2027) / 1,188 (prior), with a 229-retired / 204-new revision | Exact integer agreement across formats |
| The OCP/Principals-Protective loss cost is withdrawn in the 2027 filing | A across 448 notices, verified in ERC as 51→8 |
| Liquor and Railroad Protective have no published base rate anywhere | A 0/51, verified: no such ERC table exists |
| Countrywide factor values (medpay, LoED, cyber, product withdrawal, drone charges) | Digit-for-digit |
| Hawaii is out of scope | Both corpora, three ways |
| Edition selection must be as-of a rating date | Both |
| Refer-to-company must be a first-class outcome | Both, from disjoint evidence |

### Rests on one source only — usable, but single-threaded

**PDF only:** rounding and interpolation conventions; the rule-renumbering hazard; attachment
constraints and rule suspensions; the `–` / `(a)` / numeric cell alphabet and the Rule 48.F.1
eligibility gate; the ILTA composite-token decoding; the drone `MAX` tie-break; the ELP
`Manual` / `RTC` / `Incl.` vocabulary and the claims-made adjustment mandated for ELPs;
`CG 28 07` / `CG 31 15` as coverage transforms; the UST constructed class code.

**ERC only:** the 19-of-420 rating scope; `Status` A/C/D behaviour; the executable rule language
and its call graph; edition identity from `targetNamespace`; the explicit state→CW import edge;
cumulative-snapshot edition semantics; the DOC exception register; hazard-grade and
deductible-discount table contents; `ErcCore` and `MessageHelper` as missing engine primitives;
the compound-limit string encoding.

**Verified by me only, stated by neither:** 138 of 272 countrywide rate tables are empty stubs;
CA, NJ, NY and OH shard Prem/Ops loss costs into per-territory tables (NY additionally shipping
an empty shadow); ERC publishes drone modifiers the manual declares refer-to-company, using `0`
as a refer/not-applicable sentinel; ERC's `Subline` enumeration is not the ISO statistical
subline code and excludes Unmanned Aircraft; ERC's ILF tables carry no interpolation machinery,
so limits absent from the table cannot be rated from ERC alone.

### Open in both

1. **Terrorism.** A's G4: `TERRORISM` occurs nowhere in either PDF corpus as rate content. ERC
   carries terrorism *territory* and *stat-code* tables but no Terrorism Supplement. Unpriceable
   from anything held here.
2. **The carrier loss cost multiplier.** External by design in both.
3. **CGLES / Composite Rating / Size-of-Risk plan factors.** Referenced in both, supplied by
   neither. (ERC's `SizeOfRiskRelativity` tables are a *different* mechanism — the 18
   interpolated bands — not the CGLES plan.)
4. **Workers Compensation loss costs** for OCP class `15191` (51/51 jurisdictions price it as 75%
   of WC). Cross-line; absent from both.
5. **Rounding at every stage other than ILF interpolation.** A gives one convention; B counts
   7,682 declaration sites across four stages. The generalisation is plausible and unproven.
6. **Whether a rating terminates with a premium for every valid input.** B's explicit
   non-conclusion; A never poses it. Only an engine settles it, and the single
   `OK/GL_OK 20250601 V01` `1. Output.json` is the only fixture either corpus offers.
7. **`ErcCore` and `MessageHelper.AddErrorMessage`** — referenced by ERC, shipped by nobody, and
   the PDFs have nothing to say about an engine's internals.
8. **A class-code crosswalk for the 229/204 revision.** A's Q7. ERC ships both editions' class
   lists but no mapping between them; the `CG-LCADD` pages appear in only 2 of 51 PDF notices.
   Re-rating a pre-2027 risk under a 2027 edition is unsolved in both.
9. **`Status` A/C/D.** B falsified every reading; the PDFs contain no counterpart to falsify
   against.

### On A's predictions about ERC (`BUILD-PLAN-PLAIN-ENGLISH.md` §8)

Scored, since they were made before B ran and are therefore genuine forecasts:

- *"Effective dating … carried as structured metadata"* — **outcome right, mechanism wrong.**
  ERC's `Metadata/` carries no dates at all; the XSD namespace does, at 100%.
- *"Extraction disappears as a risk category"* — **right**, and replaced by semantic risk
  (rounding, sentinels, `Status`, empty tables).
- *"Change detection becomes cheap"* — **right** (B diffed 515 consecutive pairs mechanically).
- *"The countrywide layer still holds no increased-limit tables"* — **right**, and I verified it.
- *"Liquor Liability still has no published rate"* — **right**, and I verified it.
- *"Rule 22 still meant two different things"* — **untestable in ERC**; the hazard is
  document-specific and ERC dispatches on names.
- *"Verification loses its independence [if both come from one feed]"* — **right, and it is the
  main reason to keep both.** This document is the evidence.
