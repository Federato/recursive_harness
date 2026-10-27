# Engine fix: an empty state table does not hide the countrywide rows (Property)

**2026-09-28, chunk 18 RC-4. User's go given in session. Property only; General Liability unchanged.**

## In plain English

A state package can file a table with a header and no rows. The engine had treated
that as the state's final word ("we do not do this here"), so any lookup against it
found nothing and priced $0. ISO does not: for Property it uses the countrywide rows
instead. Vermont exposed it. Vermont files `VacancyPermitFactors` empty, so our
Vacancy Permit Special form priced $0 where ISO charged $87 on the building and $18
on contents.

## What changed

`cf_engine/resolve/book.py`: `book_for` now returns a `CFResolvedBook`. Its `table()`
keeps the state's table when it has rows (the state still wins outright), and when the
state's table is **empty and the countrywide table has rows**, returns the countrywide
table. GL's resolver (`gl_engine/resolve/book.py`) and its documented rule N3 ("a state
override is final by name, even when empty") are untouched.

## Evidence

- **Vermont, live** (`189_chunk18_rc4.py --states VT --live`): before, Special $0 vs ISO
  $87 / $18; after, 48 of 48 records, **178 of 178 premiums, messages equal**.
- **A state table with rows still wins, even on a missing key.** Kansas files its own
  `VacancyPermitFactors`; on a Standard Property Policy the CW-keyed lookup for the
  earthquake row misses and **ISO refuses the policy** rather than falling back (OI-103:
  our engine prices it).

## Open question found 2026-09-29 (chunk 19, C19-17): ISO does not always fall back

`195_chunk19_c19-17_eq_tiers.py --live`, E7. Vermont (in force: CF VT 20260201 V02 over CF CW 2023 V04)
files `EQSubLimitDeductibleTierCWTable` **header-only**, exactly as it files `VacancyPermitFactors`. An
antenna / sign on the CP 10 45 sub-limit form at Tier 1 reads that stub. **ISO REFUSES the policy**
(`Matrix: EQSubLimitDeductibleTierCWTable, Project: CF VT 20260201 V02, Keys: CW, Y`); our engine falls
back to the countrywide row (factor 0) and prices EQ $0. Yet for `VacancyPermitFactors` ISO did fall back.
Checked and ruled out as the difference: the package (both empty in every VT batch, including the one in
force), the countrywide edition (CW 2023 V04 files both with rows), and the lookup shape (both are a
state-keyed `FirstResult` lookup then a `CW`-keyed `SingleResult` one). **Unexplained; the fix stands as
built, and this is an open question for chunk 28's engine behaviour decisions** (whether the fallback should
be narrower). It widens OI-103: here ISO refuses where we price $0.

## Blast radius, checked

- 209 state tables in the 46 states are empty while the countrywide one has rows; 204 are
  read by some in-force rule (many behind conditions ordinary policies never meet).
- **Regression CLEAN, 115 of 115** (chunks 0-17 and the GL suites, `--jobs 3`,
  `logs/regression_after_empty_table_fix.log`). The only two failures were structural
  assertions in `45_` and `47_` that asked the book for a state's empty table; they now
  read the state's own file (what it filed). No premium assertion moved.
- **`157_ --all`: 293 of 293** stored ISO policies, 14,236 premiums and every total equal.
- **Every stored chunk 18 ISO response (87) re-rated with the fix: 87 of 87 equal**,
  13,640 premiums and messages.
- Puerto Rico files two coinsurance-surcharge tables empty; it now takes the countrywide
  surcharge. PR is out of scope for ISO comparison, so that is unverified for PR.

## Process gap this closes

The prediction for Vacancy Special read its factor from the engine's own tree, so it
agreed with the engine's $0. The check that was missing: **every factor a premium
multiplies is looked up independently in the prediction** (`189_` now derives the Special
factor from the table, state rows if any else countrywide).
