# How to test this, phase by phase

**Current as of 2026-08-13.** Every command on this page has been run and its stated output is what
it actually produced. **All six stages are built, and Phase 2 — the comparison against ISO's live
service — is live.** Nothing on this page is marked NOT BUILT any more.

One thing to know before you start: **the command-line tool is stage 1 only** — `resolve`, `parents`,
`table`, `check`, `census`. Rating is reached through the library, the web interface (`app.py`) or
the scripts, and this page uses whichever is real. There is no `cli rate`.

Run everything from the project root:

```
cd C:\Projects\Recursive_Harness_2.0
```

There are no dependencies to install for the engine. The document builder needs `markdown` and the
PDF scripts need `pypdf`; nothing else does.

---

## The one command

If you only run one thing, run this. It is every fixture and both expert agents.

```
python tests/verify_stage1.py                    20/20   which rulebook applies
python tests/verify_golden.py                    80/80   a real ISO-rated policy, no engine needed
python tests/verify_california.py                11/11   the sole GL_CW_20231201_V02 jurisdiction
python tests/verify_new_york.py                  10/10   the most-deviating jurisdiction
python tests/verify_oi50.py                        7/7   the one chain with no state deviation
python tests/verify_contract_figures.py             OK   every figure quoted in the contract
python tests/verify_interp.py                    58/58   the interpreter, node by node
python tests/verify_stage3.py                    38/38   premium, the two modes, referrals
python tests/verify_stage4.py                    28/28   input schemas and 51 sample submissions
python tests/verify_stage5.py                    18/18   the field catalogue and its legal values
python tests/verify_stage6.py                    30/30   the interface, over HTTP
python tests/verify_phase2.py                    11/11   against ISO's live service (see below)
python tests/verify_breadth.py                   18/18   the variant harness, and the risk shapes
                                                         it varies -- no live calls
python Agentic/iso-circular-expert/tools/smoke_test.py     19/19
python Agentic/iso-erc-expert/tools/smoke_test.py       88 checks
python -m gl_engine.cli check 20260811 --deep              13/13
```

Total run time about four minutes, most of it the last one.

**`verify_phase2` skips its live groups unless you pass `--live`**, and skips them cleanly when
`RAAS_*` is not configured. **A suite that needs a paid external service to pass is a suite people
stop running**, so the offline group always runs and reports `11/11, 1 skipped`.

Any other numbers mean something moved. **Nothing here is expected to be flaky** — every count is
pinned to a measured property of the corpus, so a change is a real change.

---

# Stage 1 — Load and resolve ✅ BUILT

*Which rulebook applies, for this state, on this date.*

### The acceptance test

```
python tests/verify_stage1.py
```

**20 cases**, each pinned to something measured before the code existed. Covers: all 51
jurisdictions resolving · identity read from ISO's own namespace and not the folder name · each
state taking **its own** declared national parent · the 2027 cliff · a pre-2022 date being refused ·
`Decimal` never float · banded and interpolated tables · empty-means-not-offered · the hidden
per-territory loss-cost files · both factor sentinels · the size-of-risk withdrawal · the typed cell.

### The load-time assertions

```
python -m gl_engine.cli check 20260811            # 6 checks, instant
python -m gl_engine.cli check 20260811 --deep     # 13 checks, ~50s
```

`--deep` opens every rate and domain table in all 51 jurisdictions — **5,364,957 numeric cells**
type-checked. The shallow form only resolves editions.

**These fail; none of them warns.** Try breaking one deliberately:

```
python -m gl_engine.cli check 20220831            # below the floor -> refuses, exit 2
python -m gl_engine.cli check 20270401 --deep     # the cliff date, also 13/13
```

