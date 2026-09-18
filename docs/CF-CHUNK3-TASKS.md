# Property chunk 3 — task list and status

**Building: Broad and Special.** Opened 2026-09-17, **gated 2026-09-18 at 8 of 9** — see [`CF-CHUNK3-GATE.md`](CF-CHUNK3-GATE.md). All 24 tasks closed, no engine code written.

Broad is the **shortest chain in the coverage — 6 steps**. Special is 9 but
structurally the simplest: its base rate is a flat statewide constant with no
class, construction, territory or symbol.

Each form gates its base rate on `CauseOfLossToUse`, so chunk 3 needs a separate
submission per form — unlike chunk 2, which stacked Group II onto chunk 1's
submission and got two premiums from one building.

**They are cumulative with Basic, not alternatives to it** — established here,
against an expectation that said otherwise. See task 23.

| # | Task | Status | Evidence |
|---|---|---|---|
| 1 | Golden case, hand-derived before code — one per form | ✅ | `15_chunk3_golden_case.py` — Broad **$16**, Special **$54**, both exact on the first run, both ISO-confirmed |
| 2 | Chain runs | ✅ | again with no engine code |
| 3 | Zero cases | ✅ | `16_chunk3_zero_cases.py` — 5 cases, both forms. **Two predictions wrong**; see [`CF-CHUNK3-ZERO-CASES.md`](CF-CHUNK3-ZERO-CASES.md) |
| 4 | 47-jurisdiction sweep, each premium predicted | ✅ | `17_chunk3_enumerate_states.py` — **Broad 47 of 47, Special 47 of 47**. FL and PR rate by their own overriding rule; see [`CF-CHUNK3-STATE-SWEEP.md`](CF-CHUNK3-STATE-SWEEP.md) |
| 5 | Shared-name adjudication | ✅ | `04_shared_names.py` extended — **9 of 9 adjudicated**, and the check itself was found blind: see [`CF-CHUNK3-SHARED-NAMES.md`](CF-CHUNK3-SHARED-NAMES.md) |
| 6 | Exclusion records | ✅ | `05_exclusion_records.py` extended + `18_chunk3_theft_exclusion.py` — theft priced $54 → **$47**. The census was missing theft entirely; see [`CF-CHUNK3-EXCLUSION-RECORDS.md`](CF-CHUNK3-EXCLUSION-RECORDS.md) |
| 7 | Hardcoded literals | ✅ | already covered — the census scans the whole Building coverage |
| 8 | ISO confirmation | ✅ | `19_chunk3_raas_sweep.py` — **7 calls, 7 matches**, message counts equal too. FL Special $38 confirms the state-override reading; see [`CF-CHUNK3-ISO-CONFIRMATION.md`](CF-CHUNK3-ISO-CONFIRMATION.md) |
| 9 | Gate document | ✅ | [`CF-CHUNK3-GATE.md`](CF-CHUNK3-GATE.md) — **8 of 9**, point 9 outstanding on chunks 1, 2 and 3 alike |

## Broad-specific

| # | Task |
|---|---|
| 10 | ~~**No cause-of-loss adjustment step at all**~~ ✅ defined in **0 of 47 + CW**; nothing substitutes, and `AdjustedBroadRate` matches the four-term product exactly |
| 11 | ~~**Roof-surfacing ACV folded into `SetAdjustedBroadRate`**~~ ✅ position confirmed — and **the factor cannot move a Broad building premium in any jurisdiction** (0 of 6 filed base rates survive the rounding), while Paragraph B's filed 0.99 is **unreachable** |
| 12 | ~~**No Broad deductible-by-location rule**~~ ✅ three rules, one record, three gates — shared 0.995 for Broad, Group II and Special both stay 1.0. No interference |
| 13 | ~~**The two-tier base rate**~~ ✅ $16 / $12 on the two tiers — and **`ConstructionType` is a 25-value domain, not the six rating names**; submitting `Joisted Masonry` prices at zero in silence |
| 14 | ~~**Class `1150` routes to the `BldrRisk` rows**~~ ✅ flat 0.012 — and it **also removes coinsurance** via a second rule that independently hardcodes `1150`, so the premium is $15 not $14 |
| 15 | ~~**`ConstructionTypeToUse` is a gate**~~ ✅ proven by zero case Z1 — blank ⇒ Broad 0, Group I 0, Group II 0, **Special still 54** |

