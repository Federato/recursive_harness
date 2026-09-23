# Chunk 11, Group C: zero cases (C11-04), and what to ask ISO (C11-23)

**Predictions written 2026-09-22, before the run.** Script:
[`117_chunk11_c11-04_zero_cases.py`](../scripts/cf/117_chunk11_c11-04_zero_cases.py).
Every case is the golden case (`114_chunk11_golden_case.py`: Tenants Lease,
gross 1,500, 10%, lease 2025–2037, policy 2027–2028 → **$268 / $30**) with
one thing changed.

## In plain English first

There are many ways a Leasehold Interest submission can come back at $0
without an error. They aren't one bug seen many times: they happen at
**seven different places** in the calculation, and it matters which one,
because each needs a different fix or a different question to ISO. Two
of them are places where **our engine and ISO will likely disagree**. That's
the input for C11-23.

## How our engine treats the two things these cases hinge on

Read from `gl_engine/interp/interpreter.py` before predicting:

* **A comparison with a null operand is FALSE, not an error**, under the
  configured `propagate` mode (`Interpreter.eval`, the `COMPARING` set).
  `01/01/0001`, which `FirstValue` substitutes for a missing date, coerces to
  **null**. ISO instead treats it as `DateTime.MinValue`, a real, very early
  date. **This is the root of divergence D1 below.**
* **A lookup that matches no row gives null, not an error.**
  `strict_single_result` is off by default. The null then meets a
  `FirstValue … FromConstant="0.0"` and becomes 0.

## The cases, by where the zero comes from

| # | Change | Where the zero comes from | Predicted (ours) | Tier |
|---|---|---|---|---|
| Z1 | LI under a `CovType = Building` structure | `AttachForm…LeaseholdInterest` **deletes** the record | no LI record at all | **T0** record deleted |
| Z2 | all four amount fields absent | every cell's gate needs its own amount ≠ 0 | record kept, **20 of 20 cells off**, total $0 | **T1** all cells off |
| Z3 | `LeaseExpDate` absent | `SetNumberOfMonths`' outer `IsNotNull` fails → both months **0** → 1 − v⁰ = 0 | Tenants BGI/BGII cells **on**, $0 / $0 | **T2** months = 0 |
| Z4 | lease ended before the policy (`LeaseExpDate 06/01/2026`) | both date tests false → months 0 | on, $0 / $0 | T2 |
| ~~Z5~~ | `ExpDate` absent | ~~months 0~~. **Wrong, see the result below**: ISO's `Default` block sets `ExpDate = EffDate + 1 year` on every run | ~~$0~~ **$268 / $30**, not a zero case | — |
| Z6 | `LeaseEffDate` absent | `null < ExpDate` is **False** (ours) → months 0. ISO: `MinValue < ExpDate` is **true** → 120/108 → **$268 / $30** | on, $0 / $0. **Diverges (D1)** | T2 |
| Z7 | `PercentInterest` absent | `SetAnnuityConstant` Else → **0.0**; `DiscFactor` 0.0 → 0^120 = 0 → factor = 0 × 1 | on, $0 / $0 | **T3** annuity = 0 |
| Z8 | `PercentInterest = "10.5%"` (not a whole point) | state and CW lookups both miss → null → `FirstValue` 0.0 → factor 0 | on, $0 / $0. **ISO may refuse instead (D2)** | T3 |
| Z9 | `PercentInterest = "10"` (no `%` sign) | same as Z8: the table keys are `"10%"` | on, $0 / $0. **D2** | T3 |
| Z10 | `TenantsGrossLeaseholdInt = -1500` | the cell gate is `≠ 0` (on), but `SetTenantsNetLeaseholdInt` needs `> 0` → net 0.0 | on, $0 / $0 | **T4** amount ≤ 0 |
| Z11 | `EQCovIndicator` blank | the EQ cell gate reads blank as elected; the Structure's EQ rate is 0 with no EQ inputs | EQ cell **on**, $0; BGI/BGII still $268 / $30 | **T5** rate = 0 |
| Z12 | Special, no Theft Exclusion | theft factor falls back to 0.0 (OI-101; run in `116…` S4) | Special cells on, $0 | T5 |
| Z13 | `PercentInterest` absent **and** lease ended before the policy | `DiscFactor` 0.0 and months 0 → **0^0**. Python `Decimal` raises `InvalidOperation`; .NET `Math.Pow(0,0)` = 1 → ISO $0 | **engine refuses** (`Power(0.0, 0) is undefined`). **Diverges (D3)** | **T6** refusal |

