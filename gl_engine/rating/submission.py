"""A submission, mapped onto the ERC data tree.

ISO's rules address repeated elements through a container: the `Default` block
iterates `GeneralLiabilityTable/GeneralLiability`, and rules reach across with
`../GeneralLiabilityLocationTable/GeneralLiabilityLocation`. **A RAaS request
does not carry those containers** -- its JSON has a bare list under
`GeneralLiability` and another under `GeneralLiabilityLocation`.

So the mapping rule is one line: **every JSON list named `X` becomes an element
`XTable` holding repeated `X` children.** Everything else is a direct
translation.

That rule is not a convention we chose. It is what ISO's own paths require, and
it is checked in `tests/verify_stage3.py` by taking every `ForEach` path in the
resolved package and asserting the built tree can satisfy them.

Getting this wrong is quiet. A path that misses returns nothing, a `ForEach`
over nothing iterates zero times and is *not* an error (contract section 9), and
the premium comes out finished and too small.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..interp.tree import Node

#: The request envelope RAaS uses. The rating content is under `body`.
BODY = "body"
SCHEME = "SchemeKeys"

#: The root element name the rules assume. `/*/State/Code` addresses it with a
#: wildcard, so the name matters less than its existence -- but it is named
#: consistently so a trace is readable.
ROOT = "GeneralLiabilityRequest"


def _build(parent: Node, key: str, value) -> None:
    """Attach `value` under `parent` as `key`, wrapping lists in `<key>Table`."""
    if isinstance(value, list):
        table = parent.add(f"{key}Table")
        for item in value:
            child = table.add(key)
            if isinstance(item, dict):
                for k, v in item.items():
                    _build(child, k, v)
            elif item is not None:
                child.text = _text(item)
        return
    if isinstance(value, dict):
        child = parent.add(key)
        for k, v in value.items():
            _build(child, k, v)
        return
    parent.add(key, None if value is None else _text(value))


def _text(v) -> str:
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def from_raas(payload: dict) -> tuple[Node, str, str]:
    """Build the data tree from a RAaS-shaped request.

    Returns `(tree, jurisdiction, effective_date)` -- the last two because the
    engine must resolve the rulebook from the submission itself rather than be
    told, which is how a request and the rules that priced it stay attached.
    """
    body = payload.get(BODY, payload)
    scheme = body.get(SCHEME, {})

    eff = scheme.get("EffectiveDateTime") or scheme.get("EffectiveDate")
    if not eff:
        raise ValueError(
            f"submission has no {SCHEME}.EffectiveDateTime; the rulebook "
            f"cannot be resolved and must not be assumed")
    eff_date = str(eff)[:10]

    root = Node(ROOT)
    root.add("EffDate", eff_date)

    for key, value in body.items():
        if key == SCHEME:
            continue
        _build(root, key, value)

    juris = _jurisdiction(root, scheme)
    return root, juris, eff_date.replace("-", "")


def _jurisdiction(root: Node, scheme: dict) -> str:
    """The state, taken from the risk rather than from the envelope.

    `SchemeKeys.ProductName` carries it too ("General Liability OK"), but the
    risk's own `State` is the authority: a multi-state request would make the
    product name a summary rather than a fact.
    """
    from ..interp import tree as _t
    found = {n.text for n in _t.select("GeneralLiabilityTable/"
                                       "GeneralLiability/State", root)
             if n.text}
    if len(found) == 1:
        return found.pop()
    if len(found) > 1:
        raise ValueError(
            f"submission spans {sorted(found)}; one request rates one "
            f"jurisdiction until multi-state is built (stage 4)")
    name = str(scheme.get("ProductName", ""))
    tail = name.rsplit(" ", 1)[-1]
    if len(tail) == 2 and tail.isalpha():
        return tail.upper()
    raise ValueError(
        "submission names no jurisdiction; it will not be guessed")


def load(path: str | Path) -> tuple[Node, str, str]:
    """Read a RAaS request from disk. BOM-tolerant, as every ISO file is."""
    return from_raas(json.loads(Path(path).read_text(encoding="utf-8-sig")))
