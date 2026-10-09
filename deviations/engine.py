"""The company layer the engine rates through (DEVIATIONS-PLAN.md §4, P2).

Nothing here runs unless a request names a writing company: an ISO-only rating
never imports this module (I4). With a company, three things change and nothing
else does:

  * **4a resolution** -- the company's filing in force for the state, line and
    new/renewal date is picked from its compiled files; an edition pin, if the
    company has one, chooses the ISO package.
  * **4b LCMs** -- submitted LCMs are removed (D13) and the company's are written
    onto each record before ISO's rules run. In Property the record carries the
    Group I LCM (G2), and each coverage group's rate product reads the
    company's LCM for that group instead (4b', D17), through the interpreter's
    `group_lcm` hook.
  * **4c company tables** -- `CompanyBook` stands in front of the ISO book and
    answers `table()` for the tables the filing overrides, composed at lookup:
    replace wins, multiply scales ISO's value, untouched keys are ISO's.
    `parent_table()` is never overridden (I3).

A request this layer cannot honour is refused with the reason (`Refused`),
never rated as technical without saying so.
"""
from __future__ import annotations

import csv
import dataclasses
import io
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from gl_engine.interp.values import InterpretError

from . import iso
from .config import CARRIERS_ROOT
from .files import carrier_json, company_json, read_json, workflow_status


class Refused(InterpretError):
    """A request the company layer cannot rate as asked; the outcome is refused."""
    outcome_kind = "deviation refused"

    def __init__(self, msg: str):
        super().__init__(msg, "deviations", "")
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


# ------------------------------------------------------------------ the plan

@dataclass
class Plan:
    """Everything one rating needs from a company's files."""

    line: str
    company: str
    juris: str
    date: str                                  # the request's effective date, YYYY-MM-DD
    policy_type: str                           # "New" | "Renewal"
    company_dir: Path
    pin: str | None = None
    filing_dir: Path | None = None
    manifest: dict | None = None
    #: CF: (group, rating basis, class) -> (value, mode, explain)
    group_lcm: dict = field(default_factory=dict)
    #: GL: (coverage, class) -> (value, mode, explain)
    lcm: dict = field(default_factory=dict)
    #: ISO table name -> {"col", "keys", "rows": {key tuple: (value, mode, explain)}}
    overrides: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    #: Track which fields the company's inputs reach (T4, P3). Off for every ordinary rating.
    track: bool = False
    #: id(record node) -> (class, rating type) as submitted, fixed before the rules run: the record LCM and every
    #: group LCM on that record use the same class, the one ISO's service sees on the request (P3 finding: a
    #: contents record ISO's rules later stamp with the building's class kept two classes otherwise).
    record_class: dict = field(default_factory=dict)

    @property
    def ref(self) -> str | None:
        return self.manifest["ref"] if self.manifest else None

    def warn(self, msg: str) -> None:
        if msg not in self.warnings:
            self.warnings.append(msg)

    def without(self, *, lcm: bool = False, tables=()) -> "Plan":
        """A copy with parts removed: the waterfall rates the deviations one step at a time."""
        p = dataclasses.replace(self, warnings=list(self.warnings))
        if lcm:
            p.group_lcm, p.lcm = {}, {}
        if tables:
            p.overrides = {k: v for k, v in self.overrides.items() if k not in set(tables)}
        return p


def find_company(code: str, root: Path = CARRIERS_ROOT) -> Path:
    hits = sorted(p.parent for p in Path(root).glob(f"*/{code}/company.json"))
    if not hits:
        raise Refused(f"writing company {code!r} is not known under {root}")
    if len(hits) > 1:
        raise Refused(f"writing company {code!r} is filed under more than one carrier: "
                      + ", ".join(str(h.parent.name) for h in hits))
    return hits[0]


def _read_table(path: Path) -> tuple[list[str], list[list[str]]]:
    rows = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8-sig"))))
    return rows[0], rows[1:]


def select_filing(company_dir: Path, line: str, juris: str, date: str,
                  policy_type: str) -> Path | None:
    """The compiled filing in force: approved now (file and log), effective by
    `date` for this policy type; the latest effective date wins, then the
    highest version. One filing per company, state and line in v1."""
    base = Path(company_dir) / "compiled" / line / juris
    need = int(carrier_json(Path(company_dir).parent).get("approval", {}).get("signoffs", 1))
    best = None
    for m in sorted(base.glob("*/manifest.json")):
        man = read_json(m)
        if man["header"].get("status") != "approved":
            continue
        if workflow_status(company_dir, man["filing"], man["version"], need)["status"] != "approved":
            continue                       # withdrawn or rejected since it compiled: not in force
        eff = man["renewal_eff"] if policy_type == "Renewal" else man["new_eff"]
        if eff > date:
            continue
        rank = (eff, man["version"])
        if best is None or rank > best[0]:
            best = (rank, m.parent)
    return best[1] if best else None


