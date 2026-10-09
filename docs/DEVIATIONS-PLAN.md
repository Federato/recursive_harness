# Carrier Deviations — Plan for sign-off

**Status: v2 SIGNED OFF 2026-10-09. Nothing built. Waiting on a real filing for P0.** This is Phase 4 of the original programme
(`EXECUTIVE-SUMMARY.md` §6, `BACKLOG-2026-08-14.md` items 7 and 8).

**v2 refocus (same day):** the goal is to **prove that deviations can be layered on without
breaking ISO**. The plan centres on three things:

- how the files and payloads behave
- the response contract
- a proof suite

UI is kept to the minimum needed to see the proof. The full Deviations tab in
`deviations-wireframes_20261008.html` is a later reference, not part of this plan.

---

## 1. The claim we are proving

> For any request, adding a writing company's deviations **changes only what those deviations say
> to change**, **by exactly the amount they say**. Everything else — and the whole result when no
> company is named — is **identical to ISO**, field for field.

Every phase below exists to make that claim testable, and then to test it at scale. The engine
produces two results from the same request:

| | Meaning |
|---|---|
| **Technical** | Pure ISO content, no deviations. What the engine does today (`strict-erc`, ISO-only, C3). Checked against ISO's service, as today. |
| **Carrier** | Technical plus the writing company's approved, in-force deviations. |

## 2. Decisions

### Inherited (Aug 2026, not reopened)

| # | Decision |
|---|---|
| I1 | Deviations are **content, not code**. They're authored in a friendlier format that compiles to ISO's shape, and the compiled form can be read back. |
| I2 | Stored **per jurisdiction, always**. "All states" is an authoring shortcut that creates one copy per state, as of the day it's authored. A state can opt out later. |
| I3 | ISO's `@parent` keeps ISO's meaning. A company layer never sits between an ISO state rule and its countrywide parent (C2). |
| I4 | `strict-erc` over ISO-only content stays runnable forever (C3). |
| I5 | LCM is a named parameter and is never defaulted silently. |

### Taken 2026-10-08

| # | Question | Answer |
|---|---|---|
| D1 | Deviation types in v1 | **LCM + factor overrides** (whole-table replacement and new rules: designed for, not built) |
| D2 | Who owns deviations | **Carrier, then writing company** |
| D3 | How finely deviations are keyed | **State × effective date × coverage/subline**, optionally narrowed by **class or class group, territory, limit or deductible** |
| D4 | Effective dates | **Separate new and renewal dates** |
| D5 | Where proposals come from | Manual, spreadsheet, SERFF. **In this plan: authored files plus spreadsheet import.** UI and SERFF intake come later. |
| D6 | Approval | Configurable per carrier. **In this plan: a status in the file plus a named sign-off in the workflow log.** The UI comes later. |
| D7 | Combining deviations | **Each row is `replace` or `multiply`** |
| D8 | Comparison | **ISO service, our technical, our carrier, plus the breakdown by deviation** |
| D9 | When ISO revises an edition | **Carry forward and flag** |
| D10 | Edition pinning | **In scope** |
| D11 | Checking against ISO's service | **Yes for LCM**, including class, territory and limit keyed LCMs (§4b makes them all checkable) |
| D12 | Storage | **Per-company content in ERC shape** (RateTable CSV + Def XML), plus workflow metadata |
| D13 | LCM already in the request | **Carrier deviation wins**, with a warning if the request's value isn't 1. Technical ignores any value in the request. |
| D14 | Class groups | **ISO groupings plus company lists** |
| D15 | How a request names its company | **`header.WritingCompany`**. If it's absent, the request rates technical only. |
| D16 | First real case | **You provide a filing** (Phase 0) |

### My calls (push back if wrong)

