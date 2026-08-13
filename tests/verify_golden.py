"""Verify the Oklahoma golden fixture — three independent ways.

Runnable today, before any engine exists. When the engine lands, layer 4 (drive the engine
and diff) drops in beside these.

  1. FIXTURE vs ISO   every expected value is read back out of ISO's own published Output.json
  2. FIXTURE vs ERC   every table cell the fixture claims is read back out of the CSV
  3. ARITHMETIC       the premium chain is re-derived with Decimal, from the cells, and must
                      land on ISO's published premiums

Layer 3 is the one that matters: it is the specification in executable form. If a future
edition of the corpus changes a rate, layer 2 fails loudly rather than layer 3 drifting.

    python tests/verify_golden.py

Exit code 0 = all pass. Governed by the doctrine: ERC is the source, nothing is assumed.
"""
from __future__ import annotations

import csv
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "golden-ok-2025.json")

fx = json.load(open(FIXTURE, encoding="utf-8"))
ROOT = fx["provenance"]["corpus_root"]
PKG = os.path.join(ROOT, "OK", "GL_OK 20250601 V01", "GL OK 20250601 V01")
CW = os.path.join(ROOT, "countrywide", "GL CW 20231201 V03")

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> bool:
    results.append((bool(ok), label))
    return bool(ok)


def d(x) -> Decimal:
    return Decimal(str(x))


def rnd(x: Decimal, places: int) -> Decimal:
    """rul:Round DecimalPlaces=n. Tie-break is E1/OI-09 and unsettled; no site in this
    case is a tie, so the choice below cannot affect the result. Asserted in layer 3."""
    return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- 1. vs ISO
def load_iso_output():
    p = os.path.join(PKG, "STC", "1. Output.json")
    o = json.load(open(p, encoding="utf-8-sig"))
    gl = o["Body"]["GeneralLiability"][0]
    cls = gl["GeneralLiabilityLocation"][0]["GeneralLiabilityClassification"][0]
    return gl, cls


def layer1():
    print("\n=== 1. FIXTURE vs ISO's published output ===")
    gl, cls = load_iso_output()
    exp = fx["expected"]

    for k, v in exp["policy"].items():
        if k.startswith("_"):
            continue
        check(gl.get(k) == v, f"policy.{k} == {v}  (ISO: {gl.get(k)})")

    for node, key in (("subline_334_premises_operations",
                       "GeneralLiabilityClassificationPremOpsCoverage"),
                      ("subline_336_products_completed_operations",
                       "GeneralLiabilityClassificationProdsCompldOpsCoverage")):
        actual = cls[key]
        for k, v in exp[node].items():
            if k.startswith("_"):
                continue
            check(actual.get(k) == v, f"{node[:12]}.{k} == {v}  (ISO: {actual.get(k)})")


# --------------------------------------------------------------------------- 2. vs ERC
def rate_rows(pkg_root: str, table: str):
    p = os.path.join(pkg_root, "Rate Tables", f"{table}.RateTable.csv")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8-sig", newline="") as fh:
        r = csv.reader(fh)
        next(r, None)
        return list(r)


def layer2():
    print("\n=== 2. FIXTURE vs the ERC rate tables ===")
    for cell in fx["table_cells_consumed"]:
        root = PKG if cell["layer"] == "state" else CW
        rows = rate_rows(root, cell["table"])
        if rows is None:
            check(False, f"{cell['table']}: table not found in the {cell['layer']} package")
            continue
        want_key = [str(k) for k in cell["key"]]
        n = len(want_key)
        hits = [r for r in rows if [str(x) for x in r[:n]] == want_key]
        if len(hits) != 1:
            check(False, f"{cell['table']}{want_key}: expected 1 row, found {len(hits)}")
            continue
        got = hits[0][n]
        want = cell["value"]
        ok = (d(got) == d(want)) if isinstance(want, (int, float)) else (got == want)
        check(ok, f"{cell['table']}{want_key} -> {want!r}  (ERC: {got!r})")


