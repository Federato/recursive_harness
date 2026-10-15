"""Filing packets (B-20): one zip that carries a filing into the carrier store -- its documents, our review, the drafts.

    packet.json                      what the filing is, and what the packet carries
    sources/<file>                   the filing's documents, exactly as received
    sources/<SERFF>-filing-sheet.md  our review (docs/deviations/FILING-SHEET-TEMPLATE.md), optional
    drafts/<COMPANY>/<filing>.vN.json  authored versions, optional

`packet.json`:

    {"packet": 1, "carrier": "UFG", "serff": "UNFG-134374972", "companies": ["UFC", "ADD"], "line": "GL",
     "juris": ["IA"], "received": "2026-10-15", "dev": "DEV-003", "stage": "Mapped", "suite": "ufg_ia_gl",
     "sheet": "UNFG-134374972-filing-sheet.md",
     "files": [{"name": "<file>", "what": "<what it is>"}, ...],
     "carrier_json": {"carrier": "UFG", "name": "...", "class_groups": {...}},      new carrier, or groups to add
     "companies_json": {"UFC": {"code": "UFC", "name": "...", "naic": "...", "edition_pins": {...}}}}

**Ingest never overwrites and never approves.** Everything is checked before anything is written: a document or a
draft that is already in the store must be byte-identical (then it is skipped), a class group or pin already defined
must say the same thing, and every name stays inside its folder. Drafts land as `status: draft` with nothing in the
workflow log, whatever the packet says. Building and approving stay a separate, deliberate step.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import time
import zipfile
from pathlib import Path

from .config import CARRIERS_ROOT

MAX_BYTES = 40 * 1024 * 1024
_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.()&,+'-]{0,200}$")
_CODE = re.compile(r"^[A-Z0-9]{2,12}$")


class PacketError(ValueError):
    pass


def _safe(name: str, what: str) -> str:
    if not _SAFE.match(name or "") or ".." in name:
        raise PacketError(f"{what} {name!r} is not a plain file name")
    return name


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


# ------------------------------------------------------------------ build

def build(serff: str, out: Path, root: Path = CARRIERS_ROOT, carrier: str | None = None) -> Path:
    """A packet of one archived filing, from the store: its documents, its sheet, every company's authored versions
    of it, the class groups those rows name and the companies' pins for its line and states."""
    root = Path(root)
    hits = sorted(root.glob(f"{carrier or '*'}/sources/{serff}/source.json"))
    if len(hits) != 1:
        raise PacketError(f"{serff}: {'not archived' if not hits else 'archived under more than one carrier'}")
    sdir = hits[0].parent
    cdir = sdir.parent.parent
    src = _read(hits[0])
    car = _read(cdir / "carrier.json")
    line, juris = src.get("line", ""), src.get("juris", [])
    drafts, groups, companies_json = {}, set(), {}
    for co in src.get("companies", []):
        cj = _read(cdir / co / "company.json") if (cdir / co / "company.json").exists() else {"code": co}
        pins = {line: {j: p for j, p in ((cj.get("edition_pins") or {}).get(line) or {}).items() if j in juris}}
        companies_json[co] = {k: cj[k] for k in ("code", "name", "naic") if k in cj}
        if pins[line]:
            companies_json[co]["edition_pins"] = pins
        for a in sorted((cdir / co / "authored").glob(f"*{serff}*.json")):
            d = _read(a)
            groups |= {str(r["scope"]["class_group"]) for r in d.get("rows", []) if "class_group" in (r.get("scope") or {})}
            drafts[f"drafts/{co}/{a.name}"] = a.read_bytes()
    meta = {"packet": 1, "carrier": cdir.name, "serff": serff, "companies": src.get("companies", []), "line": line,
            "juris": juris, "received": src.get("received"), "files": [{"name": f["name"], "what": f.get("what", "")}
                                                                     for f in src.get("files", [])],
            "carrier_json": {"carrier": car.get("carrier", cdir.name), "name": car.get("name", ""),
                             "approval": car.get("approval", {"signoffs": 1}),
                             "class_groups": {g: car.get("class_groups", {})[g] for g in sorted(groups)
                                              if g in car.get("class_groups", {})}},
            "companies_json": companies_json, "built": time.strftime("%Y-%m-%dT%H:%M:%S")}
    for k in ("sheet", "dev", "stage", "suite"):
        if src.get(k):
            meta[k] = src[k]
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("packet.json", json.dumps(meta, indent=2))
        for f in src.get("files", []):
            z.write(sdir / f["name"], f"sources/{f['name']}")
        for name, b in drafts.items():
            z.writestr(name, b)
    return out


# ----------------------------------------------------------------- ingest

