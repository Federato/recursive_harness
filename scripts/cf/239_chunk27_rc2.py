#!/usr/bin/env python3
"""Chunk 27 RC-2 (C27-03, C27-04, C27-05): gate point 9 on chunks 1-8. Every golden case's messages, tallied and sent to ISO.

The method is chunk 9's (78_): run each golden case fresh, list every message, explain each one from the register
(CF_Algorithm/CF_Message_Register.md) or match it to ISO's. What 78_ did not do, and this does: send the SAME tree to ISO
(t2.state_req(t2.m20.payload(sub), "OR"), the request every later chunk sent) and compare the (level, message) multiset.

  C27-03  chunks 1-6: 01_ A/B/C, 09_, 15_ Broad/Special, 22_ / 32_ / 41_ Basic/Broad/Special
  C27-04  chunk 7: 50_ Basic/Broad/Special and the parent's deductible removed (53_'s "OR no ded"). Chunk 7's gate recorded
          ISO 3 / engine 5 (and 1 / 4); 53_ sent ISO a HAND-BUILT sparse payload (raas6.ITEM, no structure, no building),
          while the engine rated 50_'s full tree. Predicted (2026-10-02): sent the same tree, the counts agree, and the gap
          was the two inputs differing, not the engine.
  C27-05  chunk 8: 59_ building / contents x Basic/Broad/Special (Legal Liability)

  Predicted before the run: every message is M-001 (CP 03 20), M-002 (CP 10 75 / 76) or M-003 (debris > $25,000), or
  equal to one ISO returns on the same request.

    python scripts/cf/239_chunk27_rc2.py [--live] [--cases C1A,C7nd]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
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

from gl_engine.interp.values import InterpretError
import _state_inputs as _si                                     # noqa: E402

c23 = import_module("221_chunk23_rc3")                   # wraps MessageHelper (TAGGED), iso_tagged
t2, rep, gc = c23.t2, c23.rep, c23.gc
P, TAGGED, lvl = c23.P, c23.TAGGED, c23.lvl
g1 = import_module("01_golden_case")
g2 = import_module("09_chunk2_golden_case")
g3 = import_module("15_chunk3_golden_case")
g4 = import_module("22_chunk4_golden_case")
g5 = import_module("32_chunk5_golden_case")
g6 = import_module("41_chunk6_golden_case")
g7 = import_module("50_chunk7_golden_case")
g8 = import_module("59_chunk8_golden_case")
FAIL = []
# a refusal predicted before the call: the building carries no WindstormOrHailDeductible (see wind()); each has a "w" twin
REFUSE = {"C1B", "C4Ba", "C4Br", "C4Sp", "C8CBa", "C8CBr", "C8CSp"}
# a difference explained and registered: ours sets the location's MultipleDiffDeductibleSpclIndicator "Yes" on one special
# class item with no deductible (FirstNonNull skips the rule's own "" fallback, then null <> ""), ISO "No"; one extra
# CP 03 20 message, no premium moves. Closed by chunk 28 C28-07 (2026-10-05): a filed "" Constant now ends the
# FirstNonNull, so ours says "No" as ISO does. Nothing is explained here any more.
KNOWN = {}

REGISTER = [
    ("M-001", re.compile(r"CP 03 20 Must Be Attached")),
    ("M-002", re.compile(r"Either CP 10 75 Or CP 10 76 must be attached")),
    ("M-003", re.compile(r"CP 04 15|Debris Removal", re.I)),
    ("M-004", re.compile(r"Select a valid Theft Deductible with Theft Coverage included")),
    ("M-005", re.compile(r"Full Value cannot be lower than the Limit")),
    ("M-006", re.compile(r"Deductible not valid with Coverage form selected")),
]


def no_ded():
    sub = g7.submission("Basic")
    g6.item(sub).pop("Deductible", None)
    return sub


def wind(build):
    """ISO refuses a contents policy whose BUILDING has no WindstormOrHailDeductible (chunk 4: `WindstormOrHailDeductibleAsNumber`,
    keys CW + blank, SingleResult; OI-103's class). The contents rule reads ../../../../ = the Structure (the Table wrappers
    count), which is why chunk 8's copy on the contents did not clear it. The "w" cases set it to the building's own
    deductible, "1,000", so ISO can rate the golden case at all."""
    def b():
        sub = build()
        g8.zeros2.structure(sub)["WindstormOrHailDeductible"] = "1,000"
        return sub
    return b


CASES = {
    "C1A": ("C27-03", "chunk 1 case A", lambda: g1.submission(100000, 0)),
    "C1B": ("C27-03", "chunk 1 case B (contents)", lambda: g1.submission(100000, 100000)),
    "C1C": ("C27-03", "chunk 1 case C (LOI midpoint)", lambda: g1.submission(112500, 0)),
    "C2": ("C27-03", "chunk 2 Group II", g2.submission),
    **{f"C3{c[:2]}": ("C27-03", f"chunk 3 {c}", (lambda c=c: g3.submission(c))) for c in ("Broad", "Special")},
    **{f"C{n}{c[:2]}": ("C27-03", f"chunk {n} {c}", (lambda g=g, c=c: g.submission(c)))
       for n, g in ((4, g4), (5, g5), (6, g6)) for c in ("Basic", "Broad", "Special")},
    **{f"C7{c[:2]}": ("C27-04", f"chunk 7 {c}", (lambda c=c: g7.submission(c))) for c in ("Basic", "Broad", "Special")},
    "C7nd": ("C27-04", "chunk 7 Basic, the parent's deductible removed", no_ded),
    **{f"C8{s[0]}{c[:2]}": ("C27-05", f"chunk 8 {s.lower()} {c} (Legal Liability)", (lambda f=f, c=c: f(c)))
       for s, f in (("BUILDING", g8.building), ("CONTENTS", g8.contents)) for c in ("Basic", "Broad", "Special")},
}
# the contents cases ISO refuses as built (C1B, C4*, C8C*), again with the building's windstorm deductible
CASES.update({k + "w": (t, l + ", building WindstormOrHailDeductible 1,000", wind(b)) for k, (t, l, b) in list(CASES.items())
              if k == "C1B" or k.startswith("C4") or k.startswith("C8C")})


def no_wind(build):
    """Chunk 28 C28-05 put the building's windstorm deductible into the golden builders themselves; the REFUSE cases take it
    back out, so they stay the as-built request ISO refuses (and ours now refuses too, at the same table)."""
    def b():
        sub = build()
        g8.zeros2.structure(sub).pop("WindstormOrHailDeductible", None)
        return sub
    return b


CASES.update({k: (t, l, no_wind(b)) for k, (t, l, b) in CASES.items() if k in REFUSE})


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def rate_retry(client, req, tries=3):
    """ISO's connection drops now and then (a read timeout, a closed socket): retry those, never a refusal."""
    for k in range(tries):
        try:
            return client.rate(req)
        except OSError as exc:
            if k == tries - 1:
                raise
            print(f"      network {type(exc).__name__}, retry {k + 1}")
            time.sleep(5)


