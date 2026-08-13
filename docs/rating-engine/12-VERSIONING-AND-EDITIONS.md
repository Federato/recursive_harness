# 12 — Versioned Instances: The Countrywide Base Over Time

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R1). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

How the engine holds the countrywide manual as a base, overlays each jurisdiction, and lets
the whole thing evolve across editions without breaking policies already written.

This document answers one question: **given a risk, a jurisdiction and a date, which rulebook
runs — and how does that stay correct when ISO publishes the next edition?**

---

## 12.1 What "a version" actually is in this corpus

There is no single versioned artifact. A rating instance is composed from **three
independently versioned streams**, plus a fourth that is state-only.

| Stream | Artifact | Cadence in corpus |
|---|---|---|
| **Countrywide base** | `GL-MU-<YYYY>-RU-<NNN>-C` | **4 editions**: 2022-001, 2023-001, 2023-002, 2027-001 |
| **State exception overlay** | `GL-<ST>-<YYYY>-RU-<NNN>-C` | **490 notices**, 5–17 per jurisdiction |
| **State rate layer** | `GL-<ST>-<YYYY>-LC-<NNN>-C` | **471 notices**, 4–11 per jurisdiction. **No countrywide counterpart exists** |
| **State-only rules (A-rules)** | inside the state notice | e.g. Terrorism Premium Determination (48 juris.), Stop Gap (5) |

> **The rate stream was added at Step 7.** It moves on its own cadence, is never bundled with a
> rules notice, and has no countrywide layer at all — the mirror image of the countrywide base,
> which holds the algorithm and no numbers. A jurisdiction routinely holds a rules notice and a
> loss cost notice with different effective dates, and **both** are required to produce a
> premium.

Corpus distribution by edition year:

| Year | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | 2027 |
|---|---|---|---|---|---|---|---|
| Notices | 31 | 99 | 165 | 38 | 55 | 63 | 39 |

Notices per jurisdiction range from **5 (fewest) to 17 (Illinois)**; the median jurisdiction
carries **9**. So the state stream churns roughly **2–4× faster** than the countrywide stream.

> **The first architectural consequence.** The two streams are not versioned together and do
> not move together. A jurisdiction can be three notices ahead of where it was when the current
> countrywide edition was published, and a countrywide edition can land while every state
> notice still references the prior numbering. Any model that carries a single "manual version"
> field is wrong on day one.

---

## 12.2 Why "base + override" is the wrong mental model

The intuitive design — load countrywide, apply state deltas — fails on three documented facts.

**1. The base is incomplete by design.** Rule 56.B: *"The increased limits tables are displayed
in the state exceptions."* There is **no countrywide ILF table**. The CW layer cannot produce
a premium for any jurisdiction, so the state layer is not an override — it is a required
component. Composition, not inheritance.

**2. Rule numbers are edition-scoped labels, not identifiers.** The 2027 edition renumbers
**21 rules**. The dangerous cases are not the moves but the **reuses**:

| Rule # | CW 2022 / 2023 meaning | CW 2027 meaning |
|---|---|---|
| **22** | Description Of CGL Coverage | **Mandatory Endorsements** |
| **21** | *(absent)* | **Premium Determination** |
| **35** | **Premium Determination** | *Reserved For Future Use* |
| **16** | Additional Interests | **Additional Insured Endorsements** |
| **55** | Terrorism Endorsement Options — Federal Backstop | **Terrorism** |

A state notice saying *"Rule 22 is replaced by the following"* means **Description Of CGL
Coverage** if it was written against 2022, and **Mandatory Endorsements** if written against
2027. Resolving that overlay against the wrong edition's numbering silently attaches an
exception to the wrong rule. This is the highest-severity correctness risk in the build.

**3. State-only rules have nothing to override.** 48 jurisdictions carry a *"Terrorism Premium
Determination"* A-rule; 5 carry Stop Gap — Employers Liability. No countrywide counterpart
exists. An override model has no slot for them.

