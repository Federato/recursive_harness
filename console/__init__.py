"""The ISO Rating Test Console's data layer (docs/TC-PLAN.md, RC-1). No screens, and nothing here rates.

* `status`    -- the five cell states plus n/a: keys, labels, glyphs, colours (TC-08)
* `paths`     -- the rating paths per line, their coverages, and which states file them (TC-09)
* `store`     -- one index over every ISO answer we hold, and which are stale (TC-06, TC-07)
* `signature` -- which paths one rating walked, read from the engine's own trace (TC-10)
* `mismatch`  -- the mismatch categories, tolerances and stored classifications (TC-11)
* `ledger`    -- every RaaS call, wherever it starts, against the daily cap and its lanes (TC-12)
* `rollup`    -- path states into coverage cells, and the calls left to finish (TC-13)

The rule `ui/` follows holds here too: the premium has one owner (the engine) and agreement has one (the comparison);
this package reads both and decides neither.
"""