And one boundary that must **not** be zero:

| # | Change | Predicted |
|---|---|---|
| B1 | lease ends mid-policy (`LeaseExpDate 06/01/2027`) | months 5 / 0 → factors 4.8826 / 0.0000 → nets 7,324 / 0 → avg **3,662**, **half** the at-inception value, as the averaging implies → **$9 / $1** |

## Distinct causes, not one zero counted many times

Seven tiers (T0–T6). Within T2, the three cases reach "months = 0" through
**three different mechanisms**: the outer null guard (Z3), a true date
comparison (Z4), and a null comparison forced to False (Z6). That last
one is the only mechanism that depends on an **engine policy** rather than
on ISO's filed rules.

## What C11-23 has to ask ISO

| | Case | Ours | ISO, predicted from its own semantics | Why it matters |
|---|---|---|---|---|
| **D1** | Z6, `LeaseEffDate` missing | $0 | **$268 / $30** | Our sentinel-as-null choice turns an ordinary submission into a free policy. If ISO confirms, it's an engine defect in how `01/01/0001` compares, and it reaches **all 28** date comparisons, not just this one |
| **D2** | Z8/Z9, a rate not in the table | $0 | refusal, or $0 | the standing `SingleResult` zero-hit question (open item 8), asked on a new table |
| **D3** | Z13, 0^0 | **refusal** | $0 | ours crashes where ISO would price. That's a safe direction, but still a divergence |
| — | ~~Z5~~ | — | — | withdrawn: `ExpDate` is always EffDate + 1 year, so it can't be missing |
| — | Z12, OI-101 | $0 | $0 (same rule) | carried from Group B |

## Result (2026-09-22)

**13 of 14 predictions held; one was wrong, and it was wrong usefully.**

* **Z5 was a miss.** I predicted a missing `ExpDate` would price at $0.
  It priced **$268 / $30**. `Overall Rating.Rule.xml`'s `Default` block (the
  entry point) runs `DateAdd ExpDate = EffDate + 1 Years` **unconditionally**,
  so a missing `ExpDate` is filled in, and a submitted one is
  **overwritten**. A six-month `07/01/2027` came back as `01/01/2028`, still
  $268. That fits the standing fact that **ISO prices a one-year term and
  administers nothing**. `ExpDate` is not an input to this engine at all.
  The golden-case doc's finding 4, which built a trap on the opposite
  assumption, is corrected in place.
* **Z13 refused, as predicted**, with the text `Power(0, 0) is undefined`.
  I had predicted `Power(0.0, 0)`. That's cosmetic, and the check now matches
  on the refusal, not the digits.
* **Every other case landed in the predicted tier**, including B1: a lease
  ending mid-policy prices at **$9 / $1** on an average of 3,662, half the
  at-inception value.

The seven tiers stand: six zero tiers (T0–T5) plus the T6 refusal.
Withdrawing Z5 removed a case, not a tier. T2 reaches "months = 0" through three mechanisms: the
null guard (Z3), a true date test (Z4), and a sentinel compared as null (Z6).
Only Z6 depends on an engine policy.

**For C11-23, three questions remain for ISO**: D1 (Z6, a missing
`LeaseEffDate`: $0 here, $268 / $30 predicted at ISO), D2 (Z8/Z9, a rate
not in the table), and D3 (Z13, 0^0).

## C11-23: ISO's answers (live, 2026-09-22)

Script: `118_chunk11_c11-23_raas.py`. Requests and responses:
`results/cf-raas/chunk11_*`.

