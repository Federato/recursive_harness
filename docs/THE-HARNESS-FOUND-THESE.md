# What the harness found — 17 August 2026

**One session. Five defects closed, one raised and closed the same day, and one long-standing
question settled.** Written because the *how* matters more than the count: **not one of these was
found by reading the code, and not one needed a decision before it needed a measurement.**

This project is called `Recursive_Harness`. This is the day the name earned itself.

---

## The premise, stated plainly

**A rating engine that only runs cannot tell you it is wrong.** It produces a number, and a number
always looks like an answer. The premise here is that the engine, the corpus, the oracle and the
test harness should be pointed at each other until the disagreements surface on their own — and
that **the disagreements, not the agreements, are the product.**

`PROCESS_LOG.md` step 51 recorded the premise arriving early: `1.00` used as a factor sentinel
(E20/OI-68) was found by *running* content that three weeks of *reading* had catalogued eight ways.
**Today it ran the whole way.**

---

## The five, in the order they fell

### 1 · OI-88 — the fallback that could never be reached

**Found by:** ISO's live service, on a submission the harness generated because it varied
size-of-risk rather than the jurisdiction.

ISO writes state-to-countrywide fallbacks as `Round(Lookup(state))` then `Round(Lookup('CW'))`, and
**branch one is designed to miss** — `PremOpsSizeOfRiskRelativity` holds 8,330 rows, every one of
them `CW`. Our `Round` refused on the null and the exception escaped before branch two was reached.

**Size-of-risk was rating correctly in zero of 51 jurisdictions**, and 49 of them refused outright.

**The measurement changed the fix.** 69 at-risk sites of 38,378 — but **51 of those 69 carry a
trailing `Constant`** ready to absorb a masked failure. The blunt fix was rejected on that number
alone, and the narrow one carries a trace so an absorbed null stays auditable.

> **51 of 51 rate. OK lands on 8816 and matches ISO on every published field.**

### 2 · OI-91 — a contradiction that was arithmetic

**Found by:** running two existing measurements side by side, which nobody had done.

*"Four declare `TerrorismTerritory`, eleven use `TerritoryCodeByZipCode`"* against *"fifteen resolve
a value, sixteen a ZIP, twenty neither."* Three days on record as *"they do not obviously
reconcile."*

**`4 + 11 = 15`.** One population, not two camps plus a remainder. All fifteen declare the *same
field*; the split is only which domain table backs it.

**And the blocking was ours.** Countrywide references `TerrorismTerritory` in **zero** rule files,
and our `ZipCode` fallback was **inert** — six jurisdictions rate terrorism identically with it and
without it.

> **Terrorism was blocked in zero jurisdictions, not twenty. 51 of 51 rate. AK, VT, WY and MT match
> ISO, all four having been refused that morning.**

**The uncomfortable part, kept on the record:** the harness reported `NOT APPLICABLE` in those twenty
**with a reason attached**, and that is why it was believed. *A refusal with a well-written reason is
still a refusal.*

### 3 · OI-70 — the oldest question, and a hypothesis worth raising

**Found by:** an engineered submission, after the user supplied both an answer and a competing
explanation.

Half-up versus half-even had been open since the evaluation contract. They differ on **0 of 51**
stored submissions, so no sweep could ever settle it.

`exposure / 1000` is rounded at 0dp, so `E = 1,500,000` puts a rating product on exactly **2164.5** —
`x.5` with `x` even, where the two modes must disagree.

> **Four ties, four calls, four agreements. ISO rounds half-up.**

**The second hypothesis mattered.** *"It might truncate to four digits and then round"* named a third
behaviour that **would have looked like half-even**. It changes **0 of 432** operations, and there is
a structural reason: the `.5` threshold at 0dp and 3dp is exactly representable at 4dp, so truncating
there cannot move a value across it.

**One attempt failed instructively:** exposure 2,500 ties five times and both modes still give the
same premium. *A tie that fires is not a tie that separates.*

### 4 · OI-93 — the harness auditing itself

**Found by:** closing OI-91, which immediately produced a variant that rated and changed nothing.

