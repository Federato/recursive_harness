"""Scan the GL Rules corpus for Territory Pages (CG-T-n) and the ZIP -> territory tables."""
import os, re, json, warnings
from concurrent.futures import ProcessPoolExecutor

SRC = r"C:\Projects\Recursive_Harness_2.0\Commercial Line Manuals\GL\Rules"
HERE = os.path.dirname(os.path.abspath(__file__))

ZIPROW = re.compile(r"(?<!\d)(\d{5})\s+([A-Z][A-Z .'&/-]{1,28}?)\s+(\d{3})(?!\d)")
TERRDEF = re.compile(r"(?<!\d)(\d{3})\s*[–—-]\s*([A-Z][^\n]{2,60})")
CGT = re.compile(r"CG\s*-\s*T\s*-\s*(\d{1,3})(?!\d)")


def one(f):
    warnings.filterwarnings("ignore")
    path = os.path.join(SRC, f)
    try:
        import pypdf
        rd = pypdf.PdfReader(path, strict=False)
        pages = [(p.extract_text() or "") for p in rd.pages]
    except Exception as e:
        return {"file": f, "error": repr(e)[:70]}

    tpages, zips, terrs, defs_, sublines = [], {}, set(), [], set()
    for n, txt in enumerate(pages, 1):
        up = txt.upper()
        if "TERRITORY PAGES" not in up:
            continue
        tpages.append(n)
        for m in CGT.findall(txt):
            pass
        if "TERRITORY" in up and "DEFINITIONS" in up:
            for code, label in TERRDEF.findall(txt):
                defs_.append((code, " ".join(label.split())[:60]))
        for z, name, t in ZIPROW.findall(txt):
            zips[z] = t
            terrs.add(t)
        for s in re.findall(r"Subline\s*Code\s*(\d{3})", txt, re.I):
            sublines.add(s)
    marks = sorted({int(x) for p in pages for x in CGT.findall(p)})
    return {
        "file": f,
        "st": f.split("-")[1],
        "year": int(f.split("-")[2]),
        "pages": len(pages),
        "territory_pages": len(tpages),
        "cgt_markers": (min(marks), max(marks)) if marks else None,
        "zip_rows": len(zips),
        "territories_from_zip": sorted(terrs),
        "territory_defs": defs_[:40],
        "sublines_on_terr_pages": sorted(sublines),
    }


if __name__ == "__main__":
    files = sorted(x for x in os.listdir(SRC) if x.lower().endswith(".pdf"))
    out = {}
    with ProcessPoolExecutor(max_workers=10) as ex:
        for i, r in enumerate(ex.map(one, files)):
            out[r["file"]] = r
            if i % 40 == 0:
                print(i, r["file"], r.get("zip_rows", "ERR"), flush=True)
    json.dump(out, open(os.path.join(HERE, "territory_scan.json"), "w"), indent=0)
    print("DONE", len(out))
