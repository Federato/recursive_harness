# Property chunk 28: the gate

**Engine behaviour decisions: every open item that needed a ruling, ruled on.** Filed 2026-10-06.
**22 of 22 tasks done.** Task record: [`CF-CHUNK28-TASKS.md`](CF-CHUNK28-TASKS.md). Seven sets, A to G, each engine
change built only with the user's go, one item at a time. 546 of 546 countrywide premium files built, unchanged.

**In plain English.** Chunks 1 to 27 built a rating engine that agrees with ISO wherever ISO answers. What they left
was a list of places where ours and ISO behave differently by design, or where a bad input quietly gives a cheap
policy. Chunk 28 took each one to a decision. Ours now **refuses where ISO refuses** (a lookup with no row), **refuses
an input that would silently price a coverage at $0** (stricter than ISO, by the user's choice), **says when a minimum
premium needs a company decision**, **names every attached form as ISO does**, **sends the same messages ISO sends**,
**refuses a date ISO rates on a package we don't hold**, and **holds every package ISO serves through 2027-10-01**. The
two items without a fix were decided by the user at the gate: OI-116 closed, OI-117 to the parking lot.

## Every item, and where it ended

| Set / item | Outcome | Evidence |
|---|---|---|
| **A. OI-99, OI-103**: ISO refuses, ours priced (often $0) | ✅ **fixed** (C28-05, the user's go 2026-10-05) | A `SingleResult` lookup with no row refuses (`CFResolvedBook.strict_single_result`); the EQ sub-limit stub read as filed. `245_ --refused` live: 87 of 87 lookup refusals ours refuses, 37 of 37 ISO now rates ours prices; `248_` 17 of 17 new probes refused at ISO's table and keys. [`CF-CHUNK28-REFUSALS.md`](CF-CHUNK28-REFUSALS.md), [`CF-CHUNK28-PROPOSAL-A.md`](CF-CHUNK28-PROPOSAL-A.md) |
| **A. OI-117**: `Convert` of a blank text value; ISO refuses, ours reads blank and rates | 🅿 **parking lot, the user's decision** (2026-10-06) | Not a lookup, so outside C28-05's rule ([`CF-CHUNK28-PROPOSAL-A.md`](CF-CHUNK28-PROPOSAL-A.md)); still prices where ISO refuses (`245_`, Z11). Kept with its evidence; an engine change if ever taken up |
| **B. The silent-zero inputs** (AZ reduction credit, BCEG, Group II territory, blank Broad / Special deductible; unfiled construction types) | ✅ **fixed, by decision stricter than ISO** (C28-17) | `254_ --live`: ISO prices five of them $0 silently, two both refuse, 0 divergences ([`CF-CHUNK28-SILENT-ZEROS.md`](CF-CHUNK28-SILENT-ZEROS.md)). Ours refuses (`InvalidInput`) only where the missing input zeroes an attached coverage. Test policies now carry each state's real inputs (`_state_inputs.py`); 26 scripts re-run live, all agree with ISO |
| **B. A submitted derived field** (e.g. `SpecialBaseRate`) | ✅ **fixed** (C28-08, OI-125) | A submitted value a rule writes later is not read (a look-ahead pass); 1,688 of 1,692 stored requests submit one; 0 premiums moved, K4d fixed ([`CF-CHUNK28-PROPOSAL-C2.md`](CF-CHUNK28-PROPOSAL-C2.md)) |
| **C. OI-123, OI-125, OI-126, OI-112, OI-114**: messages | ✅ **fixed, matches ISO** (C28-07 to C28-11) | Each message-only; `206_` moved exactly the predicted message sets (7, then 6), no current-edition premium; the 4 back-dated policies now rate equal to ISO. [`CF-CHUNK28-PROPOSAL-C1.md`](CF-CHUNK28-PROPOSAL-C1.md), [`CF-CHUNK28-PROPOSAL-C2.md`](CF-CHUNK28-PROPOSAL-C2.md) |
| **D. OI-106 (+ OI-118)**: form names | ✅ **fixed, matches ISO** (C28-12, C28-13) | State `FormPage` rows, then countrywide's: 90,645 of 90,645 form names and numbers equal to ISO (was 13,455); 0 premiums or messages moved ([`CF-CHUNK28-PROPOSAL-D.md`](CF-CHUNK28-PROPOSAL-D.md)) |
| **D. OI-116**: Florida's SPP condo record (CP 17 96), ISO never attaches it | ✅ **closed, the user's decision** (2026-10-06) | Unexplained by the filed rules; five live probes; the question for ISO ([`CF-CHUNK28-ISO-QUESTION-OI116.md`](CF-CHUNK28-ISO-QUESTION-OI116.md)) not sent; ours keeps attaching the record as the filed rule reads (KNOWN in `208_`) |
| **E. OI-113**: minimum premium | ✅ **fixed** (C28-16, C28-17) | ISO applies none; an optional `CompanyMinimumPremium` gives the outcome *refer to company* below it, the rated premium unchanged ([`CF-CHUNK28-DESIGN-B-E.md`](CF-CHUNK28-DESIGN-B-E.md)) |
| **F. OI-105**: dates beyond the corpus | ✅ **fixed and closed** (C28-19, C28-20, 2026-10-06) | C28-19 (the user's choice: refuse): a date ISO is known to rate on a package we lack refuses, naming both (`257_`). C28-20: all 34 newer packages imported, with the new countrywide `CF_CW_20270101_V01`; ISO and ours name the same package in 46 of 46 states at all 276 dates checked; **287 of 287 cases agree with ISO** (`256_`); OR 2027-01-01, the item's own case, equals ISO ($97). [`CF-CHUNK28-PROPOSAL-F.md`](CF-CHUNK28-PROPOSAL-F.md) |
| **G. Housekeeping** | ✅ **done, option (b)** (C28-21) | Chunk 28's Property steps moved out of GL's interpreter into `cf_engine/run_checks.py`; nothing moved (snapshot clean, no rebaseline). Option (c), a neutral shared core, left for when a Property app is built |

**The outcome field** (C28-16 on): every Property rating reports `rated`, `refused` (with the kind: a lookup with no
row, *invalid input*, *older package*) or `refer to company`, beside the premium.

## The user's decisions at the gate (2026-10-06)

* **OI-116** (FL SPP condo record): **closed** as it stands. The written question for ISO is not sent; ours keeps
  attaching the record as the filed rule reads.
* **OI-117** (`Convert` of a blank): **parking lot**, a new register status for known items deliberately not worked
  now. Taking it up would be an engine change, with the user's go and a probe set like C28-06's.

Nothing in chunk 28 is left open.

## Found at the gate

* **`248_`'s P5 and P9 had drifted** since C28-17's commit: the shared request builder began filling each state's real
  Group II inputs, which overwrote P9's deliberate territory and moved P5's refusal. Both still agreed with ISO (ISO
  refused P5 at the same table, rated P9 as ours did), but no longer tested their point. Built as written again, both
  refuse at ISO's table and keys, live. Not caught earlier because chunk 28's scripts were not in the regression;
  **`248_`, `250_` and `257_` are now registered in `104_`**.
* **`213_`'s engine-change ledger** lacked today's files (`iso_packages.json` passed unseen while uncommitted); added with
  their verification (C28-21).
* **`224_`'s census** and **`256_`'s result files** were corrected during C28-20 (imported fixtures named; files dated).

## Gate checks (C28-22)

Chunk 28 changed the engine, so the full gate ran (not the quick tier chunk 27 used), on 2026-10-06 after C28-21:

* `206_ --check` **SNAPSHOT CLEAN**: 2,074 stored requests, 1,257,442 fields, nothing moved (11 new since the baseline)
* `157_ --all` **293 of 293**: 14,236 premium values and every policy total equal to ISO
* `104_ --gate` **REGRESSION CLEAN**: 173 scripts, every grid in full, every golden case of chunks 1 to 28 reproducing its
  documented figures, GL's suites included (18m37s)

Registered in `104_` at this gate: `248_` (the 17 refusal probes), `250_` (the OI-123 probe), `257_` (C28-19). The
measurements (`245_`-`247_`, `249_`, `251_`-`256_`) stay out: they always exit 0 or replay every stored request, and
their findings are pinned by `206_`'s snapshot. `252_` (OI-114, a replay of every stored request) was not re-run to
completion at the gate (over 25 minutes beside the gate run); its finding, the 4 back-dated policies equal to ISO, is
in the snapshot above.

Engine changes in the chunk, each built with the user's go: C28-05 (strict `SingleResult`), C28-07 / C28-08 / C28-09 /
C28-10 (messages and submitted inputs), C28-12 (form pages), C28-17 (silent zeros, the outcome field), C28-19 (older
package), C28-21 (Property steps moved out of GL's interpreter, no behaviour change). Data: C28-20's 34 packages.
