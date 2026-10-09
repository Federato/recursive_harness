# Carrier Deviations — Plan for sign-off

**Status: v3, 2026-10-09. v2 signed off; v3 folds in the P0 decisions (D17–D20) from the UFG Iowa CF filing — see `docs/deviations/P0-UFG-IA-CF.md`. P0, P1 and P2 done; P3 (proof) next.** This is Phase 4 of the original programme
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
| D11 | Checking against ISO's service | **Yes for LCM**, including class, territory and limit keyed LCMs (§4b makes them all checkable). Group LCMs (D17) are checked with one ISO call per distinct LCM. |
| D12 | Storage | **Per-company content in ERC shape** (RateTable CSV + Def XML), plus workflow metadata |
| D13 | LCM already in the request | **Carrier deviation wins**, with a warning if the request's value isn't 1. Technical ignores any value in the request. |
| D14 | Class groups | **ISO groupings plus company lists** |
| D15 | How a request names its company | **`header.WritingCompany`**. If it's absent, the request rates technical only. |
| D16 | First real case | **You provide a filing** (Phase 0) — UFG Iowa CF LCMs, SERFF UNFG-134289779 |

### Taken 2026-10-09 (from P0)

| # | Question | Answer |
|---|---|---|
| D17 | A filing has a different LCM per CF coverage group, but ISO carries one `LossCostMultiplier` per record (G1) | **Option A: group LCMs.** Wherever ISO's rules multiply a group's base rate by `LossCostMultiplier`, the engine uses that group's company LCM. ISO's rules, rounding and order are unchanged. The record's own LCM field holds the Group I value. (§4b) |
| D18 | The filing's documents disagree | **The filed PDF wins** over any typed summary. UFG: 6/1/2025 new, 10/1/2025 renewal. |
| D19 | Which line the engine work starts with | **CF first, then GL** (the P0 filing is CF). |
| D20 | Smaller P0 gaps | Stat code reports the Group I LCM (G2). One authored file per company, sharing the SERFF id (G3). Scope gains a **rating basis** key, specific or class (G5). Class groups may sit at carrier level and use code ranges, expanded against the edition's class list (G7). |

### My calls (push back if wrong)

| # | Call |
|---|---|
| M1 | Layer chain: **company-state > ISO-state > ISO-countrywide** (follows from I2). |
| M2 | **LCM is written onto the request; group LCMs (D17) are substituted inside the group products; factor overrides are a table layer.** See §4. |
| M3 | Technical is rated on the **same edition** as carrier (the pinned one if there is a pin), so a carrier-vs-technical difference is only ever deviations. |
| M4 | Workflow metadata is append-only JSONL, latest line wins (the console's convention). Only approved versions compile. |
| M5 | Class groups, territory lists and the all-states shortcut are **expanded to explicit keys at compile time**. Each compiled row remembers the authored row it came from. |
| M6 | **Our own fields never go into the ISO tree.** The request's company and new/renewal fields are removed before ISO's rules run and before any call to ISO's service. Our results go in a separate `Deviation` block beside the ISO tree (§3c). |

---

## 3. Files and payloads — how each behaves

### 3a. Deviation files

```
<CARRIERS_ROOT>/                                   outside the repo and the ZIPs; configured like GL_ERC_ROOT
  <carrier>/carrier.json                           approval policy, shared class groups (versioned, code ranges allowed)
  <carrier>/<company>/company.json                 code (e.g. HP-CAS), edition pins, class groups that override the carrier's
  <carrier>/<company>/workflow.jsonl               proposals, sign-offs, rejections (append-only)
  <carrier>/<company>/authored/<filing>.v<n>.json  the friendly form — what people edit
  <carrier>/<company>/compiled/<line>/<juris>/<filing>.v<n>/
        manifest.json                               effective dates, mode per table, ISO edition at approval,
                                                    authored-row ↔ compiled-row map
        LCM.Company.RateTable.csv                   explicit keys: subline, class, territory, limit → LCM
        GroupLCM.Company.RateTable.csv              CF: explicit keys: group, class, rating basis → LCM (D17)
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
  - a class range holding a code the edition doesn't have
- LCM bands are set **per group** (UFG's Group II LCMs run 2–4 legitimately).
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
- **4b′. Group LCMs (CF, D17).**
  - ISO's CF rules multiply each group's base rate by the record's single `LossCostMultiplier`: `BasicGroupIBaseRate`, `SpecificGroupIRate`, `BasicGroupIIBaseRate` / `LowestBasicGroupIIBaseRate`, `BroadBaseRate`, `SpecialBaseRate`, `EQBaseRate`.
  - When the filing has group LCMs, the engine substitutes the company's LCM for that group in exactly that product. Nothing else reads the substituted value; the rule, its rounding and its order are ISO's.
  - The record's `LossCostMultiplier` field (and so the stat code) holds the Group I LCM (G2).
  - The trace records each substitution with the compiled row it came from.
  - **Checking against ISO:** one ISO call per distinct LCM on the case, each with that LCM written onto the request. Each group's rate is compared with the call whose LCM matches it.
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
- **4d. Untouched:** ISO's rules, rounding, `_collect`. The only interpreter change is the group-LCM substitution in 4b′, which is inactive when `company=None` (I4).
- **4e. As built (P2), and its v1 limits.**
  - Property's entry point is `cf_engine.rating.rate(request, company=None, with_technical=...)`; GL's is
    `Kernel.rate(payload, company=None, with_technical=...)`. A request names its company in
    `header.WritingCompany`; the HTTP `/api/rate` does the same, with `?with=technical`.
  - Group LCMs (4b′) are matched to a group by ISO's own operand names (`BasicGroupIBaseRate`, `EQBaseRate`, ...).
    A rate product whose operand names no group (flood, terrorism, sublimits, endorsements) reads the record's
    LCM, which holds the Group I value (G2).
  - Records with no class anywhere above them, and the policy and location records, keep ISO's LCM; a warning
    says so when a group rate meets one.
  - One filing is in force per company, state and line: the latest effective date, then the highest version.
    Two filings in force at once (an LCM filing and a separate rule filing) would need composing across
    filings; not in v1.
  - The waterfall re-rates once per step; a Property company rating with a table override costs one rating
    per overridden table on top of technical and carrier.
