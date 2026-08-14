"""Where the corpus lives, and the one date the engine refuses to go below.

The corpus path is settable by environment variable so the engine is not welded
to one machine, but it has a working default because every analysis script in
this project already assumes it.
"""
from __future__ import annotations

import os
from pathlib import Path

#: Root of the ISO ERC General Liability corpus.
CORPUS_ROOT = Path(os.environ.get(
    "GL_ERC_ROOT", r"C:\Projects\ISO_ERC_Files\General_Liability"))

#: Directories under the root that are not jurisdictions.
#: `_quarantine_misfiled` holds a stray package deliberately set aside during
#: analysis; scanning it would double-count a jurisdiction.
EXCLUDE_DIRS = frozenset({"_quarantine_misfiled", ".claude"})

#: Below this date the corpus cannot resolve all 51 jurisdictions (OI-41).
#: An engine that served a partial answer here would look like it worked.
MIN_ASOF = "20220901"

#: The jurisdiction token the countrywide layer uses in its own namespace.
COUNTRYWIDE = "CW"

#: 2027-04-01: 43 jurisdictions change classification basis on one morning.
#: Not used as a switch anywhere -- recorded so tests can name the date.
CLASS_BASIS_CLIFF = "20270401"
