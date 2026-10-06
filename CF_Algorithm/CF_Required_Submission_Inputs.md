# CF — required submission inputs, by coverage

> **Reconciled against the built engine on 2026-10-02 (commit 630ba2f; chunks 1–27 gated).**
> Confirmed by checking every row against the chunk 1–27 gate and task docs, `docs/OPEN-ITEMS.md`
> and chunk 28's refusal table, re-running the chunk 3 / 5 / 8 zero-case scripts offline
> (`16_`, `33_`, `61_`: all exit 0, figures as stated below) and re-counting the 2026 ERC
> `EarthquakeDeductibleTier` tables. Rows that drifted are marked **(updated 2026-10-02)**; inputs
> established by chunks 11–27 are summarised in the new section near the end.

**A rules-first reference, not a rater-export reference.** This catalogs every
field the ISO ERC rules themselves treat as a genuine submission input —
confirmed by reading the rule XML directly, chunk by chunk — as opposed to
`CF_Algorithm/CF_Payload_Generator_RESUME.md`'s separate, active effort to
reproduce `CFRater1.01.xlsb`'s own field set as an ISO payload. The two do
not conflict; this one answers "what does the ERC rule set require,"
independent of any one rater workbook.

Compiled 2026-09-22 from every closed chunk's own gate/tasks/golden-case
docs (chunks 1–10). Nothing below is inferred beyond what those docs
explicitly state — where a chunk's docs did not settle a field's status, it
is listed in the "ambiguous" appendix instead of being asserted.

---

## The three categories, and why the distinction matters

A submission builder needs to know, for each field, not just "is this
required" but *what happens if it's wrong or missing* — because this
project has found at least three distinct failure shapes, and they look
identical from the outside (a $0 premium, no error) unless you already know
which one you're looking at.

1. **Pure input.** No rule anywhere in the corpus ever assigns this field a
   value — confirmed by a corpus-wide `ToDataDef` search, not just "I
   didn't find one." If it's wrong, it's wrong because the submission sent
   the wrong value, not because a derivation failed. Examples: `EQClass`,
   `EQTerr`, chunk 9's `TotalLimit`.