---

## 12.3 The versioned instance model

### 12.3.1 Key on semantics, display the number

Every rule gets a **stable semantic key** that never changes across editions. The printed rule
number becomes an edition-scoped *attribute*.

```
rule_key        GL.PREMIUM_DETERMINATION          ← stable, forever
  ├─ edition CW_2022  → printed number 35,  title "Premium Determination"
  ├─ edition CW_2023  → printed number 35,  title "Premium Determination"
  └─ edition CW_2027  → printed number 21,  title "Premium Determination"

rule_key        GL.MANDATORY_ENDORSEMENTS
  └─ edition CW_2027  → printed number 22   ← same number, different key, than CGL_DESCRIPTION
```

Two invariants follow, and both should be enforced in code, not convention:

- **I1.** A state overlay is parsed with the numbering of *the edition it was written against*,
  then stored against the resolved `rule_key`. Never re-resolved later against a newer edition.
- **I2.** `(edition, printed_number)` → `rule_key` is many-to-one over time and must never be
  inverted globally. Any code path that looks up a rule by bare number is a defect.

### 12.3.2 Three-part composition

A resolved instance is:

```
RatingInstance(jurisdiction, effective_date) =
      CW_edition_effective_at(effective_date)                    # base rulebook
    ⊕ state_notice_effective_at(jurisdiction, effective_date)    # typed operations
    ⊕ state_only_rules(jurisdiction, effective_date)             # A-rules, no CW counterpart
    ⊕ lc_edition_effective_at(jurisdiction, effective_date)      # loss costs, ELPs, territories
```

The fourth term resolves **independently** of the first three. It is not an overlay on
anything — there is no countrywide rate layer for it to override — and its effective date is
its own.

`⊕` applies the typed operations already catalogued in `04-STATE-DEVIATIONS.md`:

| Operation | Effect on the composed rulebook |
|---|---|
| `REPLACE` | Substitute the CW paragraph at `rule_key` + paragraph path |
| `ADD` | Insert an additional paragraph under `rule_key` |
| `DOES_NOT_APPLY` | Mark the CW paragraph inert for this jurisdiction |
| `TABLE` | Supply a lookup the CW layer does not carry (ILFs, liquor grades, payroll limits) |
| `A_RULE` | Introduce a rule with `rule_origin = STATE_ONLY` |

Composition is at **paragraph** granularity, not rule granularity. States routinely replace
one paragraph of a rule and leave the rest countrywide — replacing the whole rule would
discard countrywide content the state never touched.

### 12.3.3 Bitemporal, because re-rating is not optional

Two independent time axes, and they do not collapse:

- **Effective time** — when the rule applies to a policy term.
- **Knowledge time** — when the engine learned about it (the filing/ingestion date).

A mid-term endorsement rated in 2027 against a policy incepting in 2025 must use **the 2025
rulebook as it stood**, not today's. A correction ingested later must be replayable against
the terms it affects. Storing only effective dates makes the audit question *"why did this
policy rate this way in March?"* unanswerable.

```
rating_instance(jurisdiction, effective_date, as_of_knowledge_date) → immutable snapshot hash
```

The snapshot hash is what a quote, a policy term, and every downstream statistical record
should carry. Two rating runs of the same risk that produce different premiums must differ in
their hash, or one of them is a bug.

---

## 12.4 Instance resolution, step by step

```
resolve(jurisdiction J, effective_date D, knowledge_date K):
  1  cw   ← latest CW edition with effective ≤ D, known ≤ K
  2  st   ← latest J notice with effective ≤ D, known ≤ K
  3  assert st.written_against_edition is recorded          # never inferred at resolve time
  4  ops  ← st.operations, each already bound to a rule_key at ingestion
  5  book ← cw.rules
     for op in ops:  book ← apply(book, op)                 # paragraph-level
  6  book ← book ∪ st.state_only_rules
  7  assert book has an ILF table for every rated subline    # the CW layer cannot supply one
  8  return Snapshot(book, hash)
```

