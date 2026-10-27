"""Chunk 13, RC-4 (C13-16 to C13-22): terrorism across the 46 states, each from its own rows.

C13-16  TABLES. For every state, the rows it resolves (its own, or the parent
        edition's) in the five terrorism tables: territory tier, loss cost,
        nuclear/biological/chemical factor, sub-limit factor, fire exception.
C13-17  TERRITORIES. Every filed TerrorismTerritory -> tier, and for every tier
        whether the loss cost (program year 3 and full) and NBC rows exist.
C13-22  THE SWEEP. Chunk 2's building with terrorism in effect (IL 09 52, factor
        1.0), in one territory of EVERY tier of EVERY state. The premium is
        predicted from the state's own rows before the engine runs:
            rate = round4( round3(PY3[state, tier] x LCM) x 1.0 )
            prem = round0( round4( round4( round4(1000 x rate) x PC ) x Coins ) x Ded )
        LCM is the state's `LossCostMultiplier` row, else CW (1.0). PC, coinsurance
        and deductible are the building factors chunks 1-3 proved in every state,
        read from the run; everything terrorism is predicted independently.
C13-18  FIRE-EXCEPTION STATES. The same building with certified acts declined
        (IL 09 53): in states that file `TerrorismFireExcptnFactor` the rate is
        PY3 x that factor; everywhere else the CW rule gives 0.
C13-21  POSTTRIA. Post-TRIA forms, "No Exclusion": rate = Full[state, tier] x 1.0,
        on the PostTRIA roll-up.

A state whose engine figure differs from its own-row prediction is listed with
its cause (a rule the state rewrites), for C13-19 / C13-20 to explain. LCM is
set to 10 so a tier's loss cost is visible above the rounding (the building's
own premium reads its own multiplier input, unchanged).

    python scripts/cf/152_chunk13_rc4_states.py [--live]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.interp.values import InterpretError
import _iso_refusals as _iso                                    # noqa: E402

gc = import_module("149_chunk13_golden_case")
si = import_module("_state_inputs")                       # C28-17: a state's own Group II territory
rc3 = import_module("151_chunk13_rc3_mechanisms")
r11, rp = gc.r11, gc.rp
ASOF = gc.ASOF
LCM = Decimal(10)
STRUCT, POL = gc.STRUCT, gc.POL
T = f"{STRUCT}/TerrorismPremium"
PT = f"{POL}/CommercialPropertyPostTRIACoverage/Premium"
TABLES = ["TerrorismTerritoryTier", "TerrorismLossCost", "TerrorismNBCExclFactor", "TerrorismSubLimitFactor",
          "TerrorismFireExcptnFactor"]
KEYCOL = {"TerrorismTerritoryTier": "StateCode", "TerrorismLossCost": "StateCode",
          "TerrorismNBCExclFactor": "StateCode", "TerrorismSubLimitFactor": "StateCode",
          "TerrorismFireExcptnFactor": "StateCode"}


import _regress  # noqa: E402  regression-mode sampling: 104_ sets CF_REGRESSION_SAMPLE; gates run in full

def q(x, places):
    return Decimal(str(x)).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def rows(book, name, juris):
    """(declared-by, rows for this state or CW) -- the lookup is state first, then CW."""
    try:
        t = book.table(name)
    except Exception:
        return None, []
    if t is None or t.is_empty:
        return book.declares(name), []
    i = t.col("StateCode")
    mine = [r for r in t.rows if str(r[i]) == juris]
    return book.declares(name), [dict(zip(t.definition.header, r)) for r in (mine or [r for r in t.rows if str(r[i]) == "CW"])]


def states():
    res = CFEditionResolver()
    return res, [j for j in sorted(res.jurisdictions) if j != "PR"]


def territory_plan(book, juris):
    """One territory per tier, with that tier's PY3 / Full loss cost, NBC and fire factors."""
    _, tiers = rows(book, "TerrorismTerritoryTier", juris)
    _, lc = rows(book, "TerrorismLossCost", juris)
    _, nbc = rows(book, "TerrorismNBCExclFactor", juris)
    decl_fire, fire = rows(book, "TerrorismFireExcptnFactor", juris)
    by_tier = {}
    for r in tiers:
        by_tier.setdefault(int(r["Teir"]), r["TerrorismTerritory"])
    out = []
    for tier, terr in sorted(by_tier.items()):
        py3 = next((r["Rate"] for r in lc if r["Year"] == "Program Year 3" and int(r["TerrorismTerritoryTier"]) == tier), None)
        full = next((r["Rate"] for r in lc if r["Year"] == "Full" and int(r["TerrorismTerritoryTier"]) == tier), None)
        nb = next((r["Factor"] for r in nbc if int(r["TerrorismTerritoryTier"]) == tier), None)
        fi = next((r["Factor"] for r in fire if int(r["TerrorismTerritoryTier"]) == tier), None)
        blank = lambda v: None if v is None or str(v).strip() == "" else v    # a filed-but-empty cell
        out.append(dict(tier=tier, territory=terr, py3=blank(py3), full=blank(full), nbc=blank(nb), fire=blank(fi)))
    return out, len(tiers), bool(fire)


