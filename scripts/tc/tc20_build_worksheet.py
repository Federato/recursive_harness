#!/usr/bin/env python3
"""TC-20: build the worksheet map's catalog, `console/config/worksheet.json`. No ISO calls.

Rates a sample of the stored request / response pairs per line on today's engine and aligns each (`console.worksheet`)
to collect, per stable ID: how often ISO publishes it, how often we write it, how often the two agree, which rule files
write it, and its kind (number, date, id, text). Versioned: the file names its build date, the engine packages seen and
a content hash of its ID list, so a later build that moves the map is visible as a new version.

    python scripts/tc/tc20_build_worksheet.py [--per-line 60]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from console import store, worksheet as W  # noqa: E402


def pairs(line: str, n: int) -> list:
    """Stored references of the line with both a request and a response on disk, a spread across states."""
    refs = [e for e in store.load()["references"] if e["line"] == line and e["outcome"] == "rated"
            and any(f.endswith("_request.json") for f in e["files"]) and any(f.endswith("_response.json") for f in e["files"])]
    by_state = collections.defaultdict(list)
    for e in refs:
        by_state[e["state"]].append(e)
    rnd = random.Random(20)
    out = []
    while len(out) < n and any(by_state.values()):
        for st in sorted(by_state):
            if by_state[st] and len(out) < n:
                out.append(by_state[st].pop(rnd.randrange(len(by_state[st]))))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-line", type=int, default=60)
    a = ap.parse_args()
    cat = {"version": "", "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "about": __doc__.split("\n\n")[1].replace("\n", " "), "lines": {}}
    for line in ("CP", "GL"):
        ids: dict = {}
        packages, rated, failed = set(), 0, 0
        for e in pairs(line, a.per_line):
            req = json.loads((ROOT / next(f for f in e["files"] if f.endswith("_request.json"))).read_text(encoding="utf-8"))
            resp = json.loads((ROOT / [f for f in e["files"] if f.endswith("_response.json")][-1]).read_text(encoding="utf-8"))
            try:
                tree, trace, _ = W.rate(line, req)
            except Exception:                                 # noqa: BLE001 -- refused / stopped: not part of the map
                failed += 1
                continue
            rated += 1
            for r in W.align(line, tree, trace, W.body_of(line, resp)):
                d = ids.setdefault(r["id"], {"record": W.record_of(r["id"]), "field": r["field"], "iso": 0, "ours": 0,
                                             "agree": 0, "kind": r["kind"], "rules": collections.Counter()})
                d["iso"] += r["in_iso"]
                d["ours"] += r["in_ours"]
                d["agree"] += bool(r["match"])
                if r["rule_file"]:
                    d["rules"][r["rule_file"]] += 1
                if r["package"]:
                    packages.add(r["package"])
        for d in ids.values():
            d["rules"] = [k for k, _ in d["rules"].most_common(3)]
            d["side"] = "both" if d["iso"] and d["ours"] else "iso-only" if d["iso"] else "ours-only"
        cat["lines"][line] = {"sampled": rated, "engine_refused": failed, "packages": sorted(packages),
                              "counts": dict(collections.Counter(d["side"] for d in ids.values())),
                              "ids": dict(sorted(ids.items()))}
        print(f"{line}: {rated} pairs rated ({failed} refused); {len(ids)} stable IDs {cat['lines'][line]['counts']}")
    h = hashlib.sha256(json.dumps({l: sorted(v["ids"]) for l, v in cat["lines"].items()}).encode()).hexdigest()[:12]
    cat["version"] = f"{time.strftime('%Y%m%d')}-{h}"
    W.CATALOG.write_text(json.dumps(cat, indent=1), encoding="utf-8")
    print(f"wrote {W.CATALOG.relative_to(ROOT)} version {cat['version']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
