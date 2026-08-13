"""Shared helpers for the ERC clean-room extraction pipeline.

Provides: corpus root discovery, package enumeration (walking the
jurisdiction dirs -> package dirs -> optional MachineReadableContent
wrapper), BOM-tolerant text/CSV reading, and namespace-agnostic XML
parsing.

Nothing here writes output; it is imported by 01_..09_ scripts.
"""
from __future__ import annotations

import csv
import io
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(r"C:\Projects\ISO_ERC_Files\General_Liability")
OUT = Path(r"C:\Projects\Recursive_Harness_2.0\scripts\erc\out")
OUT.mkdir(parents=True, exist_ok=True)

# Directory categories observed in packages.
CATEGORIES = [
    "DataDefs", "DOC", "Domain Tables", "Form Fields", "Form Pages",
    "Form Related Fields", "Metadata", "Rate Tables", "Ratebook Columns",
    "Ratebook Tables", "Rules", "STC",
]

# 'GL_NJ 20250301 V01_MachineReadableContent' or 'GL CW 20231201 V01'
PKG_RE = re.compile(
    r"^GL[ _](?P<juris>[A-Z]{2})[ _](?P<edition>\d{8})[ _](?P<version>V\d+)"
    r"(?P<suffix>.*)$"
)


@dataclass
class Package:
    juris_dir: str          # directory name under ROOT (2-letter or 'countrywide')
    outer: Path             # the directory directly under the jurisdiction dir
    content: Path           # dir actually holding DataDefs/ etc (may == outer)
    juris: str = ""
    edition: str = ""
    version: str = ""
    wrapped: bool = False
    name_ok: bool = True
    suffix: str = ""

    @property
    def pkg_id(self) -> str:
        return f"GL_{self.juris}_{self.edition}_{self.version}"

    @property
    def rel(self) -> str:
        return str(self.outer.relative_to(ROOT)).replace("\\", "/")


# Directories under ROOT that are not jurisdictions and must never be scanned.
# `_quarantine_misfiled` was created by the coordinator to hold a stray
# package; it is excluded so it cannot double-count.
EXCLUDE_DIRS = {"_quarantine_misfiled", ".claude"}


def find_packages() -> list[Package]:
    pkgs: list[Package] = []
    for jd in sorted(p for p in ROOT.iterdir()
                     if p.is_dir() and p.name not in EXCLUDE_DIRS):
        for outer in sorted(p for p in jd.iterdir() if p.is_dir()):
            m = PKG_RE.match(outer.name)
            content = outer
            wrapped = False
            # detect a single sub-directory wrapper
            subs = [p for p in outer.iterdir() if p.is_dir()]
            if not any(s.name in CATEGORIES for s in subs) and len(subs) == 1:
                content = subs[0]
                wrapped = True
            pk = Package(
                juris_dir=jd.name, outer=outer, content=content,
                wrapped=wrapped, name_ok=bool(m),
            )
            if m:
                pk.juris = m.group("juris")
                pk.edition = m.group("edition")
                pk.version = m.group("version")
                pk.suffix = m.group("suffix")
            else:
                pk.juris = jd.name
                pk.edition = pk.version = ""
            pkgs.append(pk)
    return pkgs


def read_text(p: Path) -> str:
    b = p.read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):
        b = b[3:]
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("latin-1", "replace")


def read_csv_rows(p: Path):
    """Yield (header:list[str], rows-iterator) for an ERC csv."""
    txt = read_text(p)
    rdr = csv.reader(io.StringIO(txt))
    try:
        header = next(rdr)
    except StopIteration:
        return [], iter(())
    return header, rdr


def parse_xml(p: Path):
    """Parse XML, returning root, or raise. Strips BOM."""
    return ET.fromstring(read_text(p))


def lname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def ns_of(tag: str) -> str:
    return tag[1:].split("}")[0] if tag.startswith("{") else ""
