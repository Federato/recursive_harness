#!/usr/bin/env python3
"""Chunk 11 C11-09 -- validation messages: the golden case has no unexplained
message, and our messages equal ISO's on every chunk 11 case ISO has priced.

Two parts:

  1. The golden case, run fresh: every message must be in the register
     (`CF_Algorithm/CF_Message_Register.md`). Predicted: exactly one,
     M-002 "Either CP 10 75 Or CP 10 76 must be attached" -- designed out,
     not a defect.
  2. The three message rules that read a Leasehold Interest field
     (`DoMessageAtLeastOneLeaseholdInterestLimitIsRequiredInOrderToBeValid`,
     `DoMessageCP0060LeaseholdInterestEffectiveandExpirationDateMessages`,
     `DoMessageTerrorismSubLimitCannotExceedTheCoveragesLimit`, all on the
     Structure). Checked by comparing OUR message set with ISO's saved
     `RatingMessages` for every case `118_chunk11_c11-23_raas.py` sent --
     not by reading gates. Predicted from the rule text: Z2 (no amounts)
     adds "At least one Leasehold Interest limit...", Z4 (lease already
     ended) adds "CP 00 60 - Lease does not overlap...", nothing else adds
     an LI message. The CP 00 60 rule is date comparisons, so this is also
     the first message-level check of the OI-102/OI-107 date fixes.

Part 2 reads results/cf-raas/chunk11_*_response.json; a case whose saved
response is missing is printed as SKIPPED, not passed. Re-create them with
`118_chunk11_c11-23_raas.py`.

    python scripts/cf/121_chunk11_c11-09_messages.py

Exit 0 when the golden case's messages are all registered and every
compared case's message set equals ISO's.
"""
from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gl_engine.interp.values import InterpretError

g = import_module("114_chunk11_golden_case")
m = import_module("118_chunk11_c11-23_raas")
ROOT = Path(__file__).resolve().parents[2]

REGISTERED = {"Either CP 10 75 Or CP 10 76 must be attached": "M-002, designed out"}


def ours(sub):
    try:
        _, ip = g.run(sub)
    except InterpretError as exc:
        return None, str(exc)[:80]
    return {str(x) for x in ip.messages}, None


def iso(cid):
    f = ROOT / "results" / "cf-raas" / f"chunk11_{cid}_response.json"
    if not f.exists():
        return None
    r = json.loads(f.read_text(encoding="utf-8"))
    out = set()
    for rm in m.find(r, "RatingMessages"):
        for kind in ("Errors", "Warnings"):
            for e in rm.get(kind, []) or []:
                out.add(e.get("Description", ""))
    return out


def main() -> int:
    ok = True
    print("1. The golden case, fresh")
    msgs, err = ours(g.submission())
    unexplained = sorted((msgs or set()) - set(REGISTERED))
    good = err is None and msgs == set(REGISTERED)
    ok &= good
    for x in sorted(msgs or []):
        print(f"     - {x}   [{REGISTERED.get(x, 'UNEXPLAINED')}]")
    print(f"   {'MATCH' if good else 'MISMATCH'}: {len(msgs or [])} message(s), "
          f"{len(unexplained)} unexplained")

    print("\n2. Ours vs ISO, every case already priced live (2026-09-17)")
    compared = 0
    for cid, label, sub, _ in m.cases():
        want = iso(cid)
        if want is None:
            print(f"   {cid:4s} SKIPPED  no saved ISO response")
            continue
        got, err = ours(m.at_date(sub))
        if err:
            print(f"   {cid:4s} MISMATCH ours refused: {err}")
            ok = False
            continue
        compared += 1
        good = got == want
        ok &= good
        li = sorted(x for x in want if x not in REGISTERED)
        print(f"   {cid:4s} {'MATCH   ' if good else 'MISMATCH'} {label[:44]:44s} "
              f"beyond M-002: {li if li else '-'}")
        if not good:
            print(f"          ours only: {sorted(got - want)}  ISO only: {sorted(want - got)}")
    print(f"\n   compared {compared} case(s)")
    print()
    if ok:
        print("C11-09 matches: the golden case's one message is registered "
              "(M-002), and our messages equal ISO's on every compared case.")
        return 0
    print("MISMATCH -- see above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
