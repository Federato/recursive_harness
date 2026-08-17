# Recursive Harness — General Liability Rating Engine

**Turning ISO's filed General Liability rating content into something a machine can execute**, with
proof at every step that it matches what ISO actually filed — and a harness that checks itself
against ISO's own rating service.

## 📖 Start here

**Everything below renders in GitHub. Read it in the browser — no clone required.**

| | |
|---|---|
| **[docs/EXECUTIVE-SUMMARY.md](docs/EXECUTIVE-SUMMARY.md)** | **Read this one.** What we are building, why it is hard, where we are, the architecture decision *and the honest case against it*, how it gets proved against ISO's own service, the self-correcting harness, and how carrier deviations layer on top |
| **[BUILD-LOG.md](BUILD-LOG.md)** | **The build diary — what was built, what broke, what the fix revealed. Entry 16 is the current handoff** |
| **[docs/qa-plan-proposal_20260817.html](docs/qa-plan-proposal_20260817.html)** | **The QA programme, proposed 2026-08-17.** Full 51-jurisdiction coverage sized from ISO's own declared content — two matrices not one, wireframes for terminal and button, the ISO call budget, and what can and cannot be proven. **Nothing in it is built** |
| **[docs/HOW-TO-USE-THE-TESTER.md](docs/HOW-TO-USE-THE-TESTER.md)** | **How to run the tests and read the results**, for someone who does not code. Rendered as [`how-to-use-the-tester.html`](docs/how-to-use-the-tester.html) |
| **[docs/START-HERE-TOMORROW.md](docs/START-HERE-TOMORROW.md)** | **Read this first if you are picking the project up.** What to do next, what is waiting on a person, the backlog as it stands, and how far off a product UI is. Rendered as [`start-here-tomorrow_20260818.html`](docs/start-here-tomorrow_20260818.html) |
| **[docs/WHAT-THE-HARNESS-TAUGHT-US.md](docs/WHAT-THE-HARNESS-TAUGHT-US.md)** | **Seven defects in one day, in plain English** — what each taught and the pattern underneath. Rendered as [`what-the-harness-taught-us_20260817.html`](docs/what-the-harness-taught-us_20260817.html) |
| **[docs/WHATS-LEFT-PLAIN-ENGLISH.md](docs/WHATS-LEFT-PLAIN-ENGLISH.md)** | What is left, for people who do not read code. Rendered as [`backlog_20260817.html`](docs/backlog_20260817.html) |
| [docs/WHAT-I-NEED-FROM-YOU.md](docs/WHAT-I-NEED-FROM-YOU.md) | The asks: what only a person can supply, what each unblocks, and the default if it is never answered. **Section A all decided 2026-08-17** |
| [docs/THE-HARNESS-FOUND-THESE.md](docs/THE-HARNESS-FOUND-THESE.md) | The 17 August session — five defects closed and how each was found. Not one by reading code |
| [docs/BACKLOG-FEATURE-SETS.md](docs/BACKLOG-FEATURE-SETS.md) | The backlog grouped into seven feature sets — what you are choosing between, rather than what is next |
| [docs/BACKLOG-2026-08-14.md](docs/BACKLOG-2026-08-14.md) | What to do next, ordered. **Opens with the three known defects** — D1/D2 high, D3 medium — then the numbered work, each item naming the open item it closes |
| [docs/BUILD-STAGES.md](docs/BUILD-STAGES.md) | The six build stages and the phases that follow them |
| [TESTING.md](TESTING.md) | **Every command, stage by stage.** Each one has been run and its stated output verified |
| [docs/OPEN-ITEMS.md](docs/OPEN-ITEMS.md) | **OI-1 to OI-94.** Resolved items are kept and marked, not deleted |
| [docs/WHERE-WE-PAUSED-2026-08-12.md](docs/WHERE-WE-PAUSED-2026-08-12.md) | The 12 August session, read cold. **Superseded** — everything after it is in the build log |
| [docs/PRD-GL-RATING-ENGINE.md](docs/PRD-GL-RATING-ENGINE.md) | Full status and history. §0 is the latest update |
| [docs/GL-RATING-ENGINE-BUILD-PLAN.md](docs/GL-RATING-ENGINE-BUILD-PLAN.md) | The technical plan — architecture, the 18 non-negotiables, deviation constraints C1–C3 |
| [docs/FROM-PLANNING-TO-BUILD.md](docs/FROM-PLANNING-TO-BUILD.md) | Did the analysis pay off? Written *before* each stage, so it is allowed to be wrong |
| [PROCESS_LOG.md](PROCESS_LOG.md) | The full analysis record, 51 steps. Closed — the build is logged in `BUILD-LOG.md` |