NY rates terrorism unchanged from base **and ISO agrees to the cent** — because NY territory `001`
carries no terrorism charge while `002`–`006` each charge 110. The generator took `values()[0]`, so
**the variant exercised nothing while reporting as rated.**

**This is the recursive part.** The defect was not in the engine. It was in **the thing measuring the
engine**, and it silently weakened every breadth figure it appeared in.

> `probe_no_op` now returns `INERT CONTROL` (ISO's filing), `INERT VALUE` (our pick) or `MOVED`, and
> the sweep prints the verdict with the finding.

### 5 · OI-94 — the mirror image, found by widening

**Found by:** taking breadth from two jurisdictions to seven, chosen to differ structurally.

ISO returned a 400 in TX, GA and FL. **Not a validation complaint — ISO's own rule engine failing:**
*"Matrix: PremOpsSizeOfRiskLossCost, Keys: CW, 502, 50017. No results have been found."*

**We hit the identical miss** — state, then the countrywide retry — and then carried on. The
`FirstNonNull` exhausted, C6 correctly returned null, `PremOpsLossCost = None` was written, **and a
premium came out anyway.**

**Eight jurisdictions returned the identical `6845` on different base premiums.** A premium that does
not depend on the state's loss cost is **complete, plausible and wrong** — the exact failure this
engine exists to refuse.

**Checked first, because it was the obvious suspect: this was not OI-88's fix.** That emits
`branch-abandoned`; this was `exhausted`, C6, unchanged since stage 2. **What OI-88 did was make the
path reachable** — the code had never run before that morning.

> **37 of 51 rate, 14 refuse, exactly the fourteen measured. GA now refuses without making the call
> at all** — the engine reaches ISO's conclusion independently rather than spending a request to be
> told.

---

## What the shape of these has in common

**1 · Every one was found by running something against something else.** ISO's service against our
engine (OI-88, OI-94). One measurement against another (OI-91). An engineered input against a
prediction (OI-70). The harness against itself (OI-93). **None came from reading code.**

**2 · Not one needed a decision. Every one needed a measurement.** OI-88 sat first on the list for
three entries waiting for a go it did not need — the read-only blast-radius pass was always
available. OI-91 sat for three days described as irreconcilable, and reconciled in one run.

**3 · Closing a defect exposes the next one.** OI-88 made size-of-risk reachable, which made OI-94
reachable. OI-91 unblocked terrorism, which produced OI-93 within minutes. **The queue was not a
queue; it was a stack, and the top item was hiding the rest.**

**4 · The measurement changed the fix twice.** OI-88's 51-of-69 masking count ruled out the obvious
one-line change. OI-94's fix went in the rating layer *because* the measurement showed C6 was right.
**Fixing on sight would have been wrong both times.**

**5 · The harness's own defects count.** OI-93 was in the measuring apparatus, and OI-91's twenty
`NOT APPLICABLE` verdicts were our refusal wearing a good explanation. **A harness that is never
suspected of being wrong is not a harness, it is an assumption with tests.**

---

## Where the numbers stand

| | Before 2026-08-17 | After |
|---|---|---|
| Size-of-risk rating correctly | **0 of 51** | 37 of 51, **14 refusing as ISO does** |
| Terrorism | 31 of 51, blocked in 20 | **51 of 51** |
| Breadth against ISO | 31 of 31, **two jurisdictions** | **112 of 115, seven jurisdictions** |
| Rounding mode | evidenced against truncation only | **half-up, on four engineered ties** |
| Known defects | 3 | **1** (OI-89) |
| A no-op variant | reported as rated | **diagnosed** |

**Live calls spent: 92.** Every one of them aimed by an offline measurement that cost nothing.

---

## What this does not claim

**Seven jurisdictions is not fifty-one**, and one class family is not the book. Eleven of OI-94's
fourteen are **inferred** from an identical trace rather than confirmed against ISO, and they are
labelled that way everywhere they appear.

**The coverage grid still reads 1 of 19.** OI-89 is still open. `breadth.py` still carries a second
`Declared` that never received OI-93's probe — **two harnesses with one behaviour between them is how
the next silent no-op gets through**, and it is written down rather than left to be rediscovered.
