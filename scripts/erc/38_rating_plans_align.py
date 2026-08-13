"""Build-order item 10 — Rating plans. PDF and ERC, differentially.

Closes OI-01 (Schedule Rating), OI-02 (Experience Rating) and OI-03 (Composite
Rating), all three of which were `PARTIAL` only because the manual side of the
project had no copy of the plans. It had them all along — they were on disk and
outside the expert agent's corpus (OI-55).

Three populations, enumerated before anything is classified:

  1. MANUAL DOCUMENTS  — every pdf in the two folders, by jurisdiction and
     edition, so "the plan is filed for N states" is a count and not an
     impression.
  2. ERC APPARATUS     — the rules and tables that implement the three plans,
     found by reading rule names and bodies, never by folder or file name.
  3. THE NUMBERS       — the manual's Table 9 schedule-rating ranges against
     ERC's domain tables, cell for cell.

    python 38_rating_plans_align.py 20260812 [--verbose]

Exit code 1 if any assertion fails.
"""
from __future__ import annotations

import glob
import importlib.util
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "asof", os.path.join(HERE, "32_asof_recount.py"))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

PROJ = os.path.dirname(os.path.dirname(HERE))
MANUALS = os.path.join(PROJ, "Commercial Line Manuals", "GL")
TEXT = os.path.join(PROJ, "Agentic", "iso-circular-expert", "text")
RULE = re.compile(
    r'<rul:Rule Name="([^"]+)"[^>]*?DataDefGroup="([^"]+)"[^>]*>(.*?)</rul:Rule>',
    re.S)

# The manual's Rule 9 Table 9, transcribed from GL-MU-2023-CGLES-001 p.10.
# Each range is +/- n%, and a domain enumerated in 1% steps must therefore have
# exactly 2n+1 rows. Stating the RANGE rather than the row count is the point:
# the row count is what ERC must be checked against, not what we assumed.
TABLE_9 = {
    "LocationExposureInsidePremises": 5,
    "LocationExposureOutsidePremises": 5,
    "Premises": 10,
    "Equipment": 10,
    "Classification": 10,
    "Employees": 6,
    "CooperationMedicalFacilities": 2,
    "CooperationSafetyProgram": 2,
}
MAX_CREDIT_DEBIT = 25

failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}\n         {detail}")
    if not ok:
        failures.append(name)


def manual_family(folder: str) -> dict[str, list[tuple[str, str, str]]]:
    """-> jurisdiction -> [(line prefix, year, filename)]."""
    out: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    d = os.path.join(MANUALS, folder)
    for f in sorted(os.listdir(d)):
        if not f.lower().endswith(".pdf"):
            continue
        m = re.match(r'^([A-Z]{2})-([A-Z]{2})-(\d{4})-', f)
        if m:
            out[m.group(2)].append((m.group(1), m.group(3), f))
    return dict(out)