Step 3 is where most of the risk lives. **The edition a notice was written against must be
captured at ingestion**, from the notice itself, and stored. Inferring it later from dates is
guesswork: `01-SOURCE-CORPUS.md` records that **264 of 503 PDFs were dated by edition-date
proximity only ("low confidence")**, and effective dating drives edition selection, which
drives premium. Every low-confidence date is a latent mis-resolution.

Step 7 is a **hard assertion, not a warning**. A composed book with no ILF table is not a
degraded rulebook; it cannot rate. Failing loudly at composition beats producing a number that
silently used basic limits.

---

## 12.5 How an edition change actually lands

Classify every diff between two editions into one of seven types. The type determines the
migration action, and only two of the seven are safe to automate.

| Change type | Example from CW 2022 → 2027 | Migration action |
|---|---|---|
| **Renumber** | Premium Determination 35 → 21 | Map to existing `rule_key`; **auto** |
| **Retitle** | Rule 1 Application Of This Division → Overview Of The GL Program | Update display title; **auto** |
| **Number reuse** | Rule 22 changes meaning entirely | **Manual review — blocking.** New `rule_key`; re-audit every state overlay citing 22 |
| **New rule** | Rule 40 Cyber / Loss Of Electronic Data; Rule 17 Coverage Part | New `rule_key`, new executor, new tables |
| **Withdrawn** | Rule 51 Elevator Or Escalator Inspection Charge; Rule 50 Sports Participants; Rule 52 Injury To Leased Workers | Retain for prior terms; **never delete** |
| **Reserved** | Rule 3 Effective Date, Rule 14 Minimum Premiums, Rule 54 Y2K → *Reserved For Future Use* | Mark inert from this edition forward |
| **Form set change** | **40 forms added**, **21 forms dropped** (`A3-ENDORSEMENT-CATALOG.md` §A3.4) | Edition-scope the catalog |

Three of these deserve emphasis:

**Withdrawn rules must survive.** Rule 51's Elevator Or Escalator Inspection Charge is an
additive premium in CW 2022 and absent from CW 2027. A 2023-inception policy still rates it. A
schema that deletes withdrawn rules cannot re-rate its own back book.

**Dropped forms are still valid on prior terms.** 21 forms present in CW 2022 do not appear in
CW 2027. Validating a 2022-edition policy's form list against the 2027 catalog would reject
legitimate policies. The catalog is edition-scoped, and validation always runs against the
policy's own edition.

**Number reuse blocks the migration.** When a rule number changes meaning, every state overlay
citing that number must be re-audited before the edition can be activated. This is the one
change type that cannot be shipped without human review.

### 12.5.1 The rate stream has its own change types — and one is live right now

The seven types above classify *rule* changes. The rate stream needs three more, and the
corpus contains a worked example of each in flight:

| Change type | Observed | Migration action |
|---|---|---|
| **Class-code revision** | The 2027 loss cost filing **retires 229 class codes and introduces 204** (`13-LOSS-COSTS-AND-ELP.md` §13.7) | A crosswalk is required to re-rate a pre-2027 risk under a 2027 edition. Neither corpus supplies one — open question Q7 |
| **Rate-source withdrawal** | The **OCP/PP published loss cost table is withdrawn**: 390/390 notices through 2026 carry it, only 22 of 58 2027 notices do | Fall back to the Table 5.C ELPs. **The premium does not error, it changes** |
| **Territory redefinition** | Territory sets are per-edition and non-contiguous | Re-key stored rates; never assume the prior domain |

**The 15/36 split is the live case.** As of the current corpus, 15 jurisdictions are on the
pre-2027 rate basis and 36 have migrated, and the same three tests select the same sets — this
is one filing rolling out state by state. Two consequences:

1. **A single national class list is wrong today.** Rate resolution must be keyed on
   `(jurisdiction, effective_date)`, never on a global class table.

