# 10 — Phased Build Backlog

> **Reconciliation note, 2026-08-11.** This document was derived from the filed manual PDFs and **before any subline
> was derived end to end**. The per-subline gates have since superseded or sharpened some claims
> here — see [`../gates/RECONCILIATION.md`](../gates/RECONCILIATION.md) (items R1, R2, R4). The text below is
> left as the record of what this derivation found on its own; that independence is what makes
> agreement between the two derivations evidence.

Sequenced so that the **highest-correctness-risk** items are settled first, and so that the
absence of external rate tables never blocks progress.

Nothing here has been built. This is the plan.

---

## Phase 0 — Corpus hygiene (0.5 week)

| # | Task | Exit criterion |
|---|---|---|
| 0.1 | Re-download `GL-MO-2027-RU-003-C.pdf` | Extracts cleanly |
| 0.2 | Deduplicate the three `(1)`/`(2)` files by sha256 | 500 unique documents |
| 0.3 | Confirm whether Hawaii is in scope | Documented decision |
| 0.4 | Resolve the 264 proximity-only ERC↔manual matches (defect D4) | Every promoted edition has `date_confidence` recorded; `LOW` count reduced |

> 0.4 is the highest-value item in Phase 0. Effective dating drives edition selection, which
> drives every downstream number.

---

## Phase 1 — Manual store & ingestion spine (2–3 weeks)

| # | Task | Exit criterion |
|---|---|---|
| 1.1 | Implement schema §6.1–6.4 (provenance, editions, rule catalog, deviations) | Migrations applied |
| 1.2 | Dual-mode extractor with `pypdf` fallback (§8.3) | 502/503 extract; failures quarantined not silent |
| 1.3 | Segmenter (§8.4) incl. TOC-vs-body leader-dot discrimination | No rule double-counted |
| 1.4 | Rule-heading + deviation-operation parser (§8.5.1–8.5.2) | All 490 notices parsed; matches the counts in `04-STATE-DEVIATIONS.md` |
| 1.5 | **Build `rule_concept` + `rule_number_map` for CW-2022 and CW-2027** | Both schemes loaded; all 21 renumbered rules mapped to one concept each |
| 1.6 | Validation assertions V1, V2, V10, V11 (§8.6) | Load fails on scheme mismatch |

**1.5 is the keystone task.** Everything downstream depends on edition-safe rule identity.
Do it before any calculation work.

---

## Phase 2 — State variable & lookup extraction (2 weeks)

| # | Task | Exit criterion |
|---|---|---|
| 2.1 | Payroll limitation extractor, all three shapes (§5.1) | 51/51 resolved, no `NOT_FOUND` (already demonstrated) |
| 2.2 | Liquor grade extractor | 51/51 resolved, all in 0..10 (already demonstrated) |
| 2.3 | Territory / Stop Gap / ELP flags + A-rule theme classification | Matches `04-STATE-DEVIATIONS.md` §4.4 |
| 2.4 | ILF **table inventory** per jurisdiction | 51/51; families and ordinals match `05-LOOKUP-TABLES.md` §5.3 |
| 2.5 | Assertions V7, V8, V9 | Green |

Phase 2 is largely proven — the extraction logic behind every number in
`05-LOOKUP-TABLES.md` already runs across the corpus. This phase productionises it.

---

## Phase 3 — Table extraction (3–5 weeks, the volume work)

| # | Task | Exit criterion |
|---|---|---|
| 3.1 | Coordinate-based ILF matrix parser (§8.5.3) | All Rule 56.B tables, all 51 jurisdictions, cells + `refer_to_company` flag |
| 3.2 | ILTA grid parser incl. the ILADD addendum form | `raw_code` + decomposed digit/letter |
| 3.3 | Classification table parser (~485 CW pages) | Class code, base, application, cross-refs, `has_prodcompops` |
| 3.4 | CW deductible discount factors (Rule 15.E, `CG-6`–`CG-8`) | Loaded |
| 3.5 | CW medpay (Table 23.D.3) + split-limit weights (Rule 23.D.5.c) | Loaded |
| 3.6 | CW Cyber/LoED hazard grades (Rule 40.F/G, `CG-60`–`CG-69`) | Loaded |
| 3.7 | Assertions V3, V4, V5, V6 | Green — especially V6 (monotonicity) as the matrix-alignment net |

