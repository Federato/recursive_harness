# Carrier filings log

Every carrier filing we have worked on: where it came from, what we built from it, what was decided and how it
was proved. One entry per filing, newest first. Until filing intake exists in the console, filings are passed in
the Claude Code session and logged here by hand.

**Source documents** are archived as received in the carrier store, never edited:
`C:\FederatoProjects\Carriers\<carrier>\sources\<SERFF tracking number>\`, with a `source.json` giving each file's
SHA-256. Check a copy with `sha256sum` against the hash below.

## Index

| # | Carrier | Companies | Line | State | SERFF | Effective | Status |
|---|---|---|---|---|---|---|---|
| [DEV-003](#dev-003) | UFG | UFC, ADD | GL | IA | UNFG-134374972 | 2025-07-15 new · 2025-11-01 renewal | Live, proved (v2, 38 offline + 3 live) |
| [DEV-002](#dev-002) | UFG | UFC, LAF | CF | AL | UNFG-134461534 | 2025-07-15 new · 2025-11-01 renewal | Live, proved (LCMs; v2 minimum and terrorism) |
| [DEV-001](#dev-001) | UFG | UFC, ADD | CF | IA | UNFG-134289779 | 2025-06-01 new · 2025-10-01 renewal | Live, proved (T1–T10) |

## How a filing is logged

1. **Received.** You pass the documents in the session. They're copied to `Carriers\<carrier>\sources\<SERFF>\`
   with a `source.json` (hashes, what each file is), and an entry is opened here as *Received*.
2. **Mapped (P0).** Every item in the filing is mapped to targets the engine knows, or listed as a gap. Gaps go to
   you; your decisions are written in the entry.
3. **Authored.** One authored file per writing company (`<juris>-<line>-<SERFF>.v<n>.json`), each row citing the
   page it came from; `python -m deviations validate`, then compile.
4. **Approved.** Proposed and signed off in the company's `workflow.jsonl`.
5. **Proved.** The rating checks that apply (technical vs ISO, carrier vs technical, LCMs applied where filed), with
   results recorded here.

A new version of a filing (a correction, or a later filing that replaces it) is a new entry that names the one it
supersedes.

---

## DEV-003

**UFG Iowa Commercial General Liability loss cost multipliers**: *Live, proved (v2, 38 offline checks, 3 live on ISO's edition in force)*

**In short:** UFG filed loss cost multipliers (LCMs) for general liability in Iowa: factors applied to ISO's loss costs, one per company and coverage. United Fire filed 0.942 for premises and operations (6% below ISO) and 1.789 for products and completed work (79% above); Addison filed 1.272 and 2.415 (27% and 142% above). They apply from July 15, 2025 for new policies and November 1, 2025 for renewals, on ISO's Iowa rates in force on the policy date; specialty ("a"-rated) classes are left out. Since October 16, 2026 the filing's minimum premium (United Fire $500, Addison $625 a policy) and its experience rating expected loss ratio (68.6%) are built too. On a set of typical businesses United Fire comes out about 26% above ISO and Addison about 70%, mostly through products coverage.

The first real GL filing (B-19).

| | |
|---|---|
| Carrier | UFG Insurance (`UFG`) |
| Writing companies | United Fire & Casualty Company (`UFC`, NAIC 13021) · Addison Insurance Company (`ADD`, NAIC 10324) |
| Line / state | General Liability (GL) · Iowa |
| SERFF | UNFG-134374972 (Rate/Rule, TOI 17.0 / 17.0001; companions not received: UNFG-134204780 package plan, UNFG-134564539 multistate note; replaces the three-tier LCMs of UNFG-133187379, 7/1/2022) |
| Approved | 2025-05-13 (submitted 2025-01-17) |
| Effective | **2025-07-15 new business, 2025-11-01 renewal** (the revised exception manual dated 4/2/25; the memo and ELP pages say 6/1 and 10/1) |
| ISO loss costs | The filing names **GL-2023-BGL1** (`GL_IA_20240401_V01`). **Rated on ISO's edition in force on the policy date** (`GL_IA_20250401_V01`, GL-2024-BGL1, on the effective dates): edition pins retired 2026-10-16, your decision |
| Received | 2026-10-15, three files in `Downloads` |
| Worked | 2026-10-15 |

**Source documents** (`C:\FederatoProjects\Carriers\UFG\sources\UNFG-134374972\`). **A typed extraction, not the filed PDF**: the
exception page manual (`CG-IA-UFC-ADD-071525 - PC Only - Checked Out LAK v2.pdf`, pp. 1-2, Rule 1.D.2) wasn't received. The
workbook's cell comments quote its text ("Premise/Ops: 0.942" ...). Per D18 the PDF would win if it ever disagrees.

| File | What it is | SHA-256 |
|---|---|---|
| `UFG_IA_GL_LCM_2025.xlsx` (13,018 bytes) | LCM_2025 (four LCMs, quoted sources), Apply_LCM (calculator, placeholder ISO inputs), Filing_Info | `2231e98a1a812d90fea60a02ee27f93c10136d0ce3b2030dd550ad420db1524f` |
| `UFG_IA_GL_LCM_2025_Explainer.md` (4,584 bytes) | Explainer: LCMs, exclusions, OCP, indication, date discrepancy | `0eb460a6712d6a533ec702f22cd1d0c33fafd804fd28f388bda23bb7d06a5353` |
| `UFG_IA_GL_LCM_2025.zip` (14,251 bytes) | The two files above, byte-identical | `10e69a3e2aa6cebbb658490626d50396467eb0c3448883d39ea306d3b6fec3da` |

**What was filed** (Rule 1.D.2): one multiplier per company per subline, every class

| Company | Premises/Operations (334) | Products/Completed Operations (336) |
|---|---|---|
| UFC | 0.942 | 1.789 |
| ADD | 1.272 | 2.415 |

Not on loss cost × LCM: **"a"-rated classes** (UFG's ELP ranges, separate manual), **policy writing minimums** (UFC $500,
ADD $625), **OCP** (Rule 46: Prem/Ops LCM on UFG's *own* base loss costs). Also filed, ISO's: ILFs (GL-2021-IALL1),
deductibles (GL-2014-RDD14); UFG's: schedule rating ±25%, experience rating ELR 68.6%.

**What we built**

| | |
|---|---|
| Authored | `Carriers\UFG\{UFC,ADD}\authored\IA-GL-UNFG-134374972.v1.json`: 4 rows each. `LCM:PremOps` and `LCM:ProdsCompldOps` unscoped at the filed value; the same two at **1.0 on the "a"-rated classes** (class groups `UFG-IA-GL-aRated-PremOps@v1`, 68 classes, and `…-Prods@v1`, 98: the classes ISO publishes no loss cost for, whose schema takes a company ELP). Minimums, schedule and experience bounds in `meta` (v1) |
| v2 (B-21) | `…v2.json`: v1's 4 rows plus `TABLE:ExpectedLossRatio.Factor` 0.686 (ISO's ELR table, 1) and `MIN:Policy` 500 (UFC) / 625 (ADD), a policy item applied after ISO's rules and written on ISO's own declared field `GeneralLiability.PolicyWritingMinimum`; 6 rows, 2,378 compiled keys. Proposed, signed off (Dan Roman) and compiled 2026-10-16 |
| Pin | ~~`edition_pins.GL.IA = GL_IA_20240401_V01`~~ **removed 2026-10-16**: pins retired, the filing rides ISO's edition in force |
| Validated / compiled | Clean, 2,376 keys each (2 sublines × 1,188 classes); `compiled\GL\IA\` |
| Approval | v1 proposed and signed off as Dan Roman, 2026-10-15 (as DEV-001/002) |
| Engine | v1: no change. v2: B-21's policy-level items; pins removed from the engine |
| Fixture | Both filings (v1, v2) and the class groups in `tests/fixtures/deviations/UFG/` |

**Decisions made on this filing**

| | Decision |
|---|---|
| Loss costs | ~~Pin to GL-2023-BGL1 (you, 2026-10-15)~~ **Superseded 2026-10-16 (you): no pins; a filing has its own dates and rides ISO's edition in force.** Class 18501 technical is now 2,987 (was 2,734 pinned) |
| Dates | The exception manual's 7/15/2025 and 11/1/2025 (the explainer's item 1; D18 spirit: the document carrying the LCMs) |
| "a"-rated | LCM held at 1.0 on ISO's "a"-rated classes per subline. Without it the engine multiplied the company-entered rate (a $830 test rate became $1,660 under LCM 2) |
| OCP | Not built: UFG's own OCP base loss costs aren't in what we received. OCP keeps ISO's LCM |
| Minimums, schedule ±25%, ELR | **v2 (B-21, 2026-10-16):** the minimum raises the whole GL total to $500 / $625, per annual period, GL only (your defaults, the exception page not received); one ELR 68.6% for both sublines and every class, accepting that a lower ELR lowers credibility and can switch experience (0.07) or schedule (0.03) rating off, as ISO's plan does (you). Schedule ±25% is ISO's own bound: no row |

**How it was proved** (`python tests/verify_deviations_ufg_ia_gl.py`: **38 of 38 pass offline**, 2026-10-16, on ISO's
edition in force)

- T10: v1 and v2 validate, compile and read back as the rows written (v2: the ELR a table row, the minimum a policy item).
- T5: Prem/Ops and Products records carry exactly 0.942 / 1.789 (UFC) and 1.272 / 2.415 (ADD), and each base rate is
  technical's × its LCM to ISO's three places (class 18501 Prem/Ops 1.88 → 1.771 / 2.391; premium 2,971 → 2,798 / 3,778).
- "a"-rated class 10119 (company ELP 0.5) keeps LCM 1.0 and its premium (830).
- T7: in force for new business from 7/15/2025 (not 7/14), renewals from 11/1/2025 (not 10/31).
- Technical rates on `GL_IA_20250401_V01`, ISO's edition in force on 7/15/2025, and equals an ISO-only rating that day
  (2,987); the waterfall is LCM −159 (UFC) / +831 (ADD), from 2,987 to 2,828 / 3,818, no edition step.
- T4: only the Prem/Ops and Products records and the premiums they roll into change (v2 adds `PolicyWritingMinimum` and
  `ERPExpectedLossRatio`).
- Carrier on 7/15/2025 equals ISO's own rules run that day with UFG's LCMs written into the request.
- v2 ELR: an experience-rated 18501 (exposure 50,000,000) reads `ERPExpectedLossRatio` 0.686 (technical 1); carrier
  110,687 → 117,775 (UFC) and 140,105 → 150,637 (ADD), the ELR step the whole difference.
- v2 minimum: a small risk (technical 60) is raised from 57 to $500 (UFC) and from 77 to $625 (ADD), the top-up its own
  line and waterfall step; a risk above the minimum is unchanged.
- **Live (U8, 2026-10-16, 3 ISO calls, adhoc lane, your go):** ISO's service, asked the request dated 7/15/2025 with
  UFG's LCMs written in, priced it exactly as we do on its edition in force: UFC 18501 **2,828**, Addison 18501
  **3,818**, UFC "a"-rated 10119 **830**. (On 2026-10-15 the same check on the then-pinned edition gave 2,592 / 3,500 /
  785, also exact.) The carrier's v2 items are ours only (D21) and never go to ISO.

**Open on this filing**

- The filed PDF (exception page manual), to confirm the typed values.
- OCP on UFG's own base loss costs.
- Multistate accounts stay on legacy rates until every state approves (UNFG-134564539): not modelled.

---

## DEV-002

**UFG Alabama Commercial Property loss cost multipliers, minimum premium and terrorism**: *Live, proved (v2, 2026-10-16)*

**In short:** UFG filed loss cost multipliers (LCMs) for commercial property in Alabama: factors applied to ISO's loss costs, by kind of business (three class groups) and type of loss. For most classes United Fire filed 2.185 for fire and lightning and 2.192 for other perils (about 119% above ISO), and Lafayette 2.731 and 2.740 (about 174% above); two groups of classes have lower multipliers. They apply from July 15, 2025 for new policies and November 1, 2025 for renewals. Since October 16, 2026 two more of its pages are built: every policy pays at least $300, and when terrorism coverage is taken it costs 2% of the property premium instead of ISO's charge (ISO's $7 becomes $350 for United Fire on the sample building). On a set of typical businesses United Fire comes out about 109% above ISO and Lafayette about 161%. The filing's other pages (deductibles, building age and others) are not built.

| | |
|---|---|
| Carrier | UFG Insurance (`UFG`) |
| Writing companies | United Fire & Casualty Company (`UFC`, NAIC 13021) · Lafayette Insurance Company (`LAF`, NAIC 18295), **new to us** |
| Line / state | Commercial Property (CF) · Alabama |
| SERFF | UNFG-134461534 (Rate/Rule; replaces UNFG-133706267; associated UNFG-134461533, CPP plan UNFG-134205156) |
| Filed | 2025-04-14 (submitted 2025-04-09; SERFF status Closed-Filed) |
| Effective | **2025-07-15 new business, 2025-11-01 renewal** (the exception page; the SERFF summary's *requested* renewal date is 12/01/2025) |
| Scope | LCMs (v1, 2026-10-09, your instruction), plus the policy minimum (Rule 8) and terrorism pricing (Rule A11.C) in v2 (B-21, 2026-10-16). The other exception pages are archived, not authored. |
| Received | 2026-10-09, in `DeviationDocs\UFGAL` |
| Worked | 2026-10-09 (received → proved the same day) |

**Source documents** (`C:\FederatoProjects\Carriers\UFG\sources\UNFG-134461534\`)

| File | What it is | SHA-256 |
|---|---|---|
| `AL CP UFC LAF 0725-PC Only-Final.pdf` (396,068 bytes) | The filed exception page manual, 43 pages. **LCM table on p1**, the only page used | `39b39243658eb5bd1abe79a1d6c14e7dd49a5978eff43c79dc22c0b755527f22` |
| `UFG_AL_CP_LCMs.csv` (1,204 bytes) | The LCM table typed out, with class groups and dates. Agrees with p1 on every value and class range | `c550956d165cdf6681dccd2c5108aef0b5c6baeafc9a9ab36920d20ce7c7c49b` |
| `UNFG-134461534.zip` (11,287 bytes) | SERFF's filing summary (companies, dates, rate/rule schedule) and usage agreement | `e32a65c09485b2c231cd70417d7918b9b3ab296612f9025b91cf1263b9df4973` |
| `ufg-al-cp-rating-factors.html` (33,097 bytes) | The filing's other rating factors. Not used (LCMs only) | `2bd3699074742ff5e29715e0f8eb9b4b52c831205b1b800cce078688d97c7b98` |

**What was filed** (exception page p1)

| Company | Class group | Grp I specific* | Grp I class | Group II | Broad | Special | Earthquake |
|---|---|---|---|---|---|---|---|
| UFC | A | 2.047 | 2.047 | 2.112 | 2.112 | 2.112 | 1.529 |
| UFC | B | 1.898 | 1.898 | 1.965 | 1.965 | 1.965 | 1.529 |
| UFC | All other | 2.185 | 2.185 | 2.192 | 2.192 | 2.192 | 1.529 |
| LAF | A | 2.559 | 2.559 | 2.640 | 2.640 | 2.640 | 1.910 |
| LAF | B | 2.373 | 2.373 | 2.456 | 2.456 | 2.456 | 1.910 |
| LAF | All other | 2.731 | 2.731 | 2.740 | 2.740 | 2.740 | 1.910 |

\* "including special class rates"

**Class group A** (`UFG-AL-A@v1`): 0431, 0433-0434, 0532, 0541-0542, 0550, 0561, 0565-0566, 0570, 0581-0582,
0745-0747, 0755-0757, 0931, 0933, 1052, 1150, 2000, 2059, 2200, 2250, 3409, 6009.
**Class group B** (`UFG-AL-B@v1`): 0511, 0512, 0520, 0563, 0567, 0701-0702, 0851-0852, 0900, 0921, 0922, 0923,
0932, 1051, 1070, 4809, 6850, 6900. **All other**: every other class.
These are not Iowa's groups (different ranges), so Alabama has its own, at carrier level in `carrier.json`.

**What we built**

| | |
|---|---|
| Authored | `Carriers\UFG\UFC\authored\AL-CF-UNFG-134461534.v1.json` and `…\LAF\…v1.json`: 13 rows each (Group I, Group II, Broad, Special × 3 class groups, plus Earthquake), each citing `Exc p1` |
| New company | `Carriers\UFG\LAF\company.json` (Lafayette Insurance Company, NAIC 18295) |
| Validated | Both files clean, no warnings: every class range exists in ISO's Alabama class list on 2025-07-15; 1,540 compiled keys each |
| Compiled | `Carriers\UFG\<company>\compiled\CF\AL\` |
| Approval | v1 proposed and signed off by Dan Roman, 2026-10-09; v2 the same, 2026-10-16 (`workflow.jsonl` in each company) |
| v2 (B-21) | `…v2.json`: v1's 13 rows plus `PCT:Terrorism` 0.02 (`Exc p27 Rule A11.C`) and `MIN:Policy` 300 (`Exc p3 Rule 8`); 15 rows, 1,612 compiled keys; the two policy items live in the manifest's `policy`, applied by our engine after ISO's rules |
| Engine | v1: no change (the group-LCM path, D17). v2: the policy-level items of B-21 (`deviations.engine.apply_policy`) |

**Decisions made on this filing**

| | Decision |
|---|---|
| Scope | LCMs only (you, 2026-10-09). **v2 adds the minimum premium $300 (Rule 8) and terrorism at 2% (A11), B-21 (2026-10-16).** Still not authored: Rule A4's public and institutional plan minimum (ISO has no machine content for the plan), deductible and windstorm tables (33, 81, 82), Group I class protection factors (85), age-of-building factors, Ultra Property Plus and Equipment Breakdown percentages. IRPM ±25% is ISO's own bound: no row. |
| Terrorism (v2) | 2% of the property premium after IRPM, before the minimum; the minimum floors the total with terrorism in it (you, 2026-10-16). Charged only when ISO's rules charge terrorism (coverage for certified acts taken: `CoverageForCertifiedActs` Yes, which attaches IL 09 52); it replaces ISO's per-coverage charge, which stays visible in the coverage records, and is written as `CompanyTerrorismPremium` and on the TRIA disclosure record. |
| Minimum (v2) | Raise to $300 (you, 2026-10-16), written as `MinimumPremium` (the input ISO's 2027 minimum rule reads); ISO's Alabama editions in force have no working minimum. |
| Renewal date | The filed exception page and the CSV say **11-01-2025**; the SERFF summary's *requested* renewal date is 12/01/2025. **Decided (you, 2026-10-09): the filed document wins, 11-01-2025.** |
| Status | Alabama shows the filing as *Filed* (file-and-use), not approved; authored as in force from its effective dates. |

**How it was proved** (`python scripts/filings/DEV-002_prove.py`, on the live carrier store, 2026-10-09: **22 of 22 pass**)

- **LCMs applied where filed**, both companies, one risk per class group (A: 1150, B: 0511, all other: 0951):
  every group-rate product reads exactly the filed LCM (11 per rating; Group I, Group II, Special, Earthquake), and
  the Group I and II rates equal technical × their own LCM within ISO's rounding. The sample uses the Special form,
  so Broad isn't exercised; it's authored and compiled like the others.
- **Dates:** in force for new business from 2025-07-15 (not 07-14) and for renewals from 2025-11-01 (not 10-31),
  for both companies.
- **Technical = ISO in Alabama** was already proved in T3 (96 of 96 states). No ISO calls spent: ISO only ever
  rates technical (D21).
- Sample premiums (technical → carrier): class 0951 8,006 → UFC 17,503 / LAF 21,883; class 1150 2,190 → 4,588 /
  5,744; class 0511 3,149 → 6,036 / 7,546.
- Iowa (DEV-001) unchanged: UFC 9,026, ADD 10,822 on the Iowa sample, as before.
- **v2 (2026-10-16, same script, 10 more checks, all pass):** v2 in force with both items; with no terrorism taken
  neither ISO nor the carrier charges it; with terrorism taken technical carries ISO's $7 and the carrier 2% of the rest
  of its premium (UFC $350 on 17,503; LAF $438 on 21,883), the waterfall adding up (UFC: LCM +9,497, terrorism +343,
  minimum 0); a small risk (limits a hundredth of the sample's) is raised from 229 (UFC) / 286 (LAF) to $300. Our
  engine only (D21): ISO's service never sees a carrier's items.

**Open on this filing**

- The remaining exception pages (deductibles, building age, Equipment Breakdown, Ultra Property Plus), if you want them.

---

## DEV-001

**UFG Iowa Commercial Property loss cost multipliers**: *Live, proved*

**In short:** UFG filed loss cost multipliers (LCMs) for commercial property in Iowa: factors applied to ISO's loss costs, by kind of business (three class groups) and type of loss. For most classes United Fire filed 1.511 for fire and lightning (51% above ISO) and 3.280 for wind, hail and other perils (228% above), with lower multipliers for two groups of classes; Addison's multipliers are about 20% higher than United Fire's. They apply from June 1, 2025 for new policies and October 1, 2025 for renewals. On a set of typical businesses United Fire's Iowa property comes out about 68% above ISO and Addison's about 102%. Proven in full against ISO's own system.

| | |
|---|---|
| Carrier | UFG Insurance (`UFG`) |
| Writing companies | United Fire & Casualty Company (`UFC`, NAIC 13021) · Addison Insurance Company (`ADD`, NAIC 10324) |
| Line / state | Commercial Property (CF) · Iowa |
| SERFF | UNFG-134289779 (companions, not received: UNFG-134204780 CPP plan, UNFG-134266109 forms) |
| Approved | 2025-05-06 |
| Effective | **2025-06-01 new business, 2025-10-01 renewal** (the PDF; the sheet disagreed, the PDF wins) |
| What it does | Adopts ISO's current loss costs with company LCMs by coverage group × class group. No factor overrides, no minimum premium, no terrorism item. |
| Received | 2026-10-08 |
| Worked | 2026-10-09 (P0 → P4) |

**Source documents** (`C:\FederatoProjects\Carriers\UFG\sources\UNFG-134289779\`)

| File | What it is | SHA-256 |
|---|---|---|
| `UFG_IA_CP_LCM_Filing_UNFG-134289779.pdf` (927,459 bytes) | The filing, 16 pages: memo p1; **exception page (LCM table) pp2–3**; supporting LCM forms pp4–15; permissible loss ratio p16 | `c3fd5ef14ab5a1a57f5daf061e297132902c8824356cc10c3abe0ed41fb94a71` |
| `UFG_IA_CP_LCMs.csv` (1,213 bytes) | The same LCM table typed out, with approval and effective dates. Also at `tests/fixtures/deviations/UFG_IA_CP_LCMs.csv` | `f48c5b3800bd0829e623f70f40e81b59546ade48389ba3649e37417df434f20e` |

**What was filed** (exception page pp2–3; the supporting forms agree with every value)

| Company | Class group | Grp I specific | Grp I class | Group II | Broad | Special | Earthquake |
|---|---|---|---|---|---|---|---|
| UFC | A | 1.067 | 1.067 | 2.448 | 2.448 | 2.448 | 2.11 |
| UFC | B | 0.875 | 0.875 | 2.062 | 2.062 | 2.062 | 2.11 |
| UFC | All other | 1.511 | 1.511 | 3.280 | 3.280 | 3.280 | 2.11 |
| ADD | A | 1.279 | 1.279 | 2.938 | 2.938 | 2.938 | 2.64 |
| ADD | B | 1.051 | 1.051 | 2.474 | 2.474 | 2.474 | 2.64 |
| ADD | All other | 1.813 | 1.813 | 3.934 | 3.934 | 3.934 | 2.64 |

Class groups (carrier level, `UFG-A@v1` / `UFG-B@v1` in `carrier.json`): A is 46 class ranges, B is 12, and
"all other" is everything else. The full lists are in `P0-UFG-IA-CF.md` §1. Kept as metadata, not rated: expected
loss ratios 0.543 (Group I) and 0.477 (Group II); rate level change +20.9% UFC, +1.0% ADD; expense provisions (p16).

**What we built**

| | |
|---|---|
| Mapping | [`P0-UFG-IA-CF.md`](P0-UFG-IA-CF.md): every item mapped, gaps G1–G7 |
| Authored | `Carriers\UFG\UFC\authored\IA-CF-UNFG-134289779.v1.json` and `…\ADD\…v1.json`: 13 rows each (Group I, Group II, Broad, Special × 3 class groups, plus Earthquake), each citing its page (e.g. `Exc p3; OKLCF p9`) |
| Compiled | `Carriers\UFG\<company>\compiled\CF\` (GroupLCM.Company tables with an Explain column, manifest) |
| Approval | v1 proposed and signed off by Dan Roman, 2026-10-09 (`workflow.jsonl` in each company) |
| Engine | Group LCMs substituted in each coverage group's base-rate product (D17); company ratings return a non-deviated and a deviated payload |

**Decisions made on this filing**

| | Decision |
|---|---|
| G1 → D17 | ISO's CF rules carry one LCM; UFG files one per coverage group. **Option A**: each group's LCM is substituted in that group's base-rate product. |
| G4 | The documents disagree on dates. **The PDF wins**: 6/1/2025 new, 10/1/2025 renewal. |
| G6 | **CF first**, then GL. |
| G2, G3, G5, G7 | As proposed in P0: one filing covering two companies is authored once per company; Group I specific and class rates share the Group I LCM; class groups live at carrier level and are versioned. |
| O3 | Minimum premium and terrorism follow the **deviated** premium. |
| O6 → D21 | ISO refuses CF LCMs below 1.00 (UFC's group B 0.875). **ISO only ever rates technical; LCMs are never sent.** Our engine rates below 1.00. Pattern: Technical / ISO / Carrier. |

**How it was proved** (`docs/gates/GATE-DEVIATIONS.md`, 2026-10-09)

- T1–T10 all pass. Technical matches ISO in **96 of 96** states (40,413 numbers, 0 disagreements).
- **T5:** every group-rate product reads exactly the filed LCM (UFG Iowa, both companies × 3 risks).
- **T4:** only what was deviated changes; checked exactly through the rating graph (67 changed fields, all within
  the 101 the filing reaches).
- The full snapshot regression (2,082 requests) is unchanged.
- ISO calls: 71 on 2026-10-09.
- Checked live in the console: the BGII "all other" LCM 3.28 shows as *LCM applied* on the worksheet, and the
  drill-down traces the final Group II rate back to the filing row.

**Open on this filing**

- ~~Whether the "all other" row should apply automatically to classes ISO adds after v1~~ **Decided 2026-10-15 (D22): yes, until a filing says otherwise.** Recompiled: the 7 Property special classes 1160-1200, missing from the compiled class list until now, take "all other" (UFC 1.511 / 3.280 / 2.11, ADD 1.813 / 3.934 / 2.64); before, ISO's LCM applied to them. Same for UFG Alabama (DEV-002).
- Companion filings UNFG-134204780 (CPP plan) and UNFG-134266109 (forms) haven't been received.
