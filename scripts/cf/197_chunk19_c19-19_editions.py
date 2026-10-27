#!/usr/bin/env python3
"""Chunk 19, RC-4 (C19-19): editions.

The census (900_) compared each family's SetPremium in the four countrywide editions a state can stand on
(2026 V01; 2023 V02 / V03 / V04) and found them identical. A rate or factor rule in a CONTAINER can still
differ where SetPremium does not, so:
  1  every rule, in every chunk 19 family file (premium records and containers), is compared across the four
     editions after normalising whitespace and DataDefGroup; every file / rule that differs is listed;
  2  one live probe per older edition, 196_'s per-state policy and predictions (every record from that state's
     own rule on its own edition): MO (2023 V02), NC (2023 V03; CA's earthquake setup is out of scope),
     MA (2023 V04, which also files the trees' vehicle factor 1.15). FL RI VT (V04) were rated in C19-18.
     The diff (first run, 2026-09-29): only CW 2023 V02 differs, in 4 files -- the special-class Group I rate is
     looked up under OLDER option codes (antennas 62 / 63 for 34a / 34b, signs 12 / 13 for 7a / 7b, trees 42 for
     23) and V02 lacks the trees' blanket-cause message. Each probe checks its Group I rates from its own edition's
     option codes, independently.

    python scripts/cf/197_chunk19_c19-19_editions.py [--live]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

st = import_module("196_chunk19_c19-18_states")
cen = import_module("900_chunk19_census")
P = "CommercialProperty"
FAIL = []
PROBES = ["MO", "NC", "MA"]


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def rules(path):
    t = path.read_text(encoding="utf-8-sig", errors="replace")
    return {m.group(1): cen.norm(m.group(0)) for m in re.finditer(r'<rul:Rule Name="([^"]+)".*?</rul:Rule>', t, re.S)}


def edition_diff():
    eds = cen.EDITIONS
    base = eds["CW 2026 V01"] / "Rules"
    files = sorted(f.name for f in base.glob("*.xml")
                   if any(re.search(pat, f.name) for _, pat in cen.FAMILIES) and not cen.EXCLUDE.search(f.name))
    print(f"1  every rule in the {len(files)} chunk 19 family files, compared across the four countrywide editions")
    differ = 0
    for name in files:
        ref = rules(base / name)
        for ed, root in eds.items():
            if ed == "CW 2026 V01":
                continue
            f = root / "Rules" / name
            if not f.exists():
                print(f"    {name[len(P):-14]:70s} NOT FILED in {ed}")
                differ += 1
                continue
            other = rules(f)
            gone, new = sorted(set(ref) - set(other)), sorted(set(other) - set(ref))
            changed = sorted(r for r in set(ref) & set(other) if ref[r] != other[r])
            if gone or new or changed:
                differ += 1
                print(f"    {name[len(P):-14]:70s} {ed}: changed {changed[:4]} only-2026 {gone[:3]} only-{ed[-3:]} {new[:3]}")
    print(f"    files x editions that differ: {differ}")
    return differ


#: the special-class option each edition looks the Group I rate up under (the rule-by-rule diff: only CW 2023 V02
#: differs, with its older option numbers): antenna broadcasting, detached metal sign, trees
OPTIONS = {"CF CW 20230801 V02": ("Option62", "Option12", "Option42")}
OPTIONS_DEFAULT = ("Option34a", "Option7a", "Option23")


def option_checks(orig):
    """196_'s field checks + each probe's Group I rates from ITS edition's option codes (independent lookup)."""
    def f(data, j):
        out = orig(data, j)
        ed = st.r4.pkgs(j)[1].name
        ant, sign, trees = OPTIONS.get(ed, OPTIONS_DEFAULT)
        gv = lambda n, fld: n.first(fld).text if n.first(fld) is not None else None
        pc = gv(st.r16.find(data, P + "Structure")[0], "ProtectionClassToUse")
        rate = lambda opt: st.r4.val(j, "BasicGroupIRateSpecialClass", "Rate", SpecialClassDescConvertedOption=opt,
                                     ProtectionClassToUse=pc)
        for rec, fld, opt in (("RadioOrTelevisionAntennasDetail", "BasicGroupIRate", ant),
                              ("OutsideSignsDetail", "BasicGroupIRate", sign),
                              ("OutdoorTreesShrubsAndPlants", "BasicGroupIBaseRate", trees)):
            n = st.r16.find(data, P + rec)
            if n and rec == "OutsideSignsDetail" and gv(n[0], "SignPlacement") == "Attached":
                # an ATTACHED sign copies the building's adjusted Group I rate (C19-09), no option lookup
                out.append((f"{rec[:20]} {fld} (attached: the building's)", gv(n[0], fld),
                            gv(st.r16.find(data, P + "Structure")[0], "BasicGroupICauseOfLossAdjustment")))
            elif n:
                out.append((f"{rec[:20]} {fld} ({ed[-7:]} {opt})", gv(n[0], fld), rate(opt)))
        return out
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    progress(0, 1, "edition diff")
    edition_diff()
    for j in PROBES:
        print(f"  {j} stands on {st.r4.pkgs(j)[1].name}")
    argv = ["--states", ",".join(PROBES)] + (["--live"] if a.live else [])
    sys.argv = [sys.argv[0]] + argv
    st.PROBES.clear()                                  # the plan probes belong to C19-18
    st.field_checks = option_checks(st.field_checks)
    # a DETACHED sign, so its own option code (V02: 12) is looked up; 196_'s policy carries an attached one, which
    # copies the building's rate and would not exercise the edition (first run, 2026-09-29)
    orig_fields = st.fields
    st.fields = lambda j, cause="Special": dict(orig_fields(j, cause), OutsideSignsDetail=dict(
        orig_fields(j, cause)["OutsideSignsDetail"], SignPlacement="Detached"))
    rc = st.main()
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC19-19: {'ALL AGREE' if rc == 0 else 'FAILED'}  ({m}m{s:02d}s)")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