3.1 is the single largest and riskiest task in the project. Budget for iteration: whitespace
alignment is not reliable at the wider table widths, so plan for word-coordinate clustering
from the start rather than discovering it after a text-based attempt.

---

## Phase 3A — Rate layer extraction (2–3 weeks, new at Step 7)

The loss cost corpus arrived after the original sizing. It is high-volume but *structurally
simple* — a regular grid with a three-token alphabet — so it is cheaper per cell than the ILF
matrices of Phase 3, and it is on the critical path to any dollar amount.

| # | Task | Exit criterion |
|---|---|---|
| 3A.1 | **`pypdf` extractor for `CG-LC` / `CG-ELP` / `CG-LCADD` pages**, with whitespace-normalised caption matching (§8.3.1) | Never invokes `pdftotext -layout` on a rate page. Assertion V18 green per territory |
| 3A.2 | Loss cost grid parser — class × territory × subline, 3-token alphabet | ~429,700 cells across 51 jurisdictions; V17, V18, V21 green |
| 3A.3 | ELP parser incl. H/R index pairs and the `EXTERNAL_PCT` form (OCP `15191`) | ~20,600 entries; V19 green |
| 3A.4 | `CG-LCADD` mapping parser + **recursive rate resolution with cycle detection** | V20 green |
| 3A.5 | Territory domain extraction; `8·T+1` page invariant | V16 green, 51/51 |
| 3A.6 | Countrywide-valued table extraction (UAV 370, OCP/PP 335) stored once with an availability join | `is_flat_charge` set for UAV |
| 3A.7 | `lc_edition` dating from `GL_LossCost_to_ERC.xlsx`; 57 proximity-dated notices flagged `date_confidence='LOW'` | No overlapping effective ranges per jurisdiction |
| 3A.8 | **Vintage classifier** (`PRE_2027` / `V2027`) and the OCP rate-source flag | 15/36 split reproduced by all three independent tests |
| 3A.9 | **Territory Pages parser** (`CG-T-n`, in the *Rules* notices) — scheme detection, ZIP tables, county/city place lists | 51/51 schemes classified; 23,719 ZIP rows + 432 place rows; V22, V23 green |

3A.8 is small but load-bearing: it is what stops the engine binding a rate source that 36
jurisdictions have withdrawn.

---

## Phase 4 — Resolver (1.5 weeks)

| # | Task | Exit criterion |
|---|---|---|
| 4.1 | `EffectiveRulebook` materialisation (§7.2) | Deterministic, pure |
| 4.2 | Overlay application ordering (REPLACE-whole → REPLACE-path → ADD → DELETE) | Unit-tested against hand-verified jurisdictions |
| 4.3 | Edition-safe number resolution + title guardrail (§7.4) | Wrong-scheme resolution is a hard failure |
| 4.4 | Inoperative-rule handling (`"This rule does not apply"`) | Rule present, marked inoperative, explains itself |
| 4.5 | Cache keyed on edition pair | Cold/warm parity test |

---

## Phase 5 — Calculation kernel (3 weeks)