**First, a date problem that had nothing to do with Leasehold Interest.** At
`EffectiveDateTime 2027-01-01` (the golden case's EffDate), ISO priced Basic
Group I at **$67** against our **$268**. The whole annuity matched ISO to the
digit: 120/108 months, 0.385543128682177, 77.0562 / 72.2213, net 111,958.
And Basic Group II agreed. The gap was ISO's `BasicGroupIBaseRate`: **0.125**
against our 0.498. Two more calls isolated it. Chunk 2's plain **Building**
risk at 2027-01-01 also gets 0.125, and the LI case at **2026-09-17** gets
0.498. So **ISO serves a newer Oregon rate edition for 2027 than our local
corpus holds** (OI-105). Our engine resolves editions as of 20260917, so
every comparison below is run on **both sides at 2026-09-17**. That moves
the golden premium to **$272 / $31** (months 123/111).

| # | Case | Ours | ISO | Verdict |
|---|---|---|---|---|
| C0 | golden (control) | $272 / $31 | **$272 / $31** | agree |
| Z1 | LI under a Building structure | no record | no record | agree |
| Z2 | all four amounts absent | $0 | $0 | agree |
| Z3 | `LeaseExpDate` absent | $0 | $0 | agree |
| Z4 | lease ended before the policy | $0 | $0 | agree |
| **Z6** | **`LeaseEffDate` absent** | **$0** | **$272 / $31** | **DIVERGE, as predicted (D1)** |
| Z7 | `PercentInterest` absent | $0 | $0 | agree |
| **Z8** | **`10.5%`** | **$0** | **refused (HTTP 400)** | **DIVERGE, as predicted (D2)** |
| **Z9** | **`10`, no `%`** | **$0** | **refused (HTTP 400)** | **DIVERGE (D2)** |
| Z10 | gross −1,500 | $0 | $0 | agree |
| Z11 | `EQCovIndicator` blank | $272 / $31, EQ $0 | same | agree |
| **Z13** | **0^0** | **refused** | **$0** | **DIVERGE, as predicted (D3)** |
| B1 | lease ends mid-policy | $14 / $2 | $14 / $2 | agree |
| Z12 | Special, no Theft Exclusion (OI-101) | Special $0 | **Special $0** | agree. **OI-101 confirmed as ISO's own behaviour** |
| S3 | Special + Theft Exclusion | Special $46 | $46 | agree |

**11 agree, 3 diverge, and all three divergences were predicted before the
call.**

* **D1 (OI-102) is an engine defect with a premium consequence.** A missing
  `LeaseEffDate` reaches `FirstValue … FromConstant="01/01/0001"`. ISO reads
  that as `DateTime.MinValue` and prices the lease normally. We read it as
  null, the comparison becomes False, and **the policy prices at $0**. The
  cause is general, not Leasehold-specific: **every** `dateTime`
  `FirstValue` with the `01/01/0001` fallback behaves this way in our engine.
  That's 28 ordered date comparisons corpus-wide, most of them validation
  messages.
* **D2 (OI-103): ISO refuses; we price at $0.** ISO's message is exact:
  *"Error running Lookup Rule at line 1215 … Matrix:
  LeaseholdInterestAnnuityConstant … Keys: CW, 10.5%. No results have been
  returned."* That's a `SingleResult` countrywide pass matching nothing,
  and ISO **refuses**. It's a new, concrete data point for the standing
  "`SingleResult` with zero hits" question (interpreter open item 8), where
  our engine's `strict_single_result` is off by default.
* **D3 (OI-104): we refuse, ISO prices at $0.** Python's `Decimal` refuses
  `0 ** 0`; .NET returns 1. It's the safe direction, but it is still a
  divergence, and it's trivially reachable (blank interest rate + expired
  lease).

### Update: OI-102 fixed (2026-09-22, user-authorized)

`_cmp` now orders the `01/01/0001` fallback as the earliest date, as ISO does
(`CF-ENGINE-FIX-DATE-COMPARE.md`, follow-up section). **Z6 is no longer a zero
case**: a missing `LeaseEffDate` prices at $268 / $30 on the golden date and
at **$272 / $31 at 2026-09-17, matching ISO live**. That leaves 12 agreements
and 2 divergences with ISO: D2 (OI-103) and D3 (OI-104).

### Update: OI-104 fixed (2026-09-22, user-authorized)

`Power(0, 0)` now returns 1, as ISO's .NET does. **Z13 is no longer a
refusal**: it's a T3 zero ($0), and **matches ISO live**. With OI-102 and
OI-104 both fixed, **13 of the 14 C11-23 cases agree with ISO**. The one
remaining divergence is D2 (OI-103: a rate not in the table refuses at ISO
and prices $0 here). T6 (engine refuses) now has no members in chunk 11.
