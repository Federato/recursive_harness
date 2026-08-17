# The backlog, as feature sets — 17 August 2026

**Written 2026-08-17, the day OI-88 closed.** The same work as
[`BACKLOG-2026-08-14.md`](BACKLOG-2026-08-14.md), regrouped.

**Why regrouped.** The 14 August backlog is an ordered queue, and that shape answers *"what is
next?"* It does not answer *"what am I choosing between?"* — which is the actual question, because
the items are not independent. Items 7b and 8 are the same store built twice. The live-comparison
items reinforce each other and are near-worthless one at a time. A flat list hides both.

**That file stays the source of truth for the detail** — every item below names its number there,
and nothing here restates an argument made there. This is a decision aid, not a second backlog.
`docs/OPEN-ITEMS.md` remains the register.

---

## A · Prove it against ISO — *confidence in the number*

The engine agrees with ISO on **50 of 50 jurisdictions, on the premium and every published field**.
The population is the limit, not the engine. Nothing in this set changes behaviour; it widens the
evidence.

| | What it buys | Size |
|---|---|---|
| **Keep widening breadth live** | **Eleven jurisdictions done 2026-08-17 — 184 of 184 comparable outcomes agree.** OI-94 confirmed in 13 of 14. **40 remain**, ~17 calls each — but the discovery rate is falling and the population is still **one class family**, which is now the narrowest axis | **Medium; consider varying class family next** |
| **Fill the coverage grid** | Still reads *1 of 19*. The honest measure of how much of the engine has ever been exercised | **Medium** |
| ~~**Close the rounding question — OI-70**~~ | ✅ **CLOSED 2026-08-17.** Four engineered ties, four live calls, four agreements — **ISO rounds half-up**. The *"truncate to four digits then round"* hypothesis was tested too: **0 of 432** operations change | **Done** |
| **Form attachment — item 6, OI-83** | **508 of 570 packages ship sample submissions**, 510 JSON files, and **nothing currently tests form attachment at all** | **Medium–large** |
| **Referral register vs ISO's own — items OI-81, OI-82** | Ours is **28 hand-derived conditions**; ISO declares **838** in a workbook inside every package. Five of the fourteen we carry and do not detect can produce a wrong number: `R12, R15, R17, R25, R26` | **Medium** |

**Unblocks Phase 3.** A harness that adjudicates differences is worth building once there are
differences to adjudicate. On one risk shape there are none.

---

## B · Defects

**D1/OI-88 and D2/OI-91 both closed 2026-08-17.** One item remains of *known wrong*, and the
terrorism work raised one new one.

| | Why it matters | Size |
|---|---|---|
| ~~**OI-94 — a null loss cost does not stop the rating**~~ ✅ **CLOSED 2026-08-17** | **Raised 2026-08-17 by widening breadth, and the mirror of OI-88** — there we refused where ISO rated; here **we rate where ISO refuses.** ISO's own engine 400s on the missing `PremOpsSizeOfRiskLossCost` row; we exhaust to null via C6 and finish the premium. **14 of 51 jurisdictions**, 3 confirmed live, 11 inferred. Eight return the identical `6845` on different bases. **Closed the same day.** 37 of 51 rate, 14 refuse as ISO does; zero still rates, because 0 is a filed loss cost | **Done** |
| **OI-89 / D3 — schedule rating gate** `MEDIUM` | Not a wrong number — ISO's own rule. But a plan can be **requested and silently not applied**, and no field declaration can reveal the condition. **Now measured across all 51:** with the switch *and* a percentage set, schedule rating moves the premium in exactly **FL, NY and RI** and in **48 of 51 it does not** — all three confirmed live. Three jurisdictions override countrywide wholesale (N3); 48 hold the credibility condition. **The size of the effect is no longer unknown**; the ~20 dated experience-rating fields still are | **Medium** — needs ~20 dated experience-rating fields first |
| ~~**OI-93 — `values()[0]` can be a no-op**~~ | ✅ **Raised and closed 2026-08-17.** `probe_no_op` returns `INERT CONTROL` / `INERT VALUE` / `MOVED`, and the sweep prints the verdict with the finding | **Done** |

