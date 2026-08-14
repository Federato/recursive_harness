# Files from the walkthrough

Numbered in reading order — 01 first. Original locations in the repository are listed, since this
folder is flat.

| | File | Original path | |
|---|---|---|---|
| 01 | `PROCESS_LOG.md` | root | The analysis record, 53 steps. The standing criteria — what may source a value, what may only confirm one — are near the top |
| 02 | `nodes.py` | `gl_engine/interp/` | ISO's 54 instructions, one function each |
| 03 | `interpreter.py` | `gl_engine/interp/` | Executes them. Stops on an instruction it doesn't recognise |
| 04 | `resolver.py` | `gl_engine/resolve/` | Which ISO package applies for a jurisdiction and date, state over countrywide. Also where carrier edition pinning would go |
| 05 | `kernel.py` | `gl_engine/rating/` | Entry point — submission in, rating out |
| 06 | `tables.py` | `gl_engine/erc/` | Reads ISO's tables, typed from ISO's own definition files |
| 07 | `config.py` | `gl_engine/` | Where ISO's files are read from |
| 08 | `phase2_compare.py` | `scripts/` | Rates a submission through our engine and ISO's live service, then compares field by field |
| 09 | `breadth.py` | `scripts/` | The 17 risk variants used to widen the comparison beyond one risk shape |
| 10 | `TESTING.md` | root | Every test command, stage by stage |
| 11 | `BACKLOG.md` | `docs/BACKLOG-2026-08-14.md` | What's next. Items 7 and 8 are carrier deviations and carrier edition pinning |
| 12 | `OPEN-ITEMS.md` | `docs/` | OI-1 to OI-90. Resolved items are marked, not deleted |

**02 to 07 are the engine** — about 5,000 lines in total, and these are the parts that matter.
**08 to 10 are how it's tested. 11 and 12 are what's still open.**

The Python files are numbered for reading order, which means they can't be imported under these
names. They're copies — the working versions are at the paths above.

## Not included

ISO's ERC files — 89,065 files, about 0.77 GB of licensed ISO content. Read from
`C:\Projects\ISO_ERC_Files\General_Liability`, set in `config.py`.
