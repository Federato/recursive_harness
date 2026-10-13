"""Reading and writing the carrier, company, filing and workflow files.

These are plain JSON (and JSONL for the workflow log) so that a person can read
and edit them; this module is the only place that knows their shape.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


class FileError(ValueError):
    """A deviation file that cannot be read as what it claims to be."""


def read_json(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"),
                          parse_float=Decimal)
    except FileNotFoundError:
        raise FileError(f"{path}: not found") from None
    except json.JSONDecodeError as e:
        raise FileError(f"{path}: not valid JSON ({e})") from None


_DEC = re.compile(r'"\\u0000dec:([-0-9.Ee+]+)"')


def _mark(o):
    """Decimals become marked strings so they can be written as bare numbers."""
    if isinstance(o, Decimal):
        return "\u0000dec:" + str(o)
    if isinstance(o, dict):
        return {k: _mark(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_mark(v) for v in o]
    return o


def dumps(data) -> str:
    """JSON with every Decimal written as its own digits: 1.067, never 1.0669999."""
    return _DEC.sub(r"\1", json.dumps(_mark(data), indent=2, ensure_ascii=False))


def write_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(data) + "\n", encoding="utf-8")


# -------------------------------------------------------------- the tree

@dataclass
class Row:
    """One authored row: a target, where it applies, and what it does."""

    id: str                     # '<filing>.v<n>#<1-based index>'
    target: str                 # 'LCM:GroupI', 'TABLE:<name>.<value col>'
    scope: dict
    value: Decimal
    mode: str
    cite: str = ""
    note: str = ""

    def as_authored(self) -> dict:
        out = {"target": self.target, "scope": dict(self.scope),
               "value": self.value, "mode": self.mode}
        if self.cite:
            out["cite"] = self.cite
        if self.note:
            out["note"] = self.note
        return out


@dataclass
class Filing:
    path: Path
    raw: dict
    rows: list[Row] = field(default_factory=list)

    @property
    def filing(self) -> str:
        return self.raw.get("filing", "")

    @property
    def version(self) -> int:
        return self.raw.get("version", 0)

    @property
    def ref(self) -> str:
        return f"{self.filing}.v{self.version}"

    @property
    def company(self) -> str:
        return self.raw.get("company", "")

    @property
    def line(self) -> str:
        return self.raw.get("line", "")

    @property
    def company_dir(self) -> Path:
        return self.path.parent.parent

    @property
    def carrier_dir(self) -> Path:
        return self.company_dir.parent


def load_filing(path: Path) -> Filing:
    """Read an authored filing. Shape errors are left for `validate` to report
    together; only an unreadable file raises here."""
    path = Path(path)
    raw = read_json(path)
    f = Filing(path, raw)
    for i, r in enumerate(raw.get("rows") or [], start=1):
        if not isinstance(r, dict):
            r = {}
        f.rows.append(Row(
            id=f"{f.ref}#{i}", target=str(r.get("target", "")),
            scope=r.get("scope") if isinstance(r.get("scope"), dict) else {},
            value=r.get("value") if isinstance(r.get("value"), Decimal)
            else _dec(r.get("value")),
            mode=str(r.get("mode", "")), cite=str(r.get("cite", "")),
            note=str(r.get("note", ""))))
    return f


def _dec(v):
    if isinstance(v, int) and not isinstance(v, bool):
        return Decimal(v)
    if isinstance(v, str):
        try:
            return Decimal(v)
        except Exception:
            return None
    return None


def authored_path(company_dir: Path, filing: str, version: int) -> Path:
    return Path(company_dir) / "authored" / f"{filing}.v{version}.json"


def compiled_dir(company_dir: Path, line: str, juris: str, ref: str) -> Path:
    return Path(company_dir) / "compiled" / line / juris / ref


def carrier_json(carrier_dir: Path) -> dict:
    p = Path(carrier_dir) / "carrier.json"
    return read_json(p) if p.exists() else {}


def company_json(company_dir: Path) -> dict:
    p = Path(company_dir) / "company.json"
    return read_json(p) if p.exists() else {}


def class_groups(carrier_dir: Path, company_dir: Path) -> dict[str, list[str]]:
    """Class groups as authored: carrier level, then company level over it (G7)."""
    out = dict(carrier_json(carrier_dir).get("class_groups") or {})
    out.update(company_json(company_dir).get("class_groups") or {})
    return out


def expand_codes(spec: list[str], universe: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """'0077-0079' style entries -> the edition's codes they hold.

    Returns `(codes, problems)`. A range takes every code the edition has
    between its endpoints inclusive; each endpoint must itself be a code the
    edition has, so a mistyped range is refused rather than quietly shrunk.
    """
    have = set(universe)
    codes: list[str] = []
    problems: list[str] = []
    for entry in spec:
        entry = str(entry).strip()
        lo, _, hi = entry.partition("-")
        hi = hi or lo
        bad = [e for e in dict.fromkeys((lo, hi)) if e not in have]
        if bad:
            problems.append(f"{entry}: {', '.join(bad)} not a class in this edition")
            continue
        if lo > hi:
            problems.append(f"{entry}: range runs backwards")
            continue
        codes += [c for c in universe if lo <= c <= hi]
    return sorted(set(codes)), problems


# ---------------------------------------------------------- workflow log

def workflow_path(company_dir: Path) -> Path:
    return Path(company_dir) / "workflow.jsonl"


def log_action(company_dir: Path, filing: str, version: int, action: str,
               by: str, note: str = "", ts: str | None = None) -> dict:
    """Append one line to the workflow log. The log is never rewritten (M4)."""
    if action not in ("propose", "sign-off", "reject", "withdraw"):
        raise FileError(f"unknown workflow action {action!r}")
    if not by.strip():
        raise FileError("a workflow action needs a name (--by)")
    line = {"ts": ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "filing": filing, "version": version, "action": action,
            "by": by.strip()}
    if note:
        line["note"] = note
    p = workflow_path(company_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    return line


def workflow_status(company_dir: Path, filing: str, version: int,
                    signoffs_needed: int = 1) -> dict:
    """Where one filing version stands, read from its log lines in order.

    `propose` starts (or restarts) a review and clears earlier sign-offs;
    `sign-off` adds a distinct name; `reject` and `withdraw` end it. It is
    approved when, after the last propose, enough distinct people signed off
    and nothing later rejected or withdrew it -- the latest line wins.
    """
    state, signers, lines = "draft", [], []
    p = workflow_path(company_dir)
    if p.exists():
        for raw in p.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            ln = json.loads(raw)
            if ln.get("filing") != filing or ln.get("version") != version:
                continue
            lines.append(ln)
            a = ln.get("action")
            if a == "propose":
                state, signers = "proposed", []
            elif a == "sign-off" and state in ("proposed", "approved"):
                if ln["by"] not in signers:
                    signers.append(ln["by"])
                if len(signers) >= signoffs_needed:
                    state = "approved"
            elif a == "reject":
                state = "rejected"
            elif a == "withdraw":
                state = "withdrawn"
    return {"status": state, "signers": signers, "lines": lines}
