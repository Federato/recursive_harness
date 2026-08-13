# How to test this, phase by phase

**Current as of 2026-08-12.** Every command on this page has been run and its stated output is what
it actually produced. Commands for stages that do not exist yet are marked **NOT BUILT** and will
fail — they are listed so the file stays a complete map rather than growing one stage at a time.

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
python tests/verify_stage1.py
python tests/verify_golden.py
python tests/verify_california.py
python tests/verify_new_york.py
python tests/verify_oi50.py
python Agentic/iso-circular-expert/tools/smoke_test.py
python Agentic/iso-erc-expert/tools/smoke_test.py
python -m gl_engine.cli check 20260811 --deep
```

**Expected, in order:** `20/20` · `80/80` · `11/11` · `10/10` · `7/7` · `19/19` · `88 checks` ·
`13/13`. Total run time about three minutes, most of it the last one.

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

# Stage 2 — The interpreter ⏸ NOT BUILT

*Executing ISO's rules rather than re-implementing them.*

When it exists, these will work:

```
python -m gl_engine.cli rule NJ 20260811 PremisesOperations::SetBaseRate --trace
python tests/verify_interpreter.py
```

**How you will check it:** the eleven coverage walkthroughs in `docs/gates/` each state the rule
order and the arithmetic for one coverage. If the interpreter is right, **they should pass with no
coverage-specific code at all.** That is the strongest claim in
`docs/FROM-PLANNING-TO-BUILD.md` and the one most likely to be wrong.

Until then, the walkthroughs are checked by reading, and the ERC content behind them by:

```
python Agentic/iso-erc-expert/tools/erc.py rule PremisesOperations SetBaseRate --st NJ
python scripts/erc/27_dump_rule.py
```

---

# Stage 3 — Kernel and the two modes ⏸ NOT BUILT

*A submission goes in, a premium and its factors come out.*

```
python -m gl_engine.cli rate Engine_Payloads/OK.json --mode strict-erc
python -m gl_engine.cli rate Engine_Payloads/OK.json --mode underwriting
python tests/verify_kernel.py
```

**How you will check it:** Oklahoma's real ISO-rated policy must come back
`976 + 6,845 + 18 = 7,839` exactly. That case is already re-derived in `Decimal` today and passes
as arithmetic:

```
python tests/verify_golden.py                    # 80/80, three layers
```

**The two modes are themselves a test.** Rate the same risk both ways; every difference is a risk
ISO would quote and we would refer. That report is a deliverable, not a diagnostic.

---

# Stage 4 — Schemas and payloads ⏸ NOT BUILT

*One sample submission per state, same class code and exposure everywhere.*

```
python -m gl_engine.cli schema NJ 20260811
python -m gl_engine.cli payload NJ --out Engine_Payloads/NJ.json
python tests/verify_payloads.py
```

**How you will check it:** rate all 51 and every difference must name the state deviation
responsible. Four states need an extra field — California, Florida, New York and Texas resolve
territory by county or place. **Hawaii is not in the corpus and must fail loudly.**

The 53 real ISO-rated examples this will be built from are already on disk:

```
dir Payloads
python tests/verify_california.py                # 11/11 -- uses Payloads/CA
python tests/verify_new_york.py                  # 10/10
```

---

# Stage 5 — The enum workbook ⏸ NOT BUILT

*Every field a payload can carry, and its legal values, from ISO's own tables.*

```
python -m gl_engine.cli enums --out GL_Payload_Enums.xlsx
python tests/verify_enums.py
```

**How you will check it:** every value in the 53 real submissions must appear in the workbook. A
value ISO accepted that our workbook rejects is a defect in the workbook.

The underlying domain tables are readable today:

```
python -m gl_engine.cli census 20260811
python -m gl_engine.cli table NJ 20260811 DomainScheduleType --kind Domain --rows 20
```

---

# Stage 6 — The UI ⏸ NOT BUILT

*Paste a payload, rate it, read every factor.*

```
python ui/app.py
```

**How you will check it:** it must need no change to the engine. **If the UI requires the engine to
change, the engine's interface was wrong** — that is the whole point of keeping them in separate
files.

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

## Stages 2 and 3 — the interpreter and the kernel

**Added 2026-08-13. Every command below has been executed and every stated output is what it
actually produced** — the rule this file adopted after an expected output was once written before
the command was run.

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
> `Payloads/OK/1. Input.json` — that is a different submission, it prices to `7852` against ISO's
> `8229`, and it is one of the 28 open differences (`OI-76`). The first draft of this section pointed
> at the wrong file and would have printed a number that looked like a failure.

### The acceptance suites

```
python tests/verify_interp.py
```
```
52/52 passed
```

Four groups: every one of the **54** language nodes has an evaluator (the list is read from the
corpus census, not typed into the test, so a 55th node in a future filing fails here); the semantics
of each node group against its contract clause; a real ISO package executed; and every hard failure
in contract §12 actually firing.

```
python tests/verify_stage3.py
```
```
31/31 passed
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
RECONCILIATION AGAINST ISO'S OWN PRICED EXAMPLES  (50 payloads)

    MATCH   22 of 50
    DIFF    28 of 50
```

**This is the offline half of Phase 2.** Writes `scripts/erc/out/reconciliation.csv` so runs can be
diffed. **Every DIFF is our defect until proven otherwise** — see `OI-76`.

### The other stage-2 measurements

```
python scripts/erc/43_default_block.py        # the entry point, all 567 packages
python scripts/erc/45_nillable_vs_allownull.py # who decides whether a read may be null
```

Both read the whole corpus and take about half a minute each.