### The formatted HTML versions

There are nicer, self-contained HTML versions of the main documents. **GitHub displays HTML as
source rather than rendering it**, and GitHub Pages is not enabled on this repository, so these have
to be **downloaded and opened in a browser**:

| File | |
|---|---|
| `docs/THE-BUILD-END-TO-END.html` | The executive summary and the whole build, with contents sidebar. Same content as `EXECUTIVE-SUMMARY.md` |
| `docs/THE-PLAN-IN-PLAIN-ENGLISH.html` | Why this is hard and what changed the design |
| `docs/GL-RATING-ENGINE-DOCS.html` | Every technical and gate document in one page, 24 tabs |
| `docs/qa-plan-proposal_20260817.html` | The QA programme proposal, self-contained, with six wireframes |
| `docs/backlog_20260817.html` | The plain-English backlog, rendered by `scripts/build_backlog_html.py` |
| `docs/index.html` | A landing page linking all of the above |

**Quickest way to read them:** clone the repository and open the file, or use the "Download raw
file" button on the GitHub file page and open the download.

```bash
git clone https://github.com/Federato/recursive_harness.git
cd recursive_harness
start docs/index.html          # Windows
open  docs/index.html          # macOS
```

---

## ⚠️ ISO's licensed content is not in this repository

The manuals, the machine-readable rating packages, the text extracted from them, and ISO's rated
example policies are **all excluded** — see [`.gitignore`](.gitignore), which explains each exclusion.

The engine reads the ERC corpus from **outside** the repository, at a path set by the `GL_ERC_ROOT`
environment variable:

```bash
export GL_ERC_ROOT="/path/to/ISO_ERC_Files/General_Liability"
python -m gl_engine.cli check 20260811 --deep
```

**Without a licensed copy of that corpus the code will not run.** The documents, the method and the
reasoning are what this repository is for.

**This repository is private, and the documents in it quote specific ISO loss costs and factors —
that is what makes them evidence rather than assertion. It must stay private.** One file,
`tests/fixtures/golden-ok-2025.json`, is a real ISO-rated policy; if this ever needs to be made
public, that file and 33 of the 65 documents would have to be scrubbed *and purged from history*.

---

## Status

**As of 2026-08-14.**

| | |
|---|---|
| Analysis | Complete — 14 coverage walkthroughs, 18 non-negotiables, 13 decisions taken |
| **Stage 1 — which rulebook applies** | ✅ Built |
| **Stage 2 — the interpreter** | ✅ Built. 54 language nodes, ISO's rules executed rather than re-implemented |
| **Stage 3 — premium and referrals** | ✅ Built. Two modes, one code path |
| **Stage 4 — state input formats** | ✅ Built. 51 sample submissions, the same risk in every state |
| **Stage 5 — the field catalogue** | ✅ Built. Every field and its legal values, from ISO's own tables |
| **Stage 6 — the interface** | ✅ Built. Paste a submission, read every factor and its source |
| **Phase 2 — proof against ISO's live service** | ✅ Live. **50 of 50 agree, on every field ISO publishes** |
| Then | Phase 3 — the self-correcting harness → Phase 4 — company deviations |
| **The variable tester** | ✅ Built. Dropdowns from ISO's declared domains, every jurisdiction in one run, and the coverage view that says how narrow the claim still is |
| Tests | **Fourteen suites, all green** — see [`TESTING.md`](TESTING.md) |

**The honest caveat, stated where the good number is.** All 51 submissions are **the same risk** —
one location, one classification, class `50017`, gross sales, no deductible, no rating plans. That
was chosen so differences between states would be attributable, and it worked, but **fifty matches
on one risk shape is a narrower claim than it sounds.** Widening it is the next work (OI-87), and it
is expected to find defects.

**Breadth began 2026-08-14, and it did find one.** `scripts/breadth.py` varies the *submission*
instead of the state — 17 variants over 7 groups, every value taken from ISO's own declared domains
and refused at build time if it is not in one. Run live: **OK 16 of 16, NY 15 of 15** agree with ISO
on the premium and every published field, now including deductibles, two locations, two
classifications, a non-Gross-Sales basis, both directions of the ILF table, claims-made, schedule
rating and terrorism on. It raised **OI-88** — a real engine defect, the first found by an external
oracle: size-of-risk refuses in OK where **ISO rates it at 8816** — plus **OI-89**, a filed gate
tying schedule rating to experience credibility, and **OI-90**, closed the same day.