| | What it proves |
|---|---|
| **A1 · A2** | Every package identifies itself, and its files agree about which package they are |
| **A3** | The as-of floor of 2022-09-01 holds (OI-41) |
| **A4 · A5** | All 51 jurisdictions resolve, and every declared national parent exists |
| **A6** | A state that declares an **older** parent still gets it. If this ever counts zero, the resolver has started taking the newest and five states are being rated wrong |
| **A7 · A8** | Every table classifies into a known shape; the CSV header matches ISO's declaration exactly |
| **A9** | Hidden per-territory loss-cost files are found — **or the whole family reads as unavailable**, which is what a withdrawn coverage looks like (OI-20 / OI-69 / OI-53) |
| **A10** | Both spellings of `ProductWithdraw(a)l` stay distinct — nobody "fixes the typo" and merges two different things (OI-47) |
| **A11** | Increased-limit factors never fall as the limit rises, in either direction of the grid |
| **A12** | Numeric columns hold numbers or nothing — never stray text |
| **A13** | Zero factors appear only in the three tables known to use zero as a marker (N13) |

### Looking at what resolved

```
python -m gl_engine.cli resolve NJ 20260811
python -m gl_engine.cli resolve CA NY TX 20260811
```

Shows the state package, the national parent it declares, and how many tables it overrides, inherits
and adds.

```
python -m gl_engine.cli parents 20260811
python -m gl_engine.cli parents 20270401
```

**Which national rulebooks are live.** Three today, three at the cliff — there is no date at which
one suffices. Today: California alone on `GL_CW_20231201_V02`; NJ, OK, TX and VT on `V03`; the
other 46 on `GL_CW_20260101_V01`.

### Looking at one table

```
python -m gl_engine.cli table NJ 20260811 PremOpsLossCost --rows 5
python -m gl_engine.cli table GA 20260811 PremOpsSizeOfRiskRelativity --rows 3
python -m gl_engine.cli table NJ 20260811 DomainTerritoryCodeByZipCode --kind Domain --rows 3
```

Reports which layer won, the shape, the row count, the key and value columns, and any banding or
interpolation. The Georgia one is the interesting case — it is the only shape that **interpolates**
between published values rather than stepping.

**The hidden-rows case, worth seeing directly:**

```
python -m gl_engine.cli table CA 20260811 PremOpsLossCost
python -m gl_engine.cli table TX 20260811 PremOpsLossCost
```

California reports **0 rows from a countrywide package** and then lists the **11 sibling files that
carry 13,068 rows**. Texas is the control — one populated 9,504-row table and no siblings. An engine
that read only the obvious name would price California from nothing and never say so.

### Counting what is actually there

```
python -m gl_engine.cli census 20260811
```

Table counts by kind, shape and population across the 54 packages that resolve, plus the table names
most often filed empty. **Empty is a statement, not a gap** — `CertifiedActsOfTerrorismExposureClassFactor`
tops the list because 15 states replace it with their own.

### Using it as a library

```python
from gl_engine import EditionResolver, ResolvedBook

r = EditionResolver()
book = ResolvedBook(r.resolve("NJ", "20260811"))

book.table("PremOpsLossCost")          # what applies, empty or not
book.rating_table("ILFPremOps")        # raises if empty -- for premium paths
book.parent_table("PremOpsLossCost")   # explicitly the national copy
book.siblings("PremOpsLossCost")       # hidden per-territory files
book.cite("ILFPremOps", locator="row 4")
book.inventory()
```

---

# Stage 2 — The interpreter ✅ BUILT

*Executing ISO's rules rather than re-implementing them.*

```
python tests/verify_interp.py                    # 58/58
```

**54 language nodes**, each with an evaluator, plus the path dialect ISO's rules navigate with.
The suite is organised node by node, so a failure names the construct rather than the premium.

**The claim it was built to test — and it held.** The coverage walkthroughs in `docs/gates/` each
state the rule order and the arithmetic for one coverage, and the interpreter reproduces them
**with no coverage-specific code at all.** That was the strongest claim in
`docs/FROM-PLANNING-TO-BUILD.md` and the one most likely to be wrong.

The ERC content behind any single rule is still readable directly, which is what to reach for when
a trace does not look like the filed rule:

```
python Agentic/iso-erc-expert/tools/erc.py rule PremisesOperations SetBaseRate --st NJ
python scripts/erc/27_dump_rule.py
```

