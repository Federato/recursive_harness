"""The harness reviewing its own results. Phase 5 of the QA programme.

    python scripts/qa_review.py --tier T1        # review the stored T1 runs
    python scripts/qa_review.py --juris NY       # one jurisdiction

Four passes were proposed. This module holds them as they are built:

    Pass 1  did it exercise anything?   -- BUILT, and it lives in
                                          `variants.probe_no_op`
    Pass 2  is a refusal correct?       -- not built
    Pass 3  is a NOT APPLICABLE real?   -- **this file**
    Pass 4  adversarial agent read      -- **this file**, the brief half

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

### Pass 4, and the line this file will not cross

**A Python script cannot invoke the specialist agents.** They are a capability of
the harness this project is driven from, not a library that can be imported. So
pass 4 is split honestly: **this file assembles the brief** -- the evidence, and
one refutation prompt per agent -- and the operator dispatches them.

Two rules are built into the prompts rather than left to whoever runs them:

* **Each agent is asked to refute, never to confirm.** An agent asked *"is this
  right?"* tends to agree; asked *"find what is wrong with this"* it does real
  work. The prompts state the claim and instruct the reader to break it.
* **Each agent sees only its own source.** `iso-erc-expert`'s own definition
  forbids it from reading the manual expert, because agreement between two
  independently-built corpora is only evidence while they stay independent.
  A brief that handed one agent the other's conclusion would destroy exactly the
  thing it was trying to measure.

**Pass 4 never gates a run.** It is the least deterministic thing in the
programme and it will be wrong sometimes; it generates findings, and a finding
is for a person to weigh.
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




# ---------------------------------------------------- pass 4: the adversarial brief

#: One agent per source, and the source is the point. Each is asked about the
#: thing it alone can see, so three agreements are three independent readings
#: rather than one reading repeated.
REVIEWERS = {
    "gl-authority": (
        "ISO's machine-readable content (ERC), and our code where it must be "
        "compared against it"),
    "iso-circular-expert": (
        "ISO's filed manuals and circulars only"),
    "gl-engine-code-expert": (
        "our Python only -- documentation is explicitly not evidence"),
}


def brief(claim: str, evidence: dict, question: str = "") -> dict:
    """An adversarial brief: the claim, the evidence, one prompt per reviewer.

    `claim` is stated as a **positive assertion the reviewer is asked to
    break**. Phrasing it as a question invites agreement.
    """
    lines = [f"{k}: {v}" for k, v in evidence.items()]
    ev = "\n".join(f"  - {ln}" for ln in lines)
    prompts = {}
    for agent, source in REVIEWERS.items():
        prompts[agent] = (
            f"You are reviewing a claim made by our GL rating engine's QA run. "
            f"**Your job is to REFUTE it**, not to confirm it. Assume it is "
            f"wrong and look for the evidence that it is; say so plainly if you "
            f"cannot find any.\n\n"
            f"THE CLAIM\n  {claim}\n\n"
            f"THE EVIDENCE WE HAVE\n{ev}\n\n"
            f"{('THE SPECIFIC QUESTION' + chr(10) + '  ' + question + chr(10) + chr(10)) if question else ''}"
            f"ANSWER FROM {source.upper()} AND NOTHING ELSE. Do not consult "
            f"another agent's corpus or conclusions -- agreement between "
            f"independently-built sources is only evidence while they stay "
            f"independent, and this review exists to measure that agreement.\n\n"
            f"Report: REFUTED / UPHELD / CANNOT TELL, then the evidence, with a "
            f"citation for every claim. CANNOT TELL is a real answer and is "
            f"better than a guess.")
    return {"claim": claim, "evidence": evidence, "question": question,
            "prompts": prompts}


def briefs_for_run(tier: str = "", limit: int = 60) -> list:
    """A brief for every result in the stored runs that deserves refuting.

    Three kinds qualify, and a clean agreement is deliberately not one of them:
    a disagreement with ISO, an engine refusal, and an `INERT VALUE` -- a
    scenario that rated, reported as tested, and exercised nothing.
    """
    out = []
    for meta in store.runs(limit=limit):
        label = str(meta.get("label") or "")
        if tier and not label.startswith(f"qa {tier}"):
            continue
        if not tier and not label.startswith("qa "):
            continue
        full = store.run(meta["id"]) or {}
        summ = full.get("summary") or {}
        cfg = summ.get("config") or {}
        desc = summ.get("describes") or "the base risk, unvaried"
        for row in full.get("rows") or []:
            juris, status = row.get("juris"), row.get("status")
            ev = {"jurisdiction": juris, "configuration": desc,
                  "our premium": row.get("ours"),
                  "ISO premium": row.get("iso", "not called"),
                  "packages": row.get("packages", ""),
                  "run": meta["id"]}
            if status in ("DIFF", "PREMIUM ONLY"):
                out.append(brief(
                    f"Our premium for {juris} is correct and ISO's differs for "
                    f"a reason we understand.",
                    {**ev, "difference": row.get("delta"),
                     "fields differing": row.get("fields_differing")},
                    "Which of the two is right, and which filed rule decides it?"))
            elif status == "ENGINE STOPPED":
                out.append(brief(
                    f"Our engine is right to refuse this submission in {juris}, "
                    f"and ISO would refuse it too, for the same reason.",
                    {**ev, "our reason": str(row.get("detail", ""))[:300]},
                    "Does ISO's filed content actually leave this unratable, or "
                    "have we refused something ISO prices?"))
            elif (row.get("no_op") or {}).get("verdict") == "INERT VALUE":
                v = row["no_op"]
                out.append(brief(
                    f"The value we chose for {juris} is a legitimate test value "
                    f"even though it moved nothing.",
                    {**ev, "chosen": f"{v.get('column')}={v.get('chosen')}",
                     "would have moved": f"{v.get('moves_with')} -> "
                                         f"{v.get('premium')}"},
                    "Is our chosen value one a real submission would carry, or "
                    "did we test a value ISO files but nobody uses?"))
    return out


def main(argv) -> int:
    ap = argparse.ArgumentParser(
        description="Pass 3: is a NOT APPLICABLE real, or is it ours?")
    ap.add_argument("--tier", default="")
    ap.add_argument("--juris", default="")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--pass4", action="store_true",
                    help="assemble adversarial briefs instead of running pass 3")
    ap.add_argument("--max", type=int, default=3,
                    help="how many briefs to print")
    a = ap.parse_args(argv)

    if a.pass4:
        bs = briefs_for_run(a.tier, a.limit)
        print(f"Pass 4 -- {len(bs)} result(s) worth refuting\n")
        if not bs:
            print("  Nothing to review. A clean agreement is deliberately not\n"
                  "  a brief: there is no claim to break.")
            return 0
        for b in bs[:a.max]:
            print("=" * 74)
            print(f"CLAIM   {b['claim']}")
            for k, v in b["evidence"].items():
                print(f"        {k:18s} {str(v)[:70]}")
            print(f"\n  {len(b['prompts'])} reviewers, each on its own source:")
            for agent in b["prompts"]:
                print(f"    - {agent}")
        if len(bs) > a.max:
            print("=" * 74)
            print(f"  ...and {len(bs) - a.max} more. Raise --max to see them.")
        print("\n  Pass 4 never gates a run. Dispatch these to the agents; a\n"
              "  finding is for a person to weigh.")
        return 0

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
