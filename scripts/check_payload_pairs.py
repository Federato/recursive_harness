"""Validate that each `Payloads/` input and output are the same submission.

A reconciliation run is only as good as its pairing, and this project has now
been wrong about its own oracle twice (OI-67, OI-77). So the pairing is checked
rather than assumed, before any premium is compared.

Two checks, both on fields ISO **echoes** rather than computes -- if the engine
cannot change a field, the input and the output must agree on it, and where they
do not the pair is not one submission:

  P1 identity   the `State` on the input, the output, and the folder name
  P2 echoes     every scalar the input supplies at policy level, compared with
                the same field on the output
  P3 edition    **ISO names the package it rated with**, in the response header:
                `"Scheme": "GL OK 20260801 V01 Scheme"`. That is the strongest
                provenance signal in these files and it went unused for a day.
                It settles two things at once -- whether our as-of resolution
                (N4/N5) picked the same edition ISO did, and whether the corpus
                even contains that edition

An unpaired output is **not an oracle**, and comparing against it manufactures a
defect that is not there. That is exactly what happened with AZ (+511) and AK
(+1) before this script existed.

    python scripts/check_payload_pairs.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PAYLOADS = ROOT / "Payloads"

#: `"Scheme": "GL OK 20260801 V01 Scheme"`
_SCHEME = re.compile(r"GL (?P<juris>[A-Z]{2}) (?P<edition>\d{8}) (?P<version>V\d+)")

#: Known and separately recorded: 34 pairs dispute this one field (OI-77).
#: Listed so it is reported apart from anything new rather than hidden.
KNOWN_DISPUTE = {"TerrorismCoverage"}


def scalars(obj: dict) -> dict:
    """Policy-level scalars only. Nested structures are compared elsewhere."""
    return {k: v for k, v in obj.items()
            if isinstance(v, (str, int, float)) and not isinstance(v, bool)}


def nested_scalars(obj: dict, prefix: str = "") -> dict:
    """One level into single-object children, e.g. MedPayCoverage/Limit."""
    out = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if isinstance(v2, (str, int, float)) and not isinstance(v2, bool):
                    out[f"{k}/{k2}"] = v2
    return out


def main() -> int:
    from gl_engine import EditionResolver
    resolver = EditionResolver()
    known = {p.pkg_id for p in resolver.packages}

    rows = []
    for d in sorted(p for p in PAYLOADS.iterdir() if p.is_dir()):
        fi, fo = d / "1. Input.json", d / "1. Output.json"
        if not (fi.exists() and fo.exists()):
            continue
        gi = json.loads(fi.read_text(encoding="utf-8-sig"))["body"]["GeneralLiability"][0]
        go = json.loads(fo.read_text(encoding="utf-8-sig"))["Body"]["GeneralLiability"][0]

        problems = []
        if not (d.name == gi.get("State") == go.get("State")):
            problems.append(
                f"IDENTITY: folder {d.name}, input {gi.get('State')}, "
                f"output {go.get('State')}")

        disputed = []
        si, so = scalars(gi), scalars(go)
        for k, v in si.items():
            if k in so and so[k] != v:
                (disputed if k in KNOWN_DISPUTE else problems).append(
                    f"{k}: input {v!r}, output {so[k]!r}")
        ni, no = nested_scalars(gi), nested_scalars(go)
        for k, v in ni.items():
            if k in no and no[k] != v:
                problems.append(f"{k}: input {v!r}, output {no[k]!r}")
            elif k not in no:
                problems.append(f"{k}: input {v!r}, ABSENT from output")

        # P3 -- the edition ISO actually rated with.
        raw = json.loads(fo.read_text(encoding="utf-8-sig"))
        scheme = raw.get("Header", {}).get("Scheme", "")
        m = _SCHEME.search(scheme)
        if m:
            iso_pkg = (f"GL_{m.group('juris')}_{m.group('edition')}"
                       f"_{m.group('version')}")
            eff = json.loads(fi.read_text(encoding="utf-8-sig"))["body"][
                "SchemeKeys"]["EffectiveDateTime"][:10].replace("-", "")
            try:
                ours = resolver.resolve(d.name, eff).state.pkg_id
            except Exception as exc:                      # noqa: BLE001
                ours = f"({type(exc).__name__})"
            if iso_pkg not in known:
                problems.append(
                    f"EDITION: ISO rated with {iso_pkg}, which is NOT in the "
                    f"corpus (we resolved {ours})")
            elif ours != iso_pkg:
                problems.append(
                    f"EDITION: ISO rated with {iso_pkg}, we resolved {ours}")

        rows.append((d.name, problems, disputed))

    broken = [r for r in rows if r[1]]
    print(f"PAYLOAD PAIR INTEGRITY  ({len(rows)} pairs)")
    print()
    print(f"    usable as an oracle        : {len(rows) - len(broken)} of {len(rows)}")
    print(f"    NOT usable                 : {len(broken)}")
    print(f"    disputing only {'/'.join(KNOWN_DISPUTE)} (OI-77): "
          f"{sum(1 for r in rows if r[2] and not r[1])}")
    print()
    for name, problems, _ in rows:
        if not problems:
            continue
        print(f"    {name}")
        for p in problems:
            print(f"        {p}")
    print()
    print("    An unpaired output is not an oracle. Comparing against one")
    print("    manufactures a defect that is not there.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
