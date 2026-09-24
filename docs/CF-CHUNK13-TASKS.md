# Property chunk 13: task list and status

**Terrorism / TRIA.** Opened 2026-09-24.

Derived from [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) item 13
and from the opening census
([`143_chunk13_census.py`](../scripts/cf/143_chunk13_census.py), run
2026-09-24).

**Standing rules carried in.** Analysis and gates only: no engine code
without the user's go. "All states" means the **46**; Puerto Rico is
excluded. Live ISO comparisons are sent at **2026-09-17** until OI-105 is
ingested.

**Status: OPEN 2026-09-24, 5 of 30 tasks. RC-1 COMPLETE** (C13-01 census, C13-02 rule order, C13-03 replay, C13-04 operand types, C13-05 attach map). Next: RC-2, the golden case. **OI-111 fixed 2026-09-24 with the user's authorization** (10th engine fix): replay 14 of 14, regression clean; `144_`/`145_` now in the regression.

---

## In plain English first

Terrorism isn't a coverage of its own. It's an **extra premium charged on
every coverage the policy already has** (building, contents, business
income, special class) for losses caused by terrorism. A federal program,
TRIA, backs it, and TRIA has an expiry date. So each coverage's terrorism
premium is split into the part **before** TRIA expires and the part
**after**, and the "before" part is prorated by the days left.

The charge starts from a **terrorism loss cost** that each state files by
territory. Five **exclusion or limitation forms** then change it: exclude
it entirely, cap it, exclude only nuclear/biological/chemical, or cover it
up to a sub-limit. Which forms attach depends on a few policy answers (is
terrorism covered, is TRIA in effect or expiring, conditional exclusion yes
or no).

## What the census found, before any task ran

| Where | Count | What it is |
|---|---|---|
| Terrorism-**named** rule files (countrywide 2026) | **17** (build order said 16) | 13 form files with rules but no premium, 3 inert detail files, 4 with a `SetPremium` (3 disclosure forms and PostTRIA). Older parents (20230801 V01–V03) have 14 |
| Terrorism rules **embedded** in core files | **108** | policy 23 (13 form attachments, 3 stat codes), location 9 (territory tier, loss costs), and **each of the five coverage groups 11–19**, each with its own `SetTerrorismPremium`, `SetPreTRIAPremium`, `SetPostTRIAPremium` |
| Rate tables | **6** | `TerrorismLossCost`, `TerrorismTerritoryTier`, `TerrorismNBCExclFactor`, `TerrorismSubLimitFactor` are **header-only countrywide**, filed by 44–46 states. Two stat-code tables, 1 row each |
| States that really change a terrorism rule | **20 of 46** | FL (32 rules), NY (34), AK (20, its own Alaska forms). **15 states file a "fire exception" factor**: AZ CA CT GA IA MA ME MO NC NJ **OR** RI VA WI WV (**Oregon, the golden-case state, is one**). IL validates territory against ZIP/county. AZ files its own CP 09 01 amendment. CT, MA, VA rewrite the premium rules. CA, TX: CP 00 70 messages |
| PostTRIA coverage | 8 states | AK CA DC FL IL MD NY VA |
| ISO STC fixtures | **354 of 364 elect terrorism** (`TerrorismIndicator` Yes) | 345 "TRIA in effect", 10 "will expire", 5 "already expired", 4 "expired, conditional forms". 11 carry a conditional exclusion, 6 a sub-limit above 0 |
| Stored ISO responses | **14 carry a non-zero `TerrorismPremium`** | none of our comparers has ever looked at that field |
| Engine readiness by element name | every element implemented | date arithmetic present: `DateDifference` (the OI-107 field), `DateCreate` ×2, `DatePart` ×6 |

**Three things that shape the plan:**

1. **The engine has been computing terrorism all along, unchecked.** Every
   element is implemented, so any submission that elects terrorism already
   gets a terrorism premium from our engine, and no gate has ever looked at
   it. The 14 stored ISO responses are free evidence, so they come first.
2. **"Reads other groups' finished premiums, so it runs last" looks wrong.**
   Each coverage's terrorism premium reads **its own record's** factors
   (protection class, coinsurance, deductible) and its own pre/post split,
   not another coverage's premium. C13-02 settles it, because it decides
   whether chunk 13 depends on chunk 14 or the reverse.
3. **Oregon has the fire-exception factor**, so the golden case can't dodge
   the state layer. That's good: the first case proves a state mechanism.

---

## Task groups, in priority order

Grouped like the rater's release candidates: each group is a shippable step,
and the order is the order to do them in. **Gate** names the points a task
closes.

### RC-1 · Free evidence and readiness (5 tasks) — ✅ COMPLETE 2026-09-24

