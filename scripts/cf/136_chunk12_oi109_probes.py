#!/usr/bin/env python3
"""OI-109 -- is ISO's "$0 for a null premium" general?

Found by removing one field at a time from every chunk 12 golden submission and
keeping the removals where OUR engine refuses with "Product wrote a NULL to
'Premium'". Only two shapes exist: a missing coverage Limit on the building or
Business Income record (it cascades to every endorsement priced off it), and
Ordinance or Law's own B/C limits. Each is sent to ISO live at 2026-09-17 and
every premium in the response is compared with ours.

    python scripts/cf/136_chunk12_oi109_probes.py
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from importlib import import_module

fam = import_module("132_chunk12_family_raas")
g = import_module("127_chunk12_golden_case")
o = import_module("130_chunk12_ordinance_golden_case")
u = import_module("133_chunk12_utility_golden_case")
c5 = import_module("32_chunk5_golden_case")
gates = import_module("128_chunk12_debris_removal_gates")


def without_bldg_limit(sub):
    sub = copy.deepcopy(sub)
    gates.structure(sub).pop("Limit", None)
    return sub


def without_bi_limit(sub):
    sub = copy.deepcopy(sub)
    gates.structure(sub)["CommercialPropertyBusinessIncomeTable"]["CommercialPropertyBusinessIncome"][0].pop("Limit", None)
    return sub


def _lcm10(sub):
    gates.structure(sub)["LossCostMultiplier"] = "10.0"
    return sub


CASES = [
    ("P1", "building with no Limit (chunk 2's building)", without_bldg_limit(g.chunk2.submission())),
    ("P2", "Business Income with no Limit (chunk 5)", without_bi_limit(c5.submission())),
    ("P3", "Ordinance or Law, only CovB demolition limit missing",
     o.submission(record={k: v for k, v in o.RECORD.items() if k != "CovBDemolitionLimit"})),
    ("P4", "Utility Services time element, BI with no Limit", without_bi_limit(u.te_submission())),
    # OI-110: the discriminating probe. P1-P4 cannot tell "a null premium is
    # $0" from "a null operand is SKIPPED in the product": every rate they
    # carried rounds to $0 on its own. At LossCostMultiplier 10 the building's
    # final BGI rate is 2.604, so skipping the absent limit gives $3, zeroing $0.
    ("P5", "building with no Limit, LossCostMultiplier 10 (final BGI rate 2.604)",
     without_bldg_limit(_lcm10(g.chunk2.submission()))),
]

if __name__ == "__main__":
    fam.compare("oi109", "CommercialProperty", CASES)
