# Analysis & Build Scripts

Every number in `docs/rating-engine/`, every row in `GL_LossCost_to_ERC.xlsx`, and every file
in `Agentic/iso-circular-expert/knowledge/` was produced by these scripts. They are kept so the
work is **reproducible and auditable** rather than a set of numbers nobody can re-derive.

> **These were run from a scratch working directory during Steps 6–10** and are preserved here
> as-is. Each resolves paths relative to **its own location** (`HERE = dirname(__file__)`), so
> running them from `scripts/` writes the intermediate files into `scripts/`. That is fine —
> just be aware the intermediates are large (~200 MB of extracted text) and should not be
> committed. See "Working files" below.

---

## Pipeline order

Steps 1–4 are the expensive ones (~1.5 hours total, parallelised across 10 workers). Everything
after is seconds to minutes.

| # | Script | Produces | Notes |
|---|---|---|---|
| 01 | `01_probe_extractor.py` | `lc_extractor.json` | Which loss cost PDFs `pdftotext` can read. **This is the evidence** for the 389/83 split and the finding that 41 of 51 current notices need the fallback |
| 02 | `02_extract_dualmode_losscosts.py` | `lc_text/`, `lc_layout/` | Both `pdftotext` modes. Kept because the **`-layout` vs `pypdf` comparison** is what established the row-misalignment defect. Not used for any published number |
| 03 | `03_extract_pypdf_losscosts.py` | `lc_pypdf/` | **The authoritative loss cost text.** Page-tagged `<<<PAGE n>>>` |
| 04 | `04_extract_pypdf_rules.py` | `Agentic/.../text/rules/` | **The authoritative rules text.** Writes straight into the agent |
| 05 | `05_analyze_losscosts.py` | `lc_analysis2.json` | Per-notice structure: page families, territories, class codes, cell vocabulary, ELP counts |
| 06 | `06_scan_territory.py` | `territory_scan.json` | Territory Pages (`CG-T-n`) across all 503 rules PDFs: scheme, ZIP rows, territory codes |
| 07 | `07_match_losscost_to_erc.py` | `lc_match.json` | Loss cost notice → ERC edition, via cited circular / filing / date proximity |
| 08 | `08_build_losscost_workbook.py` | `GL_LossCost_to_ERC.xlsx` | The Step 6 deliverable |
| 09 | `09_report_losscosts.py` | *(stdout)* | Roll-ups behind `13-LOSS-COSTS-AND-ELP.md` |
| 10 | `10_report_territory.py` | *(stdout)* | Roll-ups behind `05-LOOKUP-TABLES.md` §5.4.1. **Whitespace-normalised** — see below |
| 11 | `11_build_dataset.py` | `docs/rating-engine/dataset.json` | Adds `loss_costs` and `territory_definitions` blocks |
| 12 | `12_build_agent_kb.py` | `Agentic/.../knowledge/*.json` | Circulars, notices, jurisdictions |
| 13 | `13_extract_terrorism.py` | `Agentic/.../text/terrorism/` | The Terrorism Supplement, page-tagged. Superseded by 15 for new families |
| 14 | `14_build_terrorism_kb.py` | `Agentic/.../knowledge/terrorism.json` | 52 jurisdiction→version assignments, 24 version blocks, the 142 above-average classes |
| 15 | `15_extract_manual_family.py` | `Agentic/.../text/<slug>/` | **Ingest any manual family.** `--all` does Terrorism, Schedule & Experience and Composite Rating. Dual-mode extraction |
| — | `verify_index_html.js` | *(exit code)* | Executes `index.html`'s render logic under a DOM shim. `node verify_index_html.js` |

Script 03 also feeds the agent: copy `lc_pypdf/*.txt` to
`Agentic/iso-circular-expert/text/losscosts/`.

### The test harness is separate again — and it is not a pipeline

The numbered scripts derive content once. These run every day and answer *"does the engine still
agree with ISO"*. They share the run store and nothing else with the pipeline above.

