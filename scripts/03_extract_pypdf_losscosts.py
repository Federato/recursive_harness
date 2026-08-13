import os, warnings
from concurrent.futures import ProcessPoolExecutor

SRC = r"C:\Projects\Recursive_Harness_2.0\Commercial Line Manuals\GL\LossCosts"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "lc_pypdf")


def one(f):
    dst = os.path.join(OUT, f[:-4] + ".txt")
    if os.path.exists(dst) and os.path.getsize(dst) > 200:
        return f, "cached"
    warnings.filterwarnings("ignore")
    try:
        import pypdf
        rd = pypdf.PdfReader(os.path.join(SRC, f), strict=False)
        parts = []
        for i, p in enumerate(rd.pages):
            parts.append(f"\n<<<PAGE {i+1}>>>\n" + (p.extract_text() or ""))
        txt = "\n".join(parts)
    except Exception as e:
        open(dst, "w", encoding="utf-8").write("")
        return f, repr(e)[:70]
    open(dst, "w", encoding="utf-8").write(txt)
    return f, ("ok" if len(txt.strip()) > 200 else "empty")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    files = sorted(x for x in os.listdir(SRC) if x.lower().endswith(".pdf"))
    from collections import Counter
    c = Counter()
    with ProcessPoolExecutor(max_workers=10) as ex:
        for i, (f, s) in enumerate(ex.map(one, files)):
            c[s] += 1
            if s not in ("ok", "cached"):
                print("  !", f, s, flush=True)
            if i % 50 == 0:
                print(i, f, flush=True)
    print("DONE", c)
