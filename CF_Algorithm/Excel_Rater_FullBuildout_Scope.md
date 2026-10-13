# What "Fully Built, Per ERC and the Circulars" Actually Requires — CF Rater Scope

**Written:** 2026-09-02.

**Two things this project is doing in parallel, not to be conflated.** This document set
(`Excel_Rater_*.md`) is building a spreadsheet-shaped, human-readable rater — the workbook described in
`Excel_Rater_Overview.md` and `Excel_Rater_BusinessIncome_Overview.md`. Separately, `docs/CF-PROPERTY-
INTEGRATION-PROPOSAL.md` and `docs/CF-RATING-ENGINE-BUILD-PLAN.md` propose an eventual `cf_engine/`
Python package, mirroring `gl_engine/`'s architecture. Both tracks are gated the same way — no code, no
`.xlsx`, until explicitly authorized — and both draw on the same underlying source material
(`CauseOfLoss_*_RatingAlgorithms.md`, the ERC corpus, the circular corpus). This document scopes what
"fully built" means for **either** track, since the gap is the same regardless of which one gets built
first: neither can be more complete than the documentation underneath it.

---

## 1. Three legs, not one

"Fully built per ERC and the circulars" has three independent dimensions. A rater can be complete on one
and not the others — this project is currently strong on the first, thin on the second, and has
deliberately not started the third.

**Leg 1 — ERC-side coverage.** Every rating path (coverage × cause-of-loss form × rating type × premium
branch) traced from the ERC rule files into an algorithm doc, then a rater-build doc, then eventually a
workbook. This is what `Excel_Rater_RatingPaths_Checklist.md` tracks, and it's where this project's actual
work has concentrated.

