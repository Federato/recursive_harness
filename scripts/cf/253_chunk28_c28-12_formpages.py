#!/usr/bin/env python3
"""Chunk 28 C28-12 (set D): OI-106, form names and numbers from a state `Pages` table merged with countrywide's.

Every in-force state files its own `Form Pages/Pages.FormPage.csv` (4 to 258 rows; countrywide ~450). Ours resolves a
state table wholesale (rule N3), so every `InitializeRuleSet` lookup keyed `CW` misses and the form reads "Value Not
Found"; ISO resolves the name (240 of 240 on chunk 27's responses, ours 135 missing). ISO replaces a RATE table with
rows wholesale (C21-13 T8), so the change is FormPage-only:
  M  a state `FormPage` table is the state's rows, then countrywide's (state first; matched by column name)
Measured on every stored request ISO rated: every `ErcFormName` / `ErcFormNumber` ours writes against ISO's, and every
premium and (level, message) unchanged. Predicted before the run (2026-10-05): "Value Not Found" goes to 0 where ISO
names the form, no name ISO gives differs, and nothing else moves.

    python scripts/cf/253_chunk28_c28-12_formpages.py [--only chunk27]
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import glob
import json
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
T0 = time.monotonic()

from cf_engine.resolve.book import CFResolvedBook                        # noqa: E402

c23 = import_module("221_chunk23_rc3")
rep, TAGGED, lvl, OUT = c23.rep, c23.TAGGED, c23.lvl, c23.gc.OUT
ORIG_TABLE = CFResolvedBook.table
MERGE = [False]
FORM = ("ErcFormName", "ErcFormNumber")
MONEY = ("Premium", "ErcCalculatedTotalPremium")


def merged_table(self, name, kind="Rate"):
    t = ORIG_TABLE(self, name, kind)
    if not MERGE[0] or kind != "FormPage" or not self.parent or not self.parent.has(kind, name) \
            or not self.state.has(kind, name):
        return t
    cw = self.parent.table(kind, name)
    idx = [cw.header.index(h) if h in cw.header else None for h in t.header]
    # a state row shadows countrywide's for the same record (its key without StateCode): VA's own
    # "Virginia Changes - Additional Covered Property" row hides CW's CP 14 10, and ISO answers "Value Not Found"
    # ...unless that state row's Status is "D": NC's own CP 14 10 rows are "D" and ISO still names CW's form there
    keys = [t.header.index("TableName")]
    st = t.header.index("Status") if "Status" in t.header else None
    own = {tuple(r[i] for i in keys) for r in t.rows if st is None or r[st] != "D"}
    extra = [row for row in (tuple(r[i] if i is not None else None for i in idx) for r in cw.rows)
             if tuple(row[i] for i in keys) not in own]
    return dataclasses.replace(t, rows=list(t.rows) + extra)


CFResolvedBook.table = merged_table


def fields(fn, obj, which):
    rep.FIELDS = which
    try:
        return fn(obj)
    finally:
        rep.FIELDS = MONEY


def ours(req, merge):
    MERGE[0] = merge
    TAGGED.clear()
    data, ip = rep.cmp.rate(req)
    return (collections.Counter((lvl(t), x) for t, x in TAGGED), fields(rep.our_prem, data, MONEY),
            fields(rep.our_prem, data, FORM))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--shard", help="k/n: the k-th of n interleaved slices (to run in parallel)")
    a = ap.parse_args()
    reqs = sorted(f for f in glob.glob(str(OUT / "*_request.json"))
                  if Path(f[:-len("_request.json")] + "_response.json").exists() and (not a.only or a.only in Path(f).name))
    if a.shard:
        k, n = (int(x) for x in a.shard.split("/"))
        reqs = reqs[k - 1::n]
    tot = collections.Counter()
    differ_examples, moved, raised = [], [], []
    for i, f in enumerate(reqs, 1):
        name = Path(f).name[:-len("_request.json")]
        req = json.loads(Path(f).read_text(encoding="utf-8"))
        resp = json.loads(Path(f[:-len("_request.json")] + "_response.json").read_text(encoding="utf-8"))
        iso = fields(rep.iso_prem, resp, FORM)
        isos = collections.Counter(c23.iso_tagged(resp))
        try:
            m0, p0, f0 = ours(req, False)
            m1, p1, f1 = ours(req, True)
        except Exception as exc:                      # noqa: BLE001
            raised.append((name, f"{type(exc).__name__}: {str(exc)[:80]}"))
            continue
        for k, v in iso.items():
            if v in (None, ""):
                continue
            tot["iso named"] += 1
            for tag, got in (("now", f0.get(k)), ("M", f1.get(k))):
                if got == v:
                    tot[f"{tag} equal"] += 1
                elif got == "Value Not Found":
                    tot[f"{tag} Value Not Found"] += 1
                    if tag == "M" and len(differ_examples) < 15:
                        differ_examples.append((name, k[-70:], v, got))
                else:
                    tot[f"{tag} other"] += 1
                    if tag == "M" and len(differ_examples) < 15:
                        differ_examples.append((name, k[-70:], v, got))
        if p0 != p1 or m0 != m1:
            moved.append((name, "premiums" if p0 != p1 else "", "messages" if m0 != m1 else ""))
        tot["messages equal to ISO now"] += m0 == isos
        tot["messages equal to ISO M"] += m1 == isos
        if i % 200 == 0 or i == len(reqs):
            mm, s = divmod(int(time.monotonic() - T0), 60)
            print(f"[{i}/{len(reqs)}  {mm}m{s:02d}s] {dict(tot)}")
    MERGE[0] = False
    print(f"\n{len(reqs)} stored requests ISO rated; form fields ISO names: {tot['iso named']}")
    for tag in ("now", "M"):
        print(f"  {tag:4s} equal {tot[f'{tag} equal']}, 'Value Not Found' {tot[f'{tag} Value Not Found']}, other {tot[f'{tag} other']}")
    print(f"  premiums or messages moved by M: {len(moved)}; raised {len(raised)}")
    for x in differ_examples:
        print("    M differs", x)
    for x in moved[:10]:
        print("    moved", x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
