# Property chunk 28, C28-19: flag dates beyond the corpus (Set F, OI-105), measured and proposed

**Status: proposed 2026-10-06, no engine change.** Measured by `scripts/cf/255_chunk28_c28-19_coverage.py` from
`242_`'s live comparison (`results/cf-raas/chunk27_c27-13_editions.json`, 276 calls, 2026-10-02). The build waits on
the user's go and the two choices below.

## In plain English

For each state, ISO's answer depends on which rate package is in force on the policy date. Our corpus is a snapshot:
for a later date ISO may use a package we don't have, and ours then rates on the older one, without a word. On
2026-10-02 we asked ISO which package it used in every state at six dates (2026-09-17 to 2027-10-01). That tells us,
per state, the first date where ours is known to be on the wrong package. The proposal: the engine says so for a
request on or after that date.

**It mattered today**: Illinois has used `CF IL 20261001` since 2026-10-01. **Imported 2026-10-06** (C28-20, the user's
decision to refresh the corpus): 8 of 8 Illinois cases agree with ISO at 2026-11-01 (`256_`); 33 packages remain, the
first due 2027-01-01.

## What was measured

| | |
|---|---|
| States compared | 46 of 46 |
| Same package as ISO at 2026-09-17 | 46 of 46 |
| Packages ISO serves that the corpus lacks | 34 |
| States where ours goes onto the wrong package within the dates checked | 28 |
| Wrong package already today (2026-10-06) | **IL** (from 2026-10-01) |
| From 2027-01-01 | AR CT IN MD MN MO MT ND NE NH NM NV OR SD TN UT WI WV WY (19) |
| Later in 2027 | AK (02-01); AZ DC ME VA VT (03-01); GA (04-01); KS (06-01) |
| No newer package seen through 2027-10-01 | AL CA CO DE FL IA KY MA MI NC NJ NY OH OK PA RI SC TX (18) |
| Stored requests past their state's date | 1 of 1,804 (`chunk11_C0_at20270101`, OR 2027-01-01, the OI-105 original) |

**The task's own wording would have missed two states.** C28-19 says "a request dated after the latest package the
corpus holds". CT and NM hold a 2027-03-01 package, yet both miss ISO's 2027-01-01 edition, and from 2027-04-01 ISO
uses a V02 of the March package where we hold V01. A test on "the latest package we hold" passes both; the gap is a
missing edition in between, or a newer version of one we have. So the date has to come from what ISO serves, which is
what `242_` measured, not from the corpus alone.

## What the build would be

1. **A coverage table**, checked in and generated from `242_`'s results: per state, `stale_from` (the earliest
   edition date of a package ISO served that we lack) and `checked_to` (the last date compared, 2027-10-01), plus the
   date ISO was asked (2026-10-02). Re-running `242_` (C28-20, the corpus refresh) regenerates it.
2. **A check before rating** (Property only, beside the C28-17 checks): request date on or after its state's
   `stale_from` → the outcome says *wrong package*, naming both packages; after `checked_to` → *unchecked*.
3. **No premium moves** on any request dated 2026-09-17 (1,803 of the 1,804 stored); `157_ --all`, `206_ --check` and
   `104_ --quick` re-run to show it.

## The two choices (the user's)

**1. What a known-wrong-package date does** (IL today; 28 states over 2027):

* **(a) Refuse** (recommended): ours is known not to be ISO's answer, the same footing as C28-17's silent zeros. An
  Illinois request refuses until the corpus holds `CF IL 20261001` (C28-20).
* **(b) Rate, with a warning** on the outcome: the premium is a real filed one, just not the one in force.
* **(c) Refer to company**: the premium stands, a human decides.

**2. What a date past the last check does** (after 2027-10-01 anywhere, or any date once the comparison is old):
**rate with a warning** (recommended; nothing is known to be wrong), or treat it like (1).

## Not covered

* Packages that appeared and were superseded between two sampled dates can't be seen (e.g. a CT edition between
  2027-01-01 and 2027-04-01). Each state's `stale_from` is the earliest edition seen, so a request is never flagged late
  for an edition we did see.
* ISO can file more packages after 2026-10-02. The table is only as current as the last `242_` run, and the check
  will say when it was.
