"""Chunk 14 opening census: policy assembly (aggregation, minimum premium, statistical coding).

Read-only; always exits 0 -- a census, not a test.

    python scripts/cf/156_chunk14_census.py
"""
import collections
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from cf_engine.resolve import book_for

census11 = import_module("106_chunk11_census")
ASOF = "20260917"
ISO_CF = Path("F:/ISO_ERC_Files/CF")


def rules_in(s):
    return {m.group(1): m.group(0) for m in re.finditer(r'<rul:Rule Name="([^"]+)".*?</rul:Rule>', s, re.S)}


def main():
    b = book_for("OR", ASOF)
    cw = b.parent.package.content
    files = {f.name: f.read_text(encoding="utf-8-sig") for f in (cw / "Rules").glob("*.xml")}
    pol = rules_in(files["CommercialPropertyRules.Rule.xml"])

    print("1. AGGREGATION")
    n_ctp = sum(1 for s in files.values() if 'Name="CalculateTotalPremium"' in s)
    writers = sum(1 for s in files.values() for body in rules_in(s).values()
                  if 'ToDataDef="ErcCalculatedTotalPremium"' in body)
    print(f"   {n_ctp} of {len(files)} rule files carry CalculateTotalPremium; {writers} rules write ErcCalculatedTotalPremium")
    ctp = pol["CalculateTotalPremium"]
    print(f"   the policy's CalculateTotalPremium sums {len(re.findall('<rul:RunRule', ctp))} record types; "
          f"ErcCalculateTotalPremium writes {re.findall(r'ToDataDef=\"([^\"]+)\"', pol['ErcCalculateTotalPremium'])}")

    print("\n2. MINIMUM PREMIUM")
    readers = collections.Counter()
    for f in ISO_CF.rglob("Rules/*.xml"):
        s = f.read_text(encoding="utf-8-sig", errors="replace")
        # "Min" alone also matches "MineSubsidence" (KY / IL mine subsidence premiums, a state
        # coverage, not a minimum premium) -- the first cut of this census counted them.
        for t in re.findall(r'MatrixFromConstant="(\w*(?:Minimum|MinPrem|PolMin)\w*)"', s):
            readers[(f.parts[-3].split()[1] if " " in f.parts[-3] else f.parts[-3], t)] += 1
    for t in ("MinimumPremium", "PolMinPremium"):
        p = cw / "Rate Tables" / f"{t}.RateTable.csv"
        n = len(p.read_text(encoding="utf-8-sig").splitlines()) - 1 if p.exists() else None
        print(f"   {t}: {n} rows countrywide")
    print(f"   rules reading any minimum-premium table, every package: {dict(readers) or 'none'}")

    print("\n3. POLICY MODIFIERS (CW 2026 policy file)")
    for k in ("IRPM", "PackageMod", "MultipleLocations", "StandardPropertyPolicy", "SPP", "ResetPrsnlProp"):
        names = [n for n in pol if k in n]
        print(f"   {k:24s} {len(names):2d}  {names[:6]}")

    print("\n4. STATISTICAL CODING")
    sc_rules = disp = 0
    tables = set()
    for s in files.values():
        for n, body in rules_in(s).items():
            if "StatCode" in n or n == "ErcSetStatisticalCodes":
                sc_rules += 1
                disp += n == "ErcSetStatisticalCodes"
            tables |= set(re.findall(r'MatrixFromConstant="([^"]*StatCode[^"]*)"', body))
    print(f"   {sc_rules} stat-code rules ({disp} ErcSetStatisticalCodes dispatchers); {len(tables)} stat-code tables read")

    print("\n5. STATE LAYER (46, PR excluded): overrides in the state's policy file")
    ov = collections.defaultdict(list)
    names = ("CalculateTotalPremium", "ErcCalculateTotalPremium", "SetIRPMFactor", "SetIRPMMaximum",
             "SetPackageModFactor", "SetMultipleLocationsAvgRate", "ErcSetStatisticalCodes")
    for j in census11.JURIS:
        if j == "PR":
            continue
        try:
            bk = book_for(j, ASOF)
        except Exception:
            continue
        p = bk.state.package.content / "Rules" / "CommercialPropertyRules.Rule.xml"
        if p.exists():
            rs = rules_in(p.read_text(encoding="utf-8-sig"))
            for n in names:
                if n in rs:
                    ov[n].append(j)
    for n in names:
        print(f"   {n:30s} {len(ov[n]):2d}  {' '.join(ov[n]) if len(ov[n]) < 12 else ''}")

    print("\n6. EVIDENCE ALREADY STORED (chunk 13's ISO fixture responses)")
    fx = sorted((ROOT / "results" / "cf-raas").glob("chunk13_fixture_*_response.json"))
    stat = tot = 0
    for p in fx:
        r = json.loads(p.read_text(encoding="utf-8"))
        s = json.dumps(r)
        stat += len(re.findall(r'StatCode"', s))
        tot += '"ErcCalculatedTotalPremium"' in s
    print(f"   {len(fx)} stored responses; {tot} carry a policy ErcCalculatedTotalPremium; {stat} stat-code values")


if __name__ == "__main__":
    main()
