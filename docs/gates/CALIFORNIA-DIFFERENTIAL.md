# California — the sole `GL_CW_20231201_V02` jurisdiction

**Filed 2026-08-12 (Step 43).** Not a gate — California is a *jurisdiction*, not a build-order
item. This is the differential fixture the gates have been carrying as owed work since Step 38,
and it is runnable: [`tests/verify_california.py`](../../tests/verify_california.py), **11/11**.

**As-of date: 2026-08-12.** Required, not assumed (N4).

---

## 1. Why California is the only one that needs this

Two countrywide parents are in force. **50 jurisdictions declare `GL_CW_20231201_V03` or
`GL_CW_20260101_V01`. California alone declares `GL_CW_20231201_V02`** — and the golden case,
Oklahoma, is on V03.

So the V02 path is the one piece of the resolver that **nothing exercises**, and it is not a corner:
it is the path a whole state takes.

---

## 2. What actually differs — measured, not sampled

| | |
|---|---|
| Rule files in each parent | **547 = 547**, none added or removed |
| Rules compared | **4,461** |
| **Differing bodies** | **345** |
| Files containing a difference | **43 of 547** |
| Rules added or removed | **0** |

**Identical names throughout, 345 different behaviours.** N11 in its purest form: a check that
compares rule names and counts calls these editions identical, and
[`PHASE-SIZING.md`](../PHASE-SIZING.md) §4 did exactly that before this was measured.

### 341 of the 345 are one change

V03 wraps each write in `if (target IsNull)` — `<rul:IsNull><rul:Value … AllowNullReturn="true"/>`
— over **210 further DataDefs**. The other 4 are the same idea in a different shape.

**V02 is not innocent of the idiom.** It already guards **exactly 3**: `LCM`, `LCMStatCode`,
`LmtdProdsWithdrawalLCM`. So V03 **generalised a pattern from 3 DataDefs to 213**, and the three ISO
had already protected name its purpose: **the loss cost multiplier must not be recomputed.**

---

## 3. The first reading was wrong, and the right one is sharper

**First reading:** *"V02 overwrites a broker-supplied value; V03 preserves it."* Seven of the 210
newly-guarded DataDefs are `*Override` fields and four are keys California's own submission
supplies — `GeneralAggregateLimit`, `PremOpsProdsEachOccurrenceLimit`,
`ProdsCompldOpsAggregateLimit`, `PackageModFactor` — so the reading looked well-evidenced.

**It does not survive reading the rule.** `SetGeneralAggregateLimit` copies from the *policy-level*
`../../../../GeneralAggregateLimit` to a *local* one, **in both editions, from the same source**.
The guard protects the local copy from being rewritten; it does not protect the input, because the
input is not what is being written.

**The right reading:**

> **The guard is about idempotency under re-evaluation.**
> V03: those 213 DataDefs are **write-once**.
> V02: they are **recomputed on every evaluation of the rule**.

And nothing else prevents recomputation: **all 5,601 `RunRule` calls in the countrywide package
carry `ClearCache="true"`** — 5,601 of 5,601, no exceptions. The guard *is* the memoisation.

### Where re-evaluation happens

ERC re-rates a coverage wherever a minimum premium has to be reached. There are **14
`PremiumToReachMinCoverage` groups**, one per rateable coverage.

**The corroboration is that three of the four non-guard differences live inside three of them** —
`SetTotalCyberIncidentLiabilityPremium`, `SetTotalLossOfElectronicDataPremium`,
`SetTotalUnmannedAircraftPremium`. The one change ISO made that is *not* a guard, they made to the
iteration totals. The fourth is `SetHighestLmtdProdsWithdrawalFinalILFFlag`, in OI-50's chain.

---

## 4. What this does and does not license us to say

