# Excel Rater — Rating Paths Checklist

**Written:** 2026-09-02.

**Purpose.** The `Excel_Rater_*.md` documents built so far work at the grain of one document per
coverage per cause-of-loss form. That grain hides a real question: *within* a form, how many distinct
rating paths does ISO's own rule file actually branch into, and which of those are documented versus
just noted in passing? This checklist answers that at the finer grain — **Coverage × Cause-of-loss form
× Rating type × Premium branch** — so "is X done" has one place to check instead of requiring a re-read
of four documents.

**Scope.** This covers the five rating paths a chargeable premium can take once a coverage and
cause-of-loss form are selected: the primary (Class-rated, for forms that have that concept) scheduled
path, the Specific/Tentative-rated scheduled path (Basic Group I only, confirmed absent from every other
form), the Legal Liability premium branch, and the blanket-rated premium branch. It does **not**
re-itemize the 92+ endorsement families already tracked in `Coverage_Inventory_And_Tracking.md`, or the
Special Class / Special Class Business Income coverages that haven't had a rater doc started — those are
listed at the end as what's outside this checklist's grain, not repeated here.

**Legend:** ✅ documented and built into calc-tab columns with example rows &nbsp;|&nbsp; 📝 documented in
a formula (quick-reference / if-then form) but not built into calc-tab columns or example rows &nbsp;|&nbsp;
⬜ not documented at all &nbsp;|&nbsp; — structurally absent (confirmed by the source doc, not just
unbuilt — there is nothing to build)

---

## Building

