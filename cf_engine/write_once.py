"""Writes ISO keeps once made: the countrywide 2023-08 V01 rules as ISO's live service runs them (OI-144, OI-146,
OI-148, OI-149; found by ISOComputeGraph C-73, 2026-10-27).

**What the corpus holds.** ISO's later rules guard a field that may be written twice: `If IsNull(Value X
AllowNullReturn) Then <write X>`, so the first write stands. CW 2022-10 V01 files 3,847 such guards, CW 2023-08 V02
3,919, V03 3,935. **Our copy of CW 2023-08 V01 files 14.** Its rules are, almost rule for rule, the same text with the
guards taken out.

**What ISO does.** ISO's answers on that parent behave as if the guards were there. Every one of these was apart from
ISO and comes out equal with them, and every request on the parent that was equal stays equal (307 with ISO's
answer, C-73):

* OI-146: an occupancy's personal property and wind or hail totals stay 0 (the guarded `Constant 0` is the first
  write), so the building's wind or hail total is the building alone and the deductible factor's band follows (14
  ISO test cases in 10 states).
* OI-144: a blanket's `Counter` stays 0, so ISO's "Blanket Rating requires 2 or more risks to be valid" is given (91).
* OI-148: a drone schedule's `TotalScheduleLimit` stays 0, so its earthquake factor and premium are 0 (NH, 2).
* OI-149: California 2024-04 rates personal property before its base rate is set; the adjusted and final rates are
  written first as 0 and kept, so the fire premium is 0 (1).

**The reading, narrow by construction.** A V01 rule is read with guards only where it is **exactly** a reference
rule with that rule's guards taken out (CW 2023-08 V02 first, else CW 2022-10 V01): same elements, same attributes,
same order. Then each write that sits under a guard in the reference is a write-once write here: it is skipped when
its field already holds a value. A V01 rule that differs from its reference in any other way (19 of them; V02 moved
the pollutant aggregate's guard to a temporary field, for one) is read as filed. Nothing on another parent changes,
and nothing in GL: a GL book has no `write_once`.

The table (`resolve/write_once.json`) is built from the corpus by `python -m cf_engine.write_once --build` and
checked current by `tests/verify_write_once.py`.
"""
from __future__ import annotations

import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TABLE = Path(__file__).resolve().parent / "resolve" / "write_once.json"

#: The parent our corpus holds without its guards, and the references its rules are read against, in order.
PARENT = "CF_CW_20230801_V01"
REFERENCES = ("CF_CW_20230801_V02", "CF_CW_20221001_V01")

_RULES: dict | None = None
_IDS: dict[int, frozenset] = {}          # id(RuleFile) -> ids of its write-once write elements


def _lname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def guard_field(el) -> str | None:
    """X, when `el` is `If (Test IsNull(Value X AllowNullReturn="true")) Then ...` with no Else."""
    if _lname(el.tag) != "If":
        return None
    kids = list(el)
    if len(kids) != 2 or _lname(kids[0].tag) != "Test" or _lname(kids[1].tag) != "Then":
        return None
    t = list(kids[0])
    if len(t) != 1 or _lname(t[0].tag) != "IsNull":
        return None
    v = list(t[0])
    if len(v) != 1 or _lname(v[0].tag) != "Value" or v[0].attrib.get("AllowNullReturn") != "true":
        return None
    return v[0].attrib.get("FromDataDef")


def unguarded(rule):
    """A copy of the rule with every guard replaced by what it guards; each element it guarded is marked."""
    rule = copy.deepcopy(rule)

    def walk(node):
        for ch in list(node):
            if guard_field(ch):
                body = list(list(ch)[1])
                if len(body) == 1 and _lname(body[0].tag) == "Sequence":
                    body = list(body[0])
                at = list(node).index(ch)
                node.remove(ch)
                for j, b in enumerate(body):
                    node.insert(at + j, b)
                    b.set("__guarded", "1")
        for ch in node:
            walk(ch)
    walk(rule)
    return rule


def _canon(rule) -> bytes:
    e = copy.deepcopy(rule)
    for x in e.iter():
        x.attrib.pop("__guarded", None)
        x.text = (x.text or "").strip() or None
        x.tail = None
    return ET.tostring(e)


def guarded_writes(stripped) -> list[int]:
    """Positions (in `iter()` order) of the writes that sat under a guard, in a rule from `unguarded`."""
    order = list(stripped.iter())
    inside = set()
    for x in order:
        if x.attrib.get("__guarded"):
            inside |= {id(y) for y in x.iter()}
    return [i for i, x in enumerate(order) if id(x) in inside and "ToDataDef" in x.attrib]


def build() -> dict:
    """The table, from the corpus: for each V01 rule that is a reference rule less its guards, its write-once writes."""
    from cf_engine.resolve.resolver import CFEditionResolver
    from gl_engine.interp.program import RuleFile
    res = CFEditionResolver()

    def rules(pid):
        out = {}
        for f in sorted(res.by_id[pid].content.joinpath("Rules").glob("*.Rule.xml")):
            rf = RuleFile.load(f)
            for name, el in rf.rules.items():
                out[(rf.name, name)] = el
        return out

    v01 = rules(PARENT)
    refs = [{k: el for k, el in rules(pid).items() if any(guard_field(x) for x in el.iter())} for pid in REFERENCES]
    table, counts = {}, {"rules": 0, "writes": 0, "differ": 0, **{pid: 0 for pid in REFERENCES}}
    for key, el in v01.items():
        mine = _canon(el)
        for pid, ref in zip(REFERENCES, refs):
            r = ref.get(key)
            if r is None:
                continue
            st = unguarded(r)
            if _canon(st) == mine:
                pos = guarded_writes(st)
                if pos:
                    table.setdefault(key[0], {})[key[1]] = pos
                    counts["rules"] += 1
                    counts["writes"] += len(pos)
                    counts[pid] += 1
                break
        else:
            if any(key in ref for ref in refs):
                counts["differ"] += 1
    return {"parent": PARENT, "references": list(REFERENCES), "counts": counts, "rules": table}


def _rules() -> dict:
    global _RULES
    if _RULES is None:
        _RULES = json.loads(TABLE.read_text(encoding="utf-8"))["rules"]
    return _RULES


def ids_for(program, file_name: str) -> frozenset:
    """Ids of the write-once write elements in this rule file of `program` (empty unless it is the V01 parent).

    Read from the file the interpreter itself parsed (`Program.file`, cached per process), so the ids are the very
    elements it evaluates."""
    if program.pkg_id != PARENT:
        return frozenset()
    spec = _rules().get(file_name)
    if not spec:
        return frozenset()
    rf = program.file(file_name)
    got = _IDS.get(id(rf))
    if got is None:
        ids = set()
        for rule_name, pos in spec.items():
            el = rf.rules.get(rule_name)
            if el is not None:
                order = list(el.iter())
                ids |= {id(order[i]) for i in pos if i < len(order)}
        got = _IDS[id(rf)] = frozenset(ids)
    return got


if __name__ == "__main__":
    if sys.argv[1:] == ["--build"]:
        t = build()
        TABLE.write_text(json.dumps(t, indent=1, sort_keys=True), encoding="utf-8")
        print(f"{TABLE.name}: {t['counts']}")
    else:
        print(__doc__)
