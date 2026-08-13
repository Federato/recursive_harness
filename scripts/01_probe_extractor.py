"""Record, per PDF, whether pdftotext -layout works or whether the file needs the
pypdf fallback (which discards column geometry)."""
import os, subprocess, json
from concurrent.futures import ProcessPoolExecutor

SRC = r"C:\Projects\Recursive_Harness_2.0\Commercial Line Manuals\GL\LossCosts"
HERE = os.path.dirname(os.path.abspath(__file__))


def probe(f):
    src = os.path.join(SRC, f)
    try:
        r = subprocess.run(["pdftotext", "-layout", "-f", "1", "-l", "20", src, "-"],
                           capture_output=True, timeout=300)
        out = r.stdout.decode("utf-8", "replace")
        err = r.stderr.decode("utf-8", "replace")
    except Exception as e:
        return f, "ERROR", repr(e)[:60]
    if len(out.strip()) < 200:
        return f, "PYPDF_FALLBACK", err.strip().splitlines()[0][:90] if err.strip() else "empty output"
    return f, "PDFTOTEXT_LAYOUT", ""


if __name__ == "__main__":
    files = sorted(x for x in os.listdir(SRC) if x.lower().endswith(".pdf"))
    res = {}
    with ProcessPoolExecutor(max_workers=10) as ex:
        for f, mode, note in ex.map(probe, files):
            res[f] = {"mode": mode, "note": note}
    json.dump(res, open(os.path.join(HERE, "lc_extractor.json"), "w"), indent=0)
    from collections import Counter
    print(Counter(v["mode"] for v in res.values()))
    print(Counter(v["note"] for v in res.values() if v["mode"] != "PDFTOTEXT_LAYOUT").most_common(5))
