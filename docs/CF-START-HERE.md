# Property build — start here

**Last worked 2026-09-24.** This is the resume point: where things stand, how to
confirm it in two minutes, and what to pick up first.

---

## Pick up here: chunk 12 is CLOSED (2026-09-24); chunk 13 is next

**Chunk 12 gated 2026-09-24, 42 of 42** ([`CF-CHUNK12-GATE.md`](CF-CHUNK12-GATE.md)):
all six endorsement families 9 of 9, 0 unexplained messages. Ordinance or Law K7
was re-run live after the OI-109 fix and agrees (8 of 8). The regression was re-run
2026-09-24: **CLEAN** for chunks 0–12 and all GL suites.

**Chunk 13, Terrorism / TRIA, OPENED 2026-09-24 at 1 of 30**
([`CF-CHUNK13-TASKS.md`](CF-CHUNK13-TASKS.md), census `143_chunk13_census.py`).
Tasks are in five release-candidate groups, in priority order. **Start at RC-1:
C13-02 (rule order) and C13-03 (replay the 14 stored ISO responses that carry a
terrorism premium).** Both DONE 2026-09-24; C13-03 found **OI-111** (a named
`ancestor::` read as the document root), **fixed with the user's authorization,
the 10th engine fix**: replay 14 of 14, regression clean. Next: C13-04, C13-05. Then chunk 14, policy assembly.
Open from the chunk 12 gate, not blocking: priced FL/VA/WV cases, and a theft
exclusion attached to the Contents/BI records for drones and Dependent Properties.

### Chunk 12 history (as of 2026-09-23)

**All six families are closed, gated 9 of 9 and ISO-confirmed live.** Group G,
Dependent Properties: [`CF-CHUNK12-DEPENDENT-PROPERTIES.md`](CF-CHUNK12-DEPENDENT-PROPERTIES.md)
($80 + $12, 12 of 12 live). **One step left:**
1. ~~**C12-41:**~~ done: the regression now covers chunks 0–12 and ran
   **CLEAN** on 2026-09-23 (`python scripts/cf/104_chunk10_c10-21_regression.py`).
2. **C12-42:** file `docs/CF-CHUNK12-GATE.md` (six families, nine points each;
   the evidence is in the seven `CF-CHUNK12-*.md` records), then mark chunk 12
   closed on the status page.

**Engine changes this session (user-authorized, regression clean after each):**
OI-108 (`Sum` finishes before a `Break` ends the loop), and OI-109/OI-110
(Property's `Product` skips a null operand as ISO does, each skip recorded in
`Interpreter.null_skips`; GL untouched).


**Groups E and F closed 2026-09-23.** Unmanned Aircraft
([`CF-CHUNK12-UNMANNED-AIRCRAFT.md`](CF-CHUNK12-UNMANNED-AIRCRAFT.md)): $187
golden, 10 of 10 live. Green Upgrades
([`CF-CHUNK12-GREEN-UPGRADES.md`](CF-CHUNK12-GREEN-UPGRADES.md)): $33 golden,
no fixtures, 8 of 8 live. **Next: Group G, Dependent Properties
(C12-35 to C12-40), then H (fold chunk 12 into the regression, file the
gate).** Nothing from 2026-09-23 is committed yet; the user decides when.


**Groups C and D closed 2026-09-23.** Ordinance or Law
([`CF-CHUNK12-ORDINANCE-OR-LAW.md`](CF-CHUNK12-ORDINANCE-OR-LAW.md)): $198
golden, 7 of 8 live, and the one divergence, **OI-109** (absent B/C limits: ISO $0), since fixed. Utility Services
([`CF-CHUNK12-UTILITY-SERVICES.md`](CF-CHUNK12-UTILITY-SERVICES.md)): $15 + $4
direct damage, $9 + $4 time element, 10 of 11 live. The live comparer for any
family is `132_chunk12_family_raas.py`. **Next: Group E, Unmanned Aircraft
(C12-23 to C12-28)**, OI-108 (fixed 2026-09-23) is in its path.


**Group B, Debris Removal, closed 2026-09-23: gated 9 of 9 and ISO-confirmed
live** ([`CF-CHUNK12-DEBRIS-REMOVAL.md`](CF-CHUNK12-DEBRIS-REMOVAL.md)). Golden
case $49 + $6 = $55 (`127`), gates `128`, live `129` (9 of 12 agree; the 3
refusals are Earthquake lookups in old fixtures, added to OI-103). ISO itself
returns a negative premium for a limit under $25,000 (message M-003), and
charges a "No Coverage" building. **Next: Group C, Ordinance or Law
(C12-11 to C12-16)**, including Virginia's and West Virginia's state-only
forms.


