"""Find every Property package, and ask each one who it is.

The two rules General Liability learned the hard way apply here unchanged, and
the Property corpus breaks both harder than GL's does.

**N6 -- identity comes from the XSD `targetNamespace`, never the directory.**
On disk the countrywide package is `CFCW20260601V01` and Oregon is
`CF OR 20260601 V01`; in the namespaces they are `CF_CW_20260601_V01` and
`CF_OR_20260601_V01`. The folder names disagree with ISO in two different ways
at once -- one drops every separator, the other uses spaces where the namespace
uses underscores -- so a reader keyed on the path disagrees with ISO about what
it is holding.

**A search predicate must never define a population.** Discovery walks the tree
and takes every directory containing a `DataDefs/`.

**One structural difference from GL, and it changes de-duplication.** The GL
corpus is laid out root / jurisdiction / package. The Property corpus is laid
out root / *edition batch* / package -- eight snapshot folders, and the same
package is frequently present in more than one of them. De-duplicating by
package id is therefore not a tidy-up here the way it is in GL; without it
every population figure counts several jurisdictions twice.

**And an edition folder does not name its packages' editions.** `CF/20260601/`
holds `CF AK 20261101 V02`, five months after the folder it sits in. Nothing
here reads the folder name for anything except reporting where a package was
found.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..config import CORPUS_ROOT, EXCLUDE_DIRS
# The container types and the directory walk are line-agnostic and shared. Only
# identity is line-specific, which is the whole of this module.
from gl_engine.erc.discovery import Package, PackageId, _content_dirs, read_text
from gl_engine.errors import IdentityError

#: `targetNamespace="http://www.verisk.com/iso/erc/CF_OR_20260601_V01/..."`
_TARGET_NS = re.compile(
    r'targetNamespace\s*=\s*"http://www\.verisk\.com/iso/erc/([^/"]+)/')

#: the `xs:import` naming the countrywide parent this package DECLARES (N5)
_IMPORT_CW = re.compile(
    r'namespace\s*=\s*"http://www\.verisk\.com/iso/erc/(CF_CW_[^/"]+)/')

#: `CF_OR_20260601_V01` -> juris OR, edition 20260601, version V01
_PKG_ID = re.compile(
    r"^CF_(?P<juris>[A-Za-z]{2})_(?P<edition>\d{8})_(?P<version>V\d+)$")


def parse_id(raw: str) -> PackageId:
    """A Property package's identity, exactly as the package states it."""
    m = _PKG_ID.match(raw)
    if not m:
        raise IdentityError(
            f"namespace token {raw!r} is not CF_<JJ>_<YYYYMMDD>_<Vnn>; "
            f"identity cannot be established and must not be guessed")
    return PackageId(raw, m.group("juris").upper(), m.group("edition"),
                     m.group("version"))


def _identify(defs_dir: Path):
    """Identity and declared parent, from a package's DataDefs XSDs.

    Property ships ONE master XSD per package (`MasterCFCW.DataDef.xsd` and so
    on) where GL ships many, so the "every XSD must agree" check has nothing to
    disagree with here. It is still written as a loop over all of them, because
    the reason GL reads them all is that taking the first cannot detect the
    failure it would cause -- and a corpus that ships one file today may ship
    two tomorrow.

    The master XSD is large (7.6 MB countrywide) and both the namespace and the
    import sit in its opening element, so only the head is read.
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
        raise IdentityError(
            f"no targetNamespace in any of {n} XSDs under {defs_dir}")
    return sorted(namespaces)[0], namespaces, parent, n


def discover(root: Path | None = None) -> list[Package]:
    """Every Property package in the corpus, identified from its own XSDs.

    De-duplicated by package id, first path in sorted order winning, so the
    result is deterministic and a package present in three edition batches is
    one package.
    """
    root = Path(root or CORPUS_ROOT)
    if not root.is_dir():
        raise IdentityError(f"corpus root does not exist: {root}")

    by_id: dict[str, Package] = {}
    for batch_dir, content in _content_dirs(root):
        ns, all_ns, parent, n = _identify(content / "DataDefs")
        pkg = Package(
            identity=parse_id(ns), content=content, declared_parent=parent,
            juris_dir=batch_dir, xsd_count=n, namespaces=frozenset(all_ns),
        )
        by_id.setdefault(pkg.pkg_id, pkg)
    return sorted(by_id.values(),
                  key=lambda p: (p.identity.juris, p.identity.sort_key))