def lcm_row(book, juris):
    _, r = rows(book, "LossCostMultiplier", juris)
    return Decimal(str(r[0]["Factor"])) if r else Decimal(1)


def predict(rate_base, factor, pc, coins, ded, limit=100000):
    rate = q(q(Decimal(str(rate_base)) * LCM, 3) * Decimal(str(factor)), 4)
    x = q(Decimal(limit) / 100 * rate, 4)
    x = q(x * Decimal(str(pc)), 4)
    x = q(x * Decimal(str(coins)), 4)
    return int(q(x * Decimal(str(ded)), 0)), rate


r11.NUMERIC |= {"BasicGroupIRatingTerrFactor"}

#: States whose own rules never charge the post-TRIA "No Exclusion" case although they
#: file a full loss cost -- ISO-confirmed in C13-19 (153_): NY. (FL files no full loss
#: cost at all, so it drops out as "no filed rate".)
NO_POST_TRIA = {"NY"}


def il0953_uses_fire(book):
    """Does this state's SetTRIAExclFactor give IL 09 53 the fire-exception factor
    unconditionally? Read from the rule text in force, not listed by hand: OR, GA, IA ...
    copy it; CT, MA, VA keep CW's 0.0 (their fire tables feed the conditional and
    post-TRIA forms); AZ copies it only when `UnderFourUnits` = Yes (CP 09 01), which the
    golden building is not; NY writes 0.0. All ISO-confirmed in 153_."""
    for content in (book.state.package.content, book.parent.package.content):
        p = content / "Rules" / "CommercialPropertyStructureRules.Rule.xml"
        if not p.exists():
            continue
        m = re.search(r'<rul:Rule Name="SetTRIAExclFactor".*?</rul:Rule>', p.read_text(encoding="utf-8-sig"), re.S)
        if not m:
            continue
        body = m.group(0)
        i = body.find("ExclCertfdActsTerrsmCovFireLosses")
        seg = body[i:body.find("</rul:When>", i)]
        return "TerrorismFireExcptnFactor" in seg and "UnderFourUnits" not in seg
    return False


#: C28-05 / C28-06: states where the portable building sends a blank lookup key ISO refuses (P11 CO, P12 SC live)
ISO_REFUSES = {("CO", "GeographicWindHazardLevel"), ("IN", "GeographicWindHazardLevel"),
               ("OK", "GeographicWindHazardLevel"), ("SC", "BCEGEQFactor")}


def state_sub(juris, territory, **kw):
    """The Oregon building made portable, chunk 8's way: Oregon's building territories
    ("Portland", "Entire State") exist nowhere else, and ISO refuses the lookup where our
    engine tolerates it (OI-103 shape; the first live run was 105 refusals). So the
    territories are removed and the Group I territory factor pinned to 1.0. No terrorism
    input depends on them; each state's own PC, coinsurance and deductible still apply."""
    s = rc3.sub(territory=territory, lcm=int(LCM), **kw)
    cp = s["CommercialPropertyTable"]["CommercialProperty"][0]
    cp["State"] = juris
    loc = cp["CommercialPropertyLocationTable"]["CommercialPropertyLocation"][0]
    loc.pop("BasicGroupIRatingTerr", None)
    loc.pop("BasicGroupIIRatingTerr", None)
    loc["BasicGroupIRatingTerrFactor"] = "1.0"
    return si.localize_group2(s, juris)