**And breadth now has a front door.** `python app.py` then
**[/tester](http://127.0.0.1:8765/tester)**: **19 controls in 8 groups** — deductibles, limits,
classification, exposure, coverage form, subline, locations, the rating plans, terrorism — every
option read from ISO's declared domain **for that jurisdiction**, run across all 51 with **our
premium, ISO's premium and the difference** as the three columns that matter. The comparison is on
by default and states its cost first; engine-only is ~90 seconds and free for iterating. Results append to
a permanent store behind four views: **coverage** (which controls have ever been exercised where),
agreement over time, premium response curves, and a defect log with first-seen and last-seen.
**The coverage view starts nearly empty, which is the point of having it.**

**Puerto Rico is excluded from the comparison** — not on the ISO subscription and that entitlement is
not available to us (OI-86). It still rates; it is simply the one jurisdiction with **no external
check of any kind**. Every count of live agreement here is out of 50.

---

## Running the app

A viewer for the engine's output — paste a submission, read the premium and every factor behind it.
**Python 3 is the only requirement**; the app uses the standard library, so there is nothing to
install.

**Windows**

```
start.bat
```

**macOS**

```
./start.command
```

Or double-click either file. The app serves on <http://127.0.0.1:8765> and opens a browser
automatically. `Ctrl-C` in the terminal stops it.

| | |
|---|---|
| `start.bat 9000` / `./start.command 9000` | serve on a different port |
| `start.bat --no-browser` | serve without opening a browser |

**It needs ISO's ERC files, which are not in this repository.** The engine reads them from
`C:\Projects\ISO_ERC_Files\General_Liability`; point `GL_ERC_ROOT` at your own copy to change that:

```
set GL_ERC_ROOT=D:\path\to\General_Liability      &:: Windows
export GL_ERC_ROOT=/path/to/General_Liability     #   macOS
```

Sample submissions to paste are in `Engine_Payloads/<STATE>/submission.json`. The first rating in a
process takes about two seconds while ISO's content loads, and about one second thereafter.

---

## Start here

| If you are… | Read |
|---|---|
| **Reading it cold, in one sitting** | [`docs/THE-PLAN-IN-PLAIN-ENGLISH.html`](docs/THE-PLAN-IN-PLAIN-ENGLISH.html) — the whole plan on one page, plain English, ~2,500 words. Open it in a browser. **Start here** |
| **New to the project** | [`docs/PRD-GL-RATING-ENGINE.md`](docs/PRD-GL-RATING-ENGINE.md) — what we're building, every step taken to get here, requirements and risks. Plain language, no insurance or technical background assumed |
| **Tracking what's unresolved** | [`docs/OPEN-ITEMS.md`](docs/OPEN-ITEMS.md) — OI-1 to OI-92, source-tagged and reconciled against the escalation register |
| **Wanting the earlier overview** | [`docs/BUILD-PLAN-PLAIN-ENGLISH.md`](docs/BUILD-PLAN-PLAIN-ENGLISH.md) — plain-English build plan written before the ERC work; PDF-only scope |
| **About to build the engine** | [`docs/BUILD-STAGES.md`](docs/BUILD-STAGES.md) — the staged build plan, **all six now built** · [`docs/GL-RATING-ENGINE-BUILD-PLAN.md`](docs/GL-RATING-ENGINE-BUILD-PLAN.md) — architecture, doctrine, the 18 non-negotiables |
| **The engine** | [`gl_engine/`](gl_engine/) — all six stages. `python -m gl_engine.cli check 20260811 --deep` for the load-time checks; `python app.py 8776` to rate something and read every factor |
| **Rating something now** | `python app.py 8776`, then open `http://127.0.0.1:8776`. Pick a state, tick **Compare with ISO**, press Rate |
| **Briefing a sponsor** | **[`docs/THE-BUILD-END-TO-END.html`](docs/THE-BUILD-END-TO-END.html) — executive summary + the whole build in plain English: engine, RAaS proof, self-correcting harness, company deviations** · [`docs/EXECUTIVE-SUMMARY.md`](docs/EXECUTIVE-SUMMARY.md) — the same, as markdown |
| **Catching up in plain English** | [`BUILD-LOG.md`](BUILD-LOG.md) **Entry 13** — the current handoff · [`docs/WHERE-WE-PAUSED-2026-08-12.md`](docs/WHERE-WE-PAUSED-2026-08-12.md) — the whole of 12 August, readable cold, now superseded |
| **Running the tests** | [`TESTING.md`](TESTING.md) — **every command, phase by phase**, each one run and its output verified |
| **Following the build** | [`BUILD-LOG.md`](BUILD-LOG.md) — the build diary · [`docs/FROM-PLANNING-TO-BUILD.md`](docs/FROM-PLANNING-TO-BUILD.md) — what each stage expected to inherit from the analysis, written **before** the stage |
| **Building a subline** | [`docs/gates/`](docs/gates/) — the per-item gates, all filed before the build began |
| **Checking a spec claim is current** | [`docs/gates/RECONCILIATION.md`](docs/gates/RECONCILIATION.md) — what the gates superseded in the two specifications, and why |
| **Checking a *count* is current** | [`docs/gates/OI-40-ASOF-RECOUNT.md`](docs/gates/OI-40-ASOF-RECOUNT.md) — every load-bearing figure re-measured as of today, 2027-04-01 and the end state. Two survived, three needed their tense fixed |
| **Planning the build** | [`docs/PHASE-SIZING.md`](docs/PHASE-SIZING.md) — what each build-order item actually contains, measured. **Three countrywide calculators, not two** |
| **Running the golden case** | `python tests/verify_golden.py` — 80 checks against a real ISO-rated policy, no engine required |
| **Seeing every referral condition** | `scripts/erc/out/referral_register.json` — **28 entries and 13 decisions**, built by `40_referral_census.py` and `41_referral_register.py`. 16 declared · 4 missing-data · 4 guard-enforced · 4 decided not to be referrals |
| **Checking the California path** | `python tests/verify_california.py` — 11 checks on the sole `GL_CW_20231201_V02` jurisdiction, which the golden case cannot reach |
| **Checking the New York path** | `python tests/verify_new_york.py` — 10 checks on the most-deviating jurisdiction: 698 overrides, claims-made withdrawn, 83 endorsements de-rated |
| **Checking Limited Product Withdrawal** | `python tests/verify_oi50.py` — 7 checks on the one rating chain with no state deviation |
| **Comparing the two sources** | [`docs/COMPARISON-ERC-VS-PDF.md`](docs/COMPARISON-ERC-VS-PDF.md) — two independent derivations adjudicated |
| **Reading the manual spec** | [`docs/rating-engine/README.md`](docs/rating-engine/README.md) — 14 documents + 4 appendices, PDF-derived |
| **Reading the ERC spec** | [`docs/erc/`](docs/erc/) — 6 documents, derived in isolation from the ERC packages |
| **Checking a premium against the manual** | [`Agentic/iso-circular-expert/`](Agentic/iso-circular-expert/) — a working expert agent with a query tool |
| **Resuming work** | [`BUILD-LOG.md`](BUILD-LOG.md) **Entry 15** — 2026-08-14. All six stages built; Phase 2 live, 50 of 50 against ISO's own service; **breadth run in OK and NY, 31 of 31, and it found OI-88; the variable tester is live at `/tester`.** Next is the decision on **OI-88's null-in-`FirstNonNull` semantics** — the tester reproduces it in one click — then filling the coverage grid. *(`PROCESS_LOG.md` Step 51 closes the analysis phase; everything after it is in the build log)* |
| **Wondering how a number was derived** | [`PROCESS_LOG.md`](PROCESS_LOG.md) — every step, its reasoning, its findings, and its corrections |
| **Re-deriving the analysis** | [`scripts/README.md`](scripts/README.md) — the pipeline, in order |

---

## What's here

```
Commercial Line Manuals/GL/     the source corpora — 4.1 GB, not derived from anything
  Rules/          503 PDFs      how to rate: rules, state exceptions, ILF tables,
                                classification, territory definitions
  LossCosts/      472 PDFs      what to rate with: loss costs by class/territory,
                                the ELP Supplement
  Terrorism/        3 PDFs      the Terrorism Supplement — TEV/PEV versions by state
  Schedule & Experience Rating/
                   52 PDFs      the CGLES plan: eligibility, experience mod, Rule 9/16 tables
  Composite Rating/
                   90 PDFs      the Composite Rating Plan — 51 of them filed as INTERLINE (IL-)

C:\Projects\ISO_ERC_Files\General_Liability\   the ERC corpus — 567 packages, 87k files
                                (separate root; 51 jurisdictions + countrywide)

docs/
  PRD-GL-RATING-ENGINE.md         plain-language PRD: the journey, requirements, risks
  GL-RATING-ENGINE-BUILD-PLAN.md  the Python build plan
  COMPARISON-ERC-VS-PDF.md        the two derivations, adjudicated
  OPEN-ITEMS.md                   65 items, source-tagged
  BUILD-PLAN-PLAIN-ENGLISH.md     plain-English overview, PDF-only scope
  rating-engine/                  PDF-derived specification (14 docs + 4 appendices)
  erc/                            ERC-derived specification (6 docs, clean-room)
  PHASE-SIZING.md                 what each build-order item contains, measured as-of
  gates/                          per-item gates — eleven passed; three to go
                                  + California and New York differentials
    RECONCILIATION.md             what the gates superseded in the specs, and why
    OI-40-ASOF-RECOUNT.md         every load-bearing count, re-measured as of a date

Agentic/iso-circular-expert/    manual authority — 32 invariants, 19 smoke checks,
                                five corpora: rules, loss costs, terrorism,
                                schedule & experience, composite rating
Agentic/iso-erc-expert/         ERC authority — 26 invariants, 83 smoke checks

gl_engine/                      the engine — resolve, interpret, rate
  interp/                       the interpreter: 54 language nodes, ISO's path dialect
  rating/                       the kernel, two modes, the referral register
  schema/                       input schemas and legal values, from ISO's own tables
app.py                          the interface — http.server, no framework
scripts/                        the PDF pipeline, the RAaS client, the comparison
scripts/erc/                    51 scripts — the ERC pipeline
tests/                          12 suites, all green. Stage 1 (20), golden case (80),
                                California (11), New York (10), OI-50 (7), the
                                contract figures, the interpreter (58), stages 3-6
                                (38/28/18/30) and Phase 2 (11)

PROCESS_LOG.md                  chronological record of every step, with its corrections
GL_ERC_Edition_Hierarchy.xlsx   ERC edition hierarchy and circular index
GL_ERC_to_Manual.xlsx           ERC version → rules manual crosswalk
GL_LossCost_to_ERC.xlsx         loss cost notice → ERC edition crosswalk
```

---

## The corpora

| | Rules | Loss Costs |
|---|---|---|
| PDFs | 503 | 472 |
| Readable | 502 | 471 |
| Jurisdictions | 51 — 50 states less Hawaii, plus DC and PR | 51 |
| Years | 2021–2027 | 2020–2027 |
| Countrywide notices | 5 files → 4 distinct editions | **0** — the rate layer is entirely state-level |

Two files are truncated and unreadable (`GL-MO-2027-RU-003`, `GL-MI-2027-LC-003`); both have a
usable prior notice and should be re-downloaded.

---

## The findings that shape the build

Measured across the corpora, each of which would have produced a broken engine if assumed
otherwise. The first four come from the manuals; the rest from ERC, the comparison, and the
per-subline gates:

**1. The countrywide layer holds the method and almost none of the numbers.** Rule 56.B says
outright: *"The increased limits tables are displayed in the state exceptions."* There is no
national ILF table and no national loss cost publication at all. The engine **composes** three
sources; it does not inherit from one.

**2. Printed rule numbers are labels, not identities.** CW 2027 renumbers 21 of ~50 rules and
*reuses* numbers — Rule 22 means "Description Of CGL Coverage" before 2027 and "Mandatory
Endorsements" after. Resolving a state exception by printed number will one day attach it to
the wrong rule, silently.

**3. More than a third of rate cells are not numbers.** Of 429,748 cells in the current
notices: 64.3% numeric, 18.6% `–` (coverage not offered — decline it), 17.1% `(a)` (refer to
company). Reading either non-numeric token as `0.00` produces free policies and sells coverage
the manual declines.

**4. The 2027 rate change is a cliff, not a migration in progress.** Measured **as of a date**,
which is the only method the corpus permits: **today all 51 jurisdictions are on the pre-2027 class
basis and all 51 publish OCP loss costs.** On **2027-04-01**, forty-three of them change class basis
*on the same day* and lose the OCP loss-cost table with it — one dated program change, retiring 238
Premises/Operations class codes and introducing 204. **Today the class list is a single list of
1,197 codes and there is no split to reconcile**; from 2027-04-01 it is 1,401 codes across two
bases, 959 shared. So a single national class list is **right today and wrong from 2027-04-01**, and
an engine that resolves editions as-of the effective date gets this for free while one that caches
"the current class list" fails catastrophically on one day.

> Earlier drafts recorded *"15 jurisdictions on the pre-2027 basis, 36 moved"* as a present-tense
> fact, and a later ERC pass replaced it with 8/43. **Both were end-state figures** — each taken over
> the latest filing per jurisdiction, in a corpus holding 82 filings effective after today. The
> mechanism the original PDF derivation found — *"the withdrawal is sharply dated"* — was right all
> along; only the framing as a jurisdiction split was wrong. Re-measured 2026-08-11 with
> `scripts/erc/31_migration_asof.py`; full account in
> [`docs/gates/RECONCILIATION.md`](docs/gates/RECONCILIATION.md) §1. **Every other count taken the
> same way has since been re-tested as-of a date** —
> [`docs/gates/OI-40-ASOF-RECOUNT.md`](docs/gates/OI-40-ASOF-RECOUNT.md).

**5. 96.2% of the ERC content does not rate.** Of **477** coverage groups that write a `Premium`,
**383 capture** a user-entered `ManualPremium`, **76 aggregate**, and only **18 compute a premium
from rates** (verified corpus-wide over all 572 package directories). That is the honest ceiling of
an automated GL rater on this content.

> The 477/383/76 is a **union over every edition ever filed** — the right question for *what must
> the engine ever rate*. In force **today** it is 458 groups, 18/356/84. **The rate-driven set is
> identical at every date tested**, verified as a set rather than as a count, and is the one
> headline figure the as-of defect did not touch
> ([`docs/gates/OI-40-ASOF-RECOUNT.md`](docs/gates/OI-40-ASOF-RECOUNT.md) §5).
>
> **It was, however, two short — and for an unrelated reason.** Counted `16` until 2026-08-11,
> when listing the remaining gates exposed that the classifier's rate-source list omitted
> `AdjustedRate`, filing both Unmanned Aircraft coverages as aggregators. Corrected to **18**;
> exactly two groups move.

**5b. The Terrorism Supplement was on disk for the whole project and the expert agent could not
see it.** The agent's corpus was `Rules` (503) and `LossCosts` (472); the supplement — 3 notices,
113–118 pages — was never ingested, so every terrorism question it was asked was answered from a
corpus without the terrorism rules. Now fixed, and with it **OI-37 closes**: the population audit
found **20 of 477** coverage groups, four of which compute `Premium` from **other groups' finished
premiums** — a rate source the classifier does not list, which is why terrorism never appeared in
the rate-driven headline. Manual against ERC is exact: **4 of 4** factors and **142 of 142**
above-average classes. ***"Terrorism premium cannot be computed" is retired***
([`docs/gates/GATE-TERRORISM.md`](docs/gates/GATE-TERRORISM.md)).

**5d. Referral conditions were scattered across eleven gates and are now one register.** Scanning
the corpus for them rather than re-reading the gates **amended four filed gates on the first run** —
including one filed the same morning: **15 of 51 jurisdictions file their own terrorism factors**,
keyed on territory, spanning `0.004`–`0.133` against the countrywide pair's `0.009`/`0.004`, with
New York filing a **Manhattan-specific** table. The register holds **28 conditions in four kinds**,
and the split that matters is **9 detectable before rating · 6 during · 11 not at all**. The last
eleven are not a gap in the scan — ERC carries no discriminator for them, so each is a decision
rather than code (`scripts/erc/out/referral_register.json`).

**5c. The three rating plans were recorded as missing from the manual corpus, and were on disk the
whole time.** 52 Schedule & Experience documents and 90 Composite Rating documents — 654 pages —
outside the expert agent, which had been built over two of the five corpora. **Composite Rating
moved to the *Interline* manual in 2017**, so 51 of its 90 filings begin `IL-` and a `GL-*` sweep
finds 39. Now ingested and aligned: **schedule rating 8 of 8 characteristics on range and row
count; experience rating 97 of 97 bands, 291 cells, 0 mismatches; composite rating 3 rules and
executable.** PDF gap **G6 retired** — all four of its claims are false
([`docs/gates/GATE-RATING-PLANS.md`](docs/gates/GATE-RATING-PLANS.md)).

**5a. One rating mode has no manual text at all — measured, not assumed.** Size-of-risk rating
(build-order item 8) is described in **0 of 1,030** ISO manual documents. It is the first apparatus
in the project ERC must be trusted on alone, so every sentinel it carries is an escalation rather
than a confirmation. **The claim is bounded honestly: 187 of those 1,030 are image-only and cannot
be searched here**, so absence is established over 82% of the corpus, not over the corpus (OI-51).
It also brings a capability nothing else needs — **linear interpolation across an exposure band,
declared by 16 of 4,551 rate table definitions corpus-wide, all 16 of them size-of-risk**
([`docs/gates/GATE-SIZE-OF-RISK.md`](docs/gates/GATE-SIZE-OF-RISK.md)).

**6a. A `0` has four different meanings, and two now have a discriminator.** A genuine factor; an
unpublished factor guarded only by a validation rule; an unguarded refer-to-company; and a
*published* `0` that switches the rating path to the expected-loss-potential table. That last one
is declared by a sibling column — `PremOpsELPText` and friends, a closed 4-value vocabulary that
agrees with the rules **620,856 times out of 620,856**. Read as a rate instead, it writes a free
products liability policy on a class ISO prices at $6,845
([`docs/gates/GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md`](docs/gates/GATE-336-PRODUCTS-COMPLETED-OPERATIONS.md)).

**6. ERC encodes refer-to-company as `0`.** The drone loss-cost table's ">55 lb" band is `0`
where the manual says *Refer To Company*. A naive multiply yields a **$0 premium** on exactly
the risks that must be referred — found only by comparing the two sources.

**7. The corpus is 100% self-describing.** The XSD `targetNamespace` yields each package's
jurisdiction, edition and version for 567/567 — closing the PDF build's largest defect, where
264 notices were dated by positional guesswork.

**10. The two sources agree on eighteen numbers, to the cent.** Alaska's Railroad Protective
expected-loss table in the ERC packages — 2026 edition — matches Procedure 5.E of the filed Alaska
ELP Supplement — a 2020 PDF — in **all 18 cells**, across three class codes and six train-per-day
bands. So do the work-trains rate (**$56.80**), the supervisors extension (**10%**) and the
construction-owner derivation (**150% of class 16292**). Every earlier cross-source confirmation was
structural; this is the first of rate *values*, and it tests the extraction rather than the reading
([`docs/gates/GATE-335-RAILROAD-PROTECTIVE.md`](docs/gates/GATE-335-RAILROAD-PROTECTIVE.md)).

**9. A sentinel is data, not a constant.** The liquor refer marker is spelled `Refer To Co.` in every
countrywide edition before 2027 and `Refer to Company` in the 2027 one — and **on 2027-04-01 both are
live in the corpus at once**, the old spelling in the eight jurisdictions that have not migrated and
the new one in the forty-three that have. ISO's own 2027 edition shows the failure mode: one rule was
renamed and another was not, so **2027 liquor exposure is reported to the bureau 1,000× too large**
while the premium stays correct
([`docs/gates/GATE-332-LIQUOR-LIABILITY.md`](docs/gates/GATE-332-LIQUOR-LIABILITY.md)).

**8. The rating algorithm is edition-scoped, not just the rate tables.** Countrywide editions
through 2023 charge medical payments as a separate item; the 2027 edition folds it into the
increased-limits factor. The two are algebraically identical and **round differently — the same risk
prices at 976 under one and 975 under the other.** Ten distinct countrywide parents are in live use
across the 562 state packages, so an engine that swaps only tables per edition will be wrong for
some of them. Found by resolving the golden case's *declared* parent instead of reading the newest
package ([`docs/gates/GATE-334-PREMISES-OPERATIONS.md`](docs/gates/GATE-334-PREMISES-OPERATIONS.md)).

Full evidence in [`docs/rating-engine/`](docs/rating-engine/) and [`docs/erc/`](docs/erc/);
adjudication in [`docs/COMPARISON-ERC-VS-PDF.md`](docs/COMPARISON-ERC-VS-PDF.md); the first
subline's derivation in [`docs/gates/`](docs/gates/).

---

## The agent

A self-contained expert that answers manual questions **from the filed documents**, with a
citation on every claim, and checks engine output against 32 verified invariants.

```bash
cd Agentic/iso-circular-expert/tools

python iso.py territory NJ --zip 07030    # HOBOKEN → territory 504, cited to notice + page
python iso.py rate TX --class 10010       # loss cost per territory, flagged pre-LCM
python iso.py rule 56 --st MU             # countrywide rule text
python iso.py effective NJ --date 2026-06-01
python iso.py invariant --severity BLOCKER
python smoke_test.py                      # 15 cases
```

Registered as a Claude Code subagent, so it can also be invoked directly in conversation.
Python 3, no third-party dependencies at query time.

---

## What is not here

Four inputs were recorded as separate publications genuinely absent from both corpora. **Three of
the four dissolved on inspection, and the strikethroughs are kept because the pattern is the point:
each was a confident negative that nobody had checked.**

| Recorded as missing | What it turned out to be |
|---|---|
| **Company loss cost multiplier** | **Still a real external input** — carrier input by design. Every stored value is a pre-LCM ISO loss cost, and the engine refers rather than guesses |
| ~~Terrorism Supplement~~ | **On disk the whole time.** 3 notices, 113–118 pages, simply never ingested into the expert agent. Manual against ERC is exact: 4 of 4 factors, 142 of 142 above-average classes. *"Terrorism premium cannot be computed"* is retired |
| ~~Experience / schedule / composite rating plans~~ | **Also on disk** — 142 documents, 654 pages. Composite Rating moved to the **Interline** manual in 2017, so 51 of its 90 filings begin `IL-` and a `GL-*` sweep finds 39. Now aligned: schedule 8 of 8, experience 97 of 97 bands and 291 cells, composite executable |
| ~~Workers Compensation loss costs~~ | **Not a publication at all.** The 75% is a countrywide ERC cell (`PrincipalsProtvLiabFactor = 0.75`) and the WC rate is a **declared submission field** real ISO submissions supply — retired entirely by the 2027 program |

**Three of four, and each found the same way: by searching the file system rather than trusting the
record.** That is why rule #1 of this project is *before deriving anything from examples, enumerate
the directories and ask what each one is for.*

**Hawaii** appears in neither corpus. Whether that is a download gap or a filing fact is
unresolved.

**Rate cell data is specified but not loaded.** Reading the ~429,700 cells correctly is
documented and proven; doing it at scale is the largest remaining task
(`docs/rating-engine/10-BUILD-BACKLOG.md`, Phase 3A).

---

## Working notes

**Extraction is not interchangeable.** On the loss cost and ELP grids, `pdftotext -layout`
**silently misaligns rows** — values detach from their class code and reattach to the neighbour,
and every resulting number is a plausible loss cost. `pypdf` reads them correctly. This is fixed
in the tooling rather than left to whoever writes an importer, and every load is reconciled
arithmetically (territories × classes × 2 = cell count).

**`pypdf` injects spaces inside words** (`SUB LINE`, `CG -LC -89`, `LI -GL -2019 -216`), so
every caption and reference match must be whitespace-normalised. This has caused two false
negatives in this project; in this domain a false negative reads as *"the manual is silent"*.

**This is a git repository as of 2026-08-12**, and the `scripts/` intermediates (~200 MB of
extracted text) are excluded because they are regenerable — along with everything ISO licenses.
[`.gitignore`](.gitignore) explains each exclusion. **Commits name their paths explicitly rather
than `git add -A`**, because one careless stage would publish licensed content into history where
deleting it later does not remove it.

**One reproducibility gap is known and recorded.** `A3-ENDORSEMENT-CATALOG.md` was produced by
scripts from an early session that were never persisted; the catalog is intact and sourced but
cannot currently be regenerated. See `PROCESS_LOG.md` Step 11.

---

## How the work proceeded

`PROCESS_LOG.md` records every step in order, including the reasoning behind each and — where
it happened — what was got wrong and how it was corrected. Two corrections are load-bearing:

- **Step 8** — the Territory Definitions were reported absent from both corpora after only one
  was searched. They were in the Rules manual all along, on the `CG-T` pages, 51/51
  jurisdictions. The gap register now carries a standing rule: a negative result is scoped to
  the search that produced it.
- **Step 11** — the analysis was found to be non-reproducible, with the scripts living outside
  the repository and a README claiming otherwise. Now fixed in `scripts/`.

Both are the same defect: a confident statement nobody checked. The specification's validation
strategy leans on automated gates rather than review for exactly that reason — **the dangerous
failures in this domain are silent**, producing a plausible number rather than an error.