## Special-specific

| # | Task |
|---|---|
| 16 | ~~**`SpecialBuildingRate` is header-only countrywide**~~ ✅ answered by the sweep, and the premise needed correcting: 45 of 47 file it, and **FL and PR are not unrateable — they override the rule** to read `SpecialBuildingRateNonResidential`/`Residential` (FL) and `SpecialBldgRate` (PR) |
| 17 | ~~**`SpecialBuildersRiskRate` carries a countrywide row**~~ ✅ class 1150 → 0.015 → **$18**; rows resolve **47 of 47** for Builders Risk against **45 of 47** for the building path — and the two missing are FL and PR, the same two that override the rule |
| 18 | ~~**Theft exclusion (CP 10 33)**~~ ✅ indicator 0→1, factor 1.0→**0.88**, Special $54→**$47** exact on the first run, Broad unmoved at $16 |
| 19 | ~~**Two amount-of-insurance sums used only as deductible keys**~~ ✅ four cases — 0.97/$54, 0.89/**$50**, equal-deductible gate, and **excluding theft makes a separate theft deductible irrelevant** ($47). Telling the two sums apart numerically needs Contents — logged for chunk 4 |
| 20 | ~~**`SetSpecialCauseOfLossAdjustment` has no `IsNull` guard**~~ ✅ re-entry is idempotent — **and the finding is the reverse of the worry**: every *guarded* rule honours a value supplied in the payload, so a submitted `SpecialBaseRate=9.999` prices at **$11,398** with nothing raised. The unguarded rule is the safe one |

## Shared between the two

| # | Task |
|---|---|
| 21 | ~~**Broad and Special share one LOI table**~~ ✅ held across all 47 — and PR, the one jurisdiction filing its own, moves both forms together |
| 22 | ~~**`SetSpecialBaseRate` and `SetSpecialTheftExclusionFactor`**~~ ✅ both confirmed, and `SetSpecialBaseRate` is **wider than documented — 5 tables across 16 datadef groups**. The method failed its first real test: the check could not see either case until it was made transitive |

## Cross-form

| # | Task |
|---|---|
| 23 | ~~Verify the forms are mutually exclusive.~~ ✅ **The premise was wrong — they are CUMULATIVE.** See below |
| 24 | ~~**Re-confirm the override pattern**~~ ✅ **the opposite of chunk 2**: 0–3 of 47 override any chunk 3 rule, against 39 of 47 for `SetBasicGroupIIRate`. Census in [`CF-CHUNK3-STATE-SWEEP.md`](CF-CHUNK3-STATE-SWEEP.md) |

---

## 23 · The forms are cumulative, not exclusive

The task was written expecting a possible **double count**: Broad and Special
gate their base rate on the cause of loss, Group I's rate chain does not, so
Basic pricing alongside Broad looked like it could be an error.

**ISO settles it — they layer.** Same Oregon building, three cause-of-loss
selections:

| `CauseOfLoss` | Basic I | Basic II | Broad | Special | policy total |
|---|---|---|---|---|---|
| `Basic` | 261 | 32 | 0 | 0 | **293** |
| `Broad` | 261 | 32 | **16** | 0 | **309** |
| `Special` | 261 | 32 | 0 | **54** | **347** |

The engine matches all three, coverage by coverage **and** on the policy total.

And it is the right insurance reading: a Broad cause-of-loss form *covers* the
Basic Group I and II perils and adds to them, so the premium builds up in layers
rather than swapping. The cause of loss gates only the Broad and Special
increments; Basic rates whenever class, construction and territory are present,
because those perils are always in force.

**A side benefit worth noting:** this is the first check of policy-level
aggregation, which is chunk 14's job. `ErcCalculatedTotalPremium` sums the
coverages correctly at three different totals.

---

**23 was the one to watch, and it has been answered** — the first task in the
project that could have revealed a *double count* rather than a zero. Everything
found so far (Arizona's reduction credit, an unrecognised construction type, an
absent BCEG, a missing Group II rating type, a missing Group II territory) has
failed *toward* zero, which is conservative and loud in a comparison. A form
pricing when it should not is the opposite, and no single-figure premium
comparison would necessarily catch it.

It turned out not to be a defect at all — but only because it was asked. The
habit that caught it is the same one that caught Arizona: predict, assert, and
treat the disagreement as the finding.
