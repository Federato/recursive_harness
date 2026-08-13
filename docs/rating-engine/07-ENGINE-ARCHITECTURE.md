# 07 — Engine Architecture & Calculation Pipeline

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R4). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

---

## 7.1 Shape of the system

```
 ┌───────────────────────────────────────────────────────────────────┐
 │  INGESTION  (offline, versioned, re-runnable)                     │
 │    PDF ──► text (2 modes) ──► parsers ──► staged facts ──► load   │
 └───────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │  MANUAL STORE   source_document · manual_edition · rule_concept   │
 │                 state_deviation · ilf_table · ilta_assignment     │
 │                 classification · state_variable                   │
 └───────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
 ┌──────────────────────────────┐  ┌───────────────────────────────┐
 │  RESOLVER                    │  │  RATE / TERRITORY / SUPPLEMENT│
 │  (jurisdiction, coverage,    │  │  ADAPTERS   ← external sources│
 │   effective_date)            │  │  (loss costs, ZIP→territory,  │
 │   ──► EffectiveRulebook      │  │   ELP, terrorism)             │
 └──────────────────────────────┘  └───────────────────────────────┘
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │  CALCULATION KERNEL   Rule 21 pipeline, per coverage              │
 │       emits premium + full rating_trace + referrals               │
 └───────────────────────────────────────────────────────────────────┘
```

The **Resolver** is the component that earns its keep. Everything about the manual's
two-layer overlay structure is confined to it; the kernel downstream sees a flat, already-
resolved rulebook.

---

## 7.2 The Resolver

**Input:** `(jurisdiction, coverage_key, effective_date)`
**Output:** an immutable `EffectiveRulebook` — a fully materialised rule set with every state
deviation already applied, plus the state variable bag and the ILF/ILTA tables.

```
resolve(juris, coverage, as_of):
    cw_ed    := edition WHERE scope='COUNTRYWIDE'
                  AND as_of BETWEEN effective_from AND COALESCE(effective_to,'infinity')
    st_ed    := edition WHERE scope='JURISDICTION' AND jurisdiction=juris
                  AND as_of BETWEEN effective_from AND COALESCE(effective_to,'infinity')

    book     := clone(rules of cw_ed)                       # keyed by rule_key

    for dev in state_deviation(st_ed) ordered by rule_key, target_path:
        concept := resolve_number(dev.printed_number, st_ed.rule_numbering_id)   # ← §7.4
        apply(book[concept], dev.op, dev.target_path, dev.body_text)

    book.a_rules   := state_additional_rule(st_ed)
    book.variables := state_variable(st_ed)
    book.ilf       := ilf_table + ilf_factor (st_ed)
    book.ilta      := ilta_assignment (st_ed)
    return freeze(book)
```

### Overlay application order

Deviations are **not** commutative when they target overlapping paths. Apply in this order,
which mirrors how the exception pages read:

1. `REPLACE` at whole-rule scope (`target_path IS NULL`) — wholesale substitution first.
2. `REPLACE` at paragraph scope, most-specific path last (`C` before `C.2` before `C.2.a`).
3. `ADD`.
4. `DELETE` (*"does not apply"*) — applied last so it can suppress content added above.

A `REPLACE` whose body is *"This rule does not apply"* (observed in TX Rule 34) is materialised
as a rule marked `inoperative = true`, **not** deleted from the book — the engine must still be
able to report *why* nothing was applied.

### Caching

`EffectiveRulebook` is pure and deterministic. Cache on
`(jurisdiction, coverage, cw_edition_id, state_edition_id)`. Invalidate only on ingestion of a
new notice. There are 51 jurisdictions × a handful of live editions — the entire resolved set
fits comfortably in memory.

---

## 7.3 Calculation kernel — the Rule 21 pipeline

Implemented once, parameterised per coverage, because Rules 21, 45.I, 46.J and 48.I are the
same 8–9 step shape with different operands.

> This section specifies the **A1 archetype** kernel. Four further archetypes — A2 (no
> premium-base step, no deductible), A3 (factor applied to a host subline's rate), A4 (modifier
> chain), A5 (refer-to-company) — cover the remaining coverages, and each is specified
> step-by-step in **[`11-RATING-ARCHITECTURE.md`](11-RATING-ARCHITECTURE.md)** §11.4–11.7.
> Two ordering constraints from that document bind this kernel:
>
> - **A3 coverages depend on a host subline.** Product Withdrawal, Loss Of Electronic Data and
>   Cyber Incident Liability all scale the Products/Completed Operations (or Premises/
>   Operations) rate by a published factor, so the host must rate first. Order coverages
>   topologically on `coverage_part.host_coverage_key`.
> - **Rule suspensions run before STEP A.** Paragraph B of a coverage rule switches off named
>   Section I general rules (`06-DATA-SCHEMA.md` §6.11) — most consequentially, Liquor replaces
>   the entire Rule 15 deductible machinery with Rule 45.J.
>
> **Step C is no longer an external stub.** The state loss cost pages supply it
> (`13-LOSS-COSTS-AND-ELP.md`), and it turns out to be a five-way *resolution* rather than a
> lookup — including a recursive path where one class's rate is a percentage of another's.
> The rate adapter interface survives; what it returns is now sourced, not stubbed.

