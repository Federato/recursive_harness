# CF — required submission inputs, by coverage

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
   rule for that" appearance. Examples: `EQDeductibleTier`,
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
| `IRPMFactor`, `PackageModFactor`, `MultiPremiumAndDispersionCreditFactor` (policy-level) | Pure input | "Schedule inputs, not filed tables" | CF-CHUNK1-GOLDEN-CASE.md §2 |
| `FullBldgValue` | Pure input | Not rate-affecting on this branch; omission raises an ISO validation message | CF-CHUNK1-GOLDEN-CASE.md §2 |
| Arizona `BasicGroupIReductionCredit` (Location, AZ only) | Pure input | Absent → literal `0.0` fallback → every AZ building prices at zero, nothing raises | CF-CHUNK1-GATE.md pt.3 |

**Dead-derivation trap**

| Field | Trap | Source |
|---|---|---|
| `TerrorismPremium` (policy-level, read by NY's terrorism message rule) | Zero writers anywhere in the `CommercialProperty` datadef group, countrywide or in NY — "the rule is dead code as filed... can never fire for any submission" | CF-CHUNK1-GATE.md pt.3 |

**Path-selectors, not rating-value inputs**

- `RatingType` (Class vs. Specific/Tentative — the latter confirmed unbuilt project-wide)
- `CovType` — selects premium Branch A
- `IncludedInBlkt` — selects blanket vs. non-blanket path

---

## Building — Basic Group II (chunk 2)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `BasicGroupIIRatingTerr` (Location) | Pure input | Blank → base rate 0 → Group II premium zero | CF-CHUNK2-GATE.md pt.4 |
| `NumStories` | Pure input | Blank → no symbol resolves → zero | CF-CHUNK2-GATE.md pt.4 |
| `BCEG` | Pure input | Absent → `SetBCEGFactor` never assigns → literal `0.0` fallback → Group II prices at zero (ISO-confirmed: $32 with it, $0 without) | CF-CHUNK2-GATE.md pt.4 |
| `RatingTypeBasicGroupII` | Pure input | 36 of 47 states gate `SetBasicGroupIIRate` on this Group-II-specific field the countrywide rule has no concept of; omit it and those 36 states price at zero | CF-CHUNK2-GATE.md pt.3 |

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|---|
| `BCEGFactor` (derived) | Territory or grade blank | Falls back to literal `0.0` instead of the computed factor | CF-CHUNK2-GATE.md pt.4 |

**Ambiguous** — `OpenSides` (Yes moves `BasicGroupIINumericValue` 1.0→4.0, nearly quadrupling premium) is shown as a lever but its own derivation status is never stated.

**Path-selectors** — `ClassCode` (0580/0585/1150/1300/1650/1751 each route the symbol/numeric-value derivation down a different branch); the Standard Property Policy form-name election ("Allied Lines" vs "Vandalism" in the name).

**Instrument note, not a field finding**: the "ISO always refuses on an empty `SingleResult` lookup" hypothesis was tested project-wide and **disproven** — turning strict refusal on breaks GL verification on VA/VT payloads ISO itself rates, because those states file a zero-row Subline table that makes both the state and countrywide lookup passes miss identically. Not every empty `SingleResult` is a rejection signal.

---

## Building — Broad and Special (chunk 3)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `Limit` | Pure input | Absent → premium itself reaches null (not just a zeroed factor) → the null-premium guard **raises** — the one exception to the "absent means silent zero" family in chunks 1–3 | CF-CHUNK3-ZERO-CASES.md |
| `Deductible` | Pure input | Blank → Broad's `Otherwise` writes `0.0` → silent zero for Broad. Special's actual run also returned 0 rather than the predicted null — **unresolved, see appendix** | CF-CHUNK3-ZERO-CASES.md |
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

**Conditional fallback**

| Field | Fallback condition | Result | Source |
|---|---|---|---|
| `ProtectClass` (Contents-side factor) | Blank | Falls back to **0.0** for Contents (vs. Building's **1.0** fallback on the identical blank field) — Contents prices $0, Building rises, no message either way | CF-CHUNK4-GATE.md pt.4; CF-CHUNK4-TASKS.md C4-32 |
| Same factor, class 1751/1752 | Class 1751 | Falls back to 1.0 ($69 vs. true 0.96) | CF-CHUNK4-TASKS.md C4-18 |
| Same factor, class 1751/1752 | Protection class missing | Falls back to 0.0 (zero premium) — "two fallbacks in one rule" | CF-CHUNK4-TASKS.md C4-18 |
| Broad-form deductible factor | No `SetDeductibleFactorBroad` rule exists in PP at all — reads Building's ancestor value 4 levels up, whose own `Otherwise` is 0.0 | A blank building deductible silently zeros Contents' Broad premium instead of refusing | CF-CHUNK4-TASKS.md C4-21 |

**Documented but NOT one of the three categories** (derived unconditionally, submitted value silently discarded):

- `OccupCategoryRiskSeverity` — looked up from `OccupCategory` + the occupancy's own `ClassCode`, no `IsNull` guard; with no class code it's overwritten to blank, gating Special's base rate shut.
- The Basic Group I `Group` letter — derived from class code alone; a submitted `Group` is overwritten.
- Seven inherited/`Copy`'d fields — `CovForm`, `BldgClassCode`, `RatingType`, `OccupCategoryRiskSeverity`, `TheftDeductible`, item `Deductible`, the class-code chain — a per-item value is accepted and silently discarded.

**Ambiguous** — `CauseOfLoss` (plain gating field, no "zero deriving rules" statement found); `TypeOfWatchmanSrvc` (required alongside the watchman credit, not confirmed pure).

---

## Business Income (chunk 5)

| Field | Category | If omitted | Source |
|---|---|---|---|
| `MfgPct`, `OtherPct`, `Combination1Factor`, `Combination2Factor` (the "Combined" `TypeOfRisk` blend) | Pure input | All four submitted via `FromConstant="0.0"` defaults — the null does **not** trigger the null-premium guard, it reaches the premium as $0, no message | CF-CHUNK5-TASKS.md C5-12; CF-CHUNK5-GATE.md pt.4 |

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
| `ClassDescription` | Pure input | The rating driver is prose, not a code — no rule derives it. Basic I and II both price $0; Broad/Special are unaffected (they key off a hardcoded literal / flat constant instead) | CF-CHUNK6-ZERO-CASES.md; CF-CHUNK6-TASKS.md structural note 1 |
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
| `Limit` | Probable pure input (not explicitly confirmed "zero deriving rules," but its absence **refuses** rather than defaults — consistent with no fallback path existing) | Engine refuses (null-premium guard) rather than pricing $0 | CF-CHUNK8-GATE-3-5.md C8-03 case 5; CF-CHUNK8-TASKS.md map pt.20 |

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
| `EQDeductibleTier` | `LookupEarthquakeDeductibleTier` is a real rule, but its backing table (`EarthquakeDeductibleTier.RateTable.csv`) has zero rows in every state and countrywide. `SetEQDeductibleTier` only fills the field if it's null, so it correctly stays null forever against this empty table — "a dead derivation for now, not a hidden live path." **Also one of the sub-limit path's 4 equality keys**, so a sub-limit submission must supply it directly | CF-CHUNK10-TASKS.md C10-02/C10-19; verified directly against the rule XML and table CSV |

**Silent submission-shape traps found only by running** (a distinct shape from a dead-derivation trap — these are ancestor-copy overwrites, not input-vs-derived questions):
- Contents' own `SetEQClass` is an unguarded ancestor-copy from the Structure — a value set directly on the Personal Property record is silently overwritten.
- Four more of Contents' "own" EQ factor rules (`SetSoftStoryModificationFactor`, `SetEQSprinkleredRiskFactor`, `SetBldgHeightFactor`, `SetBCEGEQFactor`) are also ancestor-copies — Contents needs the Structure's own `SprinklerSystem`/`BCEG` populated correctly even when Building itself isn't EQ-elected.
- `BCEGEQFactor` defaults to **0.0** (not 1.0) on a blank `BCEG` — a genuine zero-collapses-the-premium case.
- `EQSprinklerLeakageOnly` blank satisfies neither branch of `SetEQDeductibleFactor` (no `Otherwise`) — starves `FinalEQRate`.
- Blank `SprinklerSystem` is read as "has a sprinkler," not "None" — silently adds a 1.06 factor instead of a no-op.

**Path-selectors** — `EQCovIndicator` (`"No Coverage"` / `"Not Applicable"` / `"Yes, Not Included in Blanket"` / `"Yes, Included in Blanket"` — two of the four collapse to the same "endorsement never created" outcome, the other two to "created, computed to $0"); `EQCauseOfLossForm` (selects among 4 Endorsement files — plain percentage, plain flat-dollar, sub-limit+percentage, sub-limit+flat-dollar — with destructive `Else` branches on the ones not selected); `CovType` (Building/Improvements and Betterments/Condominium Association/Builders Risk/Legal Liability/Leasehold Interest).

**Note on `EQCoinsuranceFactor`**: unlike every other EQ-prefixed factor, this one actually **shares** the ordinary chain's `CoinsuranceFactor` table (same `MatrixDef`) rather than being EQ-only — the one exception to "EQ shares zero multipliers with the ordinary chain."

---

## Appendix — ambiguous fields flagged across multiple chunks, needs verification

These fields were repeatedly treated as inputs in worked examples but no chunk's docs ever stated "zero deriving rules anywhere" for them. Listed here rather than asserted into a category:

- `BasicGroupIRatingTerr` / `BasicGroupIIRatingTerr` — used as lookup keys throughout, weaker phrasing than the confirmed pure inputs above.
- `Coinsurance` (raw percentage, appears on Blanket Detail records and elsewhere) — never explicitly labeled.
- `FullBldgValue` — a given in every worked example, never confirmed derivation-free.
- `TypeOfWatchmanSrvc` (chunk 4) — required alongside a confirmed pure input, not itself confirmed.
- `IRPMFactor` / `PackageModFactor` — only their *read depth* (how many `../` hops) is documented across chunks 8–10; their own derivation status (submitted vs. somehow computed) is never stated.
- Special form's `Deductible`-removed case (chunk 3) — predicted null, actual run returned 0; the docs never resolve why.
