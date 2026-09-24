"""RC-4: fields a state ADDS to the records our payload sends, that the payload never sends.

Found by the "more states" run: Arizona multiplies Group I by a location field
(`BasicGroupIReductionCredit`, Private Fire Department Credit, default 1) that nothing sets,
so leaving it out made ISO's Group I rate 0; Colorado requires a county-driven
`GeographicWindHazardLevelTerritory` and refuses without it. Both are state additions to the
Form Fields. This sweep lists every such field for every state (latest package, all edition
folders), against the union of fields our payloads actually send, so the gaps are found by
listing, not by waiting for ISO to refuse.

Read-only; no Excel. Prints a table and writes CF_Algorithm/CF_State_Field_Gaps.csv.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ERC = Path(r"C:\Projects\ISO_ERC_Files\CF")
CW = ERC / "20260601" / "CFCW20260601V01" / "Form Fields" / "Fields.FormField.csv"
TABLES = {"CommercialPropertyLocation", "CommercialPropertyStructure", "CommercialPropertyOccupClass",
          "CommercialPropertyPersonalProperty", "CommercialPropertyBusinessIncome",
          "CommercialPropertySpecialClass", "CommercialPropertySpecialClassBusnIncome", "CommercialProperty"}
SKIP = {"PR"}


def rows(path):
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def latest(state):
    pk = []
    for d in ERC.glob(f"*/CF {state} *"):
        m = re.match(rf"CF {state} (\d{{8}}) V(\d+)", d.name)
        if m and (d / "Form Fields" / "Fields.FormField.csv").exists():
            pk.append((m.group(1), int(m.group(2)), d))
    return max(pk)[2] if pk else None


def sent_fields():
    """Every (record, field) any stored request of ours carried."""
    out = defaultdict(set)

    def walk(node, name):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, list):
                    for x in v:
                        walk(x, k)
                else:
                    out[name].add(k)
        elif isinstance(node, list):
            for x in node:
                walk(x, name)
    for f in list((REPO / "results").glob("cf-payload/*/*_request.json")) + \
            list((REPO / "results").glob("cf-scenarios/*/*/*_request.json")):
        body = json.loads(f.read_text())["body"]["CommercialProperty"][0]
        walk(body, "CommercialProperty")
    return out


def main() -> int:
    cw = {(r["TableName"], r["ColumnName"]) for r in rows(CW)}
    sent = sent_fields()
    states = sorted({re.match(r"CF (\w\w) ", d.name).group(1) for d in ERC.glob("*/CF ?? *")} - SKIP)
    gaps = []
    for st in states:
        pkg = latest(st)
        if not pkg:
            continue
        for r in rows(pkg / "Form Fields" / "Fields.FormField.csv"):
            t, c = r["TableName"], r["ColumnName"]
            if t not in TABLES or (t, c) in cw or c in sent.get(t, set()):
                continue
            if r.get("Condition") and "Specific" in r["Condition"]:
                pass                                            # still listed; condition shown
            gaps.append({"state": st, "package": pkg.name, "record": t.replace("CommercialProperty", "") or "Policy",
                         "field": c, "label": re.sub(r"&nbsp;|<[^>]+>", "", r["Label"]).strip(),
                         "type": r["Type"], "required": r["QuoteRequired"], "default": r["Default"],
                         "min": r["Minimum"], "max": r["Maximum"], "condition": r["Condition"][:80],
                         "domain": r["DomainTableName"]})
    out = REPO / "CF_Algorithm" / "CF_State_Field_Gaps.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(gaps[0]) if gaps else ["state"])
        w.writeheader()
        w.writerows(gaps)
    by_state = defaultdict(list)
    for g in gaps:
        by_state[g["state"]].append(g)
    for st, gs in by_state.items():
        print(f"{st} ({gs[0]['package']}): " + "; ".join(
            f"{g['record']}.{g['field']}{' REQUIRED' if g['required'] == 'True' else ''}"
            f"{' default=' + g['default'] if g['default'] else ''}" for g in gs))
    print(f"\n{len(gaps)} state-added fields not sent, in {len(by_state)} states -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
