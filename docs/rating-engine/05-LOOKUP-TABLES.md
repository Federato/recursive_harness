# 05 — Lookup Tables & State-Variable Values

> Every value below is extracted verbatim from the jurisdiction notice named in the row. No value is inferred, interpolated, or carried across jurisdictions.


## 5.1 Rule 24 — Payroll limitation (Bases Of Premium, Paragraph E.2.m.)

**This is a structural deviation, not just a numeric one.** Three distinct shapes occur; a single scalar column cannot represent them.


| Shape | # jurisdictions | Meaning |
|---|---|---|
| `ANNUAL_CAP_BOTH` | 45 | One annual payroll amount applied to both executive officers and individual insureds/co-partners |
| `WEEKLY_MINMAX_EXEC + ANNUAL_INDIV` | 5 | Executive officers capped by a **weekly** min/max band; individual insureds/co-partners by an annual amount |
| `ANNUAL_INDIV_ONLY` | 1 | Annual amount for individual insureds/co-partners only; no separate executive-officer amount stated |

| ST | Shape | Exec (annual) | Indiv (annual) | Each indiv/co-partner (annual) | Weekly max | Weekly min | Seasonal reduction | Notice |
|---|---|---|---|---|---|---|---|---|
| **AK** | `ANNUAL_CAP_BOTH` | $56,800 | $56,800 | — | — | — | — | GL-AK-2026-RU-001-C |
| **AL** | `ANNUAL_CAP_BOTH` | $42,300 | $42,300 | — | — | — | — | GL-AL-2027-RU-004-C |
| **AR** | `ANNUAL_CAP_BOTH` | $30,000 | $30,000 | — | — | — | — | GL-AR-2027-RU-003-C |
| **AZ** | `ANNUAL_CAP_BOTH` | $26,400 | $26,400 | — | — | — | — | GL-AZ-2027-RU-003-C |
| **CA** | `ANNUAL_CAP_BOTH` | $33,600 | $33,600 | — | — | — | — | GL-CA-2023-RU-003-C |
| **CO** | `ANNUAL_CAP_BOTH` | $39,300 | $39,300 | — | — | — | — | GL-CO-2027-RU-003-C |
| **CT** | `WEEKLY_MINMAX_EXEC + ANNUAL_INDIV` | — | — | $10,400 | $300 | $100 | 2% per week beyond twelve | GL-CT-2026-RU-002-C |
| **DC** | `ANNUAL_CAP_BOTH` | $30,000 | $30,000 | — | — | — | — | GL-DC-2026-RU-002-C |
| **DE** | `ANNUAL_CAP_BOTH` | $49,300 | $49,300 | — | — | — | — | GL-DE-2027-RU-003-C |
| **FL** | `ANNUAL_CAP_BOTH` | $40,600 | $40,600 | — | — | — | — | GL-FL-2027-RU-003-C |
| **GA** | `ANNUAL_CAP_BOTH` | $30,500 | $30,500 | — | — | — | — | GL-GA-2026-RU-003-C |
| **IA** | `ANNUAL_CAP_BOTH` | $36,000 | $36,000 | — | — | — | — | GL-IA-2026-RU-001-C |
| **ID** | `ANNUAL_CAP_BOTH` | $32,800 | $32,800 | — | — | — | — | GL-ID-2027-RU-003-C |
| **IL** | `ANNUAL_CAP_BOTH` | $67,100 | $67,100 | — | — | — | — | GL-IL-2027-RU-004-C |
| **IN** | `ANNUAL_CAP_BOTH` | $50,300 | $50,300 | — | — | — | — | GL-IN-2027-RU-003-C |
| **KS** | `ANNUAL_CAP_BOTH` | $30,300 | $13,300 | — | — | — | — | GL-KS-2026-RU-002-C |
| **KY** | `ANNUAL_CAP_BOTH` | $47,000 | $47,000 | — | — | — | — | GL-KY-2027-RU-004-C |
| **LA** | `ANNUAL_CAP_BOTH` | $15,600 | $15,600 | — | — | — | — | GL-LA-2027-RU-003-C |
| **MA** | `ANNUAL_CAP_BOTH` | $63,700 | $63,700 | — | — | — | — | GL-MA-2027-RU-003-C |
| **MD** | `ANNUAL_CAP_BOTH` | $35,100 | $35,100 | — | — | — | — | GL-MD-2027-RU-003-C |
| **ME** | `ANNUAL_CAP_BOTH` | $43,500 | $43,500 | — | — | — | — | GL-ME-2027-RU-003-C |
| **MI** | `ANNUAL_CAP_BOTH` | $51,300 | $51,300 | — | — | — | — | GL-MI-2027-RU-003-C |
| **MN** | `ANNUAL_CAP_BOTH` | $59,600 | $59,600 | — | — | — | — | GL-MN-2027-RU-004-C |
| **MO** | `ANNUAL_CAP_BOTH` | $28,400 | $28,400 | — | — | — | — | GL-MO-2026-RU-001-C |
| **MS** | `WEEKLY_MINMAX_EXEC + ANNUAL_INDIV` | — | — | $10,400 | $500 | $100 | 2% per week beyond twelve | GL-MS-2027-RU-003-C |
| **MT** | `ANNUAL_CAP_BOTH` | $18,800 | $15,700 | — | — | — | — | GL-MT-2027-RU-003-C |
| **NC** | `ANNUAL_CAP_BOTH` | $24,800 | $24,800 | — | — | — | — | GL-NC-2026-RU-002-C |
| **ND** | `ANNUAL_CAP_BOTH` | $55,500 | $55,500 | — | — | — | — | GL-ND-2027-RU-003-C |
| **NE** | `ANNUAL_CAP_BOTH` | $34,200 | $34,200 | — | — | — | — | GL-NE-2027-RU-003-C |
| **NH** | `ANNUAL_CAP_BOTH` | $48,400 | $48,400 | — | — | — | — | GL-NH-2027-RU-003-C |
| **NJ** | `ANNUAL_CAP_BOTH` | $32,300 | $32,300 | — | — | — | — | GL-NJ-2027-RU-001-C |
| **NM** | `ANNUAL_CAP_BOTH` | $27,900 | $27,900 | — | — | — | — | GL-NM-2027-RU-003-C |
| **NV** | `ANNUAL_CAP_BOTH` | $36,600 | $36,600 | — | — | — | — | GL-NV-2027-RU-003-C |
| **NY** | `ANNUAL_CAP_BOTH` | $34,300 | $34,300 | — | — | — | — | GL-NY-2025-RU-001-C |
| **OH** | `ANNUAL_CAP_BOTH` | $46,100 | $46,100 | — | — | — | — | GL-OH-2027-RU-004-C |
| **OK** | `ANNUAL_INDIV_ONLY` | — | $19,200 | — | — | — | 2% per week beyond twelve | GL-OK-2027-RU-003-C |
| **OR** | `ANNUAL_CAP_BOTH` | $54,200 | $54,200 | — | — | — | — | GL-OR-2026-RU-002-C |
| **PA** | `WEEKLY_MINMAX_EXEC + ANNUAL_INDIV` | — | — | $5,200 | $200 | $40 | 2% per week beyond twelve | GL-PA-2027-RU-004-C |
| **PR** | `ANNUAL_CAP_BOTH` | $28,000 | $28,000 | — | — | — | — | GL-PR-2027-RU-003-C |
| **RI** | `ANNUAL_CAP_BOTH` | $52,000 | $52,000 | — | — | — | — | GL-RI-2026-RU-002-C |
| **SC** | `ANNUAL_CAP_BOTH` | $24,100 | $24,100 | — | — | — | — | GL-SC-2027-RU-003-C |
| **SD** | `ANNUAL_CAP_BOTH` | $25,800 | $25,800 | — | — | — | — | GL-SD-2027-RU-003-C |
| **TN** | `WEEKLY_MINMAX_EXEC + ANNUAL_INDIV` | — | — | $13,300 | $500 | $100 | 2% per week beyond twelve | GL-TN-2026-RU-002-C |
| **TX** | `ANNUAL_CAP_BOTH` | $39,800 | $39,800 | — | — | — | — | GL-TX-2025-RU-001-C |
| **UT** | `ANNUAL_CAP_BOTH` | $38,300 | $38,300 | — | — | — | — | GL-UT-2027-RU-003-C |
| **VA** | `ANNUAL_CAP_BOTH` | $45,500 | $45,500 | — | — | — | — | GL-VA-2026-RU-002-C |
| **VT** | `WEEKLY_MINMAX_EXEC + ANNUAL_INDIV` | — | — | $10,400 | $300 | $100 | — | GL-VT-2025-RU-001-C |
| **WA** | `ANNUAL_CAP_BOTH` | $17,800 | $17,800 | — | — | — | — | GL-WA-2026-RU-001-C |
| **WI** | `ANNUAL_CAP_BOTH` | $53,900 | $53,900 | — | — | — | — | GL-WI-2027-RU-004-C |
| **WV** | `ANNUAL_CAP_BOTH` | $39,700 | $39,700 | — | — | — | — | GL-WV-2026-RU-002-C |
| **WY** | `ANNUAL_CAP_BOTH` | $19,500 | $16,200 | — | — | — | — | GL-WY-2026-RU-002-C |

