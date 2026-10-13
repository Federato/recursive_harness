# R-4 implemented — policy-level factors now have inputs

**2026-09-22.** Applied to `CFRater1.02.xlsb` (the prototype). `CFRater1.01.xlsb`
was never opened.

| | |
|---|---|
| Inputs added | 3, on `Policy Inputs` rows 22–24, under a new **Policy Factors** heading |
| Cells repointed | **150** — 120 on `Bldg Rating Worksheet`, 30 on `BI Rating Worksheet` |
| Premiums at 1.0 | **unchanged** — 7183 / 8022 / 2699 / 1434 / 406 / **17904** |
| Premiums at IRPM 0.9 | **moved** — 6464 / 7219 / 2427 / 1434 / 406 / **16110** |

---

## The survey changed the job before any cell was written

R-4 was proposed as *"every coverage tab carries its own independent flat 1.0 —
point them all at one block."* Reading the actual formulas showed **half of that
was already wrong**, and the half that was right was worse than described.

| Factor | What was proposed | What is actually there | Action |
|---|---|---|---|
| `LCM` | flat 1.0, centralise it | **A genuine per-state lookup** — `INDEX(LCM!$B$2:$B$47, MATCH(CoreScratchpad!C2, …))`, already resolving per item | **Left alone** |
| `CyberExcl*` | flat 1.0, centralise it | **Already single-sourced** — every one of 240 cells gates off `'Policy Inputs'!$F$3/$F$4/$F$5` | **Left alone** |
| `IRPM` | flat 1.0 per tab | Hard-coded `1.0` in 40 cells, **no input anywhere in the workbook** | **Fixed** |
| `PackageMod` | flat 1.0 per tab | Same — 40 cells, no input | **Fixed** |
| `MultiPremiumDispersion` | flat 1.0 per tab | Same — 40 cells, no input | **Fixed** |

**On Cyber specifically — collapsing it would have been a bug.** Its values are
`0.995` everywhere for `CyberExclFactor`, but `CyberExclCOLExcpnsFactor` is `0.997`
for Basic Group I / II / Broad and **`0.996` for Special**. That split is *filed
data*, not duplication — it is exactly the premium bug found and fixed in
BUILD-LOG Entry 28, and treating the three tabs as interchangeable would have
reintroduced it.

**The real defect was narrower and more serious than "duplication":** there is no
way to apply an IRPM to a policy. Doing it by hand meant editing 40 cells.

---

## What was changed

```
'Policy Inputs'
  B21  Policy Factors                                (new section)
  B22  IRPM Factor:                              C22  1.0   IN_Pol_IRPMFactor
  B23  Package Mod Factor:                       C23  1.0   IN_Pol_PackageModFactor
  B24  Multi-Premium & Dispersion Credit Factor: C24  1.0   IN_Pol_MultiPremiumDispersionFactor
```

`Bldg Rating Worksheet` rows 23/53/77/103 (IRPM), 27/57/81/107 (MultiPremium),
28/58/82/108 (PackageMod), columns C:L — one row per form — now read
`=IN_Pol_IRPMFactor` and siblings. Contents inherits automatically because it
chain-references Bldg (`='Bldg Rating Worksheet'!C23`).

---

## The thing the verification caught

The first pass verified **both** directions: premiums unchanged at 1.0, and premiums
*moving* at 0.9. The second half is what earned its keep — at IRPM 0.9:

```
Building  7183 -> 6464   moved
Contents  8022 -> 7219   moved
BI        2699 -> 2699   DID NOT MOVE
```

**Cause: Business Income's head cells held the formula `=1`.** A literal dressed as
a formula. The survey's "does it start with `=`?" test read them as wired, which is
how they survived the first pass — and, presumably, how they were never noticed. 30
cells across rows 19 / 20 / 21; every later BI block chains off them.

Repointed in a second pass; BI now moves 2699 → 2427.

**A one-sided test would have passed and shipped this.** "Premiums unchanged" is
what you check to prove you broke nothing; it cannot tell you the wiring is live.
Checking that a factor *moves the number* is what proves it connected — and it is
the same discipline as the harness's gate point 4, testing every `0` against its
consuming branch rather than merely observing it.

---

## ✅ M-1 CLOSED 2026-09-22 — and the finding below was filed on a false premise

