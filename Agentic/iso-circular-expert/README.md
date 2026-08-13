# ISO Circular Expert

A self-contained agent that answers ISO General Liability manual questions **from the filed
documents**, with a citation on every claim. Built for the recursive review loop around the
GL rating engine: it checks engine output against the manual and returns machine-readable
findings that automation can act on.

- **Agent definition:** [`AGENT.md`](AGENT.md) — role, protocol, failure modes, output contract
- **Retrieval tool:** [`tools/iso.py`](tools/iso.py)
- **Knowledge base:** [`knowledge/`](knowledge/) — invariants, jurisdictions, circulars, notices
- **Corpus text:** `text/rules/` (503 files, 502 readable), `text/losscosts/` (472 files, 471 readable), page-tagged

Registered as a Claude Code subagent at `.claude/agents/iso-circular-expert.md`, so it can be
invoked directly:

```
> use the iso-circular-expert to check this premium against the manual
```

---

## What it is built on

| | Rules | Loss Costs |
|---|---|---|
| Source PDFs | 503 | 472 |
| Text-extracted | 502 | 471 |
| Jurisdictions | 51 (50 states less HI, plus DC and PR) | 51 |
| Years | 2021–2027 | 2020–2027 |
| Supplies | Rules 1–56, state exceptions, ILF tables, ILTAs, Classification Table, **Territory Pages** | Loss costs by class/territory/subline, **ELP Supplement**, loss cost mappings |

Extraction is `pypdf` throughout, page-tagged. That is deliberate: on the loss cost and ELP
grids `pdftotext -layout` **silently misaligns rows**, detaching values from their class code
and reattaching them to the neighbour. Every resulting number is a plausible loss cost, so the
corruption is invisible downstream. See `docs/rating-engine/08-INGESTION-SPEC.md` §8.3.1.

---

## Quick start

```bash
cd Agentic/iso-circular-expert/tools

python iso.py state NJ                       # jurisdiction profile
python iso.py territory NJ --zip 07030       # ZIP -> territory, cited to notice + page
python iso.py rate TX --class 10010          # loss cost per territory, with meaning
python iso.py rule 56 --st MU                # countrywide rule text
python iso.py effective NJ --date 2026-06-01 # which notices governed at a date
python iso.py invariant --severity BLOCKER   # the review checklist
python iso.py grep "OWNERSANDCONTRACTORS" --squash --kind LC
```

Python 3 only, no third-party dependencies at query time.

**`--squash` matters.** `pypdf` injects spaces inside words (`SUB LINE`, `CG -LC -89`), so a
literal match silently under-reports. In this domain a false negative reads as *"the manual is
silent"* — which is exactly the error class this agent exists to prevent.

### Worked example

```
$ python iso.py territory NJ --zip 07030
  "scheme": "ZIP_TABLE", "count": 15,
  "lookup": { "zip": "07030", "usps_name": "HOBOKEN", "territory": "504",
              "page": 28, "notice": "GL-NJ-2027-RU-001" }

$ python iso.py rate TX --class 10010
  "territory": "001", "prem_ops": ".188", "prod_compops": ".142",
  "prem_ops_meaning": "published loss cost (pre-LCM)"
```

---

## Why the invariants file is the core

`knowledge/invariants.json` holds **32 verified invariants** (17 BLOCKER, 10 MAJOR, 5 MINOR), each with severity, evidence and
a concrete check. They are not style guidance — each was computed over the corpora, and each
corresponds to a way this specific program breaks a rating engine. A sample:

| ID | Severity | What it catches |
|---|---|---|
| `INV-CELL-ALPHABET` | BLOCKER | `–` or `(a)` coerced to `0.00`. 35.7% of all grid cells are one of these two |
| `INV-TERRITORY-SCHEME` | BLOCKER | ZIP-only territory resolution — fails silently in CA, FL, NY, TX |
| `INV-VINTAGE-SPLIT` | BLOCKER | A global class list; 36 jurisdictions moved to the 2027 basis, 15 have not |
| `INV-OCP-WITHDRAWAL` | BLOCKER | OCP bound to a loss cost table 36 jurisdictions have withdrawn |
| `INV-RULE-KEY` | BLOCKER | Rules keyed by printed number; Rule 22 changed meaning in CW 2027 |
| `INV-EXTRACTION-MODE` | BLOCKER | Rate grids parsed with `pdftotext -layout` |

Start a review with `iso.py invariant --severity BLOCKER`. Most defects in this domain are
invariant violations rather than arithmetic errors.

---

## Output contract

The agent emits JSON — a verdict, ranked findings with `authority` citations, and an explicit
`unverifiable` list. `verdict: UNVERIFIABLE` is a **valid answer**, not a failure: four inputs
(Terrorism Supplement, carrier LCM, the rating plans, WC loss costs) are genuinely outside both
corpora, and inventing them would be worse than declining. Full schema in `AGENT.md` §5.

`auto_fixable: true` is reserved for mechanical fixes with unambiguous authority. Anything
needing a schema change or a business decision comes back `false` with the decision named.

---

## Rebuilding

The build scripts are in [`scripts/`](../../scripts/) at the repo root, numbered in pipeline
order and documented in [`scripts/README.md`](../../scripts/README.md). To rebuild after the
corpora change:

```bash
python scripts/03_extract_pypdf_losscosts.py   # -> lc_pypdf/, copy to text/losscosts/
python scripts/04_extract_pypdf_rules.py       # -> text/rules/ directly
python scripts/05_analyze_losscosts.py         # -> lc_analysis2.json
python scripts/06_scan_territory.py            # -> territory_scan.json
python scripts/12_build_agent_kb.py            # -> knowledge/*.json
python Agentic/iso-circular-expert/tools/smoke_test.py   # 15 cases, must stay green
```

Use `pypdf` and keep the `<<<PAGE n>>>` tags — the page tag is what makes every answer
citable, and `pdftotext -layout` silently misaligns the rate grids.

`invariants.json` is **hand-maintained**. Each entry cites the evidence that established it and
should change only when the corpus contradicts it — not to match new code.

---

## Known limits

| | |
|---|---|
| Absent from both corpora | Terrorism Supplement · company LCM · CGLES/Composite/Size-Of-Risk · Workers Compensation loss costs · Hawaii |
| Unreadable source files | `GL-MO-2027-RU-003`, `GL-MI-2027-LC-003` — truncated PDFs; the agent uses the prior notice and says so |
| Provisional dating | 264 rules notices and 57 loss cost notices are dated by proximity, not a cited circular. The tool surfaces `date_confidence` and the agent must downgrade conclusions resting on `LOW` |
| Cell-level rate data | The agent reads rates out of the page text on demand. The ~429,700 grid cells are **not** loaded into a database — that is Phase 3A of the build backlog |