def plan_for(line: str, company: str, juris: str, date: str, policy_type: str | None,
             root: Path = CARRIERS_ROOT) -> Plan:
    cdir = find_company(company, root)
    pt = policy_type or "New"
    if pt not in ("New", "Renewal"):
        raise Refused(f"header.PolicyType {pt!r} is not New or Renewal")
    plan = Plan(line, company, juris, date, pt, cdir)
    if policy_type is None:
        plan.warn("header.PolicyType not given: rated as New business (O1)")
    plan.pin = ((company_json(cdir).get("edition_pins") or {}).get(line) or {}).get(juris)
    d = select_filing(cdir, line, juris, date, pt)
    if d is None:
        plan.warn(f"{company} has no approved {line} filing in force in {juris} for "
                  f"{pt.lower()} business on {date}: carrier equals technical")
        return plan
    plan.filing_dir, plan.manifest = d, read_json(d / "manifest.json")
    for tname, meta in plan.manifest["tables"].items():
        header, rows = _read_table(d / f"{tname}.RateTable.csv")
        n = len(meta["keys"])
        vi = n                          # value column follows the keys
        entries = {tuple(r[1:n]): (Decimal(r[vi]), r[vi + 1], r[vi + 2]) for r in rows}
        if "iso_table" in meta:
            plan.overrides[meta["iso_table"]] = {"col": meta["column"], "keys": meta["keys"][1:],
                                                 "rows": entries}
        elif line == "CF":
            plan.group_lcm = entries
        else:
            plan.lcm = entries
    return plan


def book_for(plan: Plan):
    """The ISO book this rating uses: the pinned package, or the edition in force."""
    if not plan.pin:
        return iso.book(plan.line, plan.juris, plan.date)
    m = re.match(r"^(CF|GL)_([A-Z]{2})_(\d{8})_(V\d+)$", plan.pin)
    if not m or m.group(1) != plan.line or m.group(2) != plan.juris:
        raise Refused(f"edition pin {plan.pin!r} is not a {plan.line} {plan.juris} package id")
    ed, ver = m.group(3), m.group(4)
    try:
        if plan.line == "CF":
            from cf_engine.resolve.book import book_for as cf_book
            b = cf_book(plan.juris, ed, ver)
        else:
            from gl_engine.resolve.book import ResolvedBook
            b = ResolvedBook(iso.resolver("GL").resolve(plan.juris, ed, ver))
    except Exception as e:
        raise Refused(f"edition pin {plan.pin} cannot be honoured: {e}") from None
    if b.state.pkg_id != plan.pin:
        raise Refused(f"edition pin {plan.pin} cannot be honoured: {ed} resolves to "
                      f"{b.state.pkg_id}")
    return b


# --------------------------------------------------------- 4b' group LCMs

#: Which CF coverage group a rate operand belongs to, by ISO's own names
#: (every LCM product in the Iowa and countrywide rules was surveyed: 54 of 89
#: operand names carry their group in the name; the rest -- flood, terrorism,
#: sublimits, endorsements -- keep the record's LCM, which is Group I, G2).
_GROUPS = (("Earthquake", re.compile(r"EQ|Earthquake")),
           ("Broad", re.compile(r"Broad")),
           ("GroupII", re.compile(r"GroupII|BGII")),
           ("GroupI", re.compile(r"GroupI(?!I)|BGI(?!I)")),
           ("Special", re.compile(r"Special(?!Class|Coinsurance)")))


def group_of(names) -> str | None:
    for n in names:
        for g, rx in _GROUPS:
            if rx.search(n):
                return g
    return None


def _up(node, tag: str):
    n = node
    while n is not None:
        c = n.first(tag)
        if c is not None and c.text not in (None, ""):
            return str(c.text)
        n = n.parent
    return None


def _basis(node, group: str, names, fixed_rt=None) -> str:
    if any(n.startswith("Specific") for n in names):
        return "Specific"
    rt = (_up(node, "RatingTypeBasicGroupII") if group == "GroupII" else None) or fixed_rt or _up(node, "RatingType")
    return "Specific" if rt == "Specific" else "Class"


def _final(entry, iso_lcm: Decimal) -> Decimal:
    value, mode, _ = entry
    return value if mode == "replace" else iso_lcm * value


