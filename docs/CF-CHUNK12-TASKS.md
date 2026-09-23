# Property chunk 12: task list and status

**The endorsement families: six coverages sized, then sequenced.** Opened
2026-09-22.

Derived from [`CF-PROPERTY-BUILD-ORDER.md`](CF-PROPERTY-BUILD-ORDER.md) item 12
("sized, not sequenced: take them by family once the core is proved") and
from the opening census
([`123_chunk12_census.py`](../scripts/cf/123_chunk12_census.py)). The family
grouping cross-checks `CF_Algorithm/Coverage_Inventory_And_Tracking.md`
(B3 Ordinance or Law, B5 Utility Services, B8 Debris Removal, D2 Green
Upgrades, D10 Unmanned Aircraft; Dependent Properties sits under B2
time-element).

**Standing rules carried in.** Analysis and gates only: no engine code
without the user's go. "All states" means the **46**; Puerto Rico is
excluded. Live ISO comparisons are sent at **2026-09-17** until OI-105 is
ingested.

**Status: OPEN, 0 of 42 tasks (2026-09-22). The census has run; no task has.**

---

## In plain English first

Chunks 1–11 built the core: what a building, its contents and its income
cost to insure. Chunk 12 is the **add-on endorsements** that sit on top of
that core. They cover things like:
- the extra cost of rebuilding to current building codes (Ordinance or Law);
- loss caused by a supplier's or customer's premises being damaged
  (Dependent Properties);
- loss when the power or water goes off (Utility Services);
- rebuilding "green" (Green Upgrades);
- clearing debris (Debris Removal);
- drones (Unmanned Aircraft).

Each is its own small coverage with its own rules, so each gets its own
golden case and its own small gate.

## What the census found, before any task ran

