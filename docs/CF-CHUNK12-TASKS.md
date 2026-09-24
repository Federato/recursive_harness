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

**Status: CLOSED 2026-09-24, 42 of 42 tasks, gated** ([`CF-CHUNK12-GATE.md`](CF-CHUNK12-GATE.md)). **Groups A to G closed**, all six families gated 9 of 9 and ISO-confirmed live (records: `CF-CHUNK12-GROUP-A.md`, `-DEBRIS-REMOVAL`, `-ORDINANCE-OR-LAW`, `-UTILITY-SERVICES`, `-UNMANNED-AIRCRAFT`, `-GREEN-UPGRADES`, `-DEPENDENT-PROPERTIES`). Regression (C12-41) re-run 2026-09-24: CLEAN for chunks 0–12. OI-108, OI-109 and OI-110 fixed (user-authorized).

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
| C12-01 | **Sequence the six families.** Recommended: Debris Removal (smallest, 3 fixtures, tests the shared-LOI-table risk early), Ordinance or Law (10 fixtures), Utility Services (13 fixtures), Unmanned Aircraft (46-state layer), Green Upgrades (0 fixtures), Dependent Properties (0 fixtures, time-element only) | ✅ | **Done 2026-09-23.** Recommended order confirmed by the user ("do group 1", no change asked). |
| C12-02 | **Read the attach map, don't infer it.** For each family: which core record attaches it, under what gate, and what deletes it (the C10-17 and C11 "record silently deleted" lessons) | ✅ | **Done 2026-09-23** (`124_chunk12_c12-02_attach_map.py`, [`CF-CHUNK12-ATTACH-MAP.md`](CF-CHUNK12-ATTACH-MAP.md)). All 208 groups driven unconditionally by their parent; **nothing deletes any of them**, in any of the 5 parent editions or 46 states. 167 state overrides are pure pins to the declared parent. **Not in the census: 45 state-only Ordinance or Law files** (VA 43: a state broad form with its own A/B/C grid; WV 2: Flood cells), so the family is 100 files, not 55. |
| C12-03 | **Engine readiness by operand type**, not element name: every comparison, arithmetic and lookup operand type across the 208 files | ✅ | **Done 2026-09-23** (`125_chunk12_c12-03_operand_types.py`). 21,037 operators in 1,480 files: 21,031 handled, **6 wrong, one shape: OI-108** (`Sum(BlanketLimit, Break)` loses the blanket drone limit in CA, NC, MO; confirmed on a real submission, 0 vs 99,000). Live: **17 of 17** ISO fixtures carrying a chunk 12 record rate end to end. |
| C12-04 | **The 25 EQ riders.** Confirm each reuses chunk 10's EQ chain, and account for Unmanned Aircraft's 2 empty EQ tables | ✅ | **Done 2026-09-23** (`126_chunk12_c12-04_eq_riders.py`). **34 riders, not 25** (UA's `EQCov` cells). **Premise only partly true**: DR, OL, GU borrow chunk 10's rate (OL 4 with a family EQ factor on top); UA re-runs chunk 10's lookups on its own record; **Utility Services and 4 DP riders price EQ from their own tables**. The 2 empty tables are empty at CW only: **46 of 46 states file rows**. |

**What Group A changed downstream (2026-09-23):** C12-13 now has to prove
Virginia's state broad form and West Virginia's Flood cells; the Utility
Services, Unmanned Aircraft and Dependent Properties golden cases each have
to price their own Earthquake cell (chunk 10 doesn't cover them); and the
Unmanned Aircraft tasks carry OI-108 (include a blanket drone in CA, NC or
MO, and confirm it live).

### B · Debris Removal (6)

What it buys: the smallest family proved end to end, and an early answer
on whether sharing the core LOI tables is safe.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-05 | Golden case, hand-derived before code (**gate 1**) | ✅ | **Done 2026-09-23** (`127_chunk12_golden_case.py`). Chunk 2's OR building + DR limit 60,000: **$49 BGI + $6 BGII = $55**, building unmoved at $261/$32. 21 of 21 figures on the first run; **ISO live identical**. |
| C12-06 | Tables and literals: `DebrisRemovalRate`, `DebrisRemovalMinimumLimit`, and **which LOI table rows it reads, against the core's own use** (**gates 2, 5**) | ✅ | **Done 2026-09-23.** 6 + 1 CW rows, only FL files a row (min 10,000). **LOI keyed on the building's limit**, equal to the building's own factor at band edge, interpolated and higher band. All literals are domain values except one dead one (`Tobacco Sales Warehouses`, a form name). |
| C12-07 | States (FL, NY) and edition basis (**gates 3, 8**) | ✅ | **Done 2026-09-23.** 44 states run the parent unchanged. **FL**: min 10,000 (+ matching message), no Contents DR, sinkhole added to Group II. **NY**: EQ cell drops cyber factors. Rules and tables identical across 4 parents; FL's V01 differs only by missing `IsNull` guards. |
| C12-08 | Zero cases, including the minimum-limit floor (**gate 4**) | ✅ | **Done 2026-09-23.** 9 cases, 9 causes. **Limit < 25,000 gives a negative premium (−$21/−$3) behind a CP 04 15 error; a 'No Coverage' building is still charged.** Both ISO-confirmed. Injection via `IsNull` guards works (except FL). |
| C12-09 | Shared names (it reuses core LOI names) and exclusion records (**gates 6, 7**) | ✅ | **Done 2026-09-23.** 8 shared field names, all on separate records, none misread. Vandalism exclusion flows into DR (BGI $49 → $47); theft exclusion does **not** reach DR Special (flat rate). Both ISO-confirmed. |
| C12-10 | ISO confirmation (3 fixtures, plus a live call) and messages (**gate 9**) | ✅ | **Done 2026-09-23** (`129_chunk12_c12-10_raas.py`). **9 of 12 agree live**, messages identical; 3 ISO refusals are Earthquake lookups in 2023 fixtures (OI-103 data), not DR. Gate 9: 0 unexplained; CP 04 15 logged as M-003. |

### C · Ordinance or Law (6)

What it buys: the largest family, 50 premium files, with its Coverage A /
B / C combinations proved.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-11 | Golden case (**gate 1**): one Coverage A + B + C combination, hand-derived | ✅ | **Done 2026-09-23** (`130`). OR building + 'A and B & C Separate', B 20,000 / C 30,000: **$39+$5 / $55+$7 / $82+$10 = $198**, 15 of 15 first run; **ISO live identical**. |
| C12-12 | Tables and literals: the 11 single-row factor tables, and the 5 `CoverageIndicator` combinations each branch keys on (**gates 2, 5**) | ✅ | **Done 2026-09-23** (`131`). 11 single-row CW tables; MN files its own Cov A rows; FL's post-loss table is empty (falls to CW). All 5 CovType literals = the 5 domain values. |
| C12-13 | States (AK, CA, FL, NY, VA, WV) and editions (**gates 3, 8**) | ✅ | **Done 2026-09-23.** AK min Cov C limit; **CA $0 for public schools**; FL no cyber/post-loss + sinkhole; NY EQ cells; **VA 43-file state broad form**; **WV B&C-only combinations + Flood**. Editions V04 = 20260601. |
| C12-14 | Zero cases across the Cov A / B / C combinations (**gate 4**) | ✅ | **Done 2026-09-23.** 8 cases. **Blank CovType still charges Cov A** (ISO agrees). **Absent B/C limits: ISO $0, ours refuses (OI-109).** |
| C12-15 | Shared names across 55 files and the Business Income attachments, plus exclusions (**gates 6, 7**) | ✅ | **Done 2026-09-23.** 2 shared names, none misread. Vandalism flows into A, B and C; Increased Period of Restoration on BI = $22 + $3. All ISO-confirmed. |
| C12-16 | ISO confirmation (10 fixtures, plus live) and messages (**gate 9**) | ✅ | **Done 2026-09-23** (`132 ordinance`). **7 of 8 engine cases agree** (K7 = OI-109); **every fixture ISO rated agrees** incl. EQ and IPR cells; other refusals are EQ Structure lookups (OI-103). 0 unexplained messages. |

### D · Utility Services (6)

What it buys: the best-evidenced family (13 fixtures), covering both
direct damage and time element.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-17 | Golden case (**gate 1**): one direct-damage and one time-element supply type | ✅ | **Done 2026-09-23** (`133`). Direct damage **$15 + $4**; time element **$9 + $4**. 14 of 14 first run; **ISO live identical**. |
| C12-18 | Tables and literals: 9 tables; the public vs non-public split; the waiting-period factor (**gates 2, 5**) | ✅ | **Done 2026-09-23** (`134`). 9 tables; **the 3 time-element NonPublic tables are all 0** (free by filing). All literals are domain values. |
| C12-19 | States (FL) and edition (**gates 3, 8**) | ✅ | **Done 2026-09-23.** Only FL files rules: TE drops the waiting-period and cyber factors. V03/V04 identical; MO V02 lacks one validation message only. |
| C12-20 | Zero cases (**gate 4**) | ✅ | **Done 2026-09-23.** 7 cases. **No detail limit → whole building limit** (ISO agrees); no waiting period → $0 (agrees); **unfiled waiting period: ISO refuses, ours $0** (OI-103). |
| C12-21 | Shared names across the 5 core attachments, plus exclusions (**gates 6, 7**) | ✅ | **Done 2026-09-23.** The 5 attachments read identical fields. Reads no COL adjustment: vandalism moves the building, not Utility Services. |
| C12-22 | ISO confirmation (13 fixtures, plus live) and messages (**gate 9**) | ✅ | **Done 2026-09-23** (`132 utility`). **10 of 11 engine cases agree**, **all 8 fixtures ISO rated agree**; the rest are OI-103 refusals. 0 unexplained messages. |

### E · Unmanned Aircraft (6)

What it buys: the one family every state changes, proved state by state.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-23 | Golden case (**gate 1**) | ✅ | **Done 2026-09-23** (`137`). Chunk 4 Special Contents + one drone (All Other, 10,000, no deductible): **$187**, 10 of 10 first run; **ISO live identical**. Drones rate on the Special form only. |
| C12-24 | Tables and literals: 36 tables, the 2 empty EQ tables adjudicated, `DroneModificationsCode` (**gates 2, 5**) | ✅ | **Done 2026-09-23** (`138`). 36 tables; the family's own are CW with only FL filing its own; the 2 empty EQ tables are filed by all 46 states. Every golden value is a domain value. |
| C12-25 | **All 46 states, both layers**: what each overrides, and whether it's one pattern or many (**gates 3, 8**) | ✅ | **Done 2026-09-23.** Many patterns, mostly EQ plumbing: 39 states change only EQ sub-limit deductible-tier lookups; AL/TX wind; AR/DC/KS/NY/RI BI drone premium; AK/CA EQ deductible; FL own tables. V02/V03 = the OI-108 shape, fixed. |
| C12-26 | Zero cases (**gate 4**) | ✅ | **Done 2026-09-23.** 9 cases; Basic form $0, no operations $0, high risk $290, **no limit $2 (null skipped, OI-110)**, deductible $156, newly acquired $196, blanket $187, two drones $187 + $93. All ISO-confirmed. |
| C12-27 | Shared names (the EQ chain it borrows), plus exclusions (**gates 6, 7**) | ✅ | **Done 2026-09-23.** The drone adds no message; a Contents windstorm exclusion reaches it (0.315 → $59, ISO agrees). Theft exclusion not engaged by the probe (noted). |
| C12-28 | ISO confirmation (10 fixtures, plus live) and messages (**gate 9**) | ✅ | **Done 2026-09-23** (`132 drone`). **10 of 10 engine cases agree**, every fixture ISO rated agrees (drone + EQ cells); OI-108 live 8 of 8 after the fix. 0 unexplained messages. |

### F · Green Upgrades (6)

What it buys: a family with no ISO fixtures, proved by live call.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-29 | Golden case (**gate 1**) | ✅ | **Done 2026-09-23** (`139`). Green Upgrades 20,000 / 20% / related 10,000: **$30 + $3 = $33**, 12 of 12 first run; **ISO live identical**. |
| C12-30 | Tables and literals: 4 tables (**gates 2, 5**) | ✅ | **Done 2026-09-23** (`140`). 4 single-purpose CW tables, no state rows; all % keys are domain values. |
| C12-31 | States (FL) and edition (**gates 3, 8**) | ✅ | **Done 2026-09-23.** Only FL: sinkhole in Group II, no cyber. V02–V04 identical to 20260601. |
| C12-32 | Zero cases (**gate 4**) | ✅ | **Done 2026-09-23.** **Blank % → factor 1.0 → premium nearly doubles** (ISO agrees); **unfiled % → ISO refuses, ours $56** (OI-103). |
| C12-33 | Shared names across the 5 core attachments, plus exclusions (**gates 6, 7**) | ✅ | **Done 2026-09-23.** Bldg/Contents/Special Class identical; BI versions use the restoration formula (ISO $4 agrees). Vandalism flows ($30 → $28). |
| C12-34 | **Live ISO confirmation (0 fixtures)** and messages (**gate 9**) | ✅ | **Done 2026-09-23** (`132 green`). **No fixtures; 8 of 8 live cases agree**, messages identical. 0 unexplained messages. |

### G · Dependent Properties (6)

What it buys: the time-element family, proved on Business Income and
Special Class Business Income only.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-35 | Golden case on a Business Income risk (**gate 1**) | ✅ | **Done 2026-09-23** (`141`). Broad form on chunk 5's BI, dependent rate 0.2 (submitted), 'not the only source' 0.4: **$80 + $12**, 7 of 7 first run; **ISO live identical**. |
| C12-36 | Tables and literals: 6 tables, the Broad/Limited nature factor; confirm the 4 inert files are inert by reading them (**gates 2, 5**) | ✅ | **Done 2026-09-23** (`142`). 6 tables (FL files 2); the 4 inert files are the International DETAIL records (premium is a submitted ManualPremium on the parent). |
| C12-37 | States (FL) and edition (**gates 3, 8**) | ✅ | **Done 2026-09-23.** Only FL (no secondary-location or cyber factors). V04 = 20260601. |
| C12-38 | Zero cases (**gate 4**) | ✅ | **Done 2026-09-23.** Only source $200 + $30; secondary 1.5 → $120 + $18; **two properties: the highest rate wins**; blank nature → $0. All ISO-confirmed. |
| C12-39 | Shared names across the BI and SC-BI attachments, plus exclusions (**gates 6, 7**) | ✅ | **Done 2026-09-23.** SC-BI mirrors BI (17 of 25 identical; 8 differ by names/gate placement); SC-BI matches ISO live, same figures. Theft probe did not engage (not tested). |
| C12-40 | **Live ISO confirmation (0 fixtures)** and messages (**gate 9**) | ✅ | **Done 2026-09-23** (`132 dependent`). **No fixtures; 12 of 12 live cases agree**, messages identical. |

### H · Close-out (2)

What it buys: chunk 12 folded into the one-command regression, and the
gate filed.

| # | Task | Status | What it needs |
|---|---|---|---|
| C12-41 | Regression: add every chunk 12 golden case and test script to `104_…regression.py`; clean for chunks 0–12 | ✅ | **Done 2026-09-23.** Chunk 12's 6 golden cases (figures fixed before their runs) and 7 gate scripts added to `104_…regression.py`; `--selftest` passes; **full run CLEAN for chunks 0–12** and all GL suites. **Re-run 2026-09-24: CLEAN.** |
| C12-42 | File `CF-CHUNK12-GATE.md`: all six families, nine points each | ✅ | **Done 2026-09-24.** All six families 9 of 9, 0 unexplained messages. Ordinance or Law K7 re-run live after the OI-109 fix: agrees, 8 of 8. |

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
