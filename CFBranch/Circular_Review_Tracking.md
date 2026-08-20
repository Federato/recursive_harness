# CF Circular Review Tracking Ledger

**Purpose:** a master record of every ISO CF (Commercial Property) manual circular/notice this
project has on disk, whether it's been extracted, and whether it's been reviewed — so a future
session can check this file first and skip re-reading a document already covered here. Update this
file every time a circular is opened, not just when new PDFs arrive.

**Source PDFs:** `Recursive_Harness_2.0\Commercial Line Manuals\CF\` — 46 states + DC + CW, every
state now on disk except the four in "Pending acquisition" below.
**Extracted text:** `Recursive_Harness_2.0\Agentic\cf-circular-expert\text\rules\`
**Built:** 2026-08-19. **Last updated:** 2026-08-19 (same day — fourth pass: MI through WY, 27 states
at once, extracted and characterized; GA/IA/IL/IN/KS/KY/MA/MD/ME in the third; CO/CT/DC/DE/FL in the
second; AK/AL/AR/AZ/CA in the first).

**A note on format from here on.** The first three passes (19 jurisdictions) used one full table row
per document — file, edition, pages, filing ref, circular ref, level. At 376 total documents that
stops being maintainable. **From this pass forward, states are tracked at one row per state** —
notice count, page range, exception-rule range, state-rule range, and anything genuinely unusual —
with full per-document detail reserved for a state once it's promoted to L3. This trades document-
level granularity for keeping the ledger actually readable; the underlying `.txt` files and
`knowledge/notices.json` still hold the per-document data if it's ever needed.

---

## Pending acquisition — not yet in this project's corpus

| Jurisdiction | Status | Note |
|---|---|---|
| **Idaho (ID)** | **Access needs to be secured** | Directed 2026-08-19. No `CF-ID-*` PDFs exist anywhere under `Commercial Line Manuals\CF\` yet — this is a note that we need the documents, not a claim that Idaho has been reviewed and found absent from ISO's filings. Once PDFs land in a sibling `ID\` folder (matching the pattern every other state used), re-run `scripts/16_extract_cf_manuals.py` — it already sweeps every subfolder automatically — then add an Idaho section to this ledger the same way CO/CT/DC/DE/FL were added in the second ingestion pass. |
| **Louisiana (LA)** | **Access needs to be secured** | Directed 2026-08-19. Same status as Idaho, same next step: no `CF-LA-*` PDFs on disk yet, re-run the extraction script once a sibling `LA\` folder lands. |
| **Mississippi (MS)** | **Access needs to be secured** | Directed 2026-08-19. Same status as Idaho/Louisiana: no `CF-MS-*` PDFs on disk yet, re-run the extraction script once a sibling `MS\` folder lands. |
| **Washington (WA)** | **Access needs to be secured** | Directed 2026-08-19. Same status as Idaho/Louisiana/Mississippi: no `CF-WA-*` PDFs on disk yet. Not to be confused with the District of Columbia (`DC`), already ingested — this is Washington State. |

---

## Review-level legend

| Level | Meaning |
|---|---|
| **L0 — not extracted** | PDF exists on disk, no text file yet |
| **L1 — extracted** | Page-tagged text exists (`text/rules/*.txt`), nobody has looked at the content |
| **L2 — characterized** | Front matter read (circular ref, filing ref, edition stamp); for state notices, the "ADDITIONAL RULE(S)" exception-page section was scanned for which manual rule numbers it touches. **Not a line-by-line read of the rule text itself.** |
| **L3 — deep-read** | Actual rule text compared against the countrywide baseline and/or the ERC rating docs, rule by rule |

**Everything in this ledger is currently L2 at best.** No document in this project has reached L3 yet.
Don't let "reviewed" in casual conversation get read as "fully read" — check the level column.

---

## Countrywide (`CW`, filed as jurisdiction `MU`) — 6 notices, all L2

Full manual reprints, not exception pages — confirmed 2026-08-19 (Entry 7): Division Five, Fire and
Allied Lines, Multistate Rules. ~342–346 pages each. Partial rule-number TOC index is in
`knowledge/rule_index.json` (~35 of an estimated 85+ rules — now known to run at least to Rule 85,
see the state-notice findings below).

| File | Edition year | Pages | Level | Notes |
|---|---|---|---|---|
| `CF-MU-2020-RU-001-C.pdf` | 2020 | 344 | L2 | 10th Edition per TOC stamp |
| `CF-MU-2022-RU-001-C.pdf` | 2022 | 346 | L2 | |
| `CF-MU-2023-RU-001-C.pdf` | 2023 | 342 | L2 | |
| `CF-MU-2023-RU-002-C.pdf` | 2023 | 342 | L2 | second 2023 notice — supersession relationship to `-001` not checked |
| `CF-MU-2026-RU-001-C.pdf` | 2026 | 342 | L2 | 14th Edition per TOC stamp — this is the edition Rule 71/Broad-Form cross-check (Entry 7) was read against |
| `CF-MU-2027-RU-001-C.pdf` | 2027 | 344 | L2 | future-effective edition — not yet compared against the 2026 edition for what changed |

---

## Findings that apply across every state notice (read this before opening another one)

All nineteen state/DC jurisdictions ingested so far (AK, AL, AR, AZ, CA, CO, CT, DC, DE, FL, GA, IA,
IL, IN, KS, KY, MA, MD, ME) file their content as **exception pages**, not full manual reprints — confirmed directly by front-matter text:
"COMMERCIAL LINES MANUAL / DIVISION FIVE / FIRE AND ALLIED LINES / EXCEPTION PAGES / \<STATE\>
(\<code\>)" followed by an "ADDITIONAL RULE(S)" section. Page counts are 22–80, not 300+. **This
resolves the open question `cf-circular-expert/AGENT.md` was carrying since Entry 6/7** ("does CF
rules vary meaningfully by state, or are they mostly countrywide-uniform with thin exceptions") — thin
exceptions, confirmed, now across ten jurisdictions.

**A near-universal core set of countrywide rule numbers gets exception-paged in almost every state and
every edition**: Rules **2, 14, 38, 50, 72, 73, 75, 81, 82, 85** appear in the exception-rule list of
nearly every notice across all ten jurisdictions. Rules 81 and 82 are new numbers not previously in
`knowledge/rule_index.json` — confirmed from California's front matter to be **"Rule 81. Revision And
Expansion Of Deductible Insurance Plan"** and **"Rule 82. Windstorm Or Hail Percentage Deductibles."**
Rule 85 ("Basic Group I Class Rates," per the CW TOC) also recurs everywhere, consistent with it being a
rate-table appendix every state customizes. **`rule_index.json` should be extended with rules 81/82/83**
(83 now confirmed present in Alabama, Arkansas, Connecticut, Maine, Massachusetts's exception lists —
still not titled) — not done in this pass, flagged as a follow-up, now for the third time.

**Each state also files its own numbered "state rules," `A1` through roughly `A9`–`A14`, on top of the
countrywide rule exceptions** — these are wholly state-specific additions with no countrywide-rule
counterpart (e.g. Alaska's `RULE A2` is "Coverage For Year 2000 Computer-Related And Other Electronic
Problems," attaching form `CP 15 57`). The count of state rules grows over time within a state (Alaska:
A1–A9 in 2020, A1–A10 by 2023) — new state-specific rules get added edition to edition, not just
countrywide rules changing.

**Florida (single document on file) has by far the broadest exception-rule set seen yet** —
2/4/9/10/11/13/14/17/21/25/33/36/38/50/54/70/72/73/74/75/81/82/85, wider even than California's, plus
the full A1–A14 state-rule set in its very first (and so far only) notice. That makes Florida, not just
California, a strong L3 candidate — see the updated suggested order at the end of this document.

**The `CL-`-prefixed filing reference is a real, recurring second filing family, not a typo — now
confirmed at scale.** What looked like an anomaly in Arkansas (`CL-2025-RRU1`, first pass) then showed
up a few more times in the second pass; by this third pass it's present in **ten of nineteen
jurisdictions**: AR, CT, DC (as the outlier `CA-2023-REQRU`, still unexplained — see below), DE, FL, GA
(three separate `CL-` refs), IN (three), KY (four — the most of any state), MA (two, including the
**oldest filing-ref timestamp seen in this corpus, `CL-2019-OMJRU`**), and ME. At this frequency, `CL-`
almost certainly denotes a distinct, real ISO filing-reference family (state-only filings not tied to a
multistate `CF-` circular, is one plausible read, not confirmed) — this project should stop treating it
as an anomaly and instead work out what it actually denotes. DC's `CA-2023-REQRU` remains the one
genuinely odd entry — California's state-code prefix on a DC document, still unexplained, still worth a
closer look specifically.

**None of the actual rule *text* has been read yet** — this pass identified *which* rule numbers each
notice touches, not what the exception says. That's L2, not L3. See the per-state tables below for
exactly which numbers, per edition.

---

## Alaska (`AK`) — 6 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-AK-2020-RU-001-C.pdf` | 2020 | 38 | CF-2020-RCYRU | (not captured — front matter blank/unparsed) | L2 |
| `CF-AK-2023-RU-001-C.pdf` | 2023 | 50 | CF-2021-RCCRU | LI-CF-2023-018 (02/09/2023) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-AK-2024-RU-001-C.pdf` | 2024 | 36 | CF-2023-RDEQR | LI-CF-2023-117 (09/28/2023) — CP Multistate Earthquake Deductible Option | L2 |
| `CF-AK-2025-RU-001-C.pdf` | 2025 | 36 | (not captured) | LI-CF-2025-029 (03/03/2025) — CP Annual ZIP Code Territory Update | L2 |
| `CF-AK-2025-RU-002-C.pdf` | 2025 | 38 | CF-2024-RDED1 | LI-CF-2025-053 (06/12/2025) — Alaska Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-AK-2026-RU-001-C.pdf` | 2026 | 38 | CF-2025-RRU25 | LI-CF-2026-002 (01/09/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Rule-number drift across editions, briefly**: 2020's exception set is rules 2/11/14/17/25/31/38/50/51/
53/54/67/70/72/73/75/77/81/82/85 + state rules A1–A10 (missing A8). By 2023, rule 36 and state rule A8
are added. By 2024, rule 67 drops out and rules 39/76 are added. 2025 onward holds steady at that set.
**Not independently verified against the rule *text*** — this is a numbers-only diff.

---

## Alabama (`AL`) — 6 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-AL-2020-RU-001-C.pdf` | 2020 | 34 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-AL-2022-RU-001-C.pdf` | 2022 | 34 | CF-2021-RCCRU | LI-CF-2021-073 (12/10/2021) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-AL-2023-RU-001-C.pdf` | 2023 | 34 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 |
| `CF-AL-2023-RU-002-C.pdf` | 2023 | 34 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-AL-2025-RU-001-C.pdf` | 2025 | 36 | CF-2024-RDED1 | LI-CF-2024-124 (09/26/2024) — Alabama Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-AL-2026-RU-001-C.pdf` | 2026 | 36 | CF-2025-RRU25 | LI-CF-2026-002 (01/09/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set, stable across the whole run**: 2/14/18/38/50/69/70/73/74/75/81/82/83/85 + state
rules A1–A14 (all six editions carry the full A1–A14 set — no drift observed, unlike Alaska). Rule 72
only appears starting with the 2026 edition. Alabama carries **rule 83**, which Alaska's list does not
— worth checking what 83 covers when a text-level pass happens.

---

## Arkansas (`AR`) — 10 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-AR-2020-RU-001-C.pdf` | 2020 | 34 | (not captured) | (not captured) | L2 |
| `CF-AR-2020-RU-002-C.pdf` | 2020 | 34 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-AR-2022-RU-001-C.pdf` | 2022 | 34 | CF-2021-RCCRU | LI-CF-2021-073 (12/10/2021) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-AR-2023-RU-001-C.pdf` | 2023 | 34 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 |
| `CF-AR-2023-RU-002-C.pdf` | 2023 | 34 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-AR-2025-RU-001-C.pdf` | 2025 | 36 | CF-2024-RDED1 | LI-CF-2024-100 (08/22/2024) — Arkansas Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-AR-2025-RU-002-C.pdf` | 2025 | 36 | (not captured) | LI-CF-2025-029 (03/03/2025) — CP Annual ZIP Code Territory Update | L2 |
| `CF-AR-2026-RU-001-C.pdf` | 2026 | 36 | CF-2025-RRU25 | LI-CF-2026-002 (01/09/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |
| `CF-AR-2026-RU-002-C.pdf` | 2026 | 36 | CL-2025-RRU1 | (not captured) | L2 — **note the filing-ref prefix is `CL-`, not `CF-`, the only one seen in this batch; worth checking whether that's a typo in the filed document or a genuinely different filing family** |
| `CF-AR-2027-RU-001-C.pdf` | 2027 | 36 | CF-2025-R25RU | LI-CF-2026-303 (07/22/2026) — CP Multistate Revision Of The Specific [Insurance clause, title truncated] | L2 |

**Exception rule set**: 2/14/30/50/72/73/74/75/81/82/85 + state rules A1–A11, growing to A1–A12 by the
2025-002 notice. **Two notices exist for both 2020 and 2025 and 2026** — supersession order within a
year not checked (e.g. does `-002` replace `-001`, or do both remain in force for different periods?
This is exactly the kind of question `date_confidence` in GL's `notices.json` schema exists to answer,
and this project's CF registry doesn't populate that field yet).

---

## Arizona (`AZ`) — 8 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-AZ-2020-RU-001-C.pdf` | 2020 | 30 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-AZ-2022-RU-001-C.pdf` | 2022 | 30 | CF-2021-RCCRU | LI-CF-2021-073 (12/10/2021) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-AZ-2022-RU-002-C.pdf` | 2022 | 30 | (not captured) | (not captured) | L2 |
| `CF-AZ-2023-RU-001-C.pdf` | 2023 | 22 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 — **page count drops from 30 to 22 here; worth checking what content left rather than assuming it's noise** |
| `CF-AZ-2023-RU-002-C.pdf` | 2023 | 22 | CF-2022-ORU1 | LI-CF-2023-003 (01/10/2023) — Arizona Commercial Property Rules Filed And To Be [effective date, title truncated] | L2 |
| `CF-AZ-2023-RU-003-C.pdf` | 2023 | 22 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-AZ-2025-RU-001-C.pdf` | 2025 | 24 | CF-2024-RDED1 | LI-CF-2024-108 (08/28/2024) — Arizona Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-AZ-2026-RU-001-C.pdf` | 2026 | 24 | CF-2025-RRU25 | LI-CF-2026-100 (03/04/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set**: 2/14/38/50/69/72/73/75/81/82/85 + state rules A1–A12; rules 21 and 36 join
starting with the 2023-002 notice. Arizona is the shortest-page-count state ingested (22–30 pages) —
worth noting as the current low end when a future pass wants a quick state to spot-check text-level.

---

## California (`CA`) — 10 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-CA-2021-RU-001-C.pdf` | 2021 | 60 | CF-2020-OZC1 | (not captured) | L2 |
| `CF-CA-2021-RU-002-C.pdf` | 2021 | 64 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-CA-2021-RU-003-C.pdf` | 2021 | 64 | CF-2021-OZC1 | (not captured) | L2 |
| `CF-CA-2023-RU-001-C.pdf` | 2023 | 64 | CF-2022-OZC1 | LI-CF-2022-125 (09/16/2022) — California CP ZIP Code Territory Definition [update, title truncated] | L2 |
| `CF-CA-2023-RU-002-C.pdf` | 2023 | 76 | CF-2021-RCCRU | LI-CF-2023-040 (03/27/2023) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-CA-2024-RU-001-C.pdf` | 2024 | 76 | CF-2023-OZC1 | LI-CF-2023-108 (08/25/2023) — California CP ZIP Code Territory Definition [update] | L2 |
| `CF-CA-2024-RU-002-C.pdf` | 2024 | 80 | CF-2022-RRU1 | LI-CF-2024-001 (01/05/2024) — California New Individual Risk Wildfire Mitigation Premium [program, title truncated] | L2 — **California-specific wildfire program; no equivalent rule seen in any other state's exception list so far** |
| `CF-CA-2025-RU-001-C.pdf` | 2025 | 66 | CF-2023-RDEQR | LI-CF-2025-074 (07/25/2025) — CP Multistate Earthquake Deductible Option | L2 |
| `CF-CA-2026-RU-001-C.pdf` | 2026 | 66 | CF-2024-RDED1 | LI-CF-2026-212 (06/01/2026) — California Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-CA-2026-RU-002-C.pdf` | 2026 | 66 | CF-2026-OZC1 | LI-CF-2026-264 (06/26/2026) — California CP ZIP Code Territory Definition [update] | L2 |

**Exception rule set**: 2/5/10/11/13/14/17/20/25/38/50/54/72/73/75/80/81/82 + state rules A1–A9, growing
to A1–A11 by 2025. California carries the largest exception-rule set of the five states ingested (18
countrywide rules touched, vs. Arizona's 11) and is the only state seen so far with its own **Rule A1,
"Building Code Effectiveness Grading"** — confirmed by direct front-matter read (see the earlier session
excerpt) — plus rules 5, 10, 13, 20, and 80, none of which appear in any other state's exception list.
**California is very likely the highest-value state for a future L3 pass** given both its exception-rule
breadth and its three ZIP-code-territory-definition notices (`-OZC1` filings), which plausibly interact
with whatever territory logic the ERC side uses (`BasicGroupIRatingTerrFactor`, `BasicGroupIIRatingTerr`,
etc. — not cross-checked against these notices in this pass).

---

## Colorado (`CO`) — 10 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-CO-2020-RU-001-C.pdf` | 2020 | 34 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-CO-2021-RU-001-C.pdf` | 2021 | 34 | (not captured) | (not captured) | L2 |
| `CF-CO-2022-RU-001-C.pdf` | 2022 | 34 | CF-2021-RCCRU | LI-CF-2021-073 (12/10/2021) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-CO-2023-RU-001-C.pdf` | 2023 | 34 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 |
| `CF-CO-2023-RU-002-C.pdf` | 2023 | 34 | (not captured) | LI-CF-2023-030 (03/06/2023) — CP Annual ZIP Code Territory Update | L2 |
| `CF-CO-2023-RU-003-C.pdf` | 2023 | 34 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-CO-2024-RU-001-C.pdf` | 2024 | 33 | (not captured) | LI-CF-2024-015 (03/05/2024) — CP Annual ZIP Code Territory Update | L2 |
| `CF-CO-2024-RU-002-C.pdf` | 2024 | 32 | (not captured) | LI-CF-2024-015 (03/05/2024) — CP Annual ZIP Code Territory Update — **same circular as -001, two notices; supersession/split not determined** | L2 |
| `CF-CO-2025-RU-001-C.pdf` | 2025 | 32 | CF-2024-RDED1 | LI-CF-2024-072 (07/02/2024) — Colorado Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-CO-2026-RU-001-C.pdf` | 2026 | 32 | CF-2025-RRU25 | LI-CF-2026-002 (01/09/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set, stable across the whole run**: 2/14/50/72/73/74/75/81/82/85 + state rules
A1–A12, no drift observed across all ten editions — the flattest, most stable rule-number profile of
any state ingested so far.

---

## Connecticut (`CT`) — 9 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-CT-2020-RU-001-C.pdf` | 2020 | 34 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-CT-2021-RU-001-C.pdf` | 2021 | 34 | (not captured) | (not captured) | L2 |
| `CF-CT-2022-RU-001-C.pdf` | 2022 | 34 | CF-2021-RCCRU | LI-CF-2022-021 (03/07/2022) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-CT-2023-RU-001-C.pdf` | 2023 | 34 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 |
| `CF-CT-2023-RU-002-C.pdf` | 2023 | 34 | **CL-2022-ORU1** | LI-CF-2023-036 (03/13/2023) — Connecticut Revised Spoilage And Utility Services Rules | L2 — non-`CF-` filing prefix, see cross-state findings above |
| `CF-CT-2023-RU-003-C.pdf` | 2023 | 34 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-CT-2025-RU-001-C.pdf` | 2025 | 36 | CF-2024-RDED1 | LI-CF-2024-121 (09/23/2024) — Connecticut Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-CT-2026-RU-001-C.pdf` | 2026 | 36 | CF-2025-RRU25 | LI-CF-2026-143 (04/01/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |
| `CF-CT-2027-RU-001-C.pdf` | 2027 | 36 | CF-2025-R25RU | LI-CF-2026-303 (07/22/2026) — CP Multistate Revision Of The Specific [Insurance clause, title truncated] | L2 |

**Exception rule set**: 2/11/13/28/37/38/50/69/70/73/74/75/81/82/**83**/85 + state rules A1–A13 — the
widest state-rule count (A1–A13) among the non-Florida states, and the first place rule **28** and
**37** were seen (neither appears in any of the first five states' lists). Rule 72 joins starting with
the 2023-001 notice. Confirmed carrying rule 83, same as Alabama and Arkansas.

---

## District of Columbia (`DC`) — 6 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-DC-2020-RU-001-C.pdf` | 2020 | 22 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-DC-2022-RU-001-C.pdf` | 2022 | 22 | CF-2021-RCCRU | LI-CF-2022-023 (03/16/2022) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-DC-2023-RU-001-C.pdf` | 2023 | 22 | CF-2022-REQRU | LI-CF-2023-013 (01/31/2023) — CP Multistate Earthquake Rules And Loss [Costs, title truncated] | L2 |
| `CF-DC-2023-RU-002-C.pdf` | 2023 | 22 | **CA-2023-REQRU** | LI-CF-2023-076 (06/29/2023) — CP Multistate Earthquake Rules Revisions | L2 — filing ref carries California's state code prefix on a DC document; see cross-state findings above, not resolved |
| `CF-DC-2025-RU-001-C.pdf` | 2025 | 24 | CF-2024-RDED1 | LI-CF-2024-115 (09/09/2024) — District Of Columbia Revision And Expansion Of Deductible [Insurance Plan] | L2 |
| `CF-DC-2026-RU-001-C.pdf` | 2026 | 24 | CF-2025-RRU25 | LI-CF-2026-197 (05/07/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set**: 2/14/38/50/69/70/73/74/75/81/82/85 + state rules A1–A9, stable across all six
editions — DC has the smallest state-rule set (only A1–A9, never grows) and the smallest page counts
(22–24) of any jurisdiction ingested so far. Rule 72 only joins in the 2026 edition.

---

## Delaware (`DE`) — 7 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-DE-2020-RU-001-C.pdf` | 2020 | 26 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-DE-2023-RU-001-C.pdf` | 2023 | 26 | CF-2021-RCCRU | LI-CF-2022-136 (09/22/2022) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-DE-2024-RU-001-C.pdf` | 2024 | 26 | CF-2022-REQRU | LI-CF-2023-074 (06/29/2023) — CP Multistate Earthquake Rules And Loss [Costs] | L2 |
| `CF-DE-2024-RU-002-C.pdf` | 2024 | 26 | CF-2023-REQRU | LI-CF-2023-075 (06/29/2023) — CP Multistate Earthquake Rules Revisions | L2 — **same-day circulars as -001 (06/29/2023) but different filing refs; likely a Basic-vs-Special earthquake-rules split, not confirmed** |
| `CF-DE-2025-RU-001-C.pdf` | 2025 | 28 | CF-2024-RDED1 | LI-CF-2024-112 (09/05/2024) — Delaware Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-DE-2026-RU-001-C.pdf` | 2026 | 28 | **CL-2025-ORU1** | (not captured) | L2 — non-`CF-` filing prefix, see cross-state findings above |
| `CF-DE-2026-RU-002-C.pdf` | 2026 | 28 | CF-2025-RRU25 | LI-CF-2026-002 (01/09/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 — **two 2026 notices; supersession order not determined, same open question as Arkansas/Colorado** |

**Exception rule set**: 2/14/50/70/73/74/75/81/82/85 + state rules A1–A11; rule 72 joins starting with
the 2024-001 notice. Similar profile shape to Colorado's.

---

## Florida (`FL`) — 1 notice, L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-FL-2022-RU-001-C.pdf` | 2022 | 60 | CL-2021-RRU1 | LI-CF-2021-082 (12/27/2021) — Florida New And Revised Rules To Be Implemented | L2 — non-`CF-` filing prefix (`CL-`), consistent with the pattern seen in CT/DC/DE |

**Only one Florida notice exists in this project's corpus, and it already has the single broadest
exception-rule set of any jurisdiction ingested**: 2/4/9/10/11/13/14/17/21/25/33/36/38/50/54/70/72/73/
74/75/81/82/85 (23 countrywide rules touched) plus the full state-rule set A1–A14. Rule **9** and **33**
are still unique to Florida after nineteen jurisdictions; rules 4 and 21 turned out not to be — Maine
and Massachusetts also carry rule 4, and Maine's 2025-002/2026-001 editions pick up rule 21 too (see
below). Given both the breadth and that no later Florida edition has been collected yet to compare
against, **Florida is still the single strongest L3 candidate in this corpus** — more so than
California — precisely because its 2022 notice alone already reveals more structure than most states
show across five-plus editions.

---

## Georgia (`GA`) — 8 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-GA-2020-RU-001-C.pdf` | 2020 | 46 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-GA-2021-RU-001-C.pdf` | 2021 | 46 | (not captured) | (not captured) | L2 |
| `CF-GA-2024-RU-001-C.pdf` | 2024 | 46 | CL-2023-ORU1 | (not captured) | L2 — `CL-` filing prefix |
| `CF-GA-2024-RU-002-C.pdf` | 2024 | 38 | CF-2023-RDEQR | LI-CF-2023-140 (11/03/2023) — CP Multistate Earthquake Deductible Option | L2 |
| `CF-GA-2025-RU-001-C.pdf` | 2025 | 38 | CL-2024-OCMF2 | (not captured) | L2 — `CL-` filing prefix |
| `CF-GA-2025-RU-002-C.pdf` | 2025 | 40 | CL-2024-OWS1 | (not captured) | L2 — `CL-` filing prefix |
| `CF-GA-2026-RU-001-C.pdf` | 2026 | 42 | CF-2024-RDED1 | LI-CF-2025-093 (10/02/2025) — Georgia Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-GA-2026-RU-002-C.pdf` | 2026 | 42 | CF-2025-RRU25 | LI-CF-2026-100 (03/04/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set**: 2/11/14/38/50/67/70/73/74/75/81/82/85 in 2020–2021, gaining 39/69/72/78 from
2024 onward + state rules A1–A12 (A11 joins in 2024). Three of Georgia's eight notices carry `CL-`
filing refs — the highest density of the pattern seen so far relative to document count.

---

## Iowa (`IA`) — 8 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-IA-2020-RU-001-C.pdf` | 2020 | 24 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-IA-2022-RU-001-C.pdf` | 2022 | 24 | CF-2021-RCCRU | LI-CF-2022-028 (03/30/2022) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-IA-2023-RU-001-C.pdf` | 2023 | 24 | CF-2022-REQRU | LI-CF-2022-159 (12/22/2022) — CP Multistate Earthquake Rules And Loss [Costs] | L2 |
| `CF-IA-2023-RU-002-C.pdf` | 2023 | 24 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-IA-2025-RU-001-C.pdf` | 2025 | 24 | CL-2024-OCAN2 | (not captured) | L2 — `CL-` filing prefix |
| `CF-IA-2025-RU-002-C.pdf` | 2025 | 26 | CF-2024-RDED1 | LI-CF-2025-010 (02/07/2025) — Iowa Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-IA-2026-RU-001-C.pdf` | 2026 | 26 | CF-2025-RRU25 | LI-CF-2026-100 (03/04/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |
| `CF-IA-2026-RU-002-C.pdf` | 2026 | 26 | CF-2026-ORU1 | LI-CF-2026-209 (05/22/2026) — Iowa Revised State Exception To Be Implemented | L2 |

**Exception rule set**: 2/14/17/50/72/73/75/81/82/85 + state rules A1–A11, entirely stable across all
eight editions — Iowa is the second Colorado-like flat/stable profile found so far, no drift at all.

---

## Illinois (`IL`) — 10 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-IL-2020-RU-001-C.pdf` | 2020 | 48 | (not captured) | (not captured) | L2 |
| `CF-IL-2020-RU-002-C.pdf` | 2020 | 48 | CF-2020-RCYRU | (not captured) | L2 — **two 2020 notices, same page count; supersession order not determined** |
| `CF-IL-2021-RU-001-C.pdf` | 2021 | 48 | (not captured) | (not captured) | L2 |
| `CF-IL-2022-RU-001-C.pdf` | 2022 | 48 | CF-2021-RCCRU | LI-CF-2021-073 (12/10/2021) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-IL-2023-RU-001-C.pdf` | 2023 | 48 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 |
| `CF-IL-2023-RU-002-C.pdf` | 2023 | 48 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-IL-2025-RU-001-C.pdf` | 2025 | 48 | CF-2024-RDED1 | LI-CF-2025-006 (02/03/2025) — Illinois Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-IL-2025-RU-002-C.pdf` | 2025 | 48 | (not captured) | LI-CF-2025-029 (03/03/2025) — CP Annual ZIP Code Territory Update | L2 |
| `CF-IL-2026-RU-001-C.pdf` | 2026 | 48 | CF-2025-RRU25 | LI-CF-2026-270 (06/29/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |
| `CF-IL-2027-RU-001-C.pdf` | 2027 | 48 | CF-2025-R25RU | LI-CF-2026-303 (07/22/2026) — CP Multistate Revision Of The Specific | L2 |

**Exception rule set**: 2/14/17/38/50/72/73/74/75/77/78/81/82/85 + state rules A1–A11, gaining A12/A13
by 2025 — **Illinois is the only jurisdiction ingested where every single notice has exactly the same
page count (48)**, an unusually flat profile for a state with this many editions.

---

## Indiana (`IN`) — 12 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-IN-2020-RU-001-C.pdf` | 2020 | 38 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-IN-2021-RU-001-C.pdf` | 2021 | 38 | (not captured) | (not captured) | L2 |
| `CF-IN-2022-RU-001-C.pdf` | 2022 | 38 | CF-2021-RCCRU | LI-CF-2021-073 (12/10/2021) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-IN-2023-RU-001-C.pdf` | 2023 | 38 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 |
| `CF-IN-2023-RU-002-C.pdf` | 2023 | 38 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-IN-2024-RU-001-C.pdf` | 2024 | 38 | CL-2024-ORU1 | (not captured) | L2 — `CL-` filing prefix; introduces rule 28 |
| `CF-IN-2025-RU-001-C.pdf` | 2025 | 38 | CL-2024-RACV1 | (not captured) | L2 — `CL-` filing prefix |
| `CF-IN-2025-RU-002-C.pdf` | 2025 | 40 | CF-2024-RDED1 | LI-CF-2025-025 (02/25/2025) — Indiana Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-IN-2025-RU-003-C.pdf` | 2025 | 40 | (not captured) | LI-CF-2025-029 (03/03/2025) — CP Annual ZIP Code Territory Update | L2 |
| `CF-IN-2025-RU-004-C.pdf` | 2025 | 40 | CL-2025-ORU1 | (not captured) | L2 — `CL-` filing prefix — **four notices in 2025 alone, the most of any jurisdiction/year combination seen; supersession order not determined** |
| `CF-IN-2026-RU-001-C.pdf` | 2026 | 40 | CF-2025-RRU25 | LI-CF-2026-002 (01/09/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |
| `CF-IN-2027-RU-001-C.pdf` | 2027 | 40 | CF-2025-R25RU | LI-CF-2026-303 (07/22/2026) — CP Multistate Revision Of The Specific | L2 |

**Exception rule set**: 2/14/50/72/73/75/81/82/85 + state rules A1–A13 (A11 joins 2025), gaining rule 28
starting 2024 (same rule Connecticut carries) — Indiana ties Kentucky/Massachusetts/Maine for the widest
state-rule range (A1–A13) among non-Florida states.

---

## Kansas (`KS`) — 4 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-KS-2020-RU-001-C.pdf` | 2020 | 26 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-KS-2024-RU-001-C.pdf` | 2024 | 34 | CF-2023-RDEQR | LI-CF-2023-131 (10/26/2023) — CP Earthquake Rules And Loss Cost Revisions | L2 — **a four-year gap between the 2020 and 2024 notices, the largest single-notice gap seen in this corpus so far** |
| `CF-KS-2025-RU-001-C.pdf` | 2025 | 36 | CF-2024-RDED1 | LI-CF-2024-168 (12/02/2024) — Kansas Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-KS-2026-RU-001-C.pdf` | 2026 | 36 | CF-2025-RRU25 | LI-CF-2026-002 (01/09/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set**: 2/10/14/30/50/69/72/73/74/75/81/82/85 in 2020, gaining 38/39/70/78 by 2024 +
state rules A1–A12. Kansas shares rule 30 with Arkansas — the only two jurisdictions ingested so far
that carry it.

---

## Kentucky (`KY`) — 10 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-KY-2020-RU-001-C.pdf` | 2020 | 41 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-KY-2021-RU-001-C.pdf` | 2021 | 40 | (not captured) | (not captured) | L2 |
| `CF-KY-2023-RU-001-C.pdf` | 2023 | 38 | CL-2023-OMJR1 | LI-CF-2023-052 (05/02/2023) — Kentucky Forms And Rules Revisions Addressing Cannabis | L2 — `CL-` filing prefix |
| `CF-KY-2024-RU-001-C.pdf` | 2024 | 38 | CF-2021-RCCRU | LI-CF-2023-130 (10/18/2023) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-KY-2025-RU-001-C.pdf` | 2025 | 40 | CF-2023-RDEQR | LI-CF-2024-020 (03/08/2024) — CP Earthquake Rules And Loss Cost Revisions | L2 |
| `CF-KY-2025-RU-002-C.pdf` | 2025 | 40 | CL-2024-ORU1 | (not captured) | L2 — `CL-` filing prefix |
| `CF-KY-2025-RU-003-C.pdf` | 2025 | 40 | CL-2024-ORU2 | (not captured) | L2 — `CL-` filing prefix, sequential to the one above |
| `CF-KY-2025-RU-004-C.pdf` | 2025 | 42 | CF-2024-RDED1 | LI-CF-2024-175 (12/17/2024) — Kentucky Revision And Expansion Of Deductible Insurance Plan | L2 — **four notices in 2025**, tied with Indiana for the most seen |
| `CF-KY-2026-RU-001-C.pdf` | 2026 | 42 | CL-2025-RWMC1 | (not captured) | L2 — `CL-` filing prefix |
| `CF-KY-2026-RU-002-C.pdf` | 2026 | 42 | CF-2025-RRU25 | LI-CF-2026-100 (03/04/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set**: 2/14/38/50/67/72/73/75/81/82/85 in 2020, gaining 39 by 2023 (the Cannabis
notice) and 70 by 2026 + state rules A1–A13. **Kentucky carries the `CL-` filing prefix more than any
other jurisdiction — four of its ten notices**, and is the only state seen where two `CL-` refs are
directly sequential (`ORU1`, `ORU2`).

---

## Massachusetts (`MA`) — 11 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-MA-2020-RU-001-C.pdf` | 2020 | 38 | **CL-2019-OMJRU** | (not captured) | L2 — `CL-` filing prefix; **the oldest filing-reference timestamp (2019) seen anywhere in this corpus** |
| `CF-MA-2021-RU-001-C.pdf` | 2021 | 38 | CL-2020-ORU1 | (not captured) | L2 — `CL-` filing prefix |
| `CF-MA-2021-RU-002-C.pdf` | 2021 | 42 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-MA-2021-RU-003-C.pdf` | 2021 | 42 | CF-2020-RDEQR | (not captured) | L2 |
| `CF-MA-2022-RU-001-C.pdf` | 2022 | 42 | (not captured) | LI-CF-2022-016 (03/04/2022) — CP Annual ZIP Code Territory Update | L2 |
| `CF-MA-2023-RU-001-C.pdf` | 2023 | 52 | CF-2021-RCCRU | LI-CF-2023-018 (02/09/2023) — 2021 CP Multistate Optional Endorsement | L2 — page count jumps from 42 to 52 here, largest single-edition jump seen; not investigated |
| `CF-MA-2024-RU-001-C.pdf` | 2024 | 52 | (not captured) | LI-CF-2024-015 (03/05/2024) — CP Annual ZIP Code Territory Update | L2 |
| `CF-MA-2025-RU-001-C.pdf` | 2025 | 38 | CF-2023-RDEQR | LI-CF-2024-150 (11/15/2024) — CP Earthquake Rules And Loss Cost Revisions | L2 — page count drops back from 52 to 38 |
| `CF-MA-2025-RU-002-C.pdf` | 2025 | 40 | CF-2024-RDED1 | LI-CF-2025-004 (02/03/2025) — Massachusetts Revision And Expansion Of Deductible Insurance | L2 |
| `CF-MA-2026-RU-001-C.pdf` | 2026 | 40 | (not captured) | LI-CF-2026-117 (03/23/2026) — CP Annual ZIP Code Territory Update | L2 |
| `CF-MA-2026-RU-002-C.pdf` | 2026 | 40 | CF-2025-RRU25 | LI-CF-2026-204 (05/15/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set**: 2/4/13/14/28/38/50/70/72/73/74/75/81/82/83/85 + state rules A1–A14 (full set
from the very first notice, unlike every other state where the A-set grows over time) — Massachusetts
and Florida are the only two jurisdictions with the complete A1–A14 range, and Massachusetts has it in
**every** edition, not just its latest. Rule 67 appears only in 2023.

---

## Maryland (`MD`) — 10 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-MD-2020-RU-001-C.pdf` | 2020 | 32 | CF-2020-RCYRU | (not captured) | L2 |
| `CF-MD-2022-RU-001-C.pdf` | 2022 | 32 | CF-2021-RCCRU | LI-CF-2021-073 (12/10/2021) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-MD-2023-RU-001-C.pdf` | 2023 | 32 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 |
| `CF-MD-2023-RU-002-C.pdf` | 2023 | 32 | (not captured) | LI-CF-2023-030 (03/06/2023) — CP Annual ZIP Code Territory Update | L2 |
| `CF-MD-2023-RU-003-C.pdf` | 2023 | 32 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-MD-2025-RU-001-C.pdf` | 2025 | 34 | CF-2024-RDED1 | LI-CF-2024-091 (08/14/2024) — Maryland Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-MD-2025-RU-002-C.pdf` | 2025 | 34 | (not captured) | LI-CF-2025-029 (03/03/2025) — CP Annual ZIP Code Territory Update | L2 |
| `CF-MD-2026-RU-001-C.pdf` | 2026 | 34 | CF-2025-RRU25 | LI-CF-2026-002 (01/09/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |
| `CF-MD-2026-RU-002-C.pdf` | 2026 | 34 | (not captured) | LI-CF-2026-117 (03/23/2026) — CP Annual ZIP Code Territory Update | L2 |
| `CF-MD-2027-RU-001-C.pdf` | 2027 | 34 | CF-2025-R25RU | LI-CF-2026-303 (07/22/2026) — CP Multistate Revision Of The Specific | L2 |

**Exception rule set**: 2/10/11/14/50/69/70/73/74/75/**8**/81/82/85 + state rules A1–A10, stable
throughout. **Rule 8 ("Policywriting Minimum Premium," per the CW TOC) appears here and nowhere else in
this corpus so far** — every other jurisdiction's exception set starts numerically at 2 or higher;
Maryland is the only one reaching down to rule 8. No `CL-`-prefixed filing refs in this state at all.

---

## Maine (`ME`) — 6 notices, all L2

| File | Edition | Pages | Filing ref | Circular ref (date) | Level |
|---|---|---|---|---|---|
| `CF-ME-2022-RU-001-C.pdf` | 2022 | 32 | CF-2021-RCCRU | LI-CF-2021-073 (12/10/2021) — 2021 CP Multistate Optional Endorsement | L2 |
| `CF-ME-2023-RU-001-C.pdf` | 2023 | 32 | CF-2022-REQRU | LI-CF-2022-143 (10/06/2022) — CP Multistate Rules And Loss Costs Revisions | L2 |
| `CF-ME-2023-RU-002-C.pdf` | 2023 | 32 | CF-2023-REQRU | LI-CF-2023-055 (05/16/2023) — CP Multistate Earthquake Rules Revisions | L2 |
| `CF-ME-2025-RU-001-C.pdf` | 2025 | 34 | CF-2024-RDED1 | LI-CF-2024-110 (08/28/2024) — Maine Revision And Expansion Of Deductible Insurance Plan | L2 |
| `CF-ME-2025-RU-002-C.pdf` | 2025 | 34 | CL-2025-OPC2 | (not captured) | L2 — `CL-` filing prefix; introduces rules 21 and 36 |
| `CF-ME-2026-RU-001-C.pdf` | 2026 | 34 | CF-2025-RRU25 | LI-CF-2026-143 (04/01/2026) — CP 2025 Multistate Forms And Rules Revisions | L2 |

**Exception rule set**: 2/11/13/14/25/38/50/69/70/73/74/75/81/82/83/85 + state rules A1–A11, gaining
21/36/72 in the 2025-002 notice — Maine's earliest notice on file is 2022, unlike most other states
which start at 2020; no earlier Maine edition has been collected.

---

## MI through WY — 27 states, one row per state (see format note above)

**Every jurisdiction below confirms the same exception-page pattern as the first 19** — thin
documents (24–78 pages), the same near-universal core (2, 14, 50, 72, 73, 75, 81, 82, 85 present in
almost all of them), and a growing state-rule set (`A1`–`A9` through `A14` depending on state). Not
re-derived per row below; only genuine departures from that baseline are called out.

| State | Notices | Years | Pages (min–max) | Exception rules (countrywide numbers touched) | State rules | Notable |
|---|---|---|---|---|---|---|
| MI | 8 | 2020–2026 | 24–26 | 2,4,11,14,41,50,72,73,75,81,82,85 | A1–A12 | Rule 41 ("Builders' Risk Coverage Options" per CW TOC) — first state seen carrying it as an exception |
| MN | 9 | 2020–2027 | 26–28 | 2,4,8,11,14,17,36,37,38,50,69,72,73,75,81,82,85 | A1–A12 | Second state (after Maryland) to carry rule 8 |
| MO | 8 | 2020–2027 | 40–42 | 2,14,25,28,50,69,72,73,75,81,82,85 | A1–A13 | — |
| MT | 11 | 2020–2027 | 36–60 | 2,11,14,15,21,33,38,50,67,70,72,73,74,75,76,78,81,82,85 | A1–A11 | Rule 15 — new number, not seen before this batch |
| NC | 8 | 2020–2026 | 48–48 | 2,4,14,18,23,30,31,38,50,69,70,72,73,74,75,81,82,84,85 | A1–A11 | Rules 23, 31, 84 all new; flat 48-page profile like Illinois |
| ND | 8 | 2020–2027 | 24–26 | 2,14,50,72,73,75,81,82,85 | A1–A11 | Flattest rule profile in this batch — matches Iowa/Colorado's stability pattern |
| NE | 8 | 2020–2027 | 24–26 | 2,14,25,50,72,73,74,75,81,82,85 | A1–A11 | — |
| NH | 7 | 2020–2027 | 30–32 | 2,4,10,14,19,28,36,38,50,70,72,73,74,75,81,82,85 | A1–A11 | — |
| NJ | 7 distinct (8 files — **1 duplicate PDF on disk**, `CF-NJ-2020-RU-001-C (1).pdf`) | 2020–2024 | 34–36 | 2,14,50,70,73,74,75,81,82,85 | A1–A11 | **Data-hygiene flag**: a byte-for-byte-named duplicate file exists in the source folder, likely a double-download; worth deleting the `(1)` copy once confirmed identical, not done in this pass |
| NM | 10 distinct (12 files — **2 duplicate PDFs on disk**, both copies of `CF-NM-2022-RU-002-C`) | 2020–2027 | 6–32 | 2,14,50,69,72,73,74,75,81,82,85 | A1–A12 | **Two data-hygiene flags**: the `(1)`/`(2)` duplicates above, plus `CF-NM-2027-RU-001-R.pdf` — the first document in this entire corpus with an **`-R` suffix instead of `-C`**, unexplained, not investigated. Also has the smallest page count in the whole corpus (6 pages) on one notice — worth a direct look before assuming it's a trivial one-line update |
| NV | 10 | 2020–2027 | 26–26 | 2,11,14,50,72,73,75,81,82,85 | A1–A11 | Only jurisdiction in this batch with an identical page count on every single notice |
| NY | 10 | 2020–2026 | 48–62 | 2,5,11,14,19,25,38,39,50,54,67,69,70,72,73,74,75,78,81,82,85 | A1–A11 | Second-broadest exception-rule set in the whole corpus after Florida/Texas/Virginia (see below); shares rule 5 with California only |
| OH | 7 | 2020–2026 | 24–42 | 2,14,50,72,73,75,81,82,85 | A1–A11 | — |
| OK | 6 | 2022–2026 | 26–38 | 2,4,14,50,70,72,73,75,81,82,85 | A1–A14 | Third state (after Florida, Massachusetts) with the full A1–A14 range |
| OR | 8 | 2022–2027 | 28–30 | 2,11,14,50,72,73,75,81,82,85 | A1–A12 | — |
| PA | 7 | 2020–2026 | 26–26 | 2,14,50,69,72,73,75,81,82,85 | A1–A12 | Flat page count like Nevada |
| RI | 6 | 2020–2025 | 32–33 | 2,11,14,33,38,50,54,69,70,72,73,74,75,81,82,85 | A1–A13 | Shares rule 33 with Florida only |
| SC | 8 | 2020–2026 | 42–60 | 2,11,14,21,36,38,50,67,70,72,73,74,75,78,81,82,85 | A1–A13 | — |
| SD | 7 | 2020–2027 | 26–26 | 2,11,12,14,17,21,36,50,72,73,75,81,82,85 | A1–A11 | Rule 12 ("Protective Devices And Services" per CW TOC) — first and only state seen carrying it as an exception |
| TN | 7 | 2020–2027 | 34–36 | 2,11,14,50,72,73,75,81,82,85 | A1–A12 | — |
| TX | 6 | 2020–2026 | 32–78 | 2,11,13,14,15,20,21,34,35,36,38,50,54,67,69,70,72,73,74,75,78,81,82,84,85 | A1–A14 (no A10 seen) | **Tied for the broadest exception-rule set in the whole corpus** — 25 countrywide rules, four new numbers (15, 20, 34, 35) not seen anywhere else. Fourth state with the full-ish A-range. Strong L3 candidate alongside Florida |
| UT | 8 | 2020–2026 | 30–32 | 2,14,38,50,69,72,73,75,81,82,85 | A1–A11 | — |
| VA | 7 | 2020–2026 | 46–46 | 1,2,9,10,13,14,17,19,25,30,31,32,34,35,36,38,50,70,72,73,74,75,80,81,82,84 | A1–A10 | **Rule 1** ("Application Of This Division") — the lowest rule number seen as a state exception anywhere in this corpus, unusual since Rule 1 is normally boilerplate scope language, not something a state would file an exception against. Second-broadest rule set in the corpus (26 numbers). Flat 46-page profile. Worth an L3 look specifically for what Virginia's Rule 1 exception says |
| VT | 6 | 2021–2025 | 26–28 | 2,14,38,39,50,67,69,72,73,74,75,81,82,85 | A1–A11 | Earliest notice is 2021, not 2020 |
| WI | 7 | 2020–2027 | 24–26 | 2,11,14,17,50,72,73,75,81,82,85 | A1–A11 | — |
| WV | 8 | 2020–2027 | 28–32 | 2,14,17,28,32,38,50,69,72,73,75,76,81,82,85 | A1–A12 | — |
| WY | 13 | 2020–2027 | 28–30 | 2,11,14,17,28,38,50,72,73,74,75,81,82,85 | A1–A12 | **Most notices of any jurisdiction in the corpus (13)** for one of the flattest rule profiles — high edition churn without much rule-set drift |

**Corpus-wide standings after this batch**: Texas and Virginia now rival Florida for broadest
exception-rule set (25–26 countrywide rules touched, vs. Florida's 23) — **the L3 priority list should
expand from "Florida then California" to "Florida, Texas, and Virginia," roughly tied**, with
Virginia's Rule 1 anomaly the single most curious individual finding of this whole batch. Wyoming has
the most notices of any state (13); New Mexico has the smallest single document (6 pages) and the only
non-`-C`-suffixed filename in the corpus. Rules 8 and 12 each have exactly one or two states carrying
them (Maryland+Minnesota for 8; South Dakota alone for 12) — worth remembering as rare, not core, the
next time someone builds a "which rules matter most" summary from this ledger.

---

## What this pass did NOT do (so it isn't mistaken for more than it is)

- **No rule *text* was read for any state notice** — only the exception-page heading list (which rule
  numbers appear) was scanned. A rule number appearing in two states' lists does not mean the exception
  text is the same; that comparison is L3 work, not done.
- **No cross-check against the ERC package.** None of these manual rule numbers (2, 14, 38, 50, 72, 73,
  75, 81, 82, 85, or any state's `A#` rules) were compared against the actual ERC rating logic already
  documented in `CauseOfLoss_*_RatingAlgorithms.md`. The one manual↔ERC agreement point this project has
  found (Rule 71 ↔ `BroadFormBaseRate`'s "bureau rule 71.E" citation, Entry 7) predates this state-notice
  batch and was not re-attempted here.
- **Blank filing-ref / circular-ref cells** mean the automated front-matter grep didn't find a match on
  that document, not that the document lacks one — a few likely have OCR/whitespace artifacts (`pypdf`'s
  known injected-space behavior, same caveat GL's extractor documented) that a manual open would resolve.
- **Supersession order within a jurisdiction-year** (e.g. Arkansas's two 2020 notices, two 2025 notices,
  two 2026 notices) was not determined. `notices.json`'s `date_confidence` field exists for exactly this
  and is not populated yet.
- **`knowledge/rule_index.json` was not updated with rules 81/82/83** discovered in this pass — flagged,
  not done, to keep this pass's scope to the ledger itself.

## Next state-notice pass, suggested order

1. Populate `rule_index.json` with rules 81 ("Revision And Expansion Of Deductible Insurance Plan"), 82
   ("Windstorm Or Hail Percentage Deductibles"), 83 (title still unconfirmed, now seen in AL, AR, CT,
   MA, ME), and **8** ("Policywriting Minimum Premium," per the CW TOC — Maryland only so far) — cheap,
   high-value, already fully derived at this point across three passes.
2. **Florida, Texas, and Virginia, text-level (L3) — now roughly tied for top priority**, updated after
   the MI–WY batch. Florida still has the broadest set from a single notice (23 rules); Texas and
   Virginia each touch 25–26 countrywide rules across their multi-edition history, with four Texas-only
   rule numbers (15, 20, 34, 35) and Virginia's genuinely strange **Rule 1** exception (the division's
   scope/application rule — not the kind of thing states normally file exceptions against). Read
   Virginia's Rule 1 text first; it's the single most curious individual finding in the whole ledger.
3. California, text-level (L3) — still a strong candidate: unique wildfire-mitigation content, three
   ZIP-territory notices, and the most likely state to intersect the already-documented ERC
   territory-factor logic (`BasicGroupIRatingTerrFactor`, `BasicGroupIIRatingTerr`).
4. **Work out what the `CL-` filing-reference family actually denotes.** No longer a handful of
   anomalies — it now appears in ten of nineteen jurisdictions (AR, CT, DC, DE, FL, GA×3, IN×3, KY×4,
   MA×2, ME), including the corpus's oldest filing timestamp (`CL-2019-OMJRU`, Massachusetts) and two
   directly-sequential refs (`CL-2024-ORU1`/`ORU2`, Kentucky). This is a real, systematic second filing
   family and this project should identify what distinguishes it from `CF-`-prefixed filings, not keep
   flagging individual occurrences. DC's one-off `CA-2023-REQRU` is the exception worth a separate,
   narrower look.
5. Resolve the multi-notice-per-year supersession-order question — now open in AR, CO, DE, IL (two 2020
   notices), and especially IN and KY (four notices each in a single year, 2025). `date_confidence`
   still isn't populated in `notices.json` for any of this.
6. Find a later Florida edition if one exists to collect — right now FL has exactly one notice on
   file (2022), so nothing about how it evolves over time can be assessed the way every other state's
   multi-edition drift has been.
7. A handful of page-count jumps were flagged but not investigated: Arizona 30→22 (Entry 11), Delaware's
   same-day dual circulars (Entry 11), and now Massachusetts's 42→52→38 swing across 2022–2025 — worth a
   combined look, since an unexplained page-count change is exactly the kind of thing that turns out to
   matter once someone reads the actual text.
8. **Data hygiene**: delete (after confirming byte-identical) the duplicate PDFs found in New Jersey
   (`CF-NJ-2020-RU-001-C (1).pdf`) and New Mexico (`CF-NM-2022-RU-002-C (1).pdf`, `(2).pdf`) — not done
   in this pass, since deleting source files wasn't requested. Also confirm what New Mexico's
   `CF-NM-2027-RU-001-R.pdf` (`-R` suffix, the only one in the corpus) actually denotes, and read its
   6-page notice directly — that's an unusually short document to characterize by rule-number-grep alone.
