# Integrating Commercial Fire / Property — A Proposal

**A plain-language document.** How to bring a second line of business — Commercial Fire ("CF"),
i.e. Property — into this tool, following the same pattern already proven on General Liability
("GL"), with GL and CF testing and reporting kept separate. **This is a proposal only. Nothing
described below has been built.** Per this project's standing rule, engine code is not written
until explicitly authorized, item by item.

No prior knowledge of this project is assumed.

---

## 0. Where things stand today

Two facts decide how much of this is "start building" versus "finish the groundwork":

**CF's documentation is ahead of its engine, and further ahead than GL's own decision point to
start writing engine code required.** `CF_Algorithm/` already holds the same shape of
documentation `GL_Algorithm/` has — five coverage-group rating-algorithm docs (Building, Business
Income, Personal Property, Special Class, Special Class Business Income) and an interactive
rating-chain visualization. **There is no CF engine code anywhere in the repository.** CF is
100% documentation today.

**The cross-check GL relied on before writing any engine code has not happened for CF yet.** GL's
build only began after two *independent* analyses — the filed manuals read by one process, the
machine-readable data files read by a separate process with no access to the first one's
conclusions — were compared and found to agree. That cross-check is what caught GL's early
mistakes: territories believed missing that were not, a `0` in the data files that actually meant
"refer to an underwriter." CF's manual-reading side (`cf-circular-expert`) is real —
379 files, though characterized to a shallower depth than GL's ("L2," not "L3"), and four states
(Idaho, Louisiana, Mississippi, Washington) still unread. CF's data-file-reading side
(`cf-erc-expert`) is **an empty shell** — an agent definition with no knowledge base, no
extracted text, and no tools, unlike its GL counterpart (`iso-erc-expert`), which is fully built
out.

One housekeeping note found along the way: `CFBranch/` and `CF_Algorithm/` are near-duplicate
directories — `CFBranch` appears to be a leftover working session, `CF_Algorithm` the synced,
slightly more current copy. Worth tidying eventually; not part of the engine work and not
blocking it.

---

## 1. Finish the groundwork GL already did before writing code

Build out `cf-erc-expert` the way `iso-erc-expert` already exists for GL: extract CF's
machine-readable data files to a searchable knowledge base, and have it independently analyze
what those files contain — package identity, rule structure, table contents — with **no access
to `cf-circular-expert`'s existing manual-side findings.** Then compare the two.

This is exactly the check that caught GL's "a `0` means refer to underwriter" trap and its
missing-territory scare. Skipping it for CF means building on a foundation that has never been
independently verified. The output of this step is a CF technical build plan — CF's own version
of GL's eighteen non-negotiables, since Property has its own traps (coinsurance, valuation
basis, blanket coverage across locations) that GL's list does not cover.

## 2. Reuse the engine's architecture, not its code

GL's engine is not hand-translated insurance logic — it is an **interpreter** for ISO's own rule
language, because ISO's data files are already a small, executable rule format (58 node types,
54 executable, measured across 809,088 instruction occurrences). That architectural decision is
reusable: a `cf_engine/` package in the same shape as `gl_engine/` — a domain layer, an
ERC-reading layer, the interpreter itself, edition/version resolution, the rating kernel, schema
validation.

Whether the interpreter core can be genuinely **shared** between GL and CF (same publisher,
likely the same underlying rule mechanics) or needs its own copy is a real design question,
worth deciding deliberately once item 1 above shows what CF's rule files actually look like —
not assumed either way in advance.

## 3. One coverage at a time, gated — the same discipline

GL was built coverage by coverage, each one checked against the filed manual before moving to
the next, because surveying everything at once missed real traps. CF's five coverage groups
become the build order the same way GL's seven sublines did, each getting its own gate
walkthrough — a full derivation, checked against the manual — before any code is written for it.

## 4. Separate GL and CF testing and reporting

Nothing in the current test/report harness is separated by line of business — it is all
implicitly GL. Concretely, integrating CF means:

- **Run results.** `results/runs/` and `results/reviews/` have no line-of-business segment in
  their paths today. CF needs its own namespaced subtree (e.g. `results/runs/cf/...`) rather than
  writing into the folder GL already uses, so the two don't collide or get mixed into one index.
- **Test scripts.** GL's roughly twenty `verify_*.py` scripts live at the repo root and import
  `gl_engine` directly. CF needs a parallel set importing `cf_engine`, kept in their own
  directory, so "run all GL tests" and "run all CF tests" stay distinct commands.
- **Live ISO comparison.** The RAAS client, the offline-then-live pattern, and the daily
  call-budget ticker are already written in a line-of-business-agnostic way — these can likely be
  reused as-is, just pointed at CF's own submissions and given their own budget counter, so a CF
  test run never quietly spends GL's daily ISO-call allowance.
- **Notebooks and the UI test pages.** GL's notebooks mirror `gl_engine`'s module structure
  one-to-one; CF would get its own parallel set. The UI harness (`ui/tester.py`, the `/tests`
  page) needs an explicit decision — one app with a GL/CF switch, or two separate entry points —
  rather than silently defaulting to one.

---

## Decisions flagged, not made

- Shared interpreter core versus a fully separate `cf_engine/` copy of it.
- One app process with a GL/CF switch versus two separate ones.
- Whether `cf_engine` code should be blocked on item 1's groundwork finishing first — which is
  what GL's own build rule would demand, applied consistently to a second line of business.

---

## Status

| Item | Status |
|---|---|
| 1. Finish the groundwork (build out `cf-erc-expert`, independent cross-check, CF build plan + non-negotiables) | **Complete** — see below |
| 2. Reuse the engine's architecture (`cf_engine/` package) | Not started — blocked on item 1's next phase (see build plan) |
| 3. One coverage at a time, gated | Not started — blocked on item 2 |
| 4. Separate GL/CF testing and reporting | Not started — blocked on item 3 |

**Proposed and item 1 completed 2026-08-20.** `Agentic/cf-erc-expert/` now has a real,
independently-mined knowledge base and CLI (`knowledge/*.json`, `tools/erc.py`,
`tools/smoke_test.py`), built with no access to the manual/circular side. The first comparison
between the two sides is `CF_Algorithm/ERC-VS-CIRCULAR-COMPARISON.md`; the resulting first-pass
plan is `docs/CF-RATING-ENGINE-BUILD-PLAN.md`. **Nothing beyond item 1 is authorized** — the
knowledge base itself flags that its own coverage is partial (one recent edition indexed in
full, territory sampled not surveyed, one coverage chain traced) and should be extended before
item 1's findings are treated as settled.
