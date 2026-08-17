"""The harness reviewing its own results. Phase 5 of the QA programme.

    python scripts/qa_review.py --tier T1        # review the stored T1 runs
    python scripts/qa_review.py --juris NY       # one jurisdiction

Four passes were proposed. This module holds them as they are built:

    Pass 1  did it exercise anything?   -- BUILT, and it lives in
                                          `variants.probe_no_op`
    Pass 2  is a refusal correct?       -- not built
    Pass 3  is a NOT APPLICABLE real?   -- **this file**
    Pass 4  adversarial agent read      -- not built

### Why pass 3 was built first, and it is not because it was easiest

**`NOT APPLICABLE` is the only outcome never counted as a failure.** That makes
it the one place a defect can sit indefinitely without moving a number anyone
watches -- and it already did.

On 2026-08-14 the harness reported `NOT APPLICABLE` for terrorism in **twenty
jurisdictions, with a readable reason attached**, and the reason is exactly why
nobody questioned it for three days. It was our own inert `ZipCode` fallback,
not ISO's filing. Terrorism was blocked in **zero** jurisdictions (OI-91).

**A refusal with a well-written explanation is still a refusal, and nothing was
checking the explanation.**

### What "independent" means here, precisely

Re-deriving the same answer with the same code proves nothing. So this pass does
**not** call `variants.build`, `Control.options`, `Declared.values` or
`gl_engine.schema` at all. It reads **ISO's own CSVs out of the resolved
package** -- `Fields.FormField.csv` for the domain a field declares, then
`Domain<name>.DomainTable.csv` for the values in it.

Where it cannot honestly re-derive a refusal it returns **`UNVERIFIED` and says
what would settle it**, rather than returning `CONFIRMED` and meaning
*"I did not check"*. That distinction is the whole value of the pass.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import runstore as store                                       # noqa: E402
import variants as V                                           # noqa: E402
from gl_engine.resolve import EditionResolver, ResolvedBook     # noqa: E402

CONFIRMED = "CONFIRMED"        # ISO's files say the same: a real narrowing
CONTRADICTED = "CONTRADICTED"  # ISO declares it; the refusal is ours -- OI-91's shape
UNVERIFIED = "UNVERIFIED"      # this pass cannot settle it, and says so

FIELD_FILE = Path("Form Fields") / "Fields.FormField.csv"

_BOOKS: dict = {}


def _book(juris: str, asof: str):
    key = (juris, asof)
    if key not in _BOOKS:
        _BOOKS[key] = ResolvedBook(EditionResolver().resolve(juris, asof))
    return _BOOKS[key]


def _rows(path: Path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _declared_domain(book, table: str, column: str) -> str:
    """The domain table a field names, read from ISO's own field CSV.

    State layer first, then the countrywide parent -- the same precedence ISO
    files, derived here rather than borrowed from the engine.
    """
    for layer in (book.state, book.parent):
        if layer is None:
            continue
        for r in _rows(layer.package.content / FIELD_FILE):
            if r.get("TableName") == table and r.get("ColumnName") == column:
                return (r.get("DomainTableName") or "").strip()
    return ""


def _domain_values(book, domain: str) -> tuple:
    """Every value in a domain table, read from the CSV, state layer first."""
    if not domain:
        return ()
    out, seen = [], set()
    for layer in (book.state, book.parent):
        if layer is None:
            continue
        base = layer.package.content / "Domain Tables"
        for name in (f"Domain{domain}", domain):
            for f in (base / f"{name}.DomainTable.csv",):
                for r in _rows(f):
                    v = (r.get("DataValue") or "").strip()
                    if v and v not in seen:
                        seen.add(v)
                        out.append(v)
        if out:
            break                       # a state that files its own governs
    return tuple(out)


def _territories(book) -> int:
    """How many prem/ops territories the jurisdiction files.

    Counted off the loss-cost CSVs' own key values, state layer first, rather
    than asked of the engine -- *"this state declares one territory"* is exactly
    the kind of claim that must not be confirmed by the code that made it.
    """
    for layer in (book.state, book.parent):
        if layer is None:
            continue
        d = layer.package.content / "Rate Tables"
        if not d.is_dir():
            continue
        seen = set()
        for f in d.glob("PremOpsLossCost*.RateTable.csv"):
            rows = _rows(f)
            if not rows:
                continue
            col = next((h for h in rows[0] if "Terr" in h), "")
            if col:
                seen.update(str(r[col]).strip() for r in rows
                            if str(r.get(col, "")).strip())
            else:
                # Split sibling tables carry the territory in the NAME, which
                # is how CA, NJ, OH and NY file theirs -- a reader that only
                # looks for a column reports zero and is confidently wrong.
                stem = f.name.split(".")[0]
                if stem != "PremOpsLossCost":
                    seen.add(stem)
        if seen:
            return len(seen)
    return 0


def review_not_applicable(juris: str, config: dict, reason: str,
                          asof: str = V.DEFAULT_ASOF) -> dict:
    """Was this jurisdiction really unable to express this configuration?

    Returns a verdict per control, and the worst one overall. A single
    `CONTRADICTED` is a finding about **us**.
    """
    book = _book(juris, asof)
    findings = []

    for cid, value in (config or {}).items():
        control = V.BY_ID.get(cid)
        if control is None:
            findings.append({"control": cid, "verdict": UNVERIFIED,
                             "why": "not a declared control"})
            continue

        # a) A value that must appear in a declared domain. Read the domain from
        #    ISO's field CSV and the values from ISO's domain CSV.
        if control.table and control.column:
            domain = _declared_domain(book, control.table, control.column)
            values = _domain_values(book, domain)
            if values:
                if str(value) in values:
                    findings.append({
                        "control": cid, "verdict": CONTRADICTED,
                        "why": f"{juris} DOES declare {value!r} for "
                               f"{control.table}.{control.column} "
                               f"({len(values)} values in {domain}) -- the "
                               f"refusal is ours, not ISO's"})
                else:
                    findings.append({
                        "control": cid, "verdict": CONFIRMED,
                        "why": f"{value!r} is not among the {len(values)} "
                               f"values {juris} declares in {domain}"})
                continue
            findings.append({
                "control": cid, "verdict": UNVERIFIED,
                "why": f"no domain table resolved for {control.table}."
                       f"{control.column}; settled by naming the domain ISO "
                       f"files for it"})
            continue

        # b) Structural refusals. Only the territory cap can be re-derived from
        #    the tables today; the rest are conditions inside an applier and are
        #    reported as unverified rather than waved through.
        if cid == "locations":
            n = _territories(book)
            if n and int(value) > n:
                findings.append({
                    "control": cid, "verdict": CONFIRMED,
                    "why": f"{juris} files {n} prem/ops territory(ies); "
                           f"{value} locations cannot be placed"})
            elif n:
                findings.append({
                    "control": cid, "verdict": CONTRADICTED,
                    "why": f"{juris} files {n} territories, so {value} "
                           f"locations are placeable -- the refusal is ours"})
            else:
                findings.append({
                    "control": cid, "verdict": UNVERIFIED,
                    "why": "could not count territories from the rate tables"})
            continue

        findings.append({
            "control": cid, "verdict": UNVERIFIED,
            "why": f"{cid} is refused by a condition inside an applier, not by "
                   f"a declared domain; settled by re-deriving that condition "
                   f"from ISO's rules"})

    # A NOT APPLICABLE says **at least one** control cannot be expressed here.
    # Every other control in the same configuration being perfectly legal is
    # the normal case, not evidence of anything -- so a single CONFIRMED
    # settles the whole result, and only a configuration where *nothing* is
    # undeclarable is a finding about us.
    #
    # Aggregating worst-first instead produced **20+ false findings on the
    # first run** -- Montana reported as wrongly refusing a 100,000 CSL limit
    # it declares perfectly well, when the real cause was `locations=2` against
    # its single territory. A review pass that cries wolf is worse than no
    # review pass, because the next real finding is read as noise.
    verdicts = [f["verdict"] for f in findings]
    if CONFIRMED in verdicts:
        overall = CONFIRMED
    elif verdicts and all(v == CONTRADICTED for v in verdicts):
        overall = CONTRADICTED
    else:
        overall = UNVERIFIED
    return {"juris": juris, "config": config, "reason": reason,
            "verdict": overall, "findings": findings,
            "cause": next((f for f in findings if f["verdict"] == CONFIRMED),
                          None)}


def review_runs(tier: str = "", juris: str = "", limit: int = 60) -> dict:
    """Every NOT APPLICABLE in the stored runs, re-derived independently."""
    out, counts = [], {CONFIRMED: 0, CONTRADICTED: 0, UNVERIFIED: 0}
    for meta in store.runs(limit=limit):
        label = str(meta.get("label") or "")
        if tier and not label.startswith(f"qa {tier}"):
            continue
        full = store.run(meta["id"]) or {}
        cfg = (full.get("summary") or {}).get("config") or {}
        for row in full.get("rows") or []:
            if row.get("status") != "NOT APPLICABLE":
                continue
            if juris and row.get("juris") != juris:
                continue
            v = review_not_applicable(row["juris"], cfg,
                                      str(row.get("detail", ""))[:160])
            counts[v["verdict"]] += 1
            out.append(v)
    return {"reviewed": len(out), "counts": counts, "results": out}


def main(argv) -> int:
    ap = argparse.ArgumentParser(
        description="Pass 3: is a NOT APPLICABLE real, or is it ours?")
    ap.add_argument("--tier", default="")
    ap.add_argument("--juris", default="")
    ap.add_argument("--limit", type=int, default=60)
    a = ap.parse_args(argv)

    r = review_runs(a.tier, a.juris.upper(), a.limit)
    print("Pass 3 -- every NOT APPLICABLE, re-derived from ISO's own files\n")
    print(f"  reviewed        : {r['reviewed']}")
    print(f"  CONFIRMED       : {r['counts'][CONFIRMED]}   "
          f"ISO's files name the control that cannot be expressed")
    print(f"  CONTRADICTED    : {r['counts'][CONTRADICTED]}   "
          f"ISO declares it; the refusal is OURS")
    print(f"  UNVERIFIED      : {r['counts'][UNVERIFIED]}   "
          f"this pass cannot settle it, and says so")

    bad = [x for x in r["results"] if x["verdict"] == CONTRADICTED]
    if bad:
        print("\n  FINDINGS -- these are about us, not about ISO:")
        for x in bad[:20]:
            print(f"    {x['juris']}  {V.describe(x['config'])[:70]}")
            print(f"        every control in this configuration is declared "
                  f"here; nothing explains the refusal")
    unv = [x for x in r["results"] if x["verdict"] == UNVERIFIED]
    if unv:
        seen = set()
        print("\n  UNVERIFIED -- what would settle each:")
        for x in unv:
            for f in x["findings"]:
                if f["verdict"] == UNVERIFIED and f["why"] not in seen:
                    seen.add(f["why"])
                    print(f"    {f['why'][:104]}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