def run_case(book_juris, sub):
    data, ip = gc.run(sub, juris=book_juris)
    g = lambda k: gc.read(k, data)
    return {k: g(f"{STRUCT}/{k}") for k in ("ProtectionClassFactor", "CoinsuranceFactor", "DeductibleFactorBasicGroupI",
                                            "TerrorismPremium", "TRIAExclFactor", "TRIAExclusionRate",
                                            "PostTRIAExclusionRate")} | {"PostTRIA": g(PT)}


def rewrites(book, juris):
    """Terrorism premium/rate/factor rules this state's own layer rewrites (not pins)."""
    rd = book.state.package.content / "Rules"
    out = set()
    if not rd.exists():
        return out
    for f in rd.glob("*.xml"):
        if not re.search(r"Structure|Location|PersonalProperty|BusinessIncome|SpecialClass|CommercialPropertyRules|Terror|TRIA", f.name):
            continue
        for m in re.finditer(r'<rul:Rule Name="([^"]+)".*?</rul:Rule>', f.read_text(encoding="utf-8-sig"), re.S):
            n, body = m.group(1), m.group(0)
            if re.search(r"Terror|TRIA", n) and not (len(re.findall("<rul:RunRule", body)) == 1
                                                      and not re.search(r"<rul:(Lookup|Product|Copy|Constant|Choose|If)\b", body)):
                out.add(n)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    res, juris = states()

    # ---------------------------------------------------------------- C13-16 / C13-17
    print(f"C13-16 / C13-17  tables and territories, {len(juris)} states (PR excluded), as of {ASOF}\n")
    print(f"  {'st':3s} {'terr':>4s} {'tiers':>5s} {'LC rows':>7s} {'NBC':>4s} {'SubLim':>6s} {'fire':>4s}  gaps")
    plans, gaps_total = {}, 0
    for j in juris:
        book = book_for(j, ASOF, resolver=res)
        plan, nterr, has_fire = territory_plan(book, j)
        _, lc = rows(book, "TerrorismLossCost", j)
        _, nbc = rows(book, "TerrorismNBCExclFactor", j)
        _, sl = rows(book, "TerrorismSubLimitFactor", j)
        gaps = [f"tier {p['tier']} no " + "/".join(k for k in ("py3", "full", "nbc") if p[k] is None)
                for p in plan if any(p[k] is None for k in ("py3", "full", "nbc"))]
        if not plan:
            gaps.append("no territory rows")
        if not sl:
            gaps.append("no sub-limit rows")
        gaps_total += len(gaps)
        plans[j] = (book, plan, has_fire)
        print(f"  {j:3s} {nterr:4d} {len(plan):5d} {len(lc):7d} {len(nbc):4d} {len(sl):6d} {'yes' if has_fire else '':>4s}  "
              f"{'; '.join(gaps)}")
    print(f"\n  {sum(bool(p[1]) for p in plans.values())} states file territories; "
          f"{sum(p[2] for p in plans.values())} file a fire-exception factor; {gaps_total} gaps")

    # ---------------------------------------------------------------- C13-22 / 18 / 21
    print(f"\nC13-22 / C13-18 / C13-21  every tier of every state, policy LCM {LCM}\n")
    tally = collections.Counter()
    diverge = collections.defaultdict(list)
    live_cases = []
    for j in _regress.sample(juris):
        book, plan, has_fire = plans[j]
        rw = rewrites(book, j)
        fire_953 = il0953_uses_fire(book)
        for p in plan:
            if p["py3"] is None:
                continue
            for case, kw, base, factor, field in (
                    ("in-effect", {}, p["py3"], 1, "TerrorismPremium"),
                    ("declined", {"cert": "No"}, p["py3"],
                     p["fire"] if fire_953 and p["fire"] is not None else 0, "TerrorismPremium"),
                    # the coverage's own post-TRIA premium, before any state 25% cap on the
                    # roll-up (the caps are checked against ISO in 153_)
                    ("post-TRIA", {"tria": rc3.POST, "post": "No Exclusion"}, p["full"],
                     0 if j in NO_POST_TRIA else 1, "TerrorismPremium")):
                if base is None:
                    tally[(case, "no filed rate")] += 1
                    continue
                if case == "declined" and not has_fire and p["tier"] != plan[0]["tier"]:
                    continue                              # CW states: one declined case is enough
                sub = state_sub(j, p["territory"], **kw)
                try:
                    got = run_case(j, sub)
                except InterpretError as exc:
                    if (j, _iso.table_of(exc)) in ISO_REFUSES and str(exc).count("''") >= 1:
                        # C28-05: the portable building's blank key refuses, as ISO does (C28-06 P11 CO, P12 SC live)
                        tally[(case, "refused as ISO does")] += 1
                        continue
                    tally[(case, "RAISED")] += 1
                    diverge[j].append(f"{case} tier {p['tier']}: RAISED {str(exc)[:80]}")
                    continue
                if got["ProtectionClassFactor"] is None:
                    tally[(case, "no building factors")] += 1
                    diverge[j].append(f"{case} tier {p['tier']}: building factors absent")
                    continue
                want, rate = predict(base, factor, got["ProtectionClassFactor"], got["CoinsuranceFactor"],
                                     got["DeductibleFactorBasicGroupI"])
                have = got["PostTRIA"] if field == "PostTRIA" else got["TerrorismPremium"]
                ok = gc.num_eq(have if have is not None else 0, want)
                tally[(case, "ok" if ok else "DIFFERS")] += 1
                if not ok:
                    diverge[j].append(f"{case} tier {p['tier']} ({p['territory'][:28]}): predicted ${want} "
                                      f"(rate {rate}), engine ${have}; rewrites: {sorted(rw)[:5]}")
                elif a.verbose:
                    print(f"  {j} {case:9s} tier {p['tier']} ${want}")
                live_cases.append((j, case, p["tier"], sub, want, field))
    for (case, verdict), n in sorted(tally.items()):
        print(f"  {case:10s} {verdict:20s} {n}")
    print(f"\n  states with a divergence from their own rows: {len(diverge)}")
    for j, lines in sorted(diverge.items()):
        for ln in lines[:4]:
            print(f"    {j}  {ln}")
        if len(lines) > 4:
            print(f"    {j}  ... {len(lines) - 4} more")

    if a.live:
        import raas as raas_mod
        client = raas_mod.RaaS()
        print("\nISO live, one in-effect and one post-TRIA case per state (lowest tier):")
        seen, agree, refused, differ = set(), 0, 0, []
        for j, case, tier, sub, want, field in live_cases:
            if (j, case) in seen or case == "declined" and not plans[j][2]:
                continue
            seen.add((j, case))
            req = r11.payload(sub)
            for cp in req["body"]["CommercialProperty"]:
                cp["State"] = j
            req["body"]["SchemeKeys"]["ProductName"] = r11.PRODUCT.format(state=j)
            try:
                resp = client.rate(req)
            except raas_mod.RaaSError as exc:
                refused += 1
                m = re.search(r"Matrix: (\w+).*?Keys: ([^.]*)", str(exc.body)) or re.search(r'"Message":"([^"]{0,120})', str(exc.body))
                print(f"  {j} {case:9s} ISO REFUSES {m.group(0)[:110] if m else ''}")
                continue
            (gc.OUT / f"chunk13_rc4_{j}_{case}_response.json").write_text(json.dumps(resp, indent=2), encoding="utf-8")
            st, eff, ours = rp.replay(req, None)
            iso = rp.iso_fields(resp)
            d = [(k, v, ours.get(k)) for k, v in iso.items() if rp.num(v) != rp.num(ours.get(k))
                 and not (rp.num(v) in (None, 0.0) and rp.num(ours.get(k)) in (None, 0.0))]
            if d:
                differ.append((j, case, d))
            else:
                agree += 1
        for j, case, d in differ:
            print(f"  {j} {case:9s} DIFFER " + "; ".join(f"{k[-50:]} ISO {v} ours {o}" for k, v, o in d[:3]))
        print(f"\n  live: {agree} agree field for field, {len(differ)} differ, {refused} refused")
    bad = sum(n for (case, verdict), n in tally.items() if verdict in ("DIFFERS", "RAISED", "no building factors"))
    print(f"\nC13-22 {'CLEAN' if not bad else 'FAIL'}: {bad} case(s) differ from the state's own rows and rules")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
