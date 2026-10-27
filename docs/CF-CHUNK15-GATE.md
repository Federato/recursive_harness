# Property chunk 15: the gate

**The manual-premium endorsements: ten families where the company enters the
premium, in all 46 states.** Filed 2026-09-25. **9 of 9, and all 21 tasks done.**
Task record: [`CF-CHUNK15-TASKS.md`](CF-CHUNK15-TASKS.md).

**In plain English.** For these ten endorsements ISO publishes no rate. The
underwriter types the charge in; ISO's rules apply the policy-wide adjustments
(package discount, multi-premium credit, IRPM) and round to whole dollars. The
chunk proved that each one reaches the right adjustments, rounds the way ISO
does, is switched off where a state switches it off, and changes nothing else
on the policy.

Every figure was worked out by hand before it ran, with inputs chosen so the
competing readings give different dollars, and then checked against ISO live.
**ISO agreed on everything it rated:**
- the golden cases, one per formula variant, and all 23 records on one policy: 27 of 27, every premium on each policy (679);
- 21 zero, exclusion and message cases, messages included;
- **all 46 states**, every premium on each policy (7,836) and every message;
- the downstream check: the total moves by exactly the endorsements' premiums; no terrorism, no statistical codes.

**No engine change was needed.** Two predictions were wrong and are recorded as
such, each explained after ISO answered: Virginia's 2021 edition ($927, not
$1,066) and the first total-difference check (the test's own second Contents
row). A clean re-test (T2) was then predicted first and matched.

**Countrywide premium files built: 251 of 546 (46%)**, up from 228.

## The nine points

| # | Gate point | | Evidence |
|---|---|---|---|
| 1 | A golden case rates end to end | ✅ | `169_chunk15_rc2.py`, one golden case per formula variant on chunk 7's five-coverage Oregon policy, `ManualPremium` 1,090, package discount 0.85, IRPM 1.15, credit 0.9, building credit 0.95: **A** Valuable Papers **$1,013** (rival readings $959, $1,012); **B** Discretionary Payroll **$1,066** ($959, $1,065); **C** Interruption of Computer Operations **$1,065** (step rounding $1,066); **D** Newly Acquired Property **$1,013**; plus all 23 on one policy, 23 of 23. **ISO 27 of 27**, every premium on each policy equal, messages identical. Pinned in the regression |
| 2 | Every table's row count stated | ✅ | **0 rate tables**: the 29 premium files (23 countrywide, 6 VA) read none; their only lookups are form names (`168_`). The policy tables they depend on (`TotalRatingModicationStatCode`, IRPM) are chunk 14's |
| 3 | Every state is enumerated | ✅ | `171_chunk15_rc4.py`: **all 46 states**, all 23 records, their switches and a Cannabis Coverage record: engine **46 of 46** as derived, **ISO 46 of 46** (7,836 premiums, every message). Puerto Rico excluded by standing rule |
| 4 | Every `0` tested against its consuming branch | ✅ | `170_chunk15_rc3.py`, 12 cases: a blank `ManualPremium` reads 0 (not null) → $0; negative → −$1,013 (half-up away from zero); blank package discount / IRPM / credit → 1.0; a policy package discount of **0 → ISO refuses** (OI-103); the building's own credit 0 → $0, priced; switched-off records $0 with a premium entered; submitted `CoverageOnPolicyIndicator` and `Premium` overwritten. ISO 11 of 11 rated |
| 5 | Every hardcoded literal key listed | ✅ | C15-04: `FromConstant="0.0"` on every operand; the switch values "Yes" (4 records) and the Valuable Papers `CovType` string; the $2,500 message limit; the building credit's "Builders Risk" / "Legal Liability" gate |
| 6 | Shared-name traps diffed | ✅ | C15-03: every modifier path resolved on a real tree. IRPM and package discount: the **policy**, 29 of 29 (not the building's own). Multi-premium credit: the parent coverage, the policy for 4 records, and **Valuable Papers reads the building's** (ISO confirmed, $1,013). Business Income's credit is always 1.0. C15-14: `ManualPremium` is written by no rule; `Premium` and `CoverageOnPolicyIndicator` only by the record's own rules, never `IsNull`-guarded |
| 7 | Every exclusion's endorsement record identified | ✅ | C15-12: Cannabis Exclusion is 10 records, with and without the hemp exception, one each per coverage group, dispatched by the parent coverage; outside its own files it appears only in dispatch and messages. With it on all five coverages, **every other premium is identical** (119 compared, engine and ISO) |
| 8 | The edition basis stated | ✅ | Four countrywide parents in force (2026 V01, 2023 V02 / V03 / V04). Every chunk 15 formula is identical in all four **except Discretionary Payroll, which has no premium rule in 2023 V02: Missouri does not rate it** (ISO agrees). VA's 20210501 edition writes the modifiers as `ancestor::` paths, which resolve to the policy; ISO at 2021-06-01 returned $927, the 2020 policy rule overwriting a supplied IRPM with 1.0. That edition cannot be rated whole by our engine (**OI-114**, no in-force package affected) |
| 9 | No unexplained validation message | ✅ | C15-13: 9 countrywide message rules name these records, 8 of them in the parent coverages' files, plus AK, VT, IL and VA variants. Every one is a message, never a refusal. **ISO's message set equals ours on every chunk 15 case**: RC-2, RC-3 and all 46 states |

## What the chunk established, in submission terms

* **The premium is the manual premium × the policy's package discount × a
  multi-premium credit × the policy's IRPM**, each step rounded half-up to whole
  dollars. Business Income records take no credit; Interruption of Computer
  Operations rounds once.
* **An endorsement takes the policy's package discount and IRPM, not the
  building's.** Its multi-premium credit comes from the coverage it hangs on,
  except Valuable Papers (the building's) and four records (the policy's).
* **Five records need an on-switch**, or they price $0 with a premium entered:
  Newly Acquired Location (`Indicator`), Portable Storage
  (`TemporarilyInPortableStorageUnitsIndicator`), Interruption of Computer
  Operations (`InterruptionCompuOpsIndicator`), and Valuable Papers, whose
  switch is **its Contents row's `CovType`**: it needs a row of its own.
* **A Contents row's coverage form is copied from its occupancy**, so set it
  there.
* **States only switch these off:** GA (Cannabis), TX (Newly Acquired Property,
  Y2K), VA (the countrywide Y2K; it rates its own six), MO (Discretionary
  Payroll, by edition), and FL forces four to $0.
* **They feed the policy total and nothing else:** no terrorism, no statistical
  codes.

## Open items left by this chunk

| Item | What | Blocking? |
|---|---|---|
| **OI-103** | Two more cases where ISO refuses and we price: a policy package discount of 0; a special-class description FL does not file | no; engine behaviour decision (chunk 28) |
| **OI-114** (new) | A `rul:Null` test in the 2020 countrywide edition stops our engine | no; no in-force package has one |
| Process gaps found | The census counted messages only in the family's own files (C15-10), and checked a file existed rather than that it priced in each state's edition (C15-18). Both are now in the chunk 15 census notes; the next chunk's census should search every rule file for message rules naming its records, and test `SetPremium` per in-force edition | no |

## Confirmation

* **Regression CLEAN for chunks 0–15**, 2026-09-25: 105 scripts and the General
  Liability suites, 0 failures (`104_chunk10_c10-21_regression.py`, with
  `169_` pinned to $1,013 / $1,066 / $1,065 / $959 and `168_`, `170_`–`172_` added).
* **`157_ --all`**: all 293 stored ISO policies, 14,236 of 14,236 premiums and
  293 of 293 totals equal.