| # | Task | Exit criterion |
|---|---|---|
| 5.1 | Rule 21 pipeline A–I, decimal arithmetic, `round_half_up` | Manual's own worked example reproduces exactly: `1.020 + 1.95 − 1 = 1.97` |
| 5.2 | Prem-Ops (334) + Prod/CompOps (336), incl. Rule 48.F.1 exclusion | Two rate streams, one exposure |
| 5.3 | ILF selection incl. ILTA decomposition, interpolation (Rule 56.A.4), refer-to-company cells | Off-table limits referral, not silent extrapolation |
| 5.4 | Medpay ILF adjustment; split-limit weighting | Matches CW tables |
| 5.5 | Deductible applied to basic-limits rate (Rule 15.D.4), not to ILF | Ordering test |
| 5.6 | Liquor (45), OCP/Principals (46), Railroad (49), Product Withdrawal (44) | Rule 44 correctly derives from Prod/CompOps |
| 5.7 | Refer-to-company coverages (41, 42, 43, 47, 53) — structure + referral, no invented rating | Emits typed referrals |
| 5.8 | Policywriting minimum premium (Rule 21.I) | Terminal comparison |
| 5.9 | `rating_trace` emitted always | Every premium component cites a `span_id` |
| 5.10 | **Rule suspension pass** — apply Paragraph B before the pipeline (Rule 45.B over Rule 15; Rule 44.A.4 over Rule 16) | Liquor never uses the CGL deductible path; deductible on OCP/Railroad is rejected, not ignored |
| 5.11 | **A3 host ordering** — topological sort on `host_coverage_key` | Product Withdrawal, LoED and Cyber cannot rate before Prod/CompOps |
| 5.12 | **LoED / Cyber (Rule 40)** incl. Tables 40.C–40.E and the `CG 04 95` composite | `CG 04 95` = 40.B.2.a + 40.B.1, single minimum-premium referral |
| 5.13 | **Unmanned Aircraft (Rule 37)** modifier chain | `MAX` within each modifier family, never a product |
| 5.14 | **Endorsement engine** — roles, attachment constraints, `in_loss_cost` inversion | Removing a conditional-mandatory form emits a credit referral, not zero |
| 5.15 | **Referral predicates** over the request (Participation Percentage, Cut-off Date, non-owned aircraft) | Same coverage flips to referral on a Declarations field |

---

## Phase 6 — External adapters (parallel with 4–5)

| # | Task |
|---|---|
| 6.1 | Rate / loss cost adapter + LCM application (Rule 23.B) — **G1 resolved**; now backed by Phase 3A data, not a stub. Only the carrier LCM is injected |
| 6.2 | Territory resolver — **G2 resolved**; backed by Phase 3A.9 data. Not an adapter: three schemes, of which `COUNTY_CITY` (CA, FL, NY, TX) needs county derivation and an explicit unmatched→referral path |
| 6.3 | ELP adapter — **G3 resolved**; backed by Phase 3A data |
| 6.4 | Terrorism Supplement adapter — **stubbed until G4 resolved** |
| 6.5 | Workers Compensation loss cost adapter — **stubbed, G9.** Needed only for OCP class `15191`; returns a typed referral |

Remaining stubs return typed "unavailable" results that surface as referrals, so end-to-end
flows stay testable. With **G1, G2 and G3 all closed**, the engine produces **real premiums**
for Premises/Operations and Products/Completed Operations in **all 51 jurisdictions**, with no
stub in the path — only the carrier's own LCM is injected.

---

## Phase 7 — Validation & assurance (2 weeks, overlapping)