2. **Dead-derivation trap.** There IS a rule that looks like it derives this
   field — and the rule is not broken — but the table or record it reads
   from is empty in practice, so the derivation always misses and the field
   behaves exactly like a pure input, just with a misleading "there's a
   rule for that" appearance. Examples: `EQDeductibleTier` (countrywide
   only; the states file rows, corrected 2026-10-02),
   `BlktCauseOfLossValue` (before chunk 9's golden case), the New York
   `ProtectionClassFactor` shape.
3. **Conditional fallback.** The field IS genuinely derived under most
   conditions, but on a specific gate (a blank value, a particular class
   code, a missing sibling field) the derivation falls back to a literal —
   and that literal is sometimes the sensible default (1.0, "No") and
   sometimes a silent zero that collapses the premium. Examples: chunk 2's
   `BCEGFactor` (falls back to `0.0`, not `1.0`, when territory/grade are
   blank), chunk 9's `MUBlktRated` (falls back to `"No"`, the safe value).

A fourth shape recurs often enough to name separately, even though it isn't
one of the three: **a field that IS derived, unconditionally, with no
`IsNull` guard — so a value the submission supplies is silently
overwritten.** This is the opposite failure direction from a dead-derivation
trap: here the derivation always *succeeds* and the submitted value is what
gets lost, not the other way around. Examples: chunk 4's `Group` letter and
`OccupCategoryRiskSeverity`, chunk 5's `ApartmentCondoIndicator`, chunk 6's
`PolicyType`. These are listed per-coverage under "documented but not one of
the three categories," not force-fit into the main table.

**Path-selectors are a different concept entirely** and are not mixed into
the tables below. A path-selector (`CovType`, `CauseOfLossToUse`,
`IncludedInBlkt`, `BlktTypeOfBlanketRating`, `SetFactor`'s branch
conditions) is an input that decides *which formula runs*, not a value that
feeds a formula directly. Getting a path-selector wrong doesn't zero a
factor — it runs the wrong chain entirely, which can look like any of the
above from the outside. They're listed in their own section per coverage.

## How to use this doc

Before building any golden case or real submission for a coverage, check
that coverage's own section below for its pure-input list first — those are
the fields no amount of "the engine should compute this" will ever
populate. Then check the dead-derivation-trap list, since those are the
ones most likely to fool a first attempt (the rule fires, no error, and the
result is still wrong). The conditional-fallback list tells you which blank
fields are "safe" (fall back to a sensible default) and which are
"dangerous" (fall back to a silent zero) — treat every fallback as
dangerous until you've confirmed which.

---

## Building — Basic Group I (chunk 1)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `BasicGroupIRatingTerr` | Pure input | Used directly as a lookup key; not stated as raising | CF-CHUNK1-GATE.md |
| `ClassCode` | Pure input | Supplying derived `ClassCodeToUse` instead → base-rate gate fails → premium zero, no error | CF-CHUNK1-GOLDEN-CASE.md §2 |
| `ConstructionType` | Pure input | Unrecognized value resolves to code 0 → prices at zero, no raise | CF-CHUNK1-GOLDEN-CASE.md §2; CF-CHUNK1-GATE.md pt.4 |
| `CauseOfLoss` | Pure input | Blank → `CauseOfLossToUse` blank → `CoverageOnPolicyIndicator=0` → premium zero | CF-CHUNK1-GOLDEN-CASE.md §2 |
| `ProtectClass` (must be on Location, not Structure) | Pure input | Set on the wrong node → factor stays 1.0 → premium 4% too high, no error | CF-CHUNK1-GOLDEN-CASE.md §2 |
| `LossCostMultiplier` | Pure input | "Company input, not filed" | CF-CHUNK1-GOLDEN-CASE.md §2 |
| `IRPMFactor`, `PackageModFactor`, `MultiPremiumAndDispersionCreditFactor` (policy-level) | **Computed only when blank; a supplied factor always wins** (updated 2026-10-02) | Blank → computed from the IRPM categories / package rules. ISO **refuses** a policy whose combined modifier is 0 or ≥ 2.00 (stat-code lookup has rows 1–199 only), including a package discount of 0; ours prices (OI-103, chunk 28) | CF-CHUNK1-GOLDEN-CASE.md §2; CF-CHUNK14-GATE.md; OI-103 |
| `FullBldgValue` | Pure input | Not rate-affecting on this branch; omission raises an ISO validation message | CF-CHUNK1-GOLDEN-CASE.md §2 |
| Arizona `BasicGroupIReductionCredit` (Location, AZ only) | Pure input | Absent → literal `0.0` fallback → every AZ building prices at zero, nothing raises | CF-CHUNK1-GATE.md pt.3 |

**Dead-derivation trap**

| Field | Trap | Source |
|---|---|---|
| `TerrorismPremium` (policy-level, read by NY's terrorism message rule) | Zero writers anywhere in the `CommercialProperty` datadef group, countrywide or in NY — "the rule is dead code as filed... can never fire for any submission" | CF-CHUNK1-GATE.md pt.3 |

**Path-selectors, not rating-value inputs**

- `RatingType` (Class / Specific / Tentative; CA also "One-Term Loss Cost"). **Updated 2026-10-02: the Specific / Tentative path is built and ISO-confirmed (chunk 26).** Specific needs `SpecificGroupIRate` (none → building AND BI Group I $0, silently); a **blank `RatingType` prices Group I at rate 1.0** (building $1,204 where Specific gives $362), at ISO too. The occupancy and contents **copy** it (a submitted copy is overwritten). CF-CHUNK26-GATE.md
- `CovType` — selects premium Branch A
- `IncludedInBlkt` — selects blanket vs. non-blanket path

---

## Building — Basic Group II (chunk 2)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `BasicGroupIIRatingTerr` (Location) | Pure input | Blank → base rate 0 → Group II premium zero | CF-CHUNK2-GATE.md pt.4 |
| `NumStories` | Pure input | Blank → no symbol resolves → zero | CF-CHUNK2-GATE.md pt.4 |
| `BCEG` | Pure input | Absent → `SetBCEGFactor` never assigns → literal `0.0` fallback → Group II prices at zero (ISO-confirmed: $32 with it, $0 without). **Except DC and NY**, whose `SetBCEGFactor` is empty: BCEG is not read there (grade 4 = grade 9; DC $38, NY $70, ISO equal) (updated 2026-10-02) | CF-CHUNK2-GATE.md pt.4; CF-CHUNK27-TASKS.md C27-08 |
| `RatingTypeBasicGroupII` | Pure input | 36 of 47 states gate `SetBasicGroupIIRate` on this Group-II-specific field the countrywide rule has no concept of; omit it and those 36 states price at zero. "Specific" also needs `SpecificGroupIIRate` (blank type → Group II $0 on building, contents and BI, ISO the same) (chunk 26) | CF-CHUNK2-GATE.md pt.3; CF-CHUNK26-GATE.md |
| `BasicGroupIISymbol` — **New York only** | Pure input (added 2026-10-02) | NY's symbol rule is empty, so the symbol is submitted; without it Group II is **$0 at ISO too**. With it NY also needs `CompletedBasicGroupIISymbol` "Not Applicable", or ISO refuses (ours prices: OI-103, chunk 28) | CF-CHUNK27-TASKS.md C27-09 |
| `BasicGroupIIRatingTerr` — **Florida** | Pure input (added 2026-10-02) | FL uses its own Group II territories ("Entire State" is refused at ISO). Outside OR, a Specific Group II building still needs a territory the state's rate table files (the class lookup runs anyway) | CF-CHUNK27-TASKS.md C27-06; CF-CHUNK26-GATE.md |

**State shapes confirmed 2026-10-02 (chunk 27 C27-07..09, ISO live):** TX multiplies its Group II rate by a flat **0.1** when wind / hail is excluded ($800 → $79); IL maps "Cook County" to its "Cook" rows; MT's symbol now resolves ($74).

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|---|
| `BCEGFactor` (derived) | Territory or grade blank | Falls back to literal `0.0` instead of the computed factor | CF-CHUNK2-GATE.md pt.4 |

**Ambiguous** — `OpenSides` (Yes moves `BasicGroupIINumericValue` 1.0→4.0, nearly quadrupling premium) is shown as a lever but its own derivation status is never stated.

**Path-selectors** — `ClassCode` (0580/0585/1150/1300/1650/1751 each route the symbol/numeric-value derivation down a different branch); the Standard Property Policy form-name election ("Allied Lines" vs "Vandalism" in the name).

**Instrument note, not a field finding**: the "ISO always refuses on an empty `SingleResult` lookup" hypothesis was tested project-wide and **disproven** — turning strict refusal on breaks GL verification on VA/VT payloads ISO itself rates, because those states file a zero-row Subline table that makes both the state and countrywide lookup passes miss identically. Not every empty `SingleResult` is a rejection signal.

**Updated 2026-10-02 (chunk 28 C28-02, `CF-CHUNK28-REFUSALS.md`):** the Property evidence now points the other way. Of 66 ISO refusals that reproduce live, **65 are a `SingleResult` lookup that matches no row** (an unfiled or blank key), and across 1,689 requests ISO rated, our engine never misses a `SingleResult` lookup. The exception is Vermont's empty earthquake sub-limit tier table. **Our engine still prices every one of those 66 (often at $0)**; refusing where ISO refuses is chunk 28 Set A, not built. Practical rule for submitters: **every lookup key must be a value the state files**, or ISO will refuse the policy.

---

## Building — Broad and Special (chunk 3)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `Limit` | Pure input | **Updated 2026-10-02.** Absent → **$0** (Broad and Special), as at ISO, which also returns "Please enter a Limit greater than 0". No longer a refusal: since OI-109 / OI-110 (2026-09-23, user-authorized) Property's `Product` skips a null operand as ISO does, and writes 0 only when every operand is null. Re-run offline 2026-10-02: `16_chunk3_zero_cases.py` Z3 = 0 / 0 | CF-CHUNK3-ZERO-CASES.md; OI-109, OI-110 |
| `Deductible` | Pure input | Blank → silent **$0 on both Broad and Special**: both deductible rules end in an `Otherwise` worth `0.0` (the "Special has no `Otherwise`" reading was wrong; resolved, `16_` Z2) (updated 2026-10-02) | CF-CHUNK3-ZERO-CASES.md; `16_chunk3_zero_cases.py` Z2 |
| `TheftDeductible` | Pure input | Non-blank, not "Not Applicable"/"250", and ≠ `Deductible` → moves the Special deductible factor to 0.89; otherwise reverts to the building deductible (0.97) | CF-CHUNK3-SPECIAL-STRUCTURE.md task 19 |
| `ClassCode` (Florida's own 21-code list) | Pure input | Off that list → Florida rates non-residential instead of residential | CF-CHUNK3-STATE-SWEEP.md |

**Dead-derivation trap**

| Field | Trap | Source |
|---|---|---|
| `Applicability="Paragraph B"` (Broad roof-surfacing) | `SetLimitationsOnCovForRoofSurfacingACVFactor` tests `!= "Paragraph B"` *before* any lookup and its `Else` assigns a flat `1.0` — the filed `Paragraph B → 0.99` row can never be produced by any submission | CF-CHUNK3-GATE.md pt.5; CF-CHUNK3-BROAD-STRUCTURE.md §11 |
| Broad roof-surfacing ACV/cosmetic factors generally | The derivation fires and returns real factors, but every filed Broad base rate absorbs both at 3-decimal rounding — 0 of 6 can ever show a moved premium. (Special, same factor, DOES move — this is magnitude, not a rule defect) | CF-CHUNK3-BROAD-STRUCTURE.md §11 |

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|---|
| `DeductibleFactorSpecial` (theft branch) | Theft excluded, OR `TheftDeductible` blank/"250"/"Not Applicable", OR equal to `Deductible` | Falls back to the ordinary building deductible factor (0.97) instead of the theft-specific band | CF-CHUNK3-SPECIAL-STRUCTURE.md task 19 |

**A submission-override hazard, flagged separately**: `SpecialBaseRate` is guarded by `IsNull`, which can't distinguish "already set by an earlier rule" from "supplied by the submitter" — a submitted literal (e.g. `9.999`) is honoured over the filed table value, pricing at $11,398 with nothing raised. `SetSpecialCauseOfLossAdjustment` by contrast is unguarded and always re-derives, so a submitted override there is silently discarded — the *safer* rule is the unguarded one, the reverse of the usual worry.

**Path-selectors** — `CauseOfLossToUse` (Basic/Broad/Special — confirmed cumulative, not exclusive, by ISO); `Applicability`; `ClassCode=1150` (Builders Risk, routes base rate AND independently zeroes coinsurance); the theft-exclusion election (CP 10 33).

---

## Contents / Personal Property (chunk 4)

| Field | Category | If omitted | Source |
|---|---|---|---|
| Watchman/burglar-alarm schedule credit factor (Special form) | Pure input | Supplying the factor without also submitting `TypeOfWatchmanSrvc` leaves the credit at 1.0 — a discount silently not given, no message | CF-CHUNK4-TASKS.md C4-27 |
| The **building's** `WindstormOrHailDeductible` (read by contents) | Required at ISO (added 2026-10-02) | Blank → **ISO refuses every contents policy** (`WindstormOrHailDeductibleAsNumber`, keys CW + blank); ours prices. With it, chunk 8's contents premiums are ISO-confirmed. OI-103, chunk 28 Set A | CF-CHUNK27-TASKS.md (RC-2); OI-103 |
| `SpecificGroupIRate` (and `SpecificGroupIIRate`) on the contents, Specific / Tentative only | Pure input (added 2026-10-02) | Contents price on their **own** specific rate, not the building's; none of their own → contents Group I **$0**, silently (ISO the same) | CF-CHUNK26-GATE.md |

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|---|
| `ProtectClass` (Contents-side factor) | Blank | Falls back to **0.0** for Contents (vs. Building's **1.0** fallback on the identical blank field) — Contents prices $0, Building rises, no message either way | CF-CHUNK4-GATE.md pt.4; CF-CHUNK4-TASKS.md C4-32 |
| Same factor, class 1751/1752 | Class 1751 | Falls back to 1.0 ($69 vs. true 0.96) | CF-CHUNK4-TASKS.md C4-18 |
| Same factor, class 1751/1752 | Protection class missing | Falls back to 0.0 (zero premium) — "two fallbacks in one rule" | CF-CHUNK4-TASKS.md C4-18 |
| Broad-form deductible factor | No `SetDeductibleFactorBroad` rule exists in PP at all — reads Building's ancestor value 4 levels up, whose own `Otherwise` is 0.0 | A blank building deductible silently zeros Contents' Broad premium instead of refusing. **Corrected 2026-10-06** (`cf-broad-chains.html` PP review #15): the engine now refuses the policy through Contents' `DeductibleStatCode` lookup (C28-05), even when the building is "No Coverage" or not Broad | CF-CHUNK4-TASKS.md C4-21 |

**Documented but NOT one of the three categories** (derived unconditionally, submitted value silently discarded):

- `OccupCategoryRiskSeverity` — looked up from `OccupCategory` + the occupancy's own `ClassCode`, no `IsNull` guard; with no class code it's overwritten to blank, gating Special's base rate shut.
- The Basic Group I `Group` letter — derived from class code alone; a submitted `Group` is overwritten.
- Seven inherited/`Copy`'d fields — `CovForm`, `BldgClassCode`, `RatingType`, `OccupCategoryRiskSeverity`, `TheftDeductible`, item `Deductible`, the class-code chain — a per-item value is accepted and silently discarded.

**Ambiguous** — `CauseOfLoss` (plain gating field, no "zero deriving rules" statement found); `TypeOfWatchmanSrvc` (required alongside the watchman credit, not confirmed pure).

---

## Business Income (chunk 5)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `MfgPct`, `OtherPct`, `Combination1Factor`, `Combination2Factor` (the "Combined" `TypeOfRisk` blend) | Pure input | **Updated 2026-10-02.** Absent → **not** $0: each weighted term is a `Product` with a null operand, ISO skips the null and **adds the two component factors** (Factor 1.26, BI **$256** + $30, ISO-confirmed live), so a missing blend percentage **over**-prices. Ours matches since OI-110 (`33_chunk5_zero_cases.py` Z2, re-run 2026-10-02). An off-domain `TypeOfRisk` (e.g. "Mercantile") still leaves Factor null → BI $0 (Z3) | CF-CHUNK5-TASKS.md C5-12; OI-110 |
| `Limit` | Pure input (added 2026-10-02) | Absent → BI **$0 with no message at all**, at ISO too (the building still prices) | OI-109 (P-probes, `136_`) |
| Specific / Tentative rate | Inherited (added 2026-10-02) | BI rates on the **building's** `SpecificGroupIRate` (MO 2023 V02: the building's final rate). **CA One-Term Loss Cost: BI falls to rate 1.0** ($538 vs $121), ISO the same (OI-124, closed as matches ISO) | CF-CHUNK26-GATE.md; OI-124 |

**Dead-derivation trap**

| Field | Trap | Source |
|---|---|---|
| `BaseRateAdjustmentFactor`, Puerto Rico only | PR overrides `SetBGIBaseRateAdjustmentFactor` with an empty `<rul:Sequence />` — deletes the rule, not just the table row. First time seen on a rating rule, not just a message rule | CF-CHUNK5-TASKS.md C5-17 |

**Conditional fallback**

| Field | Fallback | Source |
|---|---|---|
| A `Factor` branch near the per-form specifics (task #22) | "The Factor is 0.0, not 1.0, and the premium is zero. Predicted as a null on the assumption the row was missing; it is a **written** zero" | CF-CHUNK5-TASKS.md task #22 |

*(Note: an earlier draft of this reference described this as "the educational branch" — that phrase does not actually appear in the chunk 5 docs. Only the finding above, as worded, is confirmed.)*

**Documented but NOT one of the three categories**: `ApartmentCondoIndicator` — derived from the class code against a hardcoded list of 13; setting it directly does nothing.

**Ambiguous** — `CoinsuranceToUse` (follows the BI record, not the building — not confirmed derivation-free); `TypeOfRisk` (keys the factor table; not confirmed derivation-free).

**Path-selector, not a raw input** — `SetFactor` itself: "reads no matrix at all — it is a selector, not a lookup." Four branches in priority order: `MaxPeriodOfIndemnityFactor` if `MaxPeriod="Yes"`; else `MonthlyLimitOfIndemnityFactor` if `MonthlyLimitOfIndemnity != "Not Applicable"`; else `ExtraExpenseFactor` if `CovType="Extra Expense Only"`; else `TypeOfRiskFactor`. **Failure mode**: electing all three named conditions together resolves to **null, not the highest-priority factor** — the winning branch is keyed on `CovType` and files no matching row, and it does not fall through to a lower branch. A valid combination of filed options can price at zero in silence.

**Cross-cutting note**: Basic Group I and II have no base rate of their own — they read Building's already-computed rate directly. Every Building-side pure-input/trap finding from chunks 1–2 (symbol, `ProtectClass`, `NumStories`, district overrides) is load-bearing for Business Income premiums too, without appearing anywhere in the Business Income ruleset itself.

---

## Special Class (chunk 6)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `ClassDescription` | Pure input | The rating driver is prose, not a code — no rule derives it. Basic I and II both price $0; Broad/Special are unaffected (they key off a hardcoded literal / flat constant instead). **Must be a description the state files** (FL is frozen at an older vocabulary): an unfiled one makes **ISO refuse** (`SpecialClassDescriptionConvertedOption`, OI-99) where ours prices $0 (updated 2026-10-02) | CF-CHUNK6-ZERO-CASES.md; CF-CHUNK6-TASKS.md structural note 1; OI-99; C15-16 |
| `BasicGroupIISymbol` (on the Special Class item) | Pure input | "Three datadef groups derive the Group II construction symbol... `CommercialPropertySpecialClass` is not one of them" — Group II prices $0; Group I unaffected | CF-CHUNK6-PER-FORM.md C6-18; CF-CHUNK6-ZERO-CASES.md case 5 |
| `SpecialClassDescConvertedOption` (New York only) | Pure input | NY's own converting rule is deleted (`<rul:Sequence />`) — "a deleted rule is how ISO says a field is an input," reachable only with NY's own private codes | CF-CHUNK6-DESCRIPTION-CHAIN.md C6-11/12 |

**Dead-derivation trap**

| Field | Trap | Source |
|---|---|---|
| `ProtectionClassFactor` (computed factor) | Real rule, real 168-row table, read 0 times by any rate chain — only inside its own `IsNull` guards, run after every chain that could use it. PR deletes the rule and the premium doesn't change | CF-CHUNK6-PER-FORM.md C6-16/17 |
| Class code `1150` in Special Class | Building's ruleset routes 1150 to a Builders Risk rate 6 times; Special Class routes it 0 times — submitting 1150 does nothing here | CF-CHUNK6-FORMS.md C6-23 |

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|---|
| `ProtectClass`/`ProtectionClassToUse` (Group I lookup key) | Absent | Resolves to `"9 to 10"`, the **worst** band — the only absent field in the chunk that *raises* the premium (56% up) rather than zeroing it | CF-CHUNK6-DESCRIPTION-CHAIN.md C6-10 |
| `Deductible` | No table match / absent | All four deductible rules end in an `Otherwise` worth `0.0` — takes all four Special Class forms to $0 simultaneously, the widest single-field blast radius found in six chunks | CF-CHUNK6-ZERO-CASES.md case 3 |

**Flagged, not one of the three categories**: `BasicGroupIISymbolNum` in New York is a "decoy," not an input or a trap — a live rule elsewhere overwrites it from its own lookup in most states, but NY's rewritten rule never reads it at all (its table is header-only). `PolicyType` is an unconditional, unguarded copy from the policy 4 levels up — always succeeds, overwriting to blank if the policy doesn't carry it.

**Path-selectors** — `CauseOfLossToUse`; `IncludedInBlkt`; `Coinsurance` % (selects which coinsurance branch/table).

---

## Special Class Business Income (chunk 7)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `MonthlyLimitOfIndemnity` | Pure input | Submitted classification field. Trap: the branch test is `!= "Not Applicable"` against a `""` default — an **absent** field reads `""`, which is not equal to `"Not Applicable"`, so the branch is wrongly elected anyway, copying a factor nothing computed. Both Basic I and II price $0 with `TypeOfRiskFactor` sitting healthy one field away, no message | CF-CHUNK7-GOLDEN-CASE.md; CF-CHUNK7-TASKS.md structural finding 4 |

**Dead-derivation trap**

| Field | Trap | Source |
|---|---|---|
| `ApartmentCondoIndicator` (as it feeds the theft-exclusion factor here) | The lookup's key in THIS group is a hardcoded constant `"No"` from every read site — "both dimensions are dead." The identical table is read live via the real field in plain Business Income ("pinned here, live next door") | CF-CHUNK7-PER-FORM.md C7-19/20 |
| Class code `1150` (Special Form Builders Risk base rate) | Named 0 times in this ruleset vs. 6 in plain Business Income; the table itself has 1 CW row, 0 states file their own | CF-CHUNK7-PER-FORM.md C7-21 |

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|
| `LossCostMultiplier` (this group's own) | Own value null | Copies the parent Special Class item's LCM instead | CF-CHUNK7-BORROWED-RATE.md C7-12 |

**Flagged, not one of the three categories**: `BlktTotalFullValueAmount`/`BlktCauseOfLossValue` are overwritten to `0`/`''` by `SetNonEQBlanketValues` regardless of what's submitted here — a destructive overwrite reproduced at this nesting level (C7-25), not a sensible default.

**Path-selectors** — `CauseOfLossToUse`; `CovType` (With/Without Extra Expense); `MonthlyLimitOfIndemnity` (also cataloged above for its omission trap); `TypeOfRisk` + `MaxPeriod`.

---

## Legal Liability (chunk 8)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `Limit` | Probable pure input | **Updated 2026-10-02.** Absent → **$0**, and ISO's Legal Liability premium is $0 too (no longer a refusal since OI-109 / OI-110; `61_chunk8_zero_cases.py` case 5, re-run 2026-10-02) | CF-CHUNK8-GATE-3-5.md C8-03 case 5; OI-109 |
| Location `District` — **California** | Pure input (added 2026-10-02) | CA's Legal Liability base rate is a District I / II table: without a `District` CA's Legal Liability prices **$0**; with it $57 (I) / $68 (II), ISO equal. (Chunk 8's "CA zero" was the sweep sending none) | CF-CHUNK27-TASKS.md C27-06 |
| Group II territory — **Florida** | Pure input (added 2026-10-02) | FL prices Legal Liability ($59) with its own Group II territory; "Entire State" is refused at ISO | CF-CHUNK27-TASKS.md C27-06 |

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|
| Insurable-interest option (`AddlInsurableInt`) | Blank (an appended-but-empty record) | Setter's `Else` writes a literal **0.0**, outside the normal 1.0/1.25 domain — zeroes the premium via a mechanism distinct from, but visually identical to, a deleted-record zero (see `PolicyType` below) | CF-CHUNK8-GATE-3-5.md C8-03 case 1 |

**Required-election / destructive-gate fields** (a required election whose absence *deletes* a submitted record, closer to a fourth failure shape than a plain fallback):

- `PolicyType` — `AttachFormCommercialPropertyLegalLiabilityCoverageForm` gates on `PolicyType="Commercial Property Policy" AND CovType="Legal Liability"`; its `Else` is a bare `Remove` on the whole coverage-form record. Recurs project-wide (C6-01, then here, then chunk 9's `BlktRated`).

**Ambiguous** — `Coinsurance` (submitted, derivation status never stated); `FullBldgValue`; `IRPMFactor`/`PackageModFactor` (derivation status itself unconfirmed — only their *read depth*, 5/7/9 `../` hops depending on premium group, is documented).

**Path-selectors** — `CovType` (item-level, Building) and `CovForm` (occupancy-level, Contents) — same Legal Liability fork, different level entirely; getting the level wrong (item vs. occupancy) is a real trap of its own.

---

## Blanket rating (chunk 9)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `TotalLimit` (Detail record, feeds `BlktLimit`) | Pure input | "Never set by any rule in the 13,458-line Detail file: it is a genuine input, the company's chosen total blanket limit of insurance" — contrasted directly against `TotalFullValueAmount`, which IS derived by summing `FullBldgValue` across structures | CF-CHUNK9-GOLDEN-CASE.md §2B |

**Dead-derivation trap**

| Field | Trap | Source |
|---|---|---|
| `BlktCauseOfLossValue` | `SetNonEQBlanketValues` is the ONLY rule that ever assigns it a real value, and it has three distinct ways to leave it short: gate 1 (`MUBlktRated != "No"`) skips the whole rule body, no `Else`; gate 2 (`IncludedInBlkt != "Yes"`) writes the literal `"Not Applicable"`; gate 3 (no matching Detail `UnitNumber`) leaves the field at its empty-string default. "The rule was never broken. Nothing has ever fed it." Every golden case before chunk 9's own hit gate 3 | CF-CHUNK9-TASKS.md opening §2; C9-06; C9-09 |

*(Nuance, stated explicitly in the source docs: once a submission clears all three gates — chunk 9's own golden case — the derivation works correctly and matches ISO exactly. This is a trap that was dead in practice for every submission built through chunk 8, not a rule structurally incapable of succeeding.)*

**Confirmed NOT dead-derivation traps, despite superficially similar symptoms** — flagged so they aren't confused with the above:
- `BlktTotalFullValueAmount` — its $0 in chunk 9's first run was a genuine **engine bug** (`ForEach @AtInputDataDef` write-reparenting), fixed 2026-09-21. "A starved copy, not a starved formula."
- `Blkt<Form>AvgRate` — the averaging engine itself, proven exact for both Average/Highest elections and for Basic Group II/Broad/SC Business Income.

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|
| `MUBlktRated` | Null | `SetMUBlktRated` defaults to the literal `"No"` — the safe direction, but combined with the destructive `BlktRated` gate below, still decides whether the whole blanket record survives | CF-CHUNK9-TASKS.md C9-07 |

**Required-election / destructive-gate field**: `BlktRated` (policy-level) — `AttachFormBlanketRating` tests `BlktRated="Yes" AND MUBlktRated="No"`; its `Else` **deletes** the entire submitted `CommercialPropertyBlanketRatingTable` record, before any per-structure rate chain runs. Same shape as chunk 8's `PolicyType`, one chunk later.

**Ambiguous** — `Coinsurance` (Detail record, submitted, derivation status never stated); `FullBldgValue`; `IRPMFactor`/`PackageModFactor` (as in chunk 8).

**Path-selectors** — `IncludedInBlkt` (5 separate per-form Domain Tables, not one flat switch — Legal Liability/Leasehold Interest structurally can never reach "Yes"); `BlktTypeOfBlanketRating` ({Average, Highest}, two genuinely different, both-live chains); Detail record's `Type` (4-literal subset of a 6-value domain, the other 2 routing to Business Income's own branch).

---

## Earthquake (chunk 10)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `EQClass` | Pure input | Confirmed by corpus-wide `ToDataDef` search — never assigned by any rule, only read. Structure-level, no copy-down rule at all | CF-CHUNK10-TASKS.md finding 3; CF-CHUNK10-GOLDEN-CASE.md §5 |
| `EQTerr` | Pure input | Same corpus-wide confirmation. Location-level, copied DOWN to the structure by a plain `Copy` (unlike `EQClass`) | CF-CHUNK10-TASKS.md finding 3; CF-CHUNK10-GOLDEN-CASE.md §5 |

**Dead-derivation trap**

| Field | Trap | Source |
|---|---|---|
| `EQDeductibleTier` | **Corrected 2026-10-02: not dead in the states.** The countrywide `EarthquakeDeductibleTier.RateTable.csv` is header-only, but **every 2026 state package in the corpus files rows** (1–19 each; re-counted 2026-10-02), so `SetEQDeductibleTier` (IsNull-guarded) derives the tier from `EQTerr` in-state; a submitted tier still wins. An `EQTerr` the state's tier table does not file makes **ISO refuse** (17 live cases, AK GA IN NH NV SC WY, keys CW + 22); ours prices (OI-103, chunk 28). **Also one of the sub-limit path's 4 equality keys.** The sub-limit tier tables are state-filed too: a tier a state does not file prices $0 (chunk 19), and **Vermont's empty sub-limit tier table is refused at ISO** while ours reads countrywide (CF-CHUNK28-REFUSALS.md) | CF-CHUNK10-TASKS.md C10-02/C10-19; CF-CHUNK28-REFUSALS.md; 2026 ERC table CSVs |

**Silent submission-shape traps found only by running** (a distinct shape from a dead-derivation trap — these are ancestor-copy overwrites, not input-vs-derived questions):
- Contents' own `SetEQClass` is an unguarded ancestor-copy from the Structure — a value set directly on the Personal Property record is silently overwritten.
- Four more of Contents' "own" EQ factor rules (`SetSoftStoryModificationFactor`, `SetEQSprinkleredRiskFactor`, `SetBldgHeightFactor`, `SetBCEGEQFactor`) are also ancestor-copies — Contents needs the Structure's own `SprinklerSystem`/`BCEG` populated correctly even when Building itself isn't EQ-elected.
- `BCEGEQFactor` defaults to **0.0** (not 1.0) on a blank `BCEG` — a genuine zero-collapses-the-premium case.
- `EQSprinklerLeakageOnly` blank satisfies neither branch of `SetEQDeductibleFactor` (no `Otherwise`) — starves `FinalEQRate`.
- Blank `SprinklerSystem` is read as "has a sprinkler," not "None" — silently adds a 1.06 factor instead of a no-op.

**Path-selectors** — `EQCovIndicator` (`"No Coverage"` / `"Not Applicable"` / `"Yes, Not Included in Blanket"` / `"Yes, Included in Blanket"` — two of the four collapse to the same "endorsement never created" outcome, the other two to "created, computed to $0"); `EQCauseOfLossForm` (selects among 4 Endorsement files — plain percentage, plain flat-dollar, sub-limit+percentage, sub-limit+flat-dollar — with destructive `Else` branches on the ones not selected); `CovType` (Building/Improvements and Betterments/Condominium Association/Builders Risk/Legal Liability/Leasehold Interest).

**Note on `EQCoinsuranceFactor`**: unlike every other EQ-prefixed factor, this one actually **shares** the ordinary chain's `CoinsuranceFactor` table (same `MatrixDef`) rather than being EQ-only — the one exception to "EQ shares zero multipliers with the ordinary chain."

---

## Inputs established by chunks 11–27 (added 2026-10-02)

Summarised from each chunk's gate doc ("what the chunk established, in submission terms"); every
item below was found by running and confirmed against ISO live. Detail and evidence: the gate file named.

| Chunk | Coverage | What a submission must carry, and the traps | Gate doc |
|---|---|---|---|
| 11 | Leasehold Interest | Structure `CovType` = "Leasehold Interest" with `PolicyType` = Commercial Property Policy, else the LI record is **deleted, no message**; `EQCovIndicator` "No Coverage", not blank (blank switches EQ on); `ExpDate` is never an input (EffDate + 1 year); a `PercentInterest` the table does not file (e.g. 10.5%) is refused at ISO, $0 in ours (OI-103) | CF-CHUNK11-GATE.md |
| 12 | Debris Removal, Ordinance or Law, Utility Services, Unmanned Aircraft, Green Upgrades, Dependent Properties | Ordinance or Law B / C limits: absent → the cell prices on what remains of its product (ISO skips the null operand, OI-110; usually $0), A still prices; unfiled Utility Services waiting period or Green Upgrades percentage → ISO refuses (OI-103); the drone reads the **contents'** theft factor, Dependent Properties the **BI's** (chunk 27) | CF-CHUNK12-GATE.md; CF-CHUNK27-GATE.md |
| 13 | Terrorism | **`TRIAType` drives everything** (blank → no terrorism form; submitted forms removed silently); `TerrorismIndicator` switches nothing off; send `TerrorismSubLimit`, `TerrorOverridePremium`, `BasicGroupIRatingTerrFactor` as JSON numbers; an unfiled terrorism territory is refused at ISO | CF-CHUNK13-GATE.md |
| 14 | Policy assembly | A supplied IRPM / package mod / multi-premium credit always wins; combined modifier must be 0.01–1.99 or ISO refuses; MO's seventh IRPM category blank is refused; **CO / IN need a wind-hazard county, OK "Entire State", SC an earthquake territory**, or ISO refuses; **no minimum premium** (OI-113: refer to company, not built) | CF-CHUNK14-GATE.md |
| 15 | Manual-premium endorsements | `ManualPremium` plus an on-switch on five records (`Indicator`, `TemporarilyInPortableStorageUnitsIndicator`, `InterruptionCompuOpsIndicator`; Valuable Papers needs its own Contents row `CovType`), or $0 with a premium entered; set the Contents `CovForm` **on the occupancy** (copied down); a special-class description the state files | CF-CHUNK15-GATE.md |
| 16–17 | BI add-ons, Pollutant, Spoilage, Molten Material, Mine Subsidence, Payroll, Mining, Landlord, Watercraft, Off-Premises | Send `NumOfDays` as a number (string refused); blank days price as 0 days; Mining needs `TypeOfRisk` Mining (the container is deleted otherwise); Landlord carries its **own** `CauseOfLoss`; Special Class BI spells it `WaterFrontProperty`; Off-Premises needs an extended period (blank → $0); a watercraft option "Not Applicable" is refused at ISO | CF-CHUNK16-GATE.md; CF-CHUNK17-GATE.md |
| 18 | Agreed Value, Inflation Guard, Functional Valuation, Rebuilding, Vacancy, Peak Season | `AgreedValueLimit` as a number (absent → $0, no message); Functional Valuation switched by the parent's `ValuationType`; Vacancy / Peak Season need the policy `EffectiveDt` / `ExpirationDt` (leave a blank date out, don't send it empty) | CF-CHUNK18-GATE.md |
| 19 | Scheduled items (Tenants', Antennas, Signs, Trees, contents-side families) | Tenants' needs **both** deductibles (blank → $0) and its own `CausesOfLoss`; EQ needs the item's and the building's election; give the contents their own EQ election | CF-CHUNK19-GATE.md |
| 20 | Small coverages with own tables | Radioactive needs a submitted rate; Fire Department needs `FireIncreaseLimitApplyOnPolicyIndicator` "Yes" and a limit above 1,000 (blank limit: ISO skips the blank, OI-115); special-limit items need the Special cause; Mortgageholders' `Limit` is text | CF-CHUNK20-GATE.md |
| 21 | Sewer backup, condo options | `DischargeLimitPD` / `DischargeLimitBI` (xs:int) are the only switch; send `LossAssessmentLimit` "0" when unwanted (blank with misc. real property is refused at ISO); FL's CPP condo `ManualPremium` is text, and a blank one is refused at ISO (OI-117) | CF-CHUNK21-GATE.md |
| 22 | Value Reporting, Additional Locations | General Information record at policy level; contents on a reporting coinsurance value; **send "Not Used"** (average rates "Used" is refused at ISO and ours, OI-119); the two forms are mutually exclusive; either switches the ordinary contents premium off | CF-CHUNK22-GATE.md |
| 23 | State-only (MA, AK, CA, VA) | MA remediation under the building; AK fees only on Legal Liability; CA Limited EQ via the location's `EQCauseOfLossForm`; records the rules attach on their own sit at $0 without their inputs | CF-CHUNK23-GATE.md |
| 24 | Builders Risk | `CovType` "Builders Risk", class 1150; with a reporting form `Limit` 0; renovations need `RatingType` "Class" (and `EQClass`); a 2% EQ deductible on class A1 is refused at ISO, $0 in ours (OI-103) | CF-CHUNK24-GATE.md |
| 25 | Flood | Location `FloodCovIndicator` "Yes" + General Information (`Deductible`, `FloodZone`, `FloodEffDate`, optional CRS); county states read `County` (VA `City`); each flood record `Limit`, `IncludedInBlkt`, `ExcessOverMaxNFIPIndicator`; Special Class / SCBI their own `ConstructionType`; AK / FL `ManualPremium` | CF-CHUNK25-GATE.md |
| 26 | Specific / Tentative | Building `RatingType` + `SpecificGroupIRate`; Group II in 36 states `RatingTypeBasicGroupII` "Specific", `SpecificGroupIIRate`, `SquareFootageOfBuilding`, a filed `BasicGroupIIRatingTerr`; contents their own specific rates; blank `RatingType` → rate 1.0 | CF-CHUNK26-GATE.md |
| 27 | Loose ends on chunks 1–8 | CA `District` (Legal Liability); NY `BasicGroupIISymbol` + `CompletedBasicGroupIISymbol`; FL Group II territory; the building's `WindstormOrHailDeductible` for any contents policy | CF-CHUNK27-GATE.md |

## Open behaviours — chunk 28, none built yet (added 2026-10-02)

Chunk 28 is **open (2 of 22)**; every item needs the user's go before any engine change. Until then a
submission builder must guard against these itself:

- **Refusals (Set A).** Where a lookup key is unfiled or blank, **ISO refuses the whole policy; our engine
  prices it** (often at $0). 66 live cases, 65 of them a `SingleResult` lookup with no row
  (`CF-CHUNK28-REFUSALS.md`); also `Convert` of a blank (OI-117). OI-99, OI-103, OI-117.
- **Silent zero-price inputs (Set B).** Eight inputs still price at $0 with no message: AZ's
  `BasicGroupIReductionCredit`, an unknown `ConstructionType`, no `BCEG`, no `RatingTypeBasicGroupII`, no
  Group II territory, a blank `Deductible` on Broad and on Special (two of the eight), a construction type spelled as a rating type;
  plus NY's missing Group II symbol. Many are $0 at ISO too, so the fix is a validation layer, not a rating
  change. A submitted `IsNull`-guarded derived field (e.g. `SpecialBaseRate`) overrides the filed table, at ISO too.
- **Minimum premium (Set E).** ISO applies none; the user's decision is "refer to company" (OI-113). No
  referral layer exists in the Property engine yet.
- **Messages and form names (Sets C, D).** Premiums agree; a handful of messages (OI-112, 114, 123, 125, 126)
  and 135 of 240 form names ("Value Not Found", OI-106) still differ from ISO.

## Appendix — ambiguous fields flagged across multiple chunks, needs verification

These fields were repeatedly treated as inputs in worked examples but no chunk's docs ever stated "zero deriving rules anywhere" for them. Listed here rather than asserted into a category:

- `BasicGroupIRatingTerr` / `BasicGroupIIRatingTerr` — used as lookup keys throughout, weaker phrasing than the confirmed pure inputs above.
- `Coinsurance` (raw percentage, appears on Blanket Detail records and elsewhere) — never explicitly labeled.
- `FullBldgValue` — a given in every worked example, never confirmed derivation-free.
- `TypeOfWatchmanSrvc` (chunk 4) — required alongside a confirmed pure input, not itself confirmed.
- ~~`IRPMFactor` / `PackageModFactor` — derivation status never stated.~~ **Resolved 2026-10-02 (chunks 14–15):** computed only when blank, a supplied factor always wins; endorsements take the **policy's** package discount and IRPM.
- ~~Special form's `Deductible`-removed case (chunk 3) — predicted null, actual 0, unexplained.~~ **Resolved:** the filed Special rule has an `Otherwise` worth `0.0`, like Broad's; both price $0 (`16_chunk3_zero_cases.py` Z2).