| # | Call |
|---|---|
| M1 | Layer chain: **company-state > ISO-state > ISO-countrywide** (follows from I2). |
| M2 | **LCM is written onto the request; factor overrides are a table layer.** See §4. |
| M3 | Technical is rated on the **same edition** as carrier (the pinned one if there is a pin), so a carrier-vs-technical difference is only ever deviations. |
| M4 | Workflow metadata is append-only JSONL, latest line wins (the console's convention). Only approved versions compile. |
| M5 | Class groups, territory lists and the all-states shortcut are **expanded to explicit keys at compile time**. Each compiled row remembers the authored row it came from. |
| M6 | **Our own fields never go into the ISO tree.** The request's company and new/renewal fields are removed before ISO's rules run and before any call to ISO's service. Our results go in a separate `Deviation` block beside the ISO tree (§3c). |

---

## 3. Files and payloads — how each behaves

### 3a. Deviation files

```
<CARRIERS_ROOT>/                                   outside the repo and the ZIPs; configured like GL_ERC_ROOT
  <carrier>/carrier.json                           approval policy
  <carrier>/<company>/company.json                 code (e.g. HP-CAS), edition pins, class groups (versioned)
  <carrier>/<company>/workflow.jsonl               proposals, sign-offs, rejections (append-only)
  <carrier>/<company>/authored/<filing>.v<n>.json  the friendly form — what people edit
  <carrier>/<company>/compiled/<line>/<juris>/<filing>.v<n>/
        manifest.json                               effective dates, mode per table, ISO edition at approval,
                                                    authored-row ↔ compiled-row map
        LCM.Company.RateTable.csv                   explicit keys: subline, class, territory, limit → LCM
        Rate Tables/<ISO table>.Company.RateTable.csv + <ISO table>.CompanyDef.RateTableDef.xml
```

An authored filing (example values):

```json
{ "company": "HP-CAS", "line": "GL", "juris": ["TX"], "version": 3, "status": "approved",
  "new_eff": "2026-07-01", "renewal_eff": "2026-08-01",
  "rows": [
    {"target": "LCM:PremOps",  "scope": {}, "value": 1.12, "mode": "replace", "cite": "Exh 1 p3 ln4"},
    {"target": "LCM:PremOps",  "scope": {"class_group": "Contractors@v2"}, "value": 1.08, "mode": "multiply"},
    {"target": "LCM:ProdsCompldOps", "scope": {}, "value": 1.25, "mode": "replace"},
    {"target": "TABLE:ILFPremOps.Factor",
     "scope": {"EachOccurrenceLimit": "1000000", "GeneralAggregateLimit": "2000000"},
     "value": 1.52, "mode": "replace"} ] }
```

**Command-line tools are the primary interface for v1:** `deviations validate | compile | show |
diff | import-xlsx | sign-off`.

- **`validate`** refuses:
  - a key ISO doesn't have in that edition's table
  - two `replace` rows at the same specificity
  - incoherent effective dates
  - an LCM outside the band without a note
- **`show`** reads the compiled form back as the authored rows (I1).
- **`diff`** compares versions, or a version against ISO's values.

### 3b. Request

A normal ISO request with two optional header fields we own:

```json
{"header": {"WritingCompany": "HP-CAS", "PolicyType": "New", ...}, "body": { ...unchanged ISO shape... }}
```

- `WritingCompany` absent → technical only. The response is exactly today's.
- `PolicyType` absent → `New`, with a warning (O1).
- **Both fields are removed** before ISO's rules run and before any call to ISO's service (M6).

### 3c. Response

- **The ISO tree is still ISO-shaped.** It has the same paths and fields as ISO's own response, so
  Trace Diff and every existing comparison keep working.
- In the carrier result, the only fields that differ from technical are LCM fields and values
  downstream of a deviation (proved in §5, test T4).
- The `Deviation` block sits beside the tree, never inside it:

```json
{ "<ISO-shaped rated tree, carrier values>": "...",
  "Deviation": {
    "writingCompany": "HP-CAS", "policyType": "New",
    "edition": "GL TX 20260601 V01", "pinned": false,
    "filings": [{"id": "TX-GL", "version": 3, "new_eff": "2026-07-01", "renewal_eff": "2026-08-01"}],
    "technicalPremium": 3730, "carrierPremium": 4399,
    "waterfall": [ {"step": "edition pin", "effect": 0},
                   {"step": "LCM", "effect": 748},
                   {"step": "ILFPremOps", "effect": -79},
                   {"step": "rounding left over", "effect": 0} ],
    // Step order is fixed: edition pin, then LCM, then factor overrides in ISO table order.
    // Multiplied effects depend on order, so the order is fixed to keep the breakdown repeatable.
    "changedPaths": [ {"path": "…/GeneralLiabilityClassificationPremOpsCoverage/LCM",
                       "iso": 1.0, "carrier": 1.12, "row": "TX-GL.v3#1"}, "…" ],
    "warnings": ["Submitted LCM 1.10 on …PremOpsCoverage ignored (D13)"] } }
```

- **`technical` is a separate, untouched result** from the same call (`?with=technical`), not a
  field inside the carrier result.
- A request that can't be rated for the company is **refused with the reason**, never rated
  technical without saying so. Examples: a pin that can't be honoured, an unknown company code, or
  a filing that's approved but has a key missing from the edition.

---

## 4. Engine — where deviations enter

The engine entry point becomes `Kernel.rate(payload, company=None)` (and the same for CF).
`None` loads none of the new code: no company layer and no LCM step (I4).

- **4a. Resolution.**
  - `(company, juris, line)` → edition pin. The pin overrides the date choice at `resolver.py:105`.
  - The countrywide parent follows the pinned package's own declaration (N5). An impossible pin is
    refused.
  - The filing is picked by company, state, line and new/renewal date. The latest effective
    version wins.
- **4b. LCM, written onto each coverage record before rating.**
  - For each coverage record, the most specific matching LCM rows (by subline, class, territory and
    limit) are combined by replace/multiply. The result is written to `LCM` (GL) or
    `LossCostMultiplier` (CF) after removing any submitted value.
  - ISO's own `SetLCM` / `SetLossCostMultiplier` only look up the table when that field is empty,
    so they use it. Everything downstream is ISO's own calculation: base-rate rounding, LCM stat
    code, about 290 CF reads.
  - **Because the value travels on the request, ISO's service can check it**, class-specific LCMs
    included: send it the same request with the LCMs written in.
  - In GL this step sits in `Kernel.rate`. In CF it sits in `PropertyRunChecks.before`.
- **4c. Factor overrides, as a `CompanyBook` layer.**
  - The company tables sit in front of the state and countrywide layers in `table()`/`declares()`.
  - What a lookup returns is composed when it's looked up:
    - `replace` rows: the company value wins.
    - `multiply` rows: ISO's value × the factor.
    - keys the company doesn't mention: ISO's value.
  - `parent_table()` and ISO's references to a rule's countrywide parent skip the company layer
    (I3).
  - Trace lookups record the company row they came from.
  - GL's N3, CF's fallback when a state table is empty, and `strict_single_result` are untouched.
- **4d. Untouched:** ISO's rules, the interpreter's instructions, rounding, `_collect`.

---

## 5. The proof suite — "without breaking ISO" as tests

All of this runs in the existing harness (`results/`, ledger-capped ISO calls, Trace Diff's
`same()` on stable paths). Each test is a gate condition for Phase 3. **ISO** means ISO's live
service, and **identical** means every leaf ISO publishes, compared by Trace Diff, not just the
total.

| # | Test | What it proves | Population | Costs ISO calls |
|---|---|---|---|---|
| **T1** | **No-company sameness.** No `WritingCompany` gives results byte-identical to today's engine. | The new code changes nothing when it's not asked to | Every existing case: the 50/50, Regression Library, Quick smoke, and the 921 STC request fixtures | No |
| **T2** | **Identity deviations.** A company whose every row is neutral (LCM 1.0 replace; multiply 1.0 on every table ISO's definitions list) gives results identical to technical. | Every code path the layer opens leaves ISO untouched | Same as T1, both lines, every state | No |
| **T3** | **Technical still equals ISO.** With a company header present, the technical result equals ISO's service, and equals T1. | Our header fields never leak into the ISO tree or the ISO call | Quick smoke, 1 per state per line | Yes, about 100 |
| **T4** | **Only what was deviated changes.** For each deviation, compare technical and carrier field by field. Every changed path must be (a) downstream of a deviated lookup in the trace, and (b) explained by a row in `changedPaths`. Any other changed path fails. | Locality: a deviation can't move what it doesn't touch | One case per deviable table kind × both lines + the P0 filing | No |
| **T5** | **LCMs against ISO.** The carrier request with LCMs written in, sent to ISO's service, gives an identical tree. Includes LCMs keyed by class group, territory and limit. | The LCM part is right by ISO's own arithmetic, not ours | GL + CF, about 10 states, each subline and keying | Yes, about 60 |
| **T6** | **Override arithmetic.** For single-override cases, the downstream value ÷ technical equals the factor, within the declared rounding. Cases where a minimum premium applies are flagged and checked separately, since the floor breaks the ratio. The waterfall adds up exactly to carrier − technical on every case. | The overrides that ISO can't check are still checked | T4's set + T5's set | No |
| **T7** | **Boundaries.** A TX filing doesn't touch OK. A Prem/Ops LCM doesn't touch Products. The day before vs on the new date, and new vs renewal. A withdrawn version, superseded versions, a state opted out after the all-states shortcut, and a 52nd jurisdiction added later. | Deviations apply exactly where and when they're filed | Constructed cases | No |
| **T8** | **Pins.** A pinned company with no rows gives results identical to ISO-only rating of that edition. Impossible pins are refused. When ISO's service resolves the same edition, compare with it. | Pinning swaps the edition and nothing else | Constructed cases + whatever ISO's service accepts (O2) | A few |
| **T9** | **ISO revision.** The same filing rated over two editions: multiply rows follow the new ISO values and replace rows don't, and the "ISO changed" flag is raised. | A deviation survives ISO's revision correctly | Constructed cases on two editions | No |
| **T10** | **Files round trip.** Authored → compiled → `show` gives the same rows. Spreadsheet import → the same compiled files as hand-authoring. `validate` refuses each bad case. | The files say what people wrote | Unit tests | No |

**ISO budget:** about 160 calls for the whole suite, once T3, T5 and T8 are run. Everything else
is our engine against itself.

**A regression lane:** T1–T2 and T4–T10 join the Regression Library, so every future engine
change re-proves "no company = ISO" and "deviations stay local".

---

## 6. UI in this plan (minimal)

- **Upload & Compare:** a writing-company picker that fills the header field. The result shows
  ISO's service, technical and carrier side by side, the breakdown by deviation, and the
  `Deviation` block's warnings.
- **Proof results:** T1–T10 shown on the Readiness Matrix / Coverage Board pattern that already
  exists. Each test is a row with pass/fail and a link into Trace Diff.
- Everything else (the filings board, editor, review queue, impact preview, SERFF screen) waits.
  The wireframes are the reference when it comes.

---

## 7. Phases and gates

| Phase | Builds | Gate |
|---|---|---|
| **P0 — First real case** | Map your filing onto §3a by hand. No code. | Every item can be expressed, or the gaps are listed. §3 is revised here if needed. |
| **P1 — Files** | Authored format, compiler, `deviations` command-line tools, class groups, all-states shortcut and opt-out, workflow log, spreadsheet import. | **T10** passes. The P0 filing compiles and reads back. |
| **P2 — Engine + payloads (GL, then CF)** | Header fields, `company=` context, pin, LCM step, `CompanyBook`, `Deviation` block, `?with=technical`, refusals. | **T1, T2** pass across the whole existing population. The P0 filing rates. |
| **P3 — Proof** | Dependency tracking in the trace if it only records lookups today (T4 needs "which values came from which lookup"). The T3–T9 runner, inputs built for each test, ledger plan, results into the Regression Library. | **T1–T10 all pass**, recorded in `docs/gates/GATE-DEVIATIONS.md`. **This is the "doesn't break ISO" sign-off.** |
| **P4 — Minimal UI** | §6. | Compare shows the P0 filing correctly. The proof results are visible. |
| *Later* | The full Deviations tab (wireframes), SERFF intake, impact preview. | — |

Each committed phase adds a row to `C:\FederatoProjects\R_REBUILD.md`.

---

## 8. Open items

| # | Item | When |
|---|---|---|
| O1 | New vs renewal: use an ISO request field if one exists, otherwise `header.PolicyType` (default New, with a warning). | P2 |
| O2 | Whether ISO's service will rate a pinned older edition. Where it won't, T8 is internal-only, and Compare says "not comparable" rather than showing a mismatch. | P3 |
| O3 | ~~Minimum premiums and the terrorism percentage~~ **Decided 2026-10-09: follow the deviated premium.** ISO's rules calculate both from the carrier's deviated premiums; no special handling. A carrier that files its own minimum or terrorism percentage uses a factor override. | Closed |
| O4 | Expense constants, schedule-rating bounds, tiering: beyond v1. | Later |
| O5 | Carrier visibility of ISO tables is a licensing question. | Later |