def plan(data: bytes, root: Path = CARRIERS_ROOT) -> dict:
    """Read and check a packet without writing anything: what ingest would write, skip, or refuse."""
    if len(data) > MAX_BYTES:
        raise PacketError(f"the packet is {len(data):,} bytes; the limit is {MAX_BYTES:,}")
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise PacketError("not a zip file") from None
    names = [i.filename.replace("\\", "/") for i in z.infolist() if not i.is_dir()]
    if "packet.json" not in names:
        raise PacketError("no packet.json at the top of the zip")
    try:
        meta = json.loads(z.read("packet.json").decode("utf-8-sig"))
    except ValueError as exc:
        raise PacketError(f"packet.json is not JSON: {exc}") from None
    for k in ("carrier", "serff", "companies", "line", "juris", "files"):
        if not meta.get(k):
            raise PacketError(f"packet.json has no {k!r}")
    carrier, serff = _safe(str(meta["carrier"]), "carrier"), _safe(str(meta["serff"]), "SERFF number")
    if meta["line"] not in ("CF", "GL"):
        raise PacketError(f"line {meta['line']!r} is not CF or GL")
    companies = [str(c) for c in meta["companies"]]
    for c in companies:
        if not _CODE.match(c):
            raise PacketError(f"company code {c!r} is not 2-12 capitals or digits")
    root = Path(root)
    cdir = root / carrier
    problems, writes, skips = [], [], []
    by_name = {}
    for n in names:
        if n == "packet.json":
            continue
        parts = n.split("/")
        if parts[0] == "sources" and len(parts) == 2:
            by_name[("source", _safe(parts[1], "document"))] = n
        elif parts[0] == "drafts" and len(parts) == 3 and parts[1] in companies and parts[2].endswith(".json"):
            by_name[("draft", parts[1], _safe(parts[2], "draft"))] = n
        else:
            problems.append(f"{n}: not where a packet keeps things (sources/<file> or drafts/<COMPANY>/<file>.json, "
                            f"for a company the packet names)")
    listed = {_safe(str(f.get("name", "")), "document") for f in meta["files"]}
    sheet = meta.get("sheet")
    if sheet:
        listed.add(_safe(sheet, "filing sheet"))
    present = {k[1] for k in by_name if k[0] == "source"}
    problems += [f"sources/{n}: listed in packet.json but not in the zip" for n in sorted(listed - present)]
    problems += [f"sources/{n}: in the zip but not listed in packet.json" for n in sorted(present - listed)]

    # carrier, companies, class groups, pins
    cj_new = meta.get("carrier_json") or {}
    car = _read(cdir / "carrier.json") if (cdir / "carrier.json").exists() else None
    if car is None:
        if not cj_new.get("carrier"):
            problems.append(f"carrier {carrier} is new to the store: packet.json needs carrier_json with its name")
        writes.append(f"{carrier}/carrier.json (new carrier)")
        car = {"carrier": carrier, "name": cj_new.get("name", ""), "approval": cj_new.get("approval") or {"signoffs": 1},
               "class_groups": {}}
    for g, codes in (cj_new.get("class_groups") or {}).items():
        have = (car.get("class_groups") or {}).get(g)
        if have is None:
            writes.append(f"{carrier}/carrier.json: class group {g}")
        elif have != codes:
            problems.append(f"class group {g} is already defined differently in {carrier}/carrier.json")
    comp_json = meta.get("companies_json") or {}
    for co in companies:
        p = cdir / co / "company.json"
        new = comp_json.get(co) or {}
        if not p.exists():
            if not new.get("name"):
                problems.append(f"company {co} is new to the store: packet.json needs companies_json.{co} with its name")
            writes.append(f"{carrier}/{co}/company.json (new company)")
            continue
        have = _read(p)
        for ln, by in (new.get("edition_pins") or {}).items():
            for j, pkg in by.items():
                old = ((have.get("edition_pins") or {}).get(ln) or {}).get(j)
                if old is None:
                    writes.append(f"{carrier}/{co}/company.json: {ln} {j} pinned to {pkg}")
                elif old != pkg:
                    problems.append(f"{co} already pins {ln} {j} to {old}, not {pkg}")

    # documents and drafts
    sdir = cdir / "sources" / serff
    for key, n in sorted(by_name.items()):
        b = z.read(n)
        dest = sdir / key[1] if key[0] == "source" else cdir / key[1] / "authored" / key[2]
        rel = dest.relative_to(root).as_posix()
        if key[0] == "draft":
            try:
                d = json.loads(b.decode("utf-8-sig"))
            except ValueError as exc:
                problems.append(f"{n}: not JSON ({exc})")
                continue
            if d.get("company") != key[1] or d.get("line") != meta["line"]:
                problems.append(f"{n}: says company {d.get('company')!r}, line {d.get('line')!r}")
        if dest.exists():
            if _sha(dest.read_bytes()) == _sha(b) or (key[0] == "draft" and _same_draft(dest, b)):
                skips.append(f"{rel} (already in the store, identical)")
            else:
                problems.append(f"{rel} is already in the store and differs: a changed document or draft needs a new "
                                f"name or version")
        else:
            writes.append(rel)
    return {"carrier": carrier, "serff": serff, "line": meta["line"], "juris": meta["juris"], "companies": companies,
            "writes": writes, "skips": skips, "problems": problems, "ok": not problems, "_zip": z, "_meta": meta,
            "_names": by_name, "_car": car}


