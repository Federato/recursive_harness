"""OI-144 to OI-151: Property read as ISO's live service reads it, on ISO's own answers (ISOComputeGraph C-73).

Three causes behind seven items, each fixed and checked against stored ISO answers, and one item decided:

  A  the write-once table (`cf_engine/resolve/write_once.json`) is the one the corpus builds today
     (`python -m cf_engine.write_once --build`): CW 2023-08 V01 rules that are a reference rule less its guards
  B  CW 2023-08 V01 read with its guards (`cf_engine.write_once`): the Colorado test case's wind or hail factor
     (OI-146, 3,476), New Hampshire's drone earthquake coverage (OI-148, 3,454), California's personal property
     fire (OI-149, 9,472) and the one-risk blanket's message (OI-144) all equal ISO; Wyoming's pollutant
     aggregate, a rule V02 rewrote, keeps ISO's 2,082
  C  a once-only record sent as a list is read without its fields (`cf_engine.iso_reader`): the special
     cause-of-loss extra limit (OI-145, 5,106) and the computer operations message (OI-150) equal ISO; the same
     record sent as an object is read as before
  D  a bare `ForEach` led by `FromList` loops over its parameter list (OI-147): Alabama 2021-03 rates 1,174, as ISO
  E  GL is untouched: a GL book carries no `write_once`; `FromList` is filed nowhere in GL

OI-151 (ISO fails on a loss cost multiplier below 1) is decided, not fixed: ours keeps rating (OPEN-ITEMS).

Run: python tests/verify_oi144_151.py
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from cf_engine import rating as cf  # noqa: E402
from cf_engine import write_once  # noqa: E402
from console import store  # noqa: E402

results: list[tuple[bool, str]] = []


def check(label: str, ok: bool) -> None:
    results.append((bool(ok), label))
    print(("  ok    " if ok else "  FAIL  ") + label)


def stored(h: str) -> tuple[dict, dict]:
    """(request, ISO's response body) from the answer store, by hash start."""
    req = next(store.ANSWERS.glob(f"{h}*_request.json"))
    resp = req.with_name(req.name.replace("_request.json", "_response.json"))
    body = json.loads(resp.read_text(encoding="utf-8-sig"))
    return json.loads(req.read_text(encoding="utf-8-sig")), body.get("Body") or body


def iso_premium(body: dict) -> str:
    cp = body["CommercialProperty"]
    cp = cp[0] if isinstance(cp, list) else cp
    return str(int(float(cp["ErcCalculatedTotalPremium"])))


def iso_messages(body: dict) -> list[str]:
    return sorted(m.get("Description", "") for kind in (body.get("RatingMessages") or {}).values()
                  if isinstance(kind, list) for m in kind if isinstance(m, dict))


def same_as_iso(h: str, label: str, want: str | None = None) -> None:
    req, iso = stored(h)
    r = cf.rate(copy.deepcopy(req))
    prem, msgs = iso_premium(iso), iso_messages(iso)
    ok = r.premium == prem and sorted(r.ip.messages) == msgs and (want is None or prem == want)
    check(f"{label}: ours {r.premium}, ISO {prem}; messages {'equal' if sorted(r.ip.messages) == msgs else 'differ'}",
          ok)


print("A  the write-once table")
built = write_once.build()
held = json.loads(write_once.TABLE.read_text(encoding="utf-8"))
check(f"A  current: {built['counts']['rules']} V01 rules, {built['counts']['writes']} writes, "
      f"{built['counts']['differ']} read as filed", built == held)

print("B  CW 2023-08 V01 with its guards")
same_as_iso("6e4518d8909f", "B  OI-146 CO 2023-08 STC_CP000013797, wind or hail factor 0.74", "3476")
same_as_iso("c22a525f6803", "B  OI-146 NV 2023-11 STC_CP000015041")
same_as_iso("827cabae7e39", "B  OI-146 NM 2024-04 STC_CP000015565, a 2% wind deductible")
same_as_iso("d19a64c354a5", "B  OI-148 NH 2023-08 STC_CP000014706, drone earthquake $0", "3454")
same_as_iso("379a4cf9ee22", "B  OI-149 CA 2024-04 STC_CP000016011, personal property fire $0", "9472")
same_as_iso("b1e858a14024", "B  OI-144 IA 2023-08 one-risk blanket, ISO's message")
same_as_iso("4b0244f5a4b0", "B  WY 2023-08 STC_CP000014517, the pollutant aggregate V02 rewrote, as filed", "2082")

print("C  a once-only record sent as a list")
same_as_iso("90911cd42b4e", "C  OI-145 CO 2020-12 patterns, dies, molds and forms sent as a list", "5106")
same_as_iso("bad1a5261877", "C  OI-150 ND 2027-01 computer operations sent as a list, no message")
req, _ = stored("90911cd42b4e")
obj = copy.deepcopy(req)
moved = 0
for cp in obj["body"]["CommercialProperty"]:
    stack = [cp]
    while stack:
        n = stack.pop()
        for k, v in list(n.items()):
            if k.startswith("CommercialPropertyPersonalPropertySpecialCOL") and isinstance(v, list) and len(v) == 1:
                n[k] = v[0]
                moved += 1
            elif isinstance(v, dict):
                stack.append(v)
            elif isinstance(v, list):
                stack.extend(x for x in v if isinstance(x, dict))
as_list, as_obj = cf.rate(copy.deepcopy(req)), cf.rate(obj)
check(f"C  the same record sent as an object is read: {moved} moved, ours {as_obj.premium} against {as_list.premium} "
      f"as a list", moved and as_obj.premium != as_list.premium)

print("D  a bare ForEach over a parameter list")
same_as_iso("008865a9626d", "D  OI-147 AL 2021-03, ours refused, ISO 1,174", "1174")

print("E  GL untouched")
from gl_engine.resolve.book import ResolvedBook  # noqa: E402
check("E  GL's book (ResolvedBook) carries no write_once", getattr(ResolvedBook, "write_once", None) is None)
gl_from_list = 0
import os  # noqa: E402
from gl_engine.erc.discovery import read_text  # noqa: E402
gl_root = Path(os.environ.get("GL_ERC_ROOT", r"C:\FederatoProjects\ISO_ERC_Files\General_Liability"))
for f in gl_root.rglob("*.Rule.xml"):
    if "<rul:FromList" in read_text(f):                  # past the 260-character limit too (OI-136)
        gl_from_list += 1
check(f"E  FromList in GL rule files: {gl_from_list}", gl_from_list == 0)

passed = sum(ok for ok, _ in results)
print(f"\n{'PASS' if passed == len(results) else 'FAIL'}: {passed} of {len(results)}")
sys.exit(0 if passed == len(results) else 1)