```
STEP A  classify
        → classification(class_code) from the CW edition
        → reject if coverage = PROD_COMPOPS and classification.has_prodcompops = false   [Rule 48.F.1]

STEP B  exposure base
        → base := classification.base                                          [Rule 24]
        → if base = PAYROLL: apply state payroll limitation by SHAPE           [state var]
             ANNUAL_CAP_BOTH              → min(reported, exec_annual) per officer
             WEEKLY_MINMAX_EXEC+ANNUAL_IND→ clamp(weekly, wk_min, wk_max) × weeks;
                                            individuals/co-partners at annual amount
             ANNUAL_INDIV_ONLY            → annual amount for individuals/co-partners
        → apply seasonal reduction if present (x% per full week beyond twelve)

STEP C  basic limits rate           ← state loss cost pages (13-LOSS-COSTS-AND-ELP.md)
        → territory := resolve_territory(jurisdiction, subline, risk_location)
             subline ∈ {335, 336, 350}     → '999'                      [CG-T-1, always]
             scheme = ENTIRE_STATE (20)    → '001'
             scheme = ZIP_TABLE   (27)     → territory_zip[risk.zip]     [CG-T-2..n]
             scheme = COUNTY_CITY (4)      → territory_place[county, place]
                                             ; unmatched → REFERRAL, never a fuzzy match
             (territory applies to sublines 334 and 332 only)
        → cell := loss_cost(jurisdiction, lc_edition, subline, territory, class_code)
             numeric      → rate := cell × company LCM                         [Rule 23.B]
             '-'          → REJECT this subline for this class                 [Rule 48.F.1]
             '(a)'        → elp := elp(jurisdiction, lc_edition, subline, class_code)
                              '$n.nn'  → rate := elp × LCM, claims-made adjusted [ELP Proc.1.E]
                              'Incl.'  → premium := 0; already in the host subline
                              'RTC'    → REFERRAL
                              absent   → loss_cost_mapping: rate := pct% × resolve(source_class)
                                         (recursive; detect cycles)             [CG-LCADD]
        → separate resolution for PREM_OPS and PROD_COMPOPS                    [Rule 23.A/B]
        → LCM remains a carrier input; every stored value is a pre-LCM ISO loss cost

STEP D  coverage adjustments other than deductible                             [Rule 21.D]
        → claims-made multiplier for PROD_COMPOPS                              [Rule 48.D.6]

STEP E  limits + deductible
        → ilta := ilta_assignment(class_code)                                  [Rule 56.C]
        → prem_ops_table := digit(ilta.raw_code);  prod_table := letter(...)   [Rule 15.D.2]
        → ilf := ilf_factor(table, occurrence_limit/1000, aggregate_limit/1000)
        → if cell.refer_to_company → emit REFERRAL, stop this line             [Rule 56.A.2]
        → if cell absent → interpolate per Rule 56.A.4; if either limit absent → REFERRAL
        → if medical payments increased:
              ilf := medpay_factor(group, medpay_limit) + ilf - 1              [Rule 23.D.2.c]
        → if split limits:
              ilf := bi_w×ilf_BI + pd_w×ilf_PD + constant                      [Rule 23.D.5]
        → deductible factor applied to the BASIC LIMITS RATE, not to ilf       [Rule 15.D.4]

STEP F  premium := exposure_units × adjusted_rate      (per classification)    [Rule 21.F]

STEP G  additional premiums
        → other coverages, endorsements, elevator/escalator charge (pre-2027)

STEP H  total := ΣF + ΣG                                                       [Rule 21.H]

STEP I  total := max(total, policywriting_minimum_premium)                     [Rule 21.I]
```

### Rounding

Rule 7 (Rounding Procedure) governs and is **countrywide-fixed** — no jurisdiction deviates
it. Rule 56.A.4.b additionally specifies interpolation rounding: *"All fractions in the third
decimal place shall be considered as an additional unit in the second decimal place."*
Implement as an explicit, tested `round_half_up(x, 2)`; do **not** rely on the host language's
default float rounding (banker's rounding will produce off-by-a-cent drift that compounds
across a multi-class policy).

Use fixed-point decimal throughout. Never IEEE-754 floats for money or factors.

---

## 7.4 Edition-safe rule resolution (the critical path)

Every state deviation stores a **printed number** plus the `rule_numbering_id` of the edition
it was authored against. Resolution is always:

```
concept := rule_number_map[state_edition.rule_numbering_id][printed_number].rule_key
```

**Never** `rule_number_map[current_cw_scheme][printed_number]`.

Failure mode if done wrong, using real data: a state overlay authored against `CW-2022`
deviating **Rule 22** means *Description Of CGL Coverage*. Resolved against `CW-2027`, Rule 22
is *Mandatory Endorsements*. The engine would apply a coverage-description exception to the
mandatory-endorsement logic — no error raised, wrong forms attached, wrong premium.

**Guardrail:** the resolver must assert that the deviation's `printed_title` matches the
`printed_title` in `rule_number_map` for the resolved scheme. A mismatch is a hard failure,
not a warning. Both values are captured at ingest specifically to enable this check.

---

## 7.5 Referral handling

`REFER_TO_COMPANY` is a first-class outcome, not an exception. It arises from at least five
distinct sources, and the engine must distinguish them because they route differently:

| Source | Trigger | Route |
|---|---|---|
| Coverage-level | Rules 41, 42, 43, 47, 53 — *"Premium Determination — Refer to company"* | Underwriter pricing |
| Table cell | ILF cell in the flagged block (Rule 56.A.2) | Underwriter approval of limit |
| Off-table limit | Neither limit present in the ILF table (Rule 56.A.4.c) | Underwriter |
| Rule 34 | *Special Rule For Individual Risk Situations* (deviated in 37 jurisdictions; several replace it with *"This rule does not apply"*) | Jurisdiction-dependent — may be unavailable |
| No manual rate | Rule 2.B — ELP Supplement applies | ELP adapter |
| **Input-conditional** | A Declarations field flips a rated coverage to refer-to-company — Product Withdrawal Participation Percentage / Cut-off Date (Rule 44.A.5.a.f/g), non-owned unmanned aircraft (Rule 37.C.2.a) | Underwriter pricing of the delta |
| **Minimum premium** | Rule 40.B — *"Refer to company for minimum premium"* for LoED and Cyber | Underwriter |
| **Endorsement removal** | Removing a `CONDITIONAL_MANDATORY_MULTISTATE` form already inside the loss cost | Underwriter credit |

Each referral carries `rule_key`, `edition_id` and `span_id`, so the underwriter sees the exact
manual paragraph that forced the referral.

The last three rows are why referral eligibility is modelled as **predicates over the request**
(`06-DATA-SCHEMA.md` §6.13) rather than a static per-coverage boolean: the same coverage is
algorithmic or referred depending on what the Declarations carry.

---

## 7.6 Concurrency, determinism, testability

- The kernel is a **pure function** of `(EffectiveRulebook, RatingRequest, RateSet)`. No I/O,
  no clock, no global state. This makes golden-file testing trivial and makes historical
  re-rating exact.
- `effective_date` is an **input**, never `now()`.
- All external data (rates, territory, ELP, terrorism) enters through adapter interfaces so
  the engine is buildable and fully testable **today**, against this corpus, with stubbed
  rates. That is the key sequencing insight: *absence of the rate tables does not block the
  build.*

---

## 7.7 Recommended technology posture

| Concern | Recommendation | Reason |
|---|---|---|
| Numeric type | Fixed-point decimal | Rounding rules are explicit and legally material |
| Rule storage | Relational + JSONB for rule bodies | Bodies are free text; the *structure* around them is relational |
| Kernel language | Statically typed, decimal-native (C#, Java, Kotlin, or Python + `decimal`) | Correctness over throughput; volumes are modest |
| Rulebook cache | In-process, immutable, keyed by edition pair | ~51 jurisdictions × few editions |
| Trace | Emitted always, not behind a debug flag | It is the audit artefact, not a diagnostic |

---

## 7.8 Explicitly rejected designs

| Rejected | Why |
|---|---|
| **One code module per state** | Contradicted by the evidence: states supply operands and a bounded set of typed operations against one shared algorithm. 51 modules would duplicate ~90% of logic and drift. |
| **Flattening CW + state into one merged rulebook at ingest** | Destroys the ability to answer *"is this behaviour countrywide or a state exception?"* — which is exactly what filing and audit work requires. Flatten at resolve time, in memory. |
| **Keying rules by printed number** | Broken by the 2027 renumbering of 21 rules (§7.4). |
| **Storing ILF factors as a flat list of (limit, factor)** | The tables are genuinely two-dimensional (aggregate × occurrence) and are split into usable / refer-to-company blocks. A flat list cannot represent either. |
| **Treating payroll limitation as one numeric column** | Three distinct shapes exist across 51 jurisdictions; five jurisdictions use a weekly min/max band with no annual executive cap at all. |
| **Deferring the build until rate tables arrive** | Rates enter via one adapter interface. Everything else — the entire rule and deviation surface — is complete in this corpus. |
