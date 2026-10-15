"""`python -m deviations <command>` -- the v1 interface to deviation files.

  validate <authored.json>               every problem, in one pass
  compile  <authored.json>               validated + approved -> compiled tables
  show     <authored.json>               the compiled tables read back as rows
  diff     <a.json> <b.json>             two versions, row by row
  diff     <authored.json> --iso         the filing against ISO's own values
  import-xlsx <sheet> --carrier ...      a sheet -> authored files (draft)
  propose | sign-off | reject | withdraw <authored.json> --by NAME
                                         one line in the workflow log
  status   <authored.json>               where a version stands
  impact   <COMPANY> --line CF [--state IA]
                                         B-18: technical vs carrier over a projected book, by risk type
  impact   --draft <authored.json>       B-20: the same for a draft, before it is approved or built

Exit status is 0 on success, 1 when the filing has problems, 2 on bad usage.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compile import CompileError, compile_filing, show, show_text
from .config import CARRIERS_ROOT
from .diff import diff_iso, diff_versions
from .files import FileError, load_filing, log_action, workflow_status, carrier_json
from .sheets import import_sheet
from .validate import approval, validate


def _report(rep) -> int:
    for w in rep.warnings:
        print(f"  warn  {w}")
    for e in rep.errors:
        print(f"  FAIL  {e}")
    if rep.ok:
        n = sum(len(k) for _, _, comp, _, _ in rep.plans.values() for k in comp.values())
        print(f"  ok    {rep.filing.ref}: {len(rep.filing.rows)} rows, "
              f"{', '.join(rep.juris)}, {n} compiled keys")
    return 0 if rep.ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m deviations",
                                 description="Carrier deviation files (P1).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "compile", "show", "status"):
        sub.add_parser(name).add_argument("filing", type=Path)
    d = sub.add_parser("diff")
    d.add_argument("a", type=Path)
    d.add_argument("b", type=Path, nargs="?")
    d.add_argument("--iso", action="store_true")
    for name in ("propose", "sign-off", "reject", "withdraw"):
        w = sub.add_parser(name)
        w.add_argument("filing", type=Path)
        w.add_argument("--by", required=True)
        w.add_argument("--note", default="")
    ip = sub.add_parser("impact")
    ip.add_argument("company", nargs="?")
    ip.add_argument("--draft", type=Path, help="an authored draft: its impact in a scratch store, before approval")
    ip.add_argument("--line", default="CF", choices=("CF", "GL"))
    ip.add_argument("--state", action="append", default=[])
    ip.add_argument("--root", type=Path, default=CARRIERS_ROOT)
    ip.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "results" / "impact")
    im = sub.add_parser("import-xlsx")
    im.add_argument("sheet", type=Path)
    im.add_argument("--root", type=Path, default=CARRIERS_ROOT)
    im.add_argument("--carrier", required=True)
    im.add_argument("--line", required=True, choices=("CF", "GL"))
    im.add_argument("--juris", required=True, help="comma-separated, or ALL")
    im.add_argument("--filing", required=True)
    im.add_argument("--version", type=int, default=1)
    im.add_argument("--company", action="append", default=[],
                    help='"Sheet name=CODE", once per company')
    im.add_argument("--new-eff")
    im.add_argument("--renewal-eff")
    im.add_argument("--approved")
    im.add_argument("--serff")
    im.add_argument("--overwrite", action="store_true")
    a = ap.parse_args(argv)

    try:
        if a.cmd == "impact":
            from .impact import run, run_draft, write
            n = [0]

            def tick(r):
                n[0] += 1
                if n[0] % 25 == 0:
                    print(f"  {n[0]} risks rated", flush=True)
            if a.draft:
                rep = run_draft(a.draft, progress=tick)
            elif a.company:
                rep = run(a.company, a.line, a.state or None, a.root, progress=tick)
            else:
                print("impact needs a company, or --draft <authored.json>", file=sys.stderr)
                return 2
            j, m = write(rep, a.out)
            print(f"  {rep['company']} {rep['line']}: {rep['all']['rated']} of {rep['all']['risks']} risks, "
                  f"overall {rep['all']['change']}%, 0 ISO calls")
            print(f"  wrote {j}")
            print(f"  wrote {m}")
            return 0
        if a.cmd == "import-xlsx":
            cmap = dict(c.split("=", 1) for c in a.company)
            files, warns = import_sheet(
                a.sheet, a.root, carrier=a.carrier, line=a.line,
                juris=[j.strip().upper() for j in a.juris.split(",")],
                filing=a.filing, version=a.version, company_map=cmap,
                new_eff=a.new_eff, renewal_eff=a.renewal_eff, approved=a.approved,
                serff=a.serff, overwrite=a.overwrite)
            for w in warns:
                print(f"  warn  {w}")
            for p in files:
                print(f"  wrote {p}")
            return 0

        if a.cmd == "diff":
            fa = load_filing(a.a)
            if a.iso:
                rep = validate(fa)
                if not rep.ok:
                    return _report(rep)
                print("\n".join(diff_iso(rep)))
                return 0
            if not a.b:
                print("diff needs two filings, or one with --iso", file=sys.stderr)
                return 2
            print("\n".join(diff_versions(fa, load_filing(a.b))))
            return 0

        f = load_filing(a.filing)
        if a.cmd == "validate":
            return _report(validate(f))
        if a.cmd == "compile":
            rep = validate(f)
            if not rep.ok:
                return _report(rep)
            for d in compile_filing(rep):
                print(f"  wrote {d}")
            return 0
        if a.cmd == "show":
            print(show_text(show(f.company_dir, f.line, f.ref)))
            return 0
        if a.cmd == "status":
            need = int(carrier_json(f.carrier_dir).get("approval", {}).get("signoffs", 1))
            wf = workflow_status(f.company_dir, f.filing, f.version, need)
            ok, why = approval(f)
            print(f"  {f.ref}: file {f.raw.get('status')!r}, workflow {wf['status']!r}; "
                  f"{'compiles' if ok else 'will not compile'} ({why})")
            return 0
        line = log_action(f.company_dir, f.filing, f.version, a.cmd, a.by, a.note)
        print(f"  logged {line['action']} by {line['by']} at {line['ts']}")
        return 0
    except (FileError, CompileError) as e:
        print(f"  FAIL  {e}")
        return 1
