"""OI-95: is the three-way ELP regime split stable across every jurisdiction and edition?

The finding, measured once (Texas, GL_TX 20250801 V01, 2026-08-19): `PremOpsELPText.RateTable.csv`
declares one of three values per class -- `Rate/Loss Cost Applies`, `Industry`, `Company` -- and
cross-tabulated against `PremOpsELP.RateTable.csv` it is exact with zero exceptions: `Rate/Loss Cost
Applies` always carries a zero ELP, `Industry` always carries a non-zero ELP, `Company` always
carries a zero ELP. 68 + 110 = 178, the exact count of `(a)` classes OI-95 was raised about.

That measurement is one state, one edition. This is the same generalisation error OI-68 and OI-04
were both about, and habit 9 (2026-08-19, Build Plan section 9) exists because OI-95's own escalation
sat unresolved for two days while the discriminator was sitting in a directory nobody had opened.
So before any engine branch is written on the strength of the Texas reading, this measures:

  Q1  Does every jurisdiction that files `*ELPText` carry the same three (or four, on the products
      side) values, and does the zero/nonzero pairing hold with no exceptions everywhere?
  Q2  Is the category assigned to a given class code stable across editions of the same
      jurisdiction, or does a class migrate between regimes as the corpus ages?
  Q3  Does the products side (`ProdsCompldOpsELPText` / `ProdsCompldOpsELPFactor`, which declares a
      fourth value, `Not Applicable`) show the same zero/nonzero pairing?

This script measures, and decides nothing. Emits out/oi95_elp_regimes.txt.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
c = import_module("00_common")

PAIRS = [
    ("PremOps", "PremOpsELPText.RateTable.csv", "PremOpsELP.RateTable.csv",
     "ClassCodeCGLProds", "PremOpsELP", "Rate"),
    ("ProdsCompldOps", "ProdsCompldOpsELPText.RateTable.csv",
     "ProdsCompldOpsELPFactor.RateTable.csv",
     "ClassCodeCGLProds", "ProdsCompldOpsELP", "Rate"),
]


def _is_zero(v: str) -> bool:
    try:
        return float(v) == 0.0
    except ValueError:
        return v.strip() in ("", "0")


def main() -> int:
    packages = c.find_packages()
    lines: list[str] = []
    lines.append("OI-95 -- ELP regime split, measured across every jurisdiction and edition")
    lines.append(f"packages enumerated: {len(packages)}")
    lines.append("")

    # side -> (juris, category) -> Counter(zero/nonzero)
    pairing: dict[str, dict[tuple, Counter]] = {side: defaultdict(Counter) for side, *_ in PAIRS}
    # side -> exceptions: list of (pkg_id, class_code, category, rate)
    exceptions: dict[str, list] = {side: [] for side, *_ in PAIRS}
    # side -> juris -> class_code -> set(category seen across editions)
    drift: dict[str, dict] = {side: defaultdict(lambda: defaultdict(set)) for side, *_ in PAIRS}
    # side -> juris -> set(editions seen with the table)
    coverage: dict[str, dict] = {side: defaultdict(set) for side, *_ in PAIRS}

    for pkg in packages:
        if not pkg.name_ok:
            continue
        rate_dir = pkg.content / "Rate Tables"
        if not rate_dir.is_dir():
            continue
        for side, text_name, rate_name, key_col, text_col, rate_col in PAIRS:
            text_path = rate_dir / text_name
            rate_path = rate_dir / rate_name
            if not text_path.is_file() or not rate_path.is_file():
                continue
            try:
                th, trows = c.read_csv_rows(text_path)
                rh, rrows = c.read_csv_rows(rate_path)
            except Exception as exc:
                lines.append(f"  READ ERROR {pkg.pkg_id} {side}: {exc}")
                continue
            if key_col not in th or text_col not in th:
                continue
            ti = th.index(key_col)
            tci = th.index(text_col)
            text_map = {row[ti]: row[tci] for row in trows if len(row) > max(ti, tci)}
            if key_col not in rh or rate_col not in rh:
                continue
            ri = rh.index(key_col)
            rci = rh.index(rate_col)
            rate_map = {row[ri]: row[rci] for row in rrows if len(row) > max(ri, rci)}

            coverage[side][pkg.juris].add(pkg.edition)
            for class_code, category in text_map.items():
                rate = rate_map.get(class_code)
                if rate is None:
                    continue
                zero = _is_zero(rate)
                pairing[side][(pkg.juris, category)][("zero" if zero else "nonzero")] += 1
                drift[side][pkg.juris][class_code].add(category)

                expected_zero = category in ("Rate/Loss Cost Applies", "Company")
                expected_nonzero = category == "Industry"
                if (expected_zero and not zero) or (expected_nonzero and zero):
                    exceptions[side].append((pkg.pkg_id, class_code, category, rate))
                if category not in ("Rate/Loss Cost Applies", "Industry", "Company",
                                     "Not Applicable"):
                    exceptions[side].append(
                        (pkg.pkg_id, class_code, f"UNKNOWN CATEGORY: {category!r}", rate))

    for side, *_ in PAIRS:
        lines.append(f"--- {side} ---")
        lines.append(f"jurisdictions filing this table: {len(coverage[side])} of {len(packages) and len({p.juris for p in packages if p.name_ok})}")
        for juris in sorted(coverage[side]):
            lines.append(f"  {juris}: {len(coverage[side][juris])} editions carry the table")
        lines.append("")
        lines.append("Q1 -- zero/nonzero pairing, by category, summed across every package:")
        totals: Counter = Counter()
        for (juris, category), counter in pairing[side].items():
            for k, v in counter.items():
                totals[(category, k)] += v
        for category in sorted({cat for cat, _ in totals}):
            zero = totals[(category, "zero")]
            nonzero = totals[(category, "nonzero")]
            lines.append(f"  {category:28s} zero={zero:6d}  nonzero={nonzero:6d}")
        lines.append(f"  EXCEPTIONS to the expected pairing: {len(exceptions[side])}")
        for pkg_id, class_code, category, rate in exceptions[side][:50]:
            lines.append(f"    {pkg_id}  class={class_code}  category={category}  rate={rate}")
        lines.append("")

        lines.append("Q2 -- classes whose category changes across editions of the same jurisdiction:")
        drift_count = 0
        for juris, classmap in drift[side].items():
            for class_code, cats in classmap.items():
                if len(cats) > 1:
                    drift_count += 1
                    if drift_count <= 50:
                        lines.append(f"    {juris} class={class_code}  categories seen: {sorted(cats)}")
        lines.append(f"  total classes with more than one category across editions: {drift_count}")
        lines.append("")

    out = c.OUT / "oi95_elp_regimes.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
