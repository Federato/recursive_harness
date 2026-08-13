# A4 — Loss Cost & ELP Corpus Inventory (per jurisdiction)

Companion appendix to [`13-LOSS-COSTS-AND-ELP.md`](13-LOSS-COSTS-AND-ELP.md). One row per
jurisdiction, computed from the **latest** loss cost notice held in
`Commercial Line Manuals\GL\LossCosts\`.

**Column meanings**

| Column | Meaning |
|---|---|
| `Latest LC notice` | Newest notice for the jurisdiction in the corpus |
| `Notices` | Total loss cost notices held (2020–2027) |
| `T` | Premises/Operations territories published |
| `Territory numbers` | The exact territory domain. Prod/COps is always statewide territory `999` |
| `CG-LC` | Loss cost page count — always `8·T + 1` |
| `Classes` | Distinct class codes on the loss cost grid |
| `ELP` | Distinct class codes carrying an ELP entry |
| `Vintage` | `pre-2027` (229 legacy class codes, publishes OCP/PP loss costs) or `2027` (204 new class codes, OCP/PP by ELP only) — see §13.7 |
| `Extractor` | `pdftotext` = readable directly; `pypdf` = xref-damaged, fallback required |
| `ERC edition` | Earliest ERC edition citing this notice's circular, from `GL_LossCost_to_ERC.xlsx`; `—` where the circular falls outside the ERC corpus boundary |

---

## A4.1 Inventory

| ST | Latest LC notice | Notices | T | Territory numbers | CG-LC | Classes | ELP | Vintage | Extractor | ERC edition |
|---|---|---|---|---|---|---|---|---|---|---|
| **AK** | GL-AK-2026-LC-001 | 9 | 1 | 001 | 9 | 1188 | 404 | pre-2027 | pypdf | GL AK 20260801 V02 |
| **AL** | GL-AL-2027-LC-003 | 10 | 2 | 501 503 | 17 | 1163 | 404 | 2027 | pypdf | GL AL 20270401 V04 |
| **AR** | GL-AR-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **AZ** | GL-AZ-2027-LC-003 | 10 | 3 | 502 503 504 | 25 | 1163 | 404 | 2027 | pypdf | — |
| **CA** | GL-CA-2024-LC-001 | 4 | 11 | 001 002 003 004 005 006 007 009 010 011 012 | 89 | 1188 | 404 | pre-2027 | pdftotext | GL CA 20241101 V01 |
| **CO** | GL-CO-2027-LC-003 | 10 | 2 | 501 502 | 17 | 1163 | 404 | 2027 | pypdf | GL CO 20270401 V02 |
| **CT** | GL-CT-2026-LC-001 | 8 | 8 | 501 503 504 505 506 507 508 509 | 65 | 1188 | 404 | pre-2027 | pypdf | GL CT 20260401 V03 |
| **DC** | GL-DC-2026-LC-001 | 6 | 1 | 001 | 9 | 1188 | 404 | pre-2027 | pypdf | GL DC 20260601 V01 |
| **DE** | GL-DE-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **FL** | GL-FL-2027-LC-002 | 11 | 5 | 001 002 004 005 006 | 41 | 1163 | 404 | 2027 | pypdf | — |
| **GA** | GL-GA-2026-LC-001 | 10 | 2 | 502 503 | 17 | 1188 | 404 | pre-2027 | pdftotext | GL GA 20260301 V02 |
| **IA** | GL-IA-2027-LC-002 | 9 | 2 | 501 502 | 17 | 1163 | 404 | 2027 | pypdf | GL IA 20270401 V03 |
| **ID** | GL-ID-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **IL** | GL-IL-2027-LC-002 | 10 | 7 | 501 504 506 507 508 509 514 | 57 | 1163 | 404 | 2027 | pypdf | GL IL 20270401 V04 |
| **IN** | GL-IN-2027-LC-002 | 10 | 4 | 501 502 504 506 | 33 | 1163 | 404 | 2027 | pypdf | GL IN 20270401 V03 |
| **KS** | GL-KS-2025-LC-001 | 7 | 2 | 501 502 | 17 | 1188 | 388 | pre-2027 | pdftotext | GL KS 20250301 V01 |
| **KY** | GL-KY-2027-LC-002 | 10 | 2 | 501 503 | 17 | 1163 | 404 | 2027 | pypdf | — |
| **LA** | GL-LA-2027-LC-002 | 10 | 4 | 501 502 503 504 | 33 | 1163 | 404 | 2027 | pypdf | — |
| **MA** | GL-MA-2026-LC-001 | 9 | 9 | 506 507 508 509 510 514 515 516 517 | 73 | 1188 | 404 | pre-2027 | pypdf | GL MA 20260101 V01 |
| **MD** | GL-MD-2027-LC-003 | 10 | 3 | 501 502 503 | 25 | 1163 | 404 | 2027 | pdftotext | — |
| **ME** | GL-ME-2027-LC-003 | 9 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **MI** | GL-MI-2027-LC-002 | 8 | 4 | 501 503 504 505 | 33 | 1188 | 408 | pre-2027 | pypdf | GL MI 20260401 V01 |
| **MN** | GL-MN-2027-LC-002 | 10 | 3 | 501 502 503 | 25 | 1163 | 404 | 2027 | pypdf | GL MN 20270401 V03 |
| **MO** | GL-MO-2027-LC-003 | 10 | 3 | 501 502 503 | 25 | 1163 | 404 | 2027 | pdftotext | GL MO 20270401 V02 |
| **MS** | GL-MS-2027-LC-002 | 9 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | GL MS 20270401 V04 |
| **MT** | GL-MT-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | GL MT 20270401 V03 |
| **NC** | GL-NC-2026-LC-001 | 8 | 1 | 002 | 9 | 1188 | 404 | pre-2027 | pypdf | GL NC 20260301 V02 |
| **ND** | GL-ND-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **NE** | GL-NE-2027-LC-002 | 9 | 2 | 501 502 | 17 | 1163 | 404 | 2027 | pypdf | GL NE 20270401 V03 |
| **NH** | GL-NH-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **NJ** | GL-NJ-2027-LC-001 | 9 | 15 | 501 502 503 504 505 506 507 508 509 511 512 513 515 516 517 | 121 | 1187 | 404 | pre-2027 | pypdf | GL NJ 20270101 V01 |
| **NM** | GL-NM-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | GL NM 20270401 V03 |
| **NV** | GL-NV-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **NY** | GL-NY-2025-LC-001 | 8 | 20 | 001 002 003 004 005 006 007 008 009 010 012 014 016 017 018 020 021 022 023 024 | 161 | 1181 | 404 | pre-2027 | pdftotext | GL NY 20250401 V03 |
| **OH** | GL-OH-2027-LC-002 | 10 | 10 | 501 502 503 504 505 506 507 508 509 510 | 81 | 1163 | 404 | 2027 | pypdf | — |
| **OK** | GL-OK-2027-LC-003 | 10 | 3 | 501 502 503 | 25 | 1163 | 404 | 2027 | pypdf | — |
| **OR** | GL-OR-2027-LC-002 | 9 | 2 | 501 502 | 17 | 1163 | 404 | 2027 | pypdf | GL OR 20270401 V03 |
| **PA** | GL-PA-2027-LC-003 | 10 | 11 | 501 502 503 504 505 507 509 510 511 512 513 | 89 | 1163 | 404 | 2027 | pypdf | — |
| **PR** | GL-PR-2027-LC-002 | 5 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **RI** | GL-RI-2027-LC-002 | 9 | 3 | 501 502 503 | 25 | 1188 | 404 | pre-2027 | pdftotext | — |
| **SC** | GL-SC-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | — |
| **SD** | GL-SD-2027-LC-003 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | GL SD 20270401 V03 |
| **TN** | GL-TN-2027-LC-002 | 10 | 4 | 501 503 504 505 | 33 | 1163 | 404 | 2027 | pypdf | GL TN 20270401 V02 |
| **TX** | GL-TX-2025-LC-001 | 9 | 8 | 001 002 003 004 005 006 007 008 | 65 | 1188 | 404 | pre-2027 | pdftotext | GL TX 20250801 V01 |
| **UT** | GL-UT-2027-LC-002 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | GL UT 20270401 V03 |
| **VA** | GL-VA-2027-LC-002 | 10 | 4 | 501 502 503 504 | 33 | 1163 | 404 | 2027 | pypdf | — |
| **VT** | GL-VT-2027-LC-002 | 11 | 1 | 001 | 9 | 1188 | 404 | pre-2027 | pdftotext | GL VT 20261201 V01 |
| **WA** | GL-WA-2026-LC-001 | 6 | 2 | 501 502 | 17 | 1188 | 404 | pre-2027 | pypdf | GL WA 20260101 V02 |
| **WI** | GL-WI-2027-LC-002 | 10 | 3 | 501 502 503 | 25 | 1163 | 404 | 2027 | pypdf | GL WI 20270401 V03 |
| **WV** | GL-WV-2027-LC-002 | 9 | 1 | 001 | 9 | 1163 | 404 | 2027 | pdftotext | GL WV 20270401 V03 |
| **WY** | GL-WY-2027-LC-002 | 10 | 1 | 001 | 9 | 1163 | 404 | 2027 | pypdf | GL WY 20270401 V02 |

---

## A4.2 Roll-ups

### Vintage split (§13.7)

| Vintage | Count | Jurisdictions |
|---|---|---|
| **pre-2027** | 15 | AK, CA, CT, DC, GA, KS, MA, MI, NC, NJ, NY, RI, TX, VT, WA |
| **2027** | 36 | AL, AR, AZ, CO, DE, FL, IA, ID, IL, IN, KY, LA, MD, ME, MN, MO, MS, MT, ND, NE, NH, NM, NV, OH, OK, OR, PA, PR, SC, SD, TN, UT, VA, WI, WV, WY |

The vintage is determined identically by three independent tests — legacy class codes present,
new class codes present, OCP/PP loss cost table published. All three select the same sets.

### Territory distribution

| T | Jurisdictions |
|---|---|
| 1 | AK, AR, DC, DE, ID, ME, MS, MT, NC, ND, NH, NM, NV, PR, SC, SD, UT, VT, WV, WY (**20**) |
| 2 | AL, CO, GA, IA, KS, KY, NE, OR, WA (9) |
| 3 | AZ, MD, MN, MO, OK, RI, WI (7) |
| 4 | IN, LA, MI, TN, VA (5) |
| 5 | FL |
| 7 | IL |
| 8 | CT, TX |
| 9 | MA |
| 10 | OH |
| 11 | CA, PA |
| 15 | NJ |
| 20 | NY |

Territory numbers occupy two disjoint families — `001`–`024` and `501`–`517` — and a
jurisdiction never mixes them. Numbering is **not contiguous**: Illinois publishes
`501, 504, 506, 507, 508, 509, 514`, so a range check is not a valid domain test; store the
enumerated set.

**Territory-rated but carrying no territory A-rule in the Rules exception pages: CA, FL, NY,
TX** — see §13.8. These four are among the most territorialised jurisdictions in the program.

### Extraction

| | Files | Latest-per-jurisdiction |
|---|---|---|
| `pdftotext` readable | 389 / 472 | 10 / 51 |
| xref-damaged, `pypdf` required | 83 / 472 | **41 / 51** |
| Unrecoverable | 1 (`GL-MI-2027-LC-003-C.pdf`) | — |

For the loss cost and ELP grids, `pypdf` is also the **more accurate** extractor even where
`pdftotext` succeeds — `-layout` silently misaligns grid rows (§13.9).

### Class-code and ELP coverage

| Measure | Value |
|---|---|
| Class codes on the grid in all 51 jurisdictions | 947 |
| Class codes in the pre-2027 vintage only | 229 |
| Class codes in the 2027 vintage only | 204 |
| Union across all jurisdictions | 1,396 |
| Per-jurisdiction grid size | 1,163 (2027) / 1,188 (pre-2027); NJ 1,187, NY 1,181 |
| ELP entries per jurisdiction | 404 in 49 of 51 (KS 388, MI 408) |
| Grid cells, latest notices, all territories | ~429,700 |

### Notices per jurisdiction

Range 4 (CA) – 11 (FL, VT), median 10. The loss cost stream therefore churns at a comparable
rate to the state rules stream (5–17 notices) and independently of it — the basis for treating
it as a **third version stream** in `12-VERSIONING-AND-EDITIONS.md`.

---

## A4.3 Territory definitions (from the **Rules** notices, `CG-T` pages)

The ZIP→territory mapping is not in the loss cost corpus — it is on the Territory Pages of each
jurisdiction's **Rules** notice. All 51 carry them. Full discussion in
[`05-LOOKUP-TABLES.md`](05-LOOKUP-TABLES.md) §5.4.1.

`Rows` is ZIP rows for the ZIP-table scheme and city/county rows for the county/city scheme.
`Match` compares the territory codes printed on the `CG-T` pages with the territories published
on that jurisdiction's loss cost grids.

| ST | Latest Rules notice | Scheme | CG-T pages | Rows | Territories | Match |
|---|---|---|---|---|---|---|
| **AK** | GL-AK-2026-RU-001 | Entire State | 1 | — | 1 | — |
| **AL** | GL-AL-2027-RU-004 | ZIP Table | 11 | 799 | 2 | YES |
| **AR** | GL-AR-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **AZ** | GL-AZ-2027-RU-003 | ZIP Table | 8 | 519 | 3 | YES |
| **CA** | GL-CA-2023-RU-003 | County City | 4 | 275 | 11 | — |
| **CO** | GL-CO-2027-RU-003 | ZIP Table | 9 | 640 | 2 | YES |
| **CT** | GL-CT-2026-RU-002 | ZIP Table | 7 | 422 | 8 | YES |
| **DC** | GL-DC-2026-RU-002 | Entire State | 1 | — | 1 | — |
| **DE** | GL-DE-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **FL** | GL-FL-2027-RU-003 | County City | 1 | 25 | 5 | — |
| **GA** | GL-GA-2026-RU-003 | ZIP Table | 13 | 941 | 2 | YES |
| **IA** | GL-IA-2026-RU-001 | ZIP Table | 15 | 1055 | 2 | YES |
| **ID** | GL-ID-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **IL** | GL-IL-2027-RU-004 | ZIP Table | 21 | 1569 | 7 | YES |
| **IN** | GL-IN-2027-RU-003 | ZIP Table | 13 | 958 | 4 | YES |
| **KS** | GL-KS-2026-RU-002 | ZIP Table | 11 | 747 | 2 | YES |
| **KY** | GL-KY-2027-RU-004 | ZIP Table | 13 | 946 | 2 | YES |
| **LA** | GL-LA-2027-RU-003 | ZIP Table | 10 | 719 | 4 | YES |
| **MA** | GL-MA-2027-RU-003 | ZIP Table | 10 | 679 | 9 | YES |
| **MD** | GL-MD-2027-RU-003 | ZIP Table | 9 | 608 | 3 | YES |
| **ME** | GL-ME-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **MI** | GL-MI-2027-RU-003 | ZIP Table | 16 | 1159 | 4 | YES |
| **MN** | GL-MN-2027-RU-004 | ZIP Table | 13 | 953 | 3 | YES |
| **MO** | GL-MO-2026-RU-001 | ZIP Table | 16 | 1155 | 3 | YES |
| **MS** | GL-MS-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **MT** | GL-MT-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **NC** | GL-NC-2026-RU-002 | Entire State | 1 | — | 1 | — |
| **ND** | GL-ND-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **NE** | GL-NE-2027-RU-003 | ZIP Table | 9 | 618 | 2 | YES |
| **NH** | GL-NH-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **NJ** | GL-NJ-2027-RU-001 | ZIP Table | 11 | 721 | 15 | YES |
| **NM** | GL-NM-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **NV** | GL-NV-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **NY** | GL-NY-2025-RU-001 | County City | 2 | 83 | 20 | — |
| **OH** | GL-OH-2027-RU-004 | ZIP Table | 19 | 1413 | 10 | YES |
| **OK** | GL-OK-2027-RU-003 | ZIP Table | 11 | 764 | 3 | YES |
| **OR** | GL-OR-2026-RU-002 | ZIP Table | 7 | 479 | 2 | YES |
| **PA** | GL-PA-2027-RU-004 | ZIP Table | 29 | 2162 | 11 | YES |
| **PR** | GL-PR-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **RI** | GL-RI-2026-RU-002 | ZIP Table | 3 | 90 | 3 | YES |
| **SC** | GL-SC-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **SD** | GL-SD-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **TN** | GL-TN-2026-RU-002 | ZIP Table | 11 | 787 | 4 | YES |
| **TX** | GL-TX-2025-RU-001 | County City | 2 | 49 | 8 | — |
| **UT** | GL-UT-2027-RU-003 | Entire State | 1 | — | 1 | — |
| **VA** | GL-VA-2026-RU-002 | ZIP Table | 17 | 1223 | 4 | YES |
| **VT** | GL-VT-2025-RU-001 | Entire State | 1 | — | 1 | — |
| **WA** | GL-WA-2026-RU-001 | ZIP Table | 10 | 716 | 2 | YES |
| **WI** | GL-WI-2027-RU-004 | ZIP Table | 12 | 877 | 3 | YES |
| **WV** | GL-WV-2026-RU-002 | Entire State | 1 | — | 1 | — |
| **WY** | GL-WY-2026-RU-002 | Entire State | 1 | — | 1 | — |

**Totals:** 23,719 ZIP rows across the 27 ZIP-scheme jurisdictions; 432 city/county rows across
the 4 county-scheme jurisdictions (CA 275, NY 83, TX 49, FL 25); 20 jurisdictions need no lookup.

**Cross-corpus agreement: 51 of 51 exact, zero mismatches.** The 27 ZIP-scheme jurisdictions are
verified code-for-code against their loss cost grids; the 4 county-scheme and 20 statewide
jurisdictions are verified on territory *count* and codes. Two corpora on separate release
cycles, parsed by different code paths, agreeing on all 51 domains is the only external oracle
available anywhere in this project — which is why it is also ingestion assertion **V22**.

**MO caveat:** `GL-MO-2027-RU-003-C.pdf` is truncated and unreadable, so Missouri's territory
row is taken from `GL-MO-2026-RU-001-C`.
