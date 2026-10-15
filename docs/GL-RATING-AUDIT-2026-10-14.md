# GL rating audit — what is not configured (14 October 2026)

**Asked:** a full audit of GL rating, including composite, schedule and experience rating, listing what has not been
configured. **Method:** every rating path ISO's content declares, checked four ways — does the engine run it; can our
request builders (`console/workbench.py`, `scripts/variants.py`) set it; has ISO's service ever priced it for us; is it
tested. Evidence: 326 stored GL ISO answers (`results/tc/answers`) plus ISO's 50 example pairs, the run store
(`results/runs-*.jsonl`: L3 Limits 598 matches in 50 states, classification 50, QA tiers), August's breadth runs
(OI-87, OK and NY), and ISO's 576 GL sample submissions (inputs only — no answers).

**Already proven, not listed:** Premises/Operations and Products in 50 states; limits (598 ISO matches, 50 states);
the 15 priceable coverage families (B-13); the four main premium bases across 8 states (B-12); terrorism; the
corpus resolves to ISO's package in 100 of 100 state × edition combinations (B-38).

"Configured" below means: the builders can set it, and ISO has priced it for us at least once.

## A · Rating plans and modifiers

| # | Item | Engine | Builders | ISO evidence | Gap |
|---|---|---|---|---|---|
| A1 | **Experience rating** | Rates ISO's 11 experience-rated samples: modification 0.789–0.951, credibility 0.08–0.34 | `experience_rating` sets only `ExperienceRatingApplies`; none of the 44 ERP inputs (years, losses, YIP, policy history). Switched on alone it does nothing (credibility 0) | **None** | Builder for the ERP inputs; ISO comparison **Done 2026-10-15 (B-40): builders write the ERP period; ISO 10 of 10 exact (credit, debit, 1-3 years, OK/FL/NY, 2027).** |
| A2 | **Schedule rating on Prem/Ops** | Runs; capped at ±25% (R15, ISO-confirmed) | `schedule_rating`, `schedule_pct` | Liquor (AL), OK, NY, NE — never Prem/Ops with experience on | On Prem/Ops it applies only when experience credibility ≥ 0.03 (OI-89), so it has never been exercised there; needs A1 first **Done 2026-10-15 (B-41): ISO 7 of 7 exact, incl. the cap both ways and the 0.03 gate.** |
| A3 | **Composite rating** | Rates ISO's 2 composite samples (WV liquor: $764 of classes re-expressed to $255 at the audited exposure) | **No control** | **None** | Builder; ISO comparison **Done 2026-10-15 (B-42): control added; ISO 8 of 8 exact (above, below, equal, 0, multi-class, 2027, FL, NY).** |
| A4 | **R16 refers every composite risk whose audited exposure is below the estimate** | The composite adjustment is negative by design (WV sample: −$509); R16 reads any negative premium as a defect | — | — | False referral: exempt the composite adjustment. **Fixed 2026-10-15 (B-39)**; re-measured, the WV sample gives 743 → 248, −495 |
| A5 | **Package modification factor** | Applies (0.9 → TX $7,036) | **No control** | **None** | Control; ISO comparison **Done 2026-10-15 (B-43): ISO 8 of 8 exact.** |
| A6 | **How the modifiers combine** (`ModToUse`, experience × schedule × package) | Runs | — | Only ever one at a time, each at 1 except schedule | ISO comparison with two or more on **Done 2026-10-15 (B-43): ISO 8 of 8 exact.** |
| A7 | **Modifiers on endorsement premiums** | 281 endorsements are the carrier's manual premium × the rating mods | — | The manual-premium mechanism is proven (8 endorsements), always with mods at 1 | ISO comparison with a mod ≠ 1 **Done 2026-10-15 (B-43): ISO 8 of 8 exact.** |

## B · Rating paths

| # | Item | Engine | Builders | ISO evidence | Gap |
|---|---|---|---|---|---|
| B1 | **Size-of-risk** | Rates where filed (OH, CO); refuses in the 14 states with no size-of-risk loss costs (R10); R26 refers the cannabis zeros | `size_of_risk` | **None** | ISO comparison in a filing state **Done 2026-10-15 (B-44): ISO 10 of 10 agree, refusals included; rates in 35 states on 2026-10, only NJ and WA on 2027.** |
| B2 | **Claims-made** | Runs | `coverage_form`, `claims_made_year` | OK and NY, two maturities (August); 87 ISO samples unpriced | Years 3–5+, retroactive dates, more states |
| B3 | **Multi-location / multi-class** | Runs | `locations`, `classifications` | OK and NY, 2 locations / 2 classes (August); none in the stored answers | More states; 3+ locations / classes; mixed bases |
| B4 | **Territories** | Runs (place-coded CA, FL, NY, TX proven, E8) | Location territory | At most 2 per state; 10 of 50 states with more than one | A territory sweep (e.g. OH files 10) |
| B5 | **Class codes and premium bases** | Runs | `class_code`, `premium_basis` | 17 of ~1,160 class codes; 6 of ~60 bases | The long tail: Admissions, Gallons, Acres, per-student, the "Number of …" bases |
| B6 | **Deductibles** | Runs | 6 deductible controls | Stored: only "250 Per Occurrence"; August: 6 shapes in OK and NY | Per Claim, BI / PD split, large deductibles, more states |
| B7 | **Company-rated classes** (ELP override, ILF table override) | Runs; missing overrides refuse (B-07); R29 refers on ISO's message | Not in `variants` | **None** | ISO comparison with the overrides supplied **Done 2026-10-15 (B-45): ISO 6 of 6 exact with the overrides supplied; only 54444/94444 refuse without them, the rest price the ELP part $0 and refer (R29).** |
| B8 | **As-of dates** | Resolver covers every edition in force from 2022-09 | `effective_date` | Essentially two dates (2026-08-01, 2027-05-01) | The other editions in force, e.g. early 2026 and the 2026-10 / 2027-01 packages |

## C · By design, or tracked elsewhere (not gaps)

| Item | Where |
|---|---|
| Company LCMs and carrier deviations | ISO only ever rates technical (D21); proved by the deviations tests (RC-4) |
| Minimum premiums | ISO files every minimum at $0; a carrier's minimum is a deviation (RC-4) |
| Hawaii, Puerto Rico, pro-rata / transactional premium, multi-state requests | RC-6 B-26; multi-state refuses by design |
| Forms | `docs/BACKLOG-FORMS.md` |

**Suggested order:** A4 (a false referral, small), then A1 → A2 (experience unlocks Prem/Ops schedule), A3, A5–A7
together (one modifier request set), then B1, B7, B2, B3, B6, B4, B5, B8 as ISO budget allows.
