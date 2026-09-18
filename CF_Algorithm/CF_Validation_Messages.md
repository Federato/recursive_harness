# CF validation messages — the `DoMessage` rules

**What this is.** ISO's Commercial Property ruleset carries a second body of logic alongside
rating: a large set of `DoMessage*` rules that check a submission for internal consistency
and return text. A payload can **rate correctly and still come back with messages** — that
is exactly what happened to the first sample payload built from
`CF_Payload_ClassRated_Bldg_PP_Alabama.md`.

**Companion data:** `CF_Algorithm/CF_Validation_Messages.xlsx` — one row per rule instance,
1,621 rows, filterable by jurisdiction, datadef group, check kind and the fields each rule
reads.

**Source:** the latest package of all 48 CF jurisdictions.
**Written:** 2026-09-17.

---

## 1. Everything is an "Error"

There is **one** message helper in the entire line — `AddErrorMessage`, called 621 times in
the countrywide ruleset. There is no `AddWarningMessage`, no informational variant, no
severity argument.

**So "Errors" in a RAaS response does not mean rating failed.** The response that prompted
this analysis rated *and* returned an error. Anything ISO wants to tell you about a
submission arrives in the same bucket, whether it is "this endorsement is mandatory here"
or "these two deductibles disagree".

Consumers of the API have to classify severity themselves. ISO does not.

---

## 2. How big the surface is

| | Count |
|---|---|
| Countrywide `DoMessage` rules | **434** |
| Rule instances across all 48 jurisdictions | **1,621** |
| Rules existing **only** in state packages | **233** |
| Distinct message texts | ~650 (971 of the 1,621 instances repeat a text used elsewhere) |

By record, countrywide:

| DataDefGroup | Rules |
|---|---|
| `CommercialPropertyStructure` | 554 |
| `CommercialPropertyPersonalProperty` | 296 |
| `CommercialPropertySpecialClass` | 185 |
| `CommercialPropertyBusinessIncome` | 134 |
| `CommercialProperty` (policy) | 112 |
| `CommercialPropertySpecialClassBusnIncome` | 110 |
| `CommercialPropertyLocation` | 37 |
| `CommercialPropertyOccupClass` | 12 |

**305 of the countrywide rules sit on the class-rated Building / Personal Property spine** —
the exact scope of the payload specification. The spec tells you what to *send*; these rules
decide whether what you sent is *coherent*. They are a separate body of knowledge and the
spec does not cover them.

---

## 3. States switch countrywide messages off

This is the finding that matters most, and it is invisible if you read countrywide alone.

**A state can suppress a countrywide message by overriding the rule with an empty body.**
Alaska, for example:

```xml
<rul:Rule Name="DoMessageFormCP1065NeedsAnUnderlyingCoverageSelectedToApply"
          Type="none" DataDefGroup="CommercialPropertyBusinessIncome"
          MetadataCodes="RuleTypeOverridden">
  <rul:Sequence />
</rul:Rule>
```

The countrywide version of that rule is 1,796 characters and emits *"Form CP 10 65 needs an
underlying coverage selected to apply"*. Alaska replaces it with nothing.

**316 such no-op overrides exist across the corpus**, and they are concentrated:

| State | Suppressed | Added | Overridden (real logic) | **Effective messages** |
|---|---|---|---|---|
| FL | **63** | 25 | 10 | 406 |
| PR | 49 | 15 | 45 | 400 |
| NY | 34 | 13 | 8 | 413 |
| KS | 20 | 12 | 9 | 426 |
| VT | 18 | 3 | 8 | 419 |
| TX | 10 | 4 | 6 | 428 |
| AK | 6 | 7 | 2 | 435 |
| CA | 3 | 24 | 12 | 455 |
| **AL** | **0** | **18** | 2 | **452** |

Across all 47 states: **240 suppressions and 356 additions.** The effective message count
ranges from **400 (PR) to 455 (CA)**, median 437.

**Consequence:** you cannot answer "will this submission produce a message?" from the
countrywide ruleset. The question is only answerable per jurisdiction, after applying the
state's overrides — including the ones that delete a rule rather than change it.

Alabama suppresses nothing and adds 18, six of which concern
`PublicInstitutionalPlanApply`.

---

## 4. What the rules actually check

Classifying the countrywide 610 instances by the shape of their condition:

| Check kind | Count | Meaning |
|---|---|---|
| endorsement present/absent **+** value combination | 263 | "given these values, this form must / must not be attached" |
| value combination | 178 | two or more fields disagree |
| endorsement present/absent | 60 | a record is simply required, or forbidden |
| threshold + value combination | 41 | a limit or percentage is out of range for the selection |
| threshold | 26 | a pure numeric bound |
| other | 4 | |

**The dominant pattern is form attachment.** Over half the rules are of the form *"you
chose X, therefore endorsement Y is mandatory (or prohibited)"*. That is what the sample
payload hit: differing deductibles make CP 03 20 mandatory.

### The fields that most often trigger a message

Counting across the 305 spine rules:

| Field | Rules | |
|---|---|---|
| `CovType` | 59 | by far the most contested field |
| `IncludedInBlkt` | 47 | blanket vs scheduled |
| `CovForm` | 29 | |
| `EQCovIndicator` | 27 | earthquake |
| `PolicyType` | 25 | |
| `CauseOfLossToUse` | 25 | |
| `EQCauseOfLossForm` | 16 | |
| `ClassCode` | 15 | |
| `Limit` | 15 | |

`CovType` topping the list is consistent with what the rating analysis already found: it is
the field with four different value universes depending on the coverage
(`CF_RatingPath_Switches.md`). It is both the most rating-significant switch and the most
validation-significant one.

---

## 5. The message the sample payload hit, as a worked example

`DoMessageCP0320MustBeAttachedWhenFixedDollarAmountDeductibleForEachLocationAreDifferentThanWindstormOrHailDeductibleOrTheftDeductible`
fires when **all three** hold:

1. `CovType` ∈ {`Building`, `Condominium Association`, `Builders Risk`,
   `Improvements and Betterments`} **or** the occupancy's `CovForm` is in a listed set; **and**
2. **any** of —
   - `WindstormOrHailDeductible` is a dollar amount (not `1%` / `2%` / `5%` /
     `Not Applicable`) **and** ≠ `Deductible`
   - `TheftDeductible` ≠ `Not Applicable` **and** ≠ `Deductible`
   - `OccupClassTheftDedConditionsMet` = `true` — itself derived by comparing each
     **occupancy class's** `TheftDeductible` against the **structure's** `Deductible`; **and**
3. no `CommercialPropertyMultipleDeductibleFormFixedDollarDeductibles` record is attached.

Two valid resolutions, and they are mirror images:

- **Align the deductibles.** Set `TheftDeductible` = `Deductible` at *both* Structure and
  OccupClass. Condition 2 goes false. This is what the sample now does.
- **Attach CP 03 20.** Keep them different and add the
  `CommercialPropertyMultipleDeductibleFormFixedDollarDeductibles` record. Condition 3 goes
  false.

> **They cannot be mixed.** A mirror rule,
> `DoMessageMultipleDeductibleFormCP0320ShouldNotBeAttachedWithTheSameFixedDollarAmountDeductiblesForEachLocation`,
> fires if you attach the form while the deductibles *are* the same. Different deductibles
> **and** the form, or the same deductibles **and** no form — nothing in between.

This shape — a rule and its mirror — recurs throughout the set, and is why "just attach
every endorsement" is not a strategy.

---

## 6. What this means for building submissions

1. **Treat "Errors" as "messages".** Severity is the caller's judgement, not ISO's. A
   premium can be returned alongside an error.
2. **Validation is per-jurisdiction, like rating.** The countrywide set is a starting point
   that 47 states then edit — including by deletion.
3. **Most messages are about form attachment, not bad data.** They usually mean a coverage
   selection implies an endorsement the submission did not include.
4. **Some rules come in mirrored pairs.** Attaching a form to silence one message can raise
   its opposite.
5. **The payload spec does not cover this.** It describes a *well-formed* request. A
   well-formed request can still be internally inconsistent by ISO's rules.

---

## 7. What has not been done

- **No reachability analysis.** 1,621 rules were inventoried by reading their conditions;
  none were evaluated against a submission. Which of the 452 messages live in Alabama could
  fire for a given payload is not answered here.
- **Condition parsing is structural, not semantic.** The "Fields tested" and "Check kind"
  columns come from pattern-matching the XML. Nested conditions are flattened, so a rule
  reading eight fields may only need two of them in any given branch.
- **Messages were not deduplicated by text.** 971 of the 1,621 instances repeat a text used
  elsewhere, usually the same check applied to a different coverage.
- **The mirrored-pair relationships are not mapped.** CP 03 20's pair was found by hand
  while chasing one message. There is no systematic list of which rules oppose each other,
  and that is probably the most useful next step.