| Script | What it is |
|---|---|
| `variants.py` | **What may be varied and what each option legally holds**, read from ISO's declaration per jurisdiction. 20 controls. The most-read file here |
| `sweep.py` | One configuration across jurisdictions, engine-only or against ISO. **Three outcomes, not two** — a state that cannot express the configuration is `NOT APPLICABLE` and says why |
| `qa.py` | **The tier programme** — T0–T4, a pairwise matrix, a cost estimate and a budget gate |
| `layers.py` | **The layered programme** — four layers, an allowance that thins configurations and never states, and a ticker instead of a gate. Added 2026-08-18; see [`docs/UI-STRATEGY.md`](../docs/UI-STRATEGY.md) |
| `qa_review.py` | The review passes: is a *not applicable* real, is a refusal ours or ISO's |
| `reviews.py` | **Per-run review records** — a mechanical pattern match first, a markdown brief for what it can't explain, and a place to paste back what a person said. No API key anywhere in it. Added 2026-08-18; see [`docs/UI-STRATEGY.md`](../docs/UI-STRATEGY.md) |
| `runstore.py` | **Every run, kept.** Append-only JSON lines under `results/`. A store that is rewritten cannot answer *when did this start disagreeing* |
| `phase2_compare.py` | **The one definition of agreement.** Everything else calls it, so there is never a second one to drift |

### The ERC pipeline is separate — `scripts/erc/`

Scripts 01–12 above derive from the **manual PDFs**. The ERC clean-room derivation lives in
[`scripts/erc/`](erc/), numbered `00`–`34`, and writes to `scripts/erc/out/`. It shares no code
with the pipeline above; that separation is what makes the two derivations independent evidence.

**Five of them take an as-of date, and four of those require one.** Any script that answers
*"how many jurisdictions do X"* must, because the corpus holds **82 state packages effective after
today** and "latest" therefore describes a future state (N4;
[`docs/gates/RECONCILIATION.md`](../docs/gates/RECONCILIATION.md) §1).

| Script | Answers | As-of date |
|---|---|---|
| `31_migration_asof.py` | The 2027 class-basis cliff and the OCP loss-cost withdrawal | Optional — defaults to today / cliff / end state |
| `32_asof_recount.py` | Territory scheme · countrywide table population · class inventory · rating-vs-capture · gate-cited tables | **Required** |
| `33_phase_sizing.py` | Rules, calculators, deviation surface and tables per build-order item | **Required** |
| `34_crosscheck.py` | **Cross-checks the project's lists against the corpus and each other** — every rate-driven coverage has a build-order owner; every selector found by content is named in the plan; no *populated* table is unread; sentinel families are fully counted | **Required** |
| `35_census_sizeofrisk.py` | **Build-order item 8.** Enumerates size-of-risk tables by listing the directory, size-of-risk lookups by reading rule bodies, and jurisdictions by resolving as-of — then classifies every member. Answers *who ships loss costs* (35 of 51), *who shards* (2), and *what binds a concept to a table* (the **setter**, not the lookup or the table name) | **Required** |
| `36_manual_sweep.py` | **Negative claims about the manual, with a denominator.** Opens **every** pdf under `Commercial Line Manuals/` across a process pool and reports matches plus a by-family breakdown of what could not be read. **Dual-mode: `pdftotext`, falling back to `pypdf`** — the single-mode version reported 187 documents as "image-only" and they were nothing of the kind (OI-51). Takes any regex: `python 36_manual_sweep.py "experience rat"` | On demand |
| `41_referral_register.py` | **Build-order item 12, step 2.** Classifies the referral population into the four kinds — DECLARED (load-time), MISSING (rate-time), GUARD (as wide as the guard) and NONE (undetectable, therefore a decision) — and emits `out/referral_register.json`, the artifact `escalate/` consumes. **Cross-checks its own judgement against step 1's measurement**: the NONE count and the reconciliation's undetectable count are computed separately and must agree | **Required** |
| `40_referral_census.py` | **Build-order item 12, step 1.** Finds referral conditions by scanning — sentinel cells and the rules that test them (edition-scoped, N18), single-valued rating-basis selectors, coverages with no filed rate, the guard population, and tables a jurisdiction empties while the reading rule stays in force. **Reconciles against the eleven-gate population and reports which conditions no probe can reach** — those are decisions, not code. Amended four filed gates on its first run | **Required** |
| `39_state_specific_align.py` | **Build-order item 11.** Derives the state-only coverage population by differencing countrywide groups against jurisdiction groups — never by matching state names — then classifies every member and sizes the five that rate | **Required** |
| `38_rating_plans_align.py` | **Build-order item 10 / OI-01, OI-02, OI-03.** Enumerates both plan corpora by jurisdiction and edition, finds the ERC apparatus by rule name, and differentials the numbers: manual Rule 9 Table 9 against the 8 schedule-rating domains, and Rule 16's three columns against three 99-row ERC tables | **Required** |
| `37_terrorism_align.py` | **Build-order item 9 / OI-37.** Audits the terrorism population from the 477 premium-writing groups by *rule content*, not by group name; names the premium source of every `OTHER` group; and differentials the filed factors and the above-average class list against the Terrorism Supplement | **Required** |

