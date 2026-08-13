"""Find every ERC package, and ask each one who it is.

Two rules govern this module and both were learned the hard way.

**N6 -- identity comes from the XSD `targetNamespace`, never the directory.**
The corpus is unpacked inconsistently: some packages sit directly under the
jurisdiction folder, some inside a `_MachineReadableContent` wrapper, and the
folder names use spaces where the namespace uses underscores. A reader keyed on
the path will disagree with ISO about what it is holding.

**A search predicate must never define a population.** Discovery walks the
directory tree and takes every directory containing a `DataDefs/`. It does not
match a naming pattern, because a package whose folder name is unusual is still a
package -- and this corpus has several.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..config import CORPUS_ROOT, EXCLUDE_DIRS
from ..errors import IdentityError

#: `targetNamespace="http://www.verisk.com/iso/erc/GL_NJ_20250301_V01/..."`
_TARGET_NS = re.compile(
    r'targetNamespace\s*=\s*"http://www\.verisk\.com/iso/erc/([^/"]+)/')
#: the `xs:import` that names the countrywide parent this package DECLARES (N5)
_IMPORT_CW = re.compile(
    r'namespace\s*=\s*"http://www\.verisk\.com/iso/erc/(GL_CW_[^/"]+)/')

#: `GL_NJ_20250301_V01` -> juris NJ, edition 20250301, version V01
_PKG_ID = re.compile(r"^GL_(?P<juris>[A-Za-z]{2})_(?P<edition>\d{8})_(?P<version>V\d+)$")

#: Content directories an ERC package may carry. Used only to recognise a
#: wrapper directory, never to decide whether something is a package.
CATEGORIES = (
    "DataDefs", "DOC", "Domain Tables", "Form Fields", "Form Pages",
    "Form Related Fields", "Metadata", "Rate Tables", "Ratebook Columns",
    "Ratebook Tables", "Rules", "STC",
)


def read_text(path: Path, limit: int = -1) -> str:
    """BOM-tolerant read. Every ERC file in this corpus is BOM-prefixed UTF-8."""
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        return fh.read() if limit < 0 else fh.read(limit)


@dataclass(frozen=True)
class PackageId:
    """A package's identity, as the package states it."""

    raw: str                # exactly the namespace token, e.g. 'GL_CW_20231201_V02'
    juris: str              # 'CW', 'NJ', 'DC', 'PR'
    edition: str            # 'YYYYMMDD'
    version: str            # 'V01'

    @classmethod
    def parse(cls, raw: str) -> "PackageId":
        m = _PKG_ID.match(raw)
        if not m:
            raise IdentityError(
                f"namespace token {raw!r} is not GL_<JJ>_<YYYYMMDD>_<Vnn>; "
                f"identity cannot be established and must not be guessed")
        return cls(raw, m.group("juris").upper(), m.group("edition"),
                   m.group("version"))

    @property
    def sort_key(self) -> tuple[str, str]:
        """Edition first, then version -- the tie-break for same-day filings."""
        return (self.edition, self.version)

    def __str__(self) -> str:
        return self.raw


@dataclass
class Package:
    """One ERC package on disk, with its declared identity and parentage."""

    identity: PackageId
    content: Path                    # the directory holding DataDefs/, Rules/, ...
    declared_parent: str | None      # countrywide package id, from xs:import (N5)
    juris_dir: str                   # the directory it was found under
    xsd_count: int = 0
    #: every distinct namespace seen across this package's XSDs. More than one
    #: means the package is not internally consistent and identity is a guess.
    namespaces: frozenset = field(default_factory=frozenset)

    @property
    def pkg_id(self) -> str:
        return self.identity.raw

    @property
    def is_countrywide(self) -> bool:
        return self.identity.juris == "CW"

    def dir(self, category: str) -> Path:
        return self.content / category

    def __repr__(self) -> str:       # pragma: no cover - display only
        par = f" -> {self.declared_parent}" if self.declared_parent else ""
        return f"<Package {self.pkg_id}{par}>"


def _content_dirs(root: Path):
    """Yield every directory holding a `DataDefs/`, at any depth up to three.

    Explicit iteration rather than `os.walk` over 87,000 files: the shape is
    root / jurisdiction / package [ / wrapper ], and walking the leaves costs
    seconds we pay on every engine start.
    """
    for jd in sorted(p for p in root.iterdir()
                     if p.is_dir() and p.name not in EXCLUDE_DIRS):
        for outer in sorted(p for p in jd.iterdir() if p.is_dir()):
            candidates = [outer]
            try:
                candidates += sorted(p for p in outer.iterdir() if p.is_dir())
            except OSError:                                  # pragma: no cover
                pass
            for cand in candidates:
                if (cand / "DataDefs").is_dir():
                    yield jd.name, cand
                    break


def _identify(defs_dir: Path) -> tuple[str, set[str], str | None, int]:
    """Read identity and declared parent out of a package's DataDefs XSDs.

    Reads EVERY XSD, not the first one that matches. Taking the first is faster
    and cannot detect the failure it would cause: a package whose XSDs disagree
    about what package they belong to. That is assertion A2 and it has to have
    something to test.
    """
    namespaces: set[str] = set()
    parent: str | None = None
    n = 0
    for f in sorted(defs_dir.glob("*.xsd")):
        n += 1
        txt = read_text(f, 40000)
        m = _TARGET_NS.search(txt)
        if m:
            namespaces.add(m.group(1))
        p = _IMPORT_CW.search(txt)
        if p and parent is None:
            parent = p.group(1)
    if not namespaces:
        raise IdentityError(f"no targetNamespace in any of {n} XSDs under {defs_dir}")
    return sorted(namespaces)[0], namespaces, parent, n


def discover(root: Path | None = None) -> list[Package]:
    """Every package in the corpus, identified from its own XSDs.

    De-duplicates by package id: the same package is unpacked twice in a few
    jurisdictions (once bare, once wrapped), and counting both would inflate
    every population figure downstream.
    """
    root = Path(root or CORPUS_ROOT)
    if not root.is_dir():
        raise IdentityError(f"corpus root does not exist: {root}")

    by_id: dict[str, Package] = {}
    for juris_dir, content in _content_dirs(root):
        ns, all_ns, parent, n = _identify(content / "DataDefs")
        pkg = Package(
            identity=PackageId.parse(ns), content=content,
            declared_parent=parent, juris_dir=juris_dir,
            xsd_count=n, namespaces=frozenset(all_ns),
        )
        # First path wins; deterministic because _content_dirs is sorted.
        by_id.setdefault(pkg.pkg_id, pkg)
    return sorted(by_id.values(), key=lambda p: (p.identity.juris,
                                                 p.identity.sort_key))
