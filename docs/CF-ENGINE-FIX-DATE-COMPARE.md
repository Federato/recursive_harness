# Engine fix: ordered comparison of two dates

**Found and fixed 2026-09-22, chunk 11 (C11-01), user-authorized.**
File: `gl_engine/interp/nodes.py`, `_cmp` (backs `GreaterThan`, `LessThan`,
`GreaterThanOrEqual` and `LessThanOrEqual`).

## In plain English

Leasehold Interest works out how many months are left on a lease, and to do
that it asks "does the lease end after the policy starts?" Our engine could
compare two numbers but not two dates, so it stopped with an error. It now
compares dates as dates.

## What was wrong

`_cmp` pushed both operands through `ip.num`, so a `dateTime` operand raised
`date is not numeric (§12.3)`. The chunk 11 census had confirmed that every
`rul:` **element** Leasehold Interest uses was implemented. That was true of
the element names but not of their operand types. A census that checks node
names doesn't cover operand types: that's the process gap.

## The change

If **both** operands are dates, compare them as dates. Every other shape
takes the old path unchanged:

| Operands | Before | After |
|---|---|---|
| number vs number | compared | compared (unchanged) |
| date vs date | **refused** | **compared** |
| date vs number | refused | refused (unchanged) |
| date vs `01/01/0001` (coerces to null) | null path | null path (unchanged, on purpose). Under the configured `propagate` mode, **a comparison with a null operand yields FALSE** |

The last row is deliberate, and an earlier version of this page got it
wrong. It said such a comparison "still refuses". It doesn't: under
`propagate` (the configured default), `Interpreter.eval` turns a null operand
in any ordered comparison into **False**. That was already the behaviour for
numbers, and this fix leaves it alone. In ISO, `01/01/0001` is .NET's
`DateTime.MinValue`, an ordinary date that compares normally. So the two
agree when MinValue sits on the side that makes the test false anyway, and
**disagree** when it doesn't. C11-04 measures exactly where, and C11-23 takes
it to ISO.

## Scope, corpus-wide

28 ordered comparisons with a `dateTime` operand, in 5 countrywide files
(`CF_CW_20260601_V01`):

| File | Rules | Premium-bearing? |
|---|---|---|
| `CommercialPropertyLeaseholdInterestCoverageFormRules` | `SetNumberOfMonths` | **yes**, the LI annuity |
| `CommercialPropertyBuildersRiskPremiumAdjustmentFormDetailRules` | `SetProRate` | **yes** |
| `CommercialPropertyStructureRules` | CP 00 60 Leasehold date messages, CP 04 50 permit-period messages | no (validation) |
| `CommercialPropertyPersonalPropertyRules` | CP 04 50 and CP 12 30 period messages | no (validation) |
| `CommercialPropertyRules` | Peak Season period messages | no (validation) |

None of the 28 was reachable before, because no earlier golden case supplied
the dates they read. That's why chunks 1–10 never hit this.

## Verification

* `114_chunk11_golden_case.py`: all 20 hand-derived values match, **$268 +
  $30**.
* `115_chunk11_groupA_annuity.py`: 8 of 8 one-input-changed cases match,
  including a day-of-month adjustment that exercises both date branches.
* `09_chunk2_golden_case.py`: still **$261 / $32**.
* Full regression `104_chunk10_c10-21_regression.py`: **REGRESSION CLEAN
  2026-09-22**. Every chunk 0–9 golden case reproduces its documented
  figures, and every machinery script and all 16 GL suites exit 0 with no
  failure marker.
* Chunk 10, which that harness doesn't cover yet (owed by C11-24):
  `85_chunk10_golden_case.py`, `103_…sublimit_flatdeductible.py` and
  `95_…all_groups_chain.py` all exit 0.

## Follow-up fix: the `01/01/0001` sentinel orders as the earliest date (OI-102)

**Fixed 2026-09-22, user-authorized**, same function, after C11-23 confirmed
the divergence live.

**In plain English.** A blank date falls back to "January 1, year 1". ISO
treats that as a real, very early date. Our engine treated it as "no date",
so any "is X before Y?" test involving it came out *no*. For a Leasehold
Interest with no lease start date, that meant $0 here and $272 at ISO. Now,
in an ordered comparison only, the fallback counts as the earliest possible
date, as ISO does.

**Exactly what changed.** In `_cmp`, a null operand counts as `date.min` only
when `_is_date_zero` recognises it as the sentinel: a `dateTime`
`FirstValue` whose `FromConstant` is `01/01/0001`, or a `dateTime` `Constant`
of that text. That's 56 of the 60 operands in the corpus's ordered date
comparisons. **Deliberately unchanged:**
* `coerce` still reads the sentinel as null, so `IsNull`, `IsNotNull` and
  equality behave as before;
