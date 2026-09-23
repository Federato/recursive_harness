# Engine fix — banded lookups with two range keys (Commercial Property)

User-authorized engine fix, 2026-09-22. Scoped, verified and written up to the
same standard as C9-01's authorized interpreter fix
(`CF-CHUNK9-GOLDEN-CASE.md` §8).

## 1 · In plain English

Some Commercial Property rate tables — the Earthquake sub-limit +
flat-dollar-deductible tables, the Flood "rate modification" tables, and one
Massachusetts heating-oil-tank table — pick a row two different ways at once:
one number (like "what percent of the building is sub-limited") is used to
blend smoothly between two rows, and a second, separate number (like "how
much is the whole property worth") just has to fall in some bracket, no
blending needed. The engine's table-lookup code only knew how to handle one
"blend" number per table. When it saw a table asking for two, it assumed that
was a filing mistake it didn't understand and refused to run rather than
guess. That refusal was correct caution, but it meant a real, filed ISO
rating path — Earthquake sub-limit coverage with a flat-dollar deductible —
could never be rated at all.

The fix teaches the lookup code the difference between the ONE number that
blends and any OTHER numbers that just have to fall in a bracket. It reads
that distinction directly off ISO's own table declaration (which number is
marked as the blending one) rather than guessing from position, so a table
that blends on nothing at all (the Massachusetts table) and a table that
blends on exactly one of its two bracket numbers (every other table found)
are both handled correctly, and a table that blends on more than one number,
or names a blending number that isn't one of its own brackets, still refuses
instead of guessing.

## 2 · Root cause, technical

`gl_engine/interp/interpreter.py::_lookup_banded` refused any `RateTableDef`
whose `key_ranges` had a length other than 1:

```python
rng = defn.key_ranges[0]
if len(defn.key_ranges) != 1:
    raise InterpretError(...)
```

Measured against the General Liability corpus alone
(`scripts/erc/46_banded_lookups.py`), that was the whole population — 11
table names, all with exactly one `rt:Range` key column. Commercial Property
was never scanned by that script, because it scans by a GL-specific package
walk.

Chunk 10's C10-19 task (`scripts/cf/103_chunk10_c10-19_sublimit_flatdeductible.py`)
found the gap by *running* a real Earthquake sub-limit submission, not by
reading the rule XML: `LookupEQSubLimit2500FlatDeductibleFactor` raised
`InterpretError` because its table declares TWO `rt:Range` key columns —
`EQSubLimitPct_From/ToLessThan` and `TotalPropertyValue_From/ToLessThan`.

A direct scan of the whole CF corpus (26,319 `RateTableDef.xml` files) finds
this is not a one-table quirk. Exactly **28 table names** declare 2 key
ranges (none declare more than 2), and every one of the 28 shares one shape —
some equality key columns, then two ranges:

| Family | Count | Status | Consumer |
|---|---|---|---|
| `EQSubLimit<N>FlatDeductibleFactor` | 13 | live | `CommercialPropertyStructureRules.Rule.xml`, `SetEQDeductibleFactor` |
| `PropertyRateModificationFactors1`-`7` (plural) | 7 | live | `CommercialPropertyFloodCoverageEndorsementRules.Rule.xml` |
| `HeatingOilTankServingResidentialPropertiesIndicator` | 1 | live | a Massachusetts structure rule |
| `PropertyRateModificationFactor1`-`7` (singular, unnumbered-plural) | 7 | **dead** | zero rule references corpus-wide (confirmed by direct grep) |

Of the 20 live tables, 19 declare exactly one of their two ranges with a
`ValueCols/rt:Range@RangeKeyCol` attribute naming it as the interpolation
dimension — the same attribute the single-range GL tables already carry and
the same attribute the old code never actually checked (it didn't need to,
there was only one range to choose from). The 20th, `HeatingOilTank...`,
declares a plain `ValueCol` and no `RangeKeyCol` at all: neither of its two
ranges interpolates anything, both are pure containment filters, and its
output is a flat lookup exactly like an ordinary equality match except two of
its keys are brackets instead of exact values.

## 3 · The fix

`_lookup_banded` no longer special-cases "exactly one range." Instead:

* Every `Range` key column, however many there are, is walked positionally
  (per ISO's own filed order, `defn.key_items` — unchanged from before,
  including the "band is not necessarily the last key" fix already in
  place) and treated as a `[lo, hi)`/`(lo, hi]` containment filter, using its
  own `RangeType` for inclusivity, exactly like an equality key column except
  the match is a bracket instead of an exact value. This narrows candidate
  rows (`hits`) and nothing else.
* Separately, when the requested output column (`col`) matches a declared
  `value_range`, that value range's own `RangeKeyCol` attribute says BY NAME
  which of the table's key ranges is the interpolation dimension. The code
  looks up that name in the per-row bracket bindings collected during
  filtering and interpolates `Linear` along it, exactly as before. If the
  named range isn't one of the table's own key ranges, or there are two
  value ranges naming different ranges (never observed, but the check exists
  rather than assuming the population never changes), it raises
  `InterpretError` rather than guessing.
* A table with zero interpolated ranges (`HeatingOilTank...`) simply never
  enters the interpolation branch — every range narrowed `hits`, the output
  column is a plain `ValueCol`, and the existing plain-column read path
  fires unchanged.

The single-range GL case is a special case of the same code now — one range,
walked positionally, one bracket filter, one (optional) interpolation — not
a separately maintained branch. Nothing about `key_items` traversal order,
equality-column matching, `SingleResult`/`FirstResult` uniqueness handling,
or the two `RangeType` boundary conventions changed.

`gl_engine/erc/tables.py` (the `Range`/`TableDef` dataclasses that parse
`RateTableDef.xml`) was **not** touched — `key_ranges`, `key_items`, and
`value_ranges[].range_key_col` already carried everything the fix needed.

## 4 · Verified

**Narrow, hand-derived (C10-19's own case, now closed):**
`scripts/cf/103_chunk10_c10-19_sublimit_flatdeductible.py`'s sub-limit
submission (OR, Basic Group I, EQClass A1, `EQSubLimitPct`=50 derived from a
$50,000 sub-limit against $100,000 `FullBldgValue`, `EQDeductible`="2,500")
now runs to completion. Hand-derived from
`EQSubLimit2500FlatDeductibleFactor.RateTable.csv` (CW, `20260601` package):
row `EQSubLimitPct [50,55)` (contains 50, `FromInclusiveToExclusive`) ×
`TotalPropertyValue [0,100001)` (contains 100,000) → `Factor_From=1.376`,
`Factor_ToLessThan=1.263`; interpolation position `(50-50)/(55-50)=0` →
`EQDeductibleFactor = 1.376`. Chain: `FinalEQRate = round(0.009 × 0.95 ×
1.376, 3) = 0.012`; the sub-limit endorsement's own `Premium` reads THIS
RECORD'S OWN `Limit` ($50,000, not the structure's $100,000) →
`Premium = round(0.012 × 50000/100, 0) = 6`. The engine returns
`EQDeductibleFactor=1.376` and `Premium=6` — an exact match.

**Structural, the other two live families:** direct standalone calls to
`Interpreter.lookup` (not through a full submission — no rule exercises
`PropertyRateModificationFactors1` or `HeatingOilTankServingResidential
PropertiesIndicator` from a currently-built CF chunk's own golden case) —

* `HeatingOilTankServingResidentialPropertiesIndicator["Code"]` with keys
  `["MA", 1, 0]` → engine returns `1`, matching the filed row `NumberOfTanks
  (-inf,1] × AdditionalBuildings (-inf,0] → Code=1` by direct CSV read.
* `PropertyRateModificationFactors1["Factor"]` with keys `["CW","500",80,
  50000]` → engine returns `1.00`, matching the filed row
  `InsuranceToValueLevelPercentage [80,90)` (interpolation position 0) ×
  `TotalPropertyValue [0,50001)` → `Factor_From=1, Factor_ToLessThan=0.95`
  by direct CSV read.

Neither raises; both match a hand derivation against the filed CSV, the same
discipline as the narrow case, just without a full submission built around
them (Flood and the MA heating-oil-tank endorsement are outside chunk 10's
own build scope).

**Population check, independent of the task's own background claim:** a
direct scan of all 26,319 `RateTableDef.xml` files under the CF corpus root
finds exactly 28 table names with ≥2 key ranges (none with more than 2),
matching the background exactly. A direct grep of every `.Rule.xml` for
`MatrixDef="<name>Def"` / `MatrixFromConstant="<name>"` confirms the singular
`PropertyRateModificationFactor1`-`7` family has zero references anywhere,
while the plural family and the heating-oil-tank table have live references
(24 and 10 respectively) — the dead family was left untouched, as instructed.

## 5 · Full regression

**All 16 `tests/verify_*.py` General Liability suites: 16/16 exit 0.**
No GL table in either corpus declares a second key range (confirmed by the
independent scan in §4), so this was never expected to move GL, and it
didn't.

**All 120 `scripts/cf/*.py` Commercial Property chunk scripts: 107 exit 0,
13 non-zero — every one of the 13 pre-existing and unrelated to this fix**,
same discipline as C9-01's own regression note (`07_diagnose_message` and
`63_chunk8_raas` were already the two known exceptions there):