| Form | Primary scheduled path | Specific/Tentative scheduled path | Legal Liability | Blanket-rated |
|---|---|---|---|---|
| Basic Group I | ✅ `Excel_Rater_BasicGroupI.md` §4 | ✅ `Excel_Rater_BasicGroupI.md` §9 | 📝 formula in §8, not built — `Excel_Rater_BasicGroupI.md` §7 | 📝 formula referenced, not built — §7 |
| Basic Group II | ✅ `Excel_Rater_BasicGroupII.md` §4 | — confirmed no `RatingType` branch exists for this form | 📝 not built — `Excel_Rater_BasicGroupII.md` §7 | 📝 not built — §7 |
| Broad | ✅ `Excel_Rater_Broad.md` §4 | — confirmed absent | 📝 not built — `Excel_Rater_Broad.md` §7 | 📝 not built — §7 |
| Special | ✅ `Excel_Rater_Special.md` §4 | — confirmed absent | 📝 not built — `Excel_Rater_Special.md` §7 (raw-rate formula, differs from Contents' — see below) | 📝 not built — §7 |

## Contents (Personal Property)

| Form | Primary scheduled path | Specific/Tentative scheduled path | Legal Liability | Blanket-rated |
|---|---|---|---|---|
| Basic Group I | ✅ `Excel_Rater_BasicGroupI.md` §5 | ✅ `Excel_Rater_BasicGroupI.md` §9 | 📝 formula in §8, not built — §7 | 📝 not built — §7 |
| Basic Group II | ✅ `Excel_Rater_BasicGroupII.md` §5 | — confirmed absent | 📝 not built — §7 | 📝 not built — §7 |
| Broad | ✅ `Excel_Rater_Broad.md` §5 | — confirmed absent | 📝 not built — §7 | 📝 not built — §7 |
| Special | ✅ `Excel_Rater_Special.md` §5 | — confirmed absent | 📝 formula in §8, uses `COLAdj` (not the raw rate Building's version uses) — not built, §7 | 📝 not built — §7 |

**Worth restating from `Excel_Rater_Special.md` §6:** when the Legal Liability branch does get built for
Special, Building and Contents genuinely need different formulas — Building's uses the raw,
un-theft-adjusted rate; Contents' uses the already-theft-adjusted `SpecialCauseOfLossAdjustment`. Marking
both cells 📝 in the tables above understates that this is two different formulas to build, not one
formula in two places.

## Business Income

| Form | Primary scheduled path | Specific/Tentative scheduled path | Legal Liability | Blanket-rated |
|---|---|---|---|---|
| Basic Group I | ✅ `Excel_Rater_BusinessIncome_BasicGroupI.md` §4 | ✅ `Excel_Rater_BusinessIncome_BasicGroupI.md` §8 | — Business Income has no Legal Liability coverage type at all (confirmed structural absence, all four forms) | 📝 formula referenced, not built — §7 |
| Basic Group II | ✅ `Excel_Rater_BusinessIncome_BasicGroupII.md` §4 | — confirmed absent | — | 📝 not built — §7 |
| Broad | ✅ `Excel_Rater_BusinessIncome_Broad.md` §4 | — confirmed absent | — | 📝 not built — §7 |
| Special | ✅ `Excel_Rater_BusinessIncome_Special.md` §4 | — confirmed absent | — | 📝 not built — §7 |
| Earthquake | ⬜ not started — real 5th rate chain, no standalone non-Agreed-Value premium file exists in ISO's own rules | — Earthquake has no `RatingType` concept in the source doc | — no standalone Legal Liability path (Earthquake has no scheduled premium file at all outside Agreed Value) | ⬜ Earthquake premium only exists through Agreed Value (see below) or the blanket average-rate roll-up — neither traced yet |

**Business Income add-ons, not yet started, not fitting the four-column shape above:**

| Path | Status | Note |
|---|---|---|
| Agreed Value (waives coinsurance) | ⬜ not started | Charges `(Factor − 1) × Rate × (Limit/100)` — an incremental surcharge, not a full-rate multiplication; the only way Earthquake charges standalone premium in this package |
| Extended Period of Indemnity | ⬜ not started | Same incremental-surcharge shape as Agreed Value, five per-form coverage files |

---

## What's outside this checklist's grain

This checklist stays at Coverage × Form × RatingType × Premium-branch. Two things sit at a coarser or
orthogonal grain and are tracked elsewhere, not duplicated here:

- **Special Class and Special Class Business Income** — two more core coverages, each with their own
  four-or-five-form structure mirroring Building's and Business Income's. Confirmed to exist (source
  `CauseOfLoss_SpecialClass_RatingAlgorithms.md` and the "Special Class Business Income" section of
  `CauseOfLoss_BusinessIncome_RatingAlgorithms.md`), but no `Excel_Rater_*.md` document has been started
  for either. When started, expect this same checklist shape to apply to both.
- **The 92+ endorsement families** (Ordinance or Law, Business Income time-element extensions,
  Earthquake and Volcanic Eruption endorsement, Leasehold Interest, Utility Services, Builders Risk,
  Vacancy Permit, and the rest) — tracked in `Coverage_Inventory_And_Tracking.md` Parts B/B11 at the
  family level, not the rating-path level. None have an algorithm doc traced yet, let alone a rater doc.

---

## Summary count

| | Documented ✅ | Formula-only 📝 | Not started ⬜ | Structurally absent — |
|---|---|---|---|---|
| Building (16 cells) | 5 | 8 | 0 | 3 |
| Contents (16 cells) | 5 | 8 | 0 | 3 |
| Business Income (22 cells, incl. the 2 add-on rows) | 5 | 4 | 4 | 9 |
| **Total (54 cells)** | **15** | **20** | **4** | **15** |

15 rating paths are fully built with calc-tab columns and example rows. 20 more already have their
correct formula written down (in a "quick reference" or if/then block) but aren't walked through with
calc-tab columns or example data yet — that's the fastest next tranche, since the hard tracing work is
already done for all 20. 4 are genuinely untouched (Earthquake's two grid cells plus the Agreed Value and
Extended Period of Indemnity add-ons), and 15 combinations don't exist at all in ISO's own rules
(confirmed, not assumed) — mostly the `RatingType` branch that only Basic Group I has, and Business
Income's structural lack of a Legal Liability coverage type across all five forms.

## Remaining steps

1. You review this checklist against the four coverage documents it's drawn from — flag anything marked
   📝 or ⬜ that you believe is actually further along, or ✅ that overstates what's really built.
2. Given the 📝 column is the cheapest next win (formula already traced, just needs calc-tab columns and
   example rows), that's a reasonable place to point next if you want breadth before depth — your call.
3. Nothing gets built until you say go.