class GroupLCM:
    """The interpreter's `group_lcm` hook for one company rating (D17)."""

    def __init__(self, plan: Plan, iso_lcm: Decimal):
        self.plan, self.iso_lcm = plan, iso_lcm

    def __call__(self, ip, el, kids, fr):
        at = None
        names = []
        for i, k in enumerate(kids):
            fd = k.attrib.get("FromDataDef", "")
            if fd.rsplit("/", 1)[-1] == "LossCostMultiplier" and ip.tag(k) in ("FirstValue", "Value"):
                at = i
            elif fd:
                names.append(fd.rsplit("/", 1)[-1])
        if at is None:
            return None
        group = group_of(names)
        if group is None:
            return None
        node = fr.data
        fixed = _fixed_class(self.plan, node)
        cls = fixed[0] if fixed else _up(node, "ClassCode")
        if cls is None:
            self.plan.warn(f"a {group} rate on {node.tag} has no class: it keeps the record's LCM")
            return None
        basis = _basis(node, group, names, fixed[1] if fixed else None)
        entry = self.plan.group_lcm.get((group, basis, cls))
        if entry is None:
            self.plan.warn(f"no company {group} LCM for class {cls} ({basis}): ISO's LCM applies")
            return None
        v = _final(entry, self.iso_lcm)
        if ip.taint is not None:
            ip.taint.hit()
        ip.note("company-group-lcm", f"{group}/{basis}/{cls} -> {v} ({entry[2]})",
                self.plan.ref or "", group=group, basis=basis, class_code=cls, value=str(v),
                explain=entry[2], operands=names, node=id(node))
        return {at: v}


# ----------------------------------------------------------- 4b record LCMs

#: The Property records ISO's schema gives their own `LossCostMultiplier`.
CF_LCM_RECORDS = ("CommercialPropertyStructure", "CommercialPropertyOccupClass",
                  "CommercialPropertyPersonalProperty", "CommercialPropertyBusinessIncome",
                  "CommercialPropertySpecialClass", "CommercialPropertySpecialClassBusnIncome")


#: The LCM field each line's records carry.
LCM_FIELD = {"CF": "LossCostMultiplier", "GL": "LCM"}


def strip_lcms(obj, warnings: list, path: str = "", key: str = "LossCostMultiplier") -> None:
    """Remove every submitted LCM from a request body (D13): technical ignores
    them and the carrier's are the company's. A value other than 1 is named."""
    if isinstance(obj, dict):
        for k in list(obj):
            if k == key:
                v = obj.pop(k)
                try:
                    one = Decimal(str(v)) == 1
                except Exception:
                    one = False
                if v not in (None, "") and not one:
                    warnings.append(f"submitted LossCostMultiplier {v} at {path or '/'} ignored (D13)")
            else:
                strip_lcms(obj[k], warnings, f"{path}/{k}", key)
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            strip_lcms(x, warnings, f"{path}[{i}]", key)


def iso_request(payload: dict, line: str) -> tuple[dict, list]:
    """The request ISO's service may see for a company rating: our header fields
    gone (M6) and every submitted LCM removed (D13) -- exactly what technical
    rates. Returns (request, warnings); the original is untouched."""
    import copy
    out = copy.deepcopy(payload)
    hdr = out.get("header")
    if isinstance(hdr, dict):
        for k in ("WritingCompany", "PolicyType"):
            hdr.pop(k, None)
    warnings: list = []
    block = "CommercialProperty" if line == "CF" else "GeneralLiability"
    strip_lcms((out.get("body") or {}).get(block), warnings, block, LCM_FIELD[line])
    return out, warnings


def _fixed_class(plan: Plan, node):
    n = node
    while n is not None:
        got = plan.record_class.get(id(n))
        if got is not None:
            return got
        n = n.parent
    return None


def write_record_lcms(plan: Plan, data, iso_lcm: Decimal, ip=None) -> int:
    """Write the company's Group I LCM onto every classed Property record (G2)."""
    n = 0
    stack = [data]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        if node.tag not in CF_LCM_RECORDS:
            continue
        cls = _up(node, "ClassCode")
        if cls is None:
            continue
        rt = _up(node, "RatingType")
        plan.record_class[id(node)] = (cls, rt)
        basis = "Specific" if rt == "Specific" else "Class"
        entry = plan.group_lcm.get(("GroupI", basis, cls))
        if entry is None:
            continue
        v = _final(entry, iso_lcm)
        f = node.first("LossCostMultiplier")
        if f is None:
            f = node.add("LossCostMultiplier", str(v))
        else:
            f.text = str(v)
        if ip is not None and ip.taint is not None:
            ip.taint.mark(f)
        n += 1
        if ip is not None:
            ip.note("company-record-lcm", f"{node.tag} class {cls} -> {v} ({entry[2]})",
                    plan.ref or "")
    return n


#: GL coverage records that carry their own `LCM`, and ISO's table for each.
GL_LCM_RECORDS = {"GeneralLiabilityClassificationPremOpsCoverage": ("PremOps", "PremOpsLCM"),
                  "GeneralLiabilityClassificationProdsCompldOpsCoverage": ("ProdsCompldOps",
                                                                           "ProdsCompldOpsLCM")}


