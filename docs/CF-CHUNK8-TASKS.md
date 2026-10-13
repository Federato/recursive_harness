# Property chunk 8 — task list and status

**Legal Liability: Building and Contents, all four forms.** Opened 2026-09-18.

Derived from `CF_Algorithm/Excel_Rater_LegalLiability_vs_ClassRated_Building.html`
and `..._PersonalProperty.html` — which already carry an **eleven-point
divergence map** — and from the census run while opening the chunk
([`58_chunk8_census.py`](../scripts/cf/58_chunk8_census.py)).

**No engine code is expected.** Chunks 1–7 all ran on chunk 0's foundation
unchanged.

**Tracked live** as **C8-01 … C8-26**, numbered to match this page.

**All 26 tasks are done.** Chunk 8 is gated at **7 of 9** — point 8 held open on CA, FL and PR, point 9 owed project-wide ([`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md)). **Chunk 8 is gated at 7 of 9**, with point 8 deliberately held open ([`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md)). **No engine change was needed**, though chunk 8 produced the first serious candidate for one; see the golden-case page.

| Task | Cannot start until |
|---|---|
| C8-02 chain runs | C8-01 golden cases |
| C8-03 zero cases | C8-02 |
| C8-04 state sweep | C8-03 and **C8-14** (the branch-ordering claim) |
| C8-10 the fork | C8-01 |
| C8-08 ISO confirmation | C8-04 |
| C8-09 gate document | C8-03, 04, 05, 06, 07, 08 |

---

## What is structurally new, before any task runs

**1 · This is the first chunk where the divergence is already traced.** Chunks
4–7 opened by discovering a shape. Chunk 8 opens with an eleven-point map in
hand — so the first job is not to discover it but to **check it**, exactly as
C7-27 checked the Special Class Business Income reuse map. That check found our
own error last time; it may find the map's this time. **Both outcomes are worth
the same check.**

**2 · The fork is in `SetPremium`, not the rate chain — and it starts three
steps early.** Everything through `BasicGroupICauseOfLossAdjustment` is shared,
rule for rule and table for table. Then:

| | Class-rated | **Legal Liability** |
|---|---|---|
| Coinsurance, LOI factor | used | **computed and discarded** |
| Deductible factors | used | **never referenced** |
| Premium starts from | `FinalBasicGroupIRate` | **`BasicGroupICauseOfLossAdjustment`** |
| `LegalLiabilityFactor` | forced to 0.0 | **× 0.25** (Building) / **× 0.50** (Contents) |
| `MultiPremiumAndDispersionCreditFactor` | applied | **not applied** |
| Blanket | reachable | **unreachable** |

**Three whole rating concepts are computed and thrown away.** No chunk so far
has had a path that discards work it has already done.

**3 · Contents is double.** The same two-row `LegalLiabilityFactor` table, keyed
`"Bldg"` → 0.25 and `"PersProp"` → 0.50. One table, one key, twice the money.

**4 · The two sides gate on different fields at different LEVELS.** Building
tests `CovType` on the item; Contents tests `CovForm` **inherited from the
occupancy class**. So one Contents item cannot carry a different answer from its
siblings, and Building's can.

**5 · The census already contradicts one line of the map** — see below.

---

## The state layer — the quietest of any chunk

| Table | CW rows | States filing their own |
|---|---|---|
| `LegalLiabilityFactor` | 2 — Bldg **0.25**, PersProp **0.50** | **0 of 47** |
| `AddlInsurableInterestFactor` | 4 — Option1/2 **1.25**, Option3/4 **1.0** | **0 of 47** |
| `AdditionalInsurableIntOption` | **4** — the plain-language → Option map | **0 of 47** |

**Not one jurisdiction files its own copy of any of the three.** After six
chunks of state overrides this is the first coverage whose entire distinctive
data is countrywide-only.

**And only two jurisdictions rewrite any of the eight premium files:**

