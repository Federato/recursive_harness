"""Compile a validated, approved filing into ISO's table shape -- and read it back.

**Compile** writes, per jurisdiction, one directory the engine will read (P2):

  * `GroupLCM` (CF) or `LCM` (GL): one row per explicit LCM key the filing
    reaches, with the composed factor, its mode, and the rows it came from.
  * `Rate Tables/<ISO table>.Company`: the same, for each ISO table the filing
    overrides, keyed exactly as ISO keys that table.
  * `manifest.json`: dates, the ISO edition each date resolves to, the class
    groups as compiled, the policy-level items (`policy`: a minimum premium, a
    terrorism share -- one value each, so no table), and per authored row its
    citation and note -- the only things a table cannot carry.

Each table has a `.CompanyDef.RateTableDef.xml` in ISO's own definition schema,
so the engine's table reader loads it like any ISO table.

**Show** rebuilds the authored rows from the compiled TABLES, not from a stored
copy: for each row id in the `Explain` column it finds the narrowest scope whose
expansion, less the keys more specific rows took over, is exactly the keys that
row reached. That is the I1 guarantee -- the compiled form says what people
wrote -- and `verify_deviations_files.py` holds it to that (T10).
"""
from __future__ import annotations

import csv
import dataclasses
import io
import shutil
from decimal import Decimal
from itertools import combinations
from pathlib import Path
from xml.sax.saxutils import quoteattr

from . import iso
from .config import LCM_TARGETS, RATING_BASES
from .expand import Context, canon, compose, expand, lcm_header
from .files import compiled_dir, dumps, read_json, write_json
from .validate import Report, approval

_NS = "http://www.verisk.com/iso/erc/RateTable"


class CompileError(RuntimeError):
    pass


# ------------------------------------------------------------- writing

