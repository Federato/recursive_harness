# CF validation message register

**A running log of every validation message ISO has actually returned to us**, what caused
it, how it was resolved, and what the resolution generalises to.

The point is not the diary. The point is that each message should make the *next* payload
better — either by changing how payloads are built, or by adding a check that catches the
same class of problem before a request is sent.

**Related:**
`CF_Validation_Messages.md` (what the whole rule set looks like) ·
`CF_Validation_Messages.xlsx` (all 1,621 rules) ·
`CF_Payload_ClassRated_Bldg_PP_Alabama.md` (the request spec) ·
`scripts/cf/07_diagnose_message.py` (the diagnostic)

**Opened:** 2026-09-17.

---

## The loop

**1 · Observe.** Paste the message into the register below — verbatim, with `TableName`,
the state, and the payload that produced it. `TableName` matters: the same message text is
filed on several coverages, and without it you will read the wrong rule.

**2 · Diagnose.** Run the rule down rather than guessing:

```bash
python scripts/cf/07_diagnose_message.py \
    --message "CP 03 20 Must Be Attached When Fixed Dollar" \
    --table   CommercialPropertyStructure \
    --state   AL \
    --payload CF_Algorithm/sample_payloads/AL_class_rated_bldg_pp_special.json
```

It finds the rule, decodes the condition, and prints every comparison with the value the
payload supplies and whether it is true — including field-to-field comparisons, which are
usually the deciding half and the easiest to miss by eye.

**3 · Classify.** Which of these is it?

| Class | Meaning | Typical fix |
|---|---|---|
| **Payload defect** | we sent something incoherent | fix the payload; consider a pre-flight check |
| **Spec gap** | the spec did not say a field was required or constrained | update the spec |
| **Missing endorsement** | a selection implies a form we did not attach | attach it — but check for the mirror rule first |
| **State-specific** | the rule exists only in that state's package | note it in the state's section of the spec |
| **ISO data defect** | the rule or the data behind it is wrong | log it, raise it, do not code around it |

**4 · Fix, and check the mirror.** Over half the rules are form-attachment checks, and some
come in opposing pairs: one fires if a form is missing, its mirror if the same form is
attached when it should not be. Before attaching anything, search the inventory for the
opposite message.

**5 · Generalise.** Write the lesson as a **missing check**, not as a thing to remember.
"Watch out for deductibles" is not a lesson. "Nothing compares the theft deductible against
the base deductible before we send" is.

---

## Register

| # | Date | State | Message (abbreviated) | TableName | Class | Status |
|---|---|---|---|---|---|---|
| M-001 | 2026-09-17 | AL | CP 03 20 Must Be Attached When Fixed Dollar Amount Deductible For Each Location Are Different Than Windstorm Or Hail Deductible Or Theft Deductible | `CommercialPropertyStructure` | Payload defect | **Resolved** |
| M-002 | 2026-09-21 | OR | Either CP 10 75 Or CP 10 76 must be attached | `CommercialProperty` | Designed out (not scheduled) | **Open, by design** |
| M-003 | 2026-09-23 | OR | CP 04 15 Debris Removal Additional Insurance must have a limit greater than $25,000 | `CommercialPropertyStructure` | Input validation, by filing (ISO-confirmed) | **Understood** |
| M-004 | 2026-10-02 | OR | Select a valid Theft Deductible with Theft Coverage included | `CommercialPropertyStructure`, `CommercialPropertySpecialClass` | Input validation, by filing (ISO-confirmed) | **Understood** |
| M-005 | 2026-10-02 | OR | Full Value cannot be lower than the Limit | `CommercialPropertyPersonalProperty`, `CommercialPropertySpecialClass` (and `Structure`) | Input validation, by filing (ISO-confirmed) | **Understood** |
| M-006 | 2026-10-02 | OR | Deductible not valid with Coverage form selected at Building and/or Occupancy Class levels | `CommercialPropertyStructure` | Input validation, by filing (ISO-confirmed) | **Understood** |

---

### M-001 — CP 03 20 must be attached

**Reported:** 2026-09-17, Alabama, from the first sample payload. **The submission rated**
and returned this alongside the premium.