**Group A closed 2026-09-23** ([`CF-CHUNK12-GROUP-A.md`](CF-CHUNK12-GROUP-A.md)).
Family order confirmed as recommended. Nothing ever deletes an endorsement
record; 17 of 17 ISO fixtures with a chunk 12 record rate end to end;
Ordinance or Law is 100 files, not 55 (Virginia's and West Virginia's
state-only forms). **One suspected engine gap, logged, not fixed: OI-108**
(a blanket drone's limit reads 0 in CA, NC and MO). Fixing it is an engine
change and needs the user's go. (Group B has since closed; see above.)

**Opened 2026-09-22.** [`CF-CHUNK12-TASKS.md`](CF-CHUNK12-TASKS.md) ·
[`123_chunk12_census.py`](../scripts/cf/123_chunk12_census.py). 42 tasks in 8 groups:
A (opening: sequence, attach map, operand types, EQ riders), then one six-task
group per family (B Debris Removal, C Ordinance or Law, D Utility Services,
E Unmanned Aircraft, F Green Upgrades, G Dependent Properties), then
H (regression and gate).


**Chunk 11 (Leasehold Interest) is CLOSED 2026-09-22: 24 of 24 tasks, gated 9
of 9** ([`CF-CHUNK11-GATE.md`](CF-CHUNK11-GATE.md)). The golden case matched ISO
live to the digit. Four engine fixes, all user-authorized and ISO-confirmed:
date comparison, the `01/01/0001` sentinel (OI-102), 0^0 (OI-104), and the
`DateDifference` sign (OI-107). Regression clean, 69 of 69.
**Backlog (none blocking):** OI-101 (closes with OI-105), OI-103, OI-105,
OI-106, and the GL ERP check left by OI-107. See the gate's backlog table.

### Chunk 11 history

**Chunks 0–10 are closed. Chunk 11 is OPEN at 21 of 24 tasks (2026-09-22; A–F done).** Earlier status line:
Groups A–D are done.** Group D ([`CF-CHUNK11-GROUP-D.md`](CF-CHUNK11-GROUP-D.md)): shared machinery is
clean. It found that ISO fixed OI-101 in its 2027 edition, that form names don't
resolve project-wide (OI-106, no premium impact), and that OI-104 is easy to
reach (an LI structure with no LI record crashes our engine).
**Earlier (still true):
Groups A (the annuity), B (the four sub-coverages) and C (zero cases, asked
live at ISO) are done.** Group C: [`CF-CHUNK11-ZERO-CASES.md`](CF-CHUNK11-ZERO-CASES.md).
ISO agreed on 11 of 14 and diverged on 3, all predicted. **OI-102 has since been fixed** (a blank date now orders as the earliest date, as at ISO; regression clean). OI-103 and OI-104 remain open.
**Send live ISO calls at 2026-09-17, not 2027**: ISO holds a newer Oregon
edition for 2027 than our local corpus (OI-105). Group B
([`CF-CHUNK11-GROUP-B.md`](CF-CHUNK11-GROUP-B.md)) found that only Tenants
Lease is discounted, and that Special without a Theft Exclusion prices at $0
by ISO's own rule (**OI-101**, owed a live ISO call). The golden case matches
at **$268 BGI + $30 BGII** (`114_chunk11_golden_case.py`,
[`CF-CHUNK11-GOLDEN-CASE.md`](CF-CHUNK11-GOLDEN-CASE.md)). One authorized engine fix:
ordered comparisons now accept two dates
([`CF-ENGINE-FIX-DATE-COMPARE.md`](CF-ENGINE-FIX-DATE-COMPARE.md)). The regression is clean.
**Done 2026-09-22 after Group D:** the one-command regression now covers **chunks 0–11**, and **OI-104 is fixed** (0^0 = 1, as ISO; an LI structure with no LI record now prices $0 instead of crashing). Regression clean.
**Groups E and F done 2026-09-22** ([`CF-CHUNK11-GROUPS-E-F.md`](CF-CHUNK11-GROUPS-E-F.md), 46 states): the inventory is clean, and Florida runs the 2023 chain without injection guards. **OI-107 (our `DateDifference` had the wrong sign; ISO +257, ours −257, confirmed live on Oregon's TRIA field) was fixed the same day with authorization.**
**Left in chunk 11:** C11-09 (messages), C11-22 (ISO golden + rounding tie), C11-24 (close-out regression). The tasks are grouped by
theme on `CF-BUILD-STATUS.html`.

**Two input rules every LI submission needs**, both silent if missed: the
Structure's own `CovType` must be `Leasehold Interest` (plus
`PolicyType = Commercial Property Policy`), or the LI record is deleted; and
`EQCovIndicator` must be `No Coverage`, not blank, or the EQ cell switches on.
[`CF-CHUNK11-TASKS.md`](CF-CHUNK11-TASKS.md) ·
[`106_chunk11_census.py`](../scripts/cf/106_chunk11_census.py)

**Confirm everything is green in one command** (this is new — it used to be a
page of scripts to run by hand):

    python scripts/cf/104_chunk10_c10-21_regression.py

**Four things the chunk 11 census already found, before any task has run:**

* **32 rule files, but only 21 of them rate.** The 11
  `FactorsFor<N>Percent` files (5% through 15%) declare `InitializeRuleSet` /
  `CalculateTotalPremium` / `ErcProcess` and nothing else — printed
  form-attachment markers, no `Lookup`, no `Premium`, no factor.
* **"Its own datadef group" is 32 groups, not 1** — one per file. Gate points
  6 and 7 are per-group questions, so chunk 11 asks them across 32 groups
  against the 5 that chunks 6–10 worked with. **The biggest structural jump
  in the plan so far**, and a counting fact rather than an estimate.
* **The fifth form is Earthquake.** Chunk 10 is a direct input here, not a
  parallel track — the first coverage opened *after* the form it depends on
  was built.
* **Zero ISO fixtures.** Of 364 CF payloads, **0** mention Leasehold
  Interest. This is chunk 9's situation, not chunk 10's: confirmation has to
  come from a **live ISO call**, and that is planned at task 1 rather than
  discovered at task 22.

**The single sharpest thing to be careful about:** the `rul:Power` — the only
one in all 882 countrywide rule files — sits behind an `IsNull` guard on
`DiscFactorRaisedToNumOfMonthsRemainingAtInception`. A submission that
supplies that value directly **bypasses the annuity entirely, and no ISO
comparison catches it, because ISO has the same guard.** That is the standing
"a submission can populate a derived field" trap, in the one chunk whose
exposure is computed rather than entered.

---

### The historical record, chunk by chunk

**Chunk 3 is closed — gated 8 of 9 on 2026-09-18, all 24 tasks done, no engine
code written.** See [`CF-CHUNK3-GATE.md`](CF-CHUNK3-GATE.md).

**Chunk 4 is closed — gated 8 of 9 on 2026-09-18**, **all 32 tasks done** and
still no engine code. See [`CF-CHUNK4-GATE.md`](CF-CHUNK4-GATE.md).

**Chunk 5 is closed — gated 8 of 9 on 2026-09-18**, **all 28 tasks done**
and still no engine code. See [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md).

**Chunk 6 is OPEN — Special Class, building side.** 29 tasks numbered
**C6-01–C6-29** in [`CF-CHUNK6-TASKS.md`](CF-CHUNK6-TASKS.md), derived from the
algorithms doc and from the opening census
([`40_chunk6_census.py`](../scripts/cf/40_chunk6_census.py)). **Chunk 6 is closed: all 29 tasks, gated 8 of 9.**

**Chunk 7 is OPEN — Special Class Business Income.** 28 tasks numbered
**C7-01–C7-28** in [`CF-CHUNK7-TASKS.md`](CF-CHUNK7-TASKS.md), derived from the
algorithms doc and from the opening census
([`49_chunk7_census.py`](../scripts/cf/49_chunk7_census.py)), **which carries
chunk 6's OI-100 correction in from the start** — every state diffed against its
own resolved parent, both package ids printed. **Chunk 7 is closed: all 28 tasks, gated 8 of 9.**

**Chunk 8 is closed: all 26 tasks, gated 7 of 9** —
[`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md). **Two points are held open on
purpose**: point 9 is owed project-wide, and **point 8 is held on CA, FL and
PR**, three jurisdictions that produce no Legal Liability premium for reasons
not yet established. Three unexplained zeros is the shape chunk 6 taught us not
to wave past.

**Chunk 8's headline: the best-prepared input any chunk has started from was
moved by running it.** An eleven-point divergence map, traced from rule XML by a
person — **8 of 11 confirmed, 3 corrected**, plus a stale line, an over-claim
and two things it does not mention:

* **Point 7** — blanket: the conclusion holds, the reason does not. The coverage
  gate writes 0 before the `Choose` the map reasons about is ever reached, and
  the cause is the same empty `BlktCauseOfLossValue` C6-28 and C7-25 found.
  **Three chunks, three coverages, one mechanism.**
* **Point 10** — Builders Risk is not `0.0`. `Premium` is **null**, we refuse,
  and **ISO charges $1**. OI-99's second instance, opposite in direction to
  Florida's.
* **Point 11** — the operand order **is** premium-bearing: $11 nested against
  $12 as a single product, at PackageMod and IRPM of 0.44.
* **Not mentioned at all** — switching the Building to Legal Liability takes
  **Contents'** LOI factor from 0.898 to 1 and its premium from $223 to $248.
  **The fork is not confined to its own premium.**

**And two harnesses nearly published results they had not earned.** A probe
whose ISO payload carried `PolicyType` and whose engine submission did not —
which read as an engine defect and would have put chunks 1–7 through a full
re-run. And a sweep that agreed with itself at $0 forty-six times because it
sent Oregon's territory to every state. Both recorded in place.

**Chunk 9 is CLOSED — Blanket rating, 22 of 22, gated 9 of 9.** Opened and
closed 2026-09-21. [`CF-CHUNK9-TASKS.md`](CF-CHUNK9-TASKS.md),
[`CF-CHUNK9-GOLDEN-CASE.md`](CF-CHUNK9-GOLDEN-CASE.md) and
[`CF-CHUNK9-GATE.md`](CF-CHUNK9-GATE.md) carry the full record. The opening
census overturned its own premise: **zero of the 20 premium files stub the
blanket formula out** — every one carries `IRPMFactor × PackageModFactor ×
Blkt<Form>AvgRate × (item value / BlktTotalFullValueAmount) × (BlktLimit/100)`
already filed. What was missing was the input, traced to `SetNonEQBlanketValues`
and a wholly separate 135-rule averaging engine
(`CommercialPropertyBlanketRatingDetailRules.Rule.xml`) no chunk 1–8 script had
ever opened. **The fix was a real interpreter bug**, not a rating gap:
`ForEach AtInputDataDef` reparented writes onto the iterated Detail record
along with reads — the first engine change since chunk 0, user-authorized,
with every chunk 1–8 script and all 16 GL suites re-verified green after it.
**ISO confirmed the fix live**, to the dollar, for a submission that exists
nowhere in ISO's own 924-payload fixture corpus.

**Chunk 10 is CLOSED — Earthquake, 21 of 21 tasks, gated 9 of 9.** Opened and
closed 2026-09-22. [`CF-CHUNK10-TASKS.md`](CF-CHUNK10-TASKS.md),
[`CF-CHUNK10-GOLDEN-CASE.md`](CF-CHUNK10-GOLDEN-CASE.md) and
[`CF-CHUNK10-GATE.md`](CF-CHUNK10-GATE.md) carry the full record. Three things
worth carrying forward:

* **The second real engine fix in the project**, user-authorized:
  `_lookup_banded` could not read a table with two banded key ranges at once,
  which made the Earthquake sub-limit form (CP 10 29) **unreachable**. A
  corpus-wide scan *before* the fix found the same limitation silently
  blocking **7 live Flood rate-modification tables and 1 Massachusetts
  heating-oil rider** — the fix was scoped by measuring the population, not by
  patching the one table that failed.
  [`CF-ENGINE-FIX-BANDED-LOOKUP.md`](CF-ENGINE-FIX-BANDED-LOOKUP.md).
* **The ISO fixture corpus is 364 Commercial Property payloads, not 924.**
  The 924 figure silently included **560 General Liability payloads**. Any
  fixture claim in this project states 364. C10-20 also found that counting
  one regex match per file misses every repeating record after the first —
  ISO's "69 Earthquake fixtures" are 69 *structures*, and the corpus holds
  **149 electing records**.
* **A golden case can be at 9 of 9 and still be unrepresentative.** Three of
  chunk 10's four golden-case coordinates — Oregon, Basic Group I, and its CP
  10 40 form — are exercised by **zero** of ISO's 69 fixtures. That is not a
  defect in the gate; it is the honest statement of what a gate covers.

**Next: chunk 11, Leasehold Interest** — see the top of this page.

The paragraphs below (chunk 6's opening findings) are historical — kept for
the record of how that chunk was opened.

Three things the census already found:

* **The first coverage that borrows a FULLY RATED rate.** **Eleven** values
  cross the boundary — `BasicGroupIRate` and `EQRate` copied outright, and
  three inputs feeding its own lookups. **No `BasicGroupIBaseRate` anywhere**,
  so unlike chunk 5 it cannot rate until the parent's build-up has *completed*.
* **Special's base rate is pinned to "Other than Apartments and Condominiums"**,
  making the apartment rows permanently unreachable from this group — while
  plain Business Income reaches them on the same physical table. The theft
  factor two steps earlier still varies by `ApartmentCondoIndicator`.
* **Six states delete `SetLowestBasicGroupIIBaseRate` outright** (AR, DC, KS,
  NY, RI, TX) — six of the eight that file no lowest-rate table, so C6-19's
  biconditional gets re-asked on a second coverage.

Three things the census already found, before any task has run:

* **The rating driver is a free-text class DESCRIPTION**, resolved through two
  lookups in series to one of 71 `OptionNN` codes. No construction key at all.
* **Florida is two countrywide editions behind** (`CF_CW_20230801_V01` against
  everyone else's `CF_CW_20260601_V01`), so its class vocabulary is frozen at
  2023. **The private option namespace is New York's** — 63 codes to
  countrywide's 71, 35 of them nowhere countrywide.
* **New York deletes both converter rules** and files both converter tables
  header-only, while still filing 189 Group I rate rows. Either those rows are
  unreachable or the option is a submitted field there. C6-12 decides by running
  it.

Chunk 5 is different in kind again: **Business Income is arithmetically
downstream of Building.** Three of its five forms have no base rate of their own
and read Building's already-computed rate, symbol and territory. It is the first
coverage in the project that cannot be rated without rating another coverage
first — so every chunk 1–3 finding is now load-bearing twice. Its `SetFactor`
picks **exactly one** of four values, and multiplying them would overstate the
premium by a large multiple.

Chunk 4 is different in kind, not just in data: it is the **first chunk that
rates a repeating group** (N Personal Property records per Occupancy Class,
driven by a `ForEach`), `CovForm` rather than `CovType` drives the branch and is
inherited from the occupancy class, and **PP's Special is the opposite of
Building's** — occupancy-keyed with its own territory multiplier, 14 steps
against 9.

The work follows a settled rhythm, and it is worth keeping:

> **Derive the expected numbers by hand from the filed rows FIRST, write them
> down, then run.** Every finding worth having in this project came from a
> prediction disagreeing with the engine — Arizona, the BCEG zero, the Kansas
> wind/hail mechanism, the cumulative forms. Observing what the engine does and
> writing that down proves nothing.

---

## Where the project stands

**Current as of 2026-09-22.**

| | |
|---|---|
| Chunks closed | **11 of 15** (0 through 10); chunk 11 **open at 0 of 24** |
| Chunk 1 — Building Basic Group I | gate **8 of 8**, ISO-confirmed |
| Chunk 2 — Building Basic Group II | gate **8 of 8**, ISO-confirmed |
| Chunk 3 — Broad and Special | gate **8 of 9**, ISO-confirmed; 47 of 47 states |
| Chunk 4 — Contents | gate **8 of 9**, ISO-confirmed; 46 of 47 states; 32 of 32 tasks |
| Chunk 5 — Business Income | gate **8 of 9**, ISO-confirmed; 44 of 47 states; 28 of 28 tasks |
| Chunk 6 — Special Class | gate **8 of 9**; 47 of 47 states; 29 of 29 tasks |
| Chunk 7 — SC Business Income | gate **8 of 9**; 47 of 47 states; 28 of 28 tasks |
| Chunk 8 — Legal Liability | gate **7 of 9** (2 points held open on purpose); 26 of 26 tasks |
| Chunk 9 — Blanket rating | gate **9 of 9**, ISO-confirmed live; 22 of 22 tasks |
| Chunk 10 — Earthquake | gate **9 of 9**; 21 of 21 tasks; **1 engine gap found and fixed** |
| ISO calls made | ~46. The engine has matched every premium; **one handling divergence found** — ISO refuses where we return $0 (OI-99) |
| General Liability | untouched — **16** suites green throughout |

**Two engine changes in eleven chunks, both user-authorized, both written up
in full.** Chunks 1–8 ran on chunk 0's foundation untouched. Chunk 9 fixed
`ForEach AtInputDataDef` reparenting writes as well as reads
([`CF-CHUNK9-GOLDEN-CASE.md`](CF-CHUNK9-GOLDEN-CASE.md) §8); chunk 10 fixed
`_lookup_banded`'s one-range-per-table limit
([`CF-ENGINE-FIX-BANDED-LOOKUP.md`](CF-ENGINE-FIX-BANDED-LOOKUP.md)). **Both
were found by RUNNING a real submission, not by reading rule XML**, and both
had their blast radius measured across the whole corpus before the patch
rather than after.

### Settled, with evidence

| | |
|---|---|
| **Rounding** | `ROUND_HALF_UP`, **proven** against ISO at both scales (3dp rate steps and whole-dollar premium) — not assumed |
| **Null in arithmetic** | `propagate` — null in, null out; comparison with null is false. Two rival hypotheses built and disproven |
| **Null premium guard** | a null written to `Premium` or `ErcCalculatedTotalPremium` is refused |
| **Forms are cumulative** | Broad/Special layer ON TOP of Basic, they do not replace it. ISO confirms all three totals |

---

## Confirm it is all still green

**The golden cases — one line per coverage, with what each must produce.**

| Command | Must produce |
|---|---|
| `python scripts/cf/00_chunk0_checks.py` | the foundation: operators, resolver, edition chain |
| `python scripts/cf/01_golden_case.py` | chunk 1 Building Basic Group I — **$261 / $263 / $288** |
| `python scripts/cf/09_chunk2_golden_case.py` | chunk 2 Building Basic Group II — **$261 + $32** from one submission |
| `python scripts/cf/15_chunk3_golden_case.py` | chunk 3 Building Broad and Special — **$16 / $54**, layering onto Basic's own **293** (= 261 + 32, chunk 2's figure, not printed by this script) to reach **309 / 347** |
| `python scripts/cf/22_chunk4_golden_case.py` | chunk 4 Contents, four forms — **$223 / $24 / $16 / $137**, Building unmoved at 263 / 32 |
| `python scripts/cf/32_chunk5_golden_case.py` | chunk 5 Business Income, four forms — **$112 / $13 / $23 / $47**, Building unmoved at 261 / 32 |
| `python scripts/cf/41_chunk6_golden_case.py` | chunk 6 Special Class, four forms — **$66 / $209 / $14 / $44**, Building unmoved at 261 / 32 |
| `python scripts/cf/50_chunk7_golden_case.py` | chunk 7 Special Class Business Income — **$39 / $123 / $23 / $47**, the item unmoved at 66 / 209 |
| `python scripts/cf/59_chunk8_golden_case.py` | chunk 8 Legal Liability — Building **$60 / $7 / $4 / $12**, Contents **$132 / $15 / $11 / $93** |
| `python scripts/cf/68_chunk9_golden_case.py` | chunk 9 Blanket rating, two dispersed structures — **$255 / $510** |
| `python scripts/cf/85_chunk10_golden_case.py` | chunk 10 Earthquake, Building Basic Group I — **$6** |
| **`python scripts/cf/104_chunk10_c10-21_regression.py`** | **the chunk 0–11 rows above, all at once** (chunks 10–11 added 2026-09-22) — each golden case checked against its documented figure (not just its exit code), plus 25 machinery scripts and all 16 GL suites. Chunk 10's own `85_…` case is deliberately outside it: a regression harness is for what came before the change. `--selftest` proves the harness can fail |

**The machinery each chunk added**, worth running when shared code changes:

| Command | What it holds |
|---|---|
| `python scripts/cf/21_chunk3_special_structure.py` | chunk 3's Special structure — incl. the $11,398 derived-field case |
| `python scripts/cf/23_chunk4_foreach.py` | chunk 4's repeating group — 209 + 105 = 314 |
| `python scripts/cf/35_chunk5_factor.py` | chunk 5's `SetFactor` — **233 not 252**, selection rather than multiplication |
| `python scripts/cf/39_chunk5_crossform.py` | three coverages on one submission, none of them moving |
| `python scripts/cf/04_shared_names.py` | gate point 6 across all **six** chains |
| `python scripts/cf/42_chunk6_zero_cases.py` | chunk 6's six zero cases — incl. Florida's spelling worth zero in Oregon |
| `python scripts/cf/45_chunk6_description_chain.py` | chunk 6's description chain — and the correction to the Florida claim |
| `python scripts/cf/46_chunk6_perform.py` | chunk 6's per-form specifics — the 1.5 coinsurance surcharge, the dead factor, the biconditional |
| `python scripts/cf/47_chunk6_forms.py` | chunk 6's form claims — the narrowed fire gate, Florida's 1.42, construction-blind Broad |
| `python scripts/cf/48_chunk6_crossform.py` | chunk 6's cross-form claims — the blanket branch, and four coverages on one submission |
| `python scripts/cf/51_chunk7_zero_cases.py` | chunk 7's six zero cases — incl. a parent worth $0 carrying a $39 child |
| `python scripts/cf/54_chunk7_borrowed.py` | chunk 7's borrowed rate — eleven values across the boundary, and no base rate |
| `python scripts/cf/55_chunk7_perform.py` | chunk 7's per-form specifics — both apartment dimensions dead, the pin that is live next door |
| `python scripts/cf/56_chunk7_crossform.py` | chunk 7's cross-form claims — the rounding counted, and five coverages on one submission |
| `python scripts/cf/57_chunk7_open_questions.py` | the algorithms page's five open questions — four answered, one left open with a reason |
| `python scripts/cf/61_chunk8_zero_cases.py` | chunk 8's six zero cases — four zeros, four unrelated causes |
| `python scripts/cf/64_chunk8_fork.py` | the fork — two concepts discarded, a third never computed |
| `python scripts/cf/65_chunk8_map.py` | the traced map, point by point |
| `python scripts/cf/66_chunk8_crossform.py` | the map **scored** — 8 of 11 confirmed, 3 corrected — and the cross-coverage LOI leak |
| `python scripts/cf/60_chunk8_raas_probe.py` | the standing engine-vs-ISO check on the Legal Liability form record |
| `python scripts/cf/05_exclusion_records.py` | gate point 7 census, with a per-group chunk 6 section |
| `python scripts/cf/08_hardcoded_literals.py --group CommercialPropertySpecialClass` | gate point 5 for a second datadef group |

**The six sweeps** take a few minutes each and enumerate all 47 jurisdictions:

    python scripts/cf/17_chunk3_enumerate_states.py   # Broad 47/47, Special 47/47
    python scripts/cf/24_chunk4_enumerate_states.py   # Contents 46/47, PR stated
    python scripts/cf/34_chunk5_enumerate_states.py   # Busn Income 44/47, AZ/TX stated
    python scripts/cf/43_chunk6_enumerate_states.py   # Special Class 47/47, AZ/FL/NY at $0
    python scripts/cf/52_chunk7_enumerate_states.py   # SpclClass Busn Income 47/47, the same three inherited
    python scripts/cf/62_chunk8_enumerate_states.py   # Legal Liability 47/47, 43 with a real premium

**All of the above re-run green on 2026-09-22** (C10-21), along with all 16
General Liability suites (`tests/verify_*.py`). **Chunks 6, 7 and 8 are the
only chunks to touch shared code** — `04_shared_names.py` (now reporting eight
chains), `05_exclusion_records.py` (per-group sections) and
`08_hardcoded_literals.py` (a `--group` argument) were extended to take further
datadef groups, and all three still pass for chunks 1–5 unchanged. That was
checked, not assumed.

**Do not re-run these by hand.** `104_chunk10_c10-21_regression.py` runs the
golden cases, the machinery scripts and all 16 GL suites in one command and
checks each golden case against its **documented dollar figure**, not just its
exit code — a script exiting 0 only proves it agreed with itself. It carries
`--selftest`, which plants seven defects and fails if any is reported green.

Everything exits 0. The full set is `scripts/cf/00`–`106`; the General Liability
suites are `tests/verify_*.py` and must stay green — they are the regression net
for every shared-code change.

> **`scripts/cf/` holds two unrelated workstreams that share a number range.**
> The `NN_chunkN_*` files are this engine. The `NN_r1`–`r8`/`m1`/`t1` files
> drive Excel over COM for the separate rater-streamlining project and are
> **not** part of this engine's test surface — RULE #0 applies to them.

**Nothing is committed.** All of `cf_engine/`, `scripts/cf/`, the `docs/CF-*`
files and the `gl_engine/` edits are working-tree only.

---

## Open items — none blocking

| | |
|---|---|
| **Input validation — absent means zero** | Eight inputs now price at zero rather than raising: Arizona's `BasicGroupIReductionCredit`, an unrecognised `ConstructionType`, an absent `BCEG`, a missing `RatingTypeBasicGroupII`, a missing Group II territory, a blank `Deductible` on both chunk 3 forms, and **a construction type that is spelled right but is a rating-type name rather than one of the 25 submission values**. Every one looks like a valid submission and silently produces a cheap policy. A missing `Limit` is the only one that raises |
| **Input validation — a submission can populate a derived field** | **New 2026-09-18, and the mirror image of the above.** Every `IsNull`-guarded rule honours a value that arrived in the payload, so a submitted `SpecialBaseRate=9.999` bypasses the filed table and prices at $11,398. It fails *upward*, and **no ISO comparison catches it** — ISO has the same guards and returns the same number |
| **Building's rate-step rounding is untested at a discriminating rate** | **New 2026-09-18.** Chunk 1 recorded Building's Group I rate step as rounding after every factor, but its golden case (base 0.498) gives 0.239 either way. Class 0074 discriminates: `0.143 x 0.96 x 0.499` is **0.069 rounded once** and 0.068 rounded per factor, and the engine gives 0.069. So the per-factor reading was never actually tested. **Chunks 4 and 5's sweeps both assume per-factor rounding** and match 46 of 47 and 44 of 47 — the residual mismatches may be this. Needs a deliberate tie, the way chunk 1 settled half-up |
| **`SingleResult` with zero hits** | ISO refuses on *some* empty lookups and tolerates others; the distinguishing condition is unknown. Blanket strictness was measured and **disproven** (it breaks VA and VT, which ISO rates). Needs targeted ISO probes, not more corpus reading |
| Per-state gaps | TX's wind/hail shape untraced; DC and IL have no `BCEGFactor` row for their own Group II territory; MT, NY and PR resolve to an empty Group II symbol table |
| Housekeeping | `cf_engine` imports `gl_engine`; the shared core wants a neutral home. **Never bundle that rename with a rating change** |
| GL, optional | whether it adopts `propagate`; whether it wants its own rounding tie (OI-70) |

---

## The three things most worth remembering

1. **The countrywide chain is often the minority behaviour.** 39 of 47
   jurisdictions override `SetBasicGroupIIRate`; 18 of 47 override the Group I
   chain. Re-ask per chunk, never inherit the answer.
2. **Absent means zero, and nothing raises.** This is the recurring failure
   shape in Property, and it is why the zero cases exist in every chunk. Chunk 3
   added the sharpest case: a construction type that is present, spelled right
   and semantically correct, and still prices at zero because it is a rating-type
   name rather than a submission value.
3. **A matching premium proves less than it looks.** Nine cases matched ISO
   before a rounding tie was deliberately constructed, and every one of them was
   consistent with all three rounding modes.
5. **A check that finds SOMETHING needs its denominator tested too.**
   **New 2026-09-22.** Chunk 10's opening census produced a real, believed,
   acted-upon finding — "69 of 924 ISO payloads elect Earthquake" — and it
   was wrong twice over. The 924 silently summed **560 General Liability
   payloads** into a Commercial Property statistic, and the per-file regex
   counted only the first of up to ten electing records. Neither error made
   the finding *absent*; both made it **confidently wrong**, and it survived
   nineteen tasks before C10-20 parsed what the census had only grepped. A
   finding that confirms what you expected gets the least scrutiny and needs
   the most.
4. **A check that finds nothing needs its denominator tested too.** Chunk 3
   found three defects in its own instruments and none in the corpus — gate
   point 6's shared-name check was blind to delegating rules, gate point 7's
   census was blind to theft, and the state sweep's first pass was blind to rule
   overrides. Each returned a clean result that was really an empty search.

---

## Map of the documents

| | |
|---|---|
| [`CF-BUILD-STATUS.html`](CF-BUILD-STATUS.html) | **every chunk, every task, status — one page** |
| [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) | the 15-chunk plan and the eight-point gate |
| [`CF-CHUNK0-BUILD-SPEC.md`](CF-CHUNK0-BUILD-SPEC.md) | the foundation, as built |
| [`CF-CHUNK1-GOLDEN-CASE.md`](CF-CHUNK1-GOLDEN-CASE.md) · [`CF-CHUNK1-GATE.md`](CF-CHUNK1-GATE.md) | chunk 1 |
| [`CF-CHUNK2-GOLDEN-CASE.md`](CF-CHUNK2-GOLDEN-CASE.md) · [`CF-CHUNK2-TASKS.md`](CF-CHUNK2-TASKS.md) · [`CF-CHUNK2-GATE.md`](CF-CHUNK2-GATE.md) | chunk 2 |
| [`CF-CHUNK3-TASKS.md`](CF-CHUNK3-TASKS.md) · [`CF-CHUNK3-GATE.md`](CF-CHUNK3-GATE.md) | chunk 3, closed at 8 of 9 |
| [`CF-CHUNK4-GOLDEN-CASE.md`](CF-CHUNK4-GOLDEN-CASE.md) · [`CF-CHUNK4-TASKS.md`](CF-CHUNK4-TASKS.md) · [`CF-CHUNK4-GATE.md`](CF-CHUNK4-GATE.md) | chunk 4, closed at 8 of 9 |
| [`CF-CHUNK5-GOLDEN-CASE.md`](CF-CHUNK5-GOLDEN-CASE.md) · [`CF-CHUNK5-TASKS.md`](CF-CHUNK5-TASKS.md) · [`CF-CHUNK5-GATE.md`](CF-CHUNK5-GATE.md) | chunk 5, closed at 8 of 9 |
| [`CF-CHUNK8-TASKS.md`](CF-CHUNK8-TASKS.md) · [`CF-CHUNK8-GOLDEN-CASE.md`](CF-CHUNK8-GOLDEN-CASE.md) · [`CF-CHUNK8-GATE.md`](CF-CHUNK8-GATE.md) | **chunk 8, closed at 7 of 9 — all 26 tasks** |
| [`CF-CHUNK7-TASKS.md`](CF-CHUNK7-TASKS.md) · [`CF-CHUNK7-GOLDEN-CASE.md`](CF-CHUNK7-GOLDEN-CASE.md) · [`CF-CHUNK7-GATE.md`](CF-CHUNK7-GATE.md) | **chunk 7, closed at 8 of 9 — all 28 tasks** |
| [`CF-CHUNK6-TASKS.md`](CF-CHUNK6-TASKS.md) · [`CF-CHUNK6-GOLDEN-CASE.md`](CF-CHUNK6-GOLDEN-CASE.md) · [`CF-CHUNK6-DESCRIPTION-CHAIN.md`](CF-CHUNK6-DESCRIPTION-CHAIN.md) · [`CF-CHUNK6-PER-FORM.md`](CF-CHUNK6-PER-FORM.md) · [`CF-CHUNK6-FORMS.md`](CF-CHUNK6-FORMS.md) · [`CF-CHUNK6-CROSSFORM.md`](CF-CHUNK6-CROSSFORM.md) · [`CF-CHUNK6-GATE.md`](CF-CHUNK6-GATE.md) | **chunk 6, closed at 8 of 9 — all 29 tasks** |
| [`CF-CHUNK9-TASKS.md`](CF-CHUNK9-TASKS.md) · [`CF-CHUNK9-GOLDEN-CASE.md`](CF-CHUNK9-GOLDEN-CASE.md) · [`CF-CHUNK9-GATE.md`](CF-CHUNK9-GATE.md) | **chunk 9, closed at 9 of 9 — all 22 tasks; the `ForEach` engine fix is §8 of the golden case** |
| [`CF-CHUNK10-TASKS.md`](CF-CHUNK10-TASKS.md) · [`CF-CHUNK10-GOLDEN-CASE.md`](CF-CHUNK10-GOLDEN-CASE.md) · [`CF-CHUNK10-GATE.md`](CF-CHUNK10-GATE.md) | **chunk 10, closed at 9 of 9 — all 21 tasks** |
| [`CF-ENGINE-FIX-BANDED-LOOKUP.md`](CF-ENGINE-FIX-BANDED-LOOKUP.md) | chunk 10's engine fix — root cause, scope, population check, regression |
| [`CF-CHUNK11-TASKS.md`](CF-CHUNK11-TASKS.md) | **chunk 11, OPEN at 0 of 24 — Leasehold Interest** |
| [`../CF_Algorithm/CF_Required_Submission_Inputs.md`](../CF_Algorithm/CF_Required_Submission_Inputs.md) | every field the ERC rules treat as a true submission input vs. derived, chunks 1–10. **Check this before building any new golden case** |

Saved ISO requests and responses: `results/cf-raas/`.