## 5.2 Rule 45 — Liquor Liability Numerical Grade (Subline 332)

CW Rule 45.H defines grade semantics (0 = no cause of action against the vendor; 1–9 = moderate liability; 10 = strict liability) and states *"Refer to the state exceptions for the applicable grade."* The grade itself is therefore a **mandatory state lookup**.


| Grade | # jurisdictions | Jurisdictions |
|---|---|---|
| 0 | 10 | DE, IA, KS, MD, MO, NV, PR, SD, UT, VA |
| 1 | 1 | OK |
| 2 | 1 | WI |
| 3 | 9 | AR, CA, CO, FL, IL, KY, LA, NE, TN |
| 4 | 8 | GA, ID, ME, MN, MS, NJ, OH, OR |
| 5 | 12 | AL, AZ, CT, DC, IN, MI, MT, ND, NM, VT, WA, WY |
| 6 | 7 | MA, NC, NY, RI, SC, TX, WV |
| 7 | 2 | NH, PA |
| 8 | 1 | AK |

| ST | Grade(s) cited | Notice |
|---|---|---|
| AK | 8 | GL-AK-2026-RU-001-C |
| AL | 5 | GL-AL-2027-RU-004-C |
| AR | 3 | GL-AR-2027-RU-003-C |
| AZ | 5 | GL-AZ-2027-RU-003-C |
| CA | 3 | GL-CA-2023-RU-003-C |
| CO | 3 | GL-CO-2027-RU-003-C |
| CT | 5 | GL-CT-2026-RU-002-C |
| DC | 5 | GL-DC-2026-RU-002-C |
| DE | 0 | GL-DE-2027-RU-003-C |
| FL | 3 | GL-FL-2027-RU-003-C |
| GA | 4 | GL-GA-2026-RU-003-C |
| IA | 0 | GL-IA-2026-RU-001-C |
| ID | 4 | GL-ID-2027-RU-003-C |
| IL | 3 | GL-IL-2027-RU-004-C |
| IN | 5 | GL-IN-2027-RU-003-C |
| KS | 0 | GL-KS-2026-RU-002-C |
| KY | 3 | GL-KY-2027-RU-004-C |
| LA | 3 | GL-LA-2027-RU-003-C |
| MA | 6 | GL-MA-2027-RU-003-C |
| MD | 0 | GL-MD-2027-RU-003-C |
| ME | 4 | GL-ME-2027-RU-003-C |
| MI | 5 | GL-MI-2027-RU-003-C |
| MN | 4 | GL-MN-2027-RU-004-C |
| MO | 0 | GL-MO-2026-RU-001-C |
| MS | 4 | GL-MS-2027-RU-003-C |
| MT | 5 | GL-MT-2027-RU-003-C |
| NC | 6 | GL-NC-2026-RU-002-C |
| ND | 5 | GL-ND-2027-RU-003-C |
| NE | 3 | GL-NE-2027-RU-003-C |
| NH | 7 | GL-NH-2027-RU-003-C |
| NJ | 4 | GL-NJ-2027-RU-001-C |
| NM | 5 | GL-NM-2027-RU-003-C |
| NV | 0 | GL-NV-2027-RU-003-C |
| NY | 6 | GL-NY-2025-RU-001-C |
| OH | 4 | GL-OH-2027-RU-004-C |
| OK | 1 | GL-OK-2027-RU-003-C |
| OR | 4 | GL-OR-2026-RU-002-C |
| PA | 7 | GL-PA-2027-RU-004-C |
| PR | 0 | GL-PR-2027-RU-003-C |
| RI | 6 | GL-RI-2026-RU-002-C |
| SC | 6 | GL-SC-2027-RU-003-C |
| SD | 0 | GL-SD-2027-RU-003-C |
| TN | 3 | GL-TN-2026-RU-002-C |
| TX | 6 | GL-TX-2025-RU-001-C |
| UT | 0 | GL-UT-2027-RU-003-C |
| VA | 0 | GL-VA-2026-RU-002-C |
| VT | 5 | GL-VT-2025-RU-001-C |
| WA | 5 | GL-WA-2026-RU-001-C |
| WI | 2 | GL-WI-2027-RU-004-C |
| WV | 6 | GL-WV-2026-RU-002-C |
| WY | 5 | GL-WY-2026-RU-002-C |

