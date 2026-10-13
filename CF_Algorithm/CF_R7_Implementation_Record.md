# R-7 implemented — one page that says whether the quote can be trusted

**2026-09-22.** New sheet **`OUT - Diagnostics`** at position 4, immediately after the
three `IN -` tabs. `CFRater1.01.xlsb` never opened. Premiums unchanged.

---

## Four sections, and the split between them is the point

### 1. Factor checks — live roll-up of R-3

| Sheet | Zero flags | Hard-coded | Status |
|---|---|---|---|
| CALC - Bldg Rating | 0 | 0 | ok |
| CALC - Contents Rating | 1 | 2 | 3 to review |
| CALC - BI Rating | 0 | 0 | ok |
| CALC - Special Class | 0 | 0 | ok |
| **TOTAL** | **1** | **2** | 3 flag(s) |

`=COUNTIF('CALC - Bldg Rating'!N:N,"ZERO*")` and the same against the Source column.
Nobody has to scroll four sheets to learn there is nothing wrong.

### 2. Input traps — live checks for known ways to get a confident wrong answer

Each one is a **documented defect**, not a hypothetical:

| # | Check | Now |
|---|---|---|
| 1 | Construction code resolves for every active item | ok |
| 2 | Every active item with a limit has a class code | ok |
| 3 | Legal Liability items carry an additional-insurable-interest option | ok |
| 4 | Blanket not elected (blanket rating is unbuilt) | ok |
| 5 | Total premium equals the sum of its parts | ok |
| 6 | Policy factors | ok — all neutral (1.00) |

Check 3 is backlog **Z-1**: a blank option drives the factor to `0.0` and the premium
to zero. `Option4 = None = 1.00`, so blank is *not* the same as None — the input is
mandatory once Legal Liability is selected, and nothing previously said so.

Check 5 was **failing until today**. T-1 — the total omitted both Special Class lines,
$1,840 short. It is now a standing assertion rather than something someone had to
notice.

### 3. Adjudicated — flags already investigated

The section that stops the same three flags being re-investigated every time anyone
opens the workbook. Same discipline as `Circular_Review_Tracking.md`: **record the
verdict, not just the finding.**

| Where | Flag | Verdict |
|---|---|---|
| Contents row 66 | `LOIFactor` = 0 in 4 active items | **BENIGN** — sits in the BROAD block, whose BaseRate is also 0 because this risk elects Special. A dormant block shows one factor flag |
| Contents rows 70, 98 | `MultiResidentialPropSpecialCreditFactor` hard-coded `=1` | **BENIGN** — ISO files this credit for Building only: 40 refs in `CommercialPropertyStructureRules.Rule.xml`, **zero** in any PersonalProperty rules file. The constant is correct |
| Bldg / Contents, several | Label misspelled `…SepcialCredit…` | **COSMETIC** — no premium impact; formulas address cells, not labels. Worth fixing because a label search finds one spelling and misses the rest |

### 4. Standing assumptions — accepted divergences, **not** errors

D-1 district shortcuts · D-2 full value assumed equal to limit · S-1/S-2/S-3 shared
exclusion inputs · blanket unbuilt · Earthquake unbuilt · Specific/Tentative built but
never ISO-verified · one ERC edition resolved outside the workbook.

**Why these sit on the same page as the live checks.** "The rater assumes full value
equals the limit" is obvious to whoever chose it and invisible to whoever reads the
number six months later. A diagnostics page that only reported *errors* would imply
the rest is unconditionally trustworthy. These are the conditions on the number.

---

## What this is not

**It is not a report that was true once.** Sections 1 and 2 are formulas; the page
re-evaluates on every recalculation. Sections 3 and 4 are prose, because a verdict and
an accepted trade-off are judgements, not computations.

**It does not catch what nobody has thought of.** Every check here exists because a
specific defect was found first — mostly today. It is a record of what has gone wrong,
not a proof that nothing else can.

---

## Idempotent

The script deletes and rebuilds the sheet, so checks can be added or retuned without
stale rows surviving underneath. `scripts/cf/99_r7_diagnostics_tab.py`.

---

## Streamlining status

| | |
|---|---|
| **R-1** name every input · **R-2** tab naming · **R-3** guard/provenance columns · **R-4** policy factors · **R-7** diagnostics | done |
| **M-1** Special Class factors · **T-1** total premium | fixed along the way |
| **R-5** split exclusion inputs · **R-6** edition/state basis · **R-8** row-per-item inputs | remaining |

**R-6** is the natural next one: it is pure presentation of data already pulled, and it
would fill the one gap this page leaves — the edition and state basis currently sits in
section 4 as a blanket caveat rather than naming which state is stale on this risk.
