#!/usr/bin/env python
"""Smoke test for the ISO Circular Expert knowledge base and retrieval tool.

Each case asserts a fact independently verified against the source PDFs, so a failure
means the knowledge base or the extractor has drifted -- not that the test is stale.

    python smoke_test.py
"""
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.join(HERE, "iso.py")


def run(*args):
    r = subprocess.run([sys.executable, ISO, *args], capture_output=True, timeout=900)
    if r.returncode != 0:
        raise AssertionError(r.stderr.decode("utf-8", "replace")[:400])
    return json.loads(r.stdout.decode("utf-8", "replace"))


CASES = []


def case(name):
    def deco(fn):
        CASES.append((name, fn))
        return fn
    return deco


@case("ZIP resolves to a territory with a citation")
def _():
    d = run("territory", "NJ", "--zip", "07030")
    assert d["scheme"] == "ZIP_TABLE", d["scheme"]
    assert d["count"] == 15, d["count"]
    lk = d["lookup"]
    assert lk["territory"] == "504" and lk["usps_name"] == "HOBOKEN", lk
    assert lk["notice"].startswith("GL-NJ-") and lk["page"] > 0, lk


@case("county/city jurisdictions refuse a ZIP lookup rather than guessing")
def _():
    for st in ("CA", "FL", "NY", "TX"):
        d = run("territory", st, "--zip", "90001")
        assert d["scheme"] == "COUNTY_CITY", (st, d["scheme"])
        assert d["lookup"]["resolved"] is None, (st, d["lookup"])


@case("territory applies to 334/332 only; 335/336/350 are statewide")
def _():
    d = run("territory", "NJ")
    assert d["territorial_sublines"] == ["334", "332"], d
    assert d["statewide_sublines"] == ["335", "336", "350"], d


@case("published loss cost is returned pre-LCM, per territory")
def _():
    d = run("rate", "TX", "--class", "10010")
    r = d["loss_cost_rows"][0]
    assert r["territory"] == "001" and r["prem_ops"] == ".188", r
    assert "pre-LCM" in r["prem_ops_meaning"], r
    assert len(d["loss_cost_rows"]) == 8, len(d["loss_cost_rows"])


@case("'(a)' decodes to REFER, never to zero")
def _():
    d = run("rate", "TX", "--class", "91581")
    r = d["loss_cost_rows"][0]
    assert r["prem_ops"] == "(a)" and "REFER" in r["prem_ops_meaning"], r


@case("CW Rule 56.B verbatim is retrievable from the countrywide base")
def _():
    d = run("grep", "increased limits tables are displayed", "--kind", "RU", "--max", "1")
    assert d["hits"] >= 1, d
    hit = d["results"][0]
    assert hit["notice"].startswith("GL-MU-"), hit
    assert "state exceptions" in hit["excerpt"], hit


@case("state exception text is retrievable by rule number")
def _():
    d = run("rule", "45", "--st", "TX", "--max", "1")
    assert d["hits"] >= 1, d
    assert "LIQUOR" in d["results"][0]["excerpt"].upper(), d


@case("both streams resolve independently at an effective date")
def _():
    d = run("effective", "NJ", "--date", "2026-06-01")
    assert d["rules"]["in_force"] and d["losscosts"]["in_force"], d
    assert "INV-THREE-STREAMS" in d["warning"], d


@case("circular resolves to its filings and ERC editions")
def _():
    d = run("circular", "LI-GL-2022-325")
    assert d["type"] == "LOSS COST", d["type"]
    assert "GL-2022-BGL1" in d["filings"], d["filings"]
    assert d["states"] == ["AK"], d["states"]


@case("notice metadata carries date confidence")
def _():
    d = run("notice", "GL-NJ-2026-RU-001")
    assert d["kind"] == "RU" and d["st"] == "NJ", d
    assert d["date_confidence"], d
    assert d["text_pages"] > 0, d


@case("invariant checklist is loaded and severity-filterable")
def _():
    d = run("invariant", "--severity", "BLOCKER")
    assert d["count"] >= 12, d["count"]
    ids = {e["id"] for e in d["invariants"]}
    for req in ("INV-CELL-ALPHABET", "INV-TERRITORY-SCHEME",
                "INV-VINTAGE-SPLIT", "INV-RULE-KEY"):
        assert req in ids, req
    for e in d["invariants"]:
        assert e["evidence"] and e["doc"], e["id"]


@case("rate vintage split is 15 pre-2027 / 36 on the 2027 basis IN THE END STATE")
def _():
    # This is the LATEST notice per jurisdiction, so it describes the end state, not
    # now (RECONCILIATION.md 1, OI-40). Measured as-of a date on the ERC corpus, the
    # split today is 51/0 and it becomes 8/43 on 2027-04-01. The assertion below is a
    # fact about this notice corpus and stays; only the claim it licenses is dated.
    J = json.load(open(os.path.join(HERE, "..", "knowledge", "jurisdictions.json"),
                       encoding="utf-8"))
    pre = [s for s, v in J.items() if v["rates"]["vintage"] == "PRE_2027"]
    assert len(pre) == 15 and len(J) == 51, (len(pre), len(J))
    ocp = [s for s, v in J.items() if v["rates"]["ocp_loss_costs_published"]]
    assert sorted(ocp) == sorted(pre), "OCP publication must track the vintage split"


@case("territory schemes partition all 51 jurisdictions")
def _():
    # 27/4/20 here is derived from the PDF notices; the ERC derivation reaches the
    # same 27/4/20 independently, and OI-40 confirmed the ERC figure is stable at
    # every as-of date. Two corpora, two methods, one answer.
    J = json.load(open(os.path.join(HERE, "..", "knowledge", "jurisdictions.json"),
                       encoding="utf-8"))
    from collections import Counter
    c = Counter(v["territory"]["scheme"] for v in J.values())
    assert c == {"ZIP_TABLE": 27, "COUNTY_CITY": 4, "ENTIRE_STATE": 20}, c


