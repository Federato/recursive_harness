#!/usr/bin/env python3
"""TC-09: build `console/config/paths.json`, the coverage -> path configuration, from TC-05's census and D8-D13.

Configuration, not code (spec §4): it is regenerated when ISO content changes and versioned with it. Each line lists its
coverages, its paths (stable id, label, the coverages it counts toward) and, per state, whether each path applies or is
n/a with the reason (D5). A path may count toward more than one coverage.

    python scripts/tc/tc05_cp_paths.py          # first, if the CP census is stale
    python scripts/tc/tc09_build_paths.py

Sources: `results/tc/tc05_cp_paths.json` (CP, by rating) and `results/tc/tc05_gl_paths_20261006.json` (GL, by the
state packages' tables and rule overrides; `docs/TC-05-PATHS.md`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "tc"
OUT = ROOT / "console" / "config" / "paths.json"
sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------------------------------- GL (D8-D13)
GL_COVERAGES = ["Prem/Ops", "Prod/CO", "Cov B · P&AI", "Cov C · Med pay", "Deductibles"]
PO, PCO, B, C, D = GL_COVERAGES

GL_PATHS = {
    "gl.po.basis.payroll": ("Prem/Ops · payroll", [PO]),
    "gl.po.basis.area": ("Prem/Ops · area", [PO]),
    "gl.po.basis.sales": ("Prem/Ops · gross sales", [PO]),
    "gl.po.basis.units": ("Prem/Ops · units", [PO]),
    "gl.po.basis.other": ("Prem/Ops · other bases (admissions, gallons, acres …)", [PO]),
    "gl.po.elp.industry": ("Prem/Ops · ELP industry class", [PO]),
    "gl.po.elp.company": ("Prem/Ops · ELP company class", [PO]),
    "gl.po.ilf.direct": ("Prem/Ops · increased limits", [PO]),
    "gl.po.ilf.split": ("Prem/Ops · split BI/PD limits", [PO]),
    "gl.po.sor": ("Prem/Ops · size of risk (D8: replaces \"ILF interpolated\")", [PO]),
    "gl.po.lcm.filed": ("LCM · filed", [PO, PCO]),
    "gl.po.lcm.company": ("LCM · company / deviation", [PO, PCO]),
    "gl.po.minprem": ("Prem/Ops · minimum premium (D9: filed at $0)", [PO]),
    "gl.po.stateexc": ("Prem/Ops · state exceptions", [PO]),
    "gl.po.claimsmade": ("Prem/Ops · claims-made", [PO]),
    "gl.po.ilf.govunits": ("Prem/Ops · governmental-units ILF (state-filed)", [PO]),
    "gl.po.ilf.stopgap": ("Prem/Ops · stop-gap ILF (state-filed)", [PO]),
    "gl.pco.basis.sales": ("Prod/CO · gross sales", [PCO]),
    "gl.pco.basis.payroll": ("Prod/CO · payroll", [PCO]),
    "gl.pco.included": ("Prod/CO · included in Prem/Ops", [PCO]),
    "gl.pco.elp.industry": ("Prod/CO · ELP industry class", [PCO]),
    "gl.pco.elp.company": ("Prod/CO · ELP company class", [PCO]),
    "gl.pco.ilf.direct": ("Prod/CO · increased limits", [PCO]),
    "gl.pco.minprem": ("Prod/CO · minimum premium (D9: filed at $0)", [PCO]),
    "gl.pco.stateexc": ("Prod/CO · state exceptions", [PCO]),
    "gl.covb.included": ("Cov B · included (D11)", [B]),
    "gl.covb.excluded": ("Cov B · excluded (D11)", [B]),
    "gl.covc.basic": ("Cov C · basic limit", [C]),
    "gl.covc.increased": ("Cov C · increased limit", [C, PO]),
    "gl.covc.excluded": ("Cov C · excluded", [C]),
    "gl.covc.increased.2027": ("Cov C · increased limit, 2027 mechanism", [C, PO]),
}
for cov_key, cov in (("po", PO), ("pco", PCO)):
    for part, part_label in (("bi", "BI"), ("pd", "PD"), ("bipd", "BI/PD")):
        for basis, basis_label in (("occ", "per occurrence"), ("claim", "per claim (D10: filed at zero)")):
            GL_PATHS[f"gl.ded.{cov_key}.{part}.{basis}"] = (
                f"Deductible · {'Prem/Ops' if cov_key == 'po' else 'Prod/CO'} {part_label} {basis_label}", [D, cov])

#: TC-05's GL census (gl-authority, 2026-10-06): the states that file the variable paths.
SOR_NA = "AR CA DE FL GA IL KY LA MA MN NM NV NY PR SC TX".split()
PO_STATEEXC = "CA GA IN KY MA MD MO MS MT ND NH NJ NY OH OK PR TN TX UT VA WA WY".split()
PCO_STATEEXC = "AK AR AZ CT IN LA MD MO MT ND NH NJ NV NY OK PR SD TN UT VT".split()


def gl_applies(st: str) -> dict:
    out = {}
    for pid in GL_PATHS:
        why = None
        if pid == "gl.po.sor" and st in SOR_NA:
            why = "size of risk not offered (table filed empty)"
        elif pid == "gl.po.stateexc" and st not in PO_STATEEXC:
            why = "no Prem/Ops state exception filed"
        elif pid == "gl.pco.stateexc" and st not in PCO_STATEEXC:
            why = "no Prod/CO state exception filed"
        elif pid == "gl.po.claimsmade" and st == "NY":
            why = "NY files its claims-made table empty: not offered"
        elif pid == "gl.covc.increased.2027":
            why = "from 2027-04-01 (IncreasedMedPayLimitFactor)"
        out[pid] = "applies" if why is None else "n/a: " + why
        if pid in ("gl.po.ilf.govunits", "gl.po.ilf.stopgap") and why is None:
            out[pid] = "applies: where filed (states not yet listed; confirmed when a rating walks it)"
    return out


def main() -> int:
    cp = json.loads((RES / "tc05_cp_paths.json").read_text(encoding="utf-8"))
    gl = json.loads((RES / "tc05_gl_paths_20261006.json").read_text(encoding="utf-8"))
    cp_cov = []
    for p in cp["paths"].values():
        for c in p["coverages"]:
            if c not in cp_cov:
                cp_cov.append(c)
    config = {
        "version": "2026-10-06",
        "asof": "20260917 (CP), 20261006 (GL)",
        "about": "Coverage -> path configuration (TC-09). Generated by scripts/tc/tc09_build_paths.py from TC-05; do not "
                 "edit by hand. D5: 'n/a' where the state files no such path. D8-D13 shape the GL list.",
        "lines": {
            "CP": {"coverages": cp_cov,
                   "paths": {k: {"label": v["label"], "coverages": v["coverages"]} for k, v in cp["paths"].items()},
                   "states": {st: v["paths"] for st, v in cp["states"].items() if "paths" in v},
                   "no_package": ["ID", "LA", "MS", "WA"], "no_iso": ["PR"]},
            "GL": {"coverages": GL_COVERAGES,
                   "paths": {k: {"label": v[0], "coverages": v[1]} for k, v in GL_PATHS.items()},
                   "states": {st: gl_applies(st) for st in sorted(gl)},
                   "no_package": ["HI"], "no_iso": ["PR"]},
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(config, indent=1, ensure_ascii=False), encoding="utf-8")
    for line, c in config["lines"].items():
        n = len(c["paths"])
        cells = sum(1 for s in c["states"].values() for v in s.values())
        na = sum(1 for s in c["states"].values() for v in s.values() if v.startswith("n/a"))
        print(f"{line}: {len(c['coverages'])} coverages, {n} paths, {len(c['states'])} states; {cells} state-paths, {na} n/a")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
