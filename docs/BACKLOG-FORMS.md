# The forms backlog — 14 October 2026

**Written 2026-10-14**, by the user's decision: finish rating first, and keep everything about which forms a policy
carries in its own list. It gathers B-15 (moved out of RC-3 of `docs/BACKLOG-2026-10-13.md`), the open part of OI-83,
and the form messages ISO's own service returns on our stored requests (`results/tc/answers`, 326 GL answers and the
Property ones, counted 2026-10-14).

**Why forms are separate from rating.** A form decides what is covered, and sometimes a charge; rating decides the
number. The engine already runs ISO's attachment rules (they are rules like any other), and Property's attach maps
(chunks 12-13) proved them for Property. Nothing has yet proved GL's, and our own test requests trip ISO's form
messages on most ratings. None of these move a premium we have compared: every comparable stored ISO answer agrees
on the money (B-38: 269 of 274; the other 5 are deliberate refusals).

**Needs** is what a task cannot start without: *your go* (an engine or console change), *ISO calls*, or something
from outside. Numbered F-01 onward so they never collide with the B-numbers.

---

### FC-1 · Our requests carry the forms ISO expects (3 tasks)

The cheapest wins: requests the harness itself builds, which ISO flags. Fix the builders first so that every later
form comparison starts from requests ISO considers well-formed.

| # | Task | Size | Needs |
|---|---|---|---|
| F-01 | **GL terrorism forms on a rejected-terrorism policy**: 68 stored GL answers carry both *"A Certified Acts of Terrorism Form cannot be attached to a policy when Certified Acts of Terrorism coverage is rejected"* and *"An Exclusion of Certified Acts of Terrorism Form must be attached to the policy when coverage is rejected"*. The console's GL request (and `variants.py`'s) attaches the coverage-side terrorism form and omits the exclusion when terrorism is "No". Fix the builders; check the messages disappear and no premium moves | Small | your go, a few ISO calls |
| F-02 | **Property CP 03 20 (Multiple Deductible Form)**: 134 stored Property answers say it must be attached when the fixed-dollar deductible differs by location or from windstorm. Find which of our Property requests (scenarios, chunk builders, console) set differing deductibles without the form; attach it where ISO says | Small-medium | your go, a few ISO calls |
| F-03 | **Property CP 10 75 / CP 10 76, CP 13 10, CP 13 20**: 28 answers *"Either CP 10 75 or CP 10 76 must be attached"*; 8 *"CP 13 10 not valid with selected Coverage Form"*; 8 *"Coinsurance selections must be identical between CP DS 04 and the Personal Property record that CP 13 20 is at"*. Same treatment as F-02 | Small-medium | your go, a few ISO calls |

### FC-2 · Prove GL form attachment (2 tasks)

| # | Task | Size | Needs |
|---|---|---|---|
| F-04 | **GL attach map** (was **B-15**, August item 6): 508 of 570 packages ship sample submissions and nothing tests which forms GL attaches. Build GL's attach map the way Property's was built (chunks 12-13): from ISO's rules and `Form Pages`, per state and edition. OI-127 already showed one wrong attachment (the Personal & Advertising Injury exclusion, fixed 2026-10-13) | Medium | your go |
| F-05 | **GL forms against ISO**: compare the forms we attach with ISO's on the samples and on the B-12 / B-13 requests (326 stored GL answers already carry ISO's attached forms -- measure those first, free) | Medium-large | your go, ISO calls after the free pass |

### FC-3 · Form rules ISO raises that nothing reads yet (2 tasks)

| # | Task | Size | Needs |
|---|---|---|---|
| F-06 | **Cannabis exclusion forms**: 10 stored answers *"Only one Exclusion Form for Cannabis can apply to the risk"*. Which requests attach two, and should a request with two refuse or warn (like B-07's form messages, which stay as ISO prices them). **Decided 2026-10-27 (you): warn with ISO's message, price as ISO does** | Small | your go (in the forms free pass) |
| F-07 | **The remaining unread package directories** (OI-83, partial): `Metadata` (circular provenance per rule and table), `Ratebook Tables` / `Ratebook Columns`, and GL `STC`. Read them where a form task needs them; record the rest as decided-not-needed | Small | — |

---

**Recommended order:** FC-1 first (our own requests clean), then F-05's free pass over the stored answers, which
sizes F-04 and the ISO calls F-05 needs. F-06 whenever; F-07 as needed.