def _same_draft(dest: Path, b: bytes) -> bool:
    """A draft already ingested was stored as a draft: the same content apart from its status is the same draft."""
    try:
        a, n = _read(dest), json.loads(b.decode("utf-8-sig"))
    except ValueError:
        return False
    a.pop("status", None)
    n.pop("status", None)
    return a == n


def ingest(data: bytes, root: Path = CARRIERS_ROOT) -> dict:
    """Check the packet, then write it: nothing is written if anything is wrong. Returns the report, with the drafts
    written (for the impact preview) and each draft's validation."""
    from .files import load_filing, write_json
    from .validate import validate
    pl = plan(data, root)
    report = {k: v for k, v in pl.items() if not k.startswith("_")}
    if not pl["ok"]:
        report["written"] = []
        return report
    z, meta, root = pl["_zip"], pl["_meta"], Path(root)
    cdir = root / pl["carrier"]
    cdir.mkdir(parents=True, exist_ok=True)
    car = pl["_car"]
    car.setdefault("class_groups", {}).update(meta.get("carrier_json", {}).get("class_groups") or {})
    write_json(cdir / "carrier.json", car)
    for co in pl["companies"]:
        p = cdir / co / "company.json"
        new = (meta.get("companies_json") or {}).get(co) or {}
        have = _read(p) if p.exists() else {k: new[k] for k in ("code", "name", "naic") if k in new}
        have.setdefault("code", co)
        for ln, by in (new.get("edition_pins") or {}).items():
            have.setdefault("edition_pins", {}).setdefault(ln, {}).update(by)
        p.parent.mkdir(parents=True, exist_ok=True)
        write_json(p, have)
    sdir = cdir / "sources" / pl["serff"]
    sdir.mkdir(parents=True, exist_ok=True)
    whats = {f["name"]: f.get("what", "") for f in meta["files"]}
    if meta.get("sheet"):
        whats.setdefault(meta["sheet"], "Our filing sheet: the review of this filing")
    files, drafts = [], []
    for key, n in sorted(pl["_names"].items()):
        b = z.read(n)
        if key[0] == "source":
            (sdir / key[1]).write_bytes(b)
            files.append({"name": key[1], "what": whats.get(key[1], ""), "sha256": _sha(b), "bytes": len(b)})
        else:
            dest = cdir / key[1] / "authored" / key[2]
            dest.parent.mkdir(parents=True, exist_ok=True)
            d = json.loads(b.decode("utf-8-sig"), parse_float=__import__("decimal").Decimal)
            if not dest.exists():
                d["status"] = "draft"                          # never approved by an upload
                write_json(dest, d)
            drafts.append(dest)
    src = {"serff": pl["serff"], "carrier": pl["carrier"], "companies": pl["companies"], "line": meta["line"],
           "juris": meta["juris"], "received": meta.get("received") or time.strftime("%Y-%m-%d"),
           "received_how": "filing packet uploaded in the console", "files": files}
    old = sdir / "source.json"
    if old.exists():                                           # a re-upload: keep what was recorded, add what is new
        prev = _read(old)
        known = {f["name"] for f in prev.get("files", [])}
        prev["files"] = prev.get("files", []) + [f for f in files if f["name"] not in known]
        src = {**src, **prev}
    for k in ("sheet", "dev", "suite"):
        if meta.get(k) and not src.get(k):
            src[k] = meta[k]
    # no "stage": an upload builds nothing, and the store shows where the filing is (Received ... Draft impact)
    old.write_text(json.dumps(src, indent=2), encoding="utf-8")
    checks = []
    for p in drafts:
        try:
            r = validate(load_filing(p))
            checks.append({"draft": p.relative_to(root).as_posix(), "ok": r.ok, "errors": r.errors[:10],
                           "warnings": r.warnings[:10]})
        except Exception as exc:                               # noqa: BLE001  (reported, not raised)
            checks.append({"draft": p.relative_to(root).as_posix(), "ok": False, "errors": [str(exc)[:300]],
                           "warnings": []})
    report.update(written=report["writes"], drafts=[p.as_posix() for p in drafts], validation=checks)
    return report
