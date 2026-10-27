"""Everything that must be true of a filing before it may compile.

`validate` collects every problem it can find in one pass, so a person fixes a
filing once rather than one error at a time. Each problem names the row it
belongs to. Nothing here changes a file.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import iso
from .config import LCM_BANDS, LCM_TARGETS, LINES, MODES, STATUSES
from .expand import Context, Expanded, compose, expand, parse_target
from .files import Filing, carrier_json, class_groups, expand_codes, workflow_status


@dataclass
class Report:
    filing: Filing
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    juris: list[str] = field(default_factory=list)
    #: per jurisdiction: (Context, [Expanded], composed)
    plans: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def _date(s, what: str, errors: list[str]):
    try:
        return date.fromisoformat(str(s))
    except (TypeError, ValueError):
        errors.append(f"{what} {s!r} is not a date (YYYY-MM-DD)")
        return None


def resolve_juris(f: Filing, errors: list[str]) -> list[str]:
    """The filing's jurisdictions, with the all-states shortcut expanded (I2).

    `"juris": ["ALL"]` means every jurisdiction the line has on `juris_asof`
    (the day it was authored), minus `opt_out`. A jurisdiction ISO adds later is
    NOT swept in: a filing covers what existed when it was written.
    """
    raw = f.raw.get("juris")
    if not isinstance(raw, list) or not raw:
        errors.append("juris must be a non-empty list of states, or [\"ALL\"]")
        return []
    if raw == ["ALL"]:
        asof = f.raw.get("juris_asof")
        if not asof or _date(asof, "juris_asof", errors) is None:
            if not asof:
                errors.append("juris [\"ALL\"] needs juris_asof: the day the states were taken")
            return []
        states = iso.jurisdictions(f.line, asof)
        out = [j for j in states if j not in set(f.raw.get("opt_out") or [])]
        for j in f.raw.get("opt_out") or []:
            if j not in states:
                errors.append(f"opt_out {j!r} is not a jurisdiction on {asof}")
        return out
    if "ALL" in raw:
        errors.append("\"ALL\" cannot be mixed with named states")
        return []
    return [str(j).upper() for j in raw]


def validate(f: Filing) -> Report:
    rep = Report(f)
    E, raw = rep.errors, f.raw

    # ------------------------------------------------------------ header
    for k in ("filing", "company", "line", "version", "status", "new_eff",
              "renewal_eff", "rows"):
        if k not in raw:
            E.append(f"missing {k!r}")
    if E:
        return rep
    if f.line not in LINES:
        E.append(f"line {f.line!r} is not one of {', '.join(LINES)}")
        return rep
    if not isinstance(f.version, int) or f.version < 1:
        E.append(f"version must be a whole number from 1 (got {f.version!r})")
    if raw["status"] not in STATUSES:
        E.append(f"status {raw['status']!r} is not one of {', '.join(STATUSES)}")
    if f.path.name != f"{f.ref}.json":
        E.append(f"file is named {f.path.name}; a filing version lives in {f.ref}.json")
    if f.company_dir.name != f.company:
        rep.warnings.append(f"company {f.company!r} is filed under folder {f.company_dir.name!r}")

    new = _date(raw["new_eff"], "new_eff", E)
    ren = _date(raw["renewal_eff"], "renewal_eff", E)
    if new and ren and ren < new:
        E.append(f"renewal_eff {ren} is before new_eff {new}")
    if raw.get("approved"):
        appr = _date(raw["approved"], "approved", E)
        if appr and new and appr > new:
            rep.warnings.append(f"approved {appr} is after new_eff {new}")

    rep.juris = resolve_juris(f, E)
    if not f.rows:
        E.append("a filing needs at least one row")
    if E:
        return rep

    # ---------------------------------------------------------- each row
    for r in f.rows:
        tag = r.id.rsplit("#", 1)[-1]
        if r.mode not in MODES:
            E.append(f"row #{tag}: mode {r.mode!r} is not replace or multiply")
        if r.value is None or r.value <= 0:
            E.append(f"row #{tag}: value must be a number above 0 (got {r.value!r})")
        t = parse_target(r.target, f.line)
        if t and t[0] == "LCM" and r.value is not None and r.value > 0 and r.mode == "replace":
            names = LCM_TARGETS[f.line] if t[1] == "All" else (t[1],)
            for n in names:
                lo, hi = LCM_BANDS[(f.line, n)]
                if not lo <= r.value <= hi and not r.note:
                    E.append(f"row #{tag}: LCM {r.value} for {n} is outside "
                             f"{lo}-{hi}; add a note saying why")
                    break
    if E:
        return rep

    # -------------------------------------------------- per jurisdiction
    groups_raw = class_groups(f.carrier_dir, f.company_dir)
    for j in rep.juris:
        try:
            ed_new = iso.edition(f.line, j, str(new))
            ed_ren = iso.edition(f.line, j, str(ren))
        except Exception as e:
            E.append(f"{j}: no {f.line} edition resolves on {new} ({e})")
            continue
        if ed_new != ed_ren:
            rep.warnings.append(f"{j}: new and renewal dates fall in different ISO "
                                f"editions ({ed_new['state']} / {ed_ren['state']})")
        universe = iso.class_codes(f.line, j, str(new))
        # Only the groups this filing names are expanded and checked: a carrier
        # keeps Property and GL groups side by side, and a Property group's codes
        # mean nothing against GL's class list.
        used = {str(r.scope["class_group"]) for r in f.rows if "class_group" in r.scope}
        groups = {}
        for name, spec in groups_raw.items():
            if name not in used:
                continue
            codes, probs = expand_codes(spec, universe)
            for p in probs:
                E.append(f"{j}: class group {name}: {p}")
            groups[name] = codes
        ctx = Context(f.line, j, str(new), groups, universe)
        exps: list[Expanded] = [expand(r, ctx) for r in f.rows]
        for e in exps:
            for p in e.problems:
                E.append(f"{j}: row #{e.row.id.rsplit('#', 1)[-1]}: {p}")
            for w in e.notes:
                if w not in rep.warnings:
                    rep.warnings.append(f"row #{e.row.id.rsplit('#', 1)[-1]}: {w}")
        composed, conflicts = compose(exps)
        for c in conflicts:
            E.append(f"{j}: {c}")
        rep.plans[j] = (ctx, exps, composed, ed_new, ed_ren)
    return rep


def approval(f: Filing) -> tuple[bool, str]:
    """Is this version approved, by the file AND the workflow log (D6)?"""
    need = int(carrier_json(f.carrier_dir).get("approval", {}).get("signoffs", 1))
    wf = workflow_status(f.company_dir, f.filing, f.version, need)
    if f.raw.get("status") != "approved":
        return False, f"the file's status is {f.raw.get('status')!r}, not 'approved'"
    if wf["status"] != "approved":
        got = len(wf["signers"])
        return False, (f"the workflow log says {wf['status']!r} "
                       f"({got} of {need} sign-off{'s' if need != 1 else ''})")
    return True, "approved by " + ", ".join(wf["signers"])