**The section that follows is wrong and is kept visible rather than deleted.** It says
`Special Class Worksheet` "carries no `IRPM`, `PackageMod` or `MultiPremiumDispersion`
cells at all". It has **24 of them**, and the premium formulas already consume them.

**Why the survey missed them:** it matched the **abbreviated** labels the
Building/Contents/BI sheets use (`IRPM`, `PackageMod`, `MultiPremiumDispersion`); this
sheet uses ISO's **full** names (`IRPMFactor`, `PackageModFactor`,
`MultiPremiumAndDispersionCreditFactor`). The search returned nothing and that was read
as an absence.

So M-1 was never "new rating behaviour needing approval" — it was **the same
disconnected-constant defect in a third place**: rows 17/18/19 held `=1`, and all eight
blocks chained off them. Fixed the same day: 240 cells repointed directly at the R-4
inputs. Verified unchanged at 1.0, and moving at 0.9 (SC $1,434 → $1,292, SCBI
$406 → $365).

**Plus a real bug found on the way:** row 82's
`MultiPremiumAndDispersionCreditFactor` read `=C60` — *PackageModFactor* — instead of
`=C61`. Special Class's Special form counted PackageMod twice and ignored MultiPremium.
Retired by removing the chain entirely rather than repairing the one link.

**And a separate defect found while verifying:** `'Policy Inputs'!I9` ("Total Premium")
is `=I3+I4+I5` and **omits Special Class and SCBI** — $17,904 shown against $19,744
actual. Logged as **T-1**, deliberately not fixed. See
`CF_M1_Implementation_Record.md`.

---

## Original finding, superseded — kept for the record

Special Class (**$1,434**) and SC Business Income (**$406**) did not move at IRPM 0.9,
and **cannot**: `Special Class Worksheet` carries no `IRPM`, `PackageMod` or
`MultiPremiumDispersion` cells at all. Only `LCM`.

**ISO files all three for these groups.** Checked directly against
`CFCW20260601V01\Rules`:

| Rule file | References |
|---|---|
| `…SpecialClassBasicGroupICoverageRules` (and BGII / Broad / Special) | `IRPMFactor`, `PackageModFactor`, `MultiPremiumAndDispersionCreditFactor` — 2 each |
| `…SpecialClassAgreedVal*CoverageRules` (4 files) | all three, 2 each |
| `…SpecialClassBusnIncome*CoverageRules` (4 + AgreedVal 4) | `IRPMFactor`, `PackageModFactor` — 2 each |
| `…SpecialClassBusnIncomeRules` (parent) | `MultiPremiumAndDispersionCreditFactor` ×4 |

This matches the harness's chunk 9 finding (C9-19) that IRPM/PackageMod level counts
vary by group (5 / 7 / 9) rather than being uniform — the factors exist across
groups, they are simply not wired here.

**Deliberately not fixed.** Adding them means creating rows that do not exist and
wiring them into premium formulas — that is new rating behaviour, not the
single-source-of-truth plumbing R-4 scopes. **It will change the Special Class and
SCBI premiums**, so it is the user's call, not a side effect of a refactor. Logged
as backlog **M-1**.

---

## Scripts

| | |
|---|---|
| `scripts/cf/89_r4_survey.py` | read-only formula survey → `CF_R4_Factor_Survey.csv` (730 cells) |
| `scripts/cf/90_r4_apply.py` | adds the inputs, repoints 120 cells, two-sided verification |
| `scripts/cf/91_r4_bi_disguised_constants.py` | the `=1` follow-up, 30 cells |

Both apply scripts refuse to run if any Excel process is alive, refuse
`CFRater1.01.xlsb` by filename, and **abort without saving** if premiums move at 1.0,
fail to move at 0.9, or fail to restore.

---

## Next

R-1 and R-4 done. Cheapest remaining is **R-2** (tab naming, ~1 hr). Highest payoff
is **R-3** (guard + provenance columns) — and this pass is an argument for it: a
hard-coded `=1` sat in the Business Income chain undetected, and a Check column
would have shown it as an unsourced constant on sight.

**Decision owed:** backlog M-1 — wire IRPM / PackageMod / MultiPremium into Special
Class and SCBI? It changes those premiums.
