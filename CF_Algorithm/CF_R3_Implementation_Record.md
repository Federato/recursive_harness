# R-3 implemented — every calc row now explains itself

**2026-09-22.** Applied to `CFRater1.02.xlsb`. `CFRater1.01.xlsb` never opened.

| | |
|---|---|
| Rows annotated | **434** across the four rating worksheets |
| Live zero-checks | **174** |
| Columns added | **M = Source**, **N = Check** |
| Premiums | **unchanged** — as they must be |

---

## What was added

Two columns to the right of the item columns on each `CALC -` sheet.

**`M` Source** — derived by parsing each row's actual formula, not typed by hand:

| Formula | Source reads |
|---|---|
| `=IFERROR(INDEX('TBL - LCM'!$B$2:$B$47,…))` | `sheet: TBL - LCM` |
| `=IN_Pol_IRPMFactor` | `input: IN_Pol_IRPMFactor` |
| `=C21` | `chained: C21` |
| `=1` | **`CONSTANT (hard-coded)`** |
| `1` (typed) | **`CONSTANT (typed value)`** |

**`N` Check** — a live formula counting zeros among **active** items only:

```
=IF(SUMPRODUCT((IN_Loc_State<>"State")*(C12:L12=0))=0,
    "ok","ZERO in "&…&" active item(s)")
```

Using the R-1 named ranges to tell a real item from an empty placeholder column
matters more than it sounds: without it every row reports six zeros forever and the
column gets ignored inside a day.

**This pass could not change a premium.** It writes only to two previously empty
columns that nothing reads — the one change in this series that is additive by
construction rather than by careful verification. Verified regardless.

---

## The first run cried wolf, and tuning it was the real work

| | Flags |
|---|---|
| First thresholds | **46** |
| After tuning | **3** |

Two sources of noise, both removed:

**Block titles.** `BASIC GROUP I`, `BUILDING BGI` and their siblings hold a typed
`1` as a section header. Flagged as hard-coded constants; they are not factors at
all. Now classified `block header`.

**Legitimate zeros.** The first pass checked anything rate-ish. A zero is normal in
three common cases, none of them a defect:

- **Additive rates** — `VacantBuildingRate`, `SubStdConditionRate` are `0` unless the
  condition applies, and they are *added*, so `0` is their neutral value.
- **An unelected form** — Broad's `BaseRate` is `0` on a risk that elects Special.
- **Branch-only values** — `LowestBaseRate` is `0` outside the wind/hail-excluded rebuild.

**A zero in a *factor* has none of those excuses.** It is multiplied in, so it takes
the whole chain with it — the shape of the documented Joisted-Masonry defect. The
check now covers factors, multipliers and coinsurance only.

**The lesson is the threshold, not the mechanism.** A check that fires 46 times on a
clean workbook teaches people to ignore the column, which is worse than no column —
it manufactures false confidence. Getting to 3 is what makes it usable.

---

## What the three surviving flags turned out to be — all benign

Investigated rather than reported. **None is a defect.**

**1. `LOIFactor` = 0, Contents row 66.** Sits in the `BROAD` block (row 61), whose
`BaseRate` is also 0 because this risk elects **Special**. The whole block is
correctly dormant. *Known-benign pattern:* a dormant block shows one factor flag.
Acceptable at 1 per 434 rows; suppressing it would mean teaching the check which
form is elected, which is not worth the complexity yet.

**2 & 3. `MultiResidentialPropSpecialCreditFactor` hard-coded `=1`, Contents rows 70
and 98** — while Building rows 21/75 read `'CALC - CoreScratchpad'!C51`. This looked
exactly like the `=1` defects found in R-4 and M-1, and the sample risk *does* elect
the credit.

**It is not a defect.** `MultipleResidentialPropSpecialCredit` appears in
`CommercialPropertyStructureRules.Rule.xml` **40 times and in no PersonalProperty
rules file at all**. ISO files the credit for Building only. Contents' `=1` is
correct and deliberate.

**Worth stating plainly: a hard-coded `1` is sometimes right.** It means "this factor
does not apply here". The Source column's job is to make that visible for a human to
adjudicate, not to declare it wrong. Three times today a `CONSTANT` was a real
defect; the fourth time it was correct, and only reading ISO's rules separated them.

---

## A genuine, if cosmetic, find

The label is **misspelled** on four of six rows: `MultiResidentialPropSepcialCreditFactor`
("Sepcial") on `CALC - Bldg Rating` rows 21/51/75 and `CALC - Contents Rating` row 70;
correctly spelled on Bldg 101 and Contents 98.

No premium impact — formulas address cells, not labels. But it is precisely the trap
that caused the M-1 mistake earlier today: a label-based search finds one spelling and
reports the other rows as absent. Worth correcting for that reason alone.

---

## Assurance this actually bought

After adjudication: **zero unexplained zeros and zero unexplained constants across all
174 multiplicative factor checks on the four rating worksheets.** That is a statement
the workbook could not previously make, and it is now recomputed live on every change
rather than needing a person to go looking.

---

## Scripts

`scripts/cf/98_r3_guard_columns.py` — idempotent: it clears columns M/N and rebuilds
them, so thresholds can be retuned without stale rows surviving underneath.

---

## Next

Streamlining status: **R-1, R-2, R-3, R-4 done**; M-1 and T-1 fixed along the way.
Remaining: **R-5** split exclusion inputs per datadef group · **R-6** edition/state
basis on the face · **R-7** diagnostics tab · **R-8** row-per-item inputs.

R-7 is the natural follow-on — it would surface the Check column's flags in one place
instead of requiring a scroll through four sheets.
