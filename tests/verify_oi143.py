"""OI-143: a `Count` with no path counts its child list, and `GetList Distinct` keeps each value once.

Indiana Property's IL 09 03 rule (8 editions) gives "Mine Subsidence Schedule Endorsement is not valid if all buildings
are scheduled with the same limit" unless `Count(GetList Distinct(ForEach locations / ForEach structures /
MineSubsidenceLimit)) > 1`. The engine counted 1 always, so it gave the message when the limits differed; ISO does not
(one live call, 2026-10-25, ISOComputeGraph).

  A  the nodes: `Count` over a child list counts its values; `GetList Distinct` drops repeats; a `Count` with a path
     is unchanged
  B  Indiana 2025-07, scheduled buildings in Clay County, two buildings: limits 100,000 and 200,000 rate with no
     IL 09 03 message, as ISO's stored answer (no messages, 7,354); limits equal give it; the premium is unchanged

Run: python tests/verify_oi143.py
"""
from __future__ import annotations

import copy
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import property_rating  # noqa: E402
from cf_engine import rating as cf  # noqa: E402
from console import store  # noqa: E402
from gl_engine.interp.values import Multi  # noqa: E402

MSG = "IL 09 03 - Mine Subsidence Schedule Endorsement is not valid"
results: list[tuple[bool, str]] = []


def check(label: str, ok: bool) -> None:
    results.append((bool(ok), label))
    print(("  ok    " if ok else "  FAIL  ") + label)


def _first(v):
    return v[0] if isinstance(v, list) else v


def request(limits: tuple[int, int]) -> dict:
    """The harness's Indiana sample on 2025-07-01, Mine Subsidence on scheduled buildings, two buildings."""
    r = property_rating.sample("IN", "2025-07-01")
    cp = _first(r["body"]["CommercialProperty"])
    loc = _first(cp["CommercialPropertyLocation"])
    bldgs = loc["CommercialPropertyStructure"]
    bldgs = loc["CommercialPropertyStructure"] = bldgs if isinstance(bldgs, list) else [bldgs]
    if "BCEG" not in bldgs[0]:
        bldgs[0]["BCEG"] = "1"
    cp["MineSubsidenceCoverage"], cp["MineSubsidenceLimit"] = "Scheduled Buildings", 0
    loc["County"] = "Clay"
    second = copy.deepcopy(bldgs[0])
    second["UnitNumber"] = 2
    bldgs.append(second)
    for b, lim in zip(bldgs, limits):
        b["MineSubsidenceType"], b["MineSubsidenceLimit"] = "Non Dwelling Structure", lim
    cp["CommercialPropertyMineSubsidenceSchedule"] = [
        {"UnitNumber": i + 1, "CoveragePart": "Building", "Premises": 1, "Building": i + 1, "Limit": lim}
        for i, lim in enumerate(limits)]
    return r


def group_a():
    print("\nA  THE NODES")
    import xml.etree.ElementTree as ET
    from gl_engine.interp import nodes
    ns = "{http://www.iso.com/erc/rule}"

    class Ip:
        def eval(self, el, fr):
            return Multi(Decimal(x) for x in el.text.split())

        def tag(self, el):
            return el.tag

        def where(self, el):
            return ""

    getlist = ET.fromstring(f'<rul:GetList xmlns:rul="{ns[1:-1]}" Distinct="true"><rul:X>1 2 1 2 2</rul:X></rul:GetList>')
    got = nodes._get_list(Ip(), getlist, None)
    check("A1 GetList Distinct keeps each value once, in order (1 2 1 2 2 -> 1 2)", list(got) == [1, 2])
    plain = ET.fromstring(f'<rul:GetList xmlns:rul="{ns[1:-1]}"><rul:X>1 2 1</rul:X></rul:GetList>')
    check("A2 a plain GetList is unchanged (the whole tail)", list(nodes._get_list(Ip(), plain, None)) == [1, 2, 1])

    class Ip2(Ip):
        def eval(self, el, fr):
            return nodes._get_list(Ip(), el, fr)

    count = ET.fromstring(f'<rul:Count xmlns:rul="{ns[1:-1]}"><rul:GetList Distinct="true"><rul:X>5 5 7</rul:X>'
                          f'</rul:GetList></rul:Count>')
    check("A3 Count with no path counts its child list (5 5 7 distinct -> 2)", nodes._count(Ip2(), count, None) == 2)


def group_b():
    print("\nB  INDIANA 2025-07, SCHEDULED BUILDINGS")
    differ, same = request((100000, 200000)), request((100000, 100000))
    a, b = cf.rate(copy.deepcopy(differ)), cf.rate(copy.deepcopy(same))
    msgs = lambda r: [str(m) for m in getattr(r.ip, "messages", [])]
    check("B1 limits 100,000 / 200,000: rated, no IL 09 03 message",
          a.outcome["status"] == "rated" and not any(MSG in m for m in msgs(a)))
    check("B2 limits equal: rated, the IL 09 03 message given",
          b.outcome["status"] == "rated" and any(MSG in m for m in msgs(b)))
    iso = store.lookup(differ)
    check("B3 ISO's stored answer is this request's (hash 40980d24...)",
          iso is not None and store.request_hash(differ).startswith("40980d24"))
    check(f"B4 the premium is ISO's 7,354 on both (engine {a.premium}, {b.premium})",
          float(a.premium) == 7354.0 == float(b.premium))


def main() -> int:
    print("OI-143 -- a Count of a list counts the list")
    group_a()
    group_b()
    bad = [label for ok, label in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