## 5.3 Rule 56 — Increased Limits Tables (ILFs) and Table Assignments (ILTAs)

CW Rule 56.B states verbatim: *"The increased limits tables are displayed in the state exceptions."* CW Rule 56.C states the ILTAs are *"displayed in the state company rates/ISO loss costs section or the state increased limits table assignments section by classification code."* **There is no countrywide ILF table.** Every ILF is a state lookup.


| ST | # ILF tables (Rule 56.B.n) | Tables by subline | Basic limit(s) cited | ILTA pages | Notice |
|---|---|---|---|---|---|
| **AK** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-AK-2026-RU-001-C |
| **AL** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-AL-2027-RU-004-C |
| **AR** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-AR-2027-RU-003-C |
| **AZ** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-AZ-2027-RU-003-C |
| **CA** | 7 | 334×3, 335×1, 336×3 | — | Y | GL-CA-2023-RU-003-C |
| **CO** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-CO-2027-RU-003-C |
| **CT** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-CT-2026-RU-002-C |
| **DC** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-DC-2026-RU-002-C |
| **DE** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-DE-2027-RU-003-C |
| **FL** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-FL-2027-RU-003-C |
| **GA** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-GA-2026-RU-003-C |
| **IA** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-IA-2026-RU-001-C |
| **ID** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-ID-2027-RU-003-C |
| **IL** | 8 | 332×1, 334×3, 335×1, 336×3 | — | Y | GL-IL-2027-RU-004-C |
| **IN** | 8 | 334×4, 335×1, 336×3 | $100/200 | Y | GL-IN-2027-RU-003-C |
| **KS** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-KS-2026-RU-002-C |
| **KY** | 8 | 334×4, 335×1, 336×3 | $100/200 | Y | GL-KY-2027-RU-004-C |
| **LA** | 7 | 334×3, 335×1, 336×3 | — | Y | GL-LA-2027-RU-003-C |
| **MA** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-MA-2027-RU-003-C |
| **MD** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-MD-2027-RU-003-C |
| **ME** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-ME-2027-RU-003-C |
| **MI** | 7 | 334×3, 335×1, 336×3 | — | Y | GL-MI-2027-RU-003-C |
| **MN** | 8 | 332×1, 334×3, 335×1, 336×3 | $100/200 | Y | GL-MN-2027-RU-004-C |
| **MO** | 8 | 334×4, 335×1, 336×3 | $100/200 | Y | GL-MO-2026-RU-001-C |
| **MS** | 8 | 334×4, 335×1, 336×3 | — | Y | GL-MS-2027-RU-003-C |
| **MT** | 8 | 334×4, 335×1, 336×3 | $100/200 | Y | GL-MT-2027-RU-003-C |
| **NC** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-NC-2026-RU-002-C |
| **ND** | 8 | 334×4, 335×1, 336×3 | $100/200 | Y | GL-ND-2027-RU-003-C |
| **NE** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-NE-2027-RU-003-C |
| **NH** | 8 | 334×4, 335×1, 336×3 | $100/200 | Y | GL-NH-2027-RU-003-C |
| **NJ** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-NJ-2027-RU-001-C |
| **NM** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-NM-2027-RU-003-C |
| **NV** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-NV-2027-RU-003-C |
| **NY** | 7 | 334×3, 335×1, 336×3 | — | Y | GL-NY-2025-RU-001-C |
| **OH** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-OH-2027-RU-004-C |
| **OK** | 8 | 334×4, 335×1, 336×3 | $100/200 | Y | GL-OK-2027-RU-003-C |
| **OR** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-OR-2026-RU-002-C |
| **PA** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-PA-2027-RU-004-C |
| **PR** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-PR-2027-RU-003-C |
| **RI** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-RI-2026-RU-002-C |
| **SC** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-SC-2027-RU-003-C |
| **SD** | 7 | 334×3, 335×1, 336×3 | — | Y | GL-SD-2027-RU-003-C |
| **TN** | 8 | 334×4, 335×1, 336×3 | — | Y | GL-TN-2026-RU-002-C |
| **TX** | 7 | 334×3, 335×1, 336×3 | — | Y | GL-TX-2025-RU-001-C |
| **UT** | 9 | 332×1, 334×4, 335×1, 336×3 | $100/200 | Y | GL-UT-2027-RU-003-C |
| **VA** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-VA-2026-RU-002-C |
| **VT** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-VT-2025-RU-001-C |
| **WA** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-WA-2026-RU-001-C |
| **WI** | 7 | 334×3, 335×1, 336×3 | — | Y | GL-WI-2027-RU-004-C |
| **WV** | 7 | 334×3, 335×1, 336×3 | — | Y | GL-WV-2026-RU-002-C |
| **WY** | 7 | 334×3, 335×1, 336×3 | $100/200 | Y | GL-WY-2026-RU-002-C |