@case("CG-LC page count equals 8*T+1 in every jurisdiction")
def _():
    N = json.load(open(os.path.join(HERE, "..", "knowledge", "notices.json"),
                       encoding="utf-8"))["losscosts"]
    J = json.load(open(os.path.join(HERE, "..", "knowledge", "jurisdictions.json"),
                       encoding="utf-8"))
    for st, v in J.items():
        n = N.get(v["latest_losscost_notice"] + "-C.pdf")
        if n:
            assert n["lc_pages"] == 8 * len(n["territories"]) + 1, (st, n["lc_pages"])


@case("corpus text is present and page-tagged")
def _():
    base = os.path.join(HERE, "..", "text")
    for kind, want in (("rules", 500), ("losscosts", 470)):
        files = [f for f in os.listdir(os.path.join(base, kind)) if f.endswith(".txt")]
        assert len(files) >= want, (kind, len(files))
    p = os.path.join(base, "rules", "GL-NJ-2026-RU-001-C.txt")
    assert "<<<PAGE 27>>>" in open(p, encoding="utf-8").read(), "page tags missing"


@case("the terrorism supplement is ingested, page-tagged and resolvable")
def _():
    base = os.path.join(HERE, "..", "text", "terrorism")
    files = sorted(f for f in os.listdir(base) if f.endswith(".txt"))
    assert len(files) == 3, files
    t = open(os.path.join(base, "GL-MU-2022-TERXV-001-C.txt"),
             encoding="utf-8").read()
    assert "<<<PAGE 118>>>" in t, "page tags missing or short"
    assert "Multiply the additional premium by 0.58" in " ".join(t.split()), \
        "the NBCR multiplier is not retrievable as printed"
    N = json.load(open(os.path.join(HERE, "..", "knowledge", "notices.json"),
                       encoding="utf-8"))
    assert "terrorism" in N and len(N["terrorism"]) == 3, list(N)


@case("every jurisdiction the terrorism supplement names has a version assignment")
def _():
    K = json.load(open(os.path.join(HERE, "..", "knowledge", "terrorism.json"),
                       encoding="utf-8"))
    a = K["assignments"]
    # 52 = 50 states + DC + Puerto Rico. Hawaii IS one of them and has NO ERC
    # package and no manual notices in this project — see OI-54. A count of 51
    # here would look right and would mean a row was silently dropped.
    assert len(a) == 52, len(a)
    assert "HI" in a and "DC" in a and "PR" in a, sorted(a)
    for st, v in a.items():
        assert v["endorsement_version"].startswith("TEV"), (st, v)
        assert v["premium_version"].startswith("PEV"), (st, v)
    # the countrywide premium version must be the modal one
    from collections import Counter
    modal = Counter(v["premium_version"] for v in a.values()).most_common(1)[0]
    assert modal == ("PEV001", 34), modal


@case("the rating-plan corpora are ingested and routable")
def _():
    base = os.path.join(HERE, "..", "text")
    # 54, not 52: the user supplied `GL-PR-2015-CGLES-001` and the PLAN DOCUMENT
    # itself on 2026-08-12. The plan carries a plain-English filename, so a
    # name-pattern sweep sees it as unparsed while a `*.pdf` sweep sees it fine —
    # the third form of the naming-convention trap this corpus has sprung.
    for slug, want in (("scheduleexperience", 54), ("compositerating", 90)):
        files = [f for f in os.listdir(os.path.join(base, slug))
                 if f.endswith(".txt")]
        assert len(files) == want, (slug, len(files))
    t = open(os.path.join(base, "scheduleexperience",
                          "GL-MU-2023-CGLES-001-C.txt"), encoding="utf-8").read()
    assert "<<<PAGE 18>>>" in t, "page tags missing or short"
    assert "maximum credit or debit" in " ".join(t.split())
    N = json.load(open(os.path.join(HERE, "..", "knowledge", "notices.json"),
                       encoding="utf-8"))
    assert set(N) == {"rules", "losscosts", "terrorism", "scheduleexperience",
                      "compositerating"}, sorted(N)
    assert sum(len(v) for v in N.values()) == 1121, \
        {k: len(v) for k, v in N.items()}
    # Puerto Rico IS covered by the Schedule & Experience plan — by adoption of
    # the multistate version, at the 2-15 edition. It is COMPOSITE RATING that
    # has no PR document, and that asymmetry is the whole of what remains of
    # OI-61.
    assert "GL-PR-2015-CGLES-001-C.pdf" in N["scheduleexperience"]
    assert not [f for f in N["compositerating"] if "-PR-" in f]


@case("Composite Rating is an INTERLINE manual after 2017 — do not search GL- only")
def _():
    base = os.path.join(HERE, "..", "text", "compositerating")
    files = sorted(f for f in os.listdir(base) if f.endswith(".txt"))
    gl = [f for f in files if f.startswith("GL-")]
    il = [f for f in files if f.startswith("IL-")]
    # 39 GL (2007-2012) + 51 IL (2017+). A corpus sweep that assumes every GL
    # document starts `GL-` misses 51 of 90 — which is how the plan came to be
    # recorded as absent from the manual corpus in the first place.
    assert len(gl) == 39 and len(il) == 51, (len(gl), len(il))
    assert len(files) == 90


def main():
    fails = []
    for name, fn in CASES:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as e:
            fails.append((name, e))
            print(f"  FAIL  {name}\n          {type(e).__name__}: {e}")
    print(f"\n{len(CASES)-len(fails)}/{len(CASES)} passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