def _csv(header: list[str], rows: list[list[str]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, quoting=csv.QUOTE_ALL, lineterminator="\r\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def _def_xml(code: str, keys: list[tuple[str, str]], values: list[tuple[str, str]]) -> str:
    kc = "".join(f'\t\t<rt:KeyCol Name={quoteattr(n)} Type={quoteattr(t)} CaseInsensitive="false" />\r\n'
                 for n, t in keys)
    vc = "".join(f'\t\t<rt:ValueCol Name={quoteattr(n)} Type={quoteattr(t)} />\r\n'
                 for n, t in values)
    return (f'<rt:RateTable xmlns:rt="{_NS}">\r\n'
            f'\t<rt:MetaData>\r\n\t\t<rt:MetaDataCode>{code}</rt:MetaDataCode>\r\n'
            f'\t\t<rt:MetaDataCode>CompanyDeviation</rt:MetaDataCode>\r\n\t</rt:MetaData>\r\n'
            f'\t<rt:KeyCols>\r\n{kc}\t</rt:KeyCols>\r\n'
            f'\t<rt:ValueCols>\r\n{vc}\t</rt:ValueCols>\r\n</rt:RateTable>')


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig", newline="")


def lcm_table_name(line: str) -> str:
    return "GroupLCM" if line == "CF" else "LCM"


#: The class key an "all other" row is composed for, standing in for every class the edition lacked at compile.
UNLISTED = "*"


def unlisted_lcms(rows, ctx: Context) -> dict:
    """D22: what a class ISO adds after the filing compiled is charged -- the rows written for no class and no
    class group ("all other classes"), composed as for any class, until a filing says otherwise.
    {"<target>[|<basis>]": [value, mode, explain]}; empty when the filing has no such row."""
    u = dataclasses.replace(ctx, classes=(UNLISTED,))
    mine = [r for r in rows if r.target.startswith("LCM:") and not {"class", "class_group"} & set(r.scope)]
    composed, _ = compose([expand(r, u) for r in mine])
    return {"|".join(k[:-1]): [canon(c.value), c.mode, c.explain]
            for k, c in sorted(composed.get(("LCM",), {}).items())}


def compile_filing(rep: Report, *, require_approval: bool = True) -> list[Path]:
    """Write the compiled directories for every jurisdiction. Returns them."""
    f = rep.filing
    if not rep.ok:
        raise CompileError(f"{f.ref} does not validate:\n  " + "\n  ".join(rep.errors))
    if require_approval:
        ok, why = approval(f)
        if not ok:
            raise CompileError(f"{f.ref} is not approved: {why}. Only approved "
                               f"versions compile (M4).")
    out = []
    header = {k: v for k, v in f.raw.items() if k not in ("rows",)}
    for j, (ctx, exps, composed, ed_new, ed_ren) in rep.plans.items():
        d = compiled_dir(f.company_dir, f.line, j, f.ref)
        if d.exists():
            shutil.rmtree(d)            # derived content: always rebuilt whole
        tables, policy = {}, {}
        for space, keys in sorted(composed.items()):
            if space[0] == "POLICY":                 # B-21: one value per policy, kept in the manifest
                c = keys[()]
                policy[space[1]] = [canon(c.value), c.mode, c.explain]
            elif space[0] == "LCM":
                name = lcm_table_name(f.line)
                kh = lcm_header(f.line)
                rows = [[j, *k, canon(c.value), c.mode, c.explain]
                        for k, c in sorted(keys.items())]
                _write(d / f"{name}.Company.RateTable.csv",
                       _csv(kh + ["Factor", "Mode", "Explain"], rows))
                _write(d / f"{name}.CompanyDef.RateTableDef.xml",
                       _def_xml(f"RateTable{name}Company", [(h, "string") for h in kh],
                                [("Factor", "decimal"), ("Mode", "string"), ("Explain", "string")]))
                tables[f"{name}.Company"] = {"keys": kh, "rows": len(rows)}
            else:
                _, tname, col = space
                t = iso.table(f.line, j, ctx.date, tname)
                kn = iso.table_keys(t)
                kh = ["StateCode"] + kn
                rows = [[j, *k, canon(c.value), c.mode, c.explain]
                        for k, c in sorted(keys.items())]
                base = f"Rate Tables/{tname}.Company"
                _write(d / f"{base}.RateTable.csv", _csv(kh + [col, "Mode", "Explain"], rows))
                _write(d / f"Rate Tables/{tname}.CompanyDef.RateTableDef.xml",
                       _def_xml(f"RateTable{tname}Company",
                                [(h, t.definition.type_of(h)) for h in kh],
                                [(col, t.definition.type_of(col)), ("Mode", "string"),
                                 ("Explain", "string")]))
                tables[f"{base}"] = {"iso_table": tname, "column": col, "keys": kh,
                                     "iso_package": t.package, "rows": len(rows)}
        manifest = {
            "filing": f.filing, "version": f.version, "ref": f.ref,
            "company": f.company, "line": f.line, "juris": j,
            "new_eff": str(f.raw["new_eff"]), "renewal_eff": str(f.raw["renewal_eff"]),
            "iso_edition": {"new": ed_new, "renewal": ed_ren},
            "header": header,
            "class_groups": ctx.class_groups,
            "tables": tables,
            "policy": policy,
            "unlisted_class_lcm": unlisted_lcms(f.rows, ctx),
            "rows": [{"id": r.id, "cite": r.cite, "note": r.note} for r in f.rows],
        }
        write_json(d / "manifest.json", manifest)
        out.append(d)
    return out


# ------------------------------------------------------------- reading

def _read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    text = path.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    return rows[0], rows[1:]


def _tokens(explain: str) -> list[tuple[str, str, str]]:
    out = []
    for t in explain.split(" * "):
        rid, mode, value = t.rsplit(":", 2)
        out.append((rid, mode, value))
    return out


def _reach(header, rows, nkeys) -> tuple[dict, dict]:
    """Per row id: (mode, value, keys reached); per key: the id that set its base."""
    ids: dict = {}
    winner: dict = {}
    ex = header.index("Explain")
    for r in rows:
        key = tuple(r[1:1 + nkeys])
        toks = _tokens(r[ex])
        if toks[0][1] == "replace":
            winner[key] = toks[0][0]
        for rid, mode, value in toks:
            ent = ids.setdefault(rid, [mode, value, set()])
            ent[2].add(key)
    return ids, winner


def _pick(keys: set, others_took: set, candidates) -> dict | None:
    """The narrowest candidate scope that explains exactly these keys."""
    best = None
    for scope, E in candidates:
        if keys <= E and (E - keys) <= others_took:
            rank = (len(E), len(scope))
            if best is None or rank < best[0]:
                best = (rank, scope)
    return best[1] if best else None


def _lcm_candidates(line, ctx: Context, keys: set):
    targets = list(LCM_TARGETS[line])
    classes = sorted({k[-1] for k in keys})
    class_scopes = [({}, list(ctx.classes))]
    class_scopes += [({"class_group": g}, codes) for g, codes in sorted(ctx.class_groups.items())]
    if len(classes) == 1:
        class_scopes.append(({"class": classes[0]}, classes))
    for tgt in targets + ["All"]:
        tset = targets if tgt == "All" else [tgt]
        for cs, codes in class_scopes:
            if line == "CF":
                for b in [None] + list(RATING_BASES):
                    bases = list(RATING_BASES) if b is None else [b]
                    scope = dict(cs, **({"rating_basis": b} if b else {}))
                    E = {(t, bb, c) for t in tset for bb in bases for c in codes}
                    yield (tgt, scope), E
            else:
                yield (tgt, dict(cs)), {(t, c) for t in tset for c in codes}


def show(company_dir: Path, line: str, ref: str) -> dict:
    """Rebuild a filing version's authored form from its compiled tables."""
    base = Path(company_dir) / "compiled" / line
    dirs = sorted(p for p in base.glob(f"*/{ref}") if (p / "manifest.json").exists())
    if not dirs:
        raise CompileError(f"no compiled {line} directories for {ref} under {base}")
    rebuilt: dict[str, dict] = {}
    juris: list[str] = []
    manifest = None
    for d in dirs:
        manifest = read_json(d / "manifest.json")
        j = manifest["juris"]
        juris.append(j)
        ctx = Context(line, j, manifest["new_eff"], manifest["class_groups"])
        for tname, meta in manifest["tables"].items():
            header, rows = _read_csv(d / f"{tname}.RateTable.csv")
            nkeys = len(meta["keys"]) - 1
            ids, winner = _reach(header, rows, nkeys)
            if "iso_table" not in meta:
                for rid, (mode, value, keys) in ids.items():
                    took = {k for k, w in winner.items() if w != rid}
                    pick = _pick(keys, took, _lcm_candidates(line, ctx, keys))
                    row = ({"target": f"LCM:{pick[0]}", "scope": pick[1]} if pick
                           else {"target": "LCM:?", "scope": {"unexplained_keys": len(keys)}})
                    row.update(value=Decimal(value), mode=mode)
                    _merge(rebuilt, rid, row, j)
            else:
                t = iso.table(line, j, manifest["new_eff"], meta["iso_table"])
                kn = meta["keys"][1:]
                idx = [t.col(k) for k in kn]
                iso_keys = [tuple(str(r[i]) for i in idx) for r in t.rows]
                for rid, (mode, value, keys) in ids.items():
                    took = {k for k, w in winner.items() if w != rid}
                    const = [i for i in range(len(kn)) if len({k[i] for k in keys}) == 1]
                    first = next(iter(keys))
                    cands = []
                    for n in range(len(const) + 1):
                        for sub in combinations(const, n):
                            E = {k for k in iso_keys if all(k[i] == first[i] for i in sub)}
                            cands.append(({kn[i]: first[i] for i in sub}, E))
                    scope = _pick(keys, took, cands)
                    row = {"target": f"TABLE:{meta['iso_table']}.{meta['column']}",
                           "scope": scope if scope is not None else {"unexplained_keys": len(keys)},
                           "value": Decimal(value), "mode": mode}
                    _merge(rebuilt, rid, row, j)
        for target, (value, mode, explain) in manifest.get("policy", {}).items():
            for rid, _, _ in _tokens(explain):
                _merge(rebuilt, rid, {"target": target, "scope": {}, "value": Decimal(value), "mode": mode}, j)
    meta_rows = {r["id"]: r for r in manifest["rows"]}
    rows = []
    for rid in sorted(rebuilt, key=lambda r: int(r.rsplit("#", 1)[1])):
        row = rebuilt[rid]["row"]
        m = meta_rows.get(rid, {})
        if m.get("cite"):
            row["cite"] = m["cite"]
        if m.get("note"):
            row["note"] = m["note"]
        if rebuilt[rid]["disagree"]:
            row["disagrees_in"] = rebuilt[rid]["disagree"]
        rows.append(row)
    missing = [r for r in meta_rows if r not in rebuilt]
    out = dict(manifest["header"])
    out["juris_compiled"] = juris
    out["rows"] = rows
    if missing:
        out["rows_with_no_effect"] = missing
    return out


def _merge(rebuilt: dict, rid: str, row: dict, juris: str) -> None:
    got = rebuilt.get(rid)
    if got is None:
        rebuilt[rid] = {"row": row, "disagree": []}
    elif got["row"] != row:
        got["disagree"].append(juris)


def show_text(data: dict) -> str:
    return dumps(data)