## 5.4 Territory rating

27 of 51 jurisdictions carry an explicit A-rule *"Rating Territories For Premises And Operations (Subline Code 334) [and Liquor Liability (Subline Code 332)]"*. Where present it defines territory as a **USPS ZIP-code** geography resolved by *location of the insured risk* (not the mailing address).

> ### ✅ Corrected — the Territory Definitions are in this corpus
>
> The statement that the definitions are *"held outside the Rules manual"* was **wrong**. Every
> Rules notice carries **Territory Pages** (`CG-T-1` … `CG-T-n`) after the exception pages, and
> in multi-territory jurisdictions those pages contain the **full ZIP → territory table**:
>
> ```
> GL-NJ-2026-RU-001-C.pdf, page 27, CG-T-1
>   C. Territory Definitions For Premises And Operations Liability (Subline Code 334)
>      And Liquor Liability (Subline Code 332)
>        501 - Atlantic City ZIP Codes          506 - Newark and Vicinity ZIP Codes
>        502 - Remainder of Essex County        ...
>   "The Territory Definitions Tables in numerical ZIP Code order follow."
>
> pages 28-37, CG-T-2 ... CG-T-11
>   ZIP Codes/Territories In Numerical Order By ZIP Code
>     07001 AVENEL 516 | 07002 BAYONNE 504 | 07003 BLOOMFIELD 503 | ...
> ```
>
> New Jersey alone carries **721 ZIP rows** across ten `CG-T` pages. See §5.4.1.