> **[R1] Superseded 2026-08-11 — the counts, not the conclusion.** This paragraph counts the
> *latest notice* per jurisdiction, and some of those notices are future-dated. Measured as-of a
> date over the ERC corpus (`scripts/erc/31_migration_asof.py`): **today 51 jurisdictions are on the
> pre-2027 basis and 0 have migrated; on 2027-04-01, 43 migrate on the same day.** So it is **not**
> "one filing rolling out state by state" — it is a **cliff**, and it has not happened yet.
> Consequence 1 inverts: a single national class list is **right today** and wrong from 2027-04-01.
> Consequence 2 is unaffected and is exactly right — indeed the phrase *"as their 2027 notices take
> effect"* below is the future tense this document got right and its own headline lost. Requirement
> unchanged: key rate resolution on `(jurisdiction, effective_date)`.
> See [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) §1.
2. **This is precisely what the §12.6 replay gate exists to catch.** An engine that binds the
   OCP loss cost table at build time silently loses OCP rating in 36 jurisdictions as their
   2027 notices take effect. Nothing throws; the number moves.

### The state stream migrates independently

Because states churn 2–4× faster, the normal case is: a new state notice arrives, is parsed
against the countrywide edition it cites, and takes effect for that jurisdiction only. No
countrywide change, no global rebuild, no impact on other jurisdictions. Only a **countrywide**
edition triggers the seven-type diff above — and even then, each jurisdiction re-composes
lazily at its own next effective date.

---

## 12.6 Verifying an edition change

Adding an edition is a rating change until proven otherwise. Three gates:

1. **Replay.** Re-rate a corpus of stored risks under old and new snapshots. Every premium
   delta must map to an intended change in the diff table. **An unexplained delta blocks the
   release** — that is the whole point of the exercise.
2. **Resolution coverage.** For all 51 jurisdictions × the new edition, assert composition
   succeeds and step 7 holds (an ILF table exists for every rated subline). Coverage gaps show
   up here, before production.
3. **Overlay re-binding audit.** For every `rule_key` touched by a number reuse, list every
   state overlay that cited the old number and confirm each landed on the intended key.

Gate 1 is only meaningful with stored snapshot hashes (§12.3.3) — which is why the hash is
part of the data model rather than an operational nicety.

---

## 12.7 What this buys, concretely

| Question | Answer with this model |
|---|---|
| Why did this policy rate this way? | Replay its snapshot hash |
| A state files a new notice — what breaks? | That jurisdiction, from its effective date. Nothing else |
| ISO publishes a new CW edition — what breaks? | Only rules in the diff; states re-compose lazily at their next effective date |
| Can we re-rate a 2023 policy in 2028? | Yes — the 2023 snapshot is immutable and withdrawn rules were retained |
| Which jurisdictions actually deviate step *N*? | §11.10, driven off `rule_key`, not printed numbers |

---

## 12.8 Open items this model surfaces

- **264 low-confidence PDF dates** (`01-SOURCE-CORPUS.md`) feed step 1 and step 2 of
  resolution. These need reconciliation against the ERC edition hierarchy before any premium
  is trusted, because a wrong edition selection is invisible at runtime — it produces a
  plausible number.
- **26 ERC versions have no mapped manual** (`PROCESS_LOG.md` Step 3). Those are jurisdictions
  where step 2 can silently fall back to an older notice.
- **`GL-MO-2027-RU-003-C.pdf` is truncated** and must be re-downloaded before Missouri's 2027
  overlay can be composed.
- **Hawaii is absent from the corpus** — resolution for HI has no state stream at all, which
  by §12.4 step 7 means it cannot rate. A scope decision, not a bug to work around.
- **The edition each state notice was written against is not yet captured as a field.** It is
  currently inferable from the notice text but is not extracted. This is the highest-value
  remaining ingestion task, because invariant I1 depends on it.