> **Four defects in this stage were silent rather than loud**, and each is worth knowing about
> because the shape recurs: `Sum` over a `ForEach` returned only the last iteration; the `[1]`
> path predicate went unparsed, so terrorism rows were never created; parent-scope dispatch made
> every state override unreachable; and the `ancestor::` axis was unimplemented, so statistical
> codes were absent. **None raised. All four produced a plausible number.**

---

# Stage 3 — Kernel and the two modes ✅ BUILT

*A submission goes in, a premium and its factors come out.*

```
python tests/verify_stage3.py                    # 38/38
python tests/verify_golden.py                    # 80/80, three layers
python scripts/rate_all_payloads.py              # every stored example
```

**The check it had to pass, and did:** Oklahoma's real ISO-rated policy comes back
`976 + 6,845 + 18 = 7,839` exactly, and the engine agrees with **49 of 49 usable stored examples**.

**The two modes are themselves a test.** `strict-erc` and `underwriting` run the same code path;
rate the same risk both ways and every difference is a risk ISO would quote and we would refer.
That report is a deliverable, not a diagnostic.

> **Three of the differences chased here turned out to be defects in the oracle, not the engine** —
> an ISO output filed under the wrong state, a jurisdiction rated against an edition that is not in
> the corpus, and a terrorism field ISO's own examples disagree with in 34 of 50 pairs. **Each was
> only provable because the engine was assumed wrong first** and the evidence was made to say
> otherwise. `docs/OPEN-ITEMS.md` OI-77 to OI-79 carry the account.

---

# Stage 4 — Schemas and payloads ✅ BUILT

*One sample submission per state, same class code and exposure everywhere.*

```
python scripts/build_sample_payloads.py          # writes Engine_Payloads/<ST>/submission.json
python tests/verify_stage4.py                    # 28/28
python scripts/check_payload_pairs.py            # the stored examples, input paired to output
python scripts/diff_payload.py <ST>              # ours against ISO's, field by field
```

**What it produced:** 51 submissions, **the same risk in every state** — one location, one
classification, class `50017`, gross sales. That was chosen so any difference between states is
attributable to a state deviation and nothing else, and it worked. Four states need an extra field,
because California, Florida, New York and Texas resolve territory by county or place. **Hawaii is
not in the corpus and fails loudly rather than falling back to countrywide.**

The 53 real ISO-rated examples it was built against are on disk and still checked:

```
python tests/verify_california.py                # 11/11 -- uses Payloads/CA
python tests/verify_new_york.py                  # 10/10
```

> **That one risk shape is now the limiting factor, not the engine** (OI-87). Fifty matches against
> ISO on a single shape is a narrower claim than it sounds, and widening it is the next work.

---

# Stage 5 — The enum workbook ✅ BUILT

*Every field a payload can carry, and its legal values, from ISO's own tables.*

```
python scripts/build_enum_workbook.py            # writes GL_Payload_Enums.xlsx
python tests/verify_stage5.py                    # 18/18
```

**The check it had to pass:** every value in the 53 real submissions appears in the workbook. **A
value ISO accepted that our workbook rejects is a defect in the workbook**, not in the submission —
so validation reports whether a field's legal values were resolved *exactly* or from a superset that
can accept an illegal value but never reject a legal one. 29 of 90 dependent domains resolve
exactly; every finding says which of the two it is (OI-84).

The workbook is written by `scripts/xlsx.py`, **standard library only** — like everything else here.

The underlying domain tables are readable directly:

```
python -m gl_engine.cli census 20260811
python -m gl_engine.cli table NJ 20260811 DomainScheduleType --kind Domain --rows 20
```

---

# Stage 6 — The interface ✅ BUILT

*Paste a submission, rate it, read every factor — and compare it with ISO.*

```
python app.py 8776                               # then open http://127.0.0.1:8776
python tests/verify_stage6.py                    # 30/30, exercised over HTTP
```

**It needed no change to the engine, which was the test.** If the interface had required the engine
to change, the engine's interface was wrong — that is the whole point of keeping them separate.
`http.server`, no framework.

