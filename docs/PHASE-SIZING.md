# Phase sizing, measured

**Filed 2026-08-11**, immediately after [`gates/OI-40-ASOF-RECOUNT.md`](gates/OI-40-ASOF-RECOUNT.md)
closed the as-of audit that gated it. Reproduce with:

```
python scripts/erc/33_phase_sizing.py 20260811 20270401
```

As with every measurement script in this project, **the as-of date is a required argument**. Output
of the run behind this document is kept at `scripts/erc/out/phase_sizing.txt`.

This does **not** estimate effort. It counts what each build-order item contains, from the packages
in force as of a date. Effort follows from the counts; the counts do not follow from an estimate.

---

## 1. What was measured, and why each column matters

| Column | Meaning | Why it sizes work |
|---|---|---|
| **CW rules** | Distinct rule names in the countrywide parent for that coverage | The algorithm to port |
| **variants** | How many **distinct rule sets** the countrywide parents in force hold, compared by **whitespace-normalised body**, not by name or count | **The number of calculators the phase must build** |
| **bodies differ** | Rules whose body differs from the first parent's, worst case | How far apart those calculators are |
| **state rules / juris** | Distinct state rule names, and how many jurisdictions file one | The deviation surface |
| **tables / populated** | Rate tables the rules read, and how many any jurisdiction fills | Fixture and assertion surface |

**The `variants` column is the one that changes plans**, and it exists because of a mistake this
measurement nearly made: the first version of the script compared *rule counts* across parents and
reported `same` for five of the eight items. Comparing *bodies* shows that was wrong in every case.

---

## 2. As of today — 51 jurisdictions, 3 countrywide parents in force

| Build-order item | CW rules | Variants | Bodies differ | State rules | Juris | Tables | Populated |
|---|---|---|---|---|---|---|---|
| 1 Prem/Ops (334) | 100 | **2 of 3** | 40 | 71 | 19 | 110 | 86 |
| 2 Prods/CompldOps (336) | 90 | **2 of 3** | 33 | 9 | 17 | 30 | 8 |
| 3 OCP (335) | 58 | **2 of 3** | 17 | 4 | 2 | 20 | 8 |
| 4 Liquor (332) | 50 | **2 of 3** | 12 | 11 | 8 | 20 | 6 |
| 5 Railroad Protective | 65 | **2 of 3** | 21 | 3 | 2 | 18 | 4 |
| 6 Withdrawal / LoED / Cyber | **150** | **2 of 3** | 50 | 17 | 9 | 20 | 10 |
| 7 Unmanned Aircraft (370) | 62 | **2 of 3** | 11 | 14 | 9 | 16 | 7 |
| 11 NY Special Protective & Highway | 0 | 1 | 0 | 35 | 1 | 10 | 3 |
| 11 MD lead hazard | 0 | 1 | 0 | 14 | 1 | 3 | 2 |
| 11 MA lead poisoning ×2 | 0 | 1 | 0 | 26 | 1 | 5 | 4 |

## 3. As of 2027-04-01 — same 51, still 3 parents, but a different three

| Build-order item | CW rules | Variants | Bodies differ | State rules | Juris | Tables | Populated |
|---|---|---|---|---|---|---|---|
| 1 Prem/Ops (334) | 100 | **3 of 3** | 51 | 68 | 18 | 111 | 84 |
| 2 Prods/CompldOps (336) | 90 | **3 of 3** | 42 | 9 | 17 | 31 | 8 |
| 3 OCP (335) | 58 | **3 of 3** | 27 | 4 | 2 | 20 | 8 |
| 4 Liquor (332) | 50 | **3 of 3** | 15 | 11 | 8 | 20 | 6 |
| 5 Railroad Protective | 65 | **3 of 3** | 39 | 3 | 2 | 19 | 5 |
| 6 Withdrawal / LoED / Cyber | **150** | **3 of 3** | 64 | 17 | 9 | 21 | 6 |
| 7 Unmanned Aircraft (370) | 66 | **3 of 3** | 19 | 12 | 9 | 16 | 7 |
| 11 State-specific (unchanged) | 0 | 1 | 0 | 93 | 3 | 19 | 9 |

---

## 4. The finding that resizes the build: **three calculators, not two**

Gate 334 concluded *"Both CW 2023 and CW 2027 calculators required"*. That is a **countrywide-parent
census taken over the whole corpus**. Restricted to the parents actually in force, the picture is
different and worse:

| Countrywide parent | States declaring it **today** | Prem/Ops rules | Bodies differing from V02 |
|---|---|---|---|
| `GL_CW_20231201_V02` | **1 — California** | 100 | — |
| `GL_CW_20231201_V03` | 4 — NJ, OK, TX, VT | 100 | **40** |
| `GL_CW_20260101_V01` | 46 | 100 | **40** *(byte-identical to V03)* |
| `GL_CW_20270401_V01` | 0 today · **43** from the cliff | 86 | **51** |