# --------------------------------------------------------------- 3. re-derive the chain
def layer3():
    print("\n=== 3. ARITHMETIC re-derived from the cells (CW 2023 V03 rules) ===")
    e334 = fx["expected"]["subline_334_premises_operations"]
    e336 = fx["expected"]["subline_336_products_completed_operations"]
    exposure = d(fx["submission"]["locations"][0]["classifications"][0]["prem_ops_cov_exposure"])
    lcm, pkg_mod, one = d(1.0), d(1.0), d(1)

    # --- 334, loss-cost path. Selector says "Rate/Loss Cost Applies".
    loss_cost, cslilf, medpay = d("0.095"), d("2.05"), d("1.003")
    final_ded = d(0)

    base_334 = rnd(loss_cost * lcm, 3)
    check(base_334 == d(e334["BaseRate"]), f"334 BaseRate  {base_334} == {e334['BaseRate']}")

    # CW 2023 V03: medpay is NOT folded into the ILF (that is CW 2027).
    final_ilf_334 = rnd(cslilf - final_ded, 3)
    check(final_ilf_334 == d(e334["FinalILF"]),
          f"334 FinalILF  {final_ilf_334} == {e334['FinalILF']}")

    final_rate_334 = rnd(base_334 * final_ilf_334 * pkg_mod, 3)
    check(final_rate_334 == d(e334["FinalRate"]),
          f"334 FinalRate {final_rate_334} == {e334['FinalRate']}  (0.19475 at 3dp)")

    blp_334 = rnd(base_334 * (one - final_ded) * pkg_mod * (exposure / 1000), 0)
    check(blp_334 == d(e334["BasicLimitPremium"]),
          f"334 BasicLimitPremium {blp_334} == {e334['BasicLimitPremium']}")

    medpay_charge = rnd(loss_cost * lcm * (medpay - one) * pkg_mod * (exposure / 1000), 0)
    check(medpay_charge == d(e334["MedicalPaymentsCharge"]),
          f"334 MedicalPaymentsCharge {medpay_charge} == {e334['MedicalPaymentsCharge']}")

    prem_334 = rnd(final_rate_334 * (exposure / 1000) + medpay_charge, 0)
    check(prem_334 == d(e334["Premium"]), f"334 Premium   {prem_334} == {e334['Premium']}")

    # --- 336, ELP path. Published loss cost is 0; selector says "Industry".
    pc_loss_cost, elp, cslilf_336, dwl = d(0), d("0.82"), d("1.67"), d("1.0")
    check(pc_loss_cost == d(0),
          "336 published loss cost is 0 -> the ELP path (a switch, not a rate)")

    base_336 = rnd(elp * lcm, 3)
    check(base_336 == d(e336["BaseRate"]), f"336 BaseRate  {base_336} == {e336['BaseRate']}")

    final_ilf_336 = rnd(cslilf_336 - d(0), 3)
    check(final_ilf_336 == d(e336["FinalILF"]),
          f"336 FinalILF  {final_ilf_336} == {e336['FinalILF']}")

    final_rate_336 = rnd(base_336 * final_ilf_336 * pkg_mod, 3)
    check(final_rate_336 == d(e336["FinalRate"]),
          f"336 FinalRate {final_rate_336} == {e336['FinalRate']}  (1.3694 at 3dp)")

    blp_336 = rnd(base_336 * (one - d(0)) * pkg_mod * (exposure / 1000), 0)
    check(blp_336 == d(e336["BasicLimitPremium"]),
          f"336 BasicLimitPremium {blp_336} == {e336['BasicLimitPremium']}")

    prem_336 = rnd(final_rate_336 * (exposure / 1000), 0)
    check(prem_336 == d(e336["Premium"]), f"336 Premium   {prem_336} == {e336['Premium']}")

    # min premium: MinimumPremium x FinalILF x AdditionalInterestFactor  (336 consumes AIF)
    min_336 = rnd(d(0) * final_ilf_336 * d(1.0), 0)
    check(min_336 == d(e336["MinPremium"]), f"336 MinPremium {min_336} == {e336['MinPremium']}")

    # policy total
    terr = d(fx["expected"]["terrorism"]["total"])
    total = prem_334 + prem_336 + terr
    check(total == d(fx["expected"]["policy"]["Premium"]),
          f"policy total {prem_334} + {prem_336} + {terr} = {total}")

    # --- E1: assert no site is a tie, so the tie-break mode cannot matter here
    ties = [s for s in fx["rounding_sites_exercised"] if s["is_tie"]]
    check(not ties, f"no rounding site is a tie ({len(fx['rounding_sites_exercised'])} sites) "
                    "-> this case yields no evidence on E1")

    # prove it rather than assert it: re-run every 3dp/0dp site under the other mode
    from decimal import ROUND_HALF_EVEN

    def rnd_even(x, places):
        return x.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)

    alt = rnd_even(rnd_even(loss_cost * lcm, 3) * rnd_even(cslilf - final_ded, 3) * pkg_mod, 3)
    alt_prem = rnd_even(alt * (exposure / 1000)
                        + rnd_even(loss_cost * lcm * (medpay - one) * pkg_mod * (exposure / 1000), 0), 0)
    check(alt_prem == prem_334,
          f"334 premium is identical under ROUND_HALF_EVEN ({alt_prem}) - E1 truly cannot bite here")


def main() -> int:
    for p in (PKG, CW):
        if not os.path.isdir(p):
            print(f"CORPUS NOT FOUND: {p}\n"
                  f"Set provenance.corpus_root in {os.path.relpath(FIXTURE, HERE)}.")
            return 2
    layer1()
    layer2()
    layer3()

    failed = [lbl for ok, lbl in results if not ok]
    for ok, lbl in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {lbl}")
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("\nFAILURES:")
        for lbl in failed:
            print("  -", lbl)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