**What it shows:** the premium, then *How it rated* — only the factors that actually fed the number
— with the full trace, the per-coverage premiums, referrals and the raw JSON behind tabs. **Every
number carries its source**, including which package and table it came from.

A view can be linked to, which is also how it is driven in tests:

```
http://127.0.0.1:8776/?sample=OK&mode=strict-erc&rounding=ROUND_HALF_UP&compare=1&rate=1
```

---

# Phase 2 — against ISO's live service ✅ LIVE

*The same submission through our engine and through ISO, compared on every published field.*

```
python tests/verify_phase2.py                    # 11/11 offline, live groups skipped
python tests/verify_phase2.py --live             # makes live calls
python scripts/phase2_compare.py OK              # one jurisdiction
python scripts/phase2_compare.py --all           # 50, and writes scripts/erc/out/phase2.csv
```

**Breadth — the same comparison over risks the samples never contain** (OI-87). One jurisdiction,
one risk shape is what phase 2 proves; this varies the submission instead of the state.

```
python scripts/breadth.py --list                 # the catalogue: 17 variants, 7 groups
python scripts/breadth.py                        # build, schema-check, rate ours -- no calls
python scripts/breadth.py --live                 # ...and compare against ISO
python scripts/breadth.py --juris NY --live       # any jurisdiction
python scripts/breadth.py --group deductible --live
python tests/verify_breadth.py                   # 18/18, offline
```

**Every value comes from ISO's declared domains**, and a variant whose value is not in one is
**refused at build time** rather than sent. Live calls are opt-in for the same reason `--all` is:
a script that quietly makes thirty-four calls to a rating service is a surprise nobody asked for.

> **A variant whose premium equals the base is reported as a finding, not a pass.** It means the
> chain the variant exists to exercise did not move the number.

**The result of record:** **OK 16 of 16 · NY 15 of 15** buildable variants agree with ISO on the
premium and on every published field. Breadth found **one engine defect (OI-88 — size-of-risk
refuses in OK where ISO rates it at 8816)**, one filed gate (**OI-89**) and one harness defect
(**OI-90**, closed). `verify_breadth` **asserts OI-88 is still open**, so closing it breaks that test
on purpose.

**Credentials come from the environment** (`RAAS_*`), never from a file in this repository.
`scripts/raas.py` is a standard-library OAuth2 client — no `httpx`, no dependency — and **it logs no
secret or token**, which `verify_phase2` asserts by parsing the source rather than grepping it.

**The result of record:**

| | |
|---|---|
| Sent to ISO | **50 of the 51** |
| Premium **and every field ISO publishes** agree | **50 of 50** |
| ISO used the edition we resolved | **50 of 50**, from its own response header |
| Never sent | **PR** — not on the subscription, and that entitlement is not available (OI-86) |

**Puerto Rico is excluded from comparisons, not from the engine.** It still rates; there is simply
no external answer to check it against — no entitlement and no stored priced example either. **Every
count of live agreement is `n of 50`, never `of 51`.** Naming `PR` explicitly on the command line
still runs it, so this reverses in one command if the subscription changes.

The same run is available in the interface — *Test every jurisdiction* → **Run the full test** —
which reports `50 of 51 match ISO exactly` with a pass/fail bar and a row per state. **It takes
about twenty minutes**, because each jurisdiction is a real call; the command line is faster and the
page exists so the answer can be read by someone who would run neither.

---

# The two expert agents — check the engine against the sources

These are independent of the engine and work today. Use them when a number looks wrong and you want
to know what ISO actually filed.

### The manual and circular authority — 1,122 documents

```
python Agentic/iso-circular-expert/tools/smoke_test.py          # 19/19

python Agentic/iso-circular-expert/tools/iso.py territory NJ --zip 07030
python Agentic/iso-circular-expert/tools/iso.py rate TX --class 10010
python Agentic/iso-circular-expert/tools/iso.py rate TX --class 91581      # returns REFER, not zero
python Agentic/iso-circular-expert/tools/iso.py rule 45 --st TX
python Agentic/iso-circular-expert/tools/iso.py circular LI-GL-2022-325
python Agentic/iso-circular-expert/tools/iso.py effective NJ --date 2026-06-01
python Agentic/iso-circular-expert/tools/iso.py grep "increased limits tables" --kind RU
python Agentic/iso-circular-expert/tools/iso.py invariant --severity BLOCKER
```