| Family | Rule files | With a premium | Inert | Rate tables | ISO fixtures (of 364) | States filing (of 46) | Attached from |
|---|---|---|---|---|---|---|---|
| **Ordinance or Law** | **55** (build order's figure confirmed) | 50 | 0 | 11, all single-row factors | 10 | 6: AK CA FL NY VA WV | Structure, Business Income, SC Business Income |
| **Dependent Properties** | 50 | 34 | **4** | 6 | **0** | 1: FL | Business Income, SC Business Income **only** |
| **Utility Services** | 35 | 25 | 0 | 9 | **13** | 1: FL | all 5 core groups |
| **Green Upgrades** | 30 | 25 | 0 | 4 | **0** | 1: FL | all 5 core groups |
| **Debris Removal** | 18 | 15 | 0 | 8, **6 of them the core LOI tables** | 3 | 2: FL NY | Structure, Contents, Special Class |
| **Unmanned Aircraft** | 20 | 10 | 0 | 36, **2 empty** (EQ tables) | 10 | **all 46** | all 5 core groups |

Four things that shape the task list:

1. **Two families have no ISO fixture at all** (Dependent Properties, Green
   Upgrades). Confirmation has to come from a live ISO call, planned at
   task 1, as in chunks 9 and 11.
2. **Unmanned Aircraft is filed by every one of the 46 states.** Its state
   layer is the main work, not a footnote. It also reads **chunk 10's
   Earthquake tables**, two of them empty.
3. **Debris Removal reads the core limit-of-insurance (LOI) tables**
   (`BasicGroupILOIFactorBldg`, 342 rows, and five more). That's the
   shared-table shape that has cost time before (C8-05/C8-16), so it's
   checked early.
4. **25 files across the families are Earthquake riders** already touched
   by chunk 10 (C10-02 found five coverages with their own EQ riders).
   Chunk 10's chain is reused, not re-derived.

**Engine readiness.** Every `rul:` element these 208 files use is already
implemented, and none uses date or `Power` arithmetic. Chunk 11's census
said the same thing and missed an **operand-type** gap (dates in
comparisons). So C12-03 checks operand types, not just element names.

---

## Task groups

Tasks are numbered C12-01–C12-42 and grouped by what they're about. Each
family group carries the nine-point gate in six tasks: golden case,
tables and literals, states and edition, zero cases, shared names and
exclusions, and ISO confirmation with messages. **Gate** marks the task
that closes each point.

### A · Opening: sequence and readiness (4)

What it buys: the order the families are taken in, and the engine risks
known before any golden case.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-01 | **Sequence the six families.** Recommended: Debris Removal (smallest, 3 fixtures, tests the shared-LOI-table risk early), Ordinance or Law (10 fixtures), Utility Services (13 fixtures), Unmanned Aircraft (46-state layer), Green Upgrades (0 fixtures), Dependent Properties (0 fixtures, time-element only) | ⬜ | Confirm or change the order with the user before B starts |
| C12-02 | **Read the attach map, don't infer it.** For each family: which core record attaches it, under what gate, and what deletes it (the C10-17 and C11 "record silently deleted" lessons) | ⬜ | Not started |
| C12-03 | **Engine readiness by operand type**, not element name: every comparison, arithmetic and lookup operand type across the 208 files | ⬜ | Not started |
| C12-04 | **The 25 EQ riders.** Confirm each reuses chunk 10's EQ chain, and account for Unmanned Aircraft's 2 empty EQ tables | ⬜ | Not started |

### B · Debris Removal (6)

What it buys: the smallest family proved end to end, and an early answer
on whether sharing the core LOI tables is safe.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-05 | Golden case, hand-derived before code (**gate 1**) | ⬜ | Not started |
| C12-06 | Tables and literals: `DebrisRemovalRate`, `DebrisRemovalMinimumLimit`, and **which LOI table rows it reads, against the core's own use** (**gates 2, 5**) | ⬜ | Not started |
| C12-07 | States (FL, NY) and edition basis (**gates 3, 8**) | ⬜ | Not started |
| C12-08 | Zero cases, including the minimum-limit floor (**gate 4**) | ⬜ | Not started |
| C12-09 | Shared names (it reuses core LOI names) and exclusion records (**gates 6, 7**) | ⬜ | Not started |
| C12-10 | ISO confirmation (3 fixtures, plus a live call) and messages (**gate 9**) | ⬜ | Not started |

### C · Ordinance or Law (6)

What it buys: the largest family, 50 premium files, with its Coverage A /
B / C combinations proved.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-11 | Golden case (**gate 1**): one Coverage A + B + C combination, hand-derived | ⬜ | Not started |
| C12-12 | Tables and literals: the 11 single-row factor tables, and the 5 `CoverageIndicator` combinations each branch keys on (**gates 2, 5**) | ⬜ | Not started |
| C12-13 | States (AK, CA, FL, NY, VA, WV) and editions (**gates 3, 8**) | ⬜ | Not started |
| C12-14 | Zero cases across the Cov A / B / C combinations (**gate 4**) | ⬜ | Not started |
| C12-15 | Shared names across 55 files and the Business Income attachments, plus exclusions (**gates 6, 7**) | ⬜ | Not started |
| C12-16 | ISO confirmation (10 fixtures, plus live) and messages (**gate 9**) | ⬜ | Not started |

### D · Utility Services (6)

What it buys: the best-evidenced family (13 fixtures), covering both
direct damage and time element.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-17 | Golden case (**gate 1**): one direct-damage and one time-element supply type | ⬜ | Not started |
| C12-18 | Tables and literals: 9 tables; the public vs non-public split; the waiting-period factor (**gates 2, 5**) | ⬜ | Not started |
| C12-19 | States (FL) and edition (**gates 3, 8**) | ⬜ | Not started |
| C12-20 | Zero cases (**gate 4**) | ⬜ | Not started |
| C12-21 | Shared names across the 5 core attachments, plus exclusions (**gates 6, 7**) | ⬜ | Not started |
| C12-22 | ISO confirmation (13 fixtures, plus live) and messages (**gate 9**) | ⬜ | Not started |

### E · Unmanned Aircraft (6)

What it buys: the one family every state changes, proved state by state.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-23 | Golden case (**gate 1**) | ⬜ | Not started |
| C12-24 | Tables and literals: 36 tables, the 2 empty EQ tables adjudicated, `DroneModificationsCode` (**gates 2, 5**) | ⬜ | Not started |
| C12-25 | **All 46 states, both layers**: what each overrides, and whether it's one pattern or many (**gates 3, 8**) | ⬜ | Not started |
| C12-26 | Zero cases (**gate 4**) | ⬜ | Not started |
| C12-27 | Shared names (the EQ chain it borrows), plus exclusions (**gates 6, 7**) | ⬜ | Not started |
| C12-28 | ISO confirmation (10 fixtures, plus live) and messages (**gate 9**) | ⬜ | Not started |

### F · Green Upgrades (6)

What it buys: a family with no ISO fixtures, proved by live call.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-29 | Golden case (**gate 1**) | ⬜ | Not started |
| C12-30 | Tables and literals: 4 tables (**gates 2, 5**) | ⬜ | Not started |
| C12-31 | States (FL) and edition (**gates 3, 8**) | ⬜ | Not started |
| C12-32 | Zero cases (**gate 4**) | ⬜ | Not started |
| C12-33 | Shared names across the 5 core attachments, plus exclusions (**gates 6, 7**) | ⬜ | Not started |
| C12-34 | **Live ISO confirmation (0 fixtures)** and messages (**gate 9**) | ⬜ | Not started |

### G · Dependent Properties (6)

What it buys: the time-element family, proved on Business Income and
Special Class Business Income only.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-35 | Golden case on a Business Income risk (**gate 1**) | ⬜ | Not started |
| C12-36 | Tables and literals: 6 tables, the Broad/Limited nature factor; confirm the 4 inert files are inert by reading them (**gates 2, 5**) | ⬜ | Not started |
| C12-37 | States (FL) and edition (**gates 3, 8**) | ⬜ | Not started |
| C12-38 | Zero cases (**gate 4**) | ⬜ | Not started |
| C12-39 | Shared names across the BI and SC-BI attachments, plus exclusions (**gates 6, 7**) | ⬜ | Not started |
| C12-40 | **Live ISO confirmation (0 fixtures)** and messages (**gate 9**) | ⬜ | Not started |

### H · Close-out (2)

What it buys: chunk 12 folded into the one-command regression, and the
gate filed.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-41 | Regression: add every chunk 12 golden case and test script to `104_…regression.py`; clean for chunks 0–12 | ⬜ | Not started |
| C12-42 | File `CF-CHUNK12-GATE.md`: all six families, nine points each | ⬜ | Not started |

---

## What chunk 12 inherits and must re-ask

* **Chunk 11's operand-type lesson.** "Every node implemented" is not
  engine readiness (C12-03).
* **The silent-deletion shape.** A record kept only under a specific
  `CovType`/`PolicyType` (C11) or attached under an unexpected parent
  (C10-17) (C12-02).
* **Blank is not "none".** Blank `EQCovIndicator` switched an EQ cell on in
  chunk 11. Every family's gate literals get a blank case in its zero-case
  task.
* **The derived-field injection shape.** Check which of each family's
  calculated fields are `IsNull`-guarded.
* **OI-105.** Live ISO at 2026-09-17 only.
* **OI-106.** Form names won't resolve. Don't read a missing form number as
  a missing coverage.