| # | Task | Status | Notes |
|---|---|---|---|
| C13-01 | **Opening census**: named files, embedded rules, tables, states, fixtures, elements | ✅ | **Done 2026-09-24** (`143_chunk13_census.py`). Findings above |
| C13-02 | **Rule order and dependency**: where terrorism runs in `ErcProcess`/`ErcRate`, and whether anything reads another group's finished premium. Settles the build order's "runs last" claim | ✅ | **Done 2026-09-24** (`144_chunk13_c13-02_rule_order.py`, clean in all 5 parent editions). **The claim is half right.** Each coverage record computes its own Pre-TRIA, Post-TRIA and terrorism premium at the end of its own `ErcRate`, from its own factors only, so no coverage depends on another. But no coverage total includes that premium: a **policy-level roll-up record** (one of three disclosure forms, or PostTRIA) sums `TerrorismPremium` over every coverage record at every location, and that is what enters the policy total. The roll-ups run at steps 48–50 and 57, after the last location (41). The `Zz` prefix is how the forms sort last. CA, DC, IL, MD, NY and VA add a `TerrorismCapStatePremiumCheck` after the roll-up (→ C13-19/20) |
| C13-03 | **Replay the 14 stored ISO responses** with a non-zero `TerrorismPremium` through our engine, and compare the terrorism cells only. No ISO calls needed | ✅ | **Done 2026-09-24** (`145_chunk13_c13-03_replay.py`). **Every per-coverage terrorism premium in all 14 agrees with ISO** (Pre-TRIA, Post-TRIA, total; building, contents, business income; GA, MO, NC, NY, CA, AK, WY). **12 of 14 agree completely.** The 2 that differ are CA's disclosure roll-up: ISO $153, ours $0, because CA's 25% cap reads the policy total through `ancestor::CommercialProperty` and our engine reads every `ancestor::` as the root → **OI-111** (**fixed 2026-09-24 with the user's authorization; now 14 of 14, regression clean**). A named-ancestor reading, tested in the probe only (`146_…`), gives 14 of 14. Also found and fixed **in the replay, not the engine**: ISO sends PostTRIA as a single record the rules address without a table; the chunk 12 converter wrapped it, so AK's $20 and WY's $2 read as absent until the replay unwrapped rule-addressed singletons |
| C13-04 | **Operand types** over all 125 rules (17 named files + 108 embedded), with dates first: `DateCreate`, `DatePart`, `DateDifference` | ✅ | **Done 2026-09-24** (`147_chunk13_c13-04_operand_types.py`). **Clean.** 3,054 operators across 1,969 terrorism rules (5 parent editions + every state layer): every signature is one the engine handles, no undeclared type. Dates are confined to one rule, `SetDaysUntilTRIAExpiration` (DatePart ×6 → DateCreate ×2 → DateDifference, per edition). Live, one ISO fixture per `TRIAType`, all four run, and the timeline equals the hand derivation, **including the prorated branch** (TRIA 2027-06-01: 257 days, factors 0.70 / 0.30); the fixture's own 2023 date only reaches the 0 branch, so the prorated case was added. **Edge for C13-13:** the 30 `DatePart` reads fall back to `01/01/0001`, which our engine reads as null and refuses; reachable only with a blank `EffDate` |
| C13-05 | **The attach map**: which answers (`TerrorismIndicator`, `TRIAType`, `TRIAConditionalExclusion`, `PostTRIAExclusion`, `TerrorismSubLimit`) attach which of the 17 forms (`TerrorismFormsConditionalLogic`), and what, if anything, deletes one | ✅ | **Done 2026-09-24** (`148_chunk13_c13-05_attach_map.py`, in the regression, ~6½ min). **Clean.** `ErcDoConditionalMandatoryLogic` → `TerrorismFormsConditionalLogic` runs 13 attach rules; each **attaches its form when the answers call for it and REMOVES it otherwise**, with no message. Transcribed map checked against the engine on **168 answer combinations × 2** (no forms submitted / all 13 submitted): attach, delete and the PostTRIA indicator all match. **What drives it: `TRIAType`.** Blank → no terrorism form at all, and submitted ones are deleted. In effect → Disc-TRIA + one IL 09 52/53/86/87 by `CoverageForCertifiedActs`. Will expire / expired-conditional → a cap form + IL 09 95/96/97 by `TRIAConditionalExclusion` + a premium disclosure by `ConditionalExclusionRatingOption`. Post-TRIA → IL 00 30/31/32 by `PostTRIAExclusion`. **`TerrorismIndicator` switches nothing** (read only by two CP 00 70 messages): 'No' with TRIA in effect still attaches Disc-TRIA → a live ISO question for C13-24. **AK, FL, NY attach differently** (12, 20, 20 of 21 sampled combinations; FL and NY attach the in-effect disclosure when TRIA will expire) → C13-19. My first transcription missed each test's `IsNotNull TRIAType`; the engine was right |

### RC-2 · The golden case (4 tasks) — gate 1

| # | Task | Status | Notes |
|---|---|---|---|
| C13-06 | **Golden case, Building, Oregon, TRIA in effect.** Chunk 2's building plus terrorism elected. Hand-derive before running: territory → tier → loss cost (program year 3 and full) × LCM → TRIA rate → × fire-exception factor × protection class × coinsurance × deductible → pre/post split → premium | ⬜ | **gate 1**. Includes Oregon's fire exception |
| C13-07 | **Live ISO on the golden case**, and on the same case with TRIA expiring (257 days → factor 0.70) | ⬜ | **gate 1** |
| C13-08 | **The other four coverage groups**: Contents, Business Income, Special Class, SC Business Income. Each has its own factor set (Contents 19 rules, BI 11) | ⬜ | **gate 1** per group |
| C13-09 | **The four premium-bearing named files**: what the three disclosure forms' and PostTRIA's `SetPremium` produce, and how they relate to the per-coverage premiums | ⬜ | Chunk 1 found `TerrorismPremium` never written at the policy level |

### RC-3 · The mechanisms: TRIA timeline, forms, sub-limit, zeros (6 tasks) — gates 4 and 5

| # | Task | Status | Notes |
|---|---|---|---|
| C13-10 | **The TRIA timeline**: all four `TRIAType` values (in effect, will expire, expired and use post-TRIA forms, expired but use conditional forms) through `DaysUntilTRIAExpiration` and both proration factors | ⬜ | OI-107 lives on this path |
| C13-11 | **The five exclusion/limitation forms** and `TRIAExclFactor`: cap (1.0), fire losses (0.0), nuclear/biological/chemical (state factor), sub-limit (state factor), conditional | ⬜ | |
| C13-12 | **Sub-limit**: `TerrorismSubLimit` 5–100%, `TerrorismSubLimitFactor`, and its four messages | ⬜ | 263 fixtures carry the field, only 6 above 0 |
| C13-13 | **Zero cases**: not elected, no disclosure record, blank territory, TRIA expired, sub-limit 0, fire-excluded, no loss-cost row | ⬜ | **gate 4** |
| C13-14 | **The override**: `TerrorismOverride` Yes with a submitted `TerrorOverridePremium` bypasses the rating by design. Record it as a submission rule, and check the pre/post split of an overridden premium | ⬜ | The "submitted value wins" shape, here intended |
| C13-15 | **Literals**: every `TRIAType`, `TerrorismTerritory` and form literal the rules test, checked against the Domain Tables | ⬜ | **gate 5** |

### RC-4 · The state layer (7 tasks) — gates 2, 3 and 8

| # | Task | Status | Notes |
|---|---|---|---|
| C13-16 | **Tables**: row counts per state for the 4 state-filed tables; name the states that file none (44 of 46 file NBC and sub-limit factors) | ⬜ | **gate 2** |
| C13-17 | **Territories**: every state's `TerrorismTerritory` values → tier, all 46; IL's ZIP/county validation messages | ⬜ | |
| C13-18 | **The fire-exception states** (15, including OR): the factor, its table, and one priced case outside Oregon | ⬜ | |
| C13-19 | **FL, NY and AK**: FL 32 and NY 34 rule rewrites, AK's own Alaska forms (20 rules) | ⬜ | The three heavy states |
| C13-20 | **The rest of the 20**: CT, MA, VA premium rewrites; AZ's CP 09 01 amendment; CA and TX CP 00 70 messages | ⬜ | |
| C13-21 | **PostTRIA coverage** in its 8 states (AK CA DC FL IL MD NY VA): price it | ⬜ | |
| C13-22 | **All-46 sweep and edition basis**: the golden building's terrorism premium in every state, predicted from that state's own rows; and what the 3 extra named files in V04/2026 change against V01–V03 | ⬜ | **gates 3, 8** |

### RC-5 · Confirmation and close-out (8 tasks) — gates 6, 7, 9

| # | Task | Status | Notes |
|---|---|---|---|
| C13-23 | **Fixture sweep**: convert the 354 terrorism-electing ISO fixtures (`to_engine`) and rate them; compare `TerrorismPremium` live on a sample chosen so competing rules predict different answers | ⬜ | Probes must be able to disagree |
| C13-24 | **Live ISO** on the zero cases, the timeline, the forms and one case per state mechanism | ⬜ | **gate 9** |
| C13-25 | **Shared names**: terrorism fields on the policy, location and five coverage groups (same names, different records) | ⬜ | **gate 6** |
| C13-26 | **Exclusion records**: reconcile with chunks 4–5's "ten terrorism families, each one policy-level record across 5 groups" | ⬜ | **gate 7** |
| C13-27 | **Messages**: every terrorism `DoMessage` surveyed against the golden cases (incl. NY's dead 25% rule from chunk 1) | ⬜ | **gate 9** |
| C13-28 | **Stat codes**: the three stat-code rules and two tables; record that they carry no premium, or hand them to chunk 14 | ⬜ | |
| C13-29 | **Regression**: add chunk 13's golden cases and gate scripts to `104_…regression.py`; clean for chunks 0–13 | ⬜ | |
| C13-30 | **File `CF-CHUNK13-GATE.md`**: nine points, every coverage group | ⬜ | |
