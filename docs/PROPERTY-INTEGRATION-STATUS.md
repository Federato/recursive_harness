# Property (Commercial Fire) Integration — Status & Next Steps

**A brief update, not a proposal.** For the full reasoning behind the plan, see
[`CF-PROPERTY-INTEGRATION-PROPOSAL.md`](CF-PROPERTY-INTEGRATION-PROPOSAL.md). This page is the
short version: where things stand today, and what's next. No insurance or engineering background
assumed.

---

## In one paragraph

We're bringing a second line of business — Commercial Fire / Property ("CF") — into the same tool
that already prices General Liability ("GL"), following the exact pattern GL proved out, with GL
and CF kept fully separate in testing and reporting. **Property is 100% documentation today — there
is no CF engine code anywhere in the repository.** The first piece of required groundwork was
completed 2026-08-20. Nothing beyond that is authorized yet; per this project's standing rule,
engine code isn't written until explicitly approved, item by item.

---

## Where things stand

| Item | What it is | Status |
|---|---|---|
| **1. Finish the groundwork GL already did** | Build an independent data-file reader for CF (`cf-erc-expert`), with no access to the manual-reading side's conclusions, then compare the two and produce a CF build plan | **✅ Complete, 2026-08-20** |
| **2. Reuse the engine's architecture** | A `cf_engine/` package shaped like `gl_engine/` — same interpreter-based approach, not hand-translated logic | Not started — blocked on item 1's next phase |
| **3. One coverage at a time, gated** | CF's five coverage groups built and manual-checked one at a time, the same discipline that caught GL's early mistakes | Not started — blocked on item 2 |
| **4. Separate GL/CF testing and reporting** | CF gets its own results folder, test scripts, notebooks, and ISO call budget — never sharing GL's | Not started — blocked on item 3 |

---

## What "groundwork complete" actually means

GL's build only started after two **independent** analyses — one reading the filed manuals, one
reading the machine-readable data files, each with no access to the other's conclusions — were
compared and found to agree. That cross-check is what caught GL's early mistakes: territories
believed missing that weren't, a `0` in the data that actually meant *"refer to an underwriter."*

CF's manual-reading side (`cf-circular-expert`) already existed — 379 files, though read to a
shallower depth than GL's, and four states (Idaho, Louisiana, Mississippi, Washington) still
unread. Its data-file-reading side (`cf-erc-expert`) was an **empty shell** until this pass — an
agent definition with no knowledge base, no extracted text, no tools.

**As of 2026-08-20, that's fixed:** `Agentic/cf-erc-expert/` has a real, independently-mined
knowledge base and CLI (`knowledge/*.json`, `tools/erc.py`, `tools/smoke_test.py`), built with **no
access to the manual/circular side.** The first comparison between the two sides is
`CF_Algorithm/ERC-VS-CIRCULAR-COMPARISON.md`; the resulting first-pass plan is
`docs/CF-RATING-ENGINE-BUILD-PLAN.md`.

**One caveat carried forward, not smoothed over:** the new knowledge base flags its own coverage as
partial — one recent edition indexed in full, territory sampled rather than surveyed, one coverage
chain traced. That should be extended before its findings are treated as fully settled.

---

## What's next, in order

1. **Extend `cf-erc-expert`'s coverage** — more editions, a real territory survey (not a sample),
   more than one coverage chain traced — before treating item 1's findings as final.
2. **Decide: shared interpreter core, or a separate copy for CF.** ISO's data files for GL and CF
   are likely the same underlying rule mechanics (same publisher), but that's a real design
   question worth deciding once CF's rule files are fully characterized — not assumed either way in
   advance.
3. **Build `cf_engine/`** in the same shape as `gl_engine/` — domain layer, ERC-reading layer, the
   interpreter, edition/version resolution, the rating kernel, schema validation — once item 2 is
   decided.
4. **Build CF coverage by coverage, gated**, the same discipline GL used: a full gate walkthrough,
   checked against the filed manual, before any code is written for that coverage.
5. **Stand up separate GL/CF testing and reporting** — CF needs its own `results/runs/cf/...`
   subtree, its own `verify_*.py` scripts importing `cf_engine`, its own notebook set, its own ISO
   call budget counter (so a CF test run never spends GL's daily allowance), and a decision on
   whether the UI gets a GL/CF switch or two separate entry points.

---

## Decisions flagged, not yet made

- **Shared interpreter core vs. a fully separate `cf_engine/` copy.**
- **One app process with a GL/CF switch, vs. two separate ones.**
- **Whether `cf_engine` code is blocked on item 1's extended groundwork** — which is what GL's own
  build rule would demand, applied consistently to a second line of business.

---

## One housekeeping note, unrelated to the engine work

`CFBranch/` and `CF_Algorithm/` are near-duplicate directories — `CFBranch` looks like a leftover
working session, `CF_Algorithm` the synced, slightly more current copy. Worth tidying eventually;
not blocking anything above.

---

**Document history:** written 2026-08-21 as a brief companion to
[`CF-PROPERTY-INTEGRATION-PROPOSAL.md`](CF-PROPERTY-INTEGRATION-PROPOSAL.md), which holds the full
reasoning. This page is kept short on purpose — update it in place as items move, rather than
letting it grow into a second proposal document.