**`GL_CW_20231201_V03` and `GL_CW_20260101_V01` are byte-identical for Prem/Ops** — so the 2026
edition is not a third calculator, it is the same one. **`GL_CW_20231201_V02` is a genuinely
different one**, and California is the only jurisdiction on it.

- All 100 rule **names** are identical between V02 and V03. **40 of the 100 bodies are not.**
- The difference is behavioural, not cosmetic. `SetPremOpsLossCost` in V03 wraps both loss-cost
  lookups in an `IsNull` guard on `PremOpsLossCost` that V02 does not have — **V02 overwrites a
  loss cost that is already present; V03 does not.**

**The count of calculators is right and their identity was not.** *"CW 2023 and CW 2027"* names two
editions where the real split is V02 / (V03 = 2026) / 2027 — and the odd one out is **not** the
newest, it is the one held by a single state. **Gate 334 was derived against V03** (the OK golden
case declares it) and the golden case therefore cannot exercise V02 at all.

**California is the outlier in three independent ways** — sole holder of countrywide parent V02, one
of four jurisdictions filing loss costs under sharded table names, and one of four resolving
territory by county/place. Nothing rates California today that has been tested against California.

---

## 5. What the numbers say about each phase

**Phase 4 (334) is the largest single-subline phase and always was** — 100 countrywide rules across
two live calculators, 71 state rule names in 19 jurisdictions, and 110 tables of which 86 are
populated. The 2027 edition **shrinks** it to 86 rules while raising the variant count to three.

**Phases 5b–7 are much smaller than phase 4, and their deviation surface is tiny.** OCP has 4 state
rule names in 2 jurisdictions; Railroad has 3 in 2. **The state layer is nearly absent for these
sublines** — they are countrywide algorithms with state *data*, which is exactly what N8 predicts.
Their gates were correspondingly cheap and the code should be too.

**Item 6 (Product Withdrawal / Loss of Electronic Data / Cyber) is the largest single rating item —
150 countrywide rules across six coverage groups, half again as many as 334's 100.** Its deviation
surface is small, though: **17 state rule names in 9 jurisdictions**, well under 334's 71 in 19. It
is a big countrywide algorithm with very little state variation.

> **Corrected 2026-08-11, and the correction is larger than the figure.** This row first read
> **320 countrywide / 178 state / 42 jurisdictions**, and on that basis this document recommended
> splitting item 6 into three build-order items. **The measurement was wrong.** The sizing script
> matched DataDefGroups by *substring*, and `ProductWithdrawal` also matches **19 endorsement,
> coverage-form and minimum-premium groups** carrying 167 further rules — work that belongs to items
> 8, 12 and 13, not to item 6's rating. Every match is now intersected with the RATE_DRIVEN set, and
> `SIZE_ALL=1` reproduces the old behaviour.
>
> **Third instance this session of the same error**, after Delaware's territory table and the
> `AdjustedRate` omission: *a name was matched where a thing should have been identified.* It is the
> same failure the `variants` column exists to catch, committed one column to the left.

**The split-into-three recommendation is withdrawn as originally argued, and re-made on different
grounds.** Not because item 6 is huge — it is 150 rules, not 320 — but because it contains **three
unrelated coverages that share a rule-name skeleton and *no implementation*.** Across the six
rate-driven groups, name overlap runs 12–25 rules per pair and **identical bodies run to exactly
zero**. They must be derived separately whatever the file count.

**Item 11 is misnamed.** *"State-specific rating coverages (MD, MA)"* omits **New York's Special
Protective and Highway coverage**, which is `RATE_DRIVEN`, exists in **no countrywide edition at
all**, and is filed only by NY — 10 packages, 53 state rule names, 11 tables. Its DataDefGroup
(`GeneralLiabilityClassificationSpecialProtectiveHighwayCoverage`) **carries no state name**, which
is why three gates read it as a countrywide coverage. It is the fourth state-specific rating
coverage and the largest of them.

The same scan surfaced state-only lead coverages in **New Jersey** (3 groups) and **Rhode Island**
(1). Checked against `rating_vs_capture.csv` rather than assumed: NJ's two premium-writing groups
are **CAPTURE** and RI's is **OTHER** — none of them rates, so **none belongs in item 11**. They
belong to the capture harness and to policy assembly. Item 11 is exactly four coverages: **MD lead,
MA lead ×2, and NY Special Protective & Highway.**

**Phase 16, the capture harness, stays sized at 383.** It must handle every group the engine may
meet, not the 356 in force today (OI-40 §5).

