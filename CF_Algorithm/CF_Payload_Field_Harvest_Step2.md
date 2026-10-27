# Payload generator — Step 2: the field set ISO actually accepts

**Run 2026-09-22.** Script: `scripts/cf/85_payload_step2_field_harvest.py`.
Pure analysis over files already in the repo — no workbook access, no requests sent.

**Artefacts:** `CF_Payload_Field_Matrix.csv` (508 rows) · `CF_Payload_Field_Gaps.csv`

---

## 1. What was harvested

| Corpus | Payloads | Distinct (record, field) pairs | Why it counts as evidence |
|---|---|---|---|
| `results/cf-raas/*request*.json` | **44** | 83 | Live ISO accepted every one of them |
| ISO's own `STC/` folders | **364** | 483 | ISO authored them; they are its regression set |

**58 record types** appear across the two corpora. The rater emits **7** of them; the other ~48 are
endorsement records with no counterpart in the workbook. Everything below is scoped to the 7 plus the
two envelope levels — otherwise "fields with no rater source" would just be measuring the whole CF line.

### Field counts per record type, ours vs ISO's

| Record type | Our payloads | ISO's payloads |
|---|---|---|
| `CommercialPropertyStructure` | 20 | **107** |
| `CommercialPropertySpecialClass` | 15 | 49 |
| `CommercialPropertyPersonalProperty` | 7 | 41 |
| `CommercialPropertyBusinessIncome` | 9 | 41 |
| `CommercialPropertyLocation` | 6 | 26 |
| `CommercialProperty` (policy) | 5 | 25 |
| `CommercialPropertySpecialClassBusnIncome` | 9 | 20 |
| `CommercialPropertyOccupClass` | 3 | 12 |

**The finding in that table: our payloads are minimal, ISO's are rich.** We send 20 fields on a
Structure; ISO sends up to 107. Both rate. That is strong evidence most fields are genuinely optional
— but it is *evidence*, not proof (see §4).

---

## 2. The join against the rater's 127 inputs

| | Count |
|---|---|
| Rater inputs matched to an ISO field | **63** |
| Rater inputs needing a hand verdict | **64** |
| ISO core fields with no rater source → `Defaults` sheet candidates | **165** |

63 matched only after a hand-built alias map (`ALIASES` in the script) — the naive name match got 28.
Rater labels are prose (`Building Class Code:`), ISO fields are camelCase (`ClassCode`).

### The 64 unmatched, classified

Not a flat backlog — they fall into six families, and only the last needs real thought.

| Family | Count | Verdict |
|---|---|---|
| **Workbook bookkeeping** — `Location #`, `Building #`, `Item ID`, `Item #`, `Building ID Found?`, `Linked Building Item ID`, `Burglary System Range`, `Selected Burglary System Factor`, the two decoded `Description` rows | 12 | **Not payload fields.** Become the export sheet's ID/ParentID columns, or are dropped. No mapping needed |
| **Exclusions** — Windstorm/Hail, Vandalism, Theft (on all three tabs), Cyber, Sprinkler Leakage | 11 | **Structural, see §3** |
| **Cyber endorsement detail** — `With Ensuing Cause of Loss Exceptions`, `Property Damage Sublimit`, `Aggregate Limit` | 3 | Fields *on* the Cyber record, not on the policy. Map once §3 is settled |
| **Sub-Standard Conditions A–E** | 5 | Real ISO fields (`SubStdConditionA`…`E`, decoded in BUILD-LOG Entry 24). Alias-map fix only |
| **Specific/Tentative rates** (Building, Contents, BI) | 3 | Map to `SpecificGroupIRate` and siblings — present in the Alabama sample payload |
| **Genuine inputs still needing a verdict** — `District`, `Roof Surfacing`, `Yard Property Description`, `Contents Group`, `Construction Symbol`, `Percentage (Type 1/2)`, `Extra Expense Loss Payment Schedule`, `Multi Residential Property Special Credits`, `Location of Heating Plant`, `Per Location Deductible`, `Watchman`/`Burglary Alarm`, `Special Agreed Value`, `Deductible By Location`, `Item Description`, … | **30** | The actual remaining work of Step 3 |

---

## 3. The structural finding — exclusions are records, not fields

**The rater models every exclusion as a Yes/No input. ISO models it as the presence of an endorsement
record.** In the Alabama payload, electing the Cyber exclusion is not `CyberExclusion: "Yes"` — it is:

```json
"CommercialPropertyCyberIncidentExclusion": [{}]
```

An empty object whose *existence* is the election. This is why 11 of the 64 didn't match on name and
never could: there is no scalar field to match.

**Consequences for the design:**

1. The `Payload Export` sheet needs a **records block** — a list of endorsement records to emit —
   not only a fields block. This was not in the Step 1 design sketch.
2. It confirms, from the payload side, what `Rater_Simplifications_Backlog.md` already records as
   **S-1 / S-2 / S-3**: ISO files a *separate* exclusion record per datadef group, and the rater reuses
   one Yes/No input across groups. A generator reading one input cannot emit two differing records.
   **So the backlog entries are not just a rating simplification — they are a payload-fidelity limit.**
3. It lines up with the harness's own gate point 7 ("every exclusion's endorsement record identified
   per datadef group"), which is passed on all eight closed chunks. The mapping can be lifted from that
   work rather than re-derived.

---

## 4. The caveat, carried not papered over

**Observed frequency is not requiredness.** ISO marks every field in the CF DataDef `nillable="yes"`
with no `minOccurs`, so the schema asserts nothing about what must be sent. A field appearing in 44 of
44 payloads may still be optional; one appearing in 3 may be mandatory on a path neither corpus
exercises. `CF_Payload_Field_Matrix.csv` reports counts and percentages for both corpora and labels
each row `both` / `ISO only` / `ours only` — that is the evidence, and it should be read as evidence.

The safe reading: **`ISO only` fields are safe to omit** (we already rate without them), and
**`ours only` fields are safe to send** (ISO accepted them). The `both` rows are the confident core.

---

## 5. Composition risk — now measured precisely

Step 2's other job was to size the one risk that survived the Step 2 re-scope.

| | |
|---|---|
| Coverage blocks the rater emits | **7** |
| Widest single payload ISO has ever accepted | **4** |

The widest accepted combination is `Location` + `OccupClass` + `PersonalProperty` + `Structure`.
**`BusinessIncome`, `SpecialClass` and `SpecialClassBusnIncome` have never co-occurred with that set**
in either corpus — each is proven only alongside `Structure` alone, or alongside each other.

So the risk is real and now precisely bounded: every block is individually ISO-proven; **the 7-block
combination the rater would emit has never been sent by anyone.** Step 6 must open with exactly that
payload, before any premium comparison is attempted.

---

## 6. What Step 3 inherits

1. Adjudicate the **30** genuine unmapped inputs (§2) — one verdict each.
2. Design the export sheet's **records block** (§3), lifting the per-datadef-group exclusion mapping
   from the harness's gate point 7 rather than re-deriving it.
3. Cut the **165** `Defaults` candidates down using §4's safe reading — `ISO only` fields can be
   omitted, which should remove most of them. The `Defaults` sheet is likely far smaller than 165.
4. Apply the alias map and the seven format conversions from Step 1 (`0.8` → `"80%"`, zip float →
   string, and the rest).

*Step 2 of 6 complete. Nothing built, no code beyond the harvest script, no workbook access.*
