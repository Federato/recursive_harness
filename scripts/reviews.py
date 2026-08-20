"""Per-run review records: what needs a person's attention, and what they said.

    import reviews
    reviews.load(run_file)                 # the stored record, or {}
    reviews.build_findings(run_file)       # every DIFF/PREMIUM ONLY/refusal row,
                                            # pattern-matched, merged with anything
                                            # already posted
    reviews.generate_brief(run_file, key)  # a markdown brief for one finding,
                                            # stored and returned
    reviews.post_analysis(run_file, key, text)

One JSON file per run file, same stem: `results/reviews/L3-91340-....json` sits
beside `results/runs/L3-91340-....html`. **Only the human-authored parts are
persisted** -- a finding's status, its pattern match, the row data behind it are
all recomputed fresh from the store on every read, never stored. Two numbers of
the same thing drifting apart is a mistake this project has made and fixed
before (`runstore.spent_today`, Entry 29); a review record that could go stale
against the store it describes would be the same mistake in a new place.

**No API key, anywhere in this file.** The first pass -- `pattern_match` -- is
mechanical: it reuses `qa_review.classify` to sort a refusal into a question for
ISO or a problem in our own environment, and it checks whether this exact
finding (same jurisdiction, same status, same differing fields) has already
been explained in a prior review. Nothing here guesses at *why* a number
differs. What it can't explain gets `generate_brief`, a markdown document meant
to be pasted into a conversation a person is already having -- the same
division of labor `qa_review.py`'s pass 4 already uses: this file assembles the
evidence, a person dispatches it and pastes back what came of it.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEWS = ROOT / "results" / "reviews"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import qa_review as QR                                        # noqa: E402
import runstore as store                                      # noqa: E402

#: A run's rows in these statuses are what a review is about. NOT APPLICABLE is
#: deliberately absent -- it is never a failure anywhere else in this project,
#: and a review page that treated it as one would be the one place that lied
#: about that.
FINDING_STATUSES = ("DIFF", "PREMIUM ONLY", "ENGINE STOPPED", "ENGINE ERROR",
                    "BUILD ERROR", "RAAS FAILED")

REFUSAL_STATUSES = ("ENGINE STOPPED", "ENGINE ERROR", "BUILD ERROR", "RAAS FAILED")


def _path(run_file: str) -> Path:
    return REVIEWS / (Path(run_file).stem + ".json")


def load(run_file: str) -> dict:
    p = _path(run_file)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}


def _save(run_file: str, record: dict) -> None:
    REVIEWS.mkdir(parents=True, exist_ok=True)
    _path(run_file).write_text(json.dumps(record, indent=1, sort_keys=True),
                               encoding="utf-8")


def _run_rows(run_ids: list) -> list:
    """Every row from every scenario in this run, alongside the scenario's own
    description and config -- a run file can bundle many scenarios, and a
    finding needs to say which one it came from."""
    out = []
    for rid in run_ids:
        full = store.run(rid)
        if not full:
            continue
        summ = full.get("summary") or {}
        for row in full.get("rows") or []:
            out.append({"row": row, "describes": summ.get("describes", ""),
                       "config": summ.get("config") or {}})
    return out


def _signature(row: dict) -> tuple:
    """What makes two findings 'the same' for the dedup check. Jurisdiction and
    status alone are too loose -- NY can DIFFER for two unrelated reasons in two
    different runs. The differing field names are the closer match; a refusal's
    reason text stands in for that when there is no field list."""
    diffs = tuple(sorted(d.get("field", "") for d in (row.get("differences") or [])))
    if diffs:
        return (row.get("juris"), row.get("status"), diffs)
    return (row.get("juris"), row.get("status"), str(row.get("detail", ""))[:200])


def _prior_by_signature(exclude_file: str = "") -> dict:
    """Every posted finding across every OTHER review record, keyed by
    signature -- what `build_findings` checks a fresh finding against."""
    out: dict = {}
    if not REVIEWS.is_dir():
        return out
    exclude = Path(exclude_file).stem
    for p in REVIEWS.glob("*.json"):
        if p.stem == exclude:
            continue
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        for f in (rec.get("findings") or {}).values():
            if not f.get("analysis"):
                continue
            # A signature round-tripped through JSON has its inner tuple back
            # as a list, which a dict key cannot be -- rebuild it properly.
            raw = f.get("signature") or []
            sig = tuple(tuple(x) if isinstance(x, list) else x for x in raw)
            if sig and sig not in out:
                out[sig] = {"run_file": rec.get("run_file", p.stem + ".html"),
                           "juris": f.get("juris"),
                           "analysis": f.get("analysis"),
                           "analysis_posted_at": f.get("analysis_posted_at")}
    return out


def pattern_match(row: dict, prior: dict) -> dict | None:
    """A mechanical match only -- never a guess dressed as a finding.

    Three things are checked, all of them re-derivable by someone reading this
    function: is it a refusal, and if so is it ISO's question or ours
    (`qa_review.classify`); did `probe_no_op` already catch this as an inert
    value; and has the exact same finding -- same jurisdiction, same status,
    same differing fields -- already been explained in a different run.
    """
    status = row.get("status")
    if status in REFUSAL_STATUSES:
        kind = QR.classify(str(row.get("detail", "")))
        if kind == QR.ISO_QUESTION:
            return {"kind": "iso_question",
                   "label": "Looks like a question for ISO -- a refusal or a "
                            "real error response, not something in our own "
                            "environment."}
        return {"kind": "local_problem",
               "label": "Traces to our own environment -- a corpus package "
                        "or a harness problem, not ISO's data. Sending this "
                        "to ISO would not help."}
    no_op = row.get("no_op") or {}
    if no_op.get("verdict") == "INERT VALUE":
        return {"kind": "inert_value",
               "label": f"The chosen value doesn't move the premium; "
                        f"{no_op.get('moves_with', 'another declared value')} "
                        f"does. A fact about the harness's pick, not ISO's "
                        f"filing (OI-93's shape)."}
    sig = tuple(_signature(row))
    seen = prior.get(sig)
    if seen:
        return {"kind": "seen_before", "run_file": seen["run_file"],
               "label": f"The same finding was already explained reviewing "
                        f"{seen['run_file']} on "
                        f"{seen['analysis_posted_at'][:10]}.",
               "prior_analysis": seen["analysis"]}
    return None


def build_findings(run_file: str, run_ids: list) -> dict:
    """Every finding in this run, fresh from the store, merged with anything a
    person already posted for it. `run_ids` comes from the caller rather than
    being looked up here -- that lookup lives in `ui/runfile.py`'s index, and
    `scripts/` does not import `ui/` (the one-way dependency this project
    enforces: `ui -> scripts -> gl_engine`, never the reverse).

    Returns `{key: finding}`. Nothing here is written to disk -- `load` and
    `_save` own that, so a page that only wants to read never has to write.
    """
    prior = _prior_by_signature(run_file)
    saved = load(run_file).get("findings") or {}
    findings: dict = {}
    for entry in _run_rows(run_ids):
        row = entry["row"]
        if row.get("status") not in FINDING_STATUSES:
            continue
        key = f"{entry['describes']}|{row.get('juris')}|{row.get('status')}"
        f = {
            "key": key, "juris": row.get("juris"), "status": row.get("status"),
            "config": entry["describes"], "detail": row.get("detail", ""),
            "ours": row.get("ours"), "iso": row.get("iso"), "delta": row.get("delta"),
            "edition_agrees": row.get("edition_agrees"),
            "packages": row.get("packages", ""),
            "differences": row.get("differences") or [],
            "signature": list(_signature(row)),
            "pattern": pattern_match(row, prior),
        }
        # The human-authored parts survive a rebuild; everything else above is
        # recomputed fresh, so a finding can never describe a row that no
        # longer matches what the store actually says.
        prev = saved.get(key) or {}
        f["brief_md"] = prev.get("brief_md")
        f["analysis"] = prev.get("analysis")
        f["analysis_posted_at"] = prev.get("analysis_posted_at")
        findings[key] = f
    return findings


def status(findings: dict) -> str:
    """`clean` (nothing to review) -> `needs_review` (something has neither a
    pattern nor a posted analysis) -> `explained` (every finding is accounted
    for by a mechanical match, a posted analysis, or both) -> `reviewed`
    (every finding has a posted analysis specifically, the strongest claim)."""
    if not findings:
        return "clean"
    if all(f.get("analysis") for f in findings.values()):
        return "reviewed"
    if all(f.get("pattern") or f.get("analysis") for f in findings.values()):
        return "explained"
    return "needs_review"


def quick_status(run_file: str) -> str | None:
    """A cheap status for a table of many runs -- reads only the stored
    record, no store round-trip. `None` means no review record exists yet,
    which the caller reads as "never opened," not "clean" -- only `status()`,
    computed from the live rows, can actually say a run had nothing to review.

    **Deliberately cannot claim "fully reviewed."** The saved record only ever
    holds findings a person actually clicked into -- a pattern-matched finding
    nobody opened a brief for is never written here at all, so a record with
    one posted analysis could still be hiding an unexplained finding this
    function has no way to see without the store round-trip `status()` pays
    for. `has_notes` says a person left something, not that nothing is left.
    """
    findings = load(run_file).get("findings") or {}
    if not findings:
        return None
    if any(f.get("analysis") for f in findings.values()):
        return "has_notes"
    return "pending"


def generate_brief(run_file: str, run_ids: list, key: str) -> str | None:
    """The markdown brief for one finding -- the evidence, nothing invented.

    Stored once generated, so it does not silently change under someone who
    has already started answering it. Regenerate by clearing it first.
    """
    findings = build_findings(run_file, run_ids)
    f = findings.get(key)
    if f is None:
        return None
    record = load(run_file)
    saved = record.setdefault("findings", {})
    if saved.get(key, {}).get("brief_md"):
        return saved[key]["brief_md"]

    lines = [
        f"# Review brief -- {run_file}, {f['juris']}",
        "",
        "## Claim to evaluate",
        (f"Our result for {f['juris']} disagrees with ISO's, and no pattern "
         f"this harness already knows about explains it."
         if f["status"] in ("DIFF", "PREMIUM ONLY") else
         f"Our engine refused this submission in {f['juris']}, and it is not "
         f"clear whether that refusal is correct."),
        "", "## Configuration", f["config"] or "the base risk, unvaried", "",
        "## What we got",
    ]
    if f["status"] in ("DIFF", "PREMIUM ONLY"):
        lines += [f"ours={f['ours']}   iso={f['iso']}   delta={f['delta']}",
                  f"edition_agrees: {f['edition_agrees']}"]
    else:
        lines += [f"status={f['status']}", f"detail: {f['detail']}"]
    lines += [f"packages: {f['packages']}", ""]
    if f["differences"]:
        lines.append("## Fields that differ")
        for d in f["differences"][:12]:
            lines.append(f"- {d.get('field')}: ours={d.get('ours')}  "
                         f"iso={d.get('iso')}")
        if len(f["differences"]) > 12:
            lines.append(f"- ({len(f['differences']) - 12} more -- see the "
                         f"run file for the full list)")
        lines.append("")
    lines += [
        "## Already checked, and ruled out",
        "- Not a NOT APPLICABLE misclassification (that pass only runs on "
        "NOT APPLICABLE rows, and this isn't one)",
        "- Not a known refusal reason, and not an inert-value pick "
        "(`probe_no_op`, OI-93's shape)",
        "- Not the same finding as anything already explained in a prior "
        "review of a different run",
        "",
        "## What would help",
        "Which filed rule governs this field in this jurisdiction, and "
        "whether our reading of it or ISO's is right.",
    ]
    brief_md = "\n".join(lines)
    saved[key] = {**f, "brief_md": brief_md}
    record["run_file"] = run_file
    record["run_ids"] = run_ids
    record["generated_at"] = record.get("generated_at") or time.strftime(
        "%Y-%m-%dT%H:%M:%S")
    _save(run_file, record)
    return brief_md


def post_analysis(run_file: str, run_ids: list, key: str, text: str) -> bool:
    """Store what a person said, verbatim. Not re-parsed, not treated as a
    verdict -- a record of an answer given once, not a fact about the run."""
    findings = build_findings(run_file, run_ids)
    if key not in findings:
        return False
    record = load(run_file)
    saved = record.setdefault("findings", {})
    entry = {**findings[key], **saved.get(key, {})}
    entry["analysis"] = text
    entry["analysis_posted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    saved[key] = entry
    record["run_file"] = run_file
    record["run_ids"] = run_ids
    _save(run_file, record)
    return True


def clear_analysis(run_file: str, key: str) -> bool:
    record = load(run_file)
    saved = record.get("findings") or {}
    if key not in saved:
        return False
    saved[key]["analysis"] = None
    saved[key]["analysis_posted_at"] = None
    _save(run_file, record)
    return True