**Item 7, Unmanned Aircraft, is a rating subline and the scope measurement said it was not.** Listing
the remaining gates against the rate-driven groups exposed the disagreement: item 7 was on the build
order as a rating subline and owned no rate-driven group. It owns two — `…CovABIPDCoverage` and
`…CovBPAICoverage`, 116 packages each — misclassified because the classifier's rate-source list
omitted `AdjustedRate`. **The headline is `18 · 383 · 76`, not `16 · 383 · 78`** (OI-40 §5, OI-42).

Sized after the correction, item 7 is **62 countrywide rules across two live calculators, 14 state
rule names in 9 jurisdictions, 16 tables of which 7 are populated** — comparable to Liquor (50) and
Railroad (65), and **larger than OCP's state footprint**. The build order's note, *"flat charges"*,
is wrong: it is an ordinary rate × ILF × mods chain. It should be gated like items 4 and 5.

**This table was itself incomplete until that was found.** Item 7 had no row here, because the
sizing script's build-order map was seeded from the rate-driven group list — which did not contain
it. **A sizing pass driven by a defective inventory silently sizes the wrong build.**

---

## 6. Proposed changes to the plan

Measurements, then the changes they imply. The changes are proposals; the measurements are not.

| # | Change | Evidence |
|---|---|---|
| 1 | **Phase 2's exit criterion must require three calculators addressable, and name them V02 / V03=2026 / 2027** — not "CW 2023 and CW 2027" | §4 |
| 2 | **Add a California golden or differential case before phase 4 closes.** CA is the sole V02 jurisdiction and nothing currently tests V02 | §4 |
| 3 | **Split build-order item 6 into three** — Product Withdrawal, Loss of Electronic Data, Cyber Incident | §5. *Re-argued: not on size (150 CW rules, not 320) but because the six groups share a rule-name skeleton and zero identical bodies* |
| 4 | ~~**Rename item 11 and add NY Special Protective & Highway** — four coverages, three states. NJ and RI lead were checked and do **not** rate~~ **CORRECTED 2026-08-12** — [gate state-specific](gates/GATE-STATE-SPECIFIC.md) §0: it is **five coverages in four states, 88 rules**. **Rhode Island's lead coverage rates** — 13 rules and a 16,410-character `SetPremium` — and was filed `OTHER` because its premium reads `LeadLiabilityRate`, a term `RATE_SRC` does not match (OI-63). **The NJ half stands**: 3 groups, 2 write a premium, both read `ManualPremium`. | §5. *Now **item 11** after the 2026-08-12 resequencing; gate passed* |
| 5 | **Keep the capture harness sized at 383** and say in the exit criterion that it is a union over editions, not an in-force count | OI-40 §5 |
| 6 | **Add the OI-41 as-of floor assertion (≥ 2022-09-01) to phase 1** | OI-40 §2 |
| 7 | **✅ Applied 2026-08-11 — Size-Of-Risk moved out of the rating-plans bundle to build-order item 8**, ahead of everything not yet gated; items 8–13 move down one | Gate 365 §2 / OI-46: item 6's LoED and Cyber read `PremOpsSizeOfRiskFinalRelativity` out of their host coverage group |

---

## 7. When these changes get made

**Decided 2026-08-11: gating continues through build-order item 12 *(was 11)* before any engine code
is written.** No code exists yet, and every gate so far has changed the architecture — N15, N16, N17,
per-subline premium strategies, edition-scoped calculators, and now N11's extension and a third
countrywide calculator. So the six proposals in §6 are **plan changes, applied to the plan now**,
not build work scheduled now. **Gates 332 (Liquor) and 335-RR (Railroad Protective) have since
passed** — items **1–7**, the whole rating core. **The build order was then resequenced**: Size-Of-Risk
becomes item 8 and everything below moves down one (build plan §8, OI-46 closed). Next to gate is
**item 9, refer-to-company coverages**.

The one item in §6 with a deadline attached is **#2, the California differential case**. It is not a
gate deliverable and it is not phase-4 code — it is a fixture, and it can be built the moment the
resolver exists. Until then, *nothing rates California that has been tested against California* is a
standing caveat on every 334 claim.

---

## 8. What this exercise says about the method

**The first version of this script compared rule counts and would have reported five phases as
single-calculator.** They are not; 40 of 100 Prem/Ops rule bodies differ between two parents that
carry identical rule *names* and identical rule *counts*. That is **N11 in a new place** — rules are
keyed semantically, never by printed number, **and never by name-plus-count either.** The
correction cost one line and changed the sizing of five phases.

**OI-40 was worth running for a reason it was not opened for.** It was opened to re-date counts. It
also forced the discovery that *"the countrywide parent"* is never singular — and this document is
what that turns into once the parents are counted per phase rather than per corpus.
