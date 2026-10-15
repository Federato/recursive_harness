"""B-20: filing packets -- one zip carries a filing into the carrier store; the console's upload ingests it.

Run: python tests/verify_deviations_packet.py    (offline; no ISO calls; scratch stores only)

  P1  build    a packet of an archived filing: its documents, its filing sheet, every company's versions, the class
               groups its rows name and the companies' pins for its line and states
  P2  ingest   into an empty store: a new carrier and companies, the documents re-hashed into source.json, the
               drafts as drafts (never approved, nothing in the workflow log), each validated
  P3  again    the same packet again changes nothing: every file identical, skipped
  P4  refused  a changed document, a name outside its folder, an unlisted file, a conflicting class group or pin:
               refused, and nothing is written
  P5  console  the upload route ingests a packet and runs each draft's impact preview in the background; the filing
               then shows on the screen at "Draft impact", with its documents and drafts
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="deviations_packet_"))
os.environ["CARRIERS_ROOT"] = str(TMP / "store")              # before deviations.config is imported
os.environ["IMPACT_DIR"] = str(TMP / "impact")
os.environ["RAAS_LEDGER_DIR"] = str(TMP / "ledger")
os.environ["TC_DISPATCH"] = "0"
for p in (ROOT, ROOT / "scripts", ROOT / "scripts" / "cf", ROOT / "console", ROOT / "tests"):
    sys.path.insert(0, str(p))
sys.stdout.reconfigure(encoding="utf-8")

FAILED, CHECKS = [], []
SERFF = "UNFG-134374972"


def check(label: str, ok: bool, detail="") -> None:
    CHECKS.append((label, bool(ok)))
    print(f"  {'ok  ' if ok else 'FAIL'}  {label}" + ("" if ok else f"  [{detail}]"))
    if not ok:
        FAILED.append(label)


def tree(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def repack(data: bytes, change) -> bytes:
    """The packet with `change(name, bytes) -> bytes | None` applied (None drops the member); change may add some."""
    zin = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for i in zin.infolist():
            b = change(i.filename, zin.read(i.filename))
            if b is not None:
                z.writestr(i.filename, b)
        for name, b in getattr(change, "extra", {}).items():
            z.writestr(name, b)
    return out.getvalue()


def main() -> int:
    from deviations import packet as PK
    src_store = TMP / "source"
    shutil.copytree(ROOT / "tests" / "fixtures" / "deviations" / "UFG", src_store / "UFG")
    sdir = src_store / "UFG" / "sources" / SERFF
    sdir.mkdir(parents=True)
    docs = {"filing.pdf": b"%PDF-1.4 the exception page", f"{SERFF}-filing-sheet.md": b"# Filing sheet\n\n| a | b |\n|---|---|\n"}
    for n, b in docs.items():
        (sdir / n).write_bytes(b)
    (sdir / "source.json").write_text(json.dumps({
        "serff": SERFF, "carrier": "UFG", "companies": ["UFC", "ADD"], "line": "GL", "juris": ["IA"],
        "received": "2026-10-15", "sheet": f"{SERFF}-filing-sheet.md", "dev": "DEV-003",
        "files": [{"name": n, "what": "doc", "sha256": hashlib.sha256(b).hexdigest()} for n, b in docs.items()]}),
        encoding="utf-8")

    print("\nP1  build")
    zp = PK.build(SERFF, TMP / "p.zip", src_store)
    data = zp.read_bytes()
    z = zipfile.ZipFile(io.BytesIO(data))
    meta = json.loads(z.read("packet.json"))
    check("P1 the packet carries the documents and both companies' versions",
          sorted(z.namelist()) == sorted(["packet.json", "sources/filing.pdf", f"sources/{SERFF}-filing-sheet.md",
                                          f"drafts/ADD/IA-GL-{SERFF}.v1.json", f"drafts/UFC/IA-GL-{SERFF}.v1.json"]),
          z.namelist())
    check("P1 ... the class groups its rows name, and the companies' Iowa GL pins",
          sorted(meta["carrier_json"]["class_groups"]) == ["UFG-IA-GL-aRated-PremOps@v1", "UFG-IA-GL-aRated-Prods@v1"]
          and meta["companies_json"]["UFC"]["edition_pins"] == {"GL": {"IA": "GL_IA_20240401_V01"}}
          and meta["sheet"] == f"{SERFF}-filing-sheet.md", meta["carrier_json"].keys())

    print("\nP2  ingest into an empty store")
    store = TMP / "store"
    store.mkdir()
    rep = PK.ingest(data, store)
    check(f"P2 accepted: {len(rep['written'])} written, no problems", rep["ok"] and not rep["problems"], rep["problems"])
    car = json.loads((store / "UFG" / "carrier.json").read_text())
    ufc = json.loads((store / "UFG" / "UFC" / "company.json").read_text())
    check("P2 a new carrier with the class groups, a new company with its pin",
          len(car["class_groups"]) == 2 and ufc.get("edition_pins") == {"GL": {"IA": "GL_IA_20240401_V01"}}
          and ufc.get("naic") == "13021", (car.keys(), ufc))
    sj = json.loads((store / "UFG" / "sources" / SERFF / "source.json").read_text())
    check("P2 the documents are archived and re-hashed in source.json, with the sheet named",
          {f["name"]: f["sha256"] for f in sj["files"]} == {n: hashlib.sha256(b).hexdigest() for n, b in docs.items()}
          and sj["sheet"] == f"{SERFF}-filing-sheet.md", sj)
    d = json.loads((store / "UFG" / "UFC" / "authored" / f"IA-GL-{SERFF}.v1.json").read_text())
    check("P2 the drafts land as drafts, nothing in the workflow log, and validate",
          d["status"] == "draft" and not (store / "UFG" / "UFC" / "workflow.jsonl").exists()
          and all(v["ok"] for v in rep["validation"]) and len(rep["validation"]) == 2, rep["validation"])

    print("\nP3  the same packet again")
    before = tree(store)
    again = PK.ingest(data, store)
    check(f"P3 accepted, nothing written: {len(again['skips'])} skipped as identical",
          again["ok"] and not again["writes"] and tree(store) == before, again["writes"])

    print("\nP4  refused, and nothing written")
    cases = {
        "a changed document": lambda n, b: b + b" edited" if n == "sources/filing.pdf" else b,
        "an unlisted file": None,
        "a name outside its folder": None,
        "a conflicting class group": lambda n, b: json.dumps({**json.loads(b), "carrier_json": {
            **json.loads(b)["carrier_json"], "class_groups": {"UFG-IA-GL-aRated-PremOps@v1": ["10001"]}}}).encode()
            if n == "packet.json" else b,
        "a conflicting pin": lambda n, b: json.dumps({**json.loads(b), "companies_json": {
            "UFC": {"code": "UFC", "edition_pins": {"GL": {"IA": "GL_IA_20250401_V01"}}}}}).encode()
            if n == "packet.json" else b,
    }
    keep = lambda n, b: b                                         # noqa: E731
    extra1 = type("X", (), {"__call__": staticmethod(keep), "extra": {"sources/stray.txt": b"x"}})()
    extra2 = type("X", (), {"__call__": staticmethod(keep), "extra": {"drafts/../../evil.json": b"{}"}})()
    cases["an unlisted file"], cases["a name outside its folder"] = extra1, extra2
    for name, change in cases.items():
        bad = repack(data, change)
        before = tree(store)
        try:
            r = PK.ingest(bad, store)
            ok, why = (not r["ok"]), r["problems"][:2]
        except PK.PacketError as exc:
            ok, why = True, str(exc)
        check(f"P4 {name}: refused ({str(why)[:110]})", ok and tree(store) == before, why)

    print("\nP5  the console's upload")
    store2 = TMP / "store2"
    store2.mkdir()
    import deviations.config as DC
    from console import filings as F
    from ui import console_page as CP
    keep_root = F._carriers
    F._carriers = lambda: store2                                  # the screen's store, for this part
    try:
        code, body, _ = CP.dispatch("POST", "/api/console/filings/packet", {},
                                    {"name": "p.zip", "data": base64.b64encode(data).decode()})
        r = json.loads(body)
        check("P5 the upload is accepted and starts the impact previews", code == 200 and r["ok"] and r.get("impact")
              and r["impact"]["total"] == 2, {k: r.get(k) for k in ("ok", "problems", "impact")})
        t0 = time.time()
        while F.JOBS[SERFF]["state"] == "running" and time.time() - t0 < 900:
            time.sleep(2)
        j = F.JOBS[SERFF]
        check(f"P5 both drafts' impact previews finish ({'; '.join(j['messages'])[:160]})",
              j["state"] == "done" and j["done"] == 2 and all("vs pure ISO" in m for m in j["messages"]), j)
        code, body, _ = CP.dispatch("GET", "/api/console/filings", {}, None)
        f = next((x for x in json.loads(body)["filings"] if x["serff"] == SERFF), None)
        check("P5 the filing shows at Draft impact, with its documents, its two drafts and their impact",
              f and f["stage"] == "Draft impact" and len(f["sources"]) == 2
              and sorted((v["company"], v["status"]) for v in f["versions"]) == [("ADD", "draft"), ("UFC", "draft")]
              and sorted(i["company"] for i in f["impacts"] if i["draft"]) == ["ADD", "UFC"],
              f and (f["stage"], [(v["company"], v["status"]) for v in f["versions"]]))
        code, body, _ = CP.dispatch("POST", "/api/console/filings/packet", {}, {"name": "x.zip", "data": "bm90IGEgemlw"})
        check("P5 a file that isn't a zip is refused with the reason", code == 400 and "zip" in json.loads(body)["error"])
    finally:
        F._carriers = keep_root
    from deviations import suite_log
    suite_log.record("packet", CHECKS)
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"\n{'FAILED: ' + ', '.join(FAILED) if FAILED else 'all passed'}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