def main() -> int:
    asof = next((a for a in sys.argv[1:] if len(a) == 8 and a.isdigit()), None)
    verbose = "--verbose" in sys.argv
    if not asof:
        print(__doc__)
        print("ERROR: an as-of date is REQUIRED (N4).", file=sys.stderr)
        return 2

    pk = A.discover()
    resolved = {j: r for j in pk if j != "CW"
                for r in [A.resolve(pk[j], asof)] if r}
    cw = {p: c for _e, p, _x, c in pk["CW"]}
    print(f"rating plans as of {asof}: {len(resolved)} ERC jurisdictions, "
          f"{len(cw)} countrywide packages\n")

    # ---- 1. the manual corpora, enumerated
    ses = manual_family("Schedule & Experience Rating")
    crp = manual_family("Composite Rating")
    n_ses = sum(len(v) for v in ses.values())
    n_crp = sum(len(v) for v in crp.values())
    print(f"manual corpora: Schedule & Experience {n_ses} documents / "
          f"{len(ses)} jurisdiction codes · Composite {n_crp} / {len(crp)}")

    # every ERC jurisdiction should have a schedule/experience plan filed
    erc_j = set(resolved)
    missing = sorted(erc_j - set(ses))
    extra = sorted(set(ses) - erc_j - {"MU"})
    # UPDATED 2026-08-12, second half of the day: the user supplied
    # `GL-PR-2015-CGLES-001` and the countrywide plan document itself, and this
    # check failed — correctly. Puerto Rico IS covered by the Schedule &
    # Experience plan; its notice is a pure ADOPTION of the multistate plan
    # ("There are no new or revised manual pages associated with this Notice"),
    # at the 2-15 edition rather than the 2023 one every other state carries.
    # **Composite Rating still has no PR document.** So the coverage is no longer
    # symmetric between the two corpora, and asserting that it is would now hide
    # the one real gap.
    crp_missing = sorted(erc_j - set(crp))
    check("plan coverage is measured per corpus, and the gaps are named",
          not missing and crp_missing == ["PR"] and not extra,
          f"Schedule & Experience covers {len(erc_j & set(ses))} of {len(erc_j)} "
          f"ERC jurisdictions (PR by adoption of the multistate plan, at the "
          f"2-15 edition) · Composite Rating covers "
          f"{len(erc_j & set(crp))} of {len(erc_j)}, missing {crp_missing} · "
          f"Hawaii is in neither and in no other source either (OI-54) · "
          f"manual-only {extra or 'none'}")

    # Composite Rating changed LINE PREFIX in 2017 — GL to IL (interline).
    lines = Counter(p for v in crp.values() for p, _y, _f in v)
    years = Counter(y for v in crp.values() for _p, y, _f in v)
    check("Composite Rating moved from the GL manual to the Interline manual",
          set(lines) == {"GL", "IL"},
          f"line prefixes {dict(lines)} · years {dict(sorted(years.items()))} — "
          f"the 2017+ filings are `IL-` (Interline), so a search restricted to "
          f"`GL-*` finds {lines.get('GL', 0)} of {n_crp} documents")

    # ---- 2. the ERC apparatus, found by rule name
    base = cw["GL_CW_20270401_V01"]
    groups: dict[str, list[str]] = defaultdict(list)
    for f in glob.glob(os.path.join(base, "Rules", "*.xml")):
        for m in RULE.finditer(A._read(f)):
            n, g = m.group(1), m.group(2)
            if re.search(r'ExperienceRating|ExperienceModification|ExperienceRatio'
                         r'|CredibilityFactor|ScheduleRating|CompositeRat', n):
                groups[g].append(n)
    tot = sum(len(v) for v in groups.values())
    print(f"\nERC apparatus in GL_CW_20270401_V01: {tot} rules across "
          f"{len(groups)} groups")
    for g, v in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(v):>3}  {g}")
        if verbose:
            for n in sorted(v):
                print(f"        {n}")

    check("Composite Rating is executable from ERC — OI-03's open question",
          len(groups.get("GeneralLiabilityCompositeRating", [])) == 3,
          f"{len(groups.get('GeneralLiabilityCompositeRating', []))} rules: "
          f"{sorted(groups.get('GeneralLiabilityCompositeRating', []))} — "
          f"a rate and a premium, both fully specified")

    # ---- 3. the numbers: manual Table 9 against ERC's domain tables
    d = os.path.join(base, "Domain Tables")
    found = {f[:-len(".DomainTable.csv")] for f in os.listdir(d)
             if f.startswith("DomainScheduleRatingModification")
             and f.endswith(".DomainTable.csv")}
    rows: dict[str, int] = {}
    vals: dict[str, tuple[int, int]] = {}
    for t in sorted(found):
        r = A.table(base, "Domain Tables", t + ".DomainTable.csv")
        rows[t] = len(r)
        nums = sorted(int(x[-1].strip().rstrip("%")) for x in r if x)
        vals[t] = (nums[0], nums[-1]) if nums else (0, 0)
    agree = 0
    detail: list[str] = []
    for key, pct in TABLE_9.items():
        t = f"DomainScheduleRatingModification{key}Pct"
        want_rows, want_rng = 2 * pct + 1, (-pct, pct)
        ok = rows.get(t) == want_rows and vals.get(t) == want_rng
        agree += ok
        if not ok:
            detail.append(f"{key}: manual ±{pct}% wants {want_rows} rows "
                          f"{want_rng}, ERC has {rows.get(t)} {vals.get(t)}")
    check("manual Rule 9 Table 9 matches ERC's schedule-rating domains, cell for cell",
          agree == len(TABLE_9) and len(found) == len(TABLE_9),
          f"{agree} of {len(TABLE_9)} characteristics agree on BOTH row count "
          f"(2n+1 for a ±n% range) and range · ERC ships {len(found)} such "
          f"domains, manual prints {len(TABLE_9)}"
          + (" · " + "; ".join(detail) if detail else ""))

    cred = A.table(base, "Rate Tables", "ScheduleRatingMaximumCredit.RateTable.csv")
    deb = A.table(base, "Rate Tables", "ScheduleRatingMaximumDebit.RateTable.csv")
    check("the manual's 25% cap is the filed cap",
          [r[-1] for r in cred] == [str(-MAX_CREDIT_DEBIT)]
          and [r[-1] for r in deb] == [str(MAX_CREDIT_DEBIT)],
          f"manual Rule 9 'subject to a maximum credit or debit of "
          f"{MAX_CREDIT_DEBIT}%' · ERC credit {cred} debit {deb}")

    # ---- 4. the rounding vocabulary is one value short in N10
    prec: Counter = Counter()
    sites: list[str] = []
    for f in glob.glob(os.path.join(base, "Rules", "*.xml")):
        s = A._read(f)
        prec.update(re.findall(r'DecimalPlaces="(\d+)"', s))
        if 'DecimalPlaces="8"' in s:
            for m in RULE.finditer(s):
                if 'DecimalPlaces="8"' in m.group(3):
                    sites.append(f"{m.group(2)}::{m.group(1)}")
    check("an 8-decimal-place rounding precision exists and N10 does not list it",
          prec.get("8") == 3 and len(sites) == 3,
          f"precisions {dict(sorted(prec.items(), key=lambda kv: -kv[1]))} — "
          f"N10 records 3/0/4/2 only. The 8dp sites are {sorted(sites)}")

    # ---- 5. manual Rule 16 against the three ERC tables that implement it
    #
    # The manual prints ONE table with four columns; ERC files THREE tables of
    # 99 rows sharing one band key. And the lookup rule is called
    # `LookupExperienceCredibilityFactor` while the table it reads is
    # `CredibilityFactor` — resolving the rule rather than guessing the table
    # name is what this project has had to learn twice. A first pass here looked
    # up `ExperienceCredibilityFactor`, found 0 rows, and nearly filed a gap that
    # does not exist.
    txt = os.path.join(TEXT, "scheduleexperience", "GL-MU-2023-CGLES-001-C.txt")
    seg = A._read(txt)
    seg = seg[seg.find("RULE 16."):]
    rowre = re.compile(r'([\d,]{5,})\s*[–—-]\s*([\d,]{5,})\s+([01]\.\d{2})'
                       r'\s+([01]\.\d{3})\s+([\d,]{4,})')
    man = [(int(m.group(1).replace(",", "")), int(m.group(2).replace(",", "")),
            m.group(3), m.group(4), int(m.group(5).replace(",", "")))
           for m in rowre.finditer(seg)]

    def band(t: str) -> dict[tuple[int, int], str]:
        return {(int(r[1]), int(r[2])): r[3]
                for r in A.table(base, "Rate Tables", t + ".RateTable.csv")}

    cred, eer, msl = (band("CredibilityFactor"), band("ExpectedExperienceRatio"),
                      band("MaximumSingleLoss"))
    agree3 = sum(1 for lo, hi, c, e, m in man
                 if (lo, hi + 1) in cred
                 and float(cred[(lo, hi + 1)]) == float(c)
                 and float(eer[(lo, hi + 1)]) == float(e)
                 and int(float(msl[(lo, hi + 1)])) == m)
    check("manual Rule 16 matches ERC on all three columns, band for band",
          bool(man) and agree3 == len(man)
          and len(cred) == len(eer) == len(msl) == 99,
          f"{agree3} of {len(man)} printed bands agree on credibility, expected "
          f"experience ratio AND maximum single loss — {agree3 * 3} cells, "
          f"0 mismatches · ERC files {len(cred)} rows per table: the {len(man)} "
          f"printed bands plus a `[0, 10879) -> 0` eligibility floor and an "
          f"open-ended top band")

    print(f"\n{'FAILED' if failures else 'all rating-plan checks passed'}"
          + (f": {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