**Not to be fixed by picking a value that moves the premium** — that is choosing a value to make a
test pass. Either rate every declared value where the domain is small, or report the no-op with the
value that caused it.

---

## C · Multi-carrier foundations — *the Phase 4 groundwork*

**Items 7b and 8 overlap almost exactly and should be built together.** Both are
`(carrier, jurisdiction) → thing` stores with per-jurisdiction effective dates and per-jurisdiction
opt-out.

| | State | Size |
|---|---|---|
| **Carrier edition pinning — item 8** | Decided, and **most of it already exists** — built for backdating, same machinery. Missing one input: `(carrier, jurisdiction, as-of)` instead of `(jurisdiction, as-of)`. The resolver change is small; the configuration surface and the refusal cases are the work | **Medium** |
| **Deviation authoring — items 7a, 7b** | Decided, **none built**. A friendlier format that *compiles* to ISO's shape — safe because *"ISO's answer times our factor"* is already the shape of 4,598 rules in ISO's own content — and stored **per jurisdiction, always** | **Large** |

**Know before starting:** pinned configurations **may not be externally verifiable.** ISO's service
rates on the edition *it* selects. If it will not rate an old edition, those configurations cannot
be checked against the oracle at all — establish that before assuming every carrier setup is
provable.

---

## D · Validation exactness — *item 5, OI-84*

**29 of 90 dependent domains resolve exactly**; the other 61 fall back to a superset that can accept
an illegal value but never reject a legal one, and every finding already says which of the two it
is. Precision, not correctness.

**Medium**, and it needs per-field mappings **verified one at a time** — name-based resolution was
tried and rejected on evidence, because `GeneralAggregateLimit` is keyed by a field name that does
not exist.

---

## E · Property — *a second line*

**Exploration only, by decision 2026-08-17.** `CF_Algorithm/` documents building rating across all
four cause-of-loss forms from one countrywide package.

The next honest step is **reading, not code**: what a CF *state* package changes against the
countrywide one already documented, and whether the four-form structure survives contact with a
second jurisdiction. **Small to start. No build until that is answered.**

---

## F · Housekeeping — *cheap, and one of them is a real blind spot*

- **`567 → 570`** through the docstrings and the docs. Three packages arrived since the figure was
  taken.
- **`verify_contract_figures` should re-measure rather than read cached `scripts/erc/out/`.** It
  **passed against stale numbers on 2026-08-17** — a test that cannot fail when it should is worth
  more than the prose it guards.

---

## G · Parked — *not to be picked up until something changes*

**The table browser** (item 7c and the parking lot). Constrained by per-tenant ISO licensing, and
the trace already answers *"what rated this policy, and why"* — the question underwriters actually
ask, as against *"what rates exist"*.

**Phase 3 — the self-correcting loop.** Wants set A first.

**Phase 4 — company deviations.** Deliberately last: once company content is layered on, no external
service can confirm the answer.

---

## The recommendation on 2026-08-17

~~**B first, and OI-91 within it.**~~ **Done the same day.** It reconciled rather than needing a
decision — `4 + 11 = 15` — and the blocking turned out to be ours, so terrorism went from 31
jurisdictions to 51.

**Now: A.** Both closures widened what can be rated and **nothing has been re-compared live since.**
Size-of-risk rates in 51 where it rated in 2; terrorism rates in 51 where it rated in 31; only OK and
five terrorism jurisdictions have been checked against ISO. **The breadth re-run is no longer a
tidying task — it is the largest block of unverified new coverage in the project.**

~~**Cheapest useful thing:** A's rounding experiment.~~ **Done 2026-08-17** — four calls, and the
project's oldest open question is closed. **ISO rounds half-up**, the engine's default all along, now
evidenced.

**Argued against starting yet, unchanged:** C. The largest single block, and the one place where no
external oracle can confirm the answer. Set A's evidence should be broader before the ISO baseline
has to be trusted alone.