| | rewritten by |
|---|---|
| Building Basic Group II · Contents Basic Group II | **FL** |
| Building Special · Contents Special | **PR** |
| the other four | **nobody** |

**Branch ordering, checked in all 47 rather than read once:** Legal Liability
sits at **branch 2 in all eight countrywide files** and in all four state
copies — **0 files where blanket comes first**. The map's central structural
argument survives the check.

**One line of the map is stale.** It says the plain-language → Option mapping
*"ships empty in the current package"* and tells the builder to pull it from the
20191201 edition. **It is filed with four rows in the 2026 edition** — the four
above. C8-13 confirms and corrects it.

---

## Gate-level tasks

| # | Task | Status | Evidence |
|---|---|---|---|
| 1 | Golden case, hand-derived before code — Building and Contents, all four forms | ✅ | [`59_chunk8_golden_case.py`](../scripts/cf/59_chunk8_golden_case.py) — **Building $60 / $7 / $4 / $12, Contents $132 / $15 / $11 / $93**, all eight first clean run, and **$60 / $7 ISO-confirmed**. **Contents is exactly double** (C8-12 settled early), and the Special forms already show map point 6. Two prerequisites found the hard way: **`PolicyType` on the policy** (without it ISO's own rule *deletes* the submitted record) and **`CovForm` on the occupancy class** (map point 1, early). See [`CF-CHUNK8-GOLDEN-CASE.md`](CF-CHUNK8-GOLDEN-CASE.md) |
| 2 | Chain runs, on chunk 0's foundation, with no new interpreter node | ✅ | **No new interpreter node, and one near-miss worth recording.** The first run looked like an engine defect — a submitted record present before `Interpreter.run` and gone after. It was not: ISO's `AttachForm…` rule removes it when `PolicyType` is absent, and **the probe's two sides were built from different submissions**. **A control that passes without exercising the variable under test is not a control.** The engine was right throughout |
| 3 | Zero cases — including the two factors' 0.0 defaults | ✅ | [`61_chunk8_zero_cases.py`](../scripts/cf/61_chunk8_zero_cases.py) — 6 cases. **Two identical $0s from opposite causes** (an appended empty record vs a deleted submitted one). **Two cases predicted at $0 REFUSE instead, and both correct the map**: Leasehold Interest reaches `Power(0, 0)` because a submission is not a file, and Builders Risk leaves `Premium` **null** — the outer `If` has no `Else`, so **unwritten and zero are different things**. And the case that is *not* a zero returns a plausible **$223**. See [`CF-CHUNK8-GATE-3-5.md`](CF-CHUNK8-GATE-3-5.md) |
| 4 | 47-jurisdiction sweep, each premium predicted from that state's own rows | ✅ | [`62_chunk8_enumerate_states.py`](../scripts/cf/62_chunk8_enumerate_states.py) — **47 of 47, 43 with a real premium**. **The first version reported 47 of 47 and proved nothing**: it sent Oregon's territory to all 47, so 46 agreed at $0 — an empty search wearing a pass. Fixed by pinning the territory factor, which the rules `Copy` from the location. AZ is explained (C6-04); **CA, FL and PR are not, and are carried into C8-09** |
| 5 | Shared-name adjudication. **`SetLegalLiabilityFactor` and `SetLegalLiabFactor` are different names for the same idea in sibling files** — the exact shape gate point 6 exists for | ✅ | **7 shared names, 0 reading different tables — and passing did not test the thing that would hurt.** `SetLegalLiabilityFactor` and `SetLegalLiabFactor` never collide *because they are different names*, one per datadef group. **Gate point 6 catches one-name-many-tables; Legal Liability's trap is the inverse.** Recorded as a limit of the gate rather than a pass of it; C8-16 tests it directly |
| 6 | Exclusion records — Legal Liability shares Building's and Contents' rate chains, so it should share their exclusion records too. Confirm rather than assume | ✅ | **Legal Liability files no exclusion records of its own.** It is a *branch* of Building and Contents, not a coverage beside them, so it inherits both sides' records wholesale — vandalism, sprinkler leakage, wind/hail and theft, each in its own `PrsnlProp` variant on the Contents side |
| 7 | Hardcoded literals — the `"Bldg"` and `"PersProp"` keys, and the `CovType` / `CovForm` branch strings | ✅ | **`LegalLiabilityFactor.CovType` is pinned to `"Bldg"` — 1 of 2 filed values unreachable from every site that reads it.** The two-row table is one row per coverage, **each unreachable from the other**. Branch literals: `CovType` tested against `Legal Liability` 26 times, `Leasehold Interest` 31, `Builders Risk` 30 |
| 8 | ISO confirmation | ✅ | **3 confirmed, 1 payload-blocked, 1 divergence.** Broad **$4** and Special **$12** confirmed. **Blanket elected returns $0 on BOTH sides — and both contradict the map**, which argued it still rates as scheduled. **Builders Risk + reporting form: ISO RATES ($1) where we refuse** — OI-99's second instance, opposite in direction to Florida's. Contents' $132 is **unconfirmed**: ISO refuses the payload on a known wind/hail lookup |
| 9 | Gate document | ✅ | [`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md) — **7 of 9**, and **point 8 is held open on purpose**: CA, FL and PR produce no premium and the reason is not established. Three unexplained zeros is the shape chunk 6 taught us not to wave past |

## The fork — the chunk's central machinery

| # | Task |
|---|---|
| 10 | ✅ **The two paths agree on the cause-of-loss adjustment to the digit and disagree on every number after it.** Class 0074 moves both to 0.069, and the premiums to **$17** (Legal Liability) and **$75** (class-rated). Nothing between the adjustment and the premium is shared |
| 11 | ✅ **Two computed and discarded, and a third never reached — the map says three.** Coinsurance 80% moves the class-rated premium 261→274 and deductible 250 moves it to 279, while **Legal Liability stays at $60 through all of it**. But the **LOI factor comes back at 1** on this path (1.172 on the class-rated one): its setter is gated on the class-rated CovType, so it is never computed rather than computed and ignored. **A distinction invisible in the premium and visible in one field** |
| 12 | ✅ **$60 against $132 on the same risk**, factor 0.25 against 0.50. And **each lookup pins `CovType` to its own literal**, so Building can never read the PersProp row and Contents can never read the Bldg one — one table, two coverages, no overlap |
| 13 | ✅ **Four options, two values**: Option1/2 → 1.25 → **$75**, Option3/4 → 1.0 → **$60**, so half the distinction the submitter is asked to make costs nothing. **And the map is stale**: it says the plain-language → Option mapping ships empty and to pull it from the 2019 package — **the 2026 edition files four rows** |
| 14 | ✅ **The map's conclusion is right and its reason is not the operative one.** `CovType` is still `Legal Liability` and branch 2 **does** match — but the premium never reaches the `Choose`: `CoverageOnPolicyIndicator` is already **0**, because `CauseOfLossToUse` is copied from an **empty** `BlktCauseOfLossValue`. **That is the same overwrite C6-28 and C7-25 found — three chunks, three coverages, one mechanism.** ISO agrees at $0 |

## The eleven-point map, checked point by point

| # | Task |
|---|---|
| 15 | ✅ **Two Buildings on one location disagree — $60 and $261 — and two Contents items under one occupancy cannot.** The second item's `CovForm` request is overwritten by the occupancy's. **The gate is not just a different field: it is a different level, and the level decides who may differ** |
| 16 | ✅ **Neither record carries the other's name.** `LegalLiabFactor` on a Building record and `LegalLiabilityFactor` on a Contents record both read **None**. Nothing is shared but the idea — C8-05's blind spot, demonstrated rather than argued |
| 17 | ✅ **Contents carries a live 0.50 on a risk that is not Legal Liability at all** (`LegalLiabFactor` = 0.5 on a class-rated item), where Building's gated setter writes 0.0. **The fifth populated-and-unused factor in three chunks, and the first populated with a REAL value rather than a default** |
| 18 | ✅ **Point 1's consequence, one level in.** Contents' insurable-interest record on the ITEM gives factor 0 and premium **$0**; on the OCCUPANCY it gives 1 and **$132**. One Contents item cannot carry a different answer from its siblings here either |
| 19 | ✅ **The one that moves money, proven.** Theft excluded: **Building's Legal Liability Special stays at $12** (it reads the raw `SpecialRate`) while **Contents' falls $93 → $37** — `SpecialCauseOfLossAdjustment` keeps a 0.4 Offices credit. **One submission field, one of two coverages moving.** Both factors default to 1.0, which is why the golden case could not tell the rate sources apart |
| 20 | ✅ **All four Building forms read `../Limit`; Contents' Special reads a LOCAL `Limit`.** The map calls it deliberate on both sides, and it is at least consistent: the one form with a local limit is the one form whose rate source also differs (point 6) |
| 21 | ✅ **The outer `If` names the reporting form and has no `Else`** — which is why C8-03 case 4 refuses rather than returning 0. **And the census's addition holds**: only Building's **Special** tests `IncludedInBlkt` explicitly; Basic I, Basic II and Broad reach blanket by elimination. **One coverage, two mechanisms, and the map describes only one** |

## Cross-form claims

| # | Task |
|---|---|
| 22 | ✅ **Second instance of a populated-and-unused field.** Factor 0.5 halves the class-rated premium 261 → **131** and **Legal Liability stays at $60**. Chunk 5 found the same field unused on Business Income |
| 23 | ✅ **The map is wrong: the operand order IS premium-bearing.** PackageMod and IRPM both at 0.44 give **$11** nested; a single product gives 11.616 → **$12**. One dollar. **The map verified the operands and not the arithmetic** — and the first run of this test applied only one factor, because **IRPM is read from the POLICY**, five levels up |
| 24 | ✅ **Both are correct outcomes and neither is a zero in our engine.** Leasehold Interest refuses (it activates chunk 11's rate chain); Builders Risk + reporting form refuses here and **ISO prices it at $1**. The map records both as `Premium = 0.0`. Named so a future reader does not chase them |
| 25 | ✅ **Predicted 'none of them moving' and Contents moves, $223 → $248.** The Building's `CovType` suppresses **Contents'** LOI factor (0.898 → 1) on a coverage that is still class-rated — **the fork is not confined to its own premium.** Business Income keeps $112 (it reads the RATE chain, which the fork does not touch) and both Special Class coverages are untouched because they hang off the location. **Only the coverage nested INSIDE the building follows it** |
| 26 | ✅ **8 of 11 confirmed, 3 corrected**, plus four further findings: a stale line, an over-claim, and two things the map does not mention — one of them the cross-coverage leak above. **This was the best-prepared input any chunk has started from** and running it moved five points. Every correction is a place where the rules said one thing and the arithmetic said another |

---

## What chunk 8 inherits and must re-ask

* **OI-99** — ISO refuses where we return $0. Chunk 8 has **three** correct-zero
  paths (Leasehold Interest, Builders Risk with a reporting form, and the two
  factors' 0.0 defaults), so it is the best chunk yet for asking which zeros ISO
  tolerates.
* **Gate point 9** — chunk 7 was the first chunk where ISO's message count did
  not match the engine's. Watch it here.
* **OI-100** and **C7-12's filtered enumeration** — both are built into the
  census from the start.
* **The chunk 6 lesson about harnesses that manufacture findings.** The first
  branch-ordering detector written for this census reported the map
  contradicted; it was the detector that was wrong, twice. Fixed before
  anything was published.