### The ERC authority — the machine-readable files

```
python Agentic/iso-erc-expert/tools/smoke_test.py               # 88 checks

python Agentic/iso-erc-expert/tools/erc.py --help
python Agentic/iso-erc-expert/tools/erc.py asof NJ 2026-08-11
python Agentic/iso-erc-expert/tools/erc.py resolve NJ 2026-08-11
python Agentic/iso-erc-expert/tools/erc.py identity GL_NJ_20260301_V01
python Agentic/iso-erc-expert/tools/erc.py table PremOpsLossCost
python Agentic/iso-erc-expert/tools/erc.py coverage NJ
python Agentic/iso-erc-expert/tools/erc.py juris NJ
python Agentic/iso-erc-expert/tools/erc.py territory NJ
python Agentic/iso-erc-expert/tools/erc.py rule ErcProcess
python Agentic/iso-erc-expert/tools/erc.py premium
python Agentic/iso-erc-expert/tools/erc.py corpus
python Agentic/iso-erc-expert/tools/erc.py invariants
```

**Watch the date format.** This agent takes **`2026-08-11`**; the engine takes **`20260811`**. They
disagree, deliberately — the agent's dates come from circulars, which print them that way, and the
engine's come from ISO's package names, which do not. Both refuse a malformed date rather than
interpreting it. `rule` answers from a model index, not from every rule instance, so an unknown name
returns *"unverifiable from the knowledge base"* rather than a guess — which is the behaviour you
want from a second opinion.

**Use them as a second opinion, not as a source.** The manual **confirms** and never **sources** —
if the two disagree, that is an escalation, not a correction.

---

# The analysis scripts — re-runnable evidence

Every figure in the documents came from one of these and every one still runs. Use them to re-derive
a number rather than trusting a document.

```
python scripts/erc/32_asof_recount.py 20260811 20270401 99999999
python scripts/erc/32_asof_recount.py 20260811 --only F1
python scripts/erc/35_census_sizeofrisk.py 20260812
python scripts/erc/37_terrorism_align.py 20260812
python scripts/erc/38_rating_plans_align.py 20260812
python scripts/erc/39_state_specific_align.py 20260812
python scripts/erc/40_referral_census.py 20260812
python scripts/erc/41_referral_register.py 20260812
```

**Every one of these requires an as-of date and none of them has a default.** That is deliberate and
it is the same rule the engine enforces: *"latest"* is not *"now"*, because this corpus holds filings
that have not taken effect. Passing `99999999` to `32_asof_recount.py` gives the end state, which is
how several early figures were accidentally measured — **if a number differs across the columns, it
is a claim whose tense needs fixing.**

Full index: [`scripts/README.md`](scripts/README.md).

---

# Rebuilding the documents

```
python scripts/build_docs_html.py
```

Regenerates `docs/GL-RATING-ENGINE-DOCS.html` — 21 tabs, every plan and gate document in one page.
The plain-English overview is separate and hand-written:
`docs/THE-PLAN-IN-PLAIN-ENGLISH.html`.

---

# What a failure means

| Symptom | Read it as |
|---|---|
| A count is off by a little | **The corpus changed.** ISO filed something. Find out what before adjusting the number |
| A count is off by a lot | Usually a **population error** — something measured in one place and stated about everything. Sixteen of this project's corrections are that one mistake |
| A new assertion passes first time | **Suspect it.** Twice now a check's condition has been narrower than its name, and the second one passed while blind (OI-69). Confirm it can fail before believing it can pass |
| `ReferToCompany` | Not a failure. ISO declines to price it and so do we |
| `TableError: ... NOT OFFERED HERE` | Also not a failure. An empty table is a statement, and the engine refused to read it as zero |