> ### ⚠ Corrected at Step 7 — the A-rule is not the test for territory rating
>
> The loss cost pages publish a separate Premises/Operations grid **per territory**, which
> makes the territory count directly observable. Against that evidence:
>
> - All **27** A-rule jurisdictions are indeed multi-territory. ✔
> - But **31** jurisdictions are multi-territory. **CA, FL, NY and TX are territory-rated and
>   carry no territory A-rule** — and they are among the most territorialised in the program
>   (NY **20** territories, CA **11**, TX **8**, FL **5**).
>
> The `Y`/`—` column below records *whether the Rules exception pages carry the A-rule*. It
> must **not** be used to decide whether to perform a territory lookup; use the territory count
> in [`A4-LOSS-COST-INVENTORY.md`](A4-LOSS-COST-INVENTORY.md) §A4.1.
>
> Two further facts from the rate pages:
> - **Territory applies to Premises/Operations (334) and Liquor Liability (332).** The `CG-T-1`
>   definitions page names both. Products/Completed Operations (336), OCP/Railroad Protective
>   (335) and Pollution (350) are written to the reserved statewide territory `999` in all 51
>   jurisdictions. The loss cost pages show only the 334 half, because there are no liquor loss
>   cost pages — the 332 half is visible **only** on the Territory Pages.
> - Territory numbers occupy two disjoint families, `001`–`024` and `501`–`517`, never mixed
>   within a jurisdiction, and are **not contiguous** (Illinois: `501, 504, 506, 507, 508, 509,
>   514`). Store the enumerated set, not a range.