**A new ERC script that reports a per-jurisdiction count and does not take an as-of date is a
defect. And a script that reports a bare count without its denominator is a defect too** — see
build plan §9 habit 8. Every count is `n of N`, with `N` enumerated from the corpus.

Both rules exist because both were broken — the as-of one by a gate in the same session that wrote
it down ([`docs/gates/OI-40-ASOF-RECOUNT.md`](../docs/gates/OI-40-ASOF-RECOUNT.md)), and the
denominator one **five times in a single day** across seven gates.

**A third rule, from `36_manual_sweep.py`: a tool's silence is not the corpus's silence.** That
script's first version used `pdftotext` alone and reported **187 of 1,030 manual documents have no
text layer**, which went into a gate as an 82%-of-corpus bound on a negative claim. They are not
image-only — this build of `pdftotext` returns zero bytes on them and `pypdf` reads them in full
(`GL-CT-2026-LC-001-C`: 0 against 218,978). **`scripts/02_extract_dualmode_losscosts.py` had carried
that fallback since 2026-08-10 and nothing compared the two.** Dual-mode now: **1,118 of 1,120
readable, 2 fail both.**

So: **before reporting that a corpus cannot be read, check it against another extractor already in
this repository.** And when a document genuinely cannot be read, report it separately — it is part
of the denominator and it is not evidence of absence.

*(A fourth, smaller one from the same episode: **do not read a script's truncated output as its
result.** The sweep prints 40 unreadable files; the first 40 are alphabetical, and reading them as
the whole set produced "all of them are loss-cost circulars" when it was 103 rules manuals to 83.
Every list-printing script here now prints a full by-family tally alongside the sample.)*

---

## Two defects these scripts exist to prevent

Both were found the hard way, and both are silent — they produce plausible output.

**1. `pdftotext -layout` scrambles the rate grids.** Values detach from their class code and
reattach to the row above. Every resulting number is a valid-looking loss cost. `pypdf` reads
the same pages correctly. Scripts 03 and 04 use `pypdf` for that reason; script 02 exists only
to reproduce the comparison.

*The check that catches it:* territories × classes × 2 must equal the parsed cell count.
Indiana: 4 × 1,188 × 2 = **9,504**, and the `pypdf` parse returns exactly 9,504. A misaligned
parse does not reconcile.

**2. `pypdf` injects spaces inside words.** It renders `UNMANNED AIRCRAFT LI MITED LIABILITY`,
`SUB LINE`, `CG -LC -89`, `LI -GL -2019 -216`. Any literal string match under-reports — and in
this domain a false negative reads as *"the manual is silent"*, which is the worst possible
error.

**Every caption, page-marker and reference match on `pypdf` output must be
whitespace-normalised.** This bit twice: once reporting the Unmanned Aircraft table as present
in 47 of 51 jurisdictions when all 51 carry it, and again at Step 10 missing the circular
reference on 189 loss cost notices. Script 10 normalises; scripts written later should copy its
approach.

---

## Working files (not committed)

The intermediates below are regenerable and large. Keep them out of version control.

```
lc_extractor.json      lc_match.json          lc_analysis2.json      territory_scan.json
lc_text/  lc_layout/   lc_pypdf/              appendix.json
```

`lc_text/` and `lc_layout/` (~150 MB) are needed only to reproduce the extraction comparison.
`lc_pypdf/` is superseded once its contents are copied into the agent's `text/losscosts/`.

---

## Dependencies

`pypdf`, `openpyxl`, and `pdftotext` (Poppler) on `PATH` for scripts 01–02. Node for the HTML
verifier. Scripts 05–12 are standard library plus `openpyxl`.

The **agent's** query-time tool (`Agentic/iso-circular-expert/tools/iso.py`) has no third-party
dependencies at all — that is deliberate, so the agent runs anywhere.
