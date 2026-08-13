import os, subprocess
from concurrent.futures import ProcessPoolExecutor

SRC = r"C:\Projects\Recursive_Harness_2.0\Commercial Line Manuals\GL\LossCosts"
HERE = os.path.dirname(os.path.abspath(__file__))
RO = os.path.join(HERE, "lc_text")
LO = os.path.join(HERE, "lc_layout")


def one(f):
    src = os.path.join(SRC, f)
    msgs = []
    for outdir, args in ((RO, []), (LO, ["-layout"])):
        dst = os.path.join(outdir, f[:-4] + ".txt")
        if os.path.exists(dst) and os.path.getsize(dst) > 200:
            continue
        txt = ""
        try:
            r = subprocess.run(["pdftotext"] + args + [src, "-"],
                               capture_output=True, timeout=900)
            txt = r.stdout.decode("utf-8", "replace")
        except Exception:
            txt = ""
        if len(txt.strip()) < 200:
            try:
                import pypdf, warnings
                warnings.filterwarnings("ignore")
                rd = pypdf.PdfReader(src, strict=False)
                txt = "\n".join((p.extract_text() or "") for p in rd.pages)
            except Exception as e:
                msgs.append((f, str(args), repr(e)[:70]))
        if len(txt.strip()) < 200:
            msgs.append((f, str(args), "empty"))
        open(dst, "w", encoding="utf-8").write(txt)
    return f, msgs


if __name__ == "__main__":
    os.makedirs(RO, exist_ok=True); os.makedirs(LO, exist_ok=True)
    files = sorted(x for x in os.listdir(SRC) if x.lower().endswith(".pdf"))
    todo = [f for f in files
            if not (os.path.exists(os.path.join(RO, f[:-4] + ".txt"))
                    and os.path.getsize(os.path.join(RO, f[:-4] + ".txt")) > 200
                    and os.path.exists(os.path.join(LO, f[:-4] + ".txt"))
                    and os.path.getsize(os.path.join(LO, f[:-4] + ".txt")) > 200)]
    print(len(todo), "to do of", len(files), flush=True)
    fails = []
    with ProcessPoolExecutor(max_workers=10) as ex:
        for i, (f, m) in enumerate(ex.map(one, todo)):
            fails += m
            if i % 25 == 0:
                print(i, f, flush=True)
    print("DONE fails:", len(fails))
    for x in fails:
        print("  ", x)