* the 4 bare `Value` operands, because how ISO orders a missing bare
  `Value` hasn't been measured;
* every non-date comparison.

**Verification**
* Live ISO, 2026-09-17: the missing-`LeaseEffDate` case moved from **$0** to
  **$272 / $31**, agreeing with ISO, with the golden control unchanged at
  $272 / $31 on both sides.
* `114`–`117` (chunk 11 golden, Group A, Group B, zero cases): all exit 0.
  Z6 is now a not-zero check.
* Full regression `104_chunk10_c10-21_regression.py`: **REGRESSION CLEAN
  2026-09-22**, 51 of 51. Chunk 10's `85`, `103` and `95` all exit 0.

## Second follow-up: `Power(0, 0)` returns 1 (OI-104)

**Fixed 2026-09-22, user-authorized**, in `gl_engine/interp/nodes.py`
`_power`. Not a date fix, but it came out of the same chunk 11 zero-case work,
so it's recorded here beside the other two.

**In plain English.** 0 to the power 0 has no single mathematical answer.
Python refuses to give one; ISO's .NET says 1. A Leasehold Interest with no
interest rate and no months left hits exactly that, and so does **any
Leasehold Interest building sent without its lease details**, because ISO's
rules create an empty lease record for it. Our engine crashed on those; ISO
prices them at $0. Now we say 1, as ISO does, and price them at $0.

**Exactly what changed.** `base == 0 and exp == 0` returns 1 (rounded as the
element asks), with a `power-zero-zero` trace note. Every other `Power` is
untouched, including the refusal for a non-positive base with a fractional
exponent.

**Verification**
* Live ISO, 2026-09-17, case Z13 (blank rate + expired lease): **$0 on both
  sides**. Before this fix, ours refused.
* `117` Z13 is now a T3 zero. `119`: an LI structure with no LI record runs,
  the auto-created record has all 20 cells off, and the total is $0.
* **One regression expectation moved, and it was the right one.**
  `61_chunk8_zero_cases.py` case 3 (a Legal Liability risk switched to
  `CovType = Leasehold Interest`) had pinned the old refusal, and its note
  said *"this zero belongs to chunk 11"*. It now rates to **$0**, both Legal
  Liability factors 0, which is what chunk 8's map predicted before 0^0 got
  in the way. The expectation and its note were updated, with the history
  kept.
* Full regression, now covering **chunks 0–11** (see below): the only
  failure was that pinned expectation. After updating it, **clean**.

## The regression harness now covers chunks 10 and 11

`104_chunk10_c10-21_regression.py` (same file name, so every reference still
works) now also runs:
* chunk 10's golden case (**$6 / $261**) and chunk 11's (**$268 / $30 / $298**),
  pinned to their documented figures;
* 10 chunk 10 test scripts and 4 chunk 11 test scripts (the ones that exit 1
  on disagreement). The censuses are listed as excluded, with the reason.

**One harness trap fixed while extending it.** The "zero-case" relaxation
(allow `RAISED` in output, require a match-line) keyed on `zero_cases` in the
**filename**. It would have silently applied to chunk 10's and 11's zero-case
scripts, which print neither, and failed them for the wrong reason. It now
applies to the three chunk 6/7/8 scripts it was written for, **by name**.
`--selftest` still passes, 7 of 7.

## Third follow-up: `DateDifference` sign (OI-107)

**Fixed 2026-09-22, user-authorized.** `_date_difference` now returns
`(second − first).days`; it used to return `(first − second).days`.

**In plain English.** "Days from A to B" was being computed as "days from B
to A". Anything that divided one such count by another came out right,
because the minus signs cancelled. Anything that used a single count, like
"days until TRIA expires", came out negative.

**Evidence.** Live ISO, Oregon, EffDate 2026-09-17, TRIA expiring
2027-06-01: `DaysUntilTRIAExpiration` **ISO 257, ours −257** before the fix,
**257** after. It's pinned offline in `120_chunk11_groupsEF_inventory_states.py`,
which is now in the one-command regression.

**Regression: CLEAN 2026-09-22, 68 of 68**, including all 16 General
Liability suites. **What that does not prove:** no GL suite exercises
General Liability's `SetMaturity*Year` (ERP) rules, the only GL rules using
`DateDifference`, and their operand order differs by edition. So the GL
suites passing says the fix broke nothing they test, not that GL ERP maturity
is now right. That needs its own ERP case, logged on OI-107.
