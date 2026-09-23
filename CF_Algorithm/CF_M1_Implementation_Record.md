# M-1 implemented — Special Class and SCBI now take the policy factors

**2026-09-22.** Applied to `CFRater1.02.xlsb`. `CFRater1.01.xlsb` never opened.

| | |
|---|---|
| Cells repointed | **240** on `Special Class Worksheet` — 24 rows × 10 item columns |
| Premiums at 1.0 | **unchanged** — 7183 / 8022 / 2699 / 1434 / 406 |
| IRPM 0.9 | SC **1434 → 1292**, SCBI **406 → 365** — previously inert |
| MultiPremium 0.5 | SC **1434 → 718** — proves the row-82 bug is gone |

---

## The premise was wrong, and that is the main lesson

You approved this as *"wire it in"* on my description: that Special Class had **no**
IRPM / PackageMod / MultiPremium cells, so adding them was new rating behaviour that
would change premiums.

**That description was wrong.** The sheet has **24** such rows, spread across all eight
blocks, and the premium formulas already multiply them in:

```
row 22  =ROUND((C15/100)*C16*C17*C18*C19*C20*C21,0)
                              ^^^ ^^^ ^^^
                    PackageMod  MultiPrem  IRPM
```

**Why I got it wrong:** R-4's survey matched the *abbreviated* labels the
Building / Contents / BI sheets use — `IRPM`, `PackageMod`, `MultiPremiumDispersion` —
but this sheet uses ISO's *full* names: `IRPMFactor`, `PackageModFactor`,
`MultiPremiumAndDispersionCreditFactor`. The search returned zero and I reported an
absence.

A clean result that was really an empty search. That is the exact defect shape the
harness kept finding in its own instruments — gate point 6's check blind to delegating
rules, gate point 7's census blind to theft, the state sweep blind to rule overrides.
**Third time in this project the instrument, not the corpus, was the problem.**

**So this was never new rating behaviour.** It was the same disconnected-constant defect
found on the BI sheet, in a third place — rows 17/18/19 held the formula `=1`, and all
eight blocks chained off them.

**Standing lesson:** when a survey reports a factor absent from one sheet but present on
its siblings, suspect the label vocabulary before believing the absence. Read the sheet
and report what is there; do not ask whether a guessed label exists.

---

## A real bug found while fixing it — row 82

```
row 81  PackageModFactor                       =C60   correct
row 82  MultiPremiumAndDispersionCreditFactor  =C60   WRONG — should be =C61
row 83  IRPMFactor                             =C62   correct
```

Row 82 pointed at row 60, which is `PackageModFactor`. **Special Class's Special form
counted the package mod twice and ignored the multi-premium credit entirely.** Invisible
while both sit at 1.0; wrong the moment they differ — and it would have stayed invisible,
because nothing in the workbook tests that a factor reaches the premium it belongs to.

**Fixed by deleting the chain, not repairing the link.** All 24 rows now reference the
named inputs directly. A chain already wrong in one place will be wrong again after the
next copy-paste. Direct reference makes every block independently correct and retires
the whole class of bug — which is what "single source of truth" is actually for.

---

## Verification

Three-sided, because two of the three findings here would have passed a lesser check:

1. **Unchanged at 1.0** — proves nothing was broken.
2. **Moves at IRPM 0.9** — proves the wiring is live. SC and SCBI both moved; before
   this they did not.
3. **MultiPremium 0.5 moves Special Class** — targeted at the row-82 bug specifically.
   Before the fix, the Special block read PackageMod here, so this test would not have
   isolated it.

The script aborts without saving on any failure, including failure to restore to
baseline.

---

## Separate defect found while verifying — NOT fixed

**`'Policy Inputs'!I9` — "Total Premium" — is `=I3+I4+I5`.** Building + Contents +
Business Income. It **omits `I6` Special Class ($1,434) and `I7` SCBI ($406)**, both of
which it displays directly above itself.

| | |
|---|---|
| Total shown | **$17,904** |
| Five coverages actually sum to | **$19,744** |
| Understated by | **$1,840 — about 9.3%** |

Almost certainly because the Special Class rows were added later (BUILD-LOG Entry 33,
2026-09-14) and the total was never extended.

**This is not a judgement call about ISO's rules.** A cell labelled *Total Premium* that
omits two of the five premiums listed above it is wrong on its own terms. The fix is one
character: `=I3+I4+I5+I6+I7`.

**Deliberately not applied.** It changes the headline number you read, and that should be
a deliberate act rather than something that arrives inside an unrelated change. Logged
as backlog **T-1**.

---

## Scripts

| | |
|---|---|
| `scripts/cf/92_m1_survey_specialclass.py` | read-only — reports what is on the sheet rather than testing for guessed labels |
| `scripts/cf/93_m1_apply_specialclass.py` | the 240-cell repoint, three-sided verification |

---

## Next

**One decision:** apply T-1? It is a one-character fix that moves the headline total
from $17,904 to $19,744.

Remaining streamlining items: **R-2** tab naming (~1 hr), **R-3** guard and provenance
columns (~½ day). R-3 keeps earning its case — it would have surfaced the `=1`
constants, the row-82 mis-reference, and arguably T-1, all on sight.
