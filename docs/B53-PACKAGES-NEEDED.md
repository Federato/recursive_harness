# B-53 -- future-dated GL packages: ISO holds a newer version (measured 2026-10-15)

Found by B-51: every state edition we hold dated 2026-10-16 to 2027-03-31 (16) rated once on the base risk at its own
effective date (5 in B-51, 11 in a follow-up probe; adhoc lane, the user's override). ISO rated 13 of the 16 with a
newer version (V03) than ours; in 10 of them the base premium differs (about +8-9%). CA 20270101 V01, NJ 20270101 V03
and WA 20270201 V01 are current (B-38).

**13 packages to download -- 9 in (DE, MD, MO, MT 2026-11-01; AR, ID, NH, NV, VT 2026-12-01), 4 to go (AL, AZ, ME, SC 2027-01-01) (ISO ERC, GL machine-readable content):**

| State | ISO package | We hold | Base premium ours / ISO |
|---|---|---|---|
| AL | `GL AL 20270101 V03` | V01 | 7,096 / 7,751 |
| AR | `GL AR 20261201 V03` | **V03, added 2026-10-15** | 8,501 / 8,501 |
| AZ | `GL AZ 20270101 V03` | V01 | 7,912 / 8,657 |
| DE | `GL DE 20261101 V03` | **V03, added 2026-10-15** | 8,286 / 8,286 |
| ID | `GL ID 20261201 V03` | **V03, added 2026-10-15** | 8,441 / 8,441 |
| MD | `GL MD 20261101 V03` | **V03, added 2026-10-15** | 8,421 / 8,421 |
| ME | `GL ME 20270101 V03` | V01 | 7,531 / 8,196 |
| MO | `GL MO 20261101 V03` | **V03, added 2026-10-15** | 8,361 / 8,361 |
| MT | `GL MT 20261101 V03` | **V03, added 2026-10-15** | 8,607 / 8,607 |
| NH | `GL NH 20261201 V03` | **V03, added 2026-10-15** | 8,311 / 8,311 |
| NV | `GL NV 20261201 V03` | **V03, added 2026-10-15** | 8,937 / 8,937 |
| SC | `GL SC 20270101 V03` | V01 | 7,666 / 8,331 |
| VT | `GL VT 20261201 V03` | **V03, added 2026-10-15** | 7,361 / 7,361 |

Our V01/V02 of these sit on the 2026-01-01 countrywide (VT's on 2023-12-01); ISO's V03s most likely re-point to the
2026-10-01 countrywide, which would explain the ~8-9% move. Not checked for: the 2027-04-01 editions (B-38 checked those
on 2026-10-14) and anything filed after today.

**2026-10-15, 4 of 13 in:** DE, MD, MO, MT 20261101 V03 resolve on the **2026-10-01 countrywide** (confirmed, as guessed) and price the base risk as ISO does. Stored ISO GL answers 500 exact, 5 deliberate refusals, 8 differ (exactly the 8 states still missing: AL, AR, AZ, ID, ME, NH, NV, SC). 0 ISO calls. Unpack with Python `zipfile`, not `unzip`: these ZIPs store Windows paths and `unzip` flattens them.

**2026-10-15, 9 of 13 in:** AR, ID, NH, NV, VT 20261201 V03 added; all on the 2026-10-01 countrywide (VT moves off 2023-12-01) and match ISO's base premium. Stored ISO GL answers 504 exact, 5 deliberate refusals, 4 differ (AL, AZ, ME, SC, still missing). 0 ISO calls.
