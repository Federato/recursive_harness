#!/usr/bin/env python3
"""Chunk 19, RC-4 (C19-17): the earthquake sub-limit deductible layer on Antennas and Signs.

Read from the rules first (2026-09-29):
  * The EQ sub-limit records ATTACH from the location's EQCauseOfLossForm and are REMOVED otherwise:
    "Earthquake Sub-Limit Form (CP 10 45)" -> the percentage endorsement; "(CP 10 29)" -> the flat-dollar
    deductible form. (A record submitted under CP 10 40 is deleted: the first exploration.)
  * The detail's SetEQDeductibleFactor (countrywide) then reads the BUILDING's EQDeductibleTier, EQClassToUse,
    EQSubLimitPercent (0 < % <= 75) and EQDeductible:
      CP 10 45  class A1 / "B1 and C1" -> Tier 1 Table 1, Tier 2 Table 3, Tier 3 Table 5 (D-E classes: Tables 2 / 4 / 6)
      CP 10 29  one of 15 EQSubLimit<ded>FlatDeductibleFactor tables, keyed tier, class, deductible, sub-limit %
                and the location's EarthquakeTotalPropertyValue
  * Countrywide, every tier lookup reads the one-row STUB EQSubLimitDeductibleTierCWTable (Factor 0). A state
    rewrites the lookups for the tiers it files, pointing them at its own range tables (EQClass, sub-limit %
    band From / ToLessThan, deductible; Factor_From / Factor_ToLessThan, interpolated inside the band).
    A tier the state does not rewrite stays on the stub: factor 0, EQ $0.
  * AK MA TN VT (and FL) file the stub HEADER-ONLY and leave a tier on it: our engine falls back to the
    countrywide row (0, CFResolvedBook, 2026-09-28); ISO settles whether it does the same or refuses.

Probes (antenna under 75 ft and a detached metal sign, 300,000 each, Special; the building's own earthquake
election, class A1, deductible 10%), each factor looked up independently and each premium predicted by hand:
  E1  OR  Tier 1, 25%  -> OR Tier1Table1 [25, 30) band start
  E2  OR  Tier 1, 27%  -> interpolated inside [25, 30): From + (To - From) x 2 / 5 (vs the band start, E1)
  E3  OR  Tier 2, 25%  -> OR Tier2Table3
  E4  OR  Tier 3, 25%  -> OR Tier3Table5
  E5  CO  Tier 1       -> CO rewrites only Tier 2: the countrywide stub, factor 0, EQ $0
  E6  CO  Tier 2       -> CO Tier2Table3
  E7  VT  Tier 1       -> not rewritten, VT's stub HEADER-ONLY: CW row 0, EQ $0 (or ISO refuses)
  E8  AK  Tier 2       -> AK REWRITES the antenna's Set rule (any tier but 1 -> 1.0); the sign keeps the CW rule
  E9  OR  CP 10 29, deductible 5,000, 25% -> EQSubLimit5000FlatDeductibleFactor at the location's total value

    python scripts/cf/195_chunk19_c19-17_eq_tiers.py [--live] [--cases E1,E5]

Progress streams as [i/n elapsed] lines. Exits 1 on any disagreement.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

sys.stdout.reconfigure(line_buffering=True)
T0 = time.monotonic()

from cf_engine.resolve import book_for                                   # noqa: E402
from gl_engine.interp.values import InterpretError                       # noqa: E402

g = import_module("192_chunk19_rc2")
r2, rc1, gc, rep, cmp, r11, r16 = g.r2, g.rc1, g.gc, g.rep, g.cmp, g.r11, g.r16
P, same = g.P, g.same
r11.NUMERIC |= {"EQSubLimitPercent"}
FAIL = []
ANT, SIGN = g.ANT, g.SIGN
RECS = [f"{ANT}DetailEarthquakeCoverage", f"{SIGN}DetailEarthquakeCoverage",
        f"{ANT}DetailBasicGroupICoverage", f"{SIGN}DetailBasicGroupICoverage"]
TIER_TABLE = {"1": "EQSubLimitDeductibleTier1Table1", "2": "EQSubLimitDeductibleTier2Table3", "3": "EQSubLimitDeductibleTier3Table5"}
TIER_RULE = {"1": "LookupEQSubLimitDeductibleTier1Table1", "2": "LookupEQSubLimitDeductibleTier2Table3",
             "3": "LookupEQSubLimitDeductibleTier3Table5"}


def progress(i, n, what):
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {m}m{s:02d}s] {what}")


def q3(x):
    return Decimal(str(x)).quantize(Decimal("0.001"), ROUND_HALF_UP)


# ---------------------------------------------------------------- policy

def build(j, tier="1", pct="25", flat=False, ded=None):
    def b():
        sub = g.with_cause(g.portable(j), "Special")
        at = rc1.node_dicts(sub)
        st = at[P + "Structure"]
        st["EQSubLimitPercent"] = pct
        if ded:
            # every earthquake-elected coverage on the flat form carries the flat deductible: with the special
            # class left at chunk 10's "10%", ISO refuses on EarthquakeFlatDollarDeductibleStatCode (first live run)
            st["EQDeductible"] = ded
            at[P + "SpecialClass"]["EQDeductible"] = ded
        at[P + "Location"]["EQDeductibleTier"] = tier
        at[P + "Location"]["EQCauseOfLossForm"] = ("Earthquake Sub-Limit Form (CP 10 29)" if flat
                                                   else "Earthquake Sub-Limit Form (CP 10 45)")
        sign = g.sign_det("Special", "Detached", "Entirely Metal", "300000")
        ant = {"CauseOfLoss": "Special", "Coinsurance": "80%", "Limit": "300000", "Type": g.BROADCAST,
               "Height": "Not over 75 Feet in Height", "EQCovIndicator": "Yes"}
        if j != "OR":
            # the portable policy has no Group II territory: submit the details' (IsNull-guarded) Group II base
            # rate, as 192_ does for trees (ISO refused BasicGroupIIRate "CW, , AB" on the first live run)
            sign["BasicGroupIIBaseRate"] = ant["BasicGroupIIBaseRate"] = "0.030"
        st[P + SIGN + "Table"] = {P + SIGN: [{P + SIGN + "DetailTable": {P + SIGN + "Detail": [sign]}}]}
        st[P + ANT + "Table"] = {P + ANT: [{P + ANT + "DetailTable": {P + ANT + "Detail": [ant]}}]}
        for f in ("BasicGroupI", "Earthquake"):
            r2.put(sub, f"{ANT}Detail{f}Coverage", state=j)
            r2.put(sub, f"{SIGN}Detail{f}Coverage", state=j)
        return sub
    return b


# ------------------------------------------------------- independent factor

def rows(pk, table):
    f = pk / "Rate Tables" / f"{table}.RateTable.csv"
    if not f.exists():
        return None
    with open(f, encoding="utf-8-sig") as h:
        return list(csv.DictReader(h))


def band(rs, pct, **keys):
    """the row whose [From, ToLessThan) band holds pct; the factor interpolated inside it, to 3 places."""
    p = Decimal(pct)
    for r in rs:
        if all(r[k] == v for k, v in keys.items()) and Decimal(r["EQSubLimitPct_From"]) <= p < Decimal(r["EQSubLimitPct_ToLessThan"]):
            lo, hi = Decimal(r["EQSubLimitPct_From"]), Decimal(r["EQSubLimitPct_ToLessThan"])
            f0, f1 = Decimal(r["Factor_From"]), Decimal(r["Factor_ToLessThan"])
            return q3(f0 + (f1 - f0) * (p - lo) / (hi - lo))
    raise LookupError(f"no band for {pct} {keys}")


#: each record's own rule and field (the sign's rule is named for the sub-limit factor)
FACTOR = {ANT + "Detail": ("SetEQDeductibleFactor", "EQDeductibleFactor"),
          SIGN + "Detail": ("SetEQSubLimitDeductibleFactor", "EQSubLimitDeductibleFactor")}


def rule_text(pk, rec):
    f = pk / "Rules" / f"{P}{rec}Rules.Rule.xml"
    return f.read_text(encoding="utf-8-sig", errors="replace") if f.exists() else ""


def expected_factor(j, rec, tier, pct, cls="A1", ded="10%", flat=False, tpv=None):
    """(factor, how) for record rec from THAT state's own rule and tables, independently of the engine: the
    state's Set rule if it rewrites it (AK: any tier but 1 -> 1.0), else the countrywide one; the state's lookup
    for the tier if it rewrites it (its range table, CW rows if it files it header-only), else the countrywide
    stub (a HEADER-ONLY state stub falls back to the CW row, as the engine does since 2026-09-28)."""
    book = book_for(j, r2.ASOF)
    spk, cpk = book.state.package.content, book.parent.package.content
    set_rule, _ = FACTOR[rec]
    st = rule_text(spk, rec)
    if flat:
        for r in rows(cpk, f"EQSubLimit{ded.replace(',', '')}FlatDeductibleFactor"):
            if (r["EQDeductibleTier"] == tier and r["EQClass"] == cls and r["EQDeductible"] == ded
                    and Decimal(r["EQSubLimitPct_From"]) <= Decimal(pct) < Decimal(r["EQSubLimitPct_ToLessThan"])
                    and Decimal(r["TotalPropertyValue_From"]) <= Decimal(tpv) < Decimal(r["TotalPropertyValue_ToLessThan"])):
                lo, hi = Decimal(r["EQSubLimitPct_From"]), Decimal(r["EQSubLimitPct_ToLessThan"])
                f0, f1 = Decimal(r["Factor_From"]), Decimal(r["Factor_ToLessThan"])
                return q3(f0 + (f1 - f0) * (Decimal(pct) - lo) / (hi - lo)), "CW flat-deductible table"
        raise LookupError("flat: no row")
    own_set = f'Rule Name="{set_rule}"' in st
    if own_set and tier != "1":
        m = re.search(rf'<rul:Rule Name="{set_rule}".*?</rul:Rule>', st, re.S).group(0)
        if f'"{TIER_RULE[tier]}"' not in m:
            return Decimal("1.0"), f"{j} rewrites {set_rule}: only Tier 1 is looked up, else 1.0"
    if f'Rule Name="{TIER_RULE[tier]}"' in st:
        rs = rows(spk, TIER_TABLE[tier])
        if rs:
            return band(rs, pct, EQClass=cls, EQDeductible=ded), f"{j} {TIER_TABLE[tier]} (rewritten lookup)"
        return band(rows(cpk, TIER_TABLE[tier]) or [], pct, EQClass=cls, EQDeductible=ded), f"{j} header-only, CW rows"
    stub = rows(spk, "EQSubLimitDeductibleTierCWTable")
    cw = Decimal(rows(cpk, "EQSubLimitDeductibleTierCWTable")[0]["Factor"])
    return cw, "the countrywide stub" + (" (the state files it HEADER-ONLY: CW row)" if stub == [] else "")


# ---------------------------------------------------------------- cases

def cases():
    return {
        "E1": ("OR", "Tier 1, 25%: OR Tier1Table1, band start", dict(tier="1", pct="25")),
        "E2": ("OR", "Tier 1, 27%: interpolated inside [25, 30)", dict(tier="1", pct="27")),
        "E3": ("OR", "Tier 2, 25%: OR Tier2Table3", dict(tier="2", pct="25")),
        "E4": ("OR", "Tier 3, 25%: OR Tier3Table5", dict(tier="3", pct="25")),
        "E5": ("CO", "Tier 1: CO does not rewrite it, the countrywide stub (0)", dict(tier="1", pct="25")),
        "E6": ("CO", "Tier 2: CO Tier2Table3", dict(tier="2", pct="25")),
        "E7": ("VT", "Tier 1: not rewritten, VT's stub header-only (ISO REFUSES; ours refuses too, C28-05)", dict(tier="1", pct="25")),
        "E8": ("AK", "Tier 2: not rewritten, AK's stub header-only", dict(tier="2", pct="25")),
        "E9": ("OR", "CP 10 29 flat-dollar form, deductible 5,000, 25%", dict(tier="1", pct="25", flat=True, ded="5,000")),
    }


#: Where ISO refuses (OI-103's shape). E7: VT files the stub EQSubLimitDeductibleTierCWTable header-only; ISO does NOT
#: fall back to the CW row here, although it did for VT's header-only VacancyPermitFactors (C18-16). Since chunk 28
#: C28-05 ours reads that one table as filed (`CFResolvedBook.NO_EMPTY_FALLBACK`) and refuses at the same lookup.
REFUSE = {"E7": "EQSubLimitDeductibleTierCWTable"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases")
    a = ap.parse_args()
    cs = cases()
    if a.cases:
        cs = {k: v for k, v in cs.items() if k in a.cases.split(",")}
    preds = {}
    for i, (cid, (j, label, kw)) in enumerate(cs.items(), 1):
        progress(i, len(cs), f"engine {cid}")
        try:
            data, ip = gc.run(build(j, **kw)(), j)
        except InterpretError as exc:
            if cid in REFUSE and f"NO row in '{REFUSE[cid]}'" in str(exc):
                print(f"{cid} ours REFUSES as ISO does ({REFUSE[cid]}; C28-05)")
                continue
            print(f"{cid} RAISED {str(exc)[:150]}")
            FAIL.append(cid)
            continue
        gv = lambda n, f: n.first(f).text if n.first(f) is not None else None
        loc = r16.find(data, P + "Location")[0]
        tpv = gv(loc, "EarthquakeTotalPropertyValue")
        fl = []
        for rec in (ANT + "Detail", SIGN + "Detail"):
            want, how = expected_factor(j, rec, kw["tier"], kw["pct"], flat=kw.get("flat", False), ded=kw.get("ded", "10%"), tpv=tpv)
            got = gv(r16.find(data, P + rec)[0], FACTOR[rec][1])
            fl.append((rec, got, want, how))
        fok = all(same(got, want) for _, got, want, _ in fl)
        preds[cid] = {}
        lines, bad = [], []
        for rec in RECS:
            res, _ = r2.predict(data, rec, {}, j)
            hv = [h for h, _ in res]
            ok = all(not str(h).startswith("hand") and same(h, e) for h, e in res)
            preds[cid][rec] = hv
            lines.append(f"      {'ok  ' if ok else 'FAIL'} {r16.short(rec)[:48]:48s} predicted {[str(h) for h in hv]} engine {[e for _, e in res]}")
            if not ok:
                bad.append(rec)
        print(f"{cid} {j} {label}: {'as derived' if fok and not bad else 'DIFFERS'} (total property value {tpv})")
        for rec, got, want, how in fl:
            print(f"      {'ok  ' if same(got, want) else 'FAIL'} {rec[:26]:26s} factor {got}  independent {want}: {how}")
        print("\n".join(lines))
        if bad or not fok:
            FAIL.append(cid)

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live at 2026-09-17 (predicted records, every premium field for field, messages):")
        for i, (cid, (j, label, kw)) in enumerate(cs.items(), 1):
            progress(i, len(cs), f"ISO {cid}")
            req = r11.payload(build(j, **kw)())
            if j != "OR":
                for cp in req["body"]["CommercialProperty"]:
                    cp["State"] = j
                req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            (gc.OUT / f"chunk19_c19-17_{cid}_request.json").write_text(json.dumps(req, indent=2), encoding="utf-8")
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,200})', str(exc.body))
                known = cid in REFUSE and REFUSE[cid] in str(exc.body)
                print(f"  {cid} ISO REFUSES {'(as expected: ISO refuses, ours too) ' if known else ''}"
                      f"{m.group(0)[:220] if m else str(exc.body)[:220]}")
                if not known:
                    FAIL.append(f"{cid} live")
                continue
            (gc.OUT / f"chunk19_c19-17_{cid}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            if cid in REFUSE:
                print(f"  {cid} ISO now RATES a policy it refused on 2026-09-29: re-examine")
                FAIL.append(f"{cid} live")
                continue
            pbad = []
            for rec in RECS:
                want = [w for w in preds.get(cid, {}).get(rec, []) if not same(w, 0)]
                iso = [x for x in r2.iso_of(resp, rec) if not same(x, 0)]
                if sorted(Decimal(str(x)) for x in iso) != sorted(Decimal(str(w)) for w in want):
                    pbad.append((rec, iso, [str(w) for w in want]))
            data, ip = rep.cmp.rate(req)
            ipr, opr = rep.iso_prem(resp), rep.our_prem(data)
            d = [(k, v, opr.get(k)) for k, v in ipr.items() if not rep.cmp.same(v, opr.get(k))]
            mi, mo = cmp.iso_messages(resp), set(ip.messages)
            ok = not pbad and not d and mi == mo
            print(f"  {cid} {'AGREE' if ok else 'DIFFER'}: predicted {len(RECS) - len(pbad)} of {len(RECS)} records; "
                  f"{len(ipr) - len(d)} of {len(ipr)} premiums; messages {'equal' if mi == mo else 'DIFFER'}"
                  + "".join(f"\n        predicted {r16.short(r)[:60]}: ISO {x}, derived {w}" for r, x, w in pbad[:6])
                  + "".join(f"\n        {k[-90:]} ISO {v} ours {o}" for k, v, o in d[:5])
                  + (f"\n        ISO only {sorted(mi - mo)[:3]}\n        ours only {sorted(mo - mi)[:3]}" if mi != mo else ""))
            if not ok:
                FAIL.append(f"{cid} live")
    m, s = divmod(int(time.monotonic() - T0), 60)
    print(f"\nC19-17: {'ALL AGREE' if not FAIL else 'FAILED: ' + ', '.join(FAIL)}  ({m}m{s:02d}s)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
