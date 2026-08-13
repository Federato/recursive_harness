"""Rule files, indexed -- including the entry point every census missed.

One package holds up to 526 `*.Rule.xml` files. Each is a `Rules` document
holding `Rule` elements, and -- in exactly one file per package -- a `Default`
element that is a sibling of the rules rather than one of them.

**`Default` is the program's entry point (contract §2).** Every prior analysis of
this corpus walked `Rule` elements and so could not see it, and concluded the
program began at `GeneralLiabilityRules.ErcProcess`. `ErcProcess` is the third
thing `Default` calls; before it the block seeds `ExpDate`, and after it comes
`ErcCalculateTotalPremium`. An interpreter entered at `ErcProcess` returns a
complete, plausible premium with no expiry date and no total.

Measured over 567 packages: **567 `Default` blocks, one per package, always in
`Overall Rating.Rule.xml`, one call sequence and one iteration target, with no
variation across editions within a jurisdiction.**
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..erc.discovery import Package, read_text
from .values import InterpretError

#: The one file that carries `Default`, in 567 of 567 packages.
ENTRY_FILE = "Overall Rating"

_SUFFIX = ".Rule.xml"


def lname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


@dataclass
class RuleFile:
    """One `*.Rule.xml`, parsed once."""

    name: str                                   # 'GeneralLiabilityRules'
    path: Path
    rules: dict = field(default_factory=dict)   # rule name -> Element
    default: object | None = None               # the Default element, if any

    @classmethod
    def load(cls, path: Path) -> "RuleFile":
        root = ET.fromstring(read_text(path))
        rf = cls(name=path.name[: -len(_SUFFIX)], path=path)
        for el in root:
            tag = lname(el.tag)
            if tag == "Rule":
                nm = el.attrib.get("Name")
                if not nm:
                    raise InterpretError(
                        f"unnamed Rule in {path.name}", "§3", str(path))
                # Later definitions do not silently replace earlier ones; a
                # duplicate name means the file is not what we think it is.
                if nm in rf.rules:
                    raise InterpretError(
                        f"rule {nm!r} defined twice in {path.name}", "§3",
                        str(path))
                rf.rules[nm] = el
            elif tag == "Default":
                if rf.default is not None:
                    raise InterpretError(
                        f"two Default blocks in {path.name}", "§2", str(path))
                rf.default = el
        return rf


class Program:
    """Every rule in one package, loaded lazily by file.

    Lazily because a package holds up to 526 rule files and a rating touches a
    fraction of them; the alternative is parsing 211 MB of XML to answer one
    question.
    """

    def __init__(self, package: Package):
        self.package = package
        self.dir = package.content / "Rules"
        self._files: dict[str, RuleFile] = {}
        if not self.dir.is_dir():
            raise InterpretError(
                f"{package.pkg_id} has no Rules directory", "§3", str(self.dir))

    @property
    def pkg_id(self) -> str:
        return self.package.pkg_id

    def has_file(self, name: str) -> bool:
        """Does this package hold this rule file? Asked before inheriting."""
        return (self.dir / f"{name}{_SUFFIX}").exists()

    def file(self, name: str) -> RuleFile:
        if name not in self._files:
            path = self.dir / f"{name}{_SUFFIX}"
            if not path.exists():
                raise InterpretError(
                    f"{self.pkg_id}: no rule file {name!r}", "§8", str(self.dir))
            self._files[name] = RuleFile.load(path)
        return self._files[name]

    def rule(self, file_name: str, rule_name: str):
        rf = self.file(file_name)
        el = rf.rules.get(rule_name)
        if el is None:
            raise InterpretError(
                f"{self.pkg_id}: {file_name} has no rule {rule_name!r}",
                "§8", str(rf.path))
        return el

    def entry(self):
        """The `Default` block. Hard failure if absent -- never fall back.

        Falling back to `ErcProcess` here would reintroduce exactly the defect
        contract §2 exists to prevent, and it would do it silently.
        """
        rf = self.file(ENTRY_FILE)
        if rf.default is None:
            raise InterpretError(
                f"{self.pkg_id}: {ENTRY_FILE}{_SUFFIX} has no Default block; "
                f"the engine does not fall back to a rule",
                "§2", str(rf.path))
        return rf.default

    @lru_cache(maxsize=None)
    def file_names(self) -> tuple[str, ...]:
        return tuple(sorted(p.name[: -len(_SUFFIX)]
                            for p in self.dir.glob(f"*{_SUFFIX}")))

    def __repr__(self) -> str:            # pragma: no cover - display only
        return f"<Program {self.pkg_id}>"