**Rule:**
`DoMessageCP0320MustBeAttachedWhenFixedDollarAmountDeductibleForEachLocationAreDifferentThanWindstormOrHailDeductibleOrTheftDeductible`,
`CommercialPropertyStructureRules.Rule.xml`, countrywide — Alabama does not override it.

**Condition** — fires when all three hold:

1. `CovType` ∈ {`Building`, `Condominium Association`, `Builders Risk`,
   `Improvements and Betterments`} **or** `OccupClassCovFormInList` = `true`; **and**
2. **any** of —
   - `WindstormOrHailDeductible` not in {`1%`, `2%`, `5%`, `Not Applicable`} **and**
     ≠ `Deductible`
   - `TheftDeductible` ≠ `Not Applicable` **and** ≠ `Deductible`
   - `OccupClassTheftDedConditionsMet` = `true` — derived by comparing each **occupancy
     class's** `TheftDeductible` against the **structure's** `Deductible`; **and**
3. no `CommercialPropertyMultipleDeductibleFormFixedDollarDeductibles` record attached.

**Root cause — ours, not ISO's.** The sample carried `Deductible: "1,000"` with
`TheftDeductible: "2,500"` at both Structure and OccupClass. Two of the three sub-conditions
in (2) fired: the structure comparison directly, and the occupancy comparison through the
derived flag. The value `2,500` was chosen for realism with no thought about coherence.

**Fix applied.** Aligned `TheftDeductible` to `"1,000"` at both levels — verified legal in
`DomainBuildingTheftDeductible` for AL. All three arms of (2) now evaluate false.

**The alternative, for a risk that genuinely wants a separate theft deductible:** keep the
deductibles different and attach the CP 03 20 record, which makes (3) false instead.

> **Mirror rule exists.**
> `DoMessageMultipleDeductibleFormCP0320ShouldNotBeAttachedWithTheSameFixedDollarAmountDeductiblesForEachLocation`
> fires if the form is attached while the deductibles *are* the same. Different deductibles
> **and** the form, or the same deductibles **and** no form. Nothing in between.

**Lesson — stated as the missing check.** *Nothing compares a payload's deductible fields
against each other before the request is sent.* Three deductible fields
(`Deductible`, `TheftDeductible`, `WindstormOrHailDeductible`) exist at two levels, and
their coherence is a precondition ISO enforces but our builder does not test. The
generalisation is wider than deductibles: **the payload spec validates each field in
isolation — name, group, legal enum value — and nothing validates fields against each
other.** That is the gap M-001 exposed.

**Also produced:** the diagnostic script, because working this out by hand took about an
hour and should take a minute.

---

### M-002 — Either CP 10 75 or CP 10 76 must be attached

**Reported:** 2026-09-21, Oregon, from chunk 9's blanket golden case
(`scripts/cf/68_chunk9_golden_case.py`) — first observed narratively in chunk 1's own golden
case (`CF-CHUNK1-GOLDEN-CASE.md` §5, "three ISO validation messages fire on every case") but
never before entered here.

**Rule:** `DoMessageEitherCP1075OrCP1076MustBeAttached`, `CommercialPropertyRules.Rule.xml`,
countrywide, `DataDefGroup="CommercialProperty"` — a policy-level check, not
blanket-specific; chunk 9's own 4 blanket-specific `DoMessage` rules
(`CommercialPropertyBlanketRatingDetailRules.Rule.xml`) are a separate set and none of them
fired on this case (`scripts/cf/76_chunk9_c9-10_exclusion_messages.py`).

**Condition** — fires whenever **none** of three records is attached anywhere on the
policy: `CommercialPropertyMortgageholdersErrorsAndOmissionsCoverageForm`,
`CommercialPropertyCyberIncidentExclusion`,
`CommercialPropertyCyberIncidentExclusionWithEnsuingCausesOfLossExceptions`.

**Classification — designed out, not a defect.** CP 10 75 (Mortgageholders E&O) and CP 10
76 (Cyber Incident Exclusion) are optional endorsement forms unrelated to what every CF
golden case built so far (chunks 1–9) is testing — base rating and, in this chunk, blanket
averaging. No golden case in this project schedules either form, so this message is expected
on **every** one of them, not a defect introduced by chunk 9. Attaching a form solely to
silence a validation message the case isn't testing would be worse than leaving it —
per this register's own mirror-rule caution (M-001), attaching one of the three without
meaning to elect it risks tripping an opposing "should not be attached" rule instead.