**Leg 2 — Circular/manual verification.** Every ERC-traced formula checked against what ISO's *filed
manual* actually requires — not just internally consistent with the machine-readable data, but confirmed
against the legal text. `Circular_Review_Tracking.md`'s own legend is blunt about where this stands:
**every one of 376 circular documents is at L2 ("characterized") at best; none has reached L3 ("deep-read,
compared against ERC rule by rule")**. One targeted comparison exists —
`ERC-VS-CIRCULAR-COMPARISON.md`, produced 2026-08-20 — but it samples, it doesn't systematically cover
even the coverages already ERC-traced.

**Leg 3 — Jurisdiction and edition breadth.** Every rater doc produced so far, in this document set and
in the underlying `CauseOfLoss_*` docs, traces exactly **one** ERC package:
`CFCW20260601V01` — countrywide, single edition. The real corpus is 8 edition-date folders (2019-12-01
through 2026-06-01) × up to 66 jurisdiction packages per edition. Nothing built so far says anything
about a specific state's own filed rates, or about how rating changes across editions.

A rater "fully built per ERC and the circulars" needs all three legs closed for every coverage. Right now,
for the coverages touched at all, Leg 1 is well along, Leg 2 has one spot-check, and Leg 3 hasn't started.

---

## 2. Coverage-by-coverage status

| Coverage | ERC algorithm doc (`CauseOfLoss_*`) | Rater build docs (`Excel_Rater_*`) | Circular cross-check |
|---|---|---|---|
| Building | ✅ `CauseOfLoss_Building_RatingAlgorithms.md` + `BasicGroupI_ERC_Tables.md` | ✅ all 4 forms — see `Excel_Rater_RatingPaths_Checklist.md` for path-level detail | One spot-check (Special form base rate table), not systematic |
| Personal Property (Contents) | ✅ `CauseOfLoss_PersonalProperty_RatingAlgorithms.md` + `PersonalProperty_ERC_Tables.md` | ✅ all 4 forms, bundled into the same docs as Building | Not checked |
| Business Income | ✅ `CauseOfLoss_BusinessIncome_RatingAlgorithms.md` + `BusinessIncome_ERC_Tables.md` | ✅ 4 of 5 forms (no Earthquake) | Not checked |
| Special Class | ✅ `CauseOfLoss_SpecialClass_RatingAlgorithms.md` + `SpecialClass_ERC_Tables.md` | ⬜ **not started** — algorithm doc exists, no `Excel_Rater_*` doc written yet | Not checked |
| Special Class Business Income | ✅ `CauseOfLoss_SpecialClassBusinessIncome_RatingAlgorithms.md` + `SpecialClassBusinessIncome_ERC_Tables.md` | ⬜ not started | Not checked |
| Earthquake & Volcanic Eruption endorsement (standalone, attaches to all five coverages above, up to 20 files) | ⬜ **not traced at all** — only named in passing (`Coverage_Inventory_And_Tracking.md` Part B11); Business Income's own *internal* EQ cause-of-loss chain is the one exception, already covered in `Excel_Rater_BusinessIncome_*` as "Earthquake — not started" | ⬜ not started | Not checked |
| Flood Coverage endorsement (standalone, 5+ variants) | ⬜ not traced at all — same B11 footnote-only status | ⬜ not started | Not checked |
| The other ~90 endorsement families (Ordinance or Law, time-element extensions, Leasehold Interest, Utility Services, Builders Risk, Vacancy Permit, and the rest) | ⬜ not traced — tracked at the family-name level only in `Coverage_Inventory_And_Tracking.md` Parts B/B11 | ⬜ not started | Not checked |

**The practical reading:** two of five core coverages (Special Class, Special Class Business Income)
already have their ERC-side tracing done and are waiting only for the same `Excel_Rater_Overview.md` +
per-form-doc treatment already proven three times this session (Basic Group I, II, Broad, Special) — that
is comparatively cheap. Earthquake and Flood, and the 90 remaining endorsement families, need the
ERC-tracing step done first; nothing in this document set can jump straight to a rater doc for those.

---

## 3. Cross-cutting mechanisms — needed by every coverage, not yet built for any of them

These aren't per-coverage gaps; they're shared machinery that every coverage's rater doc has referenced
and deferred, the same way every form's "left out of this pass" section says "blanket-rated premium
branch — not built."

**Blanket rating.** Referenced in every single `Excel_Rater_*.md` document produced so far as "not built
this pass," and **it has never been traced as its own mechanism** — no algorithm doc exists for
`SetBlanketValues`, `ErcSetBlanketRatesAndFactors`, or the `CommercialPropertyBlanketRatingTable` scan
that `SetCoinsuranceToUse` depends on (`Excel_Rater_BusinessIncome_Overview.md` §5). Every coverage's
blanket branch is blocked on this one piece of shared tracing, not on five separate ones — tracing it
once unblocks the Blanket column across every row of `Excel_Rater_RatingPaths_Checklist.md` at once.

**Legal Liability.** Better off than blanket — every Building and Contents form's Legal Liability formula
is already written down (📝 status in the checklist), just not built into calc-tab columns and example
rows. Business Income has no Legal Liability coverage type at all (structurally confirmed absent), so this
gap only applies to Building and Contents.

**Rating type (Class / Specific / Tentative).** Basic Group I only, now built for all three coverages
that have it (`Excel_Rater_BasicGroupI.md` §9, `Excel_Rater_BusinessIncome_BasicGroupI.md` §8) — confirmed
structurally absent from every other form. This one's done.

**Five known traps, already found, that any further tracing needs to carry forward** (from
`docs/CF-RATING-ENGINE-BUILD-PLAN.md`'s working non-negotiables — written for the engine track, but they
apply equally to anyone extending the rater docs):

1. Never treat a countrywide rate table as resolvable without checking row count — **22.4% of CF's
   countrywide tables are header-only**, and base-rate tables specifically are empty 58% of the time.
   This project's own rater docs have independently hit this same finding, table by table, throughout
   Building, Contents, and Business Income.
2. Never assume a jurisdiction's absence from the corpus is just a known, tracked gap — **Hawaii is
   missing from the ERC corpus entirely, in every edition, and was not on the manual side's known-gaps
   list until the ERC/circular comparison found it.** HI, ID, LA, MS, WA are all structurally absent.
3. CF's territory scheme is **county/place-name keyed in some states, ZIP-code keyed in others — not
   uniformly either one.** Corrected 2026-09-08: this was written as a blanket "county, not ZIP" rule
   from an early sample; a full 47-state pull for Basic Group II's `BasicGroupIIRatingTerr` found an
   almost even split — 11 states key their territory-derivation domain by ZIP code (CT, DE, MA, MD, ME,
   NC, NH, NJ, NY, RI, VA), 11 by county (AL, CO, FL, GA, IL, MT, NE, NM, SC, TX, WY), 24 need no
   derivation at all because they have only one territory (confirmed against each state's own
   `BasicGroupIIRate` table — every row uses the constant `"Entire State"`, not a gap), and one (PR) is
   moot because it files no base rate at all. Don't reuse GL's territory-resolution logic unmodified, and
   don't assume one CF coverage's keying scheme for another without checking — full per-state breakdown
   in `BGII_Territory_Derivation.xlsx` (`Spreadsheet_Rater/CF/Supporting Tables/`).
4. CF's multiply operator in the rule XML is `rul:Product`, not `rul:Multiply` — a naming trap for
   anyone grepping the raw files expecting GL's vocabulary.
5. **Edition-specific gaps are a different failure mode from corpus-wide ones.** FL, IL, and NJ are
   missing from the current (20260601) edition specifically but exist in earlier editions — don't
   conflate "missing from the one edition every rater doc so far traces" with "ISO doesn't file this
   state."

---

## 4. Circular verification — the thinnest leg

**Current state, precisely:** all 46 states + DC + countrywide are extracted to text (376 documents) and
L2-characterized (front matter read, exception-rule numbers identified). **Zero documents have reached
L3** — no rule's actual text has been compared line-by-line against what an `Excel_Rater_*` doc or a
`CauseOfLoss_*` doc claims. `ERC-VS-CIRCULAR-COMPARISON.md` is the one exception, and it's explicit about
its own limits: it compares two *analyses*, not two complete pictures, and covers one sampled path
(Building/Special's base-rate table) plus a jurisdiction census — not the four coverages this project has
since gone on to fully trace (Basic Group II, Broad, and all of Business Income postdate that comparison
and have never been checked against it).

**What closing this leg would actually require:** for each of the 15 rating paths already ✅-built in
`Excel_Rater_RatingPaths_Checklist.md`, read the corresponding manual rule text (already extracted, just
not yet read for this purpose) and confirm the formula this project traced from the ERC files matches
what's actually filed — the same L2→L3 promotion `Circular_Review_Tracking.md` already names as its own
next step, just pointed specifically at the paths this project has built a rater doc for.

---

## 5. Jurisdiction and edition breadth — not started

Every fact in every `Excel_Rater_*.md` document is sourced from one package: countrywide, edition
2026-06-01. This is deliberate and stated (`Excel_Rater_Overview.md` §3: "this pass assumes one LCM
applies... confirm against your state's actual ISO filing before using this for real business"), but it
means:

- **No state-specific override has been traced for any table**, even though nearly every countrywide
  base-rate table this project found is header-only and explicitly requires a state filing to resolve at
  all (`BasicGroupIRate`, `BasicGroupIIRate`, `LowestBasicGroupIIRate`, `SpecialBuildingRate`,
  `SpecialPrsnlPropRate`, `SpecialPrsnlPropTheftExclusionFactor`, `PrsnlPropTerrMultiplier`,
  `BaseRateAdjustmentFactor` — eight tables across the coverages built so far, all confirmed empty at CW).
  A rater that only ever resolves against the CW package cannot price most of what it claims to rate.
- **No edition-transition logic has been traced.** Which LCM, which table version, which effective-date
  rule applies to a given policy — genuinely untouched. `Policy.EffectiveDate` exists as a column
  (`Excel_Rater_Overview.md` §3) with a note that this pass "assumes one edition."
- **Five jurisdictions don't exist in the corpus at all** (§3 above) — a rater claiming full US coverage
  needs to either source those five states' rates from somewhere else or explicitly exclude them.

---

## 6. Feature-set backlog

Grouped by what each buys, not a flat queue — per this project's own standing convention.

**A. Promote the 📝 formula-only paths to ✅ built** (Legal Liability + blanket branches across every
already-traced form). *Buys:* complete premium calculation for every rating path this project has already
fully traced — no new ERC reading required, purely a documentation/workbook-column exercise. Cheapest
tranche, 20 paths per `Excel_Rater_RatingPaths_Checklist.md`.

**B. Trace blanket rating once, as its own mechanism.** *Buys:* unblocks the Blanket column across all 15
already-built rating paths simultaneously, since it's one shared piece of ERC logic (`SetBlanketValues`,
the blanket rating table scan), not fifteen separate ones.

**C. Add Special Class and Special Class Business Income to the rater-doc layer.** *Buys:* two more core
coverages, using algorithm docs that already exist — no new ERC tracing needed, just the
`Overview.md` + per-form-doc pattern already proven three times this session.

**D. Trace and build Earthquake and Flood.** *Buys:* the two largest standalone endorsement clusters (up
to 20 files and 5+ files respectively), currently zero ERC-algorithm coverage — genuinely new tracing
work, not a rater-doc-layer exercise like C.

**E. Trace and build Business Income's Agreed Value / Extended Period of Indemnity.** *Buys:* the
incremental-surcharge premium mechanism (`(Factor − 1) × Rate × Limit`), and — since Business Income's
Earthquake rate only ever charges premium through Agreed Value — this is also the only path to a working
Business Income Earthquake premium.

**F. The other ~90 endorsement families.** *Buys:* ERC-side completeness for the whole CF line. Largest
remaining backlog by count (Ordinance or Law: 18 families; Business Income time-element extensions: 17);
each needs its own algorithm doc traced before it can even reach the rater-doc layer, per
`Coverage_Inventory_And_Tracking.md`.

**G. Circular verification, L2 → L3, scoped to what's already ✅-built.** *Buys:* legal/regulatory
confidence that the 15 already-built rating paths match the filed manual, not just internal ERC
consistency — the leg with the least progress relative to its own stated importance (this project
explicitly adopted GL's rule that engine code doesn't start until this cross-check happens).

**H. Jurisdiction and edition breadth.** *Buys:* a rater that resolves for a real state and a real
effective date, not just the one CW-20260601 snapshot everything so far is scoped to. Table-by-table, this
is likely the single highest-value leg to close for anything built so far, since eight of the tables
already traced are known to be unresolvable without it.

**I. `cf-authority` build-out.** *Buys:* an automated, standing cross-check between the ERC and circular
sources — currently done by hand, once, in `ERC-VS-CIRCULAR-COMPARISON.md`. Blocked, by this project's own
stated logic, until both `cf-erc-expert` and `cf-circular-expert` are individually further along (the
former is now built per `docs/CF-PROPERTY-INTEGRATION-PROPOSAL.md`; the latter is still L2-only).

**J. The actual workbook (`.xlsx`) or engine (`cf_engine/`).** *Buys:* something runnable. Blocked
entirely on explicit authorization regardless of how complete A–I get — this project's standing rule, not
a scope gap.

**K. Wind/Hail *dollar* deductible option across the core coverages.** *Buys:* the ability to write a
separate wind/hail deductible as a flat dollar amount, not just as a 1%/2%/5% percentage — today the
core-coverage build-out only carries the percentage path. Traced 2026-09-15 while working Special Class
Basic Group II (`SetDeductibleFactorBasicGroupII` / `SetWindstormOrHailDeductibleFactor`): when
`WindstormOrHailDeductible` is a flat dollar value it reads `DeductibleFactor` keyed on the *wind/hail*
deductible rather than the main one, with `Deductible250Factor` handling the 250 case — a distinct branch
from the percentage lookup, and one the current docs don't cover for Building, Personal Property or
Business Income. Scope notes from that trace, which apply to whichever coverage this gets built for:
- **The filed dollar list is state-specific.** CW files 8 values (500 … 75,000); 43 states file 14, adding
  100,000 / 150,000 / 250,000 / 500,000 / 750,000 / 1,000,000. NY is the only state still on CW's 8.
- **Limit bands are state-specific too** — CW's second band is `50,000 < limit ≤ 100,000`, Ohio's is
  `50,000 < limit ≤ 175,000`. No shared band structure is possible.
- **Three states replace the mechanism**: RI and NC substitute a Named Storm percentage deductible
  (`NamedStormPctDeductibleFactor`, separate input field), PR uses a proportionate calculation with its
  own `WindstormDeductibleFactorPR`. All three need the dollar path checked separately.
- **Band operators differ between the two tables** — the dollar table is exclusive-from/inclusive-to, the
  percentage table inclusive-from/exclusive-to. Mixing them misprices risks sitting exactly on round-number
  boundaries.
Factor data for Special Class BGII is already extracted in
`SpecialClass_BGII_DeductibleFactors.xlsx`; the other core coverages read the same shared
`DeductibleFactor` table under a different `CauseOfLossDeductible` key, so the extraction pattern carries
over without new ERC reading.

**L. Special Class — Earthquake and Terrorism rate chains.** *Buys:* the last two untraced rate chains on
the Special Class item itself, which would complete the building side of the coverage. Both run inside the
same `SetBlanketRatesAndFactors` sequence already traced for Basic Group I / Basic Group II / Broad /
Special, so the entry points are known:
- **Earthquake** — `SetEQRatesAndFactors`, with supporting prep already visible in the traced chain
  (`SetEQCauseOfLossForm`, `SetEQDeductibleTier`, `SetEQTerr`, `SetEQSubLimitBlktIndicator`,
  `SetEQClassToUse`, `SetEQPublicInstitutionalPlanFactor`, `SetEQCauseOfLossAdjustment`). Premium is
  charged through the Earthquake endorsements, not a plain coverage file — there are four variants
  (`EarthquakeAndVolcanicEruptionEndorsementSpecialClass`, `...SubLimitForm...`,
  `...WithFlatDollarDeductible...`, `...SubLimitFormWithFlatDollarDeductible...`), plus
  `AgreedValEarthquakeCoverage` which carries its own `FinalEQRate` / `CyberIncidentExclusionFactorEQ` pair.
- **Terrorism** — `SetConditionalTerrorRate`, `SetPostTRIAExclusionRate`, `SetTerrorismPremium`, writing to
  `TerrorismFinalRate` / `TerrorismPremium` / `TerrorismSubLimitFactor` / `TerrorismCondExclFactor` /
  `TerrorismTerritoryTier` on the Special Class datadef.

*Scope note:* Earthquake is the larger of the two and shares `EQClass` / `EQTerr` machinery with Building's
Earthquake, so tracing it once likely serves both — same reasoning as item D, which scopes Earthquake and
Flood for the line generally. Terrorism is small and self-contained. Neither has any coverage in
`CauseOfLoss_SpecialClass_RatingAlgorithms.md` today. Identified 2026-09-15 while enumerating what applies
to Special Class after Basic Group I, Basic Group II, Broad and Special were traced.

---

## Remaining steps

1. You pick where to point next — this document doesn't recommend an order, it inventories what's
   available to choose from. B (blanket rating) has the widest single-tracing payoff; A is the cheapest;
   H is arguably the most consequential for whether anything built so far actually prices real business.
2. If circular verification (G) matters to you before more ERC-side breadth, that's a different kind of
   work (reading manual text, not tracing rule XML) and would want its own session framing.
3. Nothing gets built until you say go.
