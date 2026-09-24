"""The one-command regression -- chunks 0-12 and the General Liability suites.

Built for C10-21 (chunks 1-9 after chunk 10's _lookup_banded fix,
docs/CF-ENGINE-FIX-BANDED-LOOKUP.md). Extended 2026-09-22 (C11-24, part 1) to
cover chunk 10's own golden case and tests and chunk 11's, so "is everything
green?" is one command again -- before this, chunks 10 and 11 needed four
scripts run by hand after every engine change.

Three checks per script, not one:

  1. exit code 0                       -- the script's own assertions passed
  2. no failure marker in its output   -- MISMATCH / RAISED / Traceback /
                                          "<< expected", so a script that
                                          reports a disagreement without
                                          exiting non-zero is still caught
  3. every DOCUMENTED figure present   -- the dollar amounts docs/CF-START-HERE.md
                                          and the chunk golden-case docs record
                                          for that script, matched as standalone
                                          tokens in its output

Check 3 is the one that makes this a regression rather than a smoke test:
exit 0 only proves a script agreed with itself. Check 3 pins it to the number
written down before today. It can, in principle, pass on a coincidental token
match, which is why it is run ALONGSIDE checks 1 and 2 and not instead of them.

--selftest runs the harness against a deliberately wrong expectation and a
deliberately failing command, and fails if the harness reports them green --
this project's standing "a check that finds nothing needs its denominator
tested too" rule (CF-START-HERE.md).

Usage:
    python scripts/cf/104_chunk10_c10-21_regression.py
    python scripts/cf/104_chunk10_c10-21_regression.py --selftest
    python scripts/cf/104_chunk10_c10-21_regression.py --only 01 09 68
    python scripts/cf/104_chunk10_c10-21_regression.py --no-gl
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CF = ROOT / "scripts" / "cf"
TESTS = ROOT / "tests"

FAILURE_MARKERS = ("MISMATCH", "RAISED", "Traceback", "<< expected")

# The zero-case scripts PREDICT raises -- the null-premium guard firing on an
# absent Limit is the finding, not a failure. "RAISED" is a legitimate word in
# their output, so it is dropped from their marker set and replaced by a
# positive requirement: each one must still print its own all-cases-match line.
# Found by running, not assumed: all three exit 0 and all three say so.
ZERO_CASE_MARKERS = ("MISMATCH", "Traceback", "<< expected")
ZERO_CASE_REQUIRE = ("match their derivation",)

#: The scripts the relaxation above was written for, BY NAME. It used to key on
#: "zero_cases" in the filename, which silently widened to chunk 10's and 11's
#: zero-case scripts -- neither prints "RAISED" nor the match-line, so the
#: substring rule would have failed them for the wrong reason. Found when
#: adding them (2026-09-22), not after a false red.
ZERO_CASE_SCRIPTS = {"42_chunk6_zero_cases.py", "51_chunk7_zero_cases.py",
                     "61_chunk8_zero_cases.py"}

# (script, chunk, what it holds, documented figures that must appear)
#
# Figures are transcribed from docs/CF-START-HERE.md's own golden-case table
# and, for chunk 9, from docs/CF-CHUNK9-GOLDEN-CASE.md. They are the numbers
# recorded BEFORE the engine fix -- that is the whole point of listing them
# here rather than reading them back out of a fresh run.
GOLDEN = [
    ("00_chunk0_checks.py", 0,
     "foundation: operators, resolver, edition chain", []),
    ("01_golden_case.py", 1,
     "Building Basic Group I", ["261", "263", "288"]),
    ("09_chunk2_golden_case.py", 2,
     "Building Basic Group II", ["261", "32"]),
    # CF-START-HERE.md records "16 / 54, layering on Basic to 293 / 309 / 347".
    # 293 is NOT printed by this script and its absence is not a regression:
    # 293 is the Basic-only subtotal (261 + 32), which is chunk 2's figure, not
    # chunk 3's. This script prints the two CUMULATIVE totals it is responsible
    # for -- 261+32+16=309 and 261+32+54=347. Checked by reading the script's
    # own output, not by dropping an inconvenient expectation.
    ("15_chunk3_golden_case.py", 3,
     "Building Broad and Special, layering on Basic",
     ["16", "54", "309", "347"]),
    ("22_chunk4_golden_case.py", 4,
     "Contents, four forms; Building unmoved",
     ["223", "24", "16", "137", "263", "32"]),
    ("32_chunk5_golden_case.py", 5,
     "Business Income, four forms; Building unmoved",
     ["112", "13", "23", "47", "261", "32"]),
    ("41_chunk6_golden_case.py", 6,
     "Special Class, four forms; Building unmoved",
     ["66", "209", "14", "44", "261", "32"]),
    ("50_chunk7_golden_case.py", 7,
     "Special Class Business Income; the item unmoved",
     ["39", "123", "23", "47", "66", "209"]),
    ("59_chunk8_golden_case.py", 8,
     "Legal Liability, Building and Contents",
     ["60", "7", "4", "12", "132", "15", "11", "93"]),
    ("68_chunk9_golden_case.py", 9,
     "Blanket rating, two dispersed structures", ["255", "510"]),
    # docs/CF-CHUNK10-GOLDEN-CASE.md: EQ premium $6, ordinary BGI unmoved $261.
    ("85_chunk10_golden_case.py", 10,
     "Earthquake, Building; ordinary premium unmoved", ["6", "261"]),
    # docs/CF-CHUNK11-GOLDEN-CASE.md: Tenants Lease $268 BGI + $30 BGII = $298.
    ("114_chunk11_golden_case.py", 11,
     "Leasehold Interest, Tenants Lease", ["268", "30", "298"]),
    # Chunk 12 (C12-41, 2026-09-23). Each figure was derived by hand and written
    # into the family's doc BEFORE its first run, and each matched ISO live.
    ("127_chunk12_golden_case.py", 12,
     "Debris Removal on chunk 2's building; building unmoved", ["49", "6", "55", "261", "32"]),
    ("130_chunk12_ordinance_golden_case.py", 12,
     "Ordinance or Law, A and B & C Separate", ["39", "5", "55", "7", "82", "10", "198"]),
    ("133_chunk12_utility_golden_case.py", 12,
     "Utility Services, direct damage and time element", ["15", "4", "9", "112"]),
    ("137_chunk12_drone_golden_case.py", 12,
     "Unmanned Aircraft on chunk 4's Special Contents", ["187", "137"]),
    ("139_chunk12_green_golden_case.py", 12,
     "Green Upgrades on chunk 2's building", ["27", "3", "30", "33", "261"]),
    ("141_chunk12_dependent_golden_case.py", 12,
     "Dependent Properties, Broad form on chunk 5's Business Income", ["80", "12", "112"]),
]

# The machinery each chunk added -- run whenever shared code changes, which is
# exactly what happened today. No figure list: these assert internally and are
# held to checks 1 and 2.
MACHINERY = [
    ("04_shared_names.py", "gate point 6 across all chains"),
    ("05_exclusion_records.py", "gate point 7 census"),
    ("21_chunk3_special_structure.py", "chunk 3 Special structure"),
    ("23_chunk4_foreach.py", "chunk 4 repeating group"),
    ("35_chunk5_factor.py", "chunk 5 SetFactor -- selection, not multiplication"),
    ("39_chunk5_crossform.py", "chunk 5 three coverages, none moving"),
    ("42_chunk6_zero_cases.py", "chunk 6 zero cases"),
    ("45_chunk6_description_chain.py", "chunk 6 description chain"),
    ("46_chunk6_perform.py", "chunk 6 per-form specifics"),
    ("47_chunk6_forms.py", "chunk 6 form claims"),
    ("48_chunk6_crossform.py", "chunk 6 cross-form claims"),
    ("51_chunk7_zero_cases.py", "chunk 7 zero cases"),
    ("54_chunk7_borrowed.py", "chunk 7 borrowed rate"),
    ("55_chunk7_perform.py", "chunk 7 per-form specifics"),
    ("56_chunk7_crossform.py", "chunk 7 cross-form claims"),
    ("57_chunk7_open_questions.py", "chunk 7 open questions"),
    ("61_chunk8_zero_cases.py", "chunk 8 zero cases"),
    ("64_chunk8_fork.py", "chunk 8 fork"),
    ("65_chunk8_map.py", "chunk 8 traced map"),
    ("66_chunk8_crossform.py", "chunk 8 map scored, cross-coverage LOI leak"),
    ("69_chunk9_c9-02_chain_trace.py", "chunk 9 blanket chain trace"),
    ("72_chunk9_c9-06_three_gates.py", "chunk 9 three gates"),
    ("75_chunk9_c9-09_setnoneq_diff.py", "chunk 9 SetNonEQBlanketValues diff"),
    ("80_chunk9_c9-15-16-17_reachability.py", "chunk 9 reachability"),
    ("83_chunk9_c9-20_crosscoverage_leak.py", "chunk 9 cross-coverage leak"),
    # Chunk 10 -- the scripts that assert (exit 1 on disagreement). Its
    # censuses (84/86/87/89/90/92/93/94/97/102) always exit 0 and are listed
    # under EXCLUDED rather than run for show.
    ("88_chunk10_c10-04_zero_cases.py", "chunk 10 zero cases, two tiers"),
    ("91_chunk10_c10-09_message_tally.py", "chunk 10 message tally"),
    ("95_chunk10_c10-11_all_groups_chain.py", "chunk 10 EQ chain, all 5 groups"),
    ("96_chunk10_c10-12_eqclass_eqterr_live.py", "chunk 10 EQClass/EQTerr live"),
    ("98_chunk10_c10-14_ordinary_chain_separation.py", "chunk 10 EQ vs ordinary chain"),
    ("99_chunk10_c10-16_legal_liability_eq.py", "chunk 10 Legal Liability EQ"),
    ("100_chunk10_c10-15_blanket_reachability.py", "chunk 10 EQ blanket branch"),
    ("101_chunk10_c10-17_non_owned_trailers.py", "chunk 10 Non-Owned Trailers EQ"),
    ("103_chunk10_c10-19_sublimit_flatdeductible.py", "chunk 10 sub-limit (banded-lookup fix)"),
    ("105_chunk10_c10-20_fixture_sample.py", "chunk 10 fixture census, 364 CF payloads"),
    # Chunk 11.
    ("115_chunk11_groupA_annuity.py", "chunk 11 annuity, injection, live inputs"),
    ("116_chunk11_groupB_subcoverages.py", "chunk 11 four sub-coverages"),
    ("117_chunk11_c11-04_zero_cases.py", "chunk 11 zero cases, seven tiers"),
    ("119_chunk11_groupD_shared_machinery.py", "chunk 11 shared machinery"),
    ("120_chunk11_groupsEF_inventory_states.py",
     "chunk 11 inventory, states (46), DateDifference sign pinned (OI-107)"),
    # Chunk 12.
    ("125_chunk12_c12-03_operand_types.py",
     "chunk 12 operand types + 17 fixtures + the OI-108 blanket-drone probe"),
    ("128_chunk12_debris_removal_gates.py", "chunk 12 Debris Removal gates 2-8"),
    ("131_chunk12_ordinance_gates.py", "chunk 12 Ordinance or Law gates 2-8"),
    ("134_chunk12_utility_gates.py", "chunk 12 Utility Services gates 2-8"),
    ("138_chunk12_drone_gates.py", "chunk 12 Unmanned Aircraft gates 2-9"),
    ("140_chunk12_green_gates.py", "chunk 12 Green Upgrades gates 2-8"),
    ("142_chunk12_dependent_gates.py", "chunk 12 Dependent Properties gates 2-8"),
    ("121_chunk11_c11-09_messages.py",
     "chunk 11 messages: golden registered; ours == ISO's saved responses"),
    # Chunk 13 (2026-09-24). No network: 145 replays ISO's own stored responses.
    ("144_chunk13_c13-02_rule_order.py", "chunk 13 terrorism rule order and roll-up, 5 editions"),
    ("145_chunk13_c13-03_replay.py",
     "chunk 13 14 stored ISO terrorism responses, field by field (OI-111 pinned: CA $153)"),
    ("147_chunk13_c13-04_operand_types.py", "chunk 13 operand types; all four TRIA stages live, timeline by hand"),
    ("148_chunk13_c13-05_attach_map.py", "chunk 13 attach map: 168 answer combinations x attach/delete"),
    ("149_chunk13_golden_case.py", "chunk 13 golden case OR $8 + 4 variants (fire exception, TRIA proration), 38 figures"),
    ("150_chunk13_c13-08-09_groups_rollup.py", "chunk 13 other four groups + roll-ups, 9 policies, 53 figures"),
]

# Excluded on purpose, each with a reason -- no silent narrowing of scope.
EXCLUDED = [
    ("02/10/16/25/33 zero-case + 03/11/17/24/34/43/52/62 sweep scripts",
     "the state sweeps take minutes each and enumerate 47 jurisdictions; "
     "they were re-run green on 2026-09-18 and touch no banded lookup. "
     "Run them directly when a state-layer change lands."),
    ("chunk 10 censuses 84/86/87/89/90/92/93/94/97/102, chunk 11 census 106, "
     "chunk 12 censuses 123/124/126",
     "each states 'always exits 0 -- a census, not a test'; running them "
     "here would add minutes and prove only that they still print."),
    ("06/19/44/53/63/79/118/122 RaaS scripts, and chunk 12's 129/132/135/136",
     "they call ISO's live service; a regression of OUR engine must not "
     "depend on a network round trip. 63_chunk8_raas.py additionally exits "
     "non-zero BY DESIGN (OI-99)."),
    ("07_diagnose_message.py",
     "requires CLI arguments; a bare invocation is an argparse usage error."),
    ("the *_r1..r8 / *_m1 / *_t1 Excel-COM scripts",
     "a separate rater-streamlining workstream that drives Excel over COM. "
     "Not part of this engine's test surface, and RULE #0 applies."),
]


def run(cmd, cwd):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or ""), time.time() - t0


def check(rc, out, figures, markers=FAILURE_MARKERS, require=()):
    """Return (ok, list of reasons it failed)."""
    bad = []
    if rc != 0:
        bad.append(f"exit {rc}")
    hit = [m for m in markers if m in out]
    if hit:
        bad.append("output carries " + "/".join(hit))
    missing = [f for f in figures
               if not re.search(rf"(?<![\d.]){re.escape(f)}(?![\d.])", out)]
    if missing:
        bad.append("documented figure(s) absent: " + ", ".join(missing))
    absent = [p for p in require if p not in out]
    if absent:
        bad.append("required phrase(s) absent: " + "; ".join(absent))
    return (not bad), bad


def selftest():
    """Prove the harness can fail. Three planted defects, all must be caught."""
    print("SELFTEST -- planting three defects the harness must catch\n")
    ok = True

    rc, out, _ = run([sys.executable, "-c", "raise SystemExit(3)"], ROOT)
    good, why = check(rc, out, [])
    print(f"  1. non-zero exit          -> caught={not good}  {why}")
    ok &= not good

    rc, out, _ = run([sys.executable, "-c", "print('PREMIUM MISMATCH')"], ROOT)
    good, why = check(rc, out, [])
    print(f"  2. MISMATCH in output     -> caught={not good}  {why}")
    ok &= not good

    rc, out, _ = run([sys.executable, "-c", "print('premium = 999')"], ROOT)
    good, why = check(rc, out, ["261"])
    print(f"  3. documented figure gone -> caught={not good}  {why}")
    ok &= not good

    # And the inverse: a clean run must pass, or the harness is just a
    # red-light generator.
    rc, out, _ = run([sys.executable, "-c", "print('premium = 261 OK')"], ROOT)
    good, why = check(rc, out, ["261"])
    print(f"  4. clean run              -> passes={good}  {why}")
    ok &= good

    # Token boundary: 261 must not be satisfied by 1261 or 261.5
    rc, out, _ = run([sys.executable, "-c", "print('1261 and 261.5')"], ROOT)
    good, _ = check(rc, out, ["261"])
    print(f"  5. no substring false pass-> caught={not good}")
    ok &= not good

    # The zero-case relaxation must not become a blanket amnesty: dropping
    # "RAISED" from the marker set is only safe because the match-line is
    # required in its place. Prove the replacement actually bites.
    rc, out, _ = run([sys.executable, "-c", "print('case 1 RAISED InterpretError')"], ROOT)
    good, why = check(rc, out, [], markers=ZERO_CASE_MARKERS,
                      require=ZERO_CASE_REQUIRE)
    print(f"  6. zero-case w/o match-line -> caught={not good}  {why}")
    ok &= not good

    rc, out, _ = run([sys.executable, "-c",
                      "print('case 1 RAISED\\nAll 7 cases match their derivation.')"], ROOT)
    good, why = check(rc, out, [], markers=ZERO_CASE_MARKERS,
                      require=ZERO_CASE_REQUIRE)
    print(f"  7. zero-case w/ match-line  -> passes={good}  {why}")
    ok &= good

    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--only", nargs="*", default=None,
                    help="run only scripts whose filename starts with these")
    ap.add_argument("--no-gl", action="store_true",
                    help="skip the 16 General Liability suites")
    a = ap.parse_args()

    if a.selftest:
        return selftest()

    def wanted(name):
        return a.only is None or any(name.startswith(p) for p in a.only)

    failures = []
    print("Regression -- chunks 0-12 and the General Liability suites")
    print("=" * 78)

    print("\nGOLDEN CASES -- exit code, failure markers, and documented figures")
    print("-" * 78)
    for script, chunk, what, figures in GOLDEN:
        if not wanted(script):
            continue
        rc, out, secs = run([sys.executable, f"scripts/cf/{script}"], ROOT)
        good, why = check(rc, out, figures)
        fig = " ".join(f"${f}" for f in figures) or "(no dollar figure)"
        print(f"  chunk {chunk}  {script:38s} {'OK ' if good else 'FAIL'} "
              f"{secs:5.1f}s  {fig}")
        print(f"            {what}")
        if not good:
            failures.append((script, why, out))
            for w in why:
                print(f"            !! {w}")

    print("\nMACHINERY -- exit code and failure markers")
    print("-" * 78)
    for script, what in MACHINERY:
        if not wanted(script):
            continue
        zero = script in ZERO_CASE_SCRIPTS
        rc, out, secs = run([sys.executable, f"scripts/cf/{script}"], ROOT)
        good, why = check(rc, out, [],
                          markers=ZERO_CASE_MARKERS if zero else FAILURE_MARKERS,
                          require=ZERO_CASE_REQUIRE if zero else ())
        tag = "  [zero-case: predicted raises allowed, match-line required]" \
            if zero else ""
        print(f"  {script:42s} {'OK ' if good else 'FAIL'} {secs:5.1f}s  "
              f"{what}{tag}")
        if not good:
            failures.append((script, why, out))
            for w in why:
                print(f"      !! {w}")

    if not a.no_gl:
        print("\nGENERAL LIABILITY -- the regression net for shared-code changes")
        print("-" * 78)
        for t in sorted(TESTS.glob("verify_*.py")):
            if not wanted(t.name):
                continue
            rc, out, secs = run([sys.executable, f"tests/{t.name}"], ROOT)
            good, why = check(rc, out, [])
            print(f"  {t.name:42s} {'OK ' if good else 'FAIL'} {secs:5.1f}s")
            if not good:
                failures.append((t.name, why, out))
                for w in why:
                    print(f"      !! {w}")

    print("\nOUT OF SCOPE, stated rather than silently dropped")
    print("-" * 78)
    for what, why in EXCLUDED:
        print(f"  - {what}\n      {why}")

    print("\n" + "=" * 78)
    if failures:
        print(f"REGRESSION FAILED -- {len(failures)} script(s)\n")
        for script, why, out in failures:
            print(f"--- {script}: {'; '.join(why)}")
            print("\n".join(out.strip().splitlines()[-15:]))
            print()
        return 1
    print("REGRESSION CLEAN -- every chunk 0-12 golden case reproduces its "
          "documented figures,\nevery machinery script and every GL suite "
          "exits 0 with no failure marker.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
