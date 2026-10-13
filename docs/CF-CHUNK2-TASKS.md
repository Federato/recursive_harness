# Property chunk 2 — task list and status

**Building, Basic Group II, class-rated, scheduled.** Opened 2026-09-17.

The golden case and its derivation are in
[`CF-CHUNK2-GOLDEN-CASE.md`](CF-CHUNK2-GOLDEN-CASE.md). This page is the task
list; the gate document is [`CF-CHUNK2-GATE.md`](CF-CHUNK2-GATE.md).

**Chunk 2 passed 8 of 8 on 2026-09-17**, with no engine code written for it.

| # | Task | Status | Evidence |
|---|---|---|---|
| — | Golden case, hand-derived before code | ✅ | `09_chunk2_golden_case.py` — Group I $261 **and** Group II $32 from one submission, both confirmed by ISO |
| 1 | Zero cases | ✅ | `10_chunk2_zero_cases.py` — 5 cases |
| 2 | 47-jurisdiction sweep, each premium predicted | ✅ | `11_chunk2_enumerate_states.py` — **41 of 47 exact, 0 failures** |
| 3 | Wind/hail-excluded branch | ✅ | `12_chunk2_windhail.py` — 5 cases |
| 4 | Class-specific symbol overrides | ✅ | `13_chunk2_symbol_and_numeric.py` |
| 5 | `BasicGroupIINumericValue` doing something | ✅ | same, S1/S2 — $32 → $127 |
| 6 | Fire-only cause-of-loss gate, all 8 SPP options | ✅ | `14_chunk2_fire_only_gate.py` — all 8, a clean 2x2, two corners ISO-confirmed |
| 7 | Shared names · exclusion records · literals · gate doc | ✅ | `04_shared_names.py` extended to the Group II chain; [`CF-CHUNK2-GATE.md`](CF-CHUNK2-GATE.md) — **8 of 8** |
| 8 | **`SingleResult` with zero hits** | ✅ measured — **not adopted** | see below |

---

## 6 · The fire-only gate — a clean 2x2

All eight Standard Property Policy options, enumerated from ISO's own domain
table rather than typed from the manual. **Two independent dimensions, each
hitting a different coverage group:**

| | Group II | Group I |
|---|---|---|
| **"Allied Lines" in the name** | decides it — $0 without, $31 with | no effect |
| **"Vandalism" in the name** | no effect | decides `VandalismExclFactor` — 0.95 without, 1.0 with, so $242 / $255 |

Asserted rather than eyeballed: the four options the rule names, the four
without "Allied Lines", and the four that price Group II at zero are **the same
four**. The algorithms doc reasoned they would be, because Allied Lines includes
windstorm and hail — which is what Group II is. Now measured.

Group II is $31 here rather than the golden case's $32 because
`StdPropPolGroupIIFactor` (0.98) applies to a Standard Property Policy.

ISO confirms both corners: `Fire` → GI 242 / GII 0; `Fire, Vandalism and Allied
Lines` → GI 255 / GII 31.

---

## 8 · `SingleResult` with zero hits — MEASURED, and NOT adopted

**In plain terms.** When a rate-table lookup finds no matching row, ISO's engine
sometimes stops and rejects the whole submission. Ours never does — it treats it
as "no value" and carries on. The worry was that a submission ISO would refuse
could come back from us as a quiet, plausible premium.

**How it surfaced.** A bare `ConstructionType` gave us Group I $0 and Group II
$0, silently; ISO gave a 400:

```
Matrix: ConstructionTypeToUse, Keys: CW, Masonry Non-Combustible.
No results have been returned.
```

### The population, measured first

| | CF | GL |
|---|---|---|
| `Lookup` with `ResultMode="SingleResult"` | 36,045 | 6,524 |
| `FirstNonNull` constructs containing one | 23,631 | 4,935 |
| …where SingleResult is the **last resort** | 23,586 | 4,935 |
| …where a `Constant` follows it as a real fallback | **45** | 0 |

### The result: DISPROVEN as a blanket rule

`Interpreter(strict_single_result=True)` was added to measure it, defaulting
**off** (`ERC_STRICT_SINGLE_RESULT=1` to run a whole suite under it).

Switching it on **breaks General Liability**: `verify_stage3` drops 38→34 and
`verify_breadth` 28→27. Two stored payloads stop rating —

```
VA: SingleResult matched NO row in 'Subline'
VT: SingleResult matched NO row in 'Subline'
```

— and **ISO rates both of those payloads successfully.** So ISO does *not*
refuse on every `SingleResult` miss.

### What the failure actually is, traced out

* **Virginia and Vermont file `Subline` themselves with ZERO rows**, in every
  edition from 20231201 onward (Vermont regains 8 rows at 20270401). Under N3 a
  state override wins by name even when empty, so *both* passes miss — the
  countrywide pass included, because the state's empty table has replaced it.
* The failing lookup is the **Liquor** coverage's Subline. ISO's stored response
  for Virginia carries Subline codes for PremOps (`334`) and ProdsCompldOps
  (`336`) but **none for Liquor** — so ISO produced nothing there either.
* **We already agree with ISO.** Non-strict returns null, ISO omits the field.
  Strict mode would have broken an agreement that is currently correct.

### Conclusion

**Not adopted. The default stays off**, and this is now a disproven hypothesis
rather than an open question — the third of three settled the same way:
`null→zero` (disproven), `ordering` (unfalsifiable), `strict SingleResult`
(disproven).

What remains genuinely open is narrower and should be stated as such: **ISO
refuses on *some* empty `SingleResult` lookups and tolerates others, and the
distinguishing condition is not known.** The corpus cannot settle it — both
sites have the identical two-pass shape, `FirstResult` state pass then
`SingleResult` countrywide pass with no trailing constant. Settling it needs
targeted probes at ISO's service, not more corpus reading.

**Why this was still worth doing.** The switch is the only reason anyone now
knows that Virginia and Vermont cannot produce a Liquor subline code at all. The
premium never moves, so no premium comparison could ever have shown it.

**Related, and still open:** input validation. Five inputs price at zero rather
than raising — Arizona's `BasicGroupIReductionCredit`, an unrecognised
`ConstructionType`, an absent `BCEG`, a missing `RatingTypeBasicGroupII`, a
missing Group II territory. That is the content-side half, and it is not
addressed by this.
