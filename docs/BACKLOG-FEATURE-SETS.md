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

## B · The last two defects

**D1/OI-88 closed 2026-08-17.** These are what remains of *known wrong*, as against *not yet known*.

| | Why it matters | Size |
|---|---|---|
| **OI-91 / D2 — terrorism location** `HIGH` | Two measurements — *4 and 11* by which domain table the field names, *15 / 16 / 20* by whether the jurisdiction resolves a legal value — and nobody has written down which a caller should trust. **Terrorism breadth is blocked in 20 jurisdictions.** The figures are quoted in `validate.PLACE_CODED`, the E8 escalation and R22, so whichever reading wins, more than one document moves | **Small–medium** — a measurement, not a fix |
| **OI-89 / D3 — schedule rating gate** `MEDIUM` | Not a wrong number — ISO's own rule. But a plan can be **requested and silently not applied**, and no field declaration can reveal the condition. **OI-88's closure sharpened it:** CA and NY now rate size-of-risk unchanged from base, the same per-jurisdiction override in a second place | **Medium** — needs ~20 dated experience-rating fields first |

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

**B first, and OI-91 within it.** It is a measurement rather than a fix, it is the last `HIGH`, and
it is the only item actively blocking something — terrorism breadth in 20 jurisdictions. Closing it
makes set A meaningfully wider the same day.

**Cheapest useful thing:** A's rounding experiment. One live call could close the oldest open
question in the project.

**Argued against starting yet:** C. The largest single block, and the one place where no external
oracle can confirm the answer. Set A's evidence should be broader before the ISO baseline has to be
trusted alone.