def _state_value(book, table: str, col: str) -> Decimal:
    try:
        t = book.table(table)
    except Exception:
        return Decimal(1)
    si, fi = t.col("StateCode"), t.col(col)
    for r in t.rows:
        if r[si] == book.juris:
            return Decimal(str(r[fi]))
    return Decimal(str(t.rows[0][fi])) if t.rows else Decimal(1)


def iso_state_lcm(book, line: str) -> Decimal:
    """ISO's own Property LCM for the state: what a `multiply` LCM row multiplies."""
    return _state_value(book, "LossCostMultiplier", "Factor") if line == "CF" else Decimal(1)


def write_gl_lcms(plan: Plan, data, book, ip=None) -> int:
    """Write the company's LCM onto each GL coverage record, by coverage and class."""
    n = 0
    iso_lcm = {cov: _state_value(book, t, "Rate") for cov, t in GL_LCM_RECORDS.values()}
    stack = [data]
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        got = GL_LCM_RECORDS.get(node.tag)
        if got is None:
            continue
        cov = got[0]
        cls = _up(node, "ClassCode")
        entry = plan.lcm.get((cov, cls)) if cls else None
        if entry is None:
            continue
        v = _final(entry, iso_lcm[cov])
        f = node.first("LCM")
        if f is None:
            f = node.add("LCM", str(v))
        else:
            f.text = str(v)
        if ip is not None and ip.taint is not None:
            ip.taint.mark(f)
        n += 1
        if ip is not None:
            ip.note("company-record-lcm", f"{node.tag} class {cls} -> {v} ({entry[2]})", plan.ref or "")
    return n


class CompanyRunChecks:
    """The book's hooks with the company's LCM step in front (4b)."""

    def __init__(self, inner, plan: Plan, iso_lcm: Decimal, book=None):
        self.inner, self.plan, self.iso_lcm, self.book = inner, plan, iso_lcm, book

    def before(self, ip, data):
        quiet = getattr(ip, "_lookahead", False)
        if self.plan.track and not quiet:
            from gl_engine.interp.taint import Taint
            ip.taint = Taint()
        if self.plan.group_lcm:
            ip.group_lcm = GroupLCM(self.plan, self.iso_lcm)
            write_record_lcms(self.plan, data, self.iso_lcm, None if quiet else ip)
        if self.plan.lcm:
            write_gl_lcms(self.plan, data, self.book, None if quiet else ip)
        return self.inner.before(ip, data) if self.inner else None

    def after(self, ip, data, pending):
        if self.inner:
            self.inner.after(ip, data, pending)

    def finish(self, ip, data):
        if self.inner:
            self.inner.finish(ip, data)


# ----------------------------------------------------------- 4c the book

class CompanyBook:
    """An ISO book with the company's tables in front of it (M1: company-state >
    ISO-state > ISO-countrywide). Everything not overridden is the ISO book's."""

    def __init__(self, iso_book, plan: Plan):
        self._iso = iso_book
        self.plan = plan
        self._cache: dict = {}
        self.iso_lcm = iso_state_lcm(iso_book, plan.line)
        hooks = getattr(iso_book, "run_hooks", None)
        self.run_hooks = (CompanyRunChecks(hooks, plan, self.iso_lcm, iso_book)
                          if (hooks is not None or plan.group_lcm or plan.lcm) else None)
        for name in plan.overrides:          # a key the edition lacks refuses up front
            self.table(name)

    def __getattr__(self, name):
        return getattr(self._iso, name)

    def table(self, name: str, kind: str = "Rate"):
        t = self._iso.table(name, kind)
        ov = self.plan.overrides.get(name) if kind == "Rate" else None
        if ov is None:
            return t
        got = self._cache.get(name)
        if got is None:
            got = self._cache[name] = self._compose(t, ov)
        return got

    def _compose(self, t, ov):
        idx = [t.col(k) for k in ov["keys"]]
        ci = t.col(ov["col"])
        seen, rows = set(), []
        for r in t.rows:
            k = tuple(str(r[i]) for i in idx)
            e = ov["rows"].get(k)
            if e is None:
                rows.append(r)
                continue
            seen.add(k)
            value, mode, _ = e
            new = value if mode == "replace" else Decimal(str(r[ci])) * value
            rows.append(tuple(new if i == ci else c for i, c in enumerate(r)))
        missing = set(ov["rows"]) - seen
        if missing:
            raise Refused(f"{self.plan.ref} overrides {t.name} at "
                          f"{'/'.join(sorted(missing)[0])}, which {t.package} does not have "
                          f"({len(missing)} key{'s' if len(missing) != 1 else ''} missing)")
        return dataclasses.replace(t, rows=rows, package=f"{t.package}+{self.plan.ref}")
