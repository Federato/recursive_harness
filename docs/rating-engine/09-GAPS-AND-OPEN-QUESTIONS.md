# 09 — Gaps, Limits of Evidence & Open Questions

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R1, R2, R3). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

This document exists so that nothing in the specification rests on an assumption. Every item
here is something the corpus **does not** answer. None of them has been filled by inference.

---

## 9.1 Content referenced by the manual but absent from this corpus

These are hard dependencies. The engine can be built and tested without them, but cannot
produce a bindable premium without them.

> **Updated at Step 7.** The GL **Loss Costs** corpus (`Commercial Line Manuals\GL\LossCosts\`,
> 472 PDFs, 51 jurisdictions) has since been acquired and analysed, closing **G1** and **G3**.
> See [`13-LOSS-COSTS-AND-ELP.md`](13-LOSS-COSTS-AND-ELP.md).
>
> **Corrected at Step 8.** **G2 was never a gap.** The Territory Definitions are on the
> **Territory Pages (`CG-T-n`) of the Rules notices themselves** — present in all 51
> jurisdictions, with full ZIP→territory tables in the 27 that rate by ZIP. The earlier entry
> asserted they were *"held outside the Rules manual"*; that claim was inherited from
> `05-LOOKUP-TABLES.md` §5.4 and never tested against the PDFs. See §9.6.

| # | Missing content | Manual reference that proves it is required | Status |
|---|---|---|---|
| G1 | **State rates / ISO loss costs** | Rule 23.B: rates *"are shown … in the state company rates/ISO loss costs opposite the identifying code number of the classification"* | ✅ **CLOSED.** Published loss costs for sublines 334, 336, 335 (OCP/PP) and 370 by class code and territory, all 51 jurisdictions (§13.4) |
| G2 | **Territory Definitions (ZIP → territory)** | State A-rule: *"A rating territory is a geographical area defined in terms of U.S. Postal Service (USPS) ZIP codes, as shown in the Territory Definitions"* | ✅ **CLOSED.** The Territory Pages (`CG-T-1`…`CG-T-n`) are in **every** Rules notice, all 51 jurisdictions — 27 with full ZIP→territory tables (23,719 rows), 4 with county/city definitions, 20 statewide (`05-LOOKUP-TABLES.md` §5.4.1) |
| G3 | **Estimated Loss Potentials (ELP) Supplement** | Rule 2.B: ELPs *"are provided in the Estimated Loss Potentials (ELPs) Supplement for certain classifications for which no manual state company rates/ISO loss costs are given"* | ✅ **CLOSED.** Full Supplement (Procedures 1–5, Tables 5.B–5.E) in all 471 readable loss cost notices; ~404 classes per jurisdiction (§13.5) |
| G4 | **Terrorism Supplement** | 48 of 51 jurisdictions' A-rule reads in full: *"Refer to the Terrorism Supplement to the CLM."* | ⚠️ **OPEN, but narrower than stated — [R3].** True of the **PDF** corpus. **ERC supplied every terrorism factor in the Oklahoma golden case** — exposure-class `0.004`, NBCR `0.58`, `TerrorismILF 0.94`, none of them in the input — and produced `18.00` of terrorism premium. So *"terrorism premium cannot be computed"* is too strong. Population audit scheduled at build-order item 9 (OI-37); do not repeat the claim until it runs |
| G5 | **Company Loss Cost Multiplier (LCM)** | Rule 23.B: *"company rates must be calculated by applying to the ISO loss cost the appropriate loss cost multiplier which has been supplied by the company"* | ❌ Carrier-specific input, by design. Every value in the loss cost corpus is a **pre-LCM ISO loss cost** |
| G6 | **CGLES / Composite Rating / Size-Of-Risk plans** | Rule 2.A.1 refers to *"any applicable rating plan modification"*; the ERC workbook records CGLES in 63 editions, CRP in 10, SOR in 9 | ❌ Modification factors unavailable |
| G7 | **Deductible discount factor tables** | Rule 15.E — the tables are in the CW manual (`CG-6`–`CG-8`) but were **not** extracted in this pass | Recoverable from `GL-MU-2027-RU-001-C.pdf`; see §9.4 |
| G8 | **Hawaii** | No `GL-HI-*` file exists in either corpus | Cannot rate HI. The loss cost corpus independently covers the **same 51 jurisdictions**, which makes a download gap less likely and a filing fact more likely |
| ~~**G9**~~ | ~~**Workers Compensation loss costs**~~ | ELP Table 5.C prices OCP class `15191` as *"Percentage of otherwise applicable Workers Compensation loss costs: 75%"* — present in **51/51** jurisdictions | ✅ **CLOSED 2026-08-11 — [R2].** Not a gap and not cross-line. ERC holds the 75% as a countrywide cell (`PrincipalsProtvLiabFactor`) and declares `WorkersCompensationRate` as a **submission input field**; real STC submissions supply it. A submission requirement, and **retired outright by the 2027 program**, which drops class `15191`. Gate 335 §1 |

> G4 and G6 remain *outside the Rules section of the manual by design*. G1 and G3 were also
> outside it — and have now been supplied by the separate loss cost corpus, which is why they
> are closed rather than worked around.

---

## 9.2 Corpus defects

| # | Defect | Detail | Recommended action |
|---|---|---|---|
| D1 | Truncated PDF | `GL-MO-2027-RU-003-C.pdf` — no xref, no EOF; unrecoverable by `pdftotext` or `pypdf` | Re-download. Missouri's latest usable notice is `GL-MO-2026-RU-001-C`. |
| D2 | Damaged xref tables | 103 files | Already handled — full recovery via `pypdf`. No content loss. |
| D3 | Duplicate downloads | `GL-DE-2022-RU-001-C (1)`, `GL-MU-2023-RU-002-C (1)`, `GL-IA-2023-RU-002-C (2)` | Deduplicate on `sha256`; delete the suffixed copies |
| D4 | ERC↔manual mapping confidence | 26 of 570 ERC versions unmapped; 264 of 503 PDFs matched by **edition-date proximity only** (recorded as *"Low — positional guess, not a verified match"* in the ERC workbook) | Effective dating for those 264 is provisional. Affects `manual_edition.effective_from`. |
| D5 | Truncated loss cost PDF | `GL-MI-2027-LC-003-C.pdf` — no xref/EOF, unrecoverable. Michigan's usable current loss costs are `GL-MI-2027-LC-002-C` | Re-download |
| D6 | Loss cost notice dating | 415 of 472 loss cost notices matched an ERC edition on a **cited circular or filing**; 57 fall outside the ERC corpus boundary and are dated by proximity (`GL_LossCost_to_ERC.xlsx`, `Gaps` sheet) | Same class of risk as D4, at ~12% rather than ~52% |
| D7 | **Loss cost grids are mis-extracted by `pdftotext -layout`** | Rows interleave and values attach to the wrong class code — silently, with plausible output. `pypdf` renders them correctly (§13.9) | The §8.3 dual-mode rule must be **inverted** for `CG-LC` / `CG-ELP` pages. Highest-risk extraction defect in the project |

**D4 is the most consequential open item for correctness.** Roughly half the corpus is dated
by positional inference rather than by a verified circular/filing identifier. Since
`effective_date` selects the edition, and edition selection determines which rule numbering
and which state variables apply, provisional dating propagates directly into premium.
Recommendation: treat proximity-matched editions as `date_confidence = 'LOW'` in
`manual_edition`, surface it in the rating trace, and prioritise resolving them.

---

## 9.3 Structural questions the documents do not settle

| # | Question | What the corpus shows | Why it matters |
|---|---|---|---|
| Q1 | Which CW edition does each **state** notice deviate against? | Each notice carries its own footer edition marker (e.g. TX `21st Edition 5-20` on one page, `16th Edition 4-23` on the next — markers are **per page**, not per document) | Determines the `rule_numbering_scheme` for overlay resolution (§7.4). Currently inferable but not stated. |
| Q2 | When does the CW 2027 renumbering take effect per jurisdiction? | `GL-MU-2027-RU-001-C` is `1st Edition 4-27`; state notices dated 2027 exist for 41 jurisdictions | Two numbering schemes will be live simultaneously during transition |
| Q3 | Where are Liquor Liability ILFs for the 48 jurisdictions with no Rule 56.B liquor table? | Only IL, MN, UT publish one in the exception pages | Liquor limits above basic cannot be rated in 48 jurisdictions. **Compounded at Step 7:** Liquor has no published *basic limits loss cost* in **any** jurisdiction either — only ELPs (§13.3). Liquor is ELP-driven or refer-to-company countrywide |
| ~~Q4~~ | ~~Is `has_prodcompops` derivable without the rate pages?~~ | **RESOLVED at Step 7.** The `–` marker occupies **18.6%** of all loss cost grid cells and is directly readable (§13.4) | Resolved *with a correction*: the marker is **per jurisdiction**, so `has_prodcompops` belongs on the state loss cost row, not on the countrywide `classification` table (`06-DATA-SCHEMA.md` §6.5) |
| Q5 | Do the 13 "never deviated" rules stay undeviated historically? | Asserted only against the latest notice per jurisdiction | Historical rating must re-run the parse per effective date |
| Q6 | Elevator/escalator inspection charge and Sports Participants (CW 2022 Rules 50, 51) | Absent from the CW 2027 rule list | Unclear whether withdrawn or relocated; affects step G |
| **Q7** | Why does the 2027 loss cost filing retire 229 class codes and introduce 204? | The vintage split is clean and simultaneous across 36 jurisdictions (§13.7) | A class-code crosswalk is needed to re-rate a pre-2027 policy under a 2027 edition. Neither corpus supplies one; the `CG-LCADD` mapping pages are the nearest mechanism but appear in only 2 of 51 current notices |
| **Q8** | Is the OCP/PP loss cost withdrawal permanent or transitional? | 390/390 notices through 2026 publish it; 22 of 58 2027 notices do | Determines whether OCP rating should be built against loss costs with an ELP fallback, or against ELPs with a loss cost fast path |

---

## 9.4 Work deliberately not done in this pass

Stated so the backlog is honest about what remains, rather than implying the extraction is
complete:

| Item | Status | Effort |
|---|---|---|
| **ILF factor cell extraction** | Table *inventory* complete for all 51 jurisdictions (which tables exist, subline, ordinal, basic limit). Individual **factor cells not extracted.** | Largest single ingestion task. Needs coordinate-based table parsing (§8.5.3). |
| **ILTA class→table rows** | Presence confirmed for all 51; rows not extracted | Medium; regular grid, ~1,500+ classes × 51 |
| **Classification table records** | Structure confirmed and specified; ~485 pages not parsed into records | Medium; highly regular format |
| **Deductible discount factors (Rule 15.E)** | Located at `CG-6`–`CG-8` in the CW manual; not extracted | Small, countrywide only |
| **Cyber/LoED hazard grade assignments (Rule 40.F/G)** | Located at `CG-60`–`CG-69`; not extracted | Small–medium, countrywide only |
| **Full historical deviation matrix** | Per-notice deviation records exist for all 490 notices; only latest-per-jurisdiction was summarised | Small — data already parsed |
| **Loss cost grid cell extraction** | Structure, cell vocabulary, territory keys, page invariant (`8·T+1`) and the correct extractor are all established (`13-LOSS-COSTS-AND-ELP.md`). The ~429,700 cells themselves are **not** loaded | Largest remaining volume task. Mechanically simpler than the ILF matrices — the grid is regular — but 51× the page count |
| **ELP entry extraction** | Same: vocabulary and H/R index semantics established; ~20,600 entries not loaded | Medium |

None of these blocks the schema or architecture decisions; all are volume work against
structures that are now specified.

---

## 9.5 Questions for the business, not the documents

These cannot be answered from any manual and need a decision:

1. **Which carrier LCM(s)** apply, and do they vary by jurisdiction, subline, or class group?
2. **Scope of history:** is the engine required to re-rate historically (which requires
   ingesting all 490 notices and resolving D4), or only to quote prospectively?
3. **Referral routing:** for the five refer-to-company coverages, is the engine expected to
   emit a referral and stop, or to apply carrier-supplied override rates from an internal table?
4. **Hawaii:** in scope? (see G8)
5. **Deviation from ISO:** will the carrier file its own deviations on top of ISO? If so, a
   third overlay layer is needed above the state layer — the resolver design supports it, but
   it must be decided before the schema is frozen.

---

## 9.6 Corrections to this register

Recorded so the register can be trusted: an entry here is only as good as the search behind it.

### G2 — "Territory Definitions absent" was wrong

| | |
|---|---|
| **Asserted** | The ZIP→territory mapping is *"held outside the Rules manual in ISO Territory Definitions"* and *"absent from both corpora"* |
| **Actually** | Every Rules notice carries **Territory Pages** (`CG-T-1`…`CG-T-n`) after the exception pages. 27 jurisdictions publish the full ZIP table there — **23,719 ZIP rows** in the latest notices alone. Example: `GL-NJ-2026-RU-001-C.pdf` pages 27–37, `CG-T-1`…`CG-T-11`, 721 ZIP rows |
| **How the error happened** | Two compounding mistakes. (1) The original §5.4 claim was inherited from the Rules-corpus analysis and carried forward without being tested against a PDF. (2) At Step 7 the loss cost corpus was searched for the string `ZIP`, correctly returned zero, and that result was **generalised to "both corpora" without searching the Rules corpus at all** |
| **Detected by** | The user, citing `GL-NJ-2026-RU-001-C.pdf` page 27 |
| **Verification since** | All 503 Rules PDFs scanned. 51/51 carry Territory Pages. The territory codes on those pages match the territories published on the loss cost grids in **all 51 jurisdictions, zero mismatches** |

**The generalisable lesson, now applied across this document set:** a negative result is scoped
to what was actually searched. "Not in corpus A" is not evidence about corpus B, and an
inherited claim is not evidence at all. Every remaining ❌ entry in §9.1 has since been
re-tested against **both** corpora by whitespace-normalised full-text search.

### Re-verification of the remaining gaps

| Gap | Searched | Rules corpus | Loss cost corpus |
|---|---|---|---|
| G4 Terrorism Supplement | `TERRORISM` + rate/premium context | Rule 55 and 48 A-rules **reference** it; the Supplement's own rate content is not present | absent |
| G5 Company LCM | `LOSSCOSTMULTIPLIER` | referenced by Rule 23.B as a carrier input | absent — values are pre-LCM by construction |
| G6 CGLES / CRP / SOR | plan names | referenced only | absent |
| G9 WC loss costs | `WORKERSCOMPENSATION` | referenced by ELP Table 5.C | referenced, not supplied |

These four remain genuinely absent. Unlike G2, each is *referenced as an external document*
by name in the manual text, rather than being a section of it.