**Corrections are kept, never tidied away.** Anything found here belongs in
[`BUILD-LOG.md`](BUILD-LOG.md) with what it revealed — that record is the raw material for the
self-correcting harness, which is the end goal.

---

## Appendix — stages 2 and 3 in more detail

**Every command below has been executed and every stated output is what it actually produced** — the
rule this file adopted after an expected output was once written before the command was run.

### Rate the golden case

```
python -c "from gl_engine.rating import Kernel; print(Kernel().rate(r'C:\Projects\ISO_ERC_Files\General_Liability\OK\GL_OK 20250601 V01\GL OK 20250601 V01\STC\1. Input.json').premium)"
```
```
7839
```

Oklahoma's real ISO submission, priced end to end. `976 + 6845 + 2 + 16 = 7839`, which is what ISO's
own `1. Output.json` beside it publishes.

> **Note the path.** The golden case is the **STC** input inside the corpus, *not*
> `Payloads/OK/1. Input.json` — that is a different submission and prices to `8229`. The first draft
> of this section pointed at the wrong file and would have printed a number that looked like a
> failure. *(When it was written that second submission priced to `7852`, which is what made it one
> of the 28 open differences under `OI-76`; the defect behind it — an unparsed `[1]` path predicate,
> so terrorism rows were never created — has since been fixed, and it now agrees with ISO.)*

### The acceptance suites

```
python tests/verify_interp.py
```
```
58/58 passed
```

Four groups: every one of the **54** language nodes has an evaluator (the list is read from the
corpus census, not typed into the test, so a 55th node in a future filing fails here); the semantics
of each node group against its contract clause; a real ISO package executed; and every hard failure
in contract §12 actually firing.

```
python tests/verify_stage3.py
```
```
38/38 passed
```

The golden case, **all 83 policy-level numbers compared field by field against ISO's own output**,
the kernel surface, both modes, the refusals, and breadth across all 50 priced examples.

```
python tests/verify_contract_figures.py
```
```
OK  every figure quoted in the contract is one the corpus produced
    (node_surface.csv, node_children.csv, contract_questions.txt)
```

Checks the evaluation contract against the corpus. **Requires the analysis output first** —
`scripts/erc/out/` is not committed:

```
python scripts/erc/42_node_surface.py
python scripts/erc/44_contract_questions.py
```

### Reconcile against ISO's own answers

```
python scripts/rate_all_payloads.py
```
```
    AS FILED                        : 28 of 50 match
    WITH ISO'S OWN TerrorismCoverage: 48 of 50 match  (34 pairs dispute that one field -- OI-77)

    AGAINST USABLE ORACLES ONLY     : 49 of 49 match   (1 excluded, OI-78)
        AZ: its output file is Alaska's (State: AK); no AZ output exists
```

**This is the offline half of Phase 2.** Writes `scripts/erc/out/reconciliation.csv` so runs can be
diffed. **Every DIFF that survives the third line is our defect until proven otherwise** — that is
what `strict-erc` mode is for.

**Read the three lines in order, because the first one understates it badly.** The gap between line
1 and line 2 is a **single field the oracles disagree with themselves about**: 34 of the 50 stored
pairs carry a `TerrorismCoverage` value ISO's own rating does not reproduce (OI-77). The gap between
2 and 3 is **Arizona's output file being Alaska's** — there is no AZ oracle at all (OI-78). Neither
was accepted on argument; both were established from ISO's own files, after the engine was assumed
wrong first.

> **`22 of 50` was the honest number when this section was written**, and the count moved to 28 as
> real defects were fixed. **It is kept here rather than quietly overwritten** — the arc from 22 to
> 49 of 49 is the evidence that the method works, and a file that only ever shows the current
> number cannot show that.

### The other stage-2 measurements

```
python scripts/erc/43_default_block.py        # the entry point, all 567 packages
python scripts/erc/45_nillable_vs_allownull.py # who decides whether a read may be null
```

Both read the whole corpus and take about half a minute each.