### 5.4.1 Territory Pages — the definitions, and the two schemes

Every Rules notice ends with **Territory Pages** (`CG-T-1` … `CG-T-n`), and **all 51
jurisdictions carry them**. `CG-T-1` always assigns the non-territorial sublines first —
OCP and Railroad Protective (335), Pollution (350) and Products/Completed Operations (336) to
`ENTIRE STATE … 999` — then defines the territories for **Premises and Operations (334) and
Liquor Liability (332)**.

How those territories are *resolved* splits the corpus in three:

| Scheme | Jurisdictions | `CG-T` structure | Engine input required |
|---|---|---|---|
| **ZIP table** | **27** | `CG-T-1` names each territory, `CG-T-2…n` list *"ZIP Codes/Territories In Numerical Order By ZIP Code"* | 5-digit ZIP |
| **County / city** | **4** — CA, FL, NY, TX | `CG-T-1` defines territories by county and named city or borough, followed by a `LIST OF IMPORTANT CITIES AND TOWNS` mapping *City, County → territory* | County **and** city/place name |
| **Entire state** | **20** | `CG-T-1` only: *"ENTIRE STATE … 001"* | none |

Volume in the latest notice per jurisdiction: **23,719 ZIP rows** across the 27 ZIP-scheme
jurisdictions (PA 2,162 · IL 1,569 · MI 1,159 · MO 1,155 · VA 1,223 · IA 1,055 · OH 1,413 …),
plus **432 city/county rows** in the four county-scheme jurisdictions (CA 275, NY 83, TX 49,
FL 25).

**The A-rule marks the ZIP scheme, not territory rating.** The 27 jurisdictions carrying the
*"Rating Territories…"* A-rule are **exactly** the 27 with ZIP tables. CA, FL, NY and TX are
territory-rated under the older county/city scheme, which is why they have no such A-rule —
and it is why gating a territory lookup on the A-rule mis-rates them.

**Cross-validated against the rate pages.** The territory codes on the `CG-T` pages match the
territories published on the loss cost grids in **all 51 jurisdictions**, with zero mismatches
(NJ 15, NY 20, CA 11, PA 11, OH 10, MA 9, CT 8, TX 8 …). Two independently produced corpora
agreeing exactly on 51 domains is strong evidence that both parses are correct.

> **The county/city scheme is the harder engineering problem**, despite being 55× smaller. A
> ZIP is an exact key supplied on every submission; *"Ardsley, Westchester"* requires the risk
> address's county and a name match against a 1997-vintage place list. Model it as a distinct
> resolver with an explicit **unmatched → referral** path; never fuzzy-match silently.