def register_id(msg):
    return next((rid for rid, rx in REGISTER if rx.search(msg)), None)


def ours_from_tree(build):
    """The golden case as its own script rates it: the tree, straight into the engine."""
    TAGGED.clear()
    data, ip = g8.run(build())
    return collections.Counter((lvl(t), x) for t, x in TAGGED)


def ours_from_request(req):
    TAGGED.clear()
    data, ip = rep.cmp.rate(req)
    return data, collections.Counter((lvl(t), x) for t, x in TAGGED)


def show(counter):
    return "".join(f"\n        {t.replace(P, '') or '?'}: {x[:110]}  x{n}  [{register_id(x) or 'not in register'}]"
                   for (t, x), n in sorted(counter.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = {k: v for k, v in CASES.items() if not a.cases or k in a.cases.split(",")}
    reqs, ours = {}, {}
    for i, (cid, (task, label, build)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"{cid} {task} {label}")
        req = t2.state_req(t2.m20.payload(_si.localize(build(), "OR")), "OR")
        if cid in REFUSE:
            # C28-05: ours refuses where ISO does, on the same SingleResult lookup
            try:
                ours_from_tree(build)
                why = "ours PRICES it"
            except InterpretError as exc:
                why = "" if "WindstormOrHailDeductibleAsNumber" in str(exc) else f"ours raises elsewhere: {str(exc)[:160]}"
            print(f"  {cid}: {why or 'ours REFUSES as ISO does (WindstormOrHailDeductibleAsNumber, CW + blank)'}")
            if why:
                FAIL.append(cid)
            reqs[cid] = req
            continue
        tree = ours_from_tree(build)
        req = t2.state_req(t2.m20.payload(_si.localize(build(), "OR")), "OR")
        _, viareq = ours_from_request(req)
        unreg = [k for k in tree if not register_id(k[1])]
        print(f"  {cid}: {sum(tree.values())} messages from the tree; {sum(viareq.values())} from the request "
              f"({'same' if tree == viareq else 'DIFFER'}); not in register: {len(unreg)}{show(tree)}")
        if tree != viareq:
            print(f"      tree only {sorted((tree - viareq).elements())[:3]}\n      request only {sorted((viareq - tree).elements())[:3]}")
        if unreg or tree != viareq:
            FAIL.append(cid)
        reqs[cid], ours[cid] = req, viareq
    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17: the same request, every premium and the (level, message) multiset")
        for i, cid in enumerate(cs, 1):
            progress(i, len(cs), f"ISO {cid}")
            req = reqs[cid]
            (gc.OUT / f"chunk27_rc2_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = rate_retry(client, req)
            except raas_mod.RaaSError as exc:
                hit = cid in REFUSE and "WindstormOrHailDeductibleAsNumber" in str(exc.body)
                print(f"  {cid} ISO REFUSES {'as predicted (no building WindstormOrHailDeductible; see ' + cid + 'w)' if hit else str(exc.body)[:280]}")
                if not hit:
                    FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk27_rc2_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            data, mine = ours_from_request(req)
            isos = collections.Counter(c23.iso_tagged(resp))
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            dd = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            ok = not dd and mine == isos
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: {len(ipr) - len(dd)} of {len(ipr)} premiums; messages ISO "
                  f"{sum(isos.values())} ours {sum(mine.values())}, (level, message) {'equal' if mine == isos else 'DIFFER'}"
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in dd[:6])
                  + "".join(f"\n        ISO only {t.replace(P, '')}: {x[:110]} x{n}" for (t, x), n in (isos - mine).items())
                  + "".join(f"\n        ours only {t.replace(P, '')}: {x[:110]} x{n}" for (t, x), n in (mine - isos).items()))
            if cid in REFUSE:
                print(f"      {cid} was predicted to be REFUSED")
                FAIL.append(f"{cid} live")
                continue
            if not ok and cid in KNOWN and not dd and sum((mine - isos).values()) == 1 and not (isos - mine):
                print(f"      explained: {KNOWN[cid]} (premiums equal; the one extra message is the known difference)")
            elif not ok:
                FAIL.append(f"{cid} live")
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nRC-2 (C27-03..05): {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({mm}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