| # | Task | Exit criterion |
|---|---|---|
| 7.1 | Golden-file tests from the manual's own worked examples | All reproduce |
| 7.2 | Property tests: ILF monotonic in both limit axes; premium monotonic in exposure | No counterexamples |
| 7.3 | Cross-jurisdiction differential test: same risk, all 51 jurisdictions — assert differences trace to a *named deviation* | Every delta explained by a `span_id` |
| 7.4 | Historical re-rate regression across the full 490-notice set | Stable across re-ingestion |
| 7.5 | Round-trip provenance audit: sample 50 premium components, verify each cites real manual text | 50/50 |
| 7.6 | **Edition-change replay harness** (`12-VERSIONING-AND-EDITIONS.md` §12.6): re-rate stored risks under old vs new snapshot | Every premium delta maps to an intended change in the edition diff; an unexplained delta **blocks the release** |
| 7.7 | **Resolution coverage gate**: 51 jurisdictions × new edition compose successfully and each rated subline has an ILF table | No jurisdiction composes to a book that cannot rate |
| 7.8 | **Overlay re-binding audit** for every rule number reused across editions (e.g. Rule 22) | Each affected overlay confirmed on the intended `rule_key` |
| 7.9 | **Rate-vintage replay** — re-rate stored risks across the `PRE_2027` → `V2027` boundary | Every delta explained by a retired/introduced class code or the OCP rate-source change; an unexplained delta blocks the release |
| 7.10 | **Rate-coverage gate** — every `(jurisdiction, class, subline)` a quote can request resolves to a loss cost, an ELP, a mapping, or an explicit referral | No silent zero. `–` and `(a)` never coerce to `0.00` |

7.3 is the strongest available correctness check given the absence of an external premium
oracle: if two jurisdictions produce different premiums for identical input, the engine must
be able to name the deviation responsible. An unexplained delta is a bug.

---

## Critical path

```
0.4 (dating) ──► 1.5 (rule identity) ──► 4.3 (edition-safe resolution) ──► 5.x (kernel)
                          ▲                                                    ▲
      3.1 (ILF cells) ────┘   (gates any above-basic-limits quote)              │
                                                                                │
      3A.1–3A.4 (loss costs, ELPs, mappings) ───────────────────────────────────┘
                              (gates ANY dollar amount at all)
```

Phase 3A is now the harder gate: 3.1 blocks quoting *above basic limits*, while 3A blocks
quoting **at all**. The two are independent and should run in parallel.

## Sizing summary

| Phase | Estimate |
|---|---|
| 0 Corpus hygiene | 0.5 wk |
| 1 Manual store & ingestion spine | 2–3 wk |
| 2 State variables & lookups | 2 wk |
| 3 Table extraction | 3–5 wk |
| **3A Rate layer extraction** | **2–3 wk** (new at Step 7 — loss costs, ELPs, territories, LCADD mappings) |
| 4 Resolver | 1.5 wk |
| 5 Calculation kernel | 3 wk → **5–6 wk** (tasks 5.10–5.15: rule suspension, A3 ordering, Rule 40, Rule 37, endorsement engine, referral predicates) |
| 6 Adapters | 1 wk (stubs) |
| 7 Validation | 2 wk → **3 wk** (tasks 7.6–7.8: edition replay, resolution coverage, re-binding audit) |
| **Total** | **≈ 18–24 weeks** to a fully rated engine, **with real rates** |

**Re-estimated at Step 5.** The original 13–17 weeks costed the Rule 21 pipeline and the
refer-to-company coverages. Working the full architecture out (`11-RATING-ARCHITECTURE.md`)
surfaced four bodies of work that were not in the original sizing: the endorsement engine
(328 forms, six roles, attachment constraints), the Rule 40 factor-on-host coverages with
their hazard-grade tables, the Paragraph B rule-suspension pass, and the edition-migration
replay harness. None is optional — each is load-bearing for correctness, not polish.

**Re-estimated at Step 7.** Phase 3A (+2–3 weeks) is new work created by the arrival of the
loss cost corpus. It buys more than it costs: the engine is now *priceable* rather than merely
testable, and Phase 6 loses two of its four stubs.

**Corrected at Step 8.** G2 was found to be closed as well — the Territory Definitions are on
the `CG-T` pages of the Rules notices. Task 3A.9 was added for their extraction (~0.5 week,
absorbed in the 3A range).

The engine is therefore **fully priced in all 51 jurisdictions** for Premises/Operations and
Products/Completed Operations once Phase 3A completes. Nothing outside the two corpora is
required to quote those sublines — only the carrier's own loss cost multiplier.
That is an external dependency, not a build task.