* `07_diagnose_message.py` (exit 2) — requires CLI arguments (`--message` or
  `--rule`); an argparse usage error on a bare invocation, not a failure.
* `63_chunk8_raas.py` (exit 1) — its own documented disagreement-report
  script; it prints a KNOWN engine/ISO divergence (`InterpretError` where
  ISO rates Builders Risk + reporting form, OI-99) and exits non-zero by
  design to flag it. Unrelated to banded lookups.
* `100_r6_edition_basis.py` (exit 1) — the standing RULE #0 guard aborted:
  `"ABORT: 1 Excel process(es) running"`. A stray `Excel.exe` process was
  present in this environment; the script's own safety check refused to run
  rather than risk it. `CFRater1.01.xlsb` was never touched — confirmed by
  reading the script, which targets `CFRater1.02.xlsb` only and asserts
  `FORBIDDEN = "cfrater1.01.xlsb"` before ever calling COM.
* `86_r1_generate_names.py` (exit 1) — `KeyError: 'Policy Inputs'`, a
  pre-existing bug in a sheet-label lookup, nothing to do with rate tables.
* `88_r1_verify_names.py`, `89_r4_survey.py`, `90_r4_apply.py`,
  `91_r4_bi_disguised_constants.py`, `93_m1_apply_specialclass.py`,
  `94_t1_fix_total_premium.py`, `96_r2_rename_sheets.py`,
  `97_r2_fix_tab_order.py`, `98_r3_guard_columns.py` (exit 1 each) — all 9
  fail identically, at `wb.Names(p).RefersToRange.Value`, with the same
  `pywintypes.com_error`. Each of these opens `CFRater1.02.xlsb` in its OWN
  isolated `win32com.client.DispatchEx("Excel.Application")` instance (never
  `GetObject`, never the user's live session) and each asserts
  `FORBIDDEN = "cfrater1.01.xlsb"` before doing anything — read directly off
  each script to confirm neither RULE #0 nor the "never attach to a live
  instance" rule was at risk. The COM failure itself is consistent with the
  same stray Excel process `100_r6_edition_basis.py`'s own guard caught;
  none of the 9 scripts' failing line has anything to do with
  `_lookup_banded`, table lookups, or the interpreter at all.

**Every documented dollar figure this project tracks was cross-checked, not
just exit codes** — `85_chunk10_golden_case.py`'s own printed premiums,
`101_chunk10_c10-17_non_owned_trailers.py`, `102_chunk10_c10-18_special
_class_census.py`, and every earlier chunk's own golden-case script all
re-ran to their previously-recorded figures; nothing moved except
`103_chunk10_c10-19_sublimit_flatdeductible.py`'s own sub-limit case, which
moved from a confirmed `InterpretError` to a confirmed `$6` match, exactly
as intended.

**Independent verification the fix's scope is exactly what it claims:** a
direct scan of all 26,319 `RateTableDef.xml` files under the CF corpus root
found exactly 28 table names with 2 key ranges (0 with more than 2) — no
population wider than stated. A direct grep of every `.Rule.xml` file
confirmed the singular `PropertyRateModificationFactor1`-`7` family has zero
references anywhere in the corpus (left untouched, as instructed), while the
plural family (24 references each) and `HeatingOilTankServingResidential
PropertiesIndicator` (10 references) are genuinely live.
