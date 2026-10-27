"""Where carrier content lives, and the few fixed vocabularies it is checked against."""
from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

#: Root of every carrier's deviation content. Outside the repo and the ZIPs:
#: filings are a carrier's content, not the harness's, exactly as the ISO
#: corpus is ISO's (see `GL_ERC_ROOT` / `CF_ERC_ROOT`).
CARRIERS_ROOT = Path(os.environ.get(
    "CARRIERS_ROOT", r"C:\FederatoProjects\Carriers"))

LINES = ("CF", "GL")

#: What an `LCM:` target can name, per line. `All` is an authoring shortcut for
#: every entry of the line and is less specific than naming one.
#:
#: CF's entries are ISO's coverage groups, because ISO's Property rules multiply
#: each group's base rate by the record's one `LossCostMultiplier`, and a filing
#: may set a different LCM per group (D17, from the UFG Iowa filing).
#: GL's are the coverage records that each carry their own `LCM` field.
LCM_TARGETS = {
    "CF": ("GroupI", "GroupII", "Broad", "Special", "Earthquake"),
    "GL": ("PremOps", "ProdsCompldOps"),
}

#: CF only: a Group I rate is either specific or class rated, and filings may
#: price them apart (G5). "Specific" includes special class rates, per the UFG
#: exception page footnote.
RATING_BASES = ("Specific", "Class")

#: Scope keys an `LCM:` row may use in v1, per line. Territory, limit and
#: deductible keyed LCMs are in D3 but arrive with the GL engine step (P2);
#: `validate` refuses them by name rather than ignoring them.
LCM_SCOPE_KEYS = {
    "CF": ("class", "class_group", "rating_basis"),
    "GL": ("class", "class_group"),
}
LCM_SCOPE_LATER = ("territory", "limit", "deductible")

#: An LCM outside its band needs a `note` on the row saying why. Bands are per
#: target, because a Property Group II LCM of 2 to 4 is ordinary (UFG files
#: 2.062 to 3.934) where the same figure on Group I would be a typo.
LCM_BANDS = {
    ("CF", "GroupI"): (Decimal("0.25"), Decimal("3")),
    ("CF", "GroupII"): (Decimal("0.25"), Decimal("5")),
    ("CF", "Broad"): (Decimal("0.25"), Decimal("5")),
    ("CF", "Special"): (Decimal("0.25"), Decimal("5")),
    ("CF", "Earthquake"): (Decimal("0.25"), Decimal("5")),
    ("GL", "PremOps"): (Decimal("0.25"), Decimal("3")),
    ("GL", "ProdsCompldOps"): (Decimal("0.25"), Decimal("3")),
}

#: Policy-level items (B-21, plan O4): what a filing sets on the whole policy rather than on a table. Applied by our
#: engine after ISO's rules have rated the carrier; ISO's service never sees them (D21). Each is one value per
#: policy, so `replace` only and no scope.
#:   MIN:Policy        the policy minimum premium, in dollars: a carrier total under it is raised to it
#:   PCT:Terrorism     CF: terrorism as a share of the property premium (0.02 = 2%), in place of ISO's charge
POLICY_TARGETS = {
    "CF": ("MIN:Policy", "PCT:Terrorism"),
    "GL": ("MIN:Policy",),
}

MODES = ("replace", "multiply")
STATUSES = ("draft", "proposed", "approved", "withdrawn")
