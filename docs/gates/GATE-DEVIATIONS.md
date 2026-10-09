# Carrier deviations — gate

**P3 of [`DEVIATIONS-PLAN.md`](../DEVIATIONS-PLAN.md): the "doesn't break ISO" sign-off.** Gated 2026-10-09.

> **T1–T10 all pass.** With no writing company the engine is today's engine, field for field, across every
> stored Property request; with one, a carrier changes only what its filing says, by exactly the amount it says,
> and the technical result it is measured against agrees with ISO's own service on every number ISO publishes
> in 96 of 96 states.
>
> **One decision came out of the proof (O6 → D21):** ISO's service refuses every Property LCM below 1.00, so
> ISO is never sent an LCM. It rates **technical** only; the **carrier** is proved against technical.

| | |
|---|---|
| The P0 filing | UFG Iowa Commercial Property LCMs, SERFF UNFG-134289779, United Fire & Casualty and Addison |
| Tests | T1–T10, in four suites (below), all passing |
| ISO calls | **71** on 2026-10-09 (`active` lane): T3 19, T8 2, the retired T5 split check 49, O6's confirmation 1 |
| ISO agreement | T3 **96 of 96** states, 40,413 numbers, 0 disagreements · T8 **2 of 2** · retired T5 **24 of 25** (the 25th is O6) |
| Regression Library | 98 requests ISO answered (T3, T8), each a library entry: 97 pass, 1 agrees on every premium |
| Engine changes | the company layer (`deviations/engine.py`), two entry points, one inactive-by-default hook in `Product`, and dependency tracking off by default |

---

## The pattern: Technical · ISO · Carrier

| | What it is | Checked against |
|---|---|---|
| **Technical** | our engine, pure ISO content, same edition as carrier, our header fields and every submitted LCM removed | ISO (T3), and our ISO-only engine (T1) |
| **ISO** | ISO's service, answering exactly the technical request | — |
| **Carrier** | our engine through the company's filing | technical (T2, T4, T5, T6, T7, T9) |

ISO never sees a carrier request (D21). `scripts/raas.py` enforces it for every caller: a request that names a
writing company reaches ISO with our header fields and every LCM removed.

---

## The ten tests

| # | Result | Evidence |
|---|---|---|
| **T1** No company = today's engine | **PASS** | 92 stored requests in 46 states, field for field, through `cf_engine.rating` vs the console's path; a PolicyType-only header changes nothing (both lines). The full population: `206_snapshot_regression --check`, 2,082 requests, 1,260,020 fields, **nothing moved** (after every P2 and P3 engine change). GL's own suites all green. |
| **T2** Neutral deviations = technical | **PASS** | 46 Property states and 6 GL states, each under an identity filing (LCM × 1 and × 1 on every exact decimal ISO table): carrier equals technical field for field. Banded tables are outside v1 and so outside T2. |
| **T3** Technical = ISO | **PASS** | 96 of 96 (46 Property, 50 GL). ISO rated every technical request; 40,413 numbers compared, 0 disagreements, and no new disagreement against the stored originals. |
| **T4** Only what was deviated changes | **PASS** | 5 cases (UFG both companies, a two-class stored request, a Property table override, GL LCMs + a GL table override): every changed field lies inside what the carrier's inputs can reach (e.g. 67 changed within 101 of 907 fields), by `gl_engine/interp/taint.py`. |
| **T5** LCMs | **PASS** | Against technical (D21): every group-rate product reads exactly the filed LCM — UFG Iowa (2 companies × 3 risks) and 9 more Property states, 229 products; each group's rate scales by its own LCM within ISO's 3-place rounding; every GL coverage record in 10 states carries exactly its filed LCM. |
| **T6** Override arithmetic | **PASS** | 4 Iowa tables × 1.1: every lookup returns ISO's value × 1.1 exactly; the waterfall adds up to carrier − technical exactly. |
| **T7** Boundaries | **PASS** | State (IA filing, OR untouched), coverage (Prem/Ops LCM, Products untouched), coverage group (Group II LCM, Group I untouched), new-business date (5/31 vs 6/1), new vs renewal, superseded versions, an opted-out state, and a jurisdiction ISO added after an all-states filing was taken (IL). |
| **T8** Pins | **PASS** | CF IA pinned to `CF_IA_20250101_V01`: $4,503 ours, $4,503 ISO at 2/1/2025. GL TX pinned to `GL_TX_20240801_V01`: $7,731 ours, $7,731 ISO at 1/15/2025. ISO takes no pin (O2): its date chooses the edition. |
| **T9** ISO revision | **PASS** | One filing over Iowa's 2025 and 2026 editions: the replace row keeps 0.2, the multiply row is 1.1 × each edition's own value, and the "ISO revised" flag is raised. |
| **T10** Files round trip | **PASS** | 78/78: UFG compiles and reads back exactly; its sheet imports to byte-identical tables; validate refuses 21 bad cases. |

### Suites

```
python tests/verify_deviations_files.py           # T10                         78/78
python tests/verify_deviations_engine.py          # T1, T2, P2's own checks     44/44
python tests/verify_deviations_proof.py           # T4-T7, T9 + T3/T8 re-judged 57/57   (no calls)
python scripts/cf/206_snapshot_regression.py --check --jobs 12   # T1, the whole stored population
python scripts/deviations_p3.py --plan | --send | --judge | --promote   # the live part, T3 and T8
```

All but `--send` are free; `--judge` re-reads ISO's stored answers.

---

## What the proof found

1. **D13 was not enforced when a request's line block is one object, not a list.** Ohio's stored request sends
   `CommercialProperty` as an object; its submitted LCM of 1.3 reached "technical". Fixed in both lines and in the
   ISO request builder.
2. **A contents record could carry two classes.** The record LCM was chosen by the occupancy's class before the
   rules ran, the group LCM by the class ISO's rules later stamp on the record (Florida, 0331 vs 0951). Now each
   record's class is fixed once, as submitted, and both steps use it — which is also what ISO's service sees.
3. **"AdditionalLocations*Special*Coinsurance" is not the Special form.** The group matcher now says so.
4. **O6: ISO refuses every Property LCM below 1.00.** Its stat-code rule keys `Round(LCM, 2) × 100` as "88.00";
   the table files "88". Found on UFG's group-B Group I LCM (0.875), confirmed on a plain ISO request at 0.95.
   **Decided: no LCM is sent to ISO (D21).** Our engine rates such an ISO-only request ($4,103 at 0.95) where ISO
   refuses; only an ISO-only request with an LCM below 1 can reach that difference, and it is left as is.

---

## v1 limits carried forward

From the plan's §4e: one filing in force per company, state and line; banded tables cannot be overridden;
territory-, limit- and deductible-keyed LCMs arrive with later GL work; a Property rate that belongs to no
coverage group reads the record's (Group I) LCM.