**Lesson — stated as the missing check.** *Nothing in this project's golden-case builders
distinguishes "message this case's own coverage should produce" from "message every CF
case produces regardless of what it's testing."* The generalization from M-001 holds here
too: build a shared list of these policy-wide, always-on messages once (this one, plus the
two CP 03 20 variants any golden case with a non-degenerate deductible will also produce),
and check new golden cases only against the *residual* message set after subtracting it —
rather than re-diagnosing the same boilerplate message chunk to chunk.

---

### M-003 — CP 04 15 Debris Removal must have a limit greater than $25,000

**Reported:** 2026-09-23, Oregon, from chunk 12's Debris Removal zero cases
(`scripts/cf/128_chunk12_debris_removal_gates.py`, Z1/Z3/Z4) and confirmed live
(`scripts/cf/129_chunk12_c12-10_raas.py`: ISO returns the identical message set).

**Rule:** `DoMessageDebrisRemovalAdditionalInsuranceMustHaveGreaterLimit`,
`CommercialPropertyStructureRules.Rule.xml`. Fires when a Debris Removal record exists and its
`Limit` is at or below a hard-coded 25,000. Florida overrides it to $10,000, matching its own
`DebrisRemovalMinimumLimit` row.

**Classification — input validation, by filing.** It does not fire on the golden case (limit
60,000). It matters because it is the ONLY guard in front of a negative premium: the form
cells decide they are "on the policy" before `MinimumLimit` is looked up, so a limit below
the minimum rates at (Limit − MinimumLimit)/100 < 0. ISO does the same: limit 10,000 returns
−$21 / −$3 both sides. An error message, not a refusal, so a caller that ignores messages
would bill a credit.

---

### M-004..M-006 — the golden cases' input messages (chunk 27 RC-2)

**Reported:** 2026-10-02, Oregon, from the chunks 1–8 golden cases (`scripts/cf/239_chunk27_rc2.py --live`). Each fires
identically at ISO on the same request: same level, same text, same count.

* **M-004**, `DoMessageSelectAValidTheftDeductibleWithTheftCoverageIncluded` (Structure; SpecialClass has its own): cause
  of loss Special, theft not excluded, `TheftDeductible` blank or "Not Applicable", not multi-unit blanket. The Special
  golden cases send no theft deductible.
* **M-005**, `DoMessageFullValueCannotBeLowerThanTheLimit`: not in a blanket and `Limit` > the full value field
  (blank on the contents and Special Class golden cases). It does not stop the premium.
* **M-006**, the Legal Liability deductible check: a deductible sent with the Legal Liability coverage form (chunk 8's
  building cases, which keep chunk 2's deductible).

**Classification — input validation, by filing.** None moves a premium; each is a golden-case input the case was not
testing, and each is ISO's own message.

---

## Standing checks this register has produced

Each one is a check that does not exist yet. They are listed so that the next person builds
the check rather than re-learning the lesson.

| # | Check | From | Built? |
|---|---|---|---|
| C-1 | Deductible coherence: `TheftDeductible` and `WindstormOrHailDeductible` vs `Deductible`, at Structure **and** OccupClass, with CP 03 20 attached iff they differ | M-001 | **no** |
| C-2 | Mirror-pair awareness: before attaching any endorsement to silence a message, assert its opposite rule will not fire | M-001 | **no** |
| C-3 | A shared "always-on, policy-wide" message allowlist (CP 10 75/76, CP 03 20 on any non-degenerate deductible) subtracted from a golden case's own message list before calling anything unexplained | M-002 | **no** |

---

## What a pre-flight validator would be

The destination this register points at is a local check that runs the applicable
`DoMessage` conditions against a payload **before** it is sent, so messages are designed out
rather than discovered. The inventory needed for it already exists
(`CF_Validation_Messages.xlsx`, 1,621 rules with their conditions).

It is **not built, and should not be started without an explicit go** — evaluating rule
conditions is engine work, and the engine is deliberately unstarted. Until then this
register plus the diagnostic script is the loop: observe, diagnose in a minute, fix, and
record the check that was missing.
