# P0 — UFG Iowa Commercial Property LCM filing, mapped by hand

**Status: P0 done 2026-10-09. No code.** Gate: every item can be expressed, or the gaps are
listed. All gaps are decided (2026-10-09) and folded into `DEVIATIONS-PLAN.md` v3 as D17–D20:

- **G1 → option A** (group LCMs substituted in the group products; split ISO calls to check).
- **G4 → the PDF wins** whenever the filing's documents disagree: **6/1/2025 new, 10/1/2025 renewal.**
- **G6 → CF first**, then GL.
- G2, G3, G5, G7 → the proposals below, accepted.

Sources (archived in `C:\FederatoProjects\Carriers\UFG\sources\UNFG-134289779\`; see `FILINGS-LOG.md` DEV-001):
- `C:\Users\droma\Downloads\UFG_IA_CP_LCM_Filing_UNFG-134289779.pdf`. This is 16 pages: the
  explanatory memo, the exception page (LCM table) on pp. 2–3, twelve supporting forms on pp. 4–15,
  and the permissible loss ratio on p. 16.
- `C:\Users\droma\Downloads\UFG_IA_CP_LCMs.csv`. This is the same LCM table, typed out, plus a source
  line giving the approval and effective dates.

---

## 1. What the filing says

| | |
|---|---|
| Carrier | UFG Insurance |
| Writing companies | United Fire & Casualty Company (**UFC**, NAIC 13021), Addison Insurance Company (**ADD**, NAIC 10324) |
| Line / state | Commercial Property (CF), Iowa |
| SERFF | UNFG-134289779. Companion filings: UNFG-134204780 (CPP plan) and UNFG-134266109 (forms) |
| What it does | Adopts ISO's current loss costs with company LCMs. Only LCMs: no factor overrides, no minimum premium, no terrorism item. |
| Keyed by | Coverage group (Group I specific, Group I class, Group II, Broad, Special, Earthquake) × class group (A, B, all other) |

The LCMs (exception page, pp. 2–3; the supporting forms on pp. 4–15 agree with every value):

| Company | Class group | Grp I specific* | Grp I class | Group II | Broad | Special | Earthquake |
|---|---|---|---|---|---|---|---|
| UFC | A | 1.067 | 1.067 | 2.448 | 2.448 | 2.448 | 2.11 |
| UFC | B | 0.875 | 0.875 | 2.062 | 2.062 | 2.062 | 2.11 |
| UFC | All other | 1.511 | 1.511 | 3.280 | 3.280 | 3.280 | 2.11 |
| ADD | A | 1.279 | 1.279 | 2.938 | 2.938 | 2.938 | 2.64 |
| ADD | B | 1.051 | 1.051 | 2.474 | 2.474 | 2.474 | 2.64 |
| ADD | All other | 1.813 | 1.813 | 3.934 | 3.934 | 3.934 | 2.64 |

\* "including special class rates"

**Class group A:** 0077-0079, 0196-0198, 0300, 0311-0313, 0321-0323, 0331-0333, 0431, 0433-0434,
0512, 0520, 0532, 0545, 0550, 0561-0563, 0565-0567, 0581-0582, 0742-0747, 0755-0756, 0831-0832,
0844, 0922, 0931-0933, 1052, 1150, 1212-1213, 1220, 1230, 1751-1752, 2000, 2059, 2200, 2250, 2350,
2400, 2459, 2600, 3009, 3409, 4450, 4809, 5000, 5050, 5500, 5759, 6009, 6810.
**Class group B:** 0511, 0542, 0701-0702, 0757, 0851-0852, 0900, 0921, 0923, 1051, 1070, 6850, 6900.
**Class group C:** all other classes.

Supporting data that isn't rated (kept as metadata):
- Expected loss ratio: 0.543 for Group I (fire) and 0.477 for Group II (EC).
- Rate level change: +20.9% for UFC and +1.0% for ADD.
- Expense provisions, from p. 16.

---

## 2. Hand-authored form (§3a)

`carrier.json` (UFG). Both companies use the same class groups, so they sit at carrier level
(see G7):

```json
{ "carrier": "UFG", "approval": {"signoffs": 1},
  "class_groups": {
    "UFG-A@v1": ["0077-0079","0196-0198","0300","0311-0313","0321-0323","0331-0333","0431","0433-0434",
                 "0512","0520","0532","0545","0550","0561-0563","0565-0567","0581-0582","0742-0747",
                 "0755-0756","0831-0832","0844","0922","0931-0933","1052","1150","1212-1213","1220",
                 "1230","1751-1752","2000","2059","2200","2250","2350","2400","2459","2600","3009",
                 "3409","4450","4809","5000","5050","5500","5759","6009","6810"],
    "UFG-B@v1": ["0511","0542","0701-0702","0757","0851-0852","0900","0921","0923","1051","1070",
                 "6850","6900"] } }
```

`UFC/authored/IA-CF-UNFG-134289779.v1.json`. Class group C ("all other") is the unscoped row, so it
needs no list:

```json
{ "company": "UFC", "line": "CF", "juris": ["IA"], "version": 1, "status": "approved",
  "serff": "UNFG-134289779", "approved": "2025-05-06",
  "new_eff": "2025-06-01", "renewal_eff": "2025-10-01",
  "rows": [
    {"target": "LCM:GroupI",     "scope": {},                         "value": 1.511, "mode": "replace", "cite": "Exc p3; OKLCF p6"},
    {"target": "LCM:GroupI",     "scope": {"class_group": "UFG-A@v1"}, "value": 1.067, "mode": "replace", "cite": "Exc p2; OKLCF p4"},
    {"target": "LCM:GroupI",     "scope": {"class_group": "UFG-B@v1"}, "value": 0.875, "mode": "replace", "cite": "Exc p3; OKLCF p5"},
    {"target": "LCM:GroupII",    "scope": {},                         "value": 3.280, "mode": "replace", "cite": "Exc p3; OKLCF p9"},
    {"target": "LCM:GroupII",    "scope": {"class_group": "UFG-A@v1"}, "value": 2.448, "mode": "replace", "cite": "Exc p2; OKLCF p7"},
    {"target": "LCM:GroupII",    "scope": {"class_group": "UFG-B@v1"}, "value": 2.062, "mode": "replace", "cite": "Exc p3; OKLCF p8"},
    {"target": "LCM:Broad",      "scope": {},                         "value": 3.280, "mode": "replace", "cite": "Exc p3"},
    {"target": "LCM:Broad",      "scope": {"class_group": "UFG-A@v1"}, "value": 2.448, "mode": "replace", "cite": "Exc p2"},
    {"target": "LCM:Broad",      "scope": {"class_group": "UFG-B@v1"}, "value": 2.062, "mode": "replace", "cite": "Exc p3"},
    {"target": "LCM:Special",    "scope": {},                         "value": 3.280, "mode": "replace", "cite": "Exc p3"},
    {"target": "LCM:Special",    "scope": {"class_group": "UFG-A@v1"}, "value": 2.448, "mode": "replace", "cite": "Exc p2"},
    {"target": "LCM:Special",    "scope": {"class_group": "UFG-B@v1"}, "value": 2.062, "mode": "replace", "cite": "Exc p3"},
    {"target": "LCM:Earthquake", "scope": {},                         "value": 2.11,  "mode": "replace", "cite": "Exc p2-3"} ],
  "meta": {"elr": {"GroupI": 0.543, "GroupII": 0.477}, "rate_level_change": 0.209} }
```

`ADD/authored/IA-CF-UNFG-134289779.v1.json` has the same 13 rows with ADD's values: 1.813 / 1.279 /
1.051, 3.934 / 2.938 / 2.474 (×3 for Group II, Broad and Special), and 2.64. Its rate level change
is 0.010.

`LCM:GroupI` covers both the specific-rated and class-rated Group I columns, because they are equal
in this filing (see G5).

---

## 3. Item by item

| Filing item | Maps to | Expressible? |
|---|---|---|
| Two writing companies in one SERFF filing | One authored file per company, sharing the SERFF id | Yes (G3) |
| Class groups A and B as code ranges | Carrier-level `class_groups` (D14 company lists), expanded at compile (M5) | Yes, with ranges (G7) |
| Class group C "all other" | Unscoped row, the least specific | Yes |
| Group I specific / class LCMs | `LCM:GroupI` | Yes here (G5) |
| Group II, Broad, Special LCMs | `LCM:GroupII`, `LCM:Broad`, `LCM:Special` | **Authored yes; rated no (G1)** |
| Earthquake LCM, one value per company | `LCM:Earthquake`, unscoped | **Authored yes; rated no (G1)** |
| Approval 5/6/2025 | `approved` + workflow log sign-off | Yes |
| New / renewal effective dates | `new_eff` / `renewal_eff` (D4) | Yes, once G4 is settled |
| ELR, expense provisions, rate level change | `meta` (not rated) | Yes |
| Minimum premium, terrorism | Not in this filing. O3 stands. | n/a |
| "Exceptions are final rates and minimum premiums, no LCM applies, unless indicated otherwise" (p. 3 footnote) | Only the LCM table is an exception here, so nothing else is affected | n/a |

---

## 4. Gaps

### G1 — ISO's CF rules carry ONE LCM; UFG files a different LCM for each coverage group  ⚠ blocks the plan

**What ISO does.** In ISO's CF content, `LossCostMultiplier` is a single field on each record:
Structure, Personal Property, BI, Special Class, and so on. `SetLossCostMultiplier` copies it down
from the location and then the policy. The state table `LossCostMultiplier` holds one factor per
state. The same field multiplies every group's base rate:
- `BasicGroupIBaseRate`
- `SpecificGroupIRate`
- `BasicGroupIIBaseRate` and `LowestBasicGroupIIBaseRate`
- `BroadBaseRate`
- `SpecialBaseRate`
- `EQBaseRate`
- the SubStd condition rates

(CW `CommercialPropertyStructureRules`, `SetLossCostMultiplier` and the Product steps. Iowa
20250401 and 20260601 do the same for Group II.)

**Why it matters.** Plan §4b writes one LCM onto each coverage record, but UFG needs three per
building: 1.067 (Group I), 2.448 (Group II, Broad, Special) and 2.11 (EQ). No single value in that
field reproduces UFG's rating. So the plan's "ISO's service can check our LCMs" (D11) doesn't hold
for this filing as written.

**Options:**
- **A — Group LCMs applied inside the engine (recommended).** Add a deviation target kind,
  `LCM:<group>`, compiled into a company LCM table keyed by group and class. In each of ISO's group
  products (`<Group>BaseRate × LossCostMultiplier`), the engine substitutes the company's group LCM
  for the field value. ISO's rules, rounding and order stay the same; only the value that one product
  reads changes. The trace records the substitution. The record's `LossCostMultiplier` field stays as
  the Group I value (see G2).
- **B — Multiply the group base-rate lookups (CompanyBook `multiply`) and leave LCM at 1.**
  Simpler, but wrong in places. Base rates feed other steps (Lowest Group II, BI, SubStd), so those
  would pick up the factor in the wrong order. The stat code would also say 1.00. Not recommended.
- **Checking against ISO (goes with A).** ISO applies one LCM to every group, so make one ISO call
  per distinct LCM value: for UFC class A, that's LCM = 1.067, 2.448 and 2.11. Compare each group's
  rate with the call whose LCM matches. That restores D11 by ISO's own arithmetic. It costs one call
  per distinct LCM per case (3 here), so T5's budget rises from about 60 to about 180, or T5 is
  narrowed.

**If A is chosen, the plan changes:**
- **§4b:** the LCM step writes one LCM value (Group I) and also loads the group LCMs for the
  substitution.
- **§4c:** a new "group LCM" lookup, separate from the CompanyBook.
- **§3c:** `changedPaths` lists each group rate.
- **T5:** becomes the split check.
- **T4:** must allow the group rate paths.

### G2 — LCM stat code with three LCMs
ISO derives `LossCostMultiplierStatCode` from the one LCM (rounded × 100). With group LCMs, the
filing doesn't say which LCM the stat code should report. **Proposal:** report the Group I value,
matching what the record's LCM field holds under option A. This should be confirmed with the
carrier's stat reporting.

### G3 — One filing, two companies
§3a's authored file has a single `company`. **Proposal: no format change.** Write one authored file
per company sharing the SERFF id, and have `show` and `diff` group them by SERFF id.

### G4 — Effective dates disagree  ❓ needs you
- **PDF** (memo p. 1 and exception page footers): **6/1/2025 new, 10/1/2025 renewal.**
- **CSV source line:** **7/15/2025 new, 12/1/2025 renewal**, approved 5/6/2025.

SERFF dispositions often move dates, but the PDF has no disposition page. **Decided: the PDF wins** (6/1/2025 new, 10/1/2025 renewal). The CSV's dates are
not used. Both pairs fall within ISO's IA CF edition `CF IA 20250401 V01`, so the choice of edition doesn't change. Only
the switch-over dates do (T7).

### G5 — Group I specific vs class rated
The filing has separate columns for these. They are equal here, so one row covers both. A future
filing could differ, so D3's scope needs a **rating basis** dimension (specific or class), with
special class rates under "specific", per the footnote. Not needed for this filing, but it goes in
the format so P1 doesn't have to change it later.

### G6 — Line order
The plan builds GL first and CF second, but the P0 filing is CF, and the P2 gate says "the P0
filing rates". **Proposal:** build the engine on CF first (P2), then GL. Or keep GL first and move
the P0-filing part of the P2 gate to the CF step.

### G7 — Where class groups and ranges live
The plan puts class groups in `company.json`. Here two companies share them, so allow them at
carrier level, with a company able to override them. Codes are written as ranges
(`0077-0079`). Compile expands them using the ISO edition's class list, and `validate` refuses any
range that holds a code the edition doesn't have.

### Not gaps, just noted
- The supporting forms on pp. 7–9 and 13–15 are captioned "Group I", but they carry the Group II
  (EC) LCMs and ELR 0.477. This is a caption error in the filing; the exception page is authoritative.
- LCMs run from 0.875 to 3.934. Group II LCMs of 2 to 4 are normal for this carrier, so the `validate`
  LCM band has to be set per group, not as one band.
