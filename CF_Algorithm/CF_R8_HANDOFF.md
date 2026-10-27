> **SUPERSEDED 2026-09-22 (end of day):** R-8 is complete. Resume from `CF_Rater_RESUME.md`.

# R-8 handoff — paste the block below to resume

**Written 2026-09-22.** Everything to this point is saved and verified. The next
step is R-8 Phase 2b-ii, the largest and riskiest single piece.

---

```
Continue the CF rater streamlining work on the prototype workbook.

READ FIRST, IN THIS ORDER
  CF_Algorithm/CF_R8_Phase0_Spec.html      the R-8 design and all 7 settled decisions
  CF_Algorithm/CF_R8_Phase1_Record.md      what Phase 1 built, and the 133-stale-names bug
  CF_Algorithm/CF_R8_Contents_Dependency_Census.csv   the 102-row dependency survey
  CF_Algorithm/CF_Rater_Streamline_Wireframes.html    R-1..R-8 overview, R-1..R-7 marked done

HARD RULES — these are not negotiable
  1. NEVER touch C:\Projects\Spreadsheet_Rater\CF\CFRater1.01.xlsb. Not a read, not
     a write, not "just to check". It is frozen permanently. Don't ask.
     The prototype is CFRater1.02.xlsb and that is the ONLY workbook you modify.
  2. Every write script must refuse CFRater1.01.xlsb by filename, in code.
  3. Abort if ANY Excel process is running. If one exists with a non-empty
     MainWindowTitle the user has it open — stop and say so, do not kill it.
     Only reap orphans (empty MainWindowTitle) and only by PID.

COM PROTOCOL (learned the hard way, don't rediscover)
  - win32com DispatchEx, never Dispatch. Dispatch attaches to a running instance.
  - Set app.Calculation = -4135 AFTER opening the workbook, never before; Excel
    raises otherwise. Without it, bulk edits recalc a 5.4MB tree and time out.
  - Quit in a finally block, then reap orphans — Quit often doesn't end the process.
  - Move()'s argument marshalling is unreliable; don't automate sheet reordering.

VERIFICATION DISCIPLINE (every one of these caught a real bug this session)
  - Two-sided: premiums UNCHANGED at neutral values AND MOVING when a factor is
    exercised. "Unchanged" alone passed a completely inert change.
  - Structural edits (renames, defined names, sheet add/delete) must be verified
    AFTER save/close/REOPEN. An in-session check tests memory, not the artefact —
    that is how 133 defined names stayed broken for four sessions.
  - Read premiums THROUGH the defined names OUT_Prem_Building / _Contents / _BI /
    _SCBuilding / _SCBI / _Total, not by cell address.
  - Scripts abort WITHOUT saving on any gate failure.
  - Append rows, never insert — insertion shifts every row number in the docs.
  - Exercise ALL item columns in a test, not just column C. Item 1 is a Legal
    Liability risk and drops several factors, so a working change can look inert.

CURRENT STATE OF CFRater1.02.xlsb
  Premiums: Building 7183 · Contents 8022 · BI 2699 · SC 1434 · SCBI 406
            TOTAL 19744
  Done: R-1 (133 named inputs) · R-2 (sheets renamed IN-/CALC-/TBL-/OUT-) ·
        R-3 (Source+Check columns, 434 rows) · R-4 (policy factors wired) ·
        R-5 (15 per-group exclusion inputs) · R-6 (19 source stamps,
        TBL - Editions, Diagnostics §5) · R-7 (OUT - Diagnostics) ·
        M-1 (Special Class factors) · T-1 (Total Premium)
  R-8: Phase 1 done (IN - Schedule, 7 blocks, populated by formula).
       Phase 2a done (3 CoreScratchpad helpers assigned; CALC - Special Class
       row 26 defect fixed — it read the Location wind/hail input, ISO gates it
       on the SpecialClass record, confirmed at line 3202 of
       CommercialPropertySpecialClassRules.Rule.xml).
       Phase 2b-i done (CALC - Contents Rating roll-ups widened to SUM(C:AP);
       columns M..AP deliberately LEFT EMPTY).

YOUR TASK — R-8 Phase 2b-ii, migrate Contents to the new model
  Design is already decided, do not re-litigate:
    - CoreScratchpad is NOT re-shaped. It stays keyed one column per building.
    - Each contents column carries its parent building's column index, and reads
      building-level values as
        INDEX('CALC - CoreScratchpad'!$C{row}:$L{row}, 1, ParentCol)
    - Contents-level values come from the IN - Schedule CONTENTS block (rows
      134-173; header row 133).
    - Rebuild TOTAL LIMIT (CALC - CoreScratchpad row 138) as
        building's own Limit + SUMIFS over contents records sharing that building
      This is the formula that makes multiple contents types price correctly; it
      is the entire point of R-8.
    - Split CoreScratchpad helpers row 60 and row 205 — both fan out to BOTH
      Building and Contents, so each needs a per-coverage copy. Rows 26/175/182
      are already assigned. This closes R-5.
  Do NOT fill columns M..AP by copying column L — that was tried and drove
  Contents to #VALUE!, because those formulas reference CoreScratchpad!M..AP and
  Bldg Rating!M..AP which do not exist. Populate them with formulas that resolve
  their parent explicitly.

  GATE 1: Contents premium still exactly 8022, all other premiums unchanged.
  GATE 2: add a second contents type (e.g. Stock alongside All Personal Property
          on building 2-1) and confirm it rates and sums. Verify against ISO via
          scripts/raas.py, not against ourselves — the open question is whether
          ISO sums a repeating group the way we do. Harness chunk 4 says yes.

  If GATE 2 fails, STOP. Phases 4-6 do not happen and we have spent two days,
  not six.

AFTER PHASE 2: phases 4 (Building/BI/SpecialClass/SCBI), 5 (retire old inputs),
6 (collapse Payload Export — it exists only to transpose, and IN - Schedule is
already in its shape).

Write an implementation record to CF_Algorithm/ when done, matching the style of
CF_R5_Implementation_Record.md — what changed, what was verified, what was found
and deliberately NOT fixed.
```

---

## Notes for whoever picks this up

**The pattern that has worked all session:** survey read-only first and write the
findings to a CSV, then act from that list rather than searching as you go. Four
separate times the survey overturned the premise of the task — most sharply on M-1,
where a label-vocabulary mismatch made me report a whole sheet as empty when it had
24 matching rows.

**When a check reports something absent, suspect the instrument before the corpus.**
That has been true three times here and repeatedly in the harness build.

**The user makes the calls on anything that changes a premium.** Plumbing and
diagnostics are fair game; new rating behaviour is not.
