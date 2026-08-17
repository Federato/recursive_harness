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
| **Re-run breadth live, OK + NY** | The 31-of-31 figure **predates OI-88's closure**. Size-of-risk now rates in 51 jurisdictions and only OK has been checked live | **Small** — ~35 live calls |
| **Fill the coverage grid** | Still reads *1 of 19*. The honest measure of how much of the engine has ever been exercised | **Medium** |
| **Close the rounding question — OI-70** | The project's oldest open question. Half-up and half-even differ on **0 of 51** submissions today; one crafted submission settles it. The med-pay charge is the promising site — solve for an exposure landing the product on `2.5` | **Very small** — one live call |
| **Form attachment — item 6, OI-83** | **508 of 570 packages ship sample submissions**, 510 JSON files, and **nothing currently tests form attachment at all** | **Medium–large** |
| **Referral register vs ISO's own — items OI-81, OI-82** | Ours is **28 hand-derived conditions**; ISO declares **838** in a workbook inside every package. Five of the fourteen we carry and do not detect can produce a wrong number: `R12, R15, R17, R25, R26` | **Medium** |

**Unblocks Phase 3.** A harness that adjudicates differences is worth building once there are
differences to adjudicate. On one risk shape there are none.

---

## B · The last defect

**D1/OI-88 and D2/OI-91 both closed 2026-08-17.** One item remains of *known wrong*, and the
terrorism work raised one new one.

| | Why it matters | Size |
|---|---|---|
| **OI-89 / D3 — schedule rating gate** `MEDIUM` | Not a wrong number — ISO's own rule. But a plan can be **requested and silently not applied**, and no field declaration can reveal the condition. **Two closures sharpened it:** CA and NY rate size-of-risk unchanged from base, and NY rates terrorism unchanged too — the same per-jurisdiction question in three places now | **Medium** — needs ~20 dated experience-rating fields first |
| **OI-93 — the variant generator picks `values()[0]`, which can be a no-op** `NEW` | Raised 2026-08-17 the moment OI-91 unblocked terrorism. NY territory `001` carries **no** terrorism charge where `002`–`006` charge 110, so the NY variant **exercises nothing while reporting as rated**. Nothing but the sweep's per-run *"unchanged from base"* line notices. Same kind as E20/OI-68: **a legal value that does nothing looks exactly like a working one** | **Small–medium** |

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

**Cheapest useful thing, unchanged:** A's rounding experiment. One live call could close the oldest
open question in the project.

**Argued against starting yet, unchanged:** C. The largest single block, and the one place where no
external oracle can confirm the answer. Set A's evidence should be broader before the ISO baseline
has to be trusted alone.