**Says:** California evaluates under different write semantics from every other jurisdiction, in
**345 rules across every gated subline** — Prem/Ops 40 of 100, Products 33 of 90, Railroad 21 of 65,
OCP 17 of 58, Liquor 12 of 50, plus 55 in `GeneralLiabilityRules` and 33 in
`GeneralLiabilityClassification`.

**Does not say:** that any California premium is different. Recomputation from unchanged inputs
returns the same answer; it diverges only if an intermediate is mutated between passes.
**Establishing which needs an engine, and the engine is not built.**

> **CORRECTED 2026-08-12.** This section said *"1 of 517 STC payloads is a rated output and it is
> Oklahoma's — there is no California oracle to compare against."* **That was measured over the ERC
> corpus and stated about the project.** `Payloads/` — the RAAS baseline set, documented in
> [`OPEN-ITEMS`](../OPEN-ITEMS.md) §G since 2026-08-10 — holds **53 rated outputs across 50 states,
> each paired with its input**, and **California is one of them** (`Payloads/CA/1. Output.json`,
> total premium `7,586`). A scoped search restated as a universal claim: the defect this project
> has spent a week cataloguing, committed in a document about it. **OI-67.**

**So the effect CAN be settled, and should be.** The ERC corpus holds one rated output, in Oklahoma;
the RAAS baseline set holds 53 more including California. **What is still true is that settling it
needs the engine** — a rated output tells you the answer, not the mechanism, and no amount of
reading the corpus distinguishes "recomputed and identical" from "never recomputed".

This remains a *differential* fixture because that is what it is for: it pins how the two countrywide
parents differ, which an oracle test would not show. **A California oracle test should be written
alongside it once the engine exists.**

---

## 5. One risk that closed on measurement

**All ten size-of-risk setters differ between the parents** — five per subline, the whole chain
gated one day earlier. That looked like the sharpest exposure in the set.

**It is unreachable in California.** CA overrides `SetSizeOfRiskRatingApplies` with a constant stub
writing `"No"` (see [gate size-of-risk §6a](GATE-SIZE-OF-RISK.md)), so every one of the ten is
gated off before it runs. California's own filed submission agrees — it carries
`SizeOfRiskRatingApplies: "No"` and `TerrorismCoverage: "No"`, exercising the disabled paths only.

**So the exposure narrows to the non-size-of-risk differences, and the size-of-risk gate needs no
California caveat.** Both facts are assertions in the fixture.

---

## 6. What the engine owes

1. **Resolve the declared parent and evaluate under *its* rule bodies** — not a merged or
   newest-wins view. 345 rules make this a correctness requirement for one state, not a nicety.
2. **Model write-once as a property of the resolved edition**, not as an engine-wide convention.
   An engine that memoises everywhere is V03 for all 51 and silently wrong for California; one that
   memoises nowhere is V02 for all 51 and silently wrong for the other 50.
3. **A load-time assertion** that the guarded-DataDef set of the resolved parent is the one the
   fixture recorded — 3 for V02, 213 for V03 — so a new edition changing it fails loudly.
4. **Re-evaluation order is part of the algorithm**, and the 14 `PremiumToReachMinCoverage` groups
   are where it bites. This joins E18 (coverage scope) and the terrorism gate (policy scope) as the
   third place evaluation order is load-bearing.

---

## 7. Register

| | |
|---|---|
| **OI-58** | The V02/V03 write-semantics divergence: real, measured, premium effect **unproven — but provable.** `Payloads/CA` is a rated output (§4, corrected). It needs the engine, because a rated total gives the answer and not the mechanism |
| **OI-67** *(new)* | *"The project has one oracle"* was a claim scoped to the ERC corpus and stated about the project; `Payloads/` holds **53 more across 50 states**. Two green tests asserted the false version |
| **N11** | Corroborated with a number: same 547 files, same 4,461 rule names, **345 different bodies** |
| **E1** | Untouched — no rounding site is among the 345 |
| **Owed work** | This closes the California item. **New York is next**; OI-50 last |