| ST | Territory A-rule present | ZIP-code basis stated |
|---|---|---|
| AK | — | — |
| AL | Y | Y |
| AR | — | — |
| AZ | Y | Y |
| CA | — | — |
| CO | Y | Y |
| CT | Y | Y |
| DC | — | — |
| DE | — | — |
| FL | — | — |
| GA | Y | Y |
| IA | Y | Y |
| ID | — | — |
| IL | Y | Y |
| IN | Y | Y |
| KS | Y | Y |
| KY | Y | Y |
| LA | Y | Y |
| MA | Y | Y |
| MD | Y | Y |
| ME | — | — |
| MI | Y | Y |
| MN | Y | Y |
| MO | Y | Y |
| MS | — | — |
| MT | — | — |
| NC | — | — |
| ND | — | — |
| NE | Y | Y |
| NH | — | — |
| NJ | Y | Y |
| NM | — | — |
| NV | — | — |
| NY | — | — |
| OH | Y | Y |
| OK | Y | Y |
| OR | Y | Y |
| PA | Y | Y |
| PR | — | — |
| RI | Y | Y |
| SC | — | — |
| SD | — | — |
| TN | Y | Y |
| TX | — | — |
| UT | — | — |
| VA | Y | Y |
| VT | — | — |
| WA | Y | Y |
| WI | Y | Y |
| WV | — | — |
| WY | — | — |

## 5.5 Stop Gap — Employers Liability

Present only in the monopolistic-fund jurisdictions: ND, OH, PR, WA, WY.


## 5.6 Estimated Loss Potentials (ELP)

CW Rule 2.B directs that ELPs are supplied in a **separate ELP Supplement** for classifications with no manual rate/loss cost. 27 of 51 current Rules notices reference it.

> ### ✅ Supplied at Step 7
>
> The ELP Supplement **is** in the project corpus — it is the first nine pages
> (`CG-ELP-1`…`CG-ELP-9`) of every loss cost notice, present in **51 of 51** jurisdictions and
> in all 471 readable notices. Roughly **404 classes** per jurisdiction carry an entry.
>
> The "27 of 51" figure above counts jurisdictions whose *rules* cite the Supplement. It is not
> a measure of ELP availability, and an engine must not gate ELP lookup on it.
>
> Full structure, the four-valued cell vocabulary (`Manual` / `$n.nn` + H/R / `RTC` / `Incl.`)
> and the Homogeneity–Reliability index semantics are in
> [`13-LOSS-COSTS-AND-ELP.md`](13-LOSS-COSTS-AND-ELP.md) §13.5.

---

## 5.7 Published loss costs

Every rate lookup the algorithm performs is now backed by a source. Summary; detail in
[`13-LOSS-COSTS-AND-ELP.md`](13-LOSS-COSTS-AND-ELP.md) and
[`A4-LOSS-COST-INVENTORY.md`](A4-LOSS-COST-INVENTORY.md).

| Subline | Coverage | Published loss costs | Key | Basic limit |
|---|---|---|---|---|
| **334** | Premises/Operations | **51/51** | class × territory | $100,000/$200,000 |
| **336** | Products/Completed Operations | **51/51** | class × territory `999` (statewide) | $100,000/$200,000 |
| **335** | OCP / Principals Protective | **15/51** — withdrawn in the 2027 notices; ELP-only elsewhere | class, all territories | $100,000/$200,000 |
| **370** | Unmanned Aircraft | **51/51** — identical values countrywide; **flat dollar charges, not rates** | take-off weight × endorsement | $100,000/$200,000 |
| **332** | Liquor Liability | **0/51** — ELP only (Table 5.D) | — | $100,000/$200,000 |
| **335** | Railroad Protective | **0/51** — ELP only (Table 5.E) | trains per day | **$100,000/$300,000** |

Loss cost grid cell vocabulary, across ~429,700 cells in the current notices:

| Cell | Share | Meaning |
|---|---|---|
| numeric | 64.3% | Published ISO loss cost (pre-LCM) |
| `–` | 18.6% | Coverage not offered — this is Rule 48.F.1's `(−)` marker |
| `(a)` | 17.1% | Refer to company; consult the ELP |

